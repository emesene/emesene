import gtk

import protocol.base.Object as Object

class TextField(gtk.VBox, Object.Object):
    '''this class represent a widget that is a button and when clicked
    it shows a textfield until the text is set, then the button appears again'''

    def __init__(self, text, empty_text, allow_empty, dialog):
        '''class constructor, text is the text to show, empty_text is the
        text to display when no text is entered, allow_empty is a boolean
        that indicates if the user can enter an empty string'''
        gtk.VBox.__init__(self)
        Object.Object.__init__(self)

        self.entry = gtk.Entry()
        self.button = gtk.Button()
        self.button.set_relief(gtk.RELIEF_NONE)

        self.text = text
        self.empty_text = empty_text
        self.allow_empty = allow_empty
        self.dialog = dialog

        self.pack_start(self.button, True, True)
        self.pack_start(self.entry, True, True)

        self.button.set_label(self.text or self.empty_text)

        self.button.connect('clicked', self.on_button_clicked)
        self.entry.connect('activate', self.on_entry_activate)

        self.signal_add('text-changed', 2)

        self.button.show()

    def on_button_clicked(self, button):
        '''method called when the button is clicked'''
        self.button.hide()
        self.entry.show()
        self.entry.grab_focus()

    def on_entry_activate(self, entry):
        '''method called when the user press enter on the entry'''
        
        if not self.entry.get_text() and not self.allow_empty:
            if self.dialog:
                self.dialog.error("Empty text not allowed")

            return

        if self.entry.get_text() != self.text:
            old_text = self.text
            self.text = self.entry.get_text()
            self.signal_emit('text-changed', old_text, self.text)

        self.entry.hide()
        self.button.set_label(self.text)
        self.button.show()

    def show_all(self):
        '''override the show method to not show both widgets on a show_all
        call'''
        pass

if __name__ == '__main__':

    def _on_text_changed(text_field, old, new):
        print 'text changed from', old, ' to ', new

    w = gtk.Window()
    t = TextField("", "<click here to change nick>", True, None)
    t.signal_connect('text-changed', _on_text_changed)
    w.add(t)
    t.show()
    w.show()
    gtk.main()
