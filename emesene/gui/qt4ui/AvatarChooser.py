# -*- coding: utf-8 -*-

'''This module contains a class to select an avatar'''

import os

from PyQt4  import QtGui
from PyQt4  import QtCore

from gui.qt4ui import Dialog
from gui.qt4ui import widgets

class AvatarChooser(Dialog.OkCancelDialog):
    '''A dialog to choose an avatar'''
    NAME = 'Avatar Chooser'
    DESCRIPTION = 'A dialog to select the display picture'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''

    def __init__(self, response_cb, picture_path='', cache_path='.', 
                 contact_cache_path='.', faces_paths=[], 
                 avatar_manager=None, parent=None):
        '''Constructor, response_cb receive the response number, the new file
        selected and a list of the paths on the icon view.
        picture_path is the path of the current display picture,
        '''
        Dialog.OkCancelDialog.__init__(self, expanding=True, parent=parent)
        
        self._widget_dict = {}
        
        self._setup_ui()
        for path in faces_paths:
            self._populate_list(self._widget_dict['System pictures'], path)
            
        
    def _setup_ui(self):
        widget_dict = self._widget_dict
        
        widget_dict['tab_widget']       = QtGui.QTabWidget()
        widget_dict['group_box']        = QtGui.QGroupBox()
        widget_dict['preview_dpic']     = widgets.DisplayPic(clickable=False)
        widget_dict['add_btn']          = QtGui.QPushButton('Add...')
        widget_dict['remove_btn']       = QtGui.QPushButton('Remove')
        widget_dict['Used pictures']    = QtGui.QListView()
        widget_dict['System pictures']  = QtGui.QListView()
        widget_dict['Contact pictures'] = QtGui.QListView()
        
        
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
        for l_view in ['Used pictures', 'System pictures', 'Contact pictures']:
            widget_dict['tab_widget'].addTab(widget_dict[l_view], l_view)
            widget_dict[l_view].setViewMode    (QtGui.QListView.IconMode)
            widget_dict[l_view].setMovement    (QtGui.QListView.Static)
            widget_dict[l_view].setResizeMode  (QtGui.QListView.Adjust)
            widget_dict[l_view].setModel       (QtGui.QStandardItemModel())
            widget_dict[l_view].setItemDelegate(delegate)
        widget_dict['group_box'].setTitle('Preview')
        widget_dict['add_btn'].setIcon(QtGui.QIcon.fromTheme('list-add'))
        widget_dict['remove_btn'].setIcon(QtGui.QIcon.fromTheme('list-remove'))
        
       
    def _populate_list(self, listview, path):
        if not os.path.exists(path):
            return
        entries = os.listdir(path)
        for entry in entries:
            entry = os.path.join(path, entry)
            if not os.path.isfile(entry):
                continue
            if not QtGui.QImageReader(entry).canRead():
                continue
            pixmap = QtGui.QIcon(entry)
            item = QtGui.QStandardItem(entry)
            listview.model().appendRow(item)
            
        

        
