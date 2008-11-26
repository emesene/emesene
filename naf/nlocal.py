'''this modules defines the base server for naf'''

import inspect
import functools

from protocol.Session import Session
from nbase import Event
from nbase import ServerBase
from nbase import validate

class Server(ServerBase):
    '''The server class'''

    def __init__(self):
        '''class constructor'''
        ServerBase.__init__(self)

    def create_session(self):
        '''return a new session cookie'''
        cookie = Server.new_session()
        self.session = Session(cookie)
        return cookie

    def run(self, globals_, path='/naf/'):
        pass

    def build(self):
        ServerBase.build(self)
        self.create_session() 
