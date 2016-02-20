# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2009-2010 Collabora Ltd.
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
from papyon.media import MediaCall, MediaSessionType, RTCActivity
from papyon.profile import NetworkID, Presence
from papyon.service.SingleSignOn import *
from papyon.sip.constants import *
from papyon.sip.sdp import SDPMessage
from papyon.util.timer import Timer

import gobject
import logging

__all__ = ['SIPCall']

logger = logging.getLogger('papyon.sip.call')

class SIPCall(gobject.GObject, MediaCall, RTCActivity, EventsDispatcher, Timer):

    __gsignals__ = {
        'ended': (
            gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ())
    }

    def __init__(self, client, core, id, peer=None, invite=None):
        gobject.GObject.__init__(self)
        MediaCall.__init__(self, client, MediaSessionType.TUNNELED_SIP)
        RTCActivity.__init__(self, client)
        EventsDispatcher.__init__(self)
        Timer.__init__(self)

        self._core = core
        self._id = id
        self._peer = peer
        self._invite = invite

        self._incoming = (invite is not None)
        self._ringing = False
        self._pending_invite = False
        self._pending_cancel = False

        self._dialogs = []
        self._handles = {}

        if self._incoming:
            self._build_from_invite(invite)


    ### Public API -----------------------------------------------------------

    @property
    def id(self):
        return self._id

    @property
    def peer(self):
        return self._peer

    @property
    def incoming(self):
        return self._incoming

    @property
    def peer_uri(self):
        return "sip:" + self._peer.account

    @property
    def can_answer(self):
        if not self._incoming:
            logger.warning("Can't answer to outgoing call %s" % self._id)
            return False
        if self._dialog is None:
            logger.error("No dialog for the incoming call %s" % self._id)
            return False
        if self._dialog.answered:
            logger.warning("Call %s has already been answered" % self._id)
            return False
        return True

    def invite(self):
        """Send the invitation to the peer. Invite is sent by the UA Core
           because dialogs are created when receiving response."""

        if self._incoming or self._invite:
            return
        if not self.media_session.prepared:
            self._pending_invite = True
            return
        logger.info("Send call invitation to %s" % self._peer.account)
        offer = SDPMessage(session=self.media_session)
        self._pending_invite = False
        self._invite = self._core.invite(self._id, self.peer_uri, offer)

    def ring(self):
        if not self.can_answer:
            return
        if self._ringing:
            return
        self._ringing = True
        self.start_timeout("response", 50)
        self._dialog.ring()
        self._dispatch("on_call_incoming")

    def accept(self):
        if not self.can_answer:
            return
        self.stop_timeout("response")
        self._dialog.accept()
        self._accept_activity()

    def reject(self, status=603):
        if not self.can_answer:
            return
        self.stop_timeout("response")
        self._dialog.reject(status)
        self._decline_activity()

    def end(self):
        if self._peer.presence == Presence.OFFLINE:
            self._dispose()

        if not self._invite:
            self._dispose()
        elif not self._dialogs:
            self._pending_cancel = True
        else:
            for dialog in self._dialogs:
                dialog.end()

    ### Messages Handling (Outside Dialog) -----------------------------------

    def handle_invite_request(self, invite):
        logger.info("Establish new UAS dialog to handle INVITE request")
        dialog = self._core.establish_UAS_dialog(invite, 100)
        self._add_dialog(dialog)
        return dialog.handle_request(invite)

    def handle_invite_response(self, response):
        logger.info("Establish new UAC dialog to handle INVITE response")
        response.request = self._invite
        dialog = self._core.establish_UAC_dialog(response)
        self._add_dialog(dialog)
        return dialog.handle_response(response)

    def handle_cancel_request(self, request):
        logger.info("Cancel all dialogs for call %s" % self._id)
        for dialog in self._dialogs[:]:
            dialog.handle_request(request)
        return True

    ### Private API ----------------------------------------------------------

    @property
    def _dialog(self):
        if len(self._dialogs) == 0:
            return None
        return self._dialogs[0]

    def _build_from_invite(self, invite):
        account = invite.contact.uri.replace("sip:", "")
        #FIXME hack
        if ";mepid=" in account:
            account = account.split(";mepid=")[0]
        self._peer = self._client.address_book.search_or_build_contact(account,
                NetworkID.MSN)

    def _dispose(self):
        logger.info("Call has been disposed")
        MediaCall.dispose(self)
        self._remove_all_dialogs()
        self.stop_all_timeout()
        self.emit("ended")
        self._dispatch("on_call_ended")
        self._dispose_activity()

    ### Dialogs Handling -----------------------------------------------------

    def _add_dialog(self, dialog):
        """Add dialog to call"""
        self._connect_dialog(dialog)
        self._dialogs.append(dialog)

        # We were waiting for a response to cancel...
        if self._pending_cancel:
            self.end()

    def _keep_dialog(self, dialog_to_keep):
        """Remove all dialogs except the one."""
        if dialog_to_keep not in self._dialogs:
            return False
        self._dialogs.remove(dialog_to_keep)
        handles = self._handles.pop(dialog_to_keep)
        self._remove_all_dialogs()
        self._dialogs = [dialog_to_keep]
        self._handles[dialog_to_keep] = handles
        return True

    def _remove_all_dialogs(self):
        """Remove, dispose and disconnect all dialogs."""
        for dialog in self._dialogs:
            self._disconnect_dialog(dialog)
            dialog.force_dispose()
        self._dialogs = []

    def _connect_dialog(self, dialog):
        handles = []
        handles.append(dialog.connect("ringing", self._on_dialog_ringing))
        handles.append(dialog.connect("accepted", self._on_dialog_accepted))
        handles.append(dialog.connect("rejected", self._on_dialog_rejected))
        handles.append(dialog.connect("disposed", self._on_dialog_disposed))
        handles.append(dialog.connect("offer-received", self._on_offer_received))
        self._handles[dialog] = handles

    def _disconnect_dialog(self, dialog):
        if not dialog in self._handles:
            return
        handles = self._handles.pop(dialog)
        for handle in handles:
            dialog.disconnect(handle)

    def _on_dialog_ringing(self, dialog):
        if not self._ringing:
            logger.info("Call is ringing")
            self._ringing = True
            self._dispatch("on_call_ringing")

    def _on_dialog_accepted(self, dialog, response):
        logger.info("Call invitation has been accepted")
        # ignore other call dialogs
        if self._keep_dialog(dialog):
            self._dispatch("on_call_accepted")

    def _on_dialog_rejected(self, dialog, response):
        if response.status/100 == 6: # global rejection
            # we don't have any chance to receive a positive answer
            # keep that dialog for now, it will be disposed soon
            self._keep_dialog(dialog)

        remaining = len(self._dialogs) - 1
        logger.info("Call invitation has been rejected (%i)", response.status)
        logger.info("%i pending dialog(s) remaining for that call" % remaining)
        if remaining <= 0:
            self._dispatch("on_call_rejected", response)

    def _on_dialog_disposed(self, dialog):
        self._disconnect_dialog(dialog)
        self._dialogs.remove(dialog)
        if len(self._dialogs) == 0:
            self._dispose()

    ### Timer Callbacks ------------------------------------------------------

    def on_response_timeout(self):
        self.reject(408) #FIXME
        self._dispatch("on_call_missed")

    ### Media Session Callbacks ----------------------------------------------

    def _on_offer_received(self, dialog, offer, initial=False):
        #FIXME shouldn't need initial
        if self.media_session.process_remote_message(offer, initial):
            dialog.accept_remote_offer()
        else:
            dialog.reject_remote_offer()

    def on_media_session_prepared(self, session):
        if self._pending_invite:
            self.invite()
        elif self._incoming:
            offer = SDPMessage(session=self.media_session)
            self._dialog.update_local_offer(offer)

    def on_media_session_ready(self, session):
        offer = SDPMessage(session=self.media_session)
        self._dialog.update_local_offer(offer)

    ### RTC Activity Callbacks -----------------------------------------------

    def on_activity_accepted(self):
        self._dispose()

    def on_activity_declined(self):
        self._dispose()
