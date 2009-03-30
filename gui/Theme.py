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
    EMOTES['*-)'] = 'face-uncertain'
    EMOTES[':O'] = 'face-surprise'
    EMOTES[':o'] = EMOTES[':O'] 
    EMOTES[':$'] = 'face-embarrassed'
    EMOTES[':\'('] = 'face-crying'
    EMOTES[':@'] = 'face-angry'
    EMOTES['(6)'] = 'face-devilish'
    EMOTES['(A)'] = 'face-angel'
    EMOTES['(a)'] = EMOTES['(A)'] 
    #EMOTES['<:o)'] = ''
    EMOTES['(ap)'] = 'airplane'
    EMOTES['(au)'] = 'car'
    #EMOTES['8o|'] = ''
    EMOTES['(b)'] = 'beer'
    EMOTES['(^)'] = 'cake'
    EMOTES['(bah)'] = 'sheep'
    EMOTES['(nah)'] = 'goat'
    EMOTES['(||)'] = 'bowl'
    EMOTES['(z)'] = 'boy'
    EMOTES['(u)'] = 'love-over'
    EMOTES['(p)'] = 'camera'
    EMOTES['(@)'] = 'cat'
    EMOTES['(ci)'] = 'cigarette'
    EMOTES['(o)'] = 'clock'
    EMOTES['(c)'] = 'coffe'
    EMOTES['(co)'] = 'computer'
    EMOTES['(&)'] = 'dog'
    #EMOTES[':-#'] = ''
    EMOTES['(d)'] = 'drink'
    EMOTES['(e)'] = 'mail'
    #EMOTES['8-)'] = ''
    EMOTES['(~)'] = 'video'
    #EMOTES['(yn)'] = ''
    EMOTES['(g)'] = 'present'
    EMOTES['(x)'] = 'girl'
    EMOTES['(%)'] = 'handcuffs'
    EMOTES['(h5)'] = 'hifive'
    #EMOTES['(h)'] = ''
    EMOTES[':^)'] = EMOTES[':o']
    EMOTES['(ip)'] = 'island'
    EMOTES['({)'] = 'hughleft'
    EMOTES['(i)'] = 'lamp'
    EMOTES['(li)'] = 'c10ud'
    EMOTES['(m)'] = 'msn'
    EMOTES['(mp)'] = 'mobile'
    EMOTES['(mo)'] = 'coins'
    EMOTES['(8)'] = 'music'
    EMOTES['(pi)'] = 'pizza'
    EMOTES['(pl)'] = 'plate'
    EMOTES['(r)'] = 'rainbow'
    EMOTES['(st)'] = 'rain'
    EMOTES['(l)'] = 'love'
    EMOTES['(k)'] = 'face-kiss'
    EMOTES['(f)'] = 'rose'
    EMOTES['(})'] = 'hughright'
    #EMOTES['^o)'] = ''
    EMOTES[':-*'] = 'secret'
    EMOTES['(S)'] = 'moon'
    EMOTES['(sn)'] = 'snail'
    EMOTES['(so)'] = 'soccerball'
    EMOTES['(*)'] = 'star'
    EMOTES['(#)'] = 'sun'
    EMOTES['(t)'] = 'phone'
    EMOTES['(n)'] = 'bad'
    EMOTES['(y)'] = 'good'
    EMOTES['(tu)'] = 'turtle'
    EMOTES['(um)'] = 'umbrella'
    EMOTES[':-['] = 'bat'
    EMOTES['(w)'] = 'rose-dead'
    EMOTES['(xx)'] = 'console'

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
        self.chat = os.path.join(self.theme_path, "chat.png")
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

