'''a module to define a cache class for emoticons
'''
import Cache

import os
import tempfile
import shutil
import urllib

class EmoticonCache(Cache.Cache):
    '''a class to maintain a cache of an user emoticons
    '''

    def __init__(self, config_path, user):
        '''constructor
        config_path -- the path where the base configuration is located
        user -- the user account or identifier
        '''
        Cache.Cache.__init__(self, os.path.join(config_path,
            user.strip()), 'emoticons', True)

    def parse(self):
        '''parse the file that contains the dir information
        return a dictionary with the emoticon as key and the hash as value
        if an emoticon is more than once on the file the last will be returned
        '''
        emotes = {}
        try:
            with file(self.info_path) as handle:
                for line in handle.readlines():
                    shortcut, hash_ = line.split(' ', 1)
                    shortcut = urllib.unquote(shortcut)
                    emotes[shortcut] = hash_.strip()
        except:
            pass

        return emotes

    def list(self):
        '''return a list of the elements on the cache directory as tuples
        (emoticon, hash), duplicated shortcuts will be removed and the last
        appearance of the shortcut will be returned
        '''
        sorted_list = sorted(self.parse().items())
        return sorted_list

    def insert(self, item):
        '''insert a new item into the cache
        return the shortcut and the hash on success None otherwise
        item -- a tuple containing the shortcut and the path to an image
        '''
        shortcut, path = item
        hash_ = Cache.get_file_path_hash(path)

        if hash_ is None:
            return None

        new_path = os.path.join(self.path, hash_)
        shutil.copy2(path, new_path)
        return self.__add_entry(shortcut, hash_)

    def insert_raw(self, item):
        '''insert a new item into the cache
        return the information (stamp, hash) on success None otherwise
        item -- a tuple containing the shortcut and a file like object with the image
        '''
        shortcut, image = item
        position = image.tell()
        image.seek(0)
        hash_ = Cache.get_file_hash(image)

        if hash_ is None:
            return None

        path = os.path.join(self.path, hash_)
        self.create_file(path, image)

        image.seek(position)
        return self.__add_entry(shortcut, hash_)

    def insert_resized(self, item, filename, height = 50, width = 50):
        '''insert a new item into the cache with the specified filename
        resizing it if posible.
        return the shortcut and the hash on success None otherwise
        item -- a tuple containing the shortcut and the path to an image
        '''
        shortcut, image = item
        path = os.path.join(tempfile.gettempdir(), "emote")
        # save the incoming file so we can resize it using imagemagick
        self.create_file(path, image)
        self.resize_with_imagemagick(path, path, height, width)

        hash_ = Cache.get_file_path_hash(path)

        if hash_ is None:
            return None

        new_path = os.path.join(self.path, filename)
        shutil.copy2(path, new_path)
        return self.__add_entry(shortcut, filename)

    def has_emote(self, shortcut):
        '''Search an emote into cache.
        '''
        return shortcut in self.parse().keys()

    def __add_entry(self, shortcut, hash_):
        '''add an entry to the information file with the current timestamp
        and the hash_ of the file that was saved
        '''
        handle = file(self.info_path, 'a')
        handle.write('%s %s\n' % (urllib.quote(shortcut), hash_))
        handle.close()

        return shortcut, hash_

    def __remove_entry(self, hash_to_remove):
        '''remove an entry from the information file
        since self.list() removes duplicated shortcuts this will purge
        duplicated shortcuts.
        '''
        entries = self.list()

        handle = file(self.info_path, 'w')

        for stamp, hash_ in entries:
            if hash_ != hash_to_remove:
                handle.write('%s %s\n' % (str(stamp), hash_))

        handle.close()

    def add_entry(self, shortcut, hash_):
        '''wrapper method for custom emoticon manipulation'''
        return self.__add_entry(shortcut, hash_)

    def remove_entry(self, hash_to_remove):
        '''wrapper method for custom emoticon manipulation'''
        self.__remove_entry(hash_to_remove)

    def remove(self, item):
        '''remove an item from cache
        return True on success False otherwise
        item -- the name of the image to remove
        '''
        if item not in self:
            return False

        os.remove(os.path.join(self.path, item))
        self.__remove_entry(item)
        return True

    def __contains__(self, name):
        '''return True if name is in cache, False otherwise
        this method is used to do something like
        if 'lolw00t' in cache: asd()
        '''
        return os.path.isfile(os.path.join(self.path, name))

