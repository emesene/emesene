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

__all__ = ["ProtocolConstant", "ProtocolError", "ProtocolState",
        "ClientTypes", "UserNotificationTypes"]

class ProtocolConstant(object):
    VER = (18, 16, 15)
    CVR = ('0x0409', 'winnt', '5.1', 'i386', 'MSNMSGR', '8.1.0178', 'msmsgs')
    PRODUCT_ID = "PROD0114ES4Z%Q5W"
    PRODUCT_KEY = "PK}_A_0N_K%O?A9S"
    CHL_MAGIC_NUM = 0x0E79A9C1

class ProtocolError(object):
    "Protocol related errors"
    UNKNOWN = 0
    OTHER_CLIENT = 1
    SERVER_DOWN = 2
    INVALID_COMMAND = 3
    AUTHENTICATION_FAILED = 4

class ProtocolState(object):
    CLOSED = 0
    OPENING = 1
    AUTHENTICATING = 2
    AUTHENTICATED = 3
    SYNCHRONIZING = 4
    SYNCHRONIZED = 5
    OPEN = 6
    CLOSING = 7

class ClientTypes(object):
    COMPUTER = 1
    WEBSITE = 2
    MOBILE = 3
    XBOX = 4

class UserNotificationTypes(object):
    XML_DATA = 1
    SIP_INVITE = 2
    P2P_DATA = 3
    CLOSED_CONVERSATION = 5
    RESYNCHRONIZE = 6
    RTC_ACTIVITY = 11
    TUNNELED_SIP = 12
