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

__all__ = ['MediaCandidate', 'MediaCandidateEncoder']

class MediaCandidate(object):
    """Class representing a transport candidate."""

    def __init__(self, foundation=None, component_id=None, transport=None,
                 priority=None, username=None, password=None, type=None,
                 ip=None, port=None, base_ip=None, base_port=None):
        self.foundation = foundation
        self.component_id = component_id
        self.transport = transport
        self.priority = priority
        self.username = username
        self.password = password
        self.type = type
        self.ip = ip
        self.port = port
        self.base_ip = base_ip
        self.base_port = base_port

    def __eq__(self, other):
        return (self.foundation == other.foundation and
                self.component_id == other.component_id and
                self.transport == other.transport and
                self.priority == other.priority and
                self.username == other.username and
                self.password == other.password and
                self.type == other.type and
                self.ip == other.ip and
                self.port == other.port and
                self.base_ip == other.base_ip and
                self.base_port == other.base_port)

    def __repr__(self):
        return "<Media Candidate: %s>" % self.foundation


class MediaCandidateEncoder(object):
    """Class to encode and decode stream candidates into/from a media
       description."""

    def encode_candidates(self, media_stream, media_description):
        """Encode media_stream local and remote candidates into the
           given media_description."""
        pass

    def decode_candidates(self, media_description):
        """Decode local and remote candidates from the given
           media_description."""
        return [], []

    def get_default_candidates(self, media_description):
        """Create the set of default candidates from the media description."""
        return []
