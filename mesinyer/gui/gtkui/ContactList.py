# -*- coding: utf-8 -*-

#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
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
'''a gtk implementation of gui.ContactList'''
import gtk
import pango
import gobject

import e3
import gui
import utils
import extension
from debugger import dbg

from gui.base import Plus
import RichBuffer

@extension.implements('nick renderer')
class CellRendererFunction(gtk.GenericCellRenderer):
    '''
    CellRenderer that behaves like a label, but apply a function to "markup"
    to show a modified nick. Its a base class, and it is intended to be
    inherited by extensions.
    '''
    __gproperties__ = {
            'markup': (gobject.TYPE_STRING,
                "text",
                "text we'll display (even with plus markup!)",
                '', #default value
                gobject.PARAM_READWRITE)
            }

    property_names = __gproperties__.keys()

    def __init__(self, function):
        self.__gobject_init__()
        #gtk.CellRenderer.__init__(self)
        self.__dict__['markup'] = ''
        self.function = function

    def __getattr__(self, name):
         try:
             return self.get_property(name)
         except TypeError:
             raise AttributeError, name

    def __setattr__(self, name, value):
         try:
             self.set_property(name, value)
         except TypeError:
             self.__dict__[name] = value

    def on_get_size(self, widget, cell_area):

        # The following size calculations have tested so that the TextView
        # will fully fit in the cell when editing and it will be the same
        # size as a CellRendererText cell with same amount or rows.

        xpad = 2
        ypad = 2

        xalign = 0
        yalign = 0.5

        layout = self.get_layout(widget)
        width, height = layout.get_pixel_size()

        x_offset = xpad
        y_offset = ypad

        if cell_area:

            x_offset = xalign * (cell_area.width - width)
            x_offset = max(x_offset, xpad)
            x_offset = int(round(x_offset, 0))

            y_offset = yalign * (cell_area.height - height)
            y_offset = max(y_offset, ypad)
            y_offset = int(round(y_offset, 0))

        width  = width  + (xpad * 2)
        height = height + (ypad * 2)

        return x_offset, y_offset, width, height

    def do_get_property(self, property):
         if property.name not in self.property_names:
             raise TypeError('No property named %s' % (property.name,))
         return self.__dict__[property.name]

    def do_set_property(self, property, value):
        if property.name not in self.property_names:
            raise TypeError('No property named %s' % (property.name,))
        if property == 'markup': #plus formatting
            value = Plus.msnplus_to_dict
        self.__dict__[property.name] = value

    def on_render(self, window, widget, bg_area, cell_area, exp_area, flags):
        x_offset, y_offset, width, height = self.on_get_size(widget, cell_area)
        layout = self.get_layout(widget)

        # Determine state to get text color right.
        if flags & gtk.CELL_RENDERER_SELECTED:
            if widget.get_property('has-focus'):
                state = gtk.STATE_SELECTED
            else:
                state = gtk.STATE_ACTIVE
        else:
            state = gtk.STATE_NORMAL

        widget.style.paint_layout(
            window, state, True, cell_area, widget, 'foo',
            cell_area.x + x_offset, cell_area.y + y_offset, layout)

    def get_layout(self, widget):
        '''Gets the Pango layout used in the cell in a TreeView widget.'''
        '''buf = RichBuffer.RichBuffer()
        plused_markup = Plus.msnplus(self.markup)
        view = gtk.TextView()
        view.set_buffer(buf)
        buf._put_formatted(plused_markup)
        return view'''
        layout = pango.Layout(widget.get_pango_context())
        layout.set_width(-1)    # Do not wrap text.
        if self.markup:
            #try:
            decorated_markup = self.function(unicode(self.markup, 'utf-8')).encode('utf-8')
            #except Exception, error:
            '''    raise error
                print "this nick: '%s' made the parser go crazy, striping" % (self.markup,)
                print error
                log_strange_nick(self.markup, 'msnplus parser')

                decorated_markup = Plus.msnplus_strip(self.markup)'''

            try:
                pango.parse_markup(decorated_markup)
            except gobject.GError:
                print "invalid pango markup:", decorated_markup
                log_strange_nick(decorated_markup, 'pango parser')
                decorated_markup = Plus.msnplus_strip(self.markup)

            layout.set_markup(decorated_markup)
        else:
            layout.set_text('')

        return layout

@extension.implements('nick renderer')
class CellRendererPlus(CellRendererFunction):
    '''Nick renderer that parse the MSN+ markup, showing colors, gradients and
    effects'''
    def __init__(self):
        CellRendererFunction.__init__(self, lambda txt: Plus.msnplus(txt).to_xml())

@extension.implements('nick renderer')
class CellRendererNoPlus(CellRendererFunction):
    '''Nick renderer that "strip" MSN+ markup, not showing any effect/color,
    but improving the readability'''
    def __init__(self):
        CellRendererFunction.__init__(self, Plus.msnplus_strip)


gobject.type_register(CellRendererPlus)

class ContactList(gui.ContactList, gtk.TreeView):
    '''a gtk implementation of gui.ContactList'''
    NAME = 'Contact List'
    DESCRIPTION = 'The widget that displays the contact list on the main window'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    NICK_TPL = '%DISPLAY_NAME%%NL%' \
        '<span foreground="#AAAAAA" size="small">' \
        '%BLOCKED% %ACCOUNT%%NL%%MESSAGE%</span>'
    GROUP_TPL = '<b>%NAME% (%ONLINE_COUNT%/%TOTAL_COUNT%)</b>'

    def __init__(self, session):
        '''class constructor'''
        dialog = extension.get_default('dialog')
        self.pbr = gtk.CellRendererPixbuf()
        gui.ContactList.__init__(self, session, dialog)
        gtk.TreeView.__init__(self)

        if self.session.config.d_weights is None:
            self.session.config.d_weights = {}

        # the image (None for groups) the object (group or contact),
        # the string to display and a boolean indicating if the pixbuf should
        # be shown (False for groups, True for contacts), the status
        # image, and an int that is used to allow ordering specified by the user
        self._model = gtk.TreeStore(gtk.gdk.Pixbuf, object, str, bool,
            gtk.gdk.Pixbuf, int)
        self.model = self._model.filter_new(root=None)
        self.model.set_visible_func(self._visible_func)

        self._model.set_sort_func(1, self._sort_method)
        self._model.set_sort_column_id(1, gtk.SORT_ASCENDING)

        self.set_model(self.model)

        crt = extension.get_and_instantiate('nick renderer')
        #crt.set_property('ellipsize', pango.ELLIPSIZE_END)
        pbr_status = gtk.CellRendererPixbuf()

        column = gtk.TreeViewColumn()
        column.set_expand(True)

        self.exp_column = gtk.TreeViewColumn()
        self.exp_column.set_max_width(16)

        self.append_column(self.exp_column)
        self.append_column(column)
        self.set_expander_column(self.exp_column)

        column.pack_start(self.pbr, False)
        column.pack_start(crt, True)
        column.pack_start(pbr_status, False)

        column.add_attribute(self.pbr, 'pixbuf', 0)
        column.add_attribute(crt, 'markup', 2)
        column.add_attribute(self.pbr, 'visible', 3)
        column.add_attribute(pbr_status, 'visible', 3)
        column.add_attribute(pbr_status, 'pixbuf', 4)

        self.set_search_column(2)
        self.set_headers_visible(False)

        self.connect('row-activated', self._on_row_activated)
        self.connect('button-release-event' , self._on_button_press_event)

        # valid values:
        # + NICK
        # + ACCOUNT
        # + DISPLAY_NAME (alias if available, or nick if available or mail)
        # + STATUS
        # + MESSAGE
        # + BLOCKED (show the text "(blocked)" if the account is blocked)
        # + NL (new line)
        self.nick_template = session.config.get_or_set('nick_template',
                ContactList.NICK_TPL)
        # valid values:
        # + NAME
        # + ONLINE_COUNT
        # + TOTAL_COUNT
        self.group_template = session.config.get_or_set('group_template',
                ContactList.GROUP_TPL)

    def _get_contact_pixbuf_or_default(self, contact):
        '''try to return a pixbuf of the user picture or the default
        picture
        '''
        if contact.picture:
            picture = utils.safe_gtk_pixbuf_load(contact.picture,
                    (self.avatar_size, self.avatar_size))
        else:
            picture = utils.safe_gtk_pixbuf_load(gui.theme.user,
                    (self.avatar_size, self.avatar_size))

        return picture

    def _visible_func(self, model, _iter):
        '''return True if the row should be displayed according to the
        value of the config'''
        obj = self._model[_iter][1]

        if not obj:
            return

        if type(obj) == e3.Group:
            if not self.show_empty_groups:
                # get a list of contact objects from a list of accounts
                contacts = self.contacts.get_contacts(obj.contacts)
                if  self.contacts.get_online_total_count(contacts)[0] == 0:
                    return False

            return True

        # i think joining all the text from a user with a new line between
        # and searching on one string is faster (and the user cant add
        # a new line to the entry so..)
        if self._filter_text:
            if '\n'.join((obj.account, obj.alias, obj.nick, obj.message,
                obj.account)).lower().find(self._filter_text) == -1:
                return False
            else:
                return True

        if not self.show_offline and obj.status == e3.status.OFFLINE:
            return False

        if not self.show_blocked and obj.blocked:
            return False

        return True

    def _sort_method(self, model, iter1, iter2, user_data=None):
        '''callback called to decide the order of the contacts'''

        obj1 = self._model[iter1][1]
        obj2 = self._model[iter2][1]
        order1 = self._model[iter1][5]
        order2 = self._model[iter2][5]

        if type(obj1) == e3.Group and type(obj2) == e3.Group:
            return self.compare_groups(obj1, obj2, order1, order2)
        elif type(obj1) == e3.Contact and type(obj2) == e3.Contact:
            return self.compare_contacts(obj1, obj2, order1, order2)
        elif type(obj1) == e3.Group and type(obj2) == e3.Contact:
            return -1
        else:
            return 1

    def _get_selected(self):
        '''return the selected row or None'''
        iter_ = self.get_selection().get_selected()[1]

        if iter_ is None:
            return None

        return self.model.convert_iter_to_child_iter(iter_)

    def _on_row_activated(self, treeview, path, view_column):
        '''callback called when the user selects a row'''
        group = self.get_group_selected()
        contact = self.get_contact_selected()

        if group:
            self.group_selected.emit(group)
        elif contact:
            self.contact_selected.emit(contact)
        else:
            dbg('nothing selected?', 'contactlist', 1)

    def _on_button_press_event(self, treeview, event):
        '''callback called when the user press a button over a row
        chek if it's the roght button and emit a signal on that case'''
        if event.button == 3:
            paths = self.get_path_at_pos(int(event.x), int(event.y))

            if paths is None:
                dbg('invalid path', 'contactlist', 1)
            elif len(paths) > 0:
                iterator = self.model.get_iter(paths[0])
                child_iter = self.model.convert_iter_to_child_iter(iterator)
                obj = self._model[child_iter][1]

                if type(obj) == e3.Group:
                    self.group_menu_selected.emit(obj)
                elif type(obj) == e3.Contact:
                    self.contact_menu_selected.emit(obj)
            else:
                dbg('empty paths?', 'contactlist', 1)

    # overrided methods
    def refilter(self):
        '''refilter the values according to the value of self.filter_text'''
        self.model.refilter()

    def is_group_selected(self):
        '''return True if a group is selected'''
        selected = self._get_selected()

        if selected is None:
            return False

        return type(self._model[selected][1]) == e3.Group

    def is_contact_selected(self):
        '''return True if a contact is selected'''
        selected = self._get_selected()

        if selected is None:
            return False

        return type(self._model[selected][1]) == e3.Contact

    def get_group_selected(self):
        '''return a group object if there is a group selected, None otherwise
        '''
        selected = self._get_selected()

        if selected is None:
            return None

        if self.is_group_selected():
            return self._model[selected][1]

        return None

    def get_contact_selected(self):
        '''return a contact object if there is a group selected, None otherwise
        '''
        selected = self._get_selected()

        if selected is None:
            return None

        if self.is_contact_selected():
            return self._model[selected][1]

        return None

    def add_group(self, group):
        '''add a group to the contact list'''
        if self.order_by_status:
            return None

        try:
            weight = int(self.session.config.d_weights.get(group.identifier, 0))
        except ValueError:
            weight = 0

        self.session.config.d_weights[group.identifier] = weight

        group_data = (None, group, self.format_group(group), False, None,
            weight)

        for row in self._model:
            obj = row[1]
            if type(obj) == e3.Group:
                if obj.name == group.name:
                    dbg('Trying to add an existing group! ' + obj.name,
                        'contactlist', 1)
                    return row.iter

        return self._model.append(None, group_data)

    def remove_group(self, group):
        '''remove a group from the contact list'''
        for row in self._model:
            obj = row[1]
            if type(obj) == e3.Group and obj.name == group.name:
                del self._model[row.iter]

    def add_contact(self, contact, group=None):
        '''add a contact to the contact list, add it to the group if
        group is not None'''
        try:
            weight = int(self.session.config.d_weights.get(contact.account, 0))
        except ValueError:
            weight = 0

        self.session.config.d_weights[contact.account] = weight

        contact_data = (self._get_contact_pixbuf_or_default(contact), contact,
            self.format_nick(contact), True,
            utils.safe_gtk_pixbuf_load(gui.theme.status_icons[contact.status]),
            weight)

        # if no group add it to the root, but check that it's not on a group
        # or in the root already
        if not group or self.order_by_status:
            for row in self._model:
                obj = row[1]
                # check on group
                if type(obj) == e3.Group:
                    for contact_row in row.iterchildren():
                        con = contact_row[1]
                        if con.account == contact.account:
                            return contact_row.iter
                # check on the root
                elif type(obj) == e3.Contact and obj.account == contact.account:
                    return row.iter

            return self._model.append(None, contact_data)

        for row in self._model:
            obj = row[1]
            if type(obj) == e3.Group and obj.name == group.name:
                # if the contact is already on the group, then dont add it
                for contact_row in row.iterchildren():
                    con = contact_row[1]
                    if con.account == contact.account:
                        return contact_row.iter

                return_iter = self._model.append(row.iter, contact_data)
                self.update_group(group)

                # search the use on the root to remove it if it's there
                # since we added him to a group
                for irow in self._model:
                    iobj = irow[1]
                    if type(iobj) == e3.Contact and \
                            iobj.account == contact.account:
                        del self._model[irow.iter]

                return return_iter
        else:
            self.add_group(group)
            return self.add_contact(contact, group)

    def remove_contact(self, contact, group=None):
        '''remove a contact from the specified group, if group is None
        then remove him from all groups'''
        if not group:
            # go though the groups and the contacts without group
            for row in self._model:
                obj = row[1]
                # if we get a group we go through the contacts
                if type(obj) == e3.Group:
                    for contact_row in row.iterchildren():
                        con = contact_row[1]
                        # if we find it, we remove it
                        if con.account == contact.account:
                            del self._model[contact_row.iter]
                            self.update_group(obj)

                # if it's a contact without group (at the root)
                elif type(obj) == e3.Contact and obj.account == contact.account:
                    del self._model[row.iter]

            return

        # go though the groups
        for row in self._model:
            obj = row[1]
            # if it's the group we are searching
            if type(obj) == e3.Group and obj.name == group.name:
                # go through all the contacts
                for contact_row in row.iterchildren():
                    con = contact_row[1]
                    # if we find it, we remove it
                    if con.account == contact.account:
                        del self._model[contact_row.iter]
                        self.update_group(group)

    def clear(self):
        '''clear the contact list'''
        self._model.clear()

        # this is the best place to put this code without putting gtk code
        # on gui.ContactList
        self.exp_column.set_visible(not self.order_by_status)

    def update_contact(self, contact):
        '''update the data of contact'''
        try:
            weight = int(self.session.config.d_weights.get(contact.account, 0))
        except ValueError:
            weight = 0

        self.session.config.d_weights[contact.account] = weight

        contact_data = (self._get_contact_pixbuf_or_default(contact), contact,
            self.format_nick(contact), True,
            utils.safe_gtk_pixbuf_load(gui.theme.status_icons[contact.status]),
            weight)

        found = False

        for row in self._model:
            obj = row[1]
            if type(obj) == e3.Group:
                for contact_row in row.iterchildren():
                    con = contact_row[1]
                    if con.account == contact.account:
                        found = True
                        self._model[contact_row.iter] = contact_data
                        self.update_group(obj)
            elif type(obj) == e3.Contact and obj.account == contact.account:
                found = True
                self._model[row.iter] = contact_data

    def update_group(self, group):
        '''update the data of group'''
        try:
            weight = int(self.session.config.d_weights.get(group.identifier, 0))
        except ValueError:
            weight = 0

        self.session.config.d_weights[group.identifier] = weight

        group_data = (None, group, self.format_group(group), False, None,
            weight)

        for row in self._model:
            obj = row[1]
            if type(obj) == e3.Group and obj.name == group.name:
                self._model[row.iter] = group_data

    def set_group_state(self, group, state):
        '''expand group id state is True, collapse it if False'''
        for row in self._model:
            obj = row[1]
            if type(obj) == e3.Group and obj.name == group.name:
                path = self._model.get_path()

                if state:
                    self.expand_row(path, False)
                else:
                    self.collapse_row(path)

    def format_nick(self, contact):
        '''replace the appearance of the template vars using the values of
        the contact
        # valid values:
        # + NICK
        # + ACCOUNT
        # + DISPLAY_NAME (alias if available, or nick if available or mail)
        # + STATUS
        # + MESSAGE
        # + NL
        '''
        message = gobject.markup_escape_text(
                contact.message).replace('%MESSAGE%', '% MESSAGE %')
        nick = gobject.markup_escape_text(
                contact.nick).replace('%NICK%', '% NICK %')
        display_name = gobject.markup_escape_text(
                contact.display_name).replace('%DISPLAY_NAME%', '% DISPLAY_NAME %')

        template = self.nick_template
        template = template.replace('%NL%', '\n')
        template = template.replace('%ACCOUNT%',
            gobject.markup_escape_text(contact.account))
        template = template.replace('%STATUS%',
            gobject.markup_escape_text(e3.status.STATUS[contact.status]))
        template = template.replace('%DISPLAY_NAME%', display_name)
        template = template.replace('%MESSAGE%', message)
        template = template.replace('%NICK%', nick)

        blocked_text = ''
        if contact.blocked:
            blocked_text = '(blocked)'

        template = template.replace('%BLOCKED%', blocked_text)

        return template

    def format_group(self, group):
        '''replace the appearance of the template vars using the values of
        the group
        # valid values:
        # + NAME
        # + ONLINE_COUNT
        # + TOTAL_COUNT
        '''
        name = gobject.markup_escape_text(group.name).replace('%NAME%',
            '% NAME %')

        contacts = self.contacts.get_contacts(group.contacts)
        (online, total) = self.contacts.get_online_total_count(contacts)
        template = self.group_template
        template = template.replace('%ONLINE_COUNT%', str(online))
        template = template.replace('%TOTAL_COUNT%', str(total))
        template = template.replace('%NAME%', name)

        return template

    def set_avatar_size(self, size):
        """set the size of the avatars on the contact list
        """
        self.avatar_size = size
        self.pbr.set_fixed_size(size, size)

def log_strange_nick(string, reason):
    '''write to a file the nicks that make the parsers go crazy so we can
    analyze them
    '''
    handle = file('strange-nicks.txt', 'a')
    handle.write(reason + ': ' + string + '\n')
    handle.close()
