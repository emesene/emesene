'''defines an object that represent a MSN command'''

class Command(object):
    '''a class that represent a command from the server and provide
    methods to check it'''

    def __init__(self, command, tid=0, params=None, payload=None):
        '''class constructor, cmd is a string'''
        self.command = command
        self.tid = tid

        if params is None:
            self.params = []
        else:
            self.params = params

        self.payload = payload

    @classmethod
    def parse(cls, cmd):
        '''parse a command and return a Command object'''
        (tokens, payload) = cmd.split('\r\n')
        tokens = cmd.split(' ')
        params = None

        if not payload:
            payload = None

        (command, tid) = tokens[:2]
        if len(tokens) > 2:
            params = tokens[2:]

        return cls(command, tid, params, payload)

    def is_command(self, cmd):
        '''return True if self.command == cmd'''
        return self.command == cmd

    def is_tid(self, tid):
        '''return True if self.tif == tid'''
        return self.tid == tid

    def is_param(self, param):
        '''return True if self.params == param'''
        return self.params == param

    def param_num_is(self, num, param):
        '''try to get the num element on param, if we cant get it, return
        False, if we can get it and param == self.params[num] return True'''

        if num > len(self.params) - 1:
            return False

        return self.params[num] == param

    def param_num_exists(self, num):
        '''return True if the length of the param list is > num'''
        if num > len(self.params) - 1:
            return False

        return True
            
    def __str__(self):
        '''return the string representation of the object'''
        return self.command + ' ' + self.tid + ' ' + ' '.join(self.params)

    def __repr__(self):
        '''return the representation of the object'''
        return repr(str(self))
