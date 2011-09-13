# -*- coding: utf-8 -*-
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

"""File transfer event interfaces

The interfaces defined in this module allow receiving notification events 
about peer to peer sessions."""

from papyon.event import BaseEventInterface

__all__ = ["P2PSessionEventInterface"]

class P2PSessionEventInterface(BaseEventInterface):
    def __init__(self, session):
        """Initializer
            @param session: the session we want to be notified for its events
            @type session: L{P2PSession<papyon.msnp2p.session.P2PSession>}"""
        BaseEventInterface.__init__(self, session)

    def on_session_accepted(self):
        """Called when our invitation got accepted"""
        pass

    def on_session_rejected(self):
        """Called when our invitation got rejected"""
        pass

    def on_session_progressed(self, size):
        """Called when the session transfer progressed"""
        pass

    def on_session_completed(self, data):
        """Called when the session transfer is completed"""
        pass

    def on_session_canceled(self):
        """Called when the session is canceled"""
        pass

    def on_session_disposed(self):
        """Called when the session is disposed"""
        pass
