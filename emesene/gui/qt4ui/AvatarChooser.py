# -*- coding: utf-8 -*-

'''This module contains a class to select an avatar'''

import os
import logging

from PyQt4  import QtGui
from PyQt4  import QtCore

from gui.qt4ui import Dialog
from gui.qt4ui import widgets
from gui.qt4ui.Utils import tr

import extension
import gui

log = logging.getLogger('qt4ui.AvatarChooser')

class AvatarChooser(Dialog.OkCancelDialog):
    '''A dialog to choose an avatar'''
    # differently from the Gtk one, this handles avatar 
    # manager /internally/ because, at the time of writing
    # AvatarManager is alredy available in gui.base
    NAME = 'Avatar Chooser'
    DESCRIPTION = 'A dialog to select the display picture'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''

    def __init__(self, session, parent=None):
        '''Constructor, response_cb receive the response number, the new file
        selected and a list of the paths on the icon view.
        picture_path is the path of the current display picture'''
        Dialog.OkCancelDialog.__init__(self, tr('Avatar chooser'), 
                                       expanding=True, parent=parent)
        self._session = session
        self._avatar_manager = gui.base.AvatarManager(session)
        # view names:
        self._vn = [ tr('Used pictures'   ), 
                     tr('System pictures' ), 
                     tr('Contact pictures')  ]
        self._view_with_selection = None
        self._current_avatar = session.config_dir.get_path('last_avatar')
        self._widget_d = {}
        
        self._setup_ui()
        # update buttons
        self._on_tab_changed(0)
        used_path = self._avatar_manager.get_avatars_dir()
        system_paths = self._avatar_manager.get_system_avatars_dirs()
        cached_paths = self._avatar_manager.get_cached_avatars_dir()
        
        self._populate_list(self._vn[0], used_path)
        for path in system_paths:
            self._populate_list(self._vn[1], path)
        for path in cached_paths:
            self._populate_list(self._vn[2], path)

    def _setup_ui(self):
        '''Builds up the UI'''
        widget_d = self._widget_d
        
        widget_d['tab_widget'] = QtGui.QTabWidget()
        widget_d['group_box'] = QtGui.QGroupBox()
        widget_d['preview_dpic'] = widgets.DisplayPic(self._session,
                                                             clickable=False, size=QtCore.QSize(96, 96))
        widget_d['add_btn'] = QtGui.QPushButton(tr('Add...'))
        widget_d['remove_btn'] = QtGui.QPushButton(tr('Remove'))
        widget_d['remove_all_btn'] = QtGui.QPushButton(tr('Remove All'))
        widget_d['no_picture_btn'] = QtGui.QPushButton(tr('No picture'))
        widget_d[self._vn[0]] = QtGui.QListView()
        widget_d[self._vn[1]] = QtGui.QListView()
        widget_d[self._vn[2]] = QtGui.QListView()

        group_box_lay = QtGui.QVBoxLayout()
        group_box_lay.addWidget(widget_d['preview_dpic'])
        widget_d['group_box'].setLayout(group_box_lay)
        right_lay = QtGui.QVBoxLayout()
        right_lay.addWidget(widget_d['group_box'])
        right_lay.addWidget(widget_d['add_btn'])
        right_lay.addWidget(widget_d['remove_btn'])
        right_lay.addWidget(widget_d['remove_all_btn'])
        right_lay.addWidget(widget_d['no_picture_btn'])
        right_lay.addStretch(20)
        lay = QtGui.QHBoxLayout()
        lay.addWidget(widget_d['tab_widget'])
        lay.addLayout(right_lay)
        self.setLayout(lay)
        self.resize(725, 430)
        
        delegate = widgets.IconViewDelegate()
        for view_name in self._vn:
            listview = widget_d[view_name]
            model = QtGui.QStandardItemModel(listview)
            selection_model = QtGui.QItemSelectionModel(model, listview)
            widget_d['tab_widget'].addTab(listview, view_name)
            listview.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
            listview.setViewMode(QtGui.QListView.IconMode)
            listview.setMovement(QtGui.QListView.Static)
            listview.setResizeMode(QtGui.QListView.Adjust)
            listview.setModel(model)
            listview.setSelectionModel(selection_model)
            listview.setItemDelegate(delegate)
        widget_d['tab_widget'].currentChanged.connect(self._on_tab_changed)
        widget_d['group_box'].setTitle(tr('Preview'))
        widget_d['preview_dpic'].set_display_pic_of_account()
        widget_d['add_btn'].setIcon(QtGui.QIcon.fromTheme('list-add'))
        widget_d['remove_btn'].setIcon(QtGui.QIcon.fromTheme('list-remove'))

        widget_d[self._vn[0]].selectionModel().currentChanged.   \
            connect(                                                       \
                lambda *args:                                              \
                    self._on_selection_changed(self._vn[0], *args))
        widget_d[self._vn[1]].selectionModel().currentChanged.   \
            connect(                                                       \
                lambda *args:                                              \
                    self._on_selection_changed(self._vn[1], *args))
        widget_d[self._vn[2]].selectionModel().currentChanged.   \
            connect(                                                       \
                lambda *args:                                              \
                    self._on_selection_changed(self._vn[2], *args))
        widget_d['add_btn'].clicked.connect(self._on_add_clicked)
        widget_d['remove_btn'].clicked.connect(self._on_remove_clicked)
        widget_d['remove_all_btn'].clicked.connect(self._on_remove_all)
        widget_d['no_picture_btn'].clicked.connect(self._on_clear)

    def _add_image_to_view(self, view_name, filename):
        '''Adds an image element in the view having the given view_name'''
        listview = self._widget_d[view_name] 
        item = QtGui.QStandardItem(filename)
        listview.model().appendRow(item)
        return item

    def _populate_list(self, view_name, path):
        '''Iteratively finds elements to be added to a view, and adds 
        them'''
        if not os.path.exists(path):
            return
        entries = os.listdir(path)
        for entry in entries:
            # filter out last avatar
            if entry == 'last':
                continue
            entry = os.path.join(path, entry)
            if not os.path.isfile(entry):
                continue
            if not QtGui.QImageReader(entry).canRead():
                continue
            self._add_image_to_view(view_name, entry)

    def _get_selection(self):
        '''Returns the selected item'''
        if not self._view_with_selection:
            return None
        listview = self._widget_d[self._view_with_selection]
        selection_idxs = listview.selectionModel().selection().indexes()
        if len(selection_idxs) == 0:
            return None
        filename = listview.model().data(selection_idxs[0]).toString()
        return unicode(filename)

    def _on_clear(self, button):
        '''clear user avatar'''
        self._avatar_manager.set_as_avatar('')
        self._widget_d['preview_dpic'].set_display_pic_from_file('')

    def _on_remove_all(self, button):
        '''Removes all avatars from the cache'''
        def on_response_cb(response):
            '''response callback for the confirm dialog'''
            if response == gui.stock.YES:
                self.remove_all()

        extension.get_default('dialog').yes_no(
            _("Are you sure you want to remove all items?"),
            on_response_cb)

    def _on_remove_clicked(self):
        '''remove current selected avatar'''
        if not self._view_with_selection:
            return None
        listview = self._widget_d[self._view_with_selection]
        selected_index = listview.selectionModel().selection().indexes()[0]
        row = selected_index.row()
        path = unicode(listview.model().data(selected_index).toString())
        listview.model().removeRows(row, 1)
        self._avatar_manager.remove_avatar(path)

    def remove_all(self):
        '''remove all avatars from curent tab'''
        tab_index = self._widget_d['tab_widget'].currentIndex()
        listview = self._widget_d[self._vn[tab_index]]
        for index in range(0,listview.model().rowCount()):
            selected_index = listview.model().index(index, 0)
            path = unicode(listview.model().data(selected_index).toString())
            self._avatar_manager.remove_avatar(path)
            row = selected_index.row()
            listview.model().removeRows(row, 1)

    def _on_add_clicked(self):
        '''This slot is executed when the user clicks the 'Add' button.
        It shows up a file chooser, than if the image can be manipulate through
        toolkit function (Test is performed through PictureHandler) shows an
        image area selector. Then, the image in added to the cache (through 
        AvatarManager object, and to the views'''
        def add_and_select(filename):
            '''Adds the image with he given filename to the first view and 
            selects it'''
            # append the image to the first tab:
            item = self._add_image_to_view(self._vn[0], filename)
            # show first tab:
            self._widget_d['tab_widget'].setCurrentIndex(0)
            # select the new appended image:
            self._widget_d[self._vn[0]].selectionModel().\
                        select(item.index(), QtGui.QItemSelectionModel.Select)

        def response_cb(response, pixmap):
            '''Callback invoked when the crop_image dialog is closed.
            If the user clicks ok calls adds the picture to the cache
            and calls add_and_select.'''
            if response == gui.stock.ACCEPT:
                filename = self._avatar_manager.\
                        add_new_avatar_from_toolkit_pix(pixmap)
                add_and_select(filename)
        
        filename = QtGui.QFileDialog.getOpenFileName(
                                         self, tr('Select an image'), 
                                         QtCore.QString(),
                                         'Images (*.jpeg *.jpg *.png *.gif')
        if filename.isEmpty():
            return
        filename = unicode(filename)
        pic_handler = extension.get_and_instantiate('picture handler', filename)
        # substitute the filename with the name of the cached one:
        if pic_handler.can_handle():
            Dialog.Dialog.crop_image(response_cb, filename)
        else:
            filename = self._avatar_manager.add_new_avatar(filename)
            add_and_select(filename)

    def _on_selection_changed(self, view_name, current_idx, previous_idx):
        '''This slot is called when the selected image in a view changes.
        Currently it doesn't anything useful nor interesting :P'''
        if current_idx.isValid():
            self._view_with_selection = view_name
            listview = self._widget_d[self._view_with_selection]
            filename = unicode(listview.model().data(current_idx).toString())
            self._widget_d['preview_dpic'].set_display_pic_from_file(filename)

    def _on_tab_changed(self, index):
        if index == 0:
            self._widget_d['add_btn'].setEnabled(True)
            self._widget_d['remove_btn'].setEnabled(True)
            self._widget_d['remove_all_btn'].setEnabled(True)
        elif index == 1:
            self._widget_d['add_btn'].setEnabled(False)
            self._widget_d['remove_btn'].setEnabled(False)
            self._widget_d['remove_all_btn'].setEnabled(False)
        elif index == 2:
            self._widget_d['add_btn'].setEnabled(False)
            self._widget_d['remove_btn'].setEnabled(True)
            self._widget_d['remove_all_btn'].setEnabled(True)

    # OVERRIDE
    def _on_accept(self):
        '''This method overrides OkCancelDialog class' _on_accept.
        If the user clicks 'Ok', set the selected image (if any)
        as the user's avatar'''
        filename = self._get_selection()
        if filename:
            if os.path.exists(filename):
                self._avatar_manager.set_as_avatar(filename)
        Dialog.OkCancelDialog._on_accept(self)
