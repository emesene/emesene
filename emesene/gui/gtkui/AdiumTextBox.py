import os
import gtk
import logging
log = logging.getLogger('gtkui.AdiumTextBox')
import webkit

import gui

class OutputView(webkit.WebView):
    '''a class that represents the output widget of a conversation
    '''

    def __init__(self, theme, source, target, target_display, source_img,
            target_img):
        webkit.WebView.__init__(self)
        self.theme = theme
        self.last_incoming = None
        self.last_incoming_account = None
        self.ready = False
        self.pending = []
        self.connect('load-finished', self._loading_finished_cb)
        self.connect('populate-popup', self.on_populate_popup)

    def _loading_finished_cb(self, *args):
        '''callback called when the content finished loading
        '''
        self.ready = True

        for function in self.pending:
            self.execute_script(function)

        self.execute_script("scrollToBottom()")
        self.pending = []

    def clear(self, source="", target="", target_display="",
            source_img="", target_img=""):
        '''clear the content'''
        body = self.theme.get_body(source, target, target_display, source_img,
                target_img)
        self.load_string(body,
                "text/html", "utf-8", "file://" + self.theme.path)
        self.pending = []
        self.ready = False

    def add_message(self, msg, style=None, cedict={}, cedir=None):
        '''add a message to the conversation'''

        if msg.incoming:
            if self.last_incoming is None:
                self.last_incoming = False

            msg.first = not self.last_incoming
            if self.last_incoming_account != msg.sender:
                msg.first = True
            html = self.theme.format_incoming(msg, style, cedict, cedir)
            self.last_incoming = True
            self.last_incoming_account = msg.sender
        else:
            if self.last_incoming is None:
                self.last_incoming = True

            msg.first = self.last_incoming
            html = self.theme.format_outgoing(msg, style, cedict, cedir)
            self.last_incoming = False

        html = html.replace("\n", "<br>")

        if msg.first:
            function = "appendMessage('" + html + "')"
        else:
            function = "appendNextMessage('" + html + "')"

        self.append(function)

    def append(self, function):
        '''append a message if the renderer finished loading, append it to
        pending if still loading
        '''
        if self.ready:
            self.execute_script(function)
            self.execute_script("scrollToBottom()")
        else:
            self.pending.append(function)

    def _set_text(self, text):
        '''set the text on the widget'''
        self._textbox.load_string(text, "text/html", "utf-8", "")
        self.pending = []
        self.ready = False

    def _get_text(self):
        '''return the text of the widget'''
        self._textbox.execute_script('oldtitle=document.title;document.title=document.documentElement.innerHTML;')
        html = self._textbox.get_main_frame().get_title()
        self._textbox.execute_script('document.title=oldtitle;')
        return html

    text = property(fget=_get_text, fset=_set_text)

    def on_populate_popup(self, view, menu):
        '''disables the right-click menu by removing the MenuItems'''
        for child in menu.get_children():
            menu.remove(child)


class OutputText(gtk.ScrolledWindow):
    '''a text box inside a scroll that provides methods to get and set the
    text in the widget'''
    NAME = 'Adium Output'
    DESCRIPTION = _('A widget to display conversation messages using adium style')
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
        picture = os.path.abspath(gui.theme.user)
        self.view = OutputView(gui.theme.conv_theme, "", "", "", picture,
                picture)
        self.view.connect('load-finished', self._loading_stop_cb)
        self.view.connect('console-message', self._error_cb)
        self.clear()
        self.view.show()
        self.add(self.view)

    def clear(self):
        '''clear the content'''
        self._texts = []
        self.loaded = False
        self.view.clear()

    def _error_cb(self, view, message, line, source_id):
        '''called when a message is sent to the console'''
        message = _("Webkit message: %s %s %s") % (message, line, source_id)
        log.debug(message)

    def _loading_stop_cb(self, view, frame):
        '''method called when the page finish loading'''
        self.loaded = True
        for text in self._texts:
            self.append(text)

        self._texts = []

    def send_message(self, formatter, contact, text, cedict, cedir, style, is_first):
        '''add a message to the widget'''
        msg = gui.Message.from_contact(contact, text, is_first, False)
        self.view.add_message(msg, style, cedict, cedir)

    def receive_message(self, formatter, contact, message, cedict, cedir, is_first):
        '''add a message to the widget'''
        msg = gui.Message.from_contact(contact, message.body, is_first, True)
        # WARNING: this is a hack to keep out config from backend libraries
        message.style.size = self.config.get_or_set("i_font_size", 10)
        self.view.add_message(msg, message.style, cedict, cedir)

    def information(self, formatter, contact, message):
        '''add an information message to the widget'''
        # TODO: make it with a status message
        msg = gui.Message.from_contact(contact, message, False, True)
        self.view.add_message(msg, None, None, None)

