import gtk

import songretriever

import gui
from gui.gtkui import utils

class Preferences(gtk.Window):
    '''the preference window of the music plugin'''

    def __init__(self, callback, player, format):
        '''constructor, callback is a function that receives a boolean as first
        argument with the value True if ok was clicked and False otherwise,
        the rest of the arguments are the values collected during configuration
        '''
        gtk.Window.__init__(self)

        self.callback = callback
        self.set_border_width(2)
        self.set_title("Preferences")
        self.set_icon(
            utils.safe_gtk_image_load(gui.theme.logo).get_pixbuf())

        self.set_default_size(300, 150)
        self.set_role("New preferences Window")
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)

        vbox  = gtk.VBox()
        table = gtk.Table(2, 2)
        table.set_row_spacings(4)
        table.set_col_spacings(4)

        label = gtk.Label("player")
        label.set_alignment(0.0, 0.5)
        table.attach(label, 0, 1, 0, 1)

        self.combo = gtk.combo_box_new_text()

        active = 0
        count = 0
        for name in songretriever.get_handler_names():
            if name == player:
                active = count

            self.combo.append_text(name)
            count += 1

        self.combo.set_active(active)

        table.attach(self.combo, 1, 2, 0, 1)

        label = gtk.Label("format")
        label.set_alignment(0.0, 0.5)
        table.attach(label, 0, 1, 1, 2)

        self.entry = gtk.Entry()
        self.entry.set_text(format)
        table.attach(self.entry, 1, 2, 1, 2)

        buttons = gtk.HButtonBox()
        buttons.set_layout(gtk.BUTTONBOX_END)

        accept = gtk.Button(stock=gtk.STOCK_OK)
        cancel = gtk.Button(stock=gtk.STOCK_CANCEL)

        buttons.pack_start(accept)
        buttons.pack_start(cancel)

        accept.connect('clicked', self._on_accept)
        cancel.connect('clicked', self._on_cancel)
        self.connect('delete_event', self._on_close)

        vbox.pack_start(table, True, False)
        vbox.pack_start(buttons, True)

        vbox.show_all()
        self.add(vbox)

    def send_values(self, status):
        '''collect the config values and send them to the callback'''
        player = self.combo.get_active_text()
        format = self.entry.get_text()
        self.callback(status, player, format)

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

def test():
    '''test method'''
    def callback(status, player, format):
        print status, player, format

    Preferences(callback, "mpd", "%ARTIST% - %ALBUM% - %TITLE%").show()
    gtk.main()

if __name__ == "__main__":
    test()
