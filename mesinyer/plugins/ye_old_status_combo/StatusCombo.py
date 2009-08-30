import gtk

class StatusCombo(gtk.ComboBox):
    """a widget to select the status like the one in emesene 1.0"""

    def __init__(self, main_window):
        """constructor"""
        gtk.ComboBox.__init__(self)
        # TODO: get extension of userpanel and try to hide the status button
