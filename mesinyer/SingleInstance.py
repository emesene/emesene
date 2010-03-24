import os
import tempfile
import getpass


class SingleInstance:
    def __init__(self):

        self._bus_name = 'org.emesene.dbus'
        self._object_path = '/org/emesene/dbus'

        self.new_dbus = False
        self.have_dbus = False

        if os.name == 'posix':
            try:
                import dbus, dbus.service
                dbus_version = getattr(dbus, 'version', (0, 0, 0))
                if dbus_version >= (0, 41, 0):
                    import dbus.glib
                if dbus_version >= (0, 80, 0):
                    from dbus.mainloop.glib import DBusGMainLoop
                    DBusGMainLoop(set_as_default=True)
                    self.new_dbus = True
                else:
                    import dbus.mainloop.glib
                    self.new_dbus = False
                self.have_dbus = True
            except dbus.DBusException, error:
                self.have_dbus = False
                print 'Unable to use D-Bus: %s' % str(error)

        self.lock_file_name = os.path.normpath(tempfile.gettempdir() +
                            '/emesene-' + getpass.getuser() + '.lock')
        self.lock_file = None

    def emesene_is_running(self):
        '''Checks if emesene is already running'''
        if os.name == 'posix':
            import fcntl
            self.lock_file = open(self.lock_file_name, 'w')
            try:
                fcntl.lockf(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                return True
            return False
        else:
            try:
                # if file already exists, we try to remove it
                # (in case a previous execution was interrupted)
                if os.path.exists(self.lock_file_name):
                    os.unlink(self.lock_file_name)
                self.lock_file =  os.open(self.lock_file_name,
                                 os.O_CREAT | os.O_EXCL | os.O_RDWR)
            except OSError, error:
                if error.errno == 13:
                    return True
                print error.errno
                return False
            return False
                
    def show(self):
        ''' tries to bring to front the instance of emesene
        that is already running'''
        if self.have_dbus == False:
            # Is there a no dbus way to do this?
            return
        try:
            emesene_bus = dbus.SessionBus()
            emesene_object = emesene_bus.get_object(self._bus_name, self._object_path)
            emesene_object.show()
        except dbus.DBusException, error:
            print "Can't bring old instance of emesene to front: %s" % error

    def __del__(self):
        '''Be sure that the file will be closed and deleted in windows'''
        if os.name == 'nt':
            if hasattr(self, 'lock_file'):
                os.close(self.lock_file)
                os.unlink(self.lock_file_name)


