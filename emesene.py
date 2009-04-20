import sys
import gtk
import time
import base64
import gobject

import debugger

import e3
import gui
import yaber
import e3common
import protocol

import extension
import e3gtk

class Controller(object):
    '''class that handle the transition between states of the windows'''

    def __init__(self):
        '''class constructor'''
        self.window = None
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
        e3gtk.setup()
        extension.category_register('session', e3.Session)
        extension.register('session', yaber.Session)
        extension.category_register('sound', e3common.play_sound.play)
        extension.category_register('notification', e3common.notification.notify)

        if self.config.session is None:
            default_id = extension.get_category('session').default_id
            self.config.session = default_id
        else:
            default_id = self.config.session

        extension.set_default_by_id('session', default_id)

    def _new_session(self):
        '''create a new session object'''

        if self.session is not None:
            self.session.quit()

        Session = extension.get_default('session')
        self.session = Session()
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
        if self.session is not None:
            self.session.quit()

        self.window.hide()
        self.save_extensions_config()

        if self.session is not None:
            self.session.save_config()

        self.config.save(self.config_path)

        if self.conversations:
            self.conversations.get_parent().hide()

        while gtk.events_pending():
            gtk.main_iteration(False)

        time.sleep(2)
        sys.exit(0)

    def on_login_succeed(self):
        '''callback called on login succeed'''
        self.window.clear()
        self.tray_icon.set_main(self.session)
        self.config.save(self.config_path)
        self.set_default_extensions_from_config()
        self.window.go_main(self.session, self.on_new_conversation,
            self.on_close)

    def on_login_failed(self, reason):
        '''callback called on login failed'''
        self._new_session()
        dialog = extension.get_default('gtk dialog')
        dialog.error(reason)
        self.window.content.set_sensitive(True)

    def on_contact_list_ready(self):
        '''callback called when the contact list is ready to be used'''
        self.window.content.contact_list.fill()
        self.window.content.panel.enabled = True

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
        opeinig a conversation'''
        if self.conversations is None:
            Window = extension.get_default('gtk window frame')
            window = Window(self._on_conversation_window_close)
            window.set_default_size(640, 480)
            window.go_conversation(self.session)
            self.conversations = window.content
            window.show()

        (exists, conversation) = self.conversations.new_conversation(cid,
            members)

        conversation.update_data()
        self.conversations.get_parent().present()

        conversation.show()

        play = extension.get_default('sound')
        if other_started and \
            self.session.contacts.me.status != protocol.status.BUSY and \
            self.session.config.b_play_first_send:

            play(gui.theme.sound_send)

        return (exists, conversation)

    def _on_conversation_window_close(self):
        '''method called when the conversation window is closed'''
        self.conversations.close_all()
        self.conversations = None

    def start(self, account=None, accounts=None):
        Window = extension.get_default('gtk window frame')
        TrayIcon = extension.get_default('gtk tray icon')
        self.window = Window(self.on_close)
        handler = e3common.TrayIconHandler(self.session, gui.theme, 
            self.on_disconnect, self.on_close)
        self.tray_icon = TrayIcon(handler)

        proxy = self._get_proxy_settings()
        use_http = self.config.get_or_set('b_use_http', False)

        self.window.go_login(self.on_login_connect,
            self.on_preferences_changed, account,
            self.config.d_accounts, self.config.l_remember_account,
            self.config.l_remember_password, self.config.d_status,
            self.config.session, proxy, use_http, self.config.session)

        self.window.show()

    def on_disconnect(self):
        """
        method called when the user selects disconnect
        """
        pass


def main():
    """
    the main method of emesene
    """
    gobject.threads_init()
    gtk.gdk.threads_init()
    controller = Controller()
    controller.start()
    gtk.quit_add(0, controller.on_close)
    gtk.main()

if __name__ == "__main__":
    main()

