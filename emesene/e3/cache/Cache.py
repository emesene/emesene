'''a base module to manage cache subdirectories'''
import os
import abc
import hashlib
import subprocess
import logging
log = logging.getLogger('e3.cache.Cache.py')

def directory_exists(path):
    '''return true if path exists and is a directory
    '''
    return os.path.exists(path) and os.path.isdir(path)

def get_file_path_hash(file_path):
    '''return the hash of a file content located at file_path
    returns None if can't read from file
    '''

    if not os.access(file_path, os.R_OK):
        return None

    handle = file(file_path)
    return get_file_hash(handle)

def get_file_hash(file_like_obj):
    '''return the hash (base64) of a file like object
    '''
    return get_file_digest(file_like_obj).encode("hex")

def get_file_digest(file_like_obj):
    '''return a sha digest of a file like object
    '''
    sha = hashlib.sha1()

    chunk = file_like_obj.read(1024)
    while chunk:
        sha.update(chunk)
        chunk = file_like_obj.read(1024)
    return sha.digest()

class Cache(object):
    '''a base class to manage cache subdirectories
    '''
    __metaclass__ = abc.ABCMeta

    def __init__(self, base_path, name='cache', init=True):
        '''constructor
        base_path -- the base path where the cache dir will be located
        name -- the name of the cache directory
        init -- if not found init
        '''
        self.base_path = os.path.abspath(base_path)
        self.path = os.path.join(self.base_path, name)
        self.info_name = name + '.info'
        self.info_path = os.path.join(self.path, self.info_name)
        self.name = name

        if init and not directory_exists(self.path):
            self.init()

    def init(self):
        '''create the directory
        '''
        os.makedirs(self.path)
        # just create the info file
        file(self.info_path, 'w').close()

    @abc.abstractmethod
    def parse(self):
        '''parse the file that contains the dir information and return it
        you have to implement it
        '''
        pass

    @abc.abstractmethod
    def list(self):
        '''return a list of the elements on the cache directory
        sorted by the order defined by the subclass
        '''
        pass

    @abc.abstractmethod
    def insert(self, item):
        '''insert a new item into the cache
        return True on success False otherwise
        '''
        pass

    @abc.abstractmethod
    def remove(self, item):
        '''remove an item from cache
        return True on success False otherwise
        '''
        pass

    @abc.abstractmethod
    def __contains__(self, name):
        '''return True if name is in cache, False otherwise
        this method is used to do something like
        if 'lolw00t' in cache: asd()
        '''
        pass

    def create_file(self, path, data):
        '''saves data to path
        '''
        data.seek(0)
        handle = file(path, 'w+b', 0700)
        handle.write(data.read())
        handle.close()

    def resize_with_imagemagick(self, image_path, new_path, new_width, new_height):
        convert_installed = False
        for path in os.environ["PATH"].split(os.pathsep):
            exe = os.path.join(path, "convert")
            if os.path.exists(exe) and os.access(exe, os.X_OK):
                convert_installed = True
        if convert_installed:
            command = "convert -resize '%sx%s>' '%s' '%s'" % (new_width,
                                                              new_height,
                                                              image_path,
                                                              new_path)
            value = subprocess.call(command, shell=True)
            if value != 0:
                log.debug("Error while resizing image: %s" % value)
            return value == 0
        else:
            log.warning("Can't resize animated gifs, install ImageMagick")
            return false
