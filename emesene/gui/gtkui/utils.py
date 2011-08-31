'''utility module'''
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
import pango
import hashlib
import tempfile

import glib
import Queue
import threading

import e3
import urllib

pixbufs = {}

def safe_gtk_image_load(path, size=None):
    '''try to return a gtk image from path, if fails, return a broken image'''
    if file_readable(path):
        pixbuf = safe_gtk_pixbuf_load(path, size)
        return gtk.image_new_from_pixbuf(pixbuf)
    else:
        return gtk.image_new_from_stock(gtk.STOCK_MISSING_IMAGE,
            gtk.ICON_SIZE_DIALOG)

def gtk_ico_image_load(path, icosize=None):
    '''try to return a gtk image from path, if fails, return a broken image'''
    if file_readable(path):
        pixbuf = gtk_pixbuf_load(path)
        iconset = gtk.IconSet(pixbuf)
        return gtk.image_new_from_icon_set(iconset,icosize)
    else:
        return gtk.image_new_from_stock(gtk.STOCK_MISSING_IMAGE,
            gtk.ICON_SIZE_DIALOG)

def safe_gtk_pixbuf_load(path, size=None, animated=False):
    '''try to return a gtk pixbuf from path, if fails, return None'''
    if not os.path.isabs(path):
        path = os.path.abspath(path)

    if animated:
        creator = gtk.gdk.PixbufAnimation
    else:
        creator = gtk.gdk.pixbuf_new_from_file

    if file_readable(path):
        if (path, size) in pixbufs:
            return pixbufs[(path, size)]
        else:
            pixbuf = creator(path)

            if size is not None:
                width, height = size
                pixbuf = pixbuf.scale_simple(width, height,
                        gtk.gdk.INTERP_BILINEAR)

            pixbufs[(path, size)] = pixbuf
            return pixbuf
    else:
        return None


def gtk_pixbuf_load(path, size=None, animated=False):
    '''try to return a gtk pixbuf from path, if fails, return None'''
    if not os.path.isabs(path):
        path = os.path.abspath(path)
    if animated:
        creator = gtk.gdk.PixbufAnimation
    else:
        creator = gtk.gdk.pixbuf_new_from_file

    if file_readable(path):
        pixbuf = creator(path)
        if size is not None:
            width, height = size
            pixbuf = pixbuf.scale_simple(width, height,gtk.gdk.INTERP_BILINEAR)
        return pixbuf
    else:
        return None

def scale_nicely(pixbuf):
    '''scale a pixbuf'''
    return pixbuf.scale_simple(20, 20, gtk.gdk.INTERP_BILINEAR)

def file_readable(path):
    '''return True if the file is readable'''
    if path is None:
        return False
    return os.access(path, os.R_OK) and os.path.isfile(path)

def style_to_pango_font_description(style):
    '''receives a e3.Style and returns a pango.FontDescription'''
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
    '''receives a pango.FontDescription and returns a e3.Style'''
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

    return e3.Style(font, e3.Color(0, 0, 0), font_bold,
        font_italic, font_underline, font_strike, font_size)

def simple_animation_scale(path, width, height):
    f = open(path, 'rb')
    pixloader = gtk.gdk.PixbufLoader()
    pixloader.set_size(width, height)
    pixloader.write(f.read())
    pixloader.close()
    f.close()
    return pixloader.get_animation()

def simple_animation_overlap(animation,pixbuf_dest):
    iter = animation.get_iter()
    while not iter.on_currently_loading_frame():
        
        pixx=iter.get_pixbuf()
        simple_images_overlap(pixx,pixbuf_dest,-pixbuf_dest.props.width,-pixbuf_dest.props.width)
        iter.advance()


def simple_images_overlap(pixbuf_src,pixbuf_dest,x,y):
    if x>=0 :
         xstart=0
    else:
         xstart=pixbuf_src.props.height

    if y>=0 :
         ystart=0
    else:
         ystart=pixbuf_src.props.height

    pixbuf_dest.composite(pixbuf_src, 0, 0, pixbuf_src.props.width, pixbuf_src.props.height, xstart+x, ystart+y, 1.0, 1.0, gtk.gdk.INTERP_HYPER, 255)
    

def makePreview(src):
    try:
        pbf = gtk_pixbuf_load(src,(96,96))
    except glib.GError:
        return None

    filetmp = tempfile.mkstemp(prefix=hashlib.md5(src).hexdigest(), suffix=hashlib.md5(src).hexdigest())[1]

    pbf.save(filetmp,"png")
    
    out_file = open(filetmp,"rb")
    cnt = out_file.read()
    out_file.close()

    return cnt

def path_to_url(path):
    if os.name == "nt":
        # on windows os.path.join uses backslashes
        path = path.replace("\\", "/")
        path = path[2:]

    path = path.encode("iso-8859-1")
    path = urllib.quote(path)
    path = "file://" + path

    return path

class GtkRunner(threading.Thread):

    """
    Module written by Mariano Guerra. 
    Visit http://python.org.ar/pyar/Recetario/Gui/Gtk/Runner for more.
    """

    '''run *func* in a thread with *args* and *kwargs* as arguments, when
    finished call callback with a two item tuple containing a boolean as first
    item informing if the function returned correctly and the returned value or
    the exception thrown as second item
    '''

    def __init__(self, callback, func, *args, **kwargs):
        threading.Thread.__init__(self)
        self.setDaemon(True)

        self.callback = callback
        self.func = func
        self.args = args
        self.kwargs = kwargs

        self.result = Queue.Queue()

        self.start()
        glib.timeout_add_seconds(1, self.check)

    def run(self):
        '''
        main function of the thread, run func with args and kwargs
        and get the result, call callback with the (True, result)

        if an exception is thrown call callback with (False, exception)
        '''
        try:
            result = (True, self.func(*self.args, **self.kwargs))
        except Exception, ex:
            result = (False, ex)

        self.result.put(result)

    def check(self):
        '''
        check if func finished
        '''
        try:
            result = self.result.get(False, 0.1)
        except Queue.Empty:
            return True

        self.callback(result)
        return False

