import gtk

import songretriever

import gui
from gui.gtkui import utils
# from gui.gtkui.Preferences import BaseTable

class Preferences(gtk.Window):
    '''the preference basic window of the 'listening to' extension'''

    def __init__(self, callback, player_name, config_table):
        '''constructor, callback is a function that receives a boolean as first
        argument with the value True if ok was clicked and False otherwise,
        the rest of the arguments are the values collected during configuration
        '''
        gtk.Window.__init__(self)

        self.config_table = config_table
        self.callback = callback
        self.set_border_width(2)
        self.set_title(player_name + " preferences")
        self.set_icon(
            utils.safe_gtk_image_load(gui.theme.logo).get_pixbuf())

        self.set_default_size(300, 150)
        self.set_role("New preferences Window")
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)

        vbox  = gtk.VBox()

        buttons = gtk.HButtonBox()
        buttons.set_layout(gtk.BUTTONBOX_END)

        accept = gtk.Button(stock=gtk.STOCK_OK)
        cancel = gtk.Button(stock=gtk.STOCK_CANCEL)

        buttons.pack_start(accept)
        buttons.pack_start(cancel)

        accept.connect('clicked', self._on_accept)
        cancel.connect('clicked', self._on_cancel)
        self.connect('delete_event', self._on_close)

        vbox.pack_start(self.config_table, True, False)
        vbox.pack_start(buttons, True)

        vbox.show_all()
        self.add(vbox)

    def send_values(self, status):
        '''call the callback'''
        self.callback(status)

    def _on_accept(self, button):
        '''callback when accept is clicked'''
        self.send_values(True)
        self.hide()

    def _on_cancel(self, button):
        '''callback when cancel is clicked'''
        self.send_values(False)
        self.hide()

    def _on_close(self, window, unused):
        '''callback when the window is closed'''
        self.send_values(False)
        self.hide()

