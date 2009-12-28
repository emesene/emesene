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

from papyon.media import MediaCodec, MediaStreamDescription, MediaSessionMessage
from papyon.media.constants import *
from papyon.sip.ice import ICECandidateEncoder
from papyon.util.decorator import rw_property
from papyon.util.odict import odict

import logging

logger = logging.getLogger('papyon.sip.sdp')


class SDPMessage(MediaSessionMessage):

    def __init__(self, session=None, body=None):
        self._ip = ""
        MediaSessionMessage.__init__(self, session, body)

    @property
    def ip(self):
        if self._ip == "" and len(self._descriptions) > 0:
            return self._descriptions[0].ip
        return self._ip

    def _create_stream_description(self, stream):
        return SDPDescription(stream)

    def __str__(self):
        out = []
        out.append("v=0")
        out.append("o=- 0 0 IN IP4 %s" % self.ip)
        out.append("s=session")
        out.append("b=CT:99980")
        out.append("t=0 0")

        for desc in self._descriptions:
            types = " ".join(desc.payload_types)
            out.append("m=%s %i RTP/AVP %s" % (desc.name, desc.port, types))
            out.append("c=IN IP4 %s" % desc.ip)
            for (k, v) in desc.attributes.items():
                for value in v:
                    out.append("a=%s:%s" % (k, value))

        return "\r\n".join(out) + "\r\n\r\n"

    def _parse(self, message):
        desc = None

        for line in message.splitlines():
            line = line.strip()
            if not line:
                continue
            if len(line) < 2 or line[1] != '=':
                logger.warning('Invalid line "%s" in message ignored', line)
                continue

            key = line[0]
            val = line[2:]

            try:
                if key == 'o':
                    self._ip = val.split()[5]
                elif key == 'm':
                    desc = SDPDescription(name=val.split()[0],
                            direction=MediaStreamDirection.BOTH)
                    desc.port = int(val.split()[1])
                    desc.ip = self.ip # default IP address
                    desc.rtcp = desc.port + 1 # default RTCP port
                    desc.payload_types = val.split()[3:]
                    self.descriptions.append(desc)
                elif key == 'c':
                    if desc is None:
                        self._ip = val.split()[2]
                    else:
                        desc.ip = val.split()[2]
                elif key == 'a':
                    if desc is None:
                        continue
                    if ':' in val:
                        subkey, subval = val.split(':', 1)
                        desc.parse_attribute(subkey, subval)
                    else:
                        desc.add_attribute(val)
            except:
                self._descriptions = []
                raise ValueError('Invalid value "%s" for field "%s"' % (val, key))


class SDPDescription(MediaStreamDescription):

    _candidate_encoder = ICECandidateEncoder()

    def __init__(self, stream=None, name=None, direction=None):
        self._attributes = odict({"encryption": ["rejected"]})
        MediaStreamDescription.__init__(self, stream, name, direction)

    @property
    def candidate_encoder(self):
        return self._candidate_encoder

    @property
    def attributes(self):
        return self._attributes

    @rw_property
    def rtcp():
        def fget(self):
            return self.get_attribute("rtcp")
        def fset(self, value):
            self.set_attribute("rtcp", value)
        return locals()

    @rw_property
    def codecs():
        def fget(self):
            return self._codecs
        def fset(self, value):
            self._codecs = value
            self.delete_attributes("rtpmap")
            self.delete_attributes("fmtp")
            for codec in value:
                rtpmap = SDPCodecBuilder.build_rtpmap(codec)
                self.add_attribute("rtpmap", rtpmap)
                if codec.params:
                    fmtp = SDPCodecBuilder.build_fmtp(codec)
                    self.add_attribute("fmtp", fmtp)
                caps = XCAPS[self.name].get(codec.payload, None)
                if caps is not None:
                    self.add_attribute("x-caps", caps)
        return locals()

    @rw_property
    def payload_types():
        def fget(self):
            return map(lambda x: str(x.payload), self._codecs)
        def fset(self, value):
            for payload in value:
                codec = MediaCodec(int(payload))
                if codec.payload in EXTRA_PARAMS:
                    codec.params = EXTRA_PARAMS[codec.payload]
                self._codecs.append(codec)
        return locals()

    def is_valid_codec(self, codec):
        return codec.encoding.lower() in VALID_CODECS[self.name]

    def parse_attribute(self, key, value):
        try:
            if key == "rtcp":
                self.rtcp = int(value)
            else:
                if key == "rtpmap":
                    payload, values = SDPCodecParser.parse_rtpmap(value)
                    codec = self.get_codec(payload)
                    codec.encoding = values[0]
                    codec.clockrate = values[1]
                elif key == "fmtp":
                    payload, params = SDPCodecParser.parse_fmtp(value)
                    codec = self.get_codec(payload)
                    codec.params = params
                self.add_attribute(key, value)
        except ValueError:
            logger.warning("Invalid %s media attribute (%s)" % (key, value))
        except KeyError:
            logger.warning("Found %s attribute for invalid payload (%i)" %
                    (key, payload))

    def add_attribute(self, key, value=None):
        self._attributes.setdefault(key, []).append(value)

    def set_attribute(self, key, value):
        self._attributes[key] = [value]

    def get_attributes(self, key):
        return self._attributes.get(key, None)

    def get_attribute(self, key):
        values = self.get_attributes(key)
        if values is not None:
            return values[0]
        return None

    def delete_attributes(self, key):
        if key in self._attributes:
            del self._attributes[key]


class SDPCodecBuilder(object):

    @staticmethod
    def build_rtpmap(codec):
        return "%i %s/%i" % (codec.payload, codec.encoding, codec.clockrate)

    @staticmethod
    def build_params_list(codec):
        if not codec.params:
            return ""
        params = []
        for (key, value) in codec.params.items():
            if key == "events":
                params.append("0-16")
            else:
                params.append("%s=%s" % (key, value))
        return " ".join(params)

    @staticmethod
    def build_fmtp(codec):
        return "%i %s" % (codec.payload, SDPCodecBuilder.build_params_list(codec))


class SDPCodecParser(object):

    @staticmethod
    def parse_rtpmap(rtpmap):
        payload, codec = rtpmap.split()
        encoding = codec.split('/')[0]
        clockrate = int(codec.split('/')[1])
        return (int(payload), (encoding, clockrate))

    @staticmethod
    def parse_fmtp(fmtp):
        result = {}
        params = fmtp.split()
        payload = int(params[0])
        for param in params[1:]:
            if '=' in param:
                key, value = param.split('=')
            else:
                key = "events"
                value = "0-15"
            result[key] = value
        return payload, result
