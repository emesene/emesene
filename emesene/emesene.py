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

# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# we will set the default encoding ourselves to UTF-8.
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
else:
    raw_input = input

if sys.platform == 'darwin':
    sys.path.append("/Applications/emesene.app/Contents/Resources/gtk/inst/lib/python2.7/site-packages")
    sys.path.append("/Applications/emesene.app/Contents/Resources/gtk/inst/lib/python2.7/site-packages/gtk-2.0")
    sys.path.append("/Applications/emesene.app/Contents/Resources/gtk/inst/lib/python2.6/site-packages")
    sys.path.append("/Applications/emesene.app/Contents/Resources/gtk/inst/lib/python2.6/site-packages/gtk-2.0")

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

from Language import get_language_manager
language_management = get_language_manager()
language_management.install_default_translation()
import extension

if 'USE_GI' in os.environ:
    try:
        import pygicompat
    except ImportError:
        print "error: pygi compat not found"
        pass

import glib
import shutil
import signal
import time
import datetime
import Info
try:
    contrib = open("CONTRIBUTORS", "r")
    Info.EMESENE_CONTRIBUTORS = contrib.read().split("\n")
    contrib.close()
except: #gotta catch 'em all!
    Info.EMESENE_CONTRIBUTORS = ['BUG: CONTRIBUTORS file is missing!',
                                 'Report this to whoever made the package you\'re using.']
import debugger
import logging
log = logging.getLogger('emesene')

import e3
from e3 import dummy

try:
    from gui import gtkui
except ImportError, exc:
    print 'Cannot import gtkui: %s' % str(exc)

try:
    from e3 import xmpp
except ImportError, exc:
    xmpp = None
    print 'Errors occurred while importing xmpp backend: %s' % str(exc)

try:
    from gui import qt4ui
except ImportError, exc:
    log.error('Cannot import qtui: %s' % str(exc))

try:
    from e3 import papylib
except ImportError, exc:
    papylib = None
    print 'Errors occurred while importing msn backend: %s' % str(exc)

try:
    from e3 import webqq
except ImportError , exc:
    webqq = None

from e3.common.pluginmanager import get_pluginmanager
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
        self.config_dir = e3.common.ConfigDir()
        self.config_path = self.config_dir.join('config')
        self.config.load(self.config_path)

        if self.config.d_accounts is None:
            self.config.d_accounts = {}
        if self.config.d_remembers is None:
            self.config.d_remembers = {}

        self.session = None
        self.logged_in = False
        self.cur_service = None
        self.notification = None
        self.conv_manager_available = False
        self.last_session_account = None
        self.last_session_service = None

        lang = self.config.get_or_set("language_config", None)
        language_management.install_desired_translation(lang)

        self._parse_commandline()
        self._setup()

        if hasattr(signal, 'SIGINT'):
            signal.signal(signal.SIGINT,
                lambda * args: glib.idle_add(self.kill))
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM,
                lambda * args: glib.idle_add(self.kill))
        if hasattr(signal, 'SIGHUP'):
            signal.signal(signal.SIGHUP,
                lambda * args: glib.idle_add(self.kill))

    def _setup(self):
        '''register core extensions'''
        extension.category_register('session', dummy.Session,
                single_instance=True)
        if Info.EMESENE_VERSION.endswith("dev"):
            extension.register('session', dummy.Session)

        if webqq is not None:
            extension.register('session', webqq.Session)
            extension.set_default('session', webqq.Session)

        if xmpp is not None:
            extension.register('session', xmpp.Session)
            extension.set_default('session', xmpp.Session)

        if papylib is not None:
            extension.register('session', papylib.Session)
            extension.set_default('session', papylib.Session)

        #external API stuff
        self.dbus_ext = extension.get_and_instantiate('external api')
        self.network_checker = extension.get_and_instantiate(
            'network checker')

        self.unity_launcher = extension.get_and_instantiate('unity launcher')

        extension.category_register('sound', e3.common.Sounds.SoundPlayer,
                None, True)
        extension.category_register('notification',
                e3.common.notification.Notification)
        extension.category_register('history exporter', e3.Logger.ExporterTxt)
        extension.register('history exporter', e3.Logger.ExporterXml)
        extension.register('history exporter', e3.Logger.ExporterHtml)
        extension.register('history exporter', e3.Logger.ExporterCsv)
        extension.register('history exporter', e3.Logger.ExporterJSON)

        # ui callbacks for plugins
        extension.category_register('send message callback handler',
            e3.common.PriorityList, single_instance=True)
        extension.category_register('receive message callback handler',
            e3.common.PriorityList, single_instance=True)

        if self.config.session is None:
            default_id = extension.get_category('session').default_id
            self.config.session = default_id
        else:
            default_id = self.config.session

        extension.set_default_by_id('session', default_id)

    def _parse_commandline(self):
        '''parse command line options'''
        options = optionprovider.PluggableOptionParser.get_parsing()[0]

        debugger.init(debuglevel=options.debuglevel)

        if options.version:
            print "Current Emesene Version: " + Info.EMESENE_VERSION
            print "Last Stable Version: " + Info.EMESENE_LAST_STABLE
            print "\n" + Info.EMESENE_WEBSITE
            sys.exit(0)

        #needed to check for autologin
        self.emesene_is_running = False
        try:
            if os.name == 'posix':
                from SingleInstance import SingleInstancePosix as SingleInstance
            else:
                from SingleInstance import SingleInstanceWin32 as SingleInstance

            self.single_instance = SingleInstance()
            if self.single_instance.emesene_is_running():
                self.emesene_is_running = True
                # try to show the instance that's already running
                if options.single_instance:
                    print "Another instance of emesene is already running."
                    self.single_instance.show()
                    extension.get_and_instantiate('quit')
        except ImportError:
            pass

        if options.minimized:
            self.minimize = True

    def start(self, account=None):
        '''the entry point to the class'''
        windowcls = extension.get_default('window frame')
        self.window = windowcls(self.close_session) # main window
        self._set_location(self.window)

        self._draw_tray_icon() # default tray icon

        proxy = self._get_proxy_settings()
        use_http = self.config.get_or_set('b_use_http', False)
        use_ipv6 = self.config.get_or_set('b_use_ipv6', False)

        #cancel autologin if another emesene instance is running
        self.go_login(proxy, use_http, use_ipv6, no_autologin=self.emesene_is_running)

        if self.minimize:
            self.window.iconify()
        self.window.show()

    def go_login(self, proxy=None, use_http=None, use_ipv6=None,
                 cancel_clicked=False, no_autologin=False):
        '''shows the login GUI'''
        if proxy is None:
            proxy = self._get_proxy_settings()
        if use_http is None:
            use_http = self.config.get_or_set('b_use_http', False)
        if use_ipv6 is None:
            use_ipv6 = self.config.get_or_set('b_use_ipv6', False)

        self._save_login_dimensions()
        self._set_location(self.window)

        self.window.go_login(self.on_login_connect,
                             self.on_preferences_changed, self.config,
                             self.config_dir, self.config_path, proxy,
                             use_http, use_ipv6, self.config.session,
                             cancel_clicked, no_autologin)
        self.tray_icon.set_login()

    def _new_session(self, account=None):
        '''create a new session object'''

        if self.session:
            self.close_session(False)

        self.session = extension.get_and_instantiate('session')

        self.session.cb_gui_send_message = extension.get_and_instantiate('send message callback handler')
        self.session.cb_gui_recv_message = extension.get_and_instantiate('receive message callback handler')

        # if you add a signal here, add it on _remove_subscriptions
        signals = self.session.signals
        signals.close.subscribe(self.on_close)
        signals.login_succeed.subscribe(self.on_login_succeed)
        signals.login_failed.subscribe(self.on_login_failed)
        signals.contact_list_ready.subscribe(self.on_contact_list_ready)
        signals.conv_first_action.subscribe(self.on_new_conversation)
        signals.disconnected.subscribe(self.on_disconnected)
        signals.picture_change_succeed.subscribe(self.on_picture_change_succeed)

        #let's start dbus and unity launcher
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
            else:
                for conv_manager in self.conversations:
                    conv_manager.close_all()
                    self.conversations.remove(conv_manager)

        self.last_session_account = account.account
        self.last_session_service = account.service

    def kill(self):
        '''method that tries to kill emesene in a friendly way'''
        try:
            self.close_session()
        except:
            log.exception("Error while shutting down")
            sys.exit(1)

    def close_session(self, do_exit=True, server_disconnected=False):
        '''close session'''
        # prevent preference window from staying open and breaking things
        pref = extension.get_instance('preferences')
        if pref:
            pref.hide()

        # close all dialogs that are open
        extension.get_default('dialog').close_all()

        self._remove_subscriptions()

        if server_disconnected:
            for conv_manager in self.conversations:
                conv_manager.close_session()
            self.conv_manager_available = True # update with new session
        else:
            for conv_manager in self.conversations:
                conv_manager.close_all()

        if self.session:
            self.session.stop_mail_client()
            self.session.quit()
            self._save_application_language()
            self.session.save_extensions_config()

        self._save_login_dimensions()

        if self.session and self.logged_in:
            self.session.save_config()
            self.logged_in = False

        self.session = None

        self.config.save(self.config_path)

        #http://www.lshift.net/blog/2008/11/14/tracing-python-memory-leaks
        #http://mg.pov.lt/objgraph/
        # install python-objgraph
        # also you can run emesene in pdb: pdb ./emesene.py
        # then 'r' and CTRL+C when you need the shell.
        #import objgraph
        ##objgraph.show_most_common_types()
        #objgraph.show_growth(limit=None)

        if do_exit:
            extension.get_and_instantiate('quit')
            if os.name == "nt":
                os._exit(0)

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
            if self.unity_launcher is not None:
                self.unity_launcher.remove_session()
            # unsubscribe notifications signals
            if self.notification:
                self.notification.remove_subscriptions()
                self.notification = None
            if self.tray_icon:
                self.tray_icon.unsubscribe()
            self.window.on_disconnect(self.close_session)
            self.dbus_ext.stop()

    def _save_application_language(self):
        '''save global settings to application config
           obtained from session settings.
        '''
        if self.config is None:
            return
        self.config.language_config = self.session.config.language_config

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
        last_avatar_path = self.session.config_dir.get_path("last_avatar")
        self.session.load_config()

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
        self.session.set_default_extensions_from_config()

        self._draw_tray_icon() # user-specific tray icon
        self.tray_icon.set_main(self.session)

        self.window.go_main(self.session, self.on_new_conversation,
                            self.tray_icon.quit_on_close)

    def _draw_tray_icon(self):
        '''draws the tray icon'''
        trayiconcls = extension.get_default('tray icon')

        if self.tray_icon is not None:
            if trayiconcls == self.tray_icon.__class__:
                return
            self.tray_icon.hide()
        else:
            extension.subscribe(self._on_tray_icon_changed, 'tray icon')

        handler = gui.base.TrayIconHandler(self.session, gui.theme, self.close_session)
        self.tray_icon = trayiconcls(handler, self.window)

    def _on_tray_icon_changed(self, new_extension):
        self._draw_tray_icon()
        self.tray_icon.set_main(self.session)

    def _sync_emesene1(self):
        syn = extension.get_default('synch tool')
        # Check if a synch tool is present. Synch tool is only in the gtk gui.
        # Remove the following 'if' when it will be in the qt4 gui too.
        if syn:
            user = self.session.account.account
            current_service = self.session.config.service
            syn = syn(self.session, current_service)
            syn.show()

    def _set_location(self, window, is_conv=False, single_window=False):
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

        if maximized:
            window.maximize()

        window.set_location(width, height, posx, posy, single_window and is_conv)

    def on_preferences_changed(self, use_http, use_ipv6, proxy, session_id, service):
        '''called when the preferences on login change'''
        self.config.session = session_id
        extension.set_default_by_id('session', session_id)
        self.config.b_use_http = use_http
        self.config.b_use_ipv6 = use_ipv6
        self.config.service = service
        self._save_proxy_settings(proxy)

    def on_login_failed(self, reason):
        '''callback called when login fails'''
        self._save_login_dimensions()
        self._remove_subscriptions()
        self._new_session()
        self.go_login(cancel_clicked=True)
        self.window.content_main.clear_all()
        self.window.content_main.show_error(reason, login_failed=True)

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
        self.session.set_default_extensions_from_config()

    def on_login_succeed(self):
        '''callback called on login succeed'''
        self._save_login_dimensions()
        self.config.save(self.config_path)

        self.draw_main_screen()
        self._setup_plugins()

        self._restore_session()

        self._sync_emesene1()

        self.check_for_updates()

        self.session.start_mail_client()
        self.logged_in = True
        self.network_checker.set_new_session(self.session)


    def on_login_connect(self, account, session_id, proxy,
                         use_http, use_ipv6,
                         host=None, port=None, on_reconnect=False):
        '''called when the user press the connect button'''
        self._save_login_dimensions()
        self._set_location(self.window)
        self.cur_service = [host, port]
        if not on_reconnect:
            self.on_preferences_changed(use_http, use_ipv6,
                    proxy, session_id, self.config.service)
            self.avatar_path = self.config_dir.join(host, account.account,
                    'avatars', 'last')
            self.window.go_connect(self.on_cancel_login, self.avatar_path,
                    self.config)
            self.window.show()
        else:
            self.window.content_main.clear_connect()

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

        self.session.config.get_or_set('b_mute_notification', False)
        self.session.config.get_or_set('b_notify_endpoint_added', True)
        self.session.config.get_or_set('b_notify_endpoint_updated', False)
        self.session.config.get_or_set('b_notify_contact_online', True)
        self.session.config.get_or_set('b_notify_contact_offline', True)
        self.session.config.get_or_set('b_notify_receive_message', True)
        self.session.config.get_or_set('b_notify_typing', False)
        self.session.config.get_or_set('b_notify_when_focussed', False)
        self.session.config.get_or_set('b_notify_only_when_available', True)

        self.session.config.get_or_set('b_show_userpanel', True)
        self.session.config.get_or_set('b_show_mail_inbox', True)
        self.session.config.get_or_set('b_show_emoticons', True)
        self.session.config.get_or_set('b_show_header', True)
        self.session.config.get_or_set('b_show_info', True)
        self.session.config.get_or_set('b_show_toolbar', True)
        self.session.config.get_or_set('b_allow_auto_scroll', True)
        self.session.config.get_or_set('adium_theme', 'renkoo.AdiumMessageStyle')
        self.session.config.get_or_set('b_enable_spell_check', False)
        self.session.config.get_or_set('b_download_folder_per_account', False)
        self.session.config.get_or_set('b_override_text_color', False)
        self.session.config.get_or_set('override_text_color', '#000000')
        self.session.config.get_or_set('b_conversation_tabs', True)
        self.session.config.get_or_set('b_single_window', True)
        self.session.config.get_or_set('b_open_mail_in_desktop', False)

        # set account uuid for session
        self.session.account_uuid = account.uuid

        self.session.login(account.account, account.password, account.status,
            proxy, host, port, use_http, use_ipv6)

    def on_cancel_login(self):
        '''
        method called when user select cancel login
        '''
        self.close_session(False)
        self.go_login(cancel_clicked=True, no_autologin=True)

    def on_contact_list_ready(self):
        '''callback called when the contact list is ready to be used'''
        notificationcls = extension.get_default('notification')
        self.notification = notificationcls(self.session)
        self.soundPlayer = extension.get_and_instantiate('sound', self.session)

    def on_new_conversation(self, cid, members, other_started=True):
        '''callback called when the other user does an action that justify
        opening a conversation'''
        conv_tabs = self.session.config.b_conversation_tabs
        sing_wind = self.session.config.b_single_window

        conv_manager = None

        # check to see if there is a conversation with the same member
        for convman in self.conversations:
            if convman.has_similar_conversation(cid, members):
                conv_manager = convman
                break

        if conv_manager is None:
            if not self.conversations or not conv_tabs:
                if sing_wind and conv_tabs:
                    window = self.window
                else:
                    windowcls = extension.get_default('window frame')
                    window = windowcls(self._on_conversation_window_close)

                window.go_conversation(self.session, self._on_conversation_window_close)
                self._set_location(window, True, sing_wind)
                conv_manager = window.content_conv
                self.conversations.append(conv_manager)
                self.session.conversation_managers.append(conv_manager)

                if not (sing_wind and conv_tabs):
                    if self.session.config.b_conv_minimized and other_started:
                        window.iconify()
                        window.show()
                        window.iconify()
                    else:
                        window.show()
            else:
                conv_manager = self.conversations[0]

        conversation = conv_manager.new_conversation(cid, members)

        # raises the container and grabs the focus
        # handles cases where window is minimized and ctrl+tab focus stealing
        if not other_started:
            conv_manager.present(conversation, sing_wind and conv_tabs)

        if self.session.config.b_play_first_send and not \
           self.session.config.b_play_type:
            self.soundPlayer.play(gui.theme.sound_theme.sound_type)

    def _on_conversation_window_close(self, conv_manager):
        '''method called when the conversation window is closed'''
        if self.session:
            width, height, posx, posy = conv_manager.get_dimensions()

            if not conv_manager.is_maximized():
                self.session.config.i_conv_width = width
                self.session.config.i_conv_height = height
                self.session.config.i_conv_posx = posx
                self.session.config.i_conv_posy = posy
                self.session.config.b_conv_maximized = False
            else:
                self.session.config.b_conv_maximized = True
                self.session.config.i_conv_width = width #needed for single window
            self.session.conversation_managers.remove(conv_manager)

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
                self.window.content_main.clear_all()
                self.window.content_main.show_error(reason)

    def on_reconnect(self, account):
        '''makes the reconnect after 30 seconds'''
        self.window.go_connect(self.on_cancel_login, self.avatar_path,
                self.config)

        proxy = self._get_proxy_settings()
        use_http = self.config.get_or_set('b_use_http', False)
        use_ipv6 = self.config.get_or_set('b_use_ipv6', False)
        self.window.content_main.on_reconnect(self.on_login_connect, account, \
                                         self.config.session, proxy, use_http, \
                                         use_ipv6, self.cur_service)

        self.tray_icon.set_login()

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

    def check_for_updates(self):
        '''Search for any updates'''
        if not self.session.config.get_or_set('b_check_for_updates', True):
            return

        updates_time = datetime.date.fromtimestamp(
                        self.config.get_or_set('f_check_updates_time', 0))
        now = datetime.date.today()
        delta = datetime.timedelta(weeks=1)
        if now - updates_time < delta:
            return

        self.config.f_check_updates_time = time.time()
        preferences = extension.get_and_instantiate('preferences',
                                                    self.session)
        if self.session is not preferences.session:
            extension.delete_instance('preferences')
            preferences = extension.get_and_instantiate('preferences',
                                                        self.session)

        preferences.check_for_updates()

def main():
    """
    the main method of emesene
    """
    extension.category_register('session', dummy.Session, single_instance=True)
    extension.category_register('option provider', None,
            interfaces=interfaces.IOptionProvider)
    extension.register('quit', sys.exit)
    extension.get_category('option provider').multi_extension = True
    extension.get_category('option provider').activate(optionprovider.ExtensionDefault)
    options = optionprovider.PluggableOptionParser(args=emesene_args)
    options.read_options()
    main_method = extension.get_default('main')
    main_method(Controller)

if __name__ == "__main__":
    main()
