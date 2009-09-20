'''module to define a class to select an image'''
import os
import gtk
import gobject

import gui
import extension

class ImageChooser(gtk.Window):
    '''a class to select images'''

    def __init__(self, path, response_cb):
        '''class constructor, path is the directory where the
        dialog opens'''
        gtk.Window.__init__(self)

        self.response_cb = response_cb

        self.set_title("Image Chooser")
        self.set_default_size(600, 400)
        self.set_border_width(4)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)

        self.image = None
        self.vbox = gtk.VBox(spacing=4)

        self.file_chooser = gtk.FileChooserWidget()
        self.file_chooser.set_current_folder(path)

        hbbox = gtk.HButtonBox()
        hbbox.set_spacing(4)
        hbbox.set_layout(gtk.BUTTONBOX_END)

        b_accept = gtk.Button(stock=gtk.STOCK_OK)
        b_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)

        b_accept.connect('clicked', self._on_accept)
        b_cancel.connect('clicked', self._on_cancel)
        self.connect('delete-event', self._on_close)
        self.file_chooser.connect("file-activated", self._on_accept)

        hbbox.pack_start(b_cancel, False)
        hbbox.pack_start(b_accept, False)

        vbox = gtk.VBox()
        self.vbox.pack_start(self.file_chooser, True, True)

        vbox.add(self.vbox)
        vbox.pack_start(hbbox, False)
        self.add(vbox)
        vbox.show_all()

        self._add_filters()
        self._add_preview()

    def _add_filters(self):
        '''
        Adds all the possible file filters to the dialog. The filters correspond
        to the gdk available image formats
        '''

        # All files filter
        all_files = gtk.FileFilter()
        all_files.set_name('All files')
        all_files.add_pattern('*')

        # All images filter
        all_images = gtk.FileFilter()
        all_images.set_name('All images')

        filters = []
        formats = gtk.gdk.pixbuf_get_formats()
        for format_ in formats:
            filter_ = gtk.FileFilter()
            name = "%s (*.%s)" % (format_['description'], format_['name'])
            filter_.set_name(name)

            for mtype in format_['mime_types']:
                filter_.add_mime_type(mtype)
                all_images.add_mime_type(mtype)

            for pattern in format_['extensions']:
                tmp = '*.' + pattern
                filter_.add_pattern(tmp)
                all_images.add_pattern(tmp)

            filters.append(filter_)

        self.file_chooser.add_filter(all_files)
        self.file_chooser.add_filter(all_images)
        self.file_chooser.set_filter(all_images)

        for filter_ in filters:
            self.file_chooser.add_filter(filter_)

    def _add_preview(self):
        '''
        Adds a preview widget to the file chooser
        '''

        self.image = gtk.Image()
        self.image.set_size_request(128, 128)
        self.image.show()

        self.file_chooser.set_preview_widget(self.image)
        self.file_chooser.set_preview_widget_active(True)

        self.file_chooser.connect('update-preview', self._on_update_preview)

    def _on_accept(self, button):
        '''method called when the user clicks the button'''
        filename = get_filename(self)
        if os.path.isfile(filename):
            self.hide()
            self.response_cb(gui.stock.ACCEPT, filename)
        else:
            extension.get_default('dialog').error("No picture selected")

    def _on_cancel(self, button):
        '''method called when the user clicks the button'''
        self.hide()
        self.response_cb(gui.stock.CANCEL, get_filename(self))

    def _on_close(self, window, event):
        '''called when the user click on close'''
        self.hide()
        self.response_cb(gui.stock.CLOSE, get_filename(self))

    def _on_update_preview(self, filechooser):
        '''
        Updates the preview image
        '''
        path = get_preview_filename(self)

        if path:
            # if the file is smaller than 1MB we
            # load it, otherwise we dont
            if os.path.isfile(path) and os.path.getsize(path) <= 1000000:
                try:
                    pixbuf = gtk.gdk.pixbuf_new_from_file(get_filename(self))
                    if pixbuf.get_width() > 128 and pixbuf.get_height() > 128:
                        pixbuf = pixbuf.scale_simple(128, 128,
                                gtk.gdk.INTERP_BILINEAR)
                    self.image.set_from_pixbuf(pixbuf)

                except gobject.GError:
                    self.image.set_from_stock(gtk.STOCK_DIALOG_ERROR,
                        gtk.ICON_SIZE_DIALOG)
            else:
                self.image.set_from_stock(gtk.STOCK_DIALOG_ERROR,
                    gtk.ICON_SIZE_DIALOG)

def get_filename(self):
    '''Shortcut to get a properly-encoded filename from a file chooser'''
    filename = self.file_chooser.get_filename()
    if filename and gtk.gtk_version >= (2, 10, 0):
        return gobject.filename_display_name(filename)
    else:
        return filename

def get_preview_filename(self):
    '''Shortcut to get a properly-encoded preview filename'''
    filename = self.file_chooser.get_preview_filename()
    if filename and gtk.gtk_version >= (2, 10, 0):
        return gobject.filename_display_name(filename)
    else:
        return filename
