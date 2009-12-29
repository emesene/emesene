'''A module to handle a debug console'''
import time

import gtk
import pango

import debugger
import logging

class DebugWindow():
    '''The window containing the debug info'''
    def __init__(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title("debug")
        self.window.connect("delete_event", self.on_delete)
        self.store = DebugStore()
        self.view = DebugView(self.store)
        
        logging.getLogger().addHandler(self.store)
        
        self.scroll_view = gtk.ScrolledWindow()
        self.scroll_view.add(self.view)

        
        self.vbox = gtk.VBox()
        self.filter_box = gtk.HBox()
        self.buttons_box = gtk.HBox()
        self.test_box = gtk.HBox()

        self.filter_entry = gtk.Entry()
        self.filter_level = gtk.combo_box_new_text()
        self.filter_level.append_text("Debug")
        self.filter_level.append_text("Info")
        self.filter_level.append_text("Warning")
        self.filter_level.append_text("Error")
        self.filter_level.append_text("Critical")
        self.filter_level.set_active(0)
        self.filter_btn = gtk.Button("Filter")
        self.filter_box.pack_start(self.filter_entry)
        self.filter_box.pack_start(self.filter_level, False)
        self.filter_box.pack_start(self.filter_btn, False)
        self.vbox.pack_start(self.filter_box, False)

        self.vbox.pack_start(self.scroll_view)

        self.close_btn = gtk.Button("Close")
        self.buttons_box.pack_end(self.close_btn, False)
        self.vbox.pack_start(self.buttons_box, False)
        
        self.window.add(self.vbox)

        self.filter_btn.connect("clicked", self.on_filter_clicked)
        self.filter_entry.connect("activate", self.on_filter_clicked)
        self.filter_level.connect("changed", self.on_filter_clicked)
        self.close_btn.connect("clicked", self.on_close)

        self.window.set_default_size(*self.view.size_request())

    def show( self ):
        '''shows the window'''
        self.window.show_all()

    def on_filter_clicked(self, widget, data=None):
        '''used when the filter button is clicked'''
        pattern = self.filter_entry.get_text()
        level = self.filter_level.get_active_text()
        d = {'Debug':logging.DEBUG, 'Info': logging.INFO, 'Warning': logging.WARNING,
                'Error':logging.ERROR, 'Critical':logging.CRITICAL}
        levelno = d[level]
        self.view.filter_caller(pattern, levelno)

    def safely_close(self):
        self.window.hide()
        logging.getLogger().removeHandler(self.store)
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

    def filter_caller(self, pattern, level):
        self.store.filter_caller(pattern, level)
        self.buffer = DebugBuffer(self.store.custom_filter)
        self.set_buffer(self.buffer)

class DebugBuffer( gtk.TextBuffer ):
    '''A TextBuffer based on a ListStore'''
    def __init__(self, store):
        gtk.TextBuffer.__init__(self)
        self.store = store

        self.create_tag("caller", weight=pango.WEIGHT_BOLD)
        self.create_tag("message")
        self.create_tag("level", invisible=True) #if we find a good style it could be useful
        self.create_tag("time", scale=pango.SCALE_SMALL, weight=pango.WEIGHT_LIGHT)

        self.iter = self.get_start_iter()
        for row in store:
            self.add_line(row[0], row[1], row[2], row[3])

        store.connect("row-changed", self.on_store_insert)

    def on_store_insert(self, model, path, iter):
        caller = model.get_value(iter, 0)
        message =  model.get_value(iter, 1)
        level =  model.get_value(iter, 2)
        date = model.get_value(iter, 3)
        self.add_line(caller, message, level, date)

    def add_line(self, caller, message, level, date):
        if caller and message and level and date:
            record_date = time.localtime(float(date))
            record_time = time.strftime("%H:%M:%S", record_date)
            self.insert_with_tags_by_name(self.iter, "(%s) " % record_time, "time")
            self.insert_with_tags_by_name(self.iter, "%s " % level, "level")
            self.insert_with_tags_by_name(self.iter, caller + ":" , "caller")
            self.insert_with_tags_by_name(self.iter, message + '\n', "message")

class DebugStore( gtk.ListStore, logging.Handler ):
    '''A ListStore with filtering and more, optimized for debug'''
    def __init__( self):
        '''constructor'''
        gtk.ListStore.__init__(self, str, str, int, str) #caller, message, level, time
        logging.Handler.__init__(self)
        self.custom_filter = self.filter_new()
        
        queue_handler = debugger.QueueHandler.get()
        for message in queue_handler.get_all():
            self.on_message_added(message)
        #for message in _logger.get_all():
        #    self.on_message_added(message)
        #_logger.connect('message-added', self.on_message_added)

    def emit(self, record):
        self.on_message_added(record)
    
    def on_message_added(self, message):
        self.append([message.caller, message.msg.strip(), message.levelno, message.created])

    def filter_caller( self, name, level ):
        '''
        displays only the messages whose caller matches "name"
        and level is AT LEAST level.
        '''
        del self.custom_filter
        self.custom_filter = self.filter_new()
        self.custom_filter.set_visible_func(filter_func, (name, level))
    
def filter_func(model, iter, (name, required_level)):
    '''returns true if the caller column matches name
    AND level is at least required_level'''
    level = model.get_value(iter, 2)
    if level < required_level:
        return False
    caller = model.get_value(iter, 0)
    if not caller:
        return False
    if caller.find(name) == -1:
        return False
    return True

