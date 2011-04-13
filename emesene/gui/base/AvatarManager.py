''' this file contains the AvatarManager abstract class, used to manage 
Avatars. This class must be subclassed in gui code, implementing abstract
methods.'''
# -*- coding: utf-8 -*-

#    This file is part of emesene.
#
#    emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
import hashlib
import shutil
import tempfile

import extension

class AvatarManager(object):
    '''an utility class to manage avatars and their paths'''
    def __init__(self, session):
        '''constructor'''
        self.session = session
        self.config_dir = session.config_dir
        self.config = session.config
        self.avatar_path = self.session.config.last_avatar

        for contact in self.session.contacts.contacts:
            self.session.config_dir.add_path(contact, os.path.join(contact, "avatars"), False)

    def get_avatars_dir(self):
        ''' gets the user's avatar directory '''
        # this path should be set while loging in
        return self.config_dir.get_path('avatars')

    def get_cached_avatars_dir(self):
        ''' gets the contacts' cached avatar directory '''
        # this path should be set while loging in
        return self.config_dir.get_path('cached_avatars')

    def get_contact_avatars_dir(self, contact):
        ''' gets the avatar directory of specified contact'''
        # this path is set by AvatarManager on init
        return self.config_dir.get_path(contact)

    def get_system_avatars_dirs(self):
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

    def is_cached(self, filename):
        ''' check if a filename is already in one of the avatar caches '''
        bdir = os.path.dirname(filename)
        return bdir == self.get_avatars_dir() or \
            bdir == self.get_cached_avatars_dir() or \
            bdir in self.get_system_avatars_dirs()

    def add_new_avatar(self, filename):
        ''' add a new picture from filename into the avatar cache '''
        def gen_filename(source):
            # generate a unique (?) filename for the new avatar in cache
            # implemented as sha224 digest
            infile = open(source, 'rb')
            data = infile.read()
            infile.close()
            return hashlib.sha224(data).hexdigest()

        fpath = os.path.join(self.get_avatars_dir(), gen_filename(filename))

        try:
            if not os.path.exists(self.get_avatars_dir()):
                    os.makedirs(self.get_avatars_dir())
            pix_96 = extension.get_and_instantiate('picture handler', filename)
            pix_96.resize(96)
            pix_96.save(fpath)
            return fpath

        except OSError, error:
            print error
            return None, fpath


    def add_new_avatar_from_toolkit_pix(self, toolkit_pix):
        ''' add a new picture into the avatar cache '''
        fd, fn = tempfile.mkstemp(prefix='emsnpic')
        PictureHandler = extension.get_default('picture handler')
        pix = PictureHandler.from_toolkit(toolkit_pix)
        pix.save(fn)
        results = self.add_new_avatar(fn)
        os.remove(fn)
        return results


    def set_as_avatar(self, filename):
        ''' set a picture as the current avatar 
        and make a copy in the cache '''
        # Control if the filename is a already in cache
        if self.is_cached(filename):
            self.session.set_picture(filename)
            path = os.path.dirname(self.avatar_path)

            if os.path.exists(path):
                if os.path.exists(self.avatar_path):
                    os.remove(self.avatar_path)
            else:
                os.makedirs(path)

            shutil.copy(filename, self.avatar_path)
        else:
            try:
                fpath = self.add_new_avatar(filename)

                self.session.set_picture(fpath)
                if os.path.exists(self.avatar_path):
                    os.remove(self.avatar_path)
                shutil.copy(fpath, self.avatar_path)
            except OSError, error:
                print error

