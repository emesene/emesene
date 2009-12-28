# -*- coding: utf-8 -*-
#
# Copyright (C) 2007  Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2007  Johann Prieur <johann.prieur@gmail.com>
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

"""Call event interfaces

The interfaces defined in this module allow receiving notification events
from a L{MediaCall<papyon.media.MediaCall>} object."""

from papyon.event import BaseEventInterface

__all__ = ["CallEventInterface"]


class CallEventInterface(BaseEventInterface):
    """interfaces allowing the user to get notified about events
    from a L{MediaCall<papyon.media.MediaCall>} object."""

    def __init__(self, call):
        """Initializer
            @param call: the call we want to be notified for its events
            @type call: L{MediaCall<papyon.media.MediaCall>}"""
        BaseEventInterface.__init__(self, call)

    def on_call_incoming(self):
        """Called once the incoming call is ready."""
        pass

    def on_call_ringing(self):
        """Called when we received a ringing response from the callee."""
        pass

    def on_call_accepted(self):
        """Called when the callee accepted the call."""
        pass

    def on_call_rejected(self, response):
        """Called when the callee rejected the call.
            @param response: response associated with the rejection
            @type response: L{SIPResponse<papyon.sip.SIPResponse>}"""
        pass

    def on_call_error(self, response):
        """Called when an error is sent by the other party.
            @param response: response associated with the error
            @type response: L{SIPResponse<papyon.sip.SIPResponse>}"""
        pass

    def on_call_missed(self):
        """Called when the call is missed."""
        pass

    def on_call_connected(self):
        """Called once the call is connected."""
        pass

    def on_call_ended(self):
        """Called when the call is ended."""
        pass
