import os
import gtk
import pango

import protocol

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

def style_to_pango_font_description(style):
    '''receives a protocol.Style and returns a pango.FontDescription'''
    fdesc = pango.FontDescription()
    fdesc.set_family(style.font)
    if style.size < 6 or style.size > 32:
        fdesc.set_size(10 * pango.SCALE)
    else:
        fdesc.set_size(style.size * pango.SCALE)

    if style.bold:
        fdesc.set_weight(pango.WEIGHT_BOLD)

    if style.italic:
        fdesc.set_style(pango.STYLE_ITALIC)

    return fdesc

def pango_font_description_to_style(fdesc):
    '''receives a pango.FontDescription and returns a protocol.Style'''
    font = fdesc.get_family()
    
    font_italic = False
    if fdesc.get_style() != pango.STYLE_NORMAL:
        font_italic = True

    font_bold = False
    if fdesc.get_weight() == pango.WEIGHT_BOLD or \
     fdesc.get_weight() == pango.WEIGHT_ULTRABOLD or \
     fdesc.get_weight() == pango.WEIGHT_HEAVY:
        font_bold = True

    font_underline = False
    font_strike = False

    font_size = fdesc.get_size() / pango.SCALE
    if font_size < 6 or font_size > 32:
        font_size = 10

    return protocol.Style(font, protocol.Color(0, 0, 0), font_bold, 
        font_italic, font_underline, font_strike, font_size)

