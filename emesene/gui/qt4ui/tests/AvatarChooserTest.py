# -*- coding: utf-8 -*-

'''Test module for ChatTextEdit widget'''

import sys

from PyQt4 import QtGui

import gui
import e3
from gui.qt4ui import AvatarChooser

    
def main():
    '''Main method'''
    def test_stuff():
        '''Makes varios test stuff'''
        pass

    test_stuff()
    qapp = QtGui.QApplication(sys.argv)
    window = AvatarChooser.AvatarChooser(None)
    window.exec_()
    #qapp.exec_()

if __name__ == "__main__":
    main()
