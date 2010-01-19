# -*- coding: utf-8 -*-
import gtk
import base64
import gobject
import locale
import time
import sys
from shutil import rmtree

import e3
import gui
import utils
import extension
import StatusButton
import Dialog
import MainMenu
import stock

import logging
log = logging.getLogger('gtkui.Login')

class Login(gtk.Alignment):
    #TODO automatic REconnection??countdown???
    #TODO i don't like the gui "jumps" when i pass from connecting to reconnecting or 
    #when there is the nicebar for example

    def __init__(self, callback,callback_disconnect, on_preferences_changed, config,
                 config_dir,config_path, proxy=None, use_http=False, 
                 session_id=None, on_disconnect=False, interface='login'):

        gtk.Alignment.__init__(self, xalign=0.5, yalign=0.5, xscale=1.0,
            yscale=1.0)
        
        self.config = config
        self.config_dir = config_dir
        self.config_path = config_path
        self.callback = callback
        self.callback_disconnect = callback_disconnect
        self.on_preferences_changed = on_preferences_changed
        # the id of the default extension that handles the session
        # used to select the default session on the preference dialog
        self.use_http = use_http
        self.session_id = session_id

        account = self.config.get_or_set('last_logged_account', '')
        self.l_auto_login = self.config.get_or_set('l_auto_login', [])
        self.l_remember_account = self.config.get_or_set('l_remember_account', [])
        self.l_remember_password = self.config.get_or_set('l_remember_password', [])
        self.accounts = self.config.get_or_set('d_accounts', {})
        self.statuses = self.config.get_or_set('d_status', {})

        if proxy is None:
            self.proxy = e3.Proxy()
        else:
            self.proxy = proxy
        
        self.dialog = extension.get_default('dialog')

        self.menu = None
        self._build_menu()

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

        status_padding = gtk.Label()
        status_padding.set_size_request(*self.btn_status.size_request())

        self.txt_password = gtk.Entry()
        self.txt_password.set_visibility(False)
        self.txt_password.connect('key-press-event',
            self._on_password_key_press)


        pix_account = utils.safe_gtk_pixbuf_load(gui.theme.user)
        pix_password = utils.safe_gtk_pixbuf_load(gui.theme.password)
        img_logo = utils.safe_gtk_image_load(gui.theme.logo)
        th_pix = utils.safe_gtk_pixbuf_load(gui.theme.throbber, None, animated=True)
        self.throbber = gtk.image_new_from_animation(th_pix)

        self.remember_account = gtk.CheckButton(_('Remember me'))
        self.remember_password = gtk.CheckButton(_('Remember password'))
        self.auto_login = gtk.CheckButton(_('Auto-login'))
        
        self.remember_account.connect('toggled',
            self._on_remember_account_toggled)
        self.remember_password.connect('toggled',
            self._on_remember_password_toggled)
        self.auto_login.connect('toggled',
            self._on_auto_login_toggled)

        self.forgetMe = gtk.EventBox()
        self.forgetMe.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.forgetMeLabel = gtk.Label('<span foreground="#0000AA">(' + \
                                            _('Forget me') + ')</span>')
        self.forgetMeLabel.set_use_markup(True)
        self.forgetMe.add(self.forgetMeLabel)
        self.forgetMe.connect('button_press_event', self._on_forgetMe_clicked)
        self.forgetMe.set_child_visible(False)

        hboxremember = gtk.HBox(spacing=2)
        hboxremember.pack_start(self.remember_account, False, False)
        hboxremember.pack_start(self.forgetMe, False, False)
        
        vbox_remember = gtk.VBox(spacing=4)
        vbox_remember.set_border_width(8)
        vbox_remember.pack_start(hboxremember)
        vbox_remember.pack_start(self.remember_password)
        vbox_remember.pack_start(self.auto_login)
        
        self.b_connect = gtk.Button(stock=gtk.STOCK_CONNECT)
        self.b_connect.connect('clicked', self._on_connect_clicked)
        self.b_connect.set_border_width(8)
        
        self.b_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        self.b_cancel.connect('clicked', self._on_cancel_clicked)
        self.b_cancel.set_border_width(8)

        vbox = gtk.VBox()

        hbox_account = gtk.HBox(spacing=6)
        img_account = gtk.Image()
        img_account.set_from_pixbuf(utils.scale_nicely(pix_account))
        hbox_account.pack_start(img_account, False)
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

        self.eventBox = gtk.EventBox()
        nicebarBox = gtk.HBox(False)
        self.eventBox.add(nicebarBox)
        self.label = gtk.Label()
        self.label.set_line_wrap(True)
        self.image = gtk.Image()
        self.image.set_from_stock(gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_LARGE_TOOLBAR)
        nicebarBox.pack_start(self.image, False, False)
        nicebarBox.pack_start(self.label, True, False)
        self.eventBox.connect("button-press-event", self._on_nice_bar_clicked)

        al_vbox_entries = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.2,
            yscale=0.0)
        al_vbox_remember = gtk.Alignment(xalign=0.55, yalign=0.5,xscale=0.05,
            yscale=0.2)
        al_vbox_throbber = gtk.Alignment(xalign=0.5, yalign=0.5,xscale=0.2,
            yscale=0.2)
        al_button = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.15)
        al_button_cancel = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.15)
        al_logo = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.0,
            yscale=0.0)
        al_preferences = gtk.Alignment(xalign=1.0, yalign=0.5)
        
        al_vbox_entries.add(vbox_entries)
        al_vbox_remember.add(vbox_remember)
        al_vbox_throbber.add(self.throbber)
        al_button.add(self.b_connect)
        al_button_cancel.add(self.b_cancel)
        al_logo.add(img_logo)
        al_preferences.add(self.b_preferences)
        
        vbox.pack_start(self.menu,False)
        vbox.pack_start(self.eventBox,False)
        vbox.pack_start(al_logo, True, True, 10)
        vbox.pack_start(al_vbox_entries, True, True)
        vbox.pack_start(al_vbox_remember, True, False)
        vbox.pack_start(al_vbox_throbber, False, False)
        vbox.pack_start(al_button, True, True)
        vbox.pack_start(al_button_cancel, True, True)
        vbox.pack_start(al_preferences, False)

        self.add(vbox)
        vbox.show_all()

        self.throbber.hide()
        self.b_cancel.hide()
        self.eventBox.hide_all()
        
        if account != '':
            self.cmb_account.get_children()[0].set_text(account)
            self.forgetMe.set_child_visible(True)
            self.remember_account.set_sensitive(False)
            #autologin
            if account in self.l_auto_login and not on_disconnect:
                self.do_connect()

    def _build_menu(self):
        '''buildall the login menu'''
        handler = gui.base.LoginHandler(self.dialog,
            self._on_preferences, self._on_quit)

        LoginMenu = extension.get_default('login menu')
        self.menu = LoginMenu(handler, self.config)
        self.menu.show_all()

    def set_sensitive(self, sensitive):
        self.cmb_account.set_sensitive(sensitive)
        self.txt_password.set_sensitive(sensitive)
        self.btn_status.set_sensitive(sensitive)
        self.b_connect.set_sensitive(sensitive)
        self.remember_account.set_sensitive(sensitive)
        self.remember_password.set_sensitive(sensitive)
        self.forgetMe.set_child_visible(sensitive)
        self.auto_login.set_sensitive(sensitive)
        self.b_preferences.set_sensitive(sensitive)
        self.menu.set_sensitive(sensitive)

        if sensitive:
            self.throbber.hide()
            self.b_cancel.hide()
            self.b_connect.show()
        else:
            self.throbber.show()
            self.b_connect.hide()
            self.b_cancel.show()

    def do_connect(self):
        '''do all the staff needed to connect'''

        user = self.cmb_account.get_active_text()
        password = self.txt_password.get_text()
        account = e3.Account(user, password, self.btn_status.status)
        remember_password = self.remember_password.get_active()
        remember_account = self.remember_account.get_active()

        if user == '' or password == '':
            self.show_nice_bar('user or password fields are empty')
            return

        self._config_account(account, remember_account, remember_password)

        self.throbber.show()
        self.set_sensitive(False)
        self.callback(account,self.session_id, self.proxy, self.use_http)

    def _config_account(self,account, remember_account,remember_password):
        '''modify the config for the current account before login'''

        if remember_password:
            self.config.d_accounts[account.account] = base64.b64encode(
                account.password)
            self.config.d_status[account.account] = account.status
            self.config.last_logged_account = account.account

            if account.account not in self.config.l_remember_account:
                self.config.l_remember_account.append(account.account)

            if account.account not in self.config.l_remember_password:
                self.config.l_remember_password.append(account.account)

        elif remember_account:
            self.config.d_accounts[account.account] = ''
            self.config.d_status[account.account] = account.status
            self.config.last_logged_account = account.account

            if account.account not in self.config.l_remember_account:
                self.config.l_remember_account.append(account.account)

            #in the case i want remember account but not password
            if account.account in self.config.l_remember_password:
                self.config.l_remember_password.remove(account.account)

        self.config.save(self.config_path)

    def _on_account_changed(self, entry):
        '''called when the content of the account entry changes'''
        self._update_fields(self.cmb_account.get_active_text())

    def _update_fields(self, account):
        '''update the different fields according to the account that is
        on the account entry'''
        if account == '':
            self.remember_account.set_active(False)
            self.remember_password.set_active(False)
            self.auto_login.set_active(False)
            self.forgetMe.set_child_visible(False)
            self.remember_account.set_sensitive(True)
            self.txt_password.set_text('')
            self.txt_password.set_sensitive(True)
            return
        
        #update password and account checkbox
        if account in self.l_remember_password:
            self.remember_password.set_active(True)
            self.txt_password.set_sensitive(False)
        elif account in self.l_remember_account:
            self.remember_account.set_active(True)
            self.remember_password.set_active(False)
        else:
            self.remember_account.set_active(False)
            self.txt_password.set_sensitive(True)

        #update autologin checkbox
        if account in self.l_auto_login:
            self.auto_login.set_active(True)
            self.remember_password.set_active(True)
            self.remember_account.set_sensitive(False)
            self.remember_password.set_sensitive(False)
        else:
             self.auto_login.set_active(False)

        #update password and forgetme label
        if account in self.accounts:
            self.txt_password.set_text(base64.b64decode(self.accounts[account]))
            self.forgetMe.set_child_visible(True)
            self.remember_account.set_sensitive(False)
        else:
            self.txt_password.set_text('')          
            self.forgetMe.set_child_visible(False)
            self.remember_account.set_sensitive(True)

        #update status box
        if account in self.statuses:
            try:
                self.btn_status.set_status(int(self.statuses[account]))
            except ValueError:
                log.debug('invalid status')
        else:
            self.btn_status.set_status(e3.status.ONLINE)

    def _reload_account_list(self,*args):
       '''reload the account list in the combobox'''
       self.liststore.clear() 
       for mail in sorted(self.accounts):
           self.liststore.append([mail, utils.scale_nicely(self.pixbuf)])
       return

       #i'm here if self.accounts is empty
       self.liststore = None

    def show_nice_bar(self,message,color=gtk.gdk.Color(57600,23040,19712),image=gtk.STOCK_DIALOG_ERROR):
        if message != None:
            self.eventBox.modify_bg(gtk.STATE_NORMAL, color)
            self.image.set_from_stock(image, gtk.ICON_SIZE_LARGE_TOOLBAR)
            self.label.set_text(message)
            self.eventBox.show_all()
        else:
            self.eventBox.hide_all()

    def _on_password_key_press(self, widget, event):
        '''called when a key is pressed on the password field'''
        self.eventBox.hide_all()
        if event.keyval == gtk.keysyms.Return or \
           event.keyval == gtk.keysyms.KP_Enter:
            self.do_connect()

    def _on_account_key_press(self, widget, event):
        '''called when a key is pressed on the password field'''
        self.eventBox.hide_all()
        if event.keyval == gtk.keysyms.Return or \
           event.keyval == gtk.keysyms.KP_Enter:
            self.txt_password.grab_focus()

    def _on_forgetMe_clicked(self, *args):
       '''called when the forget me label is clicked'''
       def _yes_no_cb(response):
            '''callback from the confirmation dialog'''
            user = self.cmb_account.get_active_text()
            if response == stock.YES:
                try: # Delete user's folder
                    rmtree(self.config_dir.join(user))
                    dirAt = self.config_dir.join(user.replace('@','-at-'))
                    if self.config_dir.dir_exists(dirAt):
                        rmtree(dirAt)
                except: 
                   self.show_nice_bar(_('Error while deleting user'))

                if user in self.config.l_remember_account:
                    self.config.l_remember_account.remove(user)

                if user in self.config.l_remember_password:
                    self.config.l_remember_password.remove(user)
                
                if user in self.config.l_auto_login:
                    self.config.l_auto_login.remove(user)

                if user in self.config.last_logged_account:
                    self.config.last_logged_account = ''

                if user in self.config.d_accounts:
                    del self.config.d_accounts[user]

                if user in self.config.d_status:
                    del self.config.d_status[user]

                self.config.save(self.config_path)
                self. _reload_account_list()
                self.cmb_account.get_children()[0].set_text('')
                self.remember_account.set_sensitive(True)

       self.dialog.yes_no(_('Are you sure you want to delete the account %s ?') % \
                      self.cmb_account.get_active_text(), _yes_no_cb)

    def _on_connect_clicked(self, button):
        self.do_connect()
    
    def _on_cancel_clicked(self, button):
        # call the controller on_disconnect
        self.callback_disconnect()
        self._update_fields(self.cmb_account.get_active_text())

    def _on_nice_bar_clicked(self, widget, event):
        self.eventBox.hide_all()

    def _on_quit(self):
        '''close emesene'''
        while gtk.events_pending():
            gtk.main_iteration(False)

        sys.exit(0)

    def _on_preferences(self):
        '''called when button preferences in option menu is clicked'''
        self._on_preferences_selected(None)

    def _on_remember_account_toggled(self, button):
        '''called when the remember account check button is toggled'''
        if not self.remember_account.get_active():
            self.remember_password.set_active(False)

    def _on_remember_password_toggled(self, button):
        '''called when the remember password check button is toggled'''
        if self.remember_password.get_active():
            self.remember_account.set_active(True)

    def _on_auto_login_toggled(self, button):
        '''called when the auto-login check button is toggled'''
        user = self.cmb_account.get_active_text()

        if self.auto_login.get_active():
            if user != '' and user not in self.l_auto_login:
                self.config.l_auto_login.append(user)
            self.remember_password.set_active(True)
            self.remember_account.set_sensitive(False)
            self.remember_password.set_sensitive(False)

        else:
            if user != '' and user in self.l_auto_login:
                self.config.l_auto_login.remove(user)

            if user not in self.config.d_accounts:
                self.remember_account.set_active(False)
                self.remember_account.set_sensitive(True)
                self.remember_password.set_sensitive(True)
            else:
                self.remember_password.set_sensitive(True)

    def _on_preferences_enter(self, button, event):
        '''called when the mouse enters the preferences button'''
        self.img_preferences.set_sensitive(True)

    def _on_preferences_leave(self, button, event):
        '''called when the mouse leaves the preferences button'''
        self.img_preferences.set_sensitive(False)

    def _on_preferences_selected(self, button):
        '''called when the user clicks the preference button'''
        extension.get_default('dialog').login_preferences(self.session_id,
            self._on_new_preferences, self.use_http, self.proxy)

    def _on_new_preferences(self, use_http, use_proxy, host, port,
        use_auth, user, passwd, session_id):
        '''called when the user press accept on the preferences dialog'''
        self.proxy = e3.Proxy(use_proxy, host, port, use_auth, user, passwd)
        self.session_id = session_id
        self.use_http = use_http
        self.on_preferences_changed(self.use_http, self.proxy, self.session_id)
