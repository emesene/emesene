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

        self.change_profile = gtk.ImageMenuItem('Change profile')
        self.change_profile.set_image(gtk.image_new_from_stock(gtk.STOCK_EDIT,
            gtk.ICON_SIZE_MENU))
        self.change_profile.connect('activate',
            lambda *args: self.handler.change_profile())


        self.append(self.change_profile)







