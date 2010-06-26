import os
import subprocess

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
    if is_on_path('play'):
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
        macsound.initWithContentsOfFile_byReference_(soundPath, True)
        macsound.play()
else:
    play = dummy_play

