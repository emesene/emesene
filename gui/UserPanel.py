import protocol.status as status
import protocol.Object as Object
import protocol.validator as validator

class UserPanel(Object.Object):
    '''this class represents a component that allows the user to change all his
    personal information'''

    def __init__(self, contacts, dialog):
        '''class constructor'''
        Object.Object.__init__(self)

        self.contacts = contacts
        self.dialog = dialog

        self.signal_add('nick-changed', 1)
        self.signal_add('message-changed', 1)
        self.signal_add('status-changed', 1)
        self.signal_add('image-changed', 1)

    def on_nick_changed(self, old_nick, new_nick):
        '''method called when the nick is changed on the component,
        call the library to set the nick'''

        if new_nick and old_nick != new_nick:
            self.contacts.set_nick(new_nick)

    def on_status_changed(self, old_status, new_status):
        '''method called when the status is changed on the component,
        call the library to set the status'''

        if old_status != new_status and new_status in status.ALL:
            self.contacts.set_status(new_status)

    def on_message_changed(self, old_message, new_message):
        '''method called when the message is changed on the component,
        call the library to set the message'''

        if old_message != new_message:
            self.contacts.set_message(new_message)

    def on_image_changed(self, old_path, new_path):
        '''method called when the image is changed on the component,
        call the library to set the image'''

        if old_path != new_path and validator.readable(new_path):
            self.contacts.set_picture(new_path)

