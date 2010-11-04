# -*- coding: utf-8 -*-

'''This module contains a class to select an avatar'''

import os

from PyQt4  import QtGui
from PyQt4  import QtCore

import extension
import gui
from gui.qt4ui import Dialog
from gui.qt4ui import widgets

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
        Dialog.OkCancelDialog.__init__(self, expanding=True, parent=parent)
        
        self._session = session
        self._avatar_manager = gui.base.AvatarManager(session)
        # view names:
        self._vn = ['Used pictures', 'System pictures', 'Contact pictures']
        self._view_with_selection = None
        self._current_avatar = session.config_dir.get_path("last_avatar")
        self._widget_dict = {}
        
        self._setup_ui()
        used_path    = self._avatar_manager.get_avatars_dir()
        system_paths = self._avatar_manager.get_system_avatars_dirs()
        cached_path  = self._avatar_manager.get_cached_avatars_dir()
        
        self._populate_list(self._vn[0], used_path)
        for path in system_paths:
            self._populate_list(self._vn[1], path)
        self._populate_list(self._vn[2], cached_path)
        
            
        
    def _setup_ui(self):
        widget_dict = self._widget_dict
        
        widget_dict['tab_widget']   = QtGui.QTabWidget()
        widget_dict['group_box']    = QtGui.QGroupBox()
        widget_dict['preview_dpic'] = widgets.DisplayPic(self._session,
                                                             clickable=False)
        widget_dict['add_btn']      = QtGui.QPushButton('Add...')
        widget_dict['remove_btn']   = QtGui.QPushButton('Remove')
        widget_dict[self._vn[0]]    = QtGui.QListView()
        widget_dict[self._vn[1]]    = QtGui.QListView()
        widget_dict[self._vn[2]]    = QtGui.QListView()
        
        
        group_box_lay = QtGui.QVBoxLayout()
        group_box_lay.addWidget(widget_dict['preview_dpic'])
        widget_dict['group_box'].setLayout(group_box_lay)
        right_lay = QtGui.QVBoxLayout()
        right_lay.addWidget(widget_dict['group_box'])
        right_lay.addSpacing(50)
        right_lay.addWidget(widget_dict['add_btn'])
        right_lay.addWidget(widget_dict['remove_btn'])
        right_lay.addStretch(20)
        lay = QtGui.QHBoxLayout()
        lay.addWidget(widget_dict['tab_widget'])
        lay.addLayout(right_lay)
        self.setLayout(lay)
        self.resize(725, 430)
        
        delegate = widgets.IconViewDelegate()
        for view_name in self._vn:
            listview = widget_dict[view_name]
            model = QtGui.QStandardItemModel(listview)
            selection_model = QtGui.QItemSelectionModel(model, listview)
            widget_dict['tab_widget'].addTab(listview, view_name)
            listview.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
            listview.setViewMode      (QtGui.QListView.IconMode)
            listview.setMovement      (QtGui.QListView.Static)
            listview.setResizeMode    (QtGui.QListView.Adjust)
            listview.setModel         (model)
            listview.setSelectionModel(selection_model)
            listview.setItemDelegate  (delegate)
        widget_dict['group_box'].setTitle('Preview')
        widget_dict['preview_dpic'].set_display_pic_of_account()
        widget_dict['add_btn'].setIcon(QtGui.QIcon.fromTheme('list-add'))
        widget_dict['remove_btn'].setIcon(QtGui.QIcon.fromTheme('list-remove'))
        
        
        widget_dict[self._vn[0]].selectionModel().currentChanged.   \
            connect(                                                       \
                lambda *args:                                              \
                    self._on_selection_changed(self._vn[0], *args))
        widget_dict[self._vn[1]].selectionModel().currentChanged.   \
            connect(                                                       \
                lambda *args:                                              \
                    self._on_selection_changed(self._vn[1], *args))
        widget_dict[self._vn[2]].selectionModel().currentChanged.   \
            connect(                                                       \
                lambda *args:                                              \
                    self._on_selection_changed(self._vn[2], *args))
        widget_dict['add_btn'].clicked.connect(self._on_add_clicked)
        
    
    
    def _add_image_to_view(self, view_name, filename):
        listview = self._widget_dict[view_name] 
        item = QtGui.QStandardItem(filename)
        listview.model().appendRow(item)
        return item
    
    
    def _populate_list(self, view_name, path):
        #print 'PATH: %s' % path
        if not os.path.exists(path):
            return
        entries = os.listdir(path)
        for entry in entries:
            entry = os.path.join(path, entry)
            if not os.path.isfile(entry):
                continue
            if not QtGui.QImageReader(entry).canRead():
                continue
            self._add_image_to_view(view_name, entry)
            
            
    def _get_selection(self):
        if not self._view_with_selection:
            return None
        listview = self._widget_dict[self._view_with_selection]
        selection_idxs = listview.selectionModel().selection().indexes()
        filename = listview.model().data(selection_idxs[0]).toString()
        return unicode(filename)
            
            
    def _on_add_clicked(self):
        filename = QtGui.QFileDialog.getOpenFileName(
                                         self, 'Select an image', 
                                         QtCore.QString(),
                                         'Images (*.jpeg *.jpg *.png *.gif')
        if filename.isEmpty():
            return
        filename = unicode(filename)
        pic_handler = extension.get_and_instantiate('picture handler', filename)
        # substitute the filename with the name of the cached one:
        if pic_handler.is_animated():
            filename = self._avatar_manager.add_new_avatar(filename)
        else:
            filename = self._avatar_manager.add_new_avatar(filename) #:)
        # append the image to the first tab:
        item = self._add_image_to_view(self._vn[0], filename)
        # show first tab:
        self._widget_dict['tab_widget'].setCurrentIndex(0)
        # select the new appended image:
        self._widget_dict[self._vn[0]].selectionModel().\
                        select(item.index(), QtGui.QItemSelectionModel.Select)
    
    
    def _on_selection_changed(self, view_name, current_idx, previous_idx):
        if current_idx.isValid():
            self._view_with_selection = view_name
            print 'Valid: [%d:%d]' % (previous_idx.row(), current_idx.row()),
        else:
            print 'Invalid',
        print '\t%s' % view_name
        
    
    # OVERRIDE
    def _on_accept(self):
        filename = self._get_selection()
        if filename:
            print 'fn[%s]' % filename
            import os
            if os.path.exists(filename):
                #self._avatar_manager.set_as_avatar(filename)
                pass
            else:
                print "Error"
        Dialog.OkCancelDialog._on_accept(self)
        

        
