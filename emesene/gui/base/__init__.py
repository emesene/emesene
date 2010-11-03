from Theme import Theme
from Handler import *
from Message import Message
from ContactList import ContactList
from Conversation import Conversation
from ConversationManager import ConversationManager
from AvatarManager  import AvatarManager
from PictureHandler import PictureHandler

theme = Theme()

import stock
import extension
import e3

def play(session, sound):
    """play a sound if the contact is not busy"""
    play = extension.get_default('sound')
    if session.contacts.me.status != e3.status.BUSY and not \
       session.config.b_mute_sounds:
        play(sound)

