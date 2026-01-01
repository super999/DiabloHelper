# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'tab_advance_image.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QHBoxLayout, QHeaderView,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QTableWidget, QTableWidgetItem, QToolButton, QVBoxLayout,
    QWidget)

class Ui_TabAdvanceImage(object):
    def setupUi(self, TabAdvanceImage):
        if not TabAdvanceImage.objectName():
            TabAdvanceImage.setObjectName(u"TabAdvanceImage")
        TabAdvanceImage.resize(946, 482)
        self.verticalLayout = QVBoxLayout(TabAdvanceImage)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.widget_L01 = QWidget(TabAdvanceImage)
        self.widget_L01.setObjectName(u"widget_L01")
        self.widget_L01.setMinimumSize(QSize(0, 70))
        self.widget_L01.setMaximumSize(QSize(16777215, 70))
        self.widget_L01.setStyleSheet(u"")
        self.pushButton_screenshot = QPushButton(self.widget_L01)
        self.pushButton_screenshot.setObjectName(u"pushButton_screenshot")
        self.pushButton_screenshot.setGeometry(QRect(10, 5, 71, 61))
        self.pushButton_test = QPushButton(self.widget_L01)
        self.pushButton_test.setObjectName(u"pushButton_test")
        self.pushButton_test.setGeometry(QRect(350, 5, 71, 61))
        self.pushButton_smart_pic_cut = QPushButton(self.widget_L01)
        self.pushButton_smart_pic_cut.setObjectName(u"pushButton_smart_pic_cut")
        self.pushButton_smart_pic_cut.setGeometry(QRect(90, 5, 71, 61))
        self.pushButton_pic_match = QPushButton(self.widget_L01)
        self.pushButton_pic_match.setObjectName(u"pushButton_pic_match")
        self.pushButton_pic_match.setGeometry(QRect(170, 5, 71, 61))
        self.btn_save_config = QToolButton(self.widget_L01)
        self.btn_save_config.setObjectName(u"btn_save_config")
        self.btn_save_config.setGeometry(QRect(260, 5, 71, 61))
        self.btn_save_config.setIconSize(QSize(55, 55))
        self.btn_save_config.setCheckable(True)
        self.btn_save_config.setChecked(False)
        self.btn_save_config.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.btn_save_config.setAutoRaise(False)

        self.verticalLayout.addWidget(self.widget_L01)

        self.widget_L02 = QWidget(TabAdvanceImage)
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
        self.horizontalLayout_3.setContentsMargins(10, 0, 0, 0)
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
        self.widget_3.setMaximumSize(QSize(400, 16777215))
        self.verticalLayout_3 = QVBoxLayout(self.widget_3)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.labelImageShow = QLabel(self.widget_3)
        self.labelImageShow.setObjectName(u"labelImageShow")
        self.labelImageShow.setMaximumSize(QSize(400, 16777215))

        self.verticalLayout_3.addWidget(self.labelImageShow)


        self.horizontalLayout.addWidget(self.widget_3)

        self.widget_4 = QWidget(self.widget_2)
        self.widget_4.setObjectName(u"widget_4")
        self.horizontalLayout_2 = QHBoxLayout(self.widget_4)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.tableWidget = QTableWidget(self.widget_4)
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

        self.horizontalLayout_2.addWidget(self.tableWidget)


        self.horizontalLayout.addWidget(self.widget_4)

        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 1)

        self.verticalLayout_2.addWidget(self.widget_2)


        self.verticalLayout.addWidget(self.widget_L02)


        self.retranslateUi(TabAdvanceImage)

        QMetaObject.connectSlotsByName(TabAdvanceImage)
    # setupUi

    def retranslateUi(self, TabAdvanceImage):
        TabAdvanceImage.setWindowTitle(QCoreApplication.translate("TabAdvanceImage", u"\u9ad8\u7ea7\u56fe\u50cf\u8bc6\u522b-TabAdvanceImage", None))
        self.pushButton_screenshot.setText(QCoreApplication.translate("TabAdvanceImage", u"\u622a\u56fe", None))
        self.pushButton_test.setText(QCoreApplication.translate("TabAdvanceImage", u"\u6d4b\u8bd5", None))
        self.pushButton_smart_pic_cut.setText(QCoreApplication.translate("TabAdvanceImage", u"\u622a\u56fe\n"
"\u8bc6\u522b", None))
        self.pushButton_pic_match.setText(QCoreApplication.translate("TabAdvanceImage", u"\u56fe\u7247\n"
"\u5339\u914d", None))
        self.btn_save_config.setText(QCoreApplication.translate("TabAdvanceImage", u"\u4fdd\u5b58\u914d\u7f6e", None))
        self.checkBoxStartMonitor.setText(QCoreApplication.translate("TabAdvanceImage", u"\u542f\u52a8\u76d1\u63a7", None))
        self.statusLabel.setText(QCoreApplication.translate("TabAdvanceImage", u"\u5f53\u524d\u72b6\u6001\uff1a\u672a\u542f\u52a8", None))
        self.labelImageShow.setText(QCoreApplication.translate("TabAdvanceImage", u"TextLabel", None))
        ___qtablewidgetitem = self.tableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("TabAdvanceImage", u"\u542f\u7528\u70ed\u952e", None));
        ___qtablewidgetitem1 = self.tableWidget.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("TabAdvanceImage", u"\u542f\u7528", None));
        ___qtablewidgetitem2 = self.tableWidget.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("TabAdvanceImage", u"\u53d1\u9001\u70ed\u952e", None));
        ___qtablewidgetitem3 = self.tableWidget.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("TabAdvanceImage", u"\u626b\u63cf\u95f4\u9694\u65f6\u95f4", None));
        ___qtablewidgetitem4 = self.tableWidget.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("TabAdvanceImage", u"\u64cd\u4f5c", None));
        ___qtablewidgetitem5 = self.tableWidget.horizontalHeaderItem(5)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("TabAdvanceImage", u"\u8bf4\u660e\uff08\u9009\u9879\uff09", None));
    # retranslateUi

