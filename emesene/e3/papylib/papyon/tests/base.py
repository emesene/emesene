# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2010 Collabora Ltd.
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import getpass
import gobject
import logging
import optparse
import signal
import sys
import time
import unittest

sys.path.insert(0, "")

import papyon

def parse_args(opts, args):
    usage = "%prog [options] " + " ".join(map(lambda x: x[0], args))
    version = "%prog " + ".".join(map(lambda x: str(x), papyon.version))

    parser = optparse.OptionParser(usage, version=version)
    for short_name, long_name, kwargs in opts:
        parser.add_option(short_name, long_name, **kwargs)
    (options, arguments) = parser.parse_args()

    values = {}
    for i in range(len(args)):
        name, type = args[i]
        display_name = name.capitalize() + ': '
        if len(arguments) <= i:
            if type == "pass":
                value = getpass.getpass(display_name)
            elif type == "string":
                value = raw_input(display_name)
            elif type == "list":
                value = raw_input(display_name).split()
            else:
                value = input(display_name)
        else:
            value = arguments[i]
            if type == "list":
                value = arguments[i:]
            elif type not in ("pass", "string"):
                value = eval(value)
        values[name] = value

    return options, values


def get_proxies():
    import urllib
    proxies = urllib.getproxies()
    result = {}
    if 'https' not in proxies and \
            'http' in proxies:
        url = proxies['http'].replace("http://", "https://")
        result['https'] = papyon.Proxy(url)
    for type, url in proxies.items():
        if type == 'no': continue
        if type == 'https' and url.startswith('http://'):
            url = url.replace('http://', 'https://', 1)
        result[type] = papyon.Proxy(url)
    return result


class TestClientEvents(papyon.event.ClientEventInterface,
                       papyon.event.InviteEventInterface):

    def __init__(self, client):
        papyon.event.ClientEventInterface.__init__(self, client)
        papyon.event.InviteEventInterface.__init__(self, client)

    def on_client_state_changed(self, state):
        if state == papyon.event.ClientState.CLOSED:
            self._client.quit()
        elif state == papyon.event.ClientState.OPEN:
            self._client.connected()

    def on_client_error(self, type, error):
        print "ERROR %s -> %s" % (type, error)


class TestClient(papyon.Client):

    def __init__(self, name, opts, args, event_handler_class=TestClientEvents):
        base_opts = [('-m', '--procotol',  {'type': 'int', 'default': 18,
                                            'dest': 'version',
                                            'help': 'protocol version to use'}),
                     ('-l', '--level',     {'type': 'int', 'default': 0,
                                            'help': 'logging level'}),
                     ('-s', '--server',    {'default': 'messenger.hotmail.com',
                                            'help': 'live messenger server'}),
                     ('-p', '--port',      {'type': 'int', 'default': 1863,
                                            'help': 'server port'}),
                     ('-t', '--transport', {'type': 'choice', 'default': 'direct',
                                            'choices': ('direct', 'http'),
                                            'help': 'connection (direct or http)'})
                     ]
        base_args = [('account', 'string'),
                     ('password', 'pass')]

        self.name = name
        self.options, self.arguments = parse_args(base_opts + opts, base_args + args)

        logging.basicConfig(level=self.options.level)

        self.mainloop = gobject.MainLoop(is_running=True)
        signal.signal(signal.SIGTERM,
                lambda *args: gobject.idle_add(self.mainloop.quit()))

        transport_class = papyon.transport.DirectConnection
        if self.options.transport == 'http':
            transport_class = papyon.transport.HTTPPollConnection

        papyon.Client.__init__(self, (self.options.server, self.options.port),
                proxies=get_proxies(), transport_class=transport_class,
                version=self.options.version)
        self.event_handler = event_handler_class(self)
        gobject.idle_add(self.login, self.arguments['account'],
                self.arguments['password'])

    def run(self):
        while self.mainloop.is_running():
            try:
                self.mainloop.run()
            except KeyboardInterrupt:
                self.mainloop.quit()

    def quit(self):
        self.mainloop.quit()

    def connected(self):
        self.profile.display_name = "Paypon (%s)" % self.name
        self.profile.presence = papyon.Presence.ONLINE
