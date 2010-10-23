'''module to define a class to select an avatar'''
import os
import gtk
import gobject

import gui
import utils
import extension

import gc

from IconView import IconView

class AvatarChooser(gtk.Window):
    '''A dialog to choose an avatar'''

    def __init__(self, response_cb, picture_path='',
            cache_path='.', contact_cache_path='.',
            faces_paths=[], avatar_manager = None):
        '''Constructor, response_cb receive the response number, the new file
        selected and a list of the paths on the icon view.
        picture_path is the path of the current display picture,
        '''
        gtk.Window.__init__(self)
        self.set_modal(True)
        self.set_icon(gui.theme.logo)

        self.response_cb = response_cb
        self.avatar_manager = avatar_manager

        self.set_title(_("Avatar chooser"))
        self.set_default_size(620, 400)
        self.set_border_width(4)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)

        self.views = []
        self.views.append(IconView(_('Used'), [cache_path], self))
        self.views.append(IconView(_('System pictures'), faces_paths, self))
        self.views.append(IconView(_('Contact pictures'), [contact_cache_path], self))

        vbox = gtk.VBox(spacing=4)
        side_vbox = gtk.VBox(spacing=4)
        hbox = gtk.HBox(spacing=4)

        hbbox = gtk.HButtonBox()
        hbbox.set_spacing(4)
        hbbox.set_layout(gtk.BUTTONBOX_END)

        vbbox = gtk.VButtonBox()
        vbbox.set_spacing(4)
        vbbox.set_layout(gtk.BUTTONBOX_START)

        b_clear = gtk.Button(_("No picture"))
        self.b_add = gtk.Button(stock=gtk.STOCK_ADD)
        self.b_remove = gtk.Button(stock=gtk.STOCK_REMOVE)
        self.b_remove_all = gtk.Button(_("Remove all"))
        b_accept = gtk.Button(stock=gtk.STOCK_OK)
        b_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)

        b_clear.connect('clicked', self._on_clear)
        self.b_add.connect('clicked', self._on_add)
        self.b_remove.connect('clicked', self.on_remove)
        self.b_remove_all.connect('clicked', self._on_remove_all)
        b_accept.connect('clicked', self.on_accept)
        b_cancel.connect('clicked', self._on_cancel)
        self.connect('delete-event', self._on_close)
        self.connect("key-press-event", self.on_key_press)

        self.img_current = gtk.Image()
        self.img_current.set_size_request(96, 96)
        frame_current = gtk.Frame(_("Current"))
        frame_current.add(self.img_current)

        hbbox.pack_start(b_clear, False)
        hbbox.pack_start(b_cancel, False)
        hbbox.pack_start(b_accept, False)

        vbbox.pack_start(self.b_add, False)
        vbbox.pack_start(self.b_remove, False)
        vbbox.pack_start(self.b_remove_all, False)

        side_vbox.pack_start(frame_current, False)
        side_vbox.pack_start(vbbox)

        self.notebook = gtk.Notebook()
        self.notebook.set_show_tabs(True)

        for view in self.views:
            self.notebook.append_page(view, view.label)
        self.notebook.connect("switch-page", self._on_tab_changed)

        hbox.pack_start(self.notebook, True, True)
        hbox.pack_start(side_vbox, False, False)

        vbox.pack_start(hbox, True, True)
        vbox.pack_start(hbbox, False)

        vbox.show_all()
        self.add(vbox)

        self.set_current_picture(picture_path)

    def _on_tab_changed(self, notebook, page, page_num):
        view = self.views[page_num]
        if page_num == 1: # System Pictures
            self.b_add.set_sensitive(False)
            self.b_remove.set_sensitive(False)
            self.b_remove_all.set_sensitive(False)
        elif page_num == 2: #Contact Pictures
            self.b_add.set_sensitive(False)
            self.b_remove.set_sensitive(True)
            self.b_remove_all.set_sensitive(True)
        else:
            self.b_add.set_sensitive(True)
            self.b_remove.set_sensitive(True)
            self.b_remove_all.set_sensitive(True)

    def set_icon(self, icon):
        '''set the icon of the window'''
        if utils.file_readable(icon):
            gtk.Window.set_icon(self,
                utils.safe_gtk_image_load(icon).get_pixbuf())

    def set_current_picture(self, path):
        '''set the current picture on the frame'''
        if os.path.exists(path):
            pixbuf = gtk.gdk.pixbuf_new_from_file(path)
            self.img_current.set_from_pixbuf(pixbuf)

    def get_selected(self):
        '''return a tuple (pixbuf, path) of the selection, or None'''
        iter_ = self.get_selected_iter()

        if iter_:
            view = self.views[self.notebook.get_current_page()]
            return view.model[iter_]

        return None

    def get_selected_iter(self):
        '''return the selected iter or None'''
        view = self.views[self.notebook.get_current_page()]
        if len(view.get_selected_items()) > 0:
            item = view.get_selected_items()[0]
            return view.model.get_iter(item)

        return None

    def get_iter_from_filename(self, path):
        '''return the iter of a filename or None'''
        view = self.views[self.notebook.get_current_page()]
        for row in view.model:
            pixbuf, filename = row

            if samefile(filename, path):
                return row.iter

        return None

    def remove(self, path):
        '''remove the avatar in path'''
        view = self.views[self.notebook.get_current_page()]
        del view.model[self.get_iter_from_filename(path)]
        try:
            os.remove(path)
            parts = os.path.splitext(path)
            #os.remove(parts[0] + "_thumb" + parts[1])
        except OSError:
            print "could not remove", path

    def remove_selected(self):
        '''Removes avatar from a TreeIter'''
        selected = self.get_selected()

        if selected:
            (pixbuf, path) = selected
            self.remove(path)

    def remove_all(self):
        '''remove all the items on the view'''
        view = self.views[self.notebook.get_current_page()]
        for (pixbuf, path) in view.model:
            self.remove(path)

        view.model.clear()

    def _on_icon_activated(self, *args):
        '''method called when a picture is double clicked'''
        self.on_accept(None)

    def _on_add(self, button):
        '''called when the user select the add button'''
        def _on_image_selected(response, path):
            '''method called when an image is selected'''
            if response == gui.stock.ACCEPT:
                animation = gtk.gdk.PixbufAnimation(path)
                #we don't need to resize animation here
                if not animation.is_static_image():
                    view = self.views[self.notebook.get_current_page()]
                    view.add_picture(path)
                    return
                self._on_image_area_selector(path)

        class_ = extension.get_default('image chooser')
        class_(os.path.expanduser('~'), _on_image_selected).show()

    def _on_image_area_selector(self, path):
        '''called when the user must resize the added image'''
        def _on_image_resized(response, pix):
            '''method called when an image is selected'''
            if response == gtk.RESPONSE_OK:
                if self.avatar_manager is not None:
                    view = self.views[self.notebook.get_current_page()]
                    pix, avpath = self.avatar_manager.add_new_avatar_from_pix(pix)
                    view.add_picture(avpath)

        class_ = extension.get_default('image area selector')
        class_(_on_image_resized, gtk.gdk.pixbuf_new_from_file(path),
               parent=self).run()

    def on_remove(self, event):
        '''Removes the selected avatar'''
        self.remove_selected()

    def _on_remove_all(self, button):
        '''Removes all avatars from the cache'''
        def on_response_cb(response):
            '''response callback for the confirm dialog'''
            if response == gui.stock.YES:
                self.remove_all()

        extension.get_default('dialog').yes_no(
            _("Are you sure you want to remove all items?"),
            on_response_cb)

    def on_accept(self, button):
        '''method called when the user clicks the button'''
        selected = self.get_selected()
        filename = ''

        if selected:
            filename = selected[1]

            self.hide()
            print filename
            self.response_cb(gui.stock.ACCEPT, filename)
        else:
            extension.get_default('dialog').error(_("No picture selected"))

    def _on_cancel(self, button):
        '''method called when the user clicks the button'''
        self.hide()
        self.response_cb(gui.stock.CANCEL, '')

    def _on_clear(self, button):
        '''method called when the user clicks the button'''
        self.hide()
        self.response_cb(gui.stock.CLEAR, '')

    def _on_close(self, window, event):
        '''called when the user click on close'''
        self.hide()
        self.response_cb(gui.stock.CLOSE, '')

    def on_key_press(self , widget, event):
        '''called when the user press a key'''
        if event.keyval == gtk.keysyms.Delete:
            self.remove_selected()

    def stop_and_clear(self):
        for view in self.views:
            view.stop_and_clear()
        # Force Garbage Collector to tidy objects
        # see http://faq.pygtk.org/index.py?req=show&file=faq08.004.htp
        gc.collect()

def samefile(path1, path2):
    '''return True if the files are the same file
    this is a workaround to os.path.samefile that doesn't exist
    on windows'''
    path1 = os.path.abspath(os.path.normpath(path1))
    path2 = os.path.abspath(os.path.normpath(path2))

    return ((hasattr(os.path, 'samefile') and \
       os.path.samefile(path1, path2)) or \
       (path1.lower() == path2.lower()))
