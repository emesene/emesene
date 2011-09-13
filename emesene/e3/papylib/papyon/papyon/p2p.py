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
from msnp2p.filetransfer import FileTransferSession
from msnp2p.msnobject import MSNObjectSession
from msnp2p.webcam import WebcamSession
from msnp2p import EufGuid, ApplicationID
from msnp2p.constants import SLPStatus
from msnp2p.errors import P2PError, MSNObjectParseError
from profile import NetworkID, BaseContact, Contact, Profile

from papyon.util.async import *
from papyon.util.encoding import b64_decode
import papyon.util.element_tree as ElementTree
import papyon.util.string_io as StringIO

import gobject
import xml.sax.saxutils as xml
import urllib
import base64
import hashlib
import logging
import os

__all__ = ['MSNObjectType', 'MSNObject', 'MSNObjectStore',
           'FileTransferManager', 'WebcamHandler']

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
        if isinstance(creator, BaseContact):
            creator = creator.account
        self._creator = creator
        self._size = size
        self._type = typ
        self._location = location
        self._friendly = friendly

        if shad is None:
            if data is None:
                raise ValueError
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
            other._data_sha == self._data_sha and \
            other._checksum_sha == self._checksum_sha

    def __hash__(self):
        return hash(str(self._type) + self._data_sha)

    def __set_data(self, data):
        if self._data_sha != self.__compute_data_hash(data):
            logger.warning("Received data doesn't match the MSNObject data hash.")
            return

        old_pos = data.tell()
        data.seek(0, os.SEEK_END)
        self._size = data.tell()
        data.seek(old_pos, os.SEEK_SET)

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
            raise MSNObjectParseError(xml_data)

        creator = element["Creator"]
        size = int(element["Size"])
        type = int(element["Type"])

        if "Location" in element:
            location = xml.unescape(element["Location"])
        else:
            location = "0"

        if "Friendly" in element:
            friendly = b64_decode(xml.unescape(element["Friendly"]))
        else:
            friendly = '\x00\x00'

        shad = element.get("SHA1D", None)
        if shad is not None:
            try:
                shad = b64_decode(shad)
            except TypeError:
                logger.warning("Invalid SHA1D in MSNObject: %s" % shad)
                shad = None

        shac = element.get("SHA1C", None)
        if shac is not None:
            try:
                shac = b64_decode(shac)
            except TypeError:
                logger.warning("Invalid SHA1C in MSNObject: %s" % shac)
                shac = None

        try:
            result = MSNObject(creator, size, type, location, friendly, shad, shac)
            result._repr = xml_data
        except ValueError:
            raise MSNObjectParseError(xml_data)

        return result

    def __compute_data_hash(self, data):
        digest = hashlib.sha1()
        data.seek(0, os.SEEK_SET)
        read_data = data.read(1024)
        while len(read_data) > 0:
            digest.update(read_data)
            read_data = data.read(1024)
        data.seek(0, os.SEEK_SET)
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


class P2PSessionHandler(gobject.GObject):

    def __init__(self, client):
        gobject.GObject.__init__(self)
        self._client = client
        self._sessions = []
        self._handles = {} # session : handles

    def _add_session(self, session):
        self._connect_session(session)
        self._sessions.append(session)

    def _connect_session(self, session):
        handles = []
        handles.append(session.connect("disposed", self._on_session_disposed))
        self._handles[session] = handles

    def _disconnect_session(self, session):
        handles = self._handles.pop(session)
        for handle_id in handles:
            session.disconnect(handle_id)

    def _on_session_disposed(self, session):
        self._disconnect_session(session)
        self._sessions.remove(session)

    def _can_handle_message (self, message):
        raise NotImplementedError

    def _handle_message(self, peer, guid, message):
        raise NotImplementedError


class MSNObjectStore(P2PSessionHandler):
    """Stores published MSN objects.

       Peer requests are automatically accepted and the requested object is
       sent to them. This class also gives the interface to request objects
       from peers and should be called when a contact changes his display
       picture or sends a custom emoticon.

       @note Objects retrieved from peers aren't cached. Clients that use
             papyon must keep them in memory and ideally on the file system as
             well so they aren't requested too often."""

    def __init__(self, client):
        P2PSessionHandler.__init__(self, client)
        self._callbacks = {} # session => (callback, errback, msn_object)
        self._published_objects = set()

    def _get_published_object(self, msn_object):
        if msn_object is None:
            return None
        for obj in self._published_objects:
            if obj._data_sha == msn_object._data_sha:
                return obj
        return None

    def _can_handle_message (self, message):
        euf_guid = message.body.euf_guid
        if euf_guid == EufGuid.MSN_OBJECT:
            return True
        else:
            return False

    def _handle_message(self, peer, guid, message):
        session = MSNObjectSession(self._client._p2p_session_manager,
                peer, guid, message.body.application_id, message)
        try:
            msn_object = MSNObject.parse(self._client, session.context)
        except Exception, err:
            session.reject()
            raise err

        obj = self._get_published_object(msn_object)
        if obj is None:
            logger.warning("Unknown MSN object, another end point might have it")
            return

        self._add_session(session)
        self._callbacks[session] = (None, None, msn_object)
        session.accept(obj._data)
        return session

    def _connect_session(self, session):
        P2PSessionHandler._connect_session(self, session)
        self._handles[session].append(session.connect("completed",
            self._on_session_completed))
        self._handles[session].append(session.connect("rejected",
            self._on_session_rejected))

    def _on_session_completed(self, session, data):
        if session in self._callbacks:
            callback, errback, msn_object = self._callbacks[session]
            msn_object._data = data
            run(callback, msn_object)

    def _on_session_rejected(self, session):
        if session in self._callbacks:
            callback, errback, msn_object = self._callbacks[session]
            run(errback, P2PError("Request for %s was rejected" % msn_object))

    def _on_session_disposed(self, session):
        P2PSessionHandler._on_session_disposed(self, session)
        if session in self._callbacks:
            del self._callbacks[session]

    ### Public API -----------------------------------------------------------

    def request(self, msn_object, callback, errback=None, peer=None):
        """Request a MSN object from a peer.

           A session invite will be sent to each peer endpoint. When one is
           accepted, other requests are canceled.

           @param msn_object: MSN Object to retrieve
           @type msn_object: L{MSNObject<papyon.p2p.MSNObject>}
           @param callback: method called once the object is retrieved
           @type callback: tuple(method, *args)
           @param errback: method called if an error occured
           @type errback: typle(method, *args)
           @param peer: peer owning the MSN object
           @type peer: L{Contact<papyon.profile.Contact>}

           @raise NotImplementedError: if object's type is not supported"""

        if msn_object is None:
            logger.warning("Requested MSN object is 'None'")
            return

        obj = self._get_published_object(msn_object)
        if obj is not None:
            msn_object._data = obj._data
        if msn_object._data is not None:
            run(callback, msn_object)
            return

        if peer is None:
            logger.warning("Deprecated: Using MSNObject creator to guess peer")
            peer = self._client.address_book.search_contact(msn_object._creator,
                    NetworkID.MSN)
            if peer is None:
                logger.error("MSN Object creator is not in address book")
                return

        if msn_object._type == MSNObjectType.CUSTOM_EMOTICON:
            app_id = ApplicationID.CUSTOM_EMOTICON_TRANSFER
        elif msn_object._type == MSNObjectType.DISPLAY_PICTURE:
            app_id = ApplicationID.DISPLAY_PICTURE_TRANSFER
        else:
            logger.error("MSN Object type '%i' is not implemented" %
                    (msn_object._type))
            raise NotImplementedError

        context = repr(msn_object)
        session = MSNObjectMetaSession(self._client, peer, app_id, context)
        self._add_session(session)
        self._callbacks[session] = (callback, errback, msn_object)
        logger.info("Requesting a MSNObject from %s (%i end points)" %
                (peer.account, session.count))
        session.invite()

    def publish(self, msn_object):
        """Publish a MSN object that can be requested by peers.

           @param msn_object: MSN Object to publish
           @type msn_object: L{MSNObject<papyon.p2p.MSNObject>}"""

        if msn_object._data is None:
            logger.warning("Trying to publish an empty MSNObject")
        else:
            self._published_objects.add(msn_object)

    ### ----------------------------------------------------------------------


class FileTransferManager(P2PSessionHandler):
    """Manages the file transfer P2P sessions.

       The signal on_invite_file_transfer is dispatched by the
       L{Client<papyon.Client} when an invite is received."""

    __gsignals__ = {
            "transfer-requested" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,))
    }

    def __init__(self, client):
        P2PSessionHandler.__init__(self, client)

    def _can_handle_message(self, message):
        euf_guid = message.body.euf_guid
        return (euf_guid == EufGuid.FILE_TRANSFER)

    def _handle_message(self, peer, guid, message):
        session = FileTransferSession(self._client._p2p_session_manager,
                peer, guid, message)

        try:
            session.parse_context(message.body.context)
        except Exception, err:
            session.reject()
            raise err

        self._add_session(session)
        self.emit("transfer-requested", session)
        return session

    ### Public API -----------------------------------------------------------

    def send(self, peer, filename, size, data=None, preview=None):
        """Send a request to start sending a file.

           The request is sent to each peer endpoint and we keep only the
           first P2P session that get accepted. If any invite is rejected, all
           the sessions are canceled as well.

           @param peer: Peer to who the file is sent
           @type peer: L{Contact<papyon.profile.Contact>}
           @param filename: Name of the file
           @type filename: utf-8 encoded string
           @param size: Size of file content
           @type size: int
           @param data: Data to send once session is accepted
           @type data: str or file-like object
           @param preview: Preview data to send with the invitation
           @type data: string
           
           @returns the meta session created to handle the invite."""

        session = FileTransferMetaSession(self._client, peer)
        self._add_session(session)
        session.invite(filename, size, data, preview)
        return session

    ### ----------------------------------------------------------------------


class WebcamHandler(P2PSessionHandler):

    __gsignals__ = {
            "session-created" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object, bool))
    }

    def __init__(self, client):
        P2PSessionHandler.__init__(self, client)

    def _can_handle_message (self, message):
        euf_guid = message.body.euf_guid
        if (euf_guid == EufGuid.MEDIA_SESSION or
            euf_guid == EufGuid.MEDIA_RECEIVE_ONLY):
            return True
        else:
            return False

    def _handle_message (self, peer, guid, message):
        euf_guid = message.body.euf_guid
        if (euf_guid == EufGuid.MEDIA_SESSION):
            producer = False
        elif (euf_guid == EufGuid.MEDIA_RECEIVE_ONLY):
            producer = True

        session = WebcamSession(producer, self._client._p2p_session_manager, \
                                    peer, guid, message.body.euf_guid, message)
        self._add_session(session)
        self.emit("session-created", session, producer)
        return session

    ### Public API -----------------------------------------------------------

    def invite(self, peer, producer=True):
        """Invite a contact for a uni-directionnal webcam session.

           @param producer: if true, we want to send webcam
           @type producer: boolean

           @returns the meta session created to handle the invite."""

        session = WebcamMetaSession(self._client, peer, producer)
        self._add_session(session)
        session.invite()
        return session

    ### ----------------------------------------------------------------------


class P2PMetaSession(gobject.GObject):
    """ A P2PMetaSession is used to wrap multiple outgoing p2p sessions
        together. This way, we can send an invite to each end point of a peer
        and still have only one session object for methods and signals. """

    __gsignals__ = {
            "accepted" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),
            "rejected" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ()),
            "completed" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            "progressed" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                (object,)),
            "disposed" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ())
    }

    def __init__(self, client, peer, *args):
        gobject.GObject.__init__(self)
        self._sessions = []
        self._handles = {}

        if len(peer.end_points) == 0:
            session = self._create_session(client, peer, None, *args)
            self._add_session(session)
        for end_point in peer.end_points.values():
            if peer == client.profile and end_point.id == client.machine_guid:
                continue
            session = self._create_session(client, peer, end_point.id, *args)
            self._add_session(session)

    @property
    def session(self):
        if len(self._sessions) > 0:
            return self._sessions[0]
        return None

    @property
    def count(self):
        return len(self._sessions)

    def __getattr__(self, name):
        if self.session:
            return getattr(self.session, name)
        raise AttributeError

    def _connect_session(self, session):
        handles = []
        handles.append(session.connect("accepted",
            self._on_session_accepted))
        handles.append(session.connect("rejected",
            self._on_session_rejected))
        handles.append(session.connect("completed",
            self._on_session_completed))
        handles.append(session.connect("progressed",
            self._on_session_progressed))
        handles.append(session.connect("disposed",
            self._on_session_disposed))
        self._handles[session] = handles

    def _disconnect_session(self, session):
        handles = self._handles.pop(session, [])
        for handle in handles:
            session.disconnect(handle)

    def _add_session(self, session):
        if session is None:
            return
        self._connect_session(session)
        self._sessions.append(session)

    def _remove_all(self):
        for session in self._sessions:
            self._disconnect_session(session)
        self._sessions = []

    def _cancel_all(self):
        sessions = self._sessions[:]
        self._remove_all()
        for session in sessions:
            self._cancel_session(session)

    def _keep_session(self, session_to_keep):
        if session_to_keep not in self._sessions:
            return False
        logger.info("Keeping only session %s in meta session" %
                session_to_keep.id)
        self._sessions.remove(session_to_keep)
        handles = self._handles.pop(session_to_keep)
        self._cancel_all()
        self._sessions = [session_to_keep]
        self._handles[session_to_keep] = handles

    def _on_session_accepted(self, session):
        self._keep_session(session)
        self.emit("accepted")

    def _on_session_rejected(self, session):
        self._keep_session(session)
        self.emit("rejected")

    def _on_session_completed(self, session, data):
        self.emit("completed", data)

    def _on_session_progressed(self, session, data):
        self.emit("progressed", data)

    def _on_session_disposed(self, disposed_session):
        self._remove_all()
        self.emit("disposed")


class FileTransferMetaSession(P2PMetaSession):

    __gsignals__ = {
            "canceled" : (gobject.SIGNAL_RUN_FIRST,
                gobject.TYPE_NONE,
                ())
    }

    def __init__(self, client, peer):
        P2PMetaSession.__init__(self, client, peer)

    def _create_session(self, client, peer, guid):
        session = FileTransferSession(client._p2p_session_manager, peer, guid)
        return session

    def _connect_session(self, session):
        P2PMetaSession._connect_session(self, session)
        self._handles[session].append(session.connect("canceled",
            self._on_session_canceled))

    def _cancel_session(self, session):
        session.cancel()

    def _on_session_canceled(self, canceled_session):
        self.emit("canceled")

    def invite(self, filename, size, data, preview):
        for session in self._sessions:
            session.invite(filename, size, data, preview)

    def cancel(self):
        for session in self._sessions:
            session.cancel()


class MSNObjectMetaSession(P2PMetaSession):

    def __init__(self, client, peer, application_id, context):
        P2PMetaSession.__init__(self, client, peer, application_id, context)

    def _create_session(self, client, peer, guid, application_id, context):
        session = MSNObjectSession(client._p2p_session_manager, peer, guid,
                application_id, context=context)
        return session

    def _cancel_session(self, session):
        session.cancel()

    def invite(self):
        for session in self._sessions:
            session.invite()

    def cancel(self):
        for session in self._sessions:
            session.cancel()


class WebcamMetaSession(P2PMetaSession):

    def __init__(self, client, peer, producer):
        P2PMetaSession.__init__(self, client, peer, producer)

    def _create_session(self, client, peer, guid, producer):
        if guid and peer.end_points[guid]:
            has_webcam = peer.end_points[guid].capabilities.has_webcam
            if not producer and not has_webcam:
                return None

        if producer:
            euf_guid = EufGuid.MEDIA_SESSION
        else:
            euf_guid = EufGuid.MEDIA_RECEIVE_ONLY

        session = WebcamSession(client._p2p_session_manager, peer, guid,
                producer, euf_guid)
        return session

    def _cancel_session(self, session):
        session.end()

    def invite(self):
        for session in self._sessions:
            session.invite()

    def end(self, reason=None):
        for session in self._sessions:
            session.end(reason)
