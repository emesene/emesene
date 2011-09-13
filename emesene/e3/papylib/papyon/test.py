#!/usr/bin/env python

import papyon
import papyon.event


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
            self._client.profile.display_name = "Kimbix"
            self._client.profile.presence = papyon.Presence.ONLINE
            self._client.profile.current_media = ("I listen to", "Nothing")
            for contact in self._client.address_book.contacts:
                print contact
            #self._client.profile.personal_message = "Testing papyon, and freeing the pandas!"
            gobject.timeout_add_seconds(5, self._client.start_conversation)

    def on_client_error(self, error_type, error):
        print "ERROR :", error_type, " ->", error

class AnnoyingConversation(papyon.event.ConversationEventInterface):
    def on_conversation_user_joined(self, contact):
        gobject.timeout_add_seconds(5, self.annoy_user)

    def annoy_user(self):
        msg = "Let's free the pandas ! (testing papyon)"
        formatting = papyon.TextFormat("Comic Sans MS",
                         papyon.TextFormat.UNDERLINE | papyon.TextFormat.BOLD,
                         'FF0000')
        self._client.send_text_message(papyon.ConversationMessage(msg, formatting))
#         self._client.send_nudge()
#         self._client.send_typing_notification()
        return True

    def on_conversation_user_typing(self, contact):
        pass

    def on_conversation_message_received(self, sender, message):
        pass

    def on_conversation_error(self, error_type, error):
        print "ERROR :", error_type, " ->", error

class Client(papyon.Client):
    def __init__(self, account, quit, http_mode=False):
        server = ('messenger.hotmail.com', 1863)
        self.quit = quit
        self.account = account
        if http_mode:
            from papyon.transport import HTTPPollConnection
            papyon.Client.__init__(self, server, get_proxies(), HTTPPollConnection)
        else:
            papyon.Client.__init__(self, server, proxies = get_proxies())
        self._event_handler = ClientEvents(self)
        gobject.idle_add(self._connect)

    def _connect(self):
        self.login(*self.account)
        return False

    def start_conversation(self):
        global peer

        for state in [papyon.Presence.ONLINE, \
                          papyon.Presence.BUSY, \
                          papyon.Presence.IDLE, \
                          papyon.Presence.AWAY, \
                          papyon.Presence.BE_RIGHT_BACK, \
                          papyon.Presence.ON_THE_PHONE, \
                          papyon.Presence.OUT_TO_LUNCH]:
            print "Trying %s" % state
            contacts = self.address_book.contacts.\
                search_by_presence(state)

            if len(contacts) == 0:
                print "No %s contacts" % state
            else:
                for contact in contacts:
                    print "%s is %s" % (contact.display_name, state)
                    if contact.account == peer:
                        print "Inviting %s for a webcam" % contact.display_name
                        self._webcam_handler.invite(contact)
                        
                        return False

        return True

def main():
    import sys
    import getpass
    import signal

    global peer

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
        peer = raw_input('Send webcam to : ')
    else:
        peer = sys.argv[3]

    mainloop = gobject.MainLoop(is_running=True)

    def quit():
        mainloop.quit()

    def sigterm_cb():
        gobject.idle_add(quit)

    signal.signal(signal.SIGTERM, sigterm_cb)

    n = Client((account, passwd), quit, http_mode)

    while mainloop.is_running():
        try:
            mainloop.run()
        except KeyboardInterrupt:
            quit()

if __name__ == '__main__':
    main()
