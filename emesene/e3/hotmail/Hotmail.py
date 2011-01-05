# -*- coding: utf-8 -*-

#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
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
#
#    This file is taken from emesene1 and modified for 
#    emesene2 by Andrea Stagi <stagi.andrea(at)gmail.com>

import os
import hashlib
from time import time
import webbrowser

class Hotmail:
    def __init__( self, session ):
        self.session=session
        self.user = self.session.account.account
        self.profile=self.session.get_profile()
        self.password = self.session.account.password
        self.MSPAuth = self.profile['MSPAuth']
        
    def __getLoginPage( self, MessageURL=None , PostURL=None, id='2' ):
        if PostURL == None:
            if self.user.split('@')[1] == 'msn.com':
                PostURL = 'https://msnia.login.live.com/ppsecure/md5auth.srf?lc=' + self.profile['lang_preference']
            else:
                PostURL = 'https://login.live.com/ppsecure/md5auth.srf?lc=' + self.profile['lang_preference']
               
        if MessageURL == None:
            MessageURL = "/cgi-bin/HoTMaiL"
           
        sl = str( int ( time() ) - int( self.profile['LoginTime'] ) )
        auth = self.MSPAuth
        sid = self.profile['sid']
        cred =  hashlib.md5( auth + sl + self.password ).hexdigest()

        templateData = {
        'id':id,
        'site':PostURL,
        'login': self.user.split('@')[0],
        'email':self.user,
        'sid':sid,
        'kv':'',
        'sl':sl,
        'url':MessageURL,
        'auth':auth,
        'creds':cred
        }
        
        return self.parseTemplate( templateData )
        
    def parseTemplate( self, data ):
        f = open(os.path.join(os.getcwd(), 'data','hotmlog.htm'))
        hotLogHtm = f.read()
        f.close()
        for key in data:
            hotLogHtm = hotLogHtm.replace( '$'+key, data[ key ] )

        self.file = os.path.join(
            self.session.config_dir.base_dir, 'login.htm')
        
        tmpHtml = open( self.file, 'w' )
        tmpHtml.write( hotLogHtm )
        tmpHtml.close()
        
        return 'file:///' + self.file

    def openInBrowser(self):
        webbrowser.open(self.__getLoginPage())
