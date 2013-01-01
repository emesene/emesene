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

'''This module contains the ChatInput class'''

import logging
import os

import PyQt4.QtGui as QtGui
import PyQt4.QtCore  as QtCore
from PyQt4.QtCore import Qt

import e3
import gui
from HTMLParser import HTMLParser
from gui.qt4ui import Utils
log = logging.getLogger('qt4ui.widgets.ChatInput')

try:
    from SpellTextEdit import SpellTextEdit as BaseInput
except enchant.errors.DictNotFoundError:
    from QtGui import QTextEdit as BaseInput


class ChatInput (BaseInput):
    '''A widget suited for editing chat lines. Provides as-you-type
    smileys, color settings and font settings, chat line history'''
    NAME = 'Input Text'
    DESCRIPTION = 'A widget to enter messages on the conversation'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''

    style_changed = QtCore.pyqtSignal()

    def __init__(self, session, on_send_message, on_cycle_history,
                    send_typing_notification, parent=None):
        '''Constructor'''
        BaseInput.__init__(self, parent)

        self._smiley_dict = {}
        self._max_shortcut_len = 0

        self.session = session
        self.on_send_message = on_send_message
        self.on_cycle_history = on_cycle_history
        self.send_typing_notification = send_typing_notification

        self._emote_theme = gui.theme.emote_theme
        self._qt_color = QtGui.QColor(Qt.black)

        # typing notification
        self.typing_timer = QtCore.QTimer()
        self.typing_timer.setSingleShot(False)
        self.typing_timer.timeout.connect(self.on_send_typing_notification)

        if hasattr(BaseInput, 'setActivateSpellCheck'):
            self.setActivateSpellCheck(self.session.config.b_enable_spell_check)
        self.subscribe_signals()

    def subscribe_signals(self):
        if hasattr(BaseInput, 'setActivateSpellCheck'):
            self.session.config.subscribe(self.enable_spell_check_change,
                                            'b_enable_spell_check')

    def enable_spell_check_change(self, active):
        '''enable/disable spell check'''
        self.setActivateSpellCheck(active)

    def unsubscribe_signals(self):
        if hasattr(BaseInput, 'setActivateSpellCheck'):
            self.session.config.unsubscribe(self.enable_spell_check_change,
                                            'b_enable_spell_check')

    # emesene's
    def update_style(self, style):
        '''update style'''
        self.e3_style = style

    def set_smiley_dict(self, smiley_dict):
        '''Sets the smiley recognized by this widget'''
        shortcuts = smiley_dict.keys()

        for shortcut in shortcuts:
            path = unicode(self._emote_theme.emote_to_path(shortcut))
            if not path:
                log.warning('No image path for: \t%s, %s'
                              % (shortcut, smiley_dict[shortcut]))
                continue
            shortcut = unicode(shortcut)
            path = os.path.abspath(path[7:])
            self._smiley_dict[shortcut] = path

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

        max_shortcut_len = self._max_shortcut_len
        shortcuts = self._smiley_dict.keys()

        cursor = self.textCursor()
        text_search = unicode(char)
        i = 0
        while i < max_shortcut_len - 1:
            # TODO: check if the returned QChar is valid
            last_char = self.document().characterAt(cursor.position() - 1 - i)
            if last_char.isPrint():
                last_char = QtCore.QString(last_char)
                text_search = unicode(last_char) + text_search
            i += 1
            length = len(text_search)
            if text_search in shortcuts:
                for i in range(length - 1):
                    cursor.deletePreviousChar()
                self._insert_image_resource(text_search)
                cursor.insertImage(text_search)
                # Prevent the color from changing:
                self.setTextColor(self._qt_color)
                return True
        return False

    def _insert_image_resource(self, shortcut):
        '''Appends an image resource to this widget's
        QTextDocument'''
        image = QtGui.QImage(self._smiley_dict[shortcut])
        self.document().addResource(QtGui.QTextDocument.ImageResource,
                                   QtCore.QUrl(shortcut), image)

    def _get_e3_style(self):
        '''Returns the font style in e3 format'''
        qt_font = self._get_qt_font()
        e3_color = Utils.qcolor_to_e3_color(self._qt_color)
        e3_style = Utils.qfont_to_style(qt_font, e3_color)
        return e3_style

    def _set_e3_style(self, e3_style):
        '''Sets the font style, given an e3 style'''
        qt_color = Utils.e3_color_to_qcolor(e3_style.color)
        qt_font = QtGui.QFont()
        qt_font.setFamily(e3_style.font)
        qt_font.setBold(e3_style.bold)
        qt_font.setItalic(e3_style.italic)
        qt_font.setStrikeOut(e3_style.strike)
        qt_font.setPointSize(e3_style.size)

        self._set_qt_color(qt_color)
        self._set_qt_font(qt_font)

    e3_style = property(_get_e3_style, _set_e3_style)

    def _set_qt_font(self, new_font):
        '''sets the font style in qt format'''
        old_font = self._get_qt_font()
        self.document().setDefaultFont(new_font)
        if old_font != new_font:
            self.style_changed.emit()

    def _get_qt_font(self):
        '''Returns the default font in qt format'''
        return self.document().defaultFont()

    def _set_qt_color(self, new_color):
        '''Sets the color'''
        old_color = self._qt_color
        self._qt_color = new_color

        cursor = self.textCursor()
        cursor_position = cursor.position()
        cursor.select(QtGui.QTextCursor.Document)
        char_format = QtGui.QTextCharFormat()
        char_format.setForeground(QtGui.QBrush(new_color))
        cursor.mergeCharFormat(char_format)
        cursor.setPosition(cursor_position)

        # We need this beacause the previous stuff doesn't work for the last
        # block, if the block is empty. (i.e.: empty QTextEdit, QTextEdit's
        # document ends with an image (so there's an empty block after it))
        # Oh, and obviously this is not enough (and we need the previous part
        # because it just changes current block's format!
        self.setTextColor(new_color)

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
                self._on_send_btn_clicked()
                return

        if (event.key() == Qt.Key_Up or event.key() == Qt.Key_P) and \
           event.modifiers() == Qt.ControlModifier:
                self.on_cycle_history()
                return
        if (event.key() == Qt.Key_Down or event.key() == Qt.Key_N) and \
           event.modifiers() == Qt.ControlModifier:
                self.on_cycle_history(1)
                return
        if event.text().length() > 0:
            if not self.typing_timer.isActive():
                self.send_typing_notification()
                self.typing_timer.start(3000)
            if self._insert_char(event.text()):
                return
        QtGui.QTextEdit.keyPressEvent(self, event)

    def on_send_typing_notification(self):
        self.typing_timer.stop()

    def _on_send_btn_clicked(self):
        '''Slot called when the user presses Enter in
        the chat line editor. Sends the message'''
        message_string = unicode(self.toPlainText())
        if len(message_string) == 0:
            return
        self.clear()
        self.on_send_message(message_string)

    def _get_text(self):
        return unicode(self.toPlainText())

    def _set_text(self, text):
        self.clear()
        self.insert_text_after_cursor(text)

    text = property(fget=_get_text, fset=_set_text)

    def canInsertFromMimeData(self, source):
        '''Makes only plain text insertable'''
        if source.hasText():
            return True
        else:
            return False

    def insertFromMimeData(self, source):
        '''Inserts from mime data'''
        self.insert_text_after_cursor(source.text())

    def createMimeDataFromSelection(self):
        '''Creates a mime data object from selection'''
        mime_data = QtGui.QTextEdit.createMimeDataFromSelection(self)
        if mime_data.hasHtml():
            parser = MyHTMLParser()
            parser.feed(mime_data.html())
            mime_data.setText(parser.get_data())
        return mime_data

    def toPlainText(self):
        '''Gets a plain text representation of the contents'''
        parser = MyHTMLParser()
        parser.feed(self.toHtml())
        return parser.get_data()


class MyHTMLParser (HTMLParser):
    '''This class parses html text, collecting plain
    text and substituting <img> tags with a proper
    smiley shortcut if any'''

    def __init__(self):
        '''Constructor'''
        HTMLParser.__init__(self)
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
        if self._in_body:
            if tag == "body":
                raise NameError("Malformed HTML")
            if tag == "img":
                src = attrs[0][1]
                self._data += src
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
        if self._in_body:
            self._data += data

    def handle_charref(self, name):
        self._data += Utils.unescape(u'&%s;' % name)

    def handle_entityref(self, name):
        self._data += Utils.unescape(u'&%s;' % name)

    def get_data(self):
        '''returns parsed string'''
        # [1:] is to trim the leading line break.
        return self._data[1:]
