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

from papyon.sip.constants import SIPMode, T1, T2
from papyon.sip.message import SIPRequest, SIPContact, SIPCSeq, SIPRoute
from papyon.sip.sdp import SDPMessage
from papyon.util.decorator import rw_property
from papyon.util.timer import Timer

import gobject
import logging
import re

__all__ = ['SIPDialog']

logger = logging.getLogger('papyon.sip.dialog')

class SIPDialog(gobject.GObject, Timer):
    """Represent a SIP dialog between two end points. A dialog must be
       initiated by sending or receiving a response to an INVITE request.
       It is disposed when receiving or sending a CANCEL or BYE request.

       See details in section 12 of RFC 3261"""

    __gsignals__ = {
        'ringing': (
            gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ()),
        'accepted': (
            gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            (object,)),
        'rejected': (
            gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            (object,)),
        'offer-received': (
            gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            (object, object)),
        'ended': (
            gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ()),
        'disposed': (
            gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ())
    }

    @property
    def answered(self):
        return (self._state != "INVITED" or self._pending_accept)

    @property
    def call_id(self):
        return self._call_id

    @property
    def local_tag(self):
        return self._local_tag

    @property
    def remote_tag(self):
        return self._remote_tag

    def __init__(self, core, request, response, mode):
        gobject.GObject.__init__(self)
        Timer.__init__(self)
        self._core = core
        self._initial_request = request
        self._last_request = request

        self._incoming = False
        self._pending_incoming_requests = set()
        self._pending_outgoing_requests = set()
        self._local_offer = None
        self._pending_local_offer = False
        self._pending_remote_offer = False
        self._pending_accept = False

        self._remote_target = None
        self._route_set = []

        self.__state = None
        self._early = True

        if mode is SIPMode.SERVER:
            self._build_UAS_dialog(request, response)
        elif mode is SIPMode.CLIENT:
            self._build_UAC_dialog(request, response)

    # Public API -------------------------------------------------------------

    def ring(self):
        # 13.3.1.1 Progress (Processing of the INVITE)
        if self._state != "INVITED":
            return
        self.on_ringing_timeout()

    def accept(self):
        """Accept last request"""
        if self._state not in ("INVITED", "REINVITED"):
            return
        if not self._local_offer or self._pending_remote_offer:
            self._pending_accept = True
            return
        self._pending_accept = False
        self._early = False
        self.stop_timeout("ringing")
        self.start_timeout("ack", int(64 * T1))
        self.on_accept_timeout()

    def reject(self, status):
        """Reject last request"""
        if self._state not in ("INVITED", "REINVITED"):
            return
        self._state = "CONFIRMED"
        self._early = False
        self._pending_accept = False
        self.stop_timeout("ringing")
        self.answer(self._last_request, status)

        # when rejecting the initial request, the dialog is ended
        if self._initial_request == self._last_request:
            self._state = "ENDED"

    def ack(self, response):
        """Acknowledge response"""
        if self._state not in ("INVITING", "REINVITING"):
            return
        self._state = "CONFIRMED"
        request = self._create_ack_request(response)
        self._core.send(request, use_transaction=False,
                errback=(self._handle_ack_error,))

    def reinvite(self):
        if self._state == "ENDED":
            return
        if self._state != "CONFIRMED":
            self._pending_local_offer = True
            return
        logger.info("Send re-invite to %s", self._remote_uri)
        self._state = "REINVITING"
        self._pending_local_offer = None
        request = self._create_reinvite_request(self._local_offer)
        self.send_request(request)

    def end(self):
        if self._state == "ENDED":
            return
        if self._state == "INVITED":
            self.reject(603)
        elif self._state == "INVITING":
            self.cancel()
        else:
            bye = self._create_bye_request()
            self.send_request(bye)
        self._state = "ENDED"

    def reset(self):
        self._pending_incoming_requests = set()
        self._pending_local_offer = False
        self._pending_remote_offer = False
        self._pending_accept = False

    def dispose(self):
        if self._pending_outgoing_requests:
            logger.info("Waiting for %i outgoing request(s) before disposing" %
                    len(self._pending_outgoing_requests))
            self.start_timeout("dispose", 15)
            return
        self.stop_all_timeout()
        self._state = "DISPOSED"

    def force_dispose(self):
        self._pending_outgoing_requests = set()
        self.dispose()

    # States Handling --------------------------------------------------------

    @rw_property
    def _state():
        def fget(self):
            return self.__state
        def fset(self, value):
            if value == self.__state:
                return
            old_state = self.__state
            self.__state = value
            self._on_state_changed(old_state)
        return locals()

    def _on_state_changed(self, old_state):
        if self._state == "CONFIRMED":
            self.stop_timeout("accept")
            self.stop_timeout("ack")
            if self._pending_local_offer and not self._incoming:
                self.reinvite()
        elif self._state == "ENDED":
            for request in self._pending_incoming_requests:
                logger.info("Respond to pending incoming %s request" % request.code)
                self._core.answer(request, 487)
            self.reset()
            self.emit("ended")
            self.dispose()
        elif self._state == "DISPOSED":
            self.emit("disposed")

    # Offer/Answer Session Negotiation----------------------------------------

    def update_local_offer(self, offer):
        if self._local_offer == offer:
            return
        self._local_offer = offer
        if self._pending_accept:
            self.accept()
        elif not self._incoming:
            self.reinvite()

    def accept_remote_offer(self):
        if not self._pending_remote_offer:
            logger.warning("No pending remote session offer to accept")
            return True
        self._pending_remote_offer = False
        if self._state == "REINVITED":
            self.accept()
        return True

    def reject_remote_offer(self):
        if not self._pending_remote_offer:
            logger.warning("No pending remote session offer to reject")
            return False
        self._pending_remote_offer = False
        if self._state == "INVITED":
            self.reject(488)
        elif self._state == "INVITING":
            self.end()
        elif self._state == "REINVITED":
            self.reject(403)
        else:
            self.end()
        return True

    def _handle_offer(self, message, initial):
        if not message.body:
            logger.info("Message doesn't contain a media session offer")
            return True
        try:
            offer = SDPMessage(body=message.body)
            self._pending_remote_offer = True
            self.emit("offer-received", offer, initial)
        except Exception, err:
            logger.error("Malformed body in media session offer")
            logger.exception(err)
            return False
        return True

    # Creation of Dialogs ----------------------------------------------------

    def _build_UAS_dialog(self, request, response):
        # 12.1.1 UAS behavior (Creation of Dialog)
        if self._early:
            self._pending_incoming_requests.add(request)
        if response.record_route:
            self._route_set = response.record_route.route_set
        self._incoming = True
        self._local_cseq = None
        self._remote_cseq = request.cseq.number
        self._call_id = request.call_id
        self._local_tag = response.to.tag
        self._remote_tag = request.From.tag
        self._local_uri = request.to.uri
        self._remote_uri = request.From.uri

    def _build_UAC_dialog(self, request, response):
        # 12.1.2 UAC behavior (Creation of Dialog)
        self._state = "INVITING"
        self._incoming = False
        self._pending_outgoing_requests.add(request)
        if response.record_route:
            self._route_set = response.record_route.route_set.reverse()
        if response.contact:
            self._remote_target = response.contact.uri
        self._local_cseq = request.cseq.number
        self._remote_cseq = None
        self._call_id = response.call_id
        self._local_tag = response.From.tag
        self._remote_tag = response.to.tag
        self._local_uri = response.From.uri
        self._remote_uri = response.to.uri

    def _create_request(self, code, cseq=None):
        # 12.2.1 UAC Behavior (Requests within a Dialog)
        route = self._route_set
        if not route:
            uri = self._remote_target
        elif ';lr' in route[0]:
            uri = self._remote_target
        else:
            uri = route.pop(0)
            route.append(self._remote_target)

        if not self._local_cseq:
            self._local_cseq = 1 # FIXME 8.1.1.5
        if not cseq:
            self._local_cseq += 1
            cseq = self._local_cseq

        request = SIPRequest(code, self._remote_target)
        if route:
            request.add_header("Route", SIPRoute(route))
        request.add_header("To", SIPContact(None, self._remote_uri, self._remote_tag))
        request.add_header("From", SIPContact(None, self._local_uri, self._local_tag))
        request.add_header("Call-ID", self._call_id)
        request.add_header("CSeq", SIPCSeq(cseq, code))
        return request

    # Messages Handling ------------------------------------------------------

    def send_request(self, request):
        self._pending_outgoing_requests.add(request)
        self._core.send(request)

    def answer(self, request, status, extra_headers={}, content=None):
        if self._state == "ENDED":
            return
        if request in self._pending_incoming_requests and status >= 200:
            self._pending_incoming_requests.remove(request)
        return self._core.answer(request, status, tag=self._local_tag,
                extra_headers=extra_headers, content=content)

    def handle_response(self, response):
        # 12.2.1 UAC Behavior (Requests within a Dialog)
        request = response.request

        # Might happen if transaction was already completed (forked)
        if request is None:
            for outgoing_request in self._pending_outgoing_requests:
                if response.match_header("CSeq", outgoing_request):
                    request = outgoing_request
                    break

        # Check if it's the response we were waiting for before disposing
        if request in self._pending_outgoing_requests and response.status >= 200:
            self._pending_outgoing_requests.remove(request)
        if self._state == "ENDED" and not self._pending_outgoing_requests:
            self.dispose()
            return False

        if response.status in (408, 481) and not self._early:
            self.end()
            return False

        # Target refresh
        if response.code == "INVITE" and response.contact:
            self._remote_target = response.contact.uri

        # Method specific handler
        handler = getattr(self, "_handle_%s_response" % response.code.lower(), None)
        if handler is not None:
            return handler(response)
        return True

    def handle_request(self, request):
        # 12.2.2 UAS Behavior (Requests within a Dialog)
        if self._state == "ENDED":
            return

        self._last_request = request
        self._pending_incoming_requests.add(request)
        if not self._remote_cseq:
            self._remote_cseq = request.cseq.number
        elif self._remote_cseq > request.cseq.number: # Out of order
            logger.warning("CSeq is out of order (%i > %i)" %
                    (self._remote_cseq, request.cseq.number))
            self.answer(request, 500)
            return False

        # Target refresh
        if request.code in ("INVITE", "UPDATE") and request.contact:
            self._remote_target = request.contact.uri

        # Method specific handler
        handler = getattr(self, "_handle_%s_request" % request.code.lower(), None)
        if handler is not None:
            return handler(request)
        return True

    # INVITE Method ----------------------------------------------------------

    def _handle_invite_response(self, response):
        # 13.2.2 Processing INVITE Responses (UAC Processing)
        if not self._early:
            return self._handle_reinvite_response(response)

        if response.status == 180:
            self.emit("ringing")
            return True

        if response.status >= 200:
            self._early = False

        # 13.2.2.3 4xx, 5xx and 6xx Responses
        if response.status >= 300:
            self.emit("rejected", response)
            self._state = "ENDED"
            return False

        # 13.2.2.4 2xx Responses
        if response.status/100 == 2:
            success = self._handle_offer(response, False)
            self.ack(response)
            if success:
                logger.info("Call dialog is confirmed")
                self.emit("accepted", response)
                return True
            else:
                self.end()
                return False

    def _handle_invite_request(self, request):
        # 13.3.1 Processing of the INVITE (UAS Processing)
        if self._state is not None:
            return self._handle_reinvite_request(request)
        self._state = "INVITED"
        if not self._handle_offer(request, True):
            self.answer(request, 488)
            self._state = "ENDED"
            return False
        return True

    # re-INVITE Method -------------------------------------------------------

    def _create_reinvite_request(self, offer):
        # 14.1 UAC Behavior (Modifying an Existing Session)
        request = self._create_request("INVITE")
        request.add_header("Contact", SIPContact(None, self._local_uri, self._local_tag))
        request.set_content(offer)
        return request

    def _handle_reinvite_response(self, response):
        # 14.1 UAC Behavior (Modifying an Existing Session)
        if response.status/100 == 2:
            self._handle_offer(response, False)
            self.ack(response)
        #FIXME return

    def _handle_reinvite_request(self, request):
        # 14.2 UAS Behavior (Modifying an Existing Session)
        self.answer(request, 100)
        if self._state in ("INVITED", "REINVITED"):
            logger.warning("Already invited, can't handle incoming INVITE")
            self.answer(request, 500)
            return False
        elif self._state in ("INVITING", "REINVITING"):
            logger.warning("Already inviting, can't handle incoming INVITE")
            self.answer(request, 491)
            return False
        self._state = "REINVITED"
        if not self._handle_offer(request, False):
            self.answer(request, 488)
            return False
        return True

    # ACK Method -------------------------------------------------------------

    def _create_ack_request(self, response):
        request = self._create_request("ACK", cseq=response.cseq.number)
        return request

    def _handle_ack_request(self, request):
        self._pending_incoming_requests.remove(request) # No need to answer
        self._state = "CONFIRMED"

    def _handle_ack_error(self, error):
        logger.error("Received Transport error while sending ACK")
        self.force_dispose()

    # UPDATE Method ----------------------------------------------------------

    def _handle_update_request(self, request):
        self.answer(request, 200)

    # CANCEL Method ----------------------------------------------------------

    def cancel(self):
        if not self._early:
            return
        request = self._core.cancel(self._initial_request)
        self._pending_outgoing_requests.add(request)
        self._state = "ENDED"

    def _handle_cancel_request(self, request):
        self._pending_incoming_requests.remove(request) # UA core will respond
        self._state = "ENDED"

    def _handle_cancel_response(self, response):
        self.dispose()

    # BYE Method -------------------------------------------------------------

    def _create_bye_request(self):
        request = self._create_request("BYE")
        return request

    def _handle_bye_request(self, request):
        self._pending_incoming_requests.remove(request) # UA core will respond
        self._state = "ENDED"

    def _handle_bye_response(self, response):
        self.dispose()

    # Timeout Callbacks ------------------------------------------------------

    def on_ringing_timeout(self):
        self.answer(self._initial_request, 180)
        self.start_timeout("ringing", 60)

    def on_accept_timeout(self, time=T1):
        if self._state not in ("INVITED", "REINVITED"):
            return
        header = ("Contact", SIPContact(None, self._local_uri, self._local_tag))
        self.answer(self._last_request, 200, content=self._local_offer,
                extra_headers=[header])

        # [...] an interval that starts at T1 seconds and doubles for each
        # retransmission until it reaches T2 seconds (Section 13.3.1.4)
        next_time = int(min(time * 2, T2))
        self.start_timeout("accept", time, next_time)

    def on_ack_timeout(self):
        self._state = "CONFIRMED"
        self.end()

    def on_dispose_timeout(self):
        self.force_dispose()
