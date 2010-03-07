'''this module contains the logic to obtain the status and song of a music
player, you should register a new music player here.
 All the functions receive as first argument the name of the music player
and will look for the handler of that music player and call the apropiate
function there'''

import os
import paths
import urllib

__handlers = {}
__active_handlers = {}

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

# get_cover_image_path default
# where should I put this?
def get_base_cover_path(song):
    '''searches in the local covers cache
    if not found also searches in albumart covers website
    returns None if no image found'''
    
    artist = song.artist.encode('utf8')
    album = song.album.encode('utf8')

    if len(artist) == 0 and len(album) == 0:
        return None

    cover_art_path = os.path.join(paths.HOME_DIR, '.covers', '')

    image_path = cover_art_path + artist + '-' + album + '.jpg'

    if os.path.exists(image_path):
        return image_path

    # Not found locally, let's try albumart.org

    url = "http://www.albumart.org/index.php?srchkey=" + \
        urllib.quote_plus(artist) + "+" + urllib.quote_plus(album) + \
        "&itempage=1&newsearch=1&searchindex=Music"

    albumart = urllib.urlopen(url).read()
    image_url = ""

    for line in albumart.split("\n"):

        if "http://www.albumart.org/images/zoom-icon.jpg" in line:
            image_url = line.partition('src="')[2].partition('"')[0]

        if image_url:
            urllib.urlretrieve(image_url, image_path)
            break

    if os.path.exists(image_path):
        return image_path

    return None

## This method can (but not must) be implemented in Handler

def get_cover_path(name):
    '''get the current song cover image path'''

    handler = get_handler(name)

    if handler is None:
        return None

    method = "get_cover_path"

    if (hasattr(handler, method) and callable(getattr(handler, method))):
        # get_cover_path defined in handler
        image_path = handler.get_cover_path()
        # check it
        if image_path is not None and os.path.exists(image_path):
            return image_path

    # if not defined, or handler hasn't found image path,
    # we use here a "base" implementation

    song = handler.get_current_song()
    return get_base_cover_path(song)

## below are the methods that a handler should implement
def get_current_song(name):
    ''' returns current song info'''
    handler = get_handler(name)

    if handler is None:
        return None

    return handler.get_current_song()

def is_running(name):
    '''returns True if the player is running'''
    handler = get_handler(name)

    if handler is None:
        return False

    return handler.is_running()

def is_playing(name):
    '''returns True if the player is playing a song'''
    handler = get_handler(name)

    if handler is None:
        return False

    return handler.is_playing()

def get_handler(name):
    '''try to get the handler from the active handlers, if not active
    create an instance'''
    instance = __active_handlers.get(name, None)

    if instance is None:
        handler = __handlers.get(name, None)

        if handler is None:
            return None

        instance = handler()

    __active_handlers[name] = instance
    return instance

def test():
    for name in __handlers:
        print "player", name
        print "running?:", is_running(name)
        print "playing?:", is_playing(name)
        print "current song:", get_current_song(name)
        print

import handler_amarok2
import handler_audacious2
import handler_banshee
import handler_gmusicbrowser
import handler_guayadeque
import handler_mpd
import handler_rhythmbox
import handler_xmms2

