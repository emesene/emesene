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

import gobject
import sys
import unittest

bye_request = """BYE sip:207.46.112.110:32829;transport=tls;ms-received-cid=B650C000 SIP/2.0
Via: SIP/2.0/TLS 207.46.112.24:444;branch=z9hG4bK0E3C558B.765619AD;branched=TRUE;ms-internal-info="coETyDQoWCwZHL6jTa6sVdrgaboSl2VhmtzHQ35gAA"
Max-Forwards: 69
Content-Length: 0
Via: SIP/2.0/TLS 127.0.0.1:50390;received=70.25.46.249;ms-received-port=46649;ms-received-cid=B650C600
From: "0" <sip:louisfrancis.rb@gmail.com;wl-type=1>;tag=3df589cc60
To: "0" <sip:louis-francis.ratte-boulianne@collabora.co.uk;wl-type=1>;tag=1c583a7f95;epid=0f33c63844
Call-ID: d6c677ef1c9bcb62edf4cb7cd16d7780
CSeq: 3 BYE
User-Agent: aTSC/0.1
Supported: ms-dialog-route-set-update

"""

bye_response = """SIP/2.0 200 OK
v: SIP/2.0/TLS 207.46.112.24:444;branch=z9hG4bK0E3C558B.765619AD;branched=TRUE;ms-internal-info="coETyDQoWCwZHL6jTa6sVdrgaboSl2VhmtzHQ35gAA"
v: SIP/2.0/TLS 127.0.0.1:50390;received=70.25.46.249;ms-received-port=46649;ms-received-cid=B650C600
Max-Forwards: 70
f: "0" <sip:louis-francis.ratte-boulianne@collabora.co.uk;wl-type=1>;tag=1c583a7f95;epid=0f33c63844
t: "0" <sip:louisfrancis.rb@gmail.com>;tag=3df589cc60
i: d6c677ef1c9bcb62edf4cb7cd16d7780
CSeq: 1 BYE
User-Agent: aTSC/0.1
l: 0

"""

class MessageTestCase(unittest.TestCase):

    def setUp(self):
        self.ttl = Transport()
        self.parser = SIPMessageParser()
        self.message = None
        self.ttl.connect("line-received", self.parser.on_line_received)

    def testParseRequest(self):
        def verify(parser, msg, case):
            case.assertEqual(type(msg), SIPRequest)
            case.assertEqual(msg.code, "BYE")
            case.assertEqual(msg.get_header("User-Agent"), "aTSC/0.1")

        self.parser.connect("message-received", verify, self)
        self.ttl.receive(bye_request)

    def testParseResponse(self):
        def verify(parser, msg, case):
            case.assertEqual(type(msg), SIPResponse)
            case.assertEqual(msg.code, "BYE")
            case.assertEqual(msg.status, 200)
            case.assertEqual(msg.get_header("User-Agent"), "aTSC/0.1")

        self.parser.connect("message-received", verify, self)
        self.ttl.receive(bye_response)

    def testBuildParseRequest(self):
        def verify(parser, msg, case):
            case.assertEqual(type(msg), SIPRequest)
            case.assertEqual(msg.code, "BYE")
            case.assertEqual(msg.uri, "test@example.com")
            case.assertEqual(msg.get_header("User-Agent"), "aTSC/0.1")

        message = SIPRequest("BYE", "test@example.com")
        message.add_header("User-Agent", "aTSC/0.1")
        self.parser.connect("message-received", verify, self)
        self.ttl.receive(str(message))

class Transport(gobject.GObject):

    __gsignals__ = {
        "line-sent": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ([object])),
        "line-received": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ([object]))
    }

    def __init__(self):
        gobject.GObject.__init__(self)

    def send(self, message):
        for line in message.splitlines():
            self.emit("line-sent", line)

    def receive(self, message):
        for line in message.splitlines():
            self.emit("line-received", line)


if __name__ == "__main__":
    sys.path.insert(0, "")
    from papyon.sip.sip import *
    unittest.main()
