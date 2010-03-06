# -*- coding: utf-8 -*-
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
import NiceBar

import logging
log = logging.getLogger('gtkui.Login')

class Login(gtk.Alignment):
    '''
    widget that represents the login window
    '''
    def __init__(self, callback, on_preferences_changed,
                config, config_dir, config_path, proxy=None,
                use_http=None, session_id=None):

        gtk.Alignment.__init__(self, xalign=0.5, yalign=0.5, xscale=1.0,
            yscale=1.0)

        self.config = config
        self.config_dir = config_dir
        self.config_path = config_path
        self.callback = callback
        self.on_preferences_changed = on_preferences_changed
        # the id of the default extension that handles the session
        # used to select the default session on the preference dialog
        self.use_http = use_http
        self.session_id = session_id

        account = self.config.get_or_set('last_logged_account', '')
        self.remembers = self.config.get_or_set('d_remembers', {})
        self.status = self.config.get_or_set('d_status',{})
        self.accounts = self.config.d_accounts

        if proxy is None:
            self.proxy = e3.Proxy()
        else:
            self.proxy = proxy

        self.dialog = extension.get_default('dialog')

        if session_id is not None:
            for ext_id, ext in extension.get_extensions('session').iteritems():
                if session_id == ext_id:
                    self.server_host = ext.DEFAULT_HOST
                    self.server_port = ext.DEFAULT_PORT
        else:
            self.server_host = extension.get_default('session').DEFAULT_HOST
            self.server_port = extension.get_default('session').DEFAULT_PORT

        self.liststore = gtk.ListStore(gobject.TYPE_STRING, gtk.gdk.Pixbuf)
        completion = gtk.EntryCompletion()
        completion.set_model(self.liststore)
        pixbufcell = gtk.CellRendererPixbuf()
        completion.pack_start(pixbufcell)
        completion.add_attribute(pixbufcell, 'pixbuf', 1)
        completion.set_text_column(0)
        completion.set_inline_selection(True)

        self.pixbuf = utils.safe_gtk_pixbuf_load(gui.theme.user)

        self._reload_account_list()

        self.cmb_account = gtk.ComboBoxEntry(self.liststore, 0)
        self.cmb_account.get_children()[0].set_completion(completion)
        self.cmb_account.get_children()[0].connect('key-press-event',
            self._on_account_key_press)
        self.cmb_account.connect('changed',
            self._on_account_changed)

        self.btn_status = StatusButton.StatusButton()
        self.btn_status.set_status(e3.status.ONLINE)

        status_padding = gtk.Label()
        status_padding.set_size_request(*self.btn_status.size_request())

        self.txt_password = gtk.Entry()
        self.txt_password.set_visibility(False)
        self.txt_password.connect('key-press-event',
            self._on_password_key_press)

        pix_account = utils.safe_gtk_pixbuf_load(gui.theme.user)
        pix_password = utils.safe_gtk_pixbuf_load(gui.theme.password)

        self.img_account = gtk.Image()
        path = self.config_dir.join(account.replace('@','-at-'), \
                                                 'avatars', 'last')
        if self.config_dir.file_readable(path):
            pix = utils.safe_gtk_pixbuf_load(path, (96,96))
        else:
            pix = utils.safe_gtk_pixbuf_load(gui.theme.logo)
        self.img_account.set_from_pixbuf(pix)

        self.remember_account = gtk.CheckButton(_('Remember me'))
        self.remember_password = gtk.CheckButton(_('Remember password'))
        self.auto_login = gtk.CheckButton(_('Auto-login'))

        self.remember_account.connect('toggled',
            self._on_remember_account_toggled)
        self.remember_password.connect('toggled',
            self._on_remember_password_toggled)
        self.auto_login.connect('toggled',
            self._on_auto_login_toggled)

        self.forget_me = gtk.EventBox()
        self.forget_me.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.forget_me_label = gtk.Label('<span foreground="#0000AA">(' + \
                                            _('Forget me') + ')</span>')
        self.forget_me_label.set_use_markup(True)
        self.forget_me.add(self.forget_me_label)
        self.forget_me.connect('button_press_event', self._on_forget_me_clicked)
        self.forget_me.set_child_visible(False)

        hboxremember = gtk.HBox(spacing=2)
        hboxremember.pack_start(self.remember_account, False, False)
        hboxremember.pack_start(self.forget_me, False, False)

        vbox_remember = gtk.VBox(spacing=4)
        vbox_remember.set_border_width(8)
        vbox_remember.pack_start(hboxremember)
        vbox_remember.pack_start(self.remember_password)
        vbox_remember.pack_start(self.auto_login)

        self.b_connect = gtk.Button(stock=gtk.STOCK_CONNECT)
        self.b_connect.connect('clicked', self._on_connect_clicked)
        self.b_connect.set_border_width(8)

        vbox = gtk.VBox()

        hbox_account = gtk.HBox(spacing=6)
        img_accountpix = gtk.Image()
        img_accountpix.set_from_pixbuf(utils.scale_nicely(pix_account))
        hbox_account.pack_start(img_accountpix, False)
        hbox_account.pack_start(self.cmb_account, True, True)
        hbox_account.pack_start(status_padding, False)

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

        self.nicebar = NiceBar.NiceBar(default_background= \
                                       NiceBar.ALERTBACKGROUND)

        al_logo = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.0,
            yscale=0.0)
        al_vbox_entries = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.2,
            yscale=0.0)
        al_vbox_remember = gtk.Alignment(xalign=0.55, yalign=0.5, xscale=0.05,
            yscale=0.2)
        al_button = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.15)
        al_account = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.0,
            yscale=0.0)
        al_preferences = gtk.Alignment(xalign=1.0, yalign=0.5)

        al_vbox_entries.add(vbox_entries)
        al_vbox_remember.add(vbox_remember)
        al_button.add(self.b_connect)
        al_account.add(self.img_account)
        al_preferences.add(self.b_preferences)

        vbox.pack_start(self.nicebar, False)
        vbox.pack_start(al_account, True, False)
        vbox.pack_start(al_vbox_entries, True, True)
        vbox.pack_start(al_vbox_remember, True, False)
        vbox.pack_start(al_button, True, True)
        vbox.pack_start(al_preferences, False)

        self.add(vbox)
        vbox.show_all()

        self.nicebar.hide()

        if account != '':
            self.cmb_account.get_children()[0].set_text(account)

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
        if auto_login:#+1 account,+1 password,+1 autologin =  3
            self.accounts[account.account] = base64.b64encode(account.password)
            self.remembers[account.account] = 3
            self.status[account.account] = account.status
            self.config.last_logged_account = account.account

        elif remember_password:#+1 account,+1 password = 2
            self.accounts[account.account] = base64.b64encode(account.password)
            self.remembers[account.account] = 2
            self.status[account.account] = account.status
            self.config.last_logged_account = account.account

        elif remember_account:#+1 account = 1
            self.accounts[account.account] = ''
            self.remembers[account.account] = 1
            self.status[account.account] = account.status
            self.config.last_logged_account = account.account

        else:#means i have logged with nothing checked
            self.config.last_logged_account = ''

        self.config.save(self.config_path)

    def _on_account_changed(self, entry):
        '''
        called when the content of the account entry changes
        '''
        self._update_fields(self.cmb_account.get_active_text())

    def _update_fields(self, account):
        '''
        update the different fields according to the account that is
        on the account entry
        '''
        self._clear_all()
        if account == '':
            return

        flag = False

        if account in self.accounts:
            attr = int(self.remembers[account])
            self.remember_account.set_sensitive(False)
            self.forget_me.set_child_visible(True)
            self.btn_status.set_status(int(self.status[account]))

            path = self.config_dir.join(account.replace('@','-at-'), 'avatars', 'last')
            if self.config_dir.file_readable(path):
                pix = utils.safe_gtk_pixbuf_load(path, (96,96))
                self.img_account.set_from_pixbuf(pix) 

            if attr == 3:#autologin,password,account checked
                self.auto_login.set_active(True)
                flag = True
            elif attr == 2:#password,account checked
                self.remember_password.set_active(True)
                flag = True
            elif attr == 1:#only account checked
                self.remember_account.set_active(True)
            else:#if i'm here i have an error
                self.show_error(_(
                          'Error while reading user config'))
                self._clear_all()

            #for not repeating code
            if flag:
                passw = self.accounts[account]
                self.txt_password.set_text(base64.b64decode(passw))
                self.txt_password.set_sensitive(False)

    def _clear_all(self):
        '''
        clear all login fields and checkbox
        '''
        self.remember_account.set_active(False)
        self.remember_account.set_sensitive(True)
        self.remember_password.set_active(False)
        self.remember_password.set_sensitive(True)
        self.auto_login.set_active(False)
        self.forget_me.set_child_visible(False)
        self.btn_status.set_status(e3.status.ONLINE)
        self.txt_password.set_text('')
        self.txt_password.set_sensitive(True)
        self.img_account.set_from_pixbuf(
             utils.safe_gtk_pixbuf_load(gui.theme.logo))

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
                    rmtree(self.config_dir.join(account))
                    dir_at = self.config_dir.join(account.replace('@','-at-'))
                    if self.config_dir.dir_exists(dir_at):
                        rmtree(dir_at)
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
                self. _reload_account_list()
                self.cmb_account.get_children()[0].set_text('')

        self.dialog.yes_no(
               _('Are you sure you want to delete the account %s ?') % \
                      self.cmb_account.get_active_text(), _yes_no_cb)

    def _on_connect_clicked(self, button):
        '''
        called when connect button is clicked
        '''
        self.do_connect()

    def _on_cancel_clicked(self, button):
        '''
        called when cancel button is clicked
        '''
        # call the controller on_cancel_login
        self.callback_disconnect()
        self._update_fields(self.cmb_account.get_active_text())

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
        else:
            self.remember_account.set_sensitive(True)

    def _on_auto_login_toggled(self, button):
        '''
        called when the auto-login check button is toggled
        '''
        user = self.cmb_account.get_active_text()

        if self.auto_login.get_active():
            self.remember_password.set_active(True)
            self.remember_account.set_sensitive(False)
            self.remember_password.set_sensitive(False)
        else:
            if user not in self.accounts:
                self.remember_account.set_active(False)
                self.remember_account.set_sensitive(True)
                self.remember_password.set_sensitive(True)
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
        extension.get_default('dialog').login_preferences(self.session_id,
            self._on_new_preferences, self.use_http, self.proxy)

    def _on_new_preferences(self, use_http, use_proxy, proxy_host, proxy_port,
        use_auth, user, passwd, session_id, server_host, server_port):
        '''
        called when the user press accept on the preferences dialog
        '''
        self.proxy = e3.Proxy(use_proxy, proxy_host, proxy_port, use_auth, user, passwd)
        self.session_id = session_id
        self.use_http = use_http
        self.server_host = server_host
        self.server_port = server_port
        self.on_preferences_changed(self.use_http, self.proxy, self.session_id)

class ConnectingWindow(gtk.Alignment):
    '''
    widget that represents the GUI interface showed when connecting
    '''
    def __init__(self, callback, avatar_path):

        gtk.Alignment.__init__(self, xalign=0.5, yalign=0.5, xscale=1.0,
            yscale=1.0)
        self.callback = callback
        #for reconnecting
        self.reconnect_timer_id = None
        if avatar_path == '':
            self.avatar_path = gui.theme.logo
        else:
            self.avatar_path = avatar_path

        th_pix = utils.safe_gtk_pixbuf_load(gui.theme.throbber, None,
                animated=True)
        self.throbber = gtk.image_new_from_animation(th_pix)

        self.b_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        self.b_cancel.connect('clicked', self._on_cancel_clicked)
        self.b_cancel.set_border_width(8)

        self.label = gtk.Label()
        self.label.set_markup('<b>Connecting...</b>')
        self.label_timer = gtk.Label()
        self.label_timer.set_markup('<b>Connection error!\n </b>')

        self.img_account = gtk.Image()
        self.img_account.set_from_pixbuf(utils.safe_gtk_pixbuf_load(self.avatar_path,(96,96)))

        al_throbber = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.2,
            yscale=0.2)
        al_button_cancel = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.15)
        al_label = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.0,
            yscale=0.0)
        al_label_timer = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.0,
            yscale=0.0)
        al_logo = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.0,
            yscale=0.0)

        al_throbber.add(self.throbber)
        al_button_cancel.add(self.b_cancel)
        al_label.add(self.label)
        al_label_timer.add(self.label_timer)
        al_logo.add(self.img_account)

        vbox = gtk.VBox()
        vbox.pack_start(al_logo, True, False)
        vbox.pack_start(al_label, True, False)
        vbox.pack_start(al_label_timer, True, False)
        vbox.pack_start(al_throbber, True, False)
        vbox.pack_start(al_button_cancel, True, True)

        self.add(vbox)
        vbox.show_all()

        self.dim = 96
        gobject.timeout_add(20, self.do_animation)

        self.label.hide()
        self.throbber.hide()
        self.label_timer.hide()

    def do_animation(self):
       '''do the avatar's animation on login'''
       if self.dim <= 128:
           self.dim += 4
           self.img_account.set_from_pixbuf(utils.safe_gtk_pixbuf_load(
                                       self.avatar_path,(self.dim,self.dim)))
           return True
       else:
           self.label.show()
           self.clear_connect()
           return False

    def _on_cancel_clicked(self, button):
        '''
        cause the return to login window
        '''
        self.callback()

    def on_connecting(self, message):
       '''
       Show messages while connecting..
       '''
       #taken from amsn2..but i like a lot!
       #this hack resolve a problem of visualization..XD FIXME
       gobject.timeout_add(1000, lambda: self.label.set_markup('<b>%s</b>'% message))

    def clear_connect(self):
        '''
        clean the connect interface after the reconnect phase
        '''
        self.label_timer.hide()
        self.throbber.show()
        self.label.set_markup('<b>Connecting...</b>')

    def on_reconnect(self, callback, account):
        '''
        show the reconnect countdown
        '''
        self.label.show()
        self.label.set_markup('<b>Connection error\n </b>')
        self.label_timer.show()
        self.throbber.hide()
        self.reconnect_after = 30
        if self.reconnect_timer_id is None:
            self.reconnect_timer_id = gobject.timeout_add(1000, \
                self.update_reconnect_timer, callback, account)

        self.update_reconnect_timer(callback, account)

    def update_reconnect_timer(self, callback, account):
        '''
        updates reconnect label and launches login if counter is 0
        '''
        self.reconnect_after -= 1
        self.label_timer.set_text('Reconnecting in %d seconds'\
                                             % self.reconnect_after )
        if self.reconnect_after <= 0:
            gobject.source_remove(self.reconnect_timer_id)
            self.reconnect_timer_id = None
            #do login
            callback(account, None, None, None, on_reconnect=True)
            return False
        else:
            return True

