# -*- coding: utf-8 -*-

'''Test module for ChatTextEdit widget'''

import sys

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import gui
import e3
import gui.qt4ui.widgets


class Test (QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)

        tabbar = QTabBar()
        self.te1 = gui.qt4ui.widgets.ChatInput()
        self.te1.set_smiley_dict(gui.theme.EMOTES)
        self.te2 = QTextEdit()
        self.te2.setReadOnly(True)
        self.te3 = QTextEdit()
        self.te3.setReadOnly(True)
        self.lab = QLabel()
        self.font = QPushButton("font")
        self.color = QPushButton("color")
        lay = QVBoxLayout()
        lay.addWidget(tabbar)
        lay.addWidget(self.te1)
        lay.addWidget(self.te2)
        lay.addWidget(self.te3)
        lay.addWidget(self.lab)
        lay.addWidget(self.font)
        lay.addWidget(self.color)

        centralWidget = QWidget()
        centralWidget.setLayout(lay)
        self.setCentralWidget(centralWidget)

        tabbar.setTabsClosable(True)
        tabbar.addTab(QIcon(gui.theme.status_icons[e3.status.ONLINE]), '')
        lay2=QVBoxLayout()
        #lay2.addWidget(self.te1)
        tabbar.setLayout(lay2)
        #tabbar.setTabButton(0, QTabBar.RightSide, QLabel("BUGA"))
        self.te1.textChanged.connect(self.on_text_changed)
        self.te1.return_pressed.connect(self.on_return_pressed)
        self.font.clicked.connect(self.te1.show_font_chooser)
        self.color.clicked.connect(self.te1.show_color_chooser)
        
        
        label1 = QLabel('Ciao<img src="/home/fastfading/src/emesene/emesene/themes/emotes/default/face-smile.png" />')
        label2 = QLabel('<table><tr><td valign="middle">Ciao</td><td valign="middle"><img src="/home/fastfading/src/emesene/emesene/themes/emotes/default/face-smile.png" /></td></tr></table>')
        lay.addWidget(label1)
        lay.addWidget(label2)

    def on_text_changed(self):
        html = self.te1.toHtml()
        plain = self.te1.toPlainText()
        self.te2.setPlainText("["+html+"]")
        self.te3.setPlainText("["+plain+"]")

    def on_return_pressed(self):
        self.lab.setText(self.te1.toPlainText())




if __name__ == "__main__":
    def test_stuff():
        reload (sys)
        sys.setdefaultencoding("utf-8")

    test_stuff()
    qapp = QApplication(sys.argv)
    window = Test()
    window.show()
    qapp.exec_()
    

