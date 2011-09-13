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

from papyon.sip.extensions import init_extensions
from papyon.sip.constants import T1, SIPMode, SIPTransactionError, USER_AGENT
from papyon.sip.dialog import SIPDialog
from papyon.sip.message import SIPRequest, SIPResponse, SIPContact, SIPCSeq, SIPVia
from papyon.sip.transaction import SIPClientTransaction, SIPTransactionLayer
from papyon.sip.transport import SIPTunneledTransport
from papyon.util.decorator import rw_property
from papyon.util.timer import Timer

import gobject
import logging
import uuid

__all__ = ['SIPCore']

logger = logging.getLogger('papyon.sip.core')

class SIPCore(gobject.GObject, Timer):
    """ The set of processing functions required at a UAS and a UAC that
        resides above the transaction and transport layers.
        
        The core keeps track of the ongoing dialogs with peers. Apart from
        that, the core is stateless and there is only one instance per UA."""

    __gsignals__ = {
        'register-answered': (
            gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            (object,)),
        'invite-received': (
            gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            (object,)),
        'invite-answered': (
            gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            (object,)),
        'cancel-received': (
            gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            (object,))
    }

    @property
    def self_uri(self):
        return "sip:" + self._client.profile.account

    def __init__(self, client):
        gobject.GObject.__init__(self)
        Timer.__init__(self)

        self._client = client
        self._transport = SIPTunneledTransport(client._protocol)
        self._transaction_layer = SIPTransactionLayer(self._transport)
        self._transaction_layer.connect("request-received",
                self._on_request_received)
        self._transaction_layer.connect("response-received",
                self._on_response_received)
        self._transaction_layer.connect("error",
                self._on_transaction_layer_error)

        self._supported_methods = set(["INVITE", "ACK", "CANCEL", "BYE",
            "OPTIONS", "INFO", "UPDATE", "REFER", "NOTIFY", "BENOTIFY"])
        self._supported_extensions = set(init_extensions(client, self))
        self._supported_content_types = set(["application/sdp"])

        self._dialogs = {} # (call-id, local-tag, remote-tag) => dialog
        self._dialog_handles = {} # dialog => handle id

    def send(self, message, use_transaction=True, callback=None, errback=None):
        """Apply extensions and send message to transaction layer."""
        #self._add_supported_methods(message)
        self._apply_extensions(message)
        if not use_transaction:
            return self._transport.send(message, callback, errback)
        return self._transaction_layer.send(message)

    def answer(self, request, status, tag=None, extra_headers={}, content=None):
        """Create response with given status and send to transaction layer."""
        response = self.create_response(request, status, tag=tag)
        for (name, value) in extra_headers:
            response.add_header(name, value)
        if content is not None:
            response.set_content(content)
        return self.send(response)

    # Public API -------------------------------------------------------------

    def register(self, call_id, cseq, timeout, auth):
        request = self._create_register_request(call_id, cseq, timeout, auth)
        self.send(request)
        return request

    def invite(self, call_id, uri, offer):
        request = self._create_invite_request(call_id, uri, offer)
        self.request_UAC_dialog(request)
        return request

    def cancel(self, canceled_request):
        request = self._create_cancel_request(canceled_request)
        self.start_timeout("cancel", int(64 * T1), canceled_request)
        self.send(request)
        return request

    # Dialog Management ------------------------------------------------------

    def establish_UAS_dialog(self, request, status):
        # 12.1.1 UAS behavior (Creation of a Dialog)
        self_tag = self._generate_tag()
        response = self.create_response(request, status, tag=self_tag)
        response.clone_headers("Record-Route", request)
        #response.add_header("Contact", SIPContact(None, self.self_uri, None))
        request.transaction.send(response)
        return self._create_dialog(request, response, SIPMode.SERVER)

    def request_UAC_dialog(self, request):
        # 12.1.2 UAC behavior (Creation of a Dialog)
        self_tag = request.From.tag
        request.add_header("Contact", SIPContact(None, self.self_uri, self_tag))
        self.send(request)

    def establish_UAC_dialog(self, response):
        # 12.1.2 UAC behavior (Creation of a Dialog)
        return self._create_dialog(response.request, response, SIPMode.CLIENT)

    def _create_dialog(self, request, response, mode):
        dialog = SIPDialog(self, request, response, mode)
        key = (dialog.call_id, dialog.local_tag, dialog.remote_tag)
        logger.info("Create dialog (%s, %s, %s)" % key)
        handle = dialog.connect("disposed", self._on_dialog_disposed)
        self._dialogs[key] = dialog
        self._dialog_handles[dialog] = handle
        return dialog

    def _find_dialog(self, message):
        call_id = message.call_id
        if type(message) is SIPRequest:
            local_tag = message.To.tag
            remote_tag = message.From.tag
        else:
            local_tag = message.From.tag
            remote_tag = message.To.tag

        return self._dialogs.get((call_id, local_tag, remote_tag), None)

    def _forward_to_dialog(self, message):
        dialog = self._find_dialog(message)
        if dialog is not None:
            if type(message) is SIPRequest:
                dialog.handle_request(message)
            elif type(message) is SIPResponse:
                dialog.handle_response(message)

    def _on_dialog_disposed(self, dialog):
        key = (dialog.call_id, dialog.local_tag, dialog.remote_tag)
        logger.info("Dispose dialog (%s, %s, %s)" % key)
        del self._dialogs[key]
        handle = self._dialog_handles.pop(dialog)
        dialog.disconnect(handle)

    # Generating Messages -----------------------------------------------------

    def create_request(self, code, to_uri, uri=None, tag=None, call_id=None,
            cseq=None):
        """ Create a request outside of a dialog """
        # 8.1.1 Generating the Request (UAC Behavior)

        if uri is None:
            uri = to_uri
        if tag is None:
            tag = self._generate_tag()
        if call_id is None:
            call_id = self._generate_call_id()
        if cseq is None:
            cseq = self._generate_cseq()

        request = SIPRequest(code, uri)
        request.add_header("To", SIPContact("0", to_uri))
        request.add_header("From", SIPContact("0", self.self_uri, tag))
        request.add_header("Call-Id", call_id)
        request.add_header("CSeq", SIPCSeq(cseq, code))
        return request

    def create_response(self, request, status, tag=None):
        """ Create a response outside of a dialog """
        # 8.2.6 Generating the Response (UAS Behavior)
        response = SIPResponse(status)
        response.request = request

        # 8.2.6.1 Sending a Provisional Response
        if status/100 == 1 and request.code != "INVITE":
            return
        if status == 100:
            response.clone_headers("Timestamp", request)

        # 8.2.6.2 Headers and Tags
        response.clone_headers("To", request)
        response.clone_headers("From", request)
        response.clone_headers("Call-ID", request)
        response.clone_headers("CSeq", request)
        response.clone_headers("Via", request)

        # Add To tag if missing
        if not response.to.tag:
            if tag is None:
                tag = self._generate_tag()
            response.to.tag = tag

        return response

    # Extensions Management --------------------------------------------------

    def _apply_extensions(self, message):
        for extension in self._supported_extensions:
            extension.extend(message)

    def _add_supported_methods(self, message):
        methods = ", ".join(self._supported_methods)
        message.add_header("Allow", methods)

    # Messages Handling ------------------------------------------------------

    def _on_response_received(self, transaction_layer, response):
        # 8.1.3 Processing Responses (UAC Behavior)

        if len(response.get_headers("Via", [])) >= 2:
            return # discard message (8.1.3.3)

        if response.status/100 == 3:
            return # 3xx responses are not handled

        if response.status/100 == 4:
            pass # 4xx responses are not handled (Bad Request)

        handler = getattr(self, "_handle_%s_response" % response.code.lower(), None)
        if handler is not None:
            handler(response)
        else:
            self._forward_to_dialog(response)

    def _on_request_received(self, transaction_layer, request):
        # 8.2 UAS Behavior (General User Agent Behavior)
        if not self._inspect_request(request):
            return

        # 8.2.5 Processing the request:
        handler = getattr(self, "_handle_%s_request" % request.code.lower(), None)
        if handler is not None:
            handler(request)
        else:
            self._forward_to_dialog(request)

    def _inspect_request(self, request):
        # 8.2.1 Method Inspection

        # 8.2.2 Header Inspection
        if not request.uri.startswith("sip:"):
            logger.warning("Unsupported URI Scheme: %s" % request.uri)
            self.answer(request, 416)
            return False    # Unsupported URI Scheme
        #if request.uri != self.self_uri:
        #    logger.warning("Request URI is Not Found: %s" % request.uri)
        #    self.answer(request, 404)
        #    return False    # Not Found
        if not request.to.tag and self._transaction_layer.is_merged_request(request):
            logger.warning("Received merged request (Loop Detected)")
            self.answer(request, 482)
            return False    # Loop Detected
        unsupported = request.required_extensions - self._supported_extensions
        if not request.code in ("CANCEL", "ACK") and unsupported:
            headers = {"Unsupported": " ".join(unsupported)}
            logger.warning("Unsupported Extensions: %s" % unsupported)
            self.answer(request, 420, headers)
            return False    # Bad Extension

        # 8.2.3 Content Processing
        if (request.content_type and
           request.content_type not in self._supported_content_types):
            logger.warning("Unsupport Media Type: %s" % request.content_type)
            self.answer(request, 415)
            return False    # Unsupported Media Type

        return True

    # CANCEL Method ----------------------------------------------------------

    def _create_cancel_request(self, original_request):
        # 9.1 Client Behavior (Canceling a request)
        request = SIPRequest("CANCEL", original_request.uri)
        request.clone_headers("Route", original_request)
        request.clone_headers("To", original_request)
        request.clone_headers("From", original_request)
        request.clone_headers("Call-ID", original_request)
        cseq = original_request.cseq.number
        request.add_header("CSeq", SIPCSeq(cseq, "CANCEL"))
        return request

    def _handle_cancel_request(self, request):
        # 9.2 Server Behavior (Canceling a Request)
        transaction = self._transaction_layer.find_canceled_transaction(request)
        if transaction is None:
            logger.warning("Transaction to cancel doesn't exist.")
            return self.answer(request, 481) # Transaction Does Not Exist
        if type(transaction) is SIPClientTransaction:
            logger.warning("Can't remotely cancel client transaction.")
            return self.answer(request, 500) # Server Error
        if transaction.answered:
            logger.info("Call already answered, ignoring CANCEL")
            return

        dialog = self._find_dialog(request)
        if dialog is None:
            self.emit("cancel-received", request)
        else:
            dialog.handle_request(request)
        self.answer(request, 200)

    # REGISTER Method --------------------------------------------------------

    def _create_register_request(self, tag, call_id, cseq, timeout, auth):
        # 10.2 Constructing the REGISTER Request
        uri = "sip:%s" % self.self_uri('@')[1]
        to =  "sip:%s" % self.self_uri
        request = self.create_request("REGISTER", to, uri, tag, call_id, cseq)
        request.add_header("Contact", "<sip:%s:%s;transport=%s>" %
            (self._ip, self._port, self._transport_protocol))
        request.add_header("Event", "registration")
        request.add_header("Expires", timeout)
        request.add_header("Authorization", "Basic %s" % auth)
        return request

    def _handle_register_response(self, response):
        registration = self._registrations.get(call_id, None)
        if registration:
            registration.handle_response(response)

    # OPTIONS Method ---------------------------------------------------------

    def _create_options_request(self, uri):
        # 11.1 Construction of OPTIONS Request
        request = self.create_request("OPTIONS", uri)
        request.add_header("Accept", "application/sdp")
        return request

    def _handle_options_request(self, request):
        self.emit("options-received", request)

    def _handle_options_response(self, response):
        self.emit("options-answered", response)

    # INVITE Method ----------------------------------------------------------

    def _create_invite_request(self, call_id, uri, offer):
        # 13.2.1 Creating the Initial INVITE
        request = self.create_request("INVITE", uri, call_id=call_id)
        request.add_header("User-Agent", USER_AGENT)
        request.set_content(offer)
        return request

    def _handle_invite_response(self, response):
        # 13.2.2 Processing INVITE Responses (UAC Processing)
        dialog = self._find_dialog(response)
        if dialog is None:
            self.emit("invite-answered", response)
        else:
            dialog.handle_response(response)

    def _handle_invite_request(self, request):
        # 13.3.1 Processing of the INVITE (UAS Processing)
        dialog = self._find_dialog(request)
        if dialog is not None:
            dialog.handle_request(request)
        elif request.to.tag:
            logger.warning("Dialog for target refresh (INVITE) doesn't exist.")
            self.answer(request, 481) # Call Leg Does Not Exist
        else:
            self.emit("invite-received", request)

    # BYE Method -------------------------------------------------------------

    def _handle_bye_request(self, request):
        # 15.1.2 UAS Behavior (Terminating a Session with a BYE Request)
        dialog = self._find_dialog(request)
        if dialog is None:
            logger.warning("Dialog to terminate (BYE) doesn't exist.")
            self.answer(request, 481) # Call Leg Does Not Exist
        else:
            dialog.handle_request(request)
            self.answer(request, 200)

    # Timeouts Callbacks -----------------------------------------------------

    def on_cancel_timeout(self, canceled_request):
        transaction = canceled_request.transaction
        if transaction is not None and not transaction.answered:
            logger.info("Canceled request not answered, destroy transaction")
            transaction.destroy()

    # Errors Handling --------------------------------------------------------

    def _on_transaction_layer_error(self, transaction_layer, transaction, error):
        # 8.1.3.1 Transaction Layer Errors
        if error is SIPTransactionError.TIMEOUT: # Treat as 408
            logger.error("Received Timeout error from transaction layer")
            fake_response = self.create_response(transaction.request, 408)
            self._on_response_received(transaction_layer, fake_response)
        elif error is SIPTransactionError.TRANSPORT_ERROR: # Treat as 503
            logger.error("Received Transport error from transaction layer")
            fake_response = self.create_response(transaction.request, 503)
            self._on_response_received(transaction_layer, fake_response)

    # Utils Functions --------------------------------------------------------

    def _generate_tag(self):
        # 19.3 Tags
        return uuid.uuid4().get_hex()

    def _generate_call_id(self):
        # 20.8 Call-ID
        return uuid.uuid4().get_hex()

    def _generate_cseq(self):
        return 1 #FIXME random cseq
