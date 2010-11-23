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

class Proxy(object):
    """
    This class represents the information of a proxy
    """

    def __init__(self, use_proxy=False, host='', port='', use_auth=False, 
        user='', passwd=''):
        """
        Constructor.
        use_proxy -- boolean that indicates if the proxy should be used
        host -- the host url
        port -- the port number
        use_auth -- a boolean that indicates if authentication should be used
        user -- the user of the proxy
        passwd -- the password of the user
        """
        self.use_proxy = use_proxy
        self.host = host
        self.port = port
        self.use_auth = use_auth
        self.user = user
        self.passwd = passwd
