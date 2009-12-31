import os
import gtk
import time
import pango
import datetime

import e3
import gui
import utils
import extension

import logging
log = logging.getLogger('gtkui.ContactInformation')

class ContactInformation(gtk.Window):
    '''a window that displays information about a contact'''

    def __init__(self, session, account):
        '''constructor'''
        gtk.Window.__init__(self)
        self.set_default_size(640, 350)
        self.set_title('Contact information (%s)' % (account,))
        self.set_role("dialog")
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        self.set_icon(utils.safe_gtk_image_load(gui.theme.logo).get_pixbuf())

        self.session = session
        self.account = account

        self.tabs = gtk.Notebook()

        self._create_tabs()
        self.tabs.show_all()

        self.add(self.tabs)

        if self.session:
            self.fill_nicks()
            self.fill_status()
            self.fill_messages()

    def fill_nicks(self):
        '''fill the nick history (clear and refill if called another time)'''
        self.session.logger.get_nicks(self.account, 1000, self._on_nicks_ready)

    def fill_messages(self):
        '''fill the messages history (clear and refill if called another time)
        '''
        self.session.logger.get_messages(self.account, 1000,
            self._on_messages_ready)

    def fill_status(self):
        '''fill the status history (clear and refill if called another time)'''
        self.session.logger.get_status(self.account, 1000,
            self._on_status_ready)

    def fill_chats(self):
        '''fill the chats history (clear and refill if called another time)'''
        self.session.logger.get_chats(self.account,
            self.session.account.account, 1000, self.chats._on_chats_ready)

    def _create_tabs(self):
        '''create all the tabs on the window'''
        self.info = InformationWidget(self.session, self.account)
        self.nicks = ListWidget(self.session, self.account)
        self.messages = ListWidget(self.session, self.account)
        self.status = ListWidget(self.session, self.account)
        self.chats = ChatWidget(self.session, self.account)

        self.tabs.append_page(self.info, gtk.Label('Information'))
        self.tabs.append_page(self.nicks, gtk.Label('Nick history'))
        self.tabs.append_page(self.messages, gtk.Label('Message history'))
        self.tabs.append_page(self.status, gtk.Label('Status history'))
        self.tabs.append_page(self.chats, gtk.Label('Chat history'))

    def _on_nicks_ready(self, results):
        '''called when the nick history is ready'''
        for (stat, timestamp, nick) in results:
            self.nicks.add(stat, timestamp, nick)

    def _on_messages_ready(self, results):
        '''called when the message history is ready'''
        for (stat, timestamp, message) in results:
            self.messages.add(stat, timestamp, message)

    def _on_status_ready(self, results):
        '''called when the status history is ready'''
        for (stat, timestamp, stat_) in results:
            self.status.add(stat, timestamp, e3.status.STATUS.get(stat,
                'unknown'))

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

        self.nick = gtk.Label()
        self.nick.set_ellipsize(pango.ELLIPSIZE_END)
        self.message = gtk.Label()
        self.message.set_ellipsize(pango.ELLIPSIZE_END)
        self.status = gtk.Image()
        self.image = gtk.Image()

        table = gtk.Table(4, 2, True)
        table.set_border_width(20)
        table.set_row_spacings(10)
        table.set_col_spacings(10)

        l_image = gtk.Label('Image')
        l_image.set_alignment(0.0, 0.5)
        l_nick = gtk.Label('Nick')
        l_nick.set_ellipsize(pango.ELLIPSIZE_END)
        l_nick.set_alignment(0.0, 0.5)
        l_status = gtk.Label('Status')
        l_status.set_alignment(0.0, 0.5)
        l_message = gtk.Label('Message')
        l_message.set_alignment(0.0, 0.5)
        l_message.set_ellipsize(pango.ELLIPSIZE_END)

        table.attach(l_image, 0, 1, 0, 1)
        table.attach(self.image, 1, 2, 0, 1)
        table.attach(l_nick, 0, 1, 1, 2)
        table.attach(self.nick, 1, 2, 1, 2)
        table.attach(l_status, 0, 1, 2, 3)
        table.attach(self.status, 1, 2, 2, 3)
        table.attach(l_message, 0, 1, 3, 4)
        table.attach(self.message, 1, 2, 3, 4)

        self.pack_start(table, False, False)

        self.update_information()

    def update_information(self):
        '''update the information of the contact'''
        if self.contact:
            self.nick.set_markup(self.contact.display_name)
            self.message.set_markup(self.contact.message)
            self.status.set_from_file(
                gui.theme.status_icons[self.contact.status])
            self.image.set_from_file(gui.theme.user)


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

        crt = gtk.CellRendererText()
        crt_timestamp = gtk.CellRendererText()
        crt.set_property('ellipsize', pango.ELLIPSIZE_END)
        pbr = gtk.CellRendererPixbuf()
        pbr_status = gtk.CellRendererPixbuf()

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

        toggle_calendars = gtk.Button("Hide calendars")

        buttons.pack_start(toggle_calendars)
        buttons.pack_start(refresh)
        buttons.pack_start(save)

        self.from_calendar = gtk.Calendar()
        from_year, from_month, from_day = self.from_calendar.get_date()

        if from_month == 0:
            from_month = 11
            from_year -= 1
        else:
            from_month -= 1

        self.from_calendar.select_month(from_month, from_year)
        self.to_calendar = gtk.Calendar()

        save.connect('clicked', self._on_save_clicked)
        refresh.connect('clicked', self._on_refresh_clicked)
        toggle_calendars.connect('clicked', self._on_toggle_calendars)

        self.calendars.pack_start(gtk.Label('Chats from:'), False)
        self.calendars.pack_start(self.from_calendar, True, True)
        self.calendars.pack_start(gtk.Label('Chats to:'), False)
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
            button.set_label('Show calendars')
            self.calendars.hide()
        else:
            button.set_label('Hide calendars')
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
            exporter = extension.get_default('history exporter')
            exporter(results, path)

        self.request_chats_between(limit, _on_save_chats_ready)

    def _on_chats_ready(self, results):
        '''called when the chat history is ready'''
        for (stat, timestamp, message, nick) in results:
            date_text = time.strftime('[%c]', time.gmtime(timestamp))
            tokens = message.split('\r\n', 3)
            type_ = tokens[0]

            if type_ == 'text/x-msnmsgr-datacast':
                self.text.append(date_text + ' ' + nick + ': ' + '<i>nudge</i><br/>')
            elif type_.find('text/plain;') != -1:
                try:
                    (type_, format, empty, text) = tokens
                    self.text.append(self.formatter.format_history(
                        date_text, nick, text))
                except ValueError:
                    log.debug('Invalid number of tokens' + str(tokens))
            else:
                log.debug('unknown message type on ContactInfo')

