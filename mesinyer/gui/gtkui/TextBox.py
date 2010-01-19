import gtk
import gobject

import gui
import utils
import RichBuffer

from gui.base import MarkupParser

class TextBox(gtk.ScrolledWindow):
    '''a text box inside a scroll that provides methods to get and set the
    text in the widget'''

    def __init__(self, config):
        '''constructor'''
        gtk.ScrolledWindow.__init__(self)

        self.config = config

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self._textbox = gtk.TextView()
        self._textbox.set_left_margin(2)
        self._textbox.set_right_margin(2)
        self._textbox.set_wrap_mode(gtk.WRAP_WORD_CHAR)
        self._textbox.show()
        self._buffer = RichBuffer.RichBuffer()
        self._textbox.set_buffer(self._buffer)
        self.add(self._textbox)

    def clear(self):
        '''clear the content'''
        self._buffer.set_text('')

    def _append(self, text, scroll=True, fg_color=None, bg_color=None,
        font=None, size=None, bold=False, italic=False, underline=False,
        strike=False):
        '''append text to the widget'''
        self._buffer.put_text(text, fg_color, bg_color, font, size, bold,
            italic, underline, strike)

        if scroll:
            self.scroll_to_end()

    def append(self, text, scroll=True):
        '''append formatted text to the widget'''
        self._buffer.put_formatted(text)
        [self._textbox.add_child_at_anchor(*item)
            for item in self._buffer.widgets]

        self._buffer.widgets = []

        if scroll:
            self.scroll_to_end()

    def scroll_to_end(self):
        '''scroll to the end of the content'''
        end_iter = self._buffer.get_end_iter()
        self._textbox.scroll_to_iter(end_iter, 0.0, yalign=1.0)

    def _set_text(self, text):
        '''set the text on the widget'''
        self._buffer.set_text(text)

    def _get_text(self):
        '''return the text of the widget'''
        start_iter = self._buffer.get_start_iter()
        end_iter = self._buffer.get_end_iter()
        return self._buffer.get_text(start_iter, end_iter, True)

    text = property(fget=_get_text, fset=_set_text)

class InputText(TextBox):
    '''a widget that is used to insert the messages to send'''
    NAME = 'Input Text'
    DESCRIPTION = 'A widget to enter messages on the conversation'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, config, on_send_message):
        '''constructor'''
        TextBox.__init__(self, config)
        self.on_send_message = on_send_message
        self._tag = None
        self._textbox.connect('key-press-event', self._on_key_press_event)
        self._buffer.connect('changed', self.on_changed_event)

        self.changed = False
        gobject.timeout_add(500, self.parse_emotes)
        self.invisible_tag = gtk.TextTag()
        self.invisible_tag.set_property('invisible', True)
        self._buffer.get_tag_table().add(self.invisible_tag)

    def grab_focus(self):
        """
        override grab_focus method
        """
        self._textbox.grab_focus()

    def _on_key_press_event(self, widget, event):
        '''method called when a key is pressed on the input widget'''
        self.changed = True
        self.apply_tag()
        if (event.keyval == gtk.keysyms.Return or \
                event.keyval == gtk.keysyms.KP_Enter) and \
                not event.state == gtk.gdk.SHIFT_MASK:
            if not self.text:
                return True

            self.on_send_message(self.text)
            self.text = ''
            return True
        elif event.keyval == gtk.keysyms.BackSpace:
            # do backspace while we are at an invisible tag
            iter_ = self._buffer.get_iter_at_mark(self._buffer.get_mark('insert'))
            while iter_.ends_tag(self.invisible_tag) or \
                    iter_.begins_tag(self.invisible_tag):
                self._buffer.backspace(iter_, True, True)

    def parse_emotes(self):
        """
        parse the emoticons in the widget and replace them with
        images
        """
        if not self.changed:
            return True

        self.changed = False
        emos = []

        for code in gui.Theme.EMOTES:
            start = self._buffer.get_start_iter()
            path = gui.theme.emote_to_path(code, True)
            result = start.forward_search(code,
                    gtk.TEXT_SEARCH_VISIBLE_ONLY)

            if result is None:
                continue

            while result:
                position, end = result
                image = utils.safe_gtk_image_load(path)
                image.show()

                self._buffer.apply_tag(self.invisible_tag, position, end)

                mark_position = self._buffer.create_mark(None, position)
                mark_end = self._buffer.create_mark(None, end)

                emos.append((image, position))
                start = end
                result = start.forward_search(code,
                        gtk.TEXT_SEARCH_VISIBLE_ONLY)

        for image, position in emos:
                anchor = self._buffer.create_child_anchor(position)
                self._textbox.add_child_at_anchor(image, anchor)

        return True

    def update_style(self, style):
        '''update the global style of the widget'''
        try:
            color = gtk.gdk.color_parse('#' + style.color.to_hex())
            gtk.gdk.colormap_get_system().alloc_color(color)
        except ValueError:
            return

        is_new = False
        if self._tag is None:
            self._tag = gtk.TextTag()
            is_new = True

        self._tag.set_property('font-desc',
            utils.style_to_pango_font_description(style))

        self._tag.set_property('foreground', '#' + style.color.to_hex())
        self._tag.set_property('strikethrough', style.strike)
        self._tag.set_property('underline', style.underline)

        if is_new:
            self._buffer.get_tag_table().add(self._tag)

        self.apply_tag()

    def on_changed_event(self, *args):
        '''called when the content of the buffer changes'''
        self.apply_tag()

    def apply_tag(self):
        '''apply the tag that contains the global style to the text in
        the widget'''
        if self._tag:
            self._buffer.apply_tag(self._tag, self._buffer.get_start_iter(),
                self._buffer.get_end_iter())

class OutputText(TextBox):
    '''a widget that is used to display the messages on the conversation'''
    NAME = 'Output Text'
    DESCRIPTION = 'A widget to display the conversation messages'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, config):
        '''constructor'''
        TextBox.__init__(self, config)
        self.set_shadow_type(gtk.SHADOW_IN)
        self._textbox.set_editable(False)
        self._textbox.set_cursor_visible(False)

    def append(self, text, cedict,scroll=True):
        '''append formatted text to the widget'''
        if self.config.b_show_emoticons:
            text = MarkupParser.parse_emotes(text)

        TextBox.append(self, text, scroll)
