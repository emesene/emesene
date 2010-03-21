import gtk

import gui
import utils

import TextField
import StatusButton

import extension

class UserPanel(gtk.VBox):
    '''a panel to display and manipulate the user information'''
    NAME = 'User Panel'
    DESCRIPTION = 'A widget to display/modify the account information on the main window'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, session):
        '''constructor'''
        gtk.VBox.__init__(self)

        self.session = session
        self.config_dir = session.config_dir
        self._enabled = True
        
        Avatar = extension.get_default('avatar')
        AvatarManager = extension.get_default('avatar manager')

        self.avatar = Avatar(cellDimention=32)

        self.avatarBox = gtk.EventBox()
        self.avatarBox.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.avatarBox.connect('button-press-event', self.on_avatar_click)
        self.avatarBox.add(self.avatar)
        self.avatarBox.set_tooltip_text(_('Click here to set your avatar'))

        self.avatar_path = self.session.config.last_avatar
        self.avatar_manager = AvatarManager(self.session)

        if not self.session.config_dir.file_readable(self.avatar_path):
            path = gui.theme.user
        else:
            path = self.avatar_path
        self.avatar.set_from_file(path)

        self.nick = TextField.TextField(session.contacts.me.display_name, '', False)
        self.status = StatusButton.StatusButton(session)
        self.status.set_status(session.contacts.me.status)
        self.search = gtk.ToggleButton()
        self.search.set_image(gtk.image_new_from_stock(gtk.STOCK_FIND,
            gtk.ICON_SIZE_MENU))
        self.search.set_relief(gtk.RELIEF_NONE)

        self.message = TextField.TextField(session.contacts.me.message,
            '<span style="italic">&lt;Click here to set message&gt;</span>',
            True)
        self.toolbar = gtk.HBox()

        hbox = gtk.HBox()
        hbox.pack_start(self.avatarBox, False)

        vbox = gtk.VBox()
        nick_hbox = gtk.HBox()
        nick_hbox.pack_start(self.nick, True, True)
        nick_hbox.pack_start(self.search, False)
        vbox.pack_start(nick_hbox, False)
        message_hbox = gtk.HBox()
        message_hbox.pack_start(self.message, True, True)
        message_hbox.pack_start(self.status, False)
        vbox.pack_start(message_hbox, False)

        hbox.pack_start(vbox, True, True)

        self.pack_start(hbox, True, True)
        self.pack_start(self.toolbar, False)

        hbox.show()
        nick_hbox.show()
        message_hbox.show()
        vbox.show()

        session.signals.message_change_succeed.subscribe(
            self.on_message_change_succeed)
        session.signals.media_change_succeed.subscribe(
            self.on_media_change_succeed)
        session.signals.status_change_succeed.subscribe(
            self.on_status_change_succeed)
        session.signals.contact_list_ready.subscribe(
            self.on_contact_list_ready)
        session.signals.picture_change_succeed.subscribe(
            self.on_picture_change_succeed)
        session.signals.profile_get_succeed.subscribe(
                self.on_profile_update_succeed)
        session.signals.profile_set_succeed.subscribe(
                self.on_profile_update_succeed)

    def show(self):
        '''override show'''
        gtk.VBox.show(self)
        self.avatar.show()
        self.avatarBox.show()
        self.nick.show()
        self.message.show()
        self.status.show()
        self.search.show()
        self.toolbar.show()

    def show_all(self):
        '''override show_all'''
        self.show()

    def _set_enabled(self, value):
        '''set the value of enabled and modify the widgets to reflect the status
        '''
        self.nick.enabled = value
        self.message.enabled = value
        self.status.set_sensitive(value)
        self.search.set_sensitive(value)
        self._enabled = value

    def _get_enabled(self):
        '''return the value of the enabled property
        '''
        return self._enabled

    enabled = property(fget=_get_enabled, fset=_set_enabled)

    def on_status_change_succeed(self, stat):
        '''callback called when the status has been changed successfully'''
        self.status.set_status(stat)

    def on_message_change_succeed(self, message):
        '''callback called when the message has been changed successfully'''
        self.message.text = message

    def on_media_change_succeed(self, message):
        '''callback called when the message has been changed successfully'''
        self.message.text = message

    def on_contact_list_ready(self):
        '''callback called when the contact list is ready to be used'''
        self.enabled = True

    def on_picture_change_succeed(self, account, path):
        '''callback called when the picture of an account is changed'''
        # out account
        if account == self.session.account.account:
            self.avatar.set_from_file(path)

    def on_profile_update_succeed(self, nick, message):
        '''method called when information about our profile is obtained
        '''
        self.nick.text = nick
        self.message.text = message

    def on_avatar_click(self, widget, data):
        '''method called when user click on his avatar
        '''
        def set_picture_cb(response, filename):
            '''callback for the avatar chooser'''
            if _av_chooser is not None:
                _av_chooser.stop_and_clear()
            if response == gui.stock.ACCEPT:
                self.avatar_manager.set_as_avatar(filename)

        # Directory for user's avatars
        path_dir = self.avatar_manager.get_avatars_dir()                   

        # Directory for contact's cached avatars
        cached_avatar_dir = self.avatar_manager.get_cached_avatars_dir()
                   
        # Directories for System Avatars
        faces_paths = self.avatar_manager.get_system_avatars_dirs()

        _av_chooser = extension.get_default('avatar chooser')(set_picture_cb,
                                                self.avatar_path, path_dir,
                                                cached_avatar_dir, faces_paths,
                                                self.avatar_manager)
        _av_chooser.show()

