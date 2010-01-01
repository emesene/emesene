'''
Provides logging/debugging feature

How to use
==========
    You just need to import this module, and you can use our easy methods::

        import debugger
        debugger.debug('Some text')

    Levels
    ------
        Not every debug text is equally important.  That's why we have logging
        levels: info, debug, warning, error, critical The functions follows the
        same name of the levels, and all behave the same way.  Thanks to
        levels, you can put lot of debug info without having your console full
        of unimportant messages.
'''

import logging
import warnings
import collections

import inspect
import os.path

def _build_caller():
    caller_obj = inspect.stack()[2]
    filename = caller_obj[0].f_code.co_filename
    caller = '%s' % (os.path.basename(filename).split('.py')[0])
    return caller

def dbg(text, caller=None, level=1):
    warnings.warn("Use logging.getLogger(name).log instead", DeprecationWarning, stacklevel=3)

    if not caller:
        caller = _build_caller()

    logging.getLogger('debugger.' + caller).log(level*10, text)


def _log_function(level):
    '''Returns a function that calls dbg with a specific level'''
    return lambda text, caller=None: dbg(text, caller, level / 10)

log = debug = _log_function(logging.DEBUG)
info = _log_function(logging.INFO)
warning = _log_function(logging.WARNING)
error = _log_function(logging.ERROR)
critical = _log_function(logging.CRITICAL)

class QueueHandler(logging.Handler):
    '''A Handler that just keeps the last messages in memory, using a queue.
    This is useful when you want to know (i.e. in case of errors) the last
    debug messages.'''
    
    instance = None

    def __init__(self, maxlen=50):
        logging.Handler.__init__(self)
        self.setLevel(logging.DEBUG)
        
        self.queue = collections.deque()
        self.maxlen = maxlen # see below

    def emit(self, record):
        self.queue.append(record)

        # python 2.5 doesn't include the maxlen parameter of deques
        if len(self.queue) > self.maxlen:
            self.queue.popleft()

    def get_all(self):
        return self.queue.__iter__()

    @classmethod
    def get(cls):
        if cls.instance is None:
            cls.instance = cls()
        return cls.instance 

def init(debuglevel=0):
    root = logging.getLogger()
    
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s %(levelname)s %(name)s] %(message)s', '%H:%M:%S')
    console_handler.setFormatter(formatter)

    levels = {
        0: logging.WARNING,
        1: logging.INFO,
        2: logging.DEBUG,
    }
    
    console_handler.setLevel(levels[min(debuglevel, 2)])
    root.addHandler(console_handler)
    
    root.addHandler(QueueHandler.get())
    root.setLevel(logging.DEBUG)
