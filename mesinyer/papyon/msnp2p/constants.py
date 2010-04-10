# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2007 Ole André Vadla Ravnås <oleavr@gmail.com>
# Copyright (C) 2008 Richard Spiers <richard.spiers@gmail.com>
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

__all__ = ['EufGuid', 'ApplicationID', 'SLPContentType', 'SLPRequestMethod']

class EufGuid(object):
    MSN_OBJECT = "{A4268EEC-FEC5-49E5-95C3-F126696BDBF6}"
    FILE_TRANSFER = "{5D3E02AB-6190-11D3-BBBB-00C04F795683}"
    MEDIA_RECEIVE_ONLY = "{1C9AA97E-9C05-4583-A3BD-908A196F1E92}"
    MEDIA_SESSION = "{4BD96FC0-AB17-4425-A14A-439185962DC8}"
    SHARE_PHOTO = "{41D3E74E-04A2-4B37-96F8-08ACDB610874}"
    ACTIVITY = "{6A13AF9C-5308-4F35-923A-67E8DDA40C2F}"

class ApplicationID(object):
    FILE_TRANSFER = 2
    CUSTOM_EMOTICON_TRANSFER = 11
    DISPLAY_PICTURE_TRANSFER = 12
    WEBCAM           = 4 # Do we need a better name ?

class Codec(object):
    ML20 = "ML20"

class SLPContentType(object):
    """MSNSLP content types"""
    SESSION_REQUEST = "application/x-msnmsgr-sessionreqbody"
    SESSION_FAILURE = "application/x-msnmsgr-session-failure-respbody"
    SESSION_CLOSE = "application/x-msnmsgr-sessionclosebody"

    TRANSFER_REQUEST = "application/x-msnmsgr-transreqbody"
    TRANSFER_RESPONSE = "application/x-msnmsgr-transrespbody"

    TRANS_UDP_SWITCH = "application/x-msnmsgr-transudpswitch"
    
    NULL = "null"
    
class SLPRequestMethod(object):
    INVITE = 'INVITE'
    BYE = 'BYE'
    ACK = 'ACK'
