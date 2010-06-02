import pynotify
if not pynotify.init("emesene"):
    raise ImportError

import logging
log = logging.getLogger('gui.gtkui.PyNotification')

NAME = 'PyNotification'
DESCRIPTION = 'Wrapper around pynotify for the notification system'
AUTHOR = 'arielj'
WEBSITE = 'www.emesene.org'

def pyNotification(title, text, picturePath=None):
    n = pynotify.Notification(title, text, picturePath)
    n.show()