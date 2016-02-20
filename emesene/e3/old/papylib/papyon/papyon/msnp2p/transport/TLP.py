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

from papyon.msnp2p.transport import TLPv1, TLPv2
import papyon.util.string_io as StringIO

import struct
import random
import logging
import os

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

class MessageChunk(object):
    @staticmethod
    def create(version, app_id, session_id, blob_id, offset, blob_size,
            max_size, sync):
        if version in (1, 2):
            module = globals()["TLPv%i" % version]
            return module.MessageChunk.create(app_id, session_id, blob_id,
                    offset, blob_size, max_size, sync)
        else:
            raise NotImplementedError("TLPv%s is not implemented" % version)

    @staticmethod
    def parse(version, data):
        if version in (1, 2):
            module = globals()["TLPv%i" % version]
            return module.MessageChunk.parse(data)
        else:
            raise NotImplementedError("TLPv%s is not implemented" % version)

class MessageBlob(object):
    def __init__(self, application_id, data, total_size=None,
            session_id=None, blob_id=None):
        if data is not None:
            if isinstance(data, str):
                if len(data) > 0:
                    total_size = len(data)
                    data = StringIO.StringIO(data)
                else:
                    data = StringIO.StringIO()

            if total_size is None:
                data.seek(0, os.SEEK_END) # relative to the end
                total_size = data.tell()
                data.seek(0, os.SEEK_SET)
        else:
            total_size = 0

        self.data = data
        self.current_size = 0
        self.total_size = total_size
        self.application_id = application_id
        if session_id is None:
            session_id = _generate_id()
        self.session_id = session_id
        if blob_id is None:
            blob_id = _generate_id()
        self.id = blob_id

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

    def read_data(self):
        self.data.seek(0, os.SEEK_SET)
        data = self.data.read()
        self.data.seek(0, os.SEEK_SET)
        return data

    def get_chunk(self, version, max_size, sync=False):
        chunk = MessageChunk.create(version, self.application_id, self.session_id,
                self.id, self.transferred, self.total_size, max_size, sync)

        if self.data is not None:
            self.data.seek(self.transferred, os.SEEK_SET)
            data = self.data.read(chunk.size)
            assert len(data) > 0, "Trying to read more data than available"
        else:
            data = ""
        
        chunk.set_data(data)
        self.current_size += chunk.size
        return chunk

    def append_chunk(self, chunk):
        assert self.data is not None, "Trying to write to a Read Only blob"
        assert self.session_id == chunk.session_id, "Trying to append a chunk to the wrong blob"
        assert self.id == chunk.blob_id, "Trying to append a chunk to the wrong blob"
        self.data.seek(0, os.SEEK_END)
        self.data.write(chunk.body)
        self.current_size = self.data.tell()
