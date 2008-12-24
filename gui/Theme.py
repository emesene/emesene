import os

import protocol.status as status

class Theme(object):
    '''this class contains all the paths and information regarding a theme'''
    # if you add a smilie key twice you will have a nice stack overflow :D
    EMOTES = {}
    EMOTES[':)'] = 'face-smile'
    EMOTES[';)'] = 'face-wink'
    EMOTES['|-)'] = 'face-tired'
    EMOTES[':D'] = 'face-laugh'
    EMOTES[':d'] = EMOTES[':D'] 
    EMOTES[':S'] = 'face-worried'
    EMOTES[':s'] = EMOTES[':S'] 
    EMOTES[':('] = 'face-sad'
    EMOTES['(K)'] = 'face-kiss'
    EMOTES['(k)'] = EMOTES['(K)'] 
    EMOTES[':P'] = 'face-raspberry'
    EMOTES[':p'] = EMOTES[':P'] 
    EMOTES[':|'] = 'face-plain'
    EMOTES[':/'] = 'face-uncertain'
    EMOTES[':O'] = 'face-surprise'
    EMOTES[':o'] = EMOTES[':O'] 
    EMOTES[':$'] = 'face-embarrassed'
    EMOTES[':\'('] = 'face-crying'
    EMOTES[':@'] = 'face-angry'
    EMOTES['(6)'] = 'face-devilish'
    EMOTES['(A)'] = 'face-angel'
    EMOTES['(a)'] = EMOTES['(A)'] 
    EMOTES['+o('] = 'face-sick'

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
        self.connect = os.path.join(self.theme_path, "connect.png")
        self.group_chat = os.path.join(self.theme_path, "group-chat.png")
        self.typing = os.path.join(self.theme_path, "typing.png")
        self.new_message = os.path.join(self.theme_path, "new-message.png")

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

        self.emote_path = os.path.join('themes', 'emotes', 'default')

    def emote_to_path(self, shortcut):
        '''return a string representing the path to load the emote if it exist
        None otherwise'''

        if shortcut not in Theme.EMOTES:
            return None

        path = os.path.join(self.emote_path, Theme.EMOTES[shortcut]) + '.png'

        if os.access(path, os.R_OK) and os.path.isfile(path):
            return path

        return None

