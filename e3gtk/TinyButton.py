import gtk

class TinyButton(gtk.Button):
    '''a simple and tiny button'''

    def __init__(self, stock):
        '''constructor'''
        gtk.Button.__init__(self)

        self.image = gtk.image_new_from_stock(stock, gtk.ICON_SIZE_MENU)
        self.set_image(self.image)
        width, height = gtk.icon_size_lookup(gtk.ICON_SIZE_MENU)
        self.set_size_request(width + 2, height + 2)
        self.image.show()

        self.set_focus_on_click(False)
        self.set_relief(gtk.RELIEF_NONE)

if __name__ == '__main__':
    w = gtk.Window()
    w.add(TinyButton(gtk.STOCK_CLOSE))
    w.show_all()
    gtk.main()
