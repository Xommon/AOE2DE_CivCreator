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
import unicodedata
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5.QtWidgets import QUndoCommand

from PyQt5.QtWidgets import QUndoCommand

class RenameCivCommand(QUndoCommand):
    def __init__(self, app, old_name, new_name, description="Rename Civ"):
        super().__init__(description)
        self.app = app          # reference to your MyApp
        self.old_name = old_name
        self.new_name = new_name

    def undo(self):
        self.app._apply_civ_rename(self.new_name, self.old_name)

    def redo(self):
        self.app._apply_civ_rename(self.old_name, self.new_name)

class MyApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("main_window.ui", self)
        self.setWindowTitle("Talofa")
        self.centralwidget.setEnabled(False)

        # Menu buttons
        self.actionSave_Mod.triggered.connect(self.save_mod)
        self.actionOpen_Mod.triggered.connect(self.open_mod)

        # Program buttons
        self.button_civ_name.clicked.connect(self.change_name)

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
            def __init__(self, index, name, description, tech_tree_index, team_bonus_index, unique_unit_index, language, unique_techs, graphics):
                self.index = index
                self.name = name
                self.description = description
                self.tech_tree_index = tech_tree_index
                self.team_bonus_index = team_bonus_index
                self.unique_unit_index = unique_unit_index
                self.language = language
                self.unique_techs = unique_techs
                self.graphics = graphics

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
        GRAPHICS_GENERAL = {'Austronesian': 29, 'Byzantine': 7, 'Central Asian': 33, 'Central European': 4, 'East Asian': 5, 'Eastern European': 23, 'Mediterranean': 14, 'Mesoamerican': 15, 'Middle Eastern': 9, 'South Asian': 20, 'Southeast Asian': 28, 'West African': 26, 'Western European': 1}
        GRAPHICS_CASTLE = {'Armenians': 44, 'Aztecs': 15, 'Bengalis': 41, 'Berbers': 27, 'Bohemians': 39, 'Britons': 1, 'Bulgarians': 32, 'Burgundians': 36, 'Burmese': 30, 'Byzantines': 7, 'Celts': 13, 'Chinese': 6, 'Cumans': 34, 'Dravidians': 40, 'Ethiopians': 25, 'Franks': 2, 'Georgians': 45, 'Goths': 3, 'Gurjaras': 42, 'Hindustanis': 20, 'Huns': 17, 'Inca': 21, 'Italians': 19, 'Japanese': 5, 'Jurchens': 52, 'Khitan': 53, 'Khmer': 28, 'Koreans': 18, 'Lithuanians': 35, 'Magyars': 22, 'Malay': 29, 'Malians': 26, 'Maya': 16, 'Mongols': 12, 'Persians': 8, 'Poles': 38, 'Portuguese': 24, 'Romans': 43, 'Saracens': 9, 'Shu': 49, 'Sicilians': 37, 'Slavs': 23, 'Spanish': 14, 'Tatars': 33, 'Teutons': 4, 'Turks': 10, 'Vikings': 11, 'Vietnamese': 31, 'Wei': 51, 'Wu': 50}
        GRAPHICS_WONDER = {'Armenians': 44, 'Aztecs': 15, 'Bengalis': 41, 'Berbers': 27, 'Bohemians': 39, 'Britons': 1, 'Bulgarians': 32, 'Burgundians': 36, 'Burmese': 30, 'Byzantines': 7, 'Celts': 13, 'Chinese': 6, 'Cumans': 34, 'Dravidians': 40, 'Ethiopians': 25, 'Franks': 2, 'Georgians': 45, 'Goths': 3, 'Gurjaras': 42, 'Hindustanis': 20, 'Huns': 17, 'Inca': 21, 'Italians': 19, 'Japanese': 5, 'Jurchens': 52, 'Khitan': 53, 'Khmer': 28, 'Koreans': 18, 'Lithuanians': 35, 'Magyars': 22, 'Malay': 29, 'Malians': 26, 'Maya': 16, 'Mongols': 12, 'Persians': 8, 'Poles': 38, 'Portuguese': 24, 'Romans': 43, 'Saracens': 9, 'Shu': 49, 'Sicilians': 37, 'Slavs': 23, 'Spanish': 14, 'Tatars': 33, 'Teutons': 4, 'Turks': 10, 'Vikings': 11, 'Vietnamese': 31, 'Wei': 51, 'Wu': 50}
        GRAPHICS_MONK = {'African': 25, 'Buddhist': 5, 'Catholic': 14, 'Christian': 0, 'Hindu': 40, 'Mesoamerican': 15, 'Muslim': 9, 'Orthodox': 23, 'Pagan': 35, 'Tengri': 12}
        GRAPHICS_MONASTERY = {'Byzantine': 7, 'Central Asian': 33, 'Central European': 4, 'East Asian': 5, 'East African': 25, 'Eastern European': 23, 'Mediterranean': 14, 'Mesoamerican': 15, 'Middle Eastern': 9, 'Pagan': 35, 'South Asian': 40, 'Southeast Asian': 28, 'Southeast European': 44, 'Tengri': 12, 'West African': 26, 'Western European': 1}
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

        # Load all current civs
        global CIVS
        CIVS = []
        for i, civ in enumerate(DATA.civs):
            # Skip specific civs
            global DISABLED_CIVS
            DISABLED_CIVS = ['gaia', 'athenians', 'achaemenids', 'spartans']
            if civ.name.lower() in DISABLED_CIVS:
                continue

            # Get the total amount of civs
            global TOTAL_CIVS_COUNT
            TOTAL_CIVS_COUNT = len(DATA.civs) - len(DISABLED_CIVS)

            # Create new civ object
            new_civ = Civ(-1, '', '', -1, -1, -1, '', [], [])
            new_civ.index = i

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

            # Get the tech tree, team bonus, and unique unit
            for effect_index, effect in enumerate(DATA.effects):
                if effect.name.lower() == f'{civ.name.lower()} tech tree':
                    new_civ.tech_tree_index = effect_index
                elif effect.name.lower() == f'{civ.name.lower()} team bonus':
                    new_civ.team_bonus_index = effect_index
                elif effect.name.lower() == f'{civ.name.lower()}: (castle unit)':
                    new_civ.unique_unit_index = effect.effect_commands[0].a

            # Get the language
            for sound_item in DATA.sounds[303].items:
                if sound_item.civilization == new_civ.index:
                    new_civ.language = sound_item.filename.split('_')[0]

            # Load architecture sets
            global ARCHITECTURE_SETS
            ARCHITECTURE_SETS = []
            '''try:
                with open(f"{MOD_FOLDER}/{MOD_NAME}.pkl", "rb") as file:
                    while True:
                        try:
                            units = pickle.load(file)
                            ARCHITECTURE_SETS.append(units)
                        except EOFError:
                            break
            except FileNotFoundError:
                print(f"[ERROR] Could not find architecture pickle: {MOD_FOLDER}/{MOD_NAME}.pkl")
                ARCHITECTURE_SETS = []'''

            # Sort each dictionary by key alphabetically
            graphic_sets = [dict(sorted(g.items())) for g in graphic_sets]

            # Get current graphics
            graphic_titles = ["General", "Castle", "Wonder", 'Monk', 'Monastery', 'Trade Cart', 'Ships']
            unit_bank = {0: range(0, len(DATA.civs[1].units)), 1: [82, 1430], 2: [276, 1445], 3: [125, 286, 922, 1025, 1327], 4: [30, 31, 32, 104, 1421], 5: [128, 204], 6: [1103, 529, 532, 545, 17, 420, 691, 1104, 527, 528, 539, 21, 442]}
            current_graphics = [''] * len(graphic_titles)

            # Scan the units for their graphics
            '''for i, graphic_set in enumerate(graphic_sets):
                try:
                    # Select the unit to test
                    test_unit = unit_bank[i][0] if i > 0 else 463

                    for key, value in graphic_set.items():
                        if DATA.civs[new_civ.index].units[test_unit].standing_graphic == ARCHITECTURE_SETS[value][test_unit].standing_graphic:
                            current_graphics[i] = value
                            break
                except Exception as e:
                    pass'''

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
        ALL_CASTLE_UNITS = ["longbowman", "throwing axeman", "berserk", "teutonic knight", "samurai", "chu ko nu", "cataphract", "war elephant", "mameluke", "janissary", "huskarl", "mangudai", "woad raider", "conquistador", "jaguar warrior", "plumed archer", "tarkan", "war wagon", "genoese crossbowman", "ghulam", "kamayuk", "magyar huszar", "boyar", "organ gun", "shotel warrior", "gbeto", "camel archer", "ballista elephant", "karambit warrior", "arambai", "rattan archer", "konnik", "keshik", "kipchak", "leitis", "coustillier", "serjeant", "obuch", "hussite wagon", "urumi swordsman", "ratha (melee)", "chakram thrower", "centurion", "composite bowman", "monaspa", 'iron pagoda', 'liao dao', 'white feather guard', 'tiger cavalry', 'fire archer', "amazon warrior", "amazon archer", "camel raider", "crusader", "tomahawk warrior", "ninja", "scimitar warrior", "drengr", "qizilbash warrior", 'genitour', 'naasiri', 'elephant gunner', 'flamethrower', 'weichafe', 'destroyer', 'lightning warrior', 'cossack']
        self.dropdown_unique_units.clear()
        for unit_name in ALL_CASTLE_UNITS:
            self.dropdown_unique_units.addItem(unit_name.title(), userData=get_unit_id(unit_name, False))

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
        self.dropdown_scout_units.currentIndexChanged.connect(self.dropdown_scout_units_changed)
        self.dropdown_unique_units.currentIndexChanged.connect(self.dropdown_unique_units_changed)

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

    def _apply_civ_rename(self, old_name, new_name):
        # Change the name in the DAT file
        DATA.civs[CURRENT_CIV.index].name = new_name
        CURRENT_CIV.name = new_name

        # Repopulate the dropdown
        self.dropdown_civ_name.clear()
        for civ in CIVS:
            self.dropdown_civ_name.addItem(civ.name)

        # Update effects
        for effect in DATA.effects:
            if effect.name == f'{old_name} Tech Tree':
                effect.name = f'{new_name} Tech Tree'
            elif effect.name == f'{old_name} Team Bonus':
                effect.name = f'{new_name} Team Bonus'
            elif f'{old_name.upper()}' in effect.name:
                name_list = effect.name.split(':')
                name_list[0] = new_name.upper()
                effect.name = ':'.join(name_list)

        # Update techs
        for tech in DATA.techs:
            if f'{old_name.upper()}' in tech.name:
                name_list = tech.name.split(':')
                name_list[0] = new_name.upper()
                tech.name = ':'.join(name_list)

        # Mark window dirty
        if not self.windowTitle().endswith('*'):
            self.setWindowTitle(f'{self.windowTitle()}*')

    def change_name(self):
        old_name = CURRENT_CIV.name
        new_name = self.input_civ_name.text()

        if (old_name.lower() == new_name.lower() or 
            any(civ.name.lower() == new_name.lower() for civ in CIVS)):
            self.input_civ_name.setText(old_name)
            return

        # Push a rename command onto the stack
        cmd = RenameCivCommand(self, old_name, new_name)
        self.undoStack.push(cmd)

    def dropdown_civ_name_changed(self, index):
        from PyQt5 import QtCore

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
        self.image_civ_icon.setPixmap(QtGui.QPixmap(f'{MOD_FOLDER}/resources/_common/wpfg/resources/civ_techtree/menu_techtree_{icon_names[CURRENT_CIV.index]}.png'))

        # Update description text box
        self.textbox_description.setHtml(description_html)

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
        value = int(DATA.civs[CURRENT_CIV.index].resources[263])
        su_index = self.dropdown_scout_units.findData(value)
        if su_index > -1:
            self.dropdown_scout_units.blockSignals(True)
            self.dropdown_scout_units.setCurrentIndex(su_index)
            self.dropdown_scout_units.blockSignals(False)

        # Update unique unit
        value = CURRENT_CIV.unique_unit_index
        uu_index = self.dropdown_unique_units.findData(value)
        if su_index > -1:
            self.dropdown_unique_units.blockSignals(True)
            self.dropdown_unique_units.setCurrentIndex(uu_index)
            self.dropdown_unique_units.blockSignals(False)

        # Update unique techs
        self.input_castle_tech_name.setText(CURRENT_CIV.unique_techs[0].split('|')[0])
        self.input_castle_tech_description.setText(CURRENT_CIV.unique_techs[0].split('|')[1])
        self.input_imperial_tech_name.setText(CURRENT_CIV.unique_techs[1].split('|')[0])
        self.input_imperial_tech_description.setText(CURRENT_CIV.unique_techs[1].split('|')[1])

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
                current_graphic = DATA.civs[CURRENT_CIV.index].units[test_unit].standing_graphic

                # Find which entry in gdict matches
                for name, value in gdict.items():
                    if DATA.civs[CURRENT_CIV.index].units[test_unit].standing_graphic == ARCHITECTURE_SETS[value][test_unit].standing_graphic:
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

    def dropdown_language_changed(self, index):
        pass

    def dropdown_scout_units_changed(self, index):
        pass

    def dropdown_unique_units_changed(self, index):
        pass


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())

