import gtk
import pango
import gobject

import dialog

class TextField(gtk.VBox):
    '''this class represent a widget that is a button and when clicked
    it shows a textfield until the text is set, then the button appears again'''

    __gsignals__ = {
        'text-changed': (gobject.SIGNAL_RUN_LAST, 
                gobject.TYPE_NONE, 
                (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT))
        }

    def __init__(self, text, empty_text, allow_empty):
        '''class constructor, text is the text to show, empty_text is the
        text to display when no text is entered, allow_empty is a boolean
        that indicates if the user can enter an empty string'''
        gtk.VBox.__init__(self)

        self.entry = gtk.Entry()
        self.label = gtk.Label()
        self.label.set_ellipsize(pango.ELLIPSIZE_END)
        self.label.set_justify(gtk.JUSTIFY_LEFT)
        self.button = gtk.Button()
        self.button.set_relief(gtk.RELIEF_NONE)

        self._text = text
        self.empty_text = empty_text
        self.allow_empty = allow_empty

        self.pack_start(self.button, True, True)
        self.pack_start(self.entry, True, True)

        self.button.add(self.label)
        self.label.set_text(self._text or self.empty_text)

        self.button.connect('clicked', self.on_button_clicked)
        self.entry.connect('activate', self.on_entry_activate)

    def on_button_clicked(self, button):
        '''method called when the button is clicked'''
        self.button.hide()
        self.entry.show()
        self.entry.grab_focus()

    def on_entry_activate(self, entry):
        '''method called when the user press enter on the entry'''
        
        if not self.entry.get_text() and not self.allow_empty:
            dialog.error("Empty text not allowed")
            return

        if self.entry.get_text() != self._text:
            old_text = self._text
            self.text = self.entry.get_text()
            self.emit('text-changed', old_text, self._text)

        self.entry.hide()
        self.button.show()

    def show(self):
        '''override show'''
        gtk.VBox.show(self)
        self.button.show()
        self.entry.hide()
        self.label.show()

    def show_all(self):
        '''override the show method to not show both widgets on a show_all
        call'''
        self.show()

    def _get_text(self):
        '''return the value of text'''
        return self._text

    def _set_text(self, value):
        '''set the value of text'''
        self._text = value
        self.label.set_text(self._text)
        self.entry.set_text(self._text)

    text = property(fget=_get_text, fset=_set_text)

if __name__ == '__main__':

    def _on_text_changed(text_field, old, new):
        print 'text changed from', old, ' to ', new

    w = gtk.Window()
    t = TextField("", "<click here to change nick>", False)
    t.connect('text-changed', _on_text_changed)
    w.add(t)
    t.show()
    w.show()
    gtk.main()
