# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006 Ali Sabil <ali.sabil@gmail.com>
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

"""An implementation of the MSN Messenger Protocol

papyon is a library, written in Python, for accessing the MSN
instant messaging service.

    @group High Level Interface: client, profile, conversation, event
    @group Low Level Interface: msnp, msnp2p, service
    @group Network Layer: gnet
"""

version = (0, 4, 6)

__version__ = ".".join(str(x) for x in version)
__author__ = "Youness Alaoui <kakaroto@users.sourceforge.net>"
__url__ = "http://telepathy.freedesktop.org/wiki/Papyon"
__license__ = "GNU GPL"

from client import *
from conversation import *
from profile import NetworkID, Presence, Privacy, Membership, Contact, Group
import event
import sip

import gnet.proxy
Proxy = gnet.proxy.ProxyFactory
ProxyInfos = gnet.proxy.ProxyInfos
