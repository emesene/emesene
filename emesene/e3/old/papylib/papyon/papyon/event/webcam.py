# -*- coding: utf-8 -*-
#
# Copyright (C) 2007  Ali Sabil <ali.sabil@gmail.com>
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

"""Webcam event interfaces

The interfaces defined in this module allow receiving notification events 
about webcam conversations."""

from papyon.event import BaseEventInterface

__all__ = ["WebcamEventInterface"]

class WebcamEventInterface(BaseEventInterface):
    def __init__(self, session):
        """Initializer
            @param session: the session we want to be notified for its events
            @type session: L{WebcamSession<papyon.msnp2p.webcam.WebcamSession>}"""
        BaseEventInterface.__init__(self, session)

    def on_webcam_viewer_data_received(self):
        """Called when we received viewer data"""
        pass

    def on_webcam_accepted(self):
        """Called when our invitation got accepted"""
        pass

    def on_webcam_rejected(self):
        """Called when our invitation got rejected"""
        pass

    def on_webcam_paused(self):
        """Called when the webcam is paused"""
        pass
