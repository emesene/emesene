import os
import gtk

def safe_gtk_image_load(path):
    '''try to return a gtk image from path, if fails, return a broken image'''
    if file_readable(path):
        return gtk.image_new_from_file(path)
    else:
        return gtk.image_new_from_stock(gtk.STOCK_MISSING_IMAGE, 
            gtk.ICON_SIZE_DIALOG)

def file_readable(path):
    return os.access(path, os.R_OK) and os.path.isfile(path)
