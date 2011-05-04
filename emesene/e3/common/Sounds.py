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
import subprocess
import e3

HAVE_GSTREAMER = True
try:
    import pygst
    pygst.require("0.10")
    import gst

    def gst_on_message(bus, message, player):
        if message.type == gst.MESSAGE_EOS:
            player.set_state(gst.STATE_NULL)
    gst_player = gst.element_factory_make("playbin", "player")
    bus = gst_player.get_bus()
    bus.enable_sync_message_emission()
    bus.add_signal_watch()
    bus.connect('message', gst_on_message, gst_player)           
except ImportError:
    HAVE_GSTREAMER = False

def is_on_path(fname):
    """
    returns True if fname is the name of an executable on path (*nix only)
    """
    for p in os.environ['PATH'].split(os.pathsep):
        if os.path.isfile(os.path.join(p, fname)):
            return True

    return False

IS_WIN = True
try:
    import winsound
except ImportError:
    IS_WIN = False

IS_MAC = True
try:
    from AppKit import NSSound
except ImportError:
    IS_MAC = False

class SoundPlayer(object):
    '''Class used to play sounds'''
    def __init__(self, session):
        self.session = session
        if os.name == 'nt' and IS_WIN:
            self._play = self.win_play
        elif IS_MAC:
            self._play = self.mac_play
        elif os.name == 'posix':
            if HAVE_GSTREAMER:
                self._play = self.gstreamer_play
            elif is_on_path('play'):
                self._play = self.play_play
            elif is_on_path('aplay'):
                self._play = self.aplay_play
        else:
            self._play = self.dummy_play

    def play(self, path):
        if self.session.contacts.me.status != e3.status.BUSY and not \
           self.session.config.b_mute_sounds:
            self._play(path)

    def win_play(self, path):
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)

    def dummy_play(self, path):
        """
        dummy method used when no method is available
        """
        print "can't play", path

    def mac_play(self, path):
        """
        play a sound using mac api
        """
        macsound = NSSound.alloc()
        macsound.initWithContentsOfFile_byReference_(path, True)
        macsound.play()

    def gstreamer_play(self, path):
        gst_player.set_property('uri', "file://"+os.path.abspath(path))
        gst_player.set_state(gst.STATE_PLAYING)

    def aplay_play(self, path):
        subprocess.Popen(['aplay', path],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def play_play(self, path):
        subprocess.Popen(['play', path],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)