#!/usr/bin/env python
'''main module of emesene, does the startup and related stuff'''
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

import os
from e3.common.utils import project_path

os.chdir(os.path.abspath(project_path()))

import sys
import glib
import gettext
import optparse
import shutil

import string

import debugger
import logging
log = logging.getLogger('emesene')

import e3
#from e3 import msn
from e3 import jabber
from e3 import dummy

from e3.common.DBus import DBusController

try:
    from gui import gtkui
except Exception, e:
    log.error('Cannot find/load (py)gtk: %s' % str(e))

try:
    from e3 import papylib
except Exception, exc:
    papylib = None
    log.warning('Errors occurred on papyon importing: %s' % str(exc))

from pluginmanager import get_pluginmanager
import extension
import interfaces

import gui

# fix for gstreamer --help
argv = sys.argv
sys.argv = [argv[0]]

# load translations
if os.path.exists('default.mo'):
    gettext.GNUTranslations(open('default.mo')).install()
elif os.path.exists('po/'):
    gettext.install('emesene', 'po/')
else:
    gettext.install('emesene')

class SingleInstanceOption(object):
    '''option parser'''

    def option_register(self):
        '''register the options to parse by the command line option parser'''
        option = optparse.Option("-s", "--single",
            action="count", dest="single_instance", default=False,
            help="Allow only one instance of emesene")
        return option

extension.implements('option provider')(SingleInstanceOption)
extension.get_category('option provider').activate(SingleInstanceOption)

class VerboseOption(object):
    '''option parser'''

    def option_register(self):
        '''register the options to parse by the command line option parser'''
        option = optparse.Option("-v", "--verbose",
            action="count", dest="debuglevel", default=0,
            help="Enable debug in console (add another -v to show debug)")
        return option

extension.implements('option provider')(VerboseOption)
extension.get_category('option provider').activate(VerboseOption)

class Controller(object):
    '''class that handle the transition between states of the windows'''

    def __init__(self):
        '''class constructor'''
        self.window = None
        self.tray_icon = None
        self.conversations = []
        self.single_instance = None
        self.config = e3.common.Config()
        self.config_dir = e3.common.ConfigDir('emesene2')
        self.config_path = self.config_dir.join('config')
        self.config.load(self.config_path)

        if self.config.d_accounts is None:
            self.config.d_accounts = {}
        if self.config.d_remembers is None:
            self.config.d_remembers = {}

        self.session = None
        self.timeout_id = None
        self.cur_service = None
        self._parse_commandline()
        self._setup()

    def _setup(self):
        '''register core extensions'''
        extension.category_register('session', dummy.Session, single_instance=True)
        #extension.category_register('session', msn.Session,
        #        single_instance=True)
        extension.register('session', jabber.Session)
        extension.register('session', dummy.Session)
        #extension.register('session', msn.Session)

        if papylib is not None:
            extension.register('session', papylib.Session)
            extension.set_default('session', papylib.Session)
        else:
            extension.set_default('session', dummy.Session)

        #DBus extension stuffs
        extension.category_register('external api', DBusController)
        extension.set_default('external api', DBusController)
        self.dbus_ext = extension.get_and_instantiate('external api')
        
        extension.category_register('sound', e3.common.play_sound.play)
        extension.category_register('notification',
                e3.common.notification.Notification)
        extension.category_register('history exporter',
                e3.Logger.save_logs_as_txt)

        if self.config.session is None:
            default_id = extension.get_category('session').default_id
            self.config.session = default_id
        else:
            default_id = self.config.session

        extension.set_default_by_id('session', default_id)

    def _parse_commandline(self):
        '''parse command line options'''
        options = PluggableOptionParser.get_parsing()[0]

        debugger.init(debuglevel=options.debuglevel)

        if options.single_instance:
            try:
                import SingleInstance
                self.single_instance = SingleInstance.SingleInstance()
                if self.single_instance.emesene_is_running():
                    print "Another instance of emesene is already running."
                    # try to show the instance that's already running
                    self.single_instance.show()
                    sys.exit(0)
            except ImportError:
                pass

    def start(self, account=None):
        '''the entry point to the class'''
        windowcls = extension.get_default('window frame')
        self.window = windowcls(None) # main window
        self._set_location(self.window)

        if self.tray_icon is not None:
            self.tray_icon.set_visible(False)

        trayiconcls = extension.get_default('tray icon')
        handler = gui.base.TrayIconHandler(self.session, gui.theme,
            self.on_user_disconnect, self.on_close)
        self.tray_icon = trayiconcls(handler, self.window)

        proxy = self._get_proxy_settings()
        use_http = self.config.get_or_set('b_use_http', False)
        self.go_login(proxy, use_http)

    def go_login(self, proxy=None, use_http=None, cancel_clicked=False,
            no_autologin=False):
        '''shows the login GUI'''
        if proxy is None:
            proxy = self._get_proxy_settings()
        if use_http is None:
            use_http = self.config.get_or_set('b_use_http', False)

        if self.window.content_type != 'empty':
            self.window.clear()

        self._save_login_dimensions()
        self._set_location(self.window)

        self.window.go_login(self.on_login_connect,
            self.on_preferences_changed, self.config,
            self.config_dir, self.config_path, proxy,
            use_http, self.config.session, cancel_clicked, no_autologin)
        self.tray_icon.set_login()
        self.window.show()

    def _new_session(self):
        '''create a new session object'''

        if self.session is not None:
            self.session.quit()

        self.session = extension.get_and_instantiate('session')

        # if you add a signal here, add it on _remove_subscriptions
        signals = self.session.signals
        signals.login_succeed.subscribe(self.on_login_succeed)
        signals.login_failed.subscribe(self.on_login_failed)
        signals.contact_list_ready.subscribe(self.on_contact_list_ready)
        signals.conv_first_action.subscribe(self.on_new_conversation)
        signals.disconnected.subscribe(self.on_disconnected)
        signals.picture_change_succeed.subscribe(self.on_picture_change_succeed)
        signals.contact_added_you.subscribe(self.on_pending_contacts)
        
        #let's start dbus
        self.dbus_ext.set_new_session(self.session)

    def close_session(self, do_exit=True):
        '''close session'''

        self._remove_subscriptions()

        for conv_manager in self.conversations:
            conv_manager.hide_all()
            self._on_conversation_window_close(conv_manager)

        if self.timeout_id:
            glib.source_remove(self.timeout_id)
            self.timeout_id = None

        if self.session is not None:
            self.session.quit()

        self.save_extensions_config()
        self._save_login_dimensions()

        if self.session is not None:
            self.session.save_config()
            self.session = None

        self.config.save(self.config_path)

        if do_exit:
            if self.tray_icon is not None:
                self.tray_icon.set_visible(False)
            self.window.hide()
            self.window = None

            sys.exit(0)

    def _remove_subscriptions(self):
        '''remove the subscriptions to signals'''
        if self.session is not None:
            signals = self.session.signals
            signals.login_succeed.unsubscribe(self.on_login_succeed)
            signals.login_failed.unsubscribe(self.on_login_failed)
            signals.contact_list_ready.unsubscribe(self.on_contact_list_ready)
            signals.conv_first_action.unsubscribe(self.on_new_conversation)
            signals.disconnected.unsubscribe(self.on_disconnected)
            signals.picture_change_succeed.unsubscribe(
                    self.on_picture_change_succeed)
            signals.contact_added_you.unsubscribe(self.on_pending_contacts)

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
            for cat_name, ext_id in self.session.config\
                    .d_extensions.iteritems():
                extension.set_default_by_id(cat_name, ext_id)

    def _get_proxy_settings(self):
        '''return the values of the proxy settings as a e3.Proxy object
        initialize the values on config if not exist'''

        use_proxy = self.config.get_or_set('b_use_proxy', False)
        use_proxy_auth = self.config.get_or_set('b_use_proxy_auth', False)
        host = self.config.get_or_set('proxy_host', '')
        port = self.config.get_or_set('proxy_port', '')
        user = self.config.get_or_set('proxy_user', '')
        passwd = self.config.get_or_set('proxy_passwd', '')

        self.config.get_or_set('b_use_http', False)

        return e3.Proxy(use_proxy, host, port, use_proxy_auth, user,
            passwd)

    def _save_proxy_settings(self, proxy):
        '''save the values of the proxy settings to config'''
        self.config.b_use_proxy = proxy.use_proxy
        self.config.b_use_proxy_auth = proxy.use_auth
        self.config.proxy_host = proxy.host
        self.config.proxy_port = proxy.port
        self.config.proxy_user = proxy.user
        self.config.proxy_passwd = proxy.passwd

    def _save_login_dimensions(self):
        '''save the dimensions of the login window
        '''
        width, height, posx, posy = self.window.get_dimensions()

        # when login window is minimized, posx and posy are -32000 on Windows
        if os.name == "nt":
            # make sure that the saved dimensions are visible
            if posx < (-width):
                posx = 0
            if posy < (-height):
                posy = 0

        self.config.i_login_posx = posx
        self.config.i_login_posy = posy
        self.config.i_login_width = width
        self.config.i_login_height = height

    def draw_main_screen(self):
        '''create and populate the main screen
        '''
        self.window.clear()
        self.tray_icon.set_main(self.session)

        last_avatar_path = self.session.config_dir.get_path("last_avatar")

        self.session.load_config()

        image_name = self.session.config.get_or_set('image_theme', 'default')
        emote_name = self.session.config.get_or_set('emote_theme', 'default')
        sound_name = self.session.config.get_or_set('sound_theme', 'default')
        conv_name = self.session.config.get_or_set('adium_theme',
                'renkoo.AdiumMessagesStyle')
        gui.theme.set_theme(image_name, emote_name, sound_name, conv_name)

        self.session.config.get_or_set('last_avatar', last_avatar_path)

        self.config.save(self.config_path)
        self.set_default_extensions_from_config()

        self.window.go_main(self.session,
            self.on_new_conversation, self.on_close, self.on_user_disconnect)

    def _set_location(self, window, is_conv=False):
        '''get and set the location of the window'''
        if is_conv:
            posx = self.session.config.get_or_set('i_conv_posx', 100)
            posy = self.session.config.get_or_set('i_conv_posy', 100)
            width = self.session.config.get_or_set('i_conv_width', 600)
            height = self.session.config.get_or_set('i_conv_height', 400)
        else:
            posx = self.config.get_or_set('i_login_posx', 100)
            posy = self.config.get_or_set('i_login_posy', 100)
            width = self.config.get_or_set('i_login_width', 250)
            height = self.config.get_or_set('i_login_height', 410)

        window.set_location(width, height, posx, posy)

    def on_preferences_changed(self, use_http, proxy, session_id, service):
        '''called when the preferences on login change'''
        self.config.session = session_id
        extension.set_default_by_id('session', session_id)
        self.config.b_use_http = use_http
        self.config.service = service
        self._save_proxy_settings(proxy)

    def on_login_failed(self, reason):
        '''callback called when login fails'''
        self._save_login_dimensions()
        self._remove_subscriptions()
        self._new_session()
        self.go_login(cancel_clicked=True)
        self.window.content.clear_all()
        self.window.content.show_error(reason)

    def on_login_succeed(self):
        '''callback called on login succeed'''
        self._save_login_dimensions()
        self.config.save(self.config_path)
        plugin_manager = get_pluginmanager()
        plugin_manager.scan_directory('plugins')

        self.draw_main_screen()

        self.session.config.get_or_set('l_active_plugins', [])

        for plugin in self.session.config.l_active_plugins:
            plugin_manager.plugin_start(plugin, self.session)
            # hack: where do we start this? how do we generalize for other
            # extensions?
            if plugin == "music":
                extension.get_and_instantiate('listening to',
                        self.window.content)

        self.set_default_extensions_from_config()

    def on_login_connect(self, account, session_id, proxy,
                         use_http, host=None, port=None, on_reconnect=False):
        '''called when the user press the connect button'''
        self._save_login_dimensions()
        self._set_location(self.window)
        self.cur_service = [host, port]
        if not on_reconnect:
            self.on_preferences_changed(use_http, proxy, session_id,
                    self.config.service)
            self.window.clear()
            self.avatar_path = self.config_dir.join(host, account.account,
                    'avatars', 'last')
            self.window.go_connect(self.on_cancel_login, self.avatar_path,
                    self.config)
            self.window.show()
        else:
            self.window.content.clear_connect()

        self._new_session()

        # set default values if not already set
        self.session.config.get_or_set('b_conv_minimized', True)
        self.session.config.get_or_set('b_mute_sounds', False)
        self.session.config.get_or_set('b_play_send', True)
        self.session.config.get_or_set('b_play_nudge', True)
        self.session.config.get_or_set('b_play_first_send', True)
        self.session.config.get_or_set('b_play_type', True)
        self.session.config.get_or_set('b_play_contact_online', True)
        self.session.config.get_or_set('b_play_contact_offline', True)
        self.session.config.get_or_set('b_notify_contact_online', True)
        self.session.config.get_or_set('b_notify_contact_offline', True)
        self.session.config.get_or_set('b_notify_receive_message', True)
        self.session.config.get_or_set('b_show_userpanel', True)
        self.session.config.get_or_set('b_show_emoticons', True)
        self.session.config.get_or_set('b_show_header', True)
        self.session.config.get_or_set('b_show_info', True)
        self.session.config.get_or_set('b_show_toolbar', True)
        self.session.config.get_or_set('b_allow_auto_scroll', True)
        self.session.config.get_or_set('adium_theme',
                'renkoo.AdiumMessageStyle')
        self.session.config.get_or_set('b_enable_spell_check', False)
        self.session.config.get_or_set('b_download_folder_per_account', False)

        self.timeout_id = glib.timeout_add(500,
                self.session.signals._handle_events)
        self.session.login(account.account, account.password, account.status,
            proxy, host, port, use_http)

    def on_cancel_login(self):
        '''
        method called when user select cancel login
        '''
        if self.session is not None:
            self.session.quit()
        self.go_login(cancel_clicked=True, no_autologin=True)

    def on_pending_contacts(self):
        '''callback called when some contact is pending'''
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

    def on_contact_list_ready(self):
        '''callback called when the contact list is ready to be used'''
        self.window.content.contact_list.fill()

        self.on_pending_contacts()

        glib.timeout_add(500, self.session.logger.check)

        notificationcls = extension.get_default('notification')
        self.notification = notificationcls(self.session)

    def on_new_conversation(self, cid, members, other_started=True):
        '''callback called when the other user does an action that justify
        opening a conversation'''
        conversation_tabs = self.session.config.get_or_set(
                'b_conversation_tabs', True)

        conv_manager = None

        # check to see if there is a conversation with the same member
        for convman in self.conversations:
            if convman.reuse_conversation(cid, members):
                conv_manager = convman
                break

        if conv_manager is None:
            if not self.conversations or not conversation_tabs:

                windowcls = extension.get_default('window frame')
                window = windowcls(self._on_conversation_window_close)

                window.go_conversation(self.session)
                self._set_location(window, True)
                conv_manager = window.content
                self.conversations.append(conv_manager)

                if self.session.config.b_conv_minimized:
                    window.iconify()

                window.show()

            else:
                conv_manager = self.conversations[0]


        self.tray_icon.set_conversations(self.conversations)

        conversation = conv_manager.new_conversation(cid, members)

        conversation.update_data()
        conversation.show() # puts widget visible

        # raises the container and grabs the focus
        # handles cases where window is minimized and ctrl+tab focus stealing
        if not other_started:
            conv_manager.present(conversation)


        if not self.session.config.b_mute_sounds and other_started and \
           self.session.contacts.me.status != e3.status.BUSY and \
           self.session.config.b_play_first_send and not \
           self.session.config.b_play_type:
            gui.play(self.session, gui.theme.sound_send)

    def _on_conversation_window_close(self, conv_manager):
        '''method called when the conversation window is closed'''
        width, height, posx, posy = \
                conv_manager.get_dimensions()

        # when window is minimized, posx and posy are -32000 on Windows
        if os.name == "nt":
            # make sure that the saved dimensions are visible
            if posx < (-width):
                posx = 0
            if posy < (-height):
                posy = 0

        self.session.config.i_conv_width = width
        self.session.config.i_conv_height = height
        self.session.config.i_conv_posx = posx
        self.session.config.i_conv_posy = posy

        conv_manager.close_all()
        self.conversations.remove(conv_manager)

    def on_user_disconnect(self):
        '''
        method called when the user selects disconnect
        '''
        self.close_session(False)
        self.go_login(cancel_clicked=True, no_autologin=True)

    def on_close(self):
        '''called on close'''
        self.close_session()

    def on_disconnected(self, reason, reconnect=0):
        '''called when the server disconnect us'''
        account = self.session.account
        self.close_session(False)
        if reconnect:
            self.on_reconnect(account)
        else:
            self.go_login(cancel_clicked=True, no_autologin=True)
            if(reason != None):
                self.window.content.clear_all()
                self.window.content.show_error(reason)

    def on_reconnect(self, account):
        '''makes the reconnect after 30 seconds'''
        self.window.clear()
        self.window.go_connect(self.on_cancel_login, self.avatar_path,
                self.config)

        proxy = self._get_proxy_settings()
        use_http = self.config.get_or_set('b_use_http', False)
        self.window.content.on_reconnect(self.on_login_connect, account, \
                                         self.config.session, proxy, use_http, \
                                         self.cur_service)

    def on_picture_change_succeed(self, account, path):
        '''save the avatar change as the last avatar'''
        if account == self.session.account.account:
            last_avatar_path = self.session.config_dir.get_path("last_avatar")
            shutil.copy(path, last_avatar_path)

class ExtensionDefault(object):
    '''extension to register options for extensions'''

    def option_register(self):
        '''register options'''
        option = optparse.Option('--ext-default', '-e')
        option.type = 'string' #well, it's a extName:defaultValue string
        option.action = 'callback'
        option.callback = self.set_default
        option.help = 'Set the default extension by name'
        option.nargs = 1
        return option

    def set_default(self, option, opt, value, parser):
        '''set default extensions'''
        for couple in value.split(';'):
            category_name, ext_name = map(string.strip, couple.split(':', 2))

            if not extension.get_category(category_name)\
                    .set_default_by_name(ext_name):
                print 'Error setting extension "%s" default session to "%s"'\
                        % (category_name, ext_name)

extension.implements('option provider')(ExtensionDefault)
extension.get_category('option provider').activate(ExtensionDefault)


class PluggableOptionParser(object):

    results = ()

    def __init__(self, args):
        self.parser = optparse.OptionParser(conflict_handler="resolve")
        self.args = args
        custom_options = extension.get_category('option provider').use()()\
                .option_register().get_result()
        for opt in custom_options.values():
            self.parser.add_option(opt)

    def read_options(self):
        if not self.__class__.results:
            self.__class__.results = self.parser.parse_args(self.args)
        return self.__class__.results

    @classmethod
    def get_parsing(cls):
        return cls.results


def main():
    """
    the main method of emesene
    """
    extension.category_register('session', dummy.Session, single_instance=True)
    extension.category_register('option provider', None,
            interfaces=interfaces.IOptionProvider)
    extension.get_category('option provider').multi_extension = True
    extension.get_category('option provider').activate(ExtensionDefault)
    options = PluggableOptionParser(argv)
    options.read_options()
    main_method = extension.get_default('main')
    main_method(Controller)

if __name__ == "__main__":
    main()
