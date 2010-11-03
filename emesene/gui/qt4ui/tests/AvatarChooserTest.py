# -*- coding: utf-8 -*-

'''Test module for ChatTextEdit widget'''

import sys
import os

from PyQt4 import QtGui

import gui
import e3
from gui.qt4ui import AvatarChooser

    
# test stuff:
def get_system_avatars_dirs():
    ''' gets the directories where avatars are availables '''
    faces_paths = []
    if os.name == 'nt':
        app_data_folder = os.path.split(os.environ['APPDATA'])[1]
        faces_path = os.path.join(os.environ['ALLUSERSPROFILE'], \
                        app_data_folder, "Microsoft", \
                        "User Account Pictures", "Default Pictures")
        # little hack to fix problems with encoding
        unicodepath = u"%s" % faces_path
        faces_paths = [unicodepath]
    else:
        faces_paths = ['/usr/share/kde/apps/faces', \
                        '/usr/share/kde4/apps/kdm/pics/users', \
                        '/usr/share/pixmaps/faces']
    return faces_paths

def main():
    '''Main method'''
    def test_stuff():
        '''Makes varios test stuff'''
        pass

    test_stuff()
    qapp = QtGui.QApplication(sys.argv)
    faces = get_system_avatars_dirs()
    window = AvatarChooser.AvatarChooser(None, faces_paths=faces)
    window.exec_()
    #qapp.exec_()

if __name__ == "__main__":
    main()

