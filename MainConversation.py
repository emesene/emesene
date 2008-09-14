'''a module that define classes to build the conversation widget'''
import gtk

import utils

class MainConversation(gtk.Notebook):
    '''the main conversation, it only contains other widgets'''

    def __init__(self, session):
        '''class constructor'''
        gtk.Notebook.__init__(self)
        self.session = session
        if self.session:
            self.session.protocol.connect('conv-first-action', 
                self._on_first_action)

    def _on_first_action(self, protocol):
        '''called when an action is made on a conversation to justify the
        creation of a new Conversation'''
        self.new_conversation()

    def new_conversation(self):
        '''create a new conversation widget and append it to the tabs'''
        conversation = Conversation(self.session)
        self.append_page(conversation)
        return conversation

class Conversation(gtk.VBox):
    '''a widget that contains all the components inside'''

    def __init__(self, session):
        '''constructor'''
        gtk.VBox.__init__(self)
        self.session = session
        self.panel = gtk.VPaned()
        self.header = Header()
        self.output = OutputText()
        self.input = InputText()
        self.info = ContactInfo()

        self.panel.pack1(self.output, True, False)
        self.panel.pack2(self.input)

        hbox = gtk.HBox()
        hbox.pack_start(self.panel, True, True)
        hbox.pack_start(self.info, False)

        self.pack_start(self.header, False)
        self.pack_start(hbox, True, True)

        self.temp = self.panel.connect('map', self._on_panel_show)
        self.header.information = Header.INFO_TEMPLATE % ('account@host.com',
            'this is my personal message')
        self.header.set_image(gui.theme.user)
        self.info.first = utils.safe_gtk_image_load(gui.theme.logo)
        self.info.last = utils.safe_gtk_image_load(gui.theme.logo)

    def _on_panel_show(self, widget):
        '''callback called when the panel is shown, resize the panel'''
        position = self.panel.get_position()
        self.panel.set_position(position + int(position * 0.5))
        self.panel.disconnect(self.temp)
        del self.temp

class TextBox(gtk.ScrolledWindow):
    '''a text box inside a scroll that provides methods to get and set the
    text in the widget'''

    def __init__(self):
        '''constructor'''
        gtk.ScrolledWindow.__init__(self)
        self.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_IN)
        self.textbox = gtk.TextView()
        self.textbox.show()
        self.buffer = self.textbox.get_buffer()
        self.add(self.textbox)

    def clear(self):
        '''clear the content'''
        self.buffer.set_text('')

    def append(self, text):
        '''append text to the widget'''
        end_iter = self.buffer.get_end_iter()
        self.buffer.insert(end_iter, text)

    def _set_text(self, text):
        '''set the text on the widget'''
        self.buffer.set_text(text)

    def _get_text(self):
        '''return the text of the widget'''
        start_iter = self.buffer.get_start_iter()
        end_iter = self.buffer.get_end_iter()
        return self.buffer.get_text(start_iter, end_iter, True)

    text = property(fget=_get_text, fset=_set_text)

class InputText(TextBox):
    '''a widget that is used to insert the messages to send'''

    def __init__(self):
        '''constructor'''
        TextBox.__init__(self)

class OutputText(TextBox):
    '''a widget that is used to display the messages on the conversation'''

    def __init__(self):
        '''constructor'''
        TextBox.__init__(self)
        self.textbox.set_editable(False)

class Header(gtk.HBox):
    '''a widget used to display some information about the conversation'''
    INFO_TEMPLATE = '%s\n<span size="small">%s</span>'

    def __init__(self):
        '''constructor'''
        gtk.HBox.__init__(self)
        self._information = gtk.Label('info')
        self._information.set_alignment(0.0, 0.5)
        self.image = gtk.Image()

        self.pack_start(self._information, True, True)
        self.pack_start(self.image, False)

    def set_image(self, path):
        '''set the image from path'''
        self.remove(self.image)
        self.image = utils.safe_gtk_image_load(path)
        self.pack_start(self.image, False)

    def _set_information(self, text):
        '''set the text on the information'''
        self._information.set_markup(text)

    def _get_information(self):
        '''return the text on the information'''
        return self._information.get_markup()

    information = property(fget=_get_information, fset=_set_information)

class ContactInfo(gtk.VBox):
    '''a widget that contains the display pictures of the contacts and our
    own display picture'''

    def __init__(self, first=None, last=None):
        gtk.VBox.__init__(self)
        self._first = first
        self._last = last

        self._first_alig = None
        self._last_alig = None

    def _set_first(self, first):
        '''set the first element and add it to the widget (remove the 
        previous if not None'''

        if self._first_alig is not None:
            self.remove(self._first_alig)

        self._first = first
        self._first_alig = gtk.Alignment(xalign=0.5, yalign=0.0, xscale=1.0,
            yscale=0.1)
        self._first_alig.add(self._first)
        self.pack_start(self._first_alig)

    def _get_first(self):
        '''return the first widget'''
        return self._first

    first = property(fget=_get_first, fset=_set_first)

    def _set_last(self, last):
        '''set the last element and add it to the widget (remove the 
        previous if not None'''

        if self._last_alig is not None:
            self.remove(self._last_alig)

        self._last = last
        self._last_alig = gtk.Alignment(xalign=0.5, yalign=1.0, xscale=1.0,
            yscale=0.1)
        self._last_alig.add(self._last)
        self.pack_start(self._last_alig)

    def _get_last(self):
        '''return the last widget'''
        return self._last

    last = property(fget=_get_last, fset=_set_last)

if __name__ == '__main__':
    import gui
    mconv = MainConversation(None) 
    conv = mconv.new_conversation()
    mconv.new_conversation()
    window = gtk.Window()
    window.add(mconv)
    window.set_default_size(640, 480)
    mconv.show_all()
    window.show()
    gtk.main()
