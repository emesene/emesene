import sys
import gtk
import gobject

from core import Core
import dialog
import Window

import e3
from protocol.base import Action

class Controller(object):
    '''class that handle the transition between states of the windows'''
    
    def __init__(self):
        '''class constructor'''
        self.window = None
        self.conversations = None
        self.core = Core()
        self.core.connect('login-succeed', self.on_login_succeed)
        self.core.connect('login-failed', self.on_login_failed)
        self.core.connect('contact-list-ready', self.on_contact_list_ready)
        self.core.connect('conv-first-action', self.on_new_conversation)

    def on_close(self):
        '''called on close'''
        sys.exit(0)

    def on_login_succeed(self, core, args):
        '''callback called on login succeed'''
        self.window.clear()
        self.window.go_main(core.session)

    def on_login_failed(self, core, args):
        '''callback called on login failed'''
        dialog.error(args[0])
        self.window.content.set_sensitive(True)

    def on_contact_list_ready(self, core, args):
        '''callback called when the contact list is ready to be used'''
        self.window.content.contact_list.order_by_status = False
        self.window.content.contact_list.show_offline = True
        self.window.content.contact_list.fill()
        self.core.do_set_message('hola!')

    def on_login_connect(self, account, remember):
        self.core.do_login(account.account, account.password, account.status)

    def on_new_conversation(self, core, args):
        '''callback called when the other user does an action that justify
        opeinig a conversation'''
        cid = args[0]

        if self.conversations is None:
            window = Window.Window(self._on_conversation_window_close)
            window.set_default_size(640, 480)
            window.go_conversation(self.core.session)
            self.conversations = window.content
            window.show()

        conversation = self.conversations.new_conversation(cid)
        conversation.show_all()

    def _on_conversation_window_close(self):
        '''method called when the conversation window is closed'''
        self.conversations = None
        self.core.do_add_contact('mguerra@guic.com.ar')

    def start(self, account=None):
        self.window = Window.Window(self.on_close)
        self.window.go_login(self.on_login_connect, account)
        self.window.show()

if __name__ == "__main__":
    gtk.gdk.threads_init()
    controller = Controller()
    controller.start()
    gtk.main()
