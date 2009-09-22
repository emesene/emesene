'''a base module to manage cache subdirectories'''
import os
import abc
import hashlib

def directory_exists(path):
    '''return true if path exists and is a directory
    '''
    return os.path.exists(path) and os.path.isdir(path)

def get_file_hash(file_path):
    '''return the hash of a file content located at file_path
    returns None if can't read from file
    '''

    if not os.access(file_path, os.R_OK):
        return None

    handle = file(file_path)
    sha = hashlib.sha1()

    chunk = handle.read(512)
    while chunk:
        sha.update(chunk)
        chunk = handle.read(512)

    return sha.hexdigest()


class Cache(object):
    '''a base class to manage cache subdirectories
    '''
    __metaclass__ = abc.ABCMeta

    def __init__(self, base_path, name='cache', init=False):
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

