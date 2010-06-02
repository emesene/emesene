import gtk

class TinyButton(gtk.Button):
    '''a simple and tiny button'''

    def __init__(self, stock):
        '''constructor'''
        gtk.Button.__init__(self)

        # name the button to link it to a style
        self.set_name("close-button")

        self.image = gtk.image_new_from_stock(stock, gtk.ICON_SIZE_MENU)

        self.set_image(self.image)

        width, height = gtk.icon_size_lookup(gtk.ICON_SIZE_MENU)
        self.set_size_request(width + 2, height + 2)
        self.image.show()

        self.set_focus_on_click(False)
        self.set_relief(gtk.RELIEF_NONE)

        gtk.rc_parse_string('''
            style "close-button-style" {
                GtkWidget::focus-padding = 0
                GtkWidget::focus-line-width = 0
                xthickness = 0
                ythickness = 0
            }
            widget "*.close-button" style "close-button-style"
        ''')

if __name__ == '__main__':
    w = gtk.Window()

    # create a new style for the close button
    w.add(TinyButton(gtk.STOCK_CLOSE))
    w.show_all()
    gtk.main()
