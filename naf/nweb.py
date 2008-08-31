'''this modules defines the base server for naf'''

import web
import time
import types
import Queue
import random
import inspect
import functools

import simplejson

from nbase import Action
from nbase import Event
from nbase import Session
from nbase import ServerBase

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

        if inspect.ismethod(function):
            function.args = args[2:]
            function.has_self = True
        else:
            function.args = args[1:]
            function.has_self = False

        @functools.wraps(function)
        def wrapper(*f_args, **f_kwds):
            '''returns a function that receives a dict of key values, extract
            the names of the vars from the function that is wrapped and the
            valid types from the decorator arguments, try to cast the values
            to the types defined on the decorator and pass them in the order
            defined by the function, if some of the cast fails, set bad request
            status and return (dont call the wrapped function'''

            final_args = []

            if function.has_self:
                final_args.append(f_args[0])
                
            final_args.append(f_kwds.get('session', ''))
            
            for (index, arg) in enumerate(function.args):
                if arg in f_args[1]:
                    try:
                        final_args.append(self.values[index](f_args[1][arg]))
                    except ValueError:
                        Server.set_bad_request()
                        print
                        print arg, 'convertion failed'
                        return
                elif arg in function.args_def:
                    final_args.append(function.defaults[\
                        function.args_def.index(arg)])
                else:
                    Server.set_bad_request()
                    print 
                    print arg, 'not a valid arg'
                    return

            return function(*final_args)

        return wrapper

class Server(ServerBase):
    '''The server class'''

    (TYPE_GET, TYPE_ACTION, TYPE_EVENT) = range(3)
    sessions = {}

    def __init__(self):
        ServerBase.__init__(self)

    def GET(self):
        '''return a new session cookie'''
        # TODO: control DoS from an IP address, requestion many cookies
        Server.set_response_header()
        cookie = Server.new_session()
        Server.sessions[cookie] = Session(cookie)
        print simplejson.dumps(dict(cookie=cookie))

    def POST(self):
        '''handle a post request, extract the request object and handle it
        '''
        cookie = Server.validate_session()
        if cookie is None:
            return
        
        session = Server.sessions.get(cookie, None)

        if session is None:
            Server.set_bad_request()
            print
            print 'session doesn\'t exist'
            return

        try:
            dct = simplejson.loads(Server.get_request_body())
        except ValueError:
            Server.set_internal_error()
            return

        r_type = dct.get('r_type', -1)

        if  r_type == Server.TYPE_GET:
            print simplejson.dumps(self.handle_get(session, dct))
        elif  r_type == Server.TYPE_ACTION:
            self.handle_action(session, dct)
            Server.set_response_header()
            return
        else:
            Server.set_bad_request()
            print
            print "request type is not GET or ACTION"
            return
        
    def handle_get(self, session, dct):
        '''handle a get request'''
        identifier = int(dct.get('id_', -1))

        if 0 <= identifier <= self.max_getter_index:
            Server.set_response_header()
            response = self.get_handlers[identifier](dct.get('args', {}), \
                session=session)
            return simplejson.dumps(response)
        else:
            Server.set_bad_request()
            print type(self.max_getter_index), type(identifier)
            print 'id < 0 or > ', self.max_getter_index, 'id = ', identifier
            return

    def handle_action(self, session, dct):
        '''handle a action request'''
        identifier = int(dct.get('id_', -1))

        if 0 <= identifier <= self.max_action_index:
            Server.set_response_header()
            try:
                (id_, args) = self.action_handlers[identifier](dct.get('args', \
                    {}), session=session)
            except Exception:
                Server.set_bad_request()
                print
                print 'invalid action handler'

            self.add_event(session, id_, args)
            return
        else:
            Server.set_bad_request()
            print
            print 'id < 0 or > ', self.max_action_index, 'id = ', identifier
            return

    @classmethod
    def set_bad_request(cls):
        '''set the response header and the content of the response to
        bad request'''
        cls.set_response_header()
        web.webapi.badrequest()
    
    @classmethod
    def set_internal_error(cls):
        '''set the response header and the content of the response to
        internal error'''
        cls.set_response_header()
        web.webapi.internalerror()

    @classmethod
    def set_response_header(cls):
        '''set the response header'''
        web.header('content-type', 'application/json')

    @classmethod
    def validate_session(cls, set_bad_request=True):
        '''validate if the session is valid'''
        session = web.ctx.env.get('HTTP_NAF_SESSION', None)

        if set_bad_request and session is None:
            cls.set_bad_request()
            print 
            print 'session is not set on header'
            return None

        return session

    @classmethod
    def get_request_body(cls):
        '''return the content of the body of the request'''
        content_length = int(web.ctx.env.get('CONTENT_LENGTH', 0))
        file_descriptor = web.ctx.env['wsgi.input']
        data = file_descriptor.read(content_length)

        return data

    @classmethod
    def remove_session(cls, session):
        '''remove a session from the available
        sessions if it exists, override this if you need to do something
        more before removing the session'''
        if session in Server.sessions:
            del Server.sessions[session]

    def run(self, globals_, path='/naf/'):
        paths = (path, str(self.__class__.__name__))
        print 'starting server with paths', paths
        web.run(paths, globals_)

