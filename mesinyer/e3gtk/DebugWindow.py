'''A module to handle a debug console'''
import gtk
import pango

from debugger import warning,debug
from debugger import _logger
from debugger import idle_handler
import logging

class DebugWindow():
    '''The window containing the debug info'''
    def __init__(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title("debug")
        self.window.connect("delete_event", self.on_delete)
        self.store = DebugStore()
        self.view = DebugView(self.store)
        _logger.addHandler(self.store)
        self.scroll_view = gtk.ScrolledWindow()
        self.scroll_view.add(self.view)

        
        self.vbox = gtk.VBox()
        self.filter_box = gtk.HBox()
        self.buttons_box = gtk.HBox()
        self.test_box = gtk.HBox()

        self.filter_entry = gtk.Entry()
        self.filter_btn = gtk.Button("Filter")
        self.filter_box.pack_start(self.filter_entry)
        self.filter_box.pack_start(self.filter_btn, False)
        self.vbox.pack_start(self.filter_box, False)

        self.vbox.pack_start(self.scroll_view)

        self.close_btn = gtk.Button("Close")
        self.buttons_box.pack_end(self.close_btn, False)
        self.vbox.pack_start(self.buttons_box, False)
        
        self.window.add(self.vbox)

        self.filter_btn.connect("clicked", self.on_filter_clicked)
        self.filter_entry.connect("activate", self.on_filter_clicked)
        self.close_btn.connect("clicked", self.on_close)

        print self.view.size_request()
        self.window.set_default_size(*self.view.size_request())

    def show( self ):
        '''shows the window'''
        self.window.show_all()

    def on_filter_clicked(self, button, data=None):
        '''used when the filter button is clicked'''
        pattern = self.filter_entry.get_text()
        self.view.filter_caller(pattern)

    def safely_close(self):
        self.window.hide()
        _logger.removeHandler(self.store)
    def on_add(self, button, data=None):
        caller = self.test_entry.get_text()
        #self.store.append([caller, "just a test"])
        self.store.add({'category':caller, 'message':'just a test'})

    def on_close(self, button, data=None):
        self.safely_close()
        return False

    def on_delete(self, widget, event, data=None):
        self.safely_close()
        return False

class DebugView( gtk.TextView ):
    '''A TextView optimized for debug consoles'''
    def __init__(self, store):
        gtk.TextView.__init__(self)
        self.store = store
        self.buffer = DebugBuffer(store)
        self.set_buffer(self.buffer)

        self.set_editable(False)

    def filter_caller(self, pattern):
        self.store.filter_caller(pattern)
        self.buffer = DebugBuffer(self.store.custom_filter)
        self.set_buffer(self.buffer)

class DebugBuffer( gtk.TextBuffer ):
    '''A TextBuffer based on a ListStore'''
    def __init__(self, store):
        gtk.TextBuffer.__init__(self)
        self.store = store

        self.create_tag("caller", weight=pango.WEIGHT_BOLD)
        self.create_tag("message")

        self.iter = self.get_start_iter()
        for row in store:
            self.insert_with_tags_by_name(self.iter, row[0], "caller")
            self.insert_with_tags_by_name(self.iter, ": " + row[1], "message")
            self.insert(self.iter, '\n')

        store.connect("row-changed", self.on_store_insert)


    def on_store_insert(self, model, path, iter):
        caller = model.get_value(iter, 0)
        message =  model.get_value(iter, 1)
        level =  model.get_value(iter, 2)
        if caller and message and level:
            self.insert_with_tags_by_name(self.iter, caller, "caller")
            self.insert_with_tags_by_name(self.iter, ": " + message + '\n', "message")

class DebugStore( gtk.ListStore, logging.Handler ):
    '''A ListStore with filtering and more, optimized for debug'''
    def __init__( self):
        '''constructor'''
        gtk.ListStore.__init__(self, str, str, int) #caller, message
        logging.Handler.__init__(self)
        self.custom_filter = self.filter_new()
        
        for message in idle_handler.get_all():
            self.on_message_added(message)
        #for message in _logger.get_all():
        #    self.on_message_added(message)
        #_logger.connect('message-added', self.on_message_added)

    def emit(self, record):
        self.on_message_added(record)
    
    def on_message_added(self, message):
        self.append([message.caller, message.msg.strip(), message.levelno])

    def filter_caller( self, name ):
        '''displays only the messages whose caller matches "name"'''
        del self.custom_filter
        self.custom_filter = self.filter_new()
        self.custom_filter.set_visible_func(filter_func, name)
    
def filter_func(model, iter, name):
    '''returns true if the caller column matches name'''
    caller = model.get_value(iter, 0)
    if not caller:
        return False
    if caller.find(name) == -1:
        return False
    return True

