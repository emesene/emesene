import gtk

class EmptyWidget(gtk.VBox):
    '''a widget to be used as a placeholder for empty extensions'''

    def __init__(self, *args, **kwargs):
        gtk.VBox.__init__(self)
        self.set_border_width(0)
