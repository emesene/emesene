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

from papyon.msnp.constants import *

import gobject
import logging

logger = logging.getLogger('papyon.media.rtc')

__all__ = ['RTCActivity', 'RTCActivityManager']

class MessageTypes:
    REQUESTOR_BYE = 1
    SERVER_BYE = 2
    ACCEPT = 3
    DECLINE = 4
    CAPABILITIES = 5

class RTCActivityManager(object):
    """Manage the different RTC activities. Forward the messages received from
       the transport to the right activity."""

    def __init__(self, client, protocol):
        self._activities = []
        self._transport = RTCActivityTunneledTransport(protocol)
        self._transport.connect("message-received", self._on_message_received)

    def register(self, activity):
        self._activities.append(activity)

    def unregister(self, activity):
        self._activities.remove(activity)

    def get_transport(self):
        return self._transport

    def _get_activity(self, id):
        for activity in self._activities:
            if activity.id == id:
                return activity
        logger.warning("There is no registered activity with id %s." % id)
        return None

    def _on_message_received(self, transport, peer, peer_guid, type, arguments):
        if type == MessageTypes.ACCEPT:
            id = arguments[1]
            logger.info("Activity %s has been accepted elsewhere." % id)
            activity = self._get_activity(id)
            if activity:
                activity.on_activity_accepted()
        elif type == MessageTypes.DECLINE:
            id = arguments[1]
            logger.info("Activity %s has been declined elsewhere." % id)
            activity = self._get_activity(id)
            if activity:
                activity.on_activity_declined()

        #FIXME handle BYE on timeout


class RTCActivity(object):
    """RTC activity such as a video or audio call (not sure if there is any
       other type of activity). Used to communicate between end points about
       the status of an activity (accepted, declined..) in a MPOP context."""

    def __init__(self, client):
        logger.info("New RTC activity.")
        self._client = client
        self._manager = client.rtc_activity_manager
        self._manager.register(self)
        self._transport = self._manager.get_transport()

    @property
    def id(self):
        raise NotImplementedError

    @property
    def peer(self):
        raise NotImplementedError

    def on_activity_accepted(self):
        raise NotImplementedError

    def on_activity_declined(self):
        raise NotImplementedError

    def _accept_activity(self):
        logger.info("Activity %s has been accepted." % self.id)
        if self._transport is None:
            return
        self._transport.send(self._client.profile.account, None,
                MessageTypes.ACCEPT, ('1', self.id, self.peer.account, '3'))

    def _decline_activity(self):
        logger.info("Activity %s has been declined." % self.id)
        if self._transport is None:
            return
        self._transport.send(self._client.profile.account, None,
                MessageTypes.DECLINE, ('1', self.id, self.peer.account, '3'))

    def _dispose_activity(self):
        self._manager.unregister(self)


class RTCActivityTunneledTransport(gobject.GObject):
    """Default (and only?) RTC activity transport. The messages are sent to
       the notification server using UBN commands."""

    __gsignals__ = {
        "message-received": (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            (object, object, object, object))
    }

    def __init__(self, protocol):
        gobject.GObject.__init__(self)
        self._protocol = protocol
        self._protocol.connect("buddy-notification-received",
                self._on_notification_received)

    def send(self, peer, peer_guid, type, params):
        message = str(type) + ' ' + ' '.join(params)
        self._protocol.send_user_notification(message, peer, peer_guid,
                UserNotificationTypes.RTC_ACTIVITY)

    def _on_notification_received(self, protocol, peer, peer_guid, type, message):
        if type is not UserNotificationTypes.RTC_ACTIVITY:
            return
        logger.debug("<<< " + message)
        params = message.split(' ')
        self.emit("message-received", peer, peer_guid, int(params[0]), params[1:])
