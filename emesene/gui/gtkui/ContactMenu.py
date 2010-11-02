import gtk

class ContactMenu(gtk.Menu):
    """
    A class that represents a menu to handle contact related information
    """
    NAME = 'Contact Menu'
    DESCRIPTION = 'The menu that displays contact options'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, handler):
        """
        constructor

        handler -- a e3common.Handler.ContactHandler
        """
        gtk.Menu.__init__(self)
        self.handler = handler

        self.add = gtk.ImageMenuItem(gtk.STOCK_ADD)
        self.add.connect('activate',
            lambda *args: self.handler.on_add_contact_selected())

        self.remove = gtk.ImageMenuItem(gtk.STOCK_REMOVE)
        self.remove.connect('activate',
            lambda *args: self.handler.on_remove_contact_selected())

        self.block = gtk.ImageMenuItem(_('Block'))
        self.block.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL,
            gtk.ICON_SIZE_MENU))
        self.block.connect('activate',
            lambda *args: self.handler.on_block_contact_selected())

        self.unblock = gtk.ImageMenuItem(_('Unblock'))
        self.unblock.set_image(gtk.image_new_from_stock(gtk.STOCK_APPLY,
            gtk.ICON_SIZE_MENU))
        self.unblock.connect('activate',
            lambda *args: self.handler.on_unblock_contact_selected())

        self.set_alias = gtk.ImageMenuItem(_('Set alias'))
        self.set_alias.set_image(gtk.image_new_from_stock(gtk.STOCK_EDIT,
            gtk.ICON_SIZE_MENU))
        self.set_alias.connect('activate',
            lambda *args: self.handler.on_set_alias_contact_selected())

        self.view_info = gtk.ImageMenuItem(_('View information'))
        self.view_info.set_image(gtk.image_new_from_stock(gtk.STOCK_EDIT,
            gtk.ICON_SIZE_MENU))
        self.view_info.connect('activate',
            lambda *args: self.handler.on_view_information_selected())

        self.append(self.add)
        self.append(self.remove)
        self.append(self.block)
        self.append(self.unblock)
        self.append(self.set_alias)
        self.append(self.view_info)

