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
#
#    module created by Andrea Stagi stagi.andrea(at)gmail.com
#

from urllib2 import urlopen
try:
    from json import loads
except ImportError:
    from simplejson import loads

API_GITHUB_FETCHBLOB = "http://github.com/api/v2/json/blob/all/%s/%s/master"
API_GITHUB_GETRAW = "http://github.com/api/v2/json/blob/show/%s/%s/%s"

class Github(object):

    def __init__(self, org):
        self._org = org

    def get_raw(self, repo, sha):
        response = urlopen(API_GITHUB_GETRAW % (self._org, repo, sha))
        return response.read()


    def fetch_blob(self, element):
        response = urlopen(API_GITHUB_FETCHBLOB % (self._org, element))
        rq = response.read()
        return loads(rq)

