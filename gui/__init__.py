from Theme import Theme
from Signal import Signal
from Signals import Signals
from Conversation import Conversation
from ConversationManager import ConversationManager

theme = Theme()

import extension
import protocol

def play(session, sound):
    """play a sound if the contact is not busy"""
    play = extension.get_default('sound')
    if session.contacts.me.status != protocol.status.BUSY and \
            session.config.b_play_nudge:
        play(sound)

def notify(title, message, image_path=None):
    """notify the user with message"""
    notification = extension.get_default('notification')
    if notification is not None:
        notification(title, message, image_path)
