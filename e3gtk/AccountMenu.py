import gtk

class AccountMenu(gtk.Menu):
    """
    A class that represents a menu to handle contact related information
    """

    def __init__(self, handler):
        """
        constructor

        handler -- a e3common.Handler.AccountHandler
        """
        gtk.Menu.__init__(self)
        self.handler = handler

        self.set_nick = gtk.ImageMenuItem('Set nick')
        self.set_message = gtk.ImageMenuItem('Set message')
        self.set_picture = gtk.ImageMenuItem('Set picture')

        self.append(self.set_nick)
        self.append(self.set_message)
        self.append(self.set_picture)
