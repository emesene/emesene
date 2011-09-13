# -*- coding: utf-8 -*-
#
# Copyright (C) 2006  Ali Sabil <ali.sabil@gmail.com>
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

__all__ = ['ProxyfiableClient']

class ProxyfiableClient(object):
    """All proxifiable clients must inherit from this class
    to enable the Proxy object to manipulate them"""

    def __init__(self):
        pass

    def _proxy_opening(self, sock):
        if not self._configure(): return
        self._pre_open(sock)

    def _proxy_open(self):
        self._post_open()

    def _proxy_closed(self):
        self.close()
