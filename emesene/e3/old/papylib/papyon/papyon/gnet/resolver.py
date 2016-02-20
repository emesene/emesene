# -*- coding: utf-8 -*-
#
# Copyright (C) 2006  Ali Sabil <ali.sabil@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

"""GNet dns resolver"""

import socket

import gobject

from papyon.gnet.errors import IoError
from papyon.util.async import run
from papyon.util.decorator import async

__all__ = ['HostnameResolver']

class HostnameResponse(object):
    def __init__(self, response):
        self._response = response

    @property
    def cname(self):
        return self._response[0]

    @property
    def expires(self):
        return self._response[1]

    @property
    def answer(self):
        return self._response[2]

    def __repr__(self):
        return repr(self._response)

class HostnameError(IoError):
    def __init__(self, host):
        IoError.__init__(self, IoError.HOSTNAME_RESOLVE_FAILED)
        self.host = host

    def __str__(self):
        return "Couldn't resolve hostname for \"%s\"" % (self.host)

class HostnameResolver(object):
    def __init__(self):
        self._queries = {}

    @async
    def query(self, host, callback, errback):
        try:
            result = socket.getaddrinfo(host, None, socket.AF_INET, socket.SOCK_STREAM)
        except socket.gaierror:
            result = []

        if len(result) == 0:
            run(errback, HostnameError(host))
            return

        cname = result[0][3]
        expires = 0
        addresses = ((socket.AF_INET, result[0][4][0]),)
        run(callback, HostnameResponse((cname, expires, addresses)))


if __name__ == "__main__":
    mainloop = gobject.MainLoop(is_running=True)
    def print_throbber():
        print "*"
        return True

    def hostname_resolved(result):
        print result
        mainloop.quit()

    def hostname_failed(error):
        print error
        mainloop.quit()

    def resolve_hostname(resolver, host):
        print "Resolving"
        resolver.query(host, (hostname_resolved,), (hostname_failed,))
        return False

    resolver = HostnameResolver()

    gobject.timeout_add(10, print_throbber)
    gobject.timeout_add(100, resolve_hostname, resolver, 'www.google.com')
    gobject.timeout_add(100, resolve_hostname, resolver, 'www.abcdeg.hij')

    mainloop.run()
