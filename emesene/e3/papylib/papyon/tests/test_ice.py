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

import sys
import unittest

audio_candidates19 = [
(("1", 1, "UDP", 2013266431, "192.168.1.107", 54751, "host", None, None),
"1 1 UDP 2013266431 192.168.1.107 54751 typ host"),
(("3", 1, "UDP", 1677721855, "70.25.46.249", 54751, "srflx", "192.168.1.107", 54751),
"3 1 UDP 1677721855 70.25.46.249 54751 typ srflx raddr 192.168.1.107 rport 54751"),
(("4", 1, "UDP", 1006633215, "64.4.35.48", 30797, "relay", "192.168.1.107", 54751),
"4 1 UDP 1006633215 64.4.35.48 30797 typ relay raddr 192.168.1.107 rport 54751"),
(("1", 2, "UDP", 2013266430, "192.168.1.107", 49259, "host", None, None),
"1 2 UDP 2013266430 192.168.1.107 49259 typ host"),
(("3", 2, "UDP", 1677721854, "70.25.46.249", 49259, "srflx", "192.168.1.107", 49259),
"3 2 UDP 1677721854 70.25.46.249 49259 typ srflx raddr 192.168.1.107 rport 49259"),
(("4", 2, "UDP", 1006633214, "64.4.35.48", 45694, "relay", "192.168.1.107", 49259),
"4 2 UDP 1006633214 64.4.35.48 45694 typ relay raddr 192.168.1.107 rport 49259")]

video_candidates19 = [
(("2", 1, "UDP", 2013266431, "192.168.1.116", 52826, "host", None, None),
"2 1 UDP 2013266431 192.168.1.116 52826 typ host"),
(("5", 1, "UDP", 1677721855, "69.70.191.106", 52826, "srflx", "192.168.1.116", 52826),
"5 1 UDP 1677721855 69.70.191.106 52826 typ srflx raddr 192.168.1.116 rport 52826"),
(("2", 2, "UDP", 2013266430, "192.168.1.116", 37649, "host", None, None),
"2 2 UDP 2013266430 192.168.1.116 37649 typ host"),
(("5", 2, "UDP", 1677721854, "69.70.191.106", 37649, "srflx", "192.168.1.116", 37649),
"5 2 UDP 1677721854 69.70.191.106 37649 typ srflx raddr 192.168.1.116 rport 37649")]

audio_candidates6 = [
(("gAH6Rj7UAhyhL37x1myyRCEe0s90i/okTPPlQ8q9Ufg=", 1,
  "AT6jQtrWTfVi7S1Ko4pBxA==", "UDP", 0.830, "192.168.1.107", 54183),
"gAH6Rj7UAhyhL37x1myyRCEe0s90i/okTPPlQ8q9Ufg= 1 AT6jQtrWTfVi7S1Ko4pBxA== UDP 0.830 192.168.1.107 54183"),
(("wknsOPNTNLvDhc7jX+qIKK/1YwcG+8uifjfo21ridEM=", 1,
  "wWRgVlW33BSPYwEZrsFwFg==", "UDP", 0.550, "70.25.46.249", 54183),
"wknsOPNTNLvDhc7jX+qIKK/1YwcG+8uifjfo21ridEM= 1 wWRgVlW33BSPYwEZrsFwFg== UDP 0.550 70.25.46.249 54183"),
(("AHx6YkMxxV4F4diHF2o/wi6PF3hK8UPg/veO1nkC8CY=", 1,
  "iVxzBYjmxFxOHI4e3ZMq6A==", "UDP", 0.450, "64.4.34.204", 32594),
"AHx6YkMxxV4F4diHF2o/wi6PF3hK8UPg/veO1nkC8CY= 1 iVxzBYjmxFxOHI4e3ZMq6A== UDP 0.450 64.4.34.204 32594"),
(("gAH6Rj7UAhyhL37x1myyRCEe0s90i/okTPPlQ8q9Ufg=", 2,
  "AT6jQtrWTfVi7S1Ko4pBxA==", "UDP", 0.830, "192.168.1.107", 43701),
"gAH6Rj7UAhyhL37x1myyRCEe0s90i/okTPPlQ8q9Ufg= 2 AT6jQtrWTfVi7S1Ko4pBxA== UDP 0.830 192.168.1.107 43701"),
(("wknsOPNTNLvDhc7jX+qIKK/1YwcG+8uifjfo21ridEM=", 2,
  "wWRgVlW33BSPYwEZrsFwFg==", "UDP", 0.550, "70.25.46.249", 43701),
"wknsOPNTNLvDhc7jX+qIKK/1YwcG+8uifjfo21ridEM= 2 wWRgVlW33BSPYwEZrsFwFg== UDP 0.550 70.25.46.249 43701"),
(("AHx6YkMxxV4F4diHF2o/wi6PF3hK8UPg/veO1nkC8CY=", 2,
  "iVxzBYjmxFxOHI4e3ZMq6A==", "UDP", 0.450, "64.4.34.204", 56585),
"AHx6YkMxxV4F4diHF2o/wi6PF3hK8UPg/veO1nkC8CY= 2 iVxzBYjmxFxOHI4e3ZMq6A== UDP 0.450 64.4.34.204 56585")]

audio_codecs = [((8, "PCMA", 8000, None), "8 PCMA/8000", ""),
                ((0, "PCMU", 8000, None), "0 PCMU/8000", ""),
                ((101, "telephone-event", 8000, "0-16"),
                 "101 telephone-event/8000", "101 0-16")]

video_codecs = [((34, "H263", 90000, None), "34 H263/90000", "")]

audio_msg19 = """v=0
o=- 0 0 IN IP4 64.4.34.205
s=session
b=CT:99980
t=0 0
m=audio 42821 RTP/AVP 8 0 101
c=IN IP4 64.4.34.205
a=ice-ufrag:kZ+J
a=ice-pwd:LFlH+neJ0CmUG/Vm1inOCJ
a=candidate:1 1 UDP 2013266431 192.168.1.107 54751 typ host
a=candidate:3 1 UDP 1677721855 70.25.46.249 54751 typ srflx raddr 192.168.1.107 rport 54751
a=candidate:4 1 UDP 1006633215 64.4.35.48 30797 typ relay raddr 192.168.1.107 rport 54751
a=candidate:1 2 UDP 2013266430 192.168.1.107 49259 typ host
a=candidate:3 2 UDP 1677721854 70.25.46.249 49259 typ srflx raddr 192.168.1.107 rport 49259
a=candidate:4 2 UDP 1006633214 64.4.35.48 45694 typ relay raddr 192.168.1.107 rport 49259
a=rtcp:41965
a=rtpmap:8 PCMA/8000
a=rtpmap:0 PCMU/8000
a=rtpmap:101 telephone-event/8000
a=fmtp:101 0-16
a=encryption:rejected"""

video_msg19 = """m=video 52826 RTP/AVP 34
c=IN IP4 192.168.1.116
a=x-caps:34 65537:352:288:15.0:256000:1;131074:176:144:15.0:180000:1
a=ice-ufrag:JjzZ
a=ice-pwd:lfQttyfZ3SicOvs1WC2del
a=candidate:2 1 UDP 2013266431 192.168.1.116 52826 typ host
a=candidate:5 1 UDP 1677721855 69.70.191.106 52826 typ srflx raddr 192.168.1.116 rport 52826
a=candidate:2 2 UDP 2013266430 192.168.1.116 37649 typ host
a=candidate:5 2 UDP 1677721854 69.70.191.106 37649 typ srflx raddr 192.168.1.116 rport 37649
a=rtcp:37649
a=rtpmap:34 H263/90000
a=encryption:rejected"""


def createCandidate19(args):
    return ICECandidate(draft=19,
                        foundation=args[0],
                        component_id=args[1],
                        transport=args[2],
                        priority=args[3],
                        ip=args[4],
                        port=args[5],
                        type=args[6],
                        base_ip=args[7],
                        base_port=args[8])

def createCandidate6(args):
    return ICECandidate(draft=6,
                        foundation=args[0][0:31],
                        username=args[0],
                        component_id=args[1],
                        password=args[2],
                        transport=args[3],
                        priority=args[4],
                        ip=args[5],
                        port=args[6])

class CandidateTestCase(unittest.TestCase):

    def testParse19(self):
        for args, line in audio_candidates19:
            candidate = ICECandidate(draft=19)
            candidate.parse(line)
            self.assertEqual(candidate, createCandidate19(args))

    def testBuildLocal19(self):
        for args, line in audio_candidates19:
            candidate = createCandidate19(args)
            print str(candidate)

    def testBuildParse19(self):
        for args, line in audio_candidates19:
            candidate = createCandidate19(args)
            line = str(candidate)
            candidate = ICECandidate(draft=19)
            candidate.parse(line)
            self.assertEqual(candidate, createCandidate19(args))

    def testParse6(self):
        for args, line in audio_candidates6:
            candidate = ICECandidate(draft=6)
            candidate.parse(line)
            self.assertEqual(candidate, createCandidate6(args))

    def testBuildLocal6(self):
        for args, line in audio_candidates6:
            candidate = createCandidate6(args)
            self.assertEqual(str(candidate), line)

    def testBuildParse6(self):
        for args, line in audio_candidates6:
            candidate = createCandidate6(args)
            line = str(candidate)
            candidate = ICECandidate(draft=6)
            candidate.parse(line)
            self.assertEqual(candidate, createCandidate6(args))


class Session19TestCase(unittest.TestCase):

    def setUp(self):
        self.session = ICESession(draft=19)
        self.audio_candidates = []
        for args, line in audio_candidates19:
            candidate = createCandidate19(args)
            candidate.username = "kZ+J"
            candidate.password = "LFlH+neJ0CmUG/Vm1inOCJ"
            self.audio_candidates.append(candidate)
        self.video_candidates = []
        for args, line in video_candidates19:
            candidate = createCandidate19(args)
            candidate.username = "JjzZ"
            candidate.password = "lfQttyfZ3SicOvs1WC2del"
            self.video_candidates.append(candidate)

        self.audio_codecs = []
        for args, rtpmap, fmtp in audio_codecs:
            self.audio_codecs.append(SDPCodec(*args))
        self.video_codecs = []
        for args, rtpmap, fmtp in video_codecs:
            self.video_codecs.append(SDPCodec(*args))

    def testGetAudioRelay(self):
        self.session.set_local_candidates("audio", self.audio_candidates)
        relay = self.session.search_relay("audio")
        self.assertEqual(relay.foundation, '4')

    def testGetVideoRelay(self):
        self.session.set_local_candidates("video", self.video_candidates)
        relay = self.session.search_relay("video")
        self.assertEqual(relay.foundation, '5')

    def testParseSdpA(self):
        self.session.parse_sdp(audio_msg19)
        self.assertEqual(self.session.get_remote_codecs("audio"),
                         self.audio_codecs)
        self.assertEqual(self.session.get_remote_candidates("audio"),
                         self.audio_candidates)

    def testParseSdpAV(self):
        self.session.parse_sdp(audio_msg19 + "\r\n" + video_msg19)
        self.assertEqual(self.session.get_remote_codecs("audio"),
                         self.audio_codecs)
        self.assertEqual(self.session.get_remote_candidates("audio"),
                         self.audio_candidates)
        self.assertEqual(self.session.get_remote_codecs("video"),
                         self.video_codecs)
        self.assertEqual(self.session.get_remote_candidates("video"),
                         self.video_candidates)

    def testBuildParseSdpA(self):
        self.session.set_local_codecs("audio", self.audio_codecs)
        self.session.set_local_candidates("audio", self.audio_candidates)
        msg = self.session.build_sdp()
        self.session.parse_sdp(msg)
        self.assertEqual(self.session.get_remote_codecs("audio"),
                         self.audio_codecs)
        self.assertEqual(self.session.get_remote_candidates("audio"),
                         self.audio_candidates)
        self.assertEqual(self.session.get_remote_codecs("video"), [])
        self.assertEqual(self.session.get_remote_candidates("video"), [])

    def testBuildParseSdpAV(self):
        self.session.set_local_codecs("audio", self.audio_codecs)
        self.session.set_local_candidates("audio", self.audio_candidates)
        self.session.set_local_codecs("video", self.video_codecs)
        self.session.set_local_candidates("video", self.video_candidates)
        msg = self.session.build_sdp()
        self.session.parse_sdp(msg)
        self.assertEqual(self.session.get_remote_codecs("audio"),
                         self.audio_codecs)
        self.assertEqual(self.session.get_remote_candidates("audio"),
                         self.audio_candidates)
        self.assertEqual(self.session.get_remote_codecs("video"),
                         self.video_codecs)
        self.assertEqual(self.session.get_remote_candidates("video"),
                         self.video_candidates)


if __name__ == "__main__":
    sys.path.insert(0, "")
    from papyon.sip.ice import *
    unittest.main()
