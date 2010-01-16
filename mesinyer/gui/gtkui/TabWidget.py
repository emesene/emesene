import gtk
import gobject

import utils
import TinyButton

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
        self.label = gtk.Label(text)
        self.close = TinyButton.TinyButton(gtk.STOCK_CLOSE)
        self.close.connect('clicked', on_close_clicked,
            conversation)

        self.label.set_max_width_chars(20)
        self.label.set_use_markup(True)
        self.label.set_alignment(0.0, 0.5)

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
        self.label.set_markup(gobject.markup_escape_text(text))

