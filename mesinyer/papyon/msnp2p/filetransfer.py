# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2009 Collabora Ltd.
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

from papyon.msnp2p.constants import EufGuid
from papyon.msnp2p.session import P2PSession

import struct
import logging

__all__ = ['FileTransferSession']

logger = logging.getLogger('papyon.msnp2p.filetransfersession')

class FileTransferSession(P2PSession):

    def __init__(self, session_manager, peer, application_id, message=None):
        P2PSession.__init__(self, session_manager, peer,
                EufGuid.FILE_TRANSFER, application_id, message)
        self._filename = ""
        self._size = 0
        self._has_preview = False
        self._preview = None
        # data to be send if sending
        self._data = None

        if message is not None:
            self.parse_context(message.body.context)

    @property
    def filename(self):
        return self._filename

    @property
    def size(self):
        return self._size

    @property
    def has_preview(self):
        return self._has_preview

    @property
    def preview(self):
        return self._preview

    def invite(self, filename, size):
        self._filename = filename
        self._size = size
        context = self.build_context()
        self._invite(context)

    def accept(self):
        self._respond(200)

    def reject(self):
        self._respond(603)

    def send(self, data):
        logger.debug("FileTransferSession.send()")
        self._data = data
        self._transreq()

    def parse_context(self, context):
        info = struct.unpack("<5I", context[0:20])
        self._size = info[2]
        self._has_preview = not bool(info[4])
        self._filename = unicode(context[20:570], "utf-16-le").rstrip("\x00")

    def build_context(self):
        filename = self._filename.decode('ascii').encode('utf-16_le')
        context = struct.pack("<5I", 574, 2, self._size, 0, int(self._has_preview))
        context += struct.pack("550s", filename)
        context += "\xFF" * 4
        return context

    def _on_bridge_selected(self):
        logger.debug("On bridge selected %s" % (self._data != None))
        if self._data is not None:
            self._send_p2p_data("\x00" * 4)
            self._send_p2p_data(self._data, True)
