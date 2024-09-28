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

def revert_project():
    msg_box = QMessageBox()  # Create the message box
    msg_box.setWindowTitle("Revert Project")
    msg_box.setText("WARNING: Reverting your project will completely erase your mod file and restore it to the default files that are in your AoE2DE file. THIS ACTION IS IRREVERSIBLE.\n\n Do you want to continue?")
    msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

    response = msg_box.exec_()  # Execute the dialog and get the response

    if response == QMessageBox.Ok:
        print("You clicked OK!")

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
            #METADATA = DatFile.parse(DATA_FILE_DAT)

            # Import civilisations and create objects for them with unit values
            with open(CIV_TECH_TREES_FILE, 'r', encoding='utf-8') as file:
                lines = file.read().splitlines()
                MAIN_WINDOW.civilisation_dropdown.clear()  # Clear the dropdown before adding new items

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
                            MAIN_WINDOW.civilisation_dropdown.addItem(new_name)

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
                    update_civilisation_dropdown()
            # Get the description and description ID for each civilization
            with open(MODDED_STRINGS_FILE, 'r', encoding='utf-8') as strings_file:
                strings_lines = strings_file.read().splitlines()
                total_civ_count = len(civilisation_objects)
                for i in range(total_civ_count):
                    civilisation_objects[i].desc_id = strings_lines[total_civ_count + i][:6]
                    civilisation_objects[i].description = strings_lines[total_civ_count + i][7:]

            # Populate inactive civilisations
            MAIN_WINDOW.civilisation_dropdown.insertSeparator(MAIN_WINDOW.civilisation_dropdown.count())
            MAIN_WINDOW.civilisation_dropdown.addItem('New...')

            # Clear dropdowns and populate with new data
            MAIN_WINDOW.architecture_dropdown.clear()
            MAIN_WINDOW.language_dropdown.clear()

            MAIN_WINDOW.architecture_dropdown.addItems(
                ["African", "Central Asian", "Central European", "East Asian", "Eastern European", "Mediterranean",
                 "Middle Eastern", "Mesoamerican", "South Asian", "Southeast Asian", "Western European"])
            MAIN_WINDOW.language_dropdown.addItems(
                ["Armenians [Armenian]", "Aztecs [Nahuatl]", "Bengalis [Shadhu Bengali]", "Berbers [Taqbaylit]",
                 "Bohemians [Czech]", "Britons [Middle English]", "Bulgarians [South Slavic]", "Burgundians [Burgundian]",
                 "Burmese [Burmese]", "Byzantines / Italians [Latin]", "Celts [Gaelic / Irish]", "Chinese [Mandarin]",
                 "Cumans [Cuman]", "Dravidians [Tamil]", "Ethiopians [Amharic]", "Franks [Old French]", "Georgians [Georgian]",
                 "Goths / Teutons [Old German]", "Gurjaras [Gujarati]", "Hindustanis [Hindustani]", "Mongols / Huns [Mongolian]",
                 "Incas [Runasimi / Quechua]", "Japanese [Japanese]", "Khmer [Khmer]", "Koreans [Korean]",
                 "Lithuanians [Lithuanian]", "Magyars [Hungarian]", "Malay [Old Malay]", "Malians [Eastern Maninka]",
                 "Mayans [K'iche']", "Persians [Farsi / Persian]", "Poles [Polish]", "Portuguese [Portuguese]",
                 "Romans [Vulgar Latin]", "Saracens [Arabic]", "Sicilians [Sicilian]", "Slavs [Russian]",
                 "Spanish [Spanish]", "Tatars [Chagatai]", "Turks [Turkish]", "Vietnamese [Vietnamese]", "Vikings [Old Norse]"])
            
            MAIN_WINDOW.architecture_dropdown.insertSeparator(MAIN_WINDOW.architecture_dropdown.count())
            MAIN_WINDOW.language_dropdown.insertSeparator(MAIN_WINDOW.language_dropdown.count())

            MAIN_WINDOW.architecture_dropdown.addItems(["Northeast American", "Nomadic", "Pacific", "South African", "South American"])
            MAIN_WINDOW.language_dropdown.addItems(["Aromanian", "Cantonese", "Catalan", "Javanese", "Lakota", "Mohawk", "Somali", "Thai", "Tibetan", "Zapotec", "Zulu"])

            #MAIN_WINDOW.update_civs(civilisation_objects)
            #MAIN_WINDOW.changed_civilisation_dropdown()
            update_civilisation_dropdown()

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
def eventFilter(self, source, event):
    if source == MAIN_WINDOW.civilisation_dropdown.view().viewport() and event.type() == QtCore.QEvent.MouseButtonPress:
        make_editable_on_right_click(event)
    return super(MainWindow, MainWindow).eventFilter(source, event)

def update_civilisation_dropdown():
    selected_value = MAIN_WINDOW.civilisation_dropdown.currentText()  # Get the current text
    for civ in civilisation_objects:
        if (civ.name == selected_value):
            currently_selected_civilisation = civ
            new_description = civ.description[1:-1].replace('\\n', '\n').replace('<b>', '')
            MAIN_WINDOW.civilisation_description_label.setText(new_description)
            MAIN_WINDOW.civilisation_icon_image.setPixmap(QtGui.QPixmap(civ.image_path))

            # DEBUG Set architecture and sound
            if (civ.true_name == 'Britons'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(5)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(10)
            elif (civ.true_name == 'Franks'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(15)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(10)
            elif (civ.true_name == 'Goths'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(17)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(2)
            elif (civ.true_name == 'Teutons'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(17)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(2)
            elif (civ.true_name == 'Japanese'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(22)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(3)
            elif (civ.true_name == 'Chinese'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(11)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(3)
            elif (civ.true_name == 'Byzantines'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(9)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(5)
            elif (civ.true_name == 'Persians'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(30)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(6)
            elif (civ.true_name == 'Saracens'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(34)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(6)
            elif (civ.true_name == 'Turks'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(39)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(6)
            elif (civ.true_name == 'Vikings'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(41)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(2)
            elif (civ.true_name == 'Mongols'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(20)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(3)
            elif (civ.true_name == 'Celts'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(10)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(10)
            elif (civ.true_name == 'Spanish'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(37)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(5)
            elif (civ.true_name == 'Aztecs'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(1)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(7)
            elif (civ.true_name == 'Mayans'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(29)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(7)
            elif (civ.true_name == 'Huns'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(20)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(2)
            elif (civ.true_name == 'Koreans'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(24)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(3)
            elif (civ.true_name == 'Italians'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(9)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(5)
            elif (civ.true_name == 'Indians'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(19)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(8)
            elif (civ.true_name == 'Incas'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(21)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(7)
            elif (civ.true_name == 'Magyar'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(26)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(2)
            elif (civ.true_name == 'Slavs'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(36)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(4)
            elif (civ.true_name == 'Portuguese'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(32)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(5)
            elif (civ.true_name == 'Ethiopians'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(14)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(0)
            elif (civ.true_name == 'Malians'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(28)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(0)
            elif (civ.true_name == 'Berbers'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(3)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(6)
            elif (civ.true_name == 'Khmer'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(23)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(9)
            elif (civ.true_name == 'Malay'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(27)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(9)
            elif (civ.true_name == 'Burmese'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(8)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(9)
            elif (civ.true_name == 'Vietnamese'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(40)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(3)
            elif (civ.true_name == 'Bulgarians'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(6)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(4)
            elif (civ.true_name == 'Tatars'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(38)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(1)
            elif (civ.true_name == 'Cumans'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(12)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(1)
            elif (civ.true_name == 'Lithuanians'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(25)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(4)
            elif (civ.true_name == 'Burgundians'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(7)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(10)
            elif (civ.true_name == 'Sicilians'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(35)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(5)
            elif (civ.true_name == 'Poles'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(31)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(4)
            elif (civ.true_name == 'Bohemians'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(4)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(4)
            elif (civ.true_name == 'Dravidians'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(13)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(8)
            elif (civ.true_name == 'Bengalis'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(2)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(8)
            elif (civ.true_name == 'Gurjaras'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(18)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(8)
            elif (civ.true_name == 'Romans'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(33)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(5)
            elif (civ.true_name == 'Armenians'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(0)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(5)
            elif (civ.true_name == 'Georgians'):
                MAIN_WINDOW.language_dropdown.setCurrentIndex(16)
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(5)

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

    # Set application images
    MAIN_WINDOW.label.setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/dark_age.png"))
    MAIN_WINDOW.label_2.setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/feudal_age.png"))
    MAIN_WINDOW.label_3.setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/castle_age.png"))
    MAIN_WINDOW.label_4.setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/imperial_age.png"))

    # Show the main window
    MainWindow.showMaximized()

    # Assign functions to navigation buttons
    MAIN_WINDOW.actionNew_Project.triggered.connect(new_project)
    MAIN_WINDOW.actionOpen_Project.triggered.connect(open_project)
    MAIN_WINDOW.actionSave_Project.triggered.connect(save_project)
    MAIN_WINDOW.actionRevert_To_Original.triggered.connect(revert_project)

    # Update the stats when the civilisation dropdown is changed
    MAIN_WINDOW.civilisation_dropdown.currentIndexChanged.connect(update_civilisation_dropdown)

    sys.exit(app.exec_())  # Run the application's event loop