import logging
import warnings
import collections

import inspect
import os.path

def _build_caller():
    caller_obj = inspect.stack()[1]
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
        self.queue = collections.deque(maxlen=maxlen)

    def emit(self, record):
        self.queue.append(record)

    def get_all(self):
        return self.queue.__iter__()

    @classmethod
    def get(cls):
        if cls.instance is None:
            cls.instance = cls()
        return cls.instance 

def init(console=False):
    root = logging.getLogger()
    if console:
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s %(name)s] %(message)s', '%H:%M:%S')
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        root.addHandler(console_handler)
    
    root.addHandler(QueueHandler.get())
    root.setLevel(logging.DEBUG)
