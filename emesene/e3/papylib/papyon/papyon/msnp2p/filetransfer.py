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

from papyon.msnp2p.constants import ApplicationID, EufGuid
from papyon.msnp2p.errors import FTParseError
from papyon.msnp2p.session import P2PSession

import gobject
import struct

__all__ = ['FileTransferSession']

class FileTransferSession(P2PSession):

    def __init__(self, session_manager, peer, guid, message=None):
        P2PSession.__init__(self, session_manager, peer, guid,
                EufGuid.FILE_TRANSFER, ApplicationID.FILE_TRANSFER, message)
        self._filename = ""
        self._size = 0
        self._has_preview = False
        self._preview = None
        # data to be send if sending
        self._data = None

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

    def invite(self, filename, size, data, preview):
        self._filename = filename
        self._size = size
        self._data = data
        self._has_preview = preview is not None
        self._preview = preview
        context = self._build_context()
        self._invite(context)

    def accept(self, buffer=None):
        if buffer is not None:
            self.set_receive_data_buffer(buffer, self._size)
        self._accept()

    def reject(self):
        self._decline(603)

    def cancel(self):
        self._close()

    def send(self, data):
        self._data = data
        self._send_data("\x00" * 4)
        self._send_data(self._data)

    def parse_context(self, context):
        try:
            info = struct.unpack("<5I", context[0:20])
            self._size = info[2]
            self._has_preview = not bool(info[4])
            self._filename = unicode(context[20:570], "utf-16-le").rstrip("\x00")

            if self._has_preview:
                self._preview = context[574:]

        except:
            raise FTParseError(context)

    def _build_context(self):
        filename = self._filename.encode('utf-16_le')
        context = struct.pack("<5I", 574, 2, self._size, 0, int(self._has_preview))
        context += struct.pack("550s", filename)
        context += "\xFF" * 4
        if self._has_preview:
            context += self._preview
        return context

    def _on_session_accepted(self):
        if self._data:
            self.send(self._data)

    def _on_bye_received(self, message):
        if not self.completed:
            self._emit("canceled")
        self._dispose()
