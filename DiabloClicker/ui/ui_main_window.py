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
from PySide6.QtWidgets import (QApplication, QMainWindow, QMenuBar, QSizePolicy,
    QStatusBar, QToolButton, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 590)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setStyleSheet(u"\n"
"    QWidget#centralwidget {\n"
"        background-color: rgba(208, 208, 255, 1);\n"
"        border: 1px solid black;\n"
"    }\n"
"    ")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(1, 1, 1, 1)
        self.widget_L01 = QWidget(self.centralwidget)
        self.widget_L01.setObjectName(u"widget_L01")
        self.widget_L01.setMaximumSize(QSize(16777215, 100))
        self.widget_L01.setStyleSheet(u"\n"
"       background-color: rgb(200, 200, 200);\n"
"       QToolButton {           \n"
"           background-color: rgb(180, 0, 0);\n"
"           border: 1px solid black;\n"
"           border-radius: 20px;\n"
"       }\n"
"       ")
        self.toolButton_screenshot = QToolButton(self.widget_L01)
        self.toolButton_screenshot.setObjectName(u"toolButton_screenshot")
        self.toolButton_screenshot.setGeometry(QRect(30, 20, 71, 61))

        self.verticalLayout.addWidget(self.widget_L01)

        self.widget_L02 = QWidget(self.centralwidget)
        self.widget_L02.setObjectName(u"widget_L02")

        self.verticalLayout.addWidget(self.widget_L02)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 33))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.toolButton_screenshot.setText(QCoreApplication.translate("MainWindow", u"\u622a\u56fe", None))
    # retranslateUi

