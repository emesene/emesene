import gtk

import gui
import protocol.base.Account as Account
import protocol.base.status as status
import protocol.base.stock as stock
import utils
import StatusButton

class Login(gtk.Alignment):
    
    def __init__(self, callback, account=None):
        gtk.Alignment.__init__(self, xalign=0.5, yalign=0.5, xscale=1.0, 
            yscale=0.9)

        account = account or Account("", "", status.ONLINE)
        self.callback = callback

        self.txt_account = gtk.Entry()
        self.txt_account.set_text(account.account)

        self.btn_status = StatusButton.StatusButton()
        
        self.txt_password = gtk.Entry()
        self.txt_password.set_visibility(False)
        self.txt_password.set_text(account.password)

        self.remember_password = gtk.CheckButton("Remember password")
        
        self.b_connect = gtk.Button(stock=gtk.STOCK_CONNECT)
        self.b_connect.connect("clicked", self._on_connect_clicked)

        img_account = utils.safe_gtk_image_load(gui.theme.user)
        img_password = utils.safe_gtk_image_load(gui.theme.password)
        img_logo = utils.safe_gtk_image_load(gui.theme.logo)

        vbox = gtk.VBox()
        vbox.set_border_width(10)

        hbox_account = gtk.HBox(spacing=5)
        hbox_account.pack_start(img_account, False)
        hbox_account.pack_start(self.txt_account, True, False)
        hbox_account.pack_start(self.btn_status, False)

        hbox_password = gtk.HBox(spacing=5)
        hbox_password.pack_start(img_password, False)
        hbox_password.pack_start(self.txt_password, True, False)
        hbox_password.pack_start(gtk.Label('        '), False)

        al_account = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.2, 
            yscale=0.0)
        al_password = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.2, 
            yscale=0.0)
        al_remember = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.2, 
            yscale=0.2)
        al_button = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.2, 
            yscale=0.1)
        al_logo = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0.0, 
            yscale=0.0)

        al_account.add(hbox_account)
        al_password.add(hbox_password)
        al_remember.add(self.remember_password)
        al_button.add(self.b_connect)
        al_logo.add(img_logo)

        vbox.pack_start(al_logo, True, True, 10)
        vbox.pack_start(al_account, True, True)
        vbox.pack_start(al_password, True, True)
        vbox.pack_start(al_remember, True, True)
        vbox.pack_start(al_button, True, True)

        self.add(vbox)
        vbox.show_all()

    def set_sensitive(self, sensitive):
        self.txt_account.set_sensitive(sensitive)
        self.txt_password.set_sensitive(sensitive)
        self.btn_status.set_sensitive(sensitive)
        self.b_connect.set_sensitive(sensitive)
        self.remember_password.set_sensitive(sensitive)

    def _on_connect_clicked(self, button):
        user = self.txt_account.get_text()
        password = self.txt_password.get_text()
        account = Account(user, password, self.btn_status.status)
        remember = self.remember_password.get_active()
        self.set_sensitive(False)
        self.callback(account, remember)

