import gtk

class TinyButton(gtk.EventBox):
    '''a simple and tiny button'''

    def __init__(self, stock):
        '''constructor'''
        gtk.EventBox.__init__(self)
        self.set_above_child(True)

        self.image = gtk.image_new_from_stock(stock, gtk.ICON_SIZE_MENU)
        self.image.show()

        self.add(self.image)

        self.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        # TODO: when see if changing the theme maintins the colors
        self.normal_color = self.get_style().bg[gtk.STATE_NORMAL]
        self.prelight_color = self.get_style().bg[gtk.STATE_PRELIGHT]
        self.set_events(gtk.gdk.ENTER_NOTIFY_MASK)
        self.set_events(gtk.gdk.LEAVE_NOTIFY_MASK)

        self.connect('enter_notify_event', self._on_enter)
        self.connect('leave_notify_event', self._on_leave)

    def _on_enter(self, widget, event):
        '''called when the mouse enters the button'''
        self.modify_bg(gtk.STATE_NORMAL, self.prelight_color)

    def _on_leave(self, widget, event):
        '''called when the mouse leaves the button'''
        self.modify_bg(gtk.STATE_NORMAL, self.normal_color)


if __name__ == '__main__':
    def callback(button, event):
        print 'click'

    window = gtk.Window()
    b = TinyButton(gtk.STOCK_CLOSE)
    window.add(b)
    window.show_all()
    gtk.main()
