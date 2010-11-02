import gtk

class GroupMenu(gtk.Menu):
    """
    A class that represents a menu to handle contact related information
    """
    NAME = 'Group Menu'
    DESCRIPTION = 'The menu that displays all the group options'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, handler):
        """
        constructor

        handler -- a e3common.Handler.GroupHandler
        """
        gtk.Menu.__init__(self)
        self.handler = handler

        self.add = gtk.ImageMenuItem(gtk.STOCK_ADD)
        self.add.connect('activate', 
            lambda *args: self.handler.on_add_group_selected())

        self.remove = gtk.ImageMenuItem(gtk.STOCK_REMOVE)
        self.remove.connect('activate', 
            lambda *args: self.handler.on_remove_group_selected())

        self.rename = gtk.ImageMenuItem(_('Rename'))
        self.rename.set_image(gtk.image_new_from_stock(gtk.STOCK_EDIT,
            gtk.ICON_SIZE_MENU))
        self.rename.connect('activate', 
            lambda *args: self.handler.on_rename_group_selected())


        self.append(self.add)
        self.append(self.remove)
        self.append(self.rename)
