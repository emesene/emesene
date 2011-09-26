# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2005-2006 Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2007-2008 Johann Prieur <johann.prieur@gmail.com>
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

"""Profile of the User connecting to the service, as well as the profile of
contacts in his/her contact list.

    @sort: Profile, Contact, Group, ClientCapabilities
    @group Enums: Presence, Membership, Privacy, NetworkID
    @sort: Presence, Membership, Privacy, NetworkID"""

from papyon.util.decorator import rw_property

import gobject
import logging

__all__ = ['Profile', 'Contact', 'Group', 'EndPoint',
        'Presence', 'Membership', 'ContactType', 'Privacy', 'NetworkID', 'ClientCapabilities']

logger = logging.getLogger('papyon.profile')


class ClientCapabilities(gobject.GObject):
    """Capabilities of the client. This allow adverstising what the User Agent
    is capable of, for example being able to receive video stream, and being
    able to receive nudges...

        @ivar is_bot: is the client a bot
        @type is_bot: bool

        @ivar is_mobile_device: is the client running on a mobile device
        @type is_mobile_device: bool

        @ivar is_msn_mobile: is the client an MSN Mobile device
        @type is_msn_mobile: bool

        @ivar is_msn_direct_device: is the client an MSN Direct device
        @type is_msn_direct_device: bool

        @ivar is_media_center_user: is the client running on a Media Center
        @type is_media_center_user: bool

        @ivar is_msn8_user: is the client using WLM 8
        @type is_msn8_user: bool

        @ivar is_web_client: is the client web based
        @type is_web_client: bool

        @ivar is_tgw_client: is the client a gateway
        @type is_tgw_client: bool

        @ivar has_space: does the user has a space account
        @type has_space: bool

        @ivar has_webcam: does the user has a webcam plugged in
        @type has_webcam: bool

        @ivar has_onecare: does the user has the OneCare service
        @type has_onecare: bool

        @ivar renders_gif: can the client render gif (for ink)
        @type renders_gif: bool

        @ivar renders_isf: can the client render ISF (for ink)
        @type renders_isf: bool

        @ivar supports_chunking: does the client supports chunking messages
        @type supports_chunking: bool

        @ivar supports_activities: does the client supports activities
        @type supports_activities: bool

        @ivar supports_direct_im: does the client supports direct IM
        @type supports_direct_im: bool

        @ivar supports_winks: does the client supports Winks
        @type supports_winks: bool

        @ivar supports_shared_search: does the client supports Shared Search
        @type supports_shared_search: bool

        @ivar supports_voice_im: does the client supports voice clips
        @type supports_voice_im: bool

        @ivar supports_secure_channel: does the client supports secure channels
        @type supports_secure_channel: bool

        @ivar supports_sip_invite: does the client supports SIP
        @type supports_sip_invite: bool

        @ivar supports_tunneled_sip: does the client supports tunneled SIP
        @type supports_tunneled_sip: bool

        @ivar supports_shared_drive: does the client supports File sharing
        @type supports_shared_drive: bool

        @ivar p2p_supports_turn: does the client supports TURN for p2p transfer
        @type p2p_supports_turn: bool

        @ivar p2p_bootstrap_via_uun: is the client able to use and understand UUN commands
        @type p2p_bootstrap_via_uun: bool

        @undocumented: __getattr__, __setattr__, __str__
        """

    __gsignals__ = {
            "capability-changed": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object, object)),
            }

    MSNC = [0x0, # MSNC0
            0x10000000, # MSNC1
            0x20000000, # MSNC2
            0x30000000, # MSNC3
            0x40000000, # MSNC4
            0x50000000, # MSNC5
            0x60000000, # MSNC6
            0x70000000, # MSNC7
            0x80000000, # MSNC8
            0x90000000, # MSNC9
            0xA0000000] # MSNC10

    _CAPABILITIES = {
            'is_bot': 0x00020000,
            'is_mobile_device': 0x00000001,
            'is_msn_mobile': 0x00000040,
            'is_msn_direct_device': 0x00000080,

            'is_media_center_user': 0x00002000,
            'is_msn8_user': 0x00000002,

            'is_web_client': 0x00000200,
            'is_tgw_client': 0x00000800,

            'has_space': 0x00001000,
            'has_webcam': 0x00000010,
            'has_onecare': 0x01000000,

            'renders_gif': 0x00000004,
            'renders_isf': 0x00000008,

            'supports_chunking': 0x00000020,
            'supports_activities': 0x00000100,
            'supports_direct_im': 0x00004000,
            'supports_winks': 0x00008000,
            'supports_shared_search': 0x00010000,
            'supports_voice_im': 0x00040000,
            'supports_secure_channel': 0x00080000,
            'supports_sip_invite': 0x00100000,
            'supports_tunneled_sip': 0x00200000,
            'supports_shared_drive': 0x00400000,

            'p2p_aware': 0xF0000000,
            'p2p_supports_turn': 0x02000000,
            'p2p_bootstrap_via_uun': 0x04000000
            }

    _EXTRA = {
            'supports_rtc_video': 0x00000010,
            'supports_p2pv2': 0x00000030
            }

    def __init__(self, msnc=0, client_id="0:0"):
        """Initializer

            @param msnc: The MSNC version
            @type msnc: integer < 11 and >= 0

            @param client_id: the full client ID"""
        gobject.GObject.__init__(self)
        caps = client_id.split(":")
        capabilities = int(caps[0])
        if len(caps) > 1:
            extra = int(caps[1])
        else:
            extra = 0
        gobject.GObject.__setattr__(self, 'capabilities', self.MSNC[msnc] | capabilities)
        gobject.GObject.__setattr__(self, 'extra', extra)

    def __getattr__(self, name):
        if name in self._CAPABILITIES:
            mask = self._CAPABILITIES[name]
            id = self.capabilities
        elif name in self._EXTRA:
            mask = self._EXTRA[name]
            id = self.extra
        else:
            raise AttributeError("object 'ClientCapabilities' has no attribute '%s'" % name)
        return (id & mask != 0)

    def __setattr__(self, name, value):
        if name in self._CAPABILITIES:
            mask = self._CAPABILITIES[name]
            old_value = bool(self.capabilities & mask)
            if value:
                gobject.GObject.__setattr__(self, 'capabilities', self.capabilities | mask)
            else:
                gobject.GObject.__setattr__(self, 'capabilities', self.capabilities & ~mask)
            if value != old_value:
                self.emit('capability-changed', name, value)
        elif name in self._EXTRA:
            mask = self._EXTRA[name]
            old_value = bool(self.extra & mask)
            if value:
                gobject.GObject.__setattr__(self, 'extra', self.extra | mask)
            else:
                gobject.GObject.__setattr__(self, 'extra', self.extra & ~mask)
            if value != old_value:
                self.emit('capability-changed', name, value)
        else:
            raise AttributeError("object 'ClientCapabilities' has no attribute '%s'" % name)

    def __str__(self):
        msnc = self.MSNC.index(self.capabilities & 0xF0000000)
        if msnc >= 9:
            client_id = "%s:%s" % (self.capabilities, self.extra)
        else:
            client_id = str(self.capabilities)
        return client_id


class NetworkID(object):
    """Refers to the contact Network ID"""

    MSN = 1
    """Microsoft Network"""

    LCS = 2
    """Microsoft Live Communication Server"""

    MOBILE = 4
    """Mobile phones"""

    EXTERNAL = 32
    """External IM etwork, currently Yahoo!"""


class Presence(object):
    """Presence states.

    The members of this class are used to identify the Presence that a user
    wants to advertise to the contacts on his/her contact list.

        @cvar ONLINE: online
        @cvar BUSY: busy
        @cvar IDLE: idle
        @cvar AWAY: away
        @cvar BE_RIGHT_BACK: be right back
        @cvar ON_THE_PHONE: on the phone
        @cvar OUT_TO_LUNCH: out to lunch
        @cvar INVISIBLE: status hidden from contacts
        @cvar OFFLINE: offline"""
    ONLINE = 'NLN'
    BUSY = 'BSY'
    IDLE = 'IDL'
    AWAY = 'AWY'
    BE_RIGHT_BACK = 'BRB'
    ON_THE_PHONE = 'PHN'
    OUT_TO_LUNCH = 'LUN'
    INVISIBLE = 'HDN'
    OFFLINE = 'FLN'


class Privacy(object):
    """User privacy, defines the default policy concerning contacts not
    belonging to the ALLOW list nor to the BLOCK list.

        @cvar ALLOW: allow by default
        @cvar BLOCK: block by default"""
    ALLOW = 'AL'
    BLOCK = 'BL'


class Membership(object):
    """Contact Membership"""

    NONE = 0
    """Contact doesn't belong to the contact list, but belongs to the address book"""

    FORWARD = 1
    """Contact belongs to our contact list"""

    ALLOW = 2
    """Contact is explicitely allowed to see our presence regardless of the
    currently set L{Privacy<papyon.profile.Privacy>}"""

    BLOCK = 4
    """Contact is explicitely forbidden from seeing our presence regardless of
    the currently set L{Privacy<papyon.profile.Privacy>}"""

    REVERSE = 8
    """We belong to the FORWARD list of the contact"""

    PENDING = 16
    """Contact pending"""


class ContactType(object):
    """Automatic update status flag"""

    ME = "Me"
    """Contact is the user so there's no automatic update relationship"""

    EXTERNAL = "Messenger2"
    """Contact is part of an external messenger service so there's no automatic
    update relationship with the user"""

    REGULAR = "Regular"
    """Contact has no automatic update relationship with the user"""

    LIVE = "Live"
    """Contact has an automatic update relationship with the user and an
    automatic update already occured"""

    LIVE_PENDING = "LivePending"
    """Contact was requested automatic update from the user and didn't
    give its authorization yet"""

    LIVE_REJECTED = "LiveRejected"
    """Contact was requested automatic update from the user and rejected
    the request"""

    LIVE_DROPPED = "LiveDropped"
    """Contact had an automatic update relationship with the user but
    the contact dropped it"""


class ContactFlag(object):
    """Internal contact flag"""

    EXTENDED_PRESENCE_KNOWN = 1
    """Set once we receive the extended presence (UBX) for a buddy"""


class BaseContact(gobject.GObject):

    __gsignals__ = {
            "end-point-added": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "end-point-removed": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            }

    __gproperties__ = {
            "client-capabilities": (gobject.TYPE_STRING,
                "Client capabilities",
                "The client capabilities of the contact 's client",
                "",
                gobject.PARAM_READABLE),

            "current-media": (gobject.TYPE_PYOBJECT,
                "Current media",
                "The current media that the user wants to display",
                gobject.PARAM_READABLE),

            "display-name": (gobject.TYPE_STRING,
                "Friendly name",
                "A nickname that the user chooses to display to others",
                "",
                gobject.PARAM_READABLE),

            "end-points": (gobject.TYPE_PYOBJECT,
                "End points",
                "List of locations where the user is connected",
                gobject.PARAM_READABLE),

            "flags": (gobject.TYPE_UINT,
                "Flags",
                "Contact flags.",
                0, 1, 0, gobject.PARAM_READABLE),

            "msn-object": (gobject.TYPE_STRING,
                "MSN Object",
                "MSN Object attached to the user, this generally represent "
                "its display picture",
                "",
                gobject.PARAM_READABLE),

            "personal-message": (gobject.TYPE_STRING,
                "Personal message",
                "The personal message that the user wants to display",
                "",
                gobject.PARAM_READABLE),

            "presence": (gobject.TYPE_STRING,
                "Presence",
                "The presence to show to others",
                Presence.OFFLINE,
                gobject.PARAM_READABLE),

            "signature-sound": (gobject.TYPE_PYOBJECT,
                "Signature sound",
                "The sound played by others' client when the user connects",
                gobject.PARAM_READABLE),
            }

    BLANK_ID = "00000000-0000-0000-0000-000000000000"

    def __init__(self, cid=None):
        gobject.GObject.__init__(self)

        self._cid = cid or self.BLANK_ID
        self._client_capabilities = ClientCapabilities()
        self._current_media = None
        self._display_name = ""
        self._end_points = {}
        self._flags = 0
        self._personal_message = ""
        self._presence = Presence.OFFLINE
        self._msn_object = None
        self._signature_sound = None

    @property
    def account(self):
        """Contact account
            @rtype: utf-8 encoded string"""
        return self._account

    @property
    def cid(self):
        """Contact ID
            @rtype: GUID string"""
        return self._cid

    @property
    def client_id(self):
        """The user capabilities
            @rtype: ClientCapabilities"""
        return self._client_capabilities

    @property
    def client_capabilities(self):
        """The user capabilities
            @rtype: ClientCapabilities"""
        return self._client_capabilities

    @property
    def current_media(self):
        """Contact current media
            @rtype: (artist: string, track: string)"""
        return self._current_media

    @property
    def display_name(self):
        """Contact display name
            @rtype: utf-8 encoded string"""
        return self._display_name

    @property
    def end_points(self):
        """List of contact's locations
           @rtype: list of string"""
        return self._end_points

    @property
    def flags(self):
        """Internal contact flags
            @rtype: bitmask of L{Membership<papyon.profile.ContactFlag}s"""
        return self._flags

    @property
    def id(self):
        """Contact identifier in a GUID form
            @rtype: GUID string"""
        return self._id

    @property
    def msn_object(self):
        """Contact MSN Object
            @type: L{MSNObject<papyon.p2p.MSNObject>}"""
        return self._msn_object

    @property
    def network_id(self):
        """Contact network ID
            @rtype: L{NetworkID<papyon.profile.NetworkID>}"""
        return self._network_id

    @property
    def personal_message(self):
        """Contact personal message
            @rtype: utf-8 encoded string"""
        return self._personal_message

    @property
    def presence(self):
        """Contact presence
            @rtype: L{Presence<papyon.profile.Presence>}"""
        return self._presence

    @property
    def signature_sound(self):
        """Contact signature sound
            @type: string"""
        return self._signature_sound

    ### flags management
    def has_flag(self, flags):
        return (self.flags & flags) == flags

    def _set_flags(self, flags):
        logger.info("Set contact %s flags to %i" % (self._account, flags))
        self._flags = flags
        self.notify("flags")

    def _add_flag(self, flag):
        self._set_flags(self._flags | flag)

    def _remove_flag(self, flag):
        self._set_flags(self._flags & ~flag)

    def _server_property_changed(self, name, value):
        if name == "client-capabilities":
            value = ClientCapabilities(client_id=value)
        attr_name = "_" + name.lower().replace("-", "_")
        old_value = getattr(self, attr_name)
        if value != old_value:
            setattr(self, attr_name, value)
            self.notify(name)
        if name == "end-points":
            self._diff_end_points(old_value, value)

    def _diff_end_points(self, old_eps, new_eps):
        added_eps = set(new_eps.keys()) - set(old_eps.keys())
        removed_eps = set(old_eps.keys()) - set(new_eps.keys())
        for ep in added_eps:
            self.emit("end-point-added", new_eps[ep])
        for ep in removed_eps:
            self.emit("end-point-removed", old_eps[ep])

    def do_get_property(self, pspec):
        name = pspec.name.lower().replace("-", "_")
        return getattr(self, name)
gobject.type_register(BaseContact)


class Profile(BaseContact):
    """Profile of the User connecting to the service"""

    __gproperties__ = {
            "profile": (gobject.TYPE_PYOBJECT,
                "Profile",
                "the text/x-msmsgsprofile sent by the server",
                gobject.PARAM_READABLE),

            "privacy": (gobject.TYPE_STRING,
                "Privacy",
                "The privacy policy to use",
                Privacy.BLOCK,
                gobject.PARAM_READABLE),
            }

    def __init__(self, account, ns_client):
        BaseContact.__init__(self)
        self._ns_client = ns_client
        self._account = account[0]
        self._password = account[1]

        self._id = self.BLANK_ID
        self._profile = ""
        self._network_id = NetworkID.MSN
        self._display_name = self._account.split("@", 1)[0]
        self._privacy = Privacy.BLOCK
        self._end_point_name = ""

        self._client_capabilities = ClientCapabilities(10)
        self._client_capabilities.supports_sip_invite = True
        self._client_capabilities.supports_tunneled_sip = True
        self._client_capabilities.supports_p2pv2 = True
        self._client_capabilities.p2p_bootstrap_via_uun = True
        self._client_capabilities.connect("capability-changed",
                self._client_capability_changed)

        self.__pending_set_presence = [self._presence, self._client_capabilities, self._msn_object]
        self.__pending_set_personal_message = [self._personal_message, self._current_media]

    @property
    def password(self):
        """The user password
            @rtype: utf-8 encoded string"""
        return self._password

    @property
    def profile(self):
        """The user profile retrieved from the MSN servers
            @rtype: dict of fields"""
        return self._profile

    @rw_property
    def display_name():
        """The display name shown to you contacts
            @type: utf-8 encoded string"""
        def fset(self, display_name):
            if not display_name:
                return
            self._ns_client.set_display_name(display_name)
        def fget(self):
            return self._display_name
        return locals()

    @rw_property
    def presence():
        """The presence displayed to you contacts
            @type: L{Presence<papyon.profile.Presence>}"""
        def fset(self, presence):
            if presence == self._presence:
                return
            self.__pending_set_presence[0] = presence
            self._ns_client.set_presence(*self.__pending_set_presence)
        def fget(self):
            return self._presence
        return locals()

    @rw_property
    def privacy():
        """The default privacy, can be either Privacy.ALLOW or Privacy.BLOCK
            @type: L{Privacy<papyon.profile.Privacy>}"""
        def fset(self, privacy):
            self._ns_client.set_privacy(privacy)
        def fget(self):
            return self._privacy
        return locals()

    @rw_property
    def personal_message():
        """The personal message displayed to you contacts
            @type: utf-8 encoded string"""
        def fset(self, personal_message):
            if personal_message == self._personal_message:
                return
            self.__pending_set_personal_message[0] = personal_message
            self._ns_client.set_personal_message(*self.__pending_set_personal_message)
        def fget(self):
            return self._personal_message
        return locals()

    @rw_property
    def current_media():
        """The current media displayed to you contacts
            @type: (artist: string, track: string)"""
        def fset(self, current_media):
            if current_media == self._current_media:
                return
            self.__pending_set_personal_message[1] = current_media
            self._ns_client.set_personal_message(*self.__pending_set_personal_message)
        def fget(self):
            return self._current_media
        return locals()

    @rw_property
    def signature_sound():
        """The sound played when you are connecting
            @type: string"""
        def fset(self, signature_sound):
            if signature_sound == self._signature_sound:
                return
            self.__pending_set_personal_message[2] = signature_sound
            self._ns_client.set_personal_message(*self.__pending_set_personal_message)
        def fget(self):
            return self._signature_sound
        return locals()

    @rw_property
    def end_point_name():
        def fset(self, name):
            if name == self._end_point_name:
                return
            self._ns_client.set_end_point_name(name)
        def fget(self):
            return self._end_point_name
        return locals()

    @rw_property
    def msn_object():
        """The MSNObject attached to your contact, this MSNObject represents the
        display picture to be shown to your peers
            @type: L{MSNObject<papyon.p2p.MSNObject>}"""
        def fset(self, msn_object):
            if msn_object == self._msn_object:
                return
            self.__pending_set_presence[2] = msn_object
            self._ns_client.set_presence(*self.__pending_set_presence)
        def fget(self):
            return self._msn_object
        return locals()

    @rw_property
    def presence_msn_object():
        def fset(self, args):
            presence, msn_object = args
            if presence == self._presence and msn_object == self._msn_object:
                return
            self.__pending_set_presence[0] = presence
            self.__pending_set_presence[2] = msn_object
            self._ns_client.set_presence(*self.__pending_set_presence)
        def fget(self):
            return self._presence, self._msn_object
        return locals()

    @rw_property
    def personal_message_current_media():
        def fset(self, args):
            personal_message, current_media = args
            if personal_message == self._personal_message and \
                    current_media == self._current_media:
                return
            self.__pending_set_personal_message[0] = personal_message
            self.__pending_set_personal_message[1] = current_media
            self._ns_client.set_personal_message(*self.__pending_set_personal_message)
        def fget(self):
            return self._personal_message, self._current_media
        return locals()

    def request_profile_url(self, callback):
        self._ns_client.send_url_request(('PROFILE', '0x0409'), callback)

    def _client_capability_changed(self, client, name, value):
        self.__pending_set_presence[1] = self._client_capabilities
        self._ns_client.set_presence(*self.__pending_set_presence)

    def _server_property_changed(self, name, value):
        if name == "msn-object" and value is not None:
            self.__pending_set_presence[2] = value
        BaseContact._server_property_changed(self, name, value)
gobject.type_register(Profile)


class Contact(BaseContact):
    """Contact related information"""

    __gsignals__ = {
            "infos-changed": (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            }

    __gproperties__ = {
            "memberships": (gobject.TYPE_UINT,
                "Memberships",
                "Membership relation with the contact.",
                0, 31, 0, gobject.PARAM_READABLE),

             "groups": (gobject.TYPE_PYOBJECT,
                 "Groups",
                 "The groups the contact belongs to",
                 gobject.PARAM_READABLE),

            "infos": (gobject.TYPE_PYOBJECT,
                "Informations",
                "The contact informations",
                gobject.PARAM_READABLE),

            "contact-type": (gobject.TYPE_PYOBJECT,
                "Contact type",
                "The contact automatic update status flag",
                 gobject.PARAM_READABLE),
            }

    def __init__(self, id, network_id, account, display_name, cid=None,
            memberships=Membership.NONE, contact_type=ContactType.REGULAR):
        """Initializer"""
        BaseContact.__init__(self, cid)
        self._id = id or self.BLANK_ID
        self._network_id = network_id
        self._account = account
        self._display_name = display_name

        self._attributes = {'icon_url' : None}
        self._groups = set()
        self._infos = {}
        self._memberships = memberships
        self._contact_type = contact_type

    def __repr__(self):
        def memberships_str():
            m = []
            memberships = self._memberships
            if memberships & Membership.FORWARD:
                m.append('FORWARD')
            if memberships & Membership.ALLOW:
                m.append('ALLOW')
            if memberships & Membership.BLOCK:
                m.append('BLOCK')
            if memberships & Membership.REVERSE:
                m.append('REVERSE')
            if memberships & Membership.PENDING:
                m.append('PENDING')
            return " | ".join(m)
        template = "<papyon.Contact id='%s' network='%u' account='%s' memberships='%s'>"
        return template % (self._id, self._network_id, self._account, memberships_str())

    @property
    def attributes(self):
        """Contact attributes
            @rtype: {key: string => value: string}"""
        return self._attributes.copy()

    @property
    def groups(self):
        """Contact list of groups
            @rtype: set(L{Group<papyon.profile.Group>}...)"""
        return self._groups

    @property
    def infos(self):
        """Contact informations
            @rtype: {key: string => value: string}"""
        return self._infos

    @property
    def memberships(self):
        """Contact membership value
            @rtype: bitmask of L{Membership<papyon.profile.Membership>}s"""
        return self._memberships

    @property
    def contact_type(self):
        """Contact automatic update status flag
            @rtype: L{ContactType<papyon.profile.ContactType>}"""
        return self._contact_type

    @property
    def domain(self):
        """Contact domain, which is basically the part after @ in the account
            @rtype: utf-8 encoded string"""
        result = self._account.split('@', 1)
        if len(result) > 1:
            return result[1]
        else:
            return ""

    @property
    def profile_url(self):
        """Contact profile url
            @rtype: string"""
        account = self._account
        return "http://members.msn.com/default.msnw?mem=%s&pgmarket=" % account

    ### membership management
    def is_member(self, memberships):
        """Determines if this contact belongs to the specified memberships
            @type memberships: bitmask of L{Membership<papyon.profile.Membership>}s"""
        return (self.memberships & memberships) == memberships

    def is_mail_contact(self):
        """Determines if this contact is a mail contact"""
        return (not self.is_member(Membership.FORWARD) \
                and self.id != self.BLANK_ID)

    def _set_memberships(self, memberships):
        if self._memberships != memberships:
            self._memberships = memberships
            self.notify("memberships")

    def _add_membership(self, membership):
        if self._memberships != (self._memberships | membership):
            self._memberships |= membership
            self.notify("memberships")

    def _remove_membership(self, membership):
        if self._memberships != (self._memberships & ~membership):
            self._memberships &= ~membership
            self.notify("memberships")

    def _server_attribute_changed(self, name, value):
        self._attributes[name] = value

    def _server_infos_changed(self, updated_infos):
        self._infos.update(updated_infos)
        self.emit("infos-changed", updated_infos)
        self.notify("infos")

    def _reset(self):
        self._id = self.BLANK_ID
        self._cid = self.BLANK_ID
        self._groups = set()
        self._flags = 0

        self._server_property_changed("presence", Presence.OFFLINE)
        self._server_property_changed("display-name", self._account)
        self._server_property_changed("personal-message", "")
        self._server_property_changed("current-media", None)
        self._server_property_changed("msn-object", None)
        self._server_property_changed("client-capabilities", "0:0")
        self._server_property_changed("end-points", {})
        self._server_infos_changed({})

    ### group management
    def _add_group_ownership(self, group):
        self._groups.add(group)

    def _delete_group_ownership(self, group):
        self._groups.discard(group)
gobject.type_register(Contact)


class Group(gobject.GObject):
    """Group
        @undocumented: __gsignals__, __gproperties__, do_get_property"""

    __gproperties__ = {
        "name": (gobject.TYPE_STRING,
                 "Group name",
                 "Name that the user chooses for the group",
                 "",
                 gobject.PARAM_READABLE)
        }

    def __init__(self, id, name):
        """Initializer"""
        gobject.GObject.__init__(self)
        self._id = id
        self._name = name

    @property
    def id(self):
        """Group identifier in a GUID form
            @rtype: GUID string"""
        return self._id

    @property
    def name(self):
        """Group name
            @rtype: utf-8 encoded string"""
        return self._name

    def _server_property_changed(self, name, value):
        attr_name = "_" + name.lower().replace("-", "_")
        old_value = getattr(self, attr_name)
        if value != old_value:
            setattr(self, attr_name, value)
            self.notify(name)

    def do_get_property(self, pspec):
        name = pspec.name.lower().replace("-", "_")
        return getattr(self, name)
gobject.type_register(Group)


class EndPoint(object):
    def __init__(self, id, caps):
        self.id = id
        self.capabilities = ClientCapabilities(client_id=caps)
        self.name = ""
        self.idle = False
        self.state = ""
        self.client_type = 0

    def __eq__(self, endpoint):
        return (self.id == endpoint.id and
                self.capabilities == endpoint.capabilities and
                self.name == endpoint.name and
                self.idle == endpoint.idle and
                self.state == endpoint.state and
                self.client_type == endpoint.client_type)
