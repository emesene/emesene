# -*- coding: utf-8 -*-
#
# Copyright (C) 2007  Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2007  Ole André Vadla Ravnås <oleavr@gmail.com>
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

"""Contact event interfaces

The interfaces defined in this module allow receiving notification events
from the contacts."""

from papyon.event import BaseEventInterface

__all__ = ["ContactEventInterface"]

class ContactEventInterface(BaseEventInterface):
    """Interface allowing the user to get notified about the
    L{Contact<papyon.profile.Contact>}s events"""

    def __init__(self, client):
        """Initializer
            @param client: the client we want to be notified for its events
            @type client: L{Client<papyon.Client>}"""
        BaseEventInterface.__init__(self, client)

    def on_contact_memberships_changed(self, contact):
        """Called when the memberships of a contact changes.
            @param contact: the contact whose presence changed
            @type contact: L{Contact<papyon.profile.Contact>}
            @see: L{Memberships<papyon.profile.Membership>}"""
        pass

    def on_contact_presence_changed(self, contact):
        """Called when the presence of a contact changes.
            @param contact: the contact whose presence changed
            @type contact: L{Contact<papyon.profile.Contact>}"""
        pass

    def on_contact_display_name_changed(self, contact):
        """Called when the display name of a contact changes.
            @param contact: the contact whose presence changed
            @type contact: L{Contact<papyon.profile.Contact>}"""
        pass

    def on_contact_personal_message_changed(self, contact):
        """Called when the personal message of a contact changes.
            @param contact: the contact whose presence changed
            @type contact: L{Contact<papyon.profile.Contact>}"""
        pass

    def on_contact_current_media_changed(self, contact):
        """Called when the current media of a contact changes.
            @param contact: the contact whose presence changed
            @type contact: L{Contact<papyon.profile.Contact>}"""
        pass

    def on_contact_infos_changed(self, contact, infos):
        """Called when the infos of a contact changes.
            @param contact: the contact whose presence changed
            @type contact: L{Contact<papyon.profile.Contact>}"""
        pass

    def on_contact_client_capabilities_changed(self, contact):
        """Called when the client capabilities of a contact changes.
            @param contact: the contact whose presence changed
            @type contact: L{Contact<papyon.profile.Contact>}"""
        pass

    def on_contact_msn_object_changed(self, contact):
        """Called when the MSNObject of a contact changes.
            @param contact: the contact whose msn object changed
            @type contact: L{Contact<papyon.profile.Contact>}

            @see: L{MSNObjectStore<papyon.p2p.MSNObjectStore>},
                L{MSNObject<papyon.p2p.MSNObject>}"""
        pass

    def on_contact_end_points_changed(self, contact):
        """Called when the end points of a contact change.
            @param contact: the contact whose end points changed
            @type contact: L{Contact<papyon.profile.Contact>}"""
        pass
