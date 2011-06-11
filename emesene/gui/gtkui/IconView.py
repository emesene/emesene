'''module to define a class to present a list of thumbnails'''
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
import gobject

import thread
import time
import gc
from gui.base import MarkupParser

# Class that holds the iconview from the avatar chooser dialog
class IconView(gtk.HBox):
    ''' class representing a listview in icon mode
        (using gtk.IconView + gtk.ListStore)        '''
    TYPE_SYSTEM_PICS, TYPE_CONTACTS_PICS, TYPE_SELF_PICS = range(3)
    def __init__(self, label, path_list, on_remove_cb, on_accept_cb,
                 iconv_type, on_drag_data_accepted):
        gtk.HBox.__init__(self)
        self.set_spacing(4)

        self.on_remove_cb = on_remove_cb
        self.on_accept_cb = on_accept_cb
        self.on_drag_data_accepted = on_drag_data_accepted
        self.iconv_type = iconv_type

        self.model = gtk.ListStore(gtk.gdk.Pixbuf, str)
        self.iconview = gtk.IconView(self.model)
        self.iconview.enable_model_drag_dest([('text/uri-list', 0, 0)],
                                gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_COPY)
        self.iconview.connect("drag-data-received", self._drag_data_received)
        self.iconview.set_pixbuf_column(0)
        self.iconview.connect("item-activated", self._on_icon_activated)
        self.iconview.connect("button_press_event", self.pop_up)

        self.label = gtk.Label(label)

        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.scroll.set_shadow_type(gtk.SHADOW_IN)
        self.scroll.add(self.iconview)
        self.pack_start(self.scroll, True, True)

        self.stop = False
        # Start a new thread to fill the iconview with images from path_list
        thread.start_new_thread(self.fill, (path_list,))

    def stop_and_clear(self):
        ''' stop the threads and clean the model '''
        self.stop = True
        self.model.clear()

    def fill(self, path_list):
        '''fill the IconView with avatars from the list of pictures'''
        for search_path in path_list:
            if os.path.exists(search_path):
                for path in os.listdir(search_path):
                    name = os.path.splitext(path)[0]
                    if self.stop:
                        return False
                    full_path = os.path.join(search_path, path)
                    if not name.endswith('_thumb') and \
                        not path.endswith(('tmp', 'xml', 'db', 'info',
                                           'last', 'avatars')) and \
                        not os.path.isdir(full_path):
                        gtk.gdk.threads_enter()
                        self.add_picture(full_path)
                        # make update the iconview
                        self.iconview.queue_draw()
                        gtk.gdk.threads_leave()

                        # give some time to the main thread (for GUI updates)
                        time.sleep(0.001)
        # Force Garbage Collector to tidy objects
        # see http://faq.pygtk.org/index.py?req=show&file=faq08.004.htp
        gc.collect()

    def pop_up(self, iconview, event):
        ''' manage the context menu (?) '''
        if event.button == 3 and self.iconv_type != IconView.TYPE_SYSTEM_PICS:
            path = self.iconview.get_path_at_pos(int(event.x), int(event.y))
            if path != None:
                self.iconview.select_path(path)

                if self.on_remove_cb != None:
                    remove_menu = gtk.Menu()
                    remove_item = gtk.ImageMenuItem(_('Delete'))
                    remove_item.set_image(gtk.image_new_from_stock(\
                        gtk.STOCK_REMOVE, gtk.ICON_SIZE_MENU))
                    remove_item.connect('activate', self.on_remove_cb)
                    remove_menu.append(remove_item)
                    remove_menu.popup(None, None, None, event.button,
                        event.time)
                    remove_menu.show_all()

    def _drag_data_received(self, treeview, context, posx, posy, \
                            selection, info, timestamp):
        '''method called on an image dragged to the view'''
        urls = selection.data.split('\n')
        for url in urls:
            path = url.replace('file://', '')
            path = path.replace('\r', '')

            # the '\x00' value makes an error
            path = path.replace(chr(0), '')

            path = MarkupParser.urllib.url2pathname(path)

            # this seems to be an error on ntpath but we take care :S
            try:
                if os.path.exists(path):
                    self.on_drag_data_accepted(path,
                        gtk.gdk.PixbufAnimation(path).is_static_image())
            except TypeError, error:
                if self.on_drag_data_accepted is None:
                    print _("Could not add picture:\n %s") % \
                        _("Drag and drop to this IconView is not allowed.")
                else:
                    print _("Could not add picture:\n %s") % (str(error),)

    def add_picture(self, path):
        '''Adds an avatar into the IconView'''
        try:
            if os.path.exists(path) and os.access(path, os.R_OK)\
                    and not self.is_in_view(path):
                try:
                    animation = gtk.gdk.PixbufAnimation(path)
                    if animation.is_static_image():
                        pixbuf = gtk.gdk.pixbuf_new_from_file(path)
                    else:
                        pixbuf = animation.get_static_image().scale_simple( \
                                    64, 64, gtk.gdk.INTERP_BILINEAR)
                except gobject.GError:
                    print _('image at %s could not be loaded') % (path, )
                    print gobject.GError
                    return

                # On nt images are 128x128 (48x48 on xp)
                # On kde, images are 64x64
                if (self.iconv_type == IconView.TYPE_SYSTEM_PICS or \
                 self.iconv_type == IconView.TYPE_CONTACTS_PICS) and \
                 (pixbuf.get_width() != 96 or pixbuf.get_height() != 96):
                    pixbuf = pixbuf.scale_simple(96, 96,
                                        gtk.gdk.INTERP_BILINEAR)

                if self.model != None and not self.stop:
                    self.model.append([pixbuf, path])
                    # Esplicitely delete gtkpixbuf
                    del pixbuf
            else:
                print path, 'not readable'
        except gobject.GError:
            print "image at %s could not be loaded" % path

    def is_in_view(self, filename):
        '''return True if filename already on the iconview'''
        if os.name == 'nt':
            # nt doesn't include os.path.samefile
            return False

        for (pixbuf, path) in self.model:
            if os.path.samefile(filename, path):
                return True
            if self.stop:
                return False

        return False

    def _on_icon_activated(self, *args):
        '''method called when a picture is double clicked'''
        if self.on_accept_cb != None:
            self.on_accept_cb(None)

    def get_selected_items(self):
        ''' gets the selected pictures '''
        return self.iconview.get_selected_items()
