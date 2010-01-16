import gtk
import pango

import utils

class Header(gtk.HBox):
    '''a widget used to display some information about the conversation'''
    INFO_TPL = '<span>%s</span>\n'
    INFO_TPL += '<span size="small">%s</span>'

    NAME = 'Header'
    DESCRIPTION = 'The widget that displays information about the conversation'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self):
        '''constructor'''
        gtk.HBox.__init__(self)
        self.set_border_width(2)
        self._information = gtk.Label('info')
        self._information.set_ellipsize(pango.ELLIPSIZE_END)
        self._information.set_alignment(0.0, 0.5)

        self.pack_start(self._information, True, True)

    def _set_information(self, lines):
        '''set the text on the information, lines is a tuple of size 3 with 3
        strings that will be replaced on the template'''
        self._information.set_markup(Header.INFO_TPL % lines)

    def _get_information(self):
        '''return the text on the information'''
        return self._information.get_markup()

    information = property(fget=_get_information, fset=_set_information)
