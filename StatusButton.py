import gtk

import gui
import Menu
import utils
import gui.StatusMenu
import protocol.base.status as status

class StatusButton(gtk.Button):
    '''a cutton that when clicked displays a popup that allows the user to
    select a status'''

    def __init__(self, contacts=None):
        gtk.Button.__init__(self)

        # a cache of gtk.Images to not load the images everytime we change
        # our status
        self.cache_imgs = {}
        self.menu = Menu.build_pop_up(gui.StatusMenu.StatusMenu(contacts,
            self._on_status_selected))

        self.set_status(status.ONLINE)
        self.set_relief(gtk.RELIEF_NONE)
        self.set_border_width(0)

        self.connect('clicked', self._on_clicked)

    def _on_clicked(self, button):
        '''callback called when the button is clicked'''
        self.menu.popup(None, None, None, 0, 0)

    def _on_status_selected(self, stat):
        '''method called when a status is selected on the popup'''
        self.set_status(stat)
        
    def set_status(self, stat):
        '''load an image representing a status and store it on cache'''
        if stat not in status.ALL:
            return

        self.status = stat

        if stat not in self.cache_imgs:
            gtk_img = utils.safe_gtk_image_load(\
                gui.theme.status_icons[stat])
            self.cache_imgs[stat] = gtk_img
        else:
            gtk_img = self.cache_imgs[stat]

        self.set_image(gtk_img)
