# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Johann Prieur <johann.prieur@gmail.com>
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
import random

def generate_guid():
    bytes = [random.randrange(256) for i in range(16)]

    data1 = ("%02X" * 4) % tuple(bytes[0:4])
    data2 = ("%02X" * 2) % tuple(bytes[4:6])
    data3 = ("%02X" * 2) % tuple(bytes[6:8])
    data4 = ("%02X" * 2) % tuple(bytes[8:10])
    data5 = ("%02X" * 6) % tuple(bytes[10:])

    data3 = "4" + data3[1:]

    return "%s-%s-%s-%s-%s" % (data1, data2, data3, data4, data5)
