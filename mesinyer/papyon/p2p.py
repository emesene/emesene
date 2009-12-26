# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2007 Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2007 Johann Prieur <johann.prieur@gmail.com>
# Copyright (C) 2008 Richard Spiers <richard.spiers@gmail.com>
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

"""P2P
This module contains the classes needed to engage in a peer to peer transfer
with a contact.
    @group MSNObject: MSNObjectStore, MSNObject, MSNObjectType
    @sort: MSNObjectStore, MSNObject, MSNObjectType"""
from msnp2p.msnobject import MSNObjectSession
from msnp2p.webcam import WebcamSession
from msnp2p import EufGuid, ApplicationID
from msnp2p.exceptions import ParseError
from profile import NetworkID, Contact, Profile

import papyon.util.element_tree as ElementTree
import papyon.util.string_io as StringIO

import gobject
import xml.sax.saxutils as xml
import urllib
import base64
import hashlib
import logging

__all__ = ['MSNObjectType', 'MSNObject', 'MSNObjectStore', 'WebcamHandler']

logger = logging.getLogger('papyon.p2p')

class MSNObjectType(object):
    """Represent the various MSNObject types"""

    CUSTOM_EMOTICON = 2
    "Custom smiley"
    DISPLAY_PICTURE = 3
    "Display picture"
    BACKGROUND_PICTURE = 5
    "Background picture"
    DYNAMIC_DISPLAY_PICTURE = 7
    "Dynamic display picture"
    WINK = 8
    "Wink"
    VOICE_CLIP = 11
    "Void clip"
    SAVED_STATE_PROPERTY = 12
    "Saved state property"
    LOCATION = 14
    "Location"

class MSNObject(object):
    "Represents an MSNObject."
    def __init__(self, creator, size, typ, location, friendly,
                 shad=None, shac=None, data=None):
        """Initializer

            @param creator: the creator of this MSNObject
            @type creator: utf-8 encoded string representing the account

            @param size: the total size of the data represented by this MSNObject
            @type size: int

            @param typ: the type of the data
            @type typ: L{MSNObjectType}

            @param location: a filename for the MSNObject
            @type location: utf-8 encoded string

            @param friendly: a friendly name for the MSNObject
            @type friendly: utf-8 encoded string

            @param shad: sha1 digest of the data

            @param shac: sha1 digest of the MSNObject itself

            @param data: file object to the data represented by this MSNObject
            @type data: File
        """
        # Backward compatible with older clients that pass a Contact/Profile
        if type(creator) is Contact or type(creator) is Profile:
            creator = creator.account
        self._creator = creator
        self._size = size
        self._type = typ
        self._location = location
        self._friendly = friendly

        if shad is None:
            if data is None:
                raise NotImplementedError
            shad = self.__compute_data_hash(data)
        self._data_sha = shad
        self.__data = data
        if shac is None:
            shac = self.__compute_checksum()
        self._checksum_sha = shac
        self._repr = None

    def __ne__(self, other):
        return not (self == other)

    def __eq__(self, other):
        if other == None:
            return False
        return other._type == self._type and \
            other._data_sha == self._data_sha

    def __hash__(self):
        return hash(str(self._type) + self._data_sha)

    def __set_data(self, data):
        if self._data_sha != self.__compute_data_hash(data):
            logger.warning("Received data doesn't match the MSNObject data hash.")
            return

        old_pos = data.tell()
        data.seek(0, 2)
        self._size = data.tell()
        data.seek(old_pos, 0)

        self.__data = data
        self._checksum_sha = self.__compute_checksum()
    def __get_data(self):
        return self.__data
    _data = property(__get_data, __set_data)

    @staticmethod
    def parse(client, xml_data):
        data = StringIO.StringIO(xml_data)
        try:
            element = ElementTree.parse(data).getroot().attrib
        except:
            raise ParseError('Invalid MSNObject')

        creator = element["Creator"]
        size = int(element["Size"])
        type = int(element["Type"])
        location = xml.unescape(element["Location"])
        friendly = base64.b64decode(xml.unescape(element["Friendly"]))
        shad = element.get("SHA1D", None)
        if shad is not None:
            shad = base64.b64decode(shad)
        shac = element.get("SHA1C", None)
        if shac is not None:
            shac = base64.b64decode(shac)

        result = MSNObject(creator, size, type, location, friendly, shad, shac)
        result._repr = xml_data
        return result

    def __compute_data_hash(self, data):
        digest = hashlib.sha1()
        data.seek(0, 0)
        read_data = data.read(1024)
        while len(read_data) > 0:
            digest.update(read_data)
            read_data = data.read(1024)
        data.seek(0, 0)
        return digest.digest()

    def __compute_checksum(self):
        input = "Creator%sSize%sType%sLocation%sFriendly%sSHA1D%s" % \
            (self._creator, str(self._size), str(self._type),\
                 str(self._location), base64.b64encode(self._friendly), \
                 base64.b64encode(self._data_sha))
        return hashlib.sha1(input).hexdigest()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        if self._repr is not None:
            return self._repr
        dump = "<msnobj Creator=%s Type=%s SHA1D=%s Size=%s Location=%s Friendly=%s/>" % \
            (xml.quoteattr(self._creator),
                xml.quoteattr(str(self._type)),
                xml.quoteattr(base64.b64encode(self._data_sha)),
                xml.quoteattr(str(self._size)),
                xml.quoteattr(str(self._location)),
                xml.quoteattr(base64.b64encode(self._friendly)))
        return dump


class MSNObjectStore(object):

    def __init__(self, client):
        self._client = client
        self._outgoing_sessions = {} # session => (handle_id, callback, errback)
        self._incoming_sessions = {}
        self._published_objects = set()

    def _can_handle_message (self, message):
        euf_guid = message.body.euf_guid
        if euf_guid == EufGuid.MSN_OBJECT:
            return True
        else:
            return False

    def _handle_message(self, peer, message):
        session = MSNObjectSession(self._client._p2p_session_manager,
                peer, message.body.application_id, message)

        handle_id = session.connect("completed",
                        self._incoming_session_transfer_completed)
        self._incoming_sessions[session] = handle_id
        try:
            msn_object = MSNObject.parse(self._client, session._context)
        except ParseError:
            session.reject()
            return
        for obj in self._published_objects:
            if obj._data_sha == msn_object._data_sha:
                session.accept(obj._data)
                return session
        session.reject()

    def request(self, msn_object, callback, errback=None, peer=None):
        if msn_object._data is not None:
            callback[0](msn_object, *callback[1:])

        if peer is None:
            peer = self._client.address_book.search_contact(msn_object._creator,
                    NetworkID.MSN)

        if msn_object._type == MSNObjectType.CUSTOM_EMOTICON:
            application_id = ApplicationID.CUSTOM_EMOTICON_TRANSFER
        elif msn_object._type == MSNObjectType.DISPLAY_PICTURE:
            application_id = ApplicationID.DISPLAY_PICTURE_TRANSFER
        else:
            raise NotImplementedError

        session = MSNObjectSession(self._client._p2p_session_manager,
                peer, application_id)
        handle_id = session.connect("completed",
                self._outgoing_session_transfer_completed)
        self._outgoing_sessions[session] = \
                (handle_id, callback, errback, msn_object)
        session.invite(repr(msn_object))

    def publish(self, msn_object):
        if msn_object._data is None:
            logger.warning("Trying to publish an empty MSNObject")
        else:
            self._published_objects.add(msn_object)

    def _outgoing_session_transfer_completed(self, session, data):
        handle_id, callback, errback, msn_object = self._outgoing_sessions[session]
        session.disconnect(handle_id)
        msn_object._data = data

        callback[0](msn_object, *callback[1:])
        del self._outgoing_sessions[session]

    def _incoming_session_transfer_completed(self, session, data):
        handle_id = self._incoming_sessions[session]
        session.disconnect(handle_id)
        del self._incoming_sessions[session]

class WebcamHandler(gobject.GObject):

    __gsignals__ = {
            "session-created" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object, bool))
    }

    def __init__(self, client):
        gobject.GObject.__init__(self)
        self._client = client
        self._sessions = []

    def _can_handle_message (self, message):
        euf_guid = message.body.euf_guid
        if (euf_guid == EufGuid.MEDIA_SESSION or
            euf_guid == EufGuid.MEDIA_RECEIVE_ONLY):
            return True
        else:
            return False

    def _handle_message (self, peer, message):
        euf_guid = message.body.euf_guid
        if (euf_guid == EufGuid.MEDIA_SESSION):
            producer = False
        elif (euf_guid == EufGuid.MEDIA_RECEIVE_ONLY):
            producer = True

        session = WebcamSession(producer, self._client._p2p_session_manager, \
                                    peer, message.body.euf_guid, message)
        self._sessions.append(session)
        self.emit("session-created", session, producer)
        return session

    def invite(self, peer, producer=True):
        print "Creating New Send Session"
        if producer:
            euf_guid = EufGuid.MEDIA_SESSION
        else:
            euf_guid = EufGuid.MEDIA_RECEIVE_ONLY
        session = WebcamSession(producer, self._client._p2p_session_manager, \
                                    peer, euf_guid)
        self._sessions.append(session)
        session.invite()
        return session
