# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'create_project_window.ui'
#
# Created by: PyQt5 UI code generator 5.15.11
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(400, 350)
        Dialog.setMinimumSize(QtCore.QSize(400, 350))
        Dialog.setMaximumSize(QtCore.QSize(400, 350))
        self.frame_2 = QtWidgets.QFrame(Dialog)
        self.frame_2.setGeometry(QtCore.QRect(10, 10, 380, 330))
        self.frame_2.setMinimumSize(QtCore.QSize(380, 330))
        self.frame_2.setMaximumSize(QtCore.QSize(380, 330))
        self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_2.setObjectName("frame_2")
        self.gridLayout = QtWidgets.QGridLayout(self.frame_2)
        self.gridLayout.setContentsMargins(-1, -1, -1, 9)
        self.gridLayout.setObjectName("gridLayout")
        self.frame = QtWidgets.QFrame(self.frame_2)
        self.frame.setMinimumSize(QtCore.QSize(250, 0))
        self.frame.setMaximumSize(QtCore.QSize(250, 16777215))
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.frame)
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.label = QtWidgets.QLabel(self.frame)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.frame_7 = QtWidgets.QFrame(self.frame)
        self.frame_7.setMinimumSize(QtCore.QSize(0, 30))
        self.frame_7.setMaximumSize(QtCore.QSize(16777215, 30))
        self.frame_7.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_7.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_7.setObjectName("frame_7")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.frame_7)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.lineEdit = QtWidgets.QLineEdit(self.frame_7)
        self.lineEdit.setObjectName("lineEdit")
        self.horizontalLayout_2.addWidget(self.lineEdit)
        self.verticalLayout.addWidget(self.frame_7)
        self.label_2 = QtWidgets.QLabel(self.frame)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.frame_8 = QtWidgets.QFrame(self.frame)
        self.frame_8.setMinimumSize(QtCore.QSize(0, 30))
        self.frame_8.setMaximumSize(QtCore.QSize(16777215, 30))
        self.frame_8.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_8.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_8.setObjectName("frame_8")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.frame_8)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.lineEdit_2 = QtWidgets.QLineEdit(self.frame_8)
        self.lineEdit_2.setEnabled(True)
        self.lineEdit_2.setStyleSheet("")
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.horizontalLayout_3.addWidget(self.lineEdit_2)
        self.pushButton_2 = QtWidgets.QPushButton(self.frame_8)
        self.pushButton_2.setMinimumSize(QtCore.QSize(60, 0))
        self.pushButton_2.setMaximumSize(QtCore.QSize(60, 16777215))
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout_3.addWidget(self.pushButton_2)
        self.verticalLayout.addWidget(self.frame_8)
        self.label_3 = QtWidgets.QLabel(self.frame)
        self.label_3.setObjectName("label_3")
        self.verticalLayout.addWidget(self.label_3)
        self.frame_9 = QtWidgets.QFrame(self.frame)
        self.frame_9.setMinimumSize(QtCore.QSize(0, 30))
        self.frame_9.setMaximumSize(QtCore.QSize(16777215, 30))
        self.frame_9.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_9.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_9.setObjectName("frame_9")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.frame_9)
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.lineEdit_3 = QtWidgets.QLineEdit(self.frame_9)
        self.lineEdit_3.setEnabled(True)
        self.lineEdit_3.setStyleSheet("")
        self.lineEdit_3.setObjectName("lineEdit_3")
        self.horizontalLayout_4.addWidget(self.lineEdit_3)
        self.pushButton_3 = QtWidgets.QPushButton(self.frame_9)
        self.pushButton_3.setMinimumSize(QtCore.QSize(60, 0))
        self.pushButton_3.setMaximumSize(QtCore.QSize(60, 16777215))
        self.pushButton_3.setObjectName("pushButton_3")
        self.horizontalLayout_4.addWidget(self.pushButton_3)
        self.verticalLayout.addWidget(self.frame_9)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem2)
        self.frame_3 = QtWidgets.QFrame(self.frame)
        self.frame_3.setMinimumSize(QtCore.QSize(0, 50))
        self.frame_3.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_3.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_3.setObjectName("frame_3")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.frame_3)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem3)
        self.pushButton = QtWidgets.QPushButton(self.frame_3)
        self.pushButton.setMinimumSize(QtCore.QSize(80, 30))
        self.pushButton.setMaximumSize(QtCore.QSize(80, 30))
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout.addWidget(self.pushButton)
        spacerItem4 = QtWidgets.QSpacerItem(56, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem4)
        self.verticalLayout.addWidget(self.frame_3)
        self.gridLayout.addWidget(self.frame, 0, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label.setText(_translate("Dialog", "Project Name"))
        self.label_2.setText(_translate("Dialog", "Original AoE2DE Folder"))
        self.pushButton_2.setText(_translate("Dialog", "Browse"))
        self.label_3.setText(_translate("Dialog", "Mods Folder"))
        self.pushButton_3.setText(_translate("Dialog", "Browse"))
        self.pushButton.setText(_translate("Dialog", "Create Project"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())