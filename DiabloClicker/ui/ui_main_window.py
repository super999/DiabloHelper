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
from PySide6.QtWidgets import (QApplication, QCheckBox, QHBoxLayout, QLabel,
    QListView, QMainWindow, QMenuBar, QPushButton,
    QSizePolicy, QSpacerItem, QStatusBar, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1083, 692)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setStyleSheet(u"")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(1, 1, 1, 1)
        self.widget_L01 = QWidget(self.centralwidget)
        self.widget_L01.setObjectName(u"widget_L01")
        self.widget_L01.setMinimumSize(QSize(0, 70))
        self.widget_L01.setMaximumSize(QSize(16777215, 70))
        self.widget_L01.setStyleSheet(u"")
        self.pushButton_screenshot = QPushButton(self.widget_L01)
        self.pushButton_screenshot.setObjectName(u"pushButton_screenshot")
        self.pushButton_screenshot.setGeometry(QRect(10, 5, 71, 61))
        self.pushButton_test = QPushButton(self.widget_L01)
        self.pushButton_test.setObjectName(u"pushButton_test")
        self.pushButton_test.setGeometry(QRect(110, 5, 71, 61))

        self.verticalLayout.addWidget(self.widget_L01)

        self.widget_L02 = QWidget(self.centralwidget)
        self.widget_L02.setObjectName(u"widget_L02")
        self.widget_L02.setStyleSheet(u"\n"
"        QWidget#widget_L02 {\n"
"            border: 1px solid gray;\n"
"        }\n"
"       ")
        self.verticalLayout_2 = QVBoxLayout(self.widget_L02)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.widget = QWidget(self.widget_L02)
        self.widget.setObjectName(u"widget")
        self.widget.setMinimumSize(QSize(0, 50))
        self.widget.setMaximumSize(QSize(16777215, 50))
        self.widget.setStyleSheet(u"\n"
"              QWidget#widget {\n"
"                border: 1px solid gray;\n"
"              }\n"
"          ")
        self.horizontalLayout_3 = QHBoxLayout(self.widget)
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.checkBoxStartMonitor = QCheckBox(self.widget)
        self.checkBoxStartMonitor.setObjectName(u"checkBoxStartMonitor")
        self.checkBoxStartMonitor.setMinimumSize(QSize(200, 0))

        self.horizontalLayout_3.addWidget(self.checkBoxStartMonitor)

        self.statusLabel = QLabel(self.widget)
        self.statusLabel.setObjectName(u"statusLabel")
        self.statusLabel.setMinimumSize(QSize(250, 0))

        self.horizontalLayout_3.addWidget(self.statusLabel)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)


        self.verticalLayout_2.addWidget(self.widget)

        self.widget_2 = QWidget(self.widget_L02)
        self.widget_2.setObjectName(u"widget_2")
        self.horizontalLayout = QHBoxLayout(self.widget_2)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.widget_3 = QWidget(self.widget_2)
        self.widget_3.setObjectName(u"widget_3")

        self.horizontalLayout.addWidget(self.widget_3)

        self.widget_4 = QWidget(self.widget_2)
        self.widget_4.setObjectName(u"widget_4")
        self.horizontalLayout_2 = QHBoxLayout(self.widget_4)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.logList = QListView(self.widget_4)
        self.logList.setObjectName(u"logList")

        self.horizontalLayout_2.addWidget(self.logList)


        self.horizontalLayout.addWidget(self.widget_4)

        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 1)

        self.verticalLayout_2.addWidget(self.widget_2)


        self.verticalLayout.addWidget(self.widget_L02)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1083, 33))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.pushButton_screenshot.setText(QCoreApplication.translate("MainWindow", u"\u622a\u56fe", None))
        self.pushButton_test.setText(QCoreApplication.translate("MainWindow", u"\u6d4b\u8bd5", None))
        self.checkBoxStartMonitor.setText(QCoreApplication.translate("MainWindow", u"\u542f\u52a8\u76d1\u63a7", None))
        self.statusLabel.setText(QCoreApplication.translate("MainWindow", u"TextLabel", None))
    # retranslateUi

