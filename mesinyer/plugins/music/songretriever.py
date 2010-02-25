'''this module contains the logic to obtain the status and song of a music
player, you should register a new music player here.
 All the functions receive as first argument the name of the music player
and will look for the handler of that music player and call the apropiate
function there'''

__handlers = {}

# look at the bottom for the imports!

required_methods = ('is_running', 'is_playing', 'get_current_song')

class Song(object):
    '''a class representing a song'''

    def __init__(self, artist="?", album="?", title="?", filename="?"):
        self.artist     = artist
        self.album      = album
        self.title      = title
        self.filename   = filename

    def __repr__(self):
        return "%s - %s - %s" % (self.artist, self.album, self. title)

    def format(self, strfmt):
        '''replace vars in strfmt for the values of the song'''
        return strfmt.replace('%ARTIST%', self.artist).replace('%ALBUM%',
                self.album).replace('%TITLE%', self.title).replace('%FILE%',
                        self.filename)

def register(handler_name, handler):
    '''register a new music player, the module (or object)
    must have all the methods declared below but without receiving
    the name argument.
     returns False if the handler was not registered'''

    for name in required_methods:
        if not (hasattr(handler, name) and callable(getattr(handler, name))):
                logging.getLogger('music plugin').warning(
                    "handler %s could not be registered, no %s function" % \
                            (handler_name, name))
                return False

    __handlers[handler_name] = handler

def get_handler_names():
    return sorted(__handlers.keys())

## below are the methods that a handler should implement

def is_running(name):
    '''returns True if the player is running'''
    handler = __handlers.get(name, None)

    if handler is None:
        return False

    return handler.is_running()

def is_playing(name):
    '''returns True if the player is playing a song'''
    handler = __handlers.get(name, None)

    if handler is None:
        return False

    return handler.is_playing()

def get_current_song(name):
    '''returns the current song or None if no song is playing'''
    handler = __handlers.get(name, None)

    if handler is None:
        return None

    return handler.get_current_song()

def test():
    for name in __handlers:
        print "player", name
        print "running?:", is_running(name)
        print "playing?:", is_playing(name)
        print "current song:", get_current_song(name)
        print

import handler_mpd
import handler_amarok2
import handler_rhythmbox
import handler_gmusicbrowser
