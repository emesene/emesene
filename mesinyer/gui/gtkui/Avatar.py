import pygtk
import gtk
import gtk.gdk
import cairo
import gobject
 
class Avatar( gtk.Widget ):
    """AvatarWidget """
    #TODO move in an avatarManager class?????
    #TODO class for resize gif!

    #cellKeyPosition, is a Anchor Type constant
    #refer to http://www.pygtk.org/docs/pygtk/gtk-constants.html#gtk-anchor-type-constants
    __gproperties__ = {
        'pixbuf': (gtk.gdk.Pixbuf, 'Pixbuf',
        'Pixbuf',gobject.PARAM_READWRITE),
        'pixbuf_animation': (gtk.gdk.Pixbuf, 'Pixbuf',
        'Pixbuf from animation',gobject.PARAM_READWRITE),
        'crossFade' : (bool,'animate by crossfade if true','',True, gobject.PARAM_READWRITE),
        'dimention' : (gobject.TYPE_FLOAT,'cell dimensions',
        'height width of cell',0.0, 128.0,32.0, gobject.PARAM_READWRITE),
        'radius_factor' : (gobject.TYPE_FLOAT,'radius of pixbuf',
        '0.0 to 0.5 with 0.1 = 10% of dimention',0.0, 0.5,0.11, gobject.PARAM_READWRITE),
        'keyPositin' : (object,'position of avatar',
        'corresponds to position of key in numpad', gobject.PARAM_READWRITE),
        }
 
    __gsignals__ = { 'size_request' : 'override', 'expose-event' : 'override' }
 
    def __init__(self, cellDimention = 96, crossFade = True, cellRadius = 0.05,
                 cellKeyPosition = gtk.ANCHOR_CENTER):
        gobject.GObject.__init__(self)
        gtk.Widget.__init__(self)
        self.set_flags(self.flags() | gtk.NO_WINDOW )
 
        self._pixbuf = None
        self._dimention = cellDimention
        self._radius_factor = cellRadius
        self._keyPosition = cellKeyPosition
 
 
        # variables related to animation
        self._crossFade = crossFade
        self.inAnimation = False
        self.duration = 1500 # milliseconds
        self.fps = 24 # frames per second
        self.totalFrames = 0
        self.currentFrame = 0
        self.transitionPixbuf = None
        self.anim_source = None
        self.current_animation = None
 
    def do_get_property(self, property):
        if property.name == 'pixbuf':
            return self._pixbuf
        if property.name == 'pixbuf-animation':
            return self._pixbuf
        elif property.name == 'dimention':
            return self._dimention
        elif property.name == 'radius-factor':
            return self._radius_factor
        elif property.name == 'keyPosition':
            return self._keyPosition
        elif property.name == 'crossFade':
            return self._crossFade
        else:
            raise AttributeError, 'unknown property %s' % property.name
 
    def do_set_property(self, property, value):
        if property.name == 'pixbuf':
            if self.__shouldReplace(value):
                if self._crossFade and not (self._pixbuf == None) and not (value == None) :
                    self.transitionPixbuf = value
                    if self.fps < 1: self.fps = 24 # reset fps if not valid fps
                    timeBetweenFrames = 1000 / self.fps
                    self.totalFrames = self.duration / timeBetweenFrames
                    self.currentFrame = 1
                    gobject.timeout_add( timeBetweenFrames, self.animate_callback)
                    self.inAnimation = True
                else:
                    self._pixbuf = value
        elif property.name == 'pixbuf-animation':
            self._pixbuf = value
        elif property.name == 'dimention':
            self._dimention = value
        elif property.name == 'radius-factor':
            self._radius_factor = value
        elif property.name == 'keyPosition':
            self._keyPosition = value
        elif property.name == 'crossFade':
            self._crossFade = value
        else:
            raise AttributeError, 'unknown property %s' % property.name
 
    def animate_callback(self):
        if self.currentFrame > self.totalFrames :
            self.inAnimation = False
            self._pixbuf = self.transitionPixbuf
            if self.current_animation:
                self._start_animation(self.current_animation)
            return False
        else:
            if self.anim_source is not None:
                gobject.source_remove(self.anim_source)
                self.anim_source = None
            self.currentFrame += 1
            self.queue_draw()
            return True

    def __set_from_pixbuf(self, pixbuf ):
        self.set_property('pixbuf', pixbuf)
        self.queue_draw()

    def __set_from_pixbuf_animation(self, pixbuf):
        self.set_property('pixbuf-animation', pixbuf)
        self.queue_draw()
    
    #public methods
    def set_from_file(self, filename):
        animation = gtk.gdk.PixbufAnimation(filename)
        if animation.is_static_image():
            self.__set_from_pixbuf(animation.get_static_image())
            self.current_animation = None
            return
        self.current_animation = animation
        self._start_animation(animation)

    def stop(self):
        '''stop the animation'''
        if self.anim_source is not None:
            gobject.source_remove(self.anim_source)
            self.anim_source = None

    def _start_animation(self, animation):
        iteran = animation.get_iter()
        #we don't need to resize here!The resize must be done in another class
        self.__set_from_pixbuf(iteran.get_pixbuf())
        if self.anim_source is None:
            self.anim_source = gobject.timeout_add(iteran.get_delay_time(), self._advance, iteran)

    def _advance(self, iteran):
        iteran.advance()
        self.__set_from_pixbuf_animation(iteran.get_pixbuf())
        self.anim_source = gobject.timeout_add(iteran.get_delay_time(), self._advance, iteran)
        return False

    def do_size_request(self,requisition):
        requisition.width = self._dimention
        requisition.height = self._dimention
 
    def do_expose_event(self, evnt):
        if not self._pixbuf: return
 
        ctx = evnt.window.cairo_create()
        cell_area = self.get_allocation()
 
        if self.inAnimation :
            self.__draw( ctx , cell_area , self._pixbuf, 1 - \
                (float(self.currentFrame) / self.totalFrames))
            self.__draw( ctx , cell_area , self.transitionPixbuf, \
                (float(self.currentFrame) / self.totalFrames))
        else:
            self.__draw( ctx , cell_area , self._pixbuf, 1)
 
    def __shouldReplace(self,pixbuf):
        #checkEquivalence
        if self._pixbuf and pixbuf and \
          pixbuf.get_pixels() == self._pixbuf.get_pixels():
            return False
        else:
            return True

    def __draw (self,ctx, cell_area, pixbuf, alpha):
        ctx.save()
        ctx.set_antialias(cairo.ANTIALIAS_SUBPIXEL)
        cell_x, cell_y, cell_width, cell_height = cell_area
        pix_width = pixbuf.get_width()
        pix_height = pixbuf.get_height()
        ctx.translate(cell_x, cell_y)
 
        if (pix_width > self._dimention) or (pix_height > self._dimention):
            scale_factor = float(self._dimention) / max (pix_width,pix_height)
        else:
            scale_factor = 1
 
        scale_width = pix_width* scale_factor
        scale_height = pix_height* scale_factor
 
        self.__translate_keyPostion( ctx, self._keyPosition,cell_width,cell_height,scale_width,scale_height)
 
        scale_radius = self._dimention * self._radius_factor
        self.__roundedrecMoonlight(ctx,0,0,scale_width,scale_height, scale_radius)
 
        ctx.clip()
        ctx.scale(scale_factor,scale_factor)
        ctx.set_source_pixbuf(pixbuf,0,0)
 
        ctx.paint_with_alpha (alpha)
 
        ctx.restore()
 
    def __translate_keyPostion(self,cr, key, w, h ,sw, sh):
        if key in [gtk.ANCHOR_NORTH_WEST,gtk.ANCHOR_WEST,gtk.ANCHOR_SOUTH_WEST] : x = 0
        elif key in [gtk.ANCHOR_NORTH,gtk.ANCHOR_CENTER,gtk.ANCHOR_SOUTH] : x = (w/2) - (sw/2)
        else: x = w - sw
 
        if key in [gtk.ANCHOR_NORTH_WEST,gtk.ANCHOR_NORTH,gtk.ANCHOR_NORTH_EAST] : y = 0
        elif key in [gtk.ANCHOR_EAST,gtk.ANCHOR_CENTER,gtk.ANCHOR_WEST] : y = (h/2) - (sh/2)
        else: y = h - sh
 
        cr.translate( x, y)
 
    def __roundedrecMoonlight(self, cr,x,y,w,h,radius=5):
        # http://cairographics.org/cookbook/roundedrectangles/
        # modified from mono moonlight aka mono silverlight
        # test limits (without using multiplications)
        # http://graphics.stanford.edu/courses/cs248-98-fall/Final/q1.html
 
        ARC_TO_BEZIER = 0.55228475
        if radius > (min(w,h)/2):
            radius = (min(w,h)/2)
        #approximate (quite close) the arc using a bezier curve
        c = ARC_TO_BEZIER * radius
 
        cr.new_path();
        cr.move_to ( x + radius, y)
        cr.rel_line_to ( w - 2 * radius, 0.0)
        cr.rel_curve_to ( c, 0.0, radius, c, radius, radius)
        cr.rel_line_to ( 0, h - 2 * radius)
        cr.rel_curve_to ( 0.0, c, c - radius, radius, -radius, radius)
        cr.rel_line_to ( -w + 2 * radius, 0)
        cr.rel_curve_to ( -c, 0, -radius, -c, -radius, -radius)
        cr.rel_line_to (0, -h + 2 * radius)
        cr.rel_curve_to (0.0, -c, radius - c, -radius, radius, -radius)
        cr.close_path ()
 
gobject.type_register( Avatar )
