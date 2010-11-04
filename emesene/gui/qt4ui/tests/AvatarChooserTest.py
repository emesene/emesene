# -*- coding: utf-8 -*-

'''Test module for ChatTextEdit widget'''

import sys
import os

from PyQt4 import QtGui

import gui
import e3
from gui.qt4ui import AvatarChooser

    
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
    qapp = QtGui.QApplication(sys.argv)
    window = AvatarChooser.AvatarChooser(SessionStub())
    window.exec_()
    #qapp.exec_()

if __name__ == "__main__":
    main()

