# Micheal Quentin
# 02. March 2025
# 2025 Civilisation Creator

'''
# Advanced Genie Editor
wine /home/xommon/snap/steam/common/.local/share/Steam/steamapps/common/AoE2DE/Tools_Builds/AdvancedGenieEditor3.exe

# Test Mod Folder
/home/xommon/snap/steam/common/.local/share/Steam/steamapps/compatdata/813780/pfx/drive_c/users/steamuser/Games/Age of Empires 2 DE/76561198021486964/mods/local/Test

# .DAT File
/home/xommon/snap/steam/common/.local/share/Steam/steamapps/compatdata/813780/pfx/drive_c/users/steamuser/Games/Age of Empires 2 DE/76561198021486964/mods/local/Test/resources/_common/dat/empires2_x2_p1.dat

# Original AOE2DE Foler
/home/xommon/snap/steam/common/.local/share/Steam/steamapps/common/AoE2DE

# Real World Map Folder
/home/xommon/snap/steam/common/.local/share/Steam/steamapps/common/AoE2DE/resources/_common/drs/gamedata_x2

# Scenario Folder
/home/xommon/snap/steam/common/.local/share/Steam/steamapps/compatdata/813780/pfx/drive_c/users/steamuser/Games/Age of Empires 2 DE/76561198021486964/resources/_common/scenario

# Custom Map .RMS
/home/xommon/snap/steam/common/.local/share/Steam/steamapps/common/AoE2DE/resources/_common/random-map-scripts

# Terminal code to show image overlay
python3 overlay.py ~/Documents/central_america.jpg 0.5 350 350
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
import filecmp
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
from genieutils.unit import AttackOrArmor
from genieutils.unit import ResourceCost

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
            # talofa_index stored in Civ objects may be stale — find the current index in CIVS
            try:
                talofa_idx = next(i for i, c in enumerate(CIVS) if c.data_index == self.civ_index)
            except StopIteration:
                talofa_idx = None
            if talofa_idx is not None:
                self.app.dropdown_civ_name_changed(talofa_idx)

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
        self.input_civ_name.returnPressed.connect(self.change_name)
        self.button_icon_left.clicked.connect(lambda: self.button_change_emblem('left'))
        self.button_icon_right.clicked.connect(lambda: self.button_change_emblem('right'))
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

        # Pass methods to worker
        def start_worker(self):
            self.worker = self.WorkerThread(
                mod_name=self.mod_name,
                mod_folder=self.mod_folder,
                replace_3kingdoms=self.replace_3kingdoms,
                canoes_mesoamerican=self.canoes_mesoamerican,
                canoes_sea=self.canoes_sea,
                canoes_other=self.canoes_other,
                parent=self
            )
            self.worker.finished_with_mod.connect(self.open_mod)
            self.worker.start()

    # A worker that runs in background and emits progress ---
    class WorkerThread(QThread):
        progress = pyqtSignal(int)      # 0..100
        message = pyqtSignal(str)       # status text
        done = pyqtSignal()             # finished signal
        finished_with_mod = pyqtSignal(str)  # emit mod folder path when done

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
                ("Preparing Data file", self.open_data_file),
                ("Gathering Architecture Sets", self.gather_architecture_sets),
                ("Creating Settings Files", self.save_settings_files),
                ("Cleaning up JSON files", self.cleanup_json_files),
                ("Setting up Custom Sounds", self.setup_sounds),
                ("Editing Strings", self.edit_strings),
                ("Despecializing Units", self.despecialise_units),
                ("Gathering Tech Trees", self.get_tech_trees),
                ("Creating Talofa Units", self.create_talofa_units),
                ("Creating Talofa Techs", self.create_talofa_techs),
                ("Updating Civilizations for Realism", self.make_civs_more_realistic),
                ("Editing Unique Units", self.edit_unique_units),
                ("Reformatting Bonuses", self.reformat_bonuses),
                ("Tweaking Civilization Graphics", self.tweak_graphics),
                ("Editing Tech Trees", self.edit_tech_trees),
                ("Replacing Three Kingdoms civs", self.replace_3kingdoms_civs),
                ("Reordering Tech Trees", self.reorder_tech_trees),
                ("Finalizing", self.finalize),
            ]

            # use the *instance* flag, not the global
            if not self.replace_3kingdoms:
                steps = [s for s in steps if s[0] != "Replacing Three Kingdoms civs"]

            total = len(steps)

            for i, (label, func) in enumerate(steps, start=1):
                if self._cancel:
                    return

                self.message.emit(label)

                try:
                    func()  # Run one step
                except Exception as e:
                    import traceback
                    print(f"❌ Error at step '{label}': {e}")
                    traceback.print_exc()
                    # continue to the next step instead of hard-failing
                    continue

                pct = int(i * 100 / total)
                self.progress.emit(pct)

            self.done.emit()
            self.finished_with_mod.emit(self.mod_folder)

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
            # Ensure fresh mod folders
            for folder in [MOD_FOLDER, MOD_UI_FOLDER]:
                if os.path.exists(folder):
                    shutil.rmtree(folder)
                os.makedirs(folder, exist_ok=True)

            # Save important links in main mod folder
            with open(f'{MOD_FOLDER}/links.pkl', 'wb') as file:
                pickle.dump(AOE2_FOLDER, file)
                file.write(b'\n')

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
            #MOD_FOLDER = os.path.abspath(os.path.join(LOCAL_MODS_FOLDER, MOD_NAME))
            #MOD_UI_FOLDER = os.path.abspath(os.path.join(LOCAL_MODS_FOLDER, f"{MOD_NAME}-ui"))

            source_icons_folder = os.path.join("Images", "CivIcons")
            if not os.path.exists(source_icons_folder):
                print(f"⚠️ No CivIcons folder found at {source_icons_folder}")
                return

            # Get all .png files in Images/CivIcons
            icon_files = glob.glob(os.path.join(source_icons_folder, "*.png"))
            if not REPLACE_3KINGDOMS:
                filtered_icons = []
                for file in icon_files:
                    if not file.endswith(('wei.png', 'wu.png', 'shu.png')):
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

        def open_data_file(self):
            global DATA
            DATA = DatFile.parse(rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat')

        def gather_architecture_sets(self):
            global ARCHITECTURE_SETS
            ARCHITECTURE_SETS = []
            for civ in DATA.civs:
                ARCHITECTURE_SETS.append(civ.units)

        def save_settings_files(self):
            mod_settings = {
                'MOD_NAME': MOD_NAME,
                'LOCAL_MODS_FOLDER': LOCAL_MODS_FOLDER,
                'AOE2_FOLDER': AOE2_FOLDER,
                'MOD_FOLDER': MOD_FOLDER,
                'MOD_UI_FOLDER': MOD_UI_FOLDER,
                'ORIGINAL_STRINGS': ORIGINAL_STRINGS,
                'MODDED_STRINGS': MODDED_STRINGS,
            }

            # Persist settings as a pickle. Also write a readable JSON for convenience.
            try:
                with open(f'{MOD_FOLDER}/settings.pkl', 'wb') as pf:
                    pickle.dump(mod_settings, pf)
            except Exception as e:
                print(f"Warning: failed to write settings.pkl: {e}")

            # Optional: human-readable JSON alongside the pickle (useful for debugging)
            try:
                with open(f'{MOD_FOLDER}/settings.json', 'w', encoding='utf-8') as jf:
                    json.dump(mod_settings, jf, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Warning: failed to write settings.json: {e}")

            # Define ignored civs
            global IGNORED_CIVS
            IGNORED_CIVS = [0, 46, 47, 48, 54, 55, 56]

            # Save Talofa program settings
            talofa_settings = {
                'LOCAL_MODS_FOLDER': LOCAL_MODS_FOLDER,
                'AOE2_FOLDER': AOE2_FOLDER,
                'ARCHITECTURE_SETS': ARCHITECTURE_SETS,
                'IGNORED_CIVS': IGNORED_CIVS,
            }

            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.pkl"), 'wb') as file:
                pickle.dump(talofa_settings, file)

        def cleanup_json_files(self):
            # Clean-up JSON file
            with open(rf'{MOD_FOLDER}/resources/_common/dat/civTechTrees.json', 'r', encoding='utf-8') as file:
                raw = file.read()

            # Remove comma after a closing brace if it's followed by just whitespace/newlines and a closing bracket
            cleaned = re.sub(r'(})\s*,\s*(\])', r'\1\n\2', raw)
            with open(rf'{MOD_FOLDER}/resources/_common/dat/civTechTrees.json', 'w', encoding='utf-8') as file:
                file.write(cleaned)

            # Update the civilizations.json file
            with open(rf'{MOD_FOLDER}/resources/_common/dat/civilizations.json', 'r+', encoding='utf-8') as file:
                # Edit the names
                raw = file.read()
                cleaned = raw.replace(r'"MAGYAR"', r'"MAGYARS"').replace(r'"INDIANS"', r'"HINDUSTANIS"')

                # Write to file
                file.seek(0)
                file.write(cleaned)
                file.truncate()

            # Correct name mistakes
            DATA.civs[1].name = 'Britons'
            DATA.civs[2].name = 'Franks'
            DATA.civs[7].name = 'Byzantines'
            DATA.civs[16].name = 'Maya'
            DATA.effects[449].name = 'Maya Tech Tree'
            DATA.effects[489].name = 'Maya Team Bonus'
            DATA.civs[21].name = 'Inca'
            DATA.effects[3].name = 'Inca Tech Tree'
            DATA.effects[4].name = 'Inca Team Bonus'

        def setup_sounds(self):
            # Copy over custom sounds
            sounds_source_folder = os.path.join(os.path.dirname(__file__), 'sounds')  # Path to the original 'sounds' folder
            sounds_destination_folder = os.path.join(MOD_FOLDER, 'resources/_common/drs/sounds')  # Path to the new 'sounds' folder in the mod folder

            # Ensure the destination directory exists
            os.makedirs(sounds_destination_folder, exist_ok=True)

            # Copy all files from the source 'sounds' folder to the destination
            if os.path.exists(sounds_source_folder):
                for item in os.listdir(sounds_source_folder):
                    source_path = os.path.join(sounds_source_folder, item)
                    destination_path = os.path.join(sounds_destination_folder, item)

                    if os.path.isfile(source_path):
                        shutil.copy2(source_path, destination_path)  # Copy file
                    elif os.path.isdir(source_path):
                        shutil.copytree(source_path, destination_path, dirs_exist_ok=True)  # Copy directory
            else:
                print(f"Warning: Source sounds folder '{sounds_source_folder}' does not exist.")

            # Load all languages
            ALL_LANGUAGES = []
            sound_folder = f'{MOD_FOLDER}/resources/_common/drs/sounds'

            for filename in os.listdir(sound_folder):
                file_path = os.path.join(sound_folder, filename)

                # Ensure it's a file and matches the expected naming format: language_unit_action_#.ext
                if not os.path.isfile(file_path):
                    continue

                # Must have at least 3 parts: language_unit_action (e.g., "English_Soldier_Move.wav")
                parts = filename.split('_')
                if len(parts) < 3:
                    continue

                language = parts[0]
                if language not in ALL_LANGUAGES:
                    ALL_LANGUAGES.append(language)
            ALL_LANGUAGES.sort()

            # Reformat the default sounds
            sound_ids = {303: 'Villager-Male_Select_4', 301: 'Villager-Male_Move_4', 295: 'Villager-Male_Build_1', 299: 'Villager-Male_Chop_1', 455: 'Villager-Male_Farm_1', 448: 'Villager-Male_Fish_1', 297: 'Villager-Male_Forage_1', 298: 'Villager-Male_Hunt_1', 300: 'Villager-Male_Mine_1', 302: 'Villager-Male_Repair_1', 435: 'Villager-Female_Select_4', 434: 'Villager-Female_Move_4', 437: 'Villager-Female_Build_1', 442: 'Villager-Female_Chop_1', 438: 'Villager-Female_Farm_1', 487: 'Villager-Female_Fish_1', 440: 'Villager-Female_Forage_1', 441: 'Villager-Female_Hunt_1', 443: 'Villager-Female_Mine_1', 444: 'Villager-Female_Repair_1', 420: 'Soldier_Select_3', 421: 'Soldier_Move_3', 422: 'Soldier_Attack_3', 423: 'Monk_Select_3', 424: 'Monk_Move_3', 479: 'King_Select_3', 480: 'King_Move_3'}
            
            # Remove all previous sound items
            for sound_id in sound_ids:
                DATA.sounds[sound_id].items.clear()

            # Set defaults for each civilization
            for civ_id, civ in enumerate(DATA.civs):
                for sound_id in sound_ids:
                    # Get the amount of sound items to add
                    sound_count = int(sound_ids[sound_id][-1])

                    # Add the sound items to the sound
                    language_presets = {1: "English", 2: "French", 3: "Gothic", 4: "German", 5: "Japanese", 6: "Mandarin", 7: "Greek", 8: "Persian", 9: "Arabic", 10: "Turkish", 11: "Norse", 12: "Mongolian", 13: "Gaelic", 14: "Spanish", 15: "Yucatec", 16: "Kaqchikel", 17: "Chuvash", 18: "Korean", 19: "Italian", 20: "Hindustani", 21: "Quechua", 22: "Hungarian", 23: "Russian", 24: "Portuguese", 25: "Amharic", 26: "Maninka", 27: "Taqbaylit", 28: "Khmer", 29: "Malaysian", 30: "Burmese", 31: "Vietnamese", 32: "Bulgarian", 33: "Chagatai", 34: "Cuman", 35: "Lithuanian", 36: "Burgundian", 37: "Sicilian", 38: "Polish", 39: "Czech", 40: "Tamil", 41: "Bengali", 42: "Gujarati", 43: "Vulgar Latin", 44: "Armenian", 45: "Georgian", 49: "Tangut", 50: "Bai", 51: "Tibetan", 52: "Jurchen", 53: "Khitan"}
                    for i in range(sound_count):
                        # Correct the name
                        if civ_id not in language_presets:
                            continue
                        correct_name = language_presets[civ_id]

                        # Create new name
                        if sound_count == 1:
                            new_sound_name = f'{correct_name}_{sound_ids[sound_id][:-2]}'
                        else:
                            new_sound_name = f'{correct_name}_{sound_ids[sound_id][:-2]}_{i + 1}'

                        # Determine probability
                        new_sound_probability = int(100 / sound_count)

                        # Create new sound item
                        new_sound = genieutils.sound.SoundItem(new_sound_name, 0, new_sound_probability, civ_id, -1)

                        # Add sound item to the sound
                        DATA.sounds[sound_id].items.append(new_sound)

        def edit_strings(self):
            # Convert the lines with codes into a dictionary
            load_original_string_lines()

            # Write modded strings based on filter conditions
            with open(MODDED_STRINGS, 'w+', encoding='utf-8') as modded_file:
                # Write name strings
                for i in range(len(DATA.civs)):
                    try:
                        modded_file.write(ORIGINAL_STRING_LINES[10271 + i])
                    except:
                        pass
                    
                # Write description strings
                for i in range(len(DATA.civs)):
                    try:
                        modded_file.write(ORIGINAL_STRING_LINES[120150 + i])
                    except:
                        pass

            # Remove the Caravanserai and Pastures text for the Persians/Hindustanis and Khitans
            with open(MODDED_STRINGS, 'r+', encoding='utf-8') as modded_file:
                modded_strings = modded_file.readlines()
                modded_file.seek(0)  # rewind to start
                for line in modded_strings:
                    line = line.replace(r'• Can build Caravanserai in Imperial Age\n', '')
                    line = line.replace(r'• Pastures replace Farms\n', '')
                    modded_file.write(line)
                modded_file.truncate()

            # Fix the Tech Tree JSON names
            with open(f'{MOD_FOLDER}/resources/_common/dat/civTechTrees.json', 'r+', encoding='utf-8') as file:
                lines = file.readlines()
                file.seek(0)              # Go back to the start of the file
                file.truncate()           # Clear the file content

                for line in lines:
                    if line.strip() == '"civ_id": "INDIANS",':
                        line = '      "civ_id": "HINDUSTANIS",\n'
                    elif line.strip() == '"civ_id": "MAGYAR",':
                        line = '      "civ_id": "MAGYARS",\n'
                    file.write(line)

        def despecialise_units(self):
            # Make Winged Hussar available to all civs
            winged_hussar_id = 786
            DATA.techs[winged_hussar_id].required_techs = (103, 254, -1, -1, -1, -1)
            DATA.techs[winged_hussar_id].required_tech_count = 2
            for tech_id in [788, 789, 791]:
                DATA.techs[tech_id].effect_id = -1

            # Disable Three Kingdoms heroes
            for tech_id in [1066, 1038, 1083]:
                DATA.techs[tech_id].effect_id = -1

            # Adjust Fortified Church upgrade chain
            for i in range(943, 947):
                DATA.techs[i].required_techs = (929, DATA.techs[i].required_techs[0], -1, -1, -1, -1)

            # --- PREPARE CIV TECH TREE INDEXES ---
            tech_tree_indexes = []
            for civ_id, civ in enumerate(DATA.civs):
                # Skip Chronicles civs
                if civ_id in IGNORED_CIVS:
                    tech_tree_indexes.append(-1)
                    continue
                # Find each civ's tech tree
                for i, effect in enumerate(DATA.effects):
                    if effect.name == f"{civ.name.title()} Tech Tree":
                        tech_tree_indexes.append(i)
                        break

            # --- FORTIFIED CHURCH ---
            DATA.techs[941].effect_id = -1
            DATA.techs[941].name = "Fortified Church (DISABLED)"
            DATA.techs[930].effect_id = -1
            DATA.techs[930].name = "Fortified Church (DISABLED)"
            DATA.effects[941].name = "Fortified Church"
            DATA.techs[929].name = "Fortified Church"
            DATA.techs[929].effect_id = 941
            for tt in tech_tree_indexes:
                if tt not in [925, 927]:
                    DATA.effects[tt].effect_commands.append(
                        genieutils.effect.EffectCommand(102, -1, -1, -1, 929)
                    )

            # --- MULE CART ---
            DATA.techs[940].effect_id = -1
            DATA.techs[940].name = "Mule Cart (DISABLED)"
            DATA.techs[940].civ = -1
            DATA.techs[932].civ = -1
            for tt in tech_tree_indexes:
                if tt not in [925, 927]:
                    DATA.effects[tt].effect_commands.append(
                        genieutils.effect.EffectCommand(102, -1, -1, -1, 932)
                    )

            # --- UNIQUE TECHS UNIVERSAL AVAILABILITY ---
            unique_techs_indexes = [
                84, 272, 447, 448, 521, 522, 526, 528, 570, 596, 597, 598, 599,
                655, 695, 703, 773, 775, 787, 790, 793, 841, 842, 843, 885, 930,
                941, 948, 992, 1005, 1037, 1065, 1075
            ]

            hidden_civs = {522: 19, 599: 27, 655: 31}

            for tech_id in unique_techs_indexes:
                excluded_civ_id = DATA.techs[tech_id].civ
                if excluded_civ_id == -1:
                    excluded_civ_id = hidden_civs.get(tech_id, -1)

                DATA.techs[tech_id].civ = -1  # Decouple civ restriction

                for i, tt_index in enumerate(tech_tree_indexes):
                    if tt_index == -1 or tt_index == tech_tree_indexes[excluded_civ_id]:
                        continue
                    DATA.effects[tt_index].effect_commands.append(
                        genieutils.effect.EffectCommand(102, -1, -1, -1, tech_id)
                    )

            # --- DISABLE UNUSED TECHS ---
            for tech_id in [0]:
                DATA.techs[tech_id].effect_id = -1
                DATA.techs[tech_id].civ = -1

        def cleanup_strings(self):
            # Convert the lines with codes into a dictionary
            line_dictionary = {}
            with open(ORIGINAL_STRINGS, 'r', encoding='utf-8') as original_file:
                original_strings_list = original_file.readlines()
                for line in original_strings_list:
                    match = re.match(r'^(\d+)', line)
                    if match:
                        key = int(match.group(1))
                        line_dictionary[key] = line

            # Write modded strings based on filter conditions
            with open(MODDED_STRINGS, 'w+', encoding='utf-8') as modded_file:
                # Write name strings
                for i in range(len(DATA.civs)):
                    try:
                        modded_file.write(line_dictionary[10271 + i])
                    except:
                        pass
                    
                # Write description strings
                for i in range(len(DATA.civs)):
                    try:
                        modded_file.write(line_dictionary[120150 + i])
                    except:
                        pass

            # Remove the Caravanserai text for the Persians/Hindustanis
            with open(MODDED_STRINGS, 'r+', encoding='utf-8') as modded_file:
                modded_strings = modded_file.readlines()
                modded_file.seek(0)  # rewind to start
                for line in modded_strings:
                    line = line.replace(r'• Can build Caravanserai in Imperial Age\n', '')
                    modded_file.write(line)
                modded_file.truncate()

            # Remove the Pasture text for the Khitans
            with open(MODDED_STRINGS, 'r+', encoding='utf-8') as modded_file:
                modded_strings = modded_file.readlines()
                modded_file.seek(0)  # rewind to start
                for line in modded_strings:
                    line = line.replace(r'• Pastures replace Farms\n', '')
                    modded_file.write(line)
                modded_file.truncate()

        def make_civs_more_realistic(self):
            # Saracens start with Camel Scout
            DATA.civs[9].resources[263] = 1755
            DATA.civs[20].resources[263] = 1755

            # Change the Monastery and Monk graphics for the Vikings and Lithuanians
            replace_graphics_for_civs([11, 35], [30, 31, 32, 104, 1421, 125, 286, 922, 1025, 1327], [1712, 1712, 1712, 1712, 1526, 1940, 1941, 1941, 1941, 1941])

            # Change the Monastery graphics for the Chinese, Koreans, Vietnamese, and Jurchens
            replace_graphics_for_civs([6, 18, 31, 52], [30, 31, 32, 104, 2348, 1421], [2060, 2060, 2060, 2060, 2060, 145])

            # Change the Monastery graphics for the Wu, Wei, and Shu
            if REPLACE_3KINGDOMS:
                replace_graphics_for_civs([49, 50, 51], [30, 31, 32, 104, 1421], [2060, 2060, 2060, 2060, 145])

            # Split the architecture sets for Southeast Asians
            for civ in DATA.civs:
                if civ.name not in ['Khmer', 'Burmese', 'Malay']:
                    continue

                if civ.name == 'Malay':
                    # For Malay: replace Age3 and Age4 with Age2
                    target_ages = ['Age3', 'Age4']
                    replacement_age = 'Age2'
                else:
                    # For Khmer/Burmese: replace Age2 with Age3
                    target_ages = ['Age2']
                    replacement_age = 'Age3'

                # Regex to match any of the target ages
                age_pattern = re.compile(rf"({'|'.join(target_ages)})(\D|$)")

                for unit in civ.units:
                    try:
                        if unit.standing_graphic == (-1, -1):
                            continue
                    except:
                        continue

                    current_standing_name = DATA.graphics[unit.standing_graphic[0]].name

                    if 'SEAS' not in current_standing_name or not age_pattern.search(current_standing_name):
                        continue

                    matched_age = age_pattern.search(current_standing_name).group(1)

                    # Prepare the replacement names
                    new_standing_name = current_standing_name.replace(matched_age, replacement_age)

                    # Dying graphic
                    if 0 <= unit.dying_graphic < len(DATA.graphics):
                        current_dying_name = DATA.graphics[unit.dying_graphic].name
                        new_dying_name = current_dying_name.replace(matched_age, replacement_age)
                    else:
                        new_dying_name = None

                    # Search for matching graphics
                    standing_graphic_id = -1
                    dying_graphic_id = -1

                    for i, graphic in enumerate(DATA.graphics):
                        if graphic is None or not graphic.name:
                            continue

                        if standing_graphic_id == -1 and graphic.name == new_standing_name:
                            standing_graphic_id = i

                        if unit.dying_graphic != -1 and dying_graphic_id == -1:
                            if new_dying_name and graphic.name == new_dying_name:
                                dying_graphic_id = i

                        if standing_graphic_id != -1 and (
                            dying_graphic_id != -1 or unit.dying_graphic == -1
                        ):
                            break

                    # Apply changes if found
                    if standing_graphic_id != -1:
                        unit.standing_graphic = (standing_graphic_id, -1)

                    if unit.dying_graphic != -1 and dying_graphic_id != -1:
                        unit.dying_graphic = dying_graphic_id

            # Edit pastures
            DATA.techs[1008].civ = -1
            DATA.techs[1014].civ = -1
            DATA.techs[1013].civ = -1
            DATA.techs[1012].civ = -1
            DATA.techs[1008].name = 'Pasture'
            DATA.effects[1008].name = 'Pasture'
            DATA.effects[1008].effect_commands[0] = genieutils.effect.EffectCommand(3, 50, 1889, -1, -1)
            for civ in DATA.civs:
                civ.units[1890].resource_storages[0].type = 4
                civ.units[1890].resource_storages[0].amount = 0
                civ.units[1890].resource_storages[0].flag = 4

            # Rename certain techs/effects
            DATA.techs[695].name = 'Krepost'
            DATA.effects[732].name = 'Krepost'
            DATA.techs[775].name = 'Donjon'
            DATA.effects[800].name = 'Donjon'

            # Remove the Dragon Ship upgrade for the Chinese
            DATA.techs[1010].effect_id = -1
            DATA.techs[1010].civ = 0
            DATA.techs[1010].required_tech_count = 6
            for i, ec in enumerate(DATA.effects[257].effect_commands):
                if ec.type == 102 and ec.d == 246:
                    DATA.effects[257].effect_commands.pop(i)
                    break

        def create_talofa_units(self):
            global CUSTOM_UNIT_STARTING_INDEX
            CUSTOM_UNIT_STARTING_INDEX = len(DATA.civs[0].units)

            # Create units unique to Talofa
            for civ in DATA.civs:
                # Change sound for dock to port
                for unit_id in [45, 47, 51, 113, 805, 806, 807, 808, 2120, 2121, 2122, 2144, 2145, 2146, 2173]:
                    civ.units[unit_id].selection_sound = 708
                    civ.units[unit_id].train_sound = 708

                # 0: Canoe
                canoe = copy.deepcopy(DATA.civs[1].units[778])
                canoe.creatable.train_locations[0].unit_id = 45
                canoe.creatable.train_locations[0].button_id = 4
                canoe.type_50.attacks[0].amount = 8
                canoe.type_50.attacks[2].amount = 5
                canoe.type_50.displayed_attack = 5
                canoe.type_50.reload_time = 2
                canoe.type_50.displayed_reload_time = 2
                canoe.type_50.max_range = 6
                canoe.type_50.displayed_range = 6
                canoe.line_of_sight = canoe.type_50.max_range + 2
                canoe.bird.search_radius = canoe.line_of_sight
                canoe.creatable.max_charge = 20
                canoe.creatable.recharge_rate = 3.2e+18
                canoe.creatable.charge_event = -2
                canoe.creatable.charge_target = 191
                #canoe.creatable.charge_type = 6
                civ.units.append(canoe)

                # 1: War Canoe
                war_canoe = copy.deepcopy(canoe)
                change_string(90000, 'War Canoe')
                change_string(91000, 'Create War Canoe')
                war_canoe.language_dll_name = 90000
                war_canoe.language_dll_creation = 91000
                war_canoe.name = 'War Canoe'
                war_canoe.standing_graphic = civ.units[1302].standing_graphic
                war_canoe.dying_graphic = civ.units[1302].dying_graphic
                war_canoe.undead_graphic = civ.units[1302].undead_graphic
                war_canoe.dead_fish.walking_graphic = civ.units[1302].dead_fish.walking_graphic
                war_canoe.dead_fish.running_graphic = civ.units[1302].dead_fish.running_graphic
                war_canoe.type_50.attack_graphic = civ.units[1302].type_50.attack_graphic
                war_canoe.type_50.attack_graphic_2 = civ.units[1302].type_50.attack_graphic_2
                war_canoe.icon_id = civ.units[1302].icon_id
                war_canoe.type_50.max_range = 8
                war_canoe.type_50.displayed_range = 8
                war_canoe.line_of_sight = war_canoe.type_50.max_range + 2
                war_canoe.bird.search_radius = war_canoe.line_of_sight
                war_canoe.type_50.attacks[2].amount = 6
                war_canoe.type_50.displayed_attack = 6
                war_canoe.hit_points = 90
                war_canoe.type_50.attacks[0].amount = 12
                war_canoe.type_50.reload_time = 2
                war_canoe.type_50.displayed_reload_time = 2
                war_canoe.creatable.charge_event = -3
                civ.units.append(war_canoe)

                # 2: Elite War Canoe
                elite_war_canoe = copy.deepcopy(war_canoe)
                change_string(92000, 'Elite War Canoe')
                change_string(93000, 'Create Elite War Canoe')
                elite_war_canoe.language_dll_name = 92000
                elite_war_canoe.language_dll_creation = 93000
                elite_war_canoe.name = 'Elite War Canoe'
                elite_war_canoe.standing_graphic = civ.units[1302].standing_graphic
                elite_war_canoe.dying_graphic = civ.units[1302].dying_graphic
                elite_war_canoe.undead_graphic = civ.units[1302].undead_graphic
                elite_war_canoe.dead_fish.walking_graphic = civ.units[1302].dead_fish.walking_graphic
                elite_war_canoe.dead_fish.running_graphic = civ.units[1302].dead_fish.running_graphic
                elite_war_canoe.type_50.attack_graphic = civ.units[1302].type_50.attack_graphic
                elite_war_canoe.type_50.attack_graphic_2 = civ.units[1302].type_50.attack_graphic_2
                elite_war_canoe.icon_id = civ.units[1302].icon_id
                elite_war_canoe.type_50.max_range = 10
                elite_war_canoe.type_50.displayed_range = 10
                elite_war_canoe.line_of_sight = elite_war_canoe.type_50.max_range + 2
                elite_war_canoe.bird.search_radius = elite_war_canoe.line_of_sight
                elite_war_canoe.type_50.attacks[2].amount = 7
                elite_war_canoe.type_50.displayed_attack = 7
                elite_war_canoe.creatable.total_projectiles = 3
                elite_war_canoe.creatable.max_total_projectiles = 3
                elite_war_canoe.hit_points = 110
                elite_war_canoe.type_50.attacks[0].amount = 16
                elite_war_canoe.type_50.reload_time = 2
                elite_war_canoe.type_50.displayed_reload_time = 2
                elite_war_canoe.creatable.charge_event = -4
                civ.units.append(elite_war_canoe)

                # 3: Naasiri
                naasiri = copy.deepcopy(DATA.civs[1].units[2327])
                change_string(94000, 'Naasiri')
                change_string(95000, 'Create Naasiri')
                naasiri.language_dll_name = 94000
                naasiri.language_dll_creation = 95000
                naasiri.name = 'Naasiri'
                naasiri.creatable.train_locations[0].unit_id = 82
                naasiri.creatable.train_locations[0].button_id = 1
                naasiri.creatable.train_locations[0].train_time = 24
                naasiri.creatable.train_locations[0].hot_key_id = 16107
                naasiri.type_50.attacks[0].amount = 7
                naasiri.type_50.displayed_attack = 7
                naasiri.creatable.train_time = 22
                civ.units.append(naasiri)

                # 4: Elite Naasiri
                elite_naasiri = copy.deepcopy(naasiri)
                change_string(96000, 'Elite Naasiri')
                change_string(97000, 'Create Elite Naasiri')
                elite_naasiri.language_dll_name = 96000
                elite_naasiri.language_dll_creation = 97000
                elite_naasiri.name = 'Elite Naasiri'
                elite_naasiri.type_50.attacks[0].amount = 9
                elite_naasiri.type_50.displayed_attack = 9
                elite_naasiri.hit_points = 110
                civ.units.append(elite_naasiri)

                # 5: Elephant Gunner
                elephant_gunner = copy.deepcopy(DATA.civs[1].units[875])
                change_string(98000, 'Elephant Gunner')
                change_string(99000, 'Create Elephant Gunner')
                elephant_gunner.language_dll_name = 98000
                elephant_gunner.language_dll_creation = 99000
                elephant_gunner.name = 'Elephant Gunner'
                elephant_gunner.creatable.train_locations[0].unit_id = 82
                elephant_gunner.creatable.train_locations[0].button_id = 1
                elephant_gunner.type_50.max_range = 7
                elephant_gunner.type_50.displayed_range = 7
                elephant_gunner.line_of_sight = 9
                elephant_gunner.bird.search_radius = 9
                elephant_gunner.type_50.attacks[1].amount = 19
                elephant_gunner.type_50.displayed_attack = 19
                elephant_gunner.hit_points = 200
                elephant_gunner.speed = 0.8
                elephant_gunner.type_50.reload_time = 3.45
                elephant_gunner.type_50.accuracy_percent = 75
                elephant_gunner.creatable.train_locations[0].train_time = 28
                elephant_gunner.creatable.resource_costs = (ResourceCost(type=0, amount=80, flag=1), ResourceCost(type=3, amount=100, flag=1), ResourceCost(type=4, amount=1, flag=0))
                elephant_gunner.type_50.projectile_unit_id = 380
                elephant_gunner.creatable.train_locations[0].hot_key_id = 16107
                elephant_gunner.class_ = 23
                civ.units.append(elephant_gunner)

                # 6: Elite Elephant Gunner
                elite_elephant_gunner = copy.deepcopy(elephant_gunner)
                change_string(100000, 'Elite Elephant Gunner')
                change_string(101000, 'Create Elite Elephant Gunner')
                elite_elephant_gunner.language_dll_name = 100000
                elite_elephant_gunner.language_dll_creation = 101000
                elite_elephant_gunner.name = 'Elite Elephant Gunner'
                elite_elephant_gunner.type_50.attacks[1].amount = 21
                elite_elephant_gunner.type_50.displayed_attack = 21
                elite_elephant_gunner.hit_points = 250
                elite_elephant_gunner.class_ = 23
                civ.units.append(elite_elephant_gunner)

                # 7: Flamethrower
                flamethrower = copy.deepcopy(DATA.civs[1].units[188])
                flamethrower.creatable.train_locations[0].unit_id = 82
                flamethrower.creatable.train_locations[0].button_id = 1
                flamethrower.type_50.attacks[1].amount = 6
                flamethrower.type_50.displayed_attack = 6
                flamethrower.creatable.train_locations[0].hot_key_id = 16107
                civ.units.append(flamethrower)

                # 8: Elite Flamethrower
                elite_flamethrower = copy.deepcopy(flamethrower)
                change_string(102000, 'Elite Flamethrower')
                change_string(103000, 'Create Elite Flamethrower')
                elite_flamethrower.language_dll_name = 102000
                elite_flamethrower.language_dll_creation = 103000
                elite_flamethrower.type_50.attacks[1].amount = 6
                elite_flamethrower.type_50.displayed_attack = 6
                elite_flamethrower.hit_points = 180
                elite_flamethrower.name = 'Elite Flamethrower'
                civ.units.append(elite_flamethrower)

                # 9: Bolas Warrior
                weichafe = copy.deepcopy(DATA.civs[1].units[2320])
                change_string(104000, 'Bolas Warrior')
                change_string(105000, 'Create Bolas Warrior')
                weichafe.language_dll_name = 104000
                weichafe.language_dll_creation = 105000
                weichafe.creatable.train_locations[0].unit_id = 82
                weichafe.creatable.train_locations[0].button_id = 1
                weichafe.class_ = 0
                weichafe_base_attack = copy.deepcopy(weichafe.type_50.attacks[0])
                weichafe.type_50.attacks.clear()
                weichafe.type_50.attacks.append(weichafe_base_attack)
                weichafe.type_50.attacks[0].amount = 4
                weichafe.type_50.displayed_attack = 4
                weichafe.type_50.max_range = 4
                weichafe.type_50.displayed_range = 4
                weichafe.line_of_sight = 6
                weichafe.bird.search_radius = 6
                weichafe.bird.tasks = DATA.civs[1].units[1959].bird.tasks
                for i in range(6, 20):
                    weichafe.bird.tasks[i].work_value_1 = -0.25
                weichafe.name = 'Bolas Warrior'
                weichafe.creatable.train_locations[0].hot_key_id = 16107
                civ.units.append(weichafe)

                # 10: Elite Bolas Warrior
                elite_weichafe = copy.deepcopy(weichafe)
                change_string(106000, 'Elite Bolas Warrior')
                change_string(107000, 'Create Elite Bolas Warrior')
                elite_weichafe.language_dll_name = 106000
                elite_weichafe.language_dll_creation = 107000
                elite_weichafe.class_ = 0
                elite_weichafe.type_50.attacks[0].amount = 5
                elite_weichafe.type_50.displayed_attack = 5
                elite_weichafe.type_50.max_range = 5
                elite_weichafe.type_50.displayed_range = 5
                elite_weichafe.line_of_sight = 7
                elite_weichafe.bird.search_radius = 7
                elite_weichafe.name = 'Elite Bolas Warrior'
                civ.units.append(elite_weichafe)

                # 11: Crusader
                crusader = copy.deepcopy(DATA.civs[1].units[1723])
                change_string(108000, 'Crusader')
                change_string(109000, 'Create Crusader')
                crusader.language_dll_name = 108000
                crusader.language_dll_creation = 109000
                crusader.type_50.attacks[0].amount = 13
                crusader.type_50.displayed_attack = 13
                crusader.speed = 1.2
                crusader.creatable.train_locations[0].button_id = 1
                crusader.name = 'Crusader'
                crusader.creatable.train_locations[0].hot_key_id = 16107
                civ.units.append(crusader)

                # 12: Elite Crusader
                elite_crusader = copy.deepcopy(crusader)
                change_string(110000, 'Elite Crusader')
                change_string(111000, 'Elite Create Crusader')
                elite_crusader.language_dll_name = 110000
                elite_crusader.language_dll_creation = 111000
                elite_crusader.type_50.attacks[0].amount = 15
                elite_crusader.type_50.displayed_attack = 15
                elite_crusader.hit_points = 120
                elite_crusader.name = 'Elite Crusader'
                civ.units.append(elite_crusader)

                # 13: Tomahawk Warrior
                tomahawk_warrior = copy.deepcopy(DATA.civs[1].units[1374])
                change_string(112000, 'Tomahawk Warrior')
                change_string(113000, 'Create Tomahawk Warrior')
                tomahawk_warrior.language_dll_name = 112000
                tomahawk_warrior.language_dll_creation = 113000
                tomahawk_warrior.type_50.attacks[3].amount = 10
                tomahawk_warrior.name = 'Tomahawk Warrior'
                tomahawk_warrior.creatable.train_locations[0].hot_key_id = 16107
                civ.units.append(tomahawk_warrior)

                # 14: Elite Tomahawk Warrior
                elite_tomahawk_warrior = copy.deepcopy(tomahawk_warrior)
                change_string(114000, 'Elite Tomahawk Warrior')
                change_string(115000, 'Create Elite Tomahawk Warrior')
                elite_tomahawk_warrior.language_dll_name = 114000
                elite_tomahawk_warrior.language_dll_creation = 115000
                elite_tomahawk_warrior.type_50.attacks[3].amount = 12
                elite_tomahawk_warrior.type_50.attacks[2].amount = 10
                elite_tomahawk_warrior.type_50.displayed_attack = 10
                elite_tomahawk_warrior.hit_points = 80
                elite_tomahawk_warrior.name = 'Elite Tomahawk Warrior'
                civ.units.append(elite_tomahawk_warrior)

                # 15: Imperial Elephant Archer
                imperial_elephant_archer = copy.deepcopy(DATA.civs[1].units[875])
                change_string(116000, 'Imperial Elephant Archer')
                change_string(117000, 'Create Imperial Elephant Archer')
                imperial_elephant_archer.language_dll_name = 116000
                imperial_elephant_archer.language_dll_creation = 117000
                imperial_elephant_archer.type_50.attacks[1].amount = 8
                imperial_elephant_archer.type_50.displayed_attack = 8
                imperial_elephant_archer.hit_points = 320
                imperial_elephant_archer.type_50.max_range = 6
                imperial_elephant_archer.type_50.displayed_range = 6
                imperial_elephant_archer.type_50.min_range = 1
                imperial_elephant_archer.line_of_sight = 9
                imperial_elephant_archer.bird.search_radius = 8
                imperial_elephant_archer.standing_graphic = civ.units[1106].standing_graphic
                imperial_elephant_archer.dying_graphic = civ.units[1106].dying_graphic
                imperial_elephant_archer.undead_graphic = civ.units[1106].undead_graphic
                imperial_elephant_archer.dead_fish.walking_graphic = civ.units[1106].dead_fish.walking_graphic
                imperial_elephant_archer.dead_fish.running_graphic = civ.units[1106].dead_fish.running_graphic
                imperial_elephant_archer.type_50.attack_graphic = civ.units[1106].type_50.attack_graphic
                imperial_elephant_archer.type_50.attack_graphic_2 = civ.units[1106].type_50.attack_graphic_2
                imperial_elephant_archer.name = 'Imperial Elephant Archer'
                imperial_elephant_archer.creatable.train_locations[0].train_time = civ.units[875].creatable.train_locations[0].train_time
                imperial_elephant_archer.creatable.train_locations[0].unit_id = civ.units[875].creatable.train_locations[0].unit_id
                imperial_elephant_archer.creatable.train_locations[0].button_id = civ.units[875].creatable.train_locations[0].button_id
                civ.units.append(imperial_elephant_archer)

                # 16: Lightning Warrior
                '''lightning_warrior = copy.deepcopy(DATA.civs[1].units[749])
                change_string(118000, 'Lightning Warrior')
                change_string(119000, 'Create Lightning Warrior')
                lightning_warrior.language_dll_name = 118000
                lightning_warrior.language_dll_creation = 119000

                lightning_warrior.type_50.attacks.clear()
                lightning_warrior.type_50.attacks.append(AttackOrArmor(4, 5))
                lightning_warrior.type_50.displayed_attack = 5

                lightning_warrior.type_50.armours.clear()
                lightning_warrior.type_50.armours.append(AttackOrArmor(3, 0))
                lightning_warrior.type_50.armours.append(AttackOrArmor(4, 0))
                lightning_warrior.type_50.displayed_melee_armour = 0
                lightning_warrior.creatable.displayed_pierce_armor = 0

                lightning_warrior.hit_points = 35
                lightning_warrior.speed = 1.35
                lightning_warrior.type_50.reload_time = 0.85
                lightning_warrior.creatable.hero_mode = 0
                lightning_warrior.creatable.train_locations[0].unit_id = 82
                lightning_warrior.creatable.train_locations[0].train_time = 11
                lightning_warrior.creatable.train_locations[0].button_id = 1
                lightning_warrior.creatable.train_locations[0].hot_key_id = 16107
                lightning_warrior.creatable.resource_costs[1].amount = 30
                lightning_warrior.name = 'Lightning Warrior'
                civ.units.append(lightning_warrior)

                # 17: Elite Lightning Warrior
                elite_lightning_warrior = copy.deepcopy(lightning_warrior)
                change_string(120000, 'Elite Lightning Warrior')
                change_string(121000, 'Create Elite Lightning Warrior')
                elite_lightning_warrior.language_dll_name = 120000
                elite_lightning_warrior.language_dll_creation = 121000
                elite_lightning_warrior.type_50.attacks[0].amount = 7
                elite_lightning_warrior.type_50.displayed_attack = 7
                elite_lightning_warrior.hit_points = 45
                elite_lightning_warrior.name = 'Elite Lightning Warrior'
                civ.units.append(elite_lightning_warrior)'''

                # 18: Destroyer
                destroyer = copy.deepcopy(DATA.civs[1].units[1074])
                change_string(122000, 'Destroyer')
                change_string(123000, 'Create Destroyer')
                destroyer.language_dll_name = 122000
                destroyer.language_dll_creation = 123000
                #destroyer.type_50.attacks = copy.deepcopy(civ.units[755].type_50.attacks)
                #destroyer.type_50.attacks[1].amount = 14
                #destroyer.type_50.displayed_attack = 8
                destroyer.hit_points = 80
                destroyer.name = 'Destroyer'
                destroyer.speed = 0.9
                destroyer.type_50.reload_time = 3
                destroyer.creatable.hero_mode = 0
                destroyer.creatable.train_locations[0].unit_id = 82
                destroyer.creatable.train_locations[0].train_time = 14
                destroyer.creatable.train_locations[0].button_id = 1
                destroyer.creatable.train_locations[0].hot_key_id = 16107
                civ.units.append(destroyer)

                # 19: Elite Destroyer
                elite_destroyer = copy.deepcopy(destroyer)
                change_string(124000, 'Elite Destroyer')
                change_string(125000, 'Create Elite Destroyer')
                elite_destroyer.language_dll_name = 124000
                elite_destroyer.language_dll_creation = 125000
                #elite_destroyer.type_50.attacks[1].amount = 16
                #elite_destroyer.type_50.attacks[2].amount = 9
                #elite_destroyer.type_50.displayed_attack = 9
                elite_destroyer.hit_points = 90
                elite_destroyer.name = 'Elite Destroyer'
                civ.units.append(elite_destroyer)

                # 20: Cossack
                cossack = copy.deepcopy(DATA.civs[1].units[1186])
                change_string(126000, 'Cossack')
                change_string(127000, 'Create Cossack')
                cossack.language_dll_name = 126000
                cossack.language_dll_creation = 127000
                cossack.creatable.resource_costs[1].type = 3
                cossack.creatable.resource_costs[1].amount = 40
                cossack.creatable.resource_costs[1].flag = 1
                cossack.type_50.displayed_melee_armour = 1
                cossack.creatable.charge_type = 3
                cossack.creatable.charge_event = 1
                cossack.creatable.charge_target = 511
                cossack.creatable.max_charge = 15
                cossack.creatable.recharge_rate = 0.5
                cossack.creatable.hero_mode = 0
                cossack.creatable.train_locations[0].unit_id = 82
                cossack.creatable.train_locations[0].train_time = 14
                cossack.creatable.train_locations[0].button_id = 1
                cossack.creatable.train_locations[0].hot_key_id = 16107
                cossack.name = 'Cossack'
                civ.units.append(cossack)

                # 21: Elite Cossack
                elite_cossack = copy.deepcopy(cossack)
                change_string(128000, 'Elite Cossack')
                change_string(129000, 'Create Elite Cossack')
                elite_cossack.language_dll_name = 128000
                elite_cossack.language_dll_creation = 129000
                elite_cossack.creatable.recharge_rate = 1
                elite_cossack.type_50.attacks[1].amount = 14
                elite_cossack.type_50.displayed_attack = 14
                elite_cossack.type_50.armours[0].amount = 2
                elite_cossack.type_50.armours[2].amount = 2
                elite_cossack.type_50.displayed_melee_armour = 2
                elite_cossack.name = 'Elite Cossack'
                civ.units.append(elite_cossack)

                # 22: Fire Tower
                fire_tower = copy.deepcopy(DATA.civs[1].units[190])
                fire_tower.line_of_sight = 10
                fire_tower.bird.search_radius = 10
                fire_tower.type_50.attacks.append(AttackOrArmor(20, 15))
                fire_tower.creatable.train_locations[0].button_id = 10
                fire_tower.creatable.train_locations[0].hot_key_id = 16156
                fire_tower.name = 'Fire Tower'
                civ.units.append(fire_tower)

                # 23: Junk
                junk = copy.deepcopy(DATA.civs[1].units[17])
                junk.language_dll_name = 5092
                junk.language_dll_creation = 6092
                junk.creatable.train_locations = DATA.civs[1].units[17].creatable.train_locations
                junk.creatable.resource_costs = DATA.civs[1].units[17].creatable.resource_costs
                junk.hit_points = 75
                junk.speed = 1.45
                junk.line_of_sight = 6
                junk.bird.search_radius = 6
                junk.type_50.armours[1].amount = 6
                junk.creatable.displayed_pierce_armor = 6
                junk.bird.work_rate = 1
                junk.name = 'Junk'
                civ.units.append(junk)
                #replace_graphics_for_civs([-1], [len(DATA.civs[1].units)-1], [15])

                # 24: Imperial Steppe Lancer
                imperial_steppe_lancer = copy.deepcopy(DATA.civs[1].units[1372])
                change_string(130000, 'Imperial Steppe Lancer')
                change_string(131000, 'Create Imperial Steppe Lancer')
                imperial_steppe_lancer.language_dll_name = 130000
                imperial_steppe_lancer.language_dll_creation = 131000
                imperial_steppe_lancer.creatable.train_locations = DATA.civs[1].units[17].creatable.train_locations
                imperial_steppe_lancer.creatable.resource_costs = DATA.civs[1].units[17].creatable.resource_costs
                imperial_steppe_lancer.type_50.attacks[0].amount = 13
                imperial_steppe_lancer.type_50.displayed_attack = 13
                imperial_steppe_lancer.hit_points = 100
                imperial_steppe_lancer.type_50.armours[0].amount = 2
                imperial_steppe_lancer.type_50.armours[1].amount = 3
                imperial_steppe_lancer.type_50.displayed_melee_armour = 2
                imperial_steppe_lancer.creatable.displayed_pierce_armor = 3
                imperial_steppe_lancer.name = 'Imperial Steppe Lancer'
                civ.units.append(imperial_steppe_lancer)

                # 25: Scout Cavalry
                scout_cavalry = copy.deepcopy(DATA.civs[1].units[448])
                scout_cavalry.creatable.train_locations.append(genieutils.unit.TrainLocation(26, 1897, 1, 16675))
                civ.units.append(scout_cavalry)

                # 26: Light Cavalry
                light_cavalry = copy.deepcopy(DATA.civs[1].units[546])
                light_cavalry.creatable.train_locations.append(genieutils.unit.TrainLocation(26, 1897, 1, 16675))
                civ.units.append(light_cavalry)

                # 27: Hussar
                hussar = copy.deepcopy(DATA.civs[1].units[441])
                hussar.creatable.train_locations.append(genieutils.unit.TrainLocation(26, 1897, 1, 16675))
                civ.units.append(hussar)

                # EDIT: Qizilbash Warrior / Elite Qizilbash Warrior
                for i in range(len(DATA.civs)):
                    qizilbash_warrior = DATA.civs[i].units[1817]
                    qizilbash_warrior.type_50.max_range = 1
                    qizilbash_warrior.type_50.displayed_range = 1
                    elite_qizilbash_warrior = DATA.civs[i].units[1829]
                    elite_qizilbash_warrior.type_50.max_range = 1
                    elite_qizilbash_warrior.type_50.displayed_range = 1

                # Cavalry Archer Scout
                '''cavalry_archer_scout = copy.deepcopy(DATA.civs[1].units[448])
                change_string(130000, 'Cavalry Archer Scout')
                change_string(131000, 'Create Cavalry Archer Scout')
                cavalry_archer_scout.language_dll_name = 130000
                cavalry_archer_scout.language_dll_creation = 131000
                cavalry_archer_scout.type_50.max_range = 2
                cavalry_archer_scout.type_50.displayed_range = 2
                cavalry_archer_scout.speed = 1.1
                cavalry_archer_scout.type_50.attacks[1].class_ = 3
                cavalry_archer_scout.type_50.accuracy_percent = 35
                cavalry_archer_scout.type_50.armours[2].amount = 0
                cavalry_archer_scout.creatable.displayed_pierce_armor = 0
                cavalry_archer_scout.name = 'Cavalry ArcherScout'
                civ.units.append(cavalry_archer_scout)
                print(len(DATA.civs[1].units)-1)
                replace_graphics_for_civs([-1], [len(DATA.civs[1].units)-1], [2308])

                # Edit current effects for the Scout Cavalry Archer
                DATA.effects[16].effect_commands.append(genieutils.effect.EffectCommand(4, get_unit_id('cavalry archer scout', False), -1, 1, 2))
                DATA.effects[16].effect_commands.append(genieutils.effect.EffectCommand(4, get_unit_id('cavalry archer scout', False), -1, 5, 0.25))
                DATA.effects[16].effect_commands.append(genieutils.effect.EffectCommand(4, get_unit_id('cavalry archer scout', False), -1, 23, 2))
                DATA.effects[16].effect_commands.append(genieutils.effect.EffectCommand(4, get_unit_id('cavalry archer scout', False), -1, 12, 1))
                DATA.effects[16].effect_commands.append(genieutils.effect.EffectCommand(4, get_unit_id('cavalry archer scout', False), -1, 47, 1))
                DATA.effects[102].effect_commands.append(genieutils.effect.EffectCommand(3, get_unit_id('cavalry archer scout', False), 39, -1, -1))'''

                # Yurt
                '''yurt = copy.deepcopy(DATA.civs[1].units[1835])
                change_string(118000, 'Yurt')
                change_string(119000, 'Build Yurt')
                change_string(120000, r'Build <b>Yurt<b> (<cost>)\nNomadic house that can be packed and unpacked. Provides 15 population. Your current/supportable population is shown at the top of the screen.\n<GREY><i>Upgrades: line of sight (Town Center); HP, armor (University); more resistant to Monks (Monastery).<i><DEFAULT>')
                yurt.language_dll_name = 118000
                yurt.language_dll_creation = 119000
                yurt.language_dll_help = 120000 + 79000
                yurt.hit_points = 250
                yurt.resource_storages[0].amount = 15
                yurt.standing_graphic = civ.units[712].standing_graphic
                yurt.dying_graphic = civ.units[712].dying_graphic
                yurt.undead_graphic = civ.units[712].undead_graphic
                yurt.dead_fish.walking_graphic = civ.units[712].dead_fish.walking_graphic
                yurt.dead_fish.running_graphic = civ.units[712].dead_fish.running_graphic
                yurt.type_50.attack_graphic = civ.units[712].type_50.attack_graphic
                yurt.type_50.attack_graphic_2 = civ.units[712].type_50.attack_graphic_2
                yurt.name = 'Yurt'
                yurt.class_ = 54
                yurt.creatable.train_locations[0].unit_id = 118
                yurt.creatable.train_locations[0].train_time = 12
                civ.units.append(yurt)

                # Yurt (Packed)
                yurt_packed = copy.deepcopy(DATA.civs[1].units[1271])
                change_string(121000, 'Yurt (Packed)')
                yurt_packed.language_dll_name = 121000
                yurt_packed.language_dll_creation = 119000
                yurt_packed.language_dll_help = 120000 + 79000
                yurt_packed.hit_points = 250
                yurt_packed.resource_storages[0].amount = 0
                #yurt_packed.building.transform_unit = civ.units.index(yurt)
                #yurt.building.transform_unit = yurt_packed.building.transform_unit-1
                yurt_packed.name = 'Yurt (Packed)'
                yurt_packed.class_ = 51
                yurt_packed.creatable.train_locations[0].train_time = 8
                civ.units.append(yurt_packed)'''

        def create_talofa_techs(self):
            # Create techs unique to Talofa
            global CUSTOM_TECH_STARTING_INDEX, CUSTOM_EFFECT_STARTING_INDEX
            CUSTOM_TECH_STARTING_INDEX = len(DATA.techs)
            CUSTOM_EFFECT_STARTING_INDEX = len(DATA.effects)

            # 0: Canoe
            canoe_tech = copy.deepcopy(DATA.techs[151])
            canoe_tech.name = 'Canoe (make avail)'
            canoe_effect = genieutils.effect.Effect(name='Canoe (make avail)', effect_commands=[genieutils.effect.EffectCommand(3, 539, CUSTOM_UNIT_STARTING_INDEX, -1, -1)])
            DATA.effects.append(canoe_effect)
            canoe_tech.effect_id = len(DATA.effects)-1
            DATA.techs.append(canoe_tech)

            # 1: War Canoe
            war_canoe_tech = copy.deepcopy(DATA.techs[0])
            war_canoe_tech.name = 'War Canoe'
            #change_string(84000, 'War Canoe')
            #change_string(85000, 'Upgrade to War Canoe')
            #change_string(86000, r'Upgrade to <b>War Canoe<b> (<cost>)\nUpgrades your Canoes and lets you create War Canoes, which are stronger.')
            #war_canoe_tech.language_dll_name = 84000
            #war_canoe_tech.language_dll_description = 85000
            #war_canoe_tech.language_dll_help = 86000
            war_canoe_tech.required_techs = (34, -1, -1, -1, -1, -1)
            war_canoe_tech.required_tech_count = 1
            #war_canoe_tech.resource_costs[0].amount = 200
            #war_canoe_tech.resource_costs[0].type = 1
            #war_canoe_tech.resource_costs[1].amount = 100
            #war_canoe_tech.research_locations[0].research_time = 30
            #war_canoe_tech.icon_id = 105
            war_canoe_effect = genieutils.effect.Effect(name='War Canoe', effect_commands=[genieutils.effect.EffectCommand(3, 539, CUSTOM_UNIT_STARTING_INDEX+1, -1, -1), genieutils.effect.EffectCommand(3, CUSTOM_UNIT_STARTING_INDEX, CUSTOM_UNIT_STARTING_INDEX+1, -1, -1)])
            DATA.effects.append(war_canoe_effect)
            war_canoe_tech.effect_id = len(DATA.effects)-1
            DATA.techs.append(war_canoe_tech)

            # 2: Elite War Canoe
            elite_war_canoe_tech = copy.deepcopy(DATA.techs[0])
            elite_war_canoe_tech.name = 'Elite War Canoe'
            #change_string(81000, 'Elite War Canoe')
            #change_string(82000, 'Upgrade to Elite War Canoe')
            #change_string(83000, r'Upgrade to <b>Elite War Canoe<b> (<cost>)\nUpgrades your War Canoes and lets you create Elite War Canoes, which are stronger.')
            #elite_war_canoe_tech.language_dll_name = 81000
            #elite_war_canoe_tech.language_dll_description = 82000
            #elite_war_canoe_tech.language_dll_help = 83000
            elite_war_canoe_tech.required_techs = (35, -1, -1, -1, -1, -1)
            elite_war_canoe_tech.required_tech_count = 1
            #elite_war_canoe_tech.resource_costs[0].amount = 300
            #elite_war_canoe_tech.resource_costs[1].amount = 250
            #elite_war_canoe_tech.research_locations[0].research_time = 45
            #elite_war_canoe_tech.icon_id = 105
            elite_war_canoe_effect = genieutils.effect.Effect(name='Elite War Canoe', effect_commands=[genieutils.effect.EffectCommand(3, 539, CUSTOM_UNIT_STARTING_INDEX+2, -1, -1), genieutils.effect.EffectCommand(3, CUSTOM_UNIT_STARTING_INDEX, CUSTOM_UNIT_STARTING_INDEX+2, -1, -1), genieutils.effect.EffectCommand(3, CUSTOM_UNIT_STARTING_INDEX+1, CUSTOM_UNIT_STARTING_INDEX+2, -1, -1)])
            DATA.effects.append(elite_war_canoe_effect)
            elite_war_canoe_tech.effect_id = len(DATA.effects)-1
            DATA.techs.append(elite_war_canoe_tech)

            for civ_id, civ in enumerate(DATA.civs):
                if (CANOES_MESOAMERICAN and civ_id not in [15, 16, 21]) or (CANOES_SEA and REPLACE_3KINGDOMS and civ_id not in [28, 29, 50]) or (CANOES_SEA and not REPLACE_3KINGDOMS and civ_id not in [28, 29]) or (CANOES_OTHER and civ_id not in [17, 26, 34]):
                    DATA.effects[int(civ.resources[571])].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, CUSTOM_TECH_STARTING_INDEX+0))
                    DATA.effects[int(civ.resources[571])].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, CUSTOM_TECH_STARTING_INDEX+1))
                    DATA.effects[int(civ.resources[571])].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, CUSTOM_TECH_STARTING_INDEX+2))

            # 3: Junk
            junk_tech = copy.deepcopy(DATA.techs[0])
            junk_tech.name = 'Junk (make avail)'
            junk_effect = genieutils.effect.Effect(name='Junk (make avail)', effect_commands=[genieutils.effect.EffectCommand(3, 17, CUSTOM_UNIT_STARTING_INDEX+21, -1, -1)])
            DATA.effects.append(junk_effect)
            junk_tech.effect_id = len(DATA.effects)-1
            DATA.techs.append(junk_tech)
            DATA.effects[482].effect_commands.append(genieutils.effect.EffectCommand(5, CUSTOM_UNIT_STARTING_INDEX+21, -1, 5, 1.2))
            DATA.effects[482].effect_commands.append(genieutils.effect.EffectCommand(5, CUSTOM_UNIT_STARTING_INDEX+21, -1, 13, 1.2))
            for civ_id, civ in enumerate(DATA.civs):
                if civ_id not in [5, 6, 12, 18, 28, 29, 30, 31, 50] or (REPLACE_3KINGDOMS and civ_id not in [49, 51]):
                    DATA.effects[int(civ.resources[571])].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, CUSTOM_TECH_STARTING_INDEX+3))

            # 1008: Pasture
            for civ_id, civ in enumerate(DATA.civs):
                if (REPLACE_3KINGDOMS and civ_id in [12, 17, 27, 34, 49, 51, 53]) or (not REPLACE_3KINGDOMS and civ_id in [12, 17, 27, 34, 53]):
                    DATA.effects[int(civ.resources[571])].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 1008))
                    
                    # Disable farm upgrades if farm is disabled
                    DATA.effects[int(civ.resources[571])].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 14))
                    DATA.effects[int(civ.resources[571])].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 13))
                    DATA.effects[int(civ.resources[571])].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 12))
                else:
                    # Disable pasture upgrades if pasture is disabled
                    print(f"Disabled for {civ.name}.")
                    DATA.effects[int(civ.resources[571])].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 1014))
                    DATA.effects[int(civ.resources[571])].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 1013))
                    DATA.effects[int(civ.resources[571])].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 1012))

            # 4: Imperial Steppe Lancer
            '''imperial_steppe_lancer_tech = copy.deepcopy(DATA.techs[715])
            imperial_steppe_lancer_tech.name = 'Imperial Steppe Lancer'''

            '''imperial_elephant_archer_tech = copy.deepcopy(DATA.techs[481])
            change_string(87000, 'Imperial Elephant Archer')
            change_string(88000, 'Upgrade to Imperial Elephant Archer')
            change_string(89000, r'Upgrade to <b>Imperial Elephant Archer<b> (<cost>)\nUpgrades your Elite Elephant Archers and lets you create Imperial Elephant Archers, which are stronger.')
            imperial_elephant_archer_tech.language_dll_name = 87000
            imperial_elephant_archer_tech.language_dll_description = 88000
            imperial_elephant_archer_tech.language_dll_help = 89000
            imperial_elephant_archer_tech.required_techs = (103, 481, -1, -1, -1, -1)
            imperial_elephant_archer_tech.resource_costs[0].amount = 1000
            imperial_elephant_archer_tech.resource_costs[1].amount = 800
            imperial_elephant_archer_tech.research_locations[0].research_time = 110
            imperial_elephant_archer_tech.civ = -1
            DATA.techs.append(imperial_elephant_archer_tech)'''

            # Disable Canoes and Pastures for all civs
            for civ in DATA.civs:
                tech_tree_index = int(civ.resources[571])
                DATA.effects[tech_tree_index].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, CUSTOM_TECH_STARTING_INDEX))
                DATA.effects[tech_tree_index].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, CUSTOM_TECH_STARTING_INDEX + 1))
                DATA.effects[tech_tree_index].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, CUSTOM_TECH_STARTING_INDEX + 2))
                DATA.effects[tech_tree_index].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 1008))

        def edit_unique_units(self):
            # Create new unique Castle unit techs and effects
            for i, tech_id in enumerate([263, 360, 275, 363, 399, 398, 276, 364, 262, 366, 268, 362, 267, 361, 274, 367, 269, 368, 271, 369, 446, 365, 273, 371, 277, 370, 58, 60, 431, 432, 26, 27, 1, 2, 449, 450, 467, 468, 839, 840, 508, 509, 471, 472, 503, 504, 562, 563, 568, 569, 566, 567, 564, 565, 614, 615, 616, 617, 618, 619, 620, 621, 677, 678, 679, 680, 681, 682, 683, 684, 750, 751, 752, 753, 778, 779, 780, 781, 825, 826, 827, 828, 829, 830, 881, 882, 917, 918, 919, 920, 990, 991, 1001, 1002, 1063, 1064, 1035, 1036, 1073, 1074]):
                if i % 2 == 0: # Castle unit techs
                    DATA.techs[tech_id].name = f'{DATA.civs[DATA.techs[tech_id].civ].name.upper()}: (Castle Unit)'
                    DATA.effects[DATA.techs[tech_id].effect_id].name = f'{DATA.civs[DATA.techs[tech_id].civ].name.upper()}: (Castle Unit)'
                else: # Imperial unit techs
                    DATA.techs[tech_id].name = f'{DATA.civs[DATA.techs[tech_id].civ].name.upper()}: (Imperial Unit)'
                    DATA.effects[DATA.techs[tech_id].effect_id].name = f'{DATA.civs[DATA.techs[tech_id].civ].name.upper()}: (Imperial Unit)'

        def reformat_bonuses(self):
            # Rename existing bonuses (DELETE ONCE NEXT BLOCK IS COMPLETE)
            for i, tech in enumerate(DATA.techs):
                if tech.name.startswith(('C-Bonus,', 'C-Bonus')):
                    tech.name = tech.name.replace('C-Bonus,', f'{DATA.civs[tech.civ].name.upper()}:').replace('C-Bonus', f'{DATA.civs[tech.civ].name.upper()}:')

                # Try to rename the effect as well
                DATA.effects[tech.effect_id].name = DATA.effects[tech.effect_id].name.replace('C-Bonus,', f'{DATA.civs[tech.civ].name.upper()}:').replace('C-Bonus', f'{DATA.civs[tech.civ].name.upper()}:')

            # Update the names of preexisting bonuses
            preexisting_bonuses = {
                # Britons
                383: r'BRITONS: Shepherds work 25% faster',
                381: r'BRITONS: Town Centers cost -50% wood starting in the Castle Age',
                382: r'BRITONS: Foot archers +1/+2 range in the Castle/Imperial age',
                403: r'BRITONS: Foot archers +1/+2 range in the Castle/Imperial age',
                # Franks
                325: r'FRANKS: Castles cost -15/25% in Castle/Imperial Age',
                330: r'FRANKS: Castles cost -15/25% in Castle/Imperial Age',
                290: r'FRANKS: Mounted Units +20% HP starting in Feudal Age',
                524: r'FRANKS: Foragers work +15% faster',
                # Goths
                344: r'GOTHS: Infantry costs -15/20/25/30% in Dark/Feudal/Castle/Imperial Age',
                731: r'GOTHS: Infantry costs -15/20/25/30% in Dark/Feudal/Castle/Imperial Age',
                732: r'GOTHS: Infantry costs -15/20/25/30% in Dark/Feudal/Castle/Imperial Age',
                733: r'GOTHS: Infantry costs -15/20/25/30% in Dark/Feudal/Castle/Imperial Age',
                327: r'GOTHS: Infantry +1/+2/+3 attack vs. buildings in Feudal/Castle/Imperial Age',
                328: r'GOTHS: Infantry +1/+2/+3 attack vs. buildings in Feudal/Castle/Imperial Age',
                329: r'GOTHS: Infantry +1/+2/+3 attack vs. buildings in Feudal/Castle/Imperial Age',
                402: r'GOTHS: Villagers +5 attack vs. wild boar; hunters carry +15; hunted animals last +20% longer',
                343: r'GOTHS: Loom is researched instantly',
                406: r'GOTHS: +10 population space in Imperial Age',
                # Teutons
                314: r'TEUTONS: Farms cost -40%',
                336: r'TEUTONS: Town Centers +10 garrison capacity; Towers +5 garrison capacity',
                353: r'TEUTONS: Town Centers +10 garrison capacity; Towers +5 garrison capacity',
                334: r'TEUTONS: Barracks and Stable units +1/+2 melee armor in Castle/Imperial Age',
                335: r'TEUTONS: Barracks and Stable units +1/+2 melee armor in Castle/Imperial Age',
                347: r'TEUTONS: Monks +100% healing range',
                # Japanese:
                340: r'JAPANESE: Mills, Lumber- and Mining Camps cost -50%',
                341: r'JAPANESE: Infantry attacks +33% faster starting in Feudal Age',
                190: r'JAPANESE: Cavalry Archers +2 attack vs. Ranged Soldiers (except Skirmishers)',
                306: r'JAPANESE: Fishing Ships work +5/10/15/20% faster in Dark/Feudal/Castle/Imperial Age; +100 HP And +2 pierce armor',
                422: r'JAPANESE: Fishing Ships work +5/10/15/20% faster in Dark/Feudal/Castle/Imperial Age; +100 HP And +2 pierce armor',
                423: r'JAPANESE: Fishing Ships work +5/10/15/20% faster in Dark/Feudal/Castle/Imperial Age; +100 HP And +2 pierce armor',
                424: r'JAPANESE: Fishing Ships work +5/10/15/20% faster in Dark/Feudal/Castle/Imperial Age; +100 HP And +2 pierce armor',
                # Chinese:
                226: r'CHINESE: Start with +3 Villagers, but -50 wood and -200 food',
                302: r'CHINESE: Start with +3 Villagers, but -50 wood and -200 food',
                350: r'CHINESE: Technologies cost -5/10/15% in Feudal/Castle/Imperial Age',
                351: r'CHINESE: Technologies cost -5/10/15% in Feudal/Castle/Imperial Age',
                352: r'CHINESE: Technologies cost -5/10/15% in Feudal/Castle/Imperial Age',
                425: r'CHINESE: Town Centers +7 line of sight and provide +15 population space',
                983: r'CHINESE: Fire Lancers and Fire Ships move +5/10% faster in Castle/Imperial Age',
                984: r'CHINESE: Fire Lancers and Fire Ships move +5/10% faster in Castle/Imperial Age',
                # Huns
                225: r'HUNS: Do not need houses, but start with -100 wood',
                458: r'HUNS: Cavalry Archers cost -10/20% in Castle/Imperial Age',
                459: r'HUNS: Cavalry Archers cost -10/20% in Castle/Imperial Age',
                238: r'HUNS: On Nomadic maps, the first Town Center spawns a scouting Horse',
                241: r'HUNS: On Nomadic maps, the first Town Center spawns a scouting Horse',
                242: r'HUNS: On Nomadic maps, the first Town Center spawns a scouting Horse',
            }

            for key, value in preexisting_bonuses.items():
                DATA.techs[key].name = value
                DATA.effects[DATA.techs[key].effect_id].name = value

            # Add bonuses techs and effects that didn't previously exist
            base_tech = DATA.techs[0] #genieutils.tech.Tech(name='', required_techs=(0, 0, 0, 0, 0, 0), resource_costs=(ResearchResourceCost(0, 0, 0), ResearchResourceCost(0, 0, 0), ResearchResourceCost(0, 0, 0)), required_tech_count=0, civ=0, full_tech_mode=0, language_dll_name=7000, language_dll_description=8000, effect_id=-1, type=0, icon_id=-1, button_id=0, language_dll_help=107000, language_dll_tech_tree=157000, research_locations=[ResearchLocation(0, 0, 0, 0)], hot_key=-1, repeatable=1)
            base_effect = genieutils.effect.Effect(name='', effect_commands=[])

            for i, civ in enumerate(DATA.civs):
                # Clear the tech and the effect
                missed_tech = copy.deepcopy(base_tech)
                missed_effect = copy.deepcopy(base_effect)

                if i == 2: # Franks
                    missed_tech.name = 'FRANKS: Mill technologies free'
                    missed_effect.name = missed_tech.name
                    for ec_index in reversed(range(26, 35)):
                        missed_effect.effect_commands.append(DATA.effects[258].effect_commands[ec_index])
                        DATA.effects[258].effect_commands.pop(ec_index)

                elif i == 4: # Teutons
                    missed_tech.name = 'TEUTONS: Murder Holes, Herbal Medicine free'
                    missed_effect.name = missed_tech.name
                    for ec_index in reversed([23, 24, 25, 30, 31]):
                        missed_effect.effect_commands.append(DATA.effects[262].effect_commands[ec_index])
                        DATA.effects[262].effect_commands.pop(ec_index)

                elif i == 17: # Huns
                    missed_tech.name = 'HUNS: Trebuchets fire more accurately at units and small targets'
                    missed_effect.name = missed_tech.name
                    missed_effect.effect_commands = [genieutils.effect.EffectCommand(4, 42, -1, 11, 35)]

                # Add the tech and the effect
                missed_tech.civ = i
                DATA.techs.append(missed_tech)
                DATA.effects.append(missed_effect)
                    

            # Remake the bonuses so that they're compact
            # HUNS
            DATA.effects[214].effect_commands.append(genieutils.effect.EffectCommand(1, 4, 1, -1, 2000)) # Huns: Do not need houses, but start with -100 wood
            DATA.effects[214].effect_commands.append(genieutils.effect.EffectCommand(2, 70, 0, -1, 0))
            DATA.effects[448].effect_commands.remove(genieutils.effect.EffectCommand(2, 70, 0, -1, 0))
            DATA.effects[448].effect_commands.remove(genieutils.effect.EffectCommand(1, 4, 1, -1, 2000))
            DATA.effects[448].effect_commands.remove(genieutils.effect.EffectCommand(4, 42, -1, 11, 35))

        def tweak_graphics(self):
            # Units affected by each group (same as your menu)
            unit_banks = {
                0: [20, 132, 498, 1413, 1414, 10, 14, 87, 1415, 1416, 86, 101, 153, 1102, 1417, 1418, 49, 150, 1425, 1426, 18, 19, 103, 105, 1419, 1420, 47, 51, 133, 806, 807, 808, 2120, 2121, 2122, 2144, 2145, 2146, 209, 210, 1427, 1428, 79, 190, 234, 236, 235, 82, 1430, 191, 192, 463, 464, 465, 1434, 1435, 71, 141, 142, 444, 481, 482, 483, 484, 597, 611, 612, 613, 614, 615, 616, 617, 584, 585, 586, 587, 562, 563, 564, 565, 84, 116, 137, 1422, 1423, 1424, 1646, 129, 130, 131, 1411, 1412, 117, 155, 1508, 1509, 63, 64, 67, 78, 80, 81, 85, 88, 90, 91, 92, 95, 487, 488, 490, 491, 659, 660, 661, 662, 663, 664, 665, 666, 667, 668, 669, 670, 671, 672, 673, 674, 1192, 1406, 1500, 1501, 1502, 1503, 1504, 1505, 1506, 1507, 110, 179, 1647],            # General (all)
                1: [82, 1430],                                   # Castle units (building and rubble)
                2: [276, 1445],                                  # Wonder units
                3: [125, 286, 922, 1025, 1327],                  # Monk units (variants)
                4: [30, 31, 32, 104, 1421],                      # Monastery buildings
                5: [128, 204],                                   # Trade carts
                6: [1103, 529, 532, 545, 17, 420, 691,           # Ships: fire, galley, demo, transport, fish, CG, etc.
                    1104, 527, 528, 539, 21, 442]
            }

            # (General, Castle, Wonder, Monk, Monastery, Trade Cart, Ships)
            civ_presets = {
                1:  [-1, -1, -1, -1, -1, -1, -1],
                2:  [-1, -1, -1, 19, -1, -1, -1],
                3:  [19, -1, -1, -1, 19, -1, 19],
                4:  [-1, -1, -1, -1, -1, -1, -1],
                5:  [-1, -1, -1, -1, -1, -1, -1],
                6:  [-1, 49, -1, -1, -1, -1, -1], # Chinese
                7:  [47, -1, -1, -1, -1, -1, -1], # Byzantines
                8:  [33, -1, -1, -1, 33, 1, 33], # Persians
                9:  [-1, -1, -1, -1, -1, -1, -1],
                10: [-1, -1, -1, -1, -1, -1, -1],
                11: [-1, -1, -1, -1, -1, -1, -1],
                12: [-1, -1, -1, -1, -1, 1, -1],
                13: [-1, -1, -1, 19, -1, -1, -1],
                14: [-1, -1, -1, -1, -1, -1, -1],
                15: [-1, -1, -1, -1, -1, -1, -1],
                16: [-1, -1, -1, -1, -1, -1, -1],
                17: [-1, -1, -1, -1, -1, 1, -1],
                18: [-1, -1, -1, -1, -1, -1, -1],
                19: [-1, -1, -1, -1, -1, -1, -1],
                20: [9, -1, -1, -1, 9, 9, 9], # Hindustanis
                21: [-1, -1, -1, -1, -1, -1, -1],
                22: [4, -1, -1, -1, 4, -1, 4],
                23: [-1, -1, -1, -1, -1, -1, -1],
                24: [-1, -1, -1, -1, -1, -1, -1],
                25: [26, -1, -1, -1, -1, -1, -1],
                26: [-1, -1, -1, 9, -1, 9, -1],
                27: [26, -1, -1, -1, -1, 9, -1],
                28: [-1, -1, -1, 40, -1, -1, -1],
                29: [-1, -1, -1, 9, -1, -1, -1],
                30: [-1, -1, -1, 5, -1, -1, -1],
                31: [-1, -1, -1, -1, -1, -1, -1],
                32: [55, -1, -1, 5, -1, -1, 28], # Bulgarians
                33: [-1, -1, -1, -1, -1, 1, -1],
                34: [-1, -1, -1, -1, -1, 1, -1],
                35: [4, -1, -1, -1, -1, -1, 4],
                36: [-1, -1, -1, -1, -1, -1, -1],
                37: [-1, -1, -1, -1, -1, -1, -1],
                38: [4, -1, -1, -1, 4, -1, 4],
                39: [-1, -1, -1, -1, -1, -1, -1],
                40: [56, -1, -1, -1, -1, 6, -1], # Dravidians
                41: [56, -1, -1, 9, -1, -1, -1], # Bengalis
                42: [-1, -1, -1, 40, -1, 9, -1], # Gurjaras
                43: [-1, -1, -1, -1, -1, -1, -1], # Romans
                44: [55, -1, -1, -1, -1, -1, -1], # Armenians
                45: [55, -1, -1, -1, -1, -1, -1], # Georgians
                49: [42, 50, 49, 6, 6, 6, 6], # Tibetans (Shu)
                50: [-1, 6, 50, 6, 6, 6, -1], # Bai (Wu)
                51: [-1, 53, 53, -1, 6, 1, -1], # Tanguts (Wei)
                52: [-1, -1, -1, -1, 6, 1, -1], # Jurchens
                53: [-1, 51, 51, -1, -1, 1, -1], # Khitans
                # (General, Castle, Wonder, Monk, Monastery, Trade Cart, Ships)
            }

            # Define the special units
            special_unit_ids = [uid for key in unit_banks for uid in unit_banks[key]]

            for civ_id, presets in civ_presets.items():
                for key, unit_bank in unit_banks.items():
                    source_civ = presets[key]
                    if source_civ == -1:
                        continue  # skip this whole architecture group

                    for unit_id in unit_bank:
                        # Apply only if:
                        # - General group (key 0) and unit is NOT a special unit, OR
                        # - Any other key (>0)
                        if (key == 0 and unit_id not in special_unit_ids) or key > 0:
                            DATA.civs[civ_id].units[unit_id] = ARCHITECTURE_SETS[source_civ][unit_id]

        def get_tech_trees(self):
            for i, effect in enumerate(DATA.effects):
                if 'tech tree' not in effect.name.lower():
                    continue

                # Get the associated civ
                tech_tree_civ_name = effect.name.split(' ')[0]

                # Find matching civ ID (index in DATA.civs)
                civ_id = next(
                    (j for j, civ in enumerate(DATA.civs) if civ.name.lower() == tech_tree_civ_name.lower()),
                    None
                )

                # Skip ignored civs
                if civ_id in IGNORED_CIVS or civ_id is None:
                    continue

                # Record tech tree index
                DATA.civs[civ_id].resources[571] = i

        def edit_tech_trees(self):
            # Edit tech trees for rebalancing/realism
            def edit_tech_tree(tech_tree_id, effect_ids):
                if tech_tree_id == -1:
                    print('No tech tree found')
                    return
                
                for effect_id in effect_ids:
                    if effect_id < 0 and genieutils.effect.EffectCommand(102, -1, -1, -1, abs(effect_id)) not in DATA.effects[tech_tree_id].effect_commands:
                        # Disable unit
                        DATA.effects[tech_tree_id].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, abs(effect_id)))
                    else:
                        # Enable unit
                        for y, ec in enumerate(DATA.effects[tech_tree_id].effect_commands):
                            if ec.type == 102 and ec.d == effect_id:
                                DATA.effects[tech_tree_id].effect_commands.pop(y)
            
            # Make specific edits to the tech tree
            edit_tech_tree(get_effect_id('Malay Tech Tree'), [-192, -218, 480, 481, -162, -96, -255, 837, 838])
            edit_tech_tree(get_effect_id('Burmese Tech Tree'), [-192, -218, 480, 481, -162, -96, -255, 837, -838])
            edit_tech_tree(get_effect_id('Khmer Tech Tree'), [-192, -218, 480, 481, -162, -96, -255, 837, -838])
            edit_tech_tree(get_effect_id('Vietnamese Tech Tree'), [-162, -96, -255, 837, 838, -37, -376, 1034])
            edit_tech_tree(get_effect_id('Vikings Tech Tree'), [-37, -376, 886])
            edit_tech_tree(get_effect_id('Bulgarians Tech Tree'), [-37, -376, 886])
            edit_tech_tree(get_effect_id('Persians Tech Tree'), [630, 631])
            edit_tech_tree(get_effect_id('Khitans Tech Tree'), [216, -1005, 1008])
            edit_tech_tree(get_effect_id('Mongols Tech Tree'), [1008])
            edit_tech_tree(get_effect_id('Berbers Tech Tree'), [1008])
            edit_tech_tree(get_effect_id('Huns Tech Tree'), [1008])
            edit_tech_tree(get_effect_id('Cumans Tech Tree'), [1008])
            if CANOES_MESOAMERICAN:
                edit_tech_tree(get_effect_id('Aztecs Tech Tree'), [-604, -243, -246, -605, -244, -37, -376, 35, CUSTOM_TECH_STARTING_INDEX, CUSTOM_TECH_STARTING_INDEX+1, CUSTOM_TECH_STARTING_INDEX+2])
                edit_tech_tree(get_effect_id('Maya Tech Tree'), [-604, -243, -246, -605, -244, -37, -376, 35, CUSTOM_TECH_STARTING_INDEX, CUSTOM_TECH_STARTING_INDEX+1, CUSTOM_TECH_STARTING_INDEX+2])
                edit_tech_tree(get_effect_id('Inca Tech Tree'), [-604, -243, -246, -605, -244, -37, -376, 35, CUSTOM_TECH_STARTING_INDEX, CUSTOM_TECH_STARTING_INDEX+1, CUSTOM_TECH_STARTING_INDEX+2])
            if CANOES_SEA:
                edit_tech_tree(get_effect_id('Malay Tech Tree'), [-604, -243, -246, -605, -244, -37, -376, 35, CUSTOM_TECH_STARTING_INDEX, CUSTOM_TECH_STARTING_INDEX+1, CUSTOM_TECH_STARTING_INDEX+2])
                edit_tech_tree(get_effect_id('Khmer Tech Tree'), [-604, -243, -246, -605, -244, -37, -376, 35, CUSTOM_TECH_STARTING_INDEX, CUSTOM_TECH_STARTING_INDEX+1, CUSTOM_TECH_STARTING_INDEX+2])
            elif CANOES_SEA and REPLACE_3KINGDOMS:
                edit_tech_tree(get_effect_id('Bai Tech Tree'), [-604, -243, -246, -605, -244, -37, -376, 35, CUSTOM_TECH_STARTING_INDEX, CUSTOM_TECH_STARTING_INDEX+1, CUSTOM_TECH_STARTING_INDEX+2])
            if CANOES_OTHER:
                edit_tech_tree(get_effect_id('Cumans Tech Tree'), [-604, -243, -246, -605, -244, -37, -376, 35, CUSTOM_TECH_STARTING_INDEX, CUSTOM_TECH_STARTING_INDEX+1, CUSTOM_TECH_STARTING_INDEX+2])
                edit_tech_tree(get_effect_id('Malians Tech Tree'), [-604, -243, -246, -605, -244, -37, -376, 35, CUSTOM_TECH_STARTING_INDEX, CUSTOM_TECH_STARTING_INDEX+1, CUSTOM_TECH_STARTING_INDEX+2])
                edit_tech_tree(get_effect_id('Huns Tech Tree'), [-604, -243, -246, -605, -244, -37, -376, 35, CUSTOM_TECH_STARTING_INDEX, CUSTOM_TECH_STARTING_INDEX+1, CUSTOM_TECH_STARTING_INDEX+2])

        def replace_3kingdoms_civs(self):
            def replace_civ(
            old_civ_id: int,
            new_civ_id: int,
            new_name: str,
            new_description: str,
            unique_unit_ids: tuple[int, int],  # (castle_unit_id, imperial_upgrade_id)
            new_unique_techs: list[dict],      # [{"id": id, "name": str, "desc": str, "help": str, "commands": [...], "costs": {res_id: amount, ...}, "research_time": int}, ...]
            team_bonus_commands: list,         # [EffectCommand, ...]
            new_bonuses: list[dict],           # [{"name": str, "required_techs": tuple, "commands": [...]}, ...]
            string_indexes: tuple[int, int],   # (name_string_id, description_string_id)
            disabled_techs: list[int],         # tech IDs to disable
            castle_tech_config: dict = None,   # {"id": int, "costs": {0: food, 1: wood, 2: stone, 3: gold}, "research_time": t}
            imperial_tech_config: dict = None, # {"id": int, "costs": {0: food, 1: wood, 2: stone, 3: gold}, "research_time": t}
            ):
                # -----------------------
                # helpers
                # -----------------------
                def set_resource_costs(tech_obj, costs_dict: dict):
                    """
                    costs_dict keys are resource IDs: 0=food, 1=wood, 2=stone, 3=gold.
                    Updates existing slots by matching .type; if a type is missing, appends a new slot.
                    """
                    if not costs_dict:
                        return
                    # Update existing types
                    remaining = dict(costs_dict)  # copy
                    for rc in tech_obj.resource_costs:
                        if rc.type in remaining:
                            rc.amount = remaining.pop(rc.type)

                    # Append new slots for any resource types not present
                    for res_id, amount in remaining.items():
                        # genieutils.unit.ResourceCost constructor name can vary by binding; adapt if needed
                        tech_obj.resource_costs += (
                            genieutils.unit.ResourceCost(type=res_id, amount=amount, flag=1),
                        )

                    # Optional: zero out any slots with type == -1 if they exist (keeps things clean)
                    # for rc in tech_obj.resource_costs:
                    #     if rc.type == -1:
                    #         rc.amount = 0
                    #         rc.flag = 0

                def set_research_time(tech_obj, t: int):
                    """Be tolerant of schema differences: set both common places."""
                    try:
                        tech_obj.research_time = t
                    except Exception:
                        pass
                    try:
                        if getattr(tech_obj, "research_locations", None):
                            tech_obj.research_locations[0].research_time = t
                    except Exception:
                        pass

                # -----------------------
                # Civ name swap
                # -----------------------
                old_name = DATA.civs[new_civ_id].name
                DATA.civs[new_civ_id].name = new_name

                for tech in DATA.techs:
                    if tech.name == f'{old_name.upper()}: (Castle Unit)':
                        tech.name = f'{new_name.upper()}: (Castle Unit)'
                        # Force castle unique unit assignment
                        for effect in DATA.effects:
                            if effect.name == f'{old_name.upper()}: (Castle Unit)':
                                effect.name = f'{new_name.upper()}: (Castle Unit)'
                                if unique_unit_ids and len(unique_unit_ids) >= 1:
                                    effect.effect_commands[0].a = unique_unit_ids[0]

                    elif tech.name == f'{old_name.upper()}: (Imperial Unit)':
                        tech.name = f'{new_name.upper()}: (Imperial Unit)'
                        # Force imperial upgrade assignment
                        for effect in DATA.effects:
                            if effect.name == f'{old_name.upper()}: (Imperial Unit)':
                                effect.name = f'{new_name.upper()}: (Imperial Unit)'
                                if unique_unit_ids and len(unique_unit_ids) >= 2:
                                    effect.effect_commands[0].a = unique_unit_ids[0]
                                    effect.effect_commands[0].b = unique_unit_ids[1]

                    elif tech.civ == new_civ_id and ':' in tech.name:
                        tech.effect_id = -1
                        tech.name = f'DISABLED: {tech.name.split(":")[1]}'

                # --- Effects cleanup ---
                for effect in DATA.effects:
                    effect.name = effect.name.replace(DATA.civs[old_civ_id].name.upper(), "DISABLED")
                    effect.name = effect.name.replace(DATA.civs[old_civ_id].name, "Disabled")

                    # --- Tech Tree handling ---
                    if effect.name == f'{old_name.title()} Tech Tree':
                        effect.name = f'{new_name.title()} Tech Tree'
                        effect.effect_commands.clear()
                        for tech_id in disabled_techs:
                            effect.effect_commands.append(
                                genieutils.effect.EffectCommand(102, -1, -1, -1, tech_id)
                            )

                    # --- Team Bonus handling ---
                    elif effect.name == f'{old_name.title()} Team Bonus':
                        effect.name = f'{new_name.title()} Team Bonus'
                        effect.effect_commands.clear()
                        effect.effect_commands.extend(team_bonus_commands)

                    # --- Castle Unit handling ---
                    elif effect.name == f"{old_name.upper()}: (Castle Unit)":
                        effect.name = f"{new_name.upper()}: (Castle Unit)"
                        if unique_unit_ids and len(unique_unit_ids) >= 1:
                            effect.effect_commands[0].a = unique_unit_ids[0]
                        else:
                            # Keep original Castle unit
                            effect.effect_commands[0].a = effect.effect_commands[0].a

                    # --- Imperial Unit handling ---
                    elif effect.name == f"{old_name.upper()}: (Imperial Unit)":
                        effect.name = f"{new_name.upper()}: (Imperial Unit)"
                        if unique_unit_ids and len(unique_unit_ids) >= 2:
                            effect.effect_commands[0].a = unique_unit_ids[0]
                            effect.effect_commands[0].b = unique_unit_ids[1]
                        else:
                            # Keep original Castle + Imperial upgrade unit
                            effect.effect_commands[0].a = effect.effect_commands[0].a
                            effect.effect_commands[0].b = effect.effect_commands[0].b

                # -----------------------
                # Strings (name + description)
                # -----------------------
                with open(MODDED_STRINGS, 'r+', encoding='utf-8') as modded_file:
                    lines = modded_file.readlines()
                    for i, line in enumerate(lines):
                        if line.startswith(f"{string_indexes[0]} "):  # name
                            lines[i] = f'{string_indexes[0]} "{new_name}"\n'
                        elif line.startswith(f"{string_indexes[1]} "):  # description
                            lines[i] = f'{string_indexes[1]} "{new_description}"\n'
                    modded_file.seek(0)
                    modded_file.writelines(lines)
                    modded_file.truncate()

                # -----------------------
                # Add new bonuses (as techs + effects)
                # -----------------------
                for bonus in new_bonuses:
                    new_effect = copy.deepcopy(DATA.effects[0])
                    new_effect.effect_commands = bonus["commands"]
                    new_effect.name = f"{new_name.upper()}: {bonus['name']}"
                    DATA.effects.append(new_effect)

                    new_tech = copy.deepcopy(DATA.techs[0])
                    new_tech.name = f"{new_name.upper()}: {bonus['name']}"
                    new_tech.required_techs = bonus["required_techs"]
                    new_tech.required_tech_count = len([x for x in bonus["required_techs"] if x != -1])
                    new_tech.civ = new_civ_id
                    new_tech.effect_id = len(DATA.effects) - 1
                    DATA.techs.append(new_tech)

                # -----------------------
                # Unique techs (names, strings, costs, time, commands, and effect rename)
                # -----------------------
                for ut in new_unique_techs:
                    tech = DATA.techs[ut["id"]]
                    change_string(tech.language_dll_name, ut["name"])
                    change_string(tech.language_dll_description, ut["desc"])
                    change_string(tech.language_dll_help - 79000, ut["help"])
                    change_string(tech.language_dll_tech_tree - 140000, ut["name"])
                    tech.name = ut["name"]

                    # Costs: dict with resource IDs (0 food, 1 wood, 2 stone, 3 gold)
                    if "costs" in ut and isinstance(ut["costs"], dict):
                        set_resource_costs(tech, ut["costs"])

                    # Research time
                    if "research_time" in ut:
                        set_research_time(tech, ut["research_time"])

                    # Effect (rename and replace commands)
                    eff = DATA.effects[ut["id"]]
                    eff.name = ut["name"]
                    eff.effect_commands.clear()
                    eff.effect_commands.extend(ut["commands"])

                # -----------------------
                # Castle Tech config (optional)
                # -----------------------
                if castle_tech_config:
                    ctech = DATA.techs[castle_tech_config["id"]]
                    if "costs" in castle_tech_config and isinstance(castle_tech_config["costs"], dict):
                        set_resource_costs(ctech, castle_tech_config["costs"])
                    if "research_time" in castle_tech_config:
                        set_research_time(ctech, castle_tech_config["research_time"])

                # -----------------------
                # Imperial Tech config (optional)
                # -----------------------
                if imperial_tech_config:
                    itech = DATA.techs[imperial_tech_config["id"]]
                    if "costs" in imperial_tech_config and isinstance(imperial_tech_config["costs"], dict):
                        set_resource_costs(itech, imperial_tech_config["costs"])
                    if "research_time" in imperial_tech_config:
                        set_research_time(itech, imperial_tech_config["research_time"])

            # Replace the Wei with Tanguts
            replace_civ(
                old_civ_id=51,
                new_civ_id=51,
                new_name="Tanguts",
                new_description=(
                    r"Defensive and Cavalry civilization\n\n"
                    r"• Lumberjacks generate food in addition to wood\n"
                    r"• Town Watch and Town Patrol spawn 4 cows\n"
                    r"• Steppe Lancers cost -30/50% gold in the Castle/Imperial Age\n"
                    r"• Towers built +30/40/50% faster in the Feudal/Castle/Imperial Age\n\n"
                    r"<b>Unique Units:<b>\n"
                    r"Tiger Cavalry (Cavalry)\n\n"
                    r"<b>Unique Techs:<b>\n"
                    r"• Bubazi (Infantry +1 attack, armor, and pierce armor, +20HP, +2 LOS, move +10% faster, and attack +15% faster)\n"
                    r"• Timely Pearl (Enemy siege units train -20% slower)\n\n"
                    r"<b>Team Bonus:<b>\n"
                    "Mounted units and Eagle Warriors +4 line of sight"
                ),
                unique_unit_ids=(1949, 1951),
                new_unique_techs=[
                    {
                        "id": 1070,
                        "name": "Bubazi",
                        "costs": {0: 350, 3: 250},
                        "research_time": 35,
                        "desc": r"Research Bubazi (Infantry +1 attack, armor, and pierce armor, +20HP, +2 LOS, and attack +15% faster)",
                        "help": r"Research <b>Bubazi<b> (<cost>)\nInfantry +1 attack, armor, and pierce armor, +20HP, +2 LOS, and attack +15% faster.",
                        "commands": [
                            genieutils.effect.EffectCommand(4, -1, 6, 9, 1025),
                            genieutils.effect.EffectCommand(4, -1, 6, 8, 1025),
                            genieutils.effect.EffectCommand(4, -1, 6, 8, 769),
                            genieutils.effect.EffectCommand(4, -1, 6, 0, 20),
                            genieutils.effect.EffectCommand(4, -1, 6, 1, 2),
                            genieutils.effect.EffectCommand(4, -1, 6, 23, 2),
                            genieutils.effect.EffectCommand(4, -1, 6, 60, 0.85),
                        ],
                    },
                    {
                        "id": 1069,
                        "name": "Timely Pearl",
                        "costs": {1: 750, 3: 1250},
                        "research_time": 60,
                        "desc": r"Research Timely Pearl (Enemy siege units train -20% slower)",
                        "help": r"Research <b>Timely Pearl<b> (<cost>)\nEnemy siege units train -20% slower.",
                        "commands": [
                            genieutils.effect.EffectCommand(25, -1, 13, 101, 1.2),
                        ],
                    },
                ],
                team_bonus_commands=[
                    genieutils.effect.EffectCommand(4, -1, 36, 1, 4),
                    genieutils.effect.EffectCommand(4, -1, 36, 23, 4),
                    genieutils.effect.EffectCommand(4, -1, 12, 1, 4),
                    genieutils.effect.EffectCommand(4, -1, 12, 23, 4),
                    genieutils.effect.EffectCommand(4, -1, 23, 1, 4),
                    genieutils.effect.EffectCommand(4, -1, 23, 23, 4),
                    genieutils.effect.EffectCommand(4, 751, -1, 1, 4),
                    genieutils.effect.EffectCommand(4, 751, -1, 23, 4),
                    genieutils.effect.EffectCommand(4, 752, -1, 1, 4),
                    genieutils.effect.EffectCommand(4, 752, -1, 23, 4),
                    genieutils.effect.EffectCommand(4, 753, -1, 1, 4),
                    genieutils.effect.EffectCommand(4, 753, -1, 23, 4),
                ],
                new_bonuses=[
                    {
                        "name": "Lumberjacks generate food in addition to wood",
                        "required_techs": (-1, -1, -1, -1, -1, -1),
                        "commands": [
                            genieutils.effect.EffectCommand(1, 502, -1, -1, 3.5),
                            genieutils.effect.EffectCommand(1, 33, 0, -1, 16),
                        ],
                    },
                    {
                        "name": "Town Watch and Town Patrol spawn 4 cows",
                        "required_techs": (8, -1, -1, -1, -1, -1),
                        "commands": [
                            genieutils.effect.EffectCommand(1, 234, 0, -1, 1),
                            genieutils.effect.EffectCommand(7, 705, 619, 4, -1),
                        ],
                    },
                    {
                        "name": "Town Watch and Town Patrol spawn 4 cows",
                        "required_techs": (280, -1, -1, -1, -1, -1),
                        "commands": [
                            genieutils.effect.EffectCommand(1, 234, 0, -1, 1),
                            genieutils.effect.EffectCommand(7, 705, 619, 4, -1),
                        ],
                    },
                    {
                        "name": "Steppe Lancers cost -50/75% gold in the Castle/Imperial Age",
                        "required_techs": (102, -1, -1, -1, -1, -1),
                        "commands": [
                            genieutils.effect.EffectCommand(5, 1370, -1, 105, 0.5),
                            genieutils.effect.EffectCommand(5, 1372, -1, 105, 0.5),
                        ],
                    },
                    {
                        "name": "Steppe Lancers cost -50/75% gold in the Castle/Imperial Age",
                        "required_techs": (103, -1, -1, -1, -1, -1),
                        "commands": [
                            genieutils.effect.EffectCommand(5, 1370, -1, 105, 0.5),
                            genieutils.effect.EffectCommand(5, 1372, -1, 105, 0.5),
                        ],
                    },
                    {
                        "name": "Towers built +30% faster (Feudal Age)",
                        "required_techs": (101, -1, -1, -1, -1, -1),
                        "commands": [
                            genieutils.effect.EffectCommand(5, -1, 52, 101, 0.8),
                        ],
                    },
                    {
                        "name": "Towers built +40% faster (Castle Age)",
                        "required_techs": (102, -1, -1, -1, -1, -1),
                        "commands": [
                            genieutils.effect.EffectCommand(5, -1, 52, 101, 0.875),
                        ],
                    },
                    {
                        "name": "Towers built +50% faster (Imperial Age)",
                        "required_techs": (103, -1, -1, -1, -1, -1),
                        "commands": [
                            genieutils.effect.EffectCommand(5, -1, 52, 101, 0.857142857),
                        ],
                    },
                ],
                string_indexes=[10321, 120200],
                disabled_techs = [15, 37, 64, 84, 85, 188, 221, 237, 244, 264, 265, 272, 316, 320, 321, 373, 376, 384, 433, 434, 439, 447, 448, 480, 481, 518, 521, 522, 526, 528, 570, 596, 597, 598, 599, 630, 631, 655, 695, 703, 716, 773, 775, 786, 787, 790, 793, 841, 842, 843, 885, 886, 929, 930, 932, 941, 948, 979, 980, 981, 982, 992, 1008, 1065, 1075, 1037, 429, 602, 166, 209, 255, 219, 377, 35, 1014, 1013, 1012, 1025, 182, 45, 231, 233, 438, CUSTOM_TECH_STARTING_INDEX, CUSTOM_TECH_STARTING_INDEX+1, CUSTOM_TECH_STARTING_INDEX+2]
            )

            # Replace the Wu with Bai
            '''replace_civ(
                old_civ_id=50,
                new_civ_id=50,
                new_name="Bai",
                new_description=(
                    r"Infantry and Monk civilization\n\n"
                    r"• First Barracks provides +175 food\n"
                    r"• Infantry regenerates 10/20/30 HP per minute in Feudal/Castle/Imperial Age\n"
                    r"• Infantry +4 armor and pierce armor vs. siege\n"
                    r"• Relics generate stone in addition to gold\n\n"
                    r"<b>Unique Units:<b>\n"
                    r"Fire Archer (Foot Archer), Jian Swordsman (Infantry)\n\n"
                    r"<b>Unique Techs:<b>\n"
                    r"• Great Siege (Fire Archers deal fire damage to ships and buildings)\n"
                    r"• Dharma Protection (Buildings +20% HP; Monks gold cost replaced with food)\n\n"
                    r"<b>Team Bonus:<b>\n"
                    "Houses built +100% faster"
                ),
                unique_unit_ids=(1968, 1970),
                new_unique_techs=[
                    {
                        "id": 1080,
                        "name": "Great Siege",
                        "costs": {0: 350, 1: 350},
                        "research_time": 35,
                        "desc": r"Research Great Siege (Fire Archers deal fire damage to ships and buildings)",
                        "help": r"Research <b>Great Siege<b> (<cost>)\nFire Archers deal fire damage to ships and buildings.",
                        "commands": [
                            genieutils.effect.EffectCommand(0, 1968, -1, 63, 128),
                            genieutils.effect.EffectCommand(0, 1970, -1, 63, 128),
                            genieutils.effect.EffectCommand(0, 1968, -1, 16, 1972),
                            genieutils.effect.EffectCommand(0, 1970, -1, 16, 1972),
                        ],
                    },
                    {
                        "id": 1081,
                        "name": "Dharma Protection",
                        "costs": {0: 500, 2: 750},
                        "research_time": 50,
                        "desc": r"Research Dharma Protection (Buildings +20% HP; Monks gold cost replaced with food)",
                        "help": r"Research <b>Dharma Protection<b> (<cost>)\nBuildings +20% HP; Monks gold cost replaced with food.",
                        "commands": [
                            genieutils.effect.EffectCommand(5, -1, 3, 0, 1.2),
                            genieutils.effect.EffectCommand(0, 125, -1, 105, 0),
                            genieutils.effect.EffectCommand(0, 125, -1, 103, 100),
                        ],
                    },
                ],
                team_bonus_commands=[
                    genieutils.effect.EffectCommand(4, 70, -1, 101, 2),
                    genieutils.effect.EffectCommand(4, 463, -1, 101, 2),
                    genieutils.effect.EffectCommand(4, 465, -1, 101, 2),
                    genieutils.effect.EffectCommand(4, 464, -1, 101, 2),
                    genieutils.effect.EffectCommand(4, 712, -1, 101, 2),
                    genieutils.effect.EffectCommand(4, 713, -1, 101, 2),
                    genieutils.effect.EffectCommand(4, 714, -1, 101, 2),
                    genieutils.effect.EffectCommand(4, 715, -1, 101, 2),
                    genieutils.effect.EffectCommand(4, 716, -1, 101, 2),
                    genieutils.effect.EffectCommand(4, 717, -1, 101, 2),
                    genieutils.effect.EffectCommand(4, 718, -1, 101, 2),
                    genieutils.effect.EffectCommand(4, 719, -1, 101, 2),
                ],
                new_bonuses=[
                    {
                        "name": "First Barracks provides +175 food",
                        "required_techs": (122, -1, -1, -1, -1, -1),
                        "commands": [
                            genieutils.effect.EffectCommand(1, 0, 1, -1, 175),
                        ],
                    },
                    {
                        "name": "Infantry regenerates 10/20/30 HP per minute in Feudal/Castle/Imperial Age",
                        "required_techs": (101, -1, -1, -1, -1, -1),
                        "commands": [
                            genieutils.effect.EffectCommand(4, -1, 6, 109, 10),
                        ],
                    },
                    {
                        "name": "Infantry regenerates 10/20/30 HP per minute in Feudal/Castle/Imperial Age",
                        "required_techs": (102, -1, -1, -1, -1, -1),
                        "commands": [
                            genieutils.effect.EffectCommand(4, -1, 6, 109, 10),
                        ],
                    },
                    {
                        "name": "Infantry regenerates 10/20/30 HP per minute in Feudal/Castle/Imperial Age",
                        "required_techs": (103, -1, -1, -1, -1, -1),
                        "commands": [
                            genieutils.effect.EffectCommand(4, -1, 6, 109, 10),
                        ],
                    },
                    {
                        "name": "Infantry +4 armor vs. siege",
                        "required_techs": (-1, -1, -1, -1, -1, -1),
                        "commands": [
                            genieutils.effect.EffectCommand(4, -1, 6, 8, 5124),
                        ],
                    },
                    {
                        "name": "Relics generate stone in addition to gold",
                        "required_techs": (-1, -1, -1, -1, -1, -1),
                        "commands": [
                            genieutils.effect.EffectCommand(1, 265, -1, -1, 15),
                        ],
                    }
                ],
                string_indexes=[10320, 120199],
                disabled_techs = [35, 37, 54, 64, 84, 85, 166, 188, 194, 209, 218, 235, 236, 237, 244, 246, 255, 265, 272, 320, 373, 375, 376, 377, 384, 433, 434, 437, 447, 448, 480, 481, 518, 521, 522, 526, 528, 570, 596, 597, 598, 599, 655, 695, 703, 716, 773, 775, 786, 787, 790, 793, 837, 838, 841, 842, 843, 885, 886, 929, 930, 932, 941, 948, 979, 980, 981, 982, 992, 1005, 1025, 1037, 1065, 436, 264, 192, 428, 318, 714, 715, 631, 435, 39, 96, 219, 80, 240, 34, 604, 243, 605, 316, 233, 1008, 1014, 1013, 1012, CUSTOM_TECH_STARTING_INDEX, CUSTOM_TECH_STARTING_INDEX+1, CUSTOM_TECH_STARTING_INDEX+2]
            )'''

            # Replace the Shu with Tibetans
            replace_civ(
                old_civ_id=49,
                new_civ_id=49,
                new_name="Tibetans",
                new_description=(
                    r"Monk civilization\n\n"
                    r"• Pastures +45 food per animal\n"
                    r"• Armor upgrades add +5 hit points to affected units\n"
                    r"• Monks +2 range and armor; garrisoned Monks fire arrows\n\n"
                    r"<b>Unique Units:<b>\n"
                    r"Qizilbash Warrior (Cavalry)\n\n"
                    r"<b>Unique Techs:<b>\n"
                    r"• Brog-pa (Pastures provide +5 population space; Scout Cavalry-line can be trained at Pastures)\n"
                    r"• Stod Mkhar (Units and Buildings deal +15% and receive -10% damage when fighting from higher elevation; Buildings +2 line of sight)\n\n"
                    r"<b>Team Bonus:<b>\n"
                    "Monks regenerate 15 HP per second"
                ),
                unique_unit_ids=(1817, 1829),
                new_unique_techs=[
                    {
                        "id": 1061,
                        "name": "Brog-pa",
                        "costs": {0: 350, 1: 350},
                        "research_time": 35,
                        "desc": r"Research Brog-pa (Pastures provide 5 population; Scout Cavalry-line can be trained at Pastures)",
                        "help": r"Research <b>Brog-pa<b> (<cost>)\nPastures provide 5 population; Scout Cavalry-line can be trained at Pastures.",
                        "commands": [
                            genieutils.effect.EffectCommand(3, 448, get_unit_id('scout cavalry', True)[1], -1, -1),
                            genieutils.effect.EffectCommand(3, 546, get_unit_id('light cavalry', True)[0], -1, -1),
                            genieutils.effect.EffectCommand(3, 441, get_unit_id('hussar', True)[0], -1, -1),
                            genieutils.effect.EffectCommand(0, 1890, -1, 21, 5),
                        ],
                    },
                    {
                        "id": 1062,
                        "name": "Stod Mkhar",
                        "costs": {0: 500, 2: 750},
                        "research_time": 50,
                        "desc": r"Research Stod Mkhar (Units and Buildings deal +15% and receive -10% damage when fighting from higher elevation; Buildings +2 line of sight)",
                        "help": r"Research <b>Stod Mkhar<b> (<cost>)\nUnits and Buildings deal +15% and receive -10% damage when fighting from higher elevation; Buildings +2 line of sight.",
                        "commands": [
                            genieutils.effect.EffectCommand(1, 272, 1, -1, 0.15),
                            genieutils.effect.EffectCommand(1, 273, 1, -1, -0.1),
                            genieutils.effect.EffectCommand(4, -1, 3, 1, 2),
                            genieutils.effect.EffectCommand(4, -1, 3, 23, 2),
                        ],
                    },
                ],
                team_bonus_commands=[
                    genieutils.effect.EffectCommand(4, -1, 18, 109, 15)
                ],
                new_bonuses=[
                    {
                        "name": "First Barracks provides +175 food",
                        "required_techs": (122, -1, -1, -1, -1, -1),
                        "commands": [
                            genieutils.effect.EffectCommand(1, 0, 1, -1, 175),
                        ],
                    },
                    {
                        "name": "Infantry regenerates 10/20/30 HP per minute in Feudal/Castle/Imperial Age",
                        "required_techs": (101, -1, -1, -1, -1, -1),
                        "commands": [
                            genieutils.effect.EffectCommand(4, -1, 6, 109, 10),
                        ],
                    },
                    {
                        "name": "Infantry regenerates 10/20/30 HP per minute in Feudal/Castle/Imperial Age",
                        "required_techs": (102, -1, -1, -1, -1, -1),
                        "commands": [
                            genieutils.effect.EffectCommand(4, -1, 6, 109, 10),
                        ],
                    },
                    {
                        "name": "Infantry regenerates 10/20/30 HP per minute in Feudal/Castle/Imperial Age",
                        "required_techs": (103, -1, -1, -1, -1, -1),
                        "commands": [
                            genieutils.effect.EffectCommand(4, -1, 6, 109, 10),
                        ],
                    },
                    {
                        "name": "Infantry +4 armor vs. siege",
                        "required_techs": (-1, -1, -1, -1, -1, -1),
                        "commands": [
                            genieutils.effect.EffectCommand(4, -1, 6, 8, 5124),
                        ],
                    },
                    {
                        "name": "Relics generate stone in addition to gold",
                        "required_techs": (-1, -1, -1, -1, -1, -1),
                        "commands": [
                            genieutils.effect.EffectCommand(1, 265, -1, -1, 15),
                        ],
                    }
                ],
                string_indexes=[10319, 120198],
                disabled_techs = [35, 37, 54, 64, 84, 85, 166, 188, 194, 209, 218, 235, 236, 237, 244, 246, 255, 265, 272, 320, 373, 375, 376, 377, 384, 433, 434, 437, 447, 448, 480, 481, 518, 521, 522, 526, 528, 570, 596, 597, 598, 599, 655, 695, 703, 716, 773, 775, 786, 787, 790, 793, 837, 838, 841, 842, 843, 885, 886, 929, 930, 932, 941, 948, 979, 980, 981, 982, 992, 1005, 1025, 1037, 1065, 436, 264, 192, 428, 318, 714, 715, 631, 435, 39, 96, 219, 80, 240, 34, 604, 243, 605, 316, 233, 1008, 1014, 1013, 1012, CUSTOM_TECH_STARTING_INDEX, CUSTOM_TECH_STARTING_INDEX+1, CUSTOM_TECH_STARTING_INDEX+2]
            )
        
        def reorder_tech_trees(self):
            # Reorder tech trees
            for civ in DATA.civs:
                civ_tech_tree_index = -1
                for i, effect in enumerate(DATA.effects):
                    if effect.name.lower() == f'{civ.name} tech tree'.lower():
                        civ_tech_tree_index = i

                if civ_tech_tree_index == -1:
                    continue

                DATA.effects[civ_tech_tree_index].effect_commands.sort(key=lambda ec: ec.d)

        def finalize(self):
            # Clean up
            DATA.effects[0].effect_commands.clear()
            
            # Save
            print('Saving data...')
            DATA.save(rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat')
            print('Data saved!')

    def new_mod_window(self):
        dlg = QDialog(self)
        global ui
        ui = Ui_NewMod()
        ui.setupUi(dlg)

        # Load pickled Talofa settings
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.pkl"), 'rb') as file:
                talofa_settings = pickle.load(file)
                ui.local_mods_folder_input.setText(talofa_settings.get('LOCAL_MODS_FOLDER', ''))
                ui.aoe2_folder_input.setText(talofa_settings.get('AOE2_FOLDER', ''))
        except:
            print('No settings.pkl file found!')

        ui.create_mod_button.clicked.connect(lambda: self.create_new_mod(dlg, ui))
        dlg.setModal(True)
        dlg.exec_()

    def create_new_mod(self, dialog: QDialog, ui: Ui_NewMod):
        # Define global variables
        global MOD_NAME, LOCAL_MODS_FOLDER, AOE2_FOLDER, MOD_FOLDER, MOD_UI_FOLDER, ORIGINAL_STRINGS, MODDED_STRINGS, DATA
        MOD_NAME  = ui.mod_name_input.text().strip()
        LOCAL_MODS_FOLDER  = ui.local_mods_folder_input.text().strip()
        AOE2_FOLDER  = ui.aoe2_folder_input.text().strip()
        MOD_FOLDER = f"{LOCAL_MODS_FOLDER}/{MOD_NAME}"
        MOD_UI_FOLDER = f"{LOCAL_MODS_FOLDER}/{MOD_NAME}-ui"
        ORIGINAL_STRINGS = f'{MOD_FOLDER}/resources/en/strings/key-value/key-value-strings-utf8.txt'
        MODDED_STRINGS = f'{MOD_FOLDER}/resources/en/strings/key-value/key-value-modded-strings-utf8.txt'

        # Get window settings
        global REPLACE_3KINGDOMS, CANOES_MESOAMERICAN, CANOES_SEA, CANOES_OTHER
        REPLACE_3KINGDOMS = ui.replace_3kingdoms_checkbox.isChecked()
        CANOES_MESOAMERICAN = ui.canoes_mesoamericans_checkbox.isChecked()
        CANOES_SEA = ui.canoes_sea_checkbox.isChecked()
        CANOES_OTHER = ui.canoes_other_checkbox.isChecked()

        dialog.close()  # close the “New Mod” dialog

        # modal progress dialog
        self.progress_dlg = QProgressDialog("Starting…", "Cancel", 0, 100, self)
        self.progress_dlg.setWindowTitle("Creating Mod")
        self.progress_dlg.setWindowModality(Qt.ApplicationModal)
        self.progress_dlg.setAutoClose(True)
        self.progress_dlg.setAutoReset(True)
        self.progress_dlg.setMinimumDuration(0)
        self.progress_dlg.setFixedWidth(600)
        self.progress_dlg.show()

        # spin up the worker
        self.worker = self.WorkerThread(
            MOD_NAME,
            MOD_FOLDER,
            replace_3kingdoms=REPLACE_3KINGDOMS,
            canoes_mesoamerican=CANOES_MESOAMERICAN,
            canoes_sea=CANOES_SEA,
            canoes_other=CANOES_OTHER,
            parent=self
        )

        self.worker.progress.connect(self.progress_dlg.setValue)
        self.worker.message.connect(self.progress_dlg.setLabelText)
        self.worker.done.connect(self._on_mod_done)
        self.worker.finished_with_mod.connect(self.load_mod)   # <— auto-load created mod

        self.progress_dlg.canceled.connect(self.worker.cancel)

        self.worker.start()

    def _on_mod_done(self):
        # Close the progress dialog safely
        if hasattr(self, "progress_dlg") and self.progress_dlg:
            self.progress_dlg.close()

        print("Mod created!")
        self.open_mod()  # optional: open automatically


    def load_mod(self, mod_path):
        # Enable app
        self.centralwidget.setEnabled(True)

        # Load global mod variables
        global MOD_NAME, LOCAL_MODS_FOLDER, AOE2_FOLDER, MOD_FOLDER, MOD_UI_FOLDER, ORIGINAL_STRINGS, MODDED_STRINGS
        try:
            with open(f'{mod_path}/settings.pkl', 'rb') as pf:
                settings = pickle.load(pf)

            # Assign loaded values to globals dynamically
            for key, value in settings.items():
                globals()[key] = value
        except Exception as e:
            print(f"Failed to load settings from {f'{mod_path}/settings.pkl'}: {e}")

        # Load global Talofa variables
        global ARCHITECTURE_SETS, IGNORED_CIVS
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.pkl"), 'rb') as pf:
                settings = pickle.load(pf)

            # Assign loaded values to globals dynamically
            for key, value in settings.items():
                globals()[key] = value
        except Exception as e:
            print(f"Failed to load settings from {os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.pkl")}: {e}")

        # Create the civ class
        class Civ:
            def __init__(self, data_index, talofa_index, name, emblem_path, original_name, description, tech_tree_index, team_bonus_index, scout_unit_index, castle_unit_effect_index, imperial_unit_effect_index, language, unique_techs, graphics):
                self.data_index = data_index
                self.talofa_index = talofa_index
                self.name = name
                self.emblem_path = emblem_path
                self.original_name = original_name
                self.description = description
                self.tech_tree_index = tech_tree_index
                self.team_bonus_index = team_bonus_index
                self.scout_unit_index = scout_unit_index
                self.language = language
                self.unique_techs = unique_techs
                self.graphics = graphics
                self.castle_unit_effect_index = castle_unit_effect_index
                self.imperial_unit_effect_index = imperial_unit_effect_index
        
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
        global GRAPHICS_GENERAL, GRAPHICS_CASTLE, GRAPHICS_WONDER, GRAPHICS_MONK, GRAPHICS_MONASTERY, GRAPHICS_TRADECART, GRAPHICS_SHIPS
        GRAPHICS_GENERAL = {'South Indian': 55, 'Caucasian': 54,'Greek': 47, 'Mesopotamian': 46, 'Central Asian': 33, 'Central European': 4, 'East Asian': 5, 'Eastern European': 23, 'Mediterranean': 14, 'Mesoamerican': 15, 'Middle Eastern': 9, 'South Asian': 20, 'Southeast Asian': 28, 'West African': 26, 'Western European': 1}
        GRAPHICS_CASTLE = {'Greek': 47, 'Mesopotamian': 46,'Armenians': 44, 'Aztecs': 15, 'Bengalis': 41, 'Berbers': 27, 'Bohemians': 39, 'Britons': 1, 'Bulgarians': 32, 'Burgundians': 36, 'Burmese': 30, 'Byzantines': 7, 'Celts': 13, 'Chinese': 6, 'Cumans': 34, 'Dravidians': 40, 'Ethiopians': 25, 'Franks': 2, 'Georgians': 45, 'Goths': 3, 'Gurjaras': 42, 'Hindustanis': 20, 'Huns': 17, 'Inca': 21, 'Italians': 19, 'Japanese': 5, 'Jurchens': 52, 'Khitan': 53, 'Khmer': 28, 'Koreans': 18, 'Lithuanians': 35, 'Magyars': 22, 'Malay': 29, 'Malians': 26, 'Maya': 16, 'Mongols': 12, 'Persians': 8, 'Poles': 38, 'Portuguese': 24, 'Romans': 43, 'Saracens': 9, 'Shu': 49, 'Sicilians': 37, 'Slavs': 23, 'Spanish': 14, 'Tatars': 33, 'Teutons': 4, 'Turks': 10, 'Vikings': 11, 'Vietnamese': 31, 'Wei': 51, 'Wu': 50}
        GRAPHICS_WONDER = {'Athenians': 47, 'Spartans': 47, 'Achaemenids': 46,'Armenians': 44, 'Aztecs': 15, 'Bengalis': 41, 'Berbers': 27, 'Bohemians': 39, 'Britons': 1, 'Bulgarians': 32, 'Burgundians': 36, 'Burmese': 30, 'Byzantines': 7, 'Celts': 13, 'Chinese': 6, 'Cumans': 34, 'Dravidians': 40, 'Ethiopians': 25, 'Franks': 2, 'Georgians': 45, 'Goths': 3, 'Gurjaras': 42, 'Hindustanis': 20, 'Huns': 17, 'Inca': 21, 'Italians': 19, 'Japanese': 5, 'Jurchens': 52, 'Khitan': 53, 'Khmer': 28, 'Koreans': 18, 'Lithuanians': 35, 'Magyars': 22, 'Malay': 29, 'Malians': 26, 'Maya': 16, 'Mongols': 12, 'Persians': 8, 'Poles': 38, 'Portuguese': 24, 'Romans': 43, 'Saracens': 9, 'Shu': 49, 'Sicilians': 37, 'Slavs': 23, 'Spanish': 14, 'Tatars': 33, 'Teutons': 4, 'Turks': 10, 'Vikings': 11, 'Vietnamese': 31, 'Wei': 51, 'Wu': 50}
        GRAPHICS_MONK = {'African': 25, 'Buddhist': 5, 'Catholic': 14, 'Christian': 0, 'Hindu': 40, 'Mesoamerican': 15, 'Muslim': 9, 'Orthodox': 23, 'Pagan': 35, 'Tengri': 12}
        GRAPHICS_MONASTERY = {'Greek': 47, 'Mesopotamian': 46, 'Byzantines': 7, 'Central Asian': 33, 'Central European': 4, 'East Asian': 5, 'East African': 25, 'Eastern European': 23, 'Mediterranean': 14, 'Mesoamerican': 15, 'Middle Eastern': 9, 'Pagan': 35, 'South Asian': 40, 'Southeast Asian': 28, 'Southeast European': 44, 'Tengri': 12, 'West African': 26, 'Western European': 1}
        GRAPHICS_TRADECART = {'Camel': 9, 'Horse': 1, 'Human': 15, 'Ox': 25, 'Water Buffalo': 5}
        GRAPHICS_SHIPS = {'Central Asian': 33, 'Central European': 4, 'East Asian': 5, 'Eastern European': 23, 'Mediterranean': 14, 'Mesoamerican': 15, 'Middle Eastern': 9, 'Southeast Asian': 28, 'West African': 25, 'Western European': 1}

        # Sort dictionaries
        def sort_dict_by_key(d):
            return dict(sorted(d.items(), key=lambda x: x[0].lower()))
        GRAPHICS_GENERAL = sort_dict_by_key(GRAPHICS_GENERAL)
        GRAPHICS_CASTLE = sort_dict_by_key(GRAPHICS_CASTLE)
        GRAPHICS_WONDER = sort_dict_by_key(GRAPHICS_WONDER)
        GRAPHICS_MONK = sort_dict_by_key(GRAPHICS_MONK)
        GRAPHICS_MONASTERY = sort_dict_by_key(GRAPHICS_MONASTERY)
        GRAPHICS_TRADECART = sort_dict_by_key(GRAPHICS_TRADECART)
        GRAPHICS_SHIPS = sort_dict_by_key(GRAPHICS_SHIPS)

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

        # Load all current civs
        global CIVS
        CIVS = []
        talofa_index = 0
        for i, civ in enumerate(DATA.civs):
            # Skip specific civs
            if i in IGNORED_CIVS:
                talofa_index = i
                continue

            # Get the total amount of civs
            global TOTAL_CIVS_COUNT
            TOTAL_CIVS_COUNT = len(DATA.civs) - len(IGNORED_CIVS)

            # Create new civ object
            new_civ = Civ(i, talofa_index, '', '', '', '', -1, -1, int(civ.resources[263]), -1, -1, '', [], [])

            # Get the stats for the civ
            with open(MODDED_STRINGS, 'r') as file:
                lines = file.readlines()
                name_index = None

                for line_index, line in enumerate(lines):
                    # Look for an exact match in quotes
                    pattern = f'"{civ.name}"'
                    if pattern.lower() in remove_diacritics(line.lower()):
                        new_civ.name = line.split('"')[1].strip()
                        new_civ.original_name = line.split('"')[1].strip()
                        new_civ.original_name = new_civ.original_name.replace('Maya', 'Mayans')
                        new_civ.original_name = new_civ.original_name.replace('Inca', 'Incas')
                        new_civ.original_name = new_civ.original_name.replace('Hindustanis', 'Indians')
                        new_civ.original_name = new_civ.original_name.replace('Tanguts', 'Wei')
                        new_civ.original_name = new_civ.original_name.replace('Bai', 'Wu')
                        new_civ.original_name = new_civ.original_name.replace('Tibetans', 'Shu')
                        name_index = line_index
                        new_civ.emblem_path = f'{MOD_FOLDER}/widgetui/textures/menu/civs/{new_civ.original_name.lower()}.png'

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
                        new_civ.description = lines[name_index + TOTAL_CIVS_COUNT + len(IGNORED_CIVS) - 1].split('"')[1].strip()

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

        # Populate icons
        global ICON_NAMES
        ICON_NAMES = []
        for civ_id, civ in enumerate(DATA.civs):
            if civ_id not in IGNORED_CIVS:
                ICON_NAMES.append(civ.name.lower())

        # Populate unique unit dropdown
        global ALL_CASTLE_UNITS
        ALL_CASTLE_UNITS = sorted([
            "longbowman", "throwing axeman", "berserk", "teutonic knight", "samurai",
            "chu ko nu", "cataphract", "war elephant", "mameluke", "janissary", "huskarl",
            "mangudai", "woad raider", "conquistador", "jaguar warrior", "plumed archer",
            "tarkan", "war wagon", "genoese crossbowman", "ghulam", "kamayuk", "magyar huszar",
            "boyar", "organ gun", "shotel warrior", "gbeto", "camel archer", "ballista elephant",
            "karambit warrior", "arambai", "rattan archer", "konnik", "keshik", "kipchak",
            "leitis", "coustillier", "serjeant", "obuch", "hussite wagon", "urumi swordsman",
            "ratha (melee)", "chakram thrower", "centurion", "composite bowman", "monaspa",
            "iron pagoda", "liao dao", "white feather guard", "tiger cavalry", "fire archer",
            "amazon warrior", "amazon archer", "qizilbash warrior", "genitour", "naasiri",
            "elephant gunner", "flamethrower", "weichafe", "destroyer", "lightning warrior",
            "cossack"
        ])

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

        # Load all icons
        path_icons = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Images", "CivIcons", "Bank")
        global ICONS
        ICONS = [
            os.path.join(path_icons, f)
            for f in os.listdir(path_icons)
            if os.path.isfile(os.path.join(path_icons, f))
        ]

        # Change window title
        self.setWindowTitle(f"Talofa - {MOD_NAME}")

        # Run once at startup
        self.dropdown_civ_name_changed(self.dropdown_civ_name.currentIndex())

    def save_mod(self):
        if MOD_FOLDER and '*' in self.windowTitle():
            # Save data
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

            # Save civ emblems
            for civ in CIVS:
                if not hasattr(civ, "emblem_path") or not civ.emblem_path or not os.path.exists(civ.emblem_path):
                    print(f"⚠️ Skipping {civ.name}: emblem_path missing or invalid ({getattr(civ, 'emblem_path', None)})")
                    continue

                civ_name = civ.original_name.lower()
                emblem_path = civ.emblem_path

                # === Replace in civ icon folders ===
                civ_targets = [
                    os.path.join(MOD_FOLDER, "widgetui/textures/menu/civs", f"{civ_name}.png"),
                    os.path.join(MOD_UI_FOLDER, "widgetui/textures/menu/civs", f"{civ_name}.png"),
                ]

                for tgt in civ_targets:
                    folder = os.path.dirname(tgt)
                    if os.path.exists(folder):
                        try:
                            shutil.copy(emblem_path, tgt)
                        except Exception as e:
                            pass
                            #print(f"❌ Failed copying emblem for {civ_name}: {e}")

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
                            try:
                                shutil.copy(emblem_path, tgt)
                            except Exception as e:
                                print(f"❌ Failed updating {tgt}: {e}")


            # Remove save asterisk
            self.setWindowTitle(self.windowTitle().replace('*', ''))

    def open_mod(self):
        # Get mod location
        global MOD_FOLDER, DATA
        MOD_FOLDER = r'/home/xommon/snap/steam/common/.local/share/Steam/steamapps/compatdata/813780/pfx/drive_c/users/steamuser/Games/Age of Empires 2 DE/76561198021486964/mods/local/Test'

        # Load the mod
        if DATA is None:
            print("Loading file...")
            DATA = DatFile.parse(f"{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat")

        print("Mod loaded!")
        self.load_mod(MOD_FOLDER)

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
        try:
            civ_index = CURRENT_CIV.data_index
            old_value = CURRENT_CIV.scout_unit_index
            new_value = int(self.dropdown_scout_units.currentData())

            if old_value == new_value:
                return

            cmd = ChangeScoutUnitCommand(self, civ_index, old_value, new_value)
            self.undoStack.push(cmd)
        except:
            pass

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
        self.image_civ_icon.setPixmap(QtGui.QPixmap(CURRENT_CIV.emblem_path))

        # Update icon tab icon
        global ICON_INDEX
        matching_image_in_bank = find_matching_image(CURRENT_CIV.emblem_path, ICONS)
        ICON_INDEX = ICONS.index(matching_image_in_bank)
        self.image_current_icon.setPixmap(QtGui.QPixmap(ICONS[ICON_INDEX]))

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
        '''try:
            self.input_castle_tech_name.setText(CURRENT_CIV.unique_techs[0].split('|')[0])
            self.input_castle_tech_description.setText(CURRENT_CIV.unique_techs[0].split('|')[1])
            self.input_imperial_tech_name.setText(CURRENT_CIV.unique_techs[1].split('|')[0])
            self.input_imperial_tech_description.setText(CURRENT_CIV.unique_techs[1].split('|')[1])
        except Exception:
            print("Error loading unique techs")'''

        # Define which test unit corresponds to each category
        '''self.dropdown_general_graphics.setCurrentIndex(
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
        )'''

        unit_bank = {
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
                print("".join(traceback.format_exception(etype, evalue, etb)))

    def dropdown_unique_units_changed(self):
        civ_index = CURRENT_CIV.data_index

        # Old values from DATA
        old_castle = DATA.effects[CURRENT_CIV.castle_unit_effect_index].effect_commands[0].a
        old_imperial = DATA.effects[CURRENT_CIV.imperial_unit_effect_index].effect_commands[0].a
        old_upgrade = DATA.effects[CURRENT_CIV.imperial_unit_effect_index].effect_commands[0].b
        old_value = (old_castle, old_imperial, old_upgrade)

        # New values from dropdown
        try:
            unique_units_ids = self.dropdown_unique_units.currentData().split('|')
            castle_id = int(unique_units_ids[0])
            elite_id = int(unique_units_ids[1])
            new_value = (castle_id, castle_id, elite_id)   # imperial unit starts as same as castle

            if old_value == new_value:
                return

            cmd = ChangeUniqueUnitCommand(self, civ_index, old_value, new_value)
            self.undoStack.push(cmd)
        except:
            pass

    def button_change_emblem(self, direction):
            # Change the icon index
            global ICON_INDEX
            if direction == 'left':
                if ICON_INDEX == 0:
                    ICON_INDEX = len(ICONS)-1
                else:
                    ICON_INDEX -= 1
            elif direction == 'right':
                if ICON_INDEX == len(ICONS)-1:
                    ICON_INDEX = 0
                else:
                    ICON_INDEX += 1

            # Get the index of the current civ's icon
            CURRENT_CIV.emblem_path = ICONS[ICON_INDEX]
            self.image_current_icon.setPixmap(QtGui.QPixmap(ICONS[ICON_INDEX]))

            # Mark dirty
            if not self.windowTitle().endswith('*'):
                self.setWindowTitle(self.windowTitle() + '*')

def find_matching_image(target_path, image_list):
    """
    Finds a byte-for-byte matching image file in `image_list`
    that matches `target_path`. Returns the matching path or None.
    """

    # Check if the target file exists
    if not os.path.exists(target_path):
        print(f"❌ Target not found: {target_path}")
        return None

    # Normalize paths (important for relative paths)
    target_path = os.path.abspath(target_path)

    for path in image_list:
        if not os.path.exists(path):
            print(f"⚠️ Skipping missing file: {path}")
            continue

        try:
            # Compare files byte-for-byte
            if filecmp.cmp(target_path, os.path.abspath(path), shallow=False):
                return path

        except Exception as e:
            print(f"⚠️ Error comparing {target_path} and {path}: {e}")

    print(f"🚫 No byte-for-byte match found for {target_path}")
    return None
        
def get_tech_id(name):
    # Search with external name
    string_id = None
    with open(ORIGINAL_STRINGS, 'r', encoding='utf-8') as file:
        for line in file:
            if name.lower() in line.lower():
                string_id = re.sub(r'^\d+\s+', '', line)
                break

    # Search with internal name
    for i, tech in enumerate(DATA.techs):
        if tech.name.lower() == name.lower():
            return i

    if string_id:
        for i, tech in enumerate(DATA.techs):
            if tech.language_dll_name == string_id:
                return i

    return -1

def change_string(index, new_string):
    string_line = ''

    # Get the original line
    with open(ORIGINAL_STRINGS, 'r', encoding='utf-8') as original_file:
        original_lines = original_file.readlines()
        for i, line in enumerate(original_lines):
            if line.startswith(f'{index} '):
                string_line = line

    # Find modded line if it exists
    with open(MODDED_STRINGS, 'r+', encoding='utf-8') as mod_file:
        string_found = False
        mod_lines = mod_file.readlines()
        for i, line in enumerate(mod_lines):
            if line.startswith(f'{index} '):
                line = f'{index} "{new_string}"\n'
                string_found = True

        # Create the new line if it doesn't exist
        if not string_found:
            if not mod_lines or not mod_lines[-1].endswith('\n'):
                mod_lines[-1] += '\n'
            mod_lines.append(f'{index} "{new_string}"\n')

        # Write the updated lines back to the file
        mod_file.seek(0)
        mod_file.writelines(mod_lines)
        mod_file.truncate()  # Ensure remaining old content is removed

# Replace unit graphics
def replace_graphics_for_civs(civ_ids, unit_ids, replacement_ids):
    attributes = [
        ("standing_graphic",),
        ("dying_graphic",),
        ("undead_graphic",),
        ("damage_graphics",),
        ("type_50", "attack_graphic"),
        ("type_50", "attack_graphic_2"),
        ("dead_fish", "walking_graphic"),
        ("dead_fish", "running_graphic"),
        ("creatable", "garrison_graphic"),
        ("creatable", "spawning_graphic"),
        ("creatable", "upgrade_graphic"),
        ("creatable", "hero_glow_graphic"),
        ("creatable", "idle_attack_graphic"),
        ("creatable", "special_graphic"),
        ("bird", "tasks", "working_graphic_id"),
        ("bird", "tasks", "carrying_graphic_id"),
        ("bird", "tasks", "moving_graphic_id"),
        ("bird", "tasks", "proceeding_graphic_id"),
        ("selection_graphics",),
    ]

    # Expand to all civs if civ_ids == [-1]
    if civ_ids == [-1]:
        civ_ids = range(len(DATA.civs))

    for civ_id in civ_ids:
        # If unit_ids == [-1], expand to all units of this civ
        if unit_ids == [-1]:
            current_unit_ids = range(len(DATA.civs[civ_id].units))
        else:
            current_unit_ids = unit_ids

    for unit_id, replacement_id in zip(current_unit_ids, replacement_ids):
        if unit_id >= len(DATA.civs[civ_id].units) or replacement_id >= len(DATA.civs[civ_id].units):
            continue  # skip invalid indexes

    try:
        target_unit = DATA.civs[civ_id].units[unit_id]
    except:
        print(f'ERROR With unit {unit_id}')
    source_unit = DATA.civs[civ_id].units[replacement_id]

    # Copy icon if this is a creatable unit (>=125 and <=1327)
    if 125 <= unit_id <= 1327:
        target_unit.icon_id = source_unit.icon_id

    for attr_path in attributes:
        try:
            src = source_unit
            tgt = target_unit
            for attr in attr_path[:-1]:
                src = getattr(src, attr)
                tgt = getattr(tgt, attr)
            setattr(tgt, attr_path[-1], getattr(src, attr_path[-1]))
        except AttributeError:
            continue

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
        
def get_effect_id(name):
    for i, effect in enumerate(DATA.effects):
        if effect.name.lower() == name.lower():
            return i
    return -1
                    
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

def load_original_string_lines():
    global ORIGINAL_STRING_LINES
    ORIGINAL_STRING_LINES = {}
    with open(ORIGINAL_STRINGS, 'r', encoding='utf-8') as original_file:
        original_strings_list = original_file.readlines()
        for line in original_strings_list:
            match = re.match(r'^(\d+)', line)
            if match:
                key = int(match.group(1))
                ORIGINAL_STRING_LINES[key] = line

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())

