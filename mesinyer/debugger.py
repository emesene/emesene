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
import collections

class QueueHandler(logging.Handler):
    '''A Handler that just keeps the last messages in memory, using a queue.
    This is useful when you want to know (i.e. in case of errors) the last
    debug messages.'''

    instance = None

    def __init__(self, maxlen=50):
        logging.Handler.__init__(self)
        self.setLevel(logging.DEBUG)
        self.maxlen = maxlen
        self.queue = collections.deque()

    def emit(self, record):
        self.queue.append(record)
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
    formatter = logging.Formatter(
            '[%(asctime)s %(levelname)s %(name)s] %(message)s', '%H:%M:%S')
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
