import time
import logging

_logger = logging.getLogger('emesene')
_console_handler = logging.StreamHandler()
_formatter = logging.Formatter('[%(asctime)s %(mod)s] %(message)s', '%H:%M:%S')
_console_handler.setFormatter(_formatter)
_console_handler.setLevel(logging.INFO)
_logger.addHandler(_console_handler)
_logger.setLevel(logging.INFO)



######## OLD PART ########
max_level = 4
blacklist = []
callback = None

def _dbg(text, module, level=1):
    """
    show the debug on the console
    """
    if level <= max_level and module not in blacklist:
        output = "[%s %8s] %s" % (time.strftime('%H:%M:%S'), module, text)
        if callback is None:
            print output
        else:
            callback(text, module, level, output)

######## NEW dbg ########

old_dbg = _dbg
def dbg(text, module, level=1):
    '''
    debug the code through our mighty debugger
    '''
    #old_dbg(text, module, level)
    _logger.warning(text, extra={'mod':module})
