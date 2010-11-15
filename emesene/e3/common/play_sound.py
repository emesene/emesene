import os
import subprocess

HAVE_GSTREAMER = 1
try:
    import pygst
    pygst.require("0.10")
    import gst
except ImportError:
    HAVE_GSTREAMER = 0

def is_on_path(fname):
    """
    returns True if fname is the name of an executable on path (*nix only)
    """
    for p in os.environ['PATH'].split(os.pathsep):
        if os.path.isfile(os.path.join(p, fname)):
            return True

    return False

def dummy_play(path):
    """
    dummy method used when no method is available
    """
    print "can't play", path

if os.name == 'nt':
    import winsound

    def play(path):
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
elif os.name == 'posix':
    if HAVE_GSTREAMER:
        def play(path):
            def gst_on_message(bus, message, player):
                if message.type == gst.MESSAGE_EOS:
                    player.set_state(gst.STATE_NULL)
            player = gst.element_factory_make("playbin", "player")
            bus = player.get_bus()
            bus.enable_sync_message_emission()
            bus.add_signal_watch()
            bus.connect('message', gst_on_message, player)
            player.set_property('uri', "file://"+os.path.abspath(path))
            player.set_state(gst.STATE_PLAYING)
    elif is_on_path('play'):
        def play(path):
            subprocess.Popen(['play', path],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    elif is_on_path('aplay'):
        def play(path):
            subprocess.Popen(['aplay', path],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    else:
        play = dummy_play
elif os.name == 'mac':
    from AppKit import NSSound
    def play(path):
        """
        play a sound using mac api
        """
        macsound = NSSound.alloc()
        macsound.initWithContentsOfFile_byReference_(path, True)
        macsound.play()
else:
    play = dummy_play

