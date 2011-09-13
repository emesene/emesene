# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2010 Collabora Ltd.
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

from papyon.msnp2p.constants import ApplicationID, PeerInfo
from papyon.msnp2p.errors import TLPParseError
from papyon.util import debug
from papyon.util.decorator import rw_property
from papyon.util.tlv import TLV

import struct
import random
import logging

logger = logging.getLogger('msnp2p:transport')

class TLPFlag(object):
    NONE = 0x0
    SYN  = 0x1
    RAK  = 0x2

class TLPParamType(object):
    PEER_INFO = 0x1
    ACK_SEQ = 0x2
    NAK_SEQ = 0x3

class DLPType(object):
    SLP = 0x0
    MSN_OBJECT = 0x4
    FILE_TRANSFER = 0x6

class DLPParamType(object):
    DATA_REMAINING = 0x1

TLPParamLength = {
    TLPParamType.PEER_INFO: 12,
    TLPParamType.ACK_SEQ: 4,
    TLPParamType.NAK_SEQ: 4
}

DLPParamLength = {
    DLPParamType.DATA_REMAINING: 8,
}

class TLPHeader(object):
    """Transport Layer Protocol header v2:

       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1  ....
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
       |L|O|Len|ChunkID|if L>8 then TLV else skip   .... | Payload
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

       L        : Header Length
       O        : Operation Code (see TLPFlag)
       Len      : Length of payload (Data Header + Data)
       ChunkID  : ID of chunk (last chunk ID + last chunk Len)
       TLV      : See TLPParamType for possible types
       Payload  : Data Header + Data

       Data Header (if data length > 0)

       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1  ....
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
       |L|T|PN |Session|if L>8 then TLV else skip   .... | Data
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

       L        : Data Header Length
       T        : Type-First combination (see DLPType for types)
       PN       : Package number (common between chunks of the same blob)
       Session  : Session Ientifier
       TLV      : See DLPParamType for possible types"""

    def __init__(self):
        self.op_code = 0
        self.chunk_size = 0
        self.chunk_id = 0
        self.session_id = 0
        self.data_type = 0
        self.first = False
        self.package_number = 0
        self.tlv = TLV(TLPParamLength)
        self.data_tlv = TLV(DLPParamLength)

    @property
    def size(self):
        size = 8 + len(self.tlv)
        if self.chunk_size > 0:
            size += 8 + len(self.data_tlv)
        return size

    @property
    def data_size(self):
        size = self.chunk_size
        if self.chunk_size > 0:
            size += 8 + len(self.data_tlv)
        return size

    @rw_property
    def peer_info():
        def fget(self):
            return self.tlv.get(TLPParamType.PEER_INFO, "")
        def fset(self, value):
            self.tlv.update(TLPParamType.PEER_INFO, value)
        return locals()

    @rw_property
    def ack_seq():
        def fget(self):
            return self.tlv.get(TLPParamType.ACK_SEQ, 0)
        def fset(self, value):
            self.tlv.update(TLPParamType.ACK_SEQ, value)
        return locals()

    @rw_property
    def nak_seq():
        def fget(self):
            return self.tlv.get(TLPParamType.NAK_SEQ, 0)
        def fset(self, value):
            self.tlv.update(TLPParamType.NAK_SEQ, value)
        return locals()

    @rw_property
    def tf_combination():
        def fget(self):
            return self.data_type | self.first
        def fset(self, value):
            self.first = bool(value & 0x01)
            self.data_type = value & 0xFE
        return locals()

    @rw_property
    def data_remaining():
        def fget(self):
            return self.data_tlv.get(DLPParamType.DATA_REMAINING, 0)
        def fset(self, value):
            self.data_tlv.update(DLPParamType.DATA_REMAINING, value)
        return locals()

    def set_sync(self, sync):
        if sync:
            self.op_code = TLPFlag.SYN | TLPFlag.RAK
            self.peer_info = struct.pack(">HHHHI",
                    PeerInfo.PROTOCOL_VERSION, PeerInfo.IMPLEMENTATION_ID,
                    PeerInfo.VERSION, 0, PeerInfo.CAPABILITIES)
        else:
            self.op_code = 0
            self.peer_info = ""

    def __str__(self):
        size = 8 + len(self.tlv)
        data_size = self.chunk_size
        data_header = ""
        if data_size > 0:
            data_header_size, data_header = self.build_data_header()
            data_size += data_header_size
        header = struct.pack(">BBHL", size, self.op_code, data_size,
                self.chunk_id)
        header += str(self.tlv)
        header += data_header
        return header
    
    def parse(self, data):
        try:
            fields = struct.unpack(">BBHL", data[:8])
        except:
            header = debug.hexify_string(data[:8])
            raise TLPParseError(2, "invalid header", header)

        size = fields[0]
        self.op_code = fields[1]
        self.chunk_size = fields[2]
        self.chunk_id = fields[3]
        self.tlv.parse(data[8:], size - 8)
        if self.chunk_size > 0:
            dph_size = self.parse_data_header(data[size:])
            self.chunk_size -= dph_size
            size += dph_size
        return size

    def build_data_header(self):
        size = len(self.data_tlv) + 8
        header = struct.pack(">BBHL", size, self.tf_combination,
                self.package_number, self.session_id)
        header += str(self.data_tlv)
        return size, header

    def parse_data_header(self, data):
        try:
            fields = struct.unpack(">BBHI", data[:8])
        except:
            header = debug.hexify_string(data[:8])
            raise TLPParseError(2, "invalid data header", header)

        size = fields[0]
        self.tf_combination = fields[1]
        self.package_number = fields[2]
        self.session_id = fields[3]
        self.data_tlv.parse(data[8:], size - 8)
        return size


class MessageChunk(object):
    def __init__(self, header, body="", application_id=0):
        self.header = header
        self.body = body
        self.application_id = application_id

    @rw_property
    def id():
        def fget(self):
            return self.header.chunk_id
        def fset(self, value):
            self.header.chunk_id = value
        return locals()

    @property
    def next_id(self):
        return self.id + self.header.data_size

    @rw_property
    def application_id():
        def fget(self):
            return self._application_id
        def fset(self, value):
            self._application_id = value
            if self.session_id == 0 or self.is_data_preparation_chunk():
                self.header.data_type = DLPType.SLP
            elif value is ApplicationID.FILE_TRANSFER:
                self.header.data_type = DLPType.FILE_TRANSFER
            elif value is ApplicationID.CUSTOM_EMOTICON_TRANSFER or \
                 value is ApplicationID.DISPLAY_PICTURE_TRANSFER:
                self.header.data_type = DLPType.MSN_OBJECT
        return locals()

    @property
    def session_id(self):
        return self.header.session_id

    @property
    def blob_id(self):
        return self.header.package_number

    @property
    def ack_id(self):
        return self.header.chunk_id + self.header.data_size

    @property
    def acked_id(self):
        return self.header.ack_seq

    @property
    def naked_id(self):
        return self.header.nak_seq

    @property
    def size(self):
        return self.header.chunk_size

    @property
    def blob_size(self):
        if not self.header.first:
            return 0
        return self.header.data_remaining + self.size

    @property
    def version(self):
        return 2

    def is_control_chunk(self):
        return self.is_ack_chunk() or self.is_nak_chunk() or \
                (self.require_ack() and self.size == 0)

    def is_ack_chunk(self):
        return self.header.ack_seq > 0

    def is_nak_chunk(self):
        return self.header.nak_seq > 0

    def is_syn_request(self):
        return (self.header.op_code & TLPFlag.SYN) and not self.is_ack_chunk()

    def is_signaling_chunk(self):
        return (self.header.data_type == DLPType.SLP)

    def is_data_preparation_chunk(self):
        return (self.header.first and self.size == 4)

    def require_ack(self):
        return self.header.op_code & TLPFlag.RAK

    def has_progressed(self):
        return True

    def create_ack_chunk(self, sync=False):
        header = TLPHeader()
        header.ack_seq = self.ack_id
        header.set_sync(sync)
        return MessageChunk(header)

    def set_data(self, data):
        self.body = data
        self.header.chunk_size = len(data)

    @staticmethod
    def create(app_id, session_id, blob_id, offset, blob_size, max_size, sync):
        header = TLPHeader()
        header.session_id = session_id
        header.first = (offset == 0)

        # if first message of a transport, add Peer Info to TLVs
        header.set_sync(sync)

        max_chunk_size = max_size - header.size
        data_remaining = blob_size - offset
        if max_chunk_size >= data_remaining:
            chunk_size = data_remaining
        else:
            chunk_size = max_chunk_size
        header.chunk_size = chunk_size
        header.data_remaining = data_remaining - chunk_size

        # signaling messages require acknowledgement (last chunk only)
        if session_id == 0 and header.data_remaining == 0:
            header.op_code |= TLPFlag.RAK

        # set package number for split signaling messages
        header.package_number = 0
        if session_id == 0 and (not header.first or header.data_remaining > 0):
            header.package_numer = blob_id & 0xFFFF

        return MessageChunk(header, application_id=app_id)

    @staticmethod
    def parse(data):
        header = TLPHeader()
        header_size = header.parse(data)
        body = data[header_size:]
        return MessageChunk(header, body)

    def __str__(self):
        return str(self.header) + str(self.body)

    def __repr__(self):
        string = "TLPv2 chunk 0x%x: " % self.id
        string += "blob %i, " % self.blob_id
        if self.session_id:
            string += "session %d, " % self.session_id
        if self.is_ack_chunk():
            string += "ACK 0x%x, " % self.acked_id
        if self.is_nak_chunk():
            string += "NAK 0x%x, " % self.naked_id
        if self.require_ack():
            string += "RAK, "
        if self.header.op_code & TLPFlag.SYN:
            string += "SYN, "
        if self.size > 0:
            if self.session_id:
                string += "data [%d bytes]" % self.size
            else:
                string += "SLP Message"
                string += "\n\t" + debug.escape_string(self.body).\
                        replace("\r\n", "\\r\\n\n\t")
        return string
