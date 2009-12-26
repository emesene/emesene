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

from papyon.util.decorator import rw_property

__all__ = ['MediaSessionMessage', 'MediaStreamDescription']

class MediaSessionMessage(object):
    """Class representing messages sent between call participants. It contains
       the different media descriptions. Different implementations need to
       override _create_stream_description, _parse and __str__ functions."""

    def __init__(self, session=None, body=None):
        self._descriptions = []
        if session is not None:
            self._build(session)
        elif body is not None:
            self._parse(body)

    @property
    def descriptions(self):
        """Media stream descriptions"""
        return self._descriptions

    def _create_stream_description(self, stream):
        raise NotImplementedError

    def _build(self, session):
        for stream in session.streams:
            desc = self._create_stream_description(stream)
            self._descriptions.append(desc)

    def _parse(self, body):
        raise NotImplementedError

    def __str__(self):
        raise NotImplementedError

class MediaStreamDescription(object):
    """Class representing a media stream description : name, direction and
       codecs. Implementations of this class might also contain informations
       about transport candidates. Such implementation should also override
       the property "candidate_encoder" to return a subclass of
       L{papyon.media.candidate.MediaCandidateEncoder} to encode and decode
       these informations.

       If the stream only accept a specific set of codecs, the function
       is_valid_codec must be overriden as well."""

    def __init__(self, stream=None, name=None, direction=None):
        self._name = name
        self._direction = direction
        self._session_type = None
        self._codecs = []

        self.ip = ""
        self.port = 0
        self.rtcp = 0

        if stream is not None:
            self._build(stream)

    @property
    def name(self):
        return self._name

    @property
    def direction(self):
        return self._direction

    @property
    def candidate_encoder(self):
        return None

    @property
    def session_type(self):
        return self._session_type

    @rw_property
    def codecs():
        def fget(self):
            return self._codecs
        def fset(self, value):
            self._codecs = value
        return locals()

    @property
    def valid_codecs(self):
        return filter(lambda c: self.is_valid_codec(c), self.codecs)

    def is_valid_codec(self, codec):
        return True

    def set_codecs(self, codecs):
        codecs = filter(lambda c: self.is_valid_codec(c), codecs)
        self.codecs = codecs

    def get_codec(self, payload):
        for codec in self._codecs:
            if codec.payload == payload:
                return codec
        raise KeyError("No codec with payload %i in media", payload)

    def set_candidates(self, local_candidates=None, remote_candidates=None):
        if self.candidate_encoder is not None:
            encoder = self.candidate_encoder
            encoder.encode_candidates(self, local_candidates, remote_candidates)

    def get_candidates(self):
        if self.candidate_encoder is not None:
            candidates = list(self.candidate_encoder.decode_candidates(self))
            if not candidates[0]:
                candidates[0] = self.candidate_encoder.get_default_candidates(self)
            return candidates
        return [], []

    def _build(self, stream):
        local_candidates = stream.get_active_local_candidates()
        remote_candidates = stream.get_active_remote_candidates()

        self._name = stream.name
        self._direction = stream.direction
        self._session_type = stream.session.type
        self.ip, self.port, self.rtcp = stream.get_default_address()
        self.set_codecs(stream.get_local_codecs())
        self.set_candidates(local_candidates, remote_candidates)

    def __repr__(self):
        return "<Media Description: %s>" % self.name
