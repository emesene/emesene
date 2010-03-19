'''renderers for the ContactList'''
# -*- coding: utf-8 -*-

#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
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

import sys
import gtk
import pango
import gobject

import extension
from gui.base import Plus

class GtkCellRenderer(gtk.CellRendererText):
    def __init__(self):
        gtk.CellRendererText.__init__(self)

extension.implements(GtkCellRenderer, 'nick renderer')

class CellRendererFunction(gtk.GenericCellRenderer):
    '''
    CellRenderer that behaves like a label, but apply a function to "markup"
    to show a modified nick. Its a base class, and it is intended to be
    inherited by extensions.
    '''
    __gproperties__ = {
            'markup': (gobject.TYPE_STRING,
                "text",
                "text we'll display (even with plus markup!)",
                '', #default value
                gobject.PARAM_READWRITE),
            'ellipsize': (gobject.TYPE_BOOLEAN,
                "",
                "",
                True, #default value
                gobject.PARAM_READWRITE)
            }

    property_names = __gproperties__.keys()

    def __init__(self, function):
        self.__gobject_init__()
        gtk.GenericCellRenderer.__init__(self)
        self.__dict__['markup'] = ''
        self.function = function
        self._style_handler_id = None
        self._selected_flgs = (int(gtk.CELL_RENDERER_SELECTED), \
            int(gtk.CELL_RENDERER_SELECTED) + int(gtk.CELL_RENDERER_PRELIT))

        self._cached_markup = None
        self._cached_layout = None

    def __getattr__(self, name):
        try:
            return self.get_property(name)
        except TypeError:
            raise AttributeError, name

    def __setattr__(self, name, value):
        try:
            self.set_property(name, value)
        except TypeError:
            self.__dict__[name] = value

    def on_get_size(self, widget, cell_area):
        '''Returns the size of the cellrenderer'''
        if not self._style_handler_id:
            self._style_handler_id = widget.connect('style-set',
                    self._style_set)

        layout = self.get_layout(widget)
        width, height = layout.get_pixel_size()

        return (0, 0, -1, height + (self.ypad * 2))

    def do_get_property(self, prop):
        '''return the value of prop if exists, raise TypeError if not found'''
        if prop.name not in self.property_names:
            raise TypeError('No property named %s' % (prop.name,))

        return self.__dict__[prop.name]

    def do_set_property(self, prop, value):
        '''set the value of prop if exists, raise TypeError if not found'''
        if prop.name not in self.property_names:
            raise TypeError('No property named %s' % (prop.name,))

        if prop == 'markup': #plus formatting
            value = Plus.msnplus_to_dict

        self.__dict__[prop.name] = value

    def on_render(self, win, widget, bgnd_area, cell_area, expose_area, flags):
        '''Called by gtk to render the cell.'''
        x_coord, y_coord, width, height = cell_area
        x_coord += self.xpad
        y_coord += self.ypad
        width -= self.xpad
        ctx = win.cairo_create()
        layout = self.get_layout(widget)
        layout.set_width(width  * pango.SCALE)
        layout.set_in_color_override_mode(flags in self._selected_flgs)
        layout.draw(ctx, (x_coord, y_coord, width, height))

    def get_layout(self, widget):
        '''Gets the Pango layout used in the cell in a TreeView widget.'''
        layout = SmileyLayout(widget.create_pango_context(),
                self.function(unicode(self.markup,
                    'utf-8')))

        if self.markup:
            try:
                decorated_markup = self.function(unicode(self.markup,
                    'utf-8'))
            except Exception, error:
                print "this nick: '%s' made the parser go crazy, striping" % \
                        (self.markup,)
                print error

                decorated_markup = Plus.msnplus_strip(self.markup)

            try:
                pango.parse_markup(self.function(unicode(self.markup,
                    'utf-8'), False))
            except gobject.GError:
                print "invalid pango markup:", decorated_markup
                decorated_markup = Plus.msnplus_strip(self.markup)

            layout.set_text(decorated_markup)
        else:
            layout.set_text('')

        return layout

    def _style_set(self, widget, previous_style):
        '''callback to the style-set signal of widget'''
        self._cached_markup = {}
        self._cached_layout = {}
        widget.queue_resize()

extension.implements(CellRendererFunction, 'nick renderer')

def balance_spans(text):
        ''' balance the spans in the chunks of text between images
         this can happen when the template for the text shown on
         the contact list (the one you can edit on preferences)
         gets splited by an image
        '''
        opens = text.count("<span")
        closes = text.count("</span")
        difference = abs(opens - closes)

        if opens > closes:
            text += "</span>" * difference
        elif opens < closes:
            text = ("<span>" * difference) + text

        return text

def msnplus_to_list(txt, do_parse_emotes=True):
    '''parte text to a DictObj and return a list of strings and
    gtk.gdk.Pixbufs'''
    dct = Plus.msnplus(txt, do_parse_emotes)

    if not do_parse_emotes:
        return dct.to_xml()

    items = flatten_tree(dct, [], [])

    temp = []
    accum = []
    for item in items:
        if type(item) in (str, unicode):
            temp.append(item)
        else:
            text = balance_spans("".join(temp))
            accum.append(text)
            accum.append(item)
            temp = []

    accum.append(balance_spans("".join(temp)))

    return accum

def flatten_tree(dct, accum, parents):
    '''convert the tree of markup into a list of string that contain pango
    markup and pixbufs, if an img tag is found all the parent tags should be
    closed before the pixbuf and reopened after.
    example:
        <b>hi! :D lol</b>
        should be
        ["<b>hi! </b>", pixbuf, "<b> lol</b>"]
    '''
    def open_tag(tag):
        attrs = " ".join("%s=\"%s\"" % (attr, value) for attr, value in
                tag.iteritems() if attr not in ['tag', 'childs'] and value)

        if attrs:
            return '<%s %s>' % (tag.tag, attrs)
        else:
            return '<%s>' % (tag.tag, )

    if dct.tag:
        if dct.tag == "img":
            closed = "".join("</%s>" % (parent.tag, ) for parent in parents[::-1])
            opened = "".join(open_tag(parent) for parent in parents if parent)
            accum += [closed, gtk.gdk.pixbuf_new_from_file(dct.src), opened]
            return accum
        else:
            accum += [open_tag(dct)]

    for child in dct.childs:
        if type(child) in (str, unicode):
            accum += [child]
        elif dct.tag:
            flatten_tree(child, accum, parents + [dct])
        else:
            flatten_tree(child, accum, parents)

    if dct.tag:
        accum += ['</%s>' % dct.tag]

    return accum

class CellRendererPlus(CellRendererFunction):
    '''Nick renderer that parse the MSN+ markup, showing colors, gradients and
    effects'''
    def __init__(self):
        CellRendererFunction.__init__(self,
                msnplus_to_list)

extension.implements(CellRendererPlus, 'nick renderer')

class CellRendererNoPlus(CellRendererFunction):
    '''Nick renderer that "strip" MSN+ markup, not showing any effect/color,
    but improving the readability'''
    def __init__(self):
        CellRendererFunction.__init__(self, Plus.msnplus_strip)

extension.implements(CellRendererNoPlus, 'nick renderer')

gobject.type_register(CellRendererPlus)

class SmileyLayout(pango.Layout):
    '''a pango layout to draw smilies'''

    def __init__(self, context,
                 parsed_elements_list = None,
                 color = None,
                 override_color = None,
                 scaling=1.0):
        pango.Layout.__init__(self, context)

        self._width = -1
        self._ellipsize = True
        self._elayout = pango.Layout(context)
        self._elayout.set_text('___') #…
        self._elayout.set_ellipsize(pango.ELLIPSIZE_END)
        self._elayout.set_width(0)
        self._in_override = False # color override mode, used for selected text
        self._base_to_center = 0
        self._text_height = 0
        self._smilies = {} # key: (index_pos), value(pixbuf)
        self._base_attrlist = None # no color
        self._attrlist = None # with color
        self._override_attrlist = None # with override color

        if color is None:
            self._color = gtk.gdk.Color()
        else:
            self._color = color

        if override_color is None:
            self._override_color = gtk.gdk.Color()
        else:
            self._override_color = override_color

        self._smilies_scaled = {} # key: (index_pos), value(pixbuf)
        self._scaling = scaling # relative to ascent + desent, -1 for natural
        self._is_rtl = False

        self.set_element_list(parsed_elements_list)
        self._update_layout()

    def set_element_list(self, parsed_elements_list=None):
        ''' Sets Layout Text based on parsed elements '''
        if parsed_elements_list is None:
            parsed_elements_list = ['']

        self._update_base(parsed_elements_list)

    def set_text(self, text):
        ''' Sets Layout Text '''
        self.set_element_list(text)

    def set_markup(self, markup):
        ''' Same as set_text() '''
        self.set_element_list(markup)

    def set_width(self, width):
        ''' Set width of layout in pixels, -1 for natural width '''
        self._width = width
        self._update_layout()

    def get_width(self):
        '''return thw width of layout in pixels, -1 for natural width'''
        return self._width

    def set_ellipsize(self, value):
        ''' Turns Ellipsize ON/OFF '''
        if value == pango.ELLIPSIZE_END:
            self._ellipsize = True
        else:
            self._ellipsize = False
        self._update_layout()

    def set_smiley_scaling(self, smiley_scaling):
        '''
        Set smiley scalling relative to ascent + desent,
        -1 for natural size
        '''
        self._scaling = smiley_scaling
        self._update_smilies()

    def set_in_color_override_mode(self, in_override):
        if not in_override == self._in_override:
            self._in_override = in_override
            self._update_attributes()

    def set_colors(self, color=None, override_color=None):
        if color is None:
            color = gtk.gdk.Color()

        if override_color is None:
            override_color = gtk.gdk.Color()

        self._color = color
        self._override_color = override_color
        self._update_attrlists()

    def _update_base(self, elements_list=None):

        if elements_list is None:
            elements_list = ['']

        self._smilies = {}
        self._base_attrlist = pango.AttrList()
        text = ''

        if type(elements_list) in (str, unicode):
            elements_list = [elements_list]

        for element in elements_list:
            if type(element) in (str, unicode):
                try:
                    attrl, ptxt, unused = pango.parse_markup(element, u'\x00')
                except:
                    attrl, ptxt = pango.AttrList(), element

                #append attribute list
                shift = len(text)
                itter = attrl.get_iterator()

                while True:
                    attrs = itter.get_attrs()
                    for attr in attrs:
                        attr.end_index += shift
                        attr.start_index += shift
                        self._base_attrlist.insert(attr)
                    if not itter.next():
                        break

                text += ptxt
            elif type(element) == gtk.gdk.Pixbuf:
                self._smilies[len(text)] = element
                text += '_'

        pango.Layout.set_text(self, text)

        if hasattr(pango, 'find_base_dir'):
            for line in text.splitlines():
                if (pango.find_base_dir(line, -1) == pango.DIRECTION_RTL):
                    self._is_rtl = True
                    break
        else:
            self._is_rtl = False

        logical = self.get_line(0).get_pixel_extents()[1]
        ascent = pango.ASCENT(logical)
        decent = pango.DESCENT(logical)
        self._text_height =  ascent + decent
        self._base_to_center = (self._text_height / 2) - decent
        self._update_smilies()

    def _update_smilies(self):
        self._base_attrlist.filter(lambda attr: attr.type == pango.ATTR_SHAPE)
        self._smilies_scaled = {}
        #set max height of a pixbuf
        if self._scaling >= 0:
            max_height = self._text_height * self._scaling
        else:
            max_height = sys.maxint
        for index, pixbuf in self._smilies.iteritems():
            if pixbuf:
                height, width = pixbuf.get_height(), pixbuf.get_width()
                npix = pixbuf.copy()
                if height > max_height:
                    cairo_scale = float(max_height) / float(height)
                    height = int(height * cairo_scale)
                    width = int(width * cairo_scale)
                    npix = npix.scale_simple(width, height,
                            gtk.gdk.INTERP_BILINEAR)
                self._smilies_scaled[index] = npix
                rect = (0,
                    -1 * (self._base_to_center + (height /2)) * pango.SCALE,
                         width * pango.SCALE, height * pango.SCALE)
                self._base_attrlist.insert(pango.AttrShape((0, 0, 0, 0),
                    rect, index, index + 1))
        self._update_attrlists()

    def _update_attrlists(self):
        clr = self._color
        oclr = self._override_color
        norm_forground = pango.AttrForeground( clr.red,
                clr.green, clr.blue, 0, len(self.get_text()))
        override_forground = pango.AttrForeground( oclr.red,
                oclr.green, oclr.blue, 0, len(self.get_text()))
        self._attrlist = pango.AttrList()
        self._attrlist.insert(norm_forground)
        self._override_attrlist = pango.AttrList()
        self._override_attrlist.insert(override_forground)
        itter = self._base_attrlist.get_iterator()

        while True:
            attrs = itter.get_attrs()
            for attr in attrs:
                self._attrlist.insert(attr.copy())
                if not (attr.type in (pango.ATTR_FOREGROUND,
                    pango.ATTR_BACKGROUND)):
                    self._override_attrlist.insert(attr.copy())
            if not itter.next():
                break

        self._update_attributes()

    def _update_attributes(self):
        if self._in_override:
            self.set_attributes(self._override_attrlist)
        else:
            self.set_attributes(self._attrlist)

    def _update_layout(self):
        if self._width >= 0 and self._ellipsize == False: # if true, then wrap
            pango.Layout.set_width(self, self._width)
        else:
            pango.Layout.set_width(self, -1)

    def get_size(self):
        natural_width, natural_height = pango.Layout.get_size(self)
        if self._width >= 0 and self._ellipsize : # if ellipsize
            return self._width, natural_height
        else:
            return natural_width, natural_height

    def get_pixel_size(self):
        natural_width, natural_height = pango.Layout.get_pixel_size(self)
        if self._width >= 0 and self._ellipsize : # if ellipsize
            return pango.PIXELS(self._width), natural_height
        else:
            return natural_width, natural_height

    def draw(self, ctx, area):
        x, y, width, height = area
        pxls = pango.PIXELS
        ctx.rectangle(x, y , width, height)
        ctx.clip()
        if self._is_rtl:
            layout_width = pango.Layout.get_pixel_size(self)[0]
            ctx.translate(x + width - layout_width, y)
        else:
            ctx.translate(x, y)
            #Clipping and ellipsation
            if self._width >= 0:
                inline, byte = 0, 1
                X, Y, W, H = 0, 1, 2, 3
                layout_width = self._width
                lst = self.get_attributes()
                e_ascent = pango.ASCENT(
                        self._elayout.get_line(0).get_pixel_extents()[1])
                coords = [] # of path in px
                for i in range(self.get_line_count()):
                    line = self.get_line(i)
                    edge = line.x_to_index(layout_width)

                    if edge[inline]:
                        #create ellipsize layout with the style of the char
                        attrlist = pango.AttrList()
                        itter = lst.get_iterator()

                        while True:
                            attrs = itter.get_attrs()

                            for attr in attrs:
                                if not attr.type == pango.ATTR_SHAPE:
                                    start, end = itter.range()
                                    if start <= edge[byte] < end:
                                        n_attr = attr.copy()
                                        n_attr.start_index = 0
                                        n_attr.end_index = 3
                                        attrlist.insert(n_attr)

                            if not itter.next():
                                break

                        self._elayout.set_attributes(attrlist)
                        ellipsize_width = self._elayout.get_size()[0]
                        edge = line.x_to_index(layout_width - ellipsize_width)
                        char = self.index_to_pos(edge[byte])
                        char_x, char_y, char_h = (pxls(char[X]), pxls(char[Y]),
                            pxls(char[H]))
                        y1, y2 = char_y, char_y + char_h

                        if edge[inline]:
                            x1 = char_x
                        else:
                            x1 = 0

                        coords.append((x1, y1))
                        coords.append((x1, y2))
                        line_ascent = pango.ASCENT(line.get_pixel_extents()[1])
                        ctx.move_to(x1, y1 + line_ascent - e_ascent)
                        ctx.show_layout(self._elayout)
                    else:
                        char = self.index_to_pos(edge[byte])
                        coords.append((pxls(char[X] + char[W]), pxls(char[Y])))
                        coords.append((pxls(char[X] + char[W]),
                            pxls(char[Y] + char[H])))
                if coords:
                    ctx.move_to(0, 0)
                    for x, y in coords:
                        ctx.line_to(x, y)
                    ctx.line_to(0, coords[-1][1])
                    ctx.close_path()
                    ctx.clip()

        #layout
        ctx.move_to(0, 0)
        ctx.show_layout(self)
        #smilies

        for index in self._smilies.keys():
            try:
                x, y, width, height = self.index_to_pos(index)
                pixbuf = self._smilies_scaled[index]
                tx = pxls(x)
                ty = pxls(y) + (pxls(height)/2) - (pixbuf.get_height()/2)
                ctx.set_source_pixbuf(pixbuf, tx, ty)
                ctx.paint()
            except Exception, error:
                print error

import cairo
import gui
from e3 import status

#from emesene1 by mariano guerra adapted by cando
class AvatarRenderer(gtk.GenericCellRenderer):
    """Renderer for avatar """
    
    __gproperties__ = {
        'pixbuf': (gtk.gdk.Pixbuf, 'Pixbuf', '', gobject.PARAM_READWRITE),        
        'blocked': (bool, 'Contact Blocked', '', False, gobject.PARAM_READWRITE),        
        'dimention': (gobject.TYPE_INT, 'cell dimentions', 
                    'height width of cell', 0, 96, 32, gobject.PARAM_READWRITE),
        'status': (str, 'Contact status', '', 'FLN', gobject.PARAM_READWRITE),
        'radius_factor': (gobject.TYPE_FLOAT,'radius of pixbuf', 
                          '0.0 to 0.5 with 0.1 = 10% of dimention',
                          0.0, 0.5,0.11, gobject.PARAM_READWRITE),
         }
        
    def __init__(self, cellDimention = 32, cellRadius = 0.11):
        #TODO add animation! add extension e aggiungi options se vuoi di lato o sopra l'immagine
        self.__gobject_init__()
        self._pixbuf = None
        self._status = status.OFFLINE
        self._blocked = False
        self._dimention = cellDimention
        self._radius_factor = cellRadius
        
        #icon source used to render grayed out offline avatar
        self._icon_source = gtk.IconSource()
        self._icon_source.set_state(gtk.STATE_INSENSITIVE)
        
        self.set_property('xpad', 1)
        self.set_property('ypad', 1)   

        #set up information of statusTransformation
        #TODO
        self._set_transformation('corner|gray|pixelate')
        #TODO
        #self.transId = self._config.connect('change::statusTransformation', \
            #self._transformation_callback)
        
    def destroy(self):
        self._config.disconnect(self.transId)
        gtk.GenericCellRenderer.destroy(self)

    def _get_padding(self):
        return (self.get_property('xpad'), self.get_property('ypad'))

    def _set_transformation(self, setting):
        transformation = setting.split('|')
        self._pixalated = ('pixelate' in transformation)
        self._corner = ('corner' in transformation)
        self._alpha_status = ('alpha' in transformation)
        self._mini = ('mini' in transformation)
        self._gray = ('gray' in transformation)

    def _transformation_callback(self, config, newvalue, oldvalue):
        self._set_transformation(newvalue)
        
    def do_get_property(self, property):
        if property.name == 'pixbuf':
            return self._pixbuf
        elif property.name == 'dimention':
            return self._dimention
        elif property.name == 'radius-factor':
            return self._radius_factor
        elif property.name == 'blocked':
            return self._blocked
        elif property.name == 'status':
            return self._status                        
        else:
            raise AttributeError, 'unknown property %s' % property.name
  
    def do_set_property(self, property, value):
        if property.name == 'pixbuf':
            self._pixbuf = value
        elif property.name == 'dimention':            
            self._dimention = value
        elif property.name == 'radius-factor':
            self._radius_factor = value         
        elif property.name == 'blocked':
            self._blocked = value
        elif property.name == 'status':
            self._status = value      
        else:
            raise AttributeError, 'unknown property %s' % property.name

    def on_get_size(self, widget, cell_area=None):       
        """Requisition size"""
        xpad, ypad = self._get_padding()
        if self._dimention >= 32: width = self._dimention
        elif self._mini: width = self._dimention
        elif self._corner: width = self._dimention * 2            
        else: width = self._dimention            
        height = self._dimention + (ypad * 2)                       
        return (0, 0,  width, height)
        
    def on_render(self, window, widget, bg_area, cell_area, expose_area, flags):        
        """Prepare rendering setting for avatar"""
        xpad, ypad = self._get_padding()
        x, y, width, height = cell_area 
        ctx = window.cairo_create()          
        ctx.translate(x, y)
        
        avatar = self._pixbuf
        overlay = None
        alpha = 1
        dim = self._dimention
        
        if self._pixalated: 
            avatar = self._get_pixalate(self._pixbuf)            
        if self._corner: 
            overlay = self._get_overlay()
        if self._alpha_status and self._status in (status.IDLE, status.OFFLINE): 
            alpha = 0.75
        if self._gray and self._status == 'FLN' and avatar != None:
            alpha = 1
            source = self._icon_source
            source.set_pixbuf(avatar)
            direction = widget.get_direction()
            avatar = widget.style.render_icon(source, direction, 
                                              gtk.STATE_INSENSITIVE, 
                                              -1, widget, "gtk-image")
        if avatar:
            self._draw_avatar(ctx, avatar, width - dim, ypad, dim, 
                                gtk.ANCHOR_CENTER, self._radius_factor, alpha)
        
        if overlay:       
            if self._dimention >= 32 :     
                self._draw_avatar(ctx, overlay, width - 16, 
                                  ypad + dim - 16, 16, gtk.ANCHOR_SW)
            elif self._mini:
                self._draw_avatar(ctx, overlay, width - 8, 
                                  ypad + dim - 8, 8, gtk.ANCHOR_SW)
            else:
                self._draw_avatar(ctx, overlay, 0, ypad, 16)

    def _get_overlay(self):
        """Return overlay pixbuf, 
           dependant on contacts status and block state"""
        overlay = None
        if self._blocked:
            #TODO add blocked image
            #overlay = gui.theme.????
            return None 
        elif self._status == status.AWAY:
            overlay = gui.theme.status_icons[status.AWAY]
        elif self._status == status.BUSY:
            overlay = gui.theme.status_icons[status.BUSY]
        return overlay       

    def _get_pixalate(self, pixbuf):
        """Pixalate and saturate values based on original renderer
           kept to retain compatibility"""
        pixalate = pixbuf.copy()        
        if not self._status == status.ONLINE:
            if self._status == status.BUSY:
                pixalate.saturate_and_pixelate(pixbuf, 1.0, True)
            else:
                pixalate.saturate_and_pixelate(pixbuf, 0.1, False)                
        return pixalate
        
          
    def _draw_avatar(self, ctx, pixbuf, x, y, dimention, 
                         position = gtk.ANCHOR_CENTER, 
                         radius = 0, alpha = 1):
        """Render avatar"""        
        ctx.save()
        ctx.set_antialias(cairo.ANTIALIAS_SUBPIXEL)
        ctx.translate(x, y)
        
        pix_width = pixbuf.get_width()
        pix_height = pixbuf.get_height()
        if (pix_width > dimention) or (pix_height > dimention): 
            scale_factor = float(dimention) / max (pix_width,pix_height)
        else: 
            scale_factor = 1        
        scale_width = pix_width* scale_factor
        scale_height = pix_height* scale_factor 
 
        #tranlate position
        if position in (gtk.ANCHOR_NW, gtk.ANCHOR_W, gtk.ANCHOR_SW):
            x = 0
        elif position in (gtk.ANCHOR_N, gtk.ANCHOR_CENTER, gtk.ANCHOR_S): 
            x = (dimention/2) - (scale_width/2)
        else: 
            x = dimention - scale_width         
        if position in (gtk.ANCHOR_NW, gtk.ANCHOR_N, gtk.ANCHOR_NE):
            y = 0
        elif position in (gtk.ANCHOR_E, gtk.ANCHOR_CENTER, gtk.ANCHOR_W): 
            y = (dimention/2) - (scale_height/2)
        else:
            y = dimention - scale_height         
        ctx.translate(x, y)
        
        if radius > 0 : 
            self._rounded_rectangle(ctx, 0, 0, scale_width, scale_height,
                                      self._dimention * radius) 
            ctx.clip()
        ctx.scale(scale_factor,scale_factor)
        ctx.set_source_pixbuf(pixbuf, 0, 0)
        ctx.paint_with_alpha(alpha)
        ctx.restore()
    
    def _rounded_rectangle(self, cr, x, y, w, h, radius=5):
        """Create rounded rectangle path"""
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
                        
gobject.type_register(AvatarRenderer)

