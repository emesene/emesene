# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2007 Ali Sabil <asabil@gmail.com>
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

import papyon.util.string_io as StringIO

import struct
import random
import logging

__all__ = ['MessageBlob']

MAX_INT32 = 2147483647

logger = logging.getLogger('papyon.msnp2p.transport')

def _generate_id(max=MAX_INT32):
    """
    Returns a random ID.

        @return: a random integer between 1000 and sys.maxint
        @rtype: integer
    """
    return random.randint(1000, max)

_previous_chunk_id = _generate_id(MAX_INT32 - 1)
def _chunk_id():
    global _previous_chunk_id
    _previous_chunk_id += 1
    if _previous_chunk_id == MAX_INT32:
        _previous_chunk_id = 1
    return _previous_chunk_id

class TLPHeader(object):
    SIZE = 48

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

    @staticmethod
    def parse(header_data):
        header = struct.unpack("<LLQQLLLLQ", header_data[:48])
        session_id = header[0]
        blob_id = header[1]
        blob_offset = header[2]
        blob_size = header[3]
        chunk_size = header[4]
        flags = header[5]
        dw1 = header[6]
        dw2 = header[7]
        qw1 = header[8]
        return TLPHeader(session_id, blob_id, blob_offset, blob_size,
                chunk_size, flags, dw1, dw2, qw1)


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


class MessageChunk(object):
    def __init__(self, header=None, body=None):
        if header is None:
            header = TLPHeader()
        self.header = header
        if body is None:
            body = ""
        self.body = body
        self.application_id = 0

    def __str__(self):
        return str(self.header) + str(self.body)

    def is_control_chunk(self):
        return self.header.flags & 0xCF

    def is_ack_chunk(self):
        return self.header.flags & (TLPFlag.NAK | TLPFlag.ACK)

    def is_nonce_chunk(self):
        return self.header.flags & TLPFlag.KEY

    def has_progressed(self):
        return self.header.flags & TLPFlag.EACH

    def require_ack(self):
        if self.is_ack_chunk():
            return False
        current_size = self.header.chunk_size + self.header.blob_offset
        if current_size == self.header.blob_size:
            return True
        return False

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

        nonce = [("%X" % ord(byte)).zfill(2) for byte in bytes]
        for idx in (4, 7, 10, 13):
            nonce.insert(idx, '-')
        return "".join(nonce)

    def set_nonce(self, nonce):
        """Set the chunk headers from a nonce and make it a nonce chunk by
           adding the KEY flag."""

        nonce = filter(lambda c: c not in '{-}', nonce)
        bytes = ""
        for i in range(0, len(nonce), 2):
            bytes += chr(int(nonce[i:i+2], 16))

        self.header.dw1 = struct.unpack(">L", bytes[0:4])[0]
        self.header.dw2 = struct.unpack(">H", bytes[4:6])[0]
        self.header.dw2 += struct.unpack(">H", bytes[6:8])[0] << 16
        self.header.qw1 = struct.unpack("<Q", bytes[8:16])[0]
        self.header.flags |= TLPFlag.KEY

    @staticmethod
    def parse(data):
        header = TLPHeader.parse(data[:48])
        body = data[48:]
        return MessageChunk(header, body)


class MessageBlob(object):
    def __init__(self, application_id, data, total_size=None,
            session_id=None, blob_id=None, is_file=False):
        if data is not None:
            if isinstance(data, str):
                if len(data) > 0:
                    total_size = len(data)
                    data = StringIO.StringIO(data)
                else:
                    data = StringIO.StringIO()

            if total_size is None:
                data.seek(0, 2) # relative to the end
                total_size = data.tell()
                data.seek(0, 0)
        else:
            total_size = 0

        self.data = data
        self.current_size = 0
        self.total_size = total_size
        self.application_id = application_id
        if session_id is None:
            session_id = _generate_id()
        self.session_id = session_id
        self.id = blob_id or _generate_id()
        self.is_file = is_file

    def __del__(self):
        #if self.data is not None:
        #    self.data.close()
        pass

    def __str__(self):
        return repr(self)
    
    def __repr__(self):
        return """<MessageBlob :
                  id=%x == %d
                  session_id=%x
                  current_size=%d
                  total_size=%d
                  app id=%d
                  data=%s>""" % (self.id, self.id,
                              self.session_id,
                              self.current_size,
                              self.total_size,
                              self.application_id,
                              str(self.data))

    @property
    def transferred(self):
        return self.current_size

    def is_complete(self):
        return self.transferred == self.total_size

    def is_data_blob(self):
        return not self.is_control_blob()

    def is_control_blob(self):
        return False

    def read_data(self):
        self.data.seek(0, 0)
        data = self.data.read()
        self.data.seek(0, 0)
        return data

    def get_chunk(self, max_size):
        blob_offset = self.transferred

        if self.data is not None:
            self.data.seek(blob_offset, 0)
            data = self.data.read(max_size - TLPHeader.SIZE)
            assert len(data) > 0, "Trying to read more data than available"
        else:
            data = ""
        
        header = TLPHeader()
        header.session_id = self.session_id
        header.blob_id = self.id
        header.blob_offset = blob_offset
        header.blob_size = self.total_size
        header.chunk_size = len(data)
        header.dw1 = _chunk_id()
        if self.session_id != 0 and self.total_size != 4 and data != '\x00' * 4:
            header.flags = TLPFlag.EACH
            if self.is_file:
                header.flags |= TLPFlag.FILE

        chunk = MessageChunk(header, data)
        chunk.application_id = self.application_id
        self.current_size += header.chunk_size
        return chunk

    def append_chunk(self, chunk):
        assert self.data is not None, "Trying to write to a Read Only blob"
        assert self.session_id == chunk.header.session_id, "Trying to append a chunk to the wrong blob"
        assert self.id == chunk.header.blob_id, "Trying to append a chunk to the wrong blob"
        self.data.seek(chunk.header.blob_offset, 0)
        self.data.write(chunk.body)
        self.data.seek(0, 2)
        self.current_size = self.data.tell()


class ControlBlob(MessageBlob):
    def __init__(self, session_id, flags, dw1=0, dw2=0, qw1=0):
        MessageBlob.__init__(self, 0, None)
        header = TLPHeader(session_id, self.id, 0, 0, 0,
                flags, dw1, dw2, qw1)
        self.chunk = MessageChunk(header, "")

    def __repr__(self):
        return "<ControlBlob id=%x session_id=%x>" % (self.id, self.session_id)

    def get_chunk(self, max_size):
        return self.chunk
    
    def is_control_blob(self):
        return True

