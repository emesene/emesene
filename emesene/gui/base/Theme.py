import os
import re

import AdiumThemes
import e3
from e3 import status

class Theme(object):
    '''this class contains all the paths and information regarding a theme'''
    # if you add a smilie key twice you will have a nice stack overflow :D
    EMOTES = {}
    EMOTES[':)'] = 'face-smile'
    EMOTES[':-)'] = EMOTES[':)']
    EMOTES[';)'] = 'face-wink'
    EMOTES[';-)'] = EMOTES[';)']
    EMOTES['|-)'] = 'face-tired'
    EMOTES[':D'] = 'face-laugh'
    EMOTES[':d'] = EMOTES[':D']
    EMOTES[':-D'] = EMOTES[':D']
    EMOTES[':S'] = 'face-worried'
    EMOTES[':s'] = EMOTES[':S']
    EMOTES[':('] = 'face-sad'
    EMOTES[':-('] = EMOTES[':(']
    EMOTES['(K)'] = 'face-kiss'
    EMOTES['(k)'] = EMOTES['(K)']
    EMOTES[':P'] = 'face-raspberry'
    EMOTES[':p'] = EMOTES[':P']
    EMOTES[':-P'] = EMOTES[':P']
    EMOTES[':-p'] = EMOTES[':P']
    EMOTES[':|'] = 'face-plain'
    EMOTES[':-|'] = EMOTES[':|']
    EMOTES['*-)'] = 'face-uncertain'
    EMOTES[':O'] = 'face-surprise'
    EMOTES[':o'] = EMOTES[':O']
    EMOTES[':-o'] = EMOTES[':O']
    EMOTES[':-O'] = EMOTES[':O']
    EMOTES[':$'] = 'face-embarrassed'
    EMOTES[':\'('] = 'face-crying'
    EMOTES[':@'] = 'face-angry'
    EMOTES[':-@'] = EMOTES[':@']
    EMOTES['(6)'] = 'face-devilish'
    EMOTES['(A)'] = 'face-angel'
    EMOTES['(a)'] = EMOTES['(A)']
    #EMOTES['<:o)'] = ''
    EMOTES['(ap)'] = 'airplane'
    EMOTES['(au)'] = 'car'
    #EMOTES['8o|'] = ''
    EMOTES['(b)'] = 'beer'
    EMOTES['(B)'] = EMOTES['(b)']
    EMOTES['(^)'] = 'cake'
    EMOTES['(bah)'] = 'sheep'
    EMOTES['(nah)'] = 'goat'
    EMOTES['(||)'] = 'bowl'
    EMOTES['(z)'] = 'boy'
    EMOTES['(Z)'] = EMOTES['(z)']
    EMOTES['(u)'] = 'love-over'
    EMOTES['(U)'] = EMOTES['(u)']
    EMOTES['(p)'] = 'camera'
    EMOTES['(P)'] = EMOTES['(p)']
    EMOTES['(@)'] = 'cat'
    EMOTES['(ci)'] = 'cigarette'
    EMOTES['(o)'] = 'clock'
    EMOTES['(O)'] = EMOTES['(o)']
    EMOTES['(c)'] = 'coffee'
    EMOTES['(C)'] = EMOTES['(c)']
    EMOTES['(co)'] = 'computer'
    EMOTES['(&)'] = 'dog'
    #EMOTES[':-#'] = ''
    EMOTES['(d)'] = 'drink'
    EMOTES['(D)'] = EMOTES['(d)']
    EMOTES['(e)'] = 'mail'
    EMOTES['(E)'] = EMOTES['(e)']
    #EMOTES['8-)'] = ''
    EMOTES['(~)'] = 'video'
    #EMOTES['(yn)'] = ''
    EMOTES['(g)'] = 'present'
    EMOTES['(G)'] = EMOTES['(g)']
    EMOTES['(x)'] = 'girl'
    EMOTES['(X)'] = EMOTES['(x)']
    EMOTES['(%)'] = 'handcuffs'
    EMOTES['(h5)'] = 'hifive'
    #EMOTES['(h)'] = ''
    #EMOTES[':^)'] = ''
    EMOTES['(ip)'] = 'island'
    EMOTES['({)'] = 'hughleft'
    EMOTES['(i)'] = 'lamp'
    EMOTES['(I)'] = EMOTES['(i)']
    EMOTES['(li)'] = 'c10ud'
    EMOTES['(m)'] = 'msn'
    EMOTES['(M)'] = EMOTES['(m)']
    EMOTES['(mp)'] = 'mobile'
    EMOTES['(mo)'] = 'coins'
    EMOTES['(8)'] = 'music'
    EMOTES['(pi)'] = 'pizza'
    EMOTES['(pl)'] = 'plate'
    EMOTES['(r)'] = 'rainbow'
    EMOTES['(R)'] = EMOTES['(r)']
    EMOTES['(st)'] = 'rain'
    EMOTES['(l)'] = 'love'
    EMOTES['(L)'] = EMOTES['(l)']
    EMOTES['(k)'] = 'face-kiss'
    EMOTES['(K)'] = EMOTES['(k)']
    EMOTES['(f)'] = 'rose'
    EMOTES['(F)'] = EMOTES['(f)']
    EMOTES['(})'] = 'hughright'
    #EMOTES['^o)'] = ''
    EMOTES[':-*'] = 'secret'
    EMOTES['(S)'] = 'moon'
    EMOTES['(sn)'] = 'snail'
    EMOTES['(so)'] = 'soccerball'
    EMOTES['(*)'] = 'star'
    EMOTES['(#)'] = 'sun'
    EMOTES['(t)'] = 'phone'
    EMOTES['(T)'] = EMOTES['(t)']
    EMOTES['(n)'] = 'bad'
    EMOTES['(N)'] = EMOTES['(n)']
    EMOTES['(y)'] = 'good'
    EMOTES['(Y)'] = EMOTES['(y)']
    EMOTES['(tu)'] = 'turtle'
    EMOTES['(um)'] = 'umbrella'
    EMOTES[':-['] = 'bat'
    EMOTES[':['] = EMOTES[':-[']
    EMOTES['(w)'] = 'rose-dead'
    EMOTES['(W)'] = EMOTES['(w)']
    EMOTES['(xx)'] = 'console'

    EMOTE_REGEX_STR = ""
    for key in EMOTES:
        EMOTE_REGEX_STR += re.escape(key) + "|"
    EMOTE_REGEX = re.compile(EMOTE_REGEX_STR)

    SOUND_FILES = ['alert.wav', 'nudge.wav', 'offline.wav', 'online.wav',
            'send.wav', 'type.wav']
    EMOTE_FILES = ['airplane.png', 'bad.png', 'bat.png', 'beer.png', 'bomb.png',
        'bowl.png', 'boy.png', 'bunny.png', 'c10ud.png', 'cake.png',
        'camera.png', 'can.png', 'car.png', 'cat.png', 'cigarette.png',
        'clock.png', 'clown.png', 'coffee.png', 'coins.png', 'computer.png',
        'console.png', 'cow.png', 'dog.png', 'drink.png', 'face-angel.png',
        'face-angry.png', 'face-crying.png', 'face-devilish.png',
        'face-embarrassed.png', 'face-kiss.png', 'face-laugh.png',
        'face-plain.png', 'face-raspberry.png', 'face-sad.png', 'face-sick.png',
        'face-smile.png', 'face-surprise.png', 'face-tired.png',
        'face-uncertain.png', 'face-wink.png', 'face-worried.png', 'ghost.png',
        'girl.png', 'goat.png', 'good.png', 'handcuffs.png', 'hifive.png',
        'hugleft.png', 'hugright.png', 'island.png', 'lamp.png',
        'love-over.png', 'love.png', 'mail.png', 'mobile.png', 'moon.png',
        'msn.png', 'music.png', 'phone.png', 'pizza.png', 'plate.png',
        'present.png', 'rainbow.png', 'rain.png', 'rose-dead.png', 'rose.png',
        'secret.png', 'sheep.png', 'snail.png', 'soccerball.png', 'star.png',
        'sun.png', 'turtle.png', 'tv.png', 'umbrella.png', 'video.png']
    IMAGE_FILES = ['away.png', 'busy.png', 'chat.png', 'connect.png',
        'group-chat.png', 'idle.png', 'logo.png', 'new-message.png',
        'offline.png', 'online.png', 'password.png', 'typing.png', 'user.png',
        'users.png']

    def __init__(self, image_name="default", emote_name="default",
            sound_name="default", conv_name='renkoo.AdiumMessageStyle'):
        '''class constructor'''
        self.set_theme(image_name, emote_name, sound_name, conv_name)

    def set_theme(self, image_name, emote_name, sound_name, conv_name):
        '''set the theme name and change all the paths to reflect the change'''
        self.image_name = image_name
        self.emote_name = emote_name
        self.sound_name = sound_name
        # conv_name is the name of the selected adium conversation theme
        self.conv_name = conv_name

        self.theme_path = os.path.join("themes", "images", self.image_name)
        self.conv_themes_path = os.path.join(os.getcwd(), "themes", "conversations")
        self.conv_themes = AdiumThemes.get_instance()
        self.conv_themes.add_themes_path(self.conv_themes_path)

        for elem in self.conv_themes.list():
            if conv_name in elem:
                self.adium_theme_path = elem

        self.conv_theme = self.conv_themes.get(self.adium_theme_path)[1]

        self.sound_theme_path = os.path.join("themes", "sounds",
                self.sound_name)

        self.user = os.path.join(self.theme_path, "user.png")
        self.users = os.path.join(self.theme_path, "users.png")
        self.password = os.path.join(self.theme_path, "password.png")
        self.logo = os.path.join(self.theme_path, "logo.png")
        self.throbber = os.path.join(self.theme_path, "throbber.gif")
        self.connect = os.path.join(self.theme_path, "connect.png")
        self.chat = os.path.join(self.theme_path, "chat.png")
        self.group_chat = os.path.join(self.theme_path, "group-chat.png")
        self.typing = os.path.join(self.theme_path, "typing.png")
        self.new_message = os.path.join(self.theme_path, "new-message.png")

        self.sound_alert = os.path.join(self.sound_theme_path, "alert.wav")
        self.sound_nudge = os.path.join(self.sound_theme_path, "nudge.wav")
        self.sound_offline = os.path.join(self.sound_theme_path, "offline.wav")
        self.sound_online = os.path.join(self.sound_theme_path, "online.wav")
        self.sound_send = os.path.join(self.sound_theme_path, "send.wav")
        self.sound_type = os.path.join(self.sound_theme_path, "type.wav")

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

        self.status_icons_panel = {}
        self.panel_path = self.theme_path
        # allow different icons for indicators/tray icons
        # note: a panel subdirectory requires six pics: 
        #logo.png, online.png, offline.png, busy.png, away.png, idle.png
        panel_path = os.path.join(self.theme_path, "panel")        
        if os.path.exists(panel_path):
            self.panel_path = panel_path
            self.status_icons_panel[status.ONLINE] = \
                os.path.join(self.panel_path, "online.png")
            self.status_icons_panel[status.OFFLINE] = \
                os.path.join(self.panel_path, "offline.png")
            self.status_icons_panel[status.BUSY] = \
                os.path.join(self.panel_path, "busy.png")
            self.status_icons_panel[status.AWAY] = \
                os.path.join(self.panel_path, "away.png")
            self.status_icons_panel[status.IDLE] = \
                os.path.join(self.panel_path, "idle.png")
        else:
            self.status_icons_panel = self.status_icons.copy()
            
        self.emote_path = os.path.join('themes', 'emotes', self.emote_name)

    def emote_to_path(self, shortcut, remove_protocol=False):
        '''return a string representing the path to load the emote if it exist
        None otherwise'''

        if shortcut not in Theme.EMOTES:
            return None

        path = os.path.join(self.emote_path, Theme.EMOTES[shortcut]) + '.png'
        path = os.path.abspath(path)

        if os.access(path, os.R_OK) and os.path.isfile(path):
            if remove_protocol:
                return path
            else:
                return 'file://' + path

        return None

    def get_emotes_count(self):
        '''return the number of emoticons registered'''
        return len(set(Theme.EMOTES.values()))


    def is_valid_theme(self, file_list, path):
        """
        return True if the path contains a valid theme
        """

        for file_name in file_list:
            if not os.path.isfile(os.path.join(path, file_name)):
                return False

        return True

    def get_image_themes(self):
        '''return a list of names for the image themes'''
        themes = []

        for theme in self.get_child_dirs(os.path.join('themes', 'images')):
            if self.is_valid_theme(Theme.IMAGE_FILES,
                    os.path.join('themes', 'images', theme)):
                themes.append(theme)

        return themes

    def get_emote_themes(self):
        '''return a list of names for the emote themes'''
        themes = []

        for theme in self.get_child_dirs(os.path.join('themes', 'emotes')):
            if self.is_valid_theme(Theme.EMOTE_FILES,
                    os.path.join('themes', 'emotes', theme)):
                themes.append(theme)

        return themes

    def get_sound_themes(self):
        '''return a list of names for the sound themes'''
        themes = []

        for theme in self.get_child_dirs(os.path.join('themes', 'sounds')):
            if self.is_valid_theme(Theme.SOUND_FILES,
                    os.path.join('themes', 'sounds', theme)):
                themes.append(theme)

        return themes

    def get_adium_themes(self):
        '''return a list of validated adium themes'''
        themes = []
        AdiumThemesM = AdiumThemes.AdiumThemes()
        path_conv = os.path.join('themes', 'conversations')

        for theme in self.get_child_dirs(path_conv):
            if AdiumThemesM.validate(
                                os.path.join(os.path.abspath(path_conv), theme))[0]:
                theme = theme.replace('.AdiumMessageStyle', '')
                themes.append(theme)

        return themes

    def get_child_dirs(self, dir_path):
        '''return a list of dirs inside a given path'''
        try:
            return os.walk(dir_path).next()[1]
        except StopIteration:
            return ()

    def split_smilies(self, text):
        '''split text in smilies, return a list of tuples that contain
        a boolean as first item indicating if the text is an emote or not
        and the text as second item.
        example : [(False, "hi! "), (True, ":)")]
        '''
        keys = Theme.EMOTES.keys()
        return [(item in keys, item) for item in Theme.EMOTE_REGEX.split(text)
                if item is not None]

