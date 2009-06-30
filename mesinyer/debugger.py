import time
import logging

import inspect
import os.path

_logger = logging.getLogger('emesene')
_console_handler = logging.StreamHandler()
_formatter = logging.Formatter('[%(asctime)s %(caller)s] %(message)s', '%H:%M:%S')
_console_handler.setFormatter(_formatter)
_console_handler.setLevel(logging.INFO)
_logger.addHandler(_console_handler)
_logger.setLevel(logging.INFO)


def dbg(text, caller=None, level=1):
    '''
    debug the code through our mighty debugger
    '''
    if not caller:
        #Get class.method_name. Not used now, but could be useful
        #caller_obj = inspect.stack()[1]
        #try:
        #    parent_class = '%s.' % caller_obj.f_locals['self'].__class__.__name__
        #except:
        #    parent_class = ''
        #class_method = '%s%s' % (parent_class, caller_obj[3])
        filename = caller_obj[0].f_code.co_filename
        caller = '%s' % (os.path.basename(filename).split('.py')[0])


    #old_dbg(text, module, level)
    _logger.warning(text, extra={'caller':caller})
