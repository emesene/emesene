# -*- coding: utf-8 -*-
#
# Copyright (C) 2008  Ali Sabil <ali.sabil@gmail.com>
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

"""Profile event interfaces

The interfaces defined in this module allow receiving notification events when
the user's profile has been effectively changed on the server."""

from papyon.event import BaseEventInterface

__all__ = ["ProfileEventInterface"]

class ProfileEventInterface(BaseEventInterface):
    """Interface allowing the user to get notified about
    L{Profile<papyon.profile>}s events"""

    def __init__(self, client):
        """Initializer
            @param client: the client we want to be notified for its events
            @type client: L{Client<papyon.Client>}"""
        BaseEventInterface.__init__(self, client)

    def on_profile_presence_changed(self):
        """Called when the presence changes."""
        pass

    def on_profile_display_name_changed(self):
        """Called when the display name changes."""
        pass

    def on_profile_personal_message_changed(self):
        """Called when the personal message changes."""
        pass

    def on_profile_current_media_changed(self):
        """Called when the current media changes."""
        pass

    def on_profile_msn_object_changed(self):
        """Called when the MSNObject changes."""
        pass

    def on_profile_end_points_changed(self):
        """Called when end points change."""
        pass

    def on_profile_end_point_added(self, end_point):
        """Called when a new end point connects."""
        pass

    def on_profile_end_point_removed(self, end_point):
        """Called when an end point disconnects."""
        pass
