import gtk

import gui
import utils
import protocol.status as status

class StatusButton(gtk.Button):
    '''a button that when clicked displays a popup that allows the user to
    select a status'''

    def __init__(self, session=None):
        gtk.Button.__init__(self)
        self.session = session
        # a cache of gtk.Images to not load the images everytime we change
        # our status
        self.cache_imgs = {}

        self.set_status(status.ONLINE)
        self.set_relief(gtk.RELIEF_NONE)
        self.set_border_width(0)
        self.menu = gui.components.build_status_menu(self._on_status_selected)
        self.gtk_menu = self.menu.build_as_popup()

        self.connect('clicked', self._on_clicked)

    def _on_clicked(self, button):
        '''callback called when the button is clicked'''
        self.gtk_menu.popup(None, None, None, 0, 0)

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
