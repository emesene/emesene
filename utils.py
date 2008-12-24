import os
import gtk

pixbufs = {}

def safe_gtk_image_load(path):
    '''try to return a gtk image from path, if fails, return a broken image'''
    if file_readable(path):
        return gtk.image_new_from_file(path)
    else:
        return gtk.image_new_from_stock(gtk.STOCK_MISSING_IMAGE, 
            gtk.ICON_SIZE_DIALOG)

def safe_gtk_pixbuf_load(path):
    '''try to return a gtk pixbuf from path, if fials, return None'''
    path = os.path.abspath(path)

    if file_readable(path):
        if path in pixbufs:
            return pixbufs[path]
        else:
            pixbuf = gtk.gdk.pixbuf_new_from_file(path)
            pixbufs[path] = pixbuf
            return pixbuf
    else:
        return None 

def file_readable(path):
    return os.access(path, os.R_OK) and os.path.isfile(path)
