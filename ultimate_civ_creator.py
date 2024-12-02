from PyQt5 import QtWidgets
import genieutils.civ
import genieutils.effect
import genieutils.sound
import genieutils.tech
import genieutils.techtree
import genieutils.unit
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
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QFileDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import pyqtSignal
import genieutils
#from genieutils import GenieObjectContainer
from genieutils.datfile import DatFile
import ijson
import pickle
import asyncio
import traceback
import pyperclip
import requests
from PyQt5.QtWidgets import QPlainTextEdit, QApplication
from openai import OpenAI
from PyQt5.QtCore import Qt

# Constants
civilisation_objects = []
CURRENT_CIV_INDEX = -1
tech_tree_blocks = []
ORIGINAL_FOLDER = ''
MOD_FOLDER = ''
DATA = ''
DATA_FILE_DAT = ''
unique_unit = ''
PROJECT_NAME = ''
PROJECT_FILE = ''
SOUND_PROFILES = []
global JSON_DATA

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

# Create a class for the custom combo box for civilizations
class CivilisationDropdown(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super(CivilisationDropdown, self).__init__(parent)
        # Any initialization specific to this dropdown goes here

        self.setEditable(True)  # Initially not editable

    def mousePressEvent(self, event: QtGui.QMouseEvent):
    # Check if the right mouse button was clicked
        print("click")
        if event.button() == QtCore.Qt.RightButton:
            # Do nothing to prevent the dropdown from closing
            print("right click")
            event.ignore()
        else:
            # Default behavior for other mouse clicks (e.g., left-click)
            print("left click")
            super().mousePressEvent(event)
        

# Now replace the existing MAIN_WINDOW.civilisation_dropdown with the new class
class MainApp(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainApp, self).__init__()
        
        # Create an instance of Ui_MainWindow and setup the UI
        self.MAIN_WINDOW = Ui_MainWindow()
        self.MAIN_WINDOW.setupUi(self)  # Pass self (the QMainWindow) as the parent

        # Replace the existing combo box with the new custom class
        self.MAIN_WINDOW.civilisation_dropdown = CivilisationDropdown(self)

        # Set the layout or add this widget to the already existing one
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.MAIN_WINDOW.civilisation_dropdown)
        self.setLayout(layout)  # Set the layout if needed or ensure the widget placement

        # Add some example functionality
        self.MAIN_WINDOW.civilisation_dropdown.currentIndexChanged.connect(self.update_civ_info)

    def update_civ_info(self):
        current_civ = self.MAIN_WINDOW.civilisation_dropdown.currentText()
        print(f"Selected Civilization: {current_civ}")

# DEBUG Show stats of a civ object
def show_civ_object_stats(civ_object):
    print(civ_object.index, civ_object.name)
    print(civ_object.name_id, civ_object.true_name)
    print(civ_object.desc_id, civ_object.description)
    print(civ_object.image_path)
    print(len(civ_object.units))

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
        try:
            # Copy JSON file
            if os.path.exists(rf'{MOD_FOLDER}/resources/_common/dat/civTechTrees.json'):
                os.remove(rf'{MOD_FOLDER}/resources/_common/dat/civTechTrees.json')
                shutil.copy(rf'{ORIGINAL_FOLDER}/\resources\_common\dat\civTechTrees.json', rf'{MOD_FOLDER}/resources/_common/dat/')

            # Copy DAT file
            if os.path.exists(rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat'):
                os.remove(rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat')
                shutil.copy(rf'{ORIGINAL_FOLDER}/\resources\_common\dat\empires2_x2_p1.dat', rf'{MOD_FOLDER}/resources/_common/dat/')

            update_civilisation_dropdown()
        except Exception as e:
            show_error_message("ERROR: " + str(e))  # Convert exception to string

def open_saving_window(title):
    saving_dialog = QtWidgets.QDialog()
    saving_ui = Ui_Dialog()
    saving_ui.setupUi(saving_dialog)
    saving_dialog.setWindowTitle(title)
    saving_ui.progress_bar.setValue(0)
    saving_dialog.setModal(True)  # Make it modal
    saving_dialog.show()

class Worker(QtCore.QObject):
    progress = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)

    def __init__(self, files_to_copy):
        super().__init__()
        self.files_to_copy = files_to_copy
        self._is_running = True  # To handle potential cancellation in the future

    @QtCore.pyqtSlot()
    def run(self):
        total = len(self.files_to_copy)
        for i, source in enumerate(self.files_to_copy, 1):  # 'source' is a string (file path)
            if not self._is_running:
                break

            try:
                # Construct the destination path based on the source path
                dest = os.path.join(MOD_FOLDER, os.path.relpath(source, ORIGINAL_FOLDER))

                if os.path.isdir(source):
                    # Copy the entire directory
                    shutil.copytree(source, dest, dirs_exist_ok=True)
                else:
                    # Ensure destination directory exists
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    # Copy the file
                    shutil.copy2(source, dest)
            except Exception as e:
                self.error.emit(f"Error copying {source} to {dest}: {str(e)}")
                continue

            progress_percent = int((i / total) * 100)
            self.progress.emit(progress_percent)

        self.finished.emit()

def new_project(project_name):
    # File locations
    original_folder_location = ''
    mod_folder_location = ''

    # DEBUG: Default folders
    original_folder_location = rf'C:\Program Files (x86)\Steam\steamapps\common\AoE2DE'
    mod_folder_location = rf'C:\Users\Micheal Q\Games\Age of Empires 2 DE\76561198021486964\mods\local'
    CREATE_WINDOW.lineEdit_2.setText(rf"C:\Program Files (x86)\Steam\steamapps\common\AoE2DE")
    CREATE_WINDOW.lineEdit_3.setText(rf"C:\Users\Micheal Q\Games\Age of Empires 2 DE\76561198021486964\mods\local")

    # Browse for AoE2DE folder
    def browse_original_folder():
        try:
            # Use QFileDialog to open a modal folder explorer with the correct parent
            selected_dir = QtWidgets.QFileDialog.getExistingDirectory(
                CreateProjectWindow,
                "Select Original \"AoE2DE\" Folder",
                "",
                QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks
            )
            if selected_dir:
                CREATE_WINDOW.lineEdit_2.setText(selected_dir)  # Set the folder path in QLineEdit
        except Exception as e:
            show_error_message("ERROR: " + str(e))  # Convert exception to string

    # Browse for mods folder
    def browse_mod_folder():
        try:
            # Use QFileDialog to open a modal folder explorer with the correct parent
            selected_dir = QtWidgets.QFileDialog.getExistingDirectory(
                CreateProjectWindow,
                "Select \"/mods/local\" Folder",
                "",
                QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks
            )
            if selected_dir:
                CREATE_WINDOW.lineEdit_3.setText(selected_dir)  # Set the folder path in QLineEdit
        except Exception as e:
            show_error_message("ERROR: " + str(e))  # Convert exception to string

    def create_project_button():
        # Get project name and folder paths (it may seem redundant but it's to prevent failed creation from wiping the current project's files)
        project_name = CREATE_WINDOW.lineEdit.text()
        original_folder_location = CREATE_WINDOW.lineEdit_2.text()
        mod_folder_location = CREATE_WINDOW.lineEdit_3.text()

        # Check that all fields are filled
        if (project_name == ''):
            show_error_message("ERROR: Project name cannot be blank.")
            return
        elif (original_folder_location == ''):
            show_error_message("ERROR: Original AoE2DE folder path cannot be blank.")
            return
        elif (mod_folder_location == ''):
            show_error_message("ERROR: Mods folder path cannot be blank.")
            return

        # Try to create a new project
        try:
            # Create the project folder inside the mod path (with the project name)
            PROJECT_NAME = project_name
            ORIGINAL_FOLDER = original_folder_location
            MOD_FOLDER = os.path.join(mod_folder_location, PROJECT_NAME)
            os.makedirs(MOD_FOLDER, exist_ok=True)
            os.chdir(MOD_FOLDER)

            # Write the project file
            with open(f'{PROJECT_NAME}.txt', 'w') as file:
                file.write(rf"{original_folder_location}")
                file.write('\n')
                file.write(rf"{mod_folder_location}\{PROJECT_NAME}")

            files_to_copy = [
                'resources/_common/dat/civilizations.json', 
                'resources/_common/dat/civTechTrees.json', 
                'resources/_common/dat/empires2_x2_p1.dat', 
                'resources/_common/wpfg/resources/civ_techtree',
                'resources/_common/wpfg/resources/uniticons',
                'resources/en/strings/key-value/key-value-strings-utf8.txt',
                'resources/en/strings/key-value/key-value-modded-strings-utf8.txt',
                'widgetui/textures/menu/civs'
                ]
            
            for item in files_to_copy:
                # Construct the full paths for the source and destination
                source_path = os.path.join(ORIGINAL_FOLDER, item)
                dest_path = os.path.join(MOD_FOLDER, item)

                # Check if the source path exists
                if os.path.exists(source_path):
                    # If it's a file, copy it
                    if os.path.isfile(source_path):
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        shutil.copy2(source_path, dest_path)

                    # If it's a directory, copy it recursively
                    elif os.path.isdir(source_path):
                        shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                else:
                    print(f"Warning: {source_path} does not exist.")

            # Constant files
            CIV_TECH_TREES_FILE = rf'{MOD_FOLDER}/resources/_common/dat/civTechTrees.json'
            ORIGINAL_STRINGS_FILE = rf'{MOD_FOLDER}/resources/en/strings/key-value/key-value-strings-utf8.txt'
            MODDED_STRINGS_FILE = rf'{MOD_FOLDER}/resources/en/strings/key-value/key-value-modded-strings-utf8.txt'
            CIV_IMAGE_FOLDER = rf'{MOD_FOLDER}/widgetui/textures/menu/civs'

            # Import civilisations and create objects for them with unit values
            with open(CIV_TECH_TREES_FILE, 'r', encoding='utf-8') as file:
                lines = file.read().splitlines()
                MAIN_WINDOW.civilisation_dropdown.clear()  # Clear the dropdown before adding new items

                current_civilisation = None  # Initialize this to track the current civilisation

                civ_read_offset = 0
                found_index = 0
                for line in lines:
                    if '\"civ_id\":' in line:
                        # Get the true name of the civilisation
                        true_name = line[16:].replace('"', '').replace(',', '').capitalize()

                        # Write names to the string file
                        line_to_paste = 'error'
                        new_name = ''
                        new_name_id = ''
                        
                        # Write new lines to modded strings file
                        with open(ORIGINAL_STRINGS_FILE, 'r', encoding='utf-8') as original_strings_file:
                            lines = original_strings_file.readlines()
                            
                            if (found_index == 0):
                                for idx, line in enumerate(lines):
                                    if rf'{10271 + civ_read_offset} ' in line:
                                        # Paste the new line in the modded strings file
                                        line_to_paste = line

                                        # Get the modded name
                                        new_name = re.sub(r'[\d\s' + re.escape(string.punctuation) + ']', '', lines[civ_read_offset])

                                        # Get the name ID
                                        new_name_id = 10271 + civ_read_offset

                                        # Mark the index where the item was found
                                        found_index = idx
                                        break
                            else:
                                if rf'{10271 + civ_read_offset} ' in lines[found_index + civ_read_offset]:
                                    # Paste the new line in the modded strings file
                                    line_to_paste = lines[found_index + civ_read_offset]

                                    # Get the modded name
                                    new_name = re.sub(r'[\d\s' + re.escape(string.punctuation) + ']', '', lines[civ_read_offset])

                                    # Get the name ID
                                    new_name_id = 10271 + civ_read_offset

                        # Determine whether to overwrite the file or just append it
                        if (civ_read_offset == 0):
                            write_mode = 'w'
                        else:
                            write_mode = 'a'

                        # Write names to the string file
                        with open(MODDED_STRINGS_FILE, write_mode, encoding='utf-8') as modded_strings_file:
                            modded_strings_file.write(line_to_paste)

                        # Add the civilisation to the dropdown
                        MAIN_WINDOW.civilisation_dropdown.addItem(new_name)

                        # Create Civilisation object
                        magyar_correction = ''
                        if (true_name == 'Magyar'):
                            magyar_correction = 's'
                        current_civilisation = Civilisation(civ_read_offset, new_name, true_name, '', new_name_id, '', rf'{CIV_IMAGE_FOLDER}/{(true_name + magyar_correction).lower()}.png', {})
                        civilisation_objects.append(current_civilisation)

                        # Increae the civ read offset
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
                    #MAIN_WINDOW.on_civilisation_dropdown_changed

            # Get the description and description ID for each civilization
            with open(ORIGINAL_STRINGS_FILE, 'r', encoding='utf-8') as original_strings_file:
                lines = original_strings_file.readlines()
                civ_read_offset = 0

                for line in enumerate(lines):
                    if rf'{120150 + civ_read_offset} ' in line:
                        # Paste the new line in the modded strings file

                        line_to_paste = line
                        # Get the modded description
                        civilisation_objects[civ_read_offset].description = re.sub(r'[\d\s' + re.escape(string.punctuation) + ']', '', lines[civ_read_offset])

                        # Get the desc ID
                        civilisation_objects[civ_read_offset].desc_id = 120150 + civ_read_offset

                        show_civ_object_stats(civilisation_objects[civ_read_offset])

            # Open the Saving Window
            saving_dialog = QtWidgets.QDialog()
            saving_ui = Ui_Dialog()
            saving_ui.setupUi(saving_dialog)
            saving_dialog.setWindowTitle("Saving Project")
            saving_ui.progress_bar.setValue(0)
            saving_dialog.setModal(True)  # Make it modal
            saving_dialog.show()

            # Create a QThread
            thread = QtCore.QThread()

            # Create a Worker instance
            worker = Worker(files_to_copy)

            # Move the worker to the thread
            worker.moveToThread(thread)

            # Connect signals and slots
            thread.started.connect(worker.run)
            worker.progress.connect(saving_ui.progress_bar.setValue)
            worker.finished.connect(saving_dialog.accept)  # Close the dialog when done
            worker.finished.connect(thread.quit)
            worker.finished.connect(worker.deleteLater)
            thread.finished.connect(thread.deleteLater)
            worker.error.connect(show_error_message)  # Connect error signal to error handler

            # Start the thread
            thread.start()

            # Ensure the thread is safely stopped when the application closes
            app.aboutToQuit.connect(thread.quit)
            app.aboutToQuit.connect(thread.wait)

            # Close create project window
            MainWindow.setWindowTitle(f"Talofa - {project_name}")
            open_project(MOD_FOLDER)
            CreateProjectWindow.close()

        except Exception as e:
            show_error_message("ERROR: " + str(e))

    # Attach the functions to the buttons
    CREATE_WINDOW.pushButton_2.clicked.connect(browse_original_folder)
    CREATE_WINDOW.pushButton_3.clicked.connect(browse_mod_folder)
    CREATE_WINDOW.pushButton.clicked.connect(create_project_button)

    # DEBUG Randomise name if lineEdit is empty
    if CREATE_WINDOW.lineEdit.text() == "":  # <-- Add parentheses to call the method
        project_name = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(5))
        CREATE_WINDOW.lineEdit.setText(project_name)  # <-- Optionally set the randomized name in the UI

    # Show the CreateProjectWindow as a modal dialog without calling show()
    CreateProjectWindow.exec_()  # This makes the dialog modal and prevents the main window from being responsive until closed

def open_project(path = None):
    global ORIGINAL_FOLDER, MOD_FOLDER, PROJECT_FILE

    try:
        # Use QFileDialog to open a modal file explorer
        if path:
            PROJECT_FILE = path
        else:
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
            global CIV_TECH_TREES_FILE
            CIV_TECH_TREES_FILE = rf'{MOD_FOLDER}\resources\_common\dat\civTechTrees.json'
            CIV_IMAGE_FOLDER = rf'{MOD_FOLDER}\widgetui\textures\menu\civs'
            extracted_project_name = MOD_FOLDER.split('\\')
            extracted_project_name = extracted_project_name[len(extracted_project_name) - 1]
            PROJECT_FILE = extracted_project_name + rf'.txt'
            
            global DATA
            if os.path.exists('data.pkl'):
                # Load the serialized file
                with open('data.pkl', 'rb') as serialized_file:
                    DATA = pickle.load(serialized_file)
            else:
                # Parse the .dat file and save it for future use
                DATA = DatFile.parse(DATA_FILE_DAT)
                with open('data.pkl', 'wb') as serialized_file:
                    pickle.dump(DATA, serialized_file)

            #DATA.techs[22].resource_costs[0].amount = 69 --- THIS STILL WORKS

        # Import civilisations and create objects for them with unit values
        with open(CIV_TECH_TREES_FILE, 'r', encoding='utf-8') as file:
            global JSON_DATA
            JSON_DATA = json.dumps(json.load(file), indent=2).splitlines()
            MAIN_WINDOW.civilisation_dropdown.clear()  # Clear the dropdown before adding new items
            current_civilisation = None  # Initialize this to track the current civilisation
            civ_read_offset = 0

            for line in JSON_DATA:
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

        # Get the description and description ID for each civilization
        with open(MODDED_STRINGS_FILE, 'r', encoding='utf-8') as strings_file:
            strings_lines = strings_file.read().splitlines()
            total_civ_count = len(civilisation_objects)
            for i in range(total_civ_count):
                civilisation_objects[i].desc_id = strings_lines[total_civ_count + i][:6]
                civilisation_objects[i].description = strings_lines[total_civ_count + i][7:]

        # Populate inactive civilisations
        #MAIN_WINDOW.civilisation_dropdown.insertSeparator(MAIN_WINDOW.civilisation_dropdown.count())
        #MAIN_WINDOW.civilisation_dropdown.addItem('New...')

        # Clear dropdowns and populate with new data
        MAIN_WINDOW.architecture_dropdown.clear()
        MAIN_WINDOW.language_dropdown.clear()
        MAIN_WINDOW.architecture_dropdown.addItems(["Britons", "Franks", "Goths", "Teutons", "Japanese", "Chinese", "Byzantines", "Persians", "Saracens", "Turks", "Vikings", "Mongols", "Celts", "Spanish", "Aztecs", "Mayans", "Huns", "Koreans", "Italians", "Hindustanis", "Incas", "Magyars", "Slavs", "Portuguese", "Ethiopians", "Malians", "Berbers", "Khmer", "Malay", "Burmese", "Vietnamese", "Bulgarians", "Tatars", "Cumans", "Lithuanians", "Burgundians", "Sicilians", "Poles", "Bohemians", "Dravidians", "Bengalis", "Gurjaras", "Romans", "Armenians", "Georgians"])
        MAIN_WINDOW.language_dropdown.addItems(["Britons", "Franks", "Goths", "Teutons", "Japanese", "Chinese", "Byzantines", "Persians", "Saracens", "Turks", "Vikings", "Mongols", "Celts", "Spanish", "Aztecs", "Mayans", "Huns", "Koreans", "Italians", "Hindustanis", "Incas", "Magyars", "Slavs", "Portuguese", "Ethiopians", "Malians", "Berbers", "Khmer", "Malay", "Burmese", "Vietnamese", "Bulgarians", "Tatars", "Cumans", "Lithuanians", "Burgundians", "Sicilians", "Poles", "Bohemians", "Dravidians", "Bengalis", "Gurjaras", "Romans", "Armenians", "Georgians"])
        
        MAIN_WINDOW.architecture_dropdown.insertSeparator(MAIN_WINDOW.architecture_dropdown.count())
        MAIN_WINDOW.language_dropdown.insertSeparator(MAIN_WINDOW.language_dropdown.count())
        #MAIN_WINDOW.language_dropdown.addItems(["Aromanian", "Cantonese", "Catalan", "Javanese", "Lakota", "Mohawk", "Somali", "Thai", "Tibetan", "Zapotec", "Zulu"])
        MAIN_WINDOW.language_dropdown.addItems(['Greek'])
        #MAIN_WINDOW.update_civs(civilisation_objects)
        #MAIN_WINDOW.changed_civilisation_dropdown()

        # Set all default languages
        def set_default_sound(sound_index, amount, unit, action):
            # Sound list to add to file
            sound_list = []

            # Clear previous sounds
            DATA.sounds[sound_index].items.clear()
            for i2, civ in enumerate(civilisation_objects):
                # Get base sound for reference
                base_sound = genieutils.sound.SoundItem('', 0, 0, 0, -1)

                # Get the language selected
                base_sound_name = civ.true_name
                if base_sound_name == 'Indians':
                    base_sound_name = 'Hindustanis'
                elif base_sound_name == 'Magyar':
                    base_sound_name = 'Magyars'
                base_sound_name += rf'_{unit}_{action}'

                # Add extra probability
                probabilities = [0] * amount

                # Update each element in the probabilities list
                for i in range(amount):
                    probabilities[i] = int(100 / amount)

                # Adjust the first probability if the sum is less than 100
                if sum(probabilities) < 100:
                    probabilities[0] += 100 - sum(probabilities)

                # Convert the first element to an integer after adjustment (just in case)
                probabilities[0] = int(probabilities[0])
                for i in range(amount):
                    # Build new name
                    new_sound_name = base_sound_name + '_' + str(i + 1) if amount > 1 else base_sound_name

                    # Create a new sound item for each iteration
                    new_sound = genieutils.sound.SoundItem(new_sound_name, 0, probabilities[i], i2 + 1, -1)

                    # Append the new sound to the list
                    DATA.sounds[sound_index].items.append(new_sound)

        # Convert the project file's saved sounds into a variable that can be read by the program
        with open(rf'{MOD_FOLDER}/{PROJECT_FILE}', 'r+') as project_file:
            project_lines = project_file.readlines()

            try:
                # Populate the sounds list
                global sounds_list
                sounds_list = project_lines[2].split(',')

                # Load all of the sounds
                age_sounds = [[303, 4, 'Villager_Male', 'Select'], [301, 4, 'Villager_Male', 'Task'], [295, 1, 'Villager_Male', 'Build'], [299, 1, 'Villager_Male', 'Chop'], [455, 1, 'Villager_Male', 'Farm'], [448, 1, 'Villager_Male', 'Fish'], [297, 1, 'Villager_Male', 'Forage'], [298, 1, 'Villager_Male', 'Hunt'], [300, 1, 'Villager_Male', 'Mine'], [302, 1, 'Villager_Male', 'Repair'], [435, 4, 'Villager_Female', 'Select'], [434, 4, 'Villager_Female', 'Task'], [437, 1, 'Villager_Female', 'Build'], [442, 1, 'Villager_Female', 'Chop'], [438, 1, 'Villager_Female', 'Farm'], [487, 1, 'Villager_Female', 'Fish'], [440, 1, 'Villager_Female', 'Forage'], [441, 1, 'Villager_Female', 'Hunt'], [443, 1, 'Villager_Female', 'Mine'], [444, 1, 'Villager_Female', 'Repair'], [420, 3, 'Soldier', 'Select'], [421, 3, 'Soldier', 'Move'], [422, 3, 'Soldier', 'Attack'], [423, 3, 'Monk', 'Select'], [424, 3, 'Monk', 'Move'], [479, 3, 'King', 'Select'], [480, 3, 'King', 'Move']]

                for sound_index in age_sounds:
                    # Clear the existing sounds
                    DATA.sounds[sound_index[0]].items.clear()

                    # Repopulate the previously created sounds
                    for j, saved_lang in enumerate(sounds_list):
                        # Get base sound for reference
                        base_sound = genieutils.sound.SoundItem('', 0, 0, 0, -1)

                        # Create the base sound name
                        base_sound_name = rf'{sounds_list[j]}_{sound_index[2]}_{sound_index[3]}'

                        # Add extra probability
                        probabilities = [0] * sound_index[1]

                        # Update each element in the probabilities list
                        for i in range(sound_index[1]):
                            probabilities[i] = int(100 / sound_index[1])

                        # Adjust the first probability if the sum is less than 100
                        if sum(probabilities) < 100:
                            probabilities[0] += 100 - sum(probabilities)

                        # Convert the first element to an integer after adjustment (just in case)
                        probabilities[0] = int(probabilities[0])
                        for i in range(sound_index[1]):
                            # Build new name
                            new_sound_name = base_sound_name + '_' + str(i + 1) if sound_index[1] > 1 else base_sound_name

                            # Create a new sound item for each iteration
                            new_sound = genieutils.sound.SoundItem(new_sound_name, 0, probabilities[i], j + 1, -1)

                            # Append the new sound to the list
                            DATA.sounds[sound_index[0]].items.append(new_sound)

                # Save the new, default sounds
                DATA.save(rf'{MOD_FOLDER}\resources\_common\dat\empires2_x2_p1.dat')

            except IndexError:
                # Default sounds need to be created
                # Add the default sounds
                sounds_list = [
                    MAIN_WINDOW.language_dropdown.itemText(i) 
                    for i in range(min(MAIN_WINDOW.language_dropdown.count(), len(civilisation_objects)))
                ]

                # Ensure all lines end with a newline
                project_lines = [line if line.endswith('\n') else line + '\n' for line in project_lines]

                # Add new lines if the file has fewer than 3 lines
                while len(project_lines) < 3:
                    project_lines.append('\n')

                # Write the default sounds to the third line (index 2)
                project_lines[2] = ','.join(sounds_list) + '\n'  # Add newline to ensure it ends properly

                # Move the file pointer to the beginning of the file
                project_file.seek(0)

                # Write the modified lines back to the file
                project_file.writelines(project_lines)

                # Reformat the sounds so that they can be more easily edited in the future
                set_default_sound(303, 4, 'Villager_Male', 'Select')
                set_default_sound(301, 4, 'Villager_Male', 'Move')
                set_default_sound(295, 1, 'Villager_Male', 'Build')
                set_default_sound(299, 1, 'Villager_Male', 'Chop')
                set_default_sound(455, 1, 'Villager_Male', 'Farm')
                set_default_sound(448, 1, 'Villager_Male', 'Fish')
                set_default_sound(297, 1, 'Villager_Male', 'Forage')
                set_default_sound(298, 1, 'Villager_Male', 'Hunt')
                set_default_sound(300, 1, 'Villager_Male', 'Mine')
                set_default_sound(302, 1, 'Villager_Male', 'Repair')
                set_default_sound(435, 4, 'Villager_Female', 'Select')
                set_default_sound(434, 4, 'Villager_Female', 'Move')
                set_default_sound(437, 1, 'Villager_Female', 'Build')
                set_default_sound(442, 1, 'Villager_Female', 'Chop')
                set_default_sound(438, 1, 'Villager_Female', 'Farm')
                set_default_sound(487, 1, 'Villager_Female', 'Fish')
                set_default_sound(440, 1, 'Villager_Female', 'Forage')
                set_default_sound(441, 1, 'Villager_Female', 'Hunt')
                set_default_sound(443, 1, 'Villager_Female', 'Mine')
                set_default_sound(444, 1, 'Villager_Female', 'Repair')
                set_default_sound(420, 3, 'Soldier', 'Select')
                set_default_sound(421, 3, 'Soldier', 'Move')
                set_default_sound(422, 3, 'Soldier', 'Attack')
                set_default_sound(423, 3, 'Monk', 'Select')
                set_default_sound(424, 3, 'Monk', 'Move')
                set_default_sound(479, 3, 'King', 'Select')
                set_default_sound(480, 3, 'King', 'Move')

                # Save the new, default sounds
                DATA.save(rf'{MOD_FOLDER}\resources\_common\dat\empires2_x2_p1.dat')
        
        update_civilisation_dropdown()

    except Exception as e:
        error_details = traceback.format_exc()
        show_error_message(f"An error occurred: {str(e)}\n\nDetails:\n{error_details}")

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
    for i, civ in enumerate(civilisation_objects):
        if (civ.name == selected_value):
            global CURRENT_CIV_INDEX
            CURRENT_CIV_INDEX = i

            # Display description
            new_description = civ.description[1:-1].replace('\\n', '\n').replace('<b>', '')
            MAIN_WINDOW.description.setPlainText(new_description)

            # Set the civilisation icon
            MAIN_WINDOW.civilisation_icon_image.setPixmap(QtGui.QPixmap(civ.image_path))

            # Rename unique units
            match = re.search(r"Unique Unit:\s*([^\(]+)", new_description)
            if not match:
                match = re.search(r"Unique Units:\s*([^\(]+)", new_description)

            if match:
                unique_unit = match.group(1).strip()
            else:
                print("Unique Unit not found.")

            try:
                for block in unit_blocks:
                    if block.name == 'Unique Unit':
                        getattr(MAIN_WINDOW, f"Unique_Unit_4").setText(unique_unit)
                        getattr(MAIN_WINDOW, f"Unique_Unit_3").setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/{unique_unit}.png"))
                    if block.name == 'Elite Unique Unit':
                        getattr(MAIN_WINDOW, f"Elite_Unique_Unit_4").setText(rf'Elite {unique_unit}')
                        getattr(MAIN_WINDOW, f"Elite_Unique_Unit_3").setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/{unique_unit}.png"))
            except Exception as e:
                print(str(e))

            # Castle and Impertial Techs
            #job_description = "Castle_Tech_4 will be replaced with Castle Tech and Imperial_Tech_4 will be replaced with Imperial Tech."

            # Step 1: Extract the unique techs using regex
            

            # Update the tech tree
            for block in unit_blocks:
                if block.name != 'Unique Unit' and block.name != 'Elite Unique Unit' and block.name != 'Castle Tech' and block.name != 'Imperial Tech' and block.name != 'Trebuchet' and block.name != 'Spies':
                    block.enable_disable(False, True, False)
                else:
                    block.enable_disable(True, True, False)

                try:
                    if civ.units[block.name] == 1 or civ.units[block.name] == 3:
                        block.enable_disable(True, True, False)
                except:
                    continue
                
            for key, value in civ.units.items():
                for block in unit_blocks:
                    if block.name == key:
                        if value == 1 or value == 3:
                            block.enable_disable(True, True, False)
                            break

            # Set default architecture
            dying_graphic_ids = [3055, 3063, 3087, 3091, 3059, 3067, 3092, 3062, 3064, 3065, 3088, 3090, 3089, 6319, 6630, 6321, 6320, 7248, 3056, 12500, 3057, 7381, 7647, 9368, 9369, 9370, 9371, 10566, 10567, 10565, 10568, 10569, 10570, 10571, 10572, 6080, 6087, 12397, 12404, 7650, 12486, 12493, 7613, 12603, 12610]
            try:
                MAIN_WINDOW.architecture_dropdown.setCurrentIndex(dying_graphic_ids.index(DATA.civs[CURRENT_CIV_INDEX + 1].units[276].dying_graphic))
            except:
                print(DATA.civs[CURRENT_CIV_INDEX + 1].units[276].dying_graphic, "not in list for", civilisation_objects[CURRENT_CIV_INDEX].true_name)

            # Set default language
            selected_lang = sounds_list[CURRENT_CIV_INDEX] # Get the string from sounds_list at the CURRENT_CIV_INDEX
            lang_index = MAIN_WINDOW.language_dropdown.findText(selected_lang) # Find the index in the dropdown that matches this string
            if lang_index != -1:  # Set the current index if the string was found
                MAIN_WINDOW.language_dropdown.setCurrentIndex(lang_index)

def update_architecture_dropdown():
    selected_architecture = MAIN_WINDOW.architecture_dropdown.currentIndex()  # Get the current index

    # DEBUG: Create new architecture graphic sets
    all_units_to_change = [10, 12, 14, 18, 19, 20, 21, 30, 31, 32, 45, 47, 49, 50, 51, 63, 64, 67, 68, 70, 71, 72, 78, 79, 80, 81, 82, 84, 85, 86, 87, 88, 90, 91, 92, 95, 101, 103, 104, 105, 109, 116, 117, 129, 130, 131, 132, 133, 137, 141, 142, 150, 153, 191, 192, 209, 210, 234, 235, 236, 276, 420, 442, 463, 464, 465, 481, 482, 483, 484, 487, 488, 490, 491, 498, 527, 528, 529, 532, 539, 562, 563, 564, 565, 584, 585, 586, 587, 597, 598, 611, 612, 613, 614, 615, 616, 617, 659, 660, 661, 662, 663, 664, 665, 666, 667, 668, 669, 670, 671, 672, 673, 674, 691, 789, 790, 791, 792, 793, 794, 795, 796, 797, 798, 799, 800, 801, 802, 803, 804, 805, 806, 807, 808, 1103, 1104, 1189, 1192, 1251, 1646, 1665, 1711, 1720, 1734, 1795, 1808, 2120, 2121, 2122, 2144, 2145, 2146, 2173]

    '''architecture_names = ['britons_architecture', 'franks_architecture', 'goths_architecture', 'teutons_architecture', 'japanese_architecture', 'chinese_architecture', 'byzantines_architecture', 'persians_architecture', 'saracens_architecture', 'turks_architecture', 'vikings_architecture', 'mongols_architecture', 'celts_architecture', 'spanish_architecture', 'aztecs_architecture', 'mayans_architecture', 'huns_architecture', 'koreans_architecture', 'italians_architecture', 'indians_architecture', 'incas_architecture', 'magyar_architecture', 'slavs_architecture', 'portuguese_architecture', 'ethiopians_architecture', 'malians_architecture', 'berbers_architecture', 'khmer_architecture', 'malay_architecture', 'burmese_architecture', 'vietnamese_architecture', 'bulgarians_architecture', 'tatars_architecture', 'cumans_architecture', 'lithuanians_architecture', 'burgundians_architecture', 'sicilians_architecture', 'poles_architecture', 'bohemians_architecture', 'dravidians_architecture', 'bengalis_architecture', 'gurjaras_architecture', 'romans_architecture', 'armenians_architecture', 'georgians_architecture']
    
    total_lines = []
    for civ_index in range(len(civilisation_objects)):
        units = DATA.civs[civ_index + 1].units
        test_architecture = '['

        # Try getting any and all graphics
        for i, current_unit_index in enumerate(all_units_to_change):
            # Try getting any and all graphics
            try:
                standing = units[current_unit_index].standing_graphic[0]
            except:
                standing = -1

            try:
                dying = units[current_unit_index].dying_graphic
            except:
                dying = -1

            try:
                damage_25 = units[current_unit_index].damage_graphics[0].graphic_id
            except:
                damage_25 = -1

            try:
                damage_50 = units[current_unit_index].damage_graphics[1].graphic_id
            except:
                damage_50 = -1

            try:
                damage_75 = units[current_unit_index].damage_graphics[2].graphic_id
            except:
                damage_75 = -1

            # Build the graphics line
            ending = ', '
            if i == len(all_units_to_change) - 1:
                ending = ''
            test_architecture += rf'({standing}, {dying}, {damage_25}, {damage_50}, {damage_75}){ending}'

        test_architecture += ']'
        total_lines.append(rf'{architecture_names[civ_index]} = {test_architecture}')

    whole_string = '\n'.join(total_lines)
    pyperclip.copy(whole_string)
    print('Copied all lines.')'''

    # Architecture sets
    britons_architecture = [(24, 20, 4686, 4690, 4694), (2575, 2573, 4429, 4430, 4431), (24, 20, 4686, 4690, 4694), (65, 69, 4714, 4718, 4722), (65, 69, 4714, 4718, 4722), (105, 101, 4742, 4746, 4750), (4013, 813, -1, -1, -1), (150, 146, 4774, 4778, 4782), (150, 146, 4774, 4778, 4782), (150, 146, 4774, 4778, 4782), (215, 205, 4456, 4457, 4458), (236, 134, 4822, 4826, 4830), (489, 485, 5102, 5106, 5110), (255, -1, 5354, 5355, 5356), (236, 134, 4822, 4826, 4830), (2060, 2056, 5538, 5539, 5540), (2048, 2044, 5538, 5539, 5540), (2084, 2056, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (3253, 265, 5054, 5058, 5062), (588, 37, 4610, 4611, 4612), (2072, 2044, 5538, 5539, 5540), (4202, 4198, 5198, 5202, 5206), (5331, 3841, 5541, 5542, 5543), (5326, 3839, 5541, 5542, 5543), (174, 170, 4790, 4794, 4798), (2268, 2264, 4994, 4998, 5002), (2132, 2128, 5544, 5545, 5546), (525, 521, 5146, 5150, 5154), (12, 8, 4670, 4674, 4678), (2120, 2116, 5544, 5545, 5546), (2156, 2128, 5544, 5545, 5546), (2144, 2116, 5544, 5545, 5546), (5331, 3841, 5547, 5548, 5549), (5326, 3839, 5547, 5548, 5549), (513, 509, 5130, 5134, 5138), (53, 57, 4702, 4706, 4710), (150, 146, 4774, 4778, 4782), (53, 57, 4702, 4706, 4710), (3241, 419, 4563, 4564, 4565), (411, 407, 5010, 5014, 5018), (2024, 37, 3794, 3798, 3802), (368, 372, 4958, 4962, 4966), (380, 384, 4970, 4974, 4978), (380, 384, 4970, 4974, 4978), (105, 101, 4742, 4746, 4750), (224, 128, 4806, 4810, 4814), (3434, 2276, 5026, 5030, 5034), (3265, 277, 5070, 5074, 5078), (3041, 289, 5086, 5090, 5094), (489, 485, 5102, 5106, 5110), (525, 521, 5146, 5150, 5154), (2223, 2219, 4946, 4950, 4954), (2223, 2219, 4946, 4950, 4954), (569, 573, 5174, 5178, 5182), (581, 585, 5186, 5190, 5194), (2532, 2528, 5214, 5218, 5222), (2407, 4186, 5230, 5234, 5238), (2415, 4190, 5246, 5250, 5254), (3068, 3055, 5275, 5288, 5301), (3961, 1757, -1, -1, -1), (3889, 1900, -1, -1, -1), (2209, 2205, 4934, 4938, 4942), (2223, 2219, 4946, 4950, 4954), (2223, 2219, 4946, 4950, 4954), (459, 1751, -1, -1, -1), (3261, 1751, -1, -1, -1), (3257, 1751, -1, -1, -1), (3353, 40, 5428, 5429, 5430), (2539, 38, 5360, 5361, 5362), (2551, 38, 5360, 5361, 5362), (2543, 38, 5366, 5367, 5368), (2559, 38, 5366, 5367, 5368), (93, 89, 4726, 4730, 4734), (4039, 4174, -1, -1, -1), (3988, 4150, -1, -1, -1), (4182, 2720, -1, -1, -1), (4026, 2732, -1, -1, -1), (4052, 2762, -1, -1, -1), (3118, 3122, 5118, 5122, 5126), (3118, 3122, 5118, 5122, 5126), (3118, 3122, 5118, 5122, 5126), (3118, 3122, 5118, 5122, 5126), (3133, 3137, 4982, 4986, 4990), (3133, 3137, 4982, 4986, 4990), (3133, 3137, 4982, 4986, 4990), (3133, 3137, 4982, 4986, 4990), (3357, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (471, 1751, -1, -1, -1), (3037, 1751, -1, -1, -1), (3033, 1751, -1, -1, -1), (447, 1751, -1, -1, -1), (3249, 1751, -1, -1, -1), (3245, 1751, -1, -1, -1), (3349, 40, 5425, 5426, 5427), (3608, 3604, 5550, 5551, 5552), (3620, 3616, 5550, 5551, 5552), (3632, 3604, 5550, 5551, 5552), (3644, 3616, 5550, 5551, 5552), (5326, 3839, 5553, 5554, 5555), (5331, 3841, 5553, 5554, 5555), (3680, 38, 5372, 5373, 5374), (3692, 38, 5372, 5373, 5374), (3704, 3700, 5556, 5557, 5558), (3716, 3712, 5556, 5557, 5558), (3728, 3700, 5556, 5557, 5558), (3740, 3712, 5556, 5557, 5558), (5326, 3839, 5559, 5560, 5561), (5331, 3841, 5559, 5560, 5561), (3776, 38, 5378, 5379, 5380), (3788, 38, 5378, 5379, 5380), (4299, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (224, 5452, 4806, 4810, 4814), (236, 5452, 4822, 4826, 4830), (236, 5452, 4822, 4826, 4830), (8628, 2762, -1, -1, -1), (9302, 9347, -1, -1, -1), (236, 134, 4822, 4826, 4830), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (224, 5452, 4806, 4810, 4814), (236, 5452, 4822, 4826, 4830), (236, 5452, 4822, 4826, 4830), (224, 5452, 4806, 4810, 4814), (236, 5452, 4822, 4826, 4830), (236, 5452, 4822, 4826, 4830), (215, 5452, 4456, 4457, 4458)]
    franks_architecture = [(24, 20, 4686, 4690, 4694), (2575, 2573, 4429, 4430, 4431), (24, 20, 4686, 4690, 4694), (65, 69, 4714, 4718, 4722), (65, 69, 4714, 4718, 4722), (105, 101, 4742, 4746, 4750), (4013, 813, -1, -1, -1), (150, 146, 4774, 4778, 4782), (150, 146, 4774, 4778, 4782), (150, 146, 4774, 4778, 4782), (215, 205, 4456, 4457, 4458), (236, 134, 4822, 4826, 4830), (489, 485, 5102, 5106, 5110), (255, -1, 5354, 5355, 5356), (236, 134, 4822, 4826, 4830), (2060, 2056, 5538, 5539, 5540), (2048, 2044, 5538, 5539, 5540), (2084, 2056, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (3253, 265, 5054, 5058, 5062), (588, 37, 4610, 4611, 4612), (2072, 2044, 5538, 5539, 5540), (4202, 4198, 5198, 5202, 5206), (5331, 3841, 5541, 5542, 5543), (5326, 3839, 5541, 5542, 5543), (174, 170, 4790, 4794, 4798), (2268, 2264, 4994, 4998, 5002), (2132, 2128, 5544, 5545, 5546), (525, 521, 5146, 5150, 5154), (12, 8, 4670, 4674, 4678), (2120, 2116, 5544, 5545, 5546), (2156, 2128, 5544, 5545, 5546), (2144, 2116, 5544, 5545, 5546), (5331, 3841, 5547, 5548, 5549), (5326, 3839, 5547, 5548, 5549), (513, 509, 5130, 5134, 5138), (53, 57, 4702, 4706, 4710), (150, 146, 4774, 4778, 4782), (53, 57, 4702, 4706, 4710), (3241, 419, 4563, 4564, 4565), (411, 407, 5010, 5014, 5018), (2024, 37, 3794, 3798, 3802), (368, 372, 4958, 4962, 4966), (380, 384, 4970, 4974, 4978), (380, 384, 4970, 4974, 4978), (105, 101, 4742, 4746, 4750), (224, 128, 4806, 4810, 4814), (3434, 2276, 5026, 5030, 5034), (3265, 277, 5070, 5074, 5078), (3041, 289, 5086, 5090, 5094), (489, 485, 5102, 5106, 5110), (525, 521, 5146, 5150, 5154), (2223, 2219, 4946, 4950, 4954), (2223, 2219, 4946, 4950, 4954), (569, 573, 5174, 5178, 5182), (581, 585, 5186, 5190, 5194), (2532, 2528, 5214, 5218, 5222), (2407, 4186, 5230, 5234, 5238), (2415, 4190, 5246, 5250, 5254), (3076, 3063, 5282, 5295, 5308), (3961, 1757, -1, -1, -1), (3889, 1900, -1, -1, -1), (2209, 2205, 4934, 4938, 4942), (2223, 2219, 4946, 4950, 4954), (2223, 2219, 4946, 4950, 4954), (459, 1751, -1, -1, -1), (3261, 1751, -1, -1, -1), (3257, 1751, -1, -1, -1), (3353, 40, 5428, 5429, 5430), (2539, 38, 5360, 5361, 5362), (2551, 38, 5360, 5361, 5362), (2543, 38, 5366, 5367, 5368), (2559, 38, 5366, 5367, 5368), (93, 89, 4726, 4730, 4734), (4039, 4174, -1, -1, -1), (3988, 4150, -1, -1, -1), (4182, 2720, -1, -1, -1), (4026, 2732, -1, -1, -1), (4052, 2762, -1, -1, -1), (3118, 3122, 5118, 5122, 5126), (3118, 3122, 5118, 5122, 5126), (3118, 3122, 5118, 5122, 5126), (3118, 3122, 5118, 5122, 5126), (3133, 3137, 4982, 4986, 4990), (3133, 3137, 4982, 4986, 4990), (3133, 3137, 4982, 4986, 4990), (3133, 3137, 4982, 4986, 4990), (3357, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (471, 1751, -1, -1, -1), (3037, 1751, -1, -1, -1), (3033, 1751, -1, -1, -1), (447, 1751, -1, -1, -1), (3249, 1751, -1, -1, -1), (3245, 1751, -1, -1, -1), (3349, 40, 5425, 5426, 5427), (3608, 3604, 5550, 5551, 5552), (3620, 3616, 5550, 5551, 5552), (3632, 3604, 5550, 5551, 5552), (3644, 3616, 5550, 5551, 5552), (5326, 3839, 5553, 5554, 5555), (5331, 3841, 5553, 5554, 5555), (3680, 38, 5372, 5373, 5374), (3692, 38, 5372, 5373, 5374), (3704, 3700, 5556, 5557, 5558), (3716, 3712, 5556, 5557, 5558), (3728, 3700, 5556, 5557, 5558), (3740, 3712, 5556, 5557, 5558), (5326, 3839, 5559, 5560, 5561), (5331, 3841, 5559, 5560, 5561), (3776, 38, 5378, 5379, 5380), (3788, 38, 5378, 5379, 5380), (4299, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (224, 5452, 4806, 4810, 4814), (236, 5452, 4822, 4826, 4830), (236, 5452, 4822, 4826, 4830), (8628, 2762, -1, -1, -1), (9302, 9347, -1, -1, -1), (236, 134, 4822, 4826, 4830), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (224, 5452, 4806, 4810, 4814), (236, 5452, 4822, 4826, 4830), (236, 5452, 4822, 4826, 4830), (224, 5452, 4806, 4810, 4814), (236, 5452, 4822, 4826, 4830), (236, 5452, 4822, 4826, 4830), (215, 5452, 4456, 4457, 4458)]
    goths_architecture = [(21, 17, 4683, 4687, 4691), (2575, 2573, 4429, 4430, 4431), (21, 17, 4683, 4687, 4691), (62, 66, 4711, 4715, 4719), (62, 66, 4711, 4715, 4719), (102, 98, 4739, 4743, 4747), (4010, 813, -1, -1, -1), (147, 143, 4771, 4775, 4779), (147, 143, 4771, 4775, 4779), (147, 143, 4771, 4775, 4779), (215, 205, 4456, 4457, 4458), (233, 131, 4819, 4823, 4827), (486, 482, 5099, 5103, 5107), (255, -1, 5354, 5355, 5356), (233, 131, 4819, 4823, 4827), (2057, 2053, 5538, 5539, 5540), (2045, 2041, 5538, 5539, 5540), (2081, 2053, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (3250, 262, 5051, 5055, 5059), (588, 37, 4610, 4611, 4612), (2069, 2041, 5538, 5539, 5540), (4199, 4195, 5195, 5199, 5203), (5327, 3829, 5541, 5542, 5543), (5322, 3827, 5541, 5542, 5543), (171, 167, 4787, 4791, 4795), (2265, 2261, 4991, 4995, 4999), (2129, 2125, 5544, 5545, 5546), (522, 518, 5143, 5147, 5151), (9, 5, 4667, 4671, 4675), (2117, 2113, 5544, 5545, 5546), (2153, 2125, 5544, 5545, 5546), (2141, 2113, 5544, 5545, 5546), (5327, 3829, 5547, 5548, 5549), (5322, 3827, 5547, 5548, 5549), (510, 506, 5127, 5131, 5135), (50, 54, 4699, 4703, 4707), (147, 143, 4771, 4775, 4779), (50, 54, 4699, 4703, 4707), (3241, 419, 4563, 4564, 4565), (408, 404, 5007, 5011, 5015), (2021, 37, 3791, 3795, 3799), (365, 369, 4955, 4959, 4963), (377, 381, 4967, 4971, 4975), (377, 381, 4967, 4971, 4975), (102, 98, 4739, 4743, 4747), (221, 125, 4803, 4807, 4811), (3431, 2273, 5023, 5027, 5031), (3262, 274, 5067, 5071, 5075), (3038, 286, 5083, 5087, 5091), (486, 482, 5099, 5103, 5107), (522, 518, 5143, 5147, 5151), (2220, 2216, 4943, 4947, 4951), (2220, 2216, 4943, 4947, 4951), (566, 570, 5171, 5175, 5179), (578, 582, 5183, 5187, 5191), (2529, 2525, 5211, 5215, 5219), (2404, 4183, 5227, 5231, 5235), (2412, 4187, 5243, 5247, 5251), (3093, 3087, 5276, 5289, 5302), (3958, 1757, -1, -1, -1), (3886, 1900, -1, -1, -1), (2206, 2202, 4931, 4935, 4939), (2220, 2216, 4943, 4947, 4951), (2220, 2216, 4943, 4947, 4951), (456, 1751, -1, -1, -1), (3258, 1751, -1, -1, -1), (3254, 1751, -1, -1, -1), (3350, 40, 5428, 5429, 5430), (2536, 38, 5360, 5361, 5362), (2548, 38, 5360, 5361, 5362), (2540, 38, 5366, 5367, 5368), (2556, 38, 5366, 5367, 5368), (90, 86, 4723, 4727, 4731), (4036, 4174, -1, -1, -1), (3985, 4150, -1, -1, -1), (4179, 2720, -1, -1, -1), (4023, 2732, -1, -1, -1), (4049, 2762, -1, -1, -1), (3115, 3119, 5115, 5119, 5123), (3115, 3119, 5115, 5119, 5123), (3115, 3119, 5115, 5119, 5123), (3115, 3119, 5115, 5119, 5123), (3130, 3134, 4979, 4983, 4987), (3130, 3134, 4979, 4983, 4987), (3130, 3134, 4979, 4983, 4987), (3130, 3134, 4979, 4983, 4987), (3354, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (468, 1751, -1, -1, -1), (3034, 1751, -1, -1, -1), (3030, 1751, -1, -1, -1), (444, 1751, -1, -1, -1), (3246, 1751, -1, -1, -1), (3242, 1751, -1, -1, -1), (3346, 40, 5425, 5426, 5427), (3605, 3601, 5550, 5551, 5552), (3617, 3613, 5550, 5551, 5552), (3629, 3601, 5550, 5551, 5552), (3641, 3613, 5550, 5551, 5552), (5322, 3827, 5553, 5554, 5555), (5327, 3829, 5553, 5554, 5555), (3677, 38, 5372, 5373, 5374), (3689, 38, 5372, 5373, 5374), (3701, 3697, 5556, 5557, 5558), (3713, 3709, 5556, 5557, 5558), (3725, 3697, 5556, 5557, 5558), (3737, 3709, 5556, 5557, 5558), (5322, 3827, 5559, 5560, 5561), (5327, 3829, 5559, 5560, 5561), (3773, 38, 5378, 5379, 5380), (3785, 38, 5378, 5379, 5380), (4296, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (221, 5452, 4803, 4807, 4811), (233, 5452, 4819, 4823, 4827), (233, 5452, 4819, 4823, 4827), (8632, 2762, -1, -1, -1), (9306, 9347, -1, -1, -1), (233, 131, 4819, 4823, 4827), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (221, 5452, 4803, 4807, 4811), (233, 5452, 4819, 4823, 4827), (233, 5452, 4819, 4823, 4827), (221, 5452, 4803, 4807, 4811), (233, 5452, 4819, 4823, 4827), (233, 5452, 4819, 4823, 4827), (215, 5452, 4456, 4457, 4458)]
    teutons_architecture = [(21, 17, 4683, 4687, 4691), (2575, 2573, 4429, 4430, 4431), (21, 17, 4683, 4687, 4691), (62, 66, 4711, 4715, 4719), (62, 66, 4711, 4715, 4719), (102, 98, 4739, 4743, 4747), (4010, 813, -1, -1, -1), (147, 143, 4771, 4775, 4779), (147, 143, 4771, 4775, 4779), (147, 143, 4771, 4775, 4779), (215, 205, 4456, 4457, 4458), (233, 131, 4819, 4823, 4827), (486, 482, 5099, 5103, 5107), (255, -1, 5354, 5355, 5356), (233, 131, 4819, 4823, 4827), (2057, 2053, 5538, 5539, 5540), (2045, 2041, 5538, 5539, 5540), (2081, 2053, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (3250, 262, 5051, 5055, 5059), (588, 37, 4610, 4611, 4612), (2069, 2041, 5538, 5539, 5540), (4199, 4195, 5195, 5199, 5203), (5327, 3829, 5541, 5542, 5543), (5322, 3827, 5541, 5542, 5543), (171, 167, 4787, 4791, 4795), (2265, 2261, 4991, 4995, 4999), (2129, 2125, 5544, 5545, 5546), (522, 518, 5143, 5147, 5151), (9, 5, 4667, 4671, 4675), (2117, 2113, 5544, 5545, 5546), (2153, 2125, 5544, 5545, 5546), (2141, 2113, 5544, 5545, 5546), (5327, 3829, 5547, 5548, 5549), (5322, 3827, 5547, 5548, 5549), (510, 506, 5127, 5131, 5135), (50, 54, 4699, 4703, 4707), (147, 143, 4771, 4775, 4779), (50, 54, 4699, 4703, 4707), (3241, 419, 4563, 4564, 4565), (408, 404, 5007, 5011, 5015), (2021, 37, 3791, 3795, 3799), (365, 369, 4955, 4959, 4963), (377, 381, 4967, 4971, 4975), (377, 381, 4967, 4971, 4975), (102, 98, 4739, 4743, 4747), (221, 125, 4803, 4807, 4811), (3431, 2273, 5023, 5027, 5031), (3262, 274, 5067, 5071, 5075), (3038, 286, 5083, 5087, 5091), (486, 482, 5099, 5103, 5107), (522, 518, 5143, 5147, 5151), (2220, 2216, 4943, 4947, 4951), (2220, 2216, 4943, 4947, 4951), (566, 570, 5171, 5175, 5179), (578, 582, 5183, 5187, 5191), (2529, 2525, 5211, 5215, 5219), (2404, 4183, 5227, 5231, 5235), (2412, 4187, 5243, 5247, 5251), (3097, 3091, 5285, 5298, 5311), (3958, 1757, -1, -1, -1), (3886, 1900, -1, -1, -1), (2206, 2202, 4931, 4935, 4939), (2220, 2216, 4943, 4947, 4951), (2220, 2216, 4943, 4947, 4951), (456, 1751, -1, -1, -1), (3258, 1751, -1, -1, -1), (3254, 1751, -1, -1, -1), (3350, 40, 5428, 5429, 5430), (2536, 38, 5360, 5361, 5362), (2548, 38, 5360, 5361, 5362), (2540, 38, 5366, 5367, 5368), (2556, 38, 5366, 5367, 5368), (90, 86, 4723, 4727, 4731), (4036, 4174, -1, -1, -1), (3985, 4150, -1, -1, -1), (4179, 2720, -1, -1, -1), (4023, 2732, -1, -1, -1), (4049, 2762, -1, -1, -1), (3115, 3119, 5115, 5119, 5123), (3115, 3119, 5115, 5119, 5123), (3115, 3119, 5115, 5119, 5123), (3115, 3119, 5115, 5119, 5123), (3130, 3134, 4979, 4983, 4987), (3130, 3134, 4979, 4983, 4987), (3130, 3134, 4979, 4983, 4987), (3130, 3134, 4979, 4983, 4987), (3354, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (468, 1751, -1, -1, -1), (3034, 1751, -1, -1, -1), (3030, 1751, -1, -1, -1), (444, 1751, -1, -1, -1), (3246, 1751, -1, -1, -1), (3242, 1751, -1, -1, -1), (3346, 40, 5425, 5426, 5427), (3605, 3601, 5550, 5551, 5552), (3617, 3613, 5550, 5551, 5552), (3629, 3601, 5550, 5551, 5552), (3641, 3613, 5550, 5551, 5552), (5322, 3827, 5553, 5554, 5555), (5327, 3829, 5553, 5554, 5555), (3677, 38, 5372, 5373, 5374), (3689, 38, 5372, 5373, 5374), (3701, 3697, 5556, 5557, 5558), (3713, 3709, 5556, 5557, 5558), (3725, 3697, 5556, 5557, 5558), (3737, 3709, 5556, 5557, 5558), (5322, 3827, 5559, 5560, 5561), (5327, 3829, 5559, 5560, 5561), (3773, 38, 5378, 5379, 5380), (3785, 38, 5378, 5379, 5380), (4296, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (221, 5452, 4803, 4807, 4811), (233, 5452, 4819, 4823, 4827), (233, 5452, 4819, 4823, 4827), (8632, 2762, -1, -1, -1), (9306, 9347, -1, -1, -1), (233, 131, 4819, 4823, 4827), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (221, 5452, 4803, 4807, 4811), (233, 5452, 4819, 4823, 4827), (233, 5452, 4819, 4823, 4827), (221, 5452, 4803, 4807, 4811), (233, 5452, 4819, 4823, 4827), (233, 5452, 4819, 4823, 4827), (215, 5452, 4456, 4457, 4458)]
    japanese_architecture = [(22, 18, 4684, 4688, 4692), (2575, 2573, 4429, 4430, 4431), (22, 18, 4684, 4688, 4692), (63, 67, 4712, 4716, 4720), (63, 67, 4712, 4716, 4720), (103, 99, 4740, 4744, 4748), (4011, 813, -1, -1, -1), (148, 144, 4772, 4776, 4780), (148, 144, 4772, 4776, 4780), (148, 144, 4772, 4776, 4780), (215, 205, 4456, 4457, 4458), (234, 132, 4820, 4824, 4828), (487, 483, 5100, 5104, 5108), (255, -1, 5354, 5355, 5356), (234, 132, 4820, 4824, 4828), (2058, 2054, 5538, 5539, 5540), (2046, 2042, 5538, 5539, 5540), (2082, 2054, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (3251, 263, 5052, 5056, 5060), (588, 37, 4610, 4611, 4612), (2070, 2042, 5538, 5539, 5540), (4200, 4196, 5196, 5200, 5204), (5328, 3833, 5541, 5542, 5543), (5323, 3831, 5541, 5542, 5543), (172, 168, 4788, 4792, 4796), (2266, 2262, 4992, 4996, 5000), (2130, 2126, 5544, 5545, 5546), (523, 519, 5144, 5148, 5152), (10, 6, 4668, 4672, 4676), (2118, 2114, 5544, 5545, 5546), (2154, 2126, 5544, 5545, 5546), (2142, 2114, 5544, 5545, 5546), (5328, 3833, 5547, 5548, 5549), (5323, 3831, 5547, 5548, 5549), (511, 507, 5128, 5132, 5136), (51, 55, 4700, 4704, 4708), (148, 144, 4772, 4776, 4780), (51, 55, 4700, 4704, 4708), (3241, 419, 4563, 4564, 4565), (409, 405, 5008, 5012, 5016), (2022, 37, 3792, 3796, 3800), (366, 370, 4956, 4960, 4964), (378, 382, 4968, 4972, 4976), (378, 382, 4968, 4972, 4976), (103, 99, 4740, 4744, 4748), (222, 126, 4804, 4808, 4812), (3432, 2274, 5024, 5028, 5032), (3263, 275, 5068, 5072, 5076), (3039, 287, 5084, 5088, 5092), (487, 483, 5100, 5104, 5108), (523, 519, 5144, 5148, 5152), (2221, 2217, 4944, 4948, 4952), (2221, 2217, 4944, 4948, 4952), (567, 571, 5172, 5176, 5180), (579, 583, 5184, 5188, 5192), (2530, 2526, 5212, 5216, 5220), (2405, 4184, 5228, 5232, 5236), (2413, 4188, 5244, 5248, 5252), (3072, 3059, 5278, 5291, 5304), (3959, 1757, -1, -1, -1), (3887, 1900, -1, -1, -1), (2207, 2203, 4932, 4936, 4940), (2221, 2217, 4944, 4948, 4952), (2221, 2217, 4944, 4948, 4952), (457, 1751, -1, -1, -1), (3259, 1751, -1, -1, -1), (3255, 1751, -1, -1, -1), (3351, 40, 5428, 5429, 5430), (2537, 38, 5360, 5361, 5362), (2549, 38, 5360, 5361, 5362), (2541, 38, 5366, 5367, 5368), (2557, 38, 5366, 5367, 5368), (91, 87, 4724, 4728, 4732), (4037, 4174, -1, -1, -1), (3986, 4150, -1, -1, -1), (4180, 2720, -1, -1, -1), (4024, 2732, -1, -1, -1), (4050, 2762, -1, -1, -1), (3116, 3120, 5116, 5120, 5124), (3116, 3120, 5116, 5120, 5124), (3116, 3120, 5116, 5120, 5124), (3116, 3120, 5116, 5120, 5124), (3131, 3135, 4980, 4984, 4988), (3131, 3135, 4980, 4984, 4988), (3131, 3135, 4980, 4984, 4988), (3131, 3135, 4980, 4984, 4988), (3355, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (469, 1751, -1, -1, -1), (3035, 1751, -1, -1, -1), (3031, 1751, -1, -1, -1), (445, 1751, -1, -1, -1), (3247, 1751, -1, -1, -1), (3243, 1751, -1, -1, -1), (3347, 40, 5425, 5426, 5427), (3606, 3602, 5550, 5551, 5552), (3618, 3614, 5550, 5551, 5552), (3630, 3602, 5550, 5551, 5552), (3642, 3614, 5550, 5551, 5552), (5323, 3831, 5553, 5554, 5555), (5328, 3833, 5553, 5554, 5555), (3678, 38, 5372, 5373, 5374), (3690, 38, 5372, 5373, 5374), (3702, 3698, 5556, 5557, 5558), (3714, 3710, 5556, 5557, 5558), (3726, 3698, 5556, 5557, 5558), (3738, 3710, 5556, 5557, 5558), (5323, 3831, 5559, 5560, 5561), (5328, 3833, 5559, 5560, 5561), (3774, 38, 5378, 5379, 5380), (3786, 38, 5378, 5379, 5380), (4297, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (222, 5452, 4804, 4808, 4812), (234, 5452, 4820, 4824, 4828), (234, 5452, 4820, 4824, 4828), (8635, 2762, -1, -1, -1), (9309, 9347, -1, -1, -1), (234, 132, 4820, 4824, 4828), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (222, 5452, 4804, 4808, 4812), (234, 5452, 4820, 4824, 4828), (234, 5452, 4820, 4824, 4828), (222, 5452, 4804, 4808, 4812), (234, 5452, 4820, 4824, 4828), (234, 5452, 4820, 4824, 4828), (215, 5452, 4456, 4457, 4458)]
    chinese_architecture = [(22, 18, 4684, 4688, 4692), (2575, 2573, 4429, 4430, 4431), (22, 18, 4684, 4688, 4692), (63, 67, 4712, 4716, 4720), (63, 67, 4712, 4716, 4720), (103, 99, 4740, 4744, 4748), (4011, 813, -1, -1, -1), (148, 144, 4772, 4776, 4780), (148, 144, 4772, 4776, 4780), (148, 144, 4772, 4776, 4780), (215, 205, 4456, 4457, 4458), (234, 132, 4820, 4824, 4828), (487, 483, 5100, 5104, 5108), (255, -1, 5354, 5355, 5356), (234, 132, 4820, 4824, 4828), (2058, 2054, 5538, 5539, 5540), (2046, 2042, 5538, 5539, 5540), (2082, 2054, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (3251, 263, 5052, 5056, 5060), (588, 37, 4610, 4611, 4612), (2070, 2042, 5538, 5539, 5540), (4200, 4196, 5196, 5200, 5204), (5328, 3833, 5541, 5542, 5543), (5323, 3831, 5541, 5542, 5543), (172, 168, 4788, 4792, 4796), (2266, 2262, 4992, 4996, 5000), (2130, 2126, 5544, 5545, 5546), (523, 519, 5144, 5148, 5152), (10, 6, 4668, 4672, 4676), (2118, 2114, 5544, 5545, 5546), (2154, 2126, 5544, 5545, 5546), (2142, 2114, 5544, 5545, 5546), (5328, 3833, 5547, 5548, 5549), (5323, 3831, 5547, 5548, 5549), (511, 507, 5128, 5132, 5136), (51, 55, 4700, 4704, 4708), (148, 144, 4772, 4776, 4780), (51, 55, 4700, 4704, 4708), (3241, 419, 4563, 4564, 4565), (409, 405, 5008, 5012, 5016), (2022, 37, 3792, 3796, 3800), (366, 370, 4956, 4960, 4964), (378, 382, 4968, 4972, 4976), (378, 382, 4968, 4972, 4976), (103, 99, 4740, 4744, 4748), (222, 126, 4804, 4808, 4812), (3432, 2274, 5024, 5028, 5032), (3263, 275, 5068, 5072, 5076), (3039, 287, 5084, 5088, 5092), (487, 483, 5100, 5104, 5108), (523, 519, 5144, 5148, 5152), (2221, 2217, 4944, 4948, 4952), (2221, 2217, 4944, 4948, 4952), (567, 571, 5172, 5176, 5180), (579, 583, 5184, 5188, 5192), (2530, 2526, 5212, 5216, 5220), (2405, 4184, 5228, 5232, 5236), (2413, 4188, 5244, 5248, 5252), (3080, 3067, 5287, 5300, 5313), (3959, 1757, -1, -1, -1), (3887, 1900, -1, -1, -1), (2207, 2203, 4932, 4936, 4940), (2221, 2217, 4944, 4948, 4952), (2221, 2217, 4944, 4948, 4952), (457, 1751, -1, -1, -1), (3259, 1751, -1, -1, -1), (3255, 1751, -1, -1, -1), (3351, 40, 5428, 5429, 5430), (2537, 38, 5360, 5361, 5362), (2549, 38, 5360, 5361, 5362), (2541, 38, 5366, 5367, 5368), (2557, 38, 5366, 5367, 5368), (91, 87, 4724, 4728, 4732), (4037, 4174, -1, -1, -1), (3986, 4150, -1, -1, -1), (4180, 2720, -1, -1, -1), (4024, 2732, -1, -1, -1), (4050, 2762, -1, -1, -1), (3116, 3120, 5116, 5120, 5124), (3116, 3120, 5116, 5120, 5124), (3116, 3120, 5116, 5120, 5124), (3116, 3120, 5116, 5120, 5124), (3131, 3135, 4980, 4984, 4988), (3131, 3135, 4980, 4984, 4988), (3131, 3135, 4980, 4984, 4988), (3131, 3135, 4980, 4984, 4988), (3355, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (469, 1751, -1, -1, -1), (3035, 1751, -1, -1, -1), (3031, 1751, -1, -1, -1), (445, 1751, -1, -1, -1), (3247, 1751, -1, -1, -1), (3243, 1751, -1, -1, -1), (3347, 40, 5425, 5426, 5427), (3606, 3602, 5550, 5551, 5552), (3618, 3614, 5550, 5551, 5552), (3630, 3602, 5550, 5551, 5552), (3642, 3614, 5550, 5551, 5552), (5323, 3831, 5553, 5554, 5555), (5328, 3833, 5553, 5554, 5555), (3678, 38, 5372, 5373, 5374), (3690, 38, 5372, 5373, 5374), (3702, 3698, 5556, 5557, 5558), (3714, 3710, 5556, 5557, 5558), (3726, 3698, 5556, 5557, 5558), (3738, 3710, 5556, 5557, 5558), (5323, 3831, 5559, 5560, 5561), (5328, 3833, 5559, 5560, 5561), (3774, 38, 5378, 5379, 5380), (3786, 38, 5378, 5379, 5380), (4297, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (222, 5452, 4804, 4808, 4812), (234, 5452, 4820, 4824, 4828), (234, 5452, 4820, 4824, 4828), (8635, 2762, -1, -1, -1), (9309, 9347, -1, -1, -1), (234, 132, 4820, 4824, 4828), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (222, 5452, 4804, 4808, 4812), (234, 5452, 4820, 4824, 4828), (234, 5452, 4820, 4824, 4828), (222, 5452, 4804, 4808, 4812), (234, 5452, 4820, 4824, 4828), (234, 5452, 4820, 4824, 4828), (215, 5452, 4456, 4457, 4458)]
    byzantines_architecture = [(27, 26, 4532, 4533, 4534), (2575, 2573, 4429, 4430, 4431), (27, 26, 4532, 4533, 4534), (71, 72, 4567, 4568, 4569), (71, 72, 4567, 4568, 4569), (108, 107, 4542, 4543, 4544), (9262, 813, -1, -1, -1), (153, 152, 8277, 8278, 8279), (153, 152, 8277, 8278, 8279), (153, 152, 8277, 8278, 8279), (215, 205, 4456, 4457, 4458), (242, 135, 4605, 4606, 4607), (492, 491, 4537, 4538, 4539), (255, -1, 5354, 5355, 5356), (242, 135, 4605, 4606, 4607), (7421, 7420, 5538, 5539, 5540), (7417, 7416, 5538, 5539, 5540), (7429, 7420, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (12249, 266, 9210, 9211, 9212), (588, 37, 4610, 4611, 4612), (7425, 7416, 5538, 5539, 5540), (4171, 4170, 4636, 4637, 4638), (7436, 3845, 5541, 5542, 5543), (7432, 3843, 5541, 5542, 5543), (177, 176, 8295, 8296, 8297), (417, 416, 9177, 9178, 9179), (7453, 7452, 5544, 5545, 5546), (528, 527, 4576, 4577, 4578), (30, 29, 9165, 9166, 9167), (7449, 7448, 5544, 5545, 5546), (7461, 7452, 5544, 5545, 5546), (7457, 7448, 5544, 5545, 5546), (7436, 3845, 5547, 5548, 5549), (7432, 3843, 5547, 5548, 5549), (531, 530, 9216, 9217, 9218), (74, 75, 9191, 9192, 9193), (153, 152, 8277, 8278, 8279), (74, 75, 9191, 9192, 9193), (3241, 419, 4563, 4564, 4565), (414, 413, 4581, 4582, 4583), (7390, 37, 7398, 7400, 7402), (9196, 9197, 9198, 9199, 9200), (386, 387, 4618, 4619, 4620), (386, 387, 4618, 4619, 4620), (108, 107, 4542, 4543, 4544), (9182, 129, 9184, 9185, 9186), (3436, 2278, 4592, 4593, 4594), (3237, 278, 12253, 12254, 12255), (3229, 290, 12258, 12259, 12260), (492, 491, 4537, 4538, 4539), (528, 527, 4576, 4577, 4578), (2226, 2225, 4527, 4528, 4529), (2226, 2225, 4527, 4528, 4529), (593, 594, 4571, 4572, 4573), (596, 597, 4597, 4598, 4599), (2517, 2516, 4613, 4614, 4615), (2395, 2390, 4623, 4624, 4625), (2398, 2391, 4628, 4629, 4630), (3098, 3092, 5286, 5299, 5312), (9241, 1757, -1, -1, -1), (9282, 1900, -1, -1, -1), (9202, 2228, 9203, 9204, 9205), (2226, 2225, 4527, 4528, 4529), (2226, 2225, 4527, 4528, 4529), (432, 1751, -1, -1, -1), (3236, 1751, -1, -1, -1), (3235, 1751, -1, -1, -1), (3344, 40, 5428, 5429, 5430), (7441, 38, 5360, 5361, 5362), (7445, 38, 5360, 5361, 5362), (7473, 38, 5366, 5367, 5368), (7477, 38, 5366, 5367, 5368), (111, 110, 9171, 9172, 9173), (9267, 4174, -1, -1, -1), (9256, 4150, -1, -1, -1), (9259, 2720, -1, -1, -1), (9265, 2732, -1, -1, -1), (9271, 2762, -1, -1, -1), (3202, 3203, 3205, 3206, 3207), (3202, 3203, 3205, 3206, 3207), (3202, 3203, 3205, 3206, 3207), (3202, 3203, 3205, 3206, 3207), (3195, 3196, 3198, 3199, 3200), (3195, 3196, 3198, 3199, 3200), (3195, 3196, 3198, 3199, 3200), (3195, 3196, 3198, 3199, 3200), (3231, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (429, 1751, -1, -1, -1), (3228, 1751, -1, -1, -1), (3227, 1751, -1, -1, -1), (9207, 1751, -1, -1, -1), (12251, 1751, -1, -1, -1), (9208, 1751, -1, -1, -1), (9226, 40, 9230, 9231, 9232), (7481, 7480, 5550, 5551, 5552), (7485, 7484, 5550, 5551, 5552), (7489, 7480, 5550, 5551, 5552), (7493, 7484, 5550, 5551, 5552), (7432, 3843, 5553, 5554, 5555), (7436, 3845, 5553, 5554, 5555), (7505, 38, 5372, 5373, 5374), (7509, 38, 5372, 5373, 5374), (7513, 7512, 5556, 5557, 5558), (7517, 7516, 5556, 5557, 5558), (7521, 7512, 5556, 5557, 5558), (7525, 7516, 5556, 5557, 5558), (7432, 3843, 5559, 5560, 5561), (7436, 3845, 5559, 5560, 5561), (7537, 38, 5378, 5379, 5380), (7541, 38, 5378, 5379, 5380), (4314, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (224, 5452, 4806, 4810, 4814), (242, 5452, 4821, 4825, 4829), (242, 5452, 4821, 4825, 4829), (8644, 2762, -1, -1, -1), (9318, 9347, -1, -1, -1), (242, 135, 4821, 4825, 4829), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (224, 5452, 4806, 4810, 4814), (242, 5452, 4821, 4825, 4829), (242, 5452, 4821, 4825, 4829), (224, 5452, 4806, 4810, 4814), (242, 5452, 4821, 4825, 4829), (242, 5452, 4821, 4825, 4829), (215, 5452, 4456, 4457, 4458)]
    persians_architecture = [(23, 19, 4685, 4689, 4693), (2575, 2573, 4429, 4430, 4431), (23, 19, 4685, 4689, 4693), (64, 68, 4713, 4717, 4721), (64, 68, 4713, 4717, 4721), (104, 100, 4741, 4745, 4749), (4012, 813, -1, -1, -1), (149, 145, 4773, 4777, 4781), (149, 145, 4773, 4777, 4781), (149, 145, 4773, 4777, 4781), (215, 205, 4456, 4457, 4458), (235, 133, 4821, 4825, 4829), (488, 484, 5101, 5105, 5109), (255, -1, 5354, 5355, 5356), (235, 133, 4821, 4825, 4829), (2059, 2055, 5538, 5539, 5540), (2047, 2043, 5538, 5539, 5540), (2083, 2055, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (3252, 264, 5053, 5057, 5061), (588, 37, 4610, 4611, 4612), (2071, 2043, 5538, 5539, 5540), (4201, 4197, 5197, 5201, 5205), (5330, 3837, 5541, 5542, 5543), (5325, 3835, 5541, 5542, 5543), (173, 169, 4789, 4793, 4797), (2267, 2263, 4993, 4997, 5001), (2131, 2127, 5544, 5545, 5546), (524, 520, 5145, 5149, 5153), (11, 7, 4669, 4673, 4677), (2119, 2115, 5544, 5545, 5546), (2155, 2127, 5544, 5545, 5546), (2143, 2115, 5544, 5545, 5546), (5330, 3837, 5547, 5548, 5549), (5325, 3835, 5547, 5548, 5549), (512, 508, 5129, 5133, 5137), (52, 56, 4701, 4705, 4709), (149, 145, 4773, 4777, 4781), (52, 56, 4701, 4705, 4709), (3241, 419, 4563, 4564, 4565), (410, 406, 5009, 5013, 5017), (2023, 37, 3793, 3797, 3801), (367, 371, 4957, 4961, 4965), (379, 383, 4969, 4973, 4977), (379, 383, 4969, 4973, 4977), (104, 100, 4741, 4745, 4749), (223, 127, 4805, 4809, 4813), (3433, 2275, 5025, 5029, 5033), (3264, 276, 5069, 5073, 5077), (3040, 288, 5085, 5089, 5093), (488, 484, 5101, 5105, 5109), (524, 520, 5145, 5149, 5153), (2222, 2218, 4945, 4949, 4953), (2222, 2218, 4945, 4949, 4953), (568, 572, 5173, 5177, 5181), (580, 584, 5185, 5189, 5193), (2531, 2527, 5213, 5217, 5221), (2406, 4185, 5229, 5233, 5237), (2414, 4189, 5245, 5249, 5253), (3075, 3062, 5281, 5294, 5307), (3960, 1757, -1, -1, -1), (3888, 1900, -1, -1, -1), (2208, 2204, 4933, 4937, 4941), (2222, 2218, 4945, 4949, 4953), (2222, 2218, 4945, 4949, 4953), (458, 1751, -1, -1, -1), (3260, 1751, -1, -1, -1), (3256, 1751, -1, -1, -1), (3352, 40, 5428, 5429, 5430), (2538, 38, 5360, 5361, 5362), (2550, 38, 5360, 5361, 5362), (2542, 38, 5366, 5367, 5368), (2558, 38, 5366, 5367, 5368), (92, 88, 4725, 4729, 4733), (4038, 4174, -1, -1, -1), (3987, 4150, -1, -1, -1), (4181, 2720, -1, -1, -1), (4025, 2732, -1, -1, -1), (4051, 2762, -1, -1, -1), (3117, 3121, 5117, 5121, 5125), (3117, 3121, 5117, 5121, 5125), (3117, 3121, 5117, 5121, 5125), (3117, 3121, 5117, 5121, 5125), (3132, 3136, 4981, 4985, 4989), (3132, 3136, 4981, 4985, 4989), (3132, 3136, 4981, 4985, 4989), (3132, 3136, 4981, 4985, 4989), (3356, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (470, 1751, -1, -1, -1), (3036, 1751, -1, -1, -1), (3032, 1751, -1, -1, -1), (446, 1751, -1, -1, -1), (3248, 1751, -1, -1, -1), (3244, 1751, -1, -1, -1), (3348, 40, 5425, 5426, 5427), (3607, 3603, 5550, 5551, 5552), (3619, 3615, 5550, 5551, 5552), (3631, 3603, 5550, 5551, 5552), (3643, 3615, 5550, 5551, 5552), (5325, 3835, 5553, 5554, 5555), (5330, 3837, 5553, 5554, 5555), (3679, 38, 5372, 5373, 5374), (3691, 38, 5372, 5373, 5374), (3703, 3699, 5556, 5557, 5558), (3715, 3711, 5556, 5557, 5558), (3727, 3699, 5556, 5557, 5558), (3739, 3711, 5556, 5557, 5558), (5325, 3835, 5559, 5560, 5561), (5330, 3837, 5559, 5560, 5561), (3775, 38, 5378, 5379, 5380), (3787, 38, 5378, 5379, 5380), (4298, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (223, 5452, 4805, 4809, 4813), (235, 5452, 4821, 4825, 4829), (235, 5452, 4821, 4825, 4829), (8638, 2762, -1, -1, -1), (9312, 9347, -1, -1, -1), (235, 133, 4821, 4825, 4829), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (223, 5452, 4805, 4809, 4813), (235, 5452, 4821, 4825, 4829), (235, 5452, 4821, 4825, 4829), (223, 5452, 4805, 4809, 4813), (235, 5452, 4821, 4825, 4829), (235, 5452, 4821, 4825, 4829), (215, 5452, 4456, 4457, 4458)]
    saracens_architecture = [(23, 19, 4685, 4689, 4693), (2575, 2573, 4429, 4430, 4431), (23, 19, 4685, 4689, 4693), (64, 68, 4713, 4717, 4721), (64, 68, 4713, 4717, 4721), (104, 100, 4741, 4745, 4749), (4012, 813, -1, -1, -1), (149, 145, 4773, 4777, 4781), (149, 145, 4773, 4777, 4781), (149, 145, 4773, 4777, 4781), (215, 205, 4456, 4457, 4458), (235, 133, 4821, 4825, 4829), (488, 484, 5101, 5105, 5109), (255, -1, 5354, 5355, 5356), (235, 133, 4821, 4825, 4829), (2059, 2055, 5538, 5539, 5540), (2047, 2043, 5538, 5539, 5540), (2083, 2055, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (3252, 264, 5053, 5057, 5061), (588, 37, 4610, 4611, 4612), (2071, 2043, 5538, 5539, 5540), (4201, 4197, 5197, 5201, 5205), (5330, 3837, 5541, 5542, 5543), (5325, 3835, 5541, 5542, 5543), (173, 169, 4789, 4793, 4797), (2267, 2263, 4993, 4997, 5001), (2131, 2127, 5544, 5545, 5546), (524, 520, 5145, 5149, 5153), (11, 7, 4669, 4673, 4677), (2119, 2115, 5544, 5545, 5546), (2155, 2127, 5544, 5545, 5546), (2143, 2115, 5544, 5545, 5546), (5330, 3837, 5547, 5548, 5549), (5325, 3835, 5547, 5548, 5549), (512, 508, 5129, 5133, 5137), (52, 56, 4701, 4705, 4709), (149, 145, 4773, 4777, 4781), (52, 56, 4701, 4705, 4709), (3241, 419, 4563, 4564, 4565), (410, 406, 5009, 5013, 5017), (2023, 37, 3793, 3797, 3801), (367, 371, 4957, 4961, 4965), (379, 383, 4969, 4973, 4977), (379, 383, 4969, 4973, 4977), (104, 100, 4741, 4745, 4749), (223, 127, 4805, 4809, 4813), (3433, 2275, 5025, 5029, 5033), (3264, 276, 5069, 5073, 5077), (3040, 288, 5085, 5089, 5093), (488, 484, 5101, 5105, 5109), (524, 520, 5145, 5149, 5153), (2222, 2218, 4945, 4949, 4953), (2222, 2218, 4945, 4949, 4953), (568, 572, 5173, 5177, 5181), (580, 584, 5185, 5189, 5193), (2531, 2527, 5213, 5217, 5221), (2406, 4185, 5229, 5233, 5237), (2414, 4189, 5245, 5249, 5253), (3077, 3064, 5283, 5296, 5309), (3960, 1757, -1, -1, -1), (3888, 1900, -1, -1, -1), (2208, 2204, 4933, 4937, 4941), (2222, 2218, 4945, 4949, 4953), (2222, 2218, 4945, 4949, 4953), (458, 1751, -1, -1, -1), (3260, 1751, -1, -1, -1), (3256, 1751, -1, -1, -1), (3352, 40, 5428, 5429, 5430), (2538, 38, 5360, 5361, 5362), (2550, 38, 5360, 5361, 5362), (2542, 38, 5366, 5367, 5368), (2558, 38, 5366, 5367, 5368), (92, 88, 4725, 4729, 4733), (4038, 4174, -1, -1, -1), (3987, 4150, -1, -1, -1), (4181, 2720, -1, -1, -1), (4025, 2732, -1, -1, -1), (4051, 2762, -1, -1, -1), (3117, 3121, 5117, 5121, 5125), (3117, 3121, 5117, 5121, 5125), (3117, 3121, 5117, 5121, 5125), (3117, 3121, 5117, 5121, 5125), (3132, 3136, 4981, 4985, 4989), (3132, 3136, 4981, 4985, 4989), (3132, 3136, 4981, 4985, 4989), (3132, 3136, 4981, 4985, 4989), (3356, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (470, 1751, -1, -1, -1), (3036, 1751, -1, -1, -1), (3032, 1751, -1, -1, -1), (446, 1751, -1, -1, -1), (3248, 1751, -1, -1, -1), (3244, 1751, -1, -1, -1), (3348, 40, 5425, 5426, 5427), (3607, 3603, 5550, 5551, 5552), (3619, 3615, 5550, 5551, 5552), (3631, 3603, 5550, 5551, 5552), (3643, 3615, 5550, 5551, 5552), (5325, 3835, 5553, 5554, 5555), (5330, 3837, 5553, 5554, 5555), (3679, 38, 5372, 5373, 5374), (3691, 38, 5372, 5373, 5374), (3703, 3699, 5556, 5557, 5558), (3715, 3711, 5556, 5557, 5558), (3727, 3699, 5556, 5557, 5558), (3739, 3711, 5556, 5557, 5558), (5325, 3835, 5559, 5560, 5561), (5330, 3837, 5559, 5560, 5561), (3775, 38, 5378, 5379, 5380), (3787, 38, 5378, 5379, 5380), (4298, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (223, 5452, 4805, 4809, 4813), (235, 5452, 4821, 4825, 4829), (235, 5452, 4821, 4825, 4829), (8638, 2762, -1, -1, -1), (9312, 9347, -1, -1, -1), (235, 133, 4821, 4825, 4829), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (223, 5452, 4805, 4809, 4813), (235, 5452, 4821, 4825, 4829), (235, 5452, 4821, 4825, 4829), (223, 5452, 4805, 4809, 4813), (235, 5452, 4821, 4825, 4829), (235, 5452, 4821, 4825, 4829), (215, 5452, 4456, 4457, 4458)]
    turks_architecture = [(23, 19, 4685, 4689, 4693), (2575, 2573, 4429, 4430, 4431), (23, 19, 4685, 4689, 4693), (64, 68, 4713, 4717, 4721), (64, 68, 4713, 4717, 4721), (104, 100, 4741, 4745, 4749), (4012, 813, -1, -1, -1), (149, 145, 4773, 4777, 4781), (149, 145, 4773, 4777, 4781), (149, 145, 4773, 4777, 4781), (215, 205, 4456, 4457, 4458), (235, 133, 4821, 4825, 4829), (488, 484, 5101, 5105, 5109), (255, -1, 5354, 5355, 5356), (235, 133, 4821, 4825, 4829), (2059, 2055, 5538, 5539, 5540), (2047, 2043, 5538, 5539, 5540), (2083, 2055, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (3252, 264, 5053, 5057, 5061), (588, 37, 4610, 4611, 4612), (2071, 2043, 5538, 5539, 5540), (4201, 4197, 5197, 5201, 5205), (5330, 3837, 5541, 5542, 5543), (5325, 3835, 5541, 5542, 5543), (173, 169, 4789, 4793, 4797), (2267, 2263, 4993, 4997, 5001), (2131, 2127, 5544, 5545, 5546), (524, 520, 5145, 5149, 5153), (11, 7, 4669, 4673, 4677), (2119, 2115, 5544, 5545, 5546), (2155, 2127, 5544, 5545, 5546), (2143, 2115, 5544, 5545, 5546), (5330, 3837, 5547, 5548, 5549), (5325, 3835, 5547, 5548, 5549), (512, 508, 5129, 5133, 5137), (52, 56, 4701, 4705, 4709), (149, 145, 4773, 4777, 4781), (52, 56, 4701, 4705, 4709), (3241, 419, 4563, 4564, 4565), (410, 406, 5009, 5013, 5017), (2023, 37, 3793, 3797, 3801), (367, 371, 4957, 4961, 4965), (379, 383, 4969, 4973, 4977), (379, 383, 4969, 4973, 4977), (104, 100, 4741, 4745, 4749), (223, 127, 4805, 4809, 4813), (3433, 2275, 5025, 5029, 5033), (3264, 276, 5069, 5073, 5077), (3040, 288, 5085, 5089, 5093), (488, 484, 5101, 5105, 5109), (524, 520, 5145, 5149, 5153), (2222, 2218, 4945, 4949, 4953), (2222, 2218, 4945, 4949, 4953), (568, 572, 5173, 5177, 5181), (580, 584, 5185, 5189, 5193), (2531, 2527, 5213, 5217, 5221), (2406, 4185, 5229, 5233, 5237), (2414, 4189, 5245, 5249, 5253), (3078, 3065, 5284, 5297, 5310), (3960, 1757, -1, -1, -1), (3888, 1900, -1, -1, -1), (2208, 2204, 4933, 4937, 4941), (2222, 2218, 4945, 4949, 4953), (2222, 2218, 4945, 4949, 4953), (458, 1751, -1, -1, -1), (3260, 1751, -1, -1, -1), (3256, 1751, -1, -1, -1), (3352, 40, 5428, 5429, 5430), (2538, 38, 5360, 5361, 5362), (2550, 38, 5360, 5361, 5362), (2542, 38, 5366, 5367, 5368), (2558, 38, 5366, 5367, 5368), (92, 88, 4725, 4729, 4733), (4038, 4174, -1, -1, -1), (3987, 4150, -1, -1, -1), (4181, 2720, -1, -1, -1), (4025, 2732, -1, -1, -1), (4051, 2762, -1, -1, -1), (3117, 3121, 5117, 5121, 5125), (3117, 3121, 5117, 5121, 5125), (3117, 3121, 5117, 5121, 5125), (3117, 3121, 5117, 5121, 5125), (3132, 3136, 4981, 4985, 4989), (3132, 3136, 4981, 4985, 4989), (3132, 3136, 4981, 4985, 4989), (3132, 3136, 4981, 4985, 4989), (3356, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (470, 1751, -1, -1, -1), (3036, 1751, -1, -1, -1), (3032, 1751, -1, -1, -1), (446, 1751, -1, -1, -1), (3248, 1751, -1, -1, -1), (3244, 1751, -1, -1, -1), (3348, 40, 5425, 5426, 5427), (3607, 3603, 5550, 5551, 5552), (3619, 3615, 5550, 5551, 5552), (3631, 3603, 5550, 5551, 5552), (3643, 3615, 5550, 5551, 5552), (5325, 3835, 5553, 5554, 5555), (5330, 3837, 5553, 5554, 5555), (3679, 38, 5372, 5373, 5374), (3691, 38, 5372, 5373, 5374), (3703, 3699, 5556, 5557, 5558), (3715, 3711, 5556, 5557, 5558), (3727, 3699, 5556, 5557, 5558), (3739, 3711, 5556, 5557, 5558), (5325, 3835, 5559, 5560, 5561), (5330, 3837, 5559, 5560, 5561), (3775, 38, 5378, 5379, 5380), (3787, 38, 5378, 5379, 5380), (4298, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (223, 5452, 4805, 4809, 4813), (235, 5452, 4821, 4825, 4829), (235, 5452, 4821, 4825, 4829), (8638, 2762, -1, -1, -1), (9312, 9347, -1, -1, -1), (235, 133, 4821, 4825, 4829), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (223, 5452, 4805, 4809, 4813), (235, 5452, 4821, 4825, 4829), (235, 5452, 4821, 4825, 4829), (223, 5452, 4805, 4809, 4813), (235, 5452, 4821, 4825, 4829), (235, 5452, 4821, 4825, 4829), (215, 5452, 4456, 4457, 4458)]
    vikings_architecture = [(21, 17, 4683, 4687, 4691), (2575, 2573, 4429, 4430, 4431), (21, 17, 4683, 4687, 4691), (62, 66, 4711, 4715, 4719), (62, 66, 4711, 4715, 4719), (102, 98, 4739, 4743, 4747), (4010, 813, -1, -1, -1), (147, 143, 4771, 4775, 4779), (147, 143, 4771, 4775, 4779), (147, 143, 4771, 4775, 4779), (215, 205, 4456, 4457, 4458), (233, 131, 4819, 4823, 4827), (486, 482, 5099, 5103, 5107), (255, -1, 5354, 5355, 5356), (233, 131, 4819, 4823, 4827), (2057, 2053, 5538, 5539, 5540), (2045, 2041, 5538, 5539, 5540), (2081, 2053, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (3250, 262, 5051, 5055, 5059), (588, 37, 4610, 4611, 4612), (2069, 2041, 5538, 5539, 5540), (4199, 4195, 5195, 5199, 5203), (5327, 3829, 5541, 5542, 5543), (5322, 3827, 5541, 5542, 5543), (171, 167, 4787, 4791, 4795), (2265, 2261, 4991, 4995, 4999), (2129, 2125, 5544, 5545, 5546), (522, 518, 5143, 5147, 5151), (9, 5, 4667, 4671, 4675), (2117, 2113, 5544, 5545, 5546), (2153, 2125, 5544, 5545, 5546), (2141, 2113, 5544, 5545, 5546), (5327, 3829, 5547, 5548, 5549), (5322, 3827, 5547, 5548, 5549), (510, 506, 5127, 5131, 5135), (50, 54, 4699, 4703, 4707), (147, 143, 4771, 4775, 4779), (50, 54, 4699, 4703, 4707), (3241, 419, 4563, 4564, 4565), (408, 404, 5007, 5011, 5015), (2021, 37, 3791, 3795, 3799), (365, 369, 4955, 4959, 4963), (377, 381, 4967, 4971, 4975), (377, 381, 4967, 4971, 4975), (102, 98, 4739, 4743, 4747), (221, 125, 4803, 4807, 4811), (3431, 2273, 5023, 5027, 5031), (3262, 274, 5067, 5071, 5075), (3038, 286, 5083, 5087, 5091), (486, 482, 5099, 5103, 5107), (522, 518, 5143, 5147, 5151), (2220, 2216, 4943, 4947, 4951), (2220, 2216, 4943, 4947, 4951), (566, 570, 5171, 5175, 5179), (578, 582, 5183, 5187, 5191), (2529, 2525, 5211, 5215, 5219), (2404, 4183, 5227, 5231, 5235), (2412, 4187, 5243, 5247, 5251), (3094, 3088, 5277, 5290, 5303), (3958, 1757, -1, -1, -1), (3886, 1900, -1, -1, -1), (2206, 2202, 4931, 4935, 4939), (2220, 2216, 4943, 4947, 4951), (2220, 2216, 4943, 4947, 4951), (456, 1751, -1, -1, -1), (3258, 1751, -1, -1, -1), (3254, 1751, -1, -1, -1), (3350, 40, 5428, 5429, 5430), (2536, 38, 5360, 5361, 5362), (2548, 38, 5360, 5361, 5362), (2540, 38, 5366, 5367, 5368), (2556, 38, 5366, 5367, 5368), (90, 86, 4723, 4727, 4731), (4036, 4174, -1, -1, -1), (3985, 4150, -1, -1, -1), (4179, 2720, -1, -1, -1), (4023, 2732, -1, -1, -1), (4049, 2762, -1, -1, -1), (3115, 3119, 5115, 5119, 5123), (3115, 3119, 5115, 5119, 5123), (3115, 3119, 5115, 5119, 5123), (3115, 3119, 5115, 5119, 5123), (3130, 3134, 4979, 4983, 4987), (3130, 3134, 4979, 4983, 4987), (3130, 3134, 4979, 4983, 4987), (3130, 3134, 4979, 4983, 4987), (3354, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (468, 1751, -1, -1, -1), (3034, 1751, -1, -1, -1), (3030, 1751, -1, -1, -1), (444, 1751, -1, -1, -1), (3246, 1751, -1, -1, -1), (3242, 1751, -1, -1, -1), (3346, 40, 5425, 5426, 5427), (3605, 3601, 5550, 5551, 5552), (3617, 3613, 5550, 5551, 5552), (3629, 3601, 5550, 5551, 5552), (3641, 3613, 5550, 5551, 5552), (5322, 3827, 5553, 5554, 5555), (5327, 3829, 5553, 5554, 5555), (3677, 38, 5372, 5373, 5374), (3689, 38, 5372, 5373, 5374), (3701, 3697, 5556, 5557, 5558), (3713, 3709, 5556, 5557, 5558), (3725, 3697, 5556, 5557, 5558), (3737, 3709, 5556, 5557, 5558), (5322, 3827, 5559, 5560, 5561), (5327, 3829, 5559, 5560, 5561), (3773, 38, 5378, 5379, 5380), (3785, 38, 5378, 5379, 5380), (4296, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (221, 5452, 4803, 4807, 4811), (233, 5452, 4819, 4823, 4827), (233, 5452, 4819, 4823, 4827), (8632, 2762, -1, -1, -1), (9306, 9347, -1, -1, -1), (233, 131, 4819, 4823, 4827), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (221, 5452, 4803, 4807, 4811), (233, 5452, 4819, 4823, 4827), (233, 5452, 4819, 4823, 4827), (221, 5452, 4803, 4807, 4811), (233, 5452, 4819, 4823, 4827), (233, 5452, 4819, 4823, 4827), (215, 5452, 4456, 4457, 4458)]
    mongols_architecture = [(22, 18, 4684, 4688, 4692), (2575, 2573, 4429, 4430, 4431), (22, 18, 4684, 4688, 4692), (63, 67, 4712, 4716, 4720), (63, 67, 4712, 4716, 4720), (103, 99, 4740, 4744, 4748), (4011, 813, -1, -1, -1), (148, 144, 4772, 4776, 4780), (148, 144, 4772, 4776, 4780), (148, 144, 4772, 4776, 4780), (215, 205, 4456, 4457, 4458), (234, 132, 4820, 4824, 4828), (487, 483, 5100, 5104, 5108), (255, -1, 5354, 5355, 5356), (234, 132, 4820, 4824, 4828), (2058, 2054, 5538, 5539, 5540), (2046, 2042, 5538, 5539, 5540), (2082, 2054, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (3251, 263, 5052, 5056, 5060), (588, 37, 4610, 4611, 4612), (2070, 2042, 5538, 5539, 5540), (4200, 4196, 5196, 5200, 5204), (5328, 3833, 5541, 5542, 5543), (5323, 3831, 5541, 5542, 5543), (172, 168, 4788, 4792, 4796), (2266, 2262, 4992, 4996, 5000), (2130, 2126, 5544, 5545, 5546), (523, 519, 5144, 5148, 5152), (10, 6, 4668, 4672, 4676), (2118, 2114, 5544, 5545, 5546), (2154, 2126, 5544, 5545, 5546), (2142, 2114, 5544, 5545, 5546), (5328, 3833, 5547, 5548, 5549), (5323, 3831, 5547, 5548, 5549), (511, 507, 5128, 5132, 5136), (51, 55, 4700, 4704, 4708), (148, 144, 4772, 4776, 4780), (51, 55, 4700, 4704, 4708), (3241, 419, 4563, 4564, 4565), (409, 405, 5008, 5012, 5016), (2022, 37, 3792, 3796, 3800), (366, 370, 4956, 4960, 4964), (378, 382, 4968, 4972, 4976), (378, 382, 4968, 4972, 4976), (103, 99, 4740, 4744, 4748), (222, 126, 4804, 4808, 4812), (3432, 2274, 5024, 5028, 5032), (3263, 275, 5068, 5072, 5076), (3039, 287, 5084, 5088, 5092), (487, 483, 5100, 5104, 5108), (523, 519, 5144, 5148, 5152), (2221, 2217, 4944, 4948, 4952), (2221, 2217, 4944, 4948, 4952), (567, 571, 5172, 5176, 5180), (579, 583, 5184, 5188, 5192), (2530, 2526, 5212, 5216, 5220), (2405, 4184, 5228, 5232, 5236), (2413, 4188, 5244, 5248, 5252), (3096, 3090, 5280, 5293, 5306), (3959, 1757, -1, -1, -1), (3887, 1900, -1, -1, -1), (2207, 2203, 4932, 4936, 4940), (2221, 2217, 4944, 4948, 4952), (2221, 2217, 4944, 4948, 4952), (457, 1751, -1, -1, -1), (3259, 1751, -1, -1, -1), (3255, 1751, -1, -1, -1), (3351, 40, 5428, 5429, 5430), (2537, 38, 5360, 5361, 5362), (2549, 38, 5360, 5361, 5362), (2541, 38, 5366, 5367, 5368), (2557, 38, 5366, 5367, 5368), (91, 87, 4724, 4728, 4732), (4037, 4174, -1, -1, -1), (3986, 4150, -1, -1, -1), (4180, 2720, -1, -1, -1), (4024, 2732, -1, -1, -1), (4050, 2762, -1, -1, -1), (3116, 3120, 5116, 5120, 5124), (3116, 3120, 5116, 5120, 5124), (3116, 3120, 5116, 5120, 5124), (3116, 3120, 5116, 5120, 5124), (3131, 3135, 4980, 4984, 4988), (3131, 3135, 4980, 4984, 4988), (3131, 3135, 4980, 4984, 4988), (3131, 3135, 4980, 4984, 4988), (3355, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (469, 1751, -1, -1, -1), (3035, 1751, -1, -1, -1), (3031, 1751, -1, -1, -1), (445, 1751, -1, -1, -1), (3247, 1751, -1, -1, -1), (3243, 1751, -1, -1, -1), (3347, 40, 5425, 5426, 5427), (3606, 3602, 5550, 5551, 5552), (3618, 3614, 5550, 5551, 5552), (3630, 3602, 5550, 5551, 5552), (3642, 3614, 5550, 5551, 5552), (5323, 3831, 5553, 5554, 5555), (5328, 3833, 5553, 5554, 5555), (3678, 38, 5372, 5373, 5374), (3690, 38, 5372, 5373, 5374), (3702, 3698, 5556, 5557, 5558), (3714, 3710, 5556, 5557, 5558), (3726, 3698, 5556, 5557, 5558), (3738, 3710, 5556, 5557, 5558), (5323, 3831, 5559, 5560, 5561), (5328, 3833, 5559, 5560, 5561), (3774, 38, 5378, 5379, 5380), (3786, 38, 5378, 5379, 5380), (4297, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (222, 5452, 4804, 4808, 4812), (234, 5452, 4820, 4824, 4828), (234, 5452, 4820, 4824, 4828), (8635, 2762, -1, -1, -1), (9309, 9347, -1, -1, -1), (234, 132, 4820, 4824, 4828), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (222, 5452, 4804, 4808, 4812), (234, 5452, 4820, 4824, 4828), (234, 5452, 4820, 4824, 4828), (222, 5452, 4804, 4808, 4812), (234, 5452, 4820, 4824, 4828), (234, 5452, 4820, 4824, 4828), (215, 5452, 4456, 4457, 4458)]
    celts_architecture = [(24, 20, 4686, 4690, 4694), (2575, 2573, 4429, 4430, 4431), (24, 20, 4686, 4690, 4694), (65, 69, 4714, 4718, 4722), (65, 69, 4714, 4718, 4722), (105, 101, 4742, 4746, 4750), (4013, 813, -1, -1, -1), (150, 146, 4774, 4778, 4782), (150, 146, 4774, 4778, 4782), (150, 146, 4774, 4778, 4782), (215, 205, 4456, 4457, 4458), (236, 134, 4822, 4826, 4830), (489, 485, 5102, 5106, 5110), (255, -1, 5354, 5355, 5356), (236, 134, 4822, 4826, 4830), (2060, 2056, 5538, 5539, 5540), (2048, 2044, 5538, 5539, 5540), (2084, 2056, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (3253, 265, 5054, 5058, 5062), (588, 37, 4610, 4611, 4612), (2072, 2044, 5538, 5539, 5540), (4202, 4198, 5198, 5202, 5206), (5331, 3841, 5541, 5542, 5543), (5326, 3839, 5541, 5542, 5543), (174, 170, 4790, 4794, 4798), (2268, 2264, 4994, 4998, 5002), (2132, 2128, 5544, 5545, 5546), (525, 521, 5146, 5150, 5154), (12, 8, 4670, 4674, 4678), (2120, 2116, 5544, 5545, 5546), (2156, 2128, 5544, 5545, 5546), (2144, 2116, 5544, 5545, 5546), (5331, 3841, 5547, 5548, 5549), (5326, 3839, 5547, 5548, 5549), (513, 509, 5130, 5134, 5138), (53, 57, 4702, 4706, 4710), (150, 146, 4774, 4778, 4782), (53, 57, 4702, 4706, 4710), (3241, 419, 4563, 4564, 4565), (411, 407, 5010, 5014, 5018), (2024, 37, 3794, 3798, 3802), (368, 372, 4958, 4962, 4966), (380, 384, 4970, 4974, 4978), (380, 384, 4970, 4974, 4978), (105, 101, 4742, 4746, 4750), (224, 128, 4806, 4810, 4814), (3434, 2276, 5026, 5030, 5034), (3265, 277, 5070, 5074, 5078), (3041, 289, 5086, 5090, 5094), (489, 485, 5102, 5106, 5110), (525, 521, 5146, 5150, 5154), (2223, 2219, 4946, 4950, 4954), (2223, 2219, 4946, 4950, 4954), (569, 573, 5174, 5178, 5182), (581, 585, 5186, 5190, 5194), (2532, 2528, 5214, 5218, 5222), (2407, 4186, 5230, 5234, 5238), (2415, 4190, 5246, 5250, 5254), (3095, 3089, 5279, 5292, 5305), (3961, 1757, -1, -1, -1), (3889, 1900, -1, -1, -1), (2209, 2205, 4934, 4938, 4942), (2223, 2219, 4946, 4950, 4954), (2223, 2219, 4946, 4950, 4954), (459, 1751, -1, -1, -1), (3261, 1751, -1, -1, -1), (3257, 1751, -1, -1, -1), (3353, 40, 5428, 5429, 5430), (2539, 38, 5360, 5361, 5362), (2551, 38, 5360, 5361, 5362), (2543, 38, 5366, 5367, 5368), (2559, 38, 5366, 5367, 5368), (93, 89, 4726, 4730, 4734), (4039, 4174, -1, -1, -1), (3988, 4150, -1, -1, -1), (4182, 2720, -1, -1, -1), (4026, 2732, -1, -1, -1), (4052, 2762, -1, -1, -1), (3118, 3122, 5118, 5122, 5126), (3118, 3122, 5118, 5122, 5126), (3118, 3122, 5118, 5122, 5126), (3118, 3122, 5118, 5122, 5126), (3133, 3137, 4982, 4986, 4990), (3133, 3137, 4982, 4986, 4990), (3133, 3137, 4982, 4986, 4990), (3133, 3137, 4982, 4986, 4990), (3357, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (471, 1751, -1, -1, -1), (3037, 1751, -1, -1, -1), (3033, 1751, -1, -1, -1), (447, 1751, -1, -1, -1), (3249, 1751, -1, -1, -1), (3245, 1751, -1, -1, -1), (3349, 40, 5425, 5426, 5427), (3608, 3604, 5550, 5551, 5552), (3620, 3616, 5550, 5551, 5552), (3632, 3604, 5550, 5551, 5552), (3644, 3616, 5550, 5551, 5552), (5326, 3839, 5553, 5554, 5555), (5331, 3841, 5553, 5554, 5555), (3680, 38, 5372, 5373, 5374), (3692, 38, 5372, 5373, 5374), (3704, 3700, 5556, 5557, 5558), (3716, 3712, 5556, 5557, 5558), (3728, 3700, 5556, 5557, 5558), (3740, 3712, 5556, 5557, 5558), (5326, 3839, 5559, 5560, 5561), (5331, 3841, 5559, 5560, 5561), (3776, 38, 5378, 5379, 5380), (3788, 38, 5378, 5379, 5380), (4299, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (224, 5452, 4806, 4810, 4814), (236, 5452, 4822, 4826, 4830), (236, 5452, 4822, 4826, 4830), (8628, 2762, -1, -1, -1), (9302, 9347, -1, -1, -1), (236, 134, 4822, 4826, 4830), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (224, 5452, 4806, 4810, 4814), (236, 5452, 4822, 4826, 4830), (236, 5452, 4822, 4826, 4830), (224, 5452, 4806, 4810, 4814), (236, 5452, 4822, 4826, 4830), (236, 5452, 4822, 4826, 4830), (215, 5452, 4456, 4457, 4458)]
    spanish_architecture = [(27, 26, 4532, 4533, 4534), (2575, 2573, 4429, 4430, 4431), (27, 26, 4532, 4533, 4534), (71, 72, 4567, 4568, 4569), (71, 72, 4567, 4568, 4569), (108, 107, 4542, 4543, 4544), (9262, 813, -1, -1, -1), (153, 152, 8277, 8278, 8279), (153, 152, 8277, 8278, 8279), (153, 152, 8277, 8278, 8279), (215, 205, 4456, 4457, 4458), (242, 135, 4605, 4606, 4607), (492, 491, 4537, 4538, 4539), (255, -1, 5354, 5355, 5356), (242, 135, 4605, 4606, 4607), (7421, 7420, 5538, 5539, 5540), (7417, 7416, 5538, 5539, 5540), (7429, 7420, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (12249, 266, 9210, 9211, 9212), (588, 37, 4610, 4611, 4612), (7425, 7416, 5538, 5539, 5540), (4171, 4170, 4636, 4637, 4638), (7436, 3845, 5541, 5542, 5543), (7432, 3843, 5541, 5542, 5543), (177, 176, 8295, 8296, 8297), (417, 416, 9177, 9178, 9179), (7453, 7452, 5544, 5545, 5546), (528, 527, 4576, 4577, 4578), (30, 29, 9165, 9166, 9167), (7449, 7448, 5544, 5545, 5546), (7461, 7452, 5544, 5545, 5546), (7457, 7448, 5544, 5545, 5546), (7436, 3845, 5547, 5548, 5549), (7432, 3843, 5547, 5548, 5549), (531, 530, 9216, 9217, 9218), (74, 75, 9191, 9192, 9193), (153, 152, 8277, 8278, 8279), (74, 75, 9191, 9192, 9193), (3241, 419, 4563, 4564, 4565), (414, 413, 4581, 4582, 4583), (7390, 37, 7398, 7400, 7402), (9196, 9197, 9198, 9199, 9200), (386, 387, 4618, 4619, 4620), (386, 387, 4618, 4619, 4620), (108, 107, 4542, 4543, 4544), (9182, 129, 9184, 9185, 9186), (3436, 2278, 4592, 4593, 4594), (3237, 278, 12253, 12254, 12255), (3229, 290, 12258, 12259, 12260), (492, 491, 4537, 4538, 4539), (528, 527, 4576, 4577, 4578), (2226, 2225, 4527, 4528, 4529), (2226, 2225, 4527, 4528, 4529), (593, 594, 4571, 4572, 4573), (596, 597, 4597, 4598, 4599), (2517, 2516, 4613, 4614, 4615), (2395, 2390, 4623, 4624, 4625), (2398, 2391, 4628, 4629, 4630), (6322, 6319, 6307, 6310, 6313), (9241, 1757, -1, -1, -1), (9282, 1900, -1, -1, -1), (9202, 2228, 9203, 9204, 9205), (2226, 2225, 4527, 4528, 4529), (2226, 2225, 4527, 4528, 4529), (432, 1751, -1, -1, -1), (3236, 1751, -1, -1, -1), (3235, 1751, -1, -1, -1), (3344, 40, 5428, 5429, 5430), (7441, 38, 5360, 5361, 5362), (7445, 38, 5360, 5361, 5362), (7473, 38, 5366, 5367, 5368), (7477, 38, 5366, 5367, 5368), (111, 110, 9171, 9172, 9173), (9267, 4174, -1, -1, -1), (9256, 4150, -1, -1, -1), (9259, 2720, -1, -1, -1), (9265, 2732, -1, -1, -1), (9271, 2762, -1, -1, -1), (3202, 3203, 3205, 3206, 3207), (3202, 3203, 3205, 3206, 3207), (3202, 3203, 3205, 3206, 3207), (3202, 3203, 3205, 3206, 3207), (3195, 3196, 3198, 3199, 3200), (3195, 3196, 3198, 3199, 3200), (3195, 3196, 3198, 3199, 3200), (3195, 3196, 3198, 3199, 3200), (3231, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (429, 1751, -1, -1, -1), (3228, 1751, -1, -1, -1), (3227, 1751, -1, -1, -1), (9207, 1751, -1, -1, -1), (12251, 1751, -1, -1, -1), (9208, 1751, -1, -1, -1), (9226, 40, 9230, 9231, 9232), (7481, 7480, 5550, 5551, 5552), (7485, 7484, 5550, 5551, 5552), (7489, 7480, 5550, 5551, 5552), (7493, 7484, 5550, 5551, 5552), (7432, 3843, 5553, 5554, 5555), (7436, 3845, 5553, 5554, 5555), (7505, 38, 5372, 5373, 5374), (7509, 38, 5372, 5373, 5374), (7513, 7512, 5556, 5557, 5558), (7517, 7516, 5556, 5557, 5558), (7521, 7512, 5556, 5557, 5558), (7525, 7516, 5556, 5557, 5558), (7432, 3843, 5559, 5560, 5561), (7436, 3845, 5559, 5560, 5561), (7537, 38, 5378, 5379, 5380), (7541, 38, 5378, 5379, 5380), (4314, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (224, 5452, 4806, 4810, 4814), (242, 5452, 4821, 4825, 4829), (242, 5452, 4821, 4825, 4829), (8644, 2762, -1, -1, -1), (9318, 9347, -1, -1, -1), (242, 135, 4821, 4825, 4829), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (224, 5452, 4806, 4810, 4814), (242, 5452, 4821, 4825, 4829), (242, 5452, 4821, 4825, 4829), (224, 5452, 4806, 4810, 4814), (242, 5452, 4821, 4825, 4829), (242, 5452, 4821, 4825, 4829), (215, 5452, 4456, 4457, 4458)]
    aztecs_architecture = [(6665, 6664, 6659, 6660, 6661), (2575, 2573, 4429, 4430, 4431), (6665, 6664, 6659, 6660, 6661), (6680, 6681, 6676, 6677, 6678), (6680, 6681, 6676, 6677, 6678), (6706, 6705, 6700, 6701, 6702), (6771, 813, -1, -1, -1), (6734, 6733, 6728, 6729, 6730), (6734, 6733, 6728, 6729, 6730), (6734, 6733, 6728, 6729, 6730), (215, 205, 4456, 4457, 4458), (6763, 136, 6758, 6759, 6760), (7042, 7041, 7036, 7037, 7038), (255, -1, 5354, 5355, 5356), (6763, 136, 6758, 6759, 6760), (6779, 6778, 5538, 5539, 5540), (6775, 6774, 5538, 5539, 5540), (6787, 6778, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (6986, 267, 6978, 6979, 6980), (588, 37, 4610, 4611, 4612), (6783, 6774, 5538, 5539, 5540), (7116, 7115, 7110, 7111, 7112), (6794, 3849, 5541, 5542, 5543), (6790, 3847, 5541, 5542, 5543), (6747, 6746, 6741, 6742, 6743), (6951, 6950, 6945, 6946, 6947), (6811, 6810, 5544, 5545, 5546), (7068, 7067, 7062, 7063, 7064), (6658, 6657, 6652, 6653, 6654), (6807, 6806, 5544, 5545, 5546), (6819, 6810, 5544, 5545, 5546), (6815, 6806, 5544, 5545, 5546), (6794, 3849, 5547, 5548, 5549), (6790, 3847, 5547, 5548, 5549), (7061, 7060, 7055, 7056, 7057), (6673, 6674, 6669, 6670, 6671), (6734, 6733, 6728, 6729, 6730), (6673, 6674, 6669, 6670, 6671), (3241, 419, 4563, 4564, 4565), (6958, 6957, 6952, 6953, 6954), (7096, 37, 7150, 7152, 7154), (6923, 6924, 6919, 6920, 6921), (6930, 6931, 6926, 6927, 6928), (6930, 6931, 6926, 6927, 6928), (6706, 6705, 6700, 6701, 6702), (6755, 130, 6750, 6751, 6752), (6964, 2280, 6960, 6961, 6962), (7002, 279, 6994, 6995, 6996), (7018, 291, 7010, 7011, 7012), (7042, 7041, 7036, 7037, 7038), (7068, 7067, 7062, 7063, 7064), (6916, 6915, 6911, 6912, 6913), (6916, 6915, 6911, 6912, 6913), (7084, 7085, 7080, 7081, 7082), (7090, 7091, 7086, 7087, 7088), (7123, 7122, 7117, 7118, 7119), (7131, 7130, 7125, 7126, 7127), (7139, 7138, 7133, 7134, 7135), (6631, 6630, 6626, 6627, 6628), (6710, 1757, -1, -1, -1), (7103, 1900, -1, -1, -1), (6909, 6908, 6904, 6905, 6906), (6916, 6915, 6911, 6912, 6913), (6916, 6915, 6911, 6912, 6913), (7006, 1751, -1, -1, -1), (7001, 1751, -1, -1, -1), (7000, 1751, -1, -1, -1), (6993, 40, 5428, 5429, 5430), (6799, 38, 5360, 5361, 5362), (6803, 38, 5360, 5361, 5362), (6831, 38, 5366, 5367, 5368), (6835, 38, 5366, 5367, 5368), (6698, 6697, 6692, 6693, 6694), (6974, 4174, -1, -1, -1), (6739, 4150, -1, -1, -1), (6768, 2720, -1, -1, -1), (6902, 2732, -1, -1, -1), (7026, 2762, -1, -1, -1), (7049, 7050, 7045, 7046, 7047), (7049, 7050, 7045, 7046, 7047), (7049, 7050, 7045, 7046, 7047), (7049, 7050, 7045, 7046, 7047), (6939, 6940, 6935, 6936, 6937), (6939, 6940, 6935, 6936, 6937), (6939, 6940, 6935, 6936, 6937), (6939, 6940, 6935, 6936, 6937), (7009, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (7022, 1751, -1, -1, -1), (7017, 1751, -1, -1, -1), (7016, 1751, -1, -1, -1), (6990, 1751, -1, -1, -1), (6985, 1751, -1, -1, -1), (6984, 1751, -1, -1, -1), (6977, 40, 5425, 5426, 5427), (6839, 6838, 5550, 5551, 5552), (6843, 6842, 5550, 5551, 5552), (6847, 6838, 5550, 5551, 5552), (6851, 6842, 5550, 5551, 5552), (6790, 3847, 5553, 5554, 5555), (6794, 3849, 5553, 5554, 5555), (6863, 38, 5372, 5373, 5374), (6867, 38, 5372, 5373, 5374), (6871, 6870, 5556, 5557, 5558), (6875, 6874, 5556, 5557, 5558), (6879, 6870, 5556, 5557, 5558), (6883, 6874, 5556, 5557, 5558), (6790, 3847, 5559, 5560, 5561), (6794, 3849, 5559, 5560, 5561), (6895, 38, 5378, 5379, 5380), (6899, 38, 5378, 5379, 5380), (4305, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (6755, 5452, 6750, 6751, 6752), (6763, 5452, 6758, 6759, 6760), (6763, 5452, 6758, 6759, 6760), (8641, 2762, -1, -1, -1), (9315, 9347, -1, -1, -1), (6763, 136, 6758, 6759, 6760), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (6755, 5452, 6750, 6751, 6752), (6763, 5452, 6758, 6759, 6760), (6763, 5452, 6758, 6759, 6760), (6755, 5452, 6750, 6751, 6752), (6763, 5452, 6758, 6759, 6760), (6763, 5452, 6758, 6759, 6760), (215, 5452, 4456, 4457, 4458)]
    mayans_architecture = [(6665, 6664, 6659, 6660, 6661), (2575, 2573, 4429, 4430, 4431), (6665, 6664, 6659, 6660, 6661), (6680, 6681, 6676, 6677, 6678), (6680, 6681, 6676, 6677, 6678), (6706, 6705, 6700, 6701, 6702), (6771, 813, -1, -1, -1), (6734, 6733, 6728, 6729, 6730), (6734, 6733, 6728, 6729, 6730), (6734, 6733, 6728, 6729, 6730), (215, 205, 4456, 4457, 4458), (6763, 136, 6758, 6759, 6760), (7042, 7041, 7036, 7037, 7038), (255, -1, 5354, 5355, 5356), (6763, 136, 6758, 6759, 6760), (6779, 6778, 5538, 5539, 5540), (6775, 6774, 5538, 5539, 5540), (6787, 6778, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (6986, 267, 6978, 6979, 6980), (588, 37, 4610, 4611, 4612), (6783, 6774, 5538, 5539, 5540), (7116, 7115, 7110, 7111, 7112), (6794, 3849, 5541, 5542, 5543), (6790, 3847, 5541, 5542, 5543), (6747, 6746, 6741, 6742, 6743), (6951, 6950, 6945, 6946, 6947), (6811, 6810, 5544, 5545, 5546), (7068, 7067, 7062, 7063, 7064), (6658, 6657, 6652, 6653, 6654), (6807, 6806, 5544, 5545, 5546), (6819, 6810, 5544, 5545, 5546), (6815, 6806, 5544, 5545, 5546), (6794, 3849, 5547, 5548, 5549), (6790, 3847, 5547, 5548, 5549), (7061, 7060, 7055, 7056, 7057), (6673, 6674, 6669, 6670, 6671), (6734, 6733, 6728, 6729, 6730), (6673, 6674, 6669, 6670, 6671), (3241, 419, 4563, 4564, 4565), (6958, 6957, 6952, 6953, 6954), (7096, 37, 7150, 7152, 7154), (6923, 6924, 6919, 6920, 6921), (6930, 6931, 6926, 6927, 6928), (6930, 6931, 6926, 6927, 6928), (6706, 6705, 6700, 6701, 6702), (6755, 130, 6750, 6751, 6752), (6964, 2280, 6960, 6961, 6962), (7002, 279, 6994, 6995, 6996), (7018, 291, 7010, 7011, 7012), (7042, 7041, 7036, 7037, 7038), (7068, 7067, 7062, 7063, 7064), (6916, 6915, 6911, 6912, 6913), (6916, 6915, 6911, 6912, 6913), (7084, 7085, 7080, 7081, 7082), (7090, 7091, 7086, 7087, 7088), (7123, 7122, 7117, 7118, 7119), (7131, 7130, 7125, 7126, 7127), (7139, 7138, 7133, 7134, 7135), (6324, 6321, 6309, 6312, 6315), (6710, 1757, -1, -1, -1), (7103, 1900, -1, -1, -1), (6909, 6908, 6904, 6905, 6906), (6916, 6915, 6911, 6912, 6913), (6916, 6915, 6911, 6912, 6913), (7006, 1751, -1, -1, -1), (7001, 1751, -1, -1, -1), (7000, 1751, -1, -1, -1), (6993, 40, 5428, 5429, 5430), (6799, 38, 5360, 5361, 5362), (6803, 38, 5360, 5361, 5362), (6831, 38, 5366, 5367, 5368), (6835, 38, 5366, 5367, 5368), (6698, 6697, 6692, 6693, 6694), (6974, 4174, -1, -1, -1), (6739, 4150, -1, -1, -1), (6768, 2720, -1, -1, -1), (6902, 2732, -1, -1, -1), (7026, 2762, -1, -1, -1), (7049, 7050, 7045, 7046, 7047), (7049, 7050, 7045, 7046, 7047), (7049, 7050, 7045, 7046, 7047), (7049, 7050, 7045, 7046, 7047), (6939, 6940, 6935, 6936, 6937), (6939, 6940, 6935, 6936, 6937), (6939, 6940, 6935, 6936, 6937), (6939, 6940, 6935, 6936, 6937), (7009, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (7022, 1751, -1, -1, -1), (7017, 1751, -1, -1, -1), (7016, 1751, -1, -1, -1), (6990, 1751, -1, -1, -1), (6985, 1751, -1, -1, -1), (6984, 1751, -1, -1, -1), (6977, 40, 5425, 5426, 5427), (6839, 6838, 5550, 5551, 5552), (6843, 6842, 5550, 5551, 5552), (6847, 6838, 5550, 5551, 5552), (6851, 6842, 5550, 5551, 5552), (6790, 3847, 5553, 5554, 5555), (6794, 3849, 5553, 5554, 5555), (6863, 38, 5372, 5373, 5374), (6867, 38, 5372, 5373, 5374), (6871, 6870, 5556, 5557, 5558), (6875, 6874, 5556, 5557, 5558), (6879, 6870, 5556, 5557, 5558), (6883, 6874, 5556, 5557, 5558), (6790, 3847, 5559, 5560, 5561), (6794, 3849, 5559, 5560, 5561), (6895, 38, 5378, 5379, 5380), (6899, 38, 5378, 5379, 5380), (4305, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (6755, 5452, 6750, 6751, 6752), (6763, 5452, 6758, 6759, 6760), (6763, 5452, 6758, 6759, 6760), (8641, 2762, -1, -1, -1), (9315, 9347, -1, -1, -1), (6763, 136, 6758, 6759, 6760), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (6755, 5452, 6750, 6751, 6752), (6763, 5452, 6758, 6759, 6760), (6763, 5452, 6758, 6759, 6760), (6755, 5452, 6750, 6751, 6752), (6763, 5452, 6758, 6759, 6760), (6763, 5452, 6758, 6759, 6760), (215, 5452, 4456, 4457, 4458)]
    huns_architecture = [(21, 17, 4683, 4687, 4691), (2575, 2573, 4429, 4430, 4431), (21, 17, 4683, 4687, 4691), (62, 66, 4711, 4715, 4719), (62, 66, 4711, 4715, 4719), (102, 98, 4739, 4743, 4747), (4010, 813, -1, -1, -1), (147, 143, 4771, 4775, 4779), (147, 143, 4771, 4775, 4779), (147, 143, 4771, 4775, 4779), (215, 205, 4456, 4457, 4458), (233, 131, 4819, 4823, 4827), (486, 482, 5099, 5103, 5107), (255, -1, 5354, 5355, 5356), (233, 131, 4819, 4823, 4827), (2057, 2053, 5538, 5539, 5540), (2045, 2041, 5538, 5539, 5540), (2081, 2053, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (3250, 262, 5051, 5055, 5059), (588, 37, 4610, 4611, 4612), (2069, 2041, 5538, 5539, 5540), (4199, 4195, 5195, 5199, 5203), (5327, 3829, 5541, 5542, 5543), (5322, 3827, 5541, 5542, 5543), (171, 167, 4787, 4791, 4795), (2265, 2261, 4991, 4995, 4999), (2129, 2125, 5544, 5545, 5546), (522, 518, 5143, 5147, 5151), (9, 5, 4667, 4671, 4675), (2117, 2113, 5544, 5545, 5546), (2153, 2125, 5544, 5545, 5546), (2141, 2113, 5544, 5545, 5546), (5327, 3829, 5547, 5548, 5549), (5322, 3827, 5547, 5548, 5549), (510, 506, 5127, 5131, 5135), (50, 54, 4699, 4703, 4707), (147, 143, 4771, 4775, 4779), (50, 54, 4699, 4703, 4707), (3241, 419, 4563, 4564, 4565), (408, 404, 5007, 5011, 5015), (2021, 37, 3791, 3795, 3799), (365, 369, 4955, 4959, 4963), (377, 381, 4967, 4971, 4975), (377, 381, 4967, 4971, 4975), (102, 98, 4739, 4743, 4747), (221, 125, 4803, 4807, 4811), (3431, 2273, 5023, 5027, 5031), (3262, 274, 5067, 5071, 5075), (3038, 286, 5083, 5087, 5091), (486, 482, 5099, 5103, 5107), (522, 518, 5143, 5147, 5151), (2220, 2216, 4943, 4947, 4951), (2220, 2216, 4943, 4947, 4951), (566, 570, 5171, 5175, 5179), (578, 582, 5183, 5187, 5191), (2529, 2525, 5211, 5215, 5219), (2404, 4183, 5227, 5231, 5235), (2412, 4187, 5243, 5247, 5251), (6323, 6320, 6308, 6311, 6314), (3958, 1757, -1, -1, -1), (3886, 1900, -1, -1, -1), (2206, 2202, 4931, 4935, 4939), (2220, 2216, 4943, 4947, 4951), (2220, 2216, 4943, 4947, 4951), (456, 1751, -1, -1, -1), (3258, 1751, -1, -1, -1), (3254, 1751, -1, -1, -1), (3350, 40, 5428, 5429, 5430), (2536, 38, 5360, 5361, 5362), (2548, 38, 5360, 5361, 5362), (2540, 38, 5366, 5367, 5368), (2556, 38, 5366, 5367, 5368), (90, 86, 4723, 4727, 4731), (4036, 4174, -1, -1, -1), (3985, 4150, -1, -1, -1), (4179, 2720, -1, -1, -1), (4023, 2732, -1, -1, -1), (4049, 2762, -1, -1, -1), (3115, 3119, 5115, 5119, 5123), (3115, 3119, 5115, 5119, 5123), (3115, 3119, 5115, 5119, 5123), (3115, 3119, 5115, 5119, 5123), (3130, 3134, 4979, 4983, 4987), (3130, 3134, 4979, 4983, 4987), (3130, 3134, 4979, 4983, 4987), (3130, 3134, 4979, 4983, 4987), (3354, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (468, 1751, -1, -1, -1), (3034, 1751, -1, -1, -1), (3030, 1751, -1, -1, -1), (444, 1751, -1, -1, -1), (3246, 1751, -1, -1, -1), (3242, 1751, -1, -1, -1), (3346, 40, 5425, 5426, 5427), (3605, 3601, 5550, 5551, 5552), (3617, 3613, 5550, 5551, 5552), (3629, 3601, 5550, 5551, 5552), (3641, 3613, 5550, 5551, 5552), (5322, 3827, 5553, 5554, 5555), (5327, 3829, 5553, 5554, 5555), (3677, 38, 5372, 5373, 5374), (3689, 38, 5372, 5373, 5374), (3701, 3697, 5556, 5557, 5558), (3713, 3709, 5556, 5557, 5558), (3725, 3697, 5556, 5557, 5558), (3737, 3709, 5556, 5557, 5558), (5322, 3827, 5559, 5560, 5561), (5327, 3829, 5559, 5560, 5561), (3773, 38, 5378, 5379, 5380), (3785, 38, 5378, 5379, 5380), (4296, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (221, 5452, 4803, 4807, 4811), (233, 5452, 4819, 4823, 4827), (233, 5452, 4819, 4823, 4827), (8632, 2762, -1, -1, -1), (9306, 9347, -1, -1, -1), (233, 131, 4819, 4823, 4827), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (221, 5452, 4803, 4807, 4811), (233, 5452, 4819, 4823, 4827), (233, 5452, 4819, 4823, 4827), (221, 5452, 4803, 4807, 4811), (233, 5452, 4819, 4823, 4827), (233, 5452, 4819, 4823, 4827), (215, 5452, 4456, 4457, 4458)]
    koreans_architecture = [(22, 18, 4684, 4688, 4692), (2575, 2573, 4429, 4430, 4431), (22, 18, 4684, 4688, 4692), (63, 67, 4712, 4716, 4720), (63, 67, 4712, 4716, 4720), (103, 99, 4740, 4744, 4748), (4011, 813, -1, -1, -1), (148, 144, 4772, 4776, 4780), (148, 144, 4772, 4776, 4780), (148, 144, 4772, 4776, 4780), (215, 205, 4456, 4457, 4458), (234, 132, 4820, 4824, 4828), (487, 483, 5100, 5104, 5108), (255, -1, 5354, 5355, 5356), (234, 132, 4820, 4824, 4828), (2058, 2054, 5538, 5539, 5540), (2046, 2042, 5538, 5539, 5540), (2082, 2054, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (3251, 263, 5052, 5056, 5060), (588, 37, 4610, 4611, 4612), (2070, 2042, 5538, 5539, 5540), (4200, 4196, 5196, 5200, 5204), (5328, 3833, 5541, 5542, 5543), (5323, 3831, 5541, 5542, 5543), (172, 168, 4788, 4792, 4796), (2266, 2262, 4992, 4996, 5000), (2130, 2126, 5544, 5545, 5546), (523, 519, 5144, 5148, 5152), (10, 6, 4668, 4672, 4676), (2118, 2114, 5544, 5545, 5546), (2154, 2126, 5544, 5545, 5546), (2142, 2114, 5544, 5545, 5546), (5328, 3833, 5547, 5548, 5549), (5323, 3831, 5547, 5548, 5549), (511, 507, 5128, 5132, 5136), (51, 55, 4700, 4704, 4708), (148, 144, 4772, 4776, 4780), (51, 55, 4700, 4704, 4708), (3241, 419, 4563, 4564, 4565), (409, 405, 5008, 5012, 5016), (2022, 37, 3792, 3796, 3800), (366, 370, 4956, 4960, 4964), (378, 382, 4968, 4972, 4976), (378, 382, 4968, 4972, 4976), (103, 99, 4740, 4744, 4748), (222, 126, 4804, 4808, 4812), (3432, 2274, 5024, 5028, 5032), (3263, 275, 5068, 5072, 5076), (3039, 287, 5084, 5088, 5092), (487, 483, 5100, 5104, 5108), (523, 519, 5144, 5148, 5152), (2221, 2217, 4944, 4948, 4952), (2221, 2217, 4944, 4948, 4952), (567, 571, 5172, 5176, 5180), (579, 583, 5184, 5188, 5192), (2530, 2526, 5212, 5216, 5220), (2405, 4184, 5228, 5232, 5236), (2413, 4188, 5244, 5248, 5252), (7249, 7248, 7244, 7245, 7246), (3959, 1757, -1, -1, -1), (3887, 1900, -1, -1, -1), (2207, 2203, 4932, 4936, 4940), (2221, 2217, 4944, 4948, 4952), (2221, 2217, 4944, 4948, 4952), (457, 1751, -1, -1, -1), (3259, 1751, -1, -1, -1), (3255, 1751, -1, -1, -1), (3351, 40, 5428, 5429, 5430), (2537, 38, 5360, 5361, 5362), (2549, 38, 5360, 5361, 5362), (2541, 38, 5366, 5367, 5368), (2557, 38, 5366, 5367, 5368), (91, 87, 4724, 4728, 4732), (4037, 4174, -1, -1, -1), (3986, 4150, -1, -1, -1), (4180, 2720, -1, -1, -1), (4024, 2732, -1, -1, -1), (4050, 2762, -1, -1, -1), (3116, 3120, 5116, 5120, 5124), (3116, 3120, 5116, 5120, 5124), (3116, 3120, 5116, 5120, 5124), (3116, 3120, 5116, 5120, 5124), (3131, 3135, 4980, 4984, 4988), (3131, 3135, 4980, 4984, 4988), (3131, 3135, 4980, 4984, 4988), (3131, 3135, 4980, 4984, 4988), (3355, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (469, 1751, -1, -1, -1), (3035, 1751, -1, -1, -1), (3031, 1751, -1, -1, -1), (445, 1751, -1, -1, -1), (3247, 1751, -1, -1, -1), (3243, 1751, -1, -1, -1), (3347, 40, 5425, 5426, 5427), (3606, 3602, 5550, 5551, 5552), (3618, 3614, 5550, 5551, 5552), (3630, 3602, 5550, 5551, 5552), (3642, 3614, 5550, 5551, 5552), (5323, 3831, 5553, 5554, 5555), (5328, 3833, 5553, 5554, 5555), (3678, 38, 5372, 5373, 5374), (3690, 38, 5372, 5373, 5374), (3702, 3698, 5556, 5557, 5558), (3714, 3710, 5556, 5557, 5558), (3726, 3698, 5556, 5557, 5558), (3738, 3710, 5556, 5557, 5558), (5323, 3831, 5559, 5560, 5561), (5328, 3833, 5559, 5560, 5561), (3774, 38, 5378, 5379, 5380), (3786, 38, 5378, 5379, 5380), (4297, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (222, 5452, 4804, 4808, 4812), (234, 5452, 4820, 4824, 4828), (234, 5452, 4820, 4824, 4828), (8635, 2762, -1, -1, -1), (9309, 9347, -1, -1, -1), (234, 132, 4820, 4824, 4828), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (222, 5452, 4804, 4808, 4812), (234, 5452, 4820, 4824, 4828), (234, 5452, 4820, 4824, 4828), (222, 5452, 4804, 4808, 4812), (234, 5452, 4820, 4824, 4828), (234, 5452, 4820, 4824, 4828), (215, 5452, 4456, 4457, 4458)]
    italians_architecture = [(27, 26, 4532, 4533, 4534), (2575, 2573, 4429, 4430, 4431), (27, 26, 4532, 4533, 4534), (71, 72, 4567, 4568, 4569), (71, 72, 4567, 4568, 4569), (108, 107, 4542, 4543, 4544), (9262, 813, -1, -1, -1), (153, 152, 8277, 8278, 8279), (153, 152, 8277, 8278, 8279), (153, 152, 8277, 8278, 8279), (215, 205, 4456, 4457, 4458), (242, 135, 4605, 4606, 4607), (492, 491, 4537, 4538, 4539), (255, -1, 5354, 5355, 5356), (242, 135, 4605, 4606, 4607), (7421, 7420, 5538, 5539, 5540), (7417, 7416, 5538, 5539, 5540), (7429, 7420, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (12249, 266, 9210, 9211, 9212), (588, 37, 4610, 4611, 4612), (7425, 7416, 5538, 5539, 5540), (4171, 4170, 4636, 4637, 4638), (7436, 3845, 5541, 5542, 5543), (7432, 3843, 5541, 5542, 5543), (177, 176, 8295, 8296, 8297), (417, 416, 9177, 9178, 9179), (7453, 7452, 5544, 5545, 5546), (528, 527, 4576, 4577, 4578), (30, 29, 9165, 9166, 9167), (7449, 7448, 5544, 5545, 5546), (7461, 7452, 5544, 5545, 5546), (7457, 7448, 5544, 5545, 5546), (7436, 3845, 5547, 5548, 5549), (7432, 3843, 5547, 5548, 5549), (531, 530, 9216, 9217, 9218), (74, 75, 9191, 9192, 9193), (153, 152, 8277, 8278, 8279), (74, 75, 9191, 9192, 9193), (3241, 419, 4563, 4564, 4565), (414, 413, 4581, 4582, 4583), (7390, 37, 7398, 7400, 7402), (9196, 9197, 9198, 9199, 9200), (386, 387, 4618, 4619, 4620), (386, 387, 4618, 4619, 4620), (108, 107, 4542, 4543, 4544), (9182, 129, 9184, 9185, 9186), (3436, 2278, 4592, 4593, 4594), (3237, 278, 12253, 12254, 12255), (3229, 290, 12258, 12259, 12260), (492, 491, 4537, 4538, 4539), (528, 527, 4576, 4577, 4578), (2226, 2225, 4527, 4528, 4529), (2226, 2225, 4527, 4528, 4529), (593, 594, 4571, 4572, 4573), (596, 597, 4597, 4598, 4599), (2517, 2516, 4613, 4614, 4615), (2395, 2390, 4623, 4624, 4625), (2398, 2391, 4628, 4629, 4630), (3069, 3056, 5275, 5288, 5301), (9241, 1757, -1, -1, -1), (9282, 1900, -1, -1, -1), (9202, 2228, 9203, 9204, 9205), (2226, 2225, 4527, 4528, 4529), (2226, 2225, 4527, 4528, 4529), (432, 1751, -1, -1, -1), (3236, 1751, -1, -1, -1), (3235, 1751, -1, -1, -1), (3344, 40, 5428, 5429, 5430), (7441, 38, 5360, 5361, 5362), (7445, 38, 5360, 5361, 5362), (7473, 38, 5366, 5367, 5368), (7477, 38, 5366, 5367, 5368), (111, 110, 9171, 9172, 9173), (9267, 4174, -1, -1, -1), (9256, 4150, -1, -1, -1), (9259, 2720, -1, -1, -1), (9265, 2732, -1, -1, -1), (9271, 2762, -1, -1, -1), (3202, 3203, 3205, 3206, 3207), (3202, 3203, 3205, 3206, 3207), (3202, 3203, 3205, 3206, 3207), (3202, 3203, 3205, 3206, 3207), (3195, 3196, 3198, 3199, 3200), (3195, 3196, 3198, 3199, 3200), (3195, 3196, 3198, 3199, 3200), (3195, 3196, 3198, 3199, 3200), (3231, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (429, 1751, -1, -1, -1), (3228, 1751, -1, -1, -1), (3227, 1751, -1, -1, -1), (9207, 1751, -1, -1, -1), (12251, 1751, -1, -1, -1), (9208, 1751, -1, -1, -1), (9226, 40, 9230, 9231, 9232), (7481, 7480, 5550, 5551, 5552), (7485, 7484, 5550, 5551, 5552), (7489, 7480, 5550, 5551, 5552), (7493, 7484, 5550, 5551, 5552), (7432, 3843, 5553, 5554, 5555), (7436, 3845, 5553, 5554, 5555), (7505, 38, 5372, 5373, 5374), (7509, 38, 5372, 5373, 5374), (7513, 7512, 5556, 5557, 5558), (7517, 7516, 5556, 5557, 5558), (7521, 7512, 5556, 5557, 5558), (7525, 7516, 5556, 5557, 5558), (7432, 3843, 5559, 5560, 5561), (7436, 3845, 5559, 5560, 5561), (7537, 38, 5378, 5379, 5380), (7541, 38, 5378, 5379, 5380), (4314, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (224, 5452, 4806, 4810, 4814), (242, 5452, 4821, 4825, 4829), (242, 5452, 4821, 4825, 4829), (8644, 2762, -1, -1, -1), (9318, 9347, -1, -1, -1), (242, 135, 4821, 4825, 4829), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (224, 5452, 4806, 4810, 4814), (242, 5452, 4821, 4825, 4829), (242, 5452, 4821, 4825, 4829), (224, 5452, 4806, 4810, 4814), (242, 5452, 4821, 4825, 4829), (242, 5452, 4821, 4825, 4829), (215, 5452, 4456, 4457, 4458)]
    indians_architecture = [(9665, 9664, 9659, 9660, 9661), (2575, 2573, 4429, 4430, 4431), (9665, 9664, 9659, 9660, 9661), (9680, 9681, 9676, 9677, 9678), (9680, 9681, 9676, 9677, 9678), (9706, 9705, 9700, 9701, 9702), (4012, 813, -1, -1, -1), (9734, 9733, 9728, 9729, 9730), (9734, 9733, 9728, 9729, 9730), (9734, 9733, 9728, 9729, 9730), (215, 205, 4456, 4457, 4458), (9763, 10176, 9758, 9759, 9760), (10042, 10041, 10036, 10037, 10038), (255, -1, 5354, 5355, 5356), (9763, 10176, 9758, 9759, 9760), (9779, 9778, 5538, 5539, 5540), (9775, 9774, 5538, 5539, 5540), (9787, 9778, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (9986, 10556, 9978, 9979, 9980), (588, 37, 4610, 4611, 4612), (9783, 9774, 5538, 5539, 5540), (10116, 10115, 10110, 10111, 10112), (9794, 3861, 5541, 5542, 5543), (9790, 3859, 5541, 5542, 5543), (12477, 12478, 12480, 12481, 12482), (9951, 9950, 9945, 9946, 9947), (9811, 9810, 5544, 5545, 5546), (10068, 10067, 10062, 10063, 10064), (9658, 9657, 9652, 9653, 9654), (9807, 9806, 5544, 5545, 5546), (9819, 9810, 5544, 5545, 5546), (9815, 9806, 5544, 5545, 5546), (9794, 3861, 5547, 5548, 5549), (9790, 3859, 5547, 5548, 5549), (10061, 10060, 10055, 10056, 10057), (9673, 9674, 9669, 9670, 9671), (9734, 9733, 9728, 9729, 9730), (9673, 9674, 9669, 9670, 9671), (3241, 419, 4563, 4564, 4565), (9958, 9957, 9952, 9953, 9954), (10096, 37, 10150, 10152, 10154), (9923, 9924, 9919, 9920, 9921), (9930, 9931, 9926, 9927, 9928), (9930, 9931, 9926, 9927, 9928), (9706, 9705, 9700, 9701, 9702), (9755, 10175, 9750, 9751, 9752), (9964, 10174, 9960, 9961, 9962), (10002, 10558, 9994, 9995, 9996), (10018, 10560, 10010, 10011, 10012), (10042, 10041, 10036, 10037, 10038), (10068, 10067, 10062, 10063, 10064), (9916, 9915, 9911, 9912, 9913), (9916, 9915, 9911, 9912, 9913), (10084, 10085, 10080, 10081, 10082), (10090, 10091, 10086, 10087, 10088), (10123, 10122, 10117, 10118, 10119), (10131, 10130, 10125, 10126, 10127), (10139, 10138, 10133, 10134, 10135), (12499, 12500, 12502, 12503, 12504), (3960, 1757, -1, -1, -1), (3888, 1900, -1, -1, -1), (9909, 9908, 9904, 9905, 9906), (9916, 9915, 9911, 9912, 9913), (9916, 9915, 9911, 9912, 9913), (10006, 1751, -1, -1, -1), (10001, 1751, -1, -1, -1), (10000, 1751, -1, -1, -1), (9993, 40, 9994, 9995, 9996), (9799, 38, 5360, 5361, 5362), (9803, 38, 5360, 5361, 5362), (9831, 38, 5366, 5367, 5368), (9835, 38, 5366, 5367, 5368), (9698, 9697, 9692, 9693, 9694), (4038, 4174, -1, -1, -1), (3987, 4150, -1, -1, -1), (4181, 2720, -1, -1, -1), (4025, 2732, -1, -1, -1), (4051, 2762, -1, -1, -1), (10049, 10050, 10045, 10046, 10047), (10049, 10050, 10045, 10046, 10047), (10049, 10050, 10045, 10046, 10047), (10049, 10050, 10045, 10046, 10047), (9939, 9940, 9935, 9936, 9937), (9939, 9940, 9935, 9936, 9937), (9939, 9940, 9935, 9936, 9937), (9939, 9940, 9935, 9936, 9937), (10009, 40, 10010, 10011, 10012), (3223, 4172, 4633, 4634, 4635), (10022, 1751, -1, -1, -1), (10017, 1751, -1, -1, -1), (10016, 1751, -1, -1, -1), (9990, 1751, -1, -1, -1), (9985, 1751, -1, -1, -1), (9984, 1751, -1, -1, -1), (9977, 40, 9978, 9979, 9980), (9839, 9838, 5550, 5551, 5552), (9843, 9842, 5550, 5551, 5552), (9847, 9838, 5550, 5551, 5552), (9851, 9842, 5550, 5551, 5552), (9790, 3859, 5553, 5554, 5555), (9794, 3861, 5553, 5554, 5555), (9863, 38, 5372, 5373, 5374), (9867, 38, 5372, 5373, 5374), (9871, 9870, 5556, 5557, 5558), (9875, 9874, 5556, 5557, 5558), (9879, 9870, 5556, 5557, 5558), (9883, 9874, 5556, 5557, 5558), (9790, 3859, 5559, 5560, 5561), (9794, 3861, 5559, 5560, 5561), (9895, 38, 5378, 5379, 5380), (9899, 38, 5378, 5379, 5380), (4298, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (9755, 5452, 4803, 4807, 4811), (9763, 5452, 4819, 4823, 4827), (9763, 5452, 4819, 4823, 4827), (8638, 2762, -1, -1, -1), (9312, 9347, -1, -1, -1), (9763, 10176, 9758, 9759, 9760), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (9755, 5452, 4803, 4807, 4811), (9763, 5452, 4819, 4823, 4827), (9763, 5452, 4819, 4823, 4827), (9755, 5452, 4803, 4807, 4811), (9763, 5452, 4819, 4823, 4827), (9763, 5452, 4819, 4823, 4827), (215, 5452, 4456, 4457, 4458)]
    incas_architecture = [(6665, 6664, 6659, 6660, 6661), (2575, 2573, 4429, 4430, 4431), (6665, 6664, 6659, 6660, 6661), (6680, 6681, 6676, 6677, 6678), (6680, 6681, 6676, 6677, 6678), (6706, 6705, 6700, 6701, 6702), (6771, 813, -1, -1, -1), (6734, 6733, 6728, 6729, 6730), (6734, 6733, 6728, 6729, 6730), (6734, 6733, 6728, 6729, 6730), (215, 205, 4456, 4457, 4458), (6763, 136, 6758, 6759, 6760), (7042, 7041, 7036, 7037, 7038), (255, -1, 5354, 5355, 5356), (6763, 136, 6758, 6759, 6760), (6779, 6778, 5538, 5539, 5540), (6775, 6774, 5538, 5539, 5540), (6787, 6778, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (6986, 267, 6978, 6979, 6980), (588, 37, 4610, 4611, 4612), (6783, 6774, 5538, 5539, 5540), (7116, 7115, 7110, 7111, 7112), (6794, 3849, 5541, 5542, 5543), (6790, 3847, 5541, 5542, 5543), (6747, 6746, 6741, 6742, 6743), (6951, 6950, 6945, 6946, 6947), (6811, 6810, 5544, 5545, 5546), (7068, 7067, 7062, 7063, 7064), (6658, 6657, 6652, 6653, 6654), (6807, 6806, 5544, 5545, 5546), (6819, 6810, 5544, 5545, 5546), (6815, 6806, 5544, 5545, 5546), (6794, 3849, 5547, 5548, 5549), (6790, 3847, 5547, 5548, 5549), (7061, 7060, 7055, 7056, 7057), (6673, 6674, 6669, 6670, 6671), (6734, 6733, 6728, 6729, 6730), (6673, 6674, 6669, 6670, 6671), (3241, 419, 4563, 4564, 4565), (6958, 6957, 6952, 6953, 6954), (7096, 37, 7150, 7152, 7154), (6923, 6924, 6919, 6920, 6921), (6930, 6931, 6926, 6927, 6928), (6930, 6931, 6926, 6927, 6928), (6706, 6705, 6700, 6701, 6702), (6755, 130, 6750, 6751, 6752), (6964, 2280, 6960, 6961, 6962), (7002, 279, 6994, 6995, 6996), (7018, 291, 7010, 7011, 7012), (7042, 7041, 7036, 7037, 7038), (7068, 7067, 7062, 7063, 7064), (6916, 6915, 6911, 6912, 6913), (6916, 6915, 6911, 6912, 6913), (7084, 7085, 7080, 7081, 7082), (7090, 7091, 7086, 7087, 7088), (7123, 7122, 7117, 7118, 7119), (7131, 7130, 7125, 7126, 7127), (7139, 7138, 7133, 7134, 7135), (3070, 3057, 6309, 6312, 6315), (6710, 1757, -1, -1, -1), (7103, 1900, -1, -1, -1), (6909, 6908, 6904, 6905, 6906), (6916, 6915, 6911, 6912, 6913), (6916, 6915, 6911, 6912, 6913), (7006, 1751, -1, -1, -1), (7001, 1751, -1, -1, -1), (7000, 1751, -1, -1, -1), (6993, 40, 5428, 5429, 5430), (6799, 38, 5360, 5361, 5362), (6803, 38, 5360, 5361, 5362), (6831, 38, 5366, 5367, 5368), (6835, 38, 5366, 5367, 5368), (6698, 6697, 6692, 6693, 6694), (6974, 4174, -1, -1, -1), (6739, 4150, -1, -1, -1), (6768, 2720, -1, -1, -1), (6902, 2732, -1, -1, -1), (7026, 2762, -1, -1, -1), (7049, 7050, 7045, 7046, 7047), (7049, 7050, 7045, 7046, 7047), (7049, 7050, 7045, 7046, 7047), (7049, 7050, 7045, 7046, 7047), (6939, 6940, 6935, 6936, 6937), (6939, 6940, 6935, 6936, 6937), (6939, 6940, 6935, 6936, 6937), (6939, 6940, 6935, 6936, 6937), (7009, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (7022, 1751, -1, -1, -1), (7017, 1751, -1, -1, -1), (7016, 1751, -1, -1, -1), (6990, 1751, -1, -1, -1), (6985, 1751, -1, -1, -1), (6984, 1751, -1, -1, -1), (6977, 40, 5425, 5426, 5427), (6839, 6838, 5550, 5551, 5552), (6843, 6842, 5550, 5551, 5552), (6847, 6838, 5550, 5551, 5552), (6851, 6842, 5550, 5551, 5552), (6790, 3847, 5553, 5554, 5555), (6794, 3849, 5553, 5554, 5555), (6863, 38, 5372, 5373, 5374), (6867, 38, 5372, 5373, 5374), (6871, 6870, 5556, 5557, 5558), (6875, 6874, 5556, 5557, 5558), (6879, 6870, 5556, 5557, 5558), (6883, 6874, 5556, 5557, 5558), (6790, 3847, 5559, 5560, 5561), (6794, 3849, 5559, 5560, 5561), (6895, 38, 5378, 5379, 5380), (6899, 38, 5378, 5379, 5380), (4305, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (6755, 5452, 6750, 6751, 6752), (6763, 5452, 6758, 6759, 6760), (6763, 5452, 6758, 6759, 6760), (8641, 2762, -1, -1, -1), (9315, 9347, -1, -1, -1), (6763, 136, 6758, 6759, 6760), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (6755, 5452, 6750, 6751, 6752), (6763, 5452, 6758, 6759, 6760), (6763, 5452, 6758, 6759, 6760), (6755, 5452, 6750, 6751, 6752), (6763, 5452, 6758, 6759, 6760), (6763, 5452, 6758, 6759, 6760), (215, 5452, 4456, 4457, 4458)]
    magyar_architecture = [(7665, 7664, 7659, 7660, 7661), (2575, 2573, 4429, 4430, 4431), (7665, 7664, 7659, 7660, 7661), (7680, 7681, 7676, 7677, 7678), (7680, 7681, 7676, 7677, 7678), (7706, 7705, 7700, 7701, 7702), (7771, 813, -1, -1, -1), (7734, 7733, 7728, 7729, 7730), (7734, 7733, 7728, 7729, 7730), (7734, 7733, 7728, 7729, 7730), (215, 205, 4456, 4457, 4458), (7763, 7970, 7758, 7759, 7760), (8042, 8041, 8036, 8037, 8038), (255, -1, 5354, 5355, 5356), (7763, 7970, 7758, 7759, 7760), (7779, 7778, 5538, 5539, 5540), (7775, 7774, 5538, 5539, 5540), (7787, 7778, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (7986, 248, 7978, 7979, 7980), (588, 37, 4610, 4611, 4612), (7783, 7774, 5538, 5539, 5540), (8116, 8115, 8110, 8111, 8112), (7794, 3853, 5541, 5542, 5543), (7790, 3851, 5541, 5542, 5543), (7747, 7746, 7741, 7742, 7743), (7951, 7950, 7945, 7946, 7947), (7811, 7810, 5544, 5545, 5546), (8068, 8067, 8062, 8063, 8064), (7658, 7657, 7652, 7653, 7654), (7807, 7806, 5544, 5545, 5546), (7819, 7810, 5544, 5545, 5546), (7815, 7806, 5544, 5545, 5546), (7794, 3853, 5547, 5548, 5549), (7790, 3851, 5547, 5548, 5549), (8061, 8060, 8055, 8056, 8057), (7673, 7674, 7669, 7670, 7671), (7734, 7733, 7728, 7729, 7730), (7673, 7674, 7669, 7670, 7671), (3241, 419, 4563, 4564, 4565), (7958, 7957, 7952, 7953, 7954), (8096, 37, 8150, 8152, 8154), (7923, 7924, 7919, 7920, 7921), (7930, 7931, 7926, 7927, 7928), (7930, 7931, 7926, 7927, 7928), (7706, 7705, 7700, 7701, 7702), (7755, 7969, 7750, 7751, 7752), (7966, 7965, 7960, 7961, 7962), (8002, 250, 7994, 7995, 7996), (8018, 252, 8010, 8011, 8012), (8042, 8041, 8036, 8037, 8038), (8068, 8067, 8062, 8063, 8064), (7916, 7915, 7911, 7912, 7913), (7916, 7915, 7911, 7912, 7913), (8084, 8085, 8080, 8081, 8082), (8090, 8091, 8086, 8087, 8088), (8123, 8122, 8117, 8118, 8119), (8131, 8130, 8125, 8126, 8127), (8139, 8138, 8133, 8134, 8135), (7382, 7381, 6308, 6311, 6314), (7710, 1757, -1, -1, -1), (8103, 1900, -1, -1, -1), (7909, 7908, 7904, 7905, 7906), (7916, 7915, 7911, 7912, 7913), (7916, 7915, 7911, 7912, 7913), (8006, 1751, -1, -1, -1), (8001, 1751, -1, -1, -1), (8000, 1751, -1, -1, -1), (7993, 40, 7994, 7995, 7996), (7799, 38, 5360, 5361, 5362), (7803, 38, 5360, 5361, 5362), (7831, 38, 5366, 5367, 5368), (7835, 38, 5366, 5367, 5368), (7698, 7697, 7692, 7693, 7694), (7974, 4174, -1, -1, -1), (7739, 4150, -1, -1, -1), (7768, 2720, -1, -1, -1), (7902, 2732, -1, -1, -1), (8026, 2762, -1, -1, -1), (8049, 8050, 8045, 8046, 8047), (8049, 8050, 8045, 8046, 8047), (8049, 8050, 8045, 8046, 8047), (8049, 8050, 8045, 8046, 8047), (7939, 7940, 7935, 7936, 7937), (7939, 7940, 7935, 7936, 7937), (7939, 7940, 7935, 7936, 7937), (7939, 7940, 7935, 7936, 7937), (8009, 40, 8010, 8011, 8012), (3223, 4172, 4633, 4634, 4635), (8022, 1751, -1, -1, -1), (8017, 1751, -1, -1, -1), (8016, 1751, -1, -1, -1), (7990, 1751, -1, -1, -1), (7985, 1751, -1, -1, -1), (7984, 1751, -1, -1, -1), (7977, 40, 7978, 7979, 7980), (7839, 7838, 5550, 5551, 5552), (7843, 7842, 5550, 5551, 5552), (7847, 7838, 5550, 5551, 5552), (7851, 7842, 5550, 5551, 5552), (7790, 3851, 5553, 5554, 5555), (7794, 3853, 5553, 5554, 5555), (7863, 38, 5372, 5373, 5374), (7867, 38, 5372, 5373, 5374), (7871, 7870, 5556, 5557, 5558), (7875, 7874, 5556, 5557, 5558), (7879, 7870, 5556, 5557, 5558), (7883, 7874, 5556, 5557, 5558), (7790, 3851, 5559, 5560, 5561), (7794, 3853, 5559, 5560, 5561), (7895, 38, 5378, 5379, 5380), (7899, 38, 5378, 5379, 5380), (4308, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (221, 5452, 4803, 4807, 4811), (233, 5452, 4819, 4823, 4827), (233, 5452, 4819, 4823, 4827), (8647, 2762, -1, -1, -1), (9321, 9347, -1, -1, -1), (7763, 7970, 7758, 7759, 7760), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (221, 5452, 4803, 4807, 4811), (233, 5452, 4819, 4823, 4827), (233, 5452, 4819, 4823, 4827), (221, 5452, 4803, 4807, 4811), (233, 5452, 4819, 4823, 4827), (233, 5452, 4819, 4823, 4827), (215, 5452, 4456, 4457, 4458)]
    slavs_architecture = [(7665, 7664, 7659, 7660, 7661), (2575, 2573, 4429, 4430, 4431), (7665, 7664, 7659, 7660, 7661), (7680, 7681, 7676, 7677, 7678), (7680, 7681, 7676, 7677, 7678), (7706, 7705, 7700, 7701, 7702), (7771, 813, -1, -1, -1), (7734, 7733, 7728, 7729, 7730), (7734, 7733, 7728, 7729, 7730), (7734, 7733, 7728, 7729, 7730), (215, 205, 4456, 4457, 4458), (7763, 7970, 7758, 7759, 7760), (8042, 8041, 8036, 8037, 8038), (255, -1, 5354, 5355, 5356), (7763, 7970, 7758, 7759, 7760), (7779, 7778, 5538, 5539, 5540), (7775, 7774, 5538, 5539, 5540), (7787, 7778, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (7986, 248, 7978, 7979, 7980), (588, 37, 4610, 4611, 4612), (7783, 7774, 5538, 5539, 5540), (8116, 8115, 8110, 8111, 8112), (7794, 3853, 5541, 5542, 5543), (7790, 3851, 5541, 5542, 5543), (7747, 7746, 7741, 7742, 7743), (7951, 7950, 7945, 7946, 7947), (7811, 7810, 5544, 5545, 5546), (8068, 8067, 8062, 8063, 8064), (7658, 7657, 7652, 7653, 7654), (7807, 7806, 5544, 5545, 5546), (7819, 7810, 5544, 5545, 5546), (7815, 7806, 5544, 5545, 5546), (7794, 3853, 5547, 5548, 5549), (7790, 3851, 5547, 5548, 5549), (8061, 8060, 8055, 8056, 8057), (7673, 7674, 7669, 7670, 7671), (7734, 7733, 7728, 7729, 7730), (7673, 7674, 7669, 7670, 7671), (3241, 419, 4563, 4564, 4565), (7958, 7957, 7952, 7953, 7954), (8096, 37, 8150, 8152, 8154), (7923, 7924, 7919, 7920, 7921), (7930, 7931, 7926, 7927, 7928), (7930, 7931, 7926, 7927, 7928), (7706, 7705, 7700, 7701, 7702), (7755, 7969, 7750, 7751, 7752), (7966, 7965, 7960, 7961, 7962), (8002, 250, 7994, 7995, 7996), (8018, 252, 8010, 8011, 8012), (8042, 8041, 8036, 8037, 8038), (8068, 8067, 8062, 8063, 8064), (7916, 7915, 7911, 7912, 7913), (7916, 7915, 7911, 7912, 7913), (8084, 8085, 8080, 8081, 8082), (8090, 8091, 8086, 8087, 8088), (8123, 8122, 8117, 8118, 8119), (8131, 8130, 8125, 8126, 8127), (8139, 8138, 8133, 8134, 8135), (7648, 7647, 6308, 6311, 6314), (7710, 1757, -1, -1, -1), (8103, 1900, -1, -1, -1), (7909, 7908, 7904, 7905, 7906), (7916, 7915, 7911, 7912, 7913), (7916, 7915, 7911, 7912, 7913), (8006, 1751, -1, -1, -1), (8001, 1751, -1, -1, -1), (8000, 1751, -1, -1, -1), (7993, 40, 7994, 7995, 7996), (7799, 38, 5360, 5361, 5362), (7803, 38, 5360, 5361, 5362), (7831, 38, 5366, 5367, 5368), (7835, 38, 5366, 5367, 5368), (7698, 7697, 7692, 7693, 7694), (7974, 4174, -1, -1, -1), (7739, 4150, -1, -1, -1), (7768, 2720, -1, -1, -1), (7902, 2732, -1, -1, -1), (8026, 2762, -1, -1, -1), (8049, 8050, 8045, 8046, 8047), (8049, 8050, 8045, 8046, 8047), (8049, 8050, 8045, 8046, 8047), (8049, 8050, 8045, 8046, 8047), (7939, 7940, 7935, 7936, 7937), (7939, 7940, 7935, 7936, 7937), (7939, 7940, 7935, 7936, 7937), (7939, 7940, 7935, 7936, 7937), (8009, 40, 8010, 8011, 8012), (3223, 4172, 4633, 4634, 4635), (8022, 1751, -1, -1, -1), (8017, 1751, -1, -1, -1), (8016, 1751, -1, -1, -1), (7990, 1751, -1, -1, -1), (7985, 1751, -1, -1, -1), (7984, 1751, -1, -1, -1), (7977, 40, 7978, 7979, 7980), (7839, 7838, 5550, 5551, 5552), (7843, 7842, 5550, 5551, 5552), (7847, 7838, 5550, 5551, 5552), (7851, 7842, 5550, 5551, 5552), (7790, 3851, 5553, 5554, 5555), (7794, 3853, 5553, 5554, 5555), (7863, 38, 5372, 5373, 5374), (7867, 38, 5372, 5373, 5374), (7871, 7870, 5556, 5557, 5558), (7875, 7874, 5556, 5557, 5558), (7879, 7870, 5556, 5557, 5558), (7883, 7874, 5556, 5557, 5558), (7790, 3851, 5559, 5560, 5561), (7794, 3853, 5559, 5560, 5561), (7895, 38, 5378, 5379, 5380), (7899, 38, 5378, 5379, 5380), (4308, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (7755, 5452, 4803, 4807, 4811), (7763, 5452, 4819, 4823, 4827), (7763, 5452, 4819, 4823, 4827), (8647, 2762, -1, -1, -1), (9321, 9347, -1, -1, -1), (7763, 7970, 7758, 7759, 7760), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (7755, 5452, 4803, 4807, 4811), (7763, 5452, 4819, 4823, 4827), (7763, 5452, 4819, 4823, 4827), (7755, 5452, 4803, 4807, 4811), (7763, 5452, 4819, 4823, 4827), (7763, 5452, 4819, 4823, 4827), (215, 5452, 4456, 4457, 4458)]
    portuguese_architecture = [(27, 26, 4532, 4533, 4534), (2575, 2573, 4429, 4430, 4431), (27, 26, 4532, 4533, 4534), (71, 72, 4567, 4568, 4569), (71, 72, 4567, 4568, 4569), (108, 107, 4542, 4543, 4544), (9262, 813, -1, -1, -1), (153, 152, 8277, 8278, 8279), (153, 152, 8277, 8278, 8279), (153, 152, 8277, 8278, 8279), (215, 205, 4456, 4457, 4458), (242, 135, 4605, 4606, 4607), (492, 491, 4537, 4538, 4539), (255, -1, 5354, 5355, 5356), (242, 135, 4605, 4606, 4607), (7421, 7420, 5538, 5539, 5540), (7417, 7416, 5538, 5539, 5540), (7429, 7420, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (12249, 266, 9210, 9211, 9212), (588, 37, 4610, 4611, 4612), (7425, 7416, 5538, 5539, 5540), (4171, 4170, 4636, 4637, 4638), (7436, 3845, 5541, 5542, 5543), (7432, 3843, 5541, 5542, 5543), (177, 176, 8295, 8296, 8297), (417, 416, 9177, 9178, 9179), (7453, 7452, 5544, 5545, 5546), (528, 527, 4576, 4577, 4578), (30, 29, 9165, 9166, 9167), (7449, 7448, 5544, 5545, 5546), (7461, 7452, 5544, 5545, 5546), (7457, 7448, 5544, 5545, 5546), (7436, 3845, 5547, 5548, 5549), (7432, 3843, 5547, 5548, 5549), (531, 530, 9216, 9217, 9218), (74, 75, 9191, 9192, 9193), (153, 152, 8277, 8278, 8279), (74, 75, 9191, 9192, 9193), (3241, 419, 4563, 4564, 4565), (414, 413, 4581, 4582, 4583), (7390, 37, 7398, 7400, 7402), (9196, 9197, 9198, 9199, 9200), (386, 387, 4618, 4619, 4620), (386, 387, 4618, 4619, 4620), (108, 107, 4542, 4543, 4544), (9182, 129, 9184, 9185, 9186), (3436, 2278, 4592, 4593, 4594), (3237, 278, 12253, 12254, 12255), (3229, 290, 5086, 5090, 5094), (492, 491, 4537, 4538, 4539), (528, 527, 4576, 4577, 4578), (2226, 2225, 4527, 4528, 4529), (2226, 2225, 4527, 4528, 4529), (593, 594, 4571, 4572, 4573), (596, 597, 4597, 4598, 4599), (2517, 2516, 4613, 4614, 4615), (2395, 2390, 4623, 4624, 4625), (2398, 2391, 4628, 4629, 4630), (8396, 9368, 5275, 5288, 5301), (9241, 1757, -1, -1, -1), (9282, 1900, -1, -1, -1), (9202, 2228, 9203, 9204, 9205), (2226, 2225, 4527, 4528, 4529), (2226, 2225, 4527, 4528, 4529), (432, 1751, -1, -1, -1), (3236, 1751, -1, -1, -1), (3235, 1751, -1, -1, -1), (3344, 40, 5428, 5429, 5430), (7441, 38, 5360, 5361, 5362), (7445, 38, 5360, 5361, 5362), (7473, 38, 5366, 5367, 5368), (7477, 38, 5366, 5367, 5368), (111, 110, 9171, 9172, 9173), (9267, 4174, -1, -1, -1), (9256, 4150, -1, -1, -1), (9259, 2720, -1, -1, -1), (9265, 2732, -1, -1, -1), (9271, 2762, -1, -1, -1), (3202, 3203, 3205, 3206, 3207), (3202, 3203, 3205, 3206, 3207), (3202, 3203, 3205, 3206, 3207), (3202, 3203, 3205, 3206, 3207), (3195, 3196, 3198, 3199, 3200), (3195, 3196, 3198, 3199, 3200), (3195, 3196, 3198, 3199, 3200), (3195, 3196, 3198, 3199, 3200), (3231, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (429, 1751, -1, -1, -1), (3228, 1751, -1, -1, -1), (3227, 1751, -1, -1, -1), (9207, 1751, -1, -1, -1), (12251, 1751, -1, -1, -1), (9208, 1751, -1, -1, -1), (9226, 40, 9230, 9231, 9232), (7481, 7480, 5550, 5551, 5552), (7485, 7484, 5550, 5551, 5552), (7489, 7480, 5550, 5551, 5552), (7493, 7484, 5550, 5551, 5552), (7432, 3843, 5553, 5554, 5555), (7436, 3845, 5553, 5554, 5555), (7505, 38, 5372, 5373, 5374), (7509, 38, 5372, 5373, 5374), (7513, 7512, 5556, 5557, 5558), (7517, 7516, 5556, 5557, 5558), (7521, 7512, 5556, 5557, 5558), (7525, 7516, 5556, 5557, 5558), (7432, 3843, 5559, 5560, 5561), (7436, 3845, 5559, 5560, 5561), (7537, 38, 5378, 5379, 5380), (7541, 38, 5378, 5379, 5380), (4314, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (224, 5452, 4806, 4810, 4814), (242, 5452, 4821, 4825, 4829), (242, 5452, 4821, 4825, 4829), (8644, 2762, -1, -1, -1), (9318, 9347, -1, -1, -1), (242, 135, 4821, 4825, 4829), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (224, 5452, 4806, 4810, 4814), (242, 5452, 4821, 4825, 4829), (242, 5452, 4821, 4825, 4829), (224, 5452, 4806, 4810, 4814), (242, 5452, 4821, 4825, 4829), (242, 5452, 4821, 4825, 4829), (215, 5452, 4456, 4457, 4458)]
    ethiopians_architecture = [(8665, 8664, 8659, 8660, 8661), (2575, 2573, 4429, 4430, 4431), (8665, 8664, 8659, 8660, 8661), (8680, 8681, 8676, 8677, 8678), (8680, 8681, 8676, 8677, 8678), (8706, 8705, 8700, 8701, 8702), (8771, 813, -1, -1, -1), (8734, 8733, 8728, 8729, 8730), (8734, 8733, 8728, 8729, 8730), (8734, 8733, 8728, 8729, 8730), (215, 205, 4456, 4457, 4458), (8763, 9361, 8758, 8759, 8760), (9042, 9041, 9036, 9037, 9038), (255, -1, 5354, 5355, 5356), (8763, 9361, 8758, 8759, 8760), (8779, 8778, 5538, 5539, 5540), (8775, 8774, 5538, 5539, 5540), (8787, 8778, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (8986, 9363, 8978, 8979, 8980), (588, 37, 4610, 4611, 4612), (8783, 8774, 5538, 5539, 5540), (9116, 9115, 9110, 9111, 9112), (8794, 3857, 5541, 5542, 5543), (8790, 3855, 5541, 5542, 5543), (8747, 8746, 8741, 8742, 8743), (8951, 8950, 8945, 8946, 8947), (8811, 8810, 5544, 5545, 5546), (9068, 9067, 9062, 9063, 9064), (8658, 8657, 8652, 8653, 8654), (8807, 8806, 5544, 5545, 5546), (8819, 8810, 5544, 5545, 5546), (8815, 8806, 5544, 5545, 5546), (8794, 3857, 5547, 5548, 5549), (8790, 3855, 5547, 5548, 5549), (9061, 9060, 9055, 9056, 9057), (8673, 8674, 8669, 8670, 8671), (8734, 8733, 8728, 8729, 8730), (8673, 8674, 8669, 8670, 8671), (3241, 419, 4563, 4564, 4565), (8958, 8957, 8952, 8953, 8954), (9096, 37, 9150, 9152, 9154), (8923, 8924, 8919, 8920, 8921), (8930, 8931, 8926, 8927, 8928), (8930, 8931, 8926, 8927, 8928), (8706, 8705, 8700, 8701, 8702), (8755, 9360, 8750, 8751, 8752), (8964, 9359, 8960, 8961, 8962), (9002, 9365, 8994, 8995, 8996), (9018, 9367, 9010, 9011, 9012), (9042, 9041, 9036, 9037, 9038), (9068, 9067, 9062, 9063, 9064), (8916, 8915, 8911, 8912, 8913), (8916, 8915, 8911, 8912, 8913), (9084, 9085, 9080, 9081, 9082), (9090, 9091, 9086, 9087, 9088), (9123, 9122, 9117, 9118, 9119), (9131, 9130, 9125, 9126, 9127), (9139, 9138, 9133, 9134, 9135), (8398, 9369, 8410, 8411, 8412), (8710, 1757, -1, -1, -1), (9103, 1900, -1, -1, -1), (8909, 8908, 8904, 8905, 8906), (8916, 8915, 8911, 8912, 8913), (8916, 8915, 8911, 8912, 8913), (9006, 1751, -1, -1, -1), (9001, 1751, -1, -1, -1), (9000, 1751, -1, -1, -1), (8993, 40, 8994, 8995, 8996), (8799, 38, 5360, 5361, 5362), (8803, 38, 5360, 5361, 5362), (8831, 38, 5366, 5367, 5368), (8835, 38, 5366, 5367, 5368), (8698, 8697, 8692, 8693, 8694), (8974, 4174, -1, -1, -1), (8739, 4150, -1, -1, -1), (8768, 2720, -1, -1, -1), (8902, 2732, -1, -1, -1), (9026, 2762, -1, -1, -1), (9049, 9050, 9045, 9046, 9047), (9049, 9050, 9045, 9046, 9047), (9049, 9050, 9045, 9046, 9047), (9049, 9050, 9045, 9046, 9047), (8939, 8940, 8935, 8936, 8937), (8939, 8940, 8935, 8936, 8937), (8939, 8940, 8935, 8936, 8937), (8939, 8940, 8935, 8936, 8937), (9009, 40, 9010, 9011, 9012), (3223, 4172, 4633, 4634, 4635), (9022, 1751, -1, -1, -1), (9017, 1751, -1, -1, -1), (9016, 1751, -1, -1, -1), (8990, 1751, -1, -1, -1), (8985, 1751, -1, -1, -1), (8984, 1751, -1, -1, -1), (8977, 40, 8978, 8979, 8980), (8839, 8838, 5550, 5551, 5552), (8843, 8842, 5550, 5551, 5552), (8847, 8838, 5550, 5551, 5552), (8851, 8842, 5550, 5551, 5552), (8790, 3855, 5553, 5554, 5555), (8794, 3857, 5553, 5554, 5555), (8863, 38, 5372, 5373, 5374), (8867, 38, 5372, 5373, 5374), (8871, 8870, 5556, 5557, 5558), (8875, 8874, 5556, 5557, 5558), (8879, 8870, 5556, 5557, 5558), (8883, 8874, 5556, 5557, 5558), (8790, 3855, 5559, 5560, 5561), (8794, 3857, 5559, 5560, 5561), (8895, 38, 5378, 5379, 5380), (8899, 38, 5378, 5379, 5380), (4311, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (8755, 5452, 4803, 4807, 4811), (8763, 5452, 4819, 4823, 4827), (8763, 5452, 4819, 4823, 4827), (8650, 2762, -1, -1, -1), (9324, 9347, -1, -1, -1), (8763, 9361, 8758, 8759, 8760), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (8755, 5452, 4803, 4807, 4811), (8763, 5452, 4819, 4823, 4827), (8763, 5452, 4819, 4823, 4827), (8755, 5452, 4803, 4807, 4811), (8763, 5452, 4819, 4823, 4827), (8763, 5452, 4819, 4823, 4827), (215, 5452, 4456, 4457, 4458)]
    malians_architecture = [(8665, 8664, 8659, 8660, 8661), (2575, 2573, 4429, 4430, 4431), (8665, 8664, 8659, 8660, 8661), (8680, 8681, 8676, 8677, 8678), (8680, 8681, 8676, 8677, 8678), (8706, 8705, 8700, 8701, 8702), (8771, 813, -1, -1, -1), (8734, 8733, 8728, 8729, 8730), (8734, 8733, 8728, 8729, 8730), (8734, 8733, 8728, 8729, 8730), (215, 205, 4456, 4457, 4458), (8763, 9361, 8758, 8759, 8760), (9042, 9041, 9036, 9037, 9038), (255, -1, 5354, 5355, 5356), (8763, 9361, 8758, 8759, 8760), (8779, 8778, 5538, 5539, 5540), (8775, 8774, 5538, 5539, 5540), (8787, 8778, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (8986, 9363, 8978, 8979, 8980), (588, 37, 4610, 4611, 4612), (8783, 8774, 5538, 5539, 5540), (9116, 9115, 9110, 9111, 9112), (8794, 3857, 5541, 5542, 5543), (8790, 3855, 5541, 5542, 5543), (8747, 8746, 8741, 8742, 8743), (8951, 8950, 8945, 8946, 8947), (8811, 8810, 5544, 5545, 5546), (9068, 9067, 9062, 9063, 9064), (8658, 8657, 8652, 8653, 8654), (8807, 8806, 5544, 5545, 5546), (8819, 8810, 5544, 5545, 5546), (8815, 8806, 5544, 5545, 5546), (8794, 3857, 5547, 5548, 5549), (8790, 3855, 5547, 5548, 5549), (9061, 9060, 9055, 9056, 9057), (8673, 8674, 8669, 8670, 8671), (8734, 8733, 8728, 8729, 8730), (8673, 8674, 8669, 8670, 8671), (3241, 419, 4563, 4564, 4565), (8958, 8957, 8952, 8953, 8954), (9096, 37, 9150, 9152, 9154), (8923, 8924, 8919, 8920, 8921), (8930, 8931, 8926, 8927, 8928), (8930, 8931, 8926, 8927, 8928), (8706, 8705, 8700, 8701, 8702), (8755, 9360, 8750, 8751, 8752), (8964, 9359, 8960, 8961, 8962), (9002, 9365, 8994, 8995, 8996), (9018, 9367, 9010, 9011, 9012), (9042, 9041, 9036, 9037, 9038), (9068, 9067, 9062, 9063, 9064), (8916, 8915, 8911, 8912, 8913), (8916, 8915, 8911, 8912, 8913), (9084, 9085, 9080, 9081, 9082), (9090, 9091, 9086, 9087, 9088), (9123, 9122, 9117, 9118, 9119), (9131, 9130, 9125, 9126, 9127), (9139, 9138, 9133, 9134, 9135), (8400, 9370, 8413, 8414, 8415), (8710, 1757, -1, -1, -1), (9103, 1900, -1, -1, -1), (8909, 8908, 8904, 8905, 8906), (8916, 8915, 8911, 8912, 8913), (8916, 8915, 8911, 8912, 8913), (9006, 1751, -1, -1, -1), (9001, 1751, -1, -1, -1), (9000, 1751, -1, -1, -1), (8993, 40, 8994, 8995, 8996), (8799, 38, 5360, 5361, 5362), (8803, 38, 5360, 5361, 5362), (8831, 38, 5366, 5367, 5368), (8835, 38, 5366, 5367, 5368), (8698, 8697, 8692, 8693, 8694), (8974, 4174, -1, -1, -1), (8739, 4150, -1, -1, -1), (8768, 2720, -1, -1, -1), (8902, 2732, -1, -1, -1), (9026, 2762, -1, -1, -1), (9049, 9050, 9045, 9046, 9047), (9049, 9050, 9045, 9046, 9047), (9049, 9050, 9045, 9046, 9047), (9049, 9050, 9045, 9046, 9047), (8939, 8940, 8935, 8936, 8937), (8939, 8940, 8935, 8936, 8937), (8939, 8940, 8935, 8936, 8937), (8939, 8940, 8935, 8936, 8937), (9009, 40, 9010, 9011, 9012), (3223, 4172, 4633, 4634, 4635), (9022, 1751, -1, -1, -1), (9017, 1751, -1, -1, -1), (9016, 1751, -1, -1, -1), (8990, 1751, -1, -1, -1), (8985, 1751, -1, -1, -1), (8984, 1751, -1, -1, -1), (8977, 40, 8978, 8979, 8980), (8839, 8838, 5550, 5551, 5552), (8843, 8842, 5550, 5551, 5552), (8847, 8838, 5550, 5551, 5552), (8851, 8842, 5550, 5551, 5552), (8790, 3855, 5553, 5554, 5555), (8794, 3857, 5553, 5554, 5555), (8863, 38, 5372, 5373, 5374), (8867, 38, 5372, 5373, 5374), (8871, 8870, 5556, 5557, 5558), (8875, 8874, 5556, 5557, 5558), (8879, 8870, 5556, 5557, 5558), (8883, 8874, 5556, 5557, 5558), (8790, 3855, 5559, 5560, 5561), (8794, 3857, 5559, 5560, 5561), (8895, 38, 5378, 5379, 5380), (8899, 38, 5378, 5379, 5380), (4311, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (8755, 5452, 4803, 4807, 4811), (8763, 5452, 4819, 4823, 4827), (8763, 5452, 4819, 4823, 4827), (8650, 2762, -1, -1, -1), (9324, 9347, -1, -1, -1), (8763, 9361, 8758, 8759, 8760), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (8755, 5452, 4803, 4807, 4811), (8763, 5452, 4819, 4823, 4827), (8763, 5452, 4819, 4823, 4827), (8755, 5452, 4803, 4807, 4811), (8763, 5452, 4819, 4823, 4827), (8763, 5452, 4819, 4823, 4827), (215, 5452, 4456, 4457, 4458)]
    berbers_architecture = [(23, 19, 4685, 4689, 4693), (2575, 2573, 4429, 4430, 4431), (23, 19, 4685, 4689, 4693), (64, 68, 4713, 4717, 4721), (64, 68, 4713, 4717, 4721), (104, 100, 4741, 4745, 4749), (4012, 813, -1, -1, -1), (149, 145, 4773, 4777, 4781), (149, 145, 4773, 4777, 4781), (149, 145, 4773, 4777, 4781), (215, 205, 4456, 4457, 4458), (235, 133, 4821, 4825, 4829), (488, 484, 5101, 5105, 5109), (255, -1, 5354, 5355, 5356), (235, 133, 4821, 4825, 4829), (2059, 2055, 5538, 5539, 5540), (2047, 2043, 5538, 5539, 5540), (2083, 2055, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (3252, 264, 5053, 5057, 5061), (588, 37, 4610, 4611, 4612), (2071, 2043, 5538, 5539, 5540), (4201, 4197, 5197, 5201, 5205), (5330, 3837, 5541, 5542, 5543), (5325, 3835, 5541, 5542, 5543), (173, 169, 4789, 4793, 4797), (2267, 2263, 4993, 4997, 5001), (2131, 2127, 5544, 5545, 5546), (524, 520, 5145, 5149, 5153), (11, 7, 4669, 4673, 4677), (2119, 2115, 5544, 5545, 5546), (2155, 2127, 5544, 5545, 5546), (2143, 2115, 5544, 5545, 5546), (5330, 3837, 5547, 5548, 5549), (5325, 3835, 5547, 5548, 5549), (512, 508, 5129, 5133, 5137), (52, 56, 4701, 4705, 4709), (149, 145, 4773, 4777, 4781), (52, 56, 4701, 4705, 4709), (3241, 419, 4563, 4564, 4565), (410, 406, 5009, 5013, 5017), (2023, 37, 3793, 3797, 3801), (367, 371, 4957, 4961, 4965), (379, 383, 4969, 4973, 4977), (379, 383, 4969, 4973, 4977), (104, 100, 4741, 4745, 4749), (223, 127, 4805, 4809, 4813), (3433, 2275, 5025, 5029, 5033), (3264, 276, 5069, 5073, 5077), (3040, 288, 5085, 5089, 5093), (488, 484, 5101, 5105, 5109), (524, 520, 5145, 5149, 5153), (2222, 2218, 4945, 4949, 4953), (2222, 2218, 4945, 4949, 4953), (568, 572, 5173, 5177, 5181), (580, 584, 5185, 5189, 5193), (2531, 2527, 5213, 5217, 5221), (2406, 4185, 5229, 5233, 5237), (2414, 4189, 5245, 5249, 5253), (8402, 9371, 8416, 8417, 8418), (3960, 1757, -1, -1, -1), (3888, 1900, -1, -1, -1), (2208, 2204, 4933, 4937, 4941), (2222, 2218, 4945, 4949, 4953), (2222, 2218, 4945, 4949, 4953), (458, 1751, -1, -1, -1), (3260, 1751, -1, -1, -1), (3256, 1751, -1, -1, -1), (3352, 40, 5428, 5429, 5430), (2538, 38, 5360, 5361, 5362), (2550, 38, 5360, 5361, 5362), (2542, 38, 5366, 5367, 5368), (2558, 38, 5366, 5367, 5368), (92, 88, 4725, 4729, 4733), (4038, 4174, -1, -1, -1), (3987, 4150, -1, -1, -1), (4181, 2720, -1, -1, -1), (4025, 2732, -1, -1, -1), (4051, 2762, -1, -1, -1), (3117, 3121, 5117, 5121, 5125), (3117, 3121, 5117, 5121, 5125), (3117, 3121, 5117, 5121, 5125), (3117, 3121, 5117, 5121, 5125), (3132, 3136, 4981, 4985, 4989), (3132, 3136, 4981, 4985, 4989), (3132, 3136, 4981, 4985, 4989), (3132, 3136, 4981, 4985, 4989), (3356, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (470, 1751, -1, -1, -1), (3036, 1751, -1, -1, -1), (3032, 1751, -1, -1, -1), (446, 1751, -1, -1, -1), (3248, 1751, -1, -1, -1), (3244, 1751, -1, -1, -1), (3348, 40, 5425, 5426, 5427), (3607, 3603, 5550, 5551, 5552), (3619, 3615, 5550, 5551, 5552), (3631, 3603, 5550, 5551, 5552), (3643, 3615, 5550, 5551, 5552), (5325, 3835, 5553, 5554, 5555), (5330, 3837, 5553, 5554, 5555), (3679, 38, 5372, 5373, 5374), (3691, 38, 5372, 5373, 5374), (3703, 3699, 5556, 5557, 5558), (3715, 3711, 5556, 5557, 5558), (3727, 3699, 5556, 5557, 5558), (3739, 3711, 5556, 5557, 5558), (5325, 3835, 5559, 5560, 5561), (5330, 3837, 5559, 5560, 5561), (3775, 38, 5378, 5379, 5380), (3787, 38, 5378, 5379, 5380), (4298, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (223, 5452, 4805, 4809, 4813), (235, 5452, 4821, 4825, 4829), (235, 5452, 4821, 4825, 4829), (8638, 2762, -1, -1, -1), (9312, 9347, -1, -1, -1), (235, 133, 4821, 4825, 4829), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (223, 5452, 4805, 4809, 4813), (235, 5452, 4821, 4825, 4829), (235, 5452, 4821, 4825, 4829), (223, 5452, 4805, 4809, 4813), (235, 5452, 4821, 4825, 4829), (235, 5452, 4821, 4825, 4829), (215, 5452, 4456, 4457, 4458)]
    khmer_architecture = [(10665, 10664, 10659, 10660, 10661), (2575, 2573, 4429, 4430, 4431), (10665, 10664, 10659, 10660, 10661), (10680, 10681, 10676, 10677, 10678), (10680, 10681, 10676, 10677, 10678), (10706, 10705, 10700, 10701, 10702), (10771, 813, -1, -1, -1), (10734, 10733, 10728, 10729, 10730), (10734, 10733, 10728, 10729, 10730), (10734, 10733, 10728, 10729, 10730), (215, 205, 4456, 4457, 4458), (10763, 11167, 10758, 10759, 10760), (11042, 11041, 11036, 11037, 11038), (255, -1, 5354, 5355, 5356), (10763, 11167, 10758, 10759, 10760), (10779, 10778, 5538, 5539, 5540), (10775, 10774, 5538, 5539, 5540), (10787, 10778, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (10986, 11205, 10978, 10979, 10980), (588, 37, 4610, 4611, 4612), (10783, 10774, 5538, 5539, 5540), (11116, 11115, 11110, 11111, 11112), (10794, 3865, 5541, 5542, 5543), (10790, 3863, 5541, 5542, 5543), (10747, 10746, 10741, 10742, 10743), (10951, 10950, 10945, 10946, 10947), (10811, 10810, 5544, 5545, 5546), (11068, 11067, 11062, 11063, 11064), (10658, 10657, 10652, 10653, 10654), (10807, 10806, 5544, 5545, 5546), (10819, 10810, 5544, 5545, 5546), (10815, 10806, 5544, 5545, 5546), (10794, 3865, 5547, 5548, 5549), (10790, 3863, 5547, 5548, 5549), (11061, 11060, 11055, 11056, 11057), (10673, 10674, 10669, 10670, 10671), (10734, 10733, 10728, 10729, 10730), (10673, 10674, 10669, 10670, 10671), (3241, 419, 4563, 4564, 4565), (10958, 10957, 10952, 10953, 10954), (11096, 37, 11150, 11152, 11154), (10923, 10924, 10919, 10920, 10921), (10930, 10931, 10926, 10927, 10928), (10930, 10931, 10926, 10927, 10928), (10706, 10705, 10700, 10701, 10702), (10755, 11166, 10750, 10751, 10752), (10964, 11165, 10960, 10961, 10962), (11002, 11207, 10994, 10995, 10996), (11018, 11209, 11010, 11011, 11012), (11042, 11041, 11036, 11037, 11038), (11068, 11067, 11062, 11063, 11064), (10916, 10915, 10911, 10912, 10913), (10916, 10915, 10911, 10912, 10913), (11084, 11085, 11080, 11081, 11082), (11090, 11091, 11086, 11087, 11088), (11123, 11122, 11117, 11118, 11119), (11131, 11130, 11125, 11126, 11127), (11139, 11138, 11133, 11134, 11135), (10278, 10566, 10290, 10291, 10292), (10710, 1757, -1, -1, -1), (11103, 1900, -1, -1, -1), (10909, 10908, 10904, 10905, 10906), (10916, 10915, 10911, 10912, 10913), (10916, 10915, 10911, 10912, 10913), (11006, 1751, -1, -1, -1), (11001, 1751, -1, -1, -1), (11000, 1751, -1, -1, -1), (10993, 40, 10994, 10995, 10996), (10799, 38, 5360, 5361, 5362), (10803, 38, 5360, 5361, 5362), (10831, 38, 5366, 5367, 5368), (10835, 38, 5366, 5367, 5368), (10698, 10697, 10692, 10693, 10694), (10974, 4174, -1, -1, -1), (10739, 4150, -1, -1, -1), (10768, 2720, -1, -1, -1), (10902, 2732, -1, -1, -1), (11026, 2762, -1, -1, -1), (11049, 11050, 11045, 11046, 11047), (11049, 11050, 11045, 11046, 11047), (11049, 11050, 11045, 11046, 11047), (11049, 11050, 11045, 11046, 11047), (10939, 10940, 10935, 10936, 10937), (10939, 10940, 10935, 10936, 10937), (10939, 10940, 10935, 10936, 10937), (10939, 10940, 10935, 10936, 10937), (11009, 40, 11010, 11011, 11012), (3223, 4172, 4633, 4634, 4635), (11022, 1751, -1, -1, -1), (11017, 1751, -1, -1, -1), (11016, 1751, -1, -1, -1), (10990, 1751, -1, -1, -1), (10985, 1751, -1, -1, -1), (10984, 1751, -1, -1, -1), (10977, 40, 10978, 10979, 10980), (10839, 10838, 5550, 5551, 5552), (10843, 10842, 5550, 5551, 5552), (10847, 10838, 5550, 5551, 5552), (10851, 10842, 5550, 5551, 5552), (10790, 3863, 5553, 5554, 5555), (10794, 3865, 5553, 5554, 5555), (10863, 38, 5372, 5373, 5374), (10867, 38, 5372, 5373, 5374), (10871, 10870, 5556, 5557, 5558), (10875, 10874, 5556, 5557, 5558), (10879, 10870, 5556, 5557, 5558), (10883, 10874, 5556, 5557, 5558), (10790, 3863, 5559, 5560, 5561), (10794, 3865, 5559, 5560, 5561), (10895, 38, 5378, 5379, 5380), (10899, 38, 5378, 5379, 5380), (4320, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (10755, 5452, 4803, 4807, 4811), (10763, 5452, 4819, 4823, 4827), (10763, 5452, 4819, 4823, 4827), (9647, 2762, -1, -1, -1), (10321, 9347, -1, -1, -1), (10370, 11168, 10365, 10366, 10367), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (10755, 5452, 4803, 4807, 4811), (10763, 5452, 4819, 4823, 4827), (10763, 5452, 4819, 4823, 4827), (10755, 5452, 4803, 4807, 4811), (10763, 5452, 4819, 4823, 4827), (10763, 5452, 4819, 4823, 4827), (215, 5452, 4456, 4457, 4458)]
    malay_architecture = [(10665, 10664, 10659, 10660, 10661), (2575, 2573, 4429, 4430, 4431), (10665, 10664, 10659, 10660, 10661), (10680, 10681, 10676, 10677, 10678), (10680, 10681, 10676, 10677, 10678), (10706, 10705, 10700, 10701, 10702), (10771, 813, -1, -1, -1), (10734, 10733, 10728, 10729, 10730), (10734, 10733, 10728, 10729, 10730), (10734, 10733, 10728, 10729, 10730), (215, 205, 4456, 4457, 4458), (10763, 11167, 10758, 10759, 10760), (11042, 11041, 11036, 11037, 11038), (255, -1, 5354, 5355, 5356), (10763, 11167, 10758, 10759, 10760), (10779, 10778, 5538, 5539, 5540), (10775, 10774, 5538, 5539, 5540), (10787, 10778, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (10986, 11205, 10978, 10979, 10980), (588, 37, 4610, 4611, 4612), (10783, 10774, 5538, 5539, 5540), (11116, 11115, 11110, 11111, 11112), (10794, 3865, 5541, 5542, 5543), (10790, 3863, 5541, 5542, 5543), (10747, 10746, 10741, 10742, 10743), (10951, 10950, 10945, 10946, 10947), (10811, 10810, 5544, 5545, 5546), (11068, 11067, 11062, 11063, 11064), (10658, 10657, 10652, 10653, 10654), (10807, 10806, 5544, 5545, 5546), (10819, 10810, 5544, 5545, 5546), (10815, 10806, 5544, 5545, 5546), (10794, 3865, 5547, 5548, 5549), (10790, 3863, 5547, 5548, 5549), (11061, 11060, 11055, 11056, 11057), (10673, 10674, 10669, 10670, 10671), (10734, 10733, 10728, 10729, 10730), (10673, 10674, 10669, 10670, 10671), (3241, 419, 4563, 4564, 4565), (10958, 10957, 10952, 10953, 10954), (11096, 37, 11150, 11152, 11154), (10923, 10924, 10919, 10920, 10921), (10930, 10931, 10926, 10927, 10928), (10930, 10931, 10926, 10927, 10928), (10706, 10705, 10700, 10701, 10702), (10755, 11166, 10750, 10751, 10752), (10964, 11165, 10960, 10961, 10962), (11002, 11207, 10994, 10995, 10996), (11018, 11209, 11010, 11011, 11012), (11042, 11041, 11036, 11037, 11038), (11068, 11067, 11062, 11063, 11064), (10916, 10915, 10911, 10912, 10913), (10916, 10915, 10911, 10912, 10913), (11084, 11085, 11080, 11081, 11082), (11090, 11091, 11086, 11087, 11088), (11123, 11122, 11117, 11118, 11119), (11131, 11130, 11125, 11126, 11127), (11139, 11138, 11133, 11134, 11135), (10280, 10567, 10293, 10294, 10295), (10710, 1757, -1, -1, -1), (11103, 1900, -1, -1, -1), (10909, 10908, 10904, 10905, 10906), (10916, 10915, 10911, 10912, 10913), (10916, 10915, 10911, 10912, 10913), (11006, 1751, -1, -1, -1), (11001, 1751, -1, -1, -1), (11000, 1751, -1, -1, -1), (10993, 40, 10994, 10995, 10996), (10799, 38, 5360, 5361, 5362), (10803, 38, 5360, 5361, 5362), (10831, 38, 5366, 5367, 5368), (10835, 38, 5366, 5367, 5368), (10698, 10697, 10692, 10693, 10694), (10974, 4174, -1, -1, -1), (10739, 4150, -1, -1, -1), (10768, 2720, -1, -1, -1), (10902, 2732, -1, -1, -1), (11026, 2762, -1, -1, -1), (11049, 11050, 11045, 11046, 11047), (11049, 11050, 11045, 11046, 11047), (11049, 11050, 11045, 11046, 11047), (11049, 11050, 11045, 11046, 11047), (10939, 10940, 10935, 10936, 10937), (10939, 10940, 10935, 10936, 10937), (10939, 10940, 10935, 10936, 10937), (10939, 10940, 10935, 10936, 10937), (11009, 40, 11010, 11011, 11012), (3223, 4172, 4633, 4634, 4635), (11022, 1751, -1, -1, -1), (11017, 1751, -1, -1, -1), (11016, 1751, -1, -1, -1), (10990, 1751, -1, -1, -1), (10985, 1751, -1, -1, -1), (10984, 1751, -1, -1, -1), (10977, 40, 10978, 10979, 10980), (10839, 10838, 5550, 5551, 5552), (10843, 10842, 5550, 5551, 5552), (10847, 10838, 5550, 5551, 5552), (10851, 10842, 5550, 5551, 5552), (10790, 3863, 5553, 5554, 5555), (10794, 3865, 5553, 5554, 5555), (10863, 38, 5372, 5373, 5374), (10867, 38, 5372, 5373, 5374), (10871, 10870, 5556, 5557, 5558), (10875, 10874, 5556, 5557, 5558), (10879, 10870, 5556, 5557, 5558), (10883, 10874, 5556, 5557, 5558), (10790, 3863, 5559, 5560, 5561), (10794, 3865, 5559, 5560, 5561), (10895, 38, 5378, 5379, 5380), (10899, 38, 5378, 5379, 5380), (4320, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (10755, 5452, 4803, 4807, 4811), (10763, 5452, 4819, 4823, 4827), (10763, 5452, 4819, 4823, 4827), (9647, 2762, -1, -1, -1), (10321, 9347, -1, -1, -1), (10370, 11168, 10365, 10366, 10367), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (10755, 5452, 4803, 4807, 4811), (10763, 5452, 4819, 4823, 4827), (10763, 5452, 4819, 4823, 4827), (10755, 5452, 4803, 4807, 4811), (10763, 5452, 4819, 4823, 4827), (10763, 5452, 4819, 4823, 4827), (215, 5452, 4456, 4457, 4458)]
    burmese_architecture = [(10665, 10664, 10659, 10660, 10661), (2575, 2573, 4429, 4430, 4431), (10665, 10664, 10659, 10660, 10661), (10680, 10681, 10676, 10677, 10678), (10680, 10681, 10676, 10677, 10678), (10706, 10705, 10700, 10701, 10702), (10771, 813, -1, -1, -1), (10734, 10733, 10728, 10729, 10730), (10734, 10733, 10728, 10729, 10730), (10734, 10733, 10728, 10729, 10730), (215, 205, 4456, 4457, 4458), (10763, 11167, 10758, 10759, 10760), (11042, 11041, 11036, 11037, 11038), (255, -1, 5354, 5355, 5356), (10763, 11167, 10758, 10759, 10760), (10779, 10778, 5538, 5539, 5540), (10775, 10774, 5538, 5539, 5540), (10787, 10778, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (10986, 11205, 10978, 10979, 10980), (588, 37, 4610, 4611, 4612), (10783, 10774, 5538, 5539, 5540), (11116, 11115, 11110, 11111, 11112), (10794, 3865, 5541, 5542, 5543), (10790, 3863, 5541, 5542, 5543), (10747, 10746, 10741, 10742, 10743), (10951, 10950, 10945, 10946, 10947), (10811, 10810, 5544, 5545, 5546), (11068, 11067, 11062, 11063, 11064), (10658, 10657, 10652, 10653, 10654), (10807, 10806, 5544, 5545, 5546), (10819, 10810, 5544, 5545, 5546), (10815, 10806, 5544, 5545, 5546), (10794, 3865, 5547, 5548, 5549), (10790, 3863, 5547, 5548, 5549), (11061, 11060, 11055, 11056, 11057), (10673, 10674, 10669, 10670, 10671), (10734, 10733, 10728, 10729, 10730), (10673, 10674, 10669, 10670, 10671), (3241, 419, 4563, 4564, 4565), (10958, 10957, 10952, 10953, 10954), (11096, 37, 11150, 11152, 11154), (10923, 10924, 10919, 10920, 10921), (10930, 10931, 10926, 10927, 10928), (10930, 10931, 10926, 10927, 10928), (10706, 10705, 10700, 10701, 10702), (10755, 11166, 10750, 10751, 10752), (10964, 11165, 10960, 10961, 10962), (11002, 11207, 10994, 10995, 10996), (11018, 11209, 11010, 11011, 11012), (11042, 11041, 11036, 11037, 11038), (11068, 11067, 11062, 11063, 11064), (10916, 10915, 10911, 10912, 10913), (10916, 10915, 10911, 10912, 10913), (11084, 11085, 11080, 11081, 11082), (11090, 11091, 11086, 11087, 11088), (11123, 11122, 11117, 11118, 11119), (11131, 11130, 11125, 11126, 11127), (11139, 11138, 11133, 11134, 11135), (10276, 10565, 10287, 10288, 10289), (10710, 1757, -1, -1, -1), (11103, 1900, -1, -1, -1), (10909, 10908, 10904, 10905, 10906), (10916, 10915, 10911, 10912, 10913), (10916, 10915, 10911, 10912, 10913), (11006, 1751, -1, -1, -1), (11001, 1751, -1, -1, -1), (11000, 1751, -1, -1, -1), (10993, 40, 10994, 10995, 10996), (10799, 38, 5360, 5361, 5362), (10803, 38, 5360, 5361, 5362), (10831, 38, 5366, 5367, 5368), (10835, 38, 5366, 5367, 5368), (10698, 10697, 10692, 10693, 10694), (10974, 4174, -1, -1, -1), (10739, 4150, -1, -1, -1), (10768, 2720, -1, -1, -1), (10902, 2732, -1, -1, -1), (11026, 2762, -1, -1, -1), (11049, 11050, 11045, 11046, 11047), (11049, 11050, 11045, 11046, 11047), (11049, 11050, 11045, 11046, 11047), (11049, 11050, 11045, 11046, 11047), (10939, 10940, 10935, 10936, 10937), (10939, 10940, 10935, 10936, 10937), (10939, 10940, 10935, 10936, 10937), (10939, 10940, 10935, 10936, 10937), (11009, 40, 11010, 11011, 11012), (3223, 4172, 4633, 4634, 4635), (11022, 1751, -1, -1, -1), (11017, 1751, -1, -1, -1), (11016, 1751, -1, -1, -1), (10990, 1751, -1, -1, -1), (10985, 1751, -1, -1, -1), (10984, 1751, -1, -1, -1), (10977, 40, 10978, 10979, 10980), (10839, 10838, 5550, 5551, 5552), (10843, 10842, 5550, 5551, 5552), (10847, 10838, 5550, 5551, 5552), (10851, 10842, 5550, 5551, 5552), (10790, 3863, 5553, 5554, 5555), (10794, 3865, 5553, 5554, 5555), (10863, 38, 5372, 5373, 5374), (10867, 38, 5372, 5373, 5374), (10871, 10870, 5556, 5557, 5558), (10875, 10874, 5556, 5557, 5558), (10879, 10870, 5556, 5557, 5558), (10883, 10874, 5556, 5557, 5558), (10790, 3863, 5559, 5560, 5561), (10794, 3865, 5559, 5560, 5561), (10895, 38, 5378, 5379, 5380), (10899, 38, 5378, 5379, 5380), (4320, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (10755, 5452, 4803, 4807, 4811), (10763, 5452, 4819, 4823, 4827), (10763, 5452, 4819, 4823, 4827), (9647, 2762, -1, -1, -1), (10321, 9347, -1, -1, -1), (10370, 11168, 10365, 10366, 10367), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (10755, 5452, 4803, 4807, 4811), (10763, 5452, 4819, 4823, 4827), (10763, 5452, 4819, 4823, 4827), (10755, 5452, 4803, 4807, 4811), (10763, 5452, 4819, 4823, 4827), (10763, 5452, 4819, 4823, 4827), (215, 5452, 4456, 4457, 4458)]
    vietnamese_architecture = [(22, 18, 4684, 4688, 4692), (2575, 2573, 4429, 4430, 4431), (22, 18, 4684, 4688, 4692), (63, 67, 4712, 4716, 4720), (63, 67, 4712, 4716, 4720), (103, 99, 4740, 4744, 4748), (4011, 813, -1, -1, -1), (148, 144, 4772, 4776, 4780), (148, 144, 4772, 4776, 4780), (148, 144, 4772, 4776, 4780), (215, 205, 4456, 4457, 4458), (234, 132, 4820, 4824, 4828), (487, 483, 5100, 5104, 5108), (255, -1, 5354, 5355, 5356), (234, 132, 4820, 4824, 4828), (2058, 2054, 5538, 5539, 5540), (2046, 2042, 5538, 5539, 5540), (2082, 2054, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (3251, 263, 5052, 5056, 5060), (588, 37, 4610, 4611, 4612), (2070, 2042, 5538, 5539, 5540), (4200, 4196, 5196, 5200, 5204), (5328, 3833, 5541, 5542, 5543), (5323, 3831, 5541, 5542, 5543), (172, 168, 4788, 4792, 4796), (2266, 2262, 4992, 4996, 5000), (2130, 2126, 5544, 5545, 5546), (523, 519, 5144, 5148, 5152), (10, 6, 4668, 4672, 4676), (2118, 2114, 5544, 5545, 5546), (2154, 2126, 5544, 5545, 5546), (2142, 2114, 5544, 5545, 5546), (5328, 3833, 5547, 5548, 5549), (5323, 3831, 5547, 5548, 5549), (511, 507, 5128, 5132, 5136), (51, 55, 4700, 4704, 4708), (148, 144, 4772, 4776, 4780), (51, 55, 4700, 4704, 4708), (3241, 419, 4563, 4564, 4565), (409, 405, 5008, 5012, 5016), (2022, 37, 3792, 3796, 3800), (366, 370, 4956, 4960, 4964), (378, 382, 4968, 4972, 4976), (378, 382, 4968, 4972, 4976), (103, 99, 4740, 4744, 4748), (222, 126, 4804, 4808, 4812), (3432, 2274, 5024, 5028, 5032), (3263, 275, 5068, 5072, 5076), (3039, 287, 5084, 5088, 5092), (487, 483, 5100, 5104, 5108), (523, 519, 5144, 5148, 5152), (2221, 2217, 4944, 4948, 4952), (2221, 2217, 4944, 4948, 4952), (567, 571, 5172, 5176, 5180), (579, 583, 5184, 5188, 5192), (2530, 2526, 5212, 5216, 5220), (2405, 4184, 5228, 5232, 5236), (2413, 4188, 5244, 5248, 5252), (10282, 10568, 10296, 10297, 10298), (3959, 1757, -1, -1, -1), (3887, 1900, -1, -1, -1), (2207, 2203, 4932, 4936, 4940), (2221, 2217, 4944, 4948, 4952), (2221, 2217, 4944, 4948, 4952), (457, 1751, -1, -1, -1), (3259, 1751, -1, -1, -1), (3255, 1751, -1, -1, -1), (3351, 40, 5428, 5429, 5430), (2537, 38, 5360, 5361, 5362), (2549, 38, 5360, 5361, 5362), (2541, 38, 5366, 5367, 5368), (2557, 38, 5366, 5367, 5368), (91, 87, 4724, 4728, 4732), (4037, 4174, -1, -1, -1), (3986, 4150, -1, -1, -1), (4180, 2720, -1, -1, -1), (4024, 2732, -1, -1, -1), (4050, 2762, -1, -1, -1), (3116, 3120, 5116, 5120, 5124), (3116, 3120, 5116, 5120, 5124), (3116, 3120, 5116, 5120, 5124), (3116, 3120, 5116, 5120, 5124), (3131, 3135, 4980, 4984, 4988), (3131, 3135, 4980, 4984, 4988), (3131, 3135, 4980, 4984, 4988), (3131, 3135, 4980, 4984, 4988), (3355, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (469, 1751, -1, -1, -1), (3035, 1751, -1, -1, -1), (3031, 1751, -1, -1, -1), (445, 1751, -1, -1, -1), (3247, 1751, -1, -1, -1), (3243, 1751, -1, -1, -1), (3347, 40, 5425, 5426, 5427), (3606, 3602, 5550, 5551, 5552), (3618, 3614, 5550, 5551, 5552), (3630, 3602, 5550, 5551, 5552), (3642, 3614, 5550, 5551, 5552), (5323, 3831, 5553, 5554, 5555), (5328, 3833, 5553, 5554, 5555), (3678, 38, 5372, 5373, 5374), (3690, 38, 5372, 5373, 5374), (3702, 3698, 5556, 5557, 5558), (3714, 3710, 5556, 5557, 5558), (3726, 3698, 5556, 5557, 5558), (3738, 3710, 5556, 5557, 5558), (5323, 3831, 5559, 5560, 5561), (5328, 3833, 5559, 5560, 5561), (3774, 38, 5378, 5379, 5380), (3786, 38, 5378, 5379, 5380), (4297, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (222, 5452, 4804, 4808, 4812), (234, 5452, 4820, 4824, 4828), (234, 5452, 4820, 4824, 4828), (8635, 2762, -1, -1, -1), (9309, 9347, -1, -1, -1), (234, 132, 4820, 4824, 4828), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (222, 5452, 4804, 4808, 4812), (234, 5452, 4820, 4824, 4828), (234, 5452, 4820, 4824, 4828), (222, 5452, 4804, 4808, 4812), (234, 5452, 4820, 4824, 4828), (234, 5452, 4820, 4824, 4828), (215, 5452, 4456, 4457, 4458)]
    bulgarians_architecture = [(7665, 7664, 7659, 7660, 7661), (2575, 2573, 4429, 4430, 4431), (7665, 7664, 7659, 7660, 7661), (7680, 7681, 7676, 7677, 7678), (7680, 7681, 7676, 7677, 7678), (7706, 7705, 7700, 7701, 7702), (7771, 813, -1, -1, -1), (7734, 7733, 7728, 7729, 7730), (7734, 7733, 7728, 7729, 7730), (7734, 7733, 7728, 7729, 7730), (215, 205, 4456, 4457, 4458), (7763, 7970, 7758, 7759, 7760), (8042, 8041, 8036, 8037, 8038), (255, -1, 5354, 5355, 5356), (7763, 7970, 7758, 7759, 7760), (7779, 7778, 5538, 5539, 5540), (7775, 7774, 5538, 5539, 5540), (7787, 7778, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (7986, 248, 7978, 7979, 7980), (588, 37, 4610, 4611, 4612), (7783, 7774, 5538, 5539, 5540), (8116, 8115, 8110, 8111, 8112), (7794, 3853, 5541, 5542, 5543), (7790, 3851, 5541, 5542, 5543), (7747, 7746, 7741, 7742, 7743), (7951, 7950, 7945, 7946, 7947), (7811, 7810, 5544, 5545, 5546), (8068, 8067, 8062, 8063, 8064), (7658, 7657, 7652, 7653, 7654), (7807, 7806, 5544, 5545, 5546), (7819, 7810, 5544, 5545, 5546), (7815, 7806, 5544, 5545, 5546), (7794, 3853, 5547, 5548, 5549), (7790, 3851, 5547, 5548, 5549), (8061, 8060, 8055, 8056, 8057), (7673, 7674, 7669, 7670, 7671), (7734, 7733, 7728, 7729, 7730), (7673, 7674, 7669, 7670, 7671), (3241, 419, 4563, 4564, 4565), (7958, 7957, 7952, 7953, 7954), (8096, 37, 8150, 8152, 8154), (7923, 7924, 7919, 7920, 7921), (7930, 7931, 7926, 7927, 7928), (7930, 7931, 7926, 7927, 7928), (7706, 7705, 7700, 7701, 7702), (7755, 7969, 7750, 7751, 7752), (7966, 7965, 7960, 7961, 7962), (8002, 250, 7994, 7995, 7996), (8018, 252, 8010, 8011, 8012), (8042, 8041, 8036, 8037, 8038), (8068, 8067, 8062, 8063, 8064), (7916, 7915, 7911, 7912, 7913), (7916, 7915, 7911, 7912, 7913), (8084, 8085, 8080, 8081, 8082), (8090, 8091, 8086, 8087, 8088), (8123, 8122, 8117, 8118, 8119), (8131, 8130, 8125, 8126, 8127), (8139, 8138, 8133, 8134, 8135), (10473, 10569, 10484, 10485, 10486), (7710, 1757, -1, -1, -1), (8103, 1900, -1, -1, -1), (7909, 7908, 7904, 7905, 7906), (7916, 7915, 7911, 7912, 7913), (7916, 7915, 7911, 7912, 7913), (8006, 1751, -1, -1, -1), (8001, 1751, -1, -1, -1), (8000, 1751, -1, -1, -1), (7993, 40, 7994, 7995, 7996), (7799, 38, 5360, 5361, 5362), (7803, 38, 5360, 5361, 5362), (7831, 38, 5366, 5367, 5368), (7835, 38, 5366, 5367, 5368), (7698, 7697, 7692, 7693, 7694), (7974, 4174, -1, -1, -1), (7739, 4150, -1, -1, -1), (7768, 2720, -1, -1, -1), (7902, 2732, -1, -1, -1), (8026, 2762, -1, -1, -1), (8049, 8050, 8045, 8046, 8047), (8049, 8050, 8045, 8046, 8047), (8049, 8050, 8045, 8046, 8047), (8049, 8050, 8045, 8046, 8047), (7939, 7940, 7935, 7936, 7937), (7939, 7940, 7935, 7936, 7937), (7939, 7940, 7935, 7936, 7937), (7939, 7940, 7935, 7936, 7937), (8009, 40, 8010, 8011, 8012), (3223, 4172, 4633, 4634, 4635), (8022, 1751, -1, -1, -1), (8017, 1751, -1, -1, -1), (8016, 1751, -1, -1, -1), (7990, 1751, -1, -1, -1), (7985, 1751, -1, -1, -1), (7984, 1751, -1, -1, -1), (7977, 40, 7978, 7979, 7980), (7839, 7838, 5550, 5551, 5552), (7843, 7842, 5550, 5551, 5552), (7847, 7838, 5550, 5551, 5552), (7851, 7842, 5550, 5551, 5552), (7790, 3851, 5553, 5554, 5555), (7794, 3853, 5553, 5554, 5555), (7863, 38, 5372, 5373, 5374), (7867, 38, 5372, 5373, 5374), (7871, 7870, 5556, 5557, 5558), (7875, 7874, 5556, 5557, 5558), (7879, 7870, 5556, 5557, 5558), (7883, 7874, 5556, 5557, 5558), (7790, 3851, 5559, 5560, 5561), (7794, 3853, 5559, 5560, 5561), (7895, 38, 5378, 5379, 5380), (7899, 38, 5378, 5379, 5380), (4308, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (7755, 5452, 4803, 4807, 4811), (7763, 5452, 4819, 4823, 4827), (7763, 5452, 4819, 4823, 4827), (8647, 2762, -1, -1, -1), (9321, 9347, -1, -1, -1), (7763, 7970, 7758, 7759, 7760), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (7755, 5452, 4803, 4807, 4811), (7763, 5452, 4819, 4823, 4827), (7763, 5452, 4819, 4823, 4827), (7755, 5452, 4803, 4807, 4811), (7763, 5452, 4819, 4823, 4827), (7763, 5452, 4819, 4823, 4827), (215, 5452, 4456, 4457, 4458)]
    tatars_architecture = [(11665, 11664, 11659, 11660, 11661), (2575, 2573, 4429, 4430, 4431), (11665, 11664, 11659, 11660, 11661), (11680, 11681, 11676, 11677, 11678), (11680, 11681, 11676, 11677, 11678), (11706, 11705, 11700, 11701, 11702), (11771, 813, -1, -1, -1), (11734, 11733, 11728, 11729, 11730), (11734, 11733, 11728, 11729, 11730), (11734, 11733, 11728, 11729, 11730), (215, 205, 4456, 4457, 4458), (11763, 12166, 11758, 11759, 11760), (12242, 12241, 12236, 12237, 12238), (255, -1, 5354, 5355, 5356), (11763, 12166, 11758, 11759, 11760), (11779, 11778, 5538, 5539, 5540), (11775, 11774, 5538, 5539, 5540), (11787, 11778, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (11986, 12200, 11978, 11979, 11980), (588, 37, 4610, 4611, 4612), (11783, 11774, 5538, 5539, 5540), (12116, 12115, 12110, 12111, 12112), (11794, 3869, 5541, 5542, 5543), (11790, 3867, 5541, 5542, 5543), (11747, 11746, 11741, 11742, 11743), (11951, 11950, 11945, 11946, 11947), (11811, 11810, 5544, 5545, 5546), (12068, 12067, 12062, 12063, 12064), (11658, 11657, 11652, 11653, 11654), (11807, 11806, 5544, 5545, 5546), (11819, 11810, 5544, 5545, 5546), (11815, 11806, 5544, 5545, 5546), (11794, 3869, 5547, 5548, 5549), (11790, 3867, 5547, 5548, 5549), (12061, 12060, 12055, 12056, 12057), (11673, 11674, 11669, 11670, 11671), (11734, 11733, 11728, 11729, 11730), (11673, 11674, 11669, 11670, 11671), (3241, 419, 4563, 4564, 4565), (11958, 11957, 11952, 11953, 11954), (12096, 37, 12150, 12152, 12154), (11923, 11924, 11919, 11920, 11921), (11930, 11931, 11926, 11927, 11928), (11930, 11931, 11926, 11927, 11928), (11706, 11705, 11700, 11701, 11702), (11755, 12165, 11750, 11751, 11752), (11964, 12177, 11960, 11961, 11962), (12002, 12202, 11994, 11995, 11996), (12018, 12204, 12010, 12011, 12012), (12042, 12041, 12236, 12237, 12238), (12068, 12067, 12062, 12063, 12064), (11916, 11915, 11911, 11912, 11913), (11916, 11915, 11911, 11912, 11913), (12084, 12085, 12080, 12081, 12082), (12090, 12091, 12086, 12087, 12088), (12123, 12122, 12117, 12118, 12119), (12131, 12130, 12125, 12126, 12127), (12139, 12138, 12133, 12134, 12135), (10475, 10570, 10487, 10488, 10489), (11710, 1757, -1, -1, -1), (12103, 1900, -1, -1, -1), (11909, 11908, 11904, 11905, 11906), (11916, 11915, 11911, 11912, 11913), (11916, 11915, 11911, 11912, 11913), (12006, 1751, -1, -1, -1), (12001, 1751, -1, -1, -1), (12000, 1751, -1, -1, -1), (11993, 40, 11994, 11995, 11996), (11799, 38, 5360, 5361, 5362), (11803, 38, 5360, 5361, 5362), (11831, 38, 5366, 5367, 5368), (11835, 38, 5366, 5367, 5368), (11698, 11697, 11692, 11693, 11694), (11974, 4174, -1, -1, -1), (11739, 4150, -1, -1, -1), (11768, 2720, -1, -1, -1), (11902, 2732, -1, -1, -1), (12026, 2762, -1, -1, -1), (12049, 12050, 12045, 12046, 12047), (12049, 12050, 12045, 12046, 12047), (12049, 12050, 12045, 12046, 12047), (12049, 12050, 12045, 12046, 12047), (11939, 11940, 11935, 11936, 11937), (11939, 11940, 11935, 11936, 11937), (11939, 11940, 11935, 11936, 11937), (11939, 11940, 11935, 11936, 11937), (12009, 40, 12010, 12011, 12012), (3223, 4172, 4633, 4634, 4635), (12022, 1751, -1, -1, -1), (12017, 1751, -1, -1, -1), (12016, 1751, -1, -1, -1), (11990, 1751, -1, -1, -1), (11985, 1751, -1, -1, -1), (11984, 1751, -1, -1, -1), (11977, 40, 11978, 11979, 11980), (11839, 11838, 5550, 5551, 5552), (11843, 11842, 5550, 5551, 5552), (11847, 11838, 5550, 5551, 5552), (11851, 11842, 5550, 5551, 5552), (11790, 3867, 5553, 5554, 5555), (11794, 3869, 5553, 5554, 5555), (11863, 38, 5372, 5373, 5374), (11867, 38, 5372, 5373, 5374), (11871, 11870, 5556, 5557, 5558), (11875, 11874, 5556, 5557, 5558), (11879, 11870, 5556, 5557, 5558), (11883, 11874, 5556, 5557, 5558), (11790, 3867, 5559, 5560, 5561), (11794, 3869, 5559, 5560, 5561), (11895, 38, 5378, 5379, 5380), (11899, 38, 5378, 5379, 5380), (4323, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (11755, 5452, 4803, 4807, 4811), (11763, 5452, 4819, 4823, 4827), (11763, 5452, 4819, 4823, 4827), (12172, 2762, -1, -1, -1), (12175, 9347, -1, -1, -1), (11763, 12166, 11758, 11759, 11760), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (11755, 5452, 4803, 4807, 4811), (11763, 5452, 4819, 4823, 4827), (11763, 5452, 4819, 4823, 4827), (11755, 5452, 4803, 4807, 4811), (11763, 5452, 4819, 4823, 4827), (11763, 5452, 4819, 4823, 4827), (215, 5452, 4456, 4457, 4458)]
    cumans_architecture = [(11665, 11664, 11659, 11660, 11661), (2575, 2573, 4429, 4430, 4431), (11665, 11664, 11659, 11660, 11661), (11680, 11681, 11676, 11677, 11678), (11680, 11681, 11676, 11677, 11678), (11706, 11705, 11700, 11701, 11702), (11771, 813, -1, -1, -1), (11734, 11733, 11728, 11729, 11730), (11734, 11733, 11728, 11729, 11730), (11734, 11733, 11728, 11729, 11730), (215, 205, 4456, 4457, 4458), (11763, 12166, 11758, 11759, 11760), (12242, 12241, 12236, 12237, 12238), (255, -1, 5354, 5355, 5356), (11763, 12166, 11758, 11759, 11760), (11779, 11778, 5538, 5539, 5540), (11775, 11774, 5538, 5539, 5540), (11787, 11778, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (11986, 12200, 11978, 11979, 11980), (588, 37, 4610, 4611, 4612), (11783, 11774, 5538, 5539, 5540), (12116, 12115, 12110, 12111, 12112), (11794, 3869, 5541, 5542, 5543), (11790, 3867, 5541, 5542, 5543), (11747, 11746, 11741, 11742, 11743), (11951, 11950, 11945, 11946, 11947), (11811, 11810, 5544, 5545, 5546), (12068, 12067, 12062, 12063, 12064), (11658, 11657, 11652, 11653, 11654), (11807, 11806, 5544, 5545, 5546), (11819, 11810, 5544, 5545, 5546), (11815, 11806, 5544, 5545, 5546), (11794, 3869, 5547, 5548, 5549), (11790, 3867, 5547, 5548, 5549), (12061, 12060, 12055, 12056, 12057), (11673, 11674, 11669, 11670, 11671), (11734, 11733, 11728, 11729, 11730), (11673, 11674, 11669, 11670, 11671), (3241, 419, 4563, 4564, 4565), (11958, 11957, 11952, 11953, 11954), (12096, 37, 12150, 12152, 12154), (11923, 11924, 11919, 11920, 11921), (11930, 11931, 11926, 11927, 11928), (11930, 11931, 11926, 11927, 11928), (11706, 11705, 11700, 11701, 11702), (11755, 12165, 11750, 11751, 11752), (11964, 12177, 11960, 11961, 11962), (12002, 12202, 11994, 11995, 11996), (12018, 12204, 12010, 12011, 12012), (12042, 12041, 12236, 12237, 12238), (12068, 12067, 12062, 12063, 12064), (11916, 11915, 11911, 11912, 11913), (11916, 11915, 11911, 11912, 11913), (12084, 12085, 12080, 12081, 12082), (12090, 12091, 12086, 12087, 12088), (12123, 12122, 12117, 12118, 12119), (12131, 12130, 12125, 12126, 12127), (12139, 12138, 12133, 12134, 12135), (10477, 10571, 10490, 10491, 10492), (11710, 1757, -1, -1, -1), (12103, 1900, -1, -1, -1), (11909, 11908, 11904, 11905, 11906), (11916, 11915, 11911, 11912, 11913), (11916, 11915, 11911, 11912, 11913), (12006, 1751, -1, -1, -1), (12001, 1751, -1, -1, -1), (12000, 1751, -1, -1, -1), (11993, 40, 11994, 11995, 11996), (11799, 38, 5360, 5361, 5362), (11803, 38, 5360, 5361, 5362), (11831, 38, 5366, 5367, 5368), (11835, 38, 5366, 5367, 5368), (11698, 11697, 11692, 11693, 11694), (11974, 4174, -1, -1, -1), (11739, 4150, -1, -1, -1), (11768, 2720, -1, -1, -1), (11902, 2732, -1, -1, -1), (12026, 2762, -1, -1, -1), (12049, 12050, 12045, 12046, 12047), (12049, 12050, 12045, 12046, 12047), (12049, 12050, 12045, 12046, 12047), (12049, 12050, 12045, 12046, 12047), (11939, 11940, 11935, 11936, 11937), (11939, 11940, 11935, 11936, 11937), (11939, 11940, 11935, 11936, 11937), (11939, 11940, 11935, 11936, 11937), (12009, 40, 12010, 12011, 12012), (3223, 4172, 4633, 4634, 4635), (12022, 1751, -1, -1, -1), (12017, 1751, -1, -1, -1), (12016, 1751, -1, -1, -1), (11990, 1751, -1, -1, -1), (11985, 1751, -1, -1, -1), (11984, 1751, -1, -1, -1), (11977, 40, 11978, 11979, 11980), (11839, 11838, 5550, 5551, 5552), (11843, 11842, 5550, 5551, 5552), (11847, 11838, 5550, 5551, 5552), (11851, 11842, 5550, 5551, 5552), (11790, 3867, 5553, 5554, 5555), (11794, 3869, 5553, 5554, 5555), (11863, 38, 5372, 5373, 5374), (11867, 38, 5372, 5373, 5374), (11871, 11870, 5556, 5557, 5558), (11875, 11874, 5556, 5557, 5558), (11879, 11870, 5556, 5557, 5558), (11883, 11874, 5556, 5557, 5558), (11790, 3867, 5559, 5560, 5561), (11794, 3869, 5559, 5560, 5561), (11895, 38, 5378, 5379, 5380), (11899, 38, 5378, 5379, 5380), (4323, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (11755, 5452, 4803, 4807, 4811), (11763, 5452, 4819, 4823, 4827), (11763, 5452, 4819, 4823, 4827), (12172, 2762, -1, -1, -1), (12175, 9347, -1, -1, -1), (11763, 12166, 11758, 11759, 11760), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (11755, 5452, 4803, 4807, 4811), (11763, 5452, 4819, 4823, 4827), (11763, 5452, 4819, 4823, 4827), (11755, 5452, 4803, 4807, 4811), (11763, 5452, 4819, 4823, 4827), (11763, 5452, 4819, 4823, 4827), (215, 5452, 4456, 4457, 4458)]
    lithuanians_architecture = [(7665, 7664, 7659, 7660, 7661), (2575, 2573, 4429, 4430, 4431), (7665, 7664, 7659, 7660, 7661), (7680, 7681, 7676, 7677, 7678), (7680, 7681, 7676, 7677, 7678), (7706, 7705, 7700, 7701, 7702), (7771, 813, -1, -1, -1), (7734, 7733, 7728, 7729, 7730), (7734, 7733, 7728, 7729, 7730), (7734, 7733, 7728, 7729, 7730), (215, 205, 4456, 4457, 4458), (7763, 7970, 7758, 7759, 7760), (8042, 8041, 8036, 8037, 8038), (255, -1, 5354, 5355, 5356), (7763, 7970, 7758, 7759, 7760), (7779, 7778, 5538, 5539, 5540), (7775, 7774, 5538, 5539, 5540), (7787, 7778, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (7986, 248, 7978, 7979, 7980), (588, 37, 4610, 4611, 4612), (7783, 7774, 5538, 5539, 5540), (8116, 8115, 8110, 8111, 8112), (7794, 3853, 5541, 5542, 5543), (7790, 3851, 5541, 5542, 5543), (7747, 7746, 7741, 7742, 7743), (7951, 7950, 7945, 7946, 7947), (7811, 7810, 5544, 5545, 5546), (8068, 8067, 8062, 8063, 8064), (7658, 7657, 7652, 7653, 7654), (7807, 7806, 5544, 5545, 5546), (7819, 7810, 5544, 5545, 5546), (7815, 7806, 5544, 5545, 5546), (7794, 3853, 5547, 5548, 5549), (7790, 3851, 5547, 5548, 5549), (8061, 8060, 8055, 8056, 8057), (7673, 7674, 7669, 7670, 7671), (7734, 7733, 7728, 7729, 7730), (7673, 7674, 7669, 7670, 7671), (3241, 419, 4563, 4564, 4565), (7958, 7957, 7952, 7953, 7954), (8096, 37, 8150, 8152, 8154), (7923, 7924, 7919, 7920, 7921), (7930, 7931, 7926, 7927, 7928), (7930, 7931, 7926, 7927, 7928), (7706, 7705, 7700, 7701, 7702), (7755, 7969, 7750, 7751, 7752), (7966, 7965, 7960, 7961, 7962), (8002, 250, 7994, 7995, 7996), (8018, 252, 8010, 8011, 8012), (8042, 8041, 8036, 8037, 8038), (8068, 8067, 8062, 8063, 8064), (7916, 7915, 7911, 7912, 7913), (7916, 7915, 7911, 7912, 7913), (8084, 8085, 8080, 8081, 8082), (8090, 8091, 8086, 8087, 8088), (8123, 8122, 8117, 8118, 8119), (8131, 8130, 8125, 8126, 8127), (8139, 8138, 8133, 8134, 8135), (10479, 10572, 10493, 10494, 10495), (7710, 1757, -1, -1, -1), (8103, 1900, -1, -1, -1), (7909, 7908, 7904, 7905, 7906), (7916, 7915, 7911, 7912, 7913), (7916, 7915, 7911, 7912, 7913), (8006, 1751, -1, -1, -1), (8001, 1751, -1, -1, -1), (8000, 1751, -1, -1, -1), (7993, 40, 7994, 7995, 7996), (7799, 38, 5360, 5361, 5362), (7803, 38, 5360, 5361, 5362), (7831, 38, 5366, 5367, 5368), (7835, 38, 5366, 5367, 5368), (7698, 7697, 7692, 7693, 7694), (7974, 4174, -1, -1, -1), (7739, 4150, -1, -1, -1), (7768, 2720, -1, -1, -1), (7902, 2732, -1, -1, -1), (8026, 2762, -1, -1, -1), (8049, 8050, 8045, 8046, 8047), (8049, 8050, 8045, 8046, 8047), (8049, 8050, 8045, 8046, 8047), (8049, 8050, 8045, 8046, 8047), (7939, 7940, 7935, 7936, 7937), (7939, 7940, 7935, 7936, 7937), (7939, 7940, 7935, 7936, 7937), (7939, 7940, 7935, 7936, 7937), (8009, 40, 8010, 8011, 8012), (3223, 4172, 4633, 4634, 4635), (8022, 1751, -1, -1, -1), (8017, 1751, -1, -1, -1), (8016, 1751, -1, -1, -1), (7990, 1751, -1, -1, -1), (7985, 1751, -1, -1, -1), (7984, 1751, -1, -1, -1), (7977, 40, 7978, 7979, 7980), (7839, 7838, 5550, 5551, 5552), (7843, 7842, 5550, 5551, 5552), (7847, 7838, 5550, 5551, 5552), (7851, 7842, 5550, 5551, 5552), (7790, 3851, 5553, 5554, 5555), (7794, 3853, 5553, 5554, 5555), (7863, 38, 5372, 5373, 5374), (7867, 38, 5372, 5373, 5374), (7871, 7870, 5556, 5557, 5558), (7875, 7874, 5556, 5557, 5558), (7879, 7870, 5556, 5557, 5558), (7883, 7874, 5556, 5557, 5558), (7790, 3851, 5559, 5560, 5561), (7794, 3853, 5559, 5560, 5561), (7895, 38, 5378, 5379, 5380), (7899, 38, 5378, 5379, 5380), (4308, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (7755, 5452, 4803, 4807, 4811), (7763, 5452, 4819, 4823, 4827), (7763, 5452, 4819, 4823, 4827), (8647, 2762, -1, -1, -1), (9321, 9347, -1, -1, -1), (7763, 7970, 7758, 7759, 7760), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (7755, 5452, 4803, 4807, 4811), (7763, 5452, 4819, 4823, 4827), (7763, 5452, 4819, 4823, 4827), (7755, 5452, 4803, 4807, 4811), (7763, 5452, 4819, 4823, 4827), (7763, 5452, 4819, 4823, 4827), (215, 5452, 4456, 4457, 4458)]
    burgundians_architecture = [(24, 20, 4686, 4690, 4694), (2575, 2573, 4429, 4430, 4431), (24, 20, 4686, 4690, 4694), (65, 69, 4714, 4718, 4722), (65, 69, 4714, 4718, 4722), (105, 101, 4742, 4746, 4750), (4013, 813, -1, -1, -1), (150, 146, 4774, 4778, 4782), (150, 146, 4774, 4778, 4782), (150, 146, 4774, 4778, 4782), (215, 205, 4456, 4457, 4458), (236, 134, 4822, 4826, 4830), (489, 485, 5102, 5106, 5110), (255, -1, 5354, 5355, 5356), (236, 134, 4822, 4826, 4830), (2060, 2056, 5538, 5539, 5540), (2048, 2044, 5538, 5539, 5540), (2084, 2056, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (3253, 265, 5054, 5058, 5062), (588, 37, 4610, 4611, 4612), (2072, 2044, 5538, 5539, 5540), (4202, 4198, 5198, 5202, 5206), (5331, 3841, 5541, 5542, 5543), (5326, 3839, 5541, 5542, 5543), (6053, 6054, 6056, 6057, 6058), (2268, 2264, 4994, 4998, 5002), (2132, 2128, 5544, 5545, 5546), (525, 521, 5146, 5150, 5154), (12, 8, 4670, 4674, 4678), (2120, 2116, 5544, 5545, 5546), (2156, 2128, 5544, 5545, 5546), (2144, 2116, 5544, 5545, 5546), (5331, 3841, 5547, 5548, 5549), (5326, 3839, 5547, 5548, 5549), (513, 509, 5130, 5134, 5138), (53, 57, 4702, 4706, 4710), (150, 146, 4774, 4778, 4782), (53, 57, 4702, 4706, 4710), (3241, 419, 4563, 4564, 4565), (411, 407, 5010, 5014, 5018), (2024, 37, 3794, 3798, 3802), (368, 372, 4958, 4962, 4966), (380, 384, 4970, 4974, 4978), (380, 384, 4970, 4974, 4978), (105, 101, 4742, 4746, 4750), (224, 128, 4806, 4810, 4814), (3434, 2276, 5026, 5030, 5034), (3265, 277, 5070, 5074, 5078), (3041, 289, 5086, 5090, 5094), (489, 485, 5102, 5106, 5110), (525, 521, 5146, 5150, 5154), (2223, 2219, 4946, 4950, 4954), (2223, 2219, 4946, 4950, 4954), (569, 573, 5174, 5178, 5182), (581, 585, 5186, 5190, 5194), (2532, 2528, 5214, 5218, 5222), (2407, 4186, 5230, 5234, 5238), (2415, 4190, 5246, 5250, 5254), (6079, 6080, 6082, 6083, 6084), (3961, 1757, -1, -1, -1), (3889, 1900, -1, -1, -1), (2209, 2205, 4934, 4938, 4942), (2223, 2219, 4946, 4950, 4954), (2223, 2219, 4946, 4950, 4954), (459, 1751, -1, -1, -1), (3261, 1751, -1, -1, -1), (3257, 1751, -1, -1, -1), (3353, 40, 5428, 5429, 5430), (2539, 38, 5360, 5361, 5362), (2551, 38, 5360, 5361, 5362), (2543, 38, 5366, 5367, 5368), (2559, 38, 5366, 5367, 5368), (93, 89, 4726, 4730, 4734), (4039, 4174, -1, -1, -1), (3988, 4150, -1, -1, -1), (4182, 2720, -1, -1, -1), (4026, 2732, -1, -1, -1), (4052, 2762, -1, -1, -1), (3118, 3122, 5118, 5122, 5126), (3118, 3122, 5118, 5122, 5126), (3118, 3122, 5118, 5122, 5126), (3118, 3122, 5118, 5122, 5126), (3133, 3137, 4982, 4986, 4990), (3133, 3137, 4982, 4986, 4990), (3133, 3137, 4982, 4986, 4990), (3133, 3137, 4982, 4986, 4990), (3357, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (471, 1751, -1, -1, -1), (3037, 1751, -1, -1, -1), (3033, 1751, -1, -1, -1), (447, 1751, -1, -1, -1), (3249, 1751, -1, -1, -1), (3245, 1751, -1, -1, -1), (3349, 40, 5425, 5426, 5427), (3608, 3604, 5550, 5551, 5552), (3620, 3616, 5550, 5551, 5552), (3632, 3604, 5550, 5551, 5552), (3644, 3616, 5550, 5551, 5552), (5326, 3839, 5553, 5554, 5555), (5331, 3841, 5553, 5554, 5555), (3680, 38, 5372, 5373, 5374), (3692, 38, 5372, 5373, 5374), (3704, 3700, 5556, 5557, 5558), (3716, 3712, 5556, 5557, 5558), (3728, 3700, 5556, 5557, 5558), (3740, 3712, 5556, 5557, 5558), (5326, 3839, 5559, 5560, 5561), (5331, 3841, 5559, 5560, 5561), (3776, 38, 5378, 5379, 5380), (3788, 38, 5378, 5379, 5380), (4299, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (224, 5452, 4806, 4810, 4814), (236, 5452, 4822, 4826, 4830), (236, 5452, 4822, 4826, 4830), (8628, 2762, -1, -1, -1), (9302, 9347, -1, -1, -1), (236, 134, 4822, 4826, 4830), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (224, 5452, 4806, 4810, 4814), (236, 5452, 4822, 4826, 4830), (236, 5452, 4822, 4826, 4830), (224, 5452, 4806, 4810, 4814), (236, 5452, 4822, 4826, 4830), (236, 5452, 4822, 4826, 4830), (215, 5452, 4456, 4457, 4458)]
    sicilians_architecture = [(27, 26, 4532, 4533, 4534), (2575, 2573, 4429, 4430, 4431), (27, 26, 4532, 4533, 4534), (71, 72, 4567, 4568, 4569), (71, 72, 4567, 4568, 4569), (108, 107, 4542, 4543, 4544), (9262, 813, -1, -1, -1), (153, 152, 8277, 8278, 8279), (153, 152, 8277, 8278, 8279), (153, 152, 8277, 8278, 8279), (215, 205, 4456, 4457, 4458), (242, 135, 4605, 4606, 4607), (492, 491, 4537, 4538, 4539), (255, -1, 5354, 5355, 5356), (242, 135, 4605, 4606, 4607), (7421, 7420, 5538, 5539, 5540), (7417, 7416, 5538, 5539, 5540), (7429, 7420, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (12249, 266, 9210, 9211, 9212), (588, 37, 4610, 4611, 4612), (7425, 7416, 5538, 5539, 5540), (4171, 4170, 4636, 4637, 4638), (7436, 3845, 5541, 5542, 5543), (7432, 3843, 5541, 5542, 5543), (5998, 5999, 6001, 6002, 6003), (417, 416, 9177, 9178, 9179), (7453, 7452, 5544, 5545, 5546), (528, 527, 4576, 4577, 4578), (30, 29, 9165, 9166, 9167), (7449, 7448, 5544, 5545, 5546), (7461, 7452, 5544, 5545, 5546), (7457, 7448, 5544, 5545, 5546), (7436, 3845, 5547, 5548, 5549), (7432, 3843, 5547, 5548, 5549), (531, 530, 9216, 9217, 9218), (74, 75, 9191, 9192, 9193), (153, 152, 8277, 8278, 8279), (74, 75, 9191, 9192, 9193), (3241, 419, 4563, 4564, 4565), (414, 413, 4581, 4582, 4583), (7390, 37, 7398, 7400, 7402), (9196, 9197, 9198, 9199, 9200), (386, 387, 4618, 4619, 4620), (386, 387, 4618, 4619, 4620), (108, 107, 4542, 4543, 4544), (9182, 129, 9184, 9185, 9186), (3436, 2278, 4592, 4593, 4594), (3237, 278, 12253, 12254, 12255), (3229, 290, 12258, 12259, 12260), (492, 491, 4537, 4538, 4539), (528, 527, 4576, 4577, 4578), (2226, 2225, 4527, 4528, 4529), (2226, 2225, 4527, 4528, 4529), (593, 594, 4571, 4572, 4573), (596, 597, 4597, 4598, 4599), (2517, 2516, 4613, 4614, 4615), (2395, 2390, 4623, 4624, 4625), (2398, 2391, 4628, 4629, 4630), (6086, 6087, 6089, 6090, 6091), (9241, 1757, -1, -1, -1), (9282, 1900, -1, -1, -1), (9202, 2228, 9203, 9204, 9205), (2226, 2225, 4527, 4528, 4529), (2226, 2225, 4527, 4528, 4529), (432, 1751, -1, -1, -1), (3236, 1751, -1, -1, -1), (3235, 1751, -1, -1, -1), (3344, 40, 5428, 5429, 5430), (7441, 38, 5360, 5361, 5362), (7445, 38, 5360, 5361, 5362), (7473, 38, 5366, 5367, 5368), (7477, 38, 5366, 5367, 5368), (111, 110, 9171, 9172, 9173), (9267, 4174, -1, -1, -1), (9256, 4150, -1, -1, -1), (9259, 2720, -1, -1, -1), (9265, 2732, -1, -1, -1), (9271, 2762, -1, -1, -1), (3202, 3203, 3205, 3206, 3207), (3202, 3203, 3205, 3206, 3207), (3202, 3203, 3205, 3206, 3207), (3202, 3203, 3205, 3206, 3207), (3195, 3196, 3198, 3199, 3200), (3195, 3196, 3198, 3199, 3200), (3195, 3196, 3198, 3199, 3200), (3195, 3196, 3198, 3199, 3200), (3231, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (429, 1751, -1, -1, -1), (3228, 1751, -1, -1, -1), (3227, 1751, -1, -1, -1), (9207, 1751, -1, -1, -1), (12251, 1751, -1, -1, -1), (9208, 1751, -1, -1, -1), (9226, 40, 9230, 9231, 9232), (7481, 7480, 5550, 5551, 5552), (7485, 7484, 5550, 5551, 5552), (7489, 7480, 5550, 5551, 5552), (7493, 7484, 5550, 5551, 5552), (7432, 3843, 5553, 5554, 5555), (7436, 3845, 5553, 5554, 5555), (7505, 38, 5372, 5373, 5374), (7509, 38, 5372, 5373, 5374), (7513, 7512, 5556, 5557, 5558), (7517, 7516, 5556, 5557, 5558), (7521, 7512, 5556, 5557, 5558), (7525, 7516, 5556, 5557, 5558), (7432, 3843, 5559, 5560, 5561), (7436, 3845, 5559, 5560, 5561), (7537, 38, 5378, 5379, 5380), (7541, 38, 5378, 5379, 5380), (4314, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (224, 5452, 4806, 4810, 4814), (242, 5452, 4821, 4825, 4829), (242, 5452, 4821, 4825, 4829), (8644, 2762, -1, -1, -1), (9318, 9347, -1, -1, -1), (242, 135, 4821, 4825, 4829), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (224, 5452, 4806, 4810, 4814), (242, 5452, 4821, 4825, 4829), (242, 5452, 4821, 4825, 4829), (224, 5452, 4806, 4810, 4814), (242, 5452, 4821, 4825, 4829), (242, 5452, 4821, 4825, 4829), (215, 5452, 4456, 4457, 4458)]
    poles_architecture = [(7665, 7664, 7659, 7660, 7661), (2575, 2573, 4429, 4430, 4431), (7665, 7664, 7659, 7660, 7661), (7680, 7681, 7676, 7677, 7678), (7680, 7681, 7676, 7677, 7678), (7706, 7705, 7700, 7701, 7702), (7771, 813, -1, -1, -1), (7734, 7733, 7728, 7729, 7730), (7734, 7733, 7728, 7729, 7730), (7734, 7733, 7728, 7729, 7730), (215, 205, 4456, 4457, 4458), (7763, 7970, 7758, 7759, 7760), (8042, 8041, 8036, 8037, 8038), (255, -1, 5354, 5355, 5356), (7763, 7970, 7758, 7759, 7760), (7779, 7778, 5538, 5539, 5540), (7775, 7774, 5538, 5539, 5540), (7787, 7778, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (7986, 248, 7978, 7979, 7980), (588, 37, 4610, 4611, 4612), (7783, 7774, 5538, 5539, 5540), (8116, 8115, 8110, 8111, 8112), (7794, 3853, 5541, 5542, 5543), (7790, 3851, 5541, 5542, 5543), (12410, 12411, 12413, 12414, 12415), (7951, 7950, 7945, 7946, 7947), (7811, 7810, 5544, 5545, 5546), (8068, 8067, 8062, 8063, 8064), (7658, 7657, 7652, 7653, 7654), (7807, 7806, 5544, 5545, 5546), (7819, 7810, 5544, 5545, 5546), (7815, 7806, 5544, 5545, 5546), (7794, 3853, 5547, 5548, 5549), (7790, 3851, 5547, 5548, 5549), (8061, 8060, 8055, 8056, 8057), (7673, 7674, 7669, 7670, 7671), (7734, 7733, 7728, 7729, 7730), (7673, 7674, 7669, 7670, 7671), (3241, 419, 4563, 4564, 4565), (7958, 7957, 7952, 7953, 7954), (8096, 37, 8150, 8152, 8154), (7923, 7924, 7919, 7920, 7921), (7930, 7931, 7926, 7927, 7928), (7930, 7931, 7926, 7927, 7928), (7706, 7705, 7700, 7701, 7702), (7755, 7969, 7750, 7751, 7752), (7966, 7965, 7960, 7961, 7962), (8002, 250, 7994, 7995, 7996), (8018, 252, 8010, 8011, 8012), (8042, 8041, 8036, 8037, 8038), (8068, 8067, 8062, 8063, 8064), (7916, 7915, 7911, 7912, 7913), (7916, 7915, 7911, 7912, 7913), (8084, 8085, 8080, 8081, 8082), (8090, 8091, 8086, 8087, 8088), (8123, 8122, 8117, 8118, 8119), (8131, 8130, 8125, 8126, 8127), (8139, 8138, 8133, 8134, 8135), (12396, 12397, 12399, 12400, 12401), (7710, 1757, -1, -1, -1), (8103, 1900, -1, -1, -1), (7909, 7908, 7904, 7905, 7906), (7916, 7915, 7911, 7912, 7913), (7916, 7915, 7911, 7912, 7913), (8006, 1751, -1, -1, -1), (8001, 1751, -1, -1, -1), (8000, 1751, -1, -1, -1), (7993, 40, 7994, 7995, 7996), (7799, 38, 5360, 5361, 5362), (7803, 38, 5360, 5361, 5362), (7831, 38, 5366, 5367, 5368), (7835, 38, 5366, 5367, 5368), (7698, 7697, 7692, 7693, 7694), (7974, 4174, -1, -1, -1), (7739, 4150, -1, -1, -1), (7768, 2720, -1, -1, -1), (7902, 2732, -1, -1, -1), (8026, 2762, -1, -1, -1), (8049, 8050, 8045, 8046, 8047), (8049, 8050, 8045, 8046, 8047), (8049, 8050, 8045, 8046, 8047), (8049, 8050, 8045, 8046, 8047), (7939, 7940, 7935, 7936, 7937), (7939, 7940, 7935, 7936, 7937), (7939, 7940, 7935, 7936, 7937), (7939, 7940, 7935, 7936, 7937), (8009, 40, 8010, 8011, 8012), (3223, 4172, 4633, 4634, 4635), (8022, 1751, -1, -1, -1), (8017, 1751, -1, -1, -1), (8016, 1751, -1, -1, -1), (7990, 1751, -1, -1, -1), (7985, 1751, -1, -1, -1), (7984, 1751, -1, -1, -1), (7977, 40, 7978, 7979, 7980), (7839, 7838, 5550, 5551, 5552), (7843, 7842, 5550, 5551, 5552), (7847, 7838, 5550, 5551, 5552), (7851, 7842, 5550, 5551, 5552), (7790, 3851, 5553, 5554, 5555), (7794, 3853, 5553, 5554, 5555), (7863, 38, 5372, 5373, 5374), (7867, 38, 5372, 5373, 5374), (7871, 7870, 5556, 5557, 5558), (7875, 7874, 5556, 5557, 5558), (7879, 7870, 5556, 5557, 5558), (7883, 7874, 5556, 5557, 5558), (7790, 3851, 5559, 5560, 5561), (7794, 3853, 5559, 5560, 5561), (7895, 38, 5378, 5379, 5380), (7899, 38, 5378, 5379, 5380), (4308, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (7755, 5452, 4803, 4807, 4811), (7763, 5452, 4819, 4823, 4827), (7763, 5452, 4819, 4823, 4827), (8647, 2762, -1, -1, -1), (9321, 9347, -1, -1, -1), (7763, 7970, 7758, 7759, 7760), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (7755, 5452, 4803, 4807, 4811), (7763, 5452, 4819, 4823, 4827), (7763, 5452, 4819, 4823, 4827), (7755, 5452, 4803, 4807, 4811), (7763, 5452, 4819, 4823, 4827), (7763, 5452, 4819, 4823, 4827), (215, 5452, 4456, 4457, 4458)]
    bohemians_architecture = [(7665, 7664, 7659, 7660, 7661), (2575, 2573, 4429, 4430, 4431), (7665, 7664, 7659, 7660, 7661), (7680, 7681, 7676, 7677, 7678), (7680, 7681, 7676, 7677, 7678), (7706, 7705, 7700, 7701, 7702), (7771, 813, -1, -1, -1), (7734, 7733, 7728, 7729, 7730), (7734, 7733, 7728, 7729, 7730), (7734, 7733, 7728, 7729, 7730), (215, 205, 4456, 4457, 4458), (7763, 7970, 7758, 7759, 7760), (8042, 8041, 8036, 8037, 8038), (255, -1, 5354, 5355, 5356), (7763, 7970, 7758, 7759, 7760), (7779, 7778, 5538, 5539, 5540), (7775, 7774, 5538, 5539, 5540), (7787, 7778, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (7986, 248, 7978, 7979, 7980), (588, 37, 4610, 4611, 4612), (7783, 7774, 5538, 5539, 5540), (8116, 8115, 8110, 8111, 8112), (7794, 3853, 5541, 5542, 5543), (7790, 3851, 5541, 5542, 5543), (12370, 12371, 12373, 12374, 12375), (7951, 7950, 7945, 7946, 7947), (7811, 7810, 5544, 5545, 5546), (8068, 8067, 8062, 8063, 8064), (7658, 7657, 7652, 7653, 7654), (7807, 7806, 5544, 5545, 5546), (7819, 7810, 5544, 5545, 5546), (7815, 7806, 5544, 5545, 5546), (7794, 3853, 5547, 5548, 5549), (7790, 3851, 5547, 5548, 5549), (8061, 8060, 8055, 8056, 8057), (7673, 7674, 7669, 7670, 7671), (7734, 7733, 7728, 7729, 7730), (7673, 7674, 7669, 7670, 7671), (3241, 419, 4563, 4564, 4565), (7958, 7957, 7952, 7953, 7954), (8096, 37, 8150, 8152, 8154), (7923, 7924, 7919, 7920, 7921), (7930, 7931, 7926, 7927, 7928), (7930, 7931, 7926, 7927, 7928), (7706, 7705, 7700, 7701, 7702), (7755, 7969, 7750, 7751, 7752), (7966, 7965, 7960, 7961, 7962), (8002, 250, 7994, 7995, 7996), (8018, 252, 8010, 8011, 8012), (8042, 8041, 8036, 8037, 8038), (8068, 8067, 8062, 8063, 8064), (7916, 7915, 7911, 7912, 7913), (7916, 7915, 7911, 7912, 7913), (8084, 8085, 8080, 8081, 8082), (8090, 8091, 8086, 8087, 8088), (8123, 8122, 8117, 8118, 8119), (8131, 8130, 8125, 8126, 8127), (8139, 8138, 8133, 8134, 8135), (12403, 12404, 12406, 12407, 12408), (7710, 1757, -1, -1, -1), (8103, 1900, -1, -1, -1), (7909, 7908, 7904, 7905, 7906), (7916, 7915, 7911, 7912, 7913), (7916, 7915, 7911, 7912, 7913), (8006, 1751, -1, -1, -1), (8001, 1751, -1, -1, -1), (8000, 1751, -1, -1, -1), (7993, 40, 7994, 7995, 7996), (7799, 38, 5360, 5361, 5362), (7803, 38, 5360, 5361, 5362), (7831, 38, 5366, 5367, 5368), (7835, 38, 5366, 5367, 5368), (7698, 7697, 7692, 7693, 7694), (7974, 4174, -1, -1, -1), (7739, 4150, -1, -1, -1), (7768, 2720, -1, -1, -1), (7902, 2732, -1, -1, -1), (8026, 2762, -1, -1, -1), (8049, 8050, 8045, 8046, 8047), (8049, 8050, 8045, 8046, 8047), (8049, 8050, 8045, 8046, 8047), (8049, 8050, 8045, 8046, 8047), (7939, 7940, 7935, 7936, 7937), (7939, 7940, 7935, 7936, 7937), (7939, 7940, 7935, 7936, 7937), (7939, 7940, 7935, 7936, 7937), (8009, 40, 8010, 8011, 8012), (3223, 4172, 4633, 4634, 4635), (8022, 1751, -1, -1, -1), (8017, 1751, -1, -1, -1), (8016, 1751, -1, -1, -1), (7990, 1751, -1, -1, -1), (7985, 1751, -1, -1, -1), (7984, 1751, -1, -1, -1), (7977, 40, 7978, 7979, 7980), (7839, 7838, 5550, 5551, 5552), (7843, 7842, 5550, 5551, 5552), (7847, 7838, 5550, 5551, 5552), (7851, 7842, 5550, 5551, 5552), (7790, 3851, 5553, 5554, 5555), (7794, 3853, 5553, 5554, 5555), (7863, 38, 5372, 5373, 5374), (7867, 38, 5372, 5373, 5374), (7871, 7870, 5556, 5557, 5558), (7875, 7874, 5556, 5557, 5558), (7879, 7870, 5556, 5557, 5558), (7883, 7874, 5556, 5557, 5558), (7790, 3851, 5559, 5560, 5561), (7794, 3853, 5559, 5560, 5561), (7895, 38, 5378, 5379, 5380), (7899, 38, 5378, 5379, 5380), (4308, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (7755, 5452, 4803, 4807, 4811), (7763, 5452, 4819, 4823, 4827), (7763, 5452, 4819, 4823, 4827), (8647, 2762, -1, -1, -1), (9321, 9347, -1, -1, -1), (7763, 7970, 7758, 7759, 7760), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (7755, 5452, 4803, 4807, 4811), (7763, 5452, 4819, 4823, 4827), (7763, 5452, 4819, 4823, 4827), (7755, 5452, 4803, 4807, 4811), (7763, 5452, 4819, 4823, 4827), (7763, 5452, 4819, 4823, 4827), (215, 5452, 4456, 4457, 4458)]
    dravidians_architecture = [(9665, 9664, 9659, 9660, 9661), (2575, 2573, 4429, 4430, 4431), (9665, 9664, 9659, 9660, 9661), (9680, 9681, 9676, 9677, 9678), (9680, 9681, 9676, 9677, 9678), (9706, 9705, 9700, 9701, 9702), (10771, 813, -1, -1, -1), (9734, 9733, 9728, 9729, 9730), (9734, 9733, 9728, 9729, 9730), (9734, 9733, 9728, 9729, 9730), (215, 205, 4456, 4457, 4458), (9763, 10176, 9758, 9759, 9760), (10042, 10041, 10036, 10037, 10038), (255, -1, 5354, 5355, 5356), (9763, 10176, 9758, 9759, 9760), (9779, 9778, 5538, 5539, 5540), (9775, 9774, 5538, 5539, 5540), (9787, 9778, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (9986, 10556, 9978, 9979, 9980), (588, 37, 4610, 4611, 4612), (9783, 9774, 5538, 5539, 5540), (10116, 10115, 10110, 10111, 10112), (9794, 3861, 5541, 5542, 5543), (9790, 3859, 5541, 5542, 5543), (9747, 9746, 9741, 9742, 9743), (9951, 9950, 9945, 9946, 9947), (9811, 9810, 5544, 5545, 5546), (10068, 10067, 10062, 10063, 10064), (9658, 9657, 9652, 9653, 9654), (9807, 9806, 5544, 5545, 5546), (9819, 9810, 5544, 5545, 5546), (9815, 9806, 5544, 5545, 5546), (9794, 3861, 5547, 5548, 5549), (9790, 3859, 5547, 5548, 5549), (10061, 10060, 10055, 10056, 10057), (9673, 9674, 9669, 9670, 9671), (9734, 9733, 9728, 9729, 9730), (9673, 9674, 9669, 9670, 9671), (3241, 419, 4563, 4564, 4565), (9958, 9957, 9952, 9953, 9954), (10096, 37, 10150, 10152, 10154), (9923, 9924, 9919, 9920, 9921), (9930, 9931, 9926, 9927, 9928), (9930, 9931, 9926, 9927, 9928), (9706, 9705, 9700, 9701, 9702), (9755, 10175, 9750, 9751, 9752), (9964, 10174, 9960, 9961, 9962), (10002, 10558, 9994, 9995, 9996), (10018, 10560, 10010, 10011, 10012), (10042, 10041, 10036, 10037, 10038), (10068, 10067, 10062, 10063, 10064), (9916, 9915, 9911, 9912, 9913), (9916, 9915, 9911, 9912, 9913), (10084, 10085, 10080, 10081, 10082), (10090, 10091, 10086, 10087, 10088), (10123, 10122, 10117, 10118, 10119), (10131, 10130, 10125, 10126, 10127), (10139, 10138, 10133, 10134, 10135), (7651, 7650, 7244, 7245, 7246), (10710, 1757, -1, -1, -1), (11103, 1900, -1, -1, -1), (9909, 9908, 9904, 9905, 9906), (9916, 9915, 9911, 9912, 9913), (9916, 9915, 9911, 9912, 9913), (10006, 1751, -1, -1, -1), (10001, 1751, -1, -1, -1), (10000, 1751, -1, -1, -1), (9993, 40, 9994, 9995, 9996), (9799, 38, 5360, 5361, 5362), (9803, 38, 5360, 5361, 5362), (9831, 38, 5366, 5367, 5368), (9835, 38, 5366, 5367, 5368), (9698, 9697, 9692, 9693, 9694), (10974, 4174, -1, -1, -1), (10739, 4150, -1, -1, -1), (10768, 2720, -1, -1, -1), (10902, 2732, -1, -1, -1), (11026, 2762, -1, -1, -1), (10049, 10050, 10045, 10046, 10047), (10049, 10050, 10045, 10046, 10047), (10049, 10050, 10045, 10046, 10047), (10049, 10050, 10045, 10046, 10047), (9939, 9940, 9935, 9936, 9937), (9939, 9940, 9935, 9936, 9937), (9939, 9940, 9935, 9936, 9937), (9939, 9940, 9935, 9936, 9937), (10009, 40, 10010, 10011, 10012), (3223, 4172, 4633, 4634, 4635), (10022, 1751, -1, -1, -1), (10017, 1751, -1, -1, -1), (10016, 1751, -1, -1, -1), (9990, 1751, -1, -1, -1), (9985, 1751, -1, -1, -1), (9984, 1751, -1, -1, -1), (9977, 40, 9978, 9979, 9980), (9839, 9838, 5550, 5551, 5552), (9843, 9842, 5550, 5551, 5552), (9847, 9838, 5550, 5551, 5552), (9851, 9842, 5550, 5551, 5552), (9790, 3859, 5553, 5554, 5555), (9794, 3861, 5553, 5554, 5555), (9863, 38, 5372, 5373, 5374), (9867, 38, 5372, 5373, 5374), (9871, 9870, 5556, 5557, 5558), (9875, 9874, 5556, 5557, 5558), (9879, 9870, 5556, 5557, 5558), (9883, 9874, 5556, 5557, 5558), (9790, 3859, 5559, 5560, 5561), (9794, 3861, 5559, 5560, 5561), (9895, 38, 5378, 5379, 5380), (9899, 38, 5378, 5379, 5380), (4320, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (9755, 5452, 4803, 4807, 4811), (9763, 5452, 4819, 4823, 4827), (9763, 5452, 4819, 4823, 4827), (9647, 2762, -1, -1, -1), (10321, 9347, -1, -1, -1), (9763, 10176, 9758, 9759, 9760), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (9755, 5452, 4803, 4807, 4811), (9763, 5452, 4819, 4823, 4827), (9763, 5452, 4819, 4823, 4827), (9755, 5452, 4803, 4807, 4811), (9763, 5452, 4819, 4823, 4827), (9763, 5452, 4819, 4823, 4827), (215, 5452, 4456, 4457, 4458)]
    bengalis_architecture = [(9665, 9664, 9659, 9660, 9661), (2575, 2573, 4429, 4430, 4431), (9665, 9664, 9659, 9660, 9661), (9680, 9681, 9676, 9677, 9678), (9680, 9681, 9676, 9677, 9678), (9706, 9705, 9700, 9701, 9702), (10771, 813, -1, -1, -1), (9734, 9733, 9728, 9729, 9730), (9734, 9733, 9728, 9729, 9730), (9734, 9733, 9728, 9729, 9730), (215, 205, 4456, 4457, 4458), (9763, 10176, 9758, 9759, 9760), (10042, 10041, 10036, 10037, 10038), (255, -1, 5354, 5355, 5356), (9763, 10176, 9758, 9759, 9760), (9779, 9778, 5538, 5539, 5540), (9775, 9774, 5538, 5539, 5540), (9787, 9778, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (9986, 10556, 9978, 9979, 9980), (588, 37, 4610, 4611, 4612), (9783, 9774, 5538, 5539, 5540), (10116, 10115, 10110, 10111, 10112), (9794, 3861, 5541, 5542, 5543), (9790, 3859, 5541, 5542, 5543), (12461, 12462, 12464, 12465, 12466), (9951, 9950, 9945, 9946, 9947), (9811, 9810, 5544, 5545, 5546), (10068, 10067, 10062, 10063, 10064), (9658, 9657, 9652, 9653, 9654), (9807, 9806, 5544, 5545, 5546), (9819, 9810, 5544, 5545, 5546), (9815, 9806, 5544, 5545, 5546), (9794, 3861, 5547, 5548, 5549), (9790, 3859, 5547, 5548, 5549), (10061, 10060, 10055, 10056, 10057), (9673, 9674, 9669, 9670, 9671), (9734, 9733, 9728, 9729, 9730), (9673, 9674, 9669, 9670, 9671), (3241, 419, 4563, 4564, 4565), (9958, 9957, 9952, 9953, 9954), (10096, 37, 10150, 10152, 10154), (9923, 9924, 9919, 9920, 9921), (9930, 9931, 9926, 9927, 9928), (9930, 9931, 9926, 9927, 9928), (9706, 9705, 9700, 9701, 9702), (9755, 10175, 9750, 9751, 9752), (9964, 10174, 9960, 9961, 9962), (10002, 10558, 9994, 9995, 9996), (10018, 10560, 10010, 10011, 10012), (10042, 10041, 10036, 10037, 10038), (10068, 10067, 10062, 10063, 10064), (9916, 9915, 9911, 9912, 9913), (9916, 9915, 9911, 9912, 9913), (10084, 10085, 10080, 10081, 10082), (10090, 10091, 10086, 10087, 10088), (10123, 10122, 10117, 10118, 10119), (10131, 10130, 10125, 10126, 10127), (10139, 10138, 10133, 10134, 10135), (12485, 12486, 12488, 12489, 12490), (10710, 1757, -1, -1, -1), (11103, 1900, -1, -1, -1), (9909, 9908, 9904, 9905, 9906), (9916, 9915, 9911, 9912, 9913), (9916, 9915, 9911, 9912, 9913), (10006, 1751, -1, -1, -1), (10001, 1751, -1, -1, -1), (10000, 1751, -1, -1, -1), (9993, 40, 9994, 9995, 9996), (9799, 38, 5360, 5361, 5362), (9803, 38, 5360, 5361, 5362), (9831, 38, 5366, 5367, 5368), (9835, 38, 5366, 5367, 5368), (9698, 9697, 9692, 9693, 9694), (10974, 4174, -1, -1, -1), (10739, 4150, -1, -1, -1), (10768, 2720, -1, -1, -1), (10902, 2732, -1, -1, -1), (11026, 2762, -1, -1, -1), (10049, 10050, 10045, 10046, 10047), (10049, 10050, 10045, 10046, 10047), (10049, 10050, 10045, 10046, 10047), (10049, 10050, 10045, 10046, 10047), (9939, 9940, 9935, 9936, 9937), (9939, 9940, 9935, 9936, 9937), (9939, 9940, 9935, 9936, 9937), (9939, 9940, 9935, 9936, 9937), (10009, 40, 10010, 10011, 10012), (3223, 4172, 4633, 4634, 4635), (10022, 1751, -1, -1, -1), (10017, 1751, -1, -1, -1), (10016, 1751, -1, -1, -1), (9990, 1751, -1, -1, -1), (9985, 1751, -1, -1, -1), (9984, 1751, -1, -1, -1), (9977, 40, 9978, 9979, 9980), (9839, 9838, 5550, 5551, 5552), (9843, 9842, 5550, 5551, 5552), (9847, 9838, 5550, 5551, 5552), (9851, 9842, 5550, 5551, 5552), (9790, 3859, 5553, 5554, 5555), (9794, 3861, 5553, 5554, 5555), (9863, 38, 5372, 5373, 5374), (9867, 38, 5372, 5373, 5374), (9871, 9870, 5556, 5557, 5558), (9875, 9874, 5556, 5557, 5558), (9879, 9870, 5556, 5557, 5558), (9883, 9874, 5556, 5557, 5558), (9790, 3859, 5559, 5560, 5561), (9794, 3861, 5559, 5560, 5561), (9895, 38, 5378, 5379, 5380), (9899, 38, 5378, 5379, 5380), (4320, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (9755, 5452, 4803, 4807, 4811), (9763, 5452, 4819, 4823, 4827), (9763, 5452, 4819, 4823, 4827), (9647, 2762, -1, -1, -1), (10321, 9347, -1, -1, -1), (9763, 10176, 9758, 9759, 9760), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (9755, 5452, 4803, 4807, 4811), (9763, 5452, 4819, 4823, 4827), (9763, 5452, 4819, 4823, 4827), (9755, 5452, 4803, 4807, 4811), (9763, 5452, 4819, 4823, 4827), (9763, 5452, 4819, 4823, 4827), (215, 5452, 4456, 4457, 4458)]
    gurjaras_architecture = [(9665, 9664, 9659, 9660, 9661), (2575, 2573, 4429, 4430, 4431), (9665, 9664, 9659, 9660, 9661), (9680, 9681, 9676, 9677, 9678), (9680, 9681, 9676, 9677, 9678), (9706, 9705, 9700, 9701, 9702), (4012, 813, -1, -1, -1), (9734, 9733, 9728, 9729, 9730), (9734, 9733, 9728, 9729, 9730), (9734, 9733, 9728, 9729, 9730), (215, 205, 4456, 4457, 4458), (9763, 10176, 9758, 9759, 9760), (10042, 10041, 10036, 10037, 10038), (255, -1, 5354, 5355, 5356), (9763, 10176, 9758, 9759, 9760), (9779, 9778, 5538, 5539, 5540), (9775, 9774, 5538, 5539, 5540), (9787, 9778, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (9986, 10556, 9978, 9979, 9980), (588, 37, 4610, 4611, 4612), (9783, 9774, 5538, 5539, 5540), (10116, 10115, 10110, 10111, 10112), (9794, 3861, 5541, 5542, 5543), (9790, 3859, 5541, 5542, 5543), (12469, 12470, 12472, 12473, 12474), (9951, 9950, 9945, 9946, 9947), (9811, 9810, 5544, 5545, 5546), (10068, 10067, 10062, 10063, 10064), (9658, 9657, 9652, 9653, 9654), (9807, 9806, 5544, 5545, 5546), (9819, 9810, 5544, 5545, 5546), (9815, 9806, 5544, 5545, 5546), (9794, 3861, 5547, 5548, 5549), (9790, 3859, 5547, 5548, 5549), (10061, 10060, 10055, 10056, 10057), (9673, 9674, 9669, 9670, 9671), (9734, 9733, 9728, 9729, 9730), (9673, 9674, 9669, 9670, 9671), (3241, 419, 4563, 4564, 4565), (9958, 9957, 9952, 9953, 9954), (10096, 37, 10150, 10152, 10154), (9923, 9924, 9919, 9920, 9921), (9930, 9931, 9926, 9927, 9928), (9930, 9931, 9926, 9927, 9928), (9706, 9705, 9700, 9701, 9702), (9755, 10175, 9750, 9751, 9752), (9964, 10174, 9960, 9961, 9962), (10002, 10558, 9994, 9995, 9996), (10018, 10560, 10010, 10011, 10012), (10042, 10041, 10036, 10037, 10038), (10068, 10067, 10062, 10063, 10064), (9916, 9915, 9911, 9912, 9913), (9916, 9915, 9911, 9912, 9913), (10084, 10085, 10080, 10081, 10082), (10090, 10091, 10086, 10087, 10088), (10123, 10122, 10117, 10118, 10119), (10131, 10130, 10125, 10126, 10127), (10139, 10138, 10133, 10134, 10135), (12492, 12493, 12495, 12496, 12497), (3960, 1757, -1, -1, -1), (3888, 1900, -1, -1, -1), (9909, 9908, 9904, 9905, 9906), (9916, 9915, 9911, 9912, 9913), (9916, 9915, 9911, 9912, 9913), (10006, 1751, -1, -1, -1), (10001, 1751, -1, -1, -1), (10000, 1751, -1, -1, -1), (9993, 40, 9994, 9995, 9996), (9799, 38, 5360, 5361, 5362), (9803, 38, 5360, 5361, 5362), (9831, 38, 5366, 5367, 5368), (9835, 38, 5366, 5367, 5368), (9698, 9697, 9692, 9693, 9694), (4038, 4174, -1, -1, -1), (3987, 4150, -1, -1, -1), (4181, 2720, -1, -1, -1), (4025, 2732, -1, -1, -1), (4051, 2762, -1, -1, -1), (10049, 10050, 10045, 10046, 10047), (10049, 10050, 10045, 10046, 10047), (10049, 10050, 10045, 10046, 10047), (10049, 10050, 10045, 10046, 10047), (9939, 9940, 9935, 9936, 9937), (9939, 9940, 9935, 9936, 9937), (9939, 9940, 9935, 9936, 9937), (9939, 9940, 9935, 9936, 9937), (10009, 40, 10010, 10011, 10012), (3223, 4172, 4633, 4634, 4635), (10022, 1751, -1, -1, -1), (10017, 1751, -1, -1, -1), (10016, 1751, -1, -1, -1), (9990, 1751, -1, -1, -1), (9985, 1751, -1, -1, -1), (9984, 1751, -1, -1, -1), (9977, 40, 9978, 9979, 9980), (9839, 9838, 5550, 5551, 5552), (9843, 9842, 5550, 5551, 5552), (9847, 9838, 5550, 5551, 5552), (9851, 9842, 5550, 5551, 5552), (9790, 3859, 5553, 5554, 5555), (9794, 3861, 5553, 5554, 5555), (9863, 38, 5372, 5373, 5374), (9867, 38, 5372, 5373, 5374), (9871, 9870, 5556, 5557, 5558), (9875, 9874, 5556, 5557, 5558), (9879, 9870, 5556, 5557, 5558), (9883, 9874, 5556, 5557, 5558), (9790, 3859, 5559, 5560, 5561), (9794, 3861, 5559, 5560, 5561), (9895, 38, 5378, 5379, 5380), (9899, 38, 5378, 5379, 5380), (4298, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (9755, 5452, 4803, 4807, 4811), (9763, 5452, 4819, 4823, 4827), (9763, 5452, 4819, 4823, 4827), (8638, 2762, -1, -1, -1), (9312, 9347, -1, -1, -1), (9763, 10176, 9758, 9759, 9760), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (9755, 5452, 4803, 4807, 4811), (9763, 5452, 4819, 4823, 4827), (9763, 5452, 4819, 4823, 4827), (9755, 5452, 4803, 4807, 4811), (9763, 5452, 4819, 4823, 4827), (9763, 5452, 4819, 4823, 4827), (215, 5452, 4456, 4457, 4458)]
    romans_architecture = [(27, 26, 4532, 4533, 4534), (2575, 2573, 4429, 4430, 4431), (27, 26, 4532, 4533, 4534), (71, 72, 4567, 4568, 4569), (71, 72, 4567, 4568, 4569), (108, 107, 4542, 4543, 4544), (9262, 813, -1, -1, -1), (153, 152, 8277, 8278, 8279), (153, 152, 8277, 8278, 8279), (153, 152, 8277, 8278, 8279), (215, 205, 4456, 4457, 4458), (242, 135, 4605, 4606, 4607), (492, 491, 4537, 4538, 4539), (255, -1, 5354, 5355, 5356), (242, 135, 4605, 4606, 4607), (7421, 7420, 5538, 5539, 5540), (7417, 7416, 5538, 5539, 5540), (7429, 7420, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (12249, 266, 9210, 9211, 9212), (588, 37, 4610, 4611, 4612), (7425, 7416, 5538, 5539, 5540), (4171, 4170, 4636, 4637, 4638), (7436, 3845, 5541, 5542, 5543), (7432, 3843, 5541, 5542, 5543), (12566, 12567, 12569, 12570, 12571), (417, 416, 9177, 9178, 9179), (7453, 7452, 5544, 5545, 5546), (528, 527, 4576, 4577, 4578), (30, 29, 9165, 9166, 9167), (7449, 7448, 5544, 5545, 5546), (7461, 7452, 5544, 5545, 5546), (7457, 7448, 5544, 5545, 5546), (7436, 3845, 5547, 5548, 5549), (7432, 3843, 5547, 5548, 5549), (531, 530, 9216, 9217, 9218), (74, 75, 9191, 9192, 9193), (153, 152, 8277, 8278, 8279), (74, 75, 9191, 9192, 9193), (3241, 419, 4563, 4564, 4565), (414, 413, 4581, 4582, 4583), (7390, 37, 7398, 7400, 7402), (9196, 9197, 9198, 9199, 9200), (386, 387, 4618, 4619, 4620), (386, 387, 4618, 4619, 4620), (108, 107, 4542, 4543, 4544), (9182, 129, 9184, 9185, 9186), (3436, 2278, 4592, 4593, 4594), (3237, 278, 12253, 12254, 12255), (3229, 290, 12258, 12259, 12260), (492, 491, 4537, 4538, 4539), (528, 527, 4576, 4577, 4578), (2226, 2225, 4527, 4528, 4529), (2226, 2225, 4527, 4528, 4529), (593, 594, 4571, 4572, 4573), (596, 597, 4597, 4598, 4599), (2517, 2516, 4613, 4614, 4615), (2395, 2390, 4623, 4624, 4625), (2398, 2391, 4628, 4629, 4630), (7614, 7613, 3927, 3928, 3929), (9241, 1757, -1, -1, -1), (9282, 1900, -1, -1, -1), (9202, 2228, 9203, 9204, 9205), (2226, 2225, 4527, 4528, 4529), (2226, 2225, 4527, 4528, 4529), (432, 1751, -1, -1, -1), (3236, 1751, -1, -1, -1), (3235, 1751, -1, -1, -1), (3344, 40, 5428, 5429, 5430), (7441, 38, 5360, 5361, 5362), (7445, 38, 5360, 5361, 5362), (7473, 38, 5366, 5367, 5368), (7477, 38, 5366, 5367, 5368), (111, 110, 9171, 9172, 9173), (9267, 4174, -1, -1, -1), (9256, 4150, -1, -1, -1), (9259, 2720, -1, -1, -1), (9265, 2732, -1, -1, -1), (9271, 2762, -1, -1, -1), (3202, 3203, 3205, 3206, 3207), (3202, 3203, 3205, 3206, 3207), (3202, 3203, 3205, 3206, 3207), (3202, 3203, 3205, 3206, 3207), (3195, 3196, 3198, 3199, 3200), (3195, 3196, 3198, 3199, 3200), (3195, 3196, 3198, 3199, 3200), (3195, 3196, 3198, 3199, 3200), (3231, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (429, 1751, -1, -1, -1), (3228, 1751, -1, -1, -1), (3227, 1751, -1, -1, -1), (9207, 1751, -1, -1, -1), (12251, 1751, -1, -1, -1), (9208, 1751, -1, -1, -1), (9226, 40, 9230, 9231, 9232), (7481, 7480, 5550, 5551, 5552), (7485, 7484, 5550, 5551, 5552), (7489, 7480, 5550, 5551, 5552), (7493, 7484, 5550, 5551, 5552), (7432, 3843, 5553, 5554, 5555), (7436, 3845, 5553, 5554, 5555), (7505, 38, 5372, 5373, 5374), (7509, 38, 5372, 5373, 5374), (7513, 7512, 5556, 5557, 5558), (7517, 7516, 5556, 5557, 5558), (7521, 7512, 5556, 5557, 5558), (7525, 7516, 5556, 5557, 5558), (7432, 3843, 5559, 5560, 5561), (7436, 3845, 5559, 5560, 5561), (7537, 38, 5378, 5379, 5380), (7541, 38, 5378, 5379, 5380), (4314, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (224, 5452, 4806, 4810, 4814), (242, 5452, 4821, 4825, 4829), (242, 5452, 4821, 4825, 4829), (8644, 2762, -1, -1, -1), (9318, 9347, -1, -1, -1), (242, 135, 4821, 4825, 4829), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (224, 5452, 4806, 4810, 4814), (236, 5452, 4822, 4826, 4830), (236, 5452, 4822, 4826, 4830), (224, 5452, 4806, 4810, 4814), (236, 5452, 4822, 4826, 4830), (236, 5452, 4822, 4826, 4830), (215, 5452, 4456, 4457, 4458)]
    armenians_architecture = [(27, 26, 4532, 4533, 4534), (2575, 2573, 4429, 4430, 4431), (27, 26, 4532, 4533, 4534), (71, 72, 4567, 4568, 4569), (71, 72, 4567, 4568, 4569), (108, 107, 4542, 4543, 4544), (9262, 813, -1, -1, -1), (153, 152, 8277, 8278, 8279), (153, 152, 8277, 8278, 8279), (153, 152, 8277, 8278, 8279), (215, 205, 4456, 4457, 4458), (242, 135, 4605, 4606, 4607), (492, 491, 4537, 4538, 4539), (255, -1, 5354, 5355, 5356), (242, 135, 4605, 4606, 4607), (7421, 7420, 5538, 5539, 5540), (7417, 7416, 5538, 5539, 5540), (7429, 7420, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (12249, 266, 9210, 9211, 9212), (588, 37, 4610, 4611, 4612), (7425, 7416, 5538, 5539, 5540), (4171, 4170, 4636, 4637, 4638), (7436, 3845, 5541, 5542, 5543), (7432, 3843, 5541, 5542, 5543), (12586, 12587, 12589, 12590, 12591), (417, 416, 9177, 9178, 9179), (7453, 7452, 5544, 5545, 5546), (528, 527, 4576, 4577, 4578), (30, 29, 9165, 9166, 9167), (7449, 7448, 5544, 5545, 5546), (7461, 7452, 5544, 5545, 5546), (7457, 7448, 5544, 5545, 5546), (7436, 3845, 5547, 5548, 5549), (7432, 3843, 5547, 5548, 5549), (531, 530, 9216, 9217, 9218), (74, 75, 9191, 9192, 9193), (153, 152, 8277, 8278, 8279), (74, 75, 9191, 9192, 9193), (3241, 419, 4563, 4564, 4565), (414, 413, 4581, 4582, 4583), (7390, 37, 7398, 7400, 7402), (9196, 9197, 9198, 9199, 9200), (386, 387, 4618, 4619, 4620), (386, 387, 4618, 4619, 4620), (108, 107, 4542, 4543, 4544), (9182, 129, 9184, 9185, 9186), (3436, 2278, 4592, 4593, 4594), (3237, 278, 12253, 12254, 12255), (3229, 290, 12258, 12259, 12260), (492, 491, 4537, 4538, 4539), (528, 527, 4576, 4577, 4578), (2226, 2225, 4527, 4528, 4529), (2226, 2225, 4527, 4528, 4529), (593, 594, 4571, 4572, 4573), (596, 597, 4597, 4598, 4599), (2517, 2516, 4613, 4614, 4615), (2395, 2390, 4623, 4624, 4625), (2398, 2391, 4628, 4629, 4630), (12602, 12603, 12605, 12606, 12607), (9241, 1757, -1, -1, -1), (9282, 1900, -1, -1, -1), (9202, 2228, 9203, 9204, 9205), (2226, 2225, 4527, 4528, 4529), (2226, 2225, 4527, 4528, 4529), (432, 1751, -1, -1, -1), (3236, 1751, -1, -1, -1), (3235, 1751, -1, -1, -1), (3344, 40, 5428, 5429, 5430), (7441, 38, 5360, 5361, 5362), (7445, 38, 5360, 5361, 5362), (7473, 38, 5366, 5367, 5368), (7477, 38, 5366, 5367, 5368), (111, 110, 9171, 9172, 9173), (9267, 4174, -1, -1, -1), (9256, 4150, -1, -1, -1), (9259, 2720, -1, -1, -1), (9265, 2732, -1, -1, -1), (9271, 2762, -1, -1, -1), (3202, 3203, 3205, 3206, 3207), (3202, 3203, 3205, 3206, 3207), (3202, 3203, 3205, 3206, 3207), (3202, 3203, 3205, 3206, 3207), (3195, 3196, 3198, 3199, 3200), (3195, 3196, 3198, 3199, 3200), (3195, 3196, 3198, 3199, 3200), (3195, 3196, 3198, 3199, 3200), (3231, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (429, 1751, -1, -1, -1), (3228, 1751, -1, -1, -1), (3227, 1751, -1, -1, -1), (9207, 1751, -1, -1, -1), (12251, 1751, -1, -1, -1), (9208, 1751, -1, -1, -1), (9226, 40, 9230, 9231, 9232), (7481, 7480, 5550, 5551, 5552), (7485, 7484, 5550, 5551, 5552), (7489, 7480, 5550, 5551, 5552), (7493, 7484, 5550, 5551, 5552), (7432, 3843, 5553, 5554, 5555), (7436, 3845, 5553, 5554, 5555), (7505, 38, 5372, 5373, 5374), (7509, 38, 5372, 5373, 5374), (7513, 7512, 5556, 5557, 5558), (7517, 7516, 5556, 5557, 5558), (7521, 7512, 5556, 5557, 5558), (7525, 7516, 5556, 5557, 5558), (7432, 3843, 5559, 5560, 5561), (7436, 3845, 5559, 5560, 5561), (7537, 38, 5378, 5379, 5380), (7541, 38, 5378, 5379, 5380), (4314, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (224, 5452, 4806, 4810, 4814), (242, 5452, 4821, 4825, 4829), (242, 5452, 4821, 4825, 4829), (8644, 2762, -1, -1, -1), (9318, 9347, -1, -1, -1), (242, 135, 4821, 4825, 4829), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (224, 5452, 4806, 4810, 4814), (242, 5452, 4821, 4825, 4829), (242, 5452, 4821, 4825, 4829), (224, 5452, 4806, 4810, 4814), (242, 5452, 4821, 4825, 4829), (242, 5452, 4821, 4825, 4829), (215, 5452, 4456, 4457, 4458)]
    georgians_architecture = [(27, 26, 4532, 4533, 4534), (2575, 2573, 4429, 4430, 4431), (27, 26, 4532, 4533, 4534), (71, 72, 4567, 4568, 4569), (71, 72, 4567, 4568, 4569), (108, 107, 4542, 4543, 4544), (9262, 813, -1, -1, -1), (153, 152, 8277, 8278, 8279), (153, 152, 8277, 8278, 8279), (153, 152, 8277, 8278, 8279), (215, 205, 4456, 4457, 4458), (242, 135, 4605, 4606, 4607), (492, 491, 4537, 4538, 4539), (255, -1, 5354, 5355, 5356), (242, 135, 4605, 4606, 4607), (7421, 7420, 5538, 5539, 5540), (7417, 7416, 5538, 5539, 5540), (7429, 7420, 5538, 5539, 5540), (3124, 3125, 4524, 4525, 4526), (2197, 2196, 4503, 4504, 4505), (12249, 266, 9210, 9211, 9212), (588, 37, 4610, 4611, 4612), (7425, 7416, 5538, 5539, 5540), (4171, 4170, 4636, 4637, 4638), (7436, 3845, 5541, 5542, 5543), (7432, 3843, 5541, 5542, 5543), (12594, 12595, 12597, 12598, 12599), (417, 416, 9177, 9178, 9179), (7453, 7452, 5544, 5545, 5546), (528, 527, 4576, 4577, 4578), (30, 29, 9165, 9166, 9167), (7449, 7448, 5544, 5545, 5546), (7461, 7452, 5544, 5545, 5546), (7457, 7448, 5544, 5545, 5546), (7436, 3845, 5547, 5548, 5549), (7432, 3843, 5547, 5548, 5549), (531, 530, 9216, 9217, 9218), (74, 75, 9191, 9192, 9193), (153, 152, 8277, 8278, 8279), (74, 75, 9191, 9192, 9193), (3241, 419, 4563, 4564, 4565), (414, 413, 4581, 4582, 4583), (7390, 37, 7398, 7400, 7402), (9196, 9197, 9198, 9199, 9200), (386, 387, 4618, 4619, 4620), (386, 387, 4618, 4619, 4620), (108, 107, 4542, 4543, 4544), (9182, 129, 9184, 9185, 9186), (3436, 2278, 4592, 4593, 4594), (3237, 278, 12253, 12254, 12255), (3229, 290, 12258, 12259, 12260), (492, 491, 4537, 4538, 4539), (528, 527, 4576, 4577, 4578), (2226, 2225, 4527, 4528, 4529), (2226, 2225, 4527, 4528, 4529), (593, 594, 4571, 4572, 4573), (596, 597, 4597, 4598, 4599), (2517, 2516, 4613, 4614, 4615), (2395, 2390, 4623, 4624, 4625), (2398, 2391, 4628, 4629, 4630), (12609, 12610, 12612, 12613, 12614), (9241, 1757, -1, -1, -1), (9282, 1900, -1, -1, -1), (9202, 2228, 9203, 9204, 9205), (2226, 2225, 4527, 4528, 4529), (2226, 2225, 4527, 4528, 4529), (432, 1751, -1, -1, -1), (3236, 1751, -1, -1, -1), (3235, 1751, -1, -1, -1), (3344, 40, 5428, 5429, 5430), (7441, 38, 5360, 5361, 5362), (7445, 38, 5360, 5361, 5362), (7473, 38, 5366, 5367, 5368), (7477, 38, 5366, 5367, 5368), (111, 110, 9171, 9172, 9173), (9267, 4174, -1, -1, -1), (9256, 4150, -1, -1, -1), (9259, 2720, -1, -1, -1), (9265, 2732, -1, -1, -1), (9271, 2762, -1, -1, -1), (3202, 3203, 3205, 3206, 3207), (3202, 3203, 3205, 3206, 3207), (3202, 3203, 3205, 3206, 3207), (3202, 3203, 3205, 3206, 3207), (3195, 3196, 3198, 3199, 3200), (3195, 3196, 3198, 3199, 3200), (3195, 3196, 3198, 3199, 3200), (3195, 3196, 3198, 3199, 3200), (3231, 40, 5431, 5432, 5433), (3223, 4172, 4633, 4634, 4635), (429, 1751, -1, -1, -1), (3228, 1751, -1, -1, -1), (3227, 1751, -1, -1, -1), (9207, 1751, -1, -1, -1), (12251, 1751, -1, -1, -1), (9208, 1751, -1, -1, -1), (9226, 40, 9230, 9231, 9232), (7481, 7480, 5550, 5551, 5552), (7485, 7484, 5550, 5551, 5552), (7489, 7480, 5550, 5551, 5552), (7493, 7484, 5550, 5551, 5552), (7432, 3843, 5553, 5554, 5555), (7436, 3845, 5553, 5554, 5555), (7505, 38, 5372, 5373, 5374), (7509, 38, 5372, 5373, 5374), (7513, 7512, 5556, 5557, 5558), (7517, 7516, 5556, 5557, 5558), (7521, 7512, 5556, 5557, 5558), (7525, 7516, 5556, 5557, 5558), (7432, 3843, 5559, 5560, 5561), (7436, 3845, 5559, 5560, 5561), (7537, 38, 5378, 5379, 5380), (7541, 38, 5378, 5379, 5380), (4314, 1757, -1, -1, -1), (8185, 8187, 6492, 6493, 6494), (8188, 8187, 6492, 6493, 6494), (6505, 3871, 6501, 6502, 6503), (8208, 38, 6509, 6510, 6511), (8191, 8190, 6513, 6514, 6515), (8194, 8190, 6513, 6514, 6515), (6505, 3871, 6522, 6523, 6524), (8210, 38, 6530, 6531, 6532), (8197, 8196, 6534, 6535, 6536), (8200, 8196, 6534, 6535, 6536), (6505, 3871, 6543, 6544, 6545), (8212, 38, 6551, 6552, 6553), (8203, 8202, 6555, 6556, 6557), (8206, 8202, 6555, 6556, 6557), (6505, 3871, 6564, 6565, 6566), (8214, 38, 6572, 6573, 6574), (215, 5452, 4456, 4457, 4458), (224, 5452, 4806, 4810, 4814), (242, 5452, 4821, 4825, 4829), (242, 5452, 4821, 4825, 4829), (8644, 2762, -1, -1, -1), (9318, 9347, -1, -1, -1), (242, 135, 4821, 4825, 4829), (1751, 37, -1, -1, -1), (3815, 3816, 3818, 3819, 3820), (2268, 2264, 4994, 4998, 5002), (5954, 5955, 5957, 5958, 5959), (12350, 12351, 12353, 12354, 12355), (12357, 12358, 12360, 12361, 12362), (12418, 12419, 12421, 12422, 12423), (12584, 12583, -1, -1, -1), (12636, 12635, -1, -1, -1), (224, 5452, 4806, 4810, 4814), (242, 5452, 4821, 4825, 4829), (242, 5452, 4821, 4825, 4829), (224, 5452, 4806, 4810, 4814), (242, 5452, 4821, 4825, 4829), (242, 5452, 4821, 4825, 4829), (215, 5452, 4456, 4457, 4458)]
    
    architecture_sets = [britons_architecture, franks_architecture, goths_architecture, teutons_architecture, japanese_architecture, chinese_architecture, byzantines_architecture, persians_architecture, saracens_architecture, turks_architecture, vikings_architecture, mongols_architecture, celts_architecture, spanish_architecture, aztecs_architecture, mayans_architecture, huns_architecture, koreans_architecture, italians_architecture, indians_architecture, incas_architecture, magyar_architecture, slavs_architecture, portuguese_architecture, ethiopians_architecture, malians_architecture, berbers_architecture, khmer_architecture, malay_architecture, burmese_architecture, vietnamese_architecture, bulgarians_architecture, tatars_architecture, cumans_architecture, lithuanians_architecture, burgundians_architecture, sicilians_architecture, poles_architecture, bohemians_architecture, dravidians_architecture, bengalis_architecture, gurjaras_architecture, romans_architecture, armenians_architecture, georgians_architecture]

    # Set architecture
    for i, current_unit in enumerate(all_units_to_change):
        # Set standing graphic
        try:
            standing_graphic_list = list(DATA.civs[CURRENT_CIV_INDEX + 1].units[current_unit].standing_graphic)  # Convert to list for modification
            standing_graphic_list[0] = architecture_sets[selected_architecture][i][0]
            DATA.civs[CURRENT_CIV_INDEX + 1].units[current_unit].standing_graphic = tuple(standing_graphic_list)  # Convert back to tuple
        except Exception as e:
            traceback.print_exc()

        # Set dying graphic
        try:
            DATA.civs[CURRENT_CIV_INDEX + 1].units[current_unit].dying_graphic = architecture_sets[selected_architecture][i][1]
        except Exception as e:
            traceback.print_exc()

        # Set damaged graphics
        try:
            for j in range(3):  # Loop through the first 3 damage graphics
                    if j < len(DATA.civs[CURRENT_CIV_INDEX + 1].units[current_unit].damage_graphics):
                        DATA.civs[CURRENT_CIV_INDEX + 1].units[current_unit].damage_graphics[j].graphic_id = architecture_sets[selected_architecture][i][2 + j]
        except Exception as e:
            traceback.print_exc()

def update_language_dropdown():
    # Get the current index
    selected_language = MAIN_WINDOW.language_dropdown.currentIndex()

    def change_sound(sound_index, amount):
        for i in range(amount):
            try:
                edit_name = DATA.sounds[sound_index].items[CURRENT_CIV_INDEX * amount + i].filename.split('_')
                edit_name[0] = MAIN_WINDOW.language_dropdown.currentText()
                DATA.sounds[sound_index].items[CURRENT_CIV_INDEX * amount + i].filename = '_'.join(edit_name)
            except:
                show_error_message(rf"Sounds for {civilisation_objects[CURRENT_CIV_INDEX].true_name} have been corrupted.")
                break

            # Update language in sounds list
            try:
                sounds_list[CURRENT_CIV_INDEX] = MAIN_WINDOW.language_dropdown.currentText()
            except:
                pass

    # Change the sounds for each unit
    change_sound(303, 4)
    change_sound(301, 4)
    change_sound(295, 1)
    change_sound(299, 1)
    change_sound(455, 1)
    change_sound(448, 1)
    change_sound(297, 1)
    change_sound(298, 1)
    change_sound(300, 1)
    change_sound(302, 1)

    change_sound(435, 4)
    change_sound(434, 4)
    change_sound(437, 1)
    change_sound(442, 1)
    change_sound(438, 1)
    change_sound(487, 1)
    change_sound(440, 1)
    change_sound(441, 1)
    change_sound(443, 1)
    change_sound(444, 1)

    change_sound(420, 3)
    change_sound(421, 3)
    change_sound(422, 3)

    change_sound(423, 3)
    change_sound(424, 3)

    change_sound(479, 3)
    change_sound(480, 3)

def save_project():
    # Save changes to .dat file
    DATA.save(rf'{MOD_FOLDER}\resources\_common\dat\empires2_x2_p1.dat')

    # Write changes to tech tree JSON
    json_string = '\n'.join(JSON_DATA)
    with open(CIV_TECH_TREES_FILE, 'w', encoding='utf-8') as file:
        file.write(json_string)

    # Save sounds
    with open(rf'{MOD_FOLDER}/{PROJECT_FILE}', 'r+') as project_file:
        project_lines = project_file.readlines()
        project_lines[2] = ','.join(sounds_list)
        project_file.seek(0)  # Move the file pointer to the beginning
        project_file.writelines(project_lines)  # Write the modified lines back to the file

bonus_unit_lines = {
        # Categories
        #'all units' : [-1, 0, 6, 12, 13, 18, 43, 19, 22, 2, 36, 51, 44, 54, 55, 35],
        #'military' : [-1, 0, 35, 6, 36, 47, 12, 44, 23],
        #'infantry' : [-1, 6],
        #'villager' : [-1, 4],
        #'monk' : [-1, 18, 43],
        #'cavalry' : [-1, 12, 23, 47, 36],
        #'ship' : [-1, 2, 21, 22, 20, 53],
        #'boat' : [-1, 2, 21, 22, 20, 53],
        #'stable' : [-1, 12, 47],
        #'tower' : [-1, 52],
        #'building' : [-1, 3],

        # Unit lines
        'foot archers' : [4, 24, 492, 7, 6, 1155, 185, 8, 530, 73, 559, 763, 765, 866, 868, 1129, 1131, 1800, 1802, 850, -1, 493, -1],
        'archers' : [4, 24, 492],
        'archer-line' : [4, 24, 492],
        'archer line' : [4, 24, 492],
        'skirmishers' : [7, 6, 1155],
        'skirmishers-line' : [7, 6, 1155],
        'skirmishers line' : [7, 6, 1155],
        'slingers' : [185],
        'elephant archers' : [873, 875],
        'elephant archer-line' : [873, 875],
        'elephant archer line' : [873, 875],
        'infantry' : [74, 75, 76, 473, 567, 93, 358, 359, 1786, 1787, 1788, 751, 753, 752, 1699, 1663, 1697, 184],
        'militia' : [74, 75, 76, 473, 567],
        'militia-line' : [74, 75, 76, 473, 567],
        'militia line' : [74, 75, 76, 473, 567],
        'spearmen' : [93, 358, 359, 1786, 1787, 1788],
        'spearmen-line' : [93, 358, 359, 1786, 1787, 1788],
        'spearmen line' : [93, 358, 359, 1786, 1787, 1788],
        'eagles' : [751, 753, 752],
        'eagle-line' : [751, 753, 752],
        'eagle line' : [751, 753, 752],
        'eagle units' : [751, 753, 752],
        'flemish militia' : [1699, 1663, 1697],
        'war elephants' : [239, 558],
        'war elephant-line' : [239, 558],
        'war elephant line' : [239, 558],
        'elephants' : [873, 875, 239, 558, 1120, 1122, 1132, 1134, 1744, 1746],
        'elephant units' : [873, 875, 239, 558, 1120, 1122, 1132, 1134, 1744, 1746],
        'ballista elephants' : [1120, 1122],
        'battle elephants' : [1132, 1134],
        'battle elephant-line' : [1132, 1134],
        'battle elephant line' : [1132, 1134],
        'armored elephants' : [1744, 1746],
        'armored elephant-line' : [1744, 1746],
        'armored elephant line' : [1744, 1746],
        'armoured elephants' : [1744, 1746],
        'armoured elephant-line' : [1744, 1746],
        'armoured elephant line' : [1744, 1746],
        'gunpowder units' : [5, 36, 420, 46, 691, 771, 773, 557, 1001, 1003, 831, 832, 1709, 1704, 1706],
        'hand cannoneers' : [5],
        'demolition ships' : [1104, 527, 528],
        'demolition ship-line' : [1104, 527, 528],
        'demolition ship line' : [1104, 527, 528],
        'demolition-line' : [1104, 527, 528],
        'demolition line' : [1104, 527, 528],
        'fire ships' : [1103, 529, 532],
        'fire ship line' : [1103, 529, 532],
        'fire ship-line' : [1103, 529, 532],
        'fire line' : [1103, 529, 532],
        'fire-line' : [1103, 529, 532],
        'demo-line' : [1104, 527, 528],
        'demo line' : [1104, 527, 528],
        'galley-line' : [539, 21, 442],
        'galley line' : [539, 21, 442],
        'gallies' : [539, 21, 442],
        'dromon' : [1795],
        'cannon galleons' : [420, 691],
        'cannon galleon line' : [420, 691],
        'cannon galleon-line' : [420, 691],
        'warrior priest' : [1811, 1831],
        'monk' : [1811, 1826, 1827],
        'non-unique barracks units' : [74, 75, 76, 473, 567, 93, 358, 359, 1786, 1787, 1788, 751, 753, 752],
        'scouts' : [448, 546, 441, 1707],
        'scout-line' : [448, 546, 441, 1707],
        'scout line' : [448, 546, 441, 1707],
        'rathas' : [1738, 1740, 1759, 1761],
        'trade units' : [],
        'canoes' : [],
        'canoe-line' : [],
        'canoe line' : [],
        'camels' : [282, 556, 1755, 329, 330, 207, 1007, 1009, 1263],
        'camel units' : [282, 556, 1755, 329, 330, 207, 1007, 1009, 1263],
        'villagers' : [83, 293, 590, 592, 123, 218, 122, 216, 56, 57, 120, 354, 118, 212, 156, 222, 214, 259],
        'shepherds' : [590, 592],
        'lumberjacks' : [123, 218],
        'hunters' : [122, 216],
        'fishermen' : [56, 57],
        'foragers' : [120, 354],
        'builders' : [118, 212],
        'repairers' : [156, 222],
        'farmers' : [214, 259],
        'trebuchets' : [331, 42],

        # Buildings
        'buildings' : [30, 31, 32, 104, 71, 141, 142, 481, 482, 483, 484, 597, 611, 612, 613, 614, 615, 616, 617, 82, 103, 105, 18, 19, 209, 210, 84, 116, 137, 10, 14, 87, 49, 150, 12, 20, 132, 498, 86, 101, 153, 45, 47, 51, 133, 805, 806, 807, 808, 2120, 2121, 2122, 2144, 2145, 2146, 2173, 1189, 598, 79, 234, 235, 236, 72, 789, 790, 791, 792, 793, 794, 795, 796, 797, 798, 799, 800, 801, 802, 803, 804, 117, 63, 64, 67, 78, 80, 81, 85, 88, 90, 91, 92, 95, 487, 488, 490, 491, 659, 660, 661, 662, 663, 664, 665, 666, 667, 668, 669, 670, 671, 672, 673, 674, 1192, 1251, 1665, 70, 191, 192, 463, 464, 465, 584, 585, 586, 587, 1808, 562, 563, 564, 565, 1646, 1711, 1720, 1734, 68, 129, 130, 131, 50],
        'town centers' : [71, 141, 142, 481, 482, 483, 484, 597, 611, 612, 613, 614, 615, 616, 617],
        'town centres' : [71, 141, 142, 481, 482, 483, 484, 597, 611, 612, 613, 614, 615, 616, 617],
        'castles' : [82],
        'blacksmiths' : [103, 105, 18, 19],
        'universities' : [209, 210],
        'archery ranges' : [10, 14, 87],
        'siege workshops' : [49, 150],
        'barracks' : [12, 20, 132, 498],
        'stables' : [86, 101, 153],
        'docks' : [45, 47, 51, 133, 805, 806, 807, 808, 2120, 2121, 2122, 2144, 2145, 2146, 2173, 1189],
        'outposts' : [598],
        'watch towers' : [79],
        'guard towers' : [234],
        'keeps' : [235],
        'monasteries' : [30, 31, 32, 104],
        'bombard towers' : [236],
        'towers' : [79, 234, 235, 236],
        'palisade walls' : [72, 789, 790, 791, 792, 793, 794, 795, 796, 797, 798, 799, 800, 801, 802, 803, 804], # Including gates
        'walls' : [117, 63, 64, 67, 78, 80, 81, 85, 88, 90, 91, 92, 95, 487, 488, 490, 491,659, 660, 661, 662, 663, 664, 665, 666, 667, 668, 669, 670, 671, 672, 673, 674, 1192], # Including gates
        'stone walls' : [117, 63, 64, 67, 78, 80, 81, 85, 88, 90, 91, 92, 95, 487, 488, 490, 491,659, 660, 661, 662, 663, 664, 665, 666, 667, 668, 669, 670, 671, 672, 673, 674, 1192], # Including gates
        'kreposts' : [1251],
        'donjons' : [1665],
        'houses' : [70, 191, 192, 463, 464, 465],
        'mining camps' : [584, 585, 586, 587],
        'mule carts' : [1808],
        'lumber camps' : [562, 563, 564, 565],
        'markets' : [84, 116, 137, 1646],
        'folwarks' : [1711, 1720, 1734],
        'mills' : [68, 129, 130, 131],
        'farms' : [50],
        }

bonus_technologies = {
    # Technology
    'chemistry' : [-2, 47],
    'fervor' : [-2, 252],
    'sanctity' : [-2, 231],
    'gold mining' : [-2, 55, 182],
    'stone mining' : [-2, 278, 279],
    'mining camp technologies' : [-2, 55, 182, 278, 279],
    'mining technologies' : [-2, 55, 182, 278, 279],
    'mining camp technology' : [-2, 55, 182, 278, 279],
    'mining technology' : [-2, 55, 182, 278, 279],
    'monastery technologies' : [-2, 233, 230, 46, 45, 316, 438, 319, 441, 439, 231, 252],
    'monastery technology' : [-2, 233, 230, 46, 45, 316, 438, 319, 441, 439, 231, 252],
    'gillnets' : [-2, 24],
    'economic upgrade' : [-2, 24, 24, 200, 238, 55, 182, 278, 279, 192, 196, 210, 482, 15, 14, 13, 12],
    'lumber camp technology' : [-2, 192, 196, 210],
    'lumber camp technologies' : [-2, 192, 196, 210],
    'mill technology' : [-2, 14, 13, 12],
    'mill technologies' : [-2, 14, 13, 12],
    'stable technology' : [-2, 450, 39],
    'stable technologies' : [-2, 450, 39],
}

def find_bonus_units(line):
    units = []
    for unit in bonus_unit_lines:
        # Check if unit is mentioned in "(except ...)"
        pattern = rf"\(except .*?{unit}.*?\)"
        if re.search(pattern, line, re.IGNORECASE):
            units.append(f"!{unit}")  # Add "!" before the unit name
        elif unit in line:  # Add unit normally if it's in the line
            units.append(unit)
    
    return units

def find_bonus_techs(line):
    techs = []
    for tech in bonus_technologies:
        # Check if unit is mentioned in "(except ...)"
        pattern = rf"\(except .*?{unit}.*?\)"
        if re.search(pattern, line, re.IGNORECASE):
            techs.append(f"!{tech}")  # Add "!" before the unit name
        elif tech in line:  # Add unit normally if it's in the line
            techs.append(tech)

    return techs

def create_bonus(bonus_text, civ_index):
    try:
        # Reformat sentence
        bonus_text = bonus_text.lower().strip("• ").replace(', and ', ', ')

        # Split each bonus on the line into its own bonus
        bonus_lines = bonus_text.split(';')

        # Create new tech and effect
        new_bonus_tech = DATA.techs[1101]
        new_bonus_tech.civ = civ_index + 1
        #new_bonus_tech.effect_id = len(DATA.effects) - 1
        new_bonus_effect = genieutils.effect.Effect('', [])

        # Apply the bonuses
        for bonus_line in bonus_lines:
            # Gather units and technologies
            units = find_bonus_units(bonus_line)
            techs = find_bonus_techs(bonus_line)

            # Split sentence into words
            words = bonus_line.split()

            # Find the number if it exists
            number = 'x'
            for word in words:
                word.strip('+')
                if re.search(r'\d', word):
                    number = word
                    break

            # Convert the number into a decimal
            operation = ''
            if number != 'x':
                if '%' in str(number):
                    operation = '*'
                    number = int(number.strip('%'))
                    if '-' in str(number):
                        number = (100 - (number * -1)) / 100
                    else:
                        number = 1 + (number / 100)
                else:
                    operation = '+'
                    number = int(number.strip('+').strip('('))


            # Set the resource
            resource = ''
            resource_types = ['food', 'wood', 'gold', 'stone']
            for res in resource_types:
                if res in bonus_line:
                    resource = res

            if 'cost' in bonus_line or 'costs' in bonus_line: # Change cost
                # Set the name of the bonus
                for unit in units:
                    if '!' not in unit:
                        name_unit = unit
                        break
                new_bonus_tech.name = rf'{civilisation_objects[civ_index].true_name}-Bonus: {name_unit.title()} {resource.title()} Cost'
                new_bonus_effect.name = new_bonus_tech.name

                # Convert unit names into unit indexes
                unit_indexes = []
                tech_indexes = []

                # Get existing units
                for unit in units:
                    if '!' not in unit:
                        unit_indexes.append(bonus_unit_lines[unit])

                # Remove exception units
                for unit in units:
                    if '!' in unit:
                        try:
                            unit_indexes.remove(unit)
                        except:
                            pass
                unit_indexes = unit_indexes[0]

                # Get existing techs
                '''for tech in techs:
                    if '!' not in unit:
                        tech_indexes.append(bonus_technologies[tech])

                # Remove exception units
                for tech in techs:
                    if '!' in tech:
                        tech_indexes.pop(tech)'''

                # Get the resource id for units
                resource_id = 100
                if resource == 'food':
                    resource_id = 103
                elif resource == 'wood':
                    resource_id = 104
                elif resource == 'gold':
                    resource_id = 105
                elif resource == 'stone':
                    resource_id = 106

                # Get the resource id for techs
                '''resource_id_tech = []
                if resource == 'food':
                    resource_id_tech.append(0)
                elif resource == 'wood':
                    resource_id_tech.append(1)
                elif resource == 'gold':
                    resource_id_tech.append(3)
                elif resource == 'stone':
                    resource_id_tech.append(2)
                else:
                    resource_id_tech.append(0)
                    resource_id_tech.append(1)
                    resource_id_tech.append(2)
                    resource_id_tech.append(3)'''
                
                # Starting age
                if 'starting in the feudal age' in bonus_line:
                    new_bonus_tech.required_techs = [101, -1, -1, -1, -1, -1]
                    new_bonus_tech.required_tech_count = 1
                elif 'starting in the castle age' in bonus_line:
                    new_bonus_tech.required_techs = [102, -1, -1, -1, -1, -1]
                    new_bonus_tech.required_tech_count = 1
                elif 'starting in the imperial age' in bonus_line:
                    new_bonus_tech.required_techs = [103, -1, -1, -1, -1, -1]
                    new_bonus_tech.required_tech_count = 1

                # Create an effect-command for each unit and tech
                for unit_i in unit_indexes:
                    if operation == '*':
                        new_effect_command = genieutils.effect.EffectCommand(5, unit_i, -1, resource_id, number)
                    elif operation == '+':
                        new_effect_command = genieutils.effect.EffectCommand(4, unit_i, -1, resource_id, number)
                    new_bonus_effect.effect_commands.append(new_effect_command)

                # Add the new tech and effect to the DATA file
                DATA.effects.append(new_bonus_effect)
                print(DATA.effects.index(new_bonus_effect), 0)
                new_bonus_tech.effect_id = DATA.effects.index(new_bonus_effect)
                DATA.techs.append(new_bonus_tech)
                print(rf'COST BONUS ADDED: {bonus_text}')

            elif len(units) > 0 and number != 'x': # Change unit attribute (not cost)
                # Find the attribute to be changed
                attribute = ''
                attribute_id = []
                if 'health' in bonus_line or 'hp' in bonus_line or 'hit points' in bonus_line:
                    attribute = 'hp'
                    attribute_id = [0]
                elif 'attack' in bonus_line and ('faster' in bonus_line or 'slower' in bonus_line):
                    attribute = 'reload'

                    # Invert number for attack reload
                    if isinstance(number, float):
                        number = 2 - number
                    else:
                        number *= -1

                    attribute_id = [10]
                elif 'attack' in bonus_line:
                    attribute = 'attack'
                    attribute_id = [9]
                elif 'minimum range' in bonus_line or 'min range' in bonus_line:
                    attribute = 'min range'
                    attribute_id = [20]
                elif 'speed' in bonus_line or 'move' in bonus_line or ('are' in bonus_line and 'faster' in bonus_line) or ('are' in bonus_line and 'slower' in bonus_line):
                    attribute = 'speed'
                    attribute_id = [5]
                elif 'work' in bonus_line:
                    attribute = 'work'
                    attribute_id = [13]
                elif 'line of sight' in bonus_line or 'los' in bonus_line or 'see' in bonus_line or 'sight' in bonus_line:
                    attribute = 'los'
                    attribute_id = [1]
                elif 'range' in bonus_line:
                    attribute = 'range'
                    attribute_id = [12, 1, 23]
                
                # Set the name of the bonus
                for unit in units:
                    if '!' not in unit:
                        name_unit = unit
                        break
                new_bonus_tech.name = rf'{civilisation_objects[civ_index].true_name}-Bonus: {name_unit.title()} {attribute.title()}'
                new_bonus_effect.name = new_bonus_tech.name

                # Convert unit names into unit indexes
                unit_indexes = []
                tech_indexes = []

                # Get existing units
                for unit in units:
                    if '!' not in unit:
                        unit_indexes.append(bonus_unit_lines[unit])

                # Remove exception units
                for unit in units:
                    if '!' in unit:
                        try:
                            unit_indexes.remove(unit)
                        except:
                            pass
                unit_indexes = unit_indexes[0]

                # Get existing techs
                '''for tech in techs:
                    if '!' not in unit:
                        tech_indexes.append(bonus_technologies[tech])

                # Remove exception units
                for tech in techs:
                    if '!' in tech:
                        tech_indexes.pop(tech)'''

                # Affects age
                if 'in the feudal' in bonus_line:
                    new_bonus_tech.required_techs = [101, -1, -1, -1, -1, -1]
                    new_bonus_tech.required_tech_count = 1
                elif 'in the castle' in bonus_line:
                    new_bonus_tech.required_techs = [102, -1, -1, -1, -1, -1]
                    new_bonus_tech.required_tech_count = 1
                elif 'in the imperial' in bonus_line:
                    new_bonus_tech.required_techs = [103, -1, -1, -1, -1, -1]
                    new_bonus_tech.required_tech_count = 1

                # Create an effect-command for each unit and tech
                for unit_i in unit_indexes:
                    for num in attribute_id:
                        if operation == '*':
                            new_effect_command = genieutils.effect.EffectCommand(5, unit_i, -1, num, number)
                        elif operation == '+':
                            new_effect_command = genieutils.effect.EffectCommand(4, unit_i, -1, num, number)
                        new_bonus_effect.effect_commands.append(new_effect_command)

                # Add the new tech and effect to the DATA file
                DATA.effects.append(new_bonus_effect)
                print(DATA.effects.index(new_bonus_effect), 1)
                new_bonus_tech.effect_id = DATA.effects.index(new_bonus_effect)
                DATA.techs.append(new_bonus_tech)
                print(rf'{attribute.upper()} BONUS ADDED: {bonus_text}')

    except Exception as e:
        traceback.print_exc()


    #bonus_unit_lines = ['archer', 'skirmisher', 'slinger', 'hand cannoneer', 'cavalry archer', 'elephant archer', 'genitour', 'militia', 'spearman', 'eagle', 'condottiero', 'scout', 'shrivamsha', 'knight', 'lancer', 'camel', 'battle elephant', 'elite battle elephant', 'battering ram', 'capped ram', 'siege ram', 'armored elephant', 'siege elephant', 'flaming camel', 'mangonel', 'onager', 'siege onager', 'scorpion', 'heavy scorpion', 'siege tower', 'bombard cannon', 'houfnice', 'fishing ship', 'fire galley', 'fire ship', 'fast fire ship', 'transport ship', 'trade cog', 'cannon galleon', 'elite cannon galleon', 'demolition raft', 'demolition ship', 'heavy demolition ship', 'galley', 'war galley', 'galleon', 'dromon', 'turtle ship', 'elite turtle ship', 'petard', 'trebuchet', 'unique unit', 'elite unique unit', 'konnik', 'elite konnik', 'serjeant', 'elite serjeant', 'missionary', 'monk', 'villager', 'warrior priest', 'fishing ship']

def create_units():
    # Genie elements
    AttackOrArmor = genieutils.unit.AttackOrArmor
    Bird = genieutils.unit.Bird
    Building = genieutils.unit.Building
    BuildingAnnex = genieutils.unit.BuildingAnnex
    ByteHandler = genieutils.unit.ByteHandler
    Creatable = genieutils.unit.Creatable
    DamageGraphic = genieutils.unit.DamageGraphic
    DeadFish = genieutils.unit.DeadFish
    GenieClass = genieutils.unit.GenieClass
    Projectile = genieutils.unit.Projectile
    ResourceCost = genieutils.unit.ResourceCost
    Task = genieutils.unit.Task
    ResourceStorage = genieutils.unit.ResourceStorage
    Type50 = genieutils.unit.Type50
    Unit = genieutils.unit.Unit
    UnitType = genieutils.unit.UnitType
    Version = genieutils.unit.Version

    units_to_create = [
        # Canoe
        Unit(type=70, id=1901, language_dll_name=5119, language_dll_creation=6119, class_=22, standing_graphic=(8322, -1), dying_graphic=8321, undead_graphic=-1, undead_mode=0, hit_points=70, line_of_sight=7.0, garrison_capacity=0, collision_size_x=0.5, collision_size_y=0.5, collision_size_z=2.0, train_sound=338, damage_sound=-1, dead_unit_id=-1, blood_unit_id=-1, sort_number=5, can_be_built_on=0, icon_id=164, hide_in_editor=0, old_portrait_pict=-1, enabled=0, disabled=0, placement_side_terrain=(-1, -1), placement_terrain=(-1, -1), clearance_size=(0.5, 0.5), hill_mode=0, fog_visibility=0, terrain_restriction=13, fly_mode=0, resource_capacity=200, resource_decay=10.0, blast_defense_level=3, combat_level=4, interation_mode=4, minimap_mode=1, interface_kind=4, multiple_attribute_mode=1.0, minimap_color=0, language_dll_help=105119, language_dll_hotkey_text=155119, hot_key=16106, recyclable=0, enable_auto_gather=0, create_doppelganger_on_death=0, resource_gather_group=0, occlusion_mode=1, obstruction_type=5, obstruction_class=2, trait=2, civilization=0, nothing=0, selection_effect=0, editor_selection_colour=0, outline_size_x=0.5, outline_size_y=0.5, outline_size_z=2.0, scenario_triggers_1=-2, scenario_triggers_2=0, resource_storages=(ResourceStorage(type=4, amount=-1.0, flag=2), ResourceStorage(type=11, amount=1.0, flag=2), ResourceStorage(type=19, amount=1.0, flag=1)), damage_graphics=[], selection_sound=339, dying_sound=-1, wwise_train_sound_id=1505139509, wwise_damage_sound_id=0, wwise_selection_sound_id=2092618211, wwise_dying_sound_id=0, old_attack_reaction=0, convert_terrain=0, name='Canoe', copy_id=1901, base_id=1901, speed=1.600000023841858, dead_fish=DeadFish(walking_graphic=8324, running_graphic=-1, rotation_speed=0.10000000149011612, old_size_class=0, tracking_unit=-1, tracking_unit_mode=0, tracking_unit_density=0.0, old_move_algorithm=0, turn_radius=0.0, turn_radius_speed=3.4028234663852886e+38, max_yaw_per_second_moving=3.926990032196045, stationary_yaw_revolution_time=1.600000023841858, max_yaw_per_second_stationary=3.926990032196045, min_collision_size_multiplier=1.0), bird=Bird(default_task_id=-1, search_radius=7.0, work_rate=1.0, drop_sites=[45], task_swap_group=0, attack_sound=340, move_sound=340, wwise_attack_sound_id=202111958, wwise_move_sound_id=202111958, run_pattern=0, tasks=[Task(task_type=1, id=0, is_default=0, action_type=7, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=1, combat_level_flag=1, gather_type=1, work_flag_2=0, target_diplomacy=5, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=1, is_default=0, action_type=109, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=2, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=3, is_default=0, action_type=12, class_id=-1, unit_id=-1, terrain_id=2, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0)]), type_50=Type50(base_armor=10000, attacks=[AttackOrArmor(class_=3, amount=4), AttackOrArmor(class_=16, amount=8), AttackOrArmor(class_=2, amount=4), AttackOrArmor(class_=11, amount=8), AttackOrArmor(class_=34, amount=8)], armours=[AttackOrArmor(class_=16, amount=0), AttackOrArmor(class_=4, amount=1), AttackOrArmor(class_=3, amount=2), AttackOrArmor(class_=31, amount=0)], defense_terrain_bonus=-1, bonus_damage_resistance=0.0, max_range=5.0, blast_width=0.0, reload_time=2.0, projectile_unit_id=477, accuracy_percent=100, break_off_combat=2, frame_delay=0, graphic_displacement=(0.0, 1.5, 1.399999976158142), blast_attack_level=0, min_range=0.0, accuracy_dispersion=0.0, attack_graphic=8320, displayed_melee_armour=4, displayed_attack=4, displayed_range=5.0, displayed_reload_time=2.0, blast_damage=1.0), projectile=None, creatable=Creatable(resource_costs=(ResourceCost(type=1, amount=75, flag=1), ResourceCost(type=3, amount=10, flag=1), ResourceCost(type=4, amount=1, flag=0)), train_time=20, train_location_id=45, button_id=4, rear_attack_modifier=0.0, flank_attack_modifier=1.75, creatable_type=3, hero_mode=0, garrison_graphic=-1, spawning_graphic=12262, upgrade_graphic=12263, hero_glow_graphic=12222, max_charge=0.0, recharge_rate=0.0, charge_event=0, charge_type=0, min_conversion_time_mod=0.0, max_conversion_time_mod=0.0, conversion_chance_mod=0.0, total_projectiles=2.0, max_total_projectiles=2, projectile_spawning_area=(1.0, 1.0, 1.0), secondary_projectile_unit=477, special_graphic=-1, special_ability=0, displayed_pierce_armor=4), building=None),
        
        # War Canoe
        Unit(type=70, id=1902, language_dll_name=5997, language_dll_creation=5998, class_=22, standing_graphic=(8364, -1), dying_graphic=8360, undead_graphic=-1, undead_mode=0, hit_points=80, line_of_sight=9.0, garrison_capacity=0, collision_size_x=0.5, collision_size_y=0.5, collision_size_z=2.0, train_sound=338, damage_sound=-1, dead_unit_id=-1, blood_unit_id=-1, sort_number=5, can_be_built_on=0, icon_id=178, hide_in_editor=0, old_portrait_pict=-1, enabled=0, disabled=0, placement_side_terrain=(-1, -1), placement_terrain=(-1, -1), clearance_size=(0.5, 0.5), hill_mode=0, fog_visibility=0, terrain_restriction=3, fly_mode=0, resource_capacity=2, resource_decay=1000.0, blast_defense_level=3, combat_level=4, interation_mode=4, minimap_mode=1, interface_kind=4, multiple_attribute_mode=1.0, minimap_color=0, language_dll_help=105741, language_dll_hotkey_text=155119, hot_key=16106, recyclable=0, enable_auto_gather=0, create_doppelganger_on_death=0, resource_gather_group=0, occlusion_mode=1, obstruction_type=5, obstruction_class=2, trait=2, civilization=0, nothing=0, selection_effect=0, editor_selection_colour=0, outline_size_x=0.5, outline_size_y=0.5, outline_size_z=2.0, scenario_triggers_1=-2, scenario_triggers_2=0, resource_storages=(ResourceStorage(type=4, amount=-1.0, flag=2), ResourceStorage(type=11, amount=1.0, flag=2), ResourceStorage(type=19, amount=1.0, flag=1)), damage_graphics=[], selection_sound=339, dying_sound=-1, wwise_train_sound_id=1505139509, wwise_damage_sound_id=0, wwise_selection_sound_id=2092618211, wwise_dying_sound_id=0, old_attack_reaction=0, convert_terrain=0, name='War Canoe', copy_id=1902, base_id=1902, speed=1.649999976158142, dead_fish=DeadFish(walking_graphic=8365, running_graphic=-1, rotation_speed=0.10000000149011612, old_size_class=0, tracking_unit=-1, tracking_unit_mode=0, tracking_unit_density=0.0, old_move_algorithm=0, turn_radius=0.0, turn_radius_speed=3.4028234663852886e+38, max_yaw_per_second_moving=3.9269909858703613, stationary_yaw_revolution_time=1.600000023841858, max_yaw_per_second_stationary=3.9269909858703613, min_collision_size_multiplier=1.0), bird=Bird(default_task_id=-1, search_radius=9.0, work_rate=1.0, drop_sites=[], task_swap_group=0, attack_sound=340, move_sound=340, wwise_attack_sound_id=202111958, wwise_move_sound_id=202111958, run_pattern=0, tasks=[Task(task_type=1, id=0, is_default=0, action_type=7, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=1, combat_level_flag=1, gather_type=1, work_flag_2=0, target_diplomacy=5, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=1, is_default=0, action_type=109, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=2, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0)]), type_50=Type50(base_armor=10000, attacks=[AttackOrArmor(class_=3, amount=6), AttackOrArmor(class_=16, amount=10), AttackOrArmor(class_=2, amount=4), AttackOrArmor(class_=11, amount=10), AttackOrArmor(class_=34, amount=9)], armours=[AttackOrArmor(class_=16, amount=0), AttackOrArmor(class_=4, amount=2), AttackOrArmor(class_=3, amount=4), AttackOrArmor(class_=31, amount=0)], defense_terrain_bonus=-1, bonus_damage_resistance=0.0, max_range=7.0, blast_width=0.0, reload_time=2.0, projectile_unit_id=477, accuracy_percent=100, break_off_combat=2, frame_delay=0, graphic_displacement=(0.0, 1.5, 1.399999976158142), blast_attack_level=0, min_range=0.0, accuracy_dispersion=0.0, attack_graphic=8363, displayed_melee_armour=4, displayed_attack=6, displayed_range=7.0, displayed_reload_time=2.0, blast_damage=1.0), projectile=None, creatable=Creatable(resource_costs=(ResourceCost(type=1, amount=75, flag=1), ResourceCost(type=3, amount=10, flag=1), ResourceCost(type=4, amount=1, flag=0)), train_time=20, train_location_id=45, button_id=4, rear_attack_modifier=0.0, flank_attack_modifier=1.75, creatable_type=3, hero_mode=0, garrison_graphic=-1, spawning_graphic=12262, upgrade_graphic=12263, hero_glow_graphic=12221, max_charge=0.0, recharge_rate=0.0, charge_event=0, charge_type=0, min_conversion_time_mod=0.0, max_conversion_time_mod=0.0, conversion_chance_mod=0.0, total_projectiles=2.0, max_total_projectiles=2, projectile_spawning_area=(1.0, 1.0, 1.0), secondary_projectile_unit=477, special_graphic=-1, special_ability=0, displayed_pierce_armor=4), building=None),
    
        # Elite War Canoe
        Unit(type=70, id=1903, language_dll_name=5999, language_dll_creation=6000, class_=22, standing_graphic=(8364, -1), dying_graphic=8360, undead_graphic=-1, undead_mode=0, hit_points=90, line_of_sight=11.0, garrison_capacity=0, collision_size_x=0.5, collision_size_y=0.5, collision_size_z=2.0, train_sound=338, damage_sound=-1, dead_unit_id=-1, blood_unit_id=-1, sort_number=5, can_be_built_on=0, icon_id=178, hide_in_editor=0, old_portrait_pict=-1, enabled=0, disabled=0, placement_side_terrain=(-1, -1), placement_terrain=(-1, -1), clearance_size=(0.5, 0.5), hill_mode=0, fog_visibility=0, terrain_restriction=3, fly_mode=0, resource_capacity=2, resource_decay=1000.0, blast_defense_level=3, combat_level=4, interation_mode=4, minimap_mode=1, interface_kind=4, multiple_attribute_mode=1.0, minimap_color=0, language_dll_help=105742, language_dll_hotkey_text=155119, hot_key=16106, recyclable=0, enable_auto_gather=0, create_doppelganger_on_death=0, resource_gather_group=0, occlusion_mode=1, obstruction_type=5, obstruction_class=2, trait=2, civilization=0, nothing=0, selection_effect=0, editor_selection_colour=0, outline_size_x=0.5, outline_size_y=0.5, outline_size_z=2.0, scenario_triggers_1=-2, scenario_triggers_2=0, resource_storages=(ResourceStorage(type=4, amount=-1.0, flag=2), ResourceStorage(type=11, amount=1.0, flag=2), ResourceStorage(type=19, amount=1.0, flag=1)), damage_graphics=[], selection_sound=339, dying_sound=-1, wwise_train_sound_id=1505139509, wwise_damage_sound_id=0, wwise_selection_sound_id=2092618211, wwise_dying_sound_id=0, old_attack_reaction=0, convert_terrain=0, name='Elite War Canoe', copy_id=1903, base_id=1903, speed=1.7000000476837158, dead_fish=DeadFish(walking_graphic=8365, running_graphic=-1, rotation_speed=0.10000000149011612, old_size_class=0, tracking_unit=-1, tracking_unit_mode=0, tracking_unit_density=0.0, old_move_algorithm=0, turn_radius=0.0, turn_radius_speed=3.4028234663852886e+38, max_yaw_per_second_moving=3.9269909858703613, stationary_yaw_revolution_time=1.600000023841858, max_yaw_per_second_stationary=3.9269909858703613, min_collision_size_multiplier=1.0), bird=Bird(default_task_id=-1, search_radius=11.0, work_rate=1.0, drop_sites=[], task_swap_group=0, attack_sound=340, move_sound=340, wwise_attack_sound_id=202111958, wwise_move_sound_id=202111958, run_pattern=0, tasks=[Task(task_type=1, id=0, is_default=0, action_type=7, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=1, combat_level_flag=1, gather_type=1, work_flag_2=0, target_diplomacy=5, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=1, is_default=0, action_type=109, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=2, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0)]), type_50=Type50(base_armor=10000, attacks=[AttackOrArmor(class_=3, amount=8), AttackOrArmor(class_=16, amount=12), AttackOrArmor(class_=2, amount=4), AttackOrArmor(class_=11, amount=12), AttackOrArmor(class_=34, amount=10)], armours=[AttackOrArmor(class_=16, amount=0), AttackOrArmor(class_=4, amount=3), AttackOrArmor(class_=3, amount=4), AttackOrArmor(class_=31, amount=0)], defense_terrain_bonus=-1, bonus_damage_resistance=0.0, max_range=9.0, blast_width=0.0, reload_time=2.0, projectile_unit_id=477, accuracy_percent=100, break_off_combat=2, frame_delay=0, graphic_displacement=(0.0, 1.5, 1.399999976158142), blast_attack_level=0, min_range=0.0, accuracy_dispersion=0.0, attack_graphic=8363, displayed_melee_armour=4, displayed_attack=8, displayed_range=9.0, displayed_reload_time=2.0, blast_damage=1.0), projectile=None, creatable=Creatable(resource_costs=(ResourceCost(type=1, amount=75, flag=1), ResourceCost(type=3, amount=10, flag=1), ResourceCost(type=4, amount=1, flag=0)), train_time=20, train_location_id=45, button_id=4, rear_attack_modifier=0.0, flank_attack_modifier=0.0, creatable_type=0, hero_mode=0, garrison_graphic=-1, spawning_graphic=12262, upgrade_graphic=12263, hero_glow_graphic=12221, max_charge=0.0, recharge_rate=0.0, charge_event=0, charge_type=0, min_conversion_time_mod=0.0, max_conversion_time_mod=0.0, conversion_chance_mod=0.0, total_projectiles=3.0, max_total_projectiles=3, projectile_spawning_area=(1.0, 1.0, 1.0), secondary_projectile_unit=477, special_graphic=-1, special_ability=0, displayed_pierce_armor=4), building=None),
    ]

    # Add the units to the DATA file
    for unit in units_to_create:
        for i in range(len(civilisation_objects) + 1):
            try:
                DATA.civs[i].units.append(unit)
            except:
                pass

class PixmapLabel(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap_path = None  # To store the pixmap path

    def setPixmap(self, pixmap, pixmap_path=None):
        super().setPixmap(pixmap)
        self._pixmap_path = pixmap_path  # Store the path

    def getPixmapPath(self):
        return self._pixmap_path  # Return the stored path

# Unit blocks
unit_blocks = []
scout_unit_blocks = []
class UnitBlock():
    def __init__(self, index, name, type, unit_code, enabled):
        self.index = index
        self.name = name
        self.unit_code = unit_code
        self.enabled = enabled
        self.type = type
        file_name = self.name.replace(' ', '_').replace('-', '0')

        parent_widget = getattr(MAIN_WINDOW, f"{file_name}")
        self.disable_label = QtWidgets.QLabel(parent_widget)
        self.disable_label.setGeometry(0, 0, 75, 75)
        self.disable_label.setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/disabled_2.png"))
        self.disable_label.setObjectName(f"{file_name}_6")
        self.opacity_effect = QtWidgets.QGraphicsOpacityEffect()
        self.opacity_effect.setOpacity(0)  # Initially set to 0 (enabled)
        self.disable_label.setGraphicsEffect(self.opacity_effect)
        self.disable_label.show()
        self.disable_label.setScaledContents(True)

        self.hierarchies = [
            [16, 0, 1, 2],
            [16, 3, 4, 5],
            [16, 6],
            [16, 7],
            [16, 8, 9],
            [16, 10, 11],
            [16, 12, 13],
            [16, 14],
            [16, 15],
            [27, 17, 18, 19, 20, 21],
            [27, 22, 23],
            [27, 24, 25, 26],
            [27, 28, 29, 30],
            [27, 31],
            [27, 32],
            [27, 33],
            [45, 34, 35, 36],
            [45, 37],
            [45, 38, 39],
            [45, 40, 41, 42],
            [45, 43, 44],
            [45, 46],
            [45, 47, 48, 49],
            [45, 50, 51],
            [45, 52],
            [59, 53, 54, 55],
            [59, 56, 57],
            [59, 58],
            [59, 60, 61, 62],
            [59, 63, 64],
            [59, 65],
            [59, 66, 67],
            [74, 68, 69, 70],
            [74, 71, 72, 73],
            [74, 75, 76, 77],
            [74, 78, 79, 80],
            [74, 81, 82, 83],
            [100, 84],
            [100, 85, 86, 87],
            [100, 88],
            [100, 89],
            [100, 90],
            [100, 91, 92],
            [100, 93, 94, 95],
            [100, 96, 97, 98],
            [100, 99],
            [100, 101, 102],
            [100, 103, 104],
            [100, 105],
            [100, 106],
            [114, 107, 108],
            [114, 109],
            [114, 110, 111],
            [114, 112],
            [114, 113],
            [114, 115, 116],
            [114, 117],
            [114, 118],
            [114, 119],
            [114, 120],
            [137, 131, 132],
            [137, 133],
            [137, 134],
            [137, 135, 136],
            [137, 138],
            [137, 139],
            [137, 140],
            [137, 141],
            [142, 143, 144],
            [145, 146, 147],
            [156, 148],
            [156, 149],
            [156, 150],
            [156, 151],
            [156, 152, 153],
            [156, 154],
            [156, 155],
            [156, 157],
            [156, 158],
            [156, 159],
            [156, 160],
            [156, 161],
            [162, 163],
            [168, 165],
            [168, 166, 167],
            [168, 169, 170, 171],
            [168, 172],
            [168, 173, 174],
            [188, 189],
            [188, 190, 191],
            [188, 192],
            [188, 193],
            [122, 123, 124],
            [129, 130],
            [179, 180],
            [181, 182],
            [185, 186, 187],
            [197, 198, 199]
        ]

        self.equals = [(24, 148), (25, 149), (26, 150), (111, 125), (109, 130), (115, 123), (116, 124)]
        self.opposites = [(6, 7), (8, 10), (9, 10), (10, 8), (11, 8), (53, 56), (54, 56), (55, 56), (56, 53), (57, 53), (186, 181), (186, 187), (199, 197)]

    def enable_disable(self, status, setup, first):
        # Set the visuals
        self.enabled = status
        if status:
            self.opacity_effect.setOpacity(0)
        else:
            self.opacity_effect.setOpacity(0.75)
        self.disable_label.setGraphicsEffect(self.opacity_effect)

        if not setup:
            # Change scout unit
            if scout_unit_blocks[2].enabled:
                DATA.civs[CURRENT_CIV_INDEX + 1].resources[263] = 1755 # Camel Scout
            elif scout_unit_blocks[1].enabled:
                DATA.civs[CURRENT_CIV_INDEX + 1].resources[263] = 448 # Scout Cavalry
            elif scout_unit_blocks[0].enabled:
                DATA.civs[CURRENT_CIV_INDEX + 1].resources[263] = 751 # Eagle Scout
            else:
                DATA.civs[CURRENT_CIV_INDEX + 1].resources[263] = 448 # Default Scout

            # Change units dictionary
            if status:
                civilisation_objects[CURRENT_CIV_INDEX].units[self.name] = 1
            else:
                civilisation_objects[CURRENT_CIV_INDEX].units[self.name] = 2

            # Change data
            tech_tree_techs = [254, 258, 259, 262, 255, 257, 256, 260, 261, 263, 276, 277, 275, 446, 447, 449, 448, 504, 10, 1, 3, 5, 7, 31, 48, 42, 37, 646, 648, 650, 652, 706, 708, 710, 712, 782, 784, 801, 803, 838, 840, 842, 890, 925, 927]
            if status:
                for i, effect_command in enumerate(DATA.effects[tech_tree_techs[CURRENT_CIV_INDEX]].effect_commands):
                    if effect_command.type == 102 and effect_command.d == self.unit_code:
                        DATA.effects[tech_tree_techs[CURRENT_CIV_INDEX]].effect_commands.pop(i)
            else:
                DATA.effects[tech_tree_techs[CURRENT_CIV_INDEX]].effect_commands.append(genieutils.effect.EffectCommand(102, 0, 0, 0, self.unit_code))

            # Change the JSON
            for i, line in enumerate(JSON_DATA):
                if civilisation_objects[CURRENT_CIV_INDEX].true_name.upper() in line:
                    # Start searching from this point onward for the unit
                    for i2, line in enumerate(JSON_DATA[i:]):
                        if self.name in line:
                            # Start searching from this point onward for "Node Status"
                            for i3, line in enumerate(JSON_DATA[i + i2:]):
                                if 'Node Status' in line:
                                    # Update the line based on self.enabled
                                    if self.enabled:
                                        JSON_DATA[i + i2 + i3] = '          "Node Status": "ResearchedCompleted",'
                                    else:
                                        JSON_DATA[i + i2 + i3] = '          "Node Status": "NotAvailable",'
                                    break
                            break
                    break

            if not first:
                return

            # Opposite blocks
            for opposite in self.opposites:
                if self.index in opposite and self.enabled:
                    for pair in opposite:
                        if pair != self.index:
                            unit_blocks[pair].enable_disable(False, False, True)

            # Equal blocks
            for equal in self.equals:
                if self.index in equal:
                    for pair in equal:
                        unit_blocks[pair].enable_disable(status, False, False)

            # Enable/disable connected blocks
            try:
                for hierarchy in self.hierarchies:
                    if self.index in hierarchy:
                        if not status:
                            hierarchy.reverse()
                        for unit_index in hierarchy:
                            if unit_index != self.index:
                                unit_blocks[unit_index].enable_disable(status, False, False)
                            else:
                                if not status:
                                    hierarchy.reverse()
                                break
            except:
                pass

    def on_button_clicked(self):
        self.enable_disable(not self.enabled, False, True)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    CreateProjectWindow = QtWidgets.QDialog()
    SavingWindow = QtWidgets.QDialog()

    # Initialize UI components
    MAIN_WINDOW = Ui_MainWindow()
    MAIN_WINDOW.setupUi(MainWindow)

    CREATE_WINDOW = Ui_CreateProjectWindow()
    CREATE_WINDOW.setupUi(CreateProjectWindow)

    SAVING_WINDOW = Ui_Dialog()
    SAVING_WINDOW.setupUi(SavingWindow)

    # Set application images
    MAIN_WINDOW.label.setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/dark_age.png"))
    MAIN_WINDOW.label_2.setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/feudal_age.png"))
    MAIN_WINDOW.label_3.setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/castle_age.png"))
    MAIN_WINDOW.label_4.setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/imperial_age.png"))

    # Setup objects
    unit_codes = [
        151, # Archer
        100, # Crossbowman
        237, # Arbalester
        99, # Skirmisher
        98, # Elite Skirmisher
        655, # Imperial Skirmisher
        987, # Slinger
        85, # Hand Cannoneer 
        192, # Cavalry Archer
        218, # Heavy Cavalry Archer
        480, # Elephant Archer
        481, # Elite Elephant Archer
        427, # Genitour
        430, # Elite Genitour
        437, # Thumb Ring
        436, # Parthian Tactics
        -1, # Archery Range
        -1, # Militia
        222, # Man-at-Arms
        207, # Long Swordsman 
        217, # Two-Handed Swordsman
        264, # Champion
        716, # Supplies
        875, # Gambesons
        87, # Spearman 
        197, # Pikeman
        429, # Halberdier
        -1, # Barracks
        433, # Eagle Scout
        384, # Eagle Warrior
        434, # Elite Eagle Warrior
        215, # Squires
        522, # Condottiero 
        602, # Arson
        204, # Scout Cavalry
        254, # Light Cavalry
        428, # Hussar
        435, # Bloodlines
        842, # Shrivamsha Rider 
        843, # Elite Shrivamsha Rider 
        166, # Knight
        209, # Cavalier
        265, # Paladin
        714, # Steppe Lancer
        715, # Elite Steppe Lancer
        25, # Stable
        858, # Camel Scout
        235, # Camel Rider
        236, # Heavy Camel Rider
        521, # Imperial Camel Rider
        630, # Battle Elephant
        631, # Elite Battle Elephant
        39, # Husbandry
        162, # Battering Ram
        96, # Capped Ram
        255, # Siege Ram
        837, # Armored Elephant
        838, # Siege Elephant
        703, # Flaming Camel
        150, # Siege Workshop
        358, # Mangonel
        257, # Onager
        320, # Siege Onager
        94, # Scorpion
        239, # Heavy Scorpion
        603, # Siege Tower
        172, # Bombard Cannon
        787, # Houfnice
        211, # Padded Archer Armor
        212, # Leather Archer Armor
        219, # Ring Archer Armor
        199, # Fletching
        200, # Bodkin Arrow
        201, # Bracer
        -1, # Blacksmith
        67, # Forging
        68, # Iron Casting
        75, # Blast Furnace
        81, # Scale Barding Armor
        82, # Chain Barding Armor
        80, # Plate Barding Armor
        74, # Scale Mail Armor
        76, # Chain Mail Armor
        77, # Plate Mail Armor
        112, # Fishing Ship
        604, # Fire Galley
        243, # Fire Ship
        246, # Fast Fire Ship
        -1, # Transport Ship
        -1, # Trade Cog
        65, # Gillnets
        37, # Cannon Galleon
        376, # Elite Cannon Galleon
        605, # Demolition Raft
        -1, # Demolition Ship
        233, # Heavy Demolition Ship
        240, # Galley
        34, # War Galley
        35, # Galleon
        886, # Dromon
        -1, # Dock
        447, # Turtle Ship
        448, # Elite Turtle Ship
        374, # Careening
        375, # Dry Dock
        373, # Shipwright
        357, # Fish Trap
        50, # Masonry
        51, # Architecture
        194, # Fortified Wall
        47, # Chemistry
        64, # Bombard Tower
        93, # Ballistics
        377, # Siege Engineers
        -1, # University
        140, # Guard Tower
        63, # Keep
        380, # Heated Shot
        608, # Arrowslits
        322, # Murder Holes
        54, # Treadmill Crane
        332, # Outpost 
        127, # Watch Tower
        140, # Guard Tower
        63, # Keep
        64, # Bombard Tower
        523, # Palisade Walls
        -1, # Palisade Gate
        -1, # Gate
        189, # Stone Wall
        194, # Fortified Wall
        -1, # Unique UnitX
        -1, # Elite Unique UnitX
        426, # Petard
        256, # Trebuchet (Packed)
        -1, # Castle TechR
        -1, # Imperial TechR
        -1, # Castle
        379, # Hoardings
        321, # Sappers
        315, # Conscription
        408, # Spies/Treason
        -1, # Krepost
        -1, # KonnikX
        -1, # Elite KonnikX
        -1, # Donjon
        -1, # SerjeantX
        -1, # Elite SerjeantX
        157, # Monk
        233, # Illumination
        84, # Missionary
        230, # Block Printing
        46, # Devotion
        45, # Faith
        316, # Redemption
        438, # Theocracy
        -1, # Monastery
        319, # Atonement
        441, # Herbal Medicine
        439, # Heresy
        231, # Sanctity
        252, # Fervor
        929, # Fortified Church
        948, # Warrior Priest
        -1, # House
        116, # Villager
        8, # Town Watch
        280, # Town Patrol
        -1, # Town Center
        101, # Feudal Age
        102, # Castle Age
        103, # Imperial Age
        22, # Loom
        213, # Wheelbarrow
        249, # Hand Cart
        -1, # Wonder
        570, # Feitoria
        518, # Caravanserai
        552, # Caravanserai
        -1, # Mining Camp
        55, # Gold Mining
        182, # Gold Shaft Mining
        278, # Stone Mining
        279, # Stone Shaft Mining
        932, # Mule Cart
        -1, # Lumber Camp
        202, # Double-Bit Axe
        203, # Bow Saw
        221, # Two-Man Saw
        1646, # Market
        161, # Trade Cart
        23, # Coinage
        17, # Banking
        48, # Caravan
        15, # Guilds
        -1, # Folwark
        216, # Farm
        -1, # Mill
        14, # Horse Collar
        13, # Heavy Plow
        12, # Crop Rotation
    ]

    block_index = 0
    for unit in ['ArcherU', 'CrossbowmanU', 'ArbalesterU', 'SkirmisherU', 'Elite SkirmisherU', 'Imperial SkirmisherX', 'SlingerX', 'Hand CannoneerU', 'Cavalry ArcherU', 'Heavy Cavalry ArcherU', 'Elephant ArcherU', 'Elite Elephant ArcherU', 'GenitourX', 'Elite GenitourX', 'Thumb RingR', 'Parthian TacticsR', 'Archery RangeB', 'MilitiaU', 'Man-at-ArmsU', 'Long SwordsmanU', 'Two-Handed SwordsmanU', 'ChampionU', 'SuppliesR', 'GambesonsR', 'SpearmanU', 'PikemanU', 'HalberdierU', 'BarracksB', 'Eagle ScoutU', 'Eagle WarriorU', 'Elite Eagle WarriorU', 'SquiresR', 'CondottieroX', 'ArsonR', 'Scout CavalryU', 'Light CavalryU', 'HussarU', 'BloodlinesR', 'Shrivamsha RiderX', 'Elite Shrivamsha RiderX', 'KnightU', 'CavalierU', 'PaladinU', 'Steppe LancerU', 'Elite Steppe LancerU', 'StableB', 'Camel ScoutX', 'Camel RiderU', 'Heavy Camel RiderU', 'Imperial Camel RiderX', 'Battle ElephantU', 'Elite Battle ElephantU', 'HusbandryR', 'Battering RamU', 'Capped RamU', 'Siege RamU', 'Armored ElephantU', 'Siege ElephantU', 'Flaming CamelX', 'Siege WorkshopB', 'MangonelU', 'OnagerU', 'Siege OnagerU', 'ScorpionU', 'Heavy ScorpionU', 'Siege TowerU', 'Bombard CannonU', 'HoufniceX', 'Padded Archer ArmorR', 'Leather Archer ArmorR', 'Ring Archer ArmorR', 'FletchingR', 'Bodkin ArrowR', 'BracerR', 'BlacksmithB', 'ForgingR', 'Iron CastingR', 'Blast FurnaceR', 'Scale Barding ArmorR', 'Chain Barding ArmorR', 'Plate Barding ArmorR', 'Scale Mail ArmorR', 'Chain Mail ArmorR', 'Plate Mail ArmorR', 'Fishing ShipU', 'Fire GalleyU', 'Fire ShipU', 'Fast Fire ShipU', 'Transport ShipU', 'Trade CogU', 'GillnetsR', 'Cannon GalleonU', 'Elite Cannon GalleonU', 'Demolition RaftU', 'Demolition ShipU', 'Heavy Demolition ShipU', 'GalleyU', 'War GalleyU', 'GalleonU', 'DromonU', 'DockB', 'Turtle ShipU', 'Elite Turtle ShipU', 'CareeningR', 'Dry DockR', 'ShipwrightR', 'Fish TrapB', 'MasonryR', 'ArchitectureR', 'Fortified WallR', 'ChemistryR', 'Bombard TowerR', 'BallisticsR', 'Siege EngineersR', 'UniversityB', 'Guard TowerR', 'KeepR', 'Heated ShotR', 'ArrowslitsR', 'Murder HolesR', 'Treadmill CraneR', 'OutpostB', 'Watch TowerB', 'Guard TowerBB', 'KeepBB', 'Bombard TowerBB', 'Palisade WallB', 'Palisade GateB', 'GateB', 'Stone WallB', 'Fortified WallBB', 'Unique UnitX', 'Elite Unique UnitX', 'PetardU', 'TrebuchetU', 'Castle TechR', 'Imperial TechR', 'CastleB', 'HoardingsR', 'SappersR', 'ConscriptionR', 'SpiesR', 'KrepostB', 'KonnikX', 'Elite KonnikX', 'DonjonB', 'SerjeantX', 'Elite SerjeantX', 'MonkU', 'IlluminationR', 'MissionaryX', 'Block PrintingR', 'DevotionR', 'FaithR', 'RedemptionR', 'TheocracyR', 'MonasteryB', 'AtonementR', 'Herbal MedicineR', 'HeresyR', 'SanctityR', 'FervorR', 'Fortified ChurchB', 'Warrior PriestX', 'HouseB', 'VillagerU', 'Town WatchR', 'Town PatrolR', 'Town CenterB', 'Feudal AgeR', 'Castle AgeR', 'Imperial AgeR', 'LoomR', 'WheelbarrowR', 'Hand CartR', 'WonderB', 'FeitoriaB', 'CaravanseraiB', 'Mining CampB', 'Gold MiningR', 'Gold Shaft MiningR', 'Stone MiningR', 'Stone Shaft MiningR', 'Mule CartB', 'Lumber CampB', 'Double-Bit AxeR', 'Bow SawR', 'Two-Man SawR', 'MarketB', 'Trade CartU', 'CoinageR', 'BankingR', 'CaravanR', 'GuildsR', 'FolwarkB', 'FarmB', 'MillB', 'Horse CollarR', 'Heavy PlowR', 'Crop RotationR']:
        try:
            # Check the pixmap path and determine type
            if unit[-1] == 'U':
                type = 'unit'
            elif unit[-1] == 'B':
                type = 'building'
            elif unit[-1] == 'R':
                type = 'research'
            elif unit[-1] == 'X':
                type = 'unique'

            # Format the new name
            if unit[-2] == 'X':
                unit_name = unit[:-2]
            else:
                unit_name = unit[:-1]
            file_name = unit[:-1].replace(' ', '_').replace('-', '0')

            # Dynamically get the PixmapLabel for the icon and background based on the unit name
            bg_label = getattr(MAIN_WINDOW, f"{file_name}_2")
            icon_label = getattr(MAIN_WINDOW, f"{file_name}_3")
            text_label = getattr(MAIN_WINDOW, f"{file_name}_4")
            push_button = getattr(MAIN_WINDOW, f"{file_name}_5")

            # Set the pixmaps dynamically, storing the paths
            icon_label.setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/{unit_name}.png"))

            # Set the background pixmap based on type
            bg_label.setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/{type}.png"))

            # Add disable image
            parent_widget = getattr(MAIN_WINDOW, f"{file_name}")
            disable_label = QtWidgets.QLabel(parent_widget)
            disable_label.setGeometry(0, 0, 75, 75)
            disable_label.setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/disabled.png"))
            disable_label.setObjectName(f"{file_name}_5")
            opacity_effect = QtWidgets.QGraphicsOpacityEffect()
            opacity_effect.setOpacity(0)
            disable_label.setGraphicsEffect(opacity_effect)
            disable_label.show()
            disable_label.setScaledContents(True)

            # Add new block to the list
            new_block = UnitBlock(block_index, unit_name, type, unit_codes[block_index], True)
            unit_blocks.append(new_block)
            if new_block.name == 'Scout Cavalry' or new_block.name == 'Camel Scout' or new_block.name == 'Eagle Scout':
                scout_unit_blocks.append(new_block)
            block_index += 1

            # Connect the button click to a function
            push_button.setStyleSheet("background-color: transparent; border: none;")
            push_button.raise_()
            push_button.clicked.connect(new_block.on_button_clicked)
        
        except Exception as e:
            print(rf'Failed Block: {unit} : {str(e)}')

    # Show the main window
    MainWindow.setWindowTitle(f"Talofa")
    MainWindow.setWindowIcon(QtGui.QIcon(rf"{os.path.dirname(os.path.abspath(__file__))}\Images\UI\flower.ico"))
    MainWindow.showMaximized()

    # Assign functions to navigation buttons
    MAIN_WINDOW.actionNew_Project.triggered.connect(new_project)
    MAIN_WINDOW.actionOpen_Project.triggered.connect(open_project)
    MAIN_WINDOW.actionSave_Project.triggered.connect(save_project)
    MAIN_WINDOW.actionRevert_To_Original.triggered.connect(revert_project)

# Update the stats when the civilisation dropdown is changed
MAIN_WINDOW.civilisation_dropdown.currentIndexChanged.connect(update_civilisation_dropdown)
MAIN_WINDOW.architecture_dropdown.currentIndexChanged.connect(update_architecture_dropdown)
MAIN_WINDOW.language_dropdown.currentIndexChanged.connect(update_language_dropdown)

# DEBUG: Open new project when the program opens
open_project(r'C:\Users\Micheal Q\Games\Age of Empires 2 DE\76561198021486964\mods\local\15eFq\15eFq.txt')

# Read description for bonuses
#description_lines = MAIN_WINDOW.description.toPlainText().split('\n')
#for i, line in enumerate(description_lines):
#    if '•' in line or i == len(description_lines) - 1:
#        create_bonus(line, CURRENT_CIV_INDEX)

# Create new units
#create_units()

sys.exit(app.exec_())  # Run the application's event loop