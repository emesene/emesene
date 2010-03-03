import gtk
import gobject

import e3
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
        self._textbox.connect('copy-clipboard', self._on_copy_clipboard)
        self.clipboard = gtk.Clipboard(selection=gtk.gdk.atom_intern("CLIPBOARD"))
        self._buffer.add_selection_clipboard(self.clipboard)
        self.add(self._textbox)
        self.widgets = {}

    def clear(self):
        '''clear the content'''
        self._buffer.set_text('')
        self.widgets = {}

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
        for anchor in self._buffer.widgets.keys():
            widget = self._buffer.widgets[anchor]
            self._textbox.add_child_at_anchor(widget, anchor)
            self.widgets[anchor] = widget

        self._buffer.widgets = {}

        if scroll:
            self.scroll_to_end()

    def scroll_to_end(self):
        '''scroll to the end of the content'''
        end_iter = self._buffer.get_end_iter()
        self._textbox.scroll_to_iter(end_iter, 0.0, yalign=1.0)

    def _set_text(self, text):
        '''set the text on the widget'''
        self._buffer.set_text(text)

    def _replace_emo_with_shortcut(self):
        if not self._buffer.get_has_selection():
            bounds = self._buffer.get_bounds()
            self._buffer.select_range(bounds[0],bounds[1])

        try:
            start, end = self._buffer.get_selection_bounds()
        except ValueError:
            return ""

        if start.get_offset() > end.get_offset():
            start = end #set the right begining

        selection = self._buffer.get_slice(start,end)
        char = u"\uFFFC" #it means "widget or pixbuf here"

        return_string = ""
        for part in unicode(selection):
            if part == char:
                anchor = start.get_child_anchor()
                if anchor is not None:
                    alt = self.widgets[anchor].get_property("tooltip-text")
                    part = alt
            return_string += part #new string with replacements
            start.forward_char()
        return return_string

    def _on_copy_clipboard(self, textview):
        ''' replaces the copied text with a new text with the
        alt text of the images selected at copying '''
        buffer = self._buffer
        if buffer.get_has_selection():
            text = self._replace_emo_with_shortcut()

            # replace clipboard content
            self.clipboard.set_text(text, len(text))
            self.clipboard.store()

    def _get_text(self):
        '''return the text of the widget'''
        bounds = self._buffer.get_bounds()
        self._buffer.select_range(bounds[0],bounds[1])
        text = self._replace_emo_with_shortcut()
        end = self._buffer.get_end_iter()
        self._buffer.select_range(end, end)
        return text

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
            if self.text == "":
                return True

            self.on_send_message(self.text)
            self.text = ''
            return True

    def parse_emotes(self):
        """
        parse the emoticons in the widget and replace them with
        images
        """
        if not self.changed:
            return True

        self.changed = False

        for code in gui.Theme.EMOTES:
            start = self._buffer.get_start_iter()
            path = gui.theme.emote_to_path(code, True)
            result = start.forward_search(code,
                    gtk.TEXT_SEARCH_VISIBLE_ONLY)

            if result is None:
                continue

            while result is not None:
                position, end = result
                mark_begin = self._buffer.create_mark(None, start, False)
                mark_end = self._buffer.create_mark(None, end, False)
                image = utils.safe_gtk_image_load(path)
                image.set_tooltip_text(code)
                image.show()

                self._buffer.delete(position, end)
                pos = self._buffer.get_iter_at_mark(mark_end)
                anchor = self._buffer.create_child_anchor(pos)
                self._textbox.add_child_at_anchor(image, anchor)

                self.widgets[anchor] = image

                start = self._buffer.get_iter_at_mark(mark_end)
                result = start.forward_search(code,
                        gtk.TEXT_SEARCH_VISIBLE_ONLY)
                self._buffer.delete_mark(mark_begin)
                self._buffer.delete_mark(mark_end)

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

    def message(self, formatter, contact, message, cedict):
        '''add a message to the widget'''
        is_raw, consecutive, outgoing, first, last = formatter.format(contact)

        middle = MarkupParser.escape(message.body)
        if not is_raw:
            middle = e3.common.add_style_to_message(message.body, message.style)

        self.append(first + middle + last, cedict, self.config.b_allow_auto_scroll)

    def information(self, formatter, contact, message):
        '''add an information message to the widget'''
        self.append(formatter.format_information(
                '%s just sent you a nudge!' % (contact.display_name,)),
                self.config.b_allow_auto_scroll)

