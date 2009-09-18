import gtk

import e3
import gui
import utils

class StatusMenu(gtk.Menu):
    """
    A widget that contains the statuses and allows to change the current status
    """
    NAME = 'Status Menu'
    DESCRIPTION = 'A menu to select the status'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, on_status_selected):
        """
        constructor

        on_status_selected -- a callback that receives the status when changed
        """
        gtk.Menu.__init__(self)
        self.on_status_selected = on_status_selected
        self.status = {}

        for stat in e3.status.ORDERED:
            temp_item = gtk.ImageMenuItem(e3.status.STATUS[stat])
            temp_item.set_image(utils.safe_gtk_image_load(
                gui.theme.status_icons[stat]))
            temp_item.connect('activate', self._on_activate, stat)
            self.status[stat] = temp_item
            self.append(temp_item)

    def _on_activate(self, menuitem, stat):
        """
        method called when a status menu item is called
        """

        self.on_status_selected(stat)

