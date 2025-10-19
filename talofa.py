# Micheal Quentin
# 02. March 2025
# 2025 Civilisation Creator

'''
# Advanced Genie Editor
wine /home/xommon/snap/steam/common/.local/share/Steam/steamapps/common/AoE2DE/Tools_Builds/AdvancedGenieEditor3.exe

# .DAT File
/home/xommon/snap/steam/common/.local/share/Steam/steamapps/compatdata/813780/pfx/drive_c/users/steamuser/Games/Age of Empires 2 DE/76561198021486964/mods/local/Test/resources/_common/dat/empires2_x2_p1.dat

# Real World Map Folder
/home/xommon/snap/steam/common/.local/share/Steam/steamapps/common/AoE2DE/resources/_common/drs/gamedata_x2

# Scenario Folder
/home/xommon/snap/steam/common/.local/share/Steam/steamapps/compatdata/813780/pfx/drive_c/users/steamuser/Games/Age of Empires 2 DE/76561198021486964/resources/_common/scenario

# Custom Map .RMS
/home/xommon/snap/steam/common/.local/share/Steam/steamapps/common/AoE2DE/resources/_common/random-map-scripts

# Terminal code to show image overlay
python3 overlay.py ~/Documents/central_america.jpg 0.5 350 350

# Convert .ui to .py
pyuic5 -x main_window.ui -o main_window.py
'''

import os
from html import escape
import shutil
import time
import pickle
import io
import ast
import genieutils
from genieutils.datfile import DatFile
from genieutils.tech import ResearchResourceCost
import genieutils.graphic
import genieutils.sound
import glob
import genieutils.tech
import genieutils.unit
from genieutils.graphic import GraphicDelta
from genieutils.graphic import Graphic
from genieutils.graphic import GraphicAngleSound
import genieutils.effect
import json
import re
import string
import pyperclip
from prompt_toolkit import prompt
import platform
import subprocess
from threading import Thread
import sys
from colorama import Fore, Style, Back, init
from collections import defaultdict
import readline
import copy
from datetime import datetime
from math import ceil
from genieutils.tech import Tech, ResearchResourceCost, ResearchLocation
from genieutils.versions import Version
import traceback
import sys
import unicodedata
from pathlib import Path
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog
from main_window import Ui_MainWindow
from new_project_window import Ui_NewMod
import unicodedata
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5.QtWidgets import QUndoCommand
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QProgressDialog
from PyQt5.QtCore import Qt
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QProgressDialog
import time
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QDialog, QProgressDialog

class RenameCivCommand(QtWidgets.QUndoCommand):
    def __init__(self, app, civ_pos, civ_data_index, old_name, new_name, description="Rename Civ"):
        super().__init__()              # ✅ no extra args
        self.setText(description)       # ✅ proper way to set Undo menu text
        self.app = app
        self.civ_pos = civ_pos
        self.civ_data_index = civ_data_index
        self.old_name = old_name
        self.new_name = new_name

    def undo(self):
        self.app._apply_civ_rename(self.civ_pos, self.civ_data_index, self.new_name, self.old_name)

    def redo(self):
        self.app._apply_civ_rename(self.civ_pos, self.civ_data_index, self.old_name, self.new_name)

class ChangeTitleCommand(QtWidgets.QUndoCommand):
    def __init__(self, app, civ, old_title, new_title, description="Change Title"):
        super().__init__()
        self.setText(description)
        self.app = app
        self.civ = civ
        self.old_title = old_title
        self.new_title = new_title

    def undo(self):
        self.app._apply_title_change(self.civ, self.new_title, self.old_title)

    def redo(self):
        self.app._apply_title_change(self.civ, self.old_title, self.new_title)

class ChangeLanguageCommand(QtWidgets.QUndoCommand):
    def __init__(self, app, civ_index, sound_ids, old_lang, new_lang, description="Change Language"):
        super().__init__()
        self.setText(description)
        self.app = app
        self.civ_index = civ_index
        self.sound_ids = sound_ids
        self.old_lang = old_lang
        self.new_lang = new_lang

    def undo(self):
        self.app._apply_language_change(self.civ_index, self.sound_ids, self.new_lang, self.old_lang)

    def redo(self):
        self.app._apply_language_change(self.civ_index, self.sound_ids, self.old_lang, self.new_lang)

class ChangeScoutUnitCommand(QtWidgets.QUndoCommand):
    def __init__(self, app, civ_index, old_value, new_value, description="Change Scout Unit"):
        super().__init__()
        self.setText(description)
        self.app = app
        self.civ_index = civ_index
        self.old_value = old_value
        self.new_value = new_value

    def undo(self):
        self.app._apply_scout_unit_change(self.civ_index, self.new_value, self.old_value)

    def redo(self):
        self.app._apply_scout_unit_change(self.civ_index, self.old_value, self.new_value)

class ChangeUniqueUnitCommand(QtWidgets.QUndoCommand):
    def __init__(self, app, civ_data_index, old_value, new_value, description="Change Unique Unit"):
        super().__init__()
        self.setText(description)
        self.app = app
        self.civ_data_index = civ_data_index   # ✅ always store data_index, not talofa_index
        self.old_value = old_value             # tuple (castle_unit_id, imperial_unit_id, imperial_upgrade_id)
        self.new_value = new_value

    def undo(self):
        self.app._apply_unique_unit_change(self.civ_data_index, self.new_value, self.old_value)

    def redo(self):
        self.app._apply_unique_unit_change(self.civ_data_index, self.old_value, self.new_value)

class ChangeGraphicsCommand(QtWidgets.QUndoCommand):
    def __init__(self, app, civ_index, category, old_units, new_units, description=None):
        desc = description or f"Change {category} Graphics"
        super().__init__(desc)
        self.app = app
        self.civ_index = civ_index
        self.category = category
        self.old_units = old_units  # dict {unit_id: unit_obj}
        self.new_units = new_units  # dict {unit_id: unit_obj}

    def undo(self):
        self._apply(self.old_units)

    def redo(self):
        self._apply(self.new_units)

    def _apply(self, units_dict):
        for unit_id, unit_obj in units_dict.items():
            DATA.civs[self.civ_index].units[unit_id] = copy.deepcopy(unit_obj)

        # refresh CURRENT_CIV UI if this civ is active
        if CURRENT_CIV.data_index == self.civ_index:
            self.app.dropdown_civ_name_changed(CURRENT_CIV.talofa_index)

        # mark unsaved
        if not self.app.windowTitle().endswith("*"):
            self.app.setWindowTitle(self.app.windowTitle() + "*")

class MyApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("main_window.ui", self)
        self.setWindowTitle("Talofa")
        self.centralwidget.setEnabled(False)

        # Menu buttons
        self.actionSave_Mod.triggered.connect(self.save_mod)
        self.actionOpen_Mod.triggered.connect(self.open_mod)
        self.actionNew_Mod.triggered.connect(self.new_mod_window)

        # Program buttons
        self.button_civ_name.clicked.connect(self.change_name)
        self.button_civ_name.clicked.connect(self.change_name)
        self.input_civ_name.returnPressed.connect(self.change_name)

        self.button_title.clicked.connect(self.change_title)
        self.button_title.clicked.connect(self.change_title)
        self.input_title.returnPressed.connect(self.change_title)

        # Allow description textbox to wordwrap
        self.textbox_description.setWordWrap(True)

        # Define undo stack
        self.undoStack = QtWidgets.QUndoStack(self)

        # Hook Undo/Redo menu actions
        self.actionUndo.setText("Undo")
        self.actionRedo.setText("Redo")
        self.actionUndo.setShortcut("Ctrl+Z")
        self.actionRedo.setShortcut("Ctrl+Y")

        self.actionUndo.triggered.connect(self.undoStack.undo)
        self.actionRedo.triggered.connect(self.undoStack.redo)

        # auto enable/disable
        self.undoStack.canUndoChanged.connect(self.actionUndo.setEnabled)
        self.undoStack.canRedoChanged.connect(self.actionRedo.setEnabled)
        self.actionUndo.setEnabled(False)
        self.actionRedo.setEnabled(False)

    # --- 1) A worker that runs in background and emits progress ---
    class WorkerThread(QThread):
        progress = pyqtSignal(int)      # 0..100
        message = pyqtSignal(str)       # optional: status text
        done = pyqtSignal()             # finished signal

        def __init__(self, mod_name: str, mod_folder: str,
                    replace_3kingdoms: bool,
                    canoes_mesoamerican: bool,
                    canoes_sea: bool,
                    canoes_other: bool,
                    parent=None):
            super().__init__(parent)
            self.mod_name = mod_name
            self.mod_folder = mod_folder
            self.replace_3kingdoms = replace_3kingdoms
            self.canoes_mesoamerican = canoes_mesoamerican
            self.canoes_sea = canoes_sea
            self.canoes_other = canoes_other
            self._cancel = False

        def cancel(self):
            self._cancel = True

        def run(self):
            steps = [
                ("Preparing folders", self.prepare_folders),
                ("Saving links", self.save_links),
                ("Copying base files", self.copy_base_files),
                ("Copying UI files", self.copy_ui_files),
                ("Replacing Civilization Icons", self.replace_civ_icons),
            ]

            total = len(steps)

            for i, (label, func) in enumerate(steps, start=1):
                if self._cancel:
                    return

                self.message.emit(label)

                try:
                    func()   # <-- perform that step
                except Exception as e:
                    print(f"Error at step '{label}': {e}")

                pct = int(i * 100 / total)
                self.progress.emit(pct)

            self.done.emit()

        def prepare_folders(self):
            for folder in [MOD_FOLDER, MOD_UI_FOLDER]:
                if os.path.exists(folder):
                    shutil.rmtree(folder)
                os.makedirs(folder, exist_ok=True)

        def save_links(self):
            with open(f'{MOD_FOLDER}/links.pkl', 'wb') as file:
                pickle.dump(AOE2_FOLDER, file)
                file.write(b'\n')

        def copy_base_files(self):
            files_to_copy = [...]
            for item in files_to_copy:
                # Ensure fresh mod folders
                for folder in [MOD_FOLDER, MOD_UI_FOLDER]:
                    if os.path.exists(folder):
                        shutil.rmtree(folder)
                    os.makedirs(folder, exist_ok=True)

                # Save important links in main mod folder
                with open(f'{MOD_FOLDER}/links.pkl', 'wb') as file:
                    pickle.dump(AOE2_FOLDER, file)
                    file.write(b'\n')

                # Files or folders to copy into the main mod folder
                files_to_copy = [
                    'resources/_common/dat/civilizations.json', 
                    'resources/_common/dat/civTechTrees.json', 
                    'resources/_common/dat/empires2_x2_p1.dat', 
                    'resources/_common/wpfg/resources/civ_techtree',
                    'resources/_common/wpfg/resources/uniticons',
                    'resources/en/strings/key-value/key-value-strings-utf8.txt',
                    'resources/en/strings/key-value/key-value-modded-strings-utf8.txt',
                    'widgetui/textures/menu/civs',
                ]

                for item in files_to_copy:
                    source_path = os.path.join(AOE2_FOLDER, item)
                    destination_path = os.path.join(MOD_FOLDER, item)

                    os.makedirs(os.path.dirname(destination_path), exist_ok=True)

                    if os.path.isfile(source_path):
                        shutil.copy(source_path, destination_path)
                    elif os.path.isdir(source_path):
                        shutil.copytree(source_path, destination_path, dirs_exist_ok=True)

        def copy_ui_files(self):
            ui_files_to_copy = [...]
            for item in ui_files_to_copy:
                # Files or folders to copy into the UI-only mod folder
                ui_files_to_copy = [
                    'widgetui/textures/ingame/icons/civ_techtree_buttons',
                    'widgetui/textures/menu/civs',
                ]

                for item in ui_files_to_copy:
                    source_path = os.path.join(AOE2_FOLDER, item)
                    destination_path = os.path.join(MOD_UI_FOLDER, item)

                    os.makedirs(os.path.dirname(destination_path), exist_ok=True)

                    if os.path.isfile(source_path):
                        shutil.copy(source_path, destination_path)
                    elif os.path.isdir(source_path):
                        shutil.copytree(source_path, destination_path, dirs_exist_ok=True)

        def replace_civ_icons(self):
            # Replace civ icons
            MOD_FOLDER = os.path.abspath(os.path.join(LOCAL_MODS_FOLDER, MOD_NAME))
            MOD_UI_FOLDER = os.path.abspath(os.path.join(LOCAL_MODS_FOLDER, f"{MOD_NAME}-ui"))

            source_icons_folder = os.path.join("Images", "CivIcons")
            if not os.path.exists(source_icons_folder):
                print(f"⚠️ No CivIcons folder found at {source_icons_folder}")
                return

            # Get all .png files in Images/CivIcons
            icon_files = glob.glob(os.path.join(source_icons_folder, "*.png"))
            if not self.replace_3kingdoms:
                filtered_icons = []
                for file in icon_files:
                    if not file.endswith(('wu.png', 'wei.png', 'shu.png')):
                        filtered_icons.append(file)

                icon_files = filtered_icons  # replace the original list

            for icon_path in icon_files:
                civ_name = os.path.splitext(os.path.basename(icon_path))[0]  # filename without .png

                # === Replace in civ icon folders ===
                civ_targets = [
                    os.path.join(MOD_FOLDER, "widgetui/textures/menu/civs", f"{civ_name}.png"),
                    os.path.join(MOD_UI_FOLDER, "widgetui/textures/menu/civs", f"{civ_name}.png"),
                ]

                for tgt in civ_targets:
                    if os.path.exists(os.path.dirname(tgt)):
                        shutil.copy(icon_path, tgt)

                # === Replace in civ techtree/button folders ===
                tech_targets = [
                    os.path.join(MOD_FOLDER, "resources/_common/wpfg/resources/civ_techtree"),
                    os.path.join(MOD_FOLDER, "widgetui/textures/ingame/icons/civ_techtree_buttons"),
                    os.path.join(MOD_UI_FOLDER, "widgetui/textures/ingame/icons/civ_techtree_buttons"),
                ]

                for folder in tech_targets:
                    if os.path.exists(folder):
                        for suffix in ["", "_hover", "_pressed"]:
                            tgt = os.path.join(folder, f"menu_techtree_{civ_name}{suffix}.png")
                            shutil.copy(icon_path, tgt)

        def finalize(self):
            # e.g. cleanup or summary
            pass

    def new_mod_window(self):
        dlg = QDialog(self)
        global ui
        ui = Ui_NewMod()
        ui.setupUi(dlg)

        # Get window settings
        global REPLACE_3KINGDOMS, CANOES_MESOAMERICAN, CANOES_SEA, CANOES_OTHER
        REPLACE_3KINGDOMS = ui.replace_3kingdoms_checkbox.isChecked()
        CANOES_MESOAMERICAN = ui.canoes_mesoamericans_checkbox.isChecked()
        CANOES_SEA = ui.canoes_sea_checkbox.isChecked()
        CANOES_OTHER = ui.canoes_other_checkbox.isChecked()

        ui.create_mod_button.clicked.connect(lambda: self.create_new_mod(dlg, ui))
        dlg.setModal(True)
        dlg.exec_()

    def create_new_mod(self, dialog: QDialog, ui: Ui_NewMod):
        # grab inputs before closing the dialog
        global MOD_NAME, LOCAL_MODS_FOLDER, AOE2_FOLDER, MOD_FOLDER, MOD_UI_FOLDER
        MOD_NAME  = ui.mod_name_input.text().strip()
        LOCAL_MODS_FOLDER  = ui.local_mods_folder_input.text().strip()
        AOE2_FOLDER  = ui.aoe2_folder_input.text().strip()
        MOD_FOLDER = f"{LOCAL_MODS_FOLDER}/{MOD_NAME}"
        MOD_UI_FOLDER = f"{LOCAL_MODS_FOLDER}/{MOD_NAME}-ui"

        dialog.close()  # close the “New Mod” dialog

        # create a modal progress dialog
        self.progress_dlg = QProgressDialog("Starting…", "Cancel", 0, 100, self)
        self.progress_dlg.setWindowTitle("Creating Mod")
        self.progress_dlg.setWindowModality(Qt.ApplicationModal)
        self.progress_dlg.setAutoClose(True)   # closes at 100
        self.progress_dlg.setAutoReset(True)
        self.progress_dlg.setMinimumDuration(0)  # show immediately
        self.progress_dlg.setFixedWidth(600)  # adjust to your liking
        self.progress_dlg.show()

        # spin up the worker
        self.worker = self.WorkerThread(
            MOD_NAME, 
            MOD_FOLDER, 
            replace_3kingdoms=ui.replace_3kingdoms_checkbox.isChecked(),
            canoes_mesoamerican=ui.canoes_mesoamericans_checkbox.isChecked(),
            canoes_sea=ui.canoes_sea_checkbox.isChecked(),
            canoes_other=ui.canoes_other_checkbox.isChecked(),
            parent=self
        )

        self.worker.progress.connect(self.progress_dlg.setValue)
        self.worker.message.connect(self.progress_dlg.setLabelText)
        self.worker.done.connect(self._on_mod_done)

        # optional: allow cancel
        self.progress_dlg.canceled.connect(self.worker.cancel)

        self.worker.start()

    def _on_mod_done(self):
        # Called when the worker signals completion
        # The dialog will auto-close because setAutoClose(True)
        # Do any follow-up UI updates here (e.g., refresh lists)
        print("Mod creation complete!")

    def load_mod(self):
        # Enable app
        self.centralwidget.setEnabled(True)

        # Load the strings
        global MODDED_STRINGS
        MODDED_STRINGS = rf'{MOD_FOLDER}/resources/en/strings/key-value/key-value-modded-strings-utf8.txt'
        global ORIGINAL_STRINGS
        ORIGINAL_STRINGS = rf'{MOD_FOLDER}/resources/en/strings/key-value/key-value-strings-utf8.txt'
        global MOD_NAME
        MOD_NAME = MOD_FOLDER.split(r'/')[-1]
        self.setWindowTitle(f"Talofa - {MOD_NAME}")

        # Create the civ class
        class Civ:
            def __init__(self, data_index, talofa_index, name, description, tech_tree_index, team_bonus_index, scout_unit_index, castle_unit_effect_index, imperial_unit_effect_index, language, unique_techs, graphics):
                self.data_index = data_index
                self.talofa_index = talofa_index
                self.name = name
                self.description = description
                self.tech_tree_index = tech_tree_index
                self.team_bonus_index = team_bonus_index
                self.scout_unit_index = scout_unit_index
                self.language = language
                self.unique_techs = unique_techs
                self.graphics = graphics
                self.castle_unit_effect_index = castle_unit_effect_index
                self.imperial_unit_effect_index = imperial_unit_effect_index

        def get_unit_name(unit_id):
            with open(ORIGINAL_STRINGS, 'r', encoding='utf-8') as file:
                lines = file.readlines()

                # Look for the unit's name
                try:
                    for line in lines:
                        if str(DATA.civs[1].units[unit_id].language_dll_name) in line:
                            new_name = re.sub(r'^\d+\s+', '', line)
                            
                            # Return nothing if the language dll name is 0
                            if DATA.civs[1].units[unit_id].language_dll_name == 0:
                                new_name = ''
                            return new_name.strip('"')[:-2]
                except:
                    return 'NOT_FOUND^'
                    
        def get_unit_id(name, list_ids):
            name = name.strip().lower()
            names = {name}

            # Proper singular/plural variants
            if name.endswith('ies'):  # e.g., "bodies" -> "body"
                names.add(name[:-3] + 'y')
            if name.endswith('s') and len(name) > 1:  # "archers" -> "archer"
                names.add(name[:-1])
            if 'men' in name:  # "spearmen" -> "spearman"
                names.add(name.replace('men', 'man'))

            final_ids = []

            # Primary search in unit.name
            for i, unit in enumerate(DATA.civs[1].units):
                try:
                    if getattr(unit, 'name', '').strip().lower() in names:
                        if i == 778:  # Skip specific units
                            continue
                        if list_ids:
                            final_ids.append(i)
                        else:
                            return i
                except:
                    pass

            # Fallback: search in ORIGINAL_STRINGS file
            string_ids = []
            with open(ORIGINAL_STRINGS, 'r', encoding='utf-8') as file:
                for line in file:
                    for n in names:
                        if f'"{n}"' in line.lower():
                            match = re.match(r'\d+', line)
                            if match:
                                string_ids.append(match.group())

            for i, unit in enumerate(DATA.civs[1].units):
                try:
                    if str(unit.language_dll_name) in string_ids:
                        if i == 778:
                            continue
                        if list_ids:
                            final_ids.append(i)
                        else:
                            return i
                except:
                    pass

            return list(set(final_ids))
        
        # Remove diacritics method
        def remove_diacritics(text: str) -> str:
            normalized = unicodedata.normalize("NFD", text)
            no_diacritics = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
            return no_diacritics.casefold()
        
        def parse_unique_techs(description: str):
            techs = []

            # Split into lines (the description uses "\n")
            lines = description.split("\\n")

            inside_unique = False
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Look for start of unique techs section
                if "<b>Unique Techs:<b>" in line:
                    inside_unique = True
                    continue

                # Stop once we reach another <b> section (like Team Bonus)
                if inside_unique and line.startswith("<b>"):
                    break

                # Collect bullet lines after "Unique Techs"
                if inside_unique and line.startswith("•"):
                    clean_line = line.replace("•", "").strip()
                    parts = clean_line.split("(")

                    tech_name = parts[0].strip()
                    tech_description = ""
                    if len(parts) > 1:
                        tech_description = "(".join(parts[1:]).strip()
                        if tech_description.endswith(")"):
                            tech_description = tech_description[:-1]

                    techs.append(f"{tech_name}|{tech_description}")

            return techs
        
        # Update graphics
        global GRAPHICS_GENERAL
        global GRAPHICS_CASTLE
        global GRAPHICS_WONDER
        global GRAPHICS_MONK
        global GRAPHICS_MONASTERY
        global GRAPHICS_TRADECART
        global GRAPHICS_SHIPS
        GRAPHICS_GENERAL = {'South Indian': 55, 'Caucasian': 54,'Southeast European': 47, 'Mesopotamian': 46, 'Austronesian': 29, 'Byzantines': 7, 'Central Asian': 33, 'Central European': 4, 'East Asian': 5, 'Eastern European': 23, 'Mediterranean': 14, 'Mesoamerican': 15, 'Middle Eastern': 9, 'South Asian': 20, 'Southeast Asian': 28, 'West African': 26, 'Western European': 1}
        GRAPHICS_CASTLE = {'Greek': 47, 'Mesopotamian': 46,'Armenians': 44, 'Aztecs': 15, 'Bengalis': 41, 'Berbers': 27, 'Bohemians': 39, 'Britons': 1, 'Bulgarians': 32, 'Burgundians': 36, 'Burmese': 30, 'Byzantines': 7, 'Celts': 13, 'Chinese': 6, 'Cumans': 34, 'Dravidians': 40, 'Ethiopians': 25, 'Franks': 2, 'Georgians': 45, 'Goths': 3, 'Gurjaras': 42, 'Hindustanis': 20, 'Huns': 17, 'Inca': 21, 'Italians': 19, 'Japanese': 5, 'Jurchens': 52, 'Khitan': 53, 'Khmer': 28, 'Koreans': 18, 'Lithuanians': 35, 'Magyars': 22, 'Malay': 29, 'Malians': 26, 'Maya': 16, 'Mongols': 12, 'Persians': 8, 'Poles': 38, 'Portuguese': 24, 'Romans': 43, 'Saracens': 9, 'Shu': 49, 'Sicilians': 37, 'Slavs': 23, 'Spanish': 14, 'Tatars': 33, 'Teutons': 4, 'Turks': 10, 'Vikings': 11, 'Vietnamese': 31, 'Wei': 51, 'Wu': 50}
        GRAPHICS_WONDER = {'Athenians': 47, 'Spartans': 47, 'Achaemenids': 46,'Armenians': 44, 'Aztecs': 15, 'Bengalis': 41, 'Berbers': 27, 'Bohemians': 39, 'Britons': 1, 'Bulgarians': 32, 'Burgundians': 36, 'Burmese': 30, 'Byzantines': 7, 'Celts': 13, 'Chinese': 6, 'Cumans': 34, 'Dravidians': 40, 'Ethiopians': 25, 'Franks': 2, 'Georgians': 45, 'Goths': 3, 'Gurjaras': 42, 'Hindustanis': 20, 'Huns': 17, 'Inca': 21, 'Italians': 19, 'Japanese': 5, 'Jurchens': 52, 'Khitan': 53, 'Khmer': 28, 'Koreans': 18, 'Lithuanians': 35, 'Magyars': 22, 'Malay': 29, 'Malians': 26, 'Maya': 16, 'Mongols': 12, 'Persians': 8, 'Poles': 38, 'Portuguese': 24, 'Romans': 43, 'Saracens': 9, 'Shu': 49, 'Sicilians': 37, 'Slavs': 23, 'Spanish': 14, 'Tatars': 33, 'Teutons': 4, 'Turks': 10, 'Vikings': 11, 'Vietnamese': 31, 'Wei': 51, 'Wu': 50}
        GRAPHICS_MONK = {'African': 25, 'Buddhist': 5, 'Catholic': 14, 'Christian': 0, 'Hindu': 40, 'Mesoamerican': 15, 'Muslim': 9, 'Orthodox': 23, 'Pagan': 35, 'Tengri': 12}
        GRAPHICS_MONASTERY = {'Greek': 47, 'Mesopotamian': 46, 'Byzantines': 7, 'Central Asian': 33, 'Central European': 4, 'East Asian': 5, 'East African': 25, 'Eastern European': 23, 'Mediterranean': 14, 'Mesoamerican': 15, 'Middle Eastern': 9, 'Pagan': 35, 'South Asian': 40, 'Southeast Asian': 28, 'Southeast European': 44, 'Tengri': 12, 'West African': 26, 'Western European': 1}
        GRAPHICS_TRADECART = {'Camel': 9, 'Horse': 1, 'Human': 15, 'Ox': 25, 'Water Buffalo': 5}
        GRAPHICS_SHIPS = {'Central Asian': 33, 'Central European': 4, 'East Asian': 5, 'Eastern European': 23, 'Mediterranean': 14, 'Mesoamerican': 15, 'Middle Eastern': 9, 'Southeast Asian': 28, 'West African': 25, 'Western European': 1}

        # Combine all dictionaries
        graphic_sets = [GRAPHICS_GENERAL, GRAPHICS_CASTLE, GRAPHICS_WONDER, GRAPHICS_MONK, GRAPHICS_MONASTERY, GRAPHICS_TRADECART, GRAPHICS_SHIPS]

        # Add graphics
        def populate_dropdown_from_dict(dropdown, data_dict):
            dropdown.clear()
            for name, value in sorted(data_dict.items(), key=lambda x: x[0]):  # sort by name
                dropdown.addItem(name, userData=value)

        # Fill each dropdown
        populate_dropdown_from_dict(self.dropdown_general_graphics, GRAPHICS_GENERAL)
        populate_dropdown_from_dict(self.dropdown_castle_graphics, GRAPHICS_CASTLE)
        populate_dropdown_from_dict(self.dropdown_wonder_graphics, GRAPHICS_WONDER)
        populate_dropdown_from_dict(self.dropdown_monk_graphics, GRAPHICS_MONK)
        populate_dropdown_from_dict(self.dropdown_monastery_graphics, GRAPHICS_MONASTERY)
        populate_dropdown_from_dict(self.dropdown_tradecart_graphics, GRAPHICS_TRADECART)
        populate_dropdown_from_dict(self.dropdown_ships_graphics, GRAPHICS_SHIPS)

        # Load architecture sets
        global ARCHITECTURE_SETS
        ARCHITECTURE_SETS = []
        try:
            with open(f"{MOD_FOLDER}/{MOD_NAME}.pkl", "rb") as file:
                while True:
                    try:
                        units = pickle.load(file)
                        ARCHITECTURE_SETS.append(units)
                    except EOFError:
                        break
        except FileNotFoundError:
            print(f"[ERROR] Could not find architecture pickle: {MOD_FOLDER}/{MOD_NAME}.pkl")

        # Load all current civs
        global CIVS
        CIVS = []
        for i, civ in enumerate(DATA.civs):
            # Skip specific civs
            global DISABLED_CIVS
            DISABLED_CIVS = ['gaia', 'athenians', 'achaemenids', 'spartans']
            if civ.name.lower() in DISABLED_CIVS:
                talofa_index = i
                continue

            # Get the total amount of civs
            global TOTAL_CIVS_COUNT
            TOTAL_CIVS_COUNT = len(DATA.civs) - len(DISABLED_CIVS)

            # Create new civ object
            new_civ = Civ(i, talofa_index, '', '', -1, -1, int(civ.resources[263]), -1, -1, '', [], [])

            # Get the stats for the civ
            with open(MODDED_STRINGS, 'r') as file:
                lines = file.readlines()
                name_index = None

                for line_index, line in enumerate(lines):
                    # Look for an exact match in quotes
                    pattern = f'"{civ.name}"'
                    if pattern.lower() in remove_diacritics(line.lower()):
                        new_civ.name = line.split('"')[1].strip()
                        name_index = line_index

                    elif 'unique techs:' in line.lower():
                        techs = []
                        offset = 1
                        while line_index + offset < len(lines):
                            next_line = lines[line_index + offset].strip()
                            # stop if we reach blank or next <b> section
                            if not next_line or next_line.lower().startswith("<b>"):
                                break

                            if next_line.startswith('•'):
                                clean_line = next_line.replace('•', '').strip()
                                parts = clean_line.split('(')

                                # name = before '('
                                tech_name = parts[0].strip()

                                # description = everything else, minus last ')'
                                if len(parts) > 1:
                                    tech_description = "(".join(parts[1:]).strip()
                                    if tech_description.endswith(")"):
                                        tech_description = tech_description[:-1]
                                else:
                                    tech_description = ""

                                techs.append(f"{tech_name}|{tech_description}")
                            offset += 1

                        new_civ.unique_techs = techs

                if name_index is not None:
                    if name_index + TOTAL_CIVS_COUNT < len(lines):
                        new_civ.description = lines[name_index + TOTAL_CIVS_COUNT + len(DISABLED_CIVS) - 1].split('"')[1].strip()

                        # Parse unique techs from description
                        new_civ.unique_techs = parse_unique_techs(new_civ.description)

            # Get the tech tree, team bonus, castle unit, and imperial unit
            for effect_index, effect in enumerate(DATA.effects):
                if effect.name.lower() == f'{civ.name.lower()} tech tree':
                    new_civ.tech_tree_index = effect_index
                elif effect.name.lower() == f'{civ.name.lower()} team bonus':
                    new_civ.team_bonus_index = effect_index
                elif effect.name.lower() == f'{civ.name.lower()}: (castle unit)':
                    new_civ.castle_unit_effect_index = effect_index
                elif effect.name.lower() == f'{civ.name.lower()}: (imperial unit)':
                    new_civ.imperial_unit_effect_index = effect_index

            # Get the language
            for sound_item in DATA.sounds[303].items:
                if sound_item.civilization == new_civ.data_index:
                    new_civ.language = sound_item.filename.split('_')[0]

            # Sort each dictionary by key alphabetically
            graphic_sets = [dict(sorted(g.items())) for g in graphic_sets]

            # Get current graphics
            global UNIT_BANK
            UNIT_BANK = {0: range(0, len(DATA.civs[1].units)), 1: [82, 1430], 2: [276, 1445], 3: [125, 286, 922, 1025, 1327], 4: [30, 31, 32, 104, 1421], 5: [128, 204], 6: [1103, 529, 532, 545, 17, 420, 691, 1104, 527, 528, 539, 21, 442]}
            current_graphics = [''] * len(UNIT_BANK.items())

            # Scan the units for their graphics
            for i, graphic_set in enumerate(graphic_sets):
                try:
                    # Select the unit to test
                    test_unit = UNIT_BANK[i][0] if i > 0 else 463

                    for key, value in graphic_set.items():
                        if DATA.civs[new_civ.data_index].units[test_unit].standing_graphic == ARCHITECTURE_SETS[value][test_unit].standing_graphic:
                            current_graphics[i] = value
                            break
                except Exception as e:
                    pass

            new_civ.graphics = current_graphics

            # Add the civ to the list
            CIVS.append(new_civ)

        # Populate civ dropdown
        self.dropdown_civ_name.clear()
        for civ in CIVS:
            self.dropdown_civ_name.addItem(civ.name)

        # Populate language dropdown FIRST
        self.dropdown_language.clear()
        sound_folder = f'{MOD_FOLDER}/resources/_common/drs/sounds'

        languages = set()
        for filename in os.listdir(sound_folder):
            file_path = os.path.join(sound_folder, filename)
            if not os.path.isfile(file_path):
                continue
            parts = filename.split('_')
            if len(parts) < 3:
                continue
            languages.add(parts[0])

        languages = sorted(languages)
        self.dropdown_language.addItems(languages)

        # Populate scout unit dropdown
        self.dropdown_scout_units.clear()
        self.dropdown_scout_units.addItem("Scout Cavalry", userData=448)
        self.dropdown_scout_units.addItem("Eagle Scout", userData=751)
        self.dropdown_scout_units.addItem("Camel Scout", userData=1755)

        # Populate unique unit dropdown
        global ALL_CASTLE_UNITS
        ALL_CASTLE_UNITS = ["longbowman", "throwing axeman", "berserk", "teutonic knight", "samurai", "chu ko nu", "cataphract", "war elephant", "mameluke", "janissary", "huskarl", "mangudai", "woad raider", "conquistador", "jaguar warrior", "plumed archer", "tarkan", "war wagon", "genoese crossbowman", "ghulam", "kamayuk", "magyar huszar", "boyar", "organ gun", "shotel warrior", "gbeto", "camel archer", "ballista elephant", "karambit warrior", "arambai", "rattan archer", "konnik", "keshik", "kipchak", "leitis", "coustillier", "serjeant", "obuch", "hussite wagon", "urumi swordsman", "ratha (melee)", "chakram thrower", "centurion", "composite bowman", "monaspa", 'iron pagoda', 'liao dao', 'white feather guard', 'tiger cavalry', 'fire archer', "amazon warrior", "amazon archer", "qizilbash warrior", 'genitour', 'naasiri', 'elephant gunner', 'flamethrower', 'weichafe', 'destroyer', 'lightning warrior', 'cossack']
        # "crusader", "tomahawk warrior", "ninja", "scimitar warrior", "drengr",
        self.dropdown_unique_units.clear()
        for unit_name in ALL_CASTLE_UNITS:
            unique_units_ids = f'{get_unit_id(unit_name, False)}|{get_unit_id(f'elite {unit_name}', False)}'
            self.dropdown_unique_units.addItem(unit_name.title(), userData=unique_units_ids)

        # Populate graphics dropdowns
        self.dropdown_general_graphics.clear()
        for name, value in GRAPHICS_GENERAL.items():
            self.dropdown_general_graphics.addItem(name, userData=value)

        self.dropdown_castle_graphics.clear()
        for name, value in GRAPHICS_CASTLE.items():
            self.dropdown_castle_graphics.addItem(name, userData=value)

        self.dropdown_wonder_graphics.clear()
        for name, value in GRAPHICS_WONDER.items():
            self.dropdown_wonder_graphics.addItem(name, userData=value)

        self.dropdown_monk_graphics.clear()
        for name, value in GRAPHICS_MONK.items():
            self.dropdown_monk_graphics.addItem(name, userData=value)

        self.dropdown_monastery_graphics.clear()
        for name, value in GRAPHICS_MONASTERY.items():
            self.dropdown_monastery_graphics.addItem(name, userData=value)

        self.dropdown_tradecart_graphics.clear()
        for name, value in GRAPHICS_TRADECART.items():
            self.dropdown_tradecart_graphics.addItem(name, userData=value)

        self.dropdown_ships_graphics.clear()
        for name, value in GRAPHICS_SHIPS.items():
            self.dropdown_ships_graphics.addItem(name, userData=value)

        # Connect signals
        self.dropdown_civ_name.currentIndexChanged.connect(self.dropdown_civ_name_changed)
        self.dropdown_language.currentIndexChanged.connect(self.dropdown_language_changed)
        self.dropdown_scout_units.currentIndexChanged.connect(self.dropdown_scout_unit_changed)
        self.dropdown_unique_units.currentIndexChanged.connect(self.dropdown_unique_units_changed)
        self.dropdown_general_graphics.currentIndexChanged.connect(
            lambda: self.graphics_dropdown_changed(self.dropdown_general_graphics, 0)
        )
        self.dropdown_castle_graphics.currentIndexChanged.connect(
            lambda: self.graphics_dropdown_changed(self.dropdown_castle_graphics, 1)
        )
        self.dropdown_wonder_graphics.currentIndexChanged.connect(
            lambda: self.graphics_dropdown_changed(self.dropdown_wonder_graphics, 2)
        )
        self.dropdown_monk_graphics.currentIndexChanged.connect(
            lambda: self.graphics_dropdown_changed(self.dropdown_monk_graphics, 3)
        )
        self.dropdown_monastery_graphics.currentIndexChanged.connect(
            lambda: self.graphics_dropdown_changed(self.dropdown_monastery_graphics, 4)
        )
        self.dropdown_tradecart_graphics.currentIndexChanged.connect(
            lambda: self.graphics_dropdown_changed(self.dropdown_tradecart_graphics, 5)
        )
        self.dropdown_ships_graphics.currentIndexChanged.connect(
            lambda: self.graphics_dropdown_changed(self.dropdown_ships_graphics, 6)
        )

        # Run once at startup
        self.dropdown_civ_name_changed(self.dropdown_civ_name.currentIndex())

    def save_mod(self):
        if MOD_FOLDER and '*' in self.windowTitle():
            print('Saving mod...')
            DATA.save(rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat')
            print('Mod saved!')

            # Change the name in the strings
            with open(MODDED_STRINGS, 'r+', encoding='utf-8') as file:
                lines = file.readlines()  # Read all lines
                for i, line in enumerate(lines):
                    try:
                        lines[i] = lines[i][:5] + f' "{CIVS[i].name}"\n'  # Modify the specific line
                    except:
                        break

                file.seek(0)  # Move to the beginning of the file
                file.writelines(lines)  # Write all lines back

            # Remove save asterisk
            self.setWindowTitle(self.windowTitle().replace('*', ''))

    def new_mod(self):
        pass

    def open_mod(self):
        # Get mod location
        global MOD_FOLDER
        MOD_FOLDER = r'/home/xommon/snap/steam/common/.local/share/Steam/steamapps/compatdata/813780/pfx/drive_c/users/steamuser/Games/Age of Empires 2 DE/76561198021486964/mods/local/Test'

        # Load the mod
        print('Loading file...')
        global DATA
        DATA = DatFile.parse(rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat')
        print('Mod loaded!')
        self.load_mod()

    def _apply_civ_rename(self, civ_pos, civ_data_index, old_name, new_name):
        # Update civ data
        DATA.civs[civ_data_index].name = new_name
        CIVS[civ_pos].name = new_name

        # Update dropdown without changing selection
        self.dropdown_civ_name.blockSignals(True)
        self.dropdown_civ_name.setItemText(civ_pos, new_name)
        self.dropdown_civ_name.blockSignals(False)

        # If this civ is selected, update input field
        if self.dropdown_civ_name.currentIndex() == civ_pos:
            self.input_civ_name.setText(new_name)

        # Update effects
        for effect in DATA.effects:
            if effect.name == f'{old_name} Tech Tree':
                effect.name = f'{new_name} Tech Tree'
            elif effect.name == f'{old_name} Team Bonus':
                effect.name = f'{new_name} Team Bonus'
            elif f'{old_name.upper()}' in effect.name:
                parts = effect.name.split(':')
                parts[0] = new_name.upper()
                effect.name = ':'.join(parts)

        # Update techs
        for tech in DATA.techs:
            if f'{old_name.upper()}' in tech.name:
                parts = tech.name.split(':')
                parts[0] = new_name.upper()
                tech.name = ':'.join(parts)

        # Mark dirty
        if not self.windowTitle().endswith('*'):
            self.setWindowTitle(self.windowTitle() + '*')

    def _apply_title_change(self, civ, old_title, new_title):
        # Update civ object
        desc_lines = civ.description.split('\\n')
        if not desc_lines:
            return
        desc_lines[0] = new_title
        civ.description = '\\n'.join(desc_lines)

        # Build HTML version
        description_html = civ.description.replace("\\n", "<br>").replace("\n", "<br>")

        # Convert toggle <b> into paired <b>...</b>
        parts = description_html.split("<b>")
        rebuilt, bold_on = [], False
        for part in parts:
            rebuilt.append(f"<b>{part}</b>" if bold_on else part)
            bold_on = not bold_on
        description_html = "".join(rebuilt)

        # Refresh UI if this civ is currently selected
        if self.dropdown_civ_name.currentIndex() == civ.talofa_index:
            self.textbox_description.setTextFormat(QtCore.Qt.RichText)
            self.textbox_description.setText(description_html)
            self.input_title.setText(new_title)

        # Mark window as dirty (unsaved changes)
        if not self.windowTitle().endswith('*'):
            self.setWindowTitle(self.windowTitle() + '*')

    def _apply_language_change(self, civ_index, sound_ids, old_lang, new_lang):
        # Update filenames
        for sound_id in sound_ids:
            for item in DATA.sounds[sound_id].items:
                if item.civilization == civ_index:
                    parts = item.filename.split('_')
                    if parts:
                        parts[0] = new_lang
                        item.filename = '_'.join(parts)

        # Update CURRENT_CIV.language if it's the civ being modified
        for civ in CIVS:
            if civ.data_index == civ_index:
                civ.language = new_lang
                # If it's the civ currently displayed, refresh dropdown
                if civ is CURRENT_CIV:
                    self.dropdown_language.blockSignals(True)
                    self.dropdown_language.setCurrentText(new_lang)
                    self.dropdown_language.blockSignals(False)
                break

        # Mark unsaved changes
        if not self.windowTitle().endswith('*'):
            self.setWindowTitle(self.windowTitle() + '*')

    def _apply_scout_unit_change(self, civ_index, old_value, new_value):
        # Update the data file
        DATA.civs[civ_index].resources[263] = int(new_value)

        # Update CURRENT_CIV if it matches
        if CURRENT_CIV.data_index == civ_index:
            CURRENT_CIV.scout_unit_index = int(new_value)  # optional, if you track this field
            # Update dropdown without firing signal
            self.dropdown_scout_units.blockSignals(True)
            self.dropdown_scout_units.setCurrentIndex(
                self.dropdown_scout_units.findData(new_value)
            )
            self.dropdown_scout_units.blockSignals(False)

        # Mark unsaved changes
        if not self.windowTitle().endswith("*"):
            self.setWindowTitle(self.windowTitle() + "*")

    def _apply_unique_unit_change(self, civ_data_index, old_value, new_value):
        # Unpack tuple
        castle_id, imperial_id, imperial_upgrade = new_value

        # ✅ Find civ object by data_index, not by assuming position
        civ = next((c for c in CIVS if c.data_index == civ_data_index), None)
        if civ is None:
            return  # safety guard

        # ✅ Apply to DATA effects
        DATA.effects[civ.castle_unit_effect_index].effect_commands[0].a = castle_id
        DATA.effects[civ.imperial_unit_effect_index].effect_commands[0].a = imperial_id
        DATA.effects[civ.imperial_unit_effect_index].effect_commands[0].b = imperial_upgrade

        # ✅ If CURRENT_CIV is the one being modified, update & refresh dropdown
        if CURRENT_CIV.data_index == civ_data_index:
            CURRENT_CIV.unique_unit_index = castle_id

            uu_key = f"{castle_id}|{imperial_upgrade}"
            idx = self.dropdown_unique_units.findData(uu_key)
            if idx >= 0:
                self.dropdown_unique_units.blockSignals(True)
                self.dropdown_unique_units.setCurrentIndex(idx)
                self.dropdown_unique_units.blockSignals(False)

        # ✅ Refresh UI if this civ is currently selected
        if self.dropdown_civ_name.currentIndex() == civ.talofa_index:
            self.dropdown_civ_name_changed(civ.talofa_index)

        # ✅ Mark as unsaved
        if not self.windowTitle().endswith("*"):
            self.setWindowTitle(self.windowTitle() + "*")

    def _apply_general_graphics_change(self, civ_index, old_value, new_value):
        # Replace unit graphics with those from the chosen architecture set
        for unit_id, unit in enumerate(DATA.civs[civ_index].units):
            if unit_id not in [item for key in sorted(UNIT_BANK) if key >= 1 for item in UNIT_BANK[key]]:
                DATA.civs[civ_index].units[unit_id] = ARCHITECTURE_SETS[new_value][unit_id]

        # Update CURRENT_CIV if needed
        if CURRENT_CIV.data_index == civ_index:
            CURRENT_CIV.graphics[0] = new_value
            # Refresh dropdown without firing signal
            self.dropdown_general_graphics.blockSignals(True)
            idx = self.dropdown_general_graphics.findData(new_value)
            if idx >= 0:
                self.dropdown_general_graphics.setCurrentIndex(idx)
            self.dropdown_general_graphics.blockSignals(False)

        # Mark unsaved changes
        if not self.windowTitle().endswith("*"):
            self.setWindowTitle(self.windowTitle() + "*")

    def change_name(self):
        old_name = CURRENT_CIV.name
        new_name = self.input_civ_name.text()

        if (old_name.lower() == new_name.lower()
            or any(civ.name.lower() == new_name.lower() for civ in CIVS)):
            self.input_civ_name.setText(old_name)
            return

        civ_pos = self.dropdown_civ_name.currentIndex()
        civ_data_index = CURRENT_CIV.data_index

        cmd = RenameCivCommand(self, civ_pos, civ_data_index, old_name, new_name)
        self.undoStack.push(cmd)

    def change_title(self):
        desc_lines = CURRENT_CIV.description.split('\\n')
        old_title = desc_lines[0].strip()
        new_title = self.input_title.text().strip()
        desc_lines[0] = new_title
        new_description = '\\n'.join(desc_lines)

        if old_title == new_title:
            return

        # Push to undo stack
        cmd = ChangeTitleCommand(self, CURRENT_CIV, old_title, new_title)
        self.undoStack.push(cmd)

        # Update the civ object
        CURRENT_CIV.description = new_description

        # Build HTML version
        description_html = CURRENT_CIV.description.replace("\\n", "<br>").replace("\n", "<br>")

        # Convert toggle <b> into paired <b>...</b>
        parts = description_html.split("<b>")
        rebuilt, bold_on = [], False
        for part in parts:
            rebuilt.append(f"<b>{part}</b>" if bold_on else part)
            bold_on = not bold_on
        description_html = "".join(rebuilt)

        # Update description text box
        self.textbox_description.setTextFormat(QtCore.Qt.RichText)
        self.textbox_description.setText(description_html)

        # Update title text box
        self.input_title.setText(new_title)

    def graphics_dropdown_changed(self, dropdown, category_index):
        civ_index = CURRENT_CIV.data_index
        model_civ_index = dropdown.currentData()

        # Decide which units to affect
        if category_index == 0:
            # General: everything except units in other banks
            excluded = [item for key, val in UNIT_BANK.items() if key >= 1 for item in val]
            affected_units = [uid for uid in range(len(DATA.civs[civ_index].units)) if uid not in excluded]
        else:
            affected_units = UNIT_BANK.get(category_index, [])

        old_units, new_units = {}, {}
        for uid in affected_units:
            try:
                old_unit = DATA.civs[civ_index].units[uid]
                new_unit = ARCHITECTURE_SETS[model_civ_index][uid]
                # Only include if both have a valid standing_graphic
                if getattr(old_unit, "standing_graphic", None) is not None and getattr(new_unit, "standing_graphic", None) is not None:
                    old_units[uid] = copy.deepcopy(old_unit)
                    new_units[uid] = copy.deepcopy(new_unit)
            except Exception:
                continue  # skip invalid units safely

        if not old_units:
            return  # nothing valid to change

        # If all are identical already, skip
        if all(old_units[uid].standing_graphic == new_units[uid].standing_graphic for uid in old_units):
            return

        cmd = ChangeGraphicsCommand(self, civ_index, category_index, old_units, new_units)
        self.undoStack.push(cmd)

    def dropdown_language_changed(self):
        sound_ids = [303, 301, 295, 299, 455, 448, 297, 298, 300, 302,
                    435, 434, 437, 442, 438, 487, 440, 441, 443, 444,
                    420, 421, 422, 423, 424, 479, 480]

        old_lang = None
        civ_index = CURRENT_CIV.data_index

        # Peek at the current language prefix from one of the civ's sounds
        for sound_id in sound_ids:
            for item in DATA.sounds[sound_id].items:
                if item.civilization == civ_index:
                    old_lang = item.filename.split('_')[0]
                    break
            if old_lang:
                break

        new_lang = self.dropdown_language.currentText()

        if old_lang == new_lang:
            return

        cmd = ChangeLanguageCommand(self, civ_index, sound_ids, old_lang, new_lang)
        self.undoStack.push(cmd)

    def dropdown_scout_unit_changed(self):
        civ_index = CURRENT_CIV.data_index
        old_value = CURRENT_CIV.scout_unit_index
        new_value = int(self.dropdown_scout_units.currentData())


        if old_value == new_value:
            return

        cmd = ChangeScoutUnitCommand(self, civ_index, old_value, new_value)
        self.undoStack.push(cmd)

    def dropdown_civ_name_changed(self, index):
        # Get current civ
        global CURRENT_CIV
        CURRENT_CIV = CIVS[index]

        description_html = CURRENT_CIV.description.replace("\\n", "<br>").replace("\n", "<br>")

        # Convert toggle <b> into paired <b>...</b>
        parts = description_html.split("<b>")
        rebuilt, bold_on = [], False
        for part in parts:
            rebuilt.append(f"<b>{part}</b>" if bold_on else part)
            bold_on = not bold_on
        description_html = "".join(rebuilt)

        # Update icon
        icon_file_name = CURRENT_CIV.name.lower()
        icon_names = ['gaia', 'britons', 'franks', 'goths', 'teutons', 'japanese', 'chinese', 'byzantines', 'persians', 'saracens', 'turks', 'vikings', 'mongols', 'celts', 'spanish', 'aztecs', 'mayans', 'huns', 'koreans', 'italians', 'indians', 'inca', 'magyars', 'slavs', 'portuguese', 'ethiopians', 'malians', 'berber', 'khmer', 'malay', 'burmese', 'vietnamese', 'bulgarians', 'tatars', 'cumans', 'lithuanians', 'burgundians', 'sicilians', 'poles', 'bohemians', 'dravidians', 'bengalis', 'gurjaras', 'romans', 'armenians', 'georgians', 'achaemenids', 'athenians', 'spartans', 'shu', 'wu', 'wei', 'jurchens', 'khitans']
        self.image_civ_icon.setPixmap(QtGui.QPixmap(f'{MOD_FOLDER}/resources/_common/wpfg/resources/civ_techtree/menu_techtree_{icon_names[CURRENT_CIV.data_index]}.png'))

        # Update description text box
        self.textbox_description.setText(description_html)

        # Update title text box
        self.input_title.setText(self.textbox_description.text().split('<br>')[0])

        # Update name text box
        self.input_civ_name.setText(CURRENT_CIV.name)

        # Update language dropdown safely
        lang = CURRENT_CIV.language or ""
        i = self.dropdown_language.findText(lang, QtCore.Qt.MatchFixedString)
        self.dropdown_language.blockSignals(True)
        if i >= 0:
            self.dropdown_language.setCurrentIndex(i)
        else:
            if lang:
                self.dropdown_language.addItem(lang)
                self.dropdown_language.setCurrentIndex(self.dropdown_language.count() - 1)
        self.dropdown_language.blockSignals(False)

        # Update scout unit
        value = int(DATA.civs[CURRENT_CIV.data_index].resources[263])
        su_index = self.dropdown_scout_units.findData(value)
        if su_index > -1:
            self.dropdown_scout_units.blockSignals(True)
            self.dropdown_scout_units.setCurrentIndex(su_index)
            self.dropdown_scout_units.blockSignals(False)

        # Update unique unit
        uu_ec = DATA.effects[CURRENT_CIV.imperial_unit_effect_index].effect_commands[0]
        value = f'{uu_ec.a}|{uu_ec.b}'
        uu_index = self.dropdown_unique_units.findData(value)
        if uu_index > -1: 
            self.dropdown_unique_units.blockSignals(True)
            self.dropdown_unique_units.setCurrentIndex(uu_index)
            self.dropdown_unique_units.blockSignals(False)

        # Update unique techs
        try:
            self.input_castle_tech_name.setText(CURRENT_CIV.unique_techs[0].split('|')[0])
            self.input_castle_tech_description.setText(CURRENT_CIV.unique_techs[0].split('|')[1])
            self.input_imperial_tech_name.setText(CURRENT_CIV.unique_techs[1].split('|')[0])
            self.input_imperial_tech_description.setText(CURRENT_CIV.unique_techs[1].split('|')[1])
        except Exception:
            print("Error loading unique techs")

        # Define which test unit corresponds to each category
        self.dropdown_general_graphics.setCurrentIndex(
            self.dropdown_general_graphics.findData(CURRENT_CIV.graphics[0])
        )
        self.dropdown_castle_graphics.setCurrentIndex(
            self.dropdown_castle_graphics.findData(CURRENT_CIV.graphics[1])
        )
        self.dropdown_wonder_graphics.setCurrentIndex(
            self.dropdown_wonder_graphics.findData(CURRENT_CIV.graphics[2])
        )
        self.dropdown_monk_graphics.setCurrentIndex(
            self.dropdown_monk_graphics.findData(CURRENT_CIV.graphics[3])
        )
        self.dropdown_monastery_graphics.setCurrentIndex(
            self.dropdown_monastery_graphics.findData(CURRENT_CIV.graphics[4])
        )
        self.dropdown_tradecart_graphics.setCurrentIndex(
            self.dropdown_tradecart_graphics.findData(CURRENT_CIV.graphics[5])
        )
        self.dropdown_ships_graphics.setCurrentIndex(
            self.dropdown_ships_graphics.findData(CURRENT_CIV.graphics[6])
        )

        '''unit_bank = {
            0: [463],  # General (use Villager or similar)
            1: [82, 1430],  # Castle
            2: [276, 1445],  # Wonder
            3: [125, 286, 922, 1025, 1327],  # Monk
            4: [30, 31, 32, 104, 1421],  # Monastery
            5: [128, 204],  # Trade Cart
            6: [1103, 529, 532, 545, 17, 420, 691, 1104, 527, 528, 539, 21, 442],  # Ships
        }

        dropdowns = [
            self.dropdown_general_graphics,
            self.dropdown_castle_graphics,
            self.dropdown_wonder_graphics,
            self.dropdown_monk_graphics,
            self.dropdown_monastery_graphics,
            self.dropdown_tradecart_graphics,
            self.dropdown_ships_graphics
        ]

        graphic_dicts = [
            GRAPHICS_GENERAL,
            GRAPHICS_CASTLE,
            GRAPHICS_WONDER,
            GRAPHICS_MONK,
            GRAPHICS_MONASTERY,
            GRAPHICS_TRADECART,
            GRAPHICS_SHIPS
        ]

        for i, (dropdown, gdict) in enumerate(zip(dropdowns, graphic_dicts)):
            try:
                test_unit = unit_bank[i][0]
                current_graphic = DATA.civs[CURRENT_CIV.data_index].units[test_unit].standing_graphic

                # Find which entry in gdict matches
                for name, value in gdict.items():
                    if DATA.civs[CURRENT_CIV.data_index].units[test_unit].standing_graphic == ARCHITECTURE_SETS[value][test_unit].standing_graphic:
                        target_value = value
                        break
                else:
                    target_value = None

                # Update dropdown selection
                if target_value is not None:
                    idx = dropdown.findData(target_value)
                    if idx >= 0:
                        dropdown.blockSignals(True)
                        dropdown.setCurrentIndex(idx)
                        dropdown.blockSignals(False)
            except Exception as e:
                etype, evalue, etb = sys.exc_info()
                print(f"[ERROR] {etype.__name__}: {e}")
                print("".join(traceback.format_exception(etype, evalue, etb)))'''

    def dropdown_unique_units_changed(self):
        civ_index = CURRENT_CIV.data_index

        # Old values from DATA
        old_castle = DATA.effects[CURRENT_CIV.castle_unit_effect_index].effect_commands[0].a
        old_imperial = DATA.effects[CURRENT_CIV.imperial_unit_effect_index].effect_commands[0].a
        old_upgrade = DATA.effects[CURRENT_CIV.imperial_unit_effect_index].effect_commands[0].b
        old_value = (old_castle, old_imperial, old_upgrade)

        # New values from dropdown
        unique_units_ids = self.dropdown_unique_units.currentData().split('|')
        castle_id = int(unique_units_ids[0])
        elite_id = int(unique_units_ids[1])
        new_value = (castle_id, castle_id, elite_id)   # imperial unit starts as same as castle

        if old_value == new_value:
            return

        cmd = ChangeUniqueUnitCommand(self, civ_index, old_value, new_value)
        self.undoStack.push(cmd)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())

