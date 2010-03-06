import os
import re
import gtk
import webbrowser

import e3
from gui.base import MarkupParser

try:
    import webkit
    ERROR = False
except ImportError:
    ERROR = True

import logging
log = logging.getLogger('gtkui.WebKitTextBox')

class OutputText(gtk.ScrolledWindow):
    '''a text box inside a scroll that provides methods to get and set the
    text in the widget'''
    NAME = 'Webkit Output'
    DESCRIPTION = 'A widget to display conversation messages using webkit'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, config):
        '''constructor'''
        gtk.ScrolledWindow.__init__(self)

        self.config = config

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_IN)
        self._texts = []
        self.loaded = False
        self._textbox = webkit.WebView()
        self._textbox.connect('load-finished', self._loading_stop_cb)
        self._textbox.connect('console-message', self._error_cb)
        #self._textbox.connect('navigation-requested', self._navigation_requested_cb)
        self.clear()
        self._textbox.show()
        self.add(self._textbox)

    def clear(self):
        '''clear the content'''
        self._texts = []
        self.loaded = False

        dir_path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join("file://", dir_path , "conversation.html")

        self._textbox.open(path)

    def append(self, text, cedict=None, scroll=True):
        '''append formatted text to the widget'''
        if not self.loaded:
            self._texts.append(text)
            return

        if not self.config or self.config.b_show_emoticons:
            text = MarkupParser.parse_emotes(text, cedict)

        text = text.replace('\r\n', '<br/>').replace('\n', '<br/>')
        text = self.parse_url(text)
        text = text.replace('"', '\\"')
        self._textbox.execute_script('add_message("%s");' % (text,))

        if scroll:
            self.scroll_to_end()

    def parse_url(self, text):
        urlfinders = [
            re.compile("([0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}|(((news|telnet|nttp|http|ftp|https)://)|(www|ftp)[-A-Za-z0-9]*\\.)[-A-Za-z0-9\\.]+)(:[0-9]*)?/[-A-Za-z0-9_\\$\\.\\+\\!\\*\\(\\),;:@&=\\?/~\\#\\%]*[^]'\\.}>\\),\\\"]"),
            re.compile("([0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}|(((news|telnet|nttp|http|ftp|https)://)|(www|ftp)[-A-Za-z0-9]*\\.)[-A-Za-z0-9\\.]+)(:[0-9]*)?"),
            re.compile("'\\<((mailto:)|)[-A-Za-z0-9\\.]+@[-A-Za-z0-9\\.]+"),
        ]
        for i in urlfinders:
            text = i.sub("<a href=\"\g<0>\">\g<0></a>", text)

        return text

    def _error_cb(self, view, message, line, source_id):
        '''called when a message is sent to the console'''
        message = "Webkit message: %s %s %s" % (message, line, source_id)
        self.append(message)
        log.debug(message)

    def _loading_stop_cb(self, view, frame):
        '''method called when the page finish loading'''
        self.loaded = True
        for text in self._texts:
            self.append(text)

        self._texts = []

    # XXX: not used
    def _navigation_requested_cb(self, view, frame, networkRequest):
        uri = networkRequest.get_uri()
        uri = uri.replace('file://', '')

        if re.match("^(news|telnet|nttp|http|ftp|https)://", uri) is None:
            uri = 'http://' + uri

        webbrowser.open(uri)
        return 1

    def scroll_to_end(self):
        '''scroll to the end of the content'''
        vadjustment = self.get_vadjustment()
        if vadjustment.upper != vadjustment.page_size:
            vadjustment.set_value(vadjustment.upper)

    def _set_text(self, text):
        '''set the text on the widget'''
        self._textbox.load_string(text, "text/html", "utf-8", "")

    def _get_text(self):
        '''return the text of the widget'''
        self._textbox.execute_script('oldtitle=document.title;document.title=document.documentElement.innerHTML;')
        html = self._textbox.get_main_frame().get_title()
        self._textbox.execute_script('document.title=oldtitle;')
        return html

    text = property(fget=_get_text, fset=_set_text)

    def send_message(self, formatter, contact, text, cedict, style, is_first):
        '''add a message to the widget'''
        nick = contact.display_name

        is_raw, consecutive, outgoing, first, last = \
            formatter.format(contact)

        if is_raw:
            middle = MarkupParser.escape(text)
        else:
            middle = MarkupParser.escape(text)
            middle = e3.common.add_style_to_message(middle, style, False)

        all_ = first + middle + last
        self.append(all_, cedict, self.config.b_allow_auto_scroll)

    def receive_message(self, formatter, contact, message, cedict, is_first):
        '''add a message to the widget'''
        is_raw, consecutive, outgoing, first, last = formatter.format(contact)

        middle = MarkupParser.escape(message.body)
        if not is_raw:
            middle = e3.common.add_style_to_message(message.body, message.style)

        self.append(first + middle + last, cedict, self.config.b_allow_auto_scroll)

    def information(self, formatter, contact, message):
        '''add an information message to the widget'''
        self.append(formatter.format_information(message), None,
                self.config.b_allow_auto_scroll)

