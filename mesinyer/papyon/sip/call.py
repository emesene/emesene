# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2009 Collabora Ltd.
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

from papyon.event import EventsDispatcher
from papyon.media import MediaCall, MediaSessionType
from papyon.profile import Presence
from papyon.service.SingleSignOn import *
from papyon.sip.constants import *
from papyon.sip.message import SIPRequest, SIPResponse
from papyon.sip.sdp import SDPMessage
from papyon.sip.turn import TURNClient

import base64
import gobject
import logging
import re
import uuid

__all__ = ['SIPCall', 'SIPRegistration']

logger = logging.getLogger('papyon.sip.call')


class SIPBaseCall(gobject.GObject):
    """Base class representing a transaction between two entities. A transaction
       between an user and a registrar is a SIPRegistration and a transaction
       between two SIP end points is a SIPCall. This class mainly contains
       utility functions to build and parse request/responses."""

    def __init__(self, connection, client, id=None):
        gobject.GObject.__init__(self)
        self._connection = connection
        self._client = client
        self._ip = "127.0.0.1"
        self._port = 50390
        self._transport_protocol = connection.transport.protocol
        self._account = client.profile.account
        self._id = id
        self._cseq = 0
        self._remote = None
        self._route = None
        self._uri = None
        self._timeout_sources = {}

    @property
    def id(self):
        if not self._id:
            self._id = uuid.uuid4().get_hex()
        return self._id

    def get_cseq(self, incr=False):
        if incr:
            self._cseq += 1
        return self._cseq

    def get_epid(self):
        if not hasattr(self, '_epid'):
            self._epid = uuid.uuid4().get_hex()[:10]
        return self._epid

    def get_mepid(self):
        if self._connection.tunneled:
            mepid = self._connection._client.machine_guid
            mepid = filter(lambda c: c not in "{-}", mepid).upper()
            return ";mepid=%s" % mepid
        else:
            return ""

    def get_tag(self):
        if not hasattr(self, '_tag'):
            self._tag = uuid.uuid4().get_hex()
        return self._tag

    def get_sip_instance(self):
        return SIP_INSTANCE

    def send(self, message, registration=False):
        message.call = self
        self._connection.send(message, registration)

    def find_contact(self, email):
        contacts = self._client.address_book.contacts.search_by_account(email)
        if not contacts:
            return None
        return contacts[0]

    def parse_contact(self, message):
        if type(message) is SIPRequest:
            header = "From"
        elif type(message) is SIPResponse:
            header = "To"
        else:
            return None
        email = self.parse_email(message, header)
        return self.find_contact(email)

    def parse_email(self, message, name):
        header = message.get_header(name)
        if header is not None:
            return re.search("<sip:([^;>]*)(;|>)", header).group(1)

    def parse_uri(self, message, name):
        header = message.get_header(name)
        if header is not None:
            return re.search("<([^>]*)>", header).group(1)

    def parse_sip(self, message, name):
        header = message.get_header(name)
        if header is not None:
            return re.search("<sip:[^>]*>", header).group(0)

    def build_from_header(self, name="0"):
        return '"%s" <sip:%s%s>;tag=%s;epid=%s' % \
            (name, self._account, self.get_mepid(), self.get_tag(),
             self.get_epid())

    def build_request(self, code, uri, to, name="0", incr=False):
        request = SIPRequest(code, uri)
        request.add_header("Via", "SIP/2.0/%s %s:%s" %
            (self._transport_protocol, self._ip, self._port))
        request.add_header("Max-Forwards", 70)
        request.add_header("Call-ID", self.id)
        request.add_header("CSeq", "%i %s" % (self.get_cseq(incr), code))
        request.add_header("To", to)
        request.add_header("From", self.build_from_header(name))
        request.add_header("User-Agent", USER_AGENT)
        return request

    def build_response(self, request, status, reason=None):
        response = SIPResponse(status, reason)
        response.clone_headers("From", request)
        response.add_header("To", self.build_from_header())
        response.clone_headers("CSeq", request)
        response.clone_headers("Record-Route", request)
        response.clone_headers("Via", request)
        response.add_header("Call-ID", self.id)
        response.add_header("Max-Forwards", 70)
        response.add_header("User-Agent", USER_AGENT)
        return response

    def on_message_received(self, msg):
        route = self.parse_sip(msg, "Record-Route")
        if route is not None:
            self._route = route
        uri = self.parse_uri(msg, "Contact")
        if uri is not None:
            self._uri = uri

        if type(msg) is SIPResponse:
            self._remote = msg.get_header("To")
            handler_name = "on_%s_response" % msg.code.lower()
        elif type(msg) is SIPRequest:
            self._remote = msg.get_header("From")
            handler_name = "on_%s_received" % msg.code.lower()
        handler = getattr(self, handler_name, None)
        if handler is not None:
            handler(msg)
        else:
            logger.warning("Unhandled %s message" % msg.code)

    @property
    def timeouts(self):
        return self._timeout_sources.keys()

    def start_timeout(self, name, time):
        self.stop_timeout(name)
        source = gobject.timeout_add(time * 1000, self.on_timeout, name)
        self._timeout_sources[name] = source

    def stop_timeout(self, name):
        source = self._timeout_sources.get(name, None)
        if source is not None:
            gobject.source_remove(source)
            del self._timeout_sources[name]

    def stop_all_timeout(self):
        for (name, source) in self._timeout_sources.items():
            if source is not None:
                gobject.source_remove(source)
        self._timeout_sources.clear()

    def on_timeout(self, name):
        self.stop_timeout(name)
        handler = getattr(self, "on_%s_timeout" % name, None)
        if handler is not None:
            handler()


class SIPCall(SIPBaseCall, MediaCall, EventsDispatcher):
    """Represent a SIP dialog between two end points. A call must be initiated
       by sending or receiving an INVITE request. It is disposed when
       receiving or by sending a CANCEL or BYE request.

       For a more complete description of the transactions, see the SIP
       standard memo (RFC 3261) : http://tools.ietf.org/html/rfc3261"""

    def __init__(self, connection, client, peer=None, invite=None, id=None):
        session_type = connection.tunneled and MediaSessionType.TUNNELED_SIP \
                or MediaSessionType.SIP
        SIPBaseCall.__init__(self, connection, client, id)
        MediaCall.__init__(self, session_type)
        EventsDispatcher.__init__(self)

        self._incoming = (id is not None)
        self._accepted = False
        self._rejected = False
        self._answer_sent = False
        self._early = False
        self._state = None
        self._relay_requested = False

        if peer is None and invite is not None:
            peer = self.parse_contact(invite)
        self._peer = peer
        self._invite = invite

    @property
    def peer(self):
        return self._peer

    @property
    def conversation_id(self):
        if self.media_session.has_video:
            return 1
        else:
            return 0

    @property
    def answered(self):
        return (self._accepted or self._rejected) and self._answer_sent

    @property
    def incoming(self):
        return self._incoming

    def build_invite_contact(self):
        if self._connection.tunneled:
            m = "<sip:%s%s>;proxy=replace;+sip.instance=\"<urn:uuid:%s>\"" % (
                self._account, self.get_mepid(), self.get_sip_instance())
        else:
            m = "<sip:%s:%i;maddr=%s;transport=%s>;proxy=replace" % (
                self._account, self._port, self._ip, self._transport_protocol)
        return m

    def build_invite_request(self, uri, to):
        message = SDPMessage(session=self.media_session)
        request = self.build_request("INVITE", uri, to, incr=True)
        request.add_header("Ms-Conversation-ID", "f=%s" % self.conversation_id)
        request.add_header("Contact", self.build_invite_contact())
        request.set_content(str(message), "application/sdp")
        return request

    def invite(self):
        if not self.media_session.prepared:
            return
        logger.info("Send call invitation to %s", self._peer.account)
        self._state = "CALLING"
        self._early = False
        self._uri = "sip:%s" % self._peer.account
        self._remote = "<%s>" % self._uri
        self._invite = self.build_invite_request(self._uri, self._remote)
        self.start_timeout("invite", 30)
        self.send(self._invite)

    def reinvite(self):
        if self._incoming or not self.media_session.ready:
            return
        self._state = "REINVITING"
        self._invite = self.build_invite_request(self._uri, self._remote)
        self._invite.add_header("Route", self._route)
        self._invite.add_header("Supported", "ms-dialog-route-set-update")
        self.start_timeout("invite", 10)
        self.send(self._invite)

    def answer(self, status):
        response = self.build_response(self._invite, status)
        if status == 200:
            message = SDPMessage(session=self.media_session)
            response.add_header("Contact", self.build_invite_contact())
            response.set_content(str(message), "application/sdp")
        self.send(response)

    def ring(self):
        if self._invite is None :
            return
        self.start_timeout("response", 50)
        self.answer(180)
        self._dispatch("on_call_incoming")

    def accept(self):
        if self.answered:
            return
        self._accepted = True
        if not self.media_session.prepared:
            return
        self.stop_timeout("response")
        self.start_timeout("ack", 5)
        self._answer_sent = True
        self.answer(200)

    def reject(self, status=603):
        if self.answered:
            return
        self._state = "DISCONNECTING"
        self.stop_timeout("response")
        self.start_timeout("ack", 5)
        self._rejected = True
        self._answer_sent = True
        self.answer(status)

    def reaccept(self):
        if not self.media_session.ready:
            return
        self._state = "CONFIRMED"
        self.answer(200)

    def send_ack(self, response):
        request = self.build_request("ACK", self._uri, self._remote)
        request.add_header("Route", self._route)
        self.send(request)

    def end(self):
        if self._state in ("INCOMING"):
            self.reject()
        elif self._state in ("CALLING", "REINVITING"):
            self.cancel()
        elif self._peer.presence == Presence.OFFLINE:
            self.force_dispose()
        else:
            self.send_bye()

    def cancel(self):
        if self._state not in ("CALLING", "REINVITING"):
            return

        if self._state == "CALLING":
            if self._invite is None:
                self.force_dispose()
                return
            elif not self._invite.sent:
                self._invite.cancelled = True
                self.force_dispose()
                return

        self._state = "DISCONNECTING"
        request = self.build_request("CANCEL", self._invite.uri, None)
        request.clone_headers("To", self._invite)
        request.clone_headers("Route", self._invite)
        self.start_timeout("cancel", 5)
        self.send(request)

    def send_bye(self):
        if self._state == "DISCONNECTING":
            return

        self._state = "DISCONNECTING"
        request = self.build_request("BYE", self._uri, self._remote, incr=True)
        request.add_header("Route", self._route)
        self.start_timeout("bye", 5)
        self.send(request)

    def force_dispose(self):
        self._state = "DISCONNECTING"
        self.stop_all_timeout()
        self.dispose()

    def dispose(self):
        if self.timeouts:
            return # we have to wait some responses
        MediaCall.dispose(self)
        self._state = "DISCONNECTED"
        self._dispatch("on_call_ended")
        self._connection.remove_call(self)

    def on_invite_received(self, invite):
        self._invite = invite
        self.answer(100)

        try:
            message = SDPMessage(body=invite.body)
        except:
            logger.error("Malformed body in incoming call invitation")
            self.reject(488)
            return

        if self._state is None:
            self._state = "INCOMING"
            self.start_timeout("response", 50)
            self.media_session.process_remote_message(message, True)
        elif self._state == "CONFIRMED":
            self._state = "REINVITED"
            self.media_session.process_remote_message(message, False)
            self.reaccept()
        else:
            self.answer(488) # not acceptable here

    def on_ack_received(self, ack):
        self.stop_timeout("ack")
        if self._rejected:
            self.dispose()
        else:
            self._state = "CONFIRMED"

    def on_cancel_received(self, cancel):
        if self.incoming and not self.answered:
            self.reject(487)
        response = self.build_response(cancel, 200)
        self.send(response)
        self.dispose()

    def on_bye_received(self, bye):
        response = self.build_response(bye, 200)
        self.send(response)
        self.dispose()

    def on_invite_response(self, response):
        if self._state == "REINVITING":
            return self.on_reinvite_response(response)
        elif self._incoming:
            return

        self._remote = response.get_header("To")
        if response.status >= 200:
            self.send_ack(response)
            self.stop_timeout("invite")

        if response.status is 100:
            self._early = True
        elif response.status is 180:
            self._dispatch("on_call_ringing")
        elif response.status is 200:
            self._state = "CONFIRMED"
            try:
                message = SDPMessage(body=response.body)
                self.media_session.process_remote_message(message)
            except Exception, err:
                logger.error("Malformed body in invite response")
                logger.exception(err)
                self.send_bye()
            else:
                logger.info("Call invitation has been accepted")
                self._dispatch("on_call_accepted")
                self.reinvite()
        elif response.status in (408, 480, 486, 487, 504, 603):
            logger.info("Call invitation has been rejected (%i)", response.status)
            self._dispatch("on_call_rejected", response)
            self.dispose()
        else:
            self._dispatch("on_call_error", response)
            self.send_bye()

    def on_reinvite_response(self, response):
        if response.status >= 200:
            self.send_ack(response)
            self.stop_timeout("invite")

        if response.status in (100, 180):
            pass
        elif response.status in (200, 488):
            self._state = "CONFIRMED"
        else:
            self.send_bye()

    def on_cancel_response(self, response):
        self.stop_timeout("cancel")
        self.dispose()

    def on_bye_response(self, response):
        self.stop_timeout("bye")
        self.dispose()

    def on_media_session_prepared(self, session):
        if self._state is None:
            self.invite()
        elif self._state == "INCOMING" and self._accepted:
            self.accept()

    def on_media_session_ready(self, session):
        if self._state == "REINVITED":
            self.reaccept()
        elif self._state == "CONFIRMED":
            self.reinvite()

    def on_invite_timeout(self):
        self.cancel()

    def on_response_timeout(self):
        self.reject(408)
        self._dispatch("on_call_missed")

    def on_ack_timeout(self):
        self.dispose()

    def on_cancel_timeout(self):
        self.dispose()

    def on_bye_timeout(self):
        self.dispose()

    def on_end_timeout(self):
        self.dispose()

    def request_turn_relays(self, streams_count):
        # FIXME Request TURN relays before to send an invite or to accept one
        turn_client = TURNClient(self._client._sso, self._account)
        turn_client.connect("done", self.on_turn_relays_discovered)
        turn_client.request_shared_secret(None, None, streams_count * 2)

    def on_turn_relays_discovered(self, turn_client, relays):
        logger.debug("Discovered %i TURN relays" % len(relays))


class SIPRegistration(SIPBaseCall):

    __gsignals__ = {
        'registered': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ([])),
        'unregistered': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ([])),
        'failed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ([]))
    }

    def __init__(self, connection, client):
        SIPBaseCall.__init__(self, connection, client)
        self._state = "NEW"
        self._sso = client._sso
        self._src = None
        self._request = None
        self._pending_unregister = False
        self._tokens = {}

    @property
    def registered(self):
        return (self._state == "REGISTERED")

    def build_register_request(self, timeout, auth):
        uri = "sip:%s" % self._account.split('@')[1]
        to =  "<sip:%s>" % self._account
        request = self.build_request("REGISTER", uri, to, incr=1)
        request.add_header("ms-keep-alive", "UAC;hop-hop=yes")
        request.add_header("Contact", "<sip:%s:%s;transport=%s>;proxy=replace" %
            (self._ip, self._port, self._transport_protocol))
        request.add_header("Event", "registration")
        request.add_header("Expires", timeout)
        request.add_header("Authorization", "Basic %s" % auth)
        return request

    def register(self):
        if self._state in ("REGISTERING", "REGISTERED", "CANCELLED"):
            return
        self._state = "REGISTERING"
        self._do_register(None, None)

    @RequireSecurityTokens(LiveService.MESSENGER_SECURE)
    def _do_register(self, callback, errback):
        # Check if state changed while requesting security token
        if self._state != "REGISTERING":
            return
        auth = "msmsgs:RPS_%s" % self._tokens[LiveService.MESSENGER_SECURE]
        auth = base64.b64encode(auth).replace("\n", "")
        self._request = self.build_register_request(900, auth)
        self.send(self._request, True)

    def unregister(self):
        if self._state in ("NEW", "UNREGISTERING", "UNREGISTERED", "CANCELLED"):
            return
        elif self._state == "REGISTERING":
            if self._request is None:
                self._state = "CANCELLED"
                self.emit("unregistered")
            else:
                self._pending_unregister = True
            return

        self._state = "UNREGISTERING"
        self._pending_unregister = False
        if self._src is not None:
            gobject.source_remove(self._src)
        self._src = None
        self._do_unregister(None, None)

    @RequireSecurityTokens(LiveService.MESSENGER_SECURE)
    def _do_unregister(self, callback, errback):
        auth = "%s:%s" % (self._account, self._tokens[LiveService.MESSENGER_SECURE])
        auth = base64.encodestring(auth).replace("\n", "")
        request = self.build_register_request(0, auth)
        self.send(request, True)

    def on_expire(self):
        self.register()
        return False

    def on_register_response(self, response):
        if self._state == "UNREGISTERING":
            self._state = "UNREGISTERED"
            self.emit("unregistered")
        elif self._state != "REGISTERING":
            return # strange !?
        elif response.status is 200:
            self._state = "REGISTERED"
            self.emit("registered")
            timeout = int(response.get_header("Expires", 30))
            self._src = gobject.timeout_add(timeout * 1000, self.on_expire)
            if self._pending_unregister:
                self.unregister()
        else:
            self._state = "UNREGISTERED"
            self.emit("failed")
