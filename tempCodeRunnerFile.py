from PyQt5 import QtWidgets
from main_window import Ui_MainWindow
from create_project_window import Ui_CreateProjectWindow
from saving_window import Ui_Dialog
import sys
from tkinter import filedialog, messagebox
from PyQt5.QtWidgets import QMessageBox
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

# Constants
civilisation_objects = []
ORIGINAL_FOLDER = ''
MOD_FOLDER = ''

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

def show_error_message(message):
    """Displays an error message using QMessageBox"""
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setText(message)
    msg.setWindowTitle("Error")
    msg.exec_()

def new_project():
    # Show the CreateProjectWindow as a modal dialog
    CreateProjectWindow.exec_()  # This makes the main window unresponsive until the dialog is closed

def open_project():
    global ORIGINAL_FOLDER, MOD_FOLDER

    try:
        # Use QFileDialog to open a modal file explorer
        file_dialog = QtWidgets.QFileDialog(MainWindow)
        file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Text files (*.txt)")
        file_dialog.setWindowTitle("Open Project")
        if file_dialog.exec_():  # Open the dialog in a modal state
            PROJECT_FILE = file_dialog.selectedFiles()[0]  # Get the selected file

            with open(PROJECT_FILE, 'r') as file:
                lines = file.read().splitlines()
                ORIGINAL_FOLDER = lines[0]
                MOD_FOLDER = lines[1]

            DATA_FILE_DAT = rf'{MOD_FOLDER}\resources\_common\dat\empires2_x2_p1.dat'
            MODDED_STRINGS_FILE = rf'{MOD_FOLDER}\resources\en\strings\key-value\key-value-modded-strings-utf8.txt'
            CIV_TECH_TREES_FILE = rf'{MOD_FOLDER}\resources\_common\dat\civTechTrees.json'
            CIV_IMAGE_FOLDER = rf'{MOD_FOLDER}\widgetui\textures\menu\civs'

            # Add more processing logic here if needed

    except Exception as e:
        show_error_message(f"An error occurred: {str(e)}")

# Add an event for right-clicking on the QComboBox to make the text editable
def make_editable_on_right_click(event):
    if event.button() == QtCore.Qt.RightButton:
        MAIN_WINDOW.civilisation_dropdown.setEditable(True)
        MAIN_WINDOW.civilisation_dropdown.lineEdit().setFocus()

# Add an event when clicking away from the QComboBox to make it uneditable again
def make_uneditable_on_focus_out():
    MAIN_WINDOW.civilisation_dropdown.setEditable(False)

# Install an event filter on the QComboBox view to handle right-clicks
class CustomEventFilter(QtCore.QObject):
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            make_editable_on_right_click(event)
        return super().eventFilter(obj, event)

def save_project():
    print("saving")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    CreateProjectWindow = QtWidgets.QDialog()
    SavingWindow = QtWidgets.QDialog()

    # Initialize UI components
    MAIN_WINDOW = Ui_MainWindow()
    MAIN_WINDOW.setupUi(MainWindow)

    CREATE = Ui_CreateProjectWindow()
    CREATE.setupUi(CreateProjectWindow)

    SAVING_WINDOW = Ui_Dialog()
    SAVING_WINDOW.setupUi(SavingWindow)

    # Show the main window
    MainWindow.showMaximized()

    # Assign functions to navigation buttons
    MAIN_WINDOW.actionNew_Project.triggered.connect(new_project)
    MAIN_WINDOW.actionOpen_Project.triggered.connect(open_project)
    MAIN_WINDOW.actionSave_Project.triggered.connect(save_project)

    # Update the stats when the civilisation dropdown is changed
    MAIN_WINDOW.civilisation_dropdown.currentIndexChanged.connect(lambda: print("Changed"))

    # Connect the QComboBox's focus out event to make it uneditable
    MAIN_WINDOW.civilisation_dropdown.lineEdit().editingFinished.connect(make_uneditable_on_focus_out)

    # Install the event filter
    event_filter = CustomEventFilter()
    MAIN_WINDOW.civilisation_dropdown.view().viewport().installEventFilter(event_filter)

    sys.exit(app.exec_())  # Run the application's event loop