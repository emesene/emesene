import gtk

try:
    import webkit
    ERROR = False
except ImportError:
    ERROR = True

import e3common.MarkupParser
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
        self.__texts = []
        self.loaded = False
        self._textbox = webkit.WebView()
        self._textbox.connect('load-finished', self._loading_stop_cb)
        self._textbox.connect('console-message', self._error_cb)
        self.clear()
        self._textbox.show()
        self.add(self._textbox)

    def clear(self):
        '''clear the content'''
        self.__texts = []
        self.loaded = False
        self._textbox.load_string(HTML_BODY, "text/html", "utf-8", "")

    def append(self, text, scroll=True):
        '''append formatted text to the widget'''
        if not self.loaded:
            self.__texts.append(text)
            return

        if not self.config or self.config.b_show_emoticons:
            text = e3common.MarkupParser.parse_emotes(text)

        text = text.replace('\r\n', '<br/>').replace('\n', '<br/>')
        text = text.replace('"', '\\"')
        self._textbox.execute_script('add_message("%s");' % (text,))

        if scroll:
            self.scroll_to_end()

    def _error_cb(self, view, message, line, source_id):
        '''called when a message is sent to the console'''
        message = "Webkit message: %s %s %s" % (message, line, source_id)
        self.append(message)
        dbg(message, 'webkittb', 1)

    def _loading_stop_cb(self, view, frame):
        '''method called when the page finish loading'''
        self.loaded = True
        for text in self.__texts:
            self.append(text)

        del self.__texts

    def scroll_to_end(self):
        '''scroll to the end of the content'''
        vadjustment = self.get_vadjustment()
        if vadjustment.upper != vadjustment.page_size:
            vadjustment.set_value(vadjustment.upper)

    def _set_text(self, text):
        '''set the text on the widget'''
        self._buffer.set_text(text)

    def _get_text(self):
        '''return the text of the widget'''
        start_iter = self._buffer.get_start_iter()
        end_iter = self._buffer.get_end_iter()
        return self._buffer.get_text(start_iter, end_iter, True)

    text = property(fget=_get_text, fset=_set_text)

HTML_BODY = '''
<html>
 <head>
  <title>lol</title>
  <style type="text/css">
    .message-outgoing, .message-incomming, .consecutive-incomming, .consecutive-outgoing
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

if __name__ == '__main__':
    def _on_activate(entry, *args):
        output.append(entry.get_text())
        entry.set_text("")

    window = gtk.Window()
    vbox = gtk.VBox()
    output = OutputText(None)
    input = gtk.Entry()
    input.connect("activate", _on_activate)
    vbox.pack_start(output, True, True)
    vbox.pack_start(input, False)
    window.add(vbox)
    window.show_all()
    gtk.main()

