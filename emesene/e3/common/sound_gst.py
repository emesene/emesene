# -*- coding: utf-8 -*-

#    This file is part of emesene.
#
#    emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
import gobject

#check for gi
def is_gi():
    return hasattr(gobject, '_introspection_module')

if is_gi():
    from gi.repository import Gst

    class GstPlayer(object):
        def __init__(self):
            Gst.init(None)
            self.gst_player = Gst.ElementFactory.make("playbin", "player")
            bus = self.gst_player.get_bus()
            bus.enable_sync_message_emission()
            bus.add_signal_watch()
            bus.connect('message::eos', self.gst_on_message, self.gst_player)

        def gst_on_message(self, bus, message, player):
            player.set_state(Gst.State.NULL)

        def play(self, path):
            self.gst_player.set_property('uri', "file://"+os.path.abspath(path))
            self.gst_player.set_state(Gst.State.PLAYING)
else:
    #XXX: use old static bindings
    import pygst
    import gst

    class GstPlayer(object):
        def __init__(self):
            self.gst_player = gst.element_factory_make("playbin", "player")
            bus = self.gst_player.get_bus()
            bus.enable_sync_message_emission()
            bus.add_signal_watch()
            bus.connect('message', self.gst_on_message, self.gst_player)

        def gst_on_message(self, bus, message, player):
            if message.type == gst.MESSAGE_EOS:
                player.set_state(gst.STATE_NULL)

        def play(path):
            self.gst_player.set_property('uri', "file://"+os.path.abspath(path))
            self.gst_player.set_state(gst.STATE_PLAYING)

