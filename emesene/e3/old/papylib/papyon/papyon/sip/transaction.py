# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2010 Collabora Ltd.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from papyon.sip.constants import SIPTransactionError, TIMER_B, TIMER_F, TIMER_H
from papyon.sip.message import SIPResponse, SIPRequest, SIPCSeq
from papyon.util.decorator import rw_property
from papyon.util.timer import Timer

import gobject
import logging

logger = logging.getLogger('papyon.sip.transaction')

class SIPTransactionLayer(gobject.GObject):
    """ This class represents the SIP transaction layer as described in
        section 17 of RFC 2361.

        The transaction layer handles application-layer retransmissions,
        matching of responses to requests, and application-layer timeouts.
        Any task that a user agent client (UAC) accomplishes takes place
        using a series of transactions.

        TODO: Use branch parameter in Via to identify transactions"""

    __gsignals__ = {
        'request-received' : (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            (object,)),
        'response-received' : (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            (object,)),
        'error' : (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            (object, object))
    }

    def __init__(self, transport):
        gobject.GObject.__init__(self)
        self._transport = transport
        self._transport.connect("message-received", self._on_message_received)
        self._transactions = {} # transaction => event handles

    def is_merged_request(self, request):
        for transaction in self._transactions:
            if transaction is request.transaction: continue
            if request.match_headers(("From", "Call-Id", "CSeq"),
                    transaction.request):
                return True
        return False

    def find_canceled_transaction(self, cancel):
        return self._find_transaction(cancel, False)

    def send(self, message):
        transaction = None
        if type(message) is SIPRequest:
            transaction = SIPClientTransaction(self._transport)
            self._add_transaction(transaction)
        elif type(message) is SIPResponse:
            transaction = message.request.transaction
        else:
            logger.warning("Invalid message type (%s)" % type(message))
            return

        if transaction is None:
            logger.warning("Couldn't find transaction to send message")
            return

        transaction.send(message)

    def _add_transaction(self, transaction):
        handles = []
        handles.append(transaction.connect("request-received",
            self._on_request_received))
        handles.append(transaction.connect("response-received",
            self._on_response_received))
        handles.append(transaction.connect("terminated",
            self._on_transaction_terminated))
        handles.append(transaction.connect("error",
            self._on_transaction_error))
        self._transactions[transaction] = handles

    def _del_transaction(self, transaction):
        handles = self._transactions.pop(transaction)
        for handle in handles:
            transaction.disconnect(handle)

    def _find_transaction(self, msg, match_method=True):
        for transaction in self._transactions:
            if match_message_to_transaction(msg, transaction, match_method):
                return transaction
        return None

    def _on_message_received(self, transport, msg):
        transaction = self._find_transaction(msg)
        if type(msg) is SIPResponse:
            if transaction is not None:
                transaction._on_response_received(msg)
            else:
                logger.info("Can't find matching transaction for response")
                self.emit("response-received", msg)
        elif type(msg) is SIPRequest:
            if transaction is None and msg.code != "ACK":
                transaction = SIPServerTransaction(self._transport, msg)
                self._add_transaction(transaction)
            if transaction is not None:
                transaction._on_request_received(msg)
            else:
                self.emit("request-received", msg)

    def _on_request_received(self, transaction, request):
        self.emit("request-received", request)

    def _on_response_received(self, transaction, response):
        self.emit("response-received", response)

    def _on_transaction_terminated(self, transaction):
        self._del_transaction(transaction)

    def _on_transaction_error(self, transaction, error):
        self.emit("error", transaction, error)
        self._del_transaction(transaction)


class SIPTransaction(gobject.GObject, Timer):
    """ A SIP transaction consists of a single request and any responses to
        that request, which include zero or more provisional responses and
        one or more final responses. In the case of an INVITE transaction, the
        transaction also includes the ACK only if the final response was not
        a 2xx response."""

    __gsignals__ = {
        'request-received' : (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            (object,)),
        'response-received' : (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            (object,)),
        'terminated' : (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ()),
        'error' : (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            (object,)),
    }

    def __init__(self, transport):
        gobject.GObject.__init__(self)
        Timer.__init__(self)
        self._transport = transport
        self._branch = None
        self._method = None
        self._request = None
        self.__state = None

    @property
    def answered(self):
        """Final response received or not"""
        return bool(self.__state in ("COMPLETED", "TERMINATED"))

    @rw_property
    def _state():
        def fget(self):
            return self.__state
        def fset(self, value):
            if self.__state != value:
                old_state = self.__state
                self.__state = value
                self._on_state_changed(old_state)
        return locals()

    @property
    def request(self):
        return self._request

    @property
    def is_invite(self):
        return self.request.code == "INVITE"

    def destroy(self):
        self._state = "TERMINATED"

    def _send(self, message):
        self._transport.send(message,
                errback=(self._on_transport_error, message))

    def _on_state_changed(self, old_state):
        raise NotImplementedError

    def _on_transport_error(self, error, message):
        logger.error("Transport error while sending %s message" % message.code)
        self.emit("error", SIPTransactionError.TRANSPORT_ERROR)
        self._state = "TERMINATED"


# Client Transaction ---------------------------------------------------------

class SIPClientTransaction(SIPTransaction):
    """ Client component of the transaction layer used to send request.
        It's basically a state machine, working differently wether the request
        is an INVITE one or not.

        See section 17.1 of RFC 2361 for details.

        Note: We assume that the transport layer is reliable. """

    def __init__(self, transport):
        SIPTransaction.__init__(self, transport)

    def send(self, message):
        if type(message) is SIPResponse:
            logger.error("Tried to send a response from client transaction")
            self._state = "TERMINATED"
            return False
        if self._state is not None:
            logger.error("Can't send more thant one request per transaction")
            return False

        self._state = "TRYING"
        self._request = message
        self._request.transaction = self
        self._send(message)
        if self.is_invite:
            self.start_timeout("timerB", TIMER_B)
        else:
            self.start_timeout("timerF", TIMER_F)
        return True

    def _ack(self, response):
        if not self.is_invite:
            return # no need for ACK in non-INVITE transactions
        logger.info("Acking non-2xx INVITE response")
        request = self._create_ack_request(response)
        self._send(request)

    def _create_ack_request(self, response):
        # 17.1.1.3 Construction of the ACK Request
        request = SIPRequest("ACK", self._request.uri)
        request.clone_headers("Route", self._request)
        request.clone_headers("To", response)
        request.clone_headers("From", self._request)
        request.clone_headers("Call-ID", self._request)
        request.clone_headers("Via", self._request) #FIXME single via
        request.add_header("CSeq", SIPCSeq(self._request.cseq.number, "ACK"))
        return request

    def _on_request_received(self, request):
        logger.error("Received a request in client transaction")

    def _on_response_received(self, response):
        response.request = self.request
        if response.status/100 == 1: # provisional response
            if self._state == "TRYING":
                self._state = "PROCEEDING"
            self.emit("response-received", response)
        elif response.status/100 == 2: # OK final response
            if self._state in ("TRYING", "PROCEEDING"):
                self.emit("response-received", response)
                self._state = "TERMINATED"
        elif response.status >= 300: # other final response
            if self._state in ("TRYING", "PROCEEDING"):
                self.emit("response-received", response)
            self._ack(response)
            self._state = "COMPLETED"

    def _on_state_changed(self, old_state):
        if self._state == "COMPLETED":
            self._state = "TERMINATED" # skip COMPLETED state
        elif self._state == "TERMINATED":
            self.stop_all_timeout()
            self.emit("terminated")

    def on_timerB_timeout(self):
        if self._state == "TRYING":
            self.emit("error", SIPTransactionError.TIMEOUT)
            self._state = "TERMINATED"

    def on_timerF_timeout(self):
        if self._state in ("TRYING", "PROCEEDING"):
            self.emit("error", SIPTransactionError.TIMEOUT)
            self._state = "TERMINATED"


# Server Transaction ---------------------------------------------------------

class SIPServerTransaction(SIPTransaction):
    """ Server component of the transaction layer created when receiving requests.
        It's basically a state machine, working differently wether the request
        is an INVITE one or not.

        See section 17.2 of RFC 2361 for details.

        Note: We assume that the transport layer is reliable. """

    def __init__(self, transport, request):
        SIPTransaction.__init__(self, transport)
        self._request = request
        self._last_response = None
        request.transaction = self

        if self.is_invite:
            self._state = "PROCEEDING"
        else:
            self._state = "TRYING"


    def send(self, message):
        if type(message) is SIPRequest:
            logger.error("Tried to send a request from server transaction")
            return False

        if self._state not in ("TRYING", "PROCEEDING"):
            return False

        self._last_response = message
        if message.status/100 == 1:
            self._send(message)
            if self._state == "TRYING":
                self._state = "PROCEEDING"
        elif message.status/100 >= 2:
            self._send(message)
            if self.is_invite and message.status/100 == 2:
                self._state = "TERMINATED"
            else:
                self._state = "COMPLETED"
        return True

    def _on_request_received(self, request):
        # receive ACK for response
        if request.code == "ACK":
            self._on_ack_received(request)
        # request retransmission => send last response received from TU
        elif self._last_response is not None and \
             self._state in ("PROCEEDING", "COMPLETED"):
            self.info("Request retransmission detected => send last response")
            self._send(self._last_response)
        else:
            self.emit("request-received", request)

    def _on_ack_received(self, ack):
        if self._state != "COMPLETED":
            return
        self._state = "CONFIRMED"

    def _on_response_received(self, response):
        logger.error("Received a response in server transaction")

    def _on_state_changed(self, old_state):
        if self._state == "COMPLETED":
            if not self.is_invite:
                self._state = "TERMINATED" # skip CONFIRMED state
            else:
                self.start_timeout("timerH", TIMER_H)
        elif self._state == "CONFIRMED":
            self.stop_timeout("timerH")
            self._state = "TERMINATED" # skip CONFIRMED state
        elif self._state == "TERMINATED":
            self.stop_all_timeout()
            self.emit("terminated")

    def on_timerH_timeout(self):
        self._state = "TERMINATED"
        self.emit("error", SIPTransactionError.TIMEOUT)



# Transaction Matching Util Functions ----------------------------------------

def match_response_to_transaction(response, transaction, match_method=True):
    """ RFC3261: 17.1.3 Matching Responses to Client Transactions """
    # Reponse To header might have a mepid and tag added
    if not response.To.uri.startswith(transaction.request.To.uri):
        return False
    if (response.From.uri != transaction.request.From.uri or
            response.From.tag != transaction.request.From.tag):
        return False
    headers = ("Call-ID", "CSeq")
    return response.match_headers(headers, transaction.request)

def match_request_to_transaction(request, transaction, match_method=True):
    """ RFC3261: 17.2.3 Matching Requests to Server Transactions

        INVITE:         Request-URI, Call-Id, top Via, Cseq, From tag, To tag
        ACK:            Request-URI, Call-Id, top Via, Cseq number, From tag
        Other methods:  Request-URI, Call-Id, top Via, Cseq, From tag, To tag
    """
    if (request.uri != transaction.request.uri or
       not request.match_headers(("Call-Id", "Via"), transaction.request) or
       request.From.tag != transaction.request.From.tag):
        return False

    if request.code == "ACK" or not match_method:
        if request.cseq.number != transaction.request.cseq.number:
            return False
    elif not request.match_header("CSeq", transaction.request):
        return False

    if request.code != "ACK" and request.to.tag != transaction.request.to.tag:
        return False

    return True

def match_message_to_transaction(msg, transaction, match_method=True):
    if type(msg) is SIPResponse:
        return match_response_to_transaction(msg, transaction)
    elif type(msg) is SIPRequest:
        return match_request_to_transaction(msg, transaction, match_method)
    return False

