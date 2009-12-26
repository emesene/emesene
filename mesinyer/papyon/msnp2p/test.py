#!/usr/bin/env python

import papyon
import papyon.event
from papyon.msnp2p.session_manager import *
from papyon.msnp2p.session import *
from papyon.msnp2p.constants import EufGuid

import papyon.util.string_io as StringIO

import logging
import gobject

logging.basicConfig(level=logging.DEBUG)

finished = False

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


class ClientEvents(papyon.event.ClientEventInterface):
    def on_client_state_changed(self, state):
        if state == papyon.event.ClientState.CLOSED:
            self._client.quit()
        elif state == papyon.event.ClientState.OPEN:
            self._client.profile.display_name = "Papyon"

            path = self._client.msn_object_path
            f = open(path, 'r')
            old_pos = f.tell()
            f.seek(0, 2)
            size = f.tell()
            f.seek(old_pos,0)
            msn_object = \
                papyon.p2p.MSNObject(self._client.profile,
                                    size, papyon.p2p.MSNObjectType.DISPLAY_PICTURE,
                                    0, "lalala", data=f)
            self._client.profile.presence_msn_object = papyon.Presence.ONLINE, msn_object
            self._client.profile.personal_message_current_media = "yo!", None
 
            #gobject.timeout_add(3000, self._client.request_display_picture)

    def on_client_error(self, error_type, error):
        print "ERROR :", error_type, " ->", error

class Client(papyon.Client):
    def __init__(self, account, msn_object_path, quit, http_mode=False):
        server = ('messenger.hotmail.com', 1863)
        self.quit = quit
        self.account = account
        self.msn_object_path = msn_object_path
        if http_mode:
            from papyon.transport import HTTPPollConnection
            papyon.Client.__init__(self, server, get_proxies(), HTTPPollConnection)
        else:
            papyon.Client.__init__(self, server, proxies = get_proxies())
        self.client_event_handler = ClientEvents(self)
        gobject.idle_add(self._connect)

    def _connect(self):
        self.login(*self.account)
        return False

    def request_display_picture(self):
        contacts = self.address_book.contacts.\
                search_by_presence(papyon.Presence.OFFLINE)
        contacts = self.address_book.contacts - contacts
        if len(contacts) == 0:
            print "No online contacts"
            return True
        else:
            contact = contacts[0]
            print "CONTACT : ", contact.account, str(contact.msn_object)
            if not contact.msn_object:
                return True
            self._msn_object_store.request(contact.msn_object, (self.__request_display_picture_callback,))
            return False

    def __request_display_picture_callback(self, msn_object):
        print "Received %s" % str(msn_object)


def main():
    import sys
    import getpass
    import signal

    if "--http" in sys.argv:
        http_mode = True
        sys.argv.remove('--http')
    else:
        http_mode = False

    if len(sys.argv) < 2:
        account = raw_input('Account: ')
    else:
        account = sys.argv[1]

    if len(sys.argv) < 3:
        passwd = getpass.getpass('Password: ')
    else:
        passwd = sys.argv[2]

    if len(sys.argv) < 4:
        path = raw_input('Display picture path: ')
    else:
        path = sys.argv[3]

    mainloop = gobject.MainLoop(is_running=True)

    def quit():
        mainloop.quit()

    def sigterm_cb():
        gobject.idle_add(quit)

    signal.signal(signal.SIGTERM, sigterm_cb)

    n = Client((account, passwd), path, quit, http_mode)

    while mainloop.is_running():
        try:
            mainloop.run()
        except KeyboardInterrupt:
            quit()

if __name__ == '__main__':
    main()
