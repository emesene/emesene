import os

class ConfigDir(object):
    '''a class that handles the files and directories of the configuration'''

    def __init__(self, app_name, base_dir=None):
        '''constructor'''

        self.app_name = app_name

        self.paths = {}

        if base_dir is None:
            self.base_dir = self.default_base_dir
        else:
            self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

        self.create_if_not_exists('')

    def add_path(self, name, path, create_if_not_exists=True):
        '''add a path with a name to the registered paths, if
        the path is relative to base_dir
        create_if_not_exists is True, do that ;)

        returns: the full path
        '''
        path = self.join(path)
        self.paths[name] = self.join(path)

        if create_if_not_exists and not os.path.exists(path):
            os.makedirs(path)

        return path

    def get_path(self, name, default=None):
        '''return the path identified by name, if not available return default
        '''
        return self.paths.get(name, default)

    def _get_default_base_dir(self):
        '''return the default base dir for configuration according to the OS'''
        if os.name == 'posix' or os.name == 'nt' or os.name == 'mac':
            return os.path.expanduser(os.path.join('~', '.config',
                self.app_name))
        else:
            return os.path.abspath(self.app_name)

    default_base_dir = property(fget=_get_default_base_dir)

    def dir_exists(self, *dirs):
        '''returns True if the path inside the dir exists False otherwise,
        an example is cfg.dir_exists('cache', 'images')
        we take care of joining them'''

        return os.path.isdir(self.join(*dirs))

    def join(self, *paths):
        '''join the base dir with the paths received as parameters'''
        return os.path.join(self.base_dir, *paths)

    def file_readable(self, *paths):
        '''returns True if the path exists, is a file and is readable
        an example is cfg.dir_exists('cache', 'images', 'sarah-palin-lulz.jpg')
        we take care of joining them'''
        path = self.join(*paths)

        return os.path.isfile(path) and os.access(path, os.R_OK)

    def create(self, *dirs):
        '''create all the dirs to the path starting from the base config path'''

        current = self.base_dir
        for directory in dirs:
            current = os.path.join(current, directory)

            if not os.path.isdir(current):
                os.mkdir(current)

    def create_if_not_exists(self, *dirs):
        '''the name says it all :)'''

        if not self.dir_exists(*dirs):
            self.create(*dirs)

    def read(self, *paths):
        '''return the content of a file if exists, none otherwise'''

        if self.file_readable(*paths):
            return file(self.join(*paths), 'r').read()

        return None

    def write(self, content, *paths):
        '''write the content of a file to the path specified'''

        fd = file(self.join(*paths), 'w')
        fd.write(content)
        fd.close()

