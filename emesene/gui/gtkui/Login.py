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

import gtk
import base64
import gobject
import sys
from shutil import rmtree

import e3
import gui
import utils
import extension
import StatusButton
import stock

import logging
log = logging.getLogger('gtkui.Login')

class LoginBase(gtk.Alignment):
    ''' base widget that holds the visual stuff '''
    def __init__(self, callback, args=None):
        gtk.Alignment.__init__(self, xalign=0.5, yalign=0.5, xscale=0.0,
            yscale=1.0)

        self.dialog = extension.get_default('dialog')
        Avatar = extension.get_default('avatar')
        NiceBar = extension.get_default('nice bar')

        self.liststore = gtk.ListStore(gobject.TYPE_STRING, gtk.gdk.Pixbuf)
        completion = gtk.EntryCompletion()
        completion.set_model(self.liststore)
        pixbufcell = gtk.CellRendererPixbuf()
        completion.pack_start(pixbufcell)
        completion.add_attribute(pixbufcell, 'pixbuf', 1)
        completion.set_text_column(0)
        completion.set_inline_selection(True)

        self.pixbuf = utils.safe_gtk_pixbuf_load(gui.theme.user)

        self.cmb_account = gtk.ComboBoxEntry(self.liststore, 0)
        self.cmb_account.get_children()[0].set_completion(completion)
        self.cmb_account.get_children()[0].connect('key-press-event',
            self._on_account_key_press)
        self.cmb_account.connect('changed',
            self._on_account_changed)
        self.cmb_account.connect('key-release-event',
            self._on_account_key_release)

        self.btn_status = StatusButton.StatusButton()
        self.btn_status.set_status(e3.status.ONLINE)

        self.txt_password = gtk.Entry()
        self.txt_password.set_visibility(False)
        self.txt_password.connect('key-press-event',
            self._on_password_key_press)
        self.txt_password.connect('changed', self._on_password_changed)
        self.txt_password.set_sensitive(False)

        pix_account = utils.safe_gtk_pixbuf_load(gui.theme.user)
        pix_password = utils.safe_gtk_pixbuf_load(gui.theme.password)

        self.avatar = Avatar()

        self.remember_account = gtk.CheckButton(_('Remember me'))
        self.remember_password = gtk.CheckButton(_('Remember password'))
        self.auto_login = gtk.CheckButton(_('Auto-login'))

        self.remember_account.connect('toggled',
            self._on_remember_account_toggled)
        self.remember_password.connect('toggled',
            self._on_remember_password_toggled)
        self.auto_login.connect('toggled',
            self._on_auto_login_toggled)

        self.remember_account.set_sensitive(False)
        self.remember_password.set_sensitive(False)
        self.auto_login.set_sensitive(False)

        self.forget_me = gtk.Button()
        self.forget_me.set_tooltip_text(_('Delete user'))
        forget_img = gtk.image_new_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_MENU)
        self.forget_me.set_image(forget_img)
        self.forget_me.set_relief(gtk.RELIEF_NONE)
        self.forget_me.set_border_width(0)
        self.forget_me.connect('clicked', self._on_forget_me_clicked)
        self.forget_me.set_sensitive(False)

        hboxremember = gtk.HBox(spacing=2)
        hboxremember.pack_start(self.remember_account, False, False)

        vbox_remember = gtk.VBox(spacing=4)
        vbox_remember.set_border_width(8)
        vbox_remember.pack_start(hboxremember)
        vbox_remember.pack_start(self.remember_password)
        vbox_remember.pack_start(self.auto_login)
        vbox_remember.pack_start(gtk.Label())
        
        session_combo_store = gtk.ListStore(gtk.gdk.Pixbuf, str)
        crp = gtk.CellRendererPixbuf()
        crt = gtk.CellRendererText()
        crp.set_property("xalign", 0)
        crt.set_property("xalign", 0)

        self.session_combo = gtk.ComboBox()
        self.session_combo.set_model(session_combo_store)
        self.session_combo.pack_start(crp, True)
        self.session_combo.pack_start(crt, True)
        self.session_combo.add_attribute(crp, "pixbuf", 0)
        self.session_combo.add_attribute(crt, "text", 1)

        vbox_remember.pack_start(self.session_combo)

        self.b_connect = gtk.Button(stock=gtk.STOCK_CONNECT)
        self.b_connect.connect('clicked', self._on_connect_clicked)
        self.b_connect.set_sensitive(False)

        self.b_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        self.b_cancel.connect('clicked', self._on_cancel_clicked)

        vbuttonbox = gtk.VButtonBox()
        vbuttonbox.set_spacing(8)
        vbuttonbox.pack_start(self.b_connect)
        vbuttonbox.pack_start(self.b_cancel)

        vbox = gtk.VBox()

        hbox_account = gtk.HBox(spacing=6)
        img_accountpix = gtk.Image()
        img_accountpix.set_from_pixbuf(utils.scale_nicely(pix_account))
        hbox_account.pack_start(img_accountpix, False)
        hbox_account.pack_start(self.cmb_account, True, True)
        hbox_account.pack_start(self.forget_me, False)

        hbox_password = gtk.HBox(spacing=6)
        img_password = gtk.Image()
        img_password.set_from_pixbuf(utils.scale_nicely(pix_password))
        hbox_password.pack_start(img_password, False)
        hbox_password.pack_start(self.txt_password, True, True)
        hbox_password.pack_start(self.btn_status, False)

        vbox_entries = gtk.VBox(spacing=12)
        vbox_entries.set_border_width(8)
        vbox_entries.pack_start(hbox_account)
        vbox_entries.pack_start(hbox_password)

        self.b_preferences = gtk.Button()
        self.img_preferences = gtk.image_new_from_stock(gtk.STOCK_PREFERENCES,
            gtk.ICON_SIZE_MENU)
        self.img_preferences.set_sensitive(False)
        self.b_preferences.set_image(self.img_preferences)
        self.b_preferences.set_relief(gtk.RELIEF_NONE)
        self.b_preferences.connect('enter-notify-event',
            self._on_preferences_enter)
        self.b_preferences.connect('leave-notify-event',
            self._on_preferences_leave)
        self.b_preferences.connect('clicked',
            self._on_preferences_selected)

        self.nicebar = NiceBar()

        th_pix = utils.safe_gtk_pixbuf_load(gui.theme.throbber, None,
                animated=True)
        self.throbber = gtk.image_new_from_animation(th_pix)
        self.label_timer = gtk.Label()
        self.label_timer.set_markup(_('<b>Connection error!\n </b>'))

        al_label_timer = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.0,
            yscale=0.0)
        al_throbber = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.2,
            yscale=0.2)
        al_vbox_entries = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.2,
            yscale=0.0)
        al_vbox_remember = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.0,
            yscale=0.2)
        al_button = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.2)
        al_account = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.0,
            yscale=0.0)
        al_preferences = gtk.Alignment(xalign=1.0, yalign=0.5)

        al_label_timer.add(self.label_timer)
        al_throbber.add(self.throbber)
        al_vbox_entries.add(vbox_entries)
        al_vbox_remember.add(vbox_remember)
        al_button.add(vbuttonbox)
        al_account.add(self.avatar)
        al_preferences.add(self.b_preferences)

        vbox_bottom = gtk.VBox(True)
        vbox.pack_start(self.nicebar, False)
        vbox.pack_start(al_account, True, False)
        vbox.pack_start(al_vbox_entries, True, True)
        vbox.pack_start(al_vbox_remember, True, False)
        vbox_bottom.pack_start(al_label_timer, True, False)
        vbox_bottom.pack_start(al_throbber, False, False)
        vbox_bottom.pack_start(al_button, True, True)
        vbox.pack_start(vbox_bottom, True, True)
        vbox.pack_start(al_preferences, True, False)

        self.add(vbox)
        vbox.show_all()

    def _on_cancel_clicked(self, button):
        '''
        overload this
        '''
        return

class Login(LoginBase):
    '''
    widget that represents the login window
    '''
    def __init__(self, callback, on_preferences_changed,
                config, config_dir, config_path, proxy=None,
                use_http=None, session_id=None, cancel_clicked=False,
                no_autologin=False):

        LoginBase.__init__(self, callback)

        self.config = config
        self.config_dir = config_dir
        self.config_path = config_path
        self.callback = callback
        self.cancel_clicked=cancel_clicked
        self.on_preferences_changed = on_preferences_changed
        self.no_autologin = no_autologin
        # the id of the default extension that handles the session
        # used to select the default session on the preference dialog
        self.use_http = use_http
        self.session_id = session_id

        account = self.config.get_or_set('last_logged_account', '')
        self.config.get_or_set('service', 'msn')
        self.remembers = self.config.get_or_set('d_remembers', {})
        self.config.get_or_set('d_user_service', {})
        self.status = self.config.get_or_set('d_status',{})
        self.accounts = self.config.d_accounts

        self._reload_account_list()
        self.__combo_session_list=[]

        if proxy is None:
            self.proxy = e3.Proxy()
        else:
            self.proxy = proxy

        self.services = {}

        if session_id is not None:
            for ext_id, ext in extension.get_extensions('session').iteritems():
                for service_name, service_data in ext.SERVICES.iteritems():
                    self.services[service_name] = service_data

                if session_id == ext_id and self.config.service in ext.SERVICES:
                    self.server_host = ext.SERVICES[self.config.service]['host']
                    self.server_port = ext.SERVICES[self.config.service]['port']
                    break
            else:
                self.config.service = 'msn'
                self.server_host = 'messenger.hotmail.com'
                self.server_port = '1863'
        else:
            self.config.service = 'msn'
            self.server_host = 'messenger.hotmail.com'
            self.server_port = '1863'

        avatar_path = self.config_dir.join(self.server_host, account, 'avatars', 'last')
        self.avatar.set_from_file(avatar_path)

        self.nicebar.hide()
        self.throbber.hide()
        self.label_timer.hide()
        self.b_cancel.hide()

        if account != '':
            self.cmb_account.get_children()[0].set_text(account)

        if not self.cancel_clicked:
            self._check_autologin()

        self._show_sessions()

    def __on_session_changed(self, session_combo, name_to_ext):

        active = session_combo.get_active()
        model = session_combo.get_model()
        service = model[active][1]
        session_id, ext = name_to_ext[service]
        self._on_new_preferences(self.use_http, self.proxy.use_proxy, self.proxy.host, self.proxy.port,self.proxy.use_auth, self.proxy.user, self.proxy.passwd, session_id, service, ext.SERVICES[service]['host'], ext.SERVICES[service]['port'])

    def _show_sessions(self):

        self.new_combo_session(self.session_combo, self.__on_session_changed)

    def new_combo_session(self, session_combo, on_session_changed):
        account = self.config.get_or_set('last_logged_account', '')
        default_session = extension.get_default('session')
        count=0
        session_found = False

        name_to_ext = {}

        if account in self.accounts:
            service = self.config.d_user_service.get(account, 'msn')
        else:
            service = 'msn'

        for ext_id, ext in extension.get_extensions('session').iteritems():
            if default_session.NAME == ext.NAME:
                default_session_index = count

            for service_name, service_data in ext.SERVICES.iteritems():
                if service == service_name:
                    index = count
                    session_found = True

                try:
                    # ugly eval here, is there another way?
                    s_name = getattr(gui.theme, "service_" + service_name) 
                    image = utils.safe_gtk_pixbuf_load(s_name)
                except:
                    image = None

                session_combo.get_model().append([image, service_name])
                name_to_ext[service_name] = (ext_id, ext)
                count += 1

        if session_found:
            session_combo.set_active(index)
        else:
            session_combo.set_active(default_session_index)

        session_combo.connect('changed', on_session_changed, name_to_ext)

        self.__combo_session_list.append(session_combo)

        return name_to_ext
        
    def _check_autologin(self):
        '''check if autologin is set and can be started'''
        account = self.config.get_or_set('last_logged_account', '')

        if account != '' and int(self.config.d_remembers.get(account, 0)) == 3:
            password = base64.b64decode(self.config.d_accounts[account])

            self.cmb_account.get_children()[0].set_text(account)
            self.txt_password.set_text(password)

            if not self.no_autologin:
                self.do_connect()

    def do_connect(self):
        '''
        do all the stuffs needed to connect
        '''
        self.nicebar.empty_queue()
        user = self.cmb_account.get_active_text().strip()
        password = self.txt_password.get_text()
        account = e3.Account(user, password, self.btn_status.status,
                self.server_host)
        remember_password = self.remember_password.get_active()
        remember_account = self.remember_account.get_active()
        auto_login = self.auto_login.get_active()

        if user == '' or password == '':
            self.show_error(_('user or password fields are empty'))
            return

        self._config_account(account, remember_account, remember_password,
                             auto_login)

        self.callback(account, self.session_id, self.proxy, self.use_http,
                self.server_host, self.server_port)

    def _config_account(self, account, remember_account, remember_password,
                         auto_login):
        '''
        modify the config for the current account before login
        '''

        if auto_login or remember_account or remember_password:
            self.status[account.account] = account.status
            self.config.last_logged_account = account.account

        if auto_login:#+1 account,+1 password,+1 autologin =  3
            self.accounts[account.account] = base64.b64encode(account.password)
            self.remembers[account.account] = 3

        elif remember_password:#+1 account,+1 password = 2
            self.accounts[account.account] = base64.b64encode(account.password)
            self.remembers[account.account] = 2

        elif remember_account:#+1 account = 1
            self.accounts[account.account] = ''
            self.remembers[account.account] = 1

        else:#means i have logged with nothing checked
            self.config.last_logged_account = ''

        self.config.save(self.config_path)

    def _on_account_changed(self, entry):
        '''
        called when the content of the account entry changes
        '''
        self._update_fields(self.cmb_account.get_active_text())

    def _on_account_key_release(self, entry, event):
        '''
        called when a key is released in the account field
        '''
        self._update_fields(self.cmb_account.get_active_text())
        if event.keyval == gtk.keysyms.Tab:
            self.txt_password.grab_focus()

    def _update_fields(self, account):
        '''
        update the different fields according to the account that is
        on the account entry
        '''
        self._clear_all()

        if self.txt_password.get_text() == '':
            self.remember_password.set_sensitive(False)
            self.auto_login.set_sensitive(False)

        if account == '':
            self.remember_account.set_sensitive(False)
            self.txt_password.set_text('')
            self.txt_password.set_sensitive(False)
            return

        self.remember_account.set_sensitive(True)

        if account in self.config.d_user_service:
            service = self.config.d_user_service[account]

            if service in self.services:
                service_data = self.services[service]
                self.server_host = service_data['host']
                self.server_port = service_data['port']
                self.config.service = service

        if account in self.accounts:
            attr = int(self.remembers[account])
            self.remember_account.set_sensitive(False)
            self.forget_me.set_sensitive(True)
            self.btn_status.set_status(int(self.status[account]))

            passw = self.accounts[account]
            avatar_path = self.config_dir.join(self.server_host, account, 'avatars', 'last')
            self.avatar.set_from_file(avatar_path)

            if attr == 3:#autologin,password,account checked
                self.txt_password.set_text(base64.b64decode(passw))
                self.txt_password.set_sensitive(False)
                self.auto_login.set_active(True)
            elif attr == 2:#password,account checked
                self.txt_password.set_text(base64.b64decode(passw))
                self.txt_password.set_sensitive(False)
                self.remember_password.set_active(True)
            elif attr == 1:#only account checked
                self.remember_account.set_active(True)
                self.remember_account.set_sensitive(True)
                self.remember_password.set_sensitive(False)
                self.auto_login.set_sensitive(False)
            else:#if i'm here i have an error
                self.show_error(_(
                          'Error while reading user config'))
                self._clear_all()

        else:
           self.avatar.set_from_file(gui.theme.logo)

    def _clear_all(self):
        '''
        clear all login fields and checkbox
        '''
        self.remember_account.set_active(False)
        self.remember_account.set_sensitive(True)
        self.remember_password.set_active(False)
        self.remember_password.set_sensitive(True)
        self.auto_login.set_active(False)
        self.forget_me.set_sensitive(False)
        self.btn_status.set_status(e3.status.ONLINE)
        self.txt_password.set_sensitive(True)

    def clear_all(self):
        '''
        call clear_all and clean also the account combobox
        '''
        self._clear_all()
        self.cmb_account.get_children()[0].set_text('')

    def show_error(self, reason):
        '''
        show an error on the top of the window using nicebar
        '''
        self.nicebar.new_message(reason, gtk.STOCK_DIALOG_ERROR)

    def _reload_account_list(self, *args):
        '''
        reload the account list in the combobox
        '''
        self.liststore.clear()
        for mail in sorted(self.accounts):
            self.liststore.append([mail, utils.scale_nicely(self.pixbuf)])

        #this resolves a small bug
        if not len(self.liststore):
            self.liststore = None

    def _on_password_key_press(self, widget, event):
        '''
        called when a key is pressed on the password field
        '''
        self.nicebar.empty_queue()
        if event.keyval == gtk.keysyms.Return or \
           event.keyval == gtk.keysyms.KP_Enter:
            self.do_connect()

    def _on_password_changed(self, widget):
        '''
        called when the password in the combobox changes
        '''
        state = (self.txt_password.get_text() != "")

        self.remember_password.set_sensitive(state)
        self.auto_login.set_sensitive(state)
        self.b_connect.set_sensitive(state)

    def _on_account_key_press(self, widget, event):
        '''
        called when a key is pressed on the password field
        '''
        self.nicebar.empty_queue()
        if event.keyval == gtk.keysyms.Return or \
           event.keyval == gtk.keysyms.KP_Enter:
            self.txt_password.grab_focus()
            if not self.txt_password.is_focus():
                self.do_connect()

    def _on_forget_me_clicked(self, *args):
        '''
        called when the forget me label is clicked
        '''
        def _yes_no_cb(response):
            '''callback from the confirmation dialog'''
            account = self.cmb_account.get_active_text()
            if response == stock.YES:
                try: # Delete user's folder
                    rmtree(self.config_dir.join(self.server_host, account))
                except:
                    self.show_error(_('Error while deleting user'))

                if account in self.accounts:
                    del self.accounts[account]
                if account in self.remembers:
                    del self.remembers[account]
                if account in self.status:
                    del self.status[account]
                if account == self.config.last_logged_account:
                    self.config.last_logged_account = ''

                self.config.save(self.config_path)
                self._reload_account_list()
                self.cmb_account.get_children()[0].set_text('')

        self.dialog.yes_no(
               _('Are you sure you want to delete the account %s ?') % \
                      self.cmb_account.get_active_text(), _yes_no_cb)

    def _on_connect_clicked(self, button):
        '''
        called when connect button is clicked
        '''
        self.avatar.stop()
        self.do_connect()

    def _on_quit(self):
        '''
        close emesene
        '''
        while gtk.events_pending():
                gtk.main_iteration(False)

        sys.exit(0)

    def _on_remember_account_toggled(self, button):
        '''
        called when the remember account check button is toggled
        '''
        if not self.remember_account.get_active():
            self.remember_password.set_active(False)

    def _on_remember_password_toggled(self, button):
        '''
        called when the remember password check button is toggled
        '''
        if self.remember_password.get_active():
            self.remember_account.set_active(True)
            self.remember_account.set_sensitive(False)
            self.txt_password.set_sensitive(False)
        else:
            self.remember_account.set_sensitive(True)
            self.txt_password.set_sensitive(True)
            self.txt_password.set_text('')

    def _on_auto_login_toggled(self, button):
        '''
        called when the auto-login check button is toggled
        '''
        if self.auto_login.get_active():
            self.remember_password.set_active(True)
            self.remember_account.set_sensitive(False)
            self.remember_password.set_sensitive(False)
        else:
            self.remember_password.set_sensitive(True)

    def _on_preferences_enter(self, button, event):
        '''
        called when the mouse enters the preferences button
        '''
        self.img_preferences.set_sensitive(True)

    def _on_preferences_leave(self, button, event):
        '''
        called when the mouse leaves the preferences button
        '''
        self.img_preferences.set_sensitive(False)

    def _on_preferences_selected(self, button):
        '''
        called when the user clicks the preference button
        '''
        service = self.config.get_or_set('service', 'msn')

        account = self.cmb_account.get_active_text()

        if account in self.accounts:
            service = self.config.d_user_service.get(account, 'msn')

        extension.get_default('dialog').login_preferences(service,
            self._on_new_preferences, self.use_http, self.proxy,self)

    def _on_new_preferences(self, use_http, use_proxy, proxy_host, proxy_port,
        use_auth, user, passwd, session_id, service, server_host, server_port):
        '''
        called when the user press accept on the preferences dialog
        '''
        self.proxy = e3.Proxy(use_proxy, proxy_host, proxy_port, use_auth, user, passwd)
        self.session_id = session_id
        self.use_http = use_http
        self.server_host = server_host
        self.server_port = server_port

        account = self.cmb_account.get_active_text()

        if account in self.accounts:
            self.config.d_user_service[account] = service

        self.on_preferences_changed(self.use_http, self.proxy, self.session_id,
                service)
        self._on_account_changed(None)

        def searchService(model, path, iter, user_data):
                if(model.get(iter,0)[0]==user_data[0]):
                        user_data[2].set_active(user_data[1])
                        return True
                user_data[1]+=1
                return False

        i=0
	
	for combo in self.__combo_session_list:
        	combo.get_model().foreach(searchService,[service,i,combo])

class ConnectingWindow(Login):
    '''
    widget that represents the GUI interface showed when connecting
    '''
    def __init__(self, callback, avatar_path, config):
        LoginBase.__init__(self, callback)

        self.callback = callback
        self.avatar.set_from_file(avatar_path)

        #for reconnecting
        self.reconnect_timer_id = None

        account = config.get_or_set('last_logged_account', '')
        remembers = config.get_or_set('d_remembers', {})

        if not (account == ''):
            attr = int(remembers[account])
            if attr == 3:#autologin,password,account checked
                self.auto_login.set_active(True)
            elif attr == 2:#password,account checked
                self.remember_password.set_active(True)
            elif attr == 1:#only account checked
                self.remember_account.set_active(True)

            password = base64.b64decode(config.d_accounts.get(account, ""))
            self.cmb_account.get_children()[0].set_text(account)
            self.txt_password.set_text(password)

        #FIXME: If not account remembered, txt_password & cmb_account, left without text.
        self.cmb_account.set_sensitive(False)
        self.b_preferences.set_sensitive(False)
        self.btn_status.set_sensitive(False)
        self.txt_password.set_sensitive(False)
        self.nicebar.hide()
        self.throbber.show()
        self.label_timer.hide()

        self.b_connect.set_label(_("Connect now"))
        self.b_connect.set_sensitive(True)
        self.b_connect.hide()

    def _update_fields(self, *args):
        ''' override the login method with "do nothing" '''
        return

    def _on_password_changed(self, widget):
        ''' overload the login one '''
        state = 0

        self.remember_account.set_sensitive(state)
        self.remember_password.set_sensitive(state)
        self.auto_login.set_sensitive(state)

    def _on_cancel_clicked(self, button):
        '''
        cause the return to login window
        '''
        self.cancel_clicked=True
        self.avatar.stop()
        if self.reconnect_timer_id is not None:
            gobject.source_remove(self.reconnect_timer_id)
        self.reconnect_timer_id = None
        self.callback()

    def _on_connect_now_clicked(self, button, callback, account, session_id,
                            proxy, use_http, service):
        '''
        don't wait for timout to reconnect
        '''
        button.hide()
        self.avatar.stop()
        gobject.source_remove(self.reconnect_timer_id)
        self.reconnect_timer_id = None
        callback(account, session_id, proxy, use_http,\
                 service[0], service[1], on_reconnect=True)

    def clear_connect(self):
        '''
        clean the connect interface after the reconnect phase
        '''
        self.label_timer.hide()
        self.throbber.show()

    def on_reconnect(self, callback, account, session_id,
                     proxy, use_http, service):
        '''
        show the reconnect countdown
        '''
        self.label_timer.show()
        self.b_connect.show()
        self.b_connect.connect('clicked', self._on_connect_now_clicked, callback, \
                               account, session_id, proxy, use_http, service)
        self.throbber.hide()
        self.reconnect_after = 30
        if self.reconnect_timer_id is None:
            self.reconnect_timer_id = gobject.timeout_add_seconds(1, \
                self.update_reconnect_timer, callback, account, session_id,
                                    proxy, use_http, service)

        self.update_reconnect_timer(callback, account, session_id,
                                    proxy, use_http, service)

    def update_reconnect_timer(self, callback, account, session_id,
                               proxy, use_http, service):
        '''
        updates reconnect label and launches login if counter is 0
        '''
        self.reconnect_after -= 1
        self.label_timer.set_text(_('Reconnecting in %d seconds')\
                                             % self.reconnect_after )
        if self.reconnect_after <= 0:
            gobject.source_remove(self.reconnect_timer_id)
            self.reconnect_timer_id = None
            self.b_connect.hide()
            #do login
            callback(account, session_id, proxy, use_http,\
                     service[0], service[1], on_reconnect=True)
            return False
        else:
            return True

