import os
import shutil
import tkinter as tk
from tkinter import Tk, Menu, Label, ttk, Canvas, Toplevel, Entry
from tkinter.filedialog import askdirectory, askopenfilename
from tkinter import messagebox
from tkinter import filedialog
import sys
import json
import string
import re
import random
from PIL import Image, ImageTk
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QFileDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QSettings
import genieutils
#from genieutils import GenieObjectContainer
from genieutils.datfile import DatFile

civ_objects = []
class Ui_MainWindow(object):
    def update_civs(self, civ_list):
        global civ_objects
        civ_objects = civ_list

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(612, 704)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_16 = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_16.setObjectName("horizontalLayout_16")
        self.scrollArea = QtWidgets.QScrollArea(self.centralwidget)
        self.scrollArea.setEnabled(True)
        self.scrollArea.setMinimumSize(QtCore.QSize(200, 645))
        self.scrollArea.setMaximumSize(QtCore.QSize(200, 645))
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 198, 643))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.frame = QtWidgets.QFrame(self.scrollAreaWidgetContents)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.frame)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.frame_4 = QtWidgets.QFrame(self.frame)
        self.frame_4.setMinimumSize(QtCore.QSize(176, 50))
        self.frame_4.setMaximumSize(QtCore.QSize(176, 50))
        self.frame_4.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_4.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_4.setObjectName("frame_4")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.frame_4)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setSpacing(50)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.civilisation_dropdown = QtWidgets.QComboBox(self.frame_4)
        self.civilisation_dropdown.setMinimumSize(QtCore.QSize(120, 25))
        self.civilisation_dropdown.setMaximumSize(QtCore.QSize(120, 25))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setWeight(75)
        self.civilisation_dropdown.setFont(font)
        self.civilisation_dropdown.setObjectName("civilisation_dropdown")
        self.horizontalLayout_3.addWidget(self.civilisation_dropdown)
        self.civilisation_dropdown.currentIndexChanged.connect(self.on_civilisation_dropdown_changed)
        self.civilisation_icon_image = QtWidgets.QLabel(self.frame_4)
        self.civilisation_icon_image.setMinimumSize(QtCore.QSize(50, 50))
        self.civilisation_icon_image.setMaximumSize(QtCore.QSize(50, 50))
        self.civilisation_icon_image.setText("")
        self.civilisation_icon_image.setPixmap(QtGui.QPixmap("../../../../../../../../Games/Age of Empires 2 DE/76561198021486964/mods/local/NewCivilizations/resources/_common/wpfg/resources/civ_techtree/menu_techtree_britons.png"))
        self.civilisation_icon_image.setScaledContents(True)
        self.civilisation_icon_image.setObjectName("civilisation_icon_image")
        self.horizontalLayout_3.addWidget(self.civilisation_icon_image)
        self.verticalLayout_3.addWidget(self.frame_4)
        self.frame_7 = QtWidgets.QFrame(self.frame)
        self.frame_7.setMinimumSize(QtCore.QSize(0, 80))
        self.frame_7.setMaximumSize(QtCore.QSize(16777215, 80))
        self.frame_7.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_7.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_7.setObjectName("frame_7")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.frame_7)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 5)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.architecture_label = QtWidgets.QLabel(self.frame_7)
        self.architecture_label.setObjectName("architecture_label")
        self.verticalLayout_2.addWidget(self.architecture_label)
        self.architecture_dropdown = QtWidgets.QComboBox(self.frame_7)
        self.architecture_dropdown.setMinimumSize(QtCore.QSize(0, 20))
        self.architecture_dropdown.setObjectName("architecture_dropdown")
        self.architecture_dropdown.addItem("African")
        self.architecture_dropdown.addItem("Central Asian")
        self.architecture_dropdown.addItem("Central European")
        self.architecture_dropdown.addItem("East Asian")
        self.architecture_dropdown.addItem("Eastern European")
        self.architecture_dropdown.addItem("Mediterranean")
        self.architecture_dropdown.addItem("Middle Eastern")
        self.architecture_dropdown.addItem("Mesoamerican")
        self.architecture_dropdown.addItem("South Asian")
        self.architecture_dropdown.addItem("Southeast Asian")
        self.architecture_dropdown.addItem("Western European")
        self.verticalLayout_2.addWidget(self.architecture_dropdown)
        self.language_label = QtWidgets.QLabel(self.frame_7)
        self.language_label.setObjectName("language_label")
        self.verticalLayout_2.addWidget(self.language_label)
        self.language_dropdown = QtWidgets.QComboBox(self.frame_7)
        self.language_dropdown.setMinimumSize(QtCore.QSize(0, 20))
        self.language_dropdown.setObjectName("language_dropdown")
        self.language_dropdown.addItem("Armenians [Armenian]")
        self.language_dropdown.addItem("Aztecs [Nahuatl]")
        self.language_dropdown.addItem("Bengalis [Shadhu Bengali]")
        self.language_dropdown.addItem("Berbers [Taqbaylit]")
        self.language_dropdown.addItem("Bohemians [Czech]")
        self.language_dropdown.addItem("Britons [Middle English]")
        self.language_dropdown.addItem("Bulgarians [South Slavic]")
        self.language_dropdown.addItem("Burgundians [Burgundian]")
        self.language_dropdown.addItem("Burmese [Burmese]")
        self.language_dropdown.addItem("Byzantines / Italians [Latin]")
        self.language_dropdown.addItem("Celts [Gaelic / Irish]")
        self.language_dropdown.addItem("Chinese [Mandarin]")
        self.language_dropdown.addItem("Cumans [Cuman]")
        self.language_dropdown.addItem("Dravidians [Tamil]")
        self.language_dropdown.addItem("Ethiopians [Amharic]")
        self.language_dropdown.addItem("Franks [Old French]")
        self.language_dropdown.addItem("Georgians [Georgian]")
        self.language_dropdown.addItem("Goths / Teutons [Old German]")
        self.language_dropdown.addItem("Gurjaras [Gujarati]")
        self.language_dropdown.addItem("Hindustanis [Hindustani]")
        self.language_dropdown.addItem("Mongols / Huns [Mongolian]")
        self.language_dropdown.addItem("Incas [Runasimi / Quechua]")
        self.language_dropdown.addItem("Japanese [Japanese]")
        self.language_dropdown.addItem("Khmer [Khmer]")
        self.language_dropdown.addItem("Koreans [Korean]")
        self.language_dropdown.addItem("Lithuanians [Lithuanian]")
        self.language_dropdown.addItem("Magyars [Hungarian]")
        self.language_dropdown.addItem("Malay [Old Malay]")
        self.language_dropdown.addItem("Malians [Eastern Maninka]")
        self.language_dropdown.addItem("Mayans [K'iche']")
        self.language_dropdown.addItem("Persians [Farsi / Persian]")
        self.language_dropdown.addItem("Poles [Polish]")
        self.language_dropdown.addItem("Portuguese [Portuguese]")
        self.language_dropdown.addItem("Romans [Vulgar Latin]")
        self.language_dropdown.addItem("Saracens [Arabic]")
        self.language_dropdown.addItem("Sicilians [Sicilian]")
        self.language_dropdown.addItem("Slavs [Russian]")
        self.language_dropdown.addItem("Spanish [Spanish]")
        self.language_dropdown.addItem("Tatars [Chagatai]")
        self.language_dropdown.addItem("Turks [Turkish]")
        self.language_dropdown.addItem("Vietnamese [Vietnamese]")
        self.language_dropdown.addItem("Vikings [Old Norse]")
        self.verticalLayout_2.addWidget(self.language_dropdown)
        self.verticalLayout_3.addWidget(self.frame_7)
        self.civilisation_description_label = QtWidgets.QLabel(self.frame)
        self.civilisation_description_label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.civilisation_description_label.setWordWrap(True)
        self.civilisation_description_label.setObjectName("civilisation_description_label")
        self.verticalLayout_3.addWidget(self.civilisation_description_label)
        self.gridLayout_5.addWidget(self.frame, 1, 0, 1, 1)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.horizontalLayout_16.addWidget(self.scrollArea)
        self.scrollArea_2 = QtWidgets.QScrollArea(self.centralwidget)
        self.scrollArea_2.setMinimumSize(QtCore.QSize(0, 645))
        self.scrollArea_2.setMaximumSize(QtCore.QSize(16777215, 645))
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollArea_2.setObjectName("scrollArea_2")
        self.scrollAreaWidgetContents_2 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_2.setGeometry(QtCore.QRect(0, 0, 5018, 626))
        self.scrollAreaWidgetContents_2.setObjectName("scrollAreaWidgetContents_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.scrollAreaWidgetContents_2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.frame_3 = QtWidgets.QFrame(self.scrollAreaWidgetContents_2)
        self.frame_3.setMinimumSize(QtCore.QSize(5000, 0))
        self.frame_3.setMaximumSize(QtCore.QSize(5000, 16777215))
        self.frame_3.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_3.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_3.setObjectName("frame_3")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.frame_3)
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.frame_8 = QtWidgets.QFrame(self.frame_3)
        self.frame_8.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_8.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_8.setObjectName("frame_8")
        self.verticalLayout_8 = QtWidgets.QVBoxLayout(self.frame_8)
        self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_8.setSpacing(0)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.frame_10 = QtWidgets.QFrame(self.frame_8)
        self.frame_10.setMaximumSize(QtCore.QSize(16777215, 150))
        self.frame_10.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.frame_10.setStyleSheet("background-color: rgb(217, 217, 217);")
        self.frame_10.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_10.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_10.setObjectName("frame_10")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.frame_10)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.frame_5 = QtWidgets.QFrame(self.frame_10)
        self.frame_5.setMinimumSize(QtCore.QSize(100, 100))
        self.frame_5.setMaximumSize(QtCore.QSize(100, 100))
        self.frame_5.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_5.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_5.setObjectName("frame_5")
        self.gridLayout = QtWidgets.QGridLayout(self.frame_5)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(self.frame_5)
        self.label.setMinimumSize(QtCore.QSize(85, 65))
        self.label.setMaximumSize(QtCore.QSize(75, 60))
        self.label.setText("")
        self.label.setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/dark_age.png"))
        self.label.setScaledContents(True)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.horizontalLayout.addWidget(self.frame_5)
        self.frame_13 = QtWidgets.QFrame(self.frame_10)
        self.frame_13.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_13.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_13.setObjectName("frame_13")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.frame_13)
        self.verticalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_7.setSpacing(0)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.frame_15 = QtWidgets.QFrame(self.frame_13)
        self.frame_15.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_15.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_15.setObjectName("frame_15")
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout(self.frame_15)
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_7.setSpacing(0)
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.frame_27 = QtWidgets.QFrame(self.frame_15)
        self.frame_27.setMinimumSize(QtCore.QSize(100, 0))
        self.frame_27.setMaximumSize(QtCore.QSize(16777215, 75))
        font = QtGui.QFont()
        font.setKerning(True)
        self.frame_27.setFont(font)
        self.frame_27.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.frame_27.setAutoFillBackground(False)
        self.frame_27.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_27.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_27.setObjectName("frame_27")
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout(self.frame_27)
        self.horizontalLayout_8.setContentsMargins(5, 0, 5, 0)
        self.horizontalLayout_8.setSpacing(10)
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.Archer = QtWidgets.QWidget(self.frame_27)
        self.Archer.setEnabled(True)
        self.Archer.setMinimumSize(QtCore.QSize(75, 75))
        self.Archer.setMaximumSize(QtCore.QSize(75, 75))
        self.Archer.setStyleSheet("")
        self.Archer.setObjectName("Archer")
        self.background = QtWidgets.QLabel(self.Archer)
        self.background.setEnabled(True)
        self.background.setGeometry(QtCore.QRect(0, 0, 75, 75))
        self.background.setMinimumSize(QtCore.QSize(75, 75))
        self.background.setMaximumSize(QtCore.QSize(75, 75))
        self.background.setAutoFillBackground(False)
        self.background.setText("")
        self.background.setPixmap(QtGui.QPixmap("../../../../../../../../OneDrive/Documents/GitHub/AOE2DE_CivCreator/Images/TechTree/building.png"))
        self.background.setScaledContents(True)
        self.background.setObjectName("background")
        self.text = QtWidgets.QLabel(self.Archer)
        self.text.setEnabled(True)
        self.text.setGeometry(QtCore.QRect(10, 46, 55, 16))
        font = QtGui.QFont()
        font.setPointSize(5)
        self.text.setFont(font)
        self.text.setStyleSheet("color: rgb(255, 255, 255);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.text.setAlignment(QtCore.Qt.AlignCenter)
        self.text.setWordWrap(True)
        self.text.setObjectName("text")
        self.icon = QtWidgets.QLabel(self.Archer)
        self.icon.setEnabled(True)
        self.icon.setGeometry(QtCore.QRect(20, 10, 35, 35))
        self.icon.setMinimumSize(QtCore.QSize(35, 35))
        self.icon.setMaximumSize(QtCore.QSize(35, 33))
        self.icon.setText("")
        self.icon.setPixmap(QtGui.QPixmap("../../../../../../../../OneDrive/Documents/GitHub/AOE2DE_CivCreator/Images/TechTree/Archer.png"))
        self.icon.setScaledContents(True)
        self.icon.setObjectName("icon")
        self.horizontalLayout_8.addWidget(self.Archer)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_8.addItem(spacerItem)
        self.horizontalLayout_7.addWidget(self.frame_27)
        self.verticalLayout_7.addWidget(self.frame_15)
        self.frame_14 = QtWidgets.QFrame(self.frame_13)
        self.frame_14.setMaximumSize(QtCore.QSize(16777215, 75))
        self.frame_14.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_14.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_14.setObjectName("frame_14")
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout(self.frame_14)
        self.horizontalLayout_9.setContentsMargins(5, 0, 5, 0)
        self.horizontalLayout_9.setSpacing(10)
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.Archer_2 = QtWidgets.QWidget(self.frame_14)
        self.Archer_2.setEnabled(True)
        self.Archer_2.setMinimumSize(QtCore.QSize(75, 75))
        self.Archer_2.setMaximumSize(QtCore.QSize(75, 75))
        self.Archer_2.setStyleSheet("")
        self.Archer_2.setObjectName("Archer_2")
        self.background_10 = QtWidgets.QLabel(self.Archer_2)
        self.background_10.setEnabled(True)
        self.background_10.setGeometry(QtCore.QRect(0, 0, 75, 75))
        self.background_10.setMinimumSize(QtCore.QSize(75, 75))
        self.background_10.setMaximumSize(QtCore.QSize(75, 75))
        self.background_10.setAutoFillBackground(False)
        self.background_10.setText("")
        self.background_10.setPixmap(QtGui.QPixmap("../../../../../../../../OneDrive/Documents/GitHub/AOE2DE_CivCreator/Images/TechTree/building.png"))
        self.background_10.setScaledContents(True)
        self.background_10.setObjectName("background_10")
        self.text_10 = QtWidgets.QLabel(self.Archer_2)
        self.text_10.setEnabled(True)
        self.text_10.setGeometry(QtCore.QRect(10, 46, 55, 16))
        font = QtGui.QFont()
        font.setPointSize(5)
        self.text_10.setFont(font)
        self.text_10.setStyleSheet("color: rgb(255, 255, 255);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.text_10.setAlignment(QtCore.Qt.AlignCenter)
        self.text_10.setWordWrap(True)
        self.text_10.setObjectName("text_10")
        self.icon_10 = QtWidgets.QLabel(self.Archer_2)
        self.icon_10.setEnabled(True)
        self.icon_10.setGeometry(QtCore.QRect(20, 10, 35, 35))
        self.icon_10.setMinimumSize(QtCore.QSize(35, 35))
        self.icon_10.setMaximumSize(QtCore.QSize(35, 33))
        self.icon_10.setText("")
        self.icon_10.setPixmap(QtGui.QPixmap("../../../../../../../../OneDrive/Documents/GitHub/AOE2DE_CivCreator/Images/TechTree/Archer.png"))
        self.icon_10.setScaledContents(True)
        self.icon_10.setObjectName("icon_10")
        self.horizontalLayout_9.addWidget(self.Archer_2)
        spacerItem1 = QtWidgets.QSpacerItem(4792, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_9.addItem(spacerItem1)
        self.verticalLayout_7.addWidget(self.frame_14)
        self.horizontalLayout.addWidget(self.frame_13)
        self.verticalLayout_8.addWidget(self.frame_10)
        self.frame_9 = QtWidgets.QFrame(self.frame_8)
        self.frame_9.setMaximumSize(QtCore.QSize(16777215, 150))
        self.frame_9.setStyleSheet("background-color: rgb(177, 177, 177);")
        self.frame_9.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_9.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_9.setObjectName("frame_9")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.frame_9)
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.frame_16 = QtWidgets.QFrame(self.frame_9)
        self.frame_16.setMinimumSize(QtCore.QSize(100, 100))
        self.frame_16.setMaximumSize(QtCore.QSize(100, 100))
        self.frame_16.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_16.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_16.setObjectName("frame_16")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.frame_16)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.label_2 = QtWidgets.QLabel(self.frame_16)
        self.label_2.setMinimumSize(QtCore.QSize(85, 65))
        self.label_2.setMaximumSize(QtCore.QSize(75, 60))
        self.label_2.setText("")
        self.label_2.setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/feudal_age.png"))
        self.label_2.setScaledContents(True)
        self.label_2.setObjectName("label_2")
        self.gridLayout_2.addWidget(self.label_2, 0, 0, 1, 1)
        self.horizontalLayout_4.addWidget(self.frame_16)
        self.frame_17 = QtWidgets.QFrame(self.frame_9)
        self.frame_17.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_17.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_17.setObjectName("frame_17")
        self.verticalLayout_9 = QtWidgets.QVBoxLayout(self.frame_17)
        self.verticalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_9.setSpacing(0)
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.frame_18 = QtWidgets.QFrame(self.frame_17)
        self.frame_18.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.frame_18.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_18.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_18.setObjectName("frame_18")
        self.horizontalLayout_17 = QtWidgets.QHBoxLayout(self.frame_18)
        self.horizontalLayout_17.setContentsMargins(5, 0, 5, 0)
        self.horizontalLayout_17.setSpacing(10)
        self.horizontalLayout_17.setObjectName("horizontalLayout_17")
        self.Archer_9 = QtWidgets.QWidget(self.frame_18)
        self.Archer_9.setEnabled(True)
        self.Archer_9.setMinimumSize(QtCore.QSize(75, 75))
        self.Archer_9.setMaximumSize(QtCore.QSize(75, 75))
        self.Archer_9.setStyleSheet("")
        self.Archer_9.setObjectName("Archer_9")
        self.background_19 = QtWidgets.QLabel(self.Archer_9)
        self.background_19.setEnabled(True)
        self.background_19.setGeometry(QtCore.QRect(0, 0, 75, 75))
        self.background_19.setMinimumSize(QtCore.QSize(75, 75))
        self.background_19.setMaximumSize(QtCore.QSize(75, 75))
        self.background_19.setAutoFillBackground(False)
        self.background_19.setText("")
        self.background_19.setPixmap(QtGui.QPixmap("../../../../../../../../OneDrive/Documents/GitHub/AOE2DE_CivCreator/Images/TechTree/building.png"))
        self.background_19.setScaledContents(True)
        self.background_19.setObjectName("background_19")
        self.text_19 = QtWidgets.QLabel(self.Archer_9)
        self.text_19.setEnabled(True)
        self.text_19.setGeometry(QtCore.QRect(10, 46, 55, 16))
        font = QtGui.QFont()
        font.setPointSize(5)
        self.text_19.setFont(font)
        self.text_19.setStyleSheet("color: rgb(255, 255, 255);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.text_19.setAlignment(QtCore.Qt.AlignCenter)
        self.text_19.setWordWrap(True)
        self.text_19.setObjectName("text_19")
        self.icon_19 = QtWidgets.QLabel(self.Archer_9)
        self.icon_19.setEnabled(True)
        self.icon_19.setGeometry(QtCore.QRect(20, 10, 35, 35))
        self.icon_19.setMinimumSize(QtCore.QSize(35, 35))
        self.icon_19.setMaximumSize(QtCore.QSize(35, 33))
        self.icon_19.setText("")
        self.icon_19.setPixmap(QtGui.QPixmap("../../../../../../../../OneDrive/Documents/GitHub/AOE2DE_CivCreator/Images/TechTree/Archer.png"))
        self.icon_19.setScaledContents(True)
        self.icon_19.setObjectName("icon_19")
        self.horizontalLayout_17.addWidget(self.Archer_9)
        spacerItem2 = QtWidgets.QSpacerItem(4792, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_17.addItem(spacerItem2)
        self.verticalLayout_9.addWidget(self.frame_18)
        self.frame_19 = QtWidgets.QFrame(self.frame_17)
        self.frame_19.setEnabled(True)
        self.frame_19.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_19.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_19.setObjectName("frame_19")
        self.horizontalLayout_15 = QtWidgets.QHBoxLayout(self.frame_19)
        self.horizontalLayout_15.setContentsMargins(5, 0, 5, 0)
        self.horizontalLayout_15.setSpacing(10)
        self.horizontalLayout_15.setObjectName("horizontalLayout_15")
        self.Archer_8 = QtWidgets.QWidget(self.frame_19)
        self.Archer_8.setEnabled(True)
        self.Archer_8.setMinimumSize(QtCore.QSize(75, 75))
        self.Archer_8.setMaximumSize(QtCore.QSize(75, 75))
        self.Archer_8.setStyleSheet("")
        self.Archer_8.setObjectName("Archer_8")
        self.background_18 = QtWidgets.QLabel(self.Archer_8)
        self.background_18.setEnabled(True)
        self.background_18.setGeometry(QtCore.QRect(0, 0, 75, 75))
        self.background_18.setMinimumSize(QtCore.QSize(75, 75))
        self.background_18.setMaximumSize(QtCore.QSize(75, 75))
        self.background_18.setAutoFillBackground(False)
        self.background_18.setText("")
        self.background_18.setPixmap(QtGui.QPixmap("../../../../../../../../OneDrive/Documents/GitHub/AOE2DE_CivCreator/Images/TechTree/building.png"))
        self.background_18.setScaledContents(True)
        self.background_18.setObjectName("background_18")
        self.text_18 = QtWidgets.QLabel(self.Archer_8)
        self.text_18.setEnabled(True)
        self.text_18.setGeometry(QtCore.QRect(10, 46, 55, 16))
        font = QtGui.QFont()
        font.setPointSize(5)
        self.text_18.setFont(font)
        self.text_18.setStyleSheet("color: rgb(255, 255, 255);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.text_18.setAlignment(QtCore.Qt.AlignCenter)
        self.text_18.setWordWrap(True)
        self.text_18.setObjectName("text_18")
        self.icon_18 = QtWidgets.QLabel(self.Archer_8)
        self.icon_18.setEnabled(True)
        self.icon_18.setGeometry(QtCore.QRect(20, 10, 35, 35))
        self.icon_18.setMinimumSize(QtCore.QSize(35, 35))
        self.icon_18.setMaximumSize(QtCore.QSize(35, 33))
        self.icon_18.setText("")
        self.icon_18.setPixmap(QtGui.QPixmap("../../../../../../../../OneDrive/Documents/GitHub/AOE2DE_CivCreator/Images/TechTree/Archer.png"))
        self.icon_18.setScaledContents(True)
        self.icon_18.setObjectName("icon_18")
        self.horizontalLayout_15.addWidget(self.Archer_8)
        spacerItem3 = QtWidgets.QSpacerItem(4792, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_15.addItem(spacerItem3)
        self.verticalLayout_9.addWidget(self.frame_19)
        self.horizontalLayout_4.addWidget(self.frame_17)
        self.verticalLayout_8.addWidget(self.frame_9)
        self.frame_11 = QtWidgets.QFrame(self.frame_8)
        self.frame_11.setMaximumSize(QtCore.QSize(16777215, 150))
        self.frame_11.setStyleSheet("background-color: rgb(217, 217, 217);")
        self.frame_11.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_11.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_11.setObjectName("frame_11")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout(self.frame_11)
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_5.setSpacing(0)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.frame_20 = QtWidgets.QFrame(self.frame_11)
        self.frame_20.setMinimumSize(QtCore.QSize(100, 100))
        self.frame_20.setMaximumSize(QtCore.QSize(100, 100))
        self.frame_20.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_20.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_20.setObjectName("frame_20")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.frame_20)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.label_3 = QtWidgets.QLabel(self.frame_20)
        self.label_3.setMinimumSize(QtCore.QSize(85, 65))
        self.label_3.setMaximumSize(QtCore.QSize(75, 60))
        self.label_3.setText("")
        self.label_3.setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/castle_age.png"))
        self.label_3.setScaledContents(True)
        self.label_3.setObjectName("label_3")
        self.gridLayout_3.addWidget(self.label_3, 0, 0, 1, 1)
        self.horizontalLayout_5.addWidget(self.frame_20)
        self.frame_21 = QtWidgets.QFrame(self.frame_11)
        self.frame_21.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_21.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_21.setObjectName("frame_21")
        self.verticalLayout_10 = QtWidgets.QVBoxLayout(self.frame_21)
        self.verticalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_10.setSpacing(0)
        self.verticalLayout_10.setObjectName("verticalLayout_10")
        self.frame_22 = QtWidgets.QFrame(self.frame_21)
        self.frame_22.setMaximumSize(QtCore.QSize(16777215, 80))
        self.frame_22.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_22.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_22.setObjectName("frame_22")
        self.horizontalLayout_14 = QtWidgets.QHBoxLayout(self.frame_22)
        self.horizontalLayout_14.setContentsMargins(5, 0, 5, 0)
        self.horizontalLayout_14.setSpacing(10)
        self.horizontalLayout_14.setObjectName("horizontalLayout_14")
        self.Archer_7 = QtWidgets.QWidget(self.frame_22)
        self.Archer_7.setEnabled(True)
        self.Archer_7.setMinimumSize(QtCore.QSize(75, 75))
        self.Archer_7.setMaximumSize(QtCore.QSize(75, 75))
        self.Archer_7.setStyleSheet("")
        self.Archer_7.setObjectName("Archer_7")
        self.background_17 = QtWidgets.QLabel(self.Archer_7)
        self.background_17.setEnabled(True)
        self.background_17.setGeometry(QtCore.QRect(0, 0, 75, 75))
        self.background_17.setMinimumSize(QtCore.QSize(75, 75))
        self.background_17.setMaximumSize(QtCore.QSize(75, 75))
        self.background_17.setAutoFillBackground(False)
        self.background_17.setText("")
        self.background_17.setPixmap(QtGui.QPixmap("../../../../../../../../OneDrive/Documents/GitHub/AOE2DE_CivCreator/Images/TechTree/building.png"))
        self.background_17.setScaledContents(True)
        self.background_17.setObjectName("background_17")
        self.text_17 = QtWidgets.QLabel(self.Archer_7)
        self.text_17.setEnabled(True)
        self.text_17.setGeometry(QtCore.QRect(10, 46, 55, 16))
        font = QtGui.QFont()
        font.setPointSize(5)
        self.text_17.setFont(font)
        self.text_17.setStyleSheet("color: rgb(255, 255, 255);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.text_17.setAlignment(QtCore.Qt.AlignCenter)
        self.text_17.setWordWrap(True)
        self.text_17.setObjectName("text_17")
        self.icon_17 = QtWidgets.QLabel(self.Archer_7)
        self.icon_17.setEnabled(True)
        self.icon_17.setGeometry(QtCore.QRect(20, 10, 35, 35))
        self.icon_17.setMinimumSize(QtCore.QSize(35, 35))
        self.icon_17.setMaximumSize(QtCore.QSize(35, 33))
        self.icon_17.setText("")
        self.icon_17.setPixmap(QtGui.QPixmap("../../../../../../../../OneDrive/Documents/GitHub/AOE2DE_CivCreator/Images/TechTree/Archer.png"))
        self.icon_17.setScaledContents(True)
        self.icon_17.setObjectName("icon_17")
        self.horizontalLayout_14.addWidget(self.Archer_7)
        spacerItem4 = QtWidgets.QSpacerItem(4792, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_14.addItem(spacerItem4)
        self.verticalLayout_10.addWidget(self.frame_22)
        self.frame_23 = QtWidgets.QFrame(self.frame_21)
        self.frame_23.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_23.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_23.setObjectName("frame_23")
        self.horizontalLayout_13 = QtWidgets.QHBoxLayout(self.frame_23)
        self.horizontalLayout_13.setContentsMargins(5, 0, 5, 0)
        self.horizontalLayout_13.setSpacing(10)
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        self.Archer_6 = QtWidgets.QWidget(self.frame_23)
        self.Archer_6.setEnabled(True)
        self.Archer_6.setMinimumSize(QtCore.QSize(75, 75))
        self.Archer_6.setMaximumSize(QtCore.QSize(75, 75))
        self.Archer_6.setStyleSheet("")
        self.Archer_6.setObjectName("Archer_6")
        self.background_16 = QtWidgets.QLabel(self.Archer_6)
        self.background_16.setEnabled(True)
        self.background_16.setGeometry(QtCore.QRect(0, 0, 75, 75))
        self.background_16.setMinimumSize(QtCore.QSize(75, 75))
        self.background_16.setMaximumSize(QtCore.QSize(75, 75))
        self.background_16.setAutoFillBackground(False)
        self.background_16.setText("")
        self.background_16.setPixmap(QtGui.QPixmap("../../../../../../../../OneDrive/Documents/GitHub/AOE2DE_CivCreator/Images/TechTree/building.png"))
        self.background_16.setScaledContents(True)
        self.background_16.setObjectName("background_16")
        self.text_16 = QtWidgets.QLabel(self.Archer_6)
        self.text_16.setEnabled(True)
        self.text_16.setGeometry(QtCore.QRect(10, 46, 55, 16))
        font = QtGui.QFont()
        font.setPointSize(5)
        self.text_16.setFont(font)
        self.text_16.setStyleSheet("color: rgb(255, 255, 255);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.text_16.setAlignment(QtCore.Qt.AlignCenter)
        self.text_16.setWordWrap(True)
        self.text_16.setObjectName("text_16")
        self.icon_16 = QtWidgets.QLabel(self.Archer_6)
        self.icon_16.setEnabled(True)
        self.icon_16.setGeometry(QtCore.QRect(20, 10, 35, 35))
        self.icon_16.setMinimumSize(QtCore.QSize(35, 35))
        self.icon_16.setMaximumSize(QtCore.QSize(35, 33))
        self.icon_16.setText("")
        self.icon_16.setPixmap(QtGui.QPixmap("../../../../../../../../OneDrive/Documents/GitHub/AOE2DE_CivCreator/Images/TechTree/Archer.png"))
        self.icon_16.setScaledContents(True)
        self.icon_16.setObjectName("icon_16")
        self.horizontalLayout_13.addWidget(self.Archer_6)
        spacerItem5 = QtWidgets.QSpacerItem(4792, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_13.addItem(spacerItem5)
        self.verticalLayout_10.addWidget(self.frame_23)
        self.horizontalLayout_5.addWidget(self.frame_21)
        self.verticalLayout_8.addWidget(self.frame_11)
        self.frame_12 = QtWidgets.QFrame(self.frame_8)
        self.frame_12.setMaximumSize(QtCore.QSize(16777215, 150))
        self.frame_12.setStyleSheet("background-color: rgb(177, 177, 177);")
        self.frame_12.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_12.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_12.setObjectName("frame_12")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout(self.frame_12)
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_6.setSpacing(0)
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.frame_24 = QtWidgets.QFrame(self.frame_12)
        self.frame_24.setMinimumSize(QtCore.QSize(100, 100))
        self.frame_24.setMaximumSize(QtCore.QSize(100, 100))
        self.frame_24.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_24.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_24.setObjectName("frame_24")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.frame_24)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.label_4 = QtWidgets.QLabel(self.frame_24)
        self.label_4.setMinimumSize(QtCore.QSize(85, 65))
        self.label_4.setMaximumSize(QtCore.QSize(75, 60))
        self.label_4.setText("")
        self.label_4.setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/imperial_age.png"))
        self.label_4.setScaledContents(True)
        self.label_4.setObjectName("label_4")
        self.gridLayout_4.addWidget(self.label_4, 0, 0, 1, 1)
        self.horizontalLayout_6.addWidget(self.frame_24)
        self.widget = QtWidgets.QWidget(self.frame_12)
        self.widget.setObjectName("widget")
        self.verticalLayout_11 = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout_11.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_11.setSpacing(0)
        self.verticalLayout_11.setObjectName("verticalLayout_11")
        self.frame_25 = QtWidgets.QFrame(self.widget)
        self.frame_25.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_25.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_25.setObjectName("frame_25")
        self.horizontalLayout_11 = QtWidgets.QHBoxLayout(self.frame_25)
        self.horizontalLayout_11.setContentsMargins(5, 0, 5, 0)
        self.horizontalLayout_11.setSpacing(10)
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        self.Archer_4 = QtWidgets.QWidget(self.frame_25)
        self.Archer_4.setEnabled(True)
        self.Archer_4.setMinimumSize(QtCore.QSize(75, 75))
        self.Archer_4.setMaximumSize(QtCore.QSize(75, 75))
        self.Archer_4.setStyleSheet("")
        self.Archer_4.setObjectName("Archer_4")
        self.background_14 = QtWidgets.QLabel(self.Archer_4)
        self.background_14.setEnabled(True)
        self.background_14.setGeometry(QtCore.QRect(0, 0, 75, 75))
        self.background_14.setMinimumSize(QtCore.QSize(75, 75))
        self.background_14.setMaximumSize(QtCore.QSize(75, 75))
        self.background_14.setAutoFillBackground(False)
        self.background_14.setText("")
        self.background_14.setPixmap(QtGui.QPixmap("../../../../../../../../OneDrive/Documents/GitHub/AOE2DE_CivCreator/Images/TechTree/building.png"))
        self.background_14.setScaledContents(True)
        self.background_14.setObjectName("background_14")
        self.text_14 = QtWidgets.QLabel(self.Archer_4)
        self.text_14.setEnabled(True)
        self.text_14.setGeometry(QtCore.QRect(10, 46, 55, 16))
        font = QtGui.QFont()
        font.setPointSize(5)
        self.text_14.setFont(font)
        self.text_14.setStyleSheet("color: rgb(255, 255, 255);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.text_14.setAlignment(QtCore.Qt.AlignCenter)
        self.text_14.setWordWrap(True)
        self.text_14.setObjectName("text_14")
        self.icon_14 = QtWidgets.QLabel(self.Archer_4)
        self.icon_14.setEnabled(True)
        self.icon_14.setGeometry(QtCore.QRect(20, 10, 35, 35))
        self.icon_14.setMinimumSize(QtCore.QSize(35, 35))
        self.icon_14.setMaximumSize(QtCore.QSize(35, 33))
        self.icon_14.setText("")
        self.icon_14.setPixmap(QtGui.QPixmap("../../../../../../../../OneDrive/Documents/GitHub/AOE2DE_CivCreator/Images/TechTree/Archer.png"))
        self.icon_14.setScaledContents(True)
        self.icon_14.setObjectName("icon_14")
        self.horizontalLayout_11.addWidget(self.Archer_4)
        spacerItem6 = QtWidgets.QSpacerItem(4794, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_11.addItem(spacerItem6)
        self.verticalLayout_11.addWidget(self.frame_25)
        self.frame_26 = QtWidgets.QFrame(self.widget)
        self.frame_26.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_26.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_26.setObjectName("frame_26")
        self.horizontalLayout_12 = QtWidgets.QHBoxLayout(self.frame_26)
        self.horizontalLayout_12.setContentsMargins(5, 0, 5, 0)
        self.horizontalLayout_12.setSpacing(10)
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        self.Archer_5 = QtWidgets.QWidget(self.frame_26)
        self.Archer_5.setEnabled(True)
        self.Archer_5.setMinimumSize(QtCore.QSize(75, 75))
        self.Archer_5.setMaximumSize(QtCore.QSize(75, 75))
        self.Archer_5.setStyleSheet("")
        self.Archer_5.setObjectName("Archer_5")
        self.background_15 = QtWidgets.QLabel(self.Archer_5)
        self.background_15.setEnabled(True)
        self.background_15.setGeometry(QtCore.QRect(0, 0, 75, 75))
        self.background_15.setMinimumSize(QtCore.QSize(75, 75))
        self.background_15.setMaximumSize(QtCore.QSize(75, 75))
        self.background_15.setAutoFillBackground(False)
        self.background_15.setText("")
        self.background_15.setPixmap(QtGui.QPixmap("../../../../../../../../OneDrive/Documents/GitHub/AOE2DE_CivCreator/Images/TechTree/building.png"))
        self.background_15.setScaledContents(True)
        self.background_15.setObjectName("background_15")
        self.text_15 = QtWidgets.QLabel(self.Archer_5)
        self.text_15.setEnabled(True)
        self.text_15.setGeometry(QtCore.QRect(10, 46, 55, 16))
        font = QtGui.QFont()
        font.setPointSize(5)
        self.text_15.setFont(font)
        self.text_15.setStyleSheet("color: rgb(255, 255, 255);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.text_15.setAlignment(QtCore.Qt.AlignCenter)
        self.text_15.setWordWrap(True)
        self.text_15.setObjectName("text_15")
        self.icon_15 = QtWidgets.QLabel(self.Archer_5)
        self.icon_15.setEnabled(True)
        self.icon_15.setGeometry(QtCore.QRect(20, 10, 35, 35))
        self.icon_15.setMinimumSize(QtCore.QSize(35, 35))
        self.icon_15.setMaximumSize(QtCore.QSize(35, 33))
        self.icon_15.setText("")
        self.icon_15.setPixmap(QtGui.QPixmap("../../../../../../../../OneDrive/Documents/GitHub/AOE2DE_CivCreator/Images/TechTree/Archer.png"))
        self.icon_15.setScaledContents(True)
        self.icon_15.setObjectName("icon_15")
        self.horizontalLayout_12.addWidget(self.Archer_5)
        spacerItem7 = QtWidgets.QSpacerItem(4794, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_12.addItem(spacerItem7)
        self.verticalLayout_11.addWidget(self.frame_26)
        self.horizontalLayout_6.addWidget(self.widget)
        self.verticalLayout_8.addWidget(self.frame_12)
        self.verticalLayout_6.addWidget(self.frame_8)
        self.horizontalLayout_2.addWidget(self.frame_3)
        self.scrollArea_2.setWidget(self.scrollAreaWidgetContents_2)
        self.horizontalLayout_16.addWidget(self.scrollArea_2)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 612, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionNew_Project = QtWidgets.QAction(MainWindow)
        self.actionNew_Project.setObjectName("actionNew_Project")
        self.actionOpen_Project = QtWidgets.QAction(MainWindow)
        self.actionOpen_Project.setObjectName("actionOpen_Project")
        self.actionSave_Project = QtWidgets.QAction(MainWindow)
        self.actionSave_Project.setObjectName("actionSave_Project")
        self.actionQuit = QtWidgets.QAction(MainWindow)
        self.actionQuit.setObjectName("actionQuit")
        self.menuFile.addAction(self.actionNew_Project)
        self.actionNew_Project.triggered.connect(new_project) # New project
        self.menuFile.addAction(self.actionOpen_Project)
        self.actionOpen_Project.triggered.connect(lambda: open_project('')) # Open project
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionSave_Project)
        self.actionSave_Project.triggered.connect(save_project) # Save project
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionQuit)
        self.actionQuit.triggered.connect(quit_application) # Quit
        self.menubar.addAction(self.menuFile.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        # Connect the dropdown to the function
        self.civilisation_dropdown.currentIndexChanged.connect(self.on_civilisation_dropdown_changed)

    def on_civilisation_dropdown_changed(self):
        changed_civilisation_dropdown()

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.civilisation_dropdown.setItemText(0, _translate("MainWindow", "Britons"))
        self.civilisation_dropdown.setItemText(1, _translate("MainWindow", "Franks"))
        self.architecture_label.setText(_translate("MainWindow", "Architecture"))
        self.language_label.setText(_translate("MainWindow", "Language"))
        self.language_dropdown.setMaxVisibleItems(10)
        self.civilisation_description_label.setText(_translate("MainWindow", ""))
        self.text.setText(_translate("MainWindow", "Elite Elephant Archer"))
        self.text_10.setText(_translate("MainWindow", "Elite Elephant Archer"))
        self.text_19.setText(_translate("MainWindow", "Elite Elephant Archer"))
        self.text_18.setText(_translate("MainWindow", "Elite Elephant Archer"))
        self.text_17.setText(_translate("MainWindow", "Elite Elephant Archer"))
        self.text_16.setText(_translate("MainWindow", "Elite Elephant Archer"))
        self.text_14.setText(_translate("MainWindow", "Elite Elephant Archer"))
        self.text_15.setText(_translate("MainWindow", "Elite Elephant Archer"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.actionNew_Project.setText(_translate("MainWindow", "New Project..."))
        self.actionOpen_Project.setText(_translate("MainWindow", "Open Project..."))
        self.actionSave_Project.setText(_translate("MainWindow", "Save Project"))
        self.actionQuit.setText(_translate("MainWindow", "Quit"))

# Civilisation object
class Civilisation:
    def __init__(self, index: int, name: str, true_name: str, description: str, name_id: str, desc_id: str, image_path: str, units: dict[str, int] = None):
        self.index = index
        self.name = name
        self.true_name = true_name
        self.description = description
        self.units = {}
        self.name_id = name_id
        self.desc_id = desc_id
        self.image_path = image_path

# All important file paths
global ORIGINAL_FOLDER
global MOD_FOLDER
global PROJECT_FILE
global ORIGINAL_STRINGS_FILE
global MODDED_STRINGS_FILE
global CIV_TECH_TREES_FILE
global CIV_IMAGE_FOLDER
global DATA_FILE_DAT
global METADATA

# Set variables
currently_selected_civilisation = ''

class NewProjectWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Create New Project")

        # Create layout
        layout = QVBoxLayout()

        # Project Name Label and Input
        project_name_label = QLabel("Project Name")
        self.project_name_input = QLineEdit()
        layout.addWidget(project_name_label)
        layout.addWidget(self.project_name_input)

        # Original AoE2DE Folder
        aoe_folder_label = QLabel("Original AoE2DE Folder")
        self.aoe_folder_input = QLineEdit()
        aoe_folder_browse = QPushButton("Browse")
        aoe_folder_browse.clicked.connect(self.browse_aoe_folder)

        aoe_folder_layout = QHBoxLayout()
        aoe_folder_layout.addWidget(self.aoe_folder_input)
        aoe_folder_layout.addWidget(aoe_folder_browse)

        layout.addWidget(aoe_folder_label)
        layout.addLayout(aoe_folder_layout)

        # Local Mods Folder
        mods_folder_label = QLabel("Local Mods Folder")
        self.mods_folder_input = QLineEdit()
        mods_folder_browse = QPushButton("Browse")
        mods_folder_browse.clicked.connect(self.browse_mods_folder)

        mods_folder_layout = QHBoxLayout()
        mods_folder_layout.addWidget(self.mods_folder_input)
        mods_folder_layout.addWidget(mods_folder_browse)

        layout.addWidget(mods_folder_label)
        layout.addLayout(mods_folder_layout)

        # Create Project Button
        create_project_button = QPushButton("Create Project")
        create_project_button.clicked.connect(self.create_project)
        layout.addWidget(create_project_button)

        self.setLayout(layout)

    def browse_aoe_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, 'Select AoE2DE Folder')
        if folder_path:
            self.aoe_folder_input.setText(folder_path)

    def browse_mods_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Mods Folder')
        if folder_path:
            self.mods_folder_input.setText(folder_path)

    def create_project(self):
        project_name = self.project_name_input.text()
        aoe_folder = self.aoe_folder_input.text()
        mods_folder = self.mods_folder_input.text()

        if not project_name:
            messagebox.showerror("Error", "Project Name cannot be empty.")
            return

        try:
            # Create the project folder
            os.makedirs(project_name, exist_ok=True)
            project_file_path = os.path.join(project_name, f"{project_name}.txt")
            
            # Create a text file inside the folder and write the data
            with open(project_file_path, 'w') as project_file:
                project_file.write(f"AoE2DE Folder: {aoe_folder}\n")
                project_file.write(f"Mods Folder: {mods_folder}\n")

            messagebox.showinfo("Success", f"Project '{project_name}' created successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create project: {str(e)}")

new_project_window = None  # Global variable to keep the window alive
def new_project():
    global new_project_window
    new_project_window = NewProjectWindow()  # Store in a global variable
    new_project_window.show()

# Open project
def open_project(path):
    global civilisation_objects  # Ensure we are modifying the global list
    civilisation_objects = []  # Reset civ list before loading

    if path == '':
        PROJECT_FILE = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    else:
        PROJECT_FILE = path

    if PROJECT_FILE:
        with open(PROJECT_FILE, 'r') as file:
            # Set all the file and folder pathways
            lines = file.read().splitlines()
            MOD_FOLDER = lines[1]
            DATA_FILE_DAT = rf'{MOD_FOLDER}\resources\_common\dat\empires2_x2_p1.dat'
            #DATA_FILE_JSON = GenieObjectContainer(DATA_FILE_DAT)
            ORIGINAL_FOLDER = lines[0]
            ORIGINAL_STRINGS_FILE = rf'{MOD_FOLDER}\resources\en\strings\key-value\key-value-strings-utf8.txt'
            MODDED_STRINGS_FILE = rf'{MOD_FOLDER}\resources\en\strings\key-value\key-value-modded-strings-utf8.txt'
            CIV_TECH_TREES_FILE = rf'{MOD_FOLDER}\resources\_common\dat\civTechTrees.json'
            CIV_IMAGE_FOLDER = rf'{MOD_FOLDER}\widgetui\textures\menu\civs'
            METADATA = DatFile.parse(DATA_FILE_DAT)
            #METADATA.techs[22].resource_costs[0].amount = 50
            #print(METADATA.civs[1].name)
            #print(dir(METADATA.civs[1]))
            #METADATA.civs[1].icon_set = 2
            #METADATA.civs[1].graphics_set = 2
            #METADATA.civs[1].sound_set = METADATA.civs[2].sound_set
            #METADATA.save(DATA_FILE_DAT)

        # Import civilisations and create objects for them with unit values
        with open(CIV_TECH_TREES_FILE, 'r', encoding='utf-8') as file:
            lines = file.read().splitlines()
            ui.civilisation_dropdown.clear()  # Clear the dropdown before adding new items

            current_civilisation = None  # Initialize this to track the current civilisation

            civ_read_offset = 0
            for line in lines:
                if '\"civ_id\":' in line:
                    # Get the true name of the civilisation
                    true_name = line[16:].replace('"', '').replace(',', '').capitalize()
                    
                    # Get the name ID
                    with open(MODDED_STRINGS_FILE, 'r', encoding='utf-8') as strings_file:
                        strings_lines = strings_file.read().splitlines()

                        # Set the name ID
                        new_name_id = re.sub(r'\D', '', strings_lines[civ_read_offset])

                        # Get the modded name
                        new_name = re.sub(r'[\d\s' + re.escape(string.punctuation) + ']', '', strings_lines[civ_read_offset])
                        ui.civilisation_dropdown.addItem(new_name)

                    # Create Civilisation object
                    magyar_correction = ''
                    if (true_name == 'Magyar'):
                        magyar_correction = 's'
                    current_civilisation = Civilisation(civ_read_offset, new_name, true_name, '', new_name_id, '', rf'{CIV_IMAGE_FOLDER}/{(true_name + magyar_correction).lower()}.png', {})
                    civilisation_objects.append(current_civilisation)
                    civ_read_offset += 1

                elif '\"Name\":' in line and current_civilisation is not None:
                    # Enter new unit name
                    currentUnit = line[18:].replace('"', '').replace(',', '')
                elif '\"Node Status\":' in line and current_civilisation is not None:
                    # Determine the unit's availability status and store it
                    status = line[25:].replace('"', '').replace(',', '')
                    if status == "ResearchedCompleted":
                        current_civilisation.units[currentUnit] = 1
                    elif status == "NotAvailable":
                        current_civilisation.units[currentUnit] = 2
                    elif status == "ResearchRequired":
                        current_civilisation.units[currentUnit] = 3
                ui.on_civilisation_dropdown_changed
        # Get the description and description ID for each civilization
        with open(MODDED_STRINGS_FILE, 'r', encoding='utf-8') as strings_file:
            strings_lines = strings_file.read().splitlines()
            total_civ_count = len(civilisation_objects)
            for i in range(total_civ_count):
                civilisation_objects[i].desc_id = strings_lines[total_civ_count + i][:6]
                civilisation_objects[i].description = strings_lines[total_civ_count + i][7:]

        # Optionally update the UI or perform any other necessary actions here
        ui.update_civs(civilisation_objects)
        changed_civilisation_dropdown()

# Save the current project
def save_project():
    print("saved")

# Save the location of the current project and quit
def quit_application():
    QApplication.quit()

def changed_civilisation_dropdown():
    selected_value = ui.civilisation_dropdown.currentText()  # Get the current text
    for civ in civ_objects:
        if (civ.name == selected_value):
            currently_selected_civilisation = civ
            new_description = civ.description[1:-1].replace('\\n', '\n').replace('<b>', '')
            ui.civilisation_description_label.setText(new_description)
            ui.civilisation_icon_image.setPixmap(QtGui.QPixmap(civ.image_path))

            # DEBUG Set architecture and sound
            if (civ.true_name == 'Britons'):
                ui.language_dropdown.setCurrentIndex(5)
                ui.architecture_dropdown.setCurrentIndex(10)
            elif (civ.true_name == 'Franks'):
                ui.language_dropdown.setCurrentIndex(15)
                ui.architecture_dropdown.setCurrentIndex(10)
            elif (civ.true_name == 'Goths'):
                ui.language_dropdown.setCurrentIndex(17)
                ui.architecture_dropdown.setCurrentIndex(2)
            elif (civ.true_name == 'Teutons'):
                ui.language_dropdown.setCurrentIndex(17)
                ui.architecture_dropdown.setCurrentIndex(2)
            elif (civ.true_name == 'Japanese'):
                ui.language_dropdown.setCurrentIndex(22)
                ui.architecture_dropdown.setCurrentIndex(3)
            elif (civ.true_name == 'Chinese'):
                ui.language_dropdown.setCurrentIndex(11)
                ui.architecture_dropdown.setCurrentIndex(3)
            elif (civ.true_name == 'Byzantines'):
                ui.language_dropdown.setCurrentIndex(9)
                ui.architecture_dropdown.setCurrentIndex(5)
            elif (civ.true_name == 'Persians'):
                ui.language_dropdown.setCurrentIndex(30)
                ui.architecture_dropdown.setCurrentIndex(6)
            elif (civ.true_name == 'Saracens'):
                ui.language_dropdown.setCurrentIndex(34)
                ui.architecture_dropdown.setCurrentIndex(6)
            elif (civ.true_name == 'Turks'):
                ui.language_dropdown.setCurrentIndex(39)
                ui.architecture_dropdown.setCurrentIndex(6)
            elif (civ.true_name == 'Vikings'):
                ui.language_dropdown.setCurrentIndex(41)
                ui.architecture_dropdown.setCurrentIndex(2)
            elif (civ.true_name == 'Mongols'):
                ui.language_dropdown.setCurrentIndex(20)
                ui.architecture_dropdown.setCurrentIndex(3)
            elif (civ.true_name == 'Celts'):
                ui.language_dropdown.setCurrentIndex(10)
                ui.architecture_dropdown.setCurrentIndex(10)
            elif (civ.true_name == 'Spanish'):
                ui.language_dropdown.setCurrentIndex(37)
                ui.architecture_dropdown.setCurrentIndex(5)
            elif (civ.true_name == 'Aztecs'):
                ui.language_dropdown.setCurrentIndex(1)
                ui.architecture_dropdown.setCurrentIndex(7)
            elif (civ.true_name == 'Mayans'):
                ui.language_dropdown.setCurrentIndex(29)
                ui.architecture_dropdown.setCurrentIndex(7)
            elif (civ.true_name == 'Huns'):
                ui.language_dropdown.setCurrentIndex(20)
                ui.architecture_dropdown.setCurrentIndex(2)
            elif (civ.true_name == 'Koreans'):
                ui.language_dropdown.setCurrentIndex(24)
                ui.architecture_dropdown.setCurrentIndex(3)
            elif (civ.true_name == 'Italians'):
                ui.language_dropdown.setCurrentIndex(9)
                ui.architecture_dropdown.setCurrentIndex(5)
            elif (civ.true_name == 'Indians'):
                ui.language_dropdown.setCurrentIndex(19)
                ui.architecture_dropdown.setCurrentIndex(8)
            elif (civ.true_name == 'Incas'):
                ui.language_dropdown.setCurrentIndex(21)
                ui.architecture_dropdown.setCurrentIndex(7)
            elif (civ.true_name == 'Magyar'):
                ui.language_dropdown.setCurrentIndex(26)
                ui.architecture_dropdown.setCurrentIndex(2)
            elif (civ.true_name == 'Slavs'):
                ui.language_dropdown.setCurrentIndex(36)
                ui.architecture_dropdown.setCurrentIndex(4)
            elif (civ.true_name == 'Portuguese'):
                ui.language_dropdown.setCurrentIndex(32)
                ui.architecture_dropdown.setCurrentIndex(5)
            elif (civ.true_name == 'Ethiopians'):
                ui.language_dropdown.setCurrentIndex(14)
                ui.architecture_dropdown.setCurrentIndex(0)
            elif (civ.true_name == 'Malians'):
                ui.language_dropdown.setCurrentIndex(28)
                ui.architecture_dropdown.setCurrentIndex(0)
            elif (civ.true_name == 'Berbers'):
                ui.language_dropdown.setCurrentIndex(3)
                ui.architecture_dropdown.setCurrentIndex(6)
            elif (civ.true_name == 'Khmer'):
                ui.language_dropdown.setCurrentIndex(23)
                ui.architecture_dropdown.setCurrentIndex(9)
            elif (civ.true_name == 'Malay'):
                ui.language_dropdown.setCurrentIndex(27)
                ui.architecture_dropdown.setCurrentIndex(9)
            elif (civ.true_name == 'Burmese'):
                ui.language_dropdown.setCurrentIndex(8)
                ui.architecture_dropdown.setCurrentIndex(9)
            elif (civ.true_name == 'Vietnamese'):
                ui.language_dropdown.setCurrentIndex(40)
                ui.architecture_dropdown.setCurrentIndex(3)
            elif (civ.true_name == 'Bulgarians'):
                ui.language_dropdown.setCurrentIndex(6)
                ui.architecture_dropdown.setCurrentIndex(4)
            elif (civ.true_name == 'Tatars'):
                ui.language_dropdown.setCurrentIndex(38)
                ui.architecture_dropdown.setCurrentIndex(1)
            elif (civ.true_name == 'Cumans'):
                ui.language_dropdown.setCurrentIndex(12)
                ui.architecture_dropdown.setCurrentIndex(1)
            elif (civ.true_name == 'Lithuanians'):
                ui.language_dropdown.setCurrentIndex(25)
                ui.architecture_dropdown.setCurrentIndex(4)
            elif (civ.true_name == 'Burgundians'):
                ui.language_dropdown.setCurrentIndex(7)
                ui.architecture_dropdown.setCurrentIndex(10)
            elif (civ.true_name == 'Sicilians'):
                ui.language_dropdown.setCurrentIndex(35)
                ui.architecture_dropdown.setCurrentIndex(5)
            elif (civ.true_name == 'Poles'):
                ui.language_dropdown.setCurrentIndex(31)
                ui.architecture_dropdown.setCurrentIndex(4)
            elif (civ.true_name == 'Bohemians'):
                ui.language_dropdown.setCurrentIndex(4)
                ui.architecture_dropdown.setCurrentIndex(4)
            elif (civ.true_name == 'Dravidians'):
                ui.language_dropdown.setCurrentIndex(13)
                ui.architecture_dropdown.setCurrentIndex(8)
            elif (civ.true_name == 'Bengalis'):
                ui.language_dropdown.setCurrentIndex(2)
                ui.architecture_dropdown.setCurrentIndex(8)
            elif (civ.true_name == 'Gurjaras'):
                ui.language_dropdown.setCurrentIndex(18)
                ui.architecture_dropdown.setCurrentIndex(8)
            elif (civ.true_name == 'Romans'):
                ui.language_dropdown.setCurrentIndex(33)
                ui.architecture_dropdown.setCurrentIndex(5)
            elif (civ.true_name == 'Armenians'):
                ui.language_dropdown.setCurrentIndex(0)
                ui.architecture_dropdown.setCurrentIndex(5)
            elif (civ.true_name == 'Georgians'):
                ui.language_dropdown.setCurrentIndex(16)
                ui.architecture_dropdown.setCurrentIndex(5)


if __name__ == "__main__":
    # Open main window
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    MainWindow.showMaximized()

    changed_civilisation_dropdown()
    # Exit app
    sys.exit(app.exec_())