import socket

import songretriever
import xml.dom.minidom
import urllib

class LastfmHandler(object):
    '''a simple handler for lastfm web service'''

    def __init__(self, login="Diftool80", update_interval=60):
        self.login = login
        self.update_interval = update_interval
        self.url = "http://ws.audioscrobbler.com/2.0/?method=\
                    user.getrecenttracks&api_key=fbb6f8beb8be\
                    b065baf549d57c73ac66&user=" + self.login + "&limit=1"
        self.track = None

        self.reconnect()

    def reconnect(self):
        '''reconnect, only call if disconnected.
        return True if connected'''
        try:
            page = urllib.urlopen(self.url)
            doc = xml.dom.minidom.parse(page)
            self.track = doc.getElementsByTagName('track')[0]
            return True
        except IOError:
            return False
        except socket.error:
            return False

    def is_running(self):
        '''returns True if the player is running'''
        return self.reconnect()

    def is_playing(self):
        '''returns True if the player is playing a song'''
        if not self.is_running():
            return False

        return self.track.getAttribute('nowplaying') == "true"

    def get_current_song(self):
        '''returns the current song or None if no song is playing'''
        if not self.is_running() or not self.is_playing():
            return None

        element = self.track.getElementsByTagName('artist')
        artist = element[0].childNodes[0].nodeValue
        element = self.track.getElementsByTagName('album')
        album = element[0].childNodes[0].nodeValue
        element = self.track.getElementsByTagName('name')
        title = element[0].childNodes[0].nodeValue

        return songretriever.Song(artist, album, title)

songretriever.register('lastfm', LastfmHandler)

