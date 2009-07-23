import extension
from debugger import warning, debug

ERROR = False
try:
    import dbus
    import dbus.service
    from dbus.mainloop.glib import DBusGMainLoop
except ImportError, description:
    warning('failed some import on dbus: %s' % str(description))
    ERROR = True

if not ERROR:
    BUS_NAME = "com.emesene"

    def create_dbusmethod(func, in_sign, out_sign):
        type_map = {int: 'i', str:'s', list:'a', dict:'d'}
        if not out_sign:
            out_string = None
        else:
            out_string = ''
            for typ in out_sign:
                if typ in type_map:
                    out_string = '%s%s' % (out_string, type_map[typ])

        if not in_sign:
            in_string = None
        else:
            in_string = ''
            for typ in in_sign:
                if typ in type_map:
                    in_string = '%s%s' % (in_string, type_map[typ])
        
        class DBusMethod(dbus.service.Object):
            def __init__(self):
                bus_name = dbus.service.BusName(BUS_NAME, bus=dbus.SessionBus())
                dbus.service.Object.__init__(self, bus_name, '/com/emesene/%s' % func.__name__)
                self.func = func

            @dbus.service.method(BUS_NAME+'.extra', in_signature=in_string, out_signature=out_string)
            def callback(self, *args, **kwargs):
                return self.func(*args, **kwargs)
        
        method = DBusMethod()
        return method

    class DBus(object):
        provides=('external api', )
        def __init__(self):
            debug('instancing dbus')
            self.loop = DBusGMainLoop(set_as_default=True)
            self.session_bus = dbus.SessionBus()
            self.bus_name = dbus.service.BusName(BUS_NAME, bus=self.session_bus)

        def expose_method(self, name, callback, input_types, output_types):
            create_dbusmethod(callback, input_types, output_types)

        def delete_method(self, name, callback):
            return True

    extension.register('external api', DBus)


else: #ERROR
    class DummyExternalAPI(object):
        provides=('external api', )
        def __init__(self):
            pass
        def expose_method(self, name, callback, input_types, output_types):
            pass
        def delete_method(self, name, callback):
            pass
    extension.register('external api', DummyExternalAPI)


