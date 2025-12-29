# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'tab_timed_key.ui'
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
from PySide6.QtWidgets import (QApplication, QHeaderView, QSizePolicy, QTableWidget,
    QTableWidgetItem, QToolButton, QVBoxLayout, QWidget)
import res_rc

class Ui_TabTimedKey(object):
    def setupUi(self, TabTimedKey):
        if not TabTimedKey.objectName():
            TabTimedKey.setObjectName(u"TabTimedKey")
        TabTimedKey.resize(1034, 664)
        self.verticalLayout = QVBoxLayout(TabTimedKey)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget = QWidget(TabTimedKey)
        self.widget.setObjectName(u"widget")
        self.verticalLayout_2 = QVBoxLayout(self.widget)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.widget_2 = QWidget(self.widget)
        self.widget_2.setObjectName(u"widget_2")
        self.widget_2.setMinimumSize(QSize(0, 60))
        self.widget_2.setStyleSheet(u"border: 1px solid gray;")
        self.btn_start = QToolButton(self.widget_2)
        self.btn_start.setObjectName(u"btn_start")
        self.btn_start.setGeometry(QRect(30, 5, 101, 50))
        icon = QIcon()
        icon.addFile(u":/default/res/psd/ps\u5bfc\u51fa/StartGreen.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        icon.addFile(u":/default/res/psd/ps\u5bfc\u51fa/StopRed.png", QSize(), QIcon.Mode.Normal, QIcon.State.On)
        self.btn_start.setIcon(icon)
        self.btn_start.setIconSize(QSize(55, 55))
        self.btn_start.setCheckable(True)
        self.btn_start.setChecked(False)
        self.btn_start.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.btn_start.setAutoRaise(False)
        self.btn_save_config = QToolButton(self.widget_2)
        self.btn_save_config.setObjectName(u"btn_save_config")
        self.btn_save_config.setGeometry(QRect(160, 5, 131, 50))
        self.btn_save_config.setIconSize(QSize(55, 55))
        self.btn_save_config.setCheckable(True)
        self.btn_save_config.setChecked(False)
        self.btn_save_config.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.btn_save_config.setAutoRaise(False)

        self.verticalLayout_2.addWidget(self.widget_2)

        self.tableWidget = QTableWidget(self.widget)
        if (self.tableWidget.columnCount() < 6):
            self.tableWidget.setColumnCount(6)
        __qtablewidgetitem = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(5, __qtablewidgetitem5)
        self.tableWidget.setObjectName(u"tableWidget")

        self.verticalLayout_2.addWidget(self.tableWidget)


        self.verticalLayout.addWidget(self.widget)


        self.retranslateUi(TabTimedKey)

        QMetaObject.connectSlotsByName(TabTimedKey)
    # setupUi

    def retranslateUi(self, TabTimedKey):
        TabTimedKey.setWindowTitle(QCoreApplication.translate("TabTimedKey", u"\u5b9a\u65f6\u6309\u952e", None))
        self.btn_start.setText(QCoreApplication.translate("TabTimedKey", u"\u5df2\u542f\u52a8", None))
        self.btn_save_config.setText(QCoreApplication.translate("TabTimedKey", u"\u4fdd\u5b58\u914d\u7f6e", None))
        ___qtablewidgetitem = self.tableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("TabTimedKey", u"\u70ed\u952e", None));
        ___qtablewidgetitem1 = self.tableWidget.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("TabTimedKey", u"\u542f\u7528", None));
        ___qtablewidgetitem2 = self.tableWidget.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("TabTimedKey", u"\u65f6\u95f4", None));
        ___qtablewidgetitem3 = self.tableWidget.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("TabTimedKey", u"\u5269\u4f59\u65f6\u95f4", None));
        ___qtablewidgetitem4 = self.tableWidget.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("TabTimedKey", u"\u64cd\u4f5c", None));
        ___qtablewidgetitem5 = self.tableWidget.horizontalHeaderItem(5)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("TabTimedKey", u"\u8bf4\u660e\uff08\u9009\u9879\uff09", None));
    # retranslateUi

