# -*- coding: utf-8 -*-

'''Test module for ImageAreaSelector widget'''

import sys
import os

from PyQt4 import QtGui


import gui
import e3
from gui.qt4ui import widgets

    
# test stuff:
class SessionStub (object):
    class ConfigDir (object):
        def get_path(*args):
            return  '/home/fastfading/src/emesene/emesene2/'\
                    'messenger.hotmail.com/'                \
                    'atarawhisky@hotmail.com/avatars/last'
    def __init__(self):
        self.config_dir = self.ConfigDir()

def main():
    '''Main method'''
    def test_stuff():
        '''Makes varios test stuff'''
        pass

    test_stuff()
    os.putenv('QT_NO_GLIB', '1')
    qapp = QtGui.QApplication(sys.argv)
    pixmap = QtGui.QPixmap('themes/images/default/logo.png')
    window = widgets.ImageAreaSelector(pixmap)
    window.show()
    qapp.exec_()

if __name__ == "__main__":
    main()

