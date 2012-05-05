import sys
import gobject
import pango
import gtk
from gtk import gdk
import cairo
import gobject
from time import sleep
import glib

class Splash(gtk.Window):
    def __init__(self):
        super(Splash, self).__init__(gtk.WINDOW_TOPLEVEL)
        self.set_position(gtk.WIN_POS_CENTER)        
        self.set_decorated(False)
        self.set_default_size(300, 264)

        self.set_events(gtk.gdk.ALL_EVENTS_MASK)

		# Initialize colors, alpha transparency		
        self.set_app_paintable(1)
        self.gtk_screen = self.get_screen()
        colormap = self.gtk_screen.get_rgba_colormap()
        if colormap == None:
            colormap = self.gtk_screen.get_rgb_colormap()
        gtk.widget_set_default_colormap(colormap)
        if not self.is_composited():
            self.supports_alpha = False
        else:
            self.supports_alpha = True

        self.w,self.h = self.get_size()
        
        self.connect("expose_event", self.expose)
        self.connect("destroy", gtk.main_quit)

    def expose (self, widget, event):
        self.ctx = self.window.cairo_create()
		# set a clip region for the expose event, XShape stuff
        self.ctx.save()
        if self.supports_alpha == False:
            self.ctx.set_source_rgb(1, 1, 1)
        else:
            self.ctx.set_source_rgba(1, 1, 1,0)
        self.ctx.set_operator (cairo.OPERATOR_SOURCE)
        self.ctx.paint()
        self.ctx.restore()
        self.ctx.rectangle(event.area.x, event.area.y,
            event.area.width, event.area.height)
        self.ctx.clip()
        self.draw_image(self.ctx,0,0,'themes/images/default/splash.png')

    def setup(self):
		# Set menu background image
        self.background =  gtk.Image()
        frame = gtk.Fixed()
        self.add (frame)

		# Set window shape from alpha mask of background image
        w,h = self.get_size()
        if w==0: w = 300
        if h==0: h = 264
        self.w = w
        self.h = h
        self.pixmap = gtk.gdk.Pixmap (None, w, h, 1)
        ctx = self.pixmap.cairo_create()
        ctx.save()
        ctx.set_source_rgba(1, 1, 1,0)
        ctx.set_operator (cairo.OPERATOR_SOURCE)
        ctx.paint()
        ctx.restore()
        self.draw_image(ctx,0,0,'themes/images/default/splash.png')

        if self.is_composited():
            ctx.rectangle(0,0,w,h)
            ctx.fill()			
            self.input_shape_combine_mask(self.pixmap,0,0)
        else:
            self.shape_combine_mask(self.pixmap, 0, 0)

    def draw_image(self,ctx,x,y, pix):
        """Draws a picture from specified path with a certain width and height"""

        ctx.save()
        ctx.translate(x, y)	
        pixbuf = gtk.gdk.pixbuf_new_from_file(pix)
        format = cairo.FORMAT_RGB24
        if pixbuf.get_has_alpha():
            format = cairo.FORMAT_ARGB32

        iw = pixbuf.get_width()
        ih = pixbuf.get_height()
        image = cairo.ImageSurface(format, iw, ih)
        image = ctx.set_source_pixbuf(pixbuf, 0, 0)

        ctx.paint()
        puxbuf = None
        image = None
        ctx.restore()
        ctx.clip()

    def show_window(self):
        self.show_all()
        while gtk.events_pending():
            gtk.main_iteration()
        self.present()
        self.grab_focus()

    def destroy_window(self):
        self.hide()