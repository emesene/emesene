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

class COMPONENTS:
    RTP = 1
    RTCP = 2

class MediaSessionType(object):
    SIP = 1
    TUNNELED_SIP = 2
    WEBCAM_SEND = 3
    WEBCAM_RECV = 4

class MediaStreamDirection(object):
    SENDING = 1
    RECEIVING = 2
    BOTH = 3

XCAPS = {
    "audio" : {
    },
    "video" : {
        34: "34 65537:352:288:15.0:256000:1;131074:176:144:15.0:180000:1"
    }
}

VALID_CODECS = {
    "audio" : ["x-msrta", "siren", "g7221", "g723", "pcma", "pcmu", "red",
        "telephone-event", "speex"],
    "video" : ["x-rtvc1", "h263"]
}

EXTRA_PARAMS = {
    34: {"x-modea-only": "1"}
}
