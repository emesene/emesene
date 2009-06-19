import sys
import gtk

import gui
import utils
import extension

class Window(gtk.Window):
    '''the class used to create all the windows of emesene'''

    NAME = 'Window'
    DESCRIPTION = 'The window used to contain all the content of emesene'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, cb_on_close, height=410, width=250):
        gtk.Window.__init__(self)

        self.set_default_size(width, height)
        self.set_title("emesene")
        self.set_icon(gui.theme.logo)

        if cb_on_close is not None:
            self.cb_on_close = cb_on_close
        else: # we're the main window: close button only hides it
            self.cb_on_close = self.hide_on_delete

        self.connect("delete-event", self._on_delete_event)
        self.connect('key-press-event', self._on_key_press)
        self.content = None

        self.content_type = 'empty'

    def set_icon(self, icon):
        '''set the icon of the window'''
        if utils.file_readable(icon):
            gtk.Window.set_icon(self,
                utils.safe_gtk_image_load(icon).get_pixbuf())

    def clear(self):
        '''remove the content from the main window'''
        if self.get_child():
            self.remove(self.get_child())
            self.content = None

    def go_login(self, callback, on_preferences_changed,
            account=None, accounts=None,
            remember_account=None, remember_password=None, statuses=None,
            session=None, proxy=None, use_http=False, session_id=None):
        '''draw the login window on the main window'''
        LoginWindow = extension.get_default('login window')

        self.content = LoginWindow(callback, on_preferences_changed,
            account, accounts, remember_account, remember_password, statuses,
            proxy, use_http, session_id)
        self.add(self.content)
        self.content.show()
        self.content_type = 'login'

    def go_main(self, session, on_new_conversation, on_close, on_disconnect):
        '''change to the main window'''
        MainWindow = extension.get_default('main window')
        self.content = MainWindow(session, on_new_conversation,
            on_close, on_disconnect)
        self.add(self.content)
        self.content.show()
        self.content_type = 'main'

    def go_conversation(self, session):
        '''change to a conversation window'''
        ConversationManager = extension.get_default('conversation window')
        self.content = ConversationManager(session, self._on_last_tab_close)
        self.add(self.content)
        self.connect('focus-in-event', self.content._on_focus)
        self.content.show()
        self.content_type = 'conversation'

    def _on_delete_event(self, widget, event):
        '''call the cb_on_close callback, if the callback return True
        then dont close the window'''
        return self.cb_on_close()

    def _on_key_press(self, widget, event):
        '''called when a key is pressed on the window'''
        if self.content_type == 'main':
            self.content._on_key_press(widget, event)

    def _on_last_tab_close(self):
        '''do the action when the last tab is closed on a conversation window
        '''
        self.cb_on_close()
        self.hide()

