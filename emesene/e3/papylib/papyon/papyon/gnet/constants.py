# -*- coding: utf-8 -*-
#
# Copyright (C) 2005  Ole André Vadla Ravnås <oleavr@gmail.com>
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

"""Constants used in GNet."""
from socket import AF_INET, AF_INET6, \
    SOCK_STREAM, SOCK_DGRAM, SOCK_RAW, SOCK_RDM, SOCK_SEQPACKET
try:
    from socket import AF_UNIX
except ImportError:
    pass

class GNet(object):
    NAME = "gnet"
    VERSION = "0.1"

class IoStatus(object):
    """Various networking status"""
    CLOSING = 0
    CLOSED  = 1
    OPENING = 2
    OPEN    = 3
