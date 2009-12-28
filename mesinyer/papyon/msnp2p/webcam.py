# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2007 Ali Sabil <ali.sabil@gmail.com>
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

from papyon.msnp2p.constants import *
from papyon.msnp2p.SLP import *
from papyon.msnp2p.transport import *
from papyon.msnp2p.exceptions import *
from papyon.msnp2p.session import P2PSession
from papyon.event import EventsDispatcher
from papyon.util.decorator import rw_property
import papyon.util.element_tree as ElementTree
import struct

import gobject
import logging
import base64
import random

from papyon.media import MediaCall, MediaCandidate, MediaCandidateEncoder, \
                         MediaSessionMessage, MediaStreamDescription
from papyon.media.constants import MediaStreamDirection, MediaSessionType

__all__ = ['WebcamSession']

logger = logging.getLogger("papyon.msnp2p.webcam")

class WebcamSession(P2PSession, MediaCall, EventsDispatcher):

    def __init__(self, producer, session_manager, peer,
            euf_guid,  message=None):
        if producer:
            type = MediaSessionType.WEBCAM_SEND
        else:
            type = MediaSessionType.WEBCAM_RECV

        P2PSession.__init__(self, session_manager, peer, euf_guid,
                ApplicationID.WEBCAM, message)
        MediaCall.__init__(self, type)
        EventsDispatcher.__init__(self)

        self._producer = producer
        self._answered = False
        self._sent_syn = False
        self._session_id = self._generate_id(9999)
        self._xml_needed = False

    def invite(self):
        self._answered = True
        context = "{B8BE70DE-E2CA-4400-AE03-88FF85B9F4E8}"
        context = context.decode('ascii').encode('utf-16_le')
        self._invite(context)

    def accept(self):
        self._answered = True
        temp_application_id = self._application_id
        self._application_id = 0
        self._respond(200)
        self._application_id = temp_application_id
        self.send_binary_syn()

    def reject(self):
        self._answered = True
        self._respond(603)

    def end(self):
        if not self._answered:
            self.reject()
        else:
            context = '\x74\x03\x00\x81'
            self._close(context)
        self.dispose()

    def dispose(self):
        MediaCall.dispose(self)
        self._dispatch("on_call_ended")
        self._dispose()

    def on_media_session_prepared(self, session):
        if self._xml_needed:
            self._send_xml()

    def _on_invite_received(self, message):
        if self._producer:
            stream = self.media_session.create_stream("video",
                    MediaStreamDirection.SENDING, False)
            self.media_session.add_stream(stream)

    def _on_bye_received(self, message):
        self.dispose()

    def _on_session_accepted(self):
        self._dispatch("on_call_accepted")

    def _on_session_rejected(self, message):
        self._dispatch("on_call_rejected", message)

    def _on_data_blob_received(self, blob):
        blob.data.seek(0, 0)
        data = blob.data.read()
        data = unicode(data[10:], "utf-16-le").rstrip("\x00")

        if not self._sent_syn:
            self.send_binary_syn() #Send 603 first ?
        if data == 'syn':
            self.send_binary_ack()
        elif data == 'ack' and self._producer:
            self._send_xml()
        elif '<producer>' in data or '<viewer>' in data:
            self._handle_xml(data)
        elif data.startswith('ReflData'):
            refldata = data.split(':')[1]
            str = ""
            for i in range(0, len(refldata), 2):
                str += chr(int(refldata[i:i+2], 16))
            print "Got ReflData :", str

    def send_data(self, data):
        message_bytes = data.encode("utf-16-le") + "\x00\x00"
        id = (self._generate_id() << 8) | 0x80
        header = struct.pack("<LHL", id, 8, len(message_bytes))
        self._send_p2p_data(header + message_bytes)

    def send_binary_syn(self):
        self.send_data('syn')
        self._sent_syn = True

    def send_binary_ack(self):
        self.send_data('ack')

    def send_binary_viewer_data(self):
        self.send_data('receivedViewerData')

    def _send_xml(self):
        if not self.media_session.prepared:
            self._xml_needed = True
            return
        logger.info("Send XML for session %i", self._session_id)
        self._xml_needed = False
        message = WebcamSessionMessage(session=self.media_session,
                id=self._session_id, producer=self._producer)
        self.send_data(str(message))

    def _handle_xml(self, data):
        message = WebcamSessionMessage(body=data, producer=self._producer)
        initial = not self._producer
        self.media_session.process_remote_message(message, initial)
        self._session_id = message.id
        logger.info("Received XML data for session %i", self._session_id)
        if self._producer:
            self.send_binary_viewer_data()
        else:
            self._send_xml()

class WebcamCandidateEncoder(MediaCandidateEncoder):

    def __init__(self):
        MediaCandidateEncoder.__init__(self)

    def encode_candidates(self, desc, local_candidates, remote_candidates):
        for candidate in local_candidates:
            desc.ips.append(candidate.ip)
            desc.ports.append(candidate.port)
        desc.rid = int(local_candidates[0].foundation)
        desc.sid = int(local_candidates[0].username)

    def decode_candidates(self, desc):
        local_candidates = []
        remote_candidate = []

        for ip in desc.ips:
            for port in desc.ports:
                candidate = MediaCandidate()
                candidate.foundation = str(desc.rid)
                candidate.component_id = 1
                candidate.username = str(desc.sid)
                candidate.password = ""
                candidate.ip = ip
                candidate.port = port
                candidate.transport = "TCP"
                candidate.priority = 1
                local_candidates.append(candidate)

        return local_candidates, remote_candidate


class WebcamSessionMessage(MediaSessionMessage):

    def __init__(self, session=None, body=None, id=0, producer=False):
        self._id = id
        self._producer = producer
        MediaSessionMessage.__init__(self, session, body)

    @property
    def id(self):
        return self._id

    @property
    def producer(self):
        return self._producer

    def _create_stream_description(self, stream):
        return WebcamStreamDescription(stream, self._id, self._producer)

    def _parse(self, body):
        tree = ElementTree.fromstring(body)
        self._id = int(tree.find("session").text)
        desc = self._create_stream_description(None)
        self.descriptions.append(desc)
        for node in tree.findall("tcp/*"):
            if node.tag == "tcpport":
                desc.ports.append(int(node.text))
            elif node.tag.startswith("tcpipaddress"):
                desc.ips.append(node.text)
        desc.rid = tree.find("rid").text
        return self._descriptions

    def __str__(self):
        tag = self.producer and "producer" or "viewer"
        desc = self._descriptions[0]
        body = "<%s>" \
            "<version>2.0</version>" \
            "<rid>%s</rid>" \
            "<session>%u</session>" \
            "<ctypes>0</ctypes>" \
            "<cpu>2010</cpu>" % (tag, desc.rid, desc.sid)
        body += "<tcp>" \
            "<tcpport>%(port)u</tcpport>" \
            "<tcplocalport>%(port)u</tcplocalport>" \
            "<tcpexternalport>0</tcpexternalport>" % \
            {"port":  desc.ports[0]}
        for i, addr in enumerate(desc.ips):
            body += "<tcpipaddress%u>%s</tcpipaddress%u>" % (i + 1, addr, i + 1)
        body += "</tcp>"
        body += "<codec></codec><channelmode>2</channelmode>"
        body += "</%s>\r\n\r\n" % tag
        return body

class WebcamStreamDescription(MediaStreamDescription):

    _candidate_encoder = WebcamCandidateEncoder()

    def __init__(self, stream, sid, producer):
        direction = producer and MediaStreamDirection.SENDING or \
                MediaStreamDirection.RECEIVING
        self._ips = []
        self._ports = []
        self._rid = None
        self._sid = sid
        MediaStreamDescription.__init__(self, stream, "video", direction)

    @property
    def candidate_encoder(self):
        return self._candidate_encoder

    @property
    def ips(self):
        return self._ips

    @property
    def ports(self):
        return self._ports

    @rw_property
    def rid():
        def fget(self):
            return self._rid
        def fset(self, value):
            self._rid = value
        return locals()

    @rw_property
    def sid():
        def fget(self):
            return self._sid
        def fset(self, value):
            self._sid = value
        return locals()
