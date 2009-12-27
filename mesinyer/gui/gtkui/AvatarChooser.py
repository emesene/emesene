'''module to define a class to select an avatar'''
import os
import gtk
import gobject

import gui
import utils
import extension

class AvatarChooser(gtk.Window):
    '''A dialog to choose an avatar'''

    def __init__(self, response_cb, picture_path='',
            cache_path='.'):
        '''Constructor, response_cb receive the response number, the new file
        selected and a list of the paths on the icon view.
        picture_path is the path of the current display picture,
        '''
        gtk.Window.__init__(self)
        self.set_icon(gui.theme.logo)

        self.response_cb = response_cb
        self.cache_path = cache_path

        self.set_title("Avatar chooser")
        self.set_default_size(602, 400)
        self.set_border_width(4)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)

        self.model = gtk.ListStore(gtk.gdk.Pixbuf, str)

        self.view = gtk.IconView(self.model)
        self.view.enable_model_drag_dest([('text/uri-list', 0, 0)],
                gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_COPY)
        self.view.connect("drag-data-received", self._drag_data_received)

        self.view.set_pixbuf_column(0)
        self.view.connect("item-activated", self._on_icon_activated)

        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        scroll.add(self.view)

        vbox = gtk.VBox(spacing=4)
        side_vbox = gtk.VBox(spacing=4)
        hbox = gtk.HBox(spacing=4)

        hbbox = gtk.HButtonBox()
        hbbox.set_spacing(4)
        hbbox.set_layout(gtk.BUTTONBOX_END)

        vbbox = gtk.VButtonBox()
        vbbox.set_spacing(4)
        vbbox.set_layout(gtk.BUTTONBOX_START)

        b_clear = gtk.Button("No picture")
        b_add = gtk.Button(stock=gtk.STOCK_ADD)
        b_remove = gtk.Button(stock=gtk.STOCK_REMOVE)
        b_remove_all = gtk.Button("Remove all")
        b_accept = gtk.Button(stock=gtk.STOCK_OK)
        b_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)

        b_clear.connect('clicked', self._on_clear)
        b_add.connect('clicked', self._on_add)
        b_remove.connect('clicked', self._on_remove)
        b_remove_all.connect('clicked', self._on_remove_all)
        b_accept.connect('clicked', self._on_accept)
        b_cancel.connect('clicked', self._on_cancel)
        self.connect('delete-event', self._on_close)
        self.connect("key-press-event", self.on_key_press)

        self.img_current = gtk.Image()
        self.img_current.set_size_request(96, 96)
        frame_current = gtk.Frame("Current")
        frame_current.add(self.img_current)

        hbbox.pack_start(b_clear, False)
        hbbox.pack_start(b_cancel, False)
        hbbox.pack_start(b_accept, False)

        vbbox.pack_start(b_add, False)
        vbbox.pack_start(b_remove, False)
        vbbox.pack_start(b_remove_all, False)

        side_vbox.pack_start(frame_current, False)
        side_vbox.pack_start(vbbox)

        hbox.pack_start(scroll, True, True)
        hbox.pack_start(side_vbox, False, False)

        vbox.pack_start(hbox, True, True)
        vbox.pack_start(hbbox, False)

        vbox.show_all()
        self.add(vbox)

        self.fill()
        self.set_current_picture(picture_path)

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
            return self.model[iter_]

        return None

    def get_selected_iter(self):
        '''return the selected iter or None'''
        if len(self.view.get_selected_items()) > 0:
            item = self.view.get_selected_items()[0]
            return self.model.get_iter(item)

        return None

    def get_iter_from_filename(self, path):
        '''return the iter of a filename or None'''
        for row in self.model:
            pixbuf, filename = row

            if samefile(filename, path):
                return row.iter

        return None


    def fill(self):
        '''fill the IconView with avatars from the list of pictures'''
        for path in os.listdir(self.cache_path):
            if not os.path.splitext(path)[0].endswith('_thumb'):
                self.add_picture(os.path.join(self.cache_path, path))

    def is_in_view(self, filename):
        '''return True if filename already on the iconview'''
        for pixbuf, path in self.model:
            if samefile(filename, path):
                return True

        return False

    def add_picture(self, path):
        '''Adds an avatar into the IconView'''
        if os.path.exists(path) and os.access(path, os.R_OK)\
                and not self.is_in_view(path):
            try:
                pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(path,64,64)
                self.model.append([pixbuf, path])
            except gobject.GError:
                print 'image at %s could not be loaded' % (path, )
                print gobject.GError
        else:
            print path, 'not readable'

    def remove(self, path):
        '''remove the avatar in path'''
        del self.model[self.get_iter_from_filename(path)]
        try:
            os.remove(path)
            parts = os.path.splitext(path)
            os.remove(parts[0] + "_thumb" + parts[1])
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
        for (pixbuf, path) in self.model:
            self.remove(path)

        self.model.clear()

    def _drag_data_received(self, treeview, context, x_coord, y_coord,
            selection, info, timestamp):
        '''method called on an image dragged to the view'''
        urls = selection.data.split('\n')

        for url in urls:
            path = url.replace('file://', '')
            path = path.replace('\r', '')

            # the '\x00' value makes an error
            path = path.replace(chr(0), '')

            # this seems to be an error on ntpath but we take care :S
            try:
                if os.path.exists(path):
                    self.add_picture(path)
            except TypeError, error:
                extension.get_default('dialog').error(
                        "Could not add picture:\n %s" % (str(error),))

    def _on_icon_activated(self, *args):
        '''method called when a picture is double clicked'''
        self._on_accept(None)

    def _on_add(self, button):
        '''called when the user select the add button'''
        def _on_image_selected(response, path):
            '''method called when an image is selected'''
            if response == gui.stock.ACCEPT:
                self.add_picture(path)

        class_ = extension.get_default('image chooser')
        class_(os.path.expanduser('~'), _on_image_selected).show()

    def _on_remove(self, event):
        '''Removes the selected avatar'''
        self.remove_selected()

    def _on_remove_all(self, button):
        '''Removes all avatars from the cache'''
        def on_response_cb(response):
            '''response callback for the confirm dialog'''
            if response == gui.stock.YES:
                self.remove_all()

        extension.get_default('dialog').yes_no(
            "Are you sure you want to remove all items?", on_response_cb)

    def _on_accept(self, button):
        '''method called when the user clicks the button'''
        selected = self.get_selected()
        filename = ''

        if selected:
            filename = selected[1]

            self.hide()
            self.response_cb(gui.stock.ACCEPT, filename)
        else:
            extension.get_default('dialog').error("No picture selected")

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

def samefile(path1, path2):
    '''return True if the files are the same file
    this is a workaround to os.path.samefile that doesn't exist
    on windows'''
    path1 = os.path.abspath(os.path.normpath(path1))
    path2 = os.path.abspath(os.path.normpath(path2))

    return ((hasattr(os.path, 'samefile') and \
       os.path.samefile(path1, path2)) or \
       (path1.lower() == path2.lower()))
