import gtk

class EmptyWidget(gtk.VBox):
    '''a widget to be used as a placeholder for empty extensions'''
    NAME = 'Empty Widget'
    DESCRIPTION = 'Empty placeholder'
    AUTHOR = 'Mariano Guerra'
    WEBSITE = 'www.emesene.org'

    def __init__(self, *args, **kwargs):
        gtk.VBox.__init__(self)
        self.set_border_width(0)
