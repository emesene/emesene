import gtk

class GroupMenu(gtk.Menu):
    """
    A class that represents a menu to handle contact related information
    """

    def __init__(self, handler):
        """
        constructor

        handler -- a e3common.Handler.GroupHandler
        """
        gtk.Menu.__init__(self)
        self.handler = handler

        self.add = gtk.ImageMenuItem(gtk.STOCK_ADD)
        self.remove = gtk.ImageMenuItem(gtk.STOCK_REMOVE)
        self.rename = gtk.ImageMenuItem('Rename')

        self.append(self.add)
        self.append(self.remove)
        self.append(self.rename)
