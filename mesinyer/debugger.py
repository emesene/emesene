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

import time
import logging
from collections import deque

import inspect
import os.path

def _build_caller():
    #Get class.method_name. Not used now, but could be useful
    caller_obj = inspect.stack()[2]
    #try:
    #    parent_class = '%s.' % caller_obj.f_locals['self'].__class__.__name__
    #except:
    #    parent_class = ''
    #class_method = '%s%s' % (parent_class, caller_obj[3])
    filename = caller_obj[0].f_code.co_filename
    caller = '%s' % (os.path.basename(filename).split('.py')[0])
    return caller

def dbg(text, caller=None, level=1):
    '''
    DEPRECATED! debug the code through our mighty debugger: compatibility function
    '''
    if not caller:
        caller = _build_caller()

    #old_dbg(text, module, level)
    _logger.log(level*10, text, extra={'caller':caller})


def _log_function(level):
    '''Returns a function that calls dbg with a specific level'''
    return lambda text, caller=None: dbg(text, caller, level / 10)

log = debug = _log_function(logging.DEBUG)
info = _log_function(logging.INFO)
warning = _log_function(logging.WARNING)
error = _log_function(logging.ERROR)
critical = _log_function(logging.CRITICAL)

class QueueHandler(logging.Handler):
    '''
    An Handler that just keeps the last messages in memory, using a queue.
    This is useful when you want to know (i.e. in case of errors) the last
    debug messages.
    '''
    def __init__(self, maxlen=50):
        logging.Handler.__init__(self)
        self.maxlen = maxlen
        self.queue = deque()

    def emit(self, record):
        self.queue.append(record)

        if len(self.queue) > self.maxlen:
            self.queue.popleft()

    def get_all(self):
        l = len(self.queue)
        for i in range(l):
            record = self.queue.pop()
            self.queue.appendleft(record)
            yield record

_logger = logging.getLogger('emesene')
_console_handler = logging.StreamHandler()
_formatter = logging.Formatter('[%(asctime)s %(caller)s] %(message)s', '%H:%M:%S')
_console_handler.setFormatter(_formatter)
_console_handler.setLevel(logging.INFO)
_logger.addHandler(_console_handler)

queue_handler = QueueHandler()
queue_handler.setLevel(logging.DEBUG)
_logger.addHandler(queue_handler)

_logger.setLevel(logging.DEBUG)


