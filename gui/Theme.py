import os
import protocol.base.status as status

class Theme(object):
    '''this class contains all the paths and information regarding a theme'''

    def __init__(self, name="default"):
        '''class constructor'''
        self.set_theme(name)

    def set_theme(self, name):
        '''set the theme name and change all the paths to reflect the change'''
        self.name = name

        self.theme_path = os.path.join("themes", self.name)

        self.user = os.path.join(self.theme_path, "user.png")
        self.users = os.path.join(self.theme_path, "users.png")
        self.password = os.path.join(self.theme_path, "password.png")
        self.logo = os.path.join(self.theme_path, "logo.png")

        self.status_icons = {}
        self.status_icons[status.ONLINE] = \
            os.path.join(self.theme_path, "online.png")
        self.status_icons[status.OFFLINE] = \
            os.path.join(self.theme_path, "offline.png")
        self.status_icons[status.BUSY] = \
            os.path.join(self.theme_path, "busy.png")
        self.status_icons[status.AWAY] = \
            os.path.join(self.theme_path, "away.png")
        self.status_icons[status.IDLE] = \
            os.path.join(self.theme_path, "idle.png")

