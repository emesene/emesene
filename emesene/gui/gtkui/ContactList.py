'''a gtk implementation of gui.ContactList'''
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

import gtk
import pango
import gobject

import e3
import gui
import utils
import extension
import logging

import Tooltips
from gui.base import Plus

log = logging.getLogger('gtkui.ContactList')

class ContactList(gui.ContactList, gtk.TreeView):
    '''a gtk implementation of gui.ContactList'''
    NAME = 'Contact List'
    DESCRIPTION = 'The widget that displays the contact list on the main window'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, session):
        '''class constructor'''
        self._model = None
        pbr = extension.get_default('avatar renderer')
        self.pbr = pbr()

        gui.ContactList.__init__(self, session)
        gtk.TreeView.__init__(self)

        self.set_enable_search(False) # Enable our searching widget
                                      # with CTRL+F in MainWindow.py

        self.online_group = None # added
        self.online_group_iter = None # added
        self.no_group = None
        self.no_group_iter = None
        self.offline_group = None
        self.offline_group_iter = None
        self.hide_on_filtering = False

        self.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, [
                                      ('emesene-contact', 0, 0),
                                      ('text/html', 0, 1),
                                      ('text/plain', 0, 2)],
                                      gtk.gdk.ACTION_COPY)

        self.enable_model_drag_dest([('emesene-contact', 0, 0)],
                                    gtk.gdk.ACTION_DEFAULT)

        self.contact_handler = gui.base.ContactHandler(session, self)
        self.group_handler = gui.base.GroupHandler(session, self)

        if self.session.config.d_weights is None:
            self.session.config.d_weights = {}

        # [0] the image (None for groups),
        # [1] the object (group or contact),
        # [2] the string to display
        # [3] a boolean indicating if the pixbuf should
        #     be shown (False for groups, True for contacts)
        # [4] the status image
        # [5] an int that is used to allow ordering specified by the user
        # [6] a boolean indicating special groups always False for contacts,
        #     True for special groups like "No group"
        # [7] a boolean indicating if the contact is offline
        self._model = gtk.TreeStore(gtk.Image, object, str, bool,
            gtk.gdk.Pixbuf, int, bool, bool)
        self.model = self._model.filter_new(root=None)
        self.model.set_visible_func(self._visible_func)

        self._model.set_sort_func(1, self._sort_method)
        self._model.set_sort_column_id(1, gtk.SORT_ASCENDING)

        self.set_model(self.model)

        self.tooltips = Tooltips.Tooltips()
        self.connect('motion-notify-event', self.tooltips.on_motion)
        self.connect('leave-notify-event', self.tooltips.on_leave)

        crt = extension.get_and_instantiate('nick renderer')
        crt.set_property('ellipsize', pango.ELLIPSIZE_END)
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

        column.add_attribute(self.pbr, 'image', 0)
        column.add_attribute(crt, 'markup', 2)
        column.add_attribute(self.pbr, 'visible', 3)
        column.add_attribute(pbr_status, 'visible', 3)
        column.add_attribute(pbr_status, 'pixbuf', 4)
        column.add_attribute(self.pbr, 'offline', 7)

        self.set_search_column(2)
        self.set_headers_visible(False)

        self.connect('row-activated',  self._on_row_activated)
        self.connect('button-release-event',  self._on_button_press_event)
        self.connect('row-expanded',  self._on_expand)
        self.connect('row-collapsed',  self._on_collapse)
        self.connect('drag-data-get',  self._on_drag_data_get)
        self.connect('drag-drop',  self._on_drag_drop)

    def _set_accels(self, mainwindow):
        """set the keyboard shortcuts
        """
        accel_group = gtk.AccelGroup()
        mainwindow.add_accel_group(accel_group)
        self.accel_group = accel_group
        accel_group.connect_group(gtk.keysyms.Delete, 0, gtk.ACCEL_LOCKED,
                self._on_key_delete_item)
        accel_group.connect_group(gtk.keysyms.T,
                                  gtk.gdk.CONTROL_MASK,
                                  gtk.ACCEL_LOCKED,
                                  self.open_conversation)

    def _on_key_delete_item(self, accel_group, window, keyval, mod):
        if self.is_focus():
            if self.is_contact_selected():
                self.contact_handler.on_remove_contact_selected()

            elif self.is_group_selected() and \
                 self.group_handler.is_by_group_view():

                self.group_handler.on_remove_group_selected()

    def _on_expand(self, treeview, iter_, path):
        group = self.model[path][1]
        self.on_group_expanded(group)

    def _on_collapse(self, treeview, iter_, path):
        group = self.model[path][1]
        self.on_group_collapsed(group)

    def _get_contact_pixbuf_or_default(self, contact):
        '''try to return a pixbuf of the user picture or the default
        picture
        '''
        if contact.picture:
            # TODO: This could be handled in AvatarManager in the same
            # way as avatars from the Avatar class
            try:
                animation = gtk.gdk.PixbufAnimation(contact.picture)
            except gobject.GError:
                pix = utils.gtk_pixbuf_load(gui.theme.image_theme.user,
                        (self.avatar_size, self.avatar_size))
                picture = gtk.image_new_from_pixbuf(pix)
                return picture

            if animation.is_static_image():
                pix = utils.gtk_pixbuf_load(contact.picture,
                        (self.avatar_size, self.avatar_size))

                if bool(contact.blocked):
                    pixbufblock=utils.gtk_pixbuf_load(gui.theme.image_theme.blocked_overlay)
                    utils.simple_images_overlap(pix, pixbufblock,
                                                -pixbufblock.props.width,
                                                -pixbufblock.props.width)

                picture = gtk.image_new_from_pixbuf(pix)
            else:
                myanimation = utils.simple_animation_scale(contact.picture,
                                                           self.avatar_size,
                                                           self.avatar_size)

                if bool(contact.blocked):
                    pixbufblock=utils.gtk_pixbuf_load(gui.theme.image_theme.blocked_overlay)
                    static_image = myanimation.get_static_image()
                    pix = static_image.scale_simple(self.avatar_size,
                                                    self.avatar_size,
                                                    gtk.gdk.INTERP_BILINEAR)

                    utils.simple_images_overlap(pix, pixbufblock,
                                                -pixbufblock.props.width,
                                                -pixbufblock.props.width)

                    picture = gtk.image_new_from_pixbuf(pix)
                else:
                    picture = gtk.image_new_from_animation(myanimation)
        else:
            pix = utils.gtk_pixbuf_load(gui.theme.image_theme.user,
                        (self.avatar_size, self.avatar_size))

            if bool(contact.blocked):
                pixbufblock=utils.gtk_pixbuf_load(gui.theme.image_theme.blocked_overlay)
                utils.simple_images_overlap(pix, pixbufblock,
                                            -pixbufblock.props.width,
                                            -pixbufblock.props.width)

            picture = gtk.image_new_from_pixbuf(pix)

        return picture

    def _visible_func(self, model, _iter, *args):
        '''return True if the row should be displayed according to the
        value of the config'''
        obj = self._model[_iter][1]
        special = self._model[_iter][6]

        if not obj:
            return

        if isinstance(obj, e3.Group):
            if not self.show_empty_groups:
                if special and obj.type == e3.Group.OFFLINE:
                    return True

                if special and obj.type == e3.Group.ONLINE:
                    return True

                # get a list of contact objects from a list of accounts
                contacts = self.contacts.get_contacts(obj.contacts)
                con_on, con_tot = self.contacts.get_online_total_count(contacts)
                if con_on == 0:
                    return False

                if not self.show_blocked:
                    online_contacts = self.contacts.get_online_list(contacts)
                    if len([contact for contact in online_contacts \
                       if contact.blocked]) == con_on:
                        return False

            return True

        # i think joining all the text from a user with a new line between
        # and searching on one string is faster (and the user cant add
        # a new line to the entry so..)
        if self._filter_text:
            if self.hide_on_filtering:
                if not self.show_offline and obj.status == e3.status.OFFLINE:
                    return False
                if not self.show_blocked and obj.blocked:
                    return False
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
        special1 = self._model[iter1][6]
        special2 = self._model[iter2][6]

        if special2 and not special1:
            return -1
        elif special1 and not special2:
            return 1
        elif isinstance(obj1, e3.Group) and isinstance(obj2, e3.Group):
            return self.compare_groups(obj1, obj2, order1, order2)
        elif isinstance(obj1, e3.Contact) and isinstance(obj2, e3.Contact):
            return self.compare_contacts(obj1, obj2, order1, order2)
        elif isinstance(obj1, e3.Group) and isinstance(obj2, e3.Contact):
            return -1
        else:
            return 1

    def _get_selected(self):
        '''return the selected row or None'''
        iter_ = self.get_selection().get_selected()[1]

        if iter_ is None:
            return None

        return self.model.convert_iter_to_child_iter(iter_)

    def open_conversation(self, *args):
        """
        Opens a new conversation if a contact is selected
        """
        contact = self.get_contact_selected()
        if contact:
            self.contact_selected.emit(contact)

    def _on_row_activated(self, treeview, path, view_column):
        '''callback called when the user selects a row'''
        group = self.get_group_selected()
        contact = self.get_contact_selected()

        if group:
            self.group_selected.emit(group)
            if self.row_expanded(path):
                self.collapse_row(path)
            else:
                self.expand_row(path, False)
        elif contact:
            self.contact_selected.emit(contact)
        else: # "no group"-group
            if self.row_expanded(path):
                self.collapse_row(path)
            else:
                self.expand_row(path, False)

    def _on_button_press_event(self, treeview, event):
        '''callback called when the user press a button over a row
        chek if it's the roght button and emit a signal on that case'''
        if event.button == 3:
            paths = self.get_path_at_pos(int(event.x), int(event.y))

            if paths is None:
                log.debug('invalid path')
            elif len(paths) > 0:
                iterator = self.model.get_iter(paths[0])
                child_iter = self.model.convert_iter_to_child_iter(iterator)
                obj = self._model[child_iter][1]

                if isinstance(obj, e3.Group):
                    self.group_menu_selected.emit(obj)
                elif isinstance(obj, e3.Contact):
                    self.contact_menu_selected.emit(obj)
            else:
                log.debug('empty paths?')

    def escaper(self, text):
        ''' escape the text, this is a toolkit dependant method '''
        return gobject.markup_escape_text(text)

    # overrided methods
    def refilter(self):
        '''refilter the values according to the value of self.filter_text'''
        self.model.refilter()

    def is_group_selected(self):
        '''return True if a group is selected'''
        selected = self._get_selected()

        if selected is None:
            return False

        row = self._model[selected]

        if row[6]:
            return False

        return isinstance(row[1], e3.Group)

    def is_contact_selected(self):
        '''return True if a contact is selected'''
        selected = self._get_selected()

        if selected is None:
            return False

        return isinstance(self._model[selected][1], e3.Contact)

    def get_group_selected(self):
        '''return a group object if there is a group selected, None otherwise
        '''
        selected = self._get_selected()

        if selected is None:
            return None

        if self.is_group_selected():
            return self._model[selected][1]

        return None

    def is_favorite_group_selected(self):
        group = self.get_group_selected()

        if group is not None and \
            group.identifier == self.session.config.favorite_group_id:
            return True

        return False

    def get_contact_selected(self):
        '''return a contact object if there is a group selected, None otherwise
        '''
        selected = self._get_selected()

        if selected is None:
            return None

        if self.is_contact_selected():
            return self._model[selected][1]

        return None

    def get_contact_selected_group(self):
        '''return a group object for the selected contact, None otherwise
        '''
        selected = self._get_selected()

        if selected is None:
            return None

        if self.is_contact_selected():
            myiter = self._model.iter_parent(selected)
            return self._model[myiter][1]

        return None

    def add_group(self, group, special=False):
        '''add a group to the contact list'''

        try:
            weight = int(self.session.config.d_weights.get(group.identifier,
                                                           0))
        except ValueError:
            weight = 0

        self.session.config.d_weights[group.identifier] = weight

        group_data = (None, group,
            self.format_group(group),
            False, None, False, weight, special)

        for row in self._model:
            obj = row[1]
            if isinstance(obj, e3.Group):
                if obj.name == group.name:
                    log.debug('Trying to add an existing group! ' + obj.name)
                    return row.iter

        itr = self._model.append(None, group_data)

        return itr

    def remove_group(self, group):
        '''remove a group from the contact list'''
        for row in self._model:
            obj = row[1]

            if isinstance(obj, e3.Group) and obj.name == group.name:
                del self._model[row.iter]

    def add_contact(self, contact, group=None):
        '''add a contact to the contact list, add it to the group if
        group is not None'''
        try:
            weight = int(self.session.config.d_weights.get(contact.account,
                                                           0))
        except ValueError:
            weight = 0

        self.session.config.d_weights[contact.account] = weight
        offline = contact.status == e3.status.OFFLINE
        is_online  = not offline

        contact_data = (self._get_contact_pixbuf_or_default(contact),
            contact, self.format_nick(contact), True,
            utils.safe_gtk_pixbuf_load(gui.theme.image_theme.status_icons[contact.status]),
            weight, False, offline)

        # if group_offline is set and the contact is offline
        # then put it on the special offline group
        if self.group_offline and offline:
            duplicate = self._duplicate_check(contact)
            if duplicate is not None:
                return duplicate
            if not self.offline_group:
                self.session.config.d_weights['1'] = 0
                self.offline_group = e3.Group(_("Offline"),
                                              identifier='1',
                                              type_=e3.Group.OFFLINE)

                self.offline_group_iter = self.add_group(self.offline_group,
                                                         True)

            self.offline_group.contacts.append(contact.account)
            self.update_offline_group()

            return self._model.append(self.offline_group_iter, contact_data)

        # if we are in order by status mode and contact is online,
        # we add online contacts to their online group :)
        if self.order_by_status and is_online:
            duplicate = self._duplicate_check(contact)
            if duplicate is not None:
                return duplicate
            if not self.online_group:
                self.session.config.d_weights['0'] = 1

                self.online_group = e3.Group(_("Online"),
                                            identifier='0',
                                            type_=e3.Group.ONLINE)

                self.online_group_iter = self.add_group(self.online_group,
                                                        True)

            self.online_group.contacts.append(contact.account)
            self.update_online_group()

            return self._model.append(self.online_group_iter, contact_data)

        # if it has no group and we are in order by group then add it to the
        # special group "No group"
        if not group and not self.order_by_status:
            if self.no_group:
                self.no_group.contacts.append(contact.account)
                self.update_no_group()

                return self._model.append(self.no_group_iter, contact_data)
            else:
                self.no_group = e3.Group(_("No group"),
                                         identifier='0',
                                         type_ = e3.Group.NONE)

                self.no_group_iter = self.add_group(self.no_group, True)
                self.no_group.contacts.append(contact.account)
                self.update_no_group()

                return self._model.append(self.no_group_iter, contact_data)

        # if no group add it to the root, but check that it's not on a group
        # or in the root already
        if not group or self.order_by_status:
            for row in self._model:
                obj = row[1]
                # check on group
                if isinstance(obj, e3.Group):
                    for contact_row in row.iterchildren():
                        con = contact_row[1]
                        if con.account == contact.account:
                            return contact_row.iter
                # check on the root
                elif isinstance(obj, e3.Contact) and \
                        obj.account == contact.account:

                    return row.iter

            return self._model.append(None, contact_data)

        for row in self._model:
            obj = row[1]
            if isinstance(obj, e3.Group) and obj.name == group.name:
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
                    if isinstance(iobj, e3.Contact) and \
                            iobj.account == contact.account:
                        del self._model[irow.iter]

                return return_iter

        else: # for-else contingency workaround.
            log.warning("add_contact: ending for-else reached, \
                            group not found, adding new group.")
            self.add_group(group)
            result = self.add_contact(contact, group)
            self.update_group(group)
            return result

    def remove_contact(self, contact, group=None):
        '''remove a contact from the specified group, if group is None
        then remove him from all groups'''
        if not group:
            # go though the groups and the contacts without group
            for row in self._model:
                obj = row[1]
                # if we get a group we go through the contacts
                if isinstance(obj, e3.Group):
                    for contact_row in row.iterchildren():
                        con = contact_row[1]
                        # if we find it, we remove it
                        if con.account == contact.account:
                            # we remove it from tree and from group.
                            del self._model[contact_row.iter]
                            del con
                            if obj.contacts.count(contact.account) > 0:
                                obj.contacts.remove(contact.account)
                            self.update_group(obj)

                # if it's a contact without group (at the root)
                elif isinstance(obj, e3.Contact) and \
                      obj.account == contact.account:

                    # TODO: Is removing only the tree object?
                    del self._model[row.iter]
                    del obj # CHECK!!!!!

            return

        # go though the groups
        for row in self._model:
            obj = row[1]
            # if it's the group we are searching
            if isinstance(obj, e3.Group) and obj.name == group.name:
                # go through all the contacts
                for contact_row in row.iterchildren():
                    con = contact_row[1]
                    # if we find it, we remove it, from group and model
                    if con.account == contact.account:
                        del self._model[contact_row.iter]

                        if group.contacts.count(contact.account) > 0:
                            group.contacts.remove(contact.account)

                        self.update_group(group)

    def clear(self):
        '''clear the contact list, return True if the list was cleared
        False otherwise (normally returns false when clear is called before
        the contact list is in a coherent state)'''
        if not self._model:
            return False

        self.online_group = None
        self.online_group_iter = None
        self.no_group = None
        self.no_group_iter = None
        self.offline_group = None
        self.offline_group_iter = None

        self._model.clear()

        # this is the best place to put this code without putting gtk code
        # on gui.ContactList
        self.exp_column.set_visible(True)
        return True

    def update_contact(self, contact):
        '''update the data of contact'''
        try:
            weight = int(self.session.config.d_weights.get(contact.account, 0))
        except ValueError:
            weight = 0

        self.session.config.d_weights[contact.account] = weight
        offline = contact.status == e3.status.OFFLINE
        online  = not offline

        contact_data = (self._get_contact_pixbuf_or_default(contact),
            contact, self.format_nick(contact), True,
            utils.safe_gtk_pixbuf_load(gui.theme.image_theme.status_icons[contact.status]),
            weight, False, offline)

        found = False

        group_found = None
        for row in self._model:
            obj = row[1]

            if isinstance(obj, e3.Group):
                for contact_row in row.iterchildren():
                    con = contact_row[1]

                    # if we found it, update.
                    if con.account == contact.account:
                        found = True
                        group_found = obj
                        self._model[contact_row.iter] = contact_data
                        self.update_group(obj)

            # if it's a contact without group (at the root)
            elif isinstance(obj, e3.Contact) and \
                  obj.account == contact.account:

                found = True
                self._model[row.iter] = contact_data

        # if we are in order by status, the contact was found and
        # now is offline/online delete contact from offline/online
        # group and add to the oposite.
        if self.order_by_status and found:
            # y todavia no estoy en el grupo.
            if offline and \
                not self.offline_group \
                or group_found != self.offline_group:

                self.remove_contact(contact, group_found)
                self.add_contact(contact, self.offline_group)

            if online and \
                not self.online_group \
                or group_found != self.online_group:

                self.remove_contact(contact, group_found)
                self.add_contact(contact, self.online_group)

        if self.order_by_group and self.group_offline and found:
            # y todavia no estoy en el grupo.
            if offline and group_found != self.offline_group:
                self.remove_contact(contact, group_found)
                self.add_contact(contact, self.offline_group)

            if online and group_found == self.offline_group:
                self.remove_contact(contact, self.offline_group)
                if len(contact.groups) == 0:
                    self.add_contact(contact)
                else:
                    for group in contact.groups:
                        self.add_contact(contact, self.session.groups[group])

    def update_no_group(self):
        '''update the special "No group" group'''
        if self.no_group_iter is None:
            return

        group_data = (None, self.no_group,
            self.format_group(self.no_group),
            False, None, 0, True, False)

        self._model[self.no_group_iter] = group_data
        self.update_group(self.no_group)

    def update_online_group(self):
        '''update the special "Online" group '''
        group_data = (None, self.online_group,
            self.format_group(self.online_group),
            False, None, 0, True, False)

        self._model[self.online_group_iter] = group_data
        self.update_group(self.online_group)

    def update_offline_group(self):
        '''update the special "Offline" group'''
        group_data = (None, self.offline_group,
            self.format_group(self.offline_group),
            False, None, 0, True, False)

        self._model[self.offline_group_iter] = group_data
        self.update_group(self.offline_group)

    def expand_groups(self):
        ''' expand groups while searching'''
        if self.is_searching:
            self.expand_all()
            return

    def un_expand_groups(self):
        ''' restore groups after a search'''
        self.get_selection().unselect_all()
        for row in self._model:
            obj = row[1]
            if isinstance(obj, e3.Group):
                self.update_group(obj)

    def update_group(self, group):
        '''update the data of group'''

        try:
            weight = int(self.session.config.d_weights.get(group.identifier,
                                                           0))
        except ValueError:
            weight = 0

        self.session.config.d_weights[group.identifier] = weight

        for row in self._model:
            obj = row[1]
            if isinstance(obj, e3.Group) and \
                obj.identifier == group.identifier:

                path = None
                childpath = None
                if group.name in self.group_state:
                    state = self.group_state[group.name]
                    childpath = self._model.get_path(row.iter)
                    path = self.model.convert_child_path_to_path(childpath)
                    if path:
                        if state:
                            self.expand_row(path, False)
                        else:
                            self.collapse_row(path)

                group.contacts = obj.contacts
                group_data = (None, group,
                              self.format_group(group),
                              False, None, weight,
                              (group.type != e3.base.Group.STANDARD), False)

                self._model[row.iter] = group_data

                if path is None and childpath is not None:
                    path = self.model.convert_child_path_to_path(childpath)
                    if path and state:
                        self.expand_row(path, False)

    def set_avatar_size(self, size):
        """set the size of the avatars on the contact list
        """
        self.avatar_size = size
        self.pbr.set_property('dimension', size)

    def compare_contacts(self, contact1, contact2, order1=0, order2=0):
        '''compare two contacts and return 1 if contact1 should go first, 0
        if equal and -1 if contact2 should go first, use order1 and order2 to
        override the group sorting (the user can set the values on these to
        have custom ordering)'''

        override = cmp(order2, order1)

        if override != 0:
            return override

        if self.order_by_name:
            # first order by status, online contacts first
            result = cmp(e3.status.ORDERED.index(contact1.status),
                e3.status.ORDERED.index(contact2.status))
            if result == 0:
                #same status, order by name
                result = cmp(Plus.msnplus_strip(contact1.display_name),
                            Plus.msnplus_strip(contact2.display_name))
            return result

        result = cmp(e3.status.ORDERED.index(contact1.status),
            e3.status.ORDERED.index(contact2.status))

        if result != 0:
            return result

        if self.order_by_status:
            return cmp(contact1.display_name, contact2.display_name)

        if len(contact1.groups) == 0:
            if len(contact2.groups) == 0:
                return cmp(contact1.display_name, contact2.display_name)
            else:
                return -1
        elif len(contact2.groups) == 0:
            return 1

        return 0

    def _duplicate_check(self, contact):
        '''check if the contact isn't there already'''
        for row in self._model:
            obj = row[1]
            if isinstance(obj, e3.Group):
                for contact_row in row.iterchildren():
                    con = contact_row[1]
                    if con.account == contact.account:
                        return contact_row.iter

        return None

    def _on_drag_data_get(self, widget, context, selection, target_id, etime):
        if self.is_contact_selected():
            account = self.get_contact_selected().account
            display_name = self.get_contact_selected().display_name

            if selection.target == 'text/html':
                display_name = gui.base.Plus.msnplus_parse(display_name)

                for x in range(len(display_name)):
                    if isinstance(display_name[x], dict):
                        display_name[x] = '<img src="file://%s" alt="%s">' %\
                                (display_name[x]["src"], display_name[x]["alt"])

                selection.set(selection.target,
                    8, u'{0} &lt;<a href="mailto:{1}">{1}</a>&gt;'.format(''.join(display_name), account))
            elif selection.target == 'text/plain':
                selection.set(selection.target, 8, u'%s <%s>' % (Plus.msnplus_strip(display_name), account))

    def _on_drag_drop(self, widget, drag_context, x, y, time):
        drag_context.finish(True, False, time)
        if self.session.config.b_order_by_group:
            group_src = self.get_contact_selected_group()

            try:
                pos = widget.get_dest_row_at_pos(x, y)[0][0]
            except TypeError: # yes, this can happen if you drag into a blank area
                return True
            group_des = self.model[pos][1]

            if group_src and group_src != group_des and not self._model[pos][6]:

                self.session.move_to_group(self.get_contact_selected().account,
                                           group_src.identifier,
                                           group_des.identifier)

        return True

    def select_top_contact(self):
        ''' Select the topmost contact '''
        selected = self.get_selection()
        for row in self.model:
            obj = row[1]
            if isinstance(obj, e3.Group):
                for contact_row in row.iterchildren():
                    selected.select_path(contact_row.path)
                    return
            elif isinstance(obj, e3.Contact):
                selected.select_path(row.path)
                return
