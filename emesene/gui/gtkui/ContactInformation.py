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
import gtk
import time
import pango
import datetime

import e3
import gui
import utils
import extension
import gobject
import Renderers

import logging
log = logging.getLogger('gtkui.ContactInformation')

from IconView import IconView

class ContactInformation(gtk.Window, gui.base.ContactInformation):
    '''a window that displays information about a contact'''

    def __init__(self, session, account):
        '''constructor'''
        gui.base.ContactInformation.__init__(self, session, account)
        gtk.Window.__init__(self)
        self.set_default_size(640, 350)
        self.set_title(_('Contact information (%s)') % (account,))
        self.set_role("dialog")
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)

        self.tabs = gtk.Notebook()

        self._create_tabs()
        self.tabs.show_all()

        self.add(self.tabs)

        self.fill_all()

    def _create_tabs(self):
        '''create all the tabs on the window'''
        self.info = InformationWidget(self.session, self.account)
        self.nicks = ListWidget(self.session, self.account)

        self.avatar_manager = gui.base.AvatarManager(self.session)
 
        account_path = self.avatar_manager.get_contact_avatars_dir(self.account)

        self.avatars = IconView(_('Avatar history'), [account_path], 
                        None, None, IconView.TYPE_SELF_PICS)
        self.messages = ListWidget(self.session, self.account)
        self.status = ListWidget(self.session, self.account)
        self.chats = ChatWidget(self.session, self.account)

        self.tabs.append_page(self.info, gtk.Label(_('Information')))
        self.tabs.append_page(self.nicks, gtk.Label(_('Nick history')))
        self.tabs.append_page(self.avatars, gtk.Label(_('Avatar history')))
        self.tabs.append_page(self.messages, gtk.Label(_('Message history')))
        self.tabs.append_page(self.status, gtk.Label(_('Status history')))
        self.tabs.append_page(self.chats, gtk.Label(_('Chat history')))

    def add_nick(self, stat, timestamp, nick):
        '''add a nick to the list of nicks'''
        self.nicks.add(stat, timestamp, nick)

    def add_message(self, stat, timestamp, message):
        '''add a message to the list of message'''
        self.messages.add(stat, timestamp, message)

    def add_status(self, stat, timestamp, status):
        '''add a status to the list of status'''
        self.status.add(stat, timestamp, status)


class InformationWidget(gtk.VBox):
    '''shows information about the contact'''

    def __init__(self, session, account):
        '''constructor'''
        gtk.VBox.__init__(self)
        self.set_border_width(2)

        self.session = session
        if self.session:
            self.contact = self.session.contacts.get(account)
        else:
            self.contact = None

        self.nick = Renderers.SmileyLabel()
        self.nick.set_alignment(0.0, 0.5)
        self.nick.set_ellipsize(pango.ELLIPSIZE_END)
        self.mail = gtk.Label()
        self.mail.set_alignment(0.0, 0.5)
        self.mail.set_ellipsize(pango.ELLIPSIZE_END)
        self.message = Renderers.SmileyLabel()
        self.message.set_ellipsize(pango.ELLIPSIZE_END)
        self.message.set_alignment(0.0, 0.5)
        self.status = gtk.Image()
        self.status.set_alignment(0.0, 0.5)
        self.image = gtk.Image()
        image_align = gtk.Alignment(0.5,0.5)
        image_align.add(self.image)
        self.blocked = gtk.Label()
        self.blocked.set_alignment(0.0, 0.5)
        self.blocked.set_ellipsize(pango.ELLIPSIZE_END)

        table = gtk.Table(4, 2, False)
        table.set_border_width(20)
        table.set_row_spacings(10)
        table.set_col_spacings(10)

        l_image = gtk.Label(_('Image'))
        l_image.set_alignment(0.0, 0.5)
        l_nick = gtk.Label(_('Nick'))
        l_nick.set_alignment(0.0, 0.5)
        l_mail = gtk.Label(_('E-Mail'))
        l_mail.set_alignment(0.0, 0.5)
        l_status = gtk.Label(_('Status'))
        l_status.set_alignment(0.0, 0.5)
        l_message = gtk.Label(_('Message'))
        l_message.set_alignment(0.0, 0.5)
        l_blocked = gtk.Label(_('Blocked'))
        l_blocked.set_alignment(0.0, 0.5)

        table.attach(l_nick, 0, 1, 0, 1, 0)
        table.attach(self.nick, 1, 2, 0, 1)
        table.attach(l_mail, 0, 1, 1, 2, 0)
        table.attach(self.mail, 1, 2, 1, 2)
        table.attach(l_status, 0, 1, 2, 3, 0)
        table.attach(self.status, 1, 2, 2, 3)
        table.attach(l_message, 0, 1, 3, 4, 0)
        table.attach(self.message, 1, 2, 3, 4)
        table.attach(l_blocked, 0, 1, 4, 5, 0)
        table.attach(self.blocked, 1, 2, 4, 5)

        hbox = gtk.HBox(False, 0)
        self.set_border_width(15)
        hbox.pack_start(image_align, False, False)
        hbox.pack_start(table, True, True)

        self.pack_start(hbox, False, False)

        self.update_information()

    def update_information(self):
        '''update the information of the contact'''
        if self.contact:
            if self.contact.display_name == self.contact.nick:
                self.nick.set_markup(Renderers.msnplus_to_list(
                        gobject.markup_escape_text(self.contact.display_name)))
            else:
                self.nick.set_markup(Renderers.msnplus_to_list(
                        gobject.markup_escape_text(self.contact.nick
                            + ' (' + self.contact.display_name + ')')))
            self.mail.set_markup(self.contact.account)
            self.message.set_markup(Renderers.msnplus_to_list(
                    gobject.markup_escape_text(self.contact.message)))
            self.status.set_from_file(
                gui.theme.status_icons[self.contact.status])
            if (self.contact.picture):
                self.image.set_from_file(self.contact.picture)
            else:
                self.image.set_from_file(gui.theme.user)
            if (self.contact.blocked):
                self.blocked.set_markup(_('Yes'))
            else:
                self.blocked.set_markup(_('No'))


class ListWidget(gtk.VBox):
    '''a widget that displays the history of some information with status,
    date and the information provided'''

    def __init__(self, session, account):
        '''constructor'''
        gtk.VBox.__init__(self)
        self.set_border_width(2)

        self.session = session
        if self.session:
            self.contact = self.session.contacts.get(account)

        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll.set_shadow_type(gtk.SHADOW_IN)

        self.model = gtk.ListStore(gtk.gdk.Pixbuf, str, str)
        self.list = gtk.TreeView(self.model)
        column = gtk.TreeViewColumn()
        column.set_expand(False)
        column1 = gtk.TreeViewColumn()
        column1.set_expand(False)
        column2 = gtk.TreeViewColumn()
        column2.set_expand(True)

        crt = Renderers.CellRendererPlus()
        crt_timestamp = gtk.CellRendererText()
        crt.set_property('ellipsize', pango.ELLIPSIZE_END)
        pbr = gtk.CellRendererPixbuf()

        self.list.append_column(column)
        self.list.append_column(column1)
        self.list.append_column(column2)
        self.list.set_headers_visible(False)

        column.pack_start(pbr, False)
        column1.pack_start(crt_timestamp, False)
        column2.pack_start(crt, True)

        column.add_attribute(pbr, 'pixbuf', 0)
        column1.add_attribute(crt_timestamp, 'text', 1)
        column2.add_attribute(crt, 'markup', 2)

        scroll.add(self.list)

        self.pack_start(scroll, True, True)

    def add(self, stat, timestamp, text):
        '''add a row to the widget'''
        pix = utils.safe_gtk_pixbuf_load(gui.theme.status_icons[stat])
        date_text = time.strftime('%c', time.gmtime(timestamp))
        self.model.append((pix, date_text, text))

class ChatWidget(gtk.VBox):
    '''a widget that displays the history of nicks'''

    def __init__(self, session, account):
        '''constructor'''
        gtk.VBox.__init__(self)
        self.set_border_width(2)
        all = gtk.HBox()
        all.set_border_width(2)
        self.first = True

        self.calendars = gtk.VBox()
        self.calendars.set_border_width(2)

        chat_box = gtk.VBox()
        chat_box.set_border_width(2)

        self.session = session
        self.account = account

        if self.session:
            self.contact = self.session.contacts.get(account)

        OutputText = extension.get_default('conversation output')
        self.text = OutputText(session.config)
        self.formatter = e3.common.MessageFormatter(session.contacts.me)

        buttons = gtk.HButtonBox()
        buttons.set_border_width(2)
        buttons.set_layout(gtk.BUTTONBOX_END)
        save = gtk.Button(stock=gtk.STOCK_SAVE)
        refresh = gtk.Button(stock=gtk.STOCK_REFRESH)

        toggle_calendars = gtk.Button(_("Hide calendars"))

        buttons.pack_start(toggle_calendars)
        buttons.pack_start(refresh)
        buttons.pack_start(save)

        self.from_calendar = gtk.Calendar()
        from_year, from_month, from_day = self.from_calendar.get_date()
        from_datetime = datetime.date(from_year, from_month + 1,
                from_day) - datetime.timedelta(30)

        self.from_calendar.select_month(from_datetime.month - 1,
                from_datetime.year)
        self.from_calendar.select_day(from_datetime.day)
        self.to_calendar = gtk.Calendar()

        save.connect('clicked', self._on_save_clicked)
        refresh.connect('clicked', self._on_refresh_clicked)
        toggle_calendars.connect('clicked', self._on_toggle_calendars)

        self.calendars.pack_start(gtk.Label(_('Chats from')), False)
        self.calendars.pack_start(self.from_calendar, True, True)
        self.calendars.pack_start(gtk.Label(_('Chats to')), False)
        self.calendars.pack_start(self.to_calendar, True, True)

        chat_box.pack_start(self.text, True, True)

        all.pack_start(self.calendars, False)
        all.pack_start(chat_box, True, True)

        self.pack_start(all, True, True)
        self.pack_start(buttons, False)
        self.refresh_history()

    def _on_toggle_calendars(self, button):
        '''called when the toogle_calendars button is clicked
        '''
        if self.calendars.get_property('visible'):
            button.set_label(_('Show calendars'))
            self.calendars.hide()
        else:
            button.set_label(_('Hide calendars'))
            self.calendars.show()

    def _on_save_clicked(self, button):
        '''called when the save button is clicked'''
        def save_cb(response, filename=None):
            '''called when the closes the save dialog'''
            if filename is not None and response == gui.stock.SAVE:
                self.save_chats(filename)

        home = os.path.expanduser('~')
        dialog = extension.get_default('dialog')
        dialog.save_as(home, save_cb)

    def _on_refresh_clicked(self, button):
        '''called when the refresh button is clicked'''
        self.refresh_history()

    def refresh_history(self):
        '''refresh the history according to the values on the calendars
        '''
        if self.contact:
            his_picture = self.contact.picture or utils.path_to_url(os.path.abspath(gui.theme.user))
            my_picture = self.session.contacts.me.picture or utils.path_to_url(os.path.abspath(gui.theme.user))
            self.text.clear(self.account, self.contact.nick, self.contact.display_name, my_picture, his_picture)
        else:
            self.text.clear()
        self.request_chats_between(1000, self._on_chats_ready)

    def request_chats_between(self, limit, callback):
        from_year, from_month, from_day = self.from_calendar.get_date()
        from_t = time.mktime(datetime.date(from_year, from_month + 1,
            from_day).timetuple())

        to_year, to_month, to_day = self.to_calendar.get_date()
        to_t = time.mktime((datetime.date(to_year, to_month + 1,
            to_day) + datetime.timedelta(1)).timetuple())

        self.session.logger.get_chats_between(self.account,
            self.session.account.account, from_t, to_t, limit, callback)

    def save_chats(self, path, limit=1000):
        '''request amount of messages between our account and the current
        account, save it to path'''
        def _on_save_chats_ready(results):
            '''called when the chats requested are ready
            '''
            if not results:
                return

            exporter = extension.get_default('history exporter')
            exporter(results, open(path, "w"))

        self.request_chats_between(limit, _on_save_chats_ready)

    def _on_chats_ready(self, results):
        '''called when the chat history is ready'''
        if not results:
            return

        for stat, timestamp, msg_text, nick, account in results:

            contact = founded_account = self.session.contacts.get(account)

            if contact == None:
                contact = e3.Contact(account, nick=nick)

            is_me = self.session.contacts.me.account == account
            datetimestamp = datetime.datetime.fromtimestamp(timestamp)

            if is_me:
                self.text.send_message(self.formatter, contact,
                        msg_text, None, None, None, self.first)
            else:
                message = e3.Message(e3.Message.TYPE_MESSAGE, msg_text,
                            account, timestamp=datetimestamp)

                self.text.receive_message(self.formatter, contact, message,
                        None, None, self.first)

            self.first = False

