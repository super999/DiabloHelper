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
from PySide6.QtWidgets import (QApplication, QCheckBox, QMainWindow, QMenuBar,
    QPushButton, QSizePolicy, QStatusBar, QVBoxLayout,
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
        self.widget_L01.setMaximumSize(QSize(16777215, 60))
        self.widget_L01.setStyleSheet(u"")
        self.pushButton_screenshot = QPushButton(self.widget_L01)
        self.pushButton_screenshot.setObjectName(u"pushButton_screenshot")
        self.pushButton_screenshot.setGeometry(QRect(20, 0, 71, 61))
        self.pushButton_test = QPushButton(self.widget_L01)
        self.pushButton_test.setObjectName(u"pushButton_test")
        self.pushButton_test.setGeometry(QRect(110, 0, 71, 61))

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
        self.widget.setMaximumSize(QSize(16777215, 50))
        self.checkBoxStartMonitor = QCheckBox(self.widget)
        self.checkBoxStartMonitor.setObjectName(u"checkBoxStartMonitor")
        self.checkBoxStartMonitor.setGeometry(QRect(30, 15, 131, 20))

        self.verticalLayout_2.addWidget(self.widget)

        self.widget_2 = QWidget(self.widget_L02)
        self.widget_2.setObjectName(u"widget_2")

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
    # retranslateUi

