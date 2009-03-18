import gtk

class ContactMenu(gtk.Menu):
    """
    A class that represents a menu to handle contact related information
    """

    def __init__(self, handler):
        """
        constructor

        handler -- a e3common.Handler.ContactHandler
        """
        gtk.Menu.__init__(self)
        self.handler = handler

        self.add = gtk.ImageMenuItem(gtk.STOCK_ADD)
        self.remove = gtk.ImageMenuItem(gtk.STOCK_REMOVE)
        self.block = gtk.ImageMenuItem('Block')
        self.unblock = gtk.ImageMenuItem('Unblock')
        self.set_alias = gtk.ImageMenuItem('Set alias')

        self.append(self.add)
        self.append(self.remove)
        self.append(self.block)
        self.append(self.unblock)
        self.append(self.set_alias)
