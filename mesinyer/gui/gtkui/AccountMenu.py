import gtk

class AccountMenu(gtk.Menu):
    """
    A class that represents a menu to handle contact related information
    """
    NAME = 'Account menu'
    DESCRIPTION = 'The menu to handle account options'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, handler):
        """
        constructor

        handler -- a e3common.Handler.AccountHandler
        """
        gtk.Menu.__init__(self)
        self.handler = handler

        self.set_nick = gtk.ImageMenuItem('Set nick')
        self.set_nick.set_image(gtk.image_new_from_stock(gtk.STOCK_EDIT,
            gtk.ICON_SIZE_MENU))
        self.set_nick.connect('activate', 
            lambda *args: self.handler.on_set_nick_selected())

        self.set_message = gtk.ImageMenuItem('Set message')
        self.set_message.set_image(gtk.image_new_from_stock(gtk.STOCK_EDIT,
            gtk.ICON_SIZE_MENU))
        self.set_message.connect('activate', 
            lambda *args: self.handler.on_set_message_selected())

        self.set_picture = gtk.ImageMenuItem('Set picture')
        self.set_picture.set_image(gtk.image_new_from_stock(gtk.STOCK_EDIT,
            gtk.ICON_SIZE_MENU))
        self.set_picture.connect('activate', 
            lambda *args: self.handler.on_set_picture_selected())

        self.append(self.set_nick)
        self.append(self.set_message)
        self.append(self.set_picture)
