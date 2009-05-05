import gtk
import base64
import gobject

import gui
import gui.stock as stock
import protocol
import utils
import extension
import StatusButton
from debugger import dbg

class Login(gtk.Alignment):

    def __init__(self, callback, on_preferences_changed, account,
            accounts=None, remember_account=None, remember_password=None,
            statuses=None, proxy=None, use_http=False, session_id=None):

        gtk.Alignment.__init__(self, xalign=0.5, yalign=0.5, xscale=1.0,
            yscale=1.0)

        account = account or protocol.Account("", "", protocol.status.ONLINE)
        self.callback = callback
        self.on_preferences_changed = on_preferences_changed
        self.accounts = accounts or {}
        self.l_remember_account = remember_account or []
        self.l_remember_password = remember_password or []
        self.statuses = statuses or {}
        # the id of the default extension that handles the session
        # used to select the default session on the preference dialog
        self.use_http = use_http
        self.session_id = session_id

        if proxy is None:
            self.proxy = protocol.Proxy()
        else:
            self.proxy = proxy

        completion = gtk.EntryCompletion()
        liststore = gtk.ListStore(gobject.TYPE_STRING, gtk.gdk.Pixbuf)
        completion.set_model(liststore)
        pixbufcell = gtk.CellRendererPixbuf()
        completion.pack_start(pixbufcell)
        completion.add_attribute(pixbufcell, 'pixbuf', 1)
        completion.set_text_column(0)
        completion.set_inline_selection(True)

        pixbuf = utils.safe_gtk_pixbuf_load(gui.theme.user)

        for mail in sorted(self.accounts):
            liststore.append([mail, pixbuf])

        self.txt_account = gtk.Entry()

        if account:
            self.txt_account.set_text(account.account)

        self.txt_account.set_completion(completion)
        self.txt_account.connect('key-press-event',
            self._on_account_key_press)
        self.txt_account.connect('changed',
            self._on_account_changed)

        self.btn_status = StatusButton.StatusButton()

        self.txt_password = gtk.Entry()
        self.txt_password.set_visibility(False)

        if account:
            self.txt_password.set_text(account.password)

        self.txt_password.connect('key-press-event',
            self._on_password_key_press)

        self.remember_account = gtk.CheckButton("Remember account")
        self.remember_password = gtk.CheckButton("Remember password")

        self.remember_account.connect('toggled',
            self._on_remember_account_toggled)
        self.remember_password.connect('toggled',
            self._on_remember_password_toggled)

        self.b_connect = gtk.Button(stock=gtk.STOCK_CONNECT)
        self.b_connect.connect("clicked", self._on_connect_clicked)

        img_account = utils.safe_gtk_image_load(gui.theme.user)
        img_password = utils.safe_gtk_image_load(gui.theme.password)
        img_logo = utils.safe_gtk_image_load(gui.theme.logo)

        vbox = gtk.VBox()
        vbox.set_border_width(2)

        hbox_account = gtk.HBox(spacing=5)
        hbox_account.pack_start(img_account, False)
        hbox_account.pack_start(self.txt_account, True, False)
        hbox_account.pack_start(gtk.Label('       '), False)

        hbox_password = gtk.HBox(spacing=5)
        hbox_password.pack_start(img_password, False)
        hbox_password.pack_start(self.txt_password, True, False)
        hbox_password.pack_start(self.btn_status, False)

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

        al_account = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.2,
            yscale=0.0)
        al_password = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.2,
            yscale=0.0)
        al_remember_account = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.2,
            yscale=0.2)
        al_remember_passwd = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.2,
            yscale=0.2)
        al_button = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.2,
            yscale=0.1)
        al_logo = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.0,
            yscale=0.0)
        al_preferences = gtk.Alignment(xalign=1.0, yalign=0.5)

        al_account.add(hbox_account)
        al_password.add(hbox_password)
        al_remember_account.add(self.remember_account)
        al_remember_passwd.add(self.remember_password)
        al_button.add(self.b_connect)
        al_logo.add(img_logo)
        al_preferences.add(self.b_preferences)

        vbox.pack_start(al_logo, True, True, 10)
        vbox.pack_start(al_account, True, True)
        vbox.pack_start(al_password, True, True)
        vbox.pack_start(al_remember_account, True, True)
        vbox.pack_start(al_remember_passwd, True, True)
        vbox.pack_start(al_button, True, True)
        vbox.pack_start(al_preferences, False)

        self.add(vbox)
        vbox.show_all()

    def set_sensitive(self, sensitive):
        self.txt_account.set_sensitive(sensitive)
        self.txt_password.set_sensitive(sensitive)
        self.btn_status.set_sensitive(sensitive)
        self.b_connect.set_sensitive(sensitive)
        self.remember_account.set_sensitive(sensitive)
        self.remember_password.set_sensitive(sensitive)
        self.b_preferences.set_sensitive(sensitive)

    def _on_connect_clicked(self, button):
        self.do_connect()

    def do_connect(self):
        '''do all the staff needed to connect'''
        user = self.txt_account.get_text()
        password = self.txt_password.get_text()
        account = protocol.Account(user, password, self.btn_status.status)
        remember_password = self.remember_password.get_active()
        remember_account = self.remember_account.get_active()

        if user == '':
            extension.get_default('gtk dialog').error('Empty user')
            return

        if password == '':
            extension.get_default('gtk dialog').error('Empty password')
            return

        self.set_sensitive(False)
        self.callback(account, remember_account, remember_password, 
            self.session_id, self.proxy, self.use_http)

    def _on_password_key_press(self, widget, event):
        '''called when a key is pressed on the password field'''
        if event.keyval == gtk.keysyms.Return:
            self.do_connect()

    def _on_account_key_press(self, widget, event):
        '''called when a key is pressed on the password field'''
        if event.keyval == gtk.keysyms.Return:
            self.txt_password.grab_focus()

    def _on_account_changed(self, entry):
        '''called when the content of the account entry changes'''
        self._update_fields(self.txt_account.get_text()) 

    def _update_fields(self, account):
        '''update the different fields according to the account that is
        on the account entry'''
        if account in self.l_remember_password:
            self.remember_password.set_active(True)
        elif account in self.l_remember_account:
            self.remember_account.set_active(True)
        else:
            self.remember_account.set_active(False)

        if account in self.accounts:
            self.txt_password.set_text(base64.b64decode(self.accounts[account]))
        else:
            self.txt_password.set_text('')

        if account in self.statuses:
            try:
                self.btn_status.set_status(int(self.statuses[account]))
            except ValueError:
                dbg('invalid status', 'login', 1)
        else:
            self.btn_status.set_status(protocol.status.ONLINE)


    def _on_remember_account_toggled(self, button):
        '''called when the remember account check button is toggled'''
        if not self.remember_account.get_active():
            self.remember_password.set_active(False)

    def _on_remember_password_toggled(self, button):
        '''called when the remember password check button is toggled'''
        if self.remember_password.get_active():
            self.remember_account.set_active(True)

    def _on_preferences_enter(self, button, event):
        '''called when the mouse enters the preferences button'''
        self.img_preferences.set_sensitive(True)

    def _on_preferences_leave(self, button, event):
        '''called when the mouse leaves the preferences button'''
        self.img_preferences.set_sensitive(False)

    def _on_preferences_selected(self, button):
        '''called when the user clicks the preference button'''
        extension.get_default('gtk dialog').login_preferences(self.session_id,
            self._on_new_preferences, self.use_http, self.proxy)

    def _on_new_preferences(self, use_http, use_proxy, host, port, 
        use_auth, user, passwd, session_id):
        '''called when the user press accept on the preferences dialog'''
        self.proxy = protocol.Proxy(use_proxy, host, port, use_auth, user, passwd)
        self.session_id = session_id
        self.use_http = use_http
        self.on_preferences_changed(self.use_http, self.proxy, self.session_id)
