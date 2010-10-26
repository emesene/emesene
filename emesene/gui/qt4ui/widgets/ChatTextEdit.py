# -*- coding: utf-8 -*-

'''This module contains the ChatTextEdit class'''

import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore
from PyQt4.QtCore   import Qt

import gui
import e3

import os


class ChatTextEdit (QtGui.QTextEdit):
    '''A widget suited for editing chat lines. Provides as-you-type
    smileys, color settings and font settings, chat line history'''
    return_pressed = QtCore.pyqtSignal()
    style_changed = QtCore.pyqtSignal()
    
    def __init__(self, parent=None):
        '''Constructor'''
        QtGui.QTextEdit.__init__(self, parent)
        self._chat_lines = [""]
        self._current_chat_line_idx = 0

        self._smiley_dict = {}
        self._reverse_smiley_dict = {}
        self._max_shortcut_len = 0

        self._qt_color = QtGui.QColor("#000000")


    def set_smiley_dict(self, smiley_dict):
        '''Sets the smiley recognized by this widget'''
        # TODO: investigate behaviour on case-sensitiveness
        shortcuts = smiley_dict.keys()
        #print "shortcuts: " + unicode(shortcuts)
        for shortcut in shortcuts:
            path = gui.theme.emote_to_path(shortcut)
            if not path:
                print "\t%s, %s" % (shortcut, smiley_dict[shortcut])
                continue
            path = path[6:]
            path = os.path.abspath(path)
            self._smiley_dict[unicode(shortcut.lower())] = unicode(path)
            self._reverse_smiley_dict[unicode(path)]=unicode(shortcut.lower())
            current_len = len(shortcut)
            if current_len > self._max_shortcut_len:
                self._max_shortcut_len = current_len


    def insert_text_after_cursor(self, text):
        '''Insert given text at current cursor's position'''
        text = unicode(text)
        for i in range(len(text)):
            # It's a little bit dirty, but seems to work....
            fake_event = QtGui.QKeyEvent(QtCore.QEvent.KeyPress, 0, 
                                         Qt.NoModifier, text[i])
            self.keyPressEvent(fake_event)


    def _insert_char(self, char):
        '''Inserts a single char, checking for smileys'''
        # this method uses python's builtin string type, not QString
        cursor = self.textCursor()
        max_shortcut_len = self._max_shortcut_len
        shortcuts = self._smiley_dict.keys()
        smiley_found = False

        text_search = unicode(char).lower()
        i = 0
        while i < max_shortcut_len-1:
            # TODO: check if the returned QChar is valid
            last_char = self.document().characterAt(cursor.position()-1-i)  \
                                                                    .toLower()
            if last_char.isPrint():
                last_char = QtCore.QString(last_char)
                text_search = unicode(last_char) + text_search
            i += 1
            #print "parsing",
            #print [text_search],
            length = len(text_search)
            #print " (%d)" % length
            if text_search in shortcuts:
                #print "\t FOUND"
                for i in range(length-1):
                    cursor.deletePreviousChar()
                cursor.insertHtml('<img src="%s" />' % 
                                  self._smiley_dict[text_search])
                smiley_found = True
                return smiley_found
        #print "\t No smiley Found"
        return smiley_found


    def _swap_to_chat_line(self, idx):
        '''Swaps to the given chat line in the history'''
        if idx < 0 or idx > len(self._chat_lines)-1:
            #print "(%d) doing nothing" % idx
            return
        else:
            #print "switching to %d" % idx
            self._chat_lines[self._current_chat_line_idx] = self.toHtml()
            QtGui.QTextEdit.setHtml(self, self._chat_lines[idx])
            cur = self.textCursor()
            cur.setPosition( self.document().characterCount()-1 )
            self.setTextCursor(cur)
            self._current_chat_line_idx = idx


    def show_font_chooser(self):
        '''Shows the font style chooser'''
        qt_font = self._get_qt_font()
        new_qt_font, result = QtGui.QFontDialog.getFont(qt_font)
        if result:
            print "accepted"
            self._set_qt_font(new_qt_font)
        else:
            print "canceled"
            
            
    def show_color_chooser(self):
        '''Shows the font color chooser'''
        qt_color = self._qt_color
        new_qt_color = QtGui.QColorDialog.getColor(qt_color)
        if new_qt_color.isValid() and not new_qt_color == qt_color:
            self._set_qt_color(new_qt_color)
            

    def _get_e3_style(self):
        '''Returns the font style in e3 format'''
        qt_font = self._get_qt_font()
        qt_color = self._get_qt_color()
        
        e3_color = e3.Color.from_hex(unicode(qt_color.name()))
        e3_color.alpha = qt_color.alpha()
        
        font = unicode(qt_font.family())
        print "Font's raw Name: " + font
        print "Font default family: " + qt_font.defaultFamily()
        
        e3_style = e3.Style(font, e3_color, qt_font.bold(), 
                                            qt_font.italic(),
                                            qt_font.underline(), 
                                            qt_font.strikeOut(), 
                                            qt_font.pointSize())
        print qt_font.toString()
        print e3_style
        return e3_style
        
    
    def _set_e3_style(self, e3_style):
        e3_color = e3_style.color
        qt_color = QtGui.QColor(e3_color.red,  e3_color.green, 
                                e3_color.blue, e3_color.alpha  )
        qt_font = QtGui.QFont()
        qt_font.setFamily(      e3_style.font   )
        qt_font.setBold(        e3_style.bold   )
        qt_font.setItalic(      e3_style.italic )
        qt_font.setStrikeOut(   e3_style.strike )
        qt_font.setPointSize(      e3_style.size   )
        
        self._set_qt_color(qt_color)
        self._set_qt_font(qt_font)
        
    
    e3_style = property(_get_e3_style, _set_e3_style)
        

    def _set_qt_font(self, new_font):
        '''sets the font style in qt format'''
        old_font = self._get_qt_font()
        self.document().setDefaultFont(new_font)
        if not old_font == new_font:
            self.style_changed.emit()


    def _get_qt_font(self):
        '''Returns the default font in qt format'''
        return self.document().defaultFont()
        

    def _set_qt_color(self, new_color):
        '''Sets the color'''
        old_color = self._qt_color
        self._qt_color = new_color
        self.setStyleSheet("QTextEdit{color: %s;}"    \
                           "QMenu{color: palette(text);}" % new_color.name() )
        print type(self.viewport())
        print str(self.viewport().objectName())
        if not old_color == new_color:
            self.style_changed.emit()


    def _get_qt_color(self):
        '''gets the color'''
        return self._qt_color
        
# -------------------- QT_OVERRIDE

    def keyPressEvent(self, event):
        '''handles special key combinations: Return, CTRL+Return,
        CTRL+UP, CTRL+DOWN'''
        # pylint: disable=C0103
        if event.key() == Qt.Key_Return:
            if event.modifiers() == Qt.ControlModifier:
                temp = QtGui.QKeyEvent(QtCore.QEvent.KeyPress,
                                 Qt.Key_Return,
                                 Qt.NoModifier,
                                 event.text(),
                                 event.isAutoRepeat(),
                                 event.count())
                event = temp
            else:
                self.return_pressed.emit()
                return
        if event.key() == Qt.Key_Up and     \
           event.modifiers() == Qt.ControlModifier:
            self._swap_to_chat_line(self._current_chat_line_idx + 1)
            return
        if event.key() == Qt.Key_Down and   \
           event.modifiers() == Qt.ControlModifier:
            self._swap_to_chat_line(self._current_chat_line_idx - 1)
            return
        if event.text().length() > 0:
            if self._insert_char(event.text()):
                return
        QtGui.QTextEdit.keyPressEvent(self, event)
        
    
    def canInsertFromMimeData(self, source):
        '''Makes only plain text insertable'''
        # pylint: disable=C0103
        if source.hasText():
            return True
        else:
            return False

    def insertFromMimeData(self, source):
        '''Inserts from mime data'''
        # pylint: disable=C0103
        self.insert_text_after_cursor(source.text())

    def createMimeDataFromSelection(self):
        '''Creates a mime data object from selection'''
        # pylint: disable=C0103
        mime_data = QtGui.QTextEdit.createMimeDataFromSelection(self)
        if mime_data.hasHtml():
            parser = MyHTMLParser(self._reverse_smiley_dict)
            parser.feed(mime_data.html())
            mime_data.setText(parser.get_data())
        return mime_data
        
        
    def clear(self):
        '''clears the widget's contents, saving them'''
        # pylint: disable=C0103
        self._chat_lines.insert(0, "")
        self._current_chat_line_idx += 1
        if len(self._chat_lines) > 100:
            self._chat_lines = self._chat_lines[0:99]
        self._swap_to_chat_line(0)
    
    def toPlainText(self):
        '''Gets a plain text representation of the contents'''
        # pylint: disable=C0103
        parser = MyHTMLParser(self._reverse_smiley_dict)
        parser.feed(self.toHtml())
        return parser.get_data()





from HTMLParser import HTMLParser
class MyHTMLParser (HTMLParser):
    '''This class parses html text, collecting plain
    text and substituting <img> tags with a proper 
    smiley shortcut if any'''
    
    def __init__(self, reverse_img_dict):
        '''Constructor'''
        HTMLParser.__init__(self)
        self._reverse_img_dict = reverse_img_dict
        self._in_body = False
        self._data = ''

    def reset(self):
        '''Resets the parser'''
        HTMLParser.reset(self)
        self._in_body = False
        self._data = ""

    def feed(self, html_string):
        '''Feeds the parser with an html string to parse'''
        if isinstance(html_string, QtCore.QString):
            html_string = unicode(html_string)
        HTMLParser.feed(self, html_string)

    def handle_starttag(self, tag, attrs):
        '''Handle opening tags'''
        #print "TAG: %s, ATTRS: %s" % (tag, attrs)
        if self._in_body:
            if tag == "body":
                raise NameError("Malformed HTML")
            if tag == "img":
                key = attrs[0][1]
                if key in self._reverse_img_dict.keys():
                    alt = self._reverse_img_dict[key]
                    self._data += alt
                else:
                    raise NameError("Unrecognized Image")
        else:
            if tag == "body":
                self._in_body = True

    def handle_endtag(self, tag):
        '''Handle closing tags'''
        if self._in_body:
            if tag == "body":
                self._in_body = False

    def handle_data(self, data):
        '''Handle data sequences'''
        #print "DATA :",
        #print data
        if self._in_body:
            self._data += data

    def get_data(self):
        '''returns parsed string'''
        # [1:] is to trim the leading line break.
        return self._data[1:]















