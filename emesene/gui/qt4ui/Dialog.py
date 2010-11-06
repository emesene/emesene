# -*- coding: utf-8 -*-

'''a module that defines the api of objects that display dialogs'''


from PyQt4  import QtGui
from PyQt4.QtCore  import Qt

import gui

from gui.qt4ui import widgets



class Dialog(object):
    '''a class full of static methods to handle dialogs, dont instantiate it'''
    NAME = 'Dialog'
    DESCRIPTION = 'Class to show all the dialogs of the application'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''


#    @classmethod
#    def new_window(cls, title, response_cb=None, *args):
#        '''build a window with the default values and connect the common
#        signals, return the window'''
#
#        window = QtGui.QDialog()
#        window.set_title(title)
#        window.set_role("dialog")
#        window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
#        window.set_default_size(150, 100)
#        window.set_position(gtk.WIN_POS_CENTER)
#        window.set_border_width(8)
#        window.set_icon(utils.safe_gtk_image_load(gui.theme.logo).get_pixbuf())
#
#        vbox = gtk.VBox(spacing=4)
#        hbox = gtk.HBox(spacing=4)
#        bbox = gtk.HButtonBox()
#        bbox.set_spacing(4)
#        bbox.set_layout(gtk.BUTTONBOX_END)
#
#        vbox.pack_start(hbox, True, True)
#        vbox.pack_start(bbox, False)
#
#        window.add(vbox)
#
#        setattr(window, 'vbox', vbox)
#        setattr(window, 'hbox', hbox)
#        setattr(window, 'bbox', bbox)
#
#        args = list(args)
#        args.insert(0, stock.CLOSE)
#        window.connect('delete-event', cls.close_cb, window,
#            response_cb, *args)
#
#        vbox.show_all()
#
#        return window

    @classmethod
    def add_contact(cls, groups, group_selected, response_cb,
        title="Add user"):
        '''show a dialog asking for an user address, and (optional)
        the group(s) where the user should be added, the response callback
        receives the response type (stock.ADD, stock.CANCEL or stock.CLOSE)
        the account and a tuple of group names where the user should be
        added (give a empty tuple if you don't implement this feature,
        the controls are made by the callback, you just ask for the email,
        don't make any control, you are just implementing a GUI! :P'''
        print response_cb
        dialog      = OkCancelDialog()
        text_label  = QtGui.QLabel("E-mail:")
        text_edit   = QtGui.QLineEdit()
        group_label = QtGui.QLabel("Group:")
        group_combo = QtGui.QComboBox()
        
        lay = QtGui.QGridLayout()
        lay.addWidget(text_label,   0, 0)
        lay.addWidget(text_edit,    0, 1)
        lay.addWidget(group_label,  1, 0)
        lay.addWidget(group_combo,  1, 1)
        dialog.setLayout(lay)
        
        
        dialog.setWindowTitle(title)
        text_label.setAlignment(Qt.AlignRight |
                                Qt.AlignVCenter)
        group_label.setAlignment(Qt.AlignRight |
                                 Qt.AlignVCenter)
        dialog.setMinimumWidth(300)
        
        print groups
        groups = list(groups)
        print groups
        groups.sort()
        
        group_combo.addItem('<i>No Group</i>', '')
        for group in groups:
            group_combo.addItem(group.name, group.name)
        
        response = dialog.exec_()
        
        if response == QtGui.QDialog.Accepted:
            response = gui.stock.ACCEPT
        elif response == QtGui.QDialog.Rejected:
            response = gui.stock.CANCEL
        print response
        
        email = unicode(text_edit.text())
        group = group_combo.itemData(group_combo.currentIndex()).toPyObject()
        print '[%s,%s]' % (email, group)
        response_cb(response, email, group )
        
        
    @classmethod
    def add_group(cls, response_cb, title="Add group"):
        '''show a dialog asking for a group name, the response callback
        receives the response (stock.ADD, stock.CANCEL, stock.CLOSE)
        and the name of the group, the control for a valid group is made
        on the controller, so if the group is empty you just call the
        callback, to make a unified behaviour, and also, to only implement
        GUI logic on your code and not client logic
        cb args: response, group_name'''
        print response_cb
        dialog = OkCancelDialog()
        group_label = QtGui.QLabel('New group\'s name:')
        group_edit  = QtGui.QLineEdit()
        
        lay = QtGui.QHBoxLayout()
        lay.addWidget(group_label)
        lay.addWidget(group_edit)
        dialog.setLayout(lay)
        
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(380)
        
        response = dialog.exec_()
        
        if response == QtGui.QDialog.Accepted:
            response = gui.stock.ACCEPT
        elif response == QtGui.QDialog.Rejected:
            response = gui.stock.CANCEL
        print response
        
        group_name = unicode(group_edit.text())
        
        response_cb(response, group_name)
        
    @classmethod
    def crop_image(cls, response_cb, filename, title='Select image area'):
        dialog = OkCancelDialog(expanding=True)
        
        # Actions
        act_dict = {}
        act_dict['rotate_left' ] = QtGui.QAction('Rotate Left'    , dialog)
        act_dict['rotate_right'] = QtGui.QAction('Rotate right'   , dialog)
        act_dict['fit_zoom']     = QtGui.QAction('Zoom to fit'    , dialog)
        act_dict['fit_zoom']     = QtGui.QAction('Zoom to fit'    , dialog)
        act_dict['reset_zoom']   = QtGui.QAction('Reset zoom'     , dialog)
        act_dict['select_all']   = QtGui.QAction('Select All'     , dialog)
        act_dict['select_unsc']  = QtGui.QAction('Select Unscaled', dialog)
        
        # widgets
        toolbar = QtGui.QToolBar()
        scroll_area = QtGui.QScrollArea()
        area_selector = widgets.ImageAreaSelector(QtGui.QPixmap(filename))
        
        # layout
        lay = QtGui.QVBoxLayout()
        lay.addWidget(toolbar)
        lay.addWidget(scroll_area)
        dialog.setLayout(lay)
        
        # widget setup
        toolbar.addAction(act_dict['rotate_left'])
        toolbar.addAction(act_dict['rotate_right'])
        toolbar.addSeparator()
        toolbar.addAction(act_dict['fit_zoom'])
        toolbar.addAction(act_dict['reset_zoom'])
        toolbar.addSeparator()
        toolbar.addAction(act_dict['select_all'])
        toolbar.addAction(act_dict['select_unsc'])
        scroll_area.setWidget(area_selector)
        scroll_area.setWidgetResizable(True)
        
        # Signal connection:
        act_dict['rotate_left'].triggered.connect(area_selector.rotate_left)
        act_dict['rotate_right'].triggered.connect(area_selector.rotate_right)
        act_dict['fit_zoom'].triggered.connect(area_selector.fit_zoom)
        act_dict['reset_zoom'].triggered.connect(
                                            lambda: area_selector.set_zoom(1))
        act_dict['select_all'].triggered.connect(area_selector.select_all)
        act_dict['select_unsc'].triggered.connect(
                                            area_selector.select_unscaled)
                                            
        # test:
        if (False):
            preview = QtGui.QLabel()
            lay.addWidget(preview)
            area_selector.selectionChanged.connect(
                lambda: preview.setPixmap(area_selector.get_selected_pixmap()))
            
            zoom_sli = QtGui.QSlider(Qt.Horizontal)
            zoom_sli.setMinimum(1)
            zoom_sli.setMaximum(40)
            zoom_sli.setValue(20)
            zoom_sli.setSingleStep(1)
            lay.addWidget(zoom_sli)
            zoom_sli.valueChanged.connect(
                lambda z:area_selector.set_zoom(z/10.0))
                                            
        # Dialog execution:
        response = dialog.exec_()
        
        if response == QtGui.QDialog.Accepted:
            response = gui.stock.ACCEPT
        elif response == QtGui.QDialog.Rejected:
            response = gui.stock.CANCEL
        print response
        
        selected_pixmap = area_selector.get_selected_pixmap()
        
        response_cb(response, selected_pixmap)
        




class OkCancelDialog (QtGui.QDialog):
    '''Skeleton for a dialog window having Ok and Cancel buttons'''
    def __init__(self, expanding=False, parent=None):
        '''Constructor'''

        QtGui.QDialog.__init__(self, parent)

        self.central_widget = QtGui.QWidget()
        button_box  = QtGui.QDialogButtonBox()

        vlay = QtGui.QVBoxLayout()
        vlay.addWidget(self.central_widget)
        vlay.addSpacing(10)
        vlay.addWidget(button_box)
        if not expanding:
            vlay.addStretch()
        QtGui.QDialog.setLayout(self, vlay)

        button_box.addButton(QtGui.QDialogButtonBox.Cancel)
        button_box.addButton(QtGui.QDialogButtonBox.Ok)

        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self._on_reject)
        
    def _on_accept(self):
        '''Slot called when Ok is clicked'''
        self.done(QtGui.QDialog.Accepted)
        
    def _on_reject(self):
        '''Slot called when Cancel is clicked'''
        self.done(QtGui.QDialog.Rejected)
        
# -------------------- QT_OVERRIDE
        
    def setLayout(self, layout):
        '''Overrides setLayout. Sets the layout directly on
        this dialog's central widget.'''
        # pylint: disable=C0103
        self.central_widget.setLayout(layout)
        
