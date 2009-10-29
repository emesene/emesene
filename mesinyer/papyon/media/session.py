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

from papyon.event import EventsDispatcher
from papyon.media.stream import *

import gobject
import logging

logger = logging.getLogger('papyon.media.session')

__all__ = ['MediaSession']

class MediaSession(gobject.GObject, EventsDispatcher):
    """A media session represents a conference which may include multiple
       streams (audio, video). A session handler might have to be implemented
       on the client side to react to the adding/removing of streams (e.g. UI
       notification). See L{papyon.media.conference.MediaSessionHandler} for a
       default implementation using Farsight 2.0.

       The 'prepared' and 'ready' signals are meant to be handled by the media
       call. For example, we might need to send a session message to the other
       participants once the session is prepared (i.e. we discovered all local
       candidates and codecs)."""

    __gsignals__ = {
        'prepared': (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ()),
        'ready': (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            ())
    }

    def __init__(self, type):
        """Initialize the session

           @param type: Session type
           @type type: L{papyon.media.constants.MediaSessionType}
           @param msg_class: The session message class to use (e.g SDPMessage)
           @type msg_class: subclass of L{papyon.media.message.MediaSessionMessage}"""

        gobject.GObject.__init__(self)
        EventsDispatcher.__init__(self)
        self._type = type

        self._streams = []
        self._processing_message = False
        self._signals = {}

    @property
    def has_video(self):
        """Whether this session contain a video stream or not
           @rtype: bool"""
        return (self.get_stream("video") is not None)

    @property
    def streams(self):
        """List of streams
           @rtype: list of L{papyon.media.stream.MediaStream}"""
        return self._streams

    @property
    def prepared(self):
        """Are all streams prepared
           @rtype: bool"""
        if self._processing_message:
            return False
        for stream in self._streams:
            if not stream.prepared:
                return False
        return True

    @property
    def ready(self):
        """Are all streams ready
           @rtype: bool"""
        if self._processing_message:
            return False
        for stream in self._streams:
            if not stream.ready:
                return False
        return True

    @property
    def type(self):
        """Session type
           @rtype L{papyon.media.constants.MediaSessionType}"""
        return self._type

    def close(self):
        """Close the session and all contained streams."""

        for stream in self._streams[:]:
            self.remove_stream(stream)

    def create_stream(self, name, direction, created_locally=False):
        """Create a new media stream with the given name and direction.
           The created stream need to be added to the session using add_stream.

           @param name: Name of the stream (e.g. audio, video...)
           @type name: string
           @param direction: Direction of the stream
           @type direction: L{papyon.media.constants.MediaStreamDirection}
           @param created_locally: Created locally (outgoing call)
           @type created_locally: boolean

           @returns the new stream"""

        logger.debug("Create stream %s" % name)
        stream = MediaStream(self, name, direction, created_locally)
        self._dispatch("on_stream_created", stream)
        return stream

    def add_stream(self, stream):
        """Add a stream to the session and signal it that we are ready to
           handle its signals.

           @param stream: Stream to add
           @type stream: L{papyon.media.stream.MediaStream}"""

        sp = stream.connect("prepared", self.on_stream_prepared)
        sr = stream.connect("ready", self.on_stream_ready)
        self._streams.append(stream)
        self._signals[stream.name] = [sp, sr]
        self._dispatch("on_stream_added", stream)
        stream.activate()
        return stream

    def get_stream(self, name):
        """Find a stream by its name.

           @param name: Name of the stream to find
           @type name: string"""

        matching = filter(lambda x: x.name == name, self._streams)
        if not matching:
            return None
        else:
            return matching[0]

    def remove_stream(self, stream):
        """Close a stream and remove it from the session.

           @param stream: Stream to remove
           @type stream: L{papyon.media.stream.MediaStream}"""

        name = stream.name
        for handler_id in self._signals[name]:
            stream.disconnect(handler_id)
        del self._signals[name]
        stream.close()
        self._streams.remove(stream)
        self._dispatch("on_stream_removed", stream)

    def process_remote_message(self, msg, initial=False):
        """Parse the received session message and create media streams
           accordingly. The created streams are added but we only emit the
           'prepared' and 'ready' signals once all the descriptions are
           processed. 

           @param msg: Session message received from a peer
           @type msg: L{papyon.media.message.MediaSessionMessage}
           @param initial: Whether or not this is the first message received
           @type initial: boolean"""

        if not msg.descriptions:
            raise ValueError("Session message does not contain any information")

        self._processing_message = True

        for desc in msg.descriptions:
            stream = self.get_stream(desc.name)
            if stream is None:
                if initial:
                    stream = self.create_stream(desc.name, desc.direction)
                    self.add_stream(stream)
                else:
                    raise ValueError('Invalid stream "%s" in session message' % desc.name)
            stream.process_remote_description(desc)

        self._processing_message = False

        if initial:
            if self.prepared:
                self.emit("prepared")
            if self.ready:
                self.emit("ready")

    def on_stream_prepared(self, stream):
        if self.prepared:
            logger.debug("All media streams are prepared")
            self.emit("prepared")

    def on_stream_ready(self, stream):
        if self.ready:
            logger.debug("All media streams are ready")
            self.emit("ready")
