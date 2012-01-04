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
import sys


# Extract any non-GStreamer arguments, and leave the GStreamer arguments for
# processing by GStreamer. This needs to be done before GStreamer is imported,
# so that GStreamer doesn't hijack e.g. ``--help``.
# NOTE This naive fix does not support values like ``bar`` in
# ``--gst-foo bar``. Use equals to pass values, like ``--gst-foo=bar``.
gstreamer_args = [arg for arg in sys.argv[1:] if arg.startswith('--gst')]
emesene_args = [arg for arg in sys.argv[1:] if not arg.startswith('--gst')]
sys.argv[1:] = gstreamer_args

def we_are_frozen():
    """Returns whether we are frozen via py2exe.
    This will affect how we find out where we are located."""

    return hasattr(sys, "frozen")

def project_path():
    """ This will get us the program's directory,
    even if we are frozen using py2exe"""

    if we_are_frozen():
        path = os.path.abspath(os.path.dirname(unicode(sys.executable,
            sys.getfilesystemencoding())))
        if sys.executable.endswith("portable.exe") or \
           sys.executable.endswith("portable_debug.exe"):
            os.environ['APPDATA'] = path
        return path

    this_module_path = os.path.dirname(unicode(__file__,
        sys.getfilesystemencoding()))

    return os.path.abspath(this_module_path)

os.chdir(os.path.abspath(project_path()))

import gettext
# load translations
if os.path.exists('default.mo'):
    gettext.GNUTranslations(open('default.mo')).install()
elif os.path.exists('po/'):
    gettext.install('emesene', 'po/')
else:
    gettext.install('emesene')

import glib
import optparse
import shutil
import signal

import debugger
import logging
log = logging.getLogger('emesene')

import e3
#from e3 import msn
from e3 import dummy

try:
    from e3.common.DBus import DBusController
except ImportError:
    DBusController = None

try:
    from e3.common.NetworkManagerHelper import DBusNetworkChecker
except ImportError:
    DBusNetworkChecker = None

try:
    from gui import gtkui
except ImportError, exc:
    print 'Cannot import gtkui: %s' % str(exc)

try:
    from e3 import jabber
except ImportError, exc:
    jabber = None
    print 'Errors occurred while importing jabber backend: %s' % str(exc)

try:
    from gui import qt4ui
except ImportError, exc:
    log.error('Cannot import qtui: %s' % str(exc))

try:
    from e3 import papylib
except ImportError, exc:
    papylib = None
    print 'Errors occurred while importing msn backend: %s' % str(exc)

from pluginmanager import get_pluginmanager
import extension
import interfaces
import gui
import optionprovider

class Controller(object):
    '''class that handle the transition between states of the windows'''

    def __init__(self):
        '''class constructor'''
        self.window = None
        self.tray_icon = None
        self.conversations = []
        self.minimize = False
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
        self.logged_in = False
        self.timeout_id = None
        self.cur_service = None
        self.notification = None
        self.conv_manager_available = False
        self.last_session_account = None
        self.last_session_service = None

        self._parse_commandline()
        self._setup()

        if hasattr(signal, 'SIGINT'):
            signal.signal(signal.SIGINT,
                lambda * args: glib.idle_add(self.close_session))
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM,
                lambda * args: glib.idle_add(self.close_session))
        if hasattr(signal, 'SIGHUP'):
            signal.signal(signal.SIGHUP,
                lambda * args: glib.idle_add(self.close_session))

    def _setup(self):
        '''register core extensions'''
        extension.category_register('session', dummy.Session,
                single_instance=True)
        #extension.category_register('session', msn.Session,
        #        single_instance=True)
        if jabber is not None:
            extension.register('session', jabber.Session)
        extension.register('session', dummy.Session)
        #extension.register('session', msn.Session)

        if papylib is not None:
            extension.register('session', papylib.Session)
            extension.set_default('session', papylib.Session)
        else:
            extension.set_default('session', dummy.Session)

        #DBus extension stuffs
        if DBusController is not None:
            extension.category_register('external api', DBusController)
            extension.set_default('external api', DBusController)
            self.dbus_ext = extension.get_and_instantiate('external api')
        else:
            self.dbus_ext = None

        if DBusNetworkChecker is not None:
            extension.category_register('network checker', DBusNetworkChecker)
            extension.set_default('network checker', DBusNetworkChecker)
            self.network_checker = extension.get_and_instantiate(
                    'network checker')
        else:
            self.network_checker = None

        self.unity_launcher = extension.get_and_instantiate('unity launcher')

        extension.category_register('sound', e3.common.Sounds.SoundPlayer,
                None, True)
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

        if options.minimized:
            self.minimize = True

    def start(self, account=None):
        '''the entry point to the class'''
        windowcls = extension.get_default('window frame')
        self.window = windowcls(self.close_session) # main window
        self._set_location(self.window)

        self._draw_tray_icon()

        proxy = self._get_proxy_settings()
        use_http = self.config.get_or_set('b_use_http', False)
        self.go_login(proxy, use_http)

        if self.minimize:
            self.window.iconify()
        self.window.show()

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

    def _new_session(self, account=None):
        '''create a new session object'''

        if self.session is not None:
            self.session.quit()

        self.session = extension.get_and_instantiate('session')

        # if you add a signal here, add it on _remove_subscriptions
        signals = self.session.signals
        signals.close.subscribe(self.on_close)
        signals.login_succeed.subscribe(self.on_login_succeed)
        signals.login_failed.subscribe(self.on_login_failed)
        signals.contact_list_ready.subscribe(self.on_contact_list_ready)
        signals.conv_first_action.subscribe(self.on_new_conversation)
        signals.disconnected.subscribe(self.on_disconnected)
        signals.picture_change_succeed.subscribe(self.on_picture_change_succeed)
        signals.contact_added_you.subscribe(self.on_pending_contacts)

        #let's start dbus and unity launcher
        if self.dbus_ext is not None:
            self.dbus_ext.set_new_session(self.session, self.window)
        if self.unity_launcher is not None:
            self.unity_launcher.set_session(self.session)

    def _restore_session(self):
        account = self.session.account
        if self.conv_manager_available:
            self.session.conversation_managers = []
            if account and self.last_session_account == account.account and \
               self.last_session_service == account.service:
                self.conv_manager_available = False
                self.session.conversations = {}
                for conv_manager in self.conversations:
                    conv_manager.renew_session(self.session)
                    self.session.conversation_managers.append(conv_manager)
                self.tray_icon.set_conversations(self.conversations)
                if self.unity_launcher is not None:
                    self.unity_launcher.set_conversations(self.conversations)
            else:
                for conv_manager in self.conversations:
                    conv_manager.hide_all()
                    # _on_conversation_window_close, without saving settings
                    conv_manager.close_all()
                    self.conversations.remove(conv_manager)

        self.last_session_account = account.account
        self.last_session_service = account.service

    def close_session(self, do_exit=True, server_disconnected=False):
        '''close session'''
        # prevent preference window from staying open and breaking things
        pref = extension.get_instance('preferences')
        if pref:
            pref.hide()

        self._remove_subscriptions()

        if server_disconnected:
            for conv_manager in self.conversations:
                conv_manager.close_session()
            self.conv_manager_available = True # update with new session
        else:
            for conv_manager in self.conversations:
                conv_manager.hide_all()
                self._on_conversation_window_close(conv_manager)

        if self.timeout_id:
            glib.source_remove(self.timeout_id)
            self.timeout_id = None

        if self.session is not None:
            self.session.stop_mail_client()
            self.session.quit()

        self.window.on_disconnect(self.close_session)

        self.save_extensions_config()
        self._save_login_dimensions()

        if self.session is not None and self.logged_in:
            self.session.save_config()
            self.session = None
            self.logged_in = False

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
            signals.close.unsubscribe(self.on_close)
            signals.login_succeed.unsubscribe(self.on_login_succeed)
            signals.login_failed.unsubscribe(self.on_login_failed)
            signals.contact_list_ready.unsubscribe(self.on_contact_list_ready)
            signals.conv_first_action.unsubscribe(self.on_new_conversation)
            signals.disconnected.unsubscribe(self.on_disconnected)
            signals.picture_change_succeed.unsubscribe(
                    self.on_picture_change_succeed)
            signals.contact_added_you.unsubscribe(self.on_pending_contacts)
            if self.unity_launcher is not None:
                self.unity_launcher.remove_session()
            # unsubscribe notifications signals
            if self.notification:
                self.notification.remove_subscriptions()
                self.notification = None

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

        if not self.window.is_maximized():
            self.config.i_login_posx = posx
            self.config.i_login_posy = posy
            self.config.i_login_width = width
            self.config.i_login_height = height
            self.config.b_login_maximized = False
        else:
            self.config.b_login_maximized = True

    def draw_main_screen(self):
        '''create and populate the main screen
        '''
        self.window.clear()

        last_avatar_path = self.session.config_dir.get_path("last_avatar")
        self.session.load_config()

        if 'msn' in self.session.SERVICES:
            # keepalive conversations...or not
            b_keepalive = self.session.config.get_or_set("b_papylib_keepalive", False)
            self.session.get_worker().keepalive_conversations = b_keepalive

        image_name = self.session.config.get_or_set('image_theme', 'default')
        emote_name = self.session.config.get_or_set('emote_theme', 'default')
        sound_name = self.session.config.get_or_set('sound_theme', 'default')
        conv_name = self.session.config.get_or_set('adium_theme',
                'renkoo.AdiumMessagesStyle')
        conv_name_variant = self.session.config.get_or_set('adium_theme_variant',
                '')
        gui.theme.set_theme(image_name, emote_name, sound_name, conv_name, conv_name_variant)

        self.session.config.get_or_set('last_avatar', last_avatar_path)

        self.config.save(self.config_path)
        self.set_default_extensions_from_config()

        self._draw_tray_icon()
        self.tray_icon.set_main(self.session)

        self.window.go_main(self.session, self.on_new_conversation,
                            self.tray_icon.quit_on_close)

    def _draw_tray_icon(self):
        '''draws the tray icon'''
        trayiconcls = extension.get_default('tray icon')

        if self.tray_icon is not None:
            if trayiconcls == self.tray_icon.__class__:
                return
            self.tray_icon.set_visible(False)

        handler = gui.base.TrayIconHandler(self.session, gui.theme, self.close_session)
        self.tray_icon = trayiconcls(handler, self.window)

    def _sync_emesene1(self):
        syn = extension.get_default('synch tool')
        # Check if a synch tool is present. Synch tool is only in the gtk gui.
        # Remove the following 'if' when it will be in the qt4 gui too.
        if syn:
            user = self.session.account.account
            current_service = self.session.config.service
            syn = syn(self.session, current_service)
            syn.show()

    def _set_location(self, window, is_conv=False):
        '''get and set the location of the window'''
        if is_conv:
            posx = self.session.config.get_or_set('i_conv_posx', 100)
            posy = self.session.config.get_or_set('i_conv_posy', 100)
            width = self.session.config.get_or_set('i_conv_width', 600)
            height = self.session.config.get_or_set('i_conv_height', 400)
            maximized = self.session.config.get_or_set('b_conv_maximized',
                    False)
        else:
            posx = self.config.get_or_set('i_login_posx', 100)
            posy = self.config.get_or_set('i_login_posy', 100)
            width = self.config.get_or_set('i_login_width', 250)
            height = self.config.get_or_set('i_login_height', 410)
            maximized = self.config.get_or_set('b_login_maximized', False)

        screen = window.get_screen()
        pwidth, pheight = screen.get_width(), screen.get_height()
        if posx > pwidth:
            posx = (pwidth - width) // 2
        if posy > pheight:
            posy = (pheight - height) // 2
        if maximized:
            window.maximize()

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

    def _setup_plugins(self):
        plugin_manager = get_pluginmanager()
        plugin_manager.scan_directory('plugins')
        plugin_dir = self.config_dir.join('plugins')
        if not os.path.exists(plugin_dir):
            os.makedirs(plugin_dir)
        plugin_manager.scan_directory(plugin_dir)

        self.session.config.get_or_set('l_active_plugins', [])

        for plugin in self.session.config.l_active_plugins:
            plugin_manager.plugin_start(plugin, self.session)
        self.set_default_extensions_from_config()
        self.window.content.replace_extensions()

    def on_login_succeed(self):
        '''callback called on login succeed'''
        self._save_login_dimensions()
        self.config.save(self.config_path)

        self.draw_main_screen()
        self._setup_plugins()

        self._restore_session()

        self._sync_emesene1()

        self.session.start_mail_client()
        self.logged_in = True

        if self.network_checker is not None:
            self.network_checker.set_new_session(self.session)

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

        self._new_session(account)
        
        # set default values if not already set
        self.session.config.get_or_set('b_conv_minimized', True)
        self.session.config.get_or_set('b_conv_maximized', False)
        self.session.config.get_or_set('b_mute_sounds', False)
        self.session.config.get_or_set('b_play_send', False)
        self.session.config.get_or_set('b_play_nudge', True)
        self.session.config.get_or_set('b_play_first_send', True)
        self.session.config.get_or_set('b_play_type', True)
        self.session.config.get_or_set('b_mute_sounds_when_focussed', True)
        self.session.config.get_or_set('b_play_contact_online', True)
        self.session.config.get_or_set('b_play_contact_offline', True)
        self.session.config.get_or_set('b_notify_contact_online', True)
        self.session.config.get_or_set('b_notify_contact_offline', True)
        self.session.config.get_or_set('b_notify_receive_message', True)
        self.session.config.get_or_set('b_notify_only_when_available', True)
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
        self.session.config.get_or_set('b_override_text_color', False)
        self.session.config.get_or_set('override_text_color', '#000000')

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
        self.soundPlayer = extension.get_and_instantiate('sound', self.session)

    def on_new_conversation(self, cid, members, other_started=True):
        '''callback called when the other user does an action that justify
        opening a conversation'''
        conversation_tabs = self.session.config.get_or_set(
                'b_conversation_tabs', True)

        conv_manager = None

        # check to see if there is a conversation with the same member
        for convman in self.conversations:
            if convman.has_similar_conversation(cid, members):
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
                self.session.conversation_managers.append(conv_manager)

                if self.session.config.b_conv_minimized and other_started:
                    window.iconify()
                    window.show()
                    window.iconify()
                else:
                    window.show()

            else:
                conv_manager = self.conversations[0]


        self.tray_icon.set_conversations(self.conversations)
        if self.unity_launcher is not None:
            self.unity_launcher.set_conversations(self.conversations)

        conversation = conv_manager.new_conversation(cid, members)

        conversation.update_data()
        conversation.show(other_started) # puts widget visible

        # raises the container and grabs the focus
        # handles cases where window is minimized and ctrl+tab focus stealing
        if not other_started:
            conv_manager.present(conversation)


        if self.session.config.b_play_first_send and not \
           self.session.config.b_play_type:
            self.soundPlayer.play(gui.theme.sound_theme.sound_type)

    def _on_conversation_window_close(self, conv_manager):
        '''method called when the conversation window is closed'''
        if self.session:
            width, height, posx, posy = \
                    conv_manager.get_dimensions()

            # when window is minimized, posx and posy are -32000 on Windows
            if os.name == "nt":
                # make sure that the saved dimensions are visible
                if posx < (-width):
                    posx = 0
                if posy < (-height):
                    posy = 0

            if not conv_manager.is_maximized():
                self.session.config.i_conv_width = width
                self.session.config.i_conv_height = height
                self.session.config.i_conv_posx = posx
                self.session.config.i_conv_posy = posy
                self.session.config.b_conv_maximized = False
            else:
                self.session.config.b_conv_maximized = True
            self.session.conversation_managers.remove(conv_manager)

        conv_manager.close_all()
        self.conversations.remove(conv_manager)

    def on_close(self, close=False):
        '''called when the session is closed by the user'''
        self.close_session(close)
        if not close:
            self.go_login(cancel_clicked=True, no_autologin=True)

    def on_disconnected(self, reason, reconnect=0):
        '''called when the server disconnect us'''
        account = self.session.account
        self.close_session(False, True)
        if reconnect:
            self.on_reconnect(account)
        else:
            self.go_login(cancel_clicked=True, no_autologin=True)
            if reason is not None:
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
            if path:
                shutil.copy(path, last_avatar_path)
            else:
                try:
                    os.remove(last_avatar_path)
                except OSError, e:
                    log.warning("Cannot remove file: %s" % e)

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
    extension.get_category('option provider').activate(optionprovider.ExtensionDefault)
    options = PluggableOptionParser(args=emesene_args)
    options.read_options()
    main_method = extension.get_default('main')
    main_method(Controller)

if __name__ == "__main__":
    main()
