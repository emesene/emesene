'''renderers for the ContactList'''
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

from __future__ import division

import sys
import gtk
import pango
import gobject

from gui.base import Plus
import MarkupParser
import extension
from AvatarManager import AvatarManager

import logging
log = logging.getLogger('gtkui.Renderers')

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
                gobject.PARAM_READWRITE),
            'yalign': (gobject.TYPE_FLOAT,
                "The fraction of vertical free space above the child.",
                "0.0 means no free space above, 1.0 means all free space above.",
                0.0, 1.0, 0.0, #default value
                gobject.PARAM_READWRITE)
            }

    property_names = __gproperties__.keys()

    def __init__(self, function):
        self.__gobject_init__()
        gtk.GenericCellRenderer.__init__(self)
        self.__dict__['markup'] = ''
        self.__dict__['yalign'] = 0.0
        self.function = function
        self._style_handler_id = None
        self._selected_flgs = (int(gtk.CELL_RENDERER_SELECTED),
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
        if layout:
            width, height = layout.get_pixel_size()
        else:
            width, height = [0,0]
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

        self.__dict__[prop.name] = value

    def on_render(self, win, widget, bgnd_area, cell_area, expose_area, flags):
        '''Called by gtk to render the cell.'''
        x_coord, y_coord, width, height = cell_area
        x_coord += self.xpad
        y_coord += self.ypad
        width -= self.xpad
        ctx = win.cairo_create()
        layout = self.get_layout(widget)
        if layout:
            padding = (height - layout.get_size()[1] / pango.SCALE) * self.yalign
            y_coord += padding
            height -= padding

            layout.set_width(width * pango.SCALE)
            layout.set_in_color_override_mode(flags in self._selected_flgs)
            layout.draw(ctx, (x_coord, y_coord, width, height))

    def get_layout(self, widget):
        '''Gets the Pango layout used in the cell in a TreeView widget.'''
        layout = SmileyLayout(widget.create_pango_context(),
                              color=widget.style.text[gtk.STATE_NORMAL],
                              override_color=widget.style.text[gtk.STATE_SELECTED])

        if self.markup:
            decorated_markup = self.function(self.markup)
            layout.set_text(decorated_markup)
            return layout

    def _style_set(self, widget, previous_style):
        '''callback to the style-set signal of widget'''
        self._cached_markup = {}
        self._cached_layout = {}
        widget.queue_resize()

plus_or_noplus = 1 # 1 means plus, 0 means noplus

def plus_text_parse(item):
    '''parse plus in the contact list'''
    global plus_or_noplus
    # get a plain string with objects
    if plus_or_noplus:
        try:
            item = Plus.msnplus_parse(item)
        except Exception, error: # We really want to catch all exceptions
            log.info("Text: '%s' made the parser go crazy, stripping. Error: %s" % (
                      item, error))
            try:
                item = Plus.msnplus_strip(item)
            except Exception, error: # We really want to catch all exceptions
                log.info("Even stripping plus markup doesn't help. Error: %s" % error)
    else:
        item = Plus.msnplus_strip(item)
    return item

def msnplus_to_list(text):
    '''parse text and return a list of strings and gtk.gdk.Pixbufs'''
    text = plus_text_parse(text)
    text = MarkupParser.replace_markup(text)
    text_list = MarkupParser.replace_emoticons(text)
    return text_list

class CellRendererPlus(CellRendererFunction):
    '''Nick renderer that parse the MSN+ markup, showing colors, gradients and
    effects'''

    NAME = 'Cell Renderer Plus'
    DESCRIPTION = _('Parse MSN+ markup, showing colors, gradients and effects')
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self):
        global plus_or_noplus
        plus_or_noplus = 1
        CellRendererFunction.__init__(self, msnplus_to_list)

extension.implements(CellRendererPlus, 'nick renderer')

class CellRendererNoPlus(CellRendererFunction):
    '''Nick renderer that "strip" MSN+ markup, not showing any effect/color,
    but improving the readability'''

    NAME = 'Cell Renderer No Plus'
    DESCRIPTION = _('Strip MSN+ markup, not showing any effect/color, but improving the readability')
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self):
        global plus_or_noplus
        plus_or_noplus = 0
        CellRendererFunction.__init__(self, msnplus_to_list)

extension.implements(CellRendererNoPlus, 'nick renderer')

class SmileyLayout(pango.Layout):
    '''a pango layout to draw smilies'''

    def __init__(self, context,
                 parsed_elements_list = None,
                 color = None,
                 override_color = None,
                 scaling = 1.0):
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
        self.angle = 0

        self._color = color
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
        markup = msnplus_to_list(markup)
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
        self._color = color
        self._override_color = override_color
        self._update_attrlists()

    def _update_base(self, elements_list=None):
        if elements_list is None:
            elements_list = ['']

        self._smilies = {}
        self._base_attrlist = pango.AttrList()
        text = ''

        if isinstance(elements_list, basestring):
            elements_list = [elements_list]

        for element in elements_list:           
            if isinstance(element, basestring):
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
            elif isinstance(element, gtk.gdk.Pixbuf):
                self._smilies[len(text)] = element
                text += '_'

        pango.Layout.set_text(self, text)

        for line in text.splitlines():
            if pango.find_base_dir(line, -1) == pango.DIRECTION_RTL:
                self._is_rtl = True
                break

        logical = self.get_line(0).get_pixel_extents()[1]
        ascent = pango.ASCENT(logical)
        decent = pango.DESCENT(logical)
        self._text_height =  ascent + decent
        self._base_to_center = (self._text_height // 2) - decent
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
                    -1 * (self._base_to_center + (height // 2)) * pango.SCALE,
                         width * pango.SCALE, height * pango.SCALE)

                self._base_attrlist.insert(pango.AttrShape((0, 0, 0, 0),
                    rect, index, index + 1))

        self._update_attrlists()

    def _update_attrlists(self):
        self._attrlist = pango.AttrList()
        if self._color:
            clr = self._color
            norm_forground = pango.AttrForeground(clr.red,
                    clr.green, clr.blue, 0, len(self.get_text()))
            self._attrlist.insert(norm_forground)

        self._override_attrlist = pango.AttrList()
        if self._override_color:
            oclr = self._override_color
            override_forground = pango.AttrForeground(oclr.red,
                    oclr.green, oclr.blue, 0, len(self.get_text()))
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
        if self._width >= 0 and not self._ellipsize: # if true, then wrap
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

            if self.angle == 90:
                ctx.translate(width,0)
                ctx.rotate(3.14/2)
            #Clipping and ellipsation
            if self._width >= 0:
                inline, byte = 0, 1
                X, Y, W, H = 0, 1, 2, 3
                layout_width = height*pango.SCALE if (self.angle == 90) else self._width
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
                ty = pxls(y) + (pxls(height) // 2) - (pixbuf.get_height() // 2)
                ctx.set_source_pixbuf(pixbuf, tx, ty)
                ctx.paint()
            except Exception, error:
                log.error("Error when painting smilies: %s" % error)

class SmileyLabel(gtk.Label):
    '''Label with smiley support. '''

    __gsignals__ = { 'size_request' : 'override',
                     'size-allocate' : 'override',
                     'expose-event' : 'override'}

    def __init__(self):
        gtk.Widget.__init__(self)
        self.angle = 0
        self._text = ['']
        self.markup = ''
        self._ellipsize = True
        self._wrap = True
        self._smiley_layout = None
        self.set_flags(self.flags() | gtk.NO_WINDOW)
        self._smiley_layout = SmileyLayout(self.create_pango_context())
        extension.subscribe(self._on_nick_renderer_changed, 'nick renderer')

    def __del__(self):
        extension.unsubscribe(self._on_nick_renderer_changed, 'nick renderer')

    def _on_nick_renderer_changed(self, new_extension):
        self.set_markup(self.markup)

    def set_angle(self, angle):
        self.angle = angle
        self._smiley_layout.angle = self.angle

    def set_ellipsize(self, ellipsize):
        ''' Sets the ellipsize behavior '''
        self._ellipsize = ellipsize
        self.queue_resize()

    def set_wrap(self, wrap):
        ''' Sets the wrap behavior '''
        self._wrap = wrap
        self.queue_resize()

    def set_markup(self, text=['']):
        markup = msnplus_to_list(text)
        self.markup = text
        self.set_text(markup)

    def set_text(self, text=['']):
        ''' Sets widget text '''
        self._text = text
        self.setup_smiley_layout()
        self.queue_resize()

    def set_smiley_scaling(self, smiley_scaling):
        self._smiley_layout.set_smiley_scaling(smiley_scaling)
        self.queue_resize()

    def setup_smiley_layout(self):
        self._smiley_layout.set_element_list(self._text)

    def do_realize(self):
        gtk.Widget.do_realize(self)
        self.set_flags(self.flags() | gtk.REALIZED)
        self.window = self.get_parent().window

    def do_style_set(self, prev_style):
        self._smiley_layout.set_colors(self.style.text[gtk.STATE_NORMAL])
        self.queue_draw()

    def do_size_request(self, requisition):
        self._smiley_layout.set_width(-1)
        width, height = self._smiley_layout.get_pixel_size()
        requisition.height = height

        if self._ellipsize or self._wrap:
            requisition.width = 0
        else:
            requisition.width = width

    def do_size_allocate(self, allocation):
        if not (self._ellipsize or self._wrap):
            self._smiley_layout.set_width(-1)
            width, height = self._smiley_layout.get_pixel_size()
            self.set_size_request(width, height)
        else:
            if self._ellipsize:
                self._smiley_layout.set_ellipsize(pango.ELLIPSIZE_END)
            else:
                self._smiley_layout.set_ellipsize(pango.ELLIPSIZE_NONE)

            self._smiley_layout.set_width(allocation.width * pango.SCALE)
            self.set_size_request(-1, self._smiley_layout.get_pixel_size()[1])

        gtk.Widget.do_size_allocate(self, allocation)

    def do_expose_event(self, event):
        area = self.get_allocation()
        ctx = event.window.cairo_create()
        self._smiley_layout.draw(ctx, area)

#from emesene1 by mariano guerra adapted by cando
#animation support by cando
#TODO add transformation field in configuration
#TODO signals in configuration for transformation changes????

class AvatarRenderer(gtk.GenericCellRenderer, AvatarManager):
    """Renderer for avatar """

    __gproperties__ = {
        'image': (gobject.TYPE_OBJECT, 'The contact image', '',
            gobject.PARAM_READWRITE),
        'blocked': (bool, 'Contact Blocked', '', False,
            gobject.PARAM_READWRITE),
        'dimension': (gobject.TYPE_INT, 'cell dimensions',
            'height width of cell', 0, 96, 32,
            gobject.PARAM_READWRITE),
        'offline': (bool, 'Contact is offline', '', False,
            gobject.PARAM_READWRITE),
        'radius-factor': (gobject.TYPE_FLOAT, 'radius of pixbuf',
            '0.0 to 0.5 with 0.1 = 10% of dimension', 0.0, 0.5, 0.11,
            gobject.PARAM_READWRITE),
         }

    def __init__(self, cell_dimension = 32, cell_radius = 0.11):
        self.__gobject_init__()
        AvatarManager.__init__(self, cell_dimension, cell_radius)

        #icon source used to render grayed out offline avatar
        self._icon_source = gtk.IconSource()
        self._icon_source.set_state(gtk.STATE_INSENSITIVE)

        self.set_property('xpad', 1)
        self.set_property('ypad', 1)

        #set up information of statusTransformation
        self._set_transformation('corner|gray')
        #self.transId = self._config.connect('change::statusTransformation',
            #self._transformation_callback)

    def destroy(self):
        self._config.disconnect(self.transId)
        gtk.GenericCellRenderer.destroy(self)

    def _get_padding(self):
        return (self.get_property('xpad'), self.get_property('ypad'))

    def _set_transformation(self, setting):
        transformation = setting.split('|')
        self._corner = ('corner' in transformation)
        self._alpha_status = ('alpha' in transformation)
        self._gray = ('gray' in transformation)

    def _transformation_callback(self, config, newvalue, oldvalue):
        self._set_transformation(newvalue)

    def on_get_size(self, widget, cell_area=None):
        """Requisition size"""
        xpad, ypad = self._get_padding()

        if self._dimension >= 32:
            width = self._dimension
        elif self._corner:
            width = self._dimension * 2
        else:
            width = self._dimension

        height = self._dimension + (ypad * 2)

        return (0, 0,  width, height)

    def func(self, model, path, iter, image_and_tree):
      image, tree = image_and_tree
      if model.get_value(iter, 0) == image:
         self.redraw = 1
         cell_area = tree.get_cell_area(path, tree.get_column(1))
         tree.queue_draw_area(cell_area.x, cell_area.y, cell_area.width,
            cell_area.height)

    def animation_timeout(self, tree, image):
       if image.get_storage_type() == gtk.IMAGE_ANIMATION:
          self.redraw = 0
          image.get_data('iter').advance()
          model = tree.get_model()
          model.foreach(self.func, (image, tree))

          if self.redraw:
             gobject.timeout_add(image.get_data('iter').get_delay_time(),
                self.animation_timeout, tree, image)
          else:
             image.set_data('iter', None)


    def on_render(self, window, widget, bg_area, cell_area, expose_area, flags):
        """Prepare rendering setting for avatar"""
        xpad, ypad = self._get_padding()
        x, y, width, height = cell_area
        ctx = window.cairo_create()
        ctx.translate(x, y)

        avatar = None
        alpha = 1
        dim = self._dimension

        if self._image.get_storage_type() == gtk.IMAGE_ANIMATION:
            if not self._image.get_data('iter'):
                animation = self._image.get_animation()
                self._image.set_data('iter', animation.get_iter())
                gobject.timeout_add(self._image.get_data('iter').get_delay_time(),
                   self.animation_timeout, widget, self._image)

            avatar = self._image.get_data('iter').get_pixbuf()
        elif self._image.get_storage_type() == gtk.IMAGE_PIXBUF:
            avatar = self._image.get_pixbuf()
        else:
           return

        if self._gray and self._offline and avatar != None:
            alpha = 1
            source = self._icon_source
            source.set_pixbuf(avatar)
            direction = widget.get_direction()
            avatar = widget.style.render_icon(source, direction,
                gtk.STATE_INSENSITIVE, -1, widget, "gtk-image")

        if avatar:
            self.draw_avatar(ctx, avatar, width - dim, ypad, dim,
                gtk.gdk.GRAVITY_CENTER, self._radius_factor, alpha)
