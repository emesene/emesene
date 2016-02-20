# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Johann Prieur <johann.prieur@gmail.com>
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

"""Content Roaming event interfaces

The interfaces defined in this module allow receiving notification events about
content roaming."""

from papyon.event import BaseEventInterface

__all__ = ["ContentRoamingEventInterface"]

class ContentRoamingEventInterface(BaseEventInterface):
    """interfaces allowing the user to get notified about events from the
    content roaming object."""

    def __init__(self, client):
        BaseEventInterface.__init__(self, client)

    def on_roaming_state_changed(self, state):
        pass
