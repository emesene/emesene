# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2005-2007 Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2005-2006 Ole André Vadla Ravnås <oleavr@gmail.com>
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
# GNU General Public License for more details
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""Notification protocol Implementation
Implements the protocol used to communicate with the Notification Server."""

from base import BaseProtocol
from message import Message
from constants import ProtocolConstant, ProtocolError, ProtocolState
from challenge import _msn_challenge

import papyon
from papyon.gnet.message.HTTP import HTTPMessage
from papyon.util.async import run
from papyon.util.queue import PriorityQueue, LastElementQueue
from papyon.util.decorator import throttled
from papyon.util.encoding import decode_rfc2047_string
from papyon.util.parsing import build_account, parse_account
from papyon.util.timer import Timer
import papyon.util.element_tree as ElementTree
import papyon.profile as profile
import papyon.service.SingleSignOn as SSO
import papyon.service.AddressBook as AB
import papyon.service.OfflineIM as OIM

import hashlib
import time
import logging
import uuid
import urllib
import gobject
import xml.sax.saxutils as xml_utils

__all__ = ['NotificationProtocol']

logger = logging.getLogger('papyon.protocol.notification')


class NotificationProtocol(BaseProtocol, Timer):
    """Protocol used to communicate with the Notification Server

        @undocumented: do_get_property, do_set_property
        @group Handlers: _handle_*, _default_handler, _error_handler

        @ivar state: the current protocol state
        @type state: integer
        @see L{constants.ProtocolState}"""
    __gsignals__ = {
            "buddy-notification-received" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object, object, object, object)),

            "mail-received" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),

            "switchboard-invitation-received" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object, object)),

            "unmanaged-message-received" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object, object)),
            }

    def __init__(self, client, transport, proxies={}, version=15):
        """Initializer

            @param client: the parent instance of L{client.Client}
            @type client: L{client.Client}

            @param transport: The transport to use to speak the protocol
            @type transport: L{transport.BaseTransport}

            @param proxies: a dictonary mapping the proxy type to a
                L{gnet.proxy.ProxyInfos} instance
            @type proxies: {type: string, proxy:L{gnet.proxy.ProxyInfos}}
        """
        BaseProtocol.__init__(self, client, transport, proxies)
        Timer.__init__(self)
        self.__state = ProtocolState.CLOSED
        self._protocol_version = version
        self._callbacks = {} # tr_id=>(callback, errback)
        self._time_id = 0

    # Properties ------------------------------------------------------------
    def __get_state(self):
        return self.__state
    def __set_state(self, state):
        self.__state = state
        self.notify("state")
    state = property(__get_state)
    _state = property(__get_state, __set_state)

    def do_get_property(self, pspec):
        if pspec.name == "state":
            return self.__state
        else:
            raise AttributeError, "unknown property %s" % pspec.name

    def do_set_property(self, pspec, value):
        raise AttributeError, "unknown property %s" % pspec.name

    # Public API -------------------------------------------------------------
    @throttled(2, LastElementQueue())
    def set_presence(self, presence, client_id=0, msn_object=None):
        """Publish the new user presence.

            @param presence: the new presence
            @type presence: string L{profile.Presence}"""
        if msn_object == None:
            msn_object = ""

        if presence == profile.Presence.OFFLINE:
            self._client.logout()
        else:
            if msn_object:
                self._client._msn_object_store.publish(msn_object)
            self._send_command('CHG',
                    (presence, str(client_id), urllib.quote(str(msn_object))))

    @throttled(2, LastElementQueue())
    def set_display_name(self, display_name):
        """Sets the new display name

            @param display_name: the new friendly name
            @type display_name: string"""
        self._send_command('PRP',
                ('MFN', urllib.quote(display_name)))

    @throttled(2, LastElementQueue())
    def set_personal_message(self, personal_message='', current_media=None,
            signature_sound=None):
        """Sets the new personal message

            @param personal_message: the new personal message
            @type personal_message: string"""
        cm = ''
        if current_media is not None:
            cm = '\\0Music\\01\\0{0} - {1}\\0%s\\0%s\\0\\0' % \
                (xml_utils.escape(current_media[0]),
                 xml_utils.escape(current_media[1]))

        if signature_sound is not None:
            signature_sound = xml_utils.escape(signature_sound)
            ss = '<SignatureSound>%s</SignatureSound>' % signature_sound

        message = xml_utils.escape(personal_message)
        pm = '<Data>'\
                '<PSM>%s</PSM>'\
                '<CurrentMedia>%s</CurrentMedia>'\
                '<MachineGuid>%s</MachineGuid>'\
            '</Data>' % (message, cm, str(self._client.machine_guid).upper())
        self._send_command('UUX', payload=pm)
        self._client.profile._server_property_changed("personal-message",
                personal_message)
        if current_media is not None:
            self._client.profile._server_property_changed("current-media",
                current_media)

    @throttled(2, LastElementQueue())
    def set_end_point_name(self, name="Papyon", idle=False):
        ep = '<EndpointData>'\
                '<Capabilities>%s</Capabilities>'\
            '</EndpointData>' % self._client.profile.client_id

        name = xml_utils.escape(name)
        pep = '<PrivateEndpointData>'\
                '<EpName>%s</EpName>'\
                '<Idle>%s</Idle>'\
                '<State>%s</State>'\
                '<ClientType>%i</ClientType>'\
            '</PrivateEndpointData>' % (name, str(idle).lower(),
                    self._client.profile.presence, self._client.client_type)
        self._send_command('UUX', payload=ep)
        self._send_command('UUX', payload=pep)

    @throttled(2, LastElementQueue())
    def set_privacy(self, privacy=profile.Privacy.BLOCK):
        self._send_command("BLP", (privacy,))

    def signoff(self):
        """Logout from the server"""
        if self._state >= ProtocolState.AUTHENTICATING:
            self._send_command('OUT')
        self._transport.lose_connection()

    @throttled(7, list())
    def request_switchboard(self, priority, callback):
        self.__switchboard_callbacks.add(callback, priority)
        self._send_command('XFR', ('SB',))

    def add_contact_to_membership(self, account,
            network_id=profile.NetworkID.MSN,
            membership=profile.Membership.FORWARD):
        """Add a contact to a given membership.

            @param account: the contact identifier
            @type account: string

            @param network_id: the contact network
            @type network_id: integer
            @see L{papyon.profile.NetworkID}

            @param membership: the list to be added to
            @type membership: integer
            @see L{papyon.profile.Membership}"""

        if network_id == profile.NetworkID.MOBILE:
            payload = '<ml><t><c n="tel:%s" l="%d" /></t></ml>' % \
                    (account, membership)
            self._send_command("ADL", payload=payload)
        else:
            user, domain = account.split("@", 1)
            payload = '<ml><d n="%s"><c n="%s" l="%d" t="%d"/></d></ml>' % \
                    (domain, user, membership, network_id)
            self._send_command("ADL", payload=payload)

    def remove_contact_from_membership(self, account,
            network_id=profile.NetworkID.MSN,
            membership=profile.Membership.FORWARD):
        """Remove a contact from a given membership.

            @param account: the contact identifier
            @type account: string

            @param network_id: the contact network
            @type network_id: integer
            @see L{papyon.profile.NetworkID}

            @param membership: the list to be added to
            @type membership: integer
            @see L{papyon.profile.Membership}"""

        if network_id == profile.NetworkID.MOBILE:
            payload = '<ml><t><c n="tel:%s" l="%d" /></t></ml>' % \
                    (account, membership)
            self._send_command("RML", payload=payload)
        else:
            user, domain = account.split("@", 1)
            payload = '<ml><d n="%s"><c n="%s" l="%d" t="%d"/></d></ml>' % \
                    (domain, user, membership, network_id)
            self._send_command("RML", payload=payload)

    def send_user_notification(self, message, contact, contact_guid, type,
            callback=None, errback=None):
        account = build_account(contact, contact_guid)
        arguments = (account, type)
        tr_id = self._send_command("UUN", arguments, message, True)
        self._callbacks[tr_id] = (callback, errback)

    def send_unmanaged_message(self, contact, message, callback=None,
            errback=None):
        content_type = message.content_type[0]
        if content_type == 'text/x-msnmsgr-datacast':
            message_type = 3
        elif content_type == 'text/x-msmsgscontrol':
            message_type = 2
        else:
            message_type = 1
        tr_id = self._send_command('UUM',
                (contact.account, contact.network_id, message_type),
                payload=message, callback=callback)
        self._callbacks[tr_id] = (None, errback)

    def send_url_request(self, url_command_args, callback):
        tr_id = self._send_command('URL', url_command_args)
        self._callbacks[tr_id] = (callback, None)

    # Helpers ----------------------------------------------------------------
    def __search_account(self, account, network_id=profile.NetworkID.MSN):
        contact = self._client.address_book.search_contact(account, network_id)

        if contact is None:
            logger.warning("Contact (network_id=%d) %s not found" % \
                    (network_id, account))

        return contact

    def __parse_network_and_account(self, command, idx=0):
        if self._protocol_version >= 18 and ":" in command.arguments[idx]:
            temp = command.arguments[idx].split(":")
            network_id = int(temp[0])
            account = temp[1]
        else:
            account = command.arguments[idx]
            idx += 1
            network_id = int(command.arguments[idx])
        idx += 1
        return idx, network_id, account

    def __find_node(self, parent, name, default):
        node = parent.find(name)
        if node is not None and node.text is not None:
            return node.text.encode("utf-8")
        else:
            return default

    # Handlers ---------------------------------------------------------------
    # --------- Connection ---------------------------------------------------
    def _handle_VER(self, command):
        self._protocol_version = int(command.arguments[0].lstrip('MSNP'))
        self._send_command('CVR',
                ProtocolConstant.CVR + (self._client.profile.account,))

    def _handle_CVR(self, command):
        method = 'SSO'
        self._send_command('USR',
                (method, 'I', self._client.profile.account))

    def _handle_XFR(self, command):
        if command.arguments[0] == 'NS':
            try:
                host, port = command.arguments[1].split(":", 1)
                port = int(port)
            except ValueError:
                host = command.arguments[1]
                port = self._transport.server[1]
            logger.debug("<-> Redirecting to " + command.arguments[1])
            self._transport.reset_connection((host, port))
        else: # connect to a switchboard
            try:
                host, port = command.arguments[1].split(":", 1)
                port = int(port)
            except ValueError:
                host = command.arguments[1]
                port = self._transport.server[1]
            session_id = command.arguments[3]
            callback = self.__switchboard_callbacks.pop(0)
            run(callback, ((host, port), session_id, None))

    def _handle_USR(self, command):
        args_len = len(command.arguments)

        # MSNP15 have only 4 params for final USR
        assert(args_len == 3 or args_len == 4), \
                "Received USR with invalid number of params : " + str(command)

        if command.arguments[0] == "OK":
            self._state = ProtocolState.AUTHENTICATED

        # we need to authenticate with a passport server
        elif command.arguments[1] == "S":
            self._state = ProtocolState.AUTHENTICATING
            if command.arguments[0] == "SSO":
                self._client._sso.RequestMultipleSecurityTokens(
                    (self._sso_cb, command.arguments[3]),
                    ((lambda error: self.emit("error",
                        ProtocolError.AUTHENTICATION_FAILED)),),
                    SSO.LiveService.MESSENGER_CLEAR)

                self._client.address_book.connect("notify::state",
                    self._address_book_state_changed_cb)

                self._client.address_book.connect("messenger-contact-added",
                        self._address_book_contact_added_cb)
                self._client.address_book.connect("contact-accepted",
                        self._address_book_contact_accepted_cb)
                self._client.address_book.connect("contact-rejected",
                        self._address_book_contact_rejected_cb)
                self._client.address_book.connect("contact-deleted",
                        self._address_book_contact_deleted_cb)
                self._client.address_book.connect("contact-blocked",
                        self._address_book_contact_blocked_cb)
                self._client.address_book.connect("contact-unblocked",
                        self._address_book_contact_unblocked_cb)
                self._client.address_book.connect("contact-allowed",
                        self._address_book_contact_allowed_cb)
                self._client.address_book.connect("contact-disallowed",
                        self._address_book_contact_disallowed_cb)

            elif command.arguments[0] == "TWN":
                raise NotImplementedError, "Missing Implementation, please fix"

    def _handle_SBS(self, command): # unknown command
        pass

    def _handle_QNG(self, command):
        timeout = int(command.arguments[0])
        self.start_timeout("ping", timeout)
        self._time_id = time.time()
        self.start_timeout(("qing", self._time_id), timeout+5)

    def _handle_OUT(self, command):
        reason = None
        if len(command.arguments) > 0:
            reason = command.arguments[0]

        if reason == "OTH":
            self.emit("error", ProtocolError.OTHER_CLIENT)
        elif reason == "SSD":
            self.emit("error", ProtocolError.SERVER_DOWN)
        else:
            self._transport.lose_connection()

    # --------- Presence & Privacy -------------------------------------------
    def _handle_BLP(self, command):
        self._client.profile._server_property_changed("privacy",
                command.arguments[0])

    def _handle_GCF(self, command):
        pass

    def _handle_CHG(self, command):
        self._client.profile._server_property_changed("presence",
                command.arguments[0])
        if len(command.arguments) > 2:
            if command.arguments[2] != '0':
                msn_object = papyon.p2p.MSNObject.parse(self._client,
                               urllib.unquote(command.arguments[2]))
            else:
                msn_object = None
            self._client.profile._server_property_changed("msn_object", msn_object)
        else:
            self._client.profile._server_property_changed("msn_object", None)

    def _handle_ILN(self, command):
        self._handle_NLN(command)

    def _handle_FLN(self, command):
        idx, network_id, account = self.__parse_network_and_account(command)
        contact = self.__search_account(account, network_id)
        if contact is not None:
            contact._remove_flag(profile.ContactFlag.EXTENDED_PRESENCE_KNOWN)
            contact._server_property_changed("presence",
                    profile.Presence.OFFLINE)

    def _handle_NLN(self, command):
        idx, network_id, account = self.__parse_network_and_account(command, 1)
        presence = command.arguments[0]
        display_name = urllib.unquote(command.arguments[idx])
        idx += 1
        capabilities = command.arguments[idx]
        idx += 1

        msn_object = None
        icon_url = None

        if len(command.arguments) > idx:
            if command.arguments[idx] not in ('0', '1'):
                msn_object = papyon.p2p.MSNObject.parse(self._client,
                               urllib.unquote(command.arguments[idx]))

        idx += 1
        if len(command.arguments) > idx:
            icon_url = command.arguments[idx]

        contact = self.__search_account(account, network_id)
        if contact is not None:
            # don't change local presence and capabilities
            if contact is not self._client.profile:
                contact._server_property_changed("presence", presence)
                contact._server_property_changed("client-capabilities", capabilities)
            contact._server_property_changed("display-name", display_name)
            # only change MSNObject if the extended presence is known (MSNP18)
            if self._protocol_version < 18 or \
               contact.has_flag(profile.ContactFlag.EXTENDED_PRESENCE_KNOWN):
                contact._server_property_changed("msn_object", msn_object)
            if icon_url is not None:
                contact._server_attribute_changed('icon_url', icon_url)

    # --------- Display name and co ------------------------------------------
    def _handle_PRP(self, command):
        ctype = command.arguments[0]
        if len(command.arguments) < 2: return
        if ctype == 'MFN':
            self._client.profile._server_property_changed('display-name',
                    urllib.unquote(command.arguments[1]))
        # TODO: add support for other stuff

    def _handle_UUX(self, command):
        pass

    def _handle_UBN(self, command): # contact infos
        if not command.payload:
            return
        account, guid = parse_account(command.arguments[0])
        contact = self.__search_account(account)
        type = int(command.arguments[1])
        payload = command.payload
        self.emit("buddy-notification-received", contact, guid, type, payload)

    def _handle_UBX(self, command): # contact infos
        if not command.payload:
            return
        idx, network_id, account = self.__parse_network_and_account(command)

        try:
            tree = ElementTree.fromstring(command.payload)
        except:
            logger.error("Invalid XML data in received UBX command")
            return

        utl = self.__find_node(tree, "./UserTileLocation", "")
        cm_parts = self.__find_node(tree, "./CurrentMedia", "").split('\\0')
        pm = self.__find_node(tree, "./PSM", "")
        rmu = self.__find_node(tree, "./RMU", "")
        ss = self.__find_node(tree, "./SignatureSound", None)
        mg = self.__find_node(tree, "./MachineGuid", "{}").lower()[1:-1]

        msn_object = None
        if utl != "" and utl != "0":
            msn_object = papyon.p2p.MSNObject.parse(self._client, utl)

        cm = None
        if len(cm_parts) >= 6 and cm_parts[1] == 'Music' and cm_parts[2] == '1':
            cm = (cm_parts[4], cm_parts[5])

        eps = tree.findall("./EndpointData")
        end_points = {}
        for ep in eps:
            guid = uuid.UUID(ep.get("id"))
            caps = self.__find_node(ep, "Capabilities", "0:0")
            end_points[guid] = profile.EndPoint(guid, caps)
        peps = tree.findall("./PrivateEndpointData")
        for pep in peps:
            guid = uuid.UUID(pep.get("id"))
            if guid not in end_points: continue
            end_point = end_points[guid]
            end_point.name = self.__find_node(pep, "EpName", "")
            end_point.idle = bool(self.__find_node(pep, "Idle", "").lower() == "true")
            end_point.client_type = int(self.__find_node(pep, "ClientType", 0))
            end_point.state = self.__find_node(pep, "State", "")

        contact = self.__search_account(account, network_id)
        if contact is not None:
            contact._add_flag(profile.ContactFlag.EXTENDED_PRESENCE_KNOWN)
            contact._server_property_changed("end-points", end_points)
            contact._server_property_changed("msn-object", msn_object)
            contact._server_property_changed("current-media", cm)
            contact._server_property_changed("personal-message", pm)
            contact._server_property_changed("signature-sound", ss)

    def _handle_UUN(self, command): # UBN acknowledgment
        self._command_answered_cb(command.transaction_id)

    # --------- Contact List -------------------------------------------------
    def _handle_ADL(self, command):
        if len(command.arguments) > 0 and command.arguments[0] == "OK":
            # Confirmation for one of our ADLs
            if command.transaction_id != 0 \
            and self._state != ProtocolState.OPEN:
                # Initial ADL
                self._state = ProtocolState.OPEN
                self._transport.enable_ping()
        else:
            if command.payload:
                # Incoming payload ADL from the server
                self._client.address_book.sync(True)

    def _handle_RML(self, command):
        pass

    def _handle_FQY(self, command):
        pass

    # --------- Messages -----------------------------------------------------
    def _handle_MSG(self, command):
        message = Message(None, command.payload)
        content_type = message.content_type
        if content_type[0] == 'text/x-msmsgsprofile':
            profile = {}
            lines = command.payload.split("\r\n")
            for line in lines:
                line = line.strip()
                if line:
                    name, value = line.split(":", 1)
                    profile[name] = value.strip()
            self._client.profile._server_property_changed("profile", profile)

            self.set_privacy(self._client.profile.privacy)
            self._state = ProtocolState.SYNCHRONIZING
            self._client.address_book.sync()
        elif content_type[0] in \
                ('text/x-msmsgsinitialmdatanotification', \
                 'text/x-msmsgsoimnotification'):
            if self._client.oim_box is not None:
                self._client.oim_box._state = \
                    OIM.OfflineMessagesBoxState.NOT_SYNCHRONIZED
                m = HTTPMessage()
                m.parse(message.body)
                mail_data = m.get_header('Mail-Data').strip()
                if mail_data == 'too-large':
                    mail_data = None
                self._client.oim_box.sync(mail_data)
                if mail_data and \
                   content_type[0] == 'text/x-msmsgsinitialmdatanotification':
                    #Initial mail
                    start = mail_data.find('<IU>') + 4
                    end = mail_data.find('</IU>')
                    if start < end:
                        mailbox_unread = int(mail_data[start:end])
                        self._client.mailbox._initial_set(mailbox_unread)
        elif content_type[0] == 'text/x-msmsgsinitialemailnotification':
            #Initial mail (obsolete by MSNP11)
            pass
        elif content_type[0] == 'text/x-msmsgsemailnotification':
            #New mail
            m = HTTPMessage()
            m.parse(message.body)
            name = decode_rfc2047_string(m.get_header('From'))
            address = m.get_header('From-Addr')
            subject = decode_rfc2047_string(m.get_header('Subject'))
            message_url = m.get_header('Message-URL')
            post_url = m.get_header('Post-URL')
            post_id = m.get_header('id')
            dest = m.get_header('Dest-Folder')
            if dest == 'ACTIVE':
                self._client.mailbox._unread_mail_increased(1)
                build = self._build_url_post_data
                post_url, form_data = build(message_url, post_url, post_id)
                self._client.mailbox._new_mail(name, address, subject,
                                               post_url, form_data)
        elif content_type[0] == 'text/x-msmsgsactivemailnotification':
            #Movement of unread mail
            m = HTTPMessage()
            m.parse(message.body)
            src = m.get_header('Src-Folder')
            dest = m.get_header('Dest-Folder')
            delta = int(m.get_header('Message-Delta'))
            if src == 'ACTIVE':
                self._client.mailbox._unread_mail_decreased(delta)
            elif dest == 'ACTIVE':
                self._client.mailbox._unread_mail_increased(delta)

    def _handle_UBM(self, command):
        idx, network_id, account = self.__parse_network_and_account(command)
        contact = self.__search_account(account, network_id)
        if contact is not None:
            message = Message(contact, command.payload)
            self.emit("unmanaged-message-received", contact, message)

    # --------- Urls ---------------------------------------------------------

    def _build_url_post_data(self,
                message_url="/cgi-bin/HoTMaiL",
                post_url='https://loginnet.passport.com/ppsecure/md5auth.srf?',
                post_id='2'):

        profile = self._client.profile.profile
        account = self._client.profile.account
        password = str(self._client.profile.password)
        sl = str(int(time.time()) - int(profile['LoginTime']))
        sid = profile['sid']
        auth = profile['MSPAuth']
        creds = hashlib.md5(auth + sl + password).hexdigest()

        post_data = dict([
            ('mode', 'ttl'),
            ('login', account.split('@')[0]),
            ('username', account),
            ('sid', sid),
            ('kv', ''),
            ('id', post_id),
            ('sl', sl),
            ('rru', message_url),
            ('auth', auth),
            ('creds', creds),
            ('svc', 'mail'),
            ('js', 'yes')])
        return (post_url, post_data)

    def _handle_URL(self, command):
        tr_id = command.transaction_id
        if tr_id in self._callbacks:
            message_url, post_url, post_id = command.arguments
            post_url, form_dict = self._build_url_post_data(message_url,
                                                            post_url, post_id)
            self._command_answered_cb(tr_id, post_url, form_dict)

    # --------- Invitation ---------------------------------------------------
    def _handle_RNG(self, command):
        session_id = command.arguments[0]
        host, port = command.arguments[1].split(':', 1)
        port = int(port)
        key = command.arguments[3]
        account = command.arguments[4]
        display_name = urllib.unquote(command.arguments[5])

        session = ((host, port), session_id, key)
        inviter = (account, display_name)
        self.emit("switchboard-invitation-received", session, inviter)

    # --------- Challenge ----------------------------------------------------
    def _handle_QRY(self, command):
        pass

    def _handle_CHL(self, command):
        response = _msn_challenge(command.arguments[0])
        self._send_command('QRY',
                (ProtocolConstant.PRODUCT_ID,), payload=response)

    # --------- Notification -------------------------------------------------
    def _handle_NOT(self, command):
        notification_xml = xml_utils.unescape(command.payload)
        notification = ElementTree.fromstring(notification_xml)

        service = notification.findtext('MSG/BODY/NotificationData/Service')
        if service != 'ABCHInternal':
            return

        try:
            notification_id = notification.attrib['id']
            site_id = notification.attrib['siteid']
            message_id = notification.find('MSG').attrib['id']
            send_device = notification.find('TO/VIA').attrib['agent']
            receiver_cid = notification.findtext('MSG/BODY/NotificationData/CID')
            receiver_account = notification.find('TO').attrib['name'].lower()

            if notification_id != '0' or site_id != '45705' \
            or message_id != '0' or send_device != 'messenger' \
            or receiver_cid != str(self._client.profile.cid)  \
            or receiver_account != self._client.profile.account.lower():
                return

        except KeyError:
            return

        self._client.address_book.sync(True)

    #---------- Errors -------------------------------------------------------
    def _error_handler(self, error):
        logger.error('Notification got error : ' + unicode(error))
        self._command_error_cb(error.transaction_id, int(error.name))


    # callbacks --------------------------------------------------------------
    def _connect_cb(self, transport):
        self.__switchboard_callbacks = PriorityQueue()
        self._state = ProtocolState.OPENING
        versions = []
        for version in ProtocolConstant.VER:
            if version <= self._protocol_version:
                versions.append("MSNP%i" % version)
        self._send_command('VER', versions)

    def _disconnect_cb(self, transport, reason):
        self.stop_all_timeout()
        self._state = ProtocolState.CLOSED

    def _sso_cb(self, tokens, nonce):
        if self._state != ProtocolState.AUTHENTICATING:
            return

        clear_token = tokens[SSO.LiveService.MESSENGER_CLEAR]
        token = clear_token.security_token
        blob = clear_token.mbi_crypt(nonce)
        if self._protocol_version >= 16:
            arguments = ("SSO", "S", token, blob, "{%s}" %
                    str(self._client.machine_guid).upper())
        else:
            arguments = ("SSO", "S", token, blob)

        self._send_command("USR", arguments)

    def on_ping_timeout(self):
        self._transport.enable_ping()

    def on_qing_timeout(self, time_id):
        if self._time_id == time_id:
            self._transport.emit("connection-lost", "Ping timeout")

    def _command_answered_cb(self, tr_id, *args):
        callback, errback = self._callbacks.get(tr_id, (None, None))
        run(callback, *args)

    def _command_error_cb(self, tr_id, error):
        callback, errback = self._callbacks.get(tr_id, (None, None))
        run(errback, error)

    def _address_book_state_changed_cb(self, address_book, pspec):
        MAX_PAYLOAD_SIZE = 7500
        if self._state != ProtocolState.SYNCHRONIZING:
            return
        if address_book.state != AB.AddressBookState.SYNCHRONIZED:
            return
        self._client.profile._cid = address_book.profile._cid
        self._client.profile._server_property_changed("display-name",
                address_book.profile.display_name)

        contacts = address_book.contacts.group_by_domain()
        mask = ~(profile.Membership.REVERSE | profile.Membership.PENDING)

        for contact in address_book.contacts:
            if (contact.memberships & mask & ~profile.Membership.FORWARD) == \
                    (profile.Membership.ALLOW | profile.Membership.BLOCK):
                logger.warning("Contact is on both Allow and Block list; " \
                               "removing from Allow list (%s)" % contact.account)
                contact._remove_membership(profile.Membership.ALLOW)

        payloads = ['<ml l="1">']
        for domain, contacts in contacts.iteritems():
            payloads[-1] += '<d n="%s">' % domain
            for contact in contacts:
                user = contact.account.split("@", 1)[0]
                lists = contact.memberships & mask
                if lists == profile.Membership.NONE:
                    continue
                network_id = contact.network_id
                node = '<c n="%s" l="%d" t="%d"/>' % (user, lists, network_id)
                size = len(payloads[-1]) + len(node) + len('</d></ml>')
                if size >= MAX_PAYLOAD_SIZE:
                    payloads[-1] += '</d></ml>'
                    payloads.append('<ml l="1"><d n="%s">' % domain)
                payloads[-1] += node
            payloads[-1] += '</d>'
        payloads[-1] += '</ml>'

        import re
        pattern = re.compile ('<d n="[^"]+"></d>')
        for payload in payloads:
            payload = pattern.sub('', payload)
            self._send_command("ADL", payload=payload)
        self._state = ProtocolState.SYNCHRONIZED

    def _add_contact_to_membership(self, contact, membership):
        self.add_contact_to_membership(contact.account, contact.network_id,
                membership)

    def _remove_contact_from_membership(self, contact, membership):
        self.remove_contact_from_membership(contact.account,
                contact.network_id, membership)

    def _address_book_contact_added_cb(self, address_book, contact):
        if contact.is_member(profile.Membership.ALLOW):
            self._add_contact_to_membership(contact, profile.Membership.ALLOW)
        self._add_contact_to_membership(contact, profile.Membership.FORWARD)

        if contact.network_id != profile.NetworkID.MOBILE:
            account, domain = contact.account.split('@', 1)
            payload = '<ml l="2"><d n="%s"><c n="%s"/></d></ml>' % \
                    (domain, account)
            self._send_command("FQY", payload=payload)

    def _address_book_contact_deleted_cb(self, address_book, contact):
        self._remove_contact_from_membership(contact, profile.Membership.FORWARD)

    def _address_book_contact_accepted_cb(self, address_book, contact):
        mask = ~(profile.Membership.REVERSE | profile.Membership.PENDING)
        memberships = contact.memberships & mask
        if memberships:
            self._add_contact_to_membership(contact, memberships)

    def _address_book_contact_rejected_cb(self, address_book, contact):
        mask = ~(profile.Membership.REVERSE | profile.Membership.PENDING)
        memberships = contact.memberships & mask
        if memberships:
            self._add_contact_to_membership(contact, memberships)

    def _address_book_contact_blocked_cb(self, address_book, contact):
        self._remove_contact_from_membership(contact, profile.Membership.ALLOW)
        self._add_contact_to_membership(contact, profile.Membership.BLOCK)

    def _address_book_contact_unblocked_cb(self, address_book, contact):
        self._remove_contact_from_membership(contact, profile.Membership.BLOCK)
        self._add_contact_to_membership(contact, profile.Membership.ALLOW)

    def _address_book_contact_allowed_cb(self, address_book, contact):
        self._add_contact_to_membership(contact, profile.Membership.ALLOW)

    def _address_book_contact_disallowed_cb(self, address_book, contact):
        self._remove_contact_from_membership(contact, profile.Membership.ALLOW)
