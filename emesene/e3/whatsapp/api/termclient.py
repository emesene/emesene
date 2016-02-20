import hashlib
import sys
import threading
import time

import api
import config

class TermClient(api.WAClient):
    def __init__(self, num, pwd, name):
        api.WAClient.__init__(self, num, pwd, name)

        self.set_event_handler('connected', self.connected)
        self.set_event_handler('message_received', self.message_received)
        self.set_event_handler('login_failed', self.login_failed)
        self.set_event_handler('login_succeeded', self.login_succeeded)
        self.set_event_handler('last_seen_received', self.last_seen_received)
        self.set_event_handler('server_notice_received',
                self.server_notice_received)
        self.set_event_handler('message_received_at_server',
                self.message_received_at_server)
        self.set_event_handler('message_received_at_client',
                self.message_received_at_client)
        self.set_event_handler('chatstate_changed', self.chatstate_changed)


        self.connect()

    def connected(self):
        print "CONNECTED!"
    def message_received(self, message_id, sender, message, realname,
            offline_stamp):
        if offline_stamp is not None:
            offline_stamp = time.strftime("%Y-%m-%d %H:%M:%S", offline_stamp)
        print "%s (%s, %s): %s" % (realname, sender.split('@')[0],
                offline_stamp, message)
    def login_failed(self):
        print "LOGIN FAILED"
    def login_succeeded(self, status, kind, creation, expiration):
        print "LOGGED IN", status, kind, creation, expiration
        self.send_subscribe(config.test_dest)
        self.send_request_last_seen(config.test_dest)
    def last_seen_received(self, sender, seconds):
        print "LAST SEEN RESPONSE:", sender, seconds
    def server_notice_received(self, message_id, message):
        print "SERVER NOTICE:", message
    def message_received_at_server(self, dest, message_id):
        print "SERVER RECEIVED:", message_id, dest
    def message_received_at_client(self, dest, message_id):
        print "CLIENT RECEIVED:", message_id, dest
    def chatstate_changed(self, sender, state):
        print "CHATSTATE:", sender, state


def main():
    wa = TermClient(config.mobile_number,
            hashlib.md5(config.imei[::-1]).hexdigest(), config.name)

    def threaded_recv():
        print "THREAD START"

        while wa.connected:
            wa.recv_and_handle()


    threading.Thread(target=threaded_recv).start()

    try:
        while wa.connected:
            inp = raw_input()

            if inp.startswith('/state '):
                wa.send_chatstate(config.test_dest, inp.split(' ')[1])
            else:
                wa.send_message(config.test_dest, inp)
    except KeyboardInterrupt:
        wa.disconnect()
        sys.exit()

if __name__ == '__main__':
    main()
