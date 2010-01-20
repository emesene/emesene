import gtk

import e3
import logging

class RichWidget(object):
    '''a base widget that allows to add formatted text based on a
    xhtml subset'''

    def put_text(self, text, fg_color=None, bg_color=None, font=None, size=None,
        bold=False, italic=False, underline=False, strike=False):
        '''insert text at the current position with the style defined by the
        optional parameters'''
        raise NotImplementedError('Not implemented')

    def put_formatted(self, text, fg_color=None, bg_color=None, font=None, size=None,
        bold=False, italic=False, underline=False, strike=False):
        '''insert text at the current position with the style defined inside
        text'''
        try:
            result = e3.common.XmlParser.XmlParser(
                '<span>' + text.replace('\n', '') + '</span>').result
        except xml.parsers.expat.ExpatError:
            logging.getLogger("gtkui.RichWidget").debug("cant parse '%s'" % \
                    (text, ))
            return

        dct = e3.common.XmlParser.DictObj(result)
        self._put_formatted(dct, fg_color, bg_color, font, size,
            bold, italic, underline, strike)

    def _put_formatted(self, dct, fg_color=None, bg_color=None, font=None, size=None,
        bold=False, italic=False, underline=False, strike=False):
        '''insert text at the current position with the style defined inside
        text, using the parsed structure stored on dct'''
        # override the values if defined, keep the old ones if no new defined
        bold = dct.tag == 'b' or dct.tag == 'strong' or bold
        italic = dct.tag == 'i' or dct.tag == 'em' or italic
        underline = dct.tag == 'u' or underline
        strike = dct.tag == 's' or strike

        if dct.tag == 'span' and dct.style:
            style = e3.common.XmlParser.parse_css(dct.style)
            font = style.font_family or font

            try:
                # TODO: handle different units?
                size = int(style.font_size) or size
            except ValueError:
                pass
            except TypeError:
                pass

            fg_color = style.color or fg_color
            bg_color = style.background_color or bg_color

        if dct.childs is None:
            return

        for child in dct.childs:
            if type(child) == str or type(child) == unicode:
                self.put_text(child, fg_color, bg_color, font, size,
                    bold, italic, underline, strike)
            elif child.tag == 'img':
                self.put_image(child.src, child.alt)
            elif child.tag == 'br':
                self.new_line()
            else:
                self._put_formatted(child, fg_color, bg_color, font, size,
                    bold, italic, underline, strike)

    def put_image(self, path, tip=None):
        '''insert an image at the current position
        tip it's the alt text on mouse over'''
        raise NotImplementedError('Not implemented')

    def new_line(self):
        '''put a new line on the text'''
        raise NotImplementedError('Not implemented')


