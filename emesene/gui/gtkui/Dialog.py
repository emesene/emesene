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

'''a module that defines the api of objects that display dialogs'''

import traceback

import os
import gtk
import pango
import gobject
import webbrowser
import tempfile

import e3
import gui
import utils
import stock
import extension

import ContactInformation

import logging
log = logging.getLogger('gtkui.Dialog')

class Dialog(object):
    '''a class full of static methods to handle dialogs, dont instantiate it'''
    NAME = 'Dialog'
    DESCRIPTION = 'Class to show all the dialogs of the application'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    @classmethod
    def window_add_image(cls, window, stock_id):
        '''add a stock image as the first element of the window.hbox'''
        image = gtk.image_new_from_stock(stock_id, gtk.ICON_SIZE_DIALOG)
        alignment = gtk.Alignment(xalign=0.0, yalign=0.1)
        alignment.add(image)
        window.hbox.pack_start(alignment, False)
        alignment.show_all()

        return image

    @classmethod
    def window_add_button(cls, window, stock_id, label=''):
        '''add a button to the window'''

        button = gtk.Button(label, stock=stock_id)
        window.bbox.pack_start(button, True, True)
        button.show()

        return button

    @classmethod
    def window_add_label(cls, window, text):
        '''add a label with the text (as pango) on the window'''

        label = gtk.Label()
        #label.set_selectable(True)
        label.set_use_markup(True)
        label.set_markup('<span>' + \
            text + "</span>")
        window.hbox.pack_start(label, True, True)
        label.show()

        return label

    @classmethod
    def window_add_label_vbox(cls, window, text):
        '''add a label with the text (as pango) on the window'''

        label = gtk.Label()
        label.set_selectable(True)
        label.set_use_markup(True)
        label.set_markup('<span>' + \
            text + "</span>")
        window.vbox.pack_start(label, True, True)
        label.show()

        return label

    @classmethod
    def close_cb(cls, widget, event, window, response_cb, *args):
        '''default close callback, call response_cb with args if it's not
        None'''

        if response_cb:
            response_cb(*args)

        window.hide()

    @classmethod
    def default_cb(cls, widget, window, response_cb, *args):
        '''default callbacks, call response_cb with args if it's not
        None'''

        if response_cb:
            response_cb(*args)

        window.hide()

    @classmethod
    def on_file_click_cb(cls, widget, window, response_cb):
        response_cb(gtk.STOCK_OPEN, widget.get_filename())
        window.hide()

    @classmethod
    def chooser_cb(cls, widget, window, response_cb, response):
        '''callback user for dialogs that contain a chooser, return the
        status and the selected file'''
        filename = window.chooser.get_filename()

        if response_cb:
            response_cb(response, filename)

        window.hide()

    @classmethod
    def entry_cb(cls, widget, window, response_cb, *args):
        '''callback called when the entry is activated, it call the response
        callback with the stock.ACCEPT and append the value of the entry
        to args'''
        args = list(args)
        args.append(window.entry.get_text())

        if response_cb:
            if type(widget) == gtk.Entry:
                response_cb(stock.ACCEPT, *args)
            else:
                response_cb(*args)

        window.hide()

    @classmethod
    def add_contact_cb(cls, widget, window, response_cb, response):
        '''callback called when a button is selected on the add_contact
        dialog'''
        contact = window.entry.get_text()
        group = window.combo.get_model().get_value(
            window.combo.get_active_iter(), 0)

        window.hide()
        response_cb(response, contact, group)

    @classmethod
    def common_window(cls, message, stock_id, response_cb, title, *args):
        '''create a window that displays a message with a stock image'''
        window = cls.new_window(title, response_cb, *args)
        cls.window_add_image(window, stock_id)
        cls.window_add_label(window, message)

        return window

    @classmethod
    def message_window(cls, message, stock_id, response_cb, title):
        '''create a window that displays a message with a stock image
        and a close button'''
        window = cls.common_window(message, stock_id, response_cb, title)
        cls.add_button(window, gtk.STOCK_CLOSE, stock.CLOSE, response_cb,
            cls.default_cb)
        window.set_modal(True)
        return window

    @classmethod
    def entry_window(cls, message, text, response_cb, title, *args):
        '''create a window that contains a label and a entry with text set
        and selected, and two buttons, accept, cancel'''
        window = cls.new_window(title, response_cb, stock.CANCEL, *args)
        cls.window_add_label(window, message)

        entry = gtk.Entry()
        entry.set_text(text)
        entry.select_region(0, -1)

        entry.connect('activate', cls.entry_cb, window, response_cb, *args)

        window.hbox.pack_start(entry, True, True)
        cls.add_button(window, gtk.STOCK_OK, stock.ACCEPT, response_cb,
            cls.entry_cb, *args)
        cls.add_button(window, gtk.STOCK_CANCEL, stock.CANCEL, response_cb,
            cls.entry_cb, *args)

        setattr(window, 'entry', entry)

        entry.show()

        return window

    @classmethod
    def add_button(cls, window, gtk_stock, stock_id, response_cb,
        callback, *args):
        '''add a button and connect the signal'''
        button = gtk.Button(stock=gtk_stock)
        window.bbox.pack_start(button, True, True)
        button.connect('clicked', callback, window, response_cb,
            stock_id, *args)

        button.show()

        return button

    @classmethod
    def new_window(cls, title, response_cb=None, *args):
        '''build a window with the default values and connect the common
        signals, return the window'''

        window = gtk.Window()
        window.set_title(title)
        window.set_role("dialog")
        window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        window.set_default_size(150, 100)
        window.set_position(gtk.WIN_POS_CENTER)
        window.set_border_width(8)

        vbox = gtk.VBox(spacing=4)
        hbox = gtk.HBox(spacing=4)
        bbox = gtk.HButtonBox()
        bbox.set_spacing(4)
        bbox.set_layout(gtk.BUTTONBOX_END)

        vbox.pack_start(hbox, True, True)
        vbox.pack_start(bbox, False)

        window.add(vbox)

        setattr(window, 'vbox', vbox)
        setattr(window, 'hbox', hbox)
        setattr(window, 'bbox', bbox)

        args = list(args)
        args.insert(0, stock.CLOSE)
        window.connect('delete-event', cls.close_cb, window,
            response_cb, *args)

        vbox.show_all()

        return window

    @classmethod
    def save_as(cls, current_path, response_cb, title=_("Save as")):
        '''show a save as dialog with the current directory set to path.
        the buttons should display a cancel and save buttons.
         the posible reasons are stock.CANCEL, stock.SAVE and stock.CLOSE'''
        window = cls.new_window(title, response_cb)
        window.set_default_size(640, 480)
        chooser = gtk.FileChooserWidget(gtk.FILE_CHOOSER_ACTION_SAVE)
        chooser.set_current_folder(current_path)
        setattr(window, 'chooser', chooser)
        window.hbox.pack_start(chooser)
        cls.add_button(window, gtk.STOCK_CANCEL, stock.CANCEL, response_cb,
            cls.chooser_cb)
        cls.add_button(window, gtk.STOCK_SAVE, stock.SAVE, response_cb,
            cls.chooser_cb)

        window.show_all()

    @classmethod
    def choose_file(cls, current_path, response_cb, title=_("Choose file")):
        '''show a choose dialog with the current directory set to path.
        the buttons should display a cancel and save buttons.
         the posible reasons are stock.CANCEL, stock.SAVE and stock.CLOSE'''
        window = cls.new_window(title, response_cb)
        window.set_default_size(640, 480)
        chooser = gtk.FileChooserWidget(gtk.FILE_CHOOSER_ACTION_OPEN)
        chooser.set_current_folder(current_path)
        setattr(window, 'chooser', chooser)
        window.hbox.pack_start(chooser)
        chooser.connect("file-activated", cls.on_file_click_cb, window, response_cb)
        cls.add_button(window, gtk.STOCK_CANCEL, stock.CANCEL, response_cb,
            cls.chooser_cb)
        cls.add_button(window, gtk.STOCK_OPEN, stock.OPEN, response_cb,
            cls.chooser_cb)

        window.show_all()

    @classmethod
    def error(cls, message, response_cb=None, title=_("Error!")):
        '''show an error dialog displaying the message, this dialog should
        have only the option to close and the response callback is optional
        since in few cases one want to know when the error dialog was closed,
        but it can happen, so return stock.CLOSE to the callback if its set'''
        cls.message_window(message, gtk.STOCK_DIALOG_ERROR, response_cb,
            title).show()

    @classmethod
    def exc_error(cls, message, response_cb=None, title=_("Error!")):
        '''show an error dialog displaying the message and the traceback;
        this dialog should have only the option to close and the response 
        callback is optional since in few cases one want to know when the error
        dialog was closed, but it can happen, so return stock.CLOSE to the 
        callback if its set'''
        #cls.message_window('%s\n\n%s' % (message, traceback.format_exc()),
        #        gtk.STOCK_DIALOG_ERROR, response_cb, title).show()
        window = gtk.Window()
        vbox = gtk.VBox()
        text = gtk.Label(message)
        vbox.pack_start(text)
        hide_button = gtk.ToggleButton(_('Show details'))
        trace = gtk.Label(traceback.format_exc())
        def on_hide(*args):
            if hide_button.get_active(): #show
                hide_button.set_label(_('Hide details'))
                trace.show()
            else:
                hide_button.set_label(_('Show details'))
                trace.hide()
        hide_button.connect('toggled', on_hide)

        close_button = gtk.Button(stock=gtk.STOCK_OK)
        def on_ok(*args):
            window.destroy()
        close_button.connect('clicked', on_ok)
        vbox.pack_start(hide_button, False, False)
        vbox.pack_start(trace)
        vbox.pack_start(close_button, False, False)
        window.add(vbox)
        window.show_all()
        on_hide()

    @classmethod
    def warning(cls, message, response_cb=None, title=_("Warning")):
        '''show a warning dialog displaying the messge, this dialog should
        have only the option to accept, like the error dialog, the response
        callback is optional, but you have to check if it's not None and
        send the response (that can be stock.ACCEPT or stock.CLOSE, if
        the user closed the window with the x)'''
        cls.message_window(message, gtk.STOCK_DIALOG_WARNING, response_cb,
            title).show()

    @classmethod
    def information(cls, message, response_cb=None,
                            title=_("Information"),):
        '''show a warning dialog displaying the messge, this dialog should
        have only the option to accept, like the error dialog, the response
        callback is optional, but you have to check if it's not None and
        send the response (that can be stock.ACCEPT or stock.CLOSE, if
        the user closed the window with the x)'''
        cls.message_window(message, gtk.STOCK_DIALOG_INFO, response_cb,
            title).show()

    @classmethod
    def exception(cls, message, response_cb=None, title=_("Exception"),):
        '''show the message of an exception on a dialog, useful to
        connect with sys.excepthook'''
        window = cls.new_window(title, response_cb)
        label = cls.window_add_label(window, message)
        cls.add_button(window, gtk.STOCK_CLOSE, stock.CLOSE, response_cb,
            cls.default_cb)
        cls.window_add_label(window, label)

        window.show()

    @classmethod
    def yes_no(cls, message, response_cb, *args):
        '''show a confirm dialog displaying a question and two buttons:
        Yes and No, return the response as stock.YES or stock.NO or
        stock.CLOSE if the user closes the window'''
        window = cls.common_window(message, gtk.STOCK_DIALOG_QUESTION,
            response_cb, _("Confirm"), stock.NO)
        cls.add_button(window, gtk.STOCK_YES, stock.YES, response_cb,
            cls.default_cb, *args)
        cls.add_button(window, gtk.STOCK_NO, stock.NO, response_cb,
            cls.default_cb, *args)
        window.set_modal(True)
        window.show()

    @classmethod
    def yes_no_cancel(cls, message, response_cb, *args):
        '''show a confirm dialog displaying a question and three buttons:
        Yes and No and Cancel, return the response as stock.YES, stock.NO,
        stock.CANCEL or stock.CLOSE if the user closes the window'''
        window = cls.common_window(message, gtk.STOCK_DIALOG_QUESTION,
            response_cb, _("Confirm"))
        cls.add_button(window, gtk.STOCK_YES, stock.YES, response_cb,
            cls.default_cb, *args)
        cls.add_button(window, gtk.STOCK_NO, stock.NO, response_cb,
            cls.default_cb, *args)
        cls.add_button(window, gtk.STOCK_CANCEL, stock.CANCEL, response_cb,
            cls.default_cb, *args)

        window.show()

    @classmethod
    def accept_cancel(cls, message, response_cb, *args):
        '''show a confirm dialog displaying information and two buttons:
        Accept and Cancel, return stock.ACCEPT, stock.CANCEL or
        stock.CLOSE'''
        window = cls.common_window(message, gtk.STOCK_DIALOG_QUESTION,
            response_cb, _("Confirm"))
        cls.add_button(window, gtk.STOCK_OK, stock.ACCEPT, response_cb,
            cls.default_cb, *args)
        cls.add_button(window, gtk.STOCK_CANCEL, stock.CANCEL, response_cb,
            cls.default_cb, *args)

        window.show()

    @classmethod
    def contact_added_you(cls, accounts, response_cb,
                                title=_("User invitation")):
        '''show a dialog displaying information about users
        that added you to their userlists, the accounts parameter is
        a tuple of mail, nick that represent all the users that added you,
        the way you confirm (one or more dialogs) doesn't matter, but
        you should call the response callback only once with a dict
        with two keys 'accepted' and 'rejected' and a list of mail
        addresses as values
        '''    
        dialog = AddBuddy(response_cb)

        for account, nick in accounts:
            dialog.append(nick, account)

        dialog.show()

    @classmethod
    def add_contact(cls, groups, group_selected, response_cb,
        title=_("Add user")):
        '''show a dialog asking for an user address, and (optional)
        the group(s) where the user should be added, the response callback
        receives the response type (stock.ADD, stock.CANCEL or stock.CLOSE)
        the account and a tuple of group names where the user should be
        added (give a empty tuple if you don't implement this feature,
        the controls are made by the callback, you just ask for the email,
        don't make any control, you are just implementing a GUI! :P'''
        window = cls.new_window(title, response_cb)
        label = gtk.Label(_("Account"))
        label_align = gtk.Alignment(0.0, 0.5)
        label_align.add(label)
        entry = gtk.Entry()
        group_label = gtk.Label(_("Group"))
        group_label_align = gtk.Alignment(0.0, 0.5)
        group_label_align.add(group_label)
        combo = gtk.combo_box_new_text()

        combo.append_text("")

        groups = list(groups)
        groups.sort()

        selected = 0

        for (index, group) in enumerate(groups):
            combo.append_text(group.name)

            if group_selected == group.name:
                selected = index + 1

        combo.set_active(selected)

        table = gtk.Table(2, 2)
        table.attach(label_align, 0, 1, 0, 1)
        table.attach(entry, 1, 2, 0, 1)
        table.attach(group_label_align, 0, 1, 1, 2)
        table.attach(combo, 1, 2, 1, 2)
        table.set_row_spacings(2)
        table.set_col_spacings(8)

        window.hbox.pack_start(table, True, True)

        cls.add_button(window, gtk.STOCK_CANCEL, stock.CANCEL, response_cb,
            cls.add_contact_cb)
        cls.add_button(window, gtk.STOCK_OK, stock.ADD, response_cb,
            cls.add_contact_cb)

        setattr(window, 'entry', entry)
        setattr(window, 'combo', combo)

        entry.connect('activate', cls.add_contact_cb, window, response_cb,
            stock.ADD)
        window.show_all()

    @classmethod
    def add_group(cls, response_cb, title=_("Add group")):
        '''show a dialog asking for a group name, the response callback
        receives the response (stock.ADD, stock.CANCEL, stock.CLOSE)
        and the name of the group, the control for a valid group is made
        on the controller, so if the group is empty you just call the
        callback, to make a unified behaviour, and also, to only implement
        GUI logic on your code and not client logic
        cb args: response, group_name'''
        window = cls.entry_window(_("Group name"), '', response_cb, title)
        window.show()

    @classmethod
    def set_nick(cls, nick, response_cb, title=_("Change nick")):
        '''show a dialog asking for a new nick and displaying the current
        one, the response_cb receives the old nick, the new nick,
        and the response (stock.ACCEPT, stock.CANCEL or stock.CLOSE)
        cb args: response, old_nick, new_nick'''
        window = cls.entry_window(_("New nick"), nick, response_cb, title,
        nick)
        window.show()

    @classmethod
    def set_message(cls, message, response_cb,
        title=_("Change personal message")):
        '''show a dialog asking for a new personal message and displaying
        the current one, the response_cb receives the old personal message
        , the new personal message and the response
        (stock.ACCEPT, stock.CANCEL or stock.CLOSE)
        cb args: response, old_pm, new_pm'''
        window = cls.entry_window(_("New personal message"),
            message, response_cb, title, message)
        window.show()

    @classmethod
    def rename_group(cls, group, response_cb, title=_("Rename group")):
        '''show a dialog with the group name and ask to rename it, the
        response callback receives stock.ACCEPT, stock.CANCEL or stock.CLOSE
        the old and the new name.
        cb args: response, group, new_name
        '''
        window = cls.entry_window(_("New group name"), group.name, response_cb,
            title, group)
        window.show()

    @classmethod
    def set_contact_alias(cls, account, alias, response_cb,
                            title=_("Set alias")):
        '''show a dialog showing the current alias and asking for the new
        one, the response callback receives,  the response
        (stock.ACCEPT, stock.CANCEL, stock.CLEAR <- to remove the alias
        or stock.CLOSE), the account, the old and the new alias.
        cb args: response, account, old_alias, new_alias'''
        alias = alias or ''
        window = cls.entry_window(_("Contact alias"), alias, response_cb,
            title, account, alias)
        cls.add_button(window, gtk.STOCK_CLEAR, stock.CLEAR, response_cb,
            cls.entry_cb, account, alias)
        window.show()

    @classmethod
    def about_dialog(cls, name, version, copyright, comments, license, website,
        authors, translators, logo_path):
        '''show an about dialog of the application:
        * title: the title of the window
        * name: the name of the appliaction
        * version: version as string
        * copyright: the name of the copyright holder
        * comments: a description of the application
        * license: the license text
        * website: the website url
        * authors: a list or tuple of strings containing the contributors
        * translators: a string containing the translators
        '''
        def on_website_hook(dialog, web):
            '''called when the website item is selected'''
            webbrowser.open(web)

        def on_email_hook(dialog, mail):
            webbrowser.open("mailto://"+mail)

        about = gtk.AboutDialog()
        gtk.about_dialog_set_url_hook(on_website_hook)
        gtk.about_dialog_set_email_hook(on_email_hook)
        about.set_name(name)
        about.set_version(version)
        about.set_copyright(copyright)
        about.set_comments(comments)
        about.set_license(license)
        about.set_website(website)

        about.set_authors(authors)
        about.set_translator_credits(translators)
        icon = gtk.gdk.pixbuf_new_from_file(logo_path)
        about.set_logo(icon)
        about.run()
        about.hide()

    @classmethod
    def contact_information_dialog(cls, session, account):
        '''shows information about the account'''
        ContactInformation.ContactInformation(session, account).show()

    @classmethod
    def select_font(cls, style, callback):
        '''select font and if available size and style, receives a
        e3.Message.Style object with the current style
        the callback receives a new style object with the new selection
        '''
        def select_font_cb(button, window, callback, response, color_sel,
            color):
            '''callback called on button selection'''
            if response == stock.ACCEPT:
                window.hide()
                fdesc = pango.FontDescription(font_sel.get_font_name())
                style = utils.pango_font_description_to_style(fdesc)
                style.color.red = color.red
                style.color.green = color.green
                style.color.blue = color.blue
                style.color.alpha = color.alpha

                callback(style)

            window.hide()

        window = cls.new_window(_('Select font'))

        font_sel = gtk.FontSelection()
        font_sel.set_preview_text(_('This is a preview text!'))
        fdesc = utils.style_to_pango_font_description(style)

        window.hbox.pack_start(font_sel, True, True)
        font_sel.set_font_name(fdesc.to_string())

        cls.add_button(window, gtk.STOCK_CANCEL, stock.CANCEL, callback,
            select_font_cb, font_sel, style.color)
        cls.add_button(window, gtk.STOCK_OK, stock.ACCEPT, callback,
            select_font_cb, font_sel, style.color)
        window.show_all()

    @classmethod
    def select_color(cls, color, callback):
        '''select color, receives a e3.Message.Color with the current
        color the callback receives a new color object woth the new selection
        '''

        def select_color_cb(button, window, callback, response, color_sel):
            '''callback called on button selection'''

            if response == stock.ACCEPT:
                window.hide()
                gtk_color = color_sel.get_current_color()
                color = e3.Color(gtk_color.red, gtk_color.green,
                    gtk_color.blue)
                callback(color)

            window.hide()

        window = cls.new_window(_('Select color'))

        color_sel = gtk.ColorSelection()

        window.hbox.pack_start(color_sel, True, True)
        color_sel.set_current_color(gtk.gdk.color_parse('#' + color.to_hex()))

        cls.add_button(window, gtk.STOCK_CANCEL, stock.CANCEL, callback,
            select_color_cb, color_sel)
        cls.add_button(window, gtk.STOCK_OK, stock.ACCEPT, callback,
            select_color_cb, color_sel)
        window.show_all()

    @classmethod
    def select_style(cls, style, callback):
        '''select bold, italic, underline and strike, receives
        a e3.Message.Style object with the current style
        the callback receives the response and a new style object with the
        selection
        '''
        pass

    @classmethod
    def select_emote(cls, session, theme, callback, max_width=16):
        '''select an emoticon, receives a gui.Theme object with the theme
        settings the callback receives the response and a string representing
        the selected emoticon
        '''
        EmotesWindow(session, callback, max_width).show()

    @classmethod
    def invite_dialog(cls, session, callback):
        '''select a contact to add to the conversation, receives a session
        object of the current session the callback receives the response and
        a string containing the selected account
        '''
        InviteWindow(session, callback).show()

    @classmethod
    def login_preferences(cls, service, callback, use_http, proxy):
        """
        display the preferences dialog for the login window

        cls -- the dialog class
        service -- the service string identifier (for example 'gtalk')
        callback -- callback to call if the user press accept, call with the
            new values
        use_http -- boolean that indicates if the e3 should use http
            method
        proxy -- a e3.Proxy object
        """

        content = gtk.VBox(spacing=4)
        advanced = gtk.Expander(_("Advanced"))
        box = gtk.Table(10, 2)
        box.set_property('row-spacing', 4)
        box.set_property('column-spacing', 4)

        try:
            s_name = getattr(gui.theme.image_theme, "service_" + service)
            session_pixbuf = utils.safe_gtk_pixbuf_load(s_name)
        except:
            session_pixbuf = None

        session_image = gtk.Image()
        session_image.set_from_pixbuf(session_pixbuf)

        session_label = gtk.Label(service)

        t_proxy_host = gtk.Entry()
        t_proxy_port = gtk.Entry()
        t_user = gtk.Entry()
        t_passwd = gtk.Entry()

        t_server_host = gtk.Entry()
        t_server_port = gtk.Entry()

        def on_toggled(check_button, *entries):
            '''called when a check button is toggled, receive a set
            of entries, enable or disable them deppending on the state
            of the check button'''
            for entry in entries:
                entry.set_sensitive(check_button.get_active())

        c_use_http = gtk.CheckButton(_('Use HTTP method'))
        c_use_proxy = gtk.CheckButton(_('Use proxy'))
        c_use_proxy.connect('toggled', on_toggled, t_proxy_host, t_proxy_port)
        c_use_auth = gtk.CheckButton(_('Use authentication'))
        c_use_auth.connect('toggled', on_toggled, t_user, t_passwd)

        for ext_id, ext in extension.get_extensions('session').iteritems():
            for service_name, service_data in ext.SERVICES.iteritems():
                if service_name == service:
                    t_server_host.set_text(proxy.host or service_data['host'])
                    t_server_port.set_text(proxy.port or service_data['port'])
                    session_id = ext_id

        t_user.set_text(proxy.user or '')
        t_passwd.set_text(proxy.passwd or '')
        t_passwd.set_visibility(False)
        c_use_http.set_active(use_http)
        c_use_proxy.set_active(proxy.use_proxy)
        c_use_proxy.toggled()
        c_use_auth.set_active(proxy.use_auth)
        c_use_auth.toggled()

        l_session = gtk.Label(_('Session:'))
        l_session.set_alignment(0.0, 0.5)
        l_server_host = gtk.Label(_('Server'))
        l_server_host.set_alignment(0.0, 0.5)
        l_server_port = gtk.Label(_('Port'))
        l_server_port.set_alignment(0.0, 0.5)
        l_host = gtk.Label(_('Host'))
        l_host.set_alignment(0.0, 0.5)
        l_port = gtk.Label(_('Port'))
        l_port.set_alignment(0.0, 0.5)
        l_user = gtk.Label(_('User'))
        l_user.set_alignment(0.0, 0.5)
        l_passwd = gtk.Label(_('Password'))
        l_passwd.set_alignment(0.0, 0.5)

        proxy_settings = (l_host, l_port, l_user, l_passwd, t_proxy_host,
                t_proxy_port, t_user, t_passwd, c_use_auth)

        def on_use_proxy_toggled(*args):
            for widget in proxy_settings:
                if c_use_proxy.get_active():
                    widget.show()
                else:
                    widget.hide()

        c_use_proxy.connect('toggled', on_use_proxy_toggled)

        box.attach(l_server_host, 0, 1, 0, 1)
        box.attach(t_server_host, 1, 2, 0, 1)
        box.attach(l_server_port, 0, 1, 1, 2)
        box.attach(t_server_port, 1, 2, 1, 2)
        box.attach(c_use_http, 0, 2, 2, 3)
        # TODO: FIXME: Temporary hack for 2.0 release.
        # msn (papylib) automagically gets system proxies
        if service != 'msn':
            box.attach(c_use_proxy, 0, 2, 3, 4)
        box.attach(l_host, 0, 1, 4, 5)
        box.attach(t_proxy_host, 1, 2, 4, 5)
        box.attach(l_port, 0, 1, 5, 6)
        box.attach(t_proxy_port, 1, 2, 5, 6)
        box.attach(c_use_auth, 0, 2, 6, 7)
        box.attach(l_user, 0, 1, 7, 8)
        box.attach(t_user, 1, 2, 7, 8)
        box.attach(l_passwd, 0, 1, 8, 9)
        box.attach(t_passwd, 1, 2, 8, 9)

        def response_cb(response):
            '''called on any response (close, accept, cancel) if accept
            get the new values and call callback with those values'''
            if response == stock.ACCEPT:
                use_http = c_use_http.get_active()
                use_proxy = c_use_proxy.get_active()
                use_auth = c_use_auth.get_active()
                proxy_host = t_proxy_host.get_text()
                proxy_port = t_proxy_port.get_text()
                server_host = t_server_host.get_text()
                server_port = t_server_port.get_text()
                user = t_user.get_text()
                passwd = t_passwd.get_text()

                callback(use_http, use_proxy, proxy_host, proxy_port, use_auth,
                        user, passwd, session_id, service, server_host, server_port)

            window.hide()

        def button_cb(button, window, response_cb, response):
            '''called when a button is pressedm get the response id and call
            the response_cb that will handle the event according to the
            response'''
            response_cb(response)

        window = cls.new_window(_('Preferences'), response_cb)
        window.set_modal(True)
        window.hbox.pack_start(content)

        session_box = gtk.HBox(spacing=4)
        session_box.pack_start(l_session)
        session_box.pack_start(session_image)
        session_box.pack_start(session_label)

        advanced.add(box)
        content.pack_start(session_box, False)
        content.pack_start(advanced, False)

        cls.add_button(window, gtk.STOCK_CANCEL, stock.CANCEL, response_cb,
                button_cb)
        cls.add_button(window, gtk.STOCK_OK, stock.ACCEPT, response_cb,
                button_cb)

        window.show_all()

        for widget in proxy_settings:
            widget.hide()

    @classmethod
    def edit_profile(cls, handler, user_nick, user_message, last_avatar):

        windows = gtk.Window()
        windows.set_modal(True)
        windows.set_border_width(5)
        windows.set_title(_('Change profile'))
        windows.set_position(gtk.WIN_POS_CENTER)
        windows.set_resizable(False)

        hbox = gtk.HBox(spacing=5)
        vbox = gtk.VBox()

        frame = gtk.Frame(_('Picture'))

        avatar = gtk.Image()
        avatar.set_size_request(96, 96)
        frame.add(avatar)

        if utils.file_readable(last_avatar):
            pixbuf = gtk.gdk.pixbuf_new_from_file(last_avatar)
        else:
            pixbuf = gtk.gdk.pixbuf_new_from_file(gui.theme.image_theme.logo)

        avatar.set_from_pixbuf(pixbuf)
        avatarEventBox = gtk.EventBox()
        avatarEventBox.add(frame)

        hbox.pack_start(avatarEventBox)
        hbox.pack_start(vbox)

        nick_label = gtk.Label(_('Nick:'))
        nick_label.set_alignment(0.0,0.5)

        nick = gtk.Entry()
        nick.set_text(user_nick)

        pm_label = gtk.Label(_('PM:'))
        pm_label.set_alignment(0.0,0.5)

        pm = gtk.Entry()
        pm.set_text(user_message)

        savebutt = gtk.Button(stock=gtk.STOCK_SAVE)

        def save_profile(widget, data=None):
            '''save the new profile'''
            new_nick = nick.get_text()
            new_pm = pm.get_text()
            handler.save_profile(new_nick, new_pm)
            windows.hide()

        savebutt.connect('clicked', save_profile)
        avatarEventBox.connect("button-press-event", handler.on_set_picture_selected)

        vbox0 = gtk.VBox()

        vbox0.pack_start(nick_label)
        vbox0.pack_start(nick)
        vbox0.pack_start(pm_label)
        vbox0.pack_start(pm)

        vbox.pack_start(vbox0)
        vbox.pack_start(savebutt)

        windows.add(hbox)
        windows.show_all()

    @classmethod
    def contactlist_format_help(cls, format_type):
        '''called when the help button for the nick or group format
        is pressed'''
        class TableText(gtk.Alignment):
            '''class that implements selectable labels aligned to the left'''
            def __init__(self, text):
                gtk.Alignment.__init__(self, xalign=0.0, yalign=0.0, xscale=0.0,
                                       yscale=0.0)
                self.label = gtk.Label(text)
                self.label.set_selectable(True)
                self.add(self.label)

        content = gtk.Table(homogeneous=True)
        if format_type == 'nick':
            window = cls.new_window(_('Nick Format Help'))
            cls.window_add_label_vbox(window, _('Example:'))
            cls.window_add_label_vbox(window, \
            '[$DISPLAY_NAME][$NL][$small][$ACCOUNT][$/small][$NL][$small][$BLOCKED] ([$STATUS]) - [$MESSAGE][$/small]')
            content.attach(TableText('[$NICK]'), 0, 1, 0, 1)
            content.attach(TableText(_('Nickname')), 1, 2, 0, 1)
            content.attach(TableText('[$ACCOUNT]'), 0, 1, 1, 2)
            content.attach(TableText(_('Mail')), 1, 2, 1, 2)
            content.attach(TableText('[$DISPLAY_NAME]'), 0, 1, 2, 3)
            content.attach(TableText(_('Alias if available, or nick if available or mail')), 1, 2, 2, 3)
            content.attach(TableText('[$STATUS]'), 0, 1, 3, 4)
            content.attach(TableText(_('Status')), 1, 2, 3, 4)
            content.attach(TableText('[$MESSAGE]'), 0, 1, 4, 5)
            content.attach(TableText(_('Personal message')), 1, 2, 4, 5)
            content.attach(TableText('[$BLOCKED]'), 0, 1, 5, 6)
            content.attach(TableText(_('Displays \'Blocked\' if a contact is blocked')), 1, 2, 5, 6)
            last = 7
        else:
            window = cls.new_window(_('Group Format Help'))
            content.attach(TableText('[$NAME]'), 0, 1, 0, 1)
            content.attach(TableText(_('The name of the group')), 1, 2, 0, 1)
            content.attach(TableText('[$ONLINE_COUNT]'), 0, 1, 1, 2)
            content.attach(TableText(_('Contacts online')), 1, 2, 1, 2)
            content.attach(TableText('[$TOTAL_COUNT]'), 0, 1, 2, 3)
            content.attach(TableText(_('Total amount of contacts')), 1, 2, 2, 3)
            last = 4

        content.attach(TableText('[$b][$/b]'), 0, 1, last, last + 1)
        content.attach(TableText(_('Make text bold')), 1, 2, last, last + 1)
        content.attach(TableText('[$i][$/i]'), 0, 1, last + 1, last + 2)
        content.attach(TableText(_('Make text italic')), 1, 2, last + 1, last + 2)
        content.attach(TableText('[$small][$/small]'), 0, 1, last + 2, last + 3)
        content.attach(TableText(_('Make text small')), 1, 2, last + 2, last + 3)
        content.attach(TableText('[$COLOR=][$/COLOR]'), 0, 1, last + 3, last + 4)
        content.attach(TableText(_('Give text a color (in hex)')), 1, 2, last + 3, last + 4)
        window.hbox.pack_start(content)
        window.show_all()

    @classmethod
    def progress_window(cls, title, callback):
        '''returns a progress window used for emesene 1 synch'''
        dialog = ProgressWindow(title, callback)
        dialog.show_all()
        return dialog

    @classmethod
    def broken_profile(cls, close_cb):
        '''a dialog that asks you to fix your profile'''
        message = _('''\
Your live profile seems to be broken,
which will cause you to experience issues
with your display name, picture
and/or personal message.

You can fix it now by re-uploading
your profile picture on the
Live Messenger website that will open,
or you can choose to fix it later.
To fix your profile, emesene must be closed.
Clicking Yes will close emesene.

Do you want to fix your profile now?''')
        def fix_profile(button, close_cb):
            webbrowser.open("http://profile.live.com/details/Edit/Pic")
            close_cb()

        window = cls.common_window(message, gtk.STOCK_DIALOG_WARNING,
            None, _("You have a broken profile"))
        cls.add_button(window, gtk.STOCK_YES, stock.YES, fix_profile,
            cls.default_cb, close_cb)
        cls.add_button(window, gtk.STOCK_CANCEL, stock.CANCEL, None,
            cls.default_cb)

        window.show()

class ImageChooser(gtk.FileChooserDialog):
    '''a class to select images'''

    def __init__(self, path, response_cb):
        '''class constructor, path is the directory where the
        dialog opens'''
        gtk.FileChooserDialog.__init__(self, _("Image Chooser"), \
                    parent=None, action=gtk.FILE_CHOOSER_ACTION_OPEN)

        self.response_cb = response_cb

        self.set_default_size(600, 400)
        self.set_border_width(4)
        self.set_position(gtk.WIN_POS_CENTER)

        self.vbox.set_spacing(4)

        self.set_current_folder(path)

        hbbox = gtk.HButtonBox()
        hbbox.set_spacing(4)
        hbbox.set_layout(gtk.BUTTONBOX_END)

        b_accept = gtk.Button(stock=gtk.STOCK_OK)
        b_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)

        b_accept.connect('clicked', self._on_accept)
        b_cancel.connect('clicked', self._on_cancel)
        self.connect('delete-event', self._on_close)
        self.connect("file-activated",self._on_accept)

        hbbox.pack_start(b_cancel, False)
        hbbox.pack_start(b_accept, False)

        self.vbox.pack_end(hbbox, False)

        self.show_all()

        self._add_filters()
        self._add_preview()

    def _add_filters(self):
        '''
        Adds all the possible file filters to the dialog. The filters correspond
        to the gdk available image formats
        '''

        # All files filter
        all_files = gtk.FileFilter()
        all_files.set_name(_('All files'))
        all_files.add_pattern('*')

        # All images filter
        all_images = gtk.FileFilter()
        all_images.set_name(_('All images'))

        filters = []
        formats = gtk.gdk.pixbuf_get_formats()
        for format in formats:
            filter = gtk.FileFilter()
            name = "%s (*.%s)" % (format['description'], format['name'])
            filter.set_name(name)

            for mtype in format['mime_types']:
                filter.add_mime_type(mtype)
                all_images.add_mime_type(mtype)

            for pattern in format['extensions']:
                tmp = '*.' + pattern
                filter.add_pattern(tmp)
                all_images.add_pattern(tmp)

            filters.append(filter)


        self.add_filter(all_files)
        self.add_filter(all_images)
        self.set_filter(all_images)

        for filter in filters:
            self.add_filter(filter)

    def _add_preview(self):
        '''
        Adds a preview widget to the file chooser
        '''
        self.image = gtk.Image()
        self.image.set_size_request(128, 128)
        self.image.show()

        self.set_preview_widget(self.image)
        self.set_preview_widget_active(True)

        self.connect('selection-changed', self._on_update_preview)

    def _on_accept(self, button):
        '''method called when the user clicks the button'''
        filename = self.get_filename()
        if os.path.isfile(filename):
            self.hide()
            self.response_cb(gtk.RESPONSE_ACCEPT, filename)
        else:
            Dialog.error(_("No picture selected"))

    def _on_cancel(self, button):
        '''method called when the user clicks the button'''
        self.hide()
        self.response_cb(gtk.RESPONSE_CANCEL, self.get_filename())

    def _on_close(self, window, event):
        '''called when the user click on close'''
        self.hide()
        self.response_cb(gtk.RESPONSE_CLOSE, self.get_filename())

    def _on_update_preview(self, filechooser):
        '''
        Updates the preview image
        '''
        path = self.get_filename()

        if path:
            # if the file is smaller than 1MB we
            # load it, otherwise we dont
            if os.path.isfile(path) and os.path.getsize(path) <= 1000000:
                try:
                    pixbuf = gtk.gdk.pixbuf_new_from_file(self.get_filename())
                    if pixbuf.get_width() > 128 and pixbuf.get_height() > 128:
                        pixbuf = pixbuf.scale_simple(128, 128, gtk.gdk.INTERP_BILINEAR)
                    self.image.set_from_pixbuf(pixbuf)

                except gobject.GError:
                    self.image.set_from_stock(gtk.STOCK_DIALOG_ERROR,
                        gtk.ICON_SIZE_DIALOG)
            else:
                self.image.set_from_stock(gtk.STOCK_DIALOG_ERROR,
                    gtk.ICON_SIZE_DIALOG)

class CEChooser(ImageChooser):
    '''a dialog to create a custom emoticon'''
    SMALL = _("Small (16x16)")
    BIG = _("Big (50x50)")

    def __init__(self, path, response_cb, smilie_list):
        '''class constructor'''
        ImageChooser.__init__(self, path, None)

        self.response_cb = response_cb

        label = gtk.Label(_("Shortcut"))
        self.shortcut = gtk.Entry(7)
        self.combo = gtk.combo_box_new_text()

        self.combo.append_text(CEChooser.SMALL)
        self.combo.append_text(CEChooser.BIG)
        self.combo.set_active(0)

        hbox0 = gtk.HBox()
        hbox1 = gtk.HBox()
        vbox1 = gtk.VBox()
        vbox2 = gtk.VBox()

        hbox1.add(self.shortcut)
        hbox1.add(self.combo)

        vbox2.add(hbox1)

        vbox1.add(label)

        hbox0.add(vbox1)
        hbox0.add(vbox2)

        self.vbox.pack_start(hbox0, False)
        hbox0.show_all()

        self.smilie_list = smilie_list
        self._on_changed(None)
        self.shortcut.connect('changed', self._on_changed)

    def _on_accept(self, button):
        '''method called when the user clicks the button'''
        filename = self.get_filename()
        shortcut = self.shortcut.get_text()
        size = self.combo.get_model().get_value(self.combo.get_active_iter(), 0)

        if os.path.isfile(filename):
            if not shortcut:
                Dialog.error(_("Empty shortcut"))
            else:
                self.hide()
                self.response_cb(stock.ACCEPT, filename, shortcut, size)
        else:
            Dialog.error(_("No picture selected"))

    def _on_cancel(self, button):
        '''method called when the user clicks the button'''
        self.hide()
        self.response_cb(stock.CANCEL, None, None, None)

    def _on_close(self, window, event):
        '''called when the user click on close'''
        self.hide()
        self.response_cb(stock.CLOSE, None, None, None)

    def _on_changed(self, shortcut):
        '''called when the text in self.shortcut changes'''

        SHORTCUT = self.shortcut.get_text()

        if SHORTCUT in self.smilie_list or SHORTCUT == "":
            self.shortcut.set_property('secondary-icon-stock', gtk.STOCK_DIALOG_ERROR)
        else:
            self.shortcut.set_property('secondary-icon-stock', None)

class EmotesWindow(gtk.Window):
    """
    This class represents a window to select an emoticon
    """

    def __init__(self, session, emote_selected, max_width=8):
        """
        Constructor.
        max_width -- the maximum number of columns
        """
        gtk.Window.__init__(self)

        self.session = session
        self.caches = e3.cache.CacheManager(self.session.config_dir.base_dir)
        self.emcache = self.caches.get_emoticon_cache(self.session.account.account)

        self.shortcut_list = []

        self.set_decorated(False)
        self.set_role("emotes")
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        self.set_position(gtk.WIN_POS_MOUSE)
        self.set_resizable(False)

        self.max_width = max_width
        self.emote_selected = emote_selected

        rows = gui.theme.emote_theme.emotes_count/max_width # TODO: remove me

        self.table = gtk.Table(max_width, rows)
        self._fill_emote_table(max_width)
        button = gtk.Button(_("Add emoticon"))
        button.set_image(gtk.image_new_from_stock(gtk.STOCK_ADD,
            gtk.ICON_SIZE_BUTTON))
        button.connect('clicked', self._on_add_custom_emote_selected)
        
        self.box = gtk.VBox()
        self.box.pack_start(self.table)
        self.box.pack_start(button)


        self.add(self.box)
        self.box.show_all()

        self.connect('leave-notify-event', self.on_leave_notify_event)
        self.connect('enter-notify-event', self.on_enter_notify_event)

        self.tag = None

    def on_leave_notify_event(self, *args):
        """
        callback called when the mouse leaves this window
        """
        if self.tag is None:
            self.tag = gobject.timeout_add(500, self.hide)

    def on_enter_notify_event(self, *args):
        """
        callback called when the mouse enters this window
        """
        if self.tag:
            gobject.source_remove(self.tag)
            self.tag = None

    def _get_emo_image(self, path, size):
        '''try to return an image from path
        '''
        pix = utils.safe_gtk_pixbuf_load(path, size)
        picture = gtk.image_new_from_pixbuf(pix)

        return picture

    def _fill_emote_table(self, columns):
        '''fill the gtk.Table with the emoticons'''
        emotes = []

        count = 0
        column = 0
        row = 0

        emote_theme = gui.theme.emote_theme

        def button_and_coords(shortcut, path):
            self.shortcut_list.append(shortcut)
            column = count % columns
            row = count / columns
            button = gtk.Button()
            button.set_image(self._get_emo_image(path, (20, 20)))
            button.set_tooltip_text(shortcut)
            button.set_relief(gtk.RELIEF_NONE)
            button.connect('clicked', self._on_emote_selected, shortcut)
            return (column, row, button)

        for shortcut, name in emote_theme.emotes.iteritems():
            path = emote_theme.emote_to_path(shortcut, True)
            
            if path is None or name in emotes:
                continue
            emotes.append(name)
            
            column, row, button = button_and_coords(shortcut, path)
            self.table.attach(button, column, column + 1, row, row + 1)
            
            count += 1

        for shortcut, hash_ in self.emcache.list():
            path = os.path.join(self.emcache.path, hash_)

            column, row, button = button_and_coords(shortcut, path)
            button.connect('button-release-event', self._on_emote_clicked, shortcut)
            self.table.attach(button, column, column + 1, row, row + 1)

            count += 1

    def _on_add_custom_emote_selected(self, button):
        ''' called when the user wants to add a custom emoticon '''
        def _on_ce_choosed(response, path, shortcut, size):
            '''method called when the ce is selected'''
            if response != stock.ACCEPT:
                return
            if size == CEChooser.SMALL:
                size = 16
            else:
                size = 50

            image = gtk.gdk.PixbufAnimation(path)
            static = image.get_static_image()
            width = static.get_width()
            height = static.get_height()
            if width <= size and height <= size:
                #don't resize if less than size
                resized_path = path
            else:
                if width > height:
                    ratio = float(size)/width
                else:
                    ratio = float(size)/height
                width = int(width*ratio)
                height = int(height*ratio)

                fd, resized_path = tempfile.mkstemp()
                os.close(fd)

                if image.is_static_image():
                    #if static, resize using gtk
                    image = static.scale_simple(width, height,
                                                gtk.gdk.INTERP_NEAREST)

                    if gtk.gdk.pixbuf_get_file_info(path)[0]['name'] == 'jpeg':
                        format = 'jpeg'
                    else:
                        format = 'png'
                    image.save(resized_path, format)
                else:
                    #resize animated images using imagemagick
                    if not self.emcache.resize_with_imagemagick(path,
                                                                resized_path, 
                                                                width, height):
                        resized_path = path

            self.emcache.insert((shortcut, resized_path))

        CEChooser(os.path.expanduser("~"), _on_ce_choosed, self.shortcut_list)

    def _on_emote_selected(self, button, shortcut):
        '''called when an emote is selected'''
        self.emote_selected(shortcut)
        self.hide()

    def _on_emote_clicked(self, button, event, shortcut):
        '''intercept right click and show a nice menu'''
        if event.type == gtk.gdk.BUTTON_RELEASE and event.button == 3:
            emoticon_menu = gtk.Menu()
            emoticon_menu.connect('enter-notify-event', self.on_enter_notify_event)
            short_name = gtk.MenuItem(label=shortcut)
            short_edit = gtk.ImageMenuItem(_("Change shortcut"))
            short_edit.set_image(gtk.image_new_from_stock(
                gtk.STOCK_EDIT, gtk.ICON_SIZE_MENU))
            short_edit.connect("activate", self._on_emote_shortcut_edit, shortcut)

            short_dele = gtk.ImageMenuItem(_("Delete"))
            short_dele.set_image(gtk.image_new_from_stock(
                gtk.STOCK_DELETE, gtk.ICON_SIZE_MENU))
            short_dele.connect("activate", self._on_emote_shortcut_dele, shortcut)

            emoticon_menu.add(short_name)
            emoticon_menu.add(short_edit)
            emoticon_menu.add(short_dele)

            emoticon_menu.show_all()
            emoticon_menu.popup(None, None, None, event.button, event.time)

    def _on_emote_shortcut_edit(self, widget, shortcut):
        '''modify a shortcut for the selected custom emoticon'''
        self.hide()
        cedict = self.emcache.parse()

        def _on_ce_edit_cb(response, emcache, shortcut, hash_, text=''):
            '''method called when the modification is done'''
            if response == stock.ACCEPT:
                if text:
                    emcache.remove_entry(hash_)
                    emcache.add_entry(text, hash_)
                else:
                    Dialog.error(_("Empty shortcut"))

        window = Dialog.entry_window(_("New shortcut"), shortcut,
                    _on_ce_edit_cb, _("Change shortcut"), 
                    self.emcache, shortcut, cedict[shortcut])
        window.show()

    def _on_emote_shortcut_dele(self, widget, shortcut):
        '''delete a custom emoticon and its shortcut'''
        self.hide()
        cedict = self.emcache.parse()
        #TODO: confirmation? or not?
        self.emcache.remove(cedict[shortcut])

class InviteWindow(gtk.Window):
    """
    A window that display a list of users to select the ones to invite to
    the conversarion
    """

    def __init__(self, session, callback):
        """
        constructor
        """
        gtk.Window.__init__(self)
        self.set_border_width(1)
        self.set_title(_('Invite friend'))
        self.set_default_size(300, 250)
        self.session = session
        self.callback = callback
        ContactList = extension.get_default('contact list')
        self.contact_list = ContactList(session)
        self.contact_list.hide_on_filtering = True
        self.contact_list.nick_template = \
            '[$DISPLAY_NAME][$NL][$small][$ACCOUNT][$/small]'

        order_by_group = self.contact_list.session.config.b_order_by_group
        show_blocked = self.contact_list.session.config.b_show_blocked
        show_offline = self.contact_list.session.config.b_show_offline
        self.contact_list.order_by_group = False
        self.contact_list.show_blocked = False
        self.contact_list.show_offline = False
        self.contact_list.session.config.b_order_by_group = order_by_group
        self.contact_list.session.config.b_show_blocked = show_blocked
        self.contact_list.session.config.b_show_offline = show_offline

        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        self.set_position(gtk.WIN_POS_CENTER)

        vbox = gtk.VBox()
        vbox.set_spacing(1)

        bbox = gtk.HButtonBox()
        bbox.set_spacing(1)
        bbox.set_layout(gtk.BUTTONBOX_END)

        badd = gtk.Button(stock=gtk.STOCK_ADD)
        bclose = gtk.Button(stock=gtk.STOCK_CLOSE)

        search = gtk.Entry()
        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        scroll.set_border_width(1)
        scroll.add(self.contact_list)

        bbox.pack_start(bclose)
        bbox.pack_start(badd)

        vbox.pack_start(scroll, True, True)
        vbox.pack_start(search, False)
        vbox.pack_start(bbox, False)
        self.add(vbox)

        vbox.show_all()
        badd.connect('clicked', self._on_add_clicked)
        bclose.connect('clicked', lambda *args: self.hide())
        search.connect('changed', self._on_search_changed)
        self.connect('key-press-event', self._on_key_press)
        self.connect('delete-event', lambda *args: self.hide())
        self.contact_list.contact_selected.subscribe(
            self._on_contact_selected)
        self.contact_list.fill()

    def _on_key_press(self, widget, event):
        if event.keyval == gtk.keysyms.Escape:
            self._hide()

    def _on_add_clicked(self, button):
        """
        method called when the add button is clicked
        """
        contact = self.contact_list.get_contact_selected()

        if contact is None:
            Dialog.error(_("No contact selected"))
            return

        self.callback(contact.account)
        self._hide()

    def _on_search_changed(self, entry):
        """
        called when the content of the entry changes
        """
        self.contact_list.filter_text = entry.get_text()

    def _on_contact_selected(self, contact):
        """
        method called when the contact is selected
        """
        self.callback(contact.account)
        self._hide()

    def _hide(self):
        """
        unsubscribe the signal, and hide the dialog
        """
        self.contact_list.contact_selected.unsubscribe(
            self._on_contact_selected)
        self.hide()

class AddBuddy(gtk.Window):
    '''Confirm dialog informing that someone has added you
    ask if you want to add him to your contact list'''

    def __init__(self, callback):
        '''Constructor. Packs widgets'''
        gtk.Window.__init__(self)

        self.mails = []  # [(mail, nick), ...]
        self.rejected = []
        self.accepted = []
        self.callback = callback
        self.pointer = 0

        # window
        self.set_title(_("Add contact"))
        self.set_border_width(4)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        self.move(30, 30) # top-left
        self.connect('delete-event', self.cb_delete)

        ## widgets

        # main vbox
        self.vbox = gtk.VBox()

        # hbox with image, pages, and main text
        self.hbox = gtk.HBox()
        self.hbox.set_spacing(4)
        self.hbox.set_border_width(4)

        # the contents of the hbox (image+vboxtext)
        self.image = gtk.Image()
        self.image.set_from_stock(gtk.STOCK_DIALOG_QUESTION, \
            gtk.ICON_SIZE_DIALOG)
        self.imagebox = gtk.HBox()
        self.imagebox.set_border_width(4)
        self.image.set_alignment(0.0, 0.5)

        # the vboxtext (pages+text)
        self.vboxtext = gtk.VBox()
        self.pages = self._buildpages()
        self.text = gtk.Label()
        self.text.set_selectable(True)
        self.text.set_ellipsize(3) #pango.ELLIPSIZE_END
        self.text.set_alignment(0.0, 0.0) # top left
        self.text.set_width_chars(60)

        # hboxbuttons + button box
        self.hboxbuttons = gtk.HBox()
        self.hboxbuttons.set_spacing(4)
        self.hboxbuttons.set_border_width(4)
        self.buttonbox = gtk.HButtonBox()
        self.buttonbox.set_layout(gtk.BUTTONBOX_END)

        # the contents of the buttonbox
        self.later = gtk.Button()
        self.later.add(gtk.Label(_('Remind me later')))
        self.later.connect('clicked', self.cb_cancel)
        self.reject = gtk.Button(stock=gtk.STOCK_REMOVE)
        self.reject.connect('clicked', self.cb_reject)
        self.addbutton = gtk.Button(stock=gtk.STOCK_ADD)
        self.addbutton.connect('clicked', self.cb_add)

        ## packing
        self.add(self.vbox)
        self.vbox.pack_start(self.hbox, True, True)
        self.vbox.pack_start(self.hboxbuttons, False, False)

        self.imagebox.pack_start(self.image)
        self.hbox.pack_start(self.imagebox, False, False)
        self.hbox.pack_start(self.vboxtext, True, True)
        self.vboxtext.pack_start(self.pages, False, False)
        self.vboxtext.pack_start(self.text, True, True)

        self.hboxbuttons.pack_start(self.later, False, False)
        self.hboxbuttons.pack_start(self.reject, False, False)
        self.hboxbuttons.pack_start(self.buttonbox)
        self.buttonbox.pack_start(self.addbutton)

    def _buildpages(self):
        '''Builds hboxpages, that is a bit complex to include in __init__'''
        hboxpages = gtk.HBox()

        arrowleft = TinyArrow(gtk.ARROW_LEFT)
        self.buttonleft = gtk.Button()
        self.buttonleft.set_relief(gtk.RELIEF_NONE)
        self.buttonleft.add(arrowleft)
        self.buttonleft.connect('clicked', self.switchmail, -1)

        arrowright = TinyArrow(gtk.ARROW_RIGHT)
        self.buttonright = gtk.Button()
        self.buttonright.set_relief(gtk.RELIEF_NONE)
        self.buttonright.add(arrowright)
        self.buttonright.connect('clicked', self.switchmail, 1)

        self.currentpage = gtk.Label()

        hboxpages.pack_start(gtk.Label(), True, True) # align to right
        hboxpages.pack_start(self.buttonleft, False, False)
        hboxpages.pack_start(self.currentpage, False, False)
        hboxpages.pack_start(self.buttonright, False, False)

        return hboxpages

    def append(self, nick, mail):
        '''Adds a new pending user'''
        self.mails.append((mail, gobject.markup_escape_text(nick)))
        self.update()
        self.show_all()
        self.present()

    def update(self):
        '''Update the GUI, including labels, arrow buttons, etc'''
        try:
            mail, nick = self.mails[self.pointer]
        except IndexError:
            self.hide()
            return

        if nick != mail:
            mailstring = "<b>%s</b>\n<b>(%s)</b>" % (nick, mail)
        else:
            mailstring = '<b>%s</b>' % mail

        self.text.set_markup(mailstring + _(' has added you.\n'
            'Do you want to add him/her to your contact list?'))

        self.buttonleft.set_sensitive(True)
        self.buttonright.set_sensitive(True)
        if self.pointer == 0:
            self.buttonleft.set_sensitive(False)
        if self.pointer == len(self.mails) - 1:
            self.buttonright.set_sensitive(False)

        self.currentpage.set_markup('<b>(%s/%s)</b>' % \
            (self.pointer + 1, len(self.mails)))

    def switchmail(self, button, order):
        '''Moves the mail pointer +1 or -1'''
        if (self.pointer + order) >= 0:
            if (self.pointer + order) < len(self.mails):
                self.pointer += order
            else:
                self.pointer = 0
        else:
            self.pointer = len(self.mails) - 1

        self.update()

    def hide(self):
        '''Called to hide the window'''
        self.callback({'accepted': self.accepted, 'rejected': self.rejected})
        gtk.Window.hide(self)

    def cb_delete(self, *args):
        '''Callback when the window is destroyed'''
        self.destroy()

    def cb_cancel(self, button):
        '''Callback when the cancel button is clicked'''
        self.mails.pop(self.pointer)
        self.switchmail(None, -1)

    def cb_reject(self, button):
        '''Callback when the view reject button is clicked'''
        mail, nick = self.mails[self.pointer]
        self.rejected.append(mail)
        self.mails.pop(self.pointer)
        self.switchmail(None, -1)

    def cb_add(self, button):
        '''Callback when the add button is clicked'''
        mail, nick = self.mails[self.pointer]
        self.accepted.append(mail)
        self.mails.pop(self.pointer)
        self.switchmail(None, -1)

class TinyArrow(gtk.DrawingArea):
    LENGTH = 8
    WIDTH = 5

    def __init__(self, arrow_type, shadow=gtk.SHADOW_NONE):
        gtk.DrawingArea.__init__(self)
        self.arrow_type = arrow_type
        self.shadow = shadow
        self.margin = 0

        self.set_size_request(*self.get_size())
        self.connect("expose_event", self.expose)

    def get_size(self):
        if self.arrow_type in (gtk.ARROW_LEFT, gtk.ARROW_RIGHT):
            return (TinyArrow.WIDTH + self.margin*2, \
                    TinyArrow.LENGTH + self.margin*2)
        else:
            return (TinyArrow.LENGTH + self.margin*2, \
                    TinyArrow.WIDTH + self.margin*2)

    def expose(self, widget=None, event=None):
        if self.window is None:
            return
        self.window.clear()
        width, height = self.get_size()
        self.get_style().paint_arrow(self.window, self.state, \
            self.shadow, None, self, '', self.arrow_type, True, \
            0, 0, width, height)

        return False

    def set(self, arrow_type, shadow=gtk.SHADOW_NONE, margin=None):
        self.arrow_type = arrow_type
        self.shadow = shadow
        if margin is not None:
            self.margin = margin
        self.set_size_request(*self.get_size())
        self.expose()

class ProgressWindow(gtk.Window):
    '''A class for a progressbar dialog'''

    def __init__(self, title, callback):
        '''Constructor. Packs widgets'''
        gtk.Window.__init__(self)
        self.set_title(title)
        self.set_role("dialog")
        self.set_modal(True)
        self.buttoncancel = gtk.Button()
        self.buttoncancel.set_label(_("Cancel"))
        self.buttoncancel.connect('clicked', callback)
        self.connect('delete-event', callback)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        self.set_default_size(300, 50)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_border_width(8)
        vbox = gtk.VBox()
        self.progressbar = gtk.ProgressBar()
        self.desclabel = gtk.Label()
        vbox.pack_start(self.desclabel)
        vbox.pack_start(self.progressbar)
        vbox.pack_start(self.buttoncancel)
        self.add(vbox)
        
    def update(self, progress):
        '''called when the progress is updated'''
        self.progressbar.set_fraction(progress / 100.0)
        self.progressbar.set_text("%d %s" % (progress, "%"))

    def set_action(self, action):
        '''called when the action changes'''
        self.desclabel.set_text(action)

