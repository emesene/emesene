import gtk
import gobject

import utils
import TinyButton

import Renderers

CLOSE_ON_LEFT = 0
try:
    import gconf
    gclient = gconf.client_get_default()
    val = gclient.get("/apps/metacity/general/button_layout")
    if val.get_string().startswith("close"):
        CLOSE_ON_LEFT = 1
except:
    pass

class TabWidget(gtk.HBox):
    '''a widget that is placed on the tab on a notebook'''
    NAME = 'Tab Widget'
    DESCRIPTION = 'A widget to display the tab information'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, text, on_tab_menu, on_close_clicked, conversation):
        '''constructor'''
        gtk.HBox.__init__(self)
        self.set_border_width(0)
        self.set_spacing(4)

        self.image = gtk.Image()
        self.label = Renderers.SmileyLabel()
        self.label.set_text(text)
        self.close = TinyButton.TinyButton(gtk.STOCK_CLOSE)
        self.close.connect('clicked', on_close_clicked,
            conversation)

        if CLOSE_ON_LEFT:
            self.pack_start(self.close, False, False, 0)
            self.pack_start(self.image, False, False, 0)
            self.pack_start(self.label, True, True, 0)
        else:
            self.pack_start(self.image, False, False, 0)
            self.pack_start(self.label, True, True, 0)
            self.pack_start(self.close, False, False, 0)

        self.image.show()
        self.label.show()
        self.close.show()

    def set_image(self, path):
        '''set the image from path'''
        if utils.file_readable(path):
            self.image.set_from_file(path)
            self.image.show()
            return True

        return False

    def set_text(self, text):
        '''set the text of the label'''
        self.label.set_markup(Renderers.msnplus_to_list(gobject.markup_escape_text(text)))
