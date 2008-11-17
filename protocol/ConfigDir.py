import os

class ConfigDir(object):
    '''a class that handles the files and directories of the configuration'''

    def __init__(self, app_name, base_dir=None):
        '''constructor'''

        self.app_name = app_name

        if base_dir is None:
            self.base_dir = self.default_base_dir
        else:
            self.base_dir = base_dir

        self.create_if_not_exists('')

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

def _test():
    print 'remember to remove the config dir between tests :)'
    cfg = ConfigDir('emesene2')
    print 'defaul base dir:', cfg.default_base_dir
    print 'base dir:', cfg.base_dir
    print 'dir %s exists? %s' % (cfg.join('test', 'foo'), 
        cfg.dir_exists('test', 'foo'))
    print 'create if not exists'
    cfg.create_if_not_exists('test', 'foo')
    print 'file %s readable? %s' % (cfg.join('test', 'foo', 'config.txt'), 
        cfg.file_readable('test', 'foo', 'config.txt'))
    print 'write some content to the file'
    cfg.write('this is the content!', 'test', 'foo', 'config.txt')
    print 'the content written is:'
    print cfg.read('test', 'foo', 'config.txt')

if __name__ == '__main__':
    _test()
