# -*- coding: utf-8 -*-
#
# Copyright (C) 2007  Ali Sabil <ali.sabil@gmail.com>
# Copyright (C) 2007  Johann Prieur <johann.prieur@gmail.com>
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

"""Media event interfaces

The interfaces defined in this module allow receiving notification events
from a L{MediaSession<papyon.media.MediaSession>} object and a
L{MediaStream<papyon.media.MediaStream> object."""

from papyon.event import BaseEventInterface

import weakref

__all__ = ["MediaSessionEventInterface", "MediaStreamEventInterface"]


class MediaSessionEventInterface(BaseEventInterface):
    """interfaces allowing the user to get notified about events
    from a L{MediaSession<papyon.media.MediaSession>}  object."""

    def __init__(self, session):
        """Initializer
            @param session: the media session we want to be notified for its events
            @type session: L{MediaSession<papyon.media.MediaSession>}"""
        BaseEventInterface.__init__(self, session)
        self._session = weakref.proxy(session)

    def on_stream_added(self, stream):
        """Called when a new stream is added to the session
            @param stream: the media stream added
            @type stream: L{MediaStream<papyon.media.MediaStream>}"""
        pass

    def on_stream_created(self, stream):
        """Called when a stream is created upon a peer request
            @param stream: the new media stream
            @type stream: L{MediaStream<papyon.media.MediaStream>}"""
        pass

    def on_stream_removed(self, stream):
        """Called when a new stream is removed from the session
            @param stream: the new media stream
            @type stream: L{MediaStream<papyon.media.MediaStream>}"""
        pass


class MediaStreamEventInterface(BaseEventInterface):
    """interfaces allowing the user to get notified about events
    from a L{MediaSession<papyon.media.MediaSession>}  object."""

    def __init__(self, stream):
        """Initializer
            @param stream: the media stream we want to be notified for its events
            @type stream: L{MediaStream<papyon.media.MediaStream>}"""
        BaseEventInterface.__init__(self, stream)
        self._stream = weakref.proxy(stream)

    def on_stream_closed(self):
        """Called when the stream is closing"""
        pass

    def on_remote_codecs_received(self, codecs):
        """Called when the remote codecs for this stream are received
            @param codecs: the remote codecs
            @type codecs: L{SDPCodec<papyon.sip.sdp.SDPCodec>}"""
        pass

    def on_remote_candidates_received(self, candidates):
        """Called when the remote candidates for this stream are received
            @param candidates: the remote candidates
            @type candidates: L{ICECandidate<papyon.sip.ice.ICECandidate>}"""
        pass
