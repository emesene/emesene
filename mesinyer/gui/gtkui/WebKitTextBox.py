import gtk
import webbrowser
import re

try:
    import webkit
    ERROR = False
except ImportError:
    ERROR = True

import e3
from debugger import dbg

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
        self._textbox.connect('navigation-requested', self._navigation_requested_cb)
        self.clear()
        self._textbox.show()
        self.add(self._textbox)

    def clear(self):
        '''clear the content'''
        self._texts = []
        self.loaded = False
        self.text = HTML_BODY

    def append(self, text, cedict=None, scroll=True):
        '''append formatted text to the widget'''
        if not self.loaded:
            self._texts.append(text)
            return

        if not self.config or self.config.b_show_emoticons:
            text = e3.common.MarkupParser.parse_emotes(text, cedict)
    
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
        dbg(message, 'webkittb', 1)

    def _loading_stop_cb(self, view, frame):
        '''method called when the page finish loading'''
        self.loaded = True
        for text in self._texts:
            self.append(text)

        self._texts = []

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
        self._textbox.load_string(text, "text/html", "utf-8", "file://")

    def _get_text(self):
        '''return the text of the widget'''
        self._textbox.execute_script('oldtitle=document.title;document.title=document.documentElement.innerHTML;')
        html = self._textbox.get_main_frame().get_title()
        self._textbox.execute_script('document.title=oldtitle;')
        return html

    text = property(fget=_get_text, fset=_set_text)

HTML_BODY = '''
<html>
 <head>
  <title>lol</title>
  <style type="text/css">
    .message-outgoing, .message-incomming, .consecutive-incomming, .consecutive-outgoing, .message-history
    {
        -webkit-border-radius: 1em;
        margin: 2px;
        width: 100%;
        display: table;
    }

    .message-outgoing
    {
        -webkit-border-bottom-left-radius: 0px;
        border: 2px solid #cccccc; background-color: #eeeeee; padding: 5px;
    }

    .message-history
    {
        border: 2px solid #cccccc; background-color: #f3f3f3; padding: 5px;
    }

    .message-incomming
    {
        -webkit-border-bottom-right-radius: 0px;
        border: 2px solid #cccccc; background-color: #ffff99; padding: 5px;
        text-align: right;
    }

    .consecutive-incomming
    {
        -webkit-border-bottom-right-radius: 0px;
        border: background-color: #ddf8d0; padding: 5px;
        text-align: right;
        width: 97%;
        margin-right: 2%;
    }

    .consecutive-outgoing
    {
        -webkit-border-bottom-left-radius: 0px;
        border: background-color: #f0f8ff; padding: 5px;
        width: 97%;
        margin-left: 2%;
    }
  </style>
 </head>

 <body>
  <div id="wrapper">
  </div>
  <script type="text/javascript">
    function add_message(message)
    {
        var container = document.getElementById("wrapper");
        var content = document.createElement("div");
        content.innerHTML = message;
        container.appendChild(content);
    }
  </script>
 </body>
</html>
'''

