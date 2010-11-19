# -*- coding: utf-8 -*-

''' This module contains the utilities'''

import xml

import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore
from PyQt4.QtCore   import Qt

from gui.base import MarkupParser



# consider changing these directly in MarkupParser
def escape(string, add_dic=None):
    '''replace the values on dic keys with the values'''
    dic     = {' ': '&nbsp;'}
    if not add_dic:
        add_dic = {}
    add_dic.update(MarkupParser.dic)
    add_dic.update(dic)
    return xml.sax.saxutils.escape(string, dic)
    

def unescape(string, add_dic_inv=None):
    '''replace the values on dic_inv keys with the values'''
    dic_inv = {'&nbsp;': ' '}
    if not add_dic_inv:
        add_dic_inv = {}
    add_dic_inv.update(MarkupParser.dic_inv)
    add_dic_inv.update(dic_inv)
    return xml.sax.saxutils.unescape(string, dic_inv)


def pixmap_rounder(qpixmap, perc_radius=16.7):
    '''Return the given pixmap with corners 
    rounded by the given radius'''
    
    # create the clipping path:
    clip_path = QtGui.QPainterPath()
    clip_path.addRoundedRect( QtCore.QRectF( qpixmap.rect()), 
                              perc_radius, perc_radius, 
                              Qt.RelativeSize)
    
    # create the target pixmap, completerly tansparent
    rounded_pixmap = QtGui.QPixmap(qpixmap.size())
    rounded_pixmap.fill(Qt.transparent)
    
    # create the painter
    painter = QtGui.QPainter(rounded_pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
    
    # paints a black rounded rect. This will be the area where 
    # we will paint the original pixmap
    painter.fillPath(clip_path, Qt.black)
    
    # paints the original pixmap in the black area.
    painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
    rect = QtCore.QRect(QtCore.QPoint(0, 0), qpixmap.size())
    painter.drawPixmap(rect, qpixmap, rect)
    
    painter.end()
    return rounded_pixmap
    
    
    
    

def parse_emotes(text, include_table_tags=True):
    '''Parses emotes in text string, returning a html string laid out
    using a table, to vertically align emotes correctly'''
    text = MarkupParser.replace_emotes(text)
    parser = MyHTMLParser(include_table_tags)
    parser.feed(text)
    text2 = parser.get_data()
    #print '***\n%s\n%s\n***' % (text, text2)
    return text2
    
    
    
    
    
    
    
from HTMLParser import HTMLParser
class MyHTMLParser (HTMLParser):
    '''This class parses html text, collecting plain
    text and substituting <img> tags with a proper 
    smiley shortcut if any'''
    
    def __init__(self, include_table_tags):
        '''Constructor'''
        HTMLParser.__init__(self)
        self._include_table_tags = include_table_tags
        self._italic = False
        self._bold   = False
        self._small  = False
        if self._include_table_tags:
            self._data = u'<table cellspacing="0"><tr>'

    def reset(self):
        '''Resets the parser'''
        HTMLParser.reset(self)
        self._data = ''

    def feed(self, html_string):
        '''Feeds the parser with an html string to parse'''
        if isinstance(html_string, QtCore.QString):
            html_string = unicode(html_string)
        HTMLParser.feed(self, html_string)

    def handle_starttag(self, tag, attrs):
        '''Handle opening tags'''
        if tag == 'img':
            src = attrs[0][1]
            src = src.replace('file://', '')
            self._data += u'<td valign="middle"><img src="%s" \></td>' % src
        if tag == 'i':
            self._italic = True
        if tag == 'b':
            self._bold = True
        if tag == 'small':
            self._small = True
        if tag == 'br':
            self._data += u'</tr></table><table cellspacing="0"><tr>'
        

    def handle_endtag(self, tag):
        '''Handle closing tags'''
        if tag == 'i':
            self._italic = False
        if tag == 'b':
            self._bold = False
        if tag == 'small':
            self._small = False
            
            
    def handle_charref(self, name):
        self._data += u'<td>&%s;</td>' % name
    
    def handle_entityref(self, name):
        self._data += u'<td>&%s;</td>' % name
    
    def handle_data(self, data):
        '''Handle data sequences'''
        #print "DATA :",
        #print data
        if self._italic:
            data = u'<i>%s</i>' % data
        if self._bold:
            data = u'<b>%s</b>' % data
        if self._small:
            data = u'<small>%s</small>' % data
        self._data += u'<td valign="middle">%s</td>' % data

    def get_data(self):
        '''returns parsed string'''
        # [1:] is to trim the leading line break.
        if self._include_table_tags:
            self._data += u'</tr></table>'
        return self._data
