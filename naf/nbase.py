import time
import random
import functools
import Queue
import inspect

import protocol.Action as Action

class Session(object):
    '''base class for session object, contains basic session information'''

    def __init__(self, id_):
        self.id_ = id_
        self.events = Queue.Queue()
        self.actions = Queue.Queue()

    def add_event(self, id_, *args):
        '''add an event to the events queue'''
        self.events.put(Event(id_, tuple(args)))

class Event(object):
    '''a class that contains an event information'''

    def __init__(self, id_, args):
        self.id_ = id_
        self.args = args

    def dict(self):
        '''return a dict representation of the object'''
        return {'id_': self.id_, 'args': self.args}

class validate(object):
    def __init__(self, *values):
        self.values = values

    def __call__(self, function):
        (args, varargs, varkw, function.defaults) = inspect.getargspec(function)

        function.values = self.values

        if function.defaults is not None:
            function.args_def = args[-len(function.defaults):]
            function.args = args[:-len(function.defaults)]
        else:
            function.args_def = []

        function.args = args[2:]

        @functools.wraps(function)
        def wrapper(*f_args, **f_kwds):

            final_args = []

            # add self and session
            final_args.append(f_args[0])
            final_args.append(f_args[0].session)
            
            for (index, arg) in enumerate(f_args[1:]):
                if type(arg) != self.values[index]:
                    raise ValueError('Type of arg ' + str(index + 2) \
                      + ' is invalid\n' + str(self.values[index]) + \
                      ' expected got ' + str(type(arg)))
                final_args.append(arg)

            return function(*final_args)

        return wrapper

class ServerBase(object):
    '''a class that contins all the methods used by the other servers'''

    def __init__(self):
        '''class constructor'''
        self.event_names = []
        # contains the event id as key and the event name as value
        self.event_to_name = {} 
        self.max_event_index = 0
        self.max_getter_index = 0
        self.max_action_index = 0
    
    @classmethod
    def new_session(cls):
        '''generate and return a session identifier'''
        return str(time.time()) + str(random.random())
    
    def add_event(self, session, id_, args=()):
        '''add an event to the session queue'''
        session.events.put(Event(id_, args))

    def add_action(self, session, id_, args=()):
        '''add an event to the session queue'''
        session.actions.put(Action(id_, args))

    @validate()
    def get_events(self, session):
        '''return the events on the session'''
        events = []

        try:
            while True:
                event = session.events.get(False)
                events.append(event.dict())
        except Queue.Empty:
            pass

        print {'events': events}

    def build(self):
        # event stuff
        sorted = list(self.event_names)
        sorted.sort()
        self.event_names = tuple(sorted)

        for (index, event) in enumerate(self.event_names):
            attr = 'EVENT_' + event.upper().replace(' ', '_')
            method = '_event_' + event.replace(' ', '_')

            setattr(self, attr, index)
            setattr(self, method, 
                lambda session, id_, args: 
                    self.add_event(session, id_, args))
            self.event_to_name[index] = event
        
        self.max_event_index = index

        # action and get stuff
        
        dct = dict(inspect.getmembers(self, lambda x: inspect.ismethod(x)))

        vars = dct.keys()
        vars.sort();

        getters = [(x.replace('get_', ''), dct[x])
                    for x in vars if x.startswith('get_')]

        actions = [(x.replace('do_', ''), dct[x])
                    for x in vars if x.startswith('do_')]
        
        self.__add_attrs('GET_', getters, 'getter',  'get_handlers')
        self.__add_attrs('ACTION_', actions, 'action', 'action_handlers')

    def __add_attrs(self, prefix, items, collection_name, handlers_name):
        if len(items) == 0:
            return

        all_handlers = []

        for (index, (item, handler)) in enumerate(items):
            attr = prefix + item.upper()
            setattr(self, attr, index)
            all_handlers.append(handler)

        setattr(self, 'max_' + collection_name + '_index', index)
        setattr(self, handlers_name, tuple(all_handlers))

    def documentation(self):
        '''print the documentation of the object'''
        members = inspect.getmembers(self)
        events = [(attr[0].replace('_', ' '), attr[1]) for attr in members \
            if attr[0].startswith('EVENT_')]
        actions = [(attr[0].replace('_', ' '), attr[1]) for attr in members \
            if attr[0].startswith('ACTION_')]
        getters = [(attr[0].replace('_', ' '), attr[1]) for attr in members \
            if attr[0].startswith('GET_')]

        events.sort(cmp=lambda x, y: cmp(x[0], y[0]))
        actions.sort(cmp=lambda x, y: cmp(x[0], y[0]))
        getters.sort(cmp=lambda x, y: cmp(x[0], y[0]))

        events = [(name.replace(' ', '_'), value) for (name, value) in events]
        actions = [(name.replace(' ', '_'), value) for (name, value) in actions]
        getters = [(name.replace(' ', '_'), value) for (name, value) in getters]

        def document_constants(group_name, constants):
            '''format and print a list of constants'''
            print 
            print group_name, ':'
            
            for (name, value) in constants:
                print name, ':', value

        def document_list(group_name, prefix, constants):
            '''print a list of strings that are useful to build the client'''
            const_list = [value[0][len(prefix):].replace('_', ' ').lower() \
             for value in constants]

            print group_name, '=', repr(const_list)
            print

        def get_arg_list(method_name):
            '''return a list of arguments'''
            try:
                method = getattr(self, method_name)

                args = []
                for (arg, type_) in zip(method.args, method.values):
                    args.append(arg + ' : ' + type_.__name__)

                args = ', '.join(args) 

                defaults = []
                for (arg, type_, default) in zip(method.args_def, \
                  method.values[-len(method.args_def):], method.defaults or []):
                    defaults.append(arg + '=' + repr(default) + ' : ' \
                        + type_.__name__)

                defaults = ', '.join(defaults)

                if defaults != '':
                    defaults = ', ' + defaults

                return args + defaults
            except AttributeError, e:
                return '?'

        def document_methods(title, prefix, method_prefix, constants):
            '''document the methods'''
            print title + ':'
            print
            const_list = [(value[0][len(prefix):].replace('_', ' ').lower(),
             method_prefix + value[0][len(prefix):].lower())\
             for value in constants]

            for (name, method) in const_list:
                print name + '(' + get_arg_list(method) + ')'

            print

        document_constants('Events', events)
        document_constants('Actions', actions)
        document_constants('Getters', getters)
        
        print

        document_list('events', 'EVENT_', events)
        document_list('actions', 'ACTION_', actions)
        document_list('getters', 'GET_', getters)

        print

        document_methods('getters', 'GET_', 'get_', getters)
        document_methods('actions', 'ACTION_', 'do_', actions)
