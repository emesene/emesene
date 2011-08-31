# -*- coding: utf-8 -*-

#    This file is part of emesene.
#
#    emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
import re
import gtk
import glib
import urllib

import stock
import utils
import gui
import extension
import e3

class Conversation(gtk.VBox, gui.Conversation):
    '''a widget that contains all the components inside'''
    NAME = 'Conversation'
    DESCRIPTION = 'The widget that displays a conversation'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, session, cid, update_win, tab_label, members=None):
        '''constructor'''
        gtk.VBox.__init__(self)
        gui.Conversation.__init__(self, session, cid, update_win, members)
        self.set_border_width(2)

        self.tab_label = tab_label

        self._header_visible = session.config.b_show_header
        self._image_visible = session.config.b_show_info
        self._toolbar_visible = session.config.b_show_toolbar
        self.avatar_box_is_hidden = False

        self.panel = gtk.VPaned()

        self.show_avatar_in_taskbar = self.session.config.get_or_set('b_show_avatar_in_taskbar', True)

        Header = extension.get_default('conversation header')
        OutputText = extension.get_default('conversation output')
        InputText = extension.get_default('conversation input')
        ContactInfo = extension.get_default('conversation info')
        ConversationToolbar = extension.get_default(
            'conversation toolbar')
        TransfersBar = extension.get_default('filetransfer pool')
        CallWidget = extension.get_default('call widget')
        dialog = extension.get_default('dialog')
        Avatar = extension.get_default('avatar')

        avatar_size = self.session.config.get_or_set('i_conv_avatar_size', 64)

        self.avatarBox = gtk.EventBox()
        self.avatarBox.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.avatarBox.connect('button-press-event', self._on_avatar_click)

        self.avatar = Avatar(cell_dimension=avatar_size)
        self.avatarBox.add(self.avatar)

        self.avatarBox.set_tooltip_text(_('Click here to set your avatar'))
        self.avatarBox.set_border_width(4)

        self.his_avatarBox = gtk.EventBox()
        self.his_avatarBox.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.his_avatarBox.connect('button-press-event', self._on_his_avatar_click)

        self.his_avatar = Avatar(cell_dimension=avatar_size)
        self.his_avatarBox.add(self.his_avatar)

        self.his_avatarBox.set_tooltip_text(_('Click to see informations'))
        self.his_avatarBox.set_border_width(4)

        self.header = Header(session, members)
        toolbar_handler = gui.base.ConversationToolbarHandler(self.session,
            dialog, gui.theme, self)
        self.toolbar = ConversationToolbar(toolbar_handler)
        self.toolbar.set_property('can-focus', False)
        self.output = OutputText(self.session.config, self.steal_emoticon_cb)
        self.output.set_size_request(-1, 30)
        self.input = InputText(self.session, self._on_send_message,
                self.cycle_history, self.on_drag_data_received)
        self.output.set_size_request(-1, 25)
        self.input.set_size_request(-1, 25)
        self.info = ContactInfo()
        self.transfers_bar = TransfersBar(self.session)
        self.call_widget = CallWidget(self.session)

        frame_input = gtk.Frame()
        frame_input.set_shadow_type(gtk.SHADOW_IN)

        input_box = gtk.VBox()
        input_box.pack_start(self.toolbar, False)
        input_box.pack_start(self.input, True, True)

        frame_input.add(input_box)

        self.panel.pack1(self.output, True, False)
        self.panel.pack2(frame_input, False, False)

        self.panel_signal_id = self.panel.connect_after('expose-event',
                self.update_panel_position)
        self.panel.connect('button-release-event', self.on_input_panel_resize)

        self.hbox = gtk.HBox()
        if self.session.config.get_or_set('b_avatar_on_left', False):
            self.hbox.pack_start(self.info, False)
            self.hbox.pack_start(self.panel, True, True)
        else:
            self.hbox.pack_start(self.panel, True, True)
            self.hbox.pack_start(self.info, False)

        self.pack_start(self.header, False)
        self.pack_start(self.hbox, True, True)
        self.pack_start(self.transfers_bar, False)

        if len(self.members) == 0:
            self.header.information = ('connecting', 'creating conversation')

        last_avatar = self.session.config.last_avatar
        if self.session.config_dir.file_readable(last_avatar):
            my_picture = last_avatar
        else:
            my_picture = gui.theme.image_theme.user

        his_picture = gui.theme.image_theme.user
        if members:
            account = members[0]
            contact = self.session.contacts.get(account)

            if contact:
                if contact.picture:
                    his_picture = contact.picture
                self.output.clear(account, contact.nick,
                         contact.display_name, his_picture, my_picture)

        self.info.first = self.his_avatarBox
        self.his_avatar.set_from_file(his_picture)

        self.info.last = self.avatarBox
        self.avatar.set_from_file(my_picture)

        self._load_style()

        self.subscribe_signals()

        self.tab_index = -1 # used to select an existing conversation
        self.index = 0 # used for the rotate picture function
        self.rotate_started = False
        self.timer = 0

        if self.is_group_chat:
            self.rotate_started = True #to prevents more than one timeout_add
            self.timer = glib.timeout_add_seconds(5, self.rotate_picture)

    def _on_avatar_click(self, widget, data):
        '''method called when user click on his avatar
        '''
        av_chooser = extension.get_default('avatar chooser')(self.session)
        av_chooser.set_modal(True)
        av_chooser.show()

    def steal_emoticon_cb(self, path_uri):
        '''receives the path or the uri for the emoticon to be added'''
        if path_uri.startswith("file://"):
            path_uri = path_uri[7:]
            path_uri = urllib.url2pathname(path_uri)
        directory = os.path.dirname(path_uri).lower()
        caches = e3.cache.CacheManager(self.session.config_dir.base_dir)
        emcache = caches.get_emoticon_cache(self.session.account.account)
        dialog = extension.get_default('dialog')

        if directory.endswith(gui.theme.emote_theme.path.lower()):
            dialog.information(_("Can't add, default emoticon"))
        elif directory == emcache.path.lower():
            dialog.information(_("Can't add, own emoticon"))
        else:
            def on_response(response, shortcut):
                if response == stock.ACCEPT:
                    shortcut = dialog.entry.get_text()
                    if shortcut not in emcache.list():
                        self.emcache.insert((shortcut, path_uri))
                    # TODO: check if the file's hash is not already on the cache
                    else:
                        dialog.information(_("Shortcut already in use"))

            matches = re.search(r'<img src="' + path_uri + \
                '" alt="(?P<alt>\S*)" name="(?P<name>\w*)"',
                self.output.view.text)
            groupdict = {'alt': ''} if not matches else matches.groupdict()
            dialog = dialog.entry_window(
                        _("Type emoticon's shortcut: "), groupdict['alt'],
                        on_response, _("Choose custom emoticon's shortcut"))
            dialog.entry.set_max_length(7)
            dialog.show()

    def _on_his_avatar_click(self, widget, data):
        '''method called when user click on the other avatar
        '''
        account = self.members[self.index - 1]
        contact = self.session.contacts.get(account)
        dialog = extension.get_default('dialog')
        dialog.contact_information_dialog(self.session, contact.account)

    def _on_icon_size_change(self, value):
        '''callback called when config.b_toolbar_small changes'''
        self.toolbar.draw()

    def _on_avatarsize_changed(self, value):
        '''callback called when config.i_conv_avatar_size changes'''

        self.avatarBox.remove(self.avatar)
        self.his_avatarBox.remove(self.his_avatar)

        self.avatar.set_property('dimension',value)
        self.his_avatar.set_property('dimension',value)

        self.avatarBox.add(self.avatar)
        self.his_avatarBox.add(self.his_avatar)

    def _on_show_toolbar_changed(self, value):
        '''callback called when config.b_show_toolbar changes'''
        if value:
            self.toolbar.show()
        else:
            self.toolbar.hide()

    def _on_show_header_changed(self, value):
        '''callback called when config.b_show_header changes'''
        if value:
            self.header.show()
        else:
            self.header.hide()

    def _on_show_info_changed(self, value):
        '''callback called when config.b_show_info changes'''
        if value:
            self.info.show()
        else:
            self.info.hide()

    def _on_show_avatar_onleft(self,value):
        '''callback called when config.b_avatar_on_left changes'''
        if value:
            self.hbox.reorder_child(self.panel, 1)
            self.hbox.reorder_child(self.info, 0)
        else:
            self.hbox.reorder_child(self.panel, 0)
            self.hbox.reorder_child(self.info, 1)

    def on_close(self):
        '''called when the conversation is closed'''
        self.unsubscribe_signals()

        #stop the group chat image rotation timer, if it's started
        if self.rotate_started:
            glib.source_remove(self.timer)

        #stop the avatars animation...if any..
        self.avatar.stop()
        self.his_avatar.stop()

        self.destroy()

    def show(self, other_started=False):
        '''override the show method'''
        gtk.VBox.show(self)

        if self.session.config.b_show_header:
            self.header.show_all()

        self.info.show_all()
        if not self.session.config.b_show_info:
            self.info.hide()

        self.hbox.show()
        self.panel.show_all()

        if not other_started:
            self.input_grab_focus()

        if not self.session.config.b_show_toolbar:
            self.toolbar.hide()

    def input_grab_focus(self):
        '''
        sets the focus on the input widget
        '''
        self.input.grab_focus()

    def update_panel_position(self, *args):
        """update the panel position to be on the 80% of the height
        """
        height = self.panel.get_allocation().height
        if height > 0:
            pos = self.session.config.get_or_set("i_input_panel_position",
                    int(height*0.8))
            self.panel.set_position(pos)
            self.panel.disconnect(self.panel_signal_id)
            del self.panel_signal_id

    def on_input_panel_resize(self, *args):
        pos = self.panel.get_position()
        self.session.config.i_input_panel_position = pos

    def update_message_waiting(self, is_waiting):
        """
        update the information on the conversation to inform if a message
        is waiting

        is_waiting -- boolean value that indicates if a message is waiting
        """
        self.update_tab()

    def update_single_information(self, nick, message, account):
        """
        update the information for a conversation with a single user

        nick -- the nick of the other account (escaped)
        message -- the message of the other account (escaped)
        account -- the account
        """
        self.header.information = (message, account)
        self.update_tab()

    def show_tab_menu(self):
        '''callback called when the user press a button over a widget
        chek if it's the right button and display the menu'''
        pass

    def update_tab(self):
        '''update the values of the tab'''
        self.tab_label.set_image(self.icon)
        self.tab_label.set_text(self.text)

        if self.show_avatar_in_taskbar:
            self.update_window(self.text, self.his_avatar.filename, self.tab_index)
        else:
            self.update_window(self.text, self.icon, self.tab_index)

    def update_group_information(self):
        """
        update the information for a conversation with multiple users
        """
        if not self.rotate_started:
            self.rotate_started = True
            self.timer = glib.timeout_add_seconds(5, self.rotate_picture)

        #TODO add plus support for nick to the tab label!
        members_nick = []
        i = 0
        for account in self.members:
            i += 1
            contact = self.session.contacts.get(account)

            if contact is None or contact.nick is None:
                nick = account
            elif len(contact.nick) > 20 and i != len(self.members):
                nick = contact.nick[:20] + '...'
            else:
                nick = contact.nick

            members_nick.append(nick)

        self.header.information = \
            (_('%d members') % (len(self.members) + 1, ),
                    ", ".join(members_nick))
        self.update_tab()

    def set_sensitive(self, is_sensitive):
        """
        used to make the conversation insensitive while the conversation
        is still open while the user is disconnected and to set it back to
        sensitive when the user is reconnected
        """
        self.input.set_sensitive(is_sensitive)
        self.toolbar.set_sensitive(is_sensitive)
        self.avatarBox.set_sensitive(is_sensitive)
        self.his_avatarBox.set_sensitive(is_sensitive)

    def set_image_visible(self, is_visible):
        """
        set the visibility of the widget that displays the images of the members

        is_visible -- boolean that says if the widget should be shown or hidden
        """
        if is_visible:
            self.info.show()
        else:
            self.info.hide()

    def set_header_visible(self, is_visible):
        '''
        hide or show the widget according to is_visible

        is_visible -- boolean that says if the widget should be shown or hidden
        '''
        if is_visible:
            self.header.show()
        else:
            self.header.hide()

    def set_toolbar_visible(self, is_visible):
        '''
        hide or show the widget according to is_visible

        is_visible -- boolean that says if the widget should be shown or hidden
        '''
        if is_visible:
            self.toolbar.show()
        else:
            self.toolbar.hide()

    def rotate_picture(self):
        '''change the account picture in a multichat
           conversation every 5 seconds'''
        def increment():
            if self.index < len(self.members) - 1 :
                self.index += 1
            else:
                self.index = 0

        if len(self.members) == 1:
            self.index = 0
            glib.source_remove(self.timer)
            self.rotate_started = False
        elif self.index >= len(self.members):
            self.index = 0
        contact = self.session.contacts.get(self.members[self.index])

        if contact is None:
            increment()
            return True

        path = contact.picture

        if path != '':
            self.his_avatar.set_from_file(path)

        increment()
        return True

    def get_preview(self, completepath):
        return utils.makePreview(completepath)

    def on_user_typing(self, account):
        """
        inform that the other user has started typing
        """
        if account in self.members:
            self.tab_label.set_image(gui.theme.image_theme.typing)
            glib.timeout_add_seconds(3, self.update_tab)

    def on_emote(self, emote):
        '''called when an emoticon is selected'''
        self.input.append(glib.markup_escape_text(emote))
        self.input_grab_focus()

    def on_picture_change_succeed(self, account, path):
        '''callback called when the picture of an account is changed'''
        if account == self.session.account.account:
            self.avatar.set_from_file(path)
        elif account in self.members:
            self.his_avatar.set_from_file(path)

    def on_toggle_avatar(self):
        '''hide or show the avatar bar'''
        if self.avatar_box_is_hidden:
            self.avatarBox.show()
            self.his_avatarBox.show()
        else:
            self.avatarBox.hide()
            self.his_avatarBox.hide()
        self.avatar_box_is_hidden = not self.avatar_box_is_hidden

    def on_contact_attr_changed_succeed(self, account, what, old,
            do_notify=True):
        ''' called when contacts change their attributes'''
        if account in self.members and what in ('status', 'nick'):
            self.update_tab()

    def on_filetransfer_invitation(self, transfer, cid):
        ''' called when a new file transfer is issued '''
        if cid == self.cid:
            self.transfers_bar.add(transfer)

    def on_filetransfer_accepted(self, transfer):
        ''' called when the file transfer is accepted '''
        if transfer in self.transfers_bar.transfers:
            self.transfers_bar.accepted(transfer)

        if transfer.contact.account == self.members[0]:
            contact = self._member_to_contact(self.members[0])
            message = e3.base.Message(e3.base.Message.TYPE_MESSAGE, \
            _('File transfer accepted by %s') % (contact.display_name), \
            transfer.contact.account)
            self.output.information(self.formatter, contact, message)

    def on_filetransfer_progress(self, transfer):
        ''' called every chunk received '''
        if transfer in self.transfers_bar.transfers:
            self.transfers_bar.update(transfer)

    def on_filetransfer_rejected(self, transfer):
        ''' called when a file transfer is rejected '''
        if transfer in self.transfers_bar.transfers:
            self.transfers_bar.update(transfer)

        if transfer.contact.account == self.members[0]:
            contact = self._member_to_contact(self.members[0])
            message = e3.base.Message(e3.base.Message.TYPE_MESSAGE, \
            _('File transfer rejected by %s') % (contact.display_name), \
            transfer.contact.account)
            self.output.information(self.formatter, contact, message)

    def on_filetransfer_canceled(self, transfer):
        ''' called when a file transfer is canceled '''
        if transfer in self.transfers_bar.transfers:
            self.transfers_bar.canceled(transfer)

        if transfer.contact.account == self.members[0]:
            contact = self._member_to_contact(self.members[0])
            message = e3.base.Message(e3.base.Message.TYPE_MESSAGE, \
            _('File transfer canceled by %s') % (contact.display_name), \
            transfer.contact.account)
            self.output.information(self.formatter, contact, message)

    def on_filetransfer_completed(self, transfer):
        ''' called when a file transfer is completed '''
        if transfer in self.transfers_bar.transfers:
            self.transfers_bar.finished(transfer)

        if transfer.contact.account == self.members[0]:
            contact = self._member_to_contact(self.members[0])
            message = e3.base.Message(e3.base.Message.TYPE_MESSAGE, \
            _('File transfer completed!'), transfer.contact.account)
            self.output.information(self.formatter, contact, message)

    def on_call_invitation(self, call, cid, westart=False):
        '''called when a new call is issued both from us or other party'''
        if cid == self.cid:
            self.call_widget.add_call(call, westart)
            self.call_widget.show_all_widgets()
            self.call_widget.set_xids()

    def on_video_call(self):
        '''called when the user is requesting a video-only call'''
        account = self.members[0]
        self.call_widget.show_all()
        x_other, x_self = self.call_widget.get_xids()
        self.session.call_invite(self.cid, account, 0, x_other, x_self) # 0 = Video only

    def on_voice_call(self):
        '''called when the user is requesting an audio-only call'''
        account = self.members[0]
        self.call_widget.show_all()
        x_other, x_self = self.call_widget.get_xids()
        self.session.call_invite(self.cid, account, 1, x_other, x_self) # 1 = Audio only

    def on_av_call(self):
        '''called when the user is requesting an audio-video call'''
        account = self.members[0]
        self.call_widget.show_all()
        x_other, x_self = self.call_widget.get_xids()
        self.session.call_invite(self.cid, account, 2, x_other, x_self) # 2 = Audio/Video

    def on_drag_data_received(self, widget, context, posx, posy,\
                          selection, info, timestamp):
        '''called when a file is received by text input widget'''
        uri = selection.data.strip()
        uri_splitted = uri.split()
        for uri in uri_splitted:
            path = self.__get_file_path_from_dnd_dropped_uri(uri)
            if os.path.isfile(path):
                filename = os.path.basename(path)
                self.on_filetransfer_invite(filename, path)

    def __get_file_path_from_dnd_dropped_uri(self, uri):
        '''Parses an URI received from dnd and return the real path'''

        if os.name != 'nt':
            path = urllib.url2pathname(uri) # escape special chars
        else:
            path = urllib.unquote(uri) # escape special chars
        path = path.strip('\r\n\x00') # remove \r\n and NULL

        # get the path to file
        if re.match('^file:///[a-zA-Z]:/', path): # windows
            path = path[8:] # 8 is len('file:///')
        elif path.startswith('file://'): # nautilus, rox
            path = path[7:] # 7 is len('file://')
        elif path.startswith('file:'): # xffm
            path = path[5:] # 5 is len('file:')
        return path

