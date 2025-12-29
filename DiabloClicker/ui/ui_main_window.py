# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QMainWindow, QMenuBar,
    QSizePolicy, QSpacerItem, QStatusBar, QTabWidget,
    QToolButton, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1083, 671)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setStyleSheet(u"")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(1, 1, 1, 1)
        self.widget_frame_top = QWidget(self.centralwidget)
        self.widget_frame_top.setObjectName(u"widget_frame_top")
        self.widget_frame_top.setMinimumSize(QSize(0, 40))
        self.widget_frame_top.setMaximumSize(QSize(16777215, 40))
        self.widget_frame_top.setStyleSheet(u"border: 1px solid gray;")

        self.verticalLayout.addWidget(self.widget_frame_top)

        self.widget_2 = QWidget(self.centralwidget)
        self.widget_2.setObjectName(u"widget_2")
        self.horizontalLayout = QHBoxLayout(self.widget_2)
        self.horizontalLayout.setSpacing(2)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.widget_frame_left = QWidget(self.widget_2)
        self.widget_frame_left.setObjectName(u"widget_frame_left")
        self.widget_frame_left.setMinimumSize(QSize(80, 0))
        self.widget_frame_left.setMaximumSize(QSize(80, 16777215))
        self.widget_frame_left.setStyleSheet(u"border: 1px solid gray;")
        self.verticalLayout_2 = QVBoxLayout(self.widget_frame_left)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.btn_timed_key = QToolButton(self.widget_frame_left)
        self.btn_timed_key.setObjectName(u"btn_timed_key")
        self.btn_timed_key.setMinimumSize(QSize(60, 60))

        self.verticalLayout_2.addWidget(self.btn_timed_key)

        self.btn_smart_key = QToolButton(self.widget_frame_left)
        self.btn_smart_key.setObjectName(u"btn_smart_key")
        self.btn_smart_key.setMinimumSize(QSize(60, 60))

        self.verticalLayout_2.addWidget(self.btn_smart_key)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)


        self.horizontalLayout.addWidget(self.widget_frame_left)

        self.widget_frame_right = QWidget(self.widget_2)
        self.widget_frame_right.setObjectName(u"widget_frame_right")
        self.widget_frame_right.setStyleSheet(u"border: 1px solid gray;")
        self.verticalLayout_3 = QVBoxLayout(self.widget_frame_right)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.tabWidget = QTabWidget(self.widget_frame_right)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setTabsClosable(True)
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.tabWidget.addTab(self.tab_2, "")

        self.verticalLayout_3.addWidget(self.tabWidget)


        self.horizontalLayout.addWidget(self.widget_frame_right)


        self.verticalLayout.addWidget(self.widget_2)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1083, 22))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.btn_timed_key.setText(QCoreApplication.translate("MainWindow", u"\u5b9a\u65f6\n"
"\u6309\u952e", None))
        self.btn_smart_key.setText(QCoreApplication.translate("MainWindow", u"\u667a\u80fd\n"
"\u6309\u952e", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", u"Tab 1", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", u"Tab 2", None))
    # retranslateUi

