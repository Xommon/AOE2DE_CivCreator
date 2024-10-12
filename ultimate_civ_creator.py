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

# Constants
civilisation_objects = []
tech_tree_blocks = []
ORIGINAL_FOLDER = ''
MOD_FOLDER = ''
DATA = ''
DATA_FILE_DAT = ''
unique_unit = ''

# Tech tree blocks
'''class TechTreeBlock:
    def __init__(self, name: str, type: str, icon: str):
        self.name = name
        self.type = type
        self.icon = icon'''

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

        #self.MAIN_WINDOW.civilisation_dropdown.addItems(["Britons", "Franks", "Teutons"])  # Example items, can be populated dynamically

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
        print("You clicked OK!")

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
            ORIGINAL_FOLDER = original_folder_location
            MOD_FOLDER = os.path.join(mod_folder_location, project_name)
            os.makedirs(MOD_FOLDER, exist_ok=True)
            os.chdir(MOD_FOLDER)

            # Write the project file
            with open(f'{project_name}.txt', 'w') as file:
                file.write(rf"{original_folder_location}\n{mod_folder_location}\{project_name}")

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
    global ORIGINAL_FOLDER, MOD_FOLDER

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
        CIV_TECH_TREES_FILE = rf'{MOD_FOLDER}\resources\_common\dat\civTechTrees.json'
        CIV_IMAGE_FOLDER = rf'{MOD_FOLDER}\widgetui\textures\menu\civs'
        DATA = DatFile.parse(DATA_FILE_DAT)

        # Test change
        #DATA.techs[22].resource_costs[0].amount = 69
        '''DATA.civs[1].units[12].disabled = 1
        DATA.civs[1].units[12].enabled = 0
        DATA.civs[1].units[20].disabled = 1
        DATA.civs[1].units[20].enabled = 0
        DATA.civs[1].units[132].disabled = 1
        DATA.civs[1].units[132].enabled = 0
        DATA.civs[1].units[498].disabled = 1
        DATA.civs[1].units[12].enabled = 0
        
        DATA.save(DATA_FILE_DAT)'''

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
                #update_civilisation_dropdown()
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

        # Test
        #for civ in civilisation_objects:
            #print(rf'{civ.name}: {DATA.civs[civ.index]['architecture']}')
            
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
            new_description = civ.description[1:-1].replace('\\n', '\n').replace('<b>', '')
            MAIN_WINDOW.civilisation_description_label.setText(new_description)
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
            job_description = "Castle_Tech_4 will be replaced with Castle Tech and Imperial_Tech_4 will be replaced with Imperial Tech."

            # Step 1: Extract the unique techs using regex
            

            # Update the tech tree
            for block in unit_blocks:
                if block.name != 'Unique Unit' and block.name != 'Elite Unique Unit' and block.name != 'Castle Tech' and block.name != 'Imperial Tech' and block.name != 'Trebuchet' and block.name != 'Spies':
                    block.disable()
                else:
                    block.enable()

                try:
                    if civ.units[block.name] == 1 or civ.units[block.name] == 3:
                        block.enable()
                except:
                    continue
                
            for key, value in civ.units.items():
                for block in unit_blocks:
                    if block.name == key:
                        if value == 1 or value == 3:
                            block.enable()
                            break

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
    DATA.save(DATA_FILE_DAT)
    print("saving")

'''class Unit_Square(QtWidgets.QWidget):  # Inherit from QWidget to add it to a layout
    def __init__(self, name: str, type: str, coordinates: [], enabled: bool = True):
        super().__init__()
        self.name = name
        self.type = type
        self.coordinates = coordinates
        self.enabled = enabled

        # Create background image
        self.background = QtWidgets.QLabel(self)
        self.background.setEnabled(self.enabled)
        self.background.setGeometry(QtCore.QRect(0, 0, 75, 75))
        self.background.setMinimumSize(QtCore.QSize(75, 75))
        self.background.setMaximumSize(QtCore.QSize(75, 75))
        self.background.setAutoFillBackground(False)
        self.background.setText("")
        self.background.setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/{name.capitalize()}.png"))
        self.background.setScaledContents(True)
        self.background.setObjectName(rf"background_{name.lower()}")

        # Create icon
        self.icon = QtWidgets.QLabel(self)
        self.icon.setEnabled(self.enabled)
        self.icon.setGeometry(QtCore.QRect(20, 10, 35, 35))
        self.icon.setMinimumSize(QtCore.QSize(35, 35))
        self.icon.setMaximumSize(QtCore.QSize(35, 33))
        self.icon.setText("")
        self.icon.setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/{name.capitalize()}.png"))
        self.icon.setScaledContents(True)
        self.icon.setObjectName(rf"icon_{name.lower()}")

        # Create text
        self.text = QtWidgets.QLabel(self)
        self.text.setEnabled(self.enabled)
        self.text.setGeometry(QtCore.QRect(10, 46, 55, 16))
        font = QtGui.QFont()
        font.setPointSize(5)
        self.text.setFont(font)
        self.text.setStyleSheet("color: rgb(255, 255, 255);\n"
                                "background-color: rgba(255, 255, 255, 0);")
        self.text.setAlignment(QtCore.Qt.AlignCenter)
        self.text.setWordWrap(True)
        self.text.setObjectName(rf"text_{name.lower()}")
        self.text.setText(name.title())'''

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
class UnitBlock():
    def __init__(self, index, name, type, unit_code, enabled, enable_list, disable_list):
        self.index = index
        self.name = name
        self.unit_code = unit_code
        self.enabled = enabled
        self.type = type
        self.disable_list = disable_list
        self.enable_list = enable_list
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
    (16, 0, 1, 2), (16, 3, 4, 5), (16, 6), (16, 7), (16, 8, 9), (16, 10, 11), (16, 12, 13), 
    (16, 14), (16, 15), (27, 17, 18, 19, 20, 21), (27, 22, 23), (27, 24, 25, 26), 
    (27, 28, 29, 30), (27, 31), (27, 32), (27, 33), (45, 34, 35, 36), (45, 37), 
    (45, 38, 39), (45, 40, 41, 42), (45, 43, 44), (45, 46), (45, 47, 48, 49), 
    (45, 50, 51), (45, 52), (59, 53, 54, 55), (59, 56, 57), (59, 58), (59, 60, 61, 62), 
    (59, 63, 64), (59, 65), (59, 66, 67), (74, 68, 69, 70), (74, 71, 72, 73), 
    (74, 75, 76, 77), (74, 78, 79, 80), (74, 81, 82, 83), (100, 84), (100, 85, 86, 87), 
    (100, 88), (100, 89), (100, 90), (100, 91, 92), (100, 93, 94, 95), (100, 96, 97, 98), 
    (100, 99), (100, 101, 102), (100, 103, 104), (100, 105), (100, 106), (114, 107, 108), 
    (114, 109), (114, 110, 111), (114, 112), (114, 113), (114, 115, 116), (114, 117), 
    (114, 118), (114, 119), (114, 120),
    (137, 131, 132), (137, 133), (137, 134), (137, 135, 136), (137, 138), 
    (137, 139), (137, 140), (137, 141), (142, 143, 144), (145, 146, 147), (145, 148, 149, 150), 
    (159, 151), (159, 152), (159, 153), (159, 154), (159, 155, 156), (159, 157), (159, 158), 
    (159, 160), (159, 161), (159, 162), (159, 163), (159, 164), (165, 166), (171, 168), 
    (171, 169, 170), (171, 172, 173, 174), (171, 175), (171, 176, 177), (191, 192), 
    (191, 193, 194), (191, 195), (191, 196), (122, 123, 124), (129, 130), (182, 183), (184, 185), (188, 189, 190), (200, 201, 202)
]
        self.equals = [(24, 148), (25, 149), (26, 150), (111, 125), (109, 130), (115, 123), (116, 124)]
        #self.opposites = [(6, 7), (8, 10), (9, 10), (10, 8), (11, 8), (53, 56), (54, 56), (55, 56), (56, 53), (57, 53), (186, 181), (186, 187), (199, 197)]

    def enable(self):
        self.enabled = True
        self.opacity_effect.setOpacity(0)
        self.disable_label.setGraphicsEffect(self.opacity_effect)

        # Enabled equals
        

        # Enable other units in hierarchy
        for hierarchy in self.hierarchies:
            if self.index in hierarchy:
                for unit_index in hierarchy:
                    if unit_index != self.index:
                        unit_blocks[unit_index].enable()
                    else:
                        break

    def disable(self):
        self.enabled = False
        self.opacity_effect.setOpacity(0.75)
        self.disable_label.setGraphicsEffect(self.opacity_effect)

        # Enabled equals
        

        # Disable other units in hierarchy
        for hierarchy in self.hierarchies:
            reverse_hierarchy = hierarchy[::-1]  # Create a reversed copy of the hierarchy
            if self.index in reverse_hierarchy:
                for unit_index in reverse_hierarchy:
                    if unit_index != self.index:
                        unit_blocks[unit_index].disable()
                    else:
                        break


    def on_button_clicked(self):
        # Toggle the enabled state
        if self.enabled:
            self.disable()
        else:
            self.enable()

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

    # Connect Civilisation dropdown
    #MAIN_WINDOW.civilisation_dropdown = CivilisationDropdown(QtWidgets.QComboBox)

    # Set application images
    MAIN_WINDOW.label.setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/dark_age.png"))
    MAIN_WINDOW.label_2.setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/feudal_age.png"))
    MAIN_WINDOW.label_3.setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/castle_age.png"))
    MAIN_WINDOW.label_4.setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/imperial_age.png"))

    # Setup objects
    #unit_codes = [4, 24, 492, 7, 6, 1155, 185, 5, 39, 474, 873, 875, 583, 586, 437, 'Parthian TacticsR', 'Archery RangeB', 'MilitiaU', 'Man-at-ArmsU', 'Long SwordsmanU', 'Two-Handed SwordsmanU', 'ChampionU', 'SuppliesR', 'GambesonsR', 'SpearmanU', 'PikemanU', 'HalberdierU', 'BarracksB', 'Eagle ScoutU', 'Eagle WarriorU', 'Elite Eagle WarriorU', 'SquiresR', 'CondottieroX', 'ArsonR', 'Scout CavalryU', 'Light CavalryU', 'HussarU', 'BloodlinesR', 'Shrivamsha RiderX', 'Elite Shrivamsha RiderX', 'KnightU', 'CavalierU', 'PaladinU', 'Steppe LancerU', 'Elite Steppe LancerU', 'StableB', 'Camel ScoutX', 'Camel RiderU', 'Heavy Camel RiderU', 'Imperial Camel RiderX', 'Battle ElephantU', 'Elite Battle ElephantU', 'HusbandryR', 'Battering RamU', 'Capped RamU', 'Siege RamU', 'Armored ElephantU', 'Siege ElephantU', 'Flaming CamelX', 'Siege WorkshopB', 'MangonelU', 'OnagerU', 'Siege OnagerU', 'ScorpionU', 'Heavy ScorpionU', 'Siege TowerU', 'Bombard CannonU', 'HoufniceX', 'Padded Archer ArmorR', 'Leather Archer ArmorR', 'Ring Archer ArmorR', 'FletchingR', 'Bodkin ArrowR', 'BracerR', 'BlacksmithB', 'ForgingR', 'Iron CastingR', 'Blast FurnaceR', 'Scale Barding ArmorR', 'Chain Barding ArmorR', 'Plate Barding ArmorR', 'Scale Mail ArmorR', 'Chain Mail ArmorR', 'Plate Mail ArmorR', 'Fishing ShipU', 'Fire GalleyU', 'Fire ShipU', 'Fast Fire ShipU', 'Transport ShipU', 'Trade CogU', 'GillnetsR', 'Cannon GalleonU', 'Elite Cannon GalleonU', 'Demolition RaftU', 'Demolition ShipU', 'Heavy Demolition ShipU', 'GalleyU', 'War GalleyU', 'GalleonU', 'DromonU', 'DockB', 'Turtle ShipU', 'Elite Turtle ShipU', 'CareeningR', 'Dry DockR', 'ShipwrightR', 'Fish TrapB', 'MasonryR', 'ArchitectureR', 'Fortified WallR', 'ChemistryR', 'Bombard TowerR', 'BallisticsR', 'Siege EngineersR', 'UniversityB', 'Guard TowerR', 'KeepR', 'Heated ShotR', 'ArrowslitsR', 'Murder HolesR', 'Treadmill CraneR', 'OutpostB', 'Watch TowerB', 'Guard TowerBB', 'KeepBB', 'Bombard TowerBB', 'Palisade WallB', 'Palisade GateB', 'GateB', 'Stone WallB', 'Fortified WallBB', 'Unique UnitX', 'Elite Unique UnitX', 'PetardU', 'TrebuchetU', 'Castle TechR', 'Imperial TechR', 'CastleB', 'HoardingsR', 'SappersR', 'ConscriptionR', 'SpiesR', 'KrepostB', 'KonnikX', 'Elite KonnikX', 'DonjonB', 'SerjeantX', 'Elite SerjeantX', 'SpearmanXU', 'PikemanXU', 'HalberdierXU', 'MonkU', 'IlluminationR', 'MissionaryX', 'Block PrintingR', 'DevotionR', 'FaithR', 'RedemptionR', 'TheocracyR', 'MonasteryB', 'AtonementR', 'Herbal MedicineR', 'HeresyR', 'SanctityR', 'FervorR', 'Fortified ChurchB', 'Warrior PriestX', 'HouseB', 'VillagerU', 'Town WatchR', 'Town PatrolR', 'Town CenterB', 'Feudal AgeR', 'Castle AgeR', 'Imperial AgeR', 'LoomR', 'WheelbarrowR', 'Hand CartR', 'WonderB', 'FeitoriaB', 'CaravanseraiB', 'Mining CampB', 'Gold MiningR', 'Gold Shaft MiningR', 'Stone MiningR', 'Stone Shaft MiningR', 'Mule CartB', 'Lumber CampB', 'Double-Bit AxeR', 'Bow SawR', 'Two-Man SawR', 'MarketB', 'Trade CartU', 'CoinageR', 'BankingR', 'CaravanR', 'GuildsR', 'FolwarkB', 'FarmB', 'MillB', 'Horse CollarR', 'Heavy PlowR', 'Crop RotationR']:
    block_index = 0
    for unit in ['ArcherU', 'CrossbowmanU', 'ArbalesterU', 'SkirmisherU', 'Elite SkirmisherU', 'Imperial SkirmisherX', 'SlingerX', 'Hand CannoneerU', 'Cavalry ArcherU', 'Heavy Cavalry ArcherU', 'Elephant ArcherU', 'Elite Elephant ArcherU', 'GenitourX', 'Elite GenitourX', 'Thumb RingR', 'Parthian TacticsR', 'Archery RangeB', 'MilitiaU', 'Man-at-ArmsU', 'Long SwordsmanU', 'Two-Handed SwordsmanU', 'ChampionU', 'SuppliesR', 'GambesonsR', 'SpearmanU', 'PikemanU', 'HalberdierU', 'BarracksB', 'Eagle ScoutU', 'Eagle WarriorU', 'Elite Eagle WarriorU', 'SquiresR', 'CondottieroX', 'ArsonR', 'Scout CavalryU', 'Light CavalryU', 'HussarU', 'BloodlinesR', 'Shrivamsha RiderX', 'Elite Shrivamsha RiderX', 'KnightU', 'CavalierU', 'PaladinU', 'Steppe LancerU', 'Elite Steppe LancerU', 'StableB', 'Camel ScoutX', 'Camel RiderU', 'Heavy Camel RiderU', 'Imperial Camel RiderX', 'Battle ElephantU', 'Elite Battle ElephantU', 'HusbandryR', 'Battering RamU', 'Capped RamU', 'Siege RamU', 'Armored ElephantU', 'Siege ElephantU', 'Flaming CamelX', 'Siege WorkshopB', 'MangonelU', 'OnagerU', 'Siege OnagerU', 'ScorpionU', 'Heavy ScorpionU', 'Siege TowerU', 'Bombard CannonU', 'HoufniceX', 'Padded Archer ArmorR', 'Leather Archer ArmorR', 'Ring Archer ArmorR', 'FletchingR', 'Bodkin ArrowR', 'BracerR', 'BlacksmithB', 'ForgingR', 'Iron CastingR', 'Blast FurnaceR', 'Scale Barding ArmorR', 'Chain Barding ArmorR', 'Plate Barding ArmorR', 'Scale Mail ArmorR', 'Chain Mail ArmorR', 'Plate Mail ArmorR', 'Fishing ShipU', 'Fire GalleyU', 'Fire ShipU', 'Fast Fire ShipU', 'Transport ShipU', 'Trade CogU', 'GillnetsR', 'Cannon GalleonU', 'Elite Cannon GalleonU', 'Demolition RaftU', 'Demolition ShipU', 'Heavy Demolition ShipU', 'GalleyU', 'War GalleyU', 'GalleonU', 'DromonU', 'DockB', 'Turtle ShipU', 'Elite Turtle ShipU', 'CareeningR', 'Dry DockR', 'ShipwrightR', 'Fish TrapB', 'MasonryR', 'ArchitectureR', 'Fortified WallR', 'ChemistryR', 'Bombard TowerR', 'BallisticsR', 'Siege EngineersR', 'UniversityB', 'Guard TowerR', 'KeepR', 'Heated ShotR', 'ArrowslitsR', 'Murder HolesR', 'Treadmill CraneR', 'OutpostB', 'Watch TowerB', 'Guard TowerBB', 'KeepBB', 'Bombard TowerBB', 'Palisade WallB', 'Palisade GateB', 'GateB', 'Stone WallB', 'Fortified WallBB', 'Unique UnitX', 'Elite Unique UnitX', 'PetardU', 'TrebuchetU', 'Castle TechR', 'Imperial TechR', 'CastleB', 'HoardingsR', 'SappersR', 'ConscriptionR', 'SpiesR', 'KrepostB', 'KonnikX', 'Elite KonnikX', 'DonjonB', 'SerjeantX', 'Elite SerjeantX', 'SpearmanXU', 'PikemanXU', 'HalberdierXU', 'MonkU', 'IlluminationR', 'MissionaryX', 'Block PrintingR', 'DevotionR', 'FaithR', 'RedemptionR', 'TheocracyR', 'MonasteryB', 'AtonementR', 'Herbal MedicineR', 'HeresyR', 'SanctityR', 'FervorR', 'Fortified ChurchB', 'Warrior PriestX', 'HouseB', 'VillagerU', 'Town WatchR', 'Town PatrolR', 'Town CenterB', 'Feudal AgeR', 'Castle AgeR', 'Imperial AgeR', 'LoomR', 'WheelbarrowR', 'Hand CartR', 'WonderB', 'FeitoriaB', 'CaravanseraiB', 'Mining CampB', 'Gold MiningR', 'Gold Shaft MiningR', 'Stone MiningR', 'Stone Shaft MiningR', 'Mule CartB', 'Lumber CampB', 'Double-Bit AxeR', 'Bow SawR', 'Two-Man SawR', 'MarketB', 'Trade CartU', 'CoinageR', 'BankingR', 'CaravanR', 'GuildsR', 'FolwarkB', 'FarmB', 'MillB', 'Horse CollarR', 'Heavy PlowR', 'Crop RotationR']:
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
            new_block = UnitBlock(block_index, unit_name, type, -1, True, [], [])
            unit_blocks.append(new_block)
            block_index += 1

            # Connect the button click to a function
            push_button.setStyleSheet("background-color: transparent; border: none;")
            push_button.raise_()
            #push_button.setEnabled(True)
            push_button.clicked.connect(new_block.on_button_clicked)
        
        except Exception as e:
            print(rf'Failed Block: {unit} : {str(e)}')

    '''unit_list = [
        'Archer',                # 0
        'Crossbowman',           # 1
        'Arbalester',            # 2
        'Skirmisher',            # 3
        'Elite Skirmisher',      # 4
        'Imperial Skirmisher',   # 5
        'Slinger',               # 6
        'Hand Cannoneer',        # 7
        'Cavalry Archer',        # 8
        'Heavy Cavalry Archer',  # 9
        'Elephant Archer',       # 10
        'Elite Elephant Archer', # 11
        'Genitour',              # 12
        'Elite Genitour',        # 13
        'Thumb Ring',            # 14
        'Parthian Tactics',      # 15
        'Archery Range',         # 16
        'Militia',               # 17
        'Man-at-Arms',           # 18
        'Long Swordsman',        # 19
        'Two-Handed Swordsman',  # 20
        'Champion',              # 21
        'Supplies',              # 22
        'Gambesons',             # 23
        'Spearman',              # 24
        'Pikeman',               # 25
        'Halberdier',            # 26
        'Barracks',              # 27
        'Eagle Scout',           # 28
        'Eagle Warrior',         # 29
        'Elite Eagle Warrior',   # 30
        'Squires',               # 31
        'Condottiero',           # 32
        'Arson',                 # 33
        'Scout Cavalry',         # 34
        'Light Cavalry',         # 35
        'Hussar',                # 36
        'Bloodlines',            # 37
        'Shrivamsha Rider',      # 38
        'Elite Shrivamsha Rider',# 39
        'Knight',                # 40
        'Cavalier',              # 41
        'Paladin',               # 42
        'Steppe Lancer',         # 43
        'Elite Steppe Lancer',   # 44
        'Stable',                # 45
        'Camel Scout',           # 46
        'Camel Rider',           # 47
        'Heavy Camel Rider',     # 48
        'Imperial Camel Rider',  # 49
        'Battle Elephant',       # 50
        'Elite Battle Elephant', # 51
        'Husbandry',             # 52
        'Battering Ram',         # 53
        'Capped Ram',            # 54
        'Siege Ram',             # 55
        'Armored Elephant',      # 56
        'Siege Elephant',        # 57
        'Flaming Camel',         # 58
        'Siege Workshop',        # 59
        'Mangonel',              # 60
        'Onager',                # 61
        'Siege Onager',          # 62
        'Scorpion',              # 63
        'Heavy Scorpion',        # 64
        'Siege Tower',           # 65
        'Bombard Cannon',        # 66
        'Houfnice',              # 67
        'Padded Archer Armor',   # 68
        'Leather Archer Armor',  # 69
        'Ring Archer Armor',     # 70
        'Fletching',             # 71
        'Bodkin Arrow',          # 72
        'Bracer',                # 73
        'Blacksmith',            # 74
        'Forging',               # 75
        'Iron Casting',          # 76
        'Blast Furnace',         # 77
        'Scale Barding Armor',   # 78
        'Chain Barding Armor',   # 79
        'Plate Barding Armor',   # 80
        'Scale Mail Armor',      # 81
        'Chain Mail Armor',      # 82
        'Plate Mail Armor',      # 83
        'Fishing Ship',          # 84
        'Fire Galley',           # 85
        'Fire Ship',             # 86
        'Fast Fire Ship',        # 87
        'Transport Ship',        # 88
        'Trade Cog',             # 89
        'Gillnets',              # 90
        'Cannon Galleon',        # 91
        'Elite Cannon Galleon',  # 92
        'Demolition Raft',       # 93
        'Demolition Ship',       # 94
        'Heavy Demolition Ship', # 95
        'Galley',                # 96
        'War Galley',            # 97
        'Galleon',               # 98
        'Dromon',                # 99
        'Dock',                  # 100
        'Turtle Ship',           # 101
        'Elite Turtle Ship',     # 102
        'Careening',             # 103
        'Dry Dock',              # 104
        'Shipwright',            # 105
        'Fish Trap',             # 106
        'Masonry',               # 107
        'Architecture',          # 108
        'Fortified Wall',        # 109
        'Chemistry',             # 110
        'Bombard Tower',         # 111
        'Ballistics',            # 112
        'Siege Engineers',       # 113
        'University',            # 114
        'Guard Tower',           # 115
        'Keep',                  # 116
        'Heated Shot',           # 117
        'Arrowslits',            # 118
        'Murder Holes',          # 119
        'Treadmill Crane',       # 120
        'Outpost',               # 121
        'Watch Tower',           # 122
        'Guard TowerB',          # 123
        'KeepBB',                # 124
        'Bombard TowerBB',       # 125
        'Palisade Wall',         # 126
        'Palisade Gate',         # 127
        'Gate',                  # 128
        'Stone Wall',            # 129
        'Fortified WallBB',      # 130
        'Unique Unit',           # 131
        'Elite Unique Unit',     # 132
        'Petard',                # 133
        'Trebuchet',             # 134
        'Castle Tech',           # 135
        'Imperial Tech',         # 136
        'Castle',                # 137
        'Hoardings',             # 138
        'Sappers',               # 139
        'Conscription',          # 140
        'Spies',                 # 141
        'Krepost',               # 142
        'Konnik',                # 143
        'Elite Konnik',          # 144
        'Donjon',                # 145
        'Serjeant',              # 146
        'Elite Serjeant',        # 147
        'SpearmanXU',            # 148
        'PikemanXU',             # 149
        'HalberdierXU',          # 150
        'Monk',                  # 151
        'Illumination',          # 152
        'Missionary',            # 153
        'Block Printing',        # 154
        'Devotion',              # 155
        'Faith',                 # 156
        'Redemption',            # 157
        'Theocracy',             # 158
        'Monastery',             # 159
        'Atonement',             # 160
        'Herbal Medicine',       # 161
        'Heresy',                # 162
        'Sanctity',              # 163
        'Fervor',                # 164
        'Fortified Church',      # 165
        'Warrior Priest',        # 166
        'House',                 # 167
        'Villager',              # 168
        'Town Watch',            # 169
        'Town Patrol',           # 170
        'Town Center',           # 171
        'Feudal Age',            # 172
        'Castle Age',            # 173
        'Imperial Age',          # 174
        'Loom',                  # 175
        'Wheelbarrow',           # 176
        'Hand Cart',             # 177
        'Wonder',                # 178
        'Feitoria',              # 179
        'Caravanserai',          # 180
        'Mining Camp',           # 181
        'Gold Mining',           # 182
        'Gold Shaft Mining',     # 183
        'Stone Mining',          # 184
        'Stone Shaft Mining',    # 185
        'Mule Cart',             # 186
        'Lumber Camp',           # 187
        'Double-Bit Axe',        # 188
        'Bow Saw',               # 189
        'Two-Man Saw',           # 190
        'Market',                # 191
        'Trade Cart',            # 192
        'Coinage',               # 193
        'Banking',               # 194
        'Caravan',               # 195
        'Guilds',                # 196
        'Folwark',               # 197
        'Farm',                  # 198
        'Mill',                  # 199
        'Horse Collar',          # 200
        'Heavy Plow',            # 201
        'Crop Rotation'          # 202
    ]'''

    # Show the main window
    MainWindow.setWindowTitle(f"Talofa")
    MainWindow.setWindowIcon(QtGui.QIcon(rf"{os.path.dirname(os.path.abspath(__file__))}\Images\UI\flower.ico"))
    MainWindow.showMaximized()

    # Assign functions to navigation buttons
    MAIN_WINDOW.actionNew_Project.triggered.connect(new_project)
    MAIN_WINDOW.actionOpen_Project.triggered.connect(open_project)
    MAIN_WINDOW.actionSave_Project.triggered.connect(save_project)
    MAIN_WINDOW.actionRevert_To_Original.triggered.connect(revert_project)

# Set up tech tree
'''class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Window Example")
        print("show item")
        
        # Create central widget and set layout
        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)  # A vertical layout for simplicity

        # Create and add Unit_Square instance to layout
        unit_square = Unit_Square(name="Crossbowman", type="Infantry", coordinates=[10, 20], enabled=True)
        layout.addWidget(unit_square)

    # Test layout
    MAIN_WINDOW.background.setEnabled(True)
    MAIN_WINDOW.background.setGeometry(QtCore.QRect(0, 0, 75, 75))
    MAIN_WINDOW.background.setMinimumSize(QtCore.QSize(75, 75))
    MAIN_WINDOW.background.setMaximumSize(QtCore.QSize(75, 75))
    MAIN_WINDOW.background.setAutoFillBackground(False)
    MAIN_WINDOW.background.setText("")
    MAIN_WINDOW.background.setPixmap(QtGui.QPixmap("../../../../../../../../OneDrive/Documents/GitHub/AOE2DE_CivCreator/Images/TechTree/unit.png"))
    MAIN_WINDOW.background.setScaledContents(True)
    MAIN_WINDOW.background.setObjectName("background")'''

#special_ui.setup_custom_dropbox()    

# Update the stats when the civilisation dropdown is changed
MAIN_WINDOW.civilisation_dropdown.currentIndexChanged.connect(update_civilisation_dropdown)

sys.exit(app.exec_())  # Run the application's event loop