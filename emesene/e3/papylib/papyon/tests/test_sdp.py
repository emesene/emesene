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

import unittest
import sys

audio_definitions = [((8, "PCMA", 8000, None), "8 PCMA/8000", ""),
                     ((0, "PCMU", 8000, None), "0 PCMU/8000", ""),
                     ((101, "telephone-event", 8000, "0-16"), 
                      "101 telephone-event/8000", "101 0-16")]

video_definitions = [((34, "H263", 90000, None), "34 H263/90000", "")]

attributes = { "rtcp" : [42],
               "rtpmap" : ["8 PCMA/8000",
                           "0 PCMU/8000",
                           "101 telephone-event/8000"],
               "fmtp" : ["101 0-16"] }

msg_audio = """v=0
o=- 0 0 IN IP4 64.4.34.205
s=session
b=CT:99980
t=0 0
m=audio 42821 RTP/AVP 8 0 101
c=IN IP4 64.4.34.205
a=rtcp:41965
a=rtpmap:8 PCMA/8000
a=rtpmap:0 PCMU/8000
a=rtpmap:101 telephone-event/8000
a=fmtp:101 0-16
a=encryption:rejected"""

msg_video = """m=video 52826 RTP/AVP 34
c=IN IP4 192.168.1.116
a=x-caps:34 65537:352:288:15.0:256000:1;131074:176:144:15.0:180000:1
a=rtcp:37649
a=rtpmap:34 H263/90000
a=encryption:rejected"""

class CodecTestCase(unittest.TestCase):

    def testBuilding(self):
        for args, rtpmap, fmtp in audio_definitions:
            codec = SDPCodec(*args)
            self.assertEqual(codec.build_rtpmap(), rtpmap)

    def testParsing(self):
        for args, rtpmap, fmtp in audio_definitions:
            codec = SDPCodec()
            codec.parse_rtpmap(rtpmap)
            self.assertEqual(codec.payload, args[0])
            self.assertEqual(codec.encoding, args[1])
            self.assertEqual(codec.bitrate, args[2])

class MediaTestCase(unittest.TestCase):

    def setUp(self):
        self.media = SDPMedia("audio")
        self.codecs = []
        for args, rtpmap, fmtp in audio_definitions:
            self.codecs.append(SDPCodec(*args))

    def testRtcpAssigned(self):
        self.media.rtcp = 42
        self.assertEqual(self.media.rtcp, 42)

    def testRtcpAssignedTwice(self):
        self.media.rtcp = 10
        self.media.rtcp = 11
        self.assertEqual(self.media.rtcp, 11)

    def testAttributeGetter(self):
        self.media.set_attribute("attr", "value")
        self.assertEqual(self.media.get_attribute("attr"), "value")

    def testAttributesGetter(self):
        self.media.add_attribute("list", 1)
        self.media.add_attribute("list", 2)
        self.assertEqual(self.media.get_attributes("list"), [1, 2])

    def testUnexistingAttribute(self):
        self.assertEqual(self.media.get_attribute("foo"), None)

    def testSetCodecs(self):
        self.media.codecs = self.codecs
        self.assertEqual(self.media.get_attributes("rtpmap"),
            attributes["rtpmap"])
        self.assertEqual(self.media.get_attributes("fmtp"),
            attributes["fmtp"])

    def testParseAttributes(self):
        self.media.payload_types = ['8', '0', '101']
        for key, values in attributes.iteritems():
            for value in values:
                self.media.parse_attribute(key, value)
        self.assertEqual(self.media.rtcp, 42)
        self.assertEqual(self.media.codecs, self.codecs)

    def testListPayloadTypes(self):
        self.media.codecs = self.codecs
        self.assertEqual(self.media.payload_types, ['8', '0', '101'])

class MessageTestCase(unittest.TestCase):

    def setUp(self):
        self.message = SDPMessage()
        audio_codecs = []
        video_codecs = []
        for args, rtpmap, fmtp in audio_definitions:
            audio_codecs.append(SDPCodec(*args))
        for args, rtpmap, fmtp in video_definitions:
            video_codecs.append(SDPCodec(*args))
        self.audio = SDPMedia("audio", "64.4.34.205", 42821, 41965)
        self.audio.codecs = audio_codecs
        self.video = SDPMedia("video", "192.168.1.116", 52826, 37649)
        self.video.codecs = video_codecs

    def testParseMessageA(self):
        self.message.parse(msg_audio)
        medias = self.message.medias
        self.assertEqual(len(medias), 1)
        self.assertEqual(medias["audio"].ip, "64.4.34.205")
        self.assertEqual(medias["audio"].port, 42821)
        self.assertEqual(medias["audio"].rtcp, 41965)

    def testParseMessageAV(self):
        self.message.parse(msg_audio + "\r\n" + msg_video)
        medias = self.message.medias
        self.assertEqual(len(medias), 2)
        self.assertEqual(medias["audio"].ip, "64.4.34.205")
        self.assertEqual(medias["audio"].port, 42821)
        self.assertEqual(medias["audio"].rtcp, 41965)
        self.assertEqual(medias["video"].ip, "192.168.1.116")
        self.assertEqual(medias["video"].port, 52826)
        self.assertEqual(medias["video"].rtcp, 37649)

    def testBuildMessageA(self):
        self.message.medias["audio"] = self.audio
        print self.message

    def testBuildMessageAV(self):
        self.message.medias["audio"] = self.audio
        self.message.medias["video"] = self.video
        print self.message


if __name__ == "__main__":
    sys.path.insert(0, "")
    from papyon.sip.sdp import *
    unittest.main()
