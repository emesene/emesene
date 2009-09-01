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
    BUS_NAME = "com.gtk.emesene"
    BUS_PATH = "/com/gtk/emesene"

    
    def create_function(name,Qargs):
        '''hack to create a function with a certain number of arguments'''
        def y():
            pass
        
        y_code = types.CodeType(args,\
                    y.func_code.co_nlocals,\
                    y.func_code.co_stacksize,\
                    y.func_code.co_flags,\
                    y.func_code.co_code,\
                    y.func_code.co_consts,\
                    y.func_code.co_names,\
                    y.func_code.co_varnames,\
                    y.func_code.co_filename,\
                    name,\
                    y.func_code.co_firstlineno,\
                    y.func_code.co_lnotab
                )
        return types.FunctionType(y_code, y.func_globals, name)

    def create_dbus_method(name, func, in_sign, out_sign):
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
        
        real_func_name = func.__name__
        func.__name__ = 'callback' #so ugly hack, but it makes the magic work
        class DBusMethod(dbus.service.Object):
            #we are decorating func!
            callback =  dbus.service.method('%s.%s' % (BUS_NAME,name),
                    in_signature=in_string, out_signature=out_string)(func)
            def __init__(self):
                bus_name = dbus.service.BusName(BUS_NAME, bus=dbus.SessionBus())
                dbus.service.Object.__init__(self, bus_name, '%s/%s' % (BUS_PATH, real_func_name))
        method = DBusMethod()
        return method

    def create_dbus_event(name, out_sign):
        type_map = {int: 'i', str:'s', list:'a', dict:'d'}
        if not out_sign:
            out_string = None
        else:
            out_string = ''
            for typ in out_sign:
                if typ in type_map:
                    out_string = '%s%s' % (out_string, type_map[typ])
        #create a function with right number of arguments (len(out_string+1))
        func = create_function('event', len(out_string)+1)

        class DBusEvent(dbus.service.Object):
            event = dbus.service.signal('%s.%s' % (BUS_NAME, name),
                    signature=out_string)(func)
            def __init__(self):
                bus_name = dbus.service.BusName(BUS_NAME, bus=dbus.SessionBus())
                dbus.service.Object.__init__(self, bus_name, '%s/%s' % (BUS_PATH, name))
        
        evnt = DBusEvent()
        return evnt
                


    @extension.implements('external api')
    class DBus(object):
        def __init__(self):
            debug('instancing dbus') 
            self.loop = DBusGMainLoop(set_as_default=True)
            self.session_bus = dbus.SessionBus()
            self.bus_name = dbus.service.BusName(BUS_NAME, bus=self.session_bus)

            self.objects = {} #name: instance
            self.events = {} #name: instance

        def expose_method(self, name, callback, input_types, output_types):
            if name in self.objects:
                self.delete_method(name)
            self.objects[name] = create_dbus_method(name, callback, input_types, output_types)

        def delete_method(self, name):
            self.objects[name].remove_from_connection()

        def expose_event(self, name, output_types):
            self.events[name] = create_dbus_event(name, output_types)

        def emit_event(self, name, *args):
            if not name in self.events:
                raise ValueError
            self.events[name].event(*args)


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

class expose(object):
	'''This is actually a decorator. It can be used to easily expose a method'''
	def __init__(self, in_sign, out_sign):
		self.in_sign = in_sign
		self.out_sign = out_sign
	
	def __call__(self, func):
		external = extension.get_and_instantiate('external api')
		external.expose_method(func.__name__, func, self.in_sign, self.out_sign)
		

