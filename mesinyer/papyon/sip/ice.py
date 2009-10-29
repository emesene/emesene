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

from papyon.media import MediaCandidate, MediaCandidateEncoder, MediaSessionType
from papyon.media.constants import *
from papyon.util.encoding import *

import logging

logger = logging.getLogger('papyon.sip.ice')

class ICECandidateEncoder(MediaCandidateEncoder):
    """Class to encode and decode ICE media candidates from a SDP message.
       See section "4.3 Encoding the SDP" of the ICE draft for more
       details. Both versions 6 and 19 of the draft are supported."""

    def __init__(self):
        MediaCandidateEncoder.__init__(self)

    def encode_candidates(self, desc, local_candidates, remote_candidates):
        if desc.session_type is MediaSessionType.TUNNELED_SIP:
            draft = 19
        else:
            draft = 6

        if local_candidates:
            if draft is 19:
                desc.add_attribute("ice-ufrag", local_candidates[0].username)
                desc.add_attribute("ice-pwd", local_candidates[0].password)
            for candidate in local_candidates:
                attribute = ICECandidateBuilder.build_candidate(draft, candidate)
                desc.add_attribute("candidate", attribute)

        if remote_candidates:
            if draft is 6:
                remote_candidates = remote_candidates[0:1]
            list = [ICECandidateBuilder.build_remote_id(draft, candidate) \
                    for candidate in remote_candidates]
            name = (len(list) > 1 and "remote-candidates") or "remote-candidate"
            desc.add_attribute(name, " ".join(list))

    def decode_candidates(self, desc):
        local_candidates = []
        remote_candidates = []

        # Local candidates
        ufrag = desc.get_attribute("ice-ufrag")
        pwd = desc.get_attribute("ice-pwd")
        attributes = desc.get_attributes("candidate")
        if attributes is not None:
            if ufrag and pwd:
                draft = 19
            else:
                draft = 6

            for attribute in attributes:
                candidate = MediaCandidate(username=ufrag, password=pwd)
                try:
                    ICECandidateParser.parse_candidate(draft, candidate, attribute)
                except:
                    logger.warning('Invalid ICE candidate "%s"' % attribute)
                else:
                    local_candidates.append(candidate)

        # Remote candidates
        attribute = desc.get_attribute("remote-candidates")
        if attribute is None:
            attribute = desc.get_attribute("remote-candidate")
        if attribute is not None:
            try:
                remote_candidates = ICECandidateParser.parse_remote_id(attribute)
            except:
                logger.warning('Invalid ICE remote candidates "%s"' % attribute)

        return local_candidates, remote_candidates


    def get_default_candidates(self, desc):
        candidates = []
        candidates.append(MediaCandidate(component_id=COMPONENTS.RTP,
            ip=desc.ip, port=desc.port, transport="UDP", priority=1,
            type="host"))
        candidates.append(MediaCandidate(component_id=COMPONENTS.RTCP,
            ip=desc.ip, port=desc.rtcp, transport="UDP", priority=1,
            type="host"))
        return candidates


REL_EXT = [("typ", "type"), ("raddr", "base_ip"), ("rport", "base_port")]

class ICECandidateBuilder(object):
    """Class to build the ICE string representation of a MediaCandidate."""

    @staticmethod
    def build_candidate(draft, cand):
        if draft is 6:
            priority = float(cand.priority) / 1000
            return "%s %i %s %s %.3f %s %i" % (cand.username, cand.component_id,
                cand.password, cand.transport, priority, cand.ip, cand.port)
        elif draft is 19:
            ext = []
            for (name, attr) in REL_EXT:
                if getattr(cand, attr):
                    ext.append("%s %s" % (name, getattr(cand, attr)))
            return "%s %i %s %i %s %i %s" % (cand.foundation, cand.component_id,
                cand.transport, cand.priority, cand.ip, cand.port, " ".join(ext))

    @staticmethod
    def build_remote_id(draft, cand):
        if draft is 6:
            return cand.username
        elif draft is 19:
            return "%i %s %i" % (cand.component_id, cand.ip, cand.port)


class ICECandidateParser(object):
    """Class to parse a MediaCandidate from its ICE representation."""

    @staticmethod
    def parse_candidate(draft, cand, line):
        parts = line.split()

        if draft is 19:
            (cand.foundation, cand.component_id, cand.transport,
                cand.priority, cand.ip, cand.port) = parts[0:6]
            for i in range(6, len(parts), 2):
                key, val = parts[i:i + 2]
                for (name, attr) in REL_EXT:
                    if key == name:
                        setattr(cand, attr, val)
        elif draft is 6:
            (cand.username, cand.component_id, cand.password, cand.transport,
                cand.priority, cand.ip, cand.port) = parts[0:7]
            cand.foundation = cand.username[0:32]

        if draft is 19:
            cand.priority = int(cand.priority)
        if draft is 6:
            cand.priority = int(float(cand.priority) * 1000)
            if cand.priority < 0.5:
                cand.type = "relay"

        cand.component_id = int(cand.component_id)
        cand.username = fix_b64_padding(cand.username)
        cand.password = fix_b64_padding(cand.password)
        cand.port = int(cand.port)
        if cand.base_port is not None:
            cand.base_port = int(cand.base_port)

    @staticmethod
    def parse_remote_id(remote_id):
        candidates = []

        parts = remote_id.split(" ")
        if len(parts) == 1: # ICE 6
            candidates.append(MediaCandidate(foundation=parts[0]))
        else: #ICE 19
            for i in range(0, len(parts), 3):
                component_id = int(parts[i])
                ip = parts[i + 1]
                port = int(parts[i + 2])
                candidates.append(MediaCandidate(component_id=component_id,
                    ip=ip, port=port))

        return candidates
