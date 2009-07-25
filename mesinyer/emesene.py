import sys
import gtk
import time
import base64
import gobject

from debugger import warning

import e3
import gui
import yaber
import utils
import dummy
import e3common
import protocol

from pluginmanager import get_pluginmanager
import extension
import interfaces

import e3gtk

class Controller(object):
    '''class that handle the transition between states of the windows'''
    
    def __init__(self):
        '''class constructor'''
        self.window = None
        self.tray_icon = None
        self.conversations = None
        self.config = e3common.Config.Config()
        self.config_dir = e3common.ConfigDir.ConfigDir('emesene2')
        self.config_path = self.config_dir.join('config')
        self.config.load(self.config_path)

        if self.config.d_status is None:
            self.config.d_status = {}

        if self.config.d_accounts is None:
            self.config.d_accounts = {}

        self.session = None
        self._setup()
    
    def _setup(self):
        '''register core extensions'''
        extension.category_register('session', e3.Session, single_instance=True)
        extension.register('session', yaber.Session)
        extension.register('session', dummy.Session)
        extension.category_register('sound', e3common.play_sound.play)
        extension.category_register('notification', e3common.notification.notify)
        extension.category_register('history exporter',
                protocol.Logger.save_logs_as_txt)
        extension.category_register('external api', None, interfaces.IExternalAPI)
        
        if self.config.session is None:
            default_id = extension.get_category('session').default_id
            self.config.session = default_id
        else:
            default_id = self.config.session

        extension.set_default_by_id('session', default_id)
        get_pluginmanager().scan_directory('plugins')

    def _new_session(self):
        '''create a new session object'''

        if self.session is not None:
            self.session.quit()

        self.session = extension.get_and_instantiate('session')
        self.session.signals = gui.Signals(protocol.EVENTS,
            self.session.events)
        self.session.signals.login_succeed.subscribe(self.on_login_succeed)
        self.session.signals.login_failed.subscribe(self.on_login_failed)
        self.session.signals.contact_list_ready.subscribe(
            self.on_contact_list_ready)
        self.session.signals.conv_first_action.subscribe(
            self.on_new_conversation)
        self.session.signals.nick_change_succeed.subscribe(
            self.on_nick_change_succeed)
        self.session.signals.message_change_succeed.subscribe(
            self.on_message_change_succeed)
        self.session.signals.status_change_succeed.subscribe(
            self.on_status_change_succeed)
        self.session.signals.disconnected.subscribe(
            self.on_disconnected)

    def save_extensions_config(self):
        '''save the state of the extensions to the config'''
        if self.session is None:
            return

        if self.session.config.d_extensions is None:
            self.session.config.d_extensions = {}

        for name, category in extension.get_categories().iteritems():
            self.session.config.d_extensions[name] = \
                category.default_id

    def set_default_extensions_from_config(self):
        '''get the ids of the default extensions stored on config
        and set them as default on the extensions module'''

        if self.session.config.d_extensions is not None:
            for cat_name, ext_id in self.session.config.d_extensions.iteritems():
                extension.set_default_by_id(cat_name, ext_id)

    def _get_proxy_settings(self):
        '''return the values of the proxy settings as a protocol.Proxy object
        initialize the values on config if not exist'''

        use_proxy = self.config.get_or_set('b_use_proxy', False)
        use_proxy_auth = self.config.get_or_set('b_use_proxy_auth', False)
        host = self.config.get_or_set('proxy_host', '')
        port = self.config.get_or_set('proxy_port', '')
        user = self.config.get_or_set('proxy_user', '')
        passwd = self.config.get_or_set('proxy_passwd', '')

        use_http = self.config.get_or_set('b_use_http', False)

        return protocol.Proxy(use_proxy, host, port, use_proxy_auth, user,
            passwd)

    def _save_proxy_settings(self, proxy):
        '''save the values of the proxy settings to config'''
        self.config.b_use_proxy = proxy.use_proxy
        self.config.b_use_proxy_auth = proxy.use_auth
        self.config.proxy_host = proxy.host
        self.config.proxy_port = proxy.port
        self.config.proxy_user = proxy.user
        self.config.proxy_passwd = proxy.passwd

    def on_close(self):
        '''called on close'''
        self.close_session()

    def on_disconnected(self, reason):
        '''called when the server disconnect us'''
        dialog = extension.get_default('dialog')
        dialog.error('Session disconnected by server')
        self.close_session(False)
        self.start()

    def close_session(self, exit=True):
        if self.session is not None:
            self.session.quit()

        self.save_extensions_config()

        if self.session is not None:
            self._save_main_dimensions()
            self.session.save_config()
            self.session = None
        else:
            self._save_login_dimensions()

        self.config.save(self.config_path)

        if self.conversations:
            self.conversations.get_parent().hide()
            self.conversations = None

        self.window.hide()
        self.window = None

        if exit:
            while gtk.events_pending():
                gtk.main_iteration(False)

            time.sleep(2)
            sys.exit(0)

    def _save_login_dimensions(self):
        '''save the dimensions of the login window
        '''
        width, height, posx, posy = self.window.get_dimensions()

        self.config.i_login_posx = posx
        self.config.i_login_posy = posy
        self.config.i_login_width = width
        self.config.i_login_height = height

    def _save_main_dimensions(self):
        '''save the dimensions of the main window
        '''
        width, height, posx, posy = self.window.get_dimensions()

        self.session.config.i_main_width = width
        self.session.config.i_main_height = height
        self.session.config.i_main_posx = posx
        self.session.config.i_main_posy = posy

    def on_login_succeed(self):
        '''callback called on login succeed'''
        self._save_login_dimensions()
        self.config.save(self.config_path)
        self.draw_main_screen()

    def draw_main_screen(self):
        """create and populate the main screen
        """
        # clear image cache
        utils.pixbufs = {}
        self.window.clear()
        self.tray_icon.set_main(self.session)
        image_name = self.session.config.get_or_set('image_theme', 'default')
        emote_name = self.session.config.get_or_set('emote_theme', 'default')
        sound_name = self.session.config.get_or_set('sound_theme', 'default')
        gui.theme.set_theme(image_name, emote_name, sound_name)
        self.config.save(self.config_path)
        self.set_default_extensions_from_config()

        posx = self.session.config.get_or_set('i_main_posx', 100)
        posy = self.session.config.get_or_set('i_main_posy', 100)
        width = self.session.config.get_or_set('i_main_width', 250)
        height = self.session.config.get_or_set('i_main_height', 410)

        self.window.go_main(self.session,
                self.on_new_conversation, self.on_close, self.on_disconnect)
        self.window.set_location(width, height, posx, posy)

    def on_login_failed(self, reason):
        '''callback called on login failed'''
        self._new_session()
        dialog = extension.get_default('dialog')
        dialog.error(reason)
        self.window.content.set_sensitive(True)

    def on_contact_list_ready(self):
        '''callback called when the contact list is ready to be used'''
        self.window.content.contact_list.fill()
        self.window.content.panel.enabled = True

        def on_contact_added_you(responses):
            '''
            callback called when the dialog is closed
            '''
            for account in responses['accepted']:
                self.session.add_contact(account)

            for account in responses['rejected']:
                self.session.reject_contact(account)

        if self.session.contacts.pending:
            accounts = []
            for contact in self.session.contacts.pending.values():
                accounts.append((contact.account, contact.display_name))

            dialog = extension.get_default('dialog')
            dialog.contact_added_you(accounts, on_contact_added_you)

        gobject.timeout_add(500, self.session.logger.check)

    def on_nick_change_succeed(self, nick):
        '''callback called when the nick has been changed successfully'''
        self.window.content.panel.nick.text = nick

    def on_status_change_succeed(self, stat):
        '''callback called when the status has been changed successfully'''
        self.window.content.panel.status.set_status(stat)

    def on_message_change_succeed(self, message):
        '''callback called when the message has been changed successfully'''
        self.window.content.panel.message.text = message

    def on_preferences_changed(self, use_http, proxy, session_id):
        '''called when the preferences on login change'''
        self.config.session = session_id
        extension.set_default_by_id('session', session_id)
        self.config.b_use_http = use_http
        self._save_proxy_settings(proxy)

    def on_login_connect(self, account, remember_account, remember_password,
        session_id, proxy, use_http):
        '''called when the user press the connect button'''
        self.on_preferences_changed(use_http, proxy, session_id)

        if self.config.l_remember_account is None:
            self.config.l_remember_account = []

        if self.config.l_remember_password is None:
            self.config.l_remember_password = []

        if remember_password:
            self.config.d_accounts[account.account] = base64.b64encode(
                account.password)
            self.config.d_status[account.account] = account.status

            if account.account not in self.config.l_remember_account:
                self.config.l_remember_account.append(account.account)

            if account.account not in self.config.l_remember_password:
                self.config.l_remember_password.append(account.account)

        elif remember_account:
            self.config.d_accounts[account.account] = ''
            self.config.d_status[account.account] = account.status

            if account.account not in self.config.l_remember_account:
                self.config.l_remember_account.append(account.account)

        else:
            if account.account in self.config.l_remember_account:
                self.config.l_remember_account.remove(account.account)

            if account.account in self.config.l_remember_password:
                self.config.l_remember_password.remove(account.account)

            if account.account in self.config.d_accounts:
                del self.config.d_accounts[account.account]

            if account.account in self.config.d_status:
                del self.config.d_status[account.account]

        self._new_session()
        self.session.config.get_or_set('b_play_send', True)
        self.session.config.get_or_set('b_play_nudge', True)
        self.session.config.get_or_set('b_play_first_send', True)
        self.session.config.get_or_set('b_play_type', True)
        self.session.config.get_or_set('b_play_contact_online', True)
        self.session.config.get_or_set('b_play_contact_offline', True)
        self.session.config.get_or_set('b_notify_contact_online', True)
        self.session.config.get_or_set('b_notify_contact_offline', True)
        self.session.config.get_or_set('b_show_userpanel', True)
        self.session.config.get_or_set('b_show_emoticons', True)
        self.session.config.get_or_set('b_show_header', True)
        self.session.config.get_or_set('b_show_info', True)
        self.session.config.get_or_set('b_show_toolbar', True)
        self.session.login(account.account, account.password, account.status,
            proxy, use_http)
        gobject.timeout_add(500, self.session.signals._handle_events)

    def on_new_conversation(self, cid, members, other_started=True):
        '''callback called when the other user does an action that justify
        opening a conversation'''
        if self.conversations is None:
            Window = extension.get_default('window frame')
            window = Window(self._on_conversation_window_close)

            posx = self.session.config.get_or_set('i_conv_posx', 100)
            posy = self.session.config.get_or_set('i_conv_posy', 100)
            width = self.session.config.get_or_set('i_conv_width', 600)
            height = self.session.config.get_or_set('i_conv_height', 400)

            window.go_conversation(self.session)
            window.set_location(width, height, posx, posy)
            self.conversations = window.content
            window.show()

        (exists, conversation) = self.conversations.new_conversation(cid,
            members)

        conversation.update_data()

        # the following lines (up to and including the second show() )
        # do 2 things:
        # a) make sure proper tab is selected (if multiple tabs are opened)
        #    when clicking on a user icon
        # b) place cursor on text box
        # both the show() calls are needed - won't work otherwise

        conversation.show() # puts widget visible

        # conversation widget MUST be visible (cf. previous line)
        self.conversations.set_current_page(conversation.tab_index)

        # raises the container (tabbed windows) if its minimized
        self.conversations.get_parent().present()

        conversation.show() # puts cursor in textbox

        play = extension.get_default('sound')
        if other_started and \
            self.session.contacts.me.status != protocol.status.BUSY and \
            self.session.config.b_play_first_send:

            play(gui.theme.sound_send)

        return (exists, conversation)

    def _on_conversation_window_close(self):
        '''method called when the conversation window is closed'''
        width, height, posx, posy = self.conversations.get_parent().get_dimensions()
        self.session.config.i_conv_width = width
        self.session.config.i_conv_height = height
        self.session.config.i_conv_posx = posx
        self.session.config.i_conv_posy = posy

        self.conversations.close_all()
        self.conversations = None

    def start(self, account=None, accounts=None):
        Window = extension.get_default('window frame')
        self.window = Window(None) # main window

        if self.tray_icon is not None:
            self.tray_icon.set_visible(False)

        TrayIcon = extension.get_default('tray icon')
        handler = e3common.TrayIconHandler(self.session, gui.theme,
            self.on_disconnect, self.on_close)
        self.tray_icon = TrayIcon(handler, self.window)

        self.external_api = []
        for ext in extension.get_extensions('external api').values():
            try:
                inst = ext()
            except Exception, description: #on error, just discard it
                warning("errors occured when instancing %s: '%s'" % (str(ext), str(description)))
            else:
                self.external_api.append(inst)


        proxy = self._get_proxy_settings()
        use_http = self.config.get_or_set('b_use_http', False)

        posx = self.config.get_or_set('i_login_posx', 100)
        posy = self.config.get_or_set('i_login_posy', 100)
        width = self.config.get_or_set('i_login_width', 250)
        height = self.config.get_or_set('i_login_height', 410)

        self.window.go_login(self.on_login_connect,
            self.on_preferences_changed, account,
            self.config.d_accounts, self.config.l_remember_account,
            self.config.l_remember_password, self.config.d_status,
            self.config.session, proxy, use_http, self.config.session)
        self.window.set_location(width, height, posx, posy)

        self.window.show()

    def on_disconnect(self):
        """
        method called when the user selects disconnect
        """
        self.close_session(False)
        self.start()


def main():
    """
    the main method of emesene
    """
    main_method = extension.get_default('gtk main')
    main_method(Controller)

if __name__ == "__main__":
    main()
