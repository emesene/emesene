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

from papyon.msnp2p.constants import ApplicationID
from papyon.msnp2p.errors import TLPParseError
from papyon.util import debug
from papyon.util.decorator import rw_property

import struct
import random
import logging
import uuid

logger = logging.getLogger('papyon.msnp2p.transport')


MAX_INT32 = 2147483647

def _generate_id(max=MAX_INT32):
    return random.randint(1000, max)


class TLPFlag(object):
    NAK = 0x1
    ACK = 0x2
    RAK = 0x4
    RST = 0x8
    FILE = 0x10
    EACH = 0x20
    CAN = 0x40
    ERR = 0x80
    KEY = 0x100
    CRYPT = 0x200
    UNKNOWN = 0x1000000


class TLPHeader(object):
    size = 48

    def __init__(self, *header):
        header = list(header)
        header[len(header):] = [0] * (9 - len(header))

        self.session_id = header[0]
        self.blob_id = header[1]
        self.blob_offset = header[2]
        self.blob_size = header[3]
        self.chunk_size = header[4]
        self.flags = header[5]
        self.dw1 = header[6]
        self.dw2 = header[7]
        self.qw1 = header[8]

    def __str__(self):
        return struct.pack("<LLQQLLLLQ", self.session_id,
                self.blob_id,
                self.blob_offset,
                self.blob_size,
                self.chunk_size,
                self.flags,
                self.dw1,
                self.dw2,
                self.qw1)

    def parse(self, data, chunk_size):
        header = debug.hexify_string(data[:48])

        try:
            fields = struct.unpack("<LLQQLLLLQ", data[:48])
        except:
            raise TLPParseError(1, "invalid header", header)

        self.session_id = fields[0]
        self.blob_id = fields[1]
        self.blob_offset = fields[2]
        self.blob_size = fields[3]
        self.chunk_size = fields[4]
        self.flags = fields[5]
        self.dw1 = fields[6]
        self.dw2 = fields[7]
        self.qw1 = fields[8]

        # if chunk is containing all blob data, chunk_size field might be 0
        if self.blob_size == chunk_size and self.chunk_size == 0:
            self.chunk_size = chunk_size

        if self.blob_offset + self.chunk_size > self.blob_size:
            logger.warning(str(TLPParseError(1, "chunk end exceeds blob size", header)))
            self.chunk_size = chunk_size
        if self.blob_size >= 0 and self.chunk_size == 0:
            logger.warning(str(TLPParseError(1, "empty chunk for non-empty blob", header)))
            self.blob_size = 0


class MessageChunk(object):
    def __init__(self, header=TLPHeader(), body="", application_id=0):
        self.header = header
        self.body = body
        self.application_id = application_id

    def __str__(self):
        return str(self.header) + str(self.body)

    @rw_property
    def id():
        def fget(self):
            return self.header.dw1
        def fset(self, value):
            self.header.dw1 = value
        return locals()

    @property
    def next_id(self):
        if self.id + 1 == MAX_INT32:
            return 1
        return self.id + 1

    @property
    def session_id(self):
        return self.header.session_id

    @property
    def blob_id(self):
        return self.header.blob_id

    @property
    def ack_id(self):
        return (self.header.blob_id, self.header.dw1)

    @property
    def acked_id(self):
        return (self.header.dw1, self.header.dw2)

    @property
    def size(self):
        return self.header.chunk_size

    @property
    def blob_size(self):
        return self.header.blob_size

    @property
    def version(self):
        return 1

    def is_control_chunk(self):
        return self.header.flags & 0xCF

    def is_ack_chunk(self):
        return self.header.flags & TLPFlag.ACK

    def is_nak_chunk(self):
        return self.header.flags & TLPFlag.NAK

    def is_nonce_chunk(self):
        return self.header.flags & TLPFlag.KEY

    def is_syn_request(self):
        return False

    def is_data_preparation_chunk(self):
        return (self.header.chunk_size == 4 and self.header.blob_size == 4 and
                self.body == "\x00\x00\x00\x00" and
                not self.header.flags & TLPFlag.FILE)

    def is_signaling_chunk(self):
        return (self.session_id == 0)

    def has_progressed(self):
        return self.header.flags & TLPFlag.EACH

    def set_data(self, data):
        self.body = data
        self.header.chunk_size = len(data)

        if self.session_id != 0 and self.blob_size != 4 and data != '\x00' * 4:
            self.header.flags = TLPFlag.UNKNOWN | TLPFlag.EACH
            if self.application_id is ApplicationID.FILE_TRANSFER:
                self.header.flags |= TLPFlag.FILE

    def require_ack(self):
        if self.is_ack_chunk():
            return False
        current_size = self.header.chunk_size + self.header.blob_offset
        if current_size == self.header.blob_size:
            return True
        return False

    def create_ack_chunk(self, sync=False):
        flags = TLPFlag.ACK
        if self.header.flags & TLPFlag.RAK:
            flags |= TLPFlag.RAK

        blob_id = _generate_id()
        header = TLPHeader(self.header.session_id, blob_id, 0, 0, 0, flags,
            self.header.blob_id, self.header.dw1, self.header.blob_size)
        return MessageChunk(header)

    def get_nonce(self):
        """Get the nonce from the chunk. The chunk needs to have the KEY flag
           for that nonce to make sense (use is_nonce_chunk to check that)"""

        if not self.is_nonce_chunk():
            return "00000000-0000-0000-0000-000000000000"

        bytes = ""
        bytes += struct.pack(">L", self.header.dw1)
        bytes += struct.pack(">H", self.header.dw2 & 0xFFFF)
        bytes += struct.pack(">H", self.header.dw2 >> 16)
        bytes += struct.pack("<Q", self.header.qw1)

        return uuid.UUID(bytes=bytes)

    def set_nonce(self, nonce):
        """Set the chunk headers from a nonce and make it a nonce chunk by
           adding the KEY flag."""

        bytes = nonce.bytes

        self.header.dw1 = struct.unpack(">L", bytes[0:4])[0]
        self.header.dw2 = struct.unpack(">H", bytes[4:6])[0]
        self.header.dw2 += struct.unpack(">H", bytes[6:8])[0] << 16
        self.header.qw1 = struct.unpack("<Q", bytes[8:16])[0]
        self.header.flags |= TLPFlag.KEY

    @staticmethod
    def create(app_id, session_id, blob_id, offset, blob_size, max_size, sync):
        header = TLPHeader()
        header.session_id = session_id
        header.blob_id = blob_id
        header.blob_offset = offset
        header.blob_size = blob_size
        header.chunk_size = min(blob_size - offset, max_size - header.size)
        return MessageChunk(header, application_id=app_id)

    @staticmethod
    def parse(data):
        if len(data) < 48:
            raise TLPParseError(1, "chunk should be at least 48 bytes")

        header = TLPHeader()
        header.parse(data[:48], len(data) - 48)
        body = data[48:]
        return MessageChunk(header, body)

    def __repr__(self):
        string = "TLPv1 chunk 0x%x: " % self.id
        string += "blob %i, " % self.blob_id
        if self.session_id:
            string += "session %d, " % self.session_id
        if self.is_ack_chunk():
            string += "ACK 0x%x 0x%x" % self.acked_id
        elif self.is_nak_chunk():
            string += "NAK 0x%x 0x%x" % self.acked_id
        if self.size > 0:
            if self.session_id:
                string += "data [%d bytes]" % self.size
            else:
                string += "SLP Message"
                string += "\n\t" + debug.escape_string(self.body).\
                        replace("\r\n", "\\r\\n\n\t")
        return string
