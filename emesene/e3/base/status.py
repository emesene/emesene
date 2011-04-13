# -*- coding: utf-8 -*-

#    This file is part of emesene.
#
#    emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

(ONLINE, OFFLINE, BUSY, AWAY, IDLE) = range(5)

ORDERED = [ONLINE, BUSY, AWAY, IDLE, OFFLINE]
ALL = ORDERED

STATUS = {}
STATUS[ONLINE] = _("Available")
STATUS[OFFLINE] = _("Offline")
STATUS[BUSY] = _("Busy")
STATUS[AWAY] = _("Away")
STATUS[IDLE] = _("Idle")
