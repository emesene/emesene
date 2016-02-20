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

from papyon.media.session import MediaSession

__all__ = ['MediaCall']

class MediaCall(object):
    """This class represents the signaling part in a call between two or more
       peers. Subclasses need to implement the underneath protocol to handle
       invitations and transaction during calls (start/pause/end).

       The media related stuff (NAT traversal, codecs, etc.) would be handled
       by the MediaSession. The MediaCall might however need to implement the
       on_media_prepared and on_media_ready functions. For example, once the
       media session is prepared, we might send a message with the media
       details."""

    def __init__(self, client, session_type):
        """Initialize the media call.

           @param client: Papyon client instance
           @type client: L{papyon.Client}
           @param session_type: Type of session (SIP, webcam...)
           @type session_type: L{papyon.media.constants.MediaSessionType}"""

        self._client = client
        self._media_session = MediaSession(client, session_type)

        self._signals = []
        self._signals.append(self._media_session.connect("prepared",
                self.on_media_session_prepared))
        self._signals.append(self._media_session.connect("ready",
            self.on_media_session_ready))

    @property
    def incoming(self):
        raise NotImplementedError

    @property
    def peer(self):
        raise NotImplementedError

    @property
    def media_session(self):
        return self._media_session

    def invite(self):
        """Invite the peer for a call.
           @note The other participants need to have been previously set."""
        pass

    def accept(self):
        """Accept the call invitation."""
        pass

    def reject(self):
        """Reject the call invitation."""
        pass

    def ring(self):
        """Signal to the peer that we are waiting for the user approval."""
        pass

    def end(self):
        """End the call."""
        pass

    def dispose(self):
        """Close the media session and dispose the call."""
        for handler_id in self._signals:
            self._media_session.disconnect(handler_id)
        self._media_session.close()

    def on_media_session_prepared(self):
        pass

    def on_media_session_ready(self):
        pass
