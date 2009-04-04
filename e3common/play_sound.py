import os

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
        winsound.PlaySound(path, winsound.SND_FILENAME)
elif os.name == 'posix':
    try:
        import gst

        def play(path):
            """
            play a sound using gstreamer api
            """
            _player = gst.element_factory_make("playbin", "player")
            uri = "file://" + os.path.abspath(path)
            _player.set_property('uri', uri)
            _player.set_state(gst.STATE_PLAYING)
    except ImportError:
        if is_on_path('play'):
            play = lambda path: os.popen4('play ' + path)
        elif is_on_path('aplay'):
            play = lambda path: os.popen4('aplay ' + path)
        else:
            play = dummy_play
elif os.name == 'mac':
    from AppKit import NSSound
    def play(path):
        """
        play a sound using mac api
        """
        macsound = NSSound.alloc()
        macsound.initWithContentsOfFile_byReference_(soundPath, True)
        macsound.play()
else:
    play = dummy_play

