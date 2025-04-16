# Micheal Quentin
# 02. March 2025
# 2025 Civilisation Creator
# DEBUG: wine /home/xommon/snap/steam/common/.local/share/Steam/steamapps/common/AoE2DE/Tools_Builds/AdvancedGenieEditor3.exe
# DEBUG: /home/xommon/snap/steam/common/.local/share/Steam/steamapps/compatdata/813780/pfx/drive_c/users/steamuser/Games/Age of Empires 2 DE/76561198021486964/mods/local/Test/resources/_common/dat/empires2_x2_p1.dat

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

class Civ:
    def __init__(self, civ_id, buildings, units):
        self.civ_id = civ_id
        self.buildings = buildings
        self.units = units

    def __repr__(self):
        return f"<Civ {self.civ_id} | {len(self.buildings)} buildings, {len(self.units)} units>"

class ProgressTracker:
    def __init__(self, total):
        self.total = total
        self.current = 0

def import_tech_tree():
    import json

    with open(rf'{MOD_FOLDER}/resources/_common/dat/civTechTrees.json', 'r', encoding="utf-8") as file:
        data = json.load(file)

    global CIV_OBJECTS
    CIV_OBJECTS = []

    global FOREST
    FOREST = []

    seen_names = set()  # to track unique names across all civs

    for civ in data["civs"]:
        civ_id = civ.get("civ_id")

        # Skips Battle for Greece civs
        if civ_id == 'ACHAEMENIDS' or civ_id == 'ATHENIANS' or civ_id == 'SPARTANS':
            continue

        buildings = civ.get("civ_techs_buildings", [])
        units = civ.get("civ_techs_units", [])

        CIV_OBJECTS.append(Civ(civ_id, buildings, units))

        # Add unique buildings to FOREST
        for b in buildings:
            name = b.get("Name")
            if name and name not in seen_names:
                seen_names.add(name)
                FOREST.append(b)

        # Add unique units to FOREST
        for u in units:
            name = u.get("Name")
            if name and name not in seen_names:
                seen_names.add(name)
                FOREST.append(u)

def loading_bar(progress: ProgressTracker, label="Progress", length=30):
    while progress.current < progress.total:
        percent = progress.current / progress.total
        filled = int(length * percent)
        bar = colour(Fore.MAGENTA, '█') * filled + '-' * (length - filled)
        sys.stdout.write(f'\r{label}: [{bar}] {int(percent * 100)}%')
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write(f'\r{label}: [{colour(Fore.MAGENTA, '█') * length}] 100%\n')

def slow_task(progress: ProgressTracker, label):
    for i in range(progress.total):
        time.sleep(0.1)  # Simulate work
        progress.current = i + 1  # Update progress

def with_real_progress(task_func, label, total_steps):
    progress = ProgressTracker(total_steps)
    bar_thread = Thread(target=loading_bar, args=(progress, label))
    bar_thread.start()
    
    task_func(progress)  # run your actual logic with progress tracking

    bar_thread.join()

def save_dat(progress: ProgressTracker, path):
    # Simulate steps while saving (real .save() is a black box)
    for i in range(progress.total - 1):
        time.sleep(0.01)
        progress.current = i + 1

    DATA.save(path)
    
    progress.current = progress.total


def load_dat(progress: ProgressTracker, path):
    global DATA
    DATA = DatFile.parse(path)

    # Simulate progress steps — if you can't track real ones
    for i in range(progress.total):
        time.sleep(0.01)  # Very short sleep to simulate "work"
        progress.current = i + 1

def colour(*args):
    # Last argument is the string
    string = args[-1]
    
    # All previous args are styles
    styles = args[:-1]

    # Combine styles
    new_string = ''.join(styles) + string + Style.RESET_ALL
    return new_string

def save_description(description_code_, description_lines_):
    with open(MOD_STRINGS, 'r+') as file:
        # Read all lines
        lines = file.readlines()

        # Find and modify the line with description_code
        for i, current_line in enumerate(lines):
            if current_line.startswith(description_code_):
                # Reconstruct the modified line
                lines[i] = description_code_ + f' "{r"\n".join(description_lines_)}"\n'
                break

        # Write the updated lines back to the file
        file.seek(0)
        file.writelines(lines)
        file.truncate()  # Ensure remaining old content is removed

def get_unit_name(unit_id):
    with open(ORIGINAL_STRINGS, 'r') as file:
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
            
def get_unit_id(name):
    names = [name]
    # Try to depluralise the word
    if name[:-1] == 's':
        names.append(name[-1])
    if name[:-3] == 'ies':
        names.append(f'{name[-3]}y')
    if name == 'men-at-arms':
        names.append('man-at-arms')

    for name_type in names:
        try:
            for i, unit in enumerate(DATA.civs[1].units):
                if unit.name.lower() == name_type.lower():
                    return i
        except:
            # As a backup, search for name in the strings JSON file
            string_ids = []
            with open(ORIGINAL_STRINGS, 'r') as file:
                get_unit_id_lines = file.readlines()
                for line in get_unit_id_lines:
                    if f'"{name_type.lower()}"' in line.lower():
                        match = re.match(r'\d+', line)
                        if match:
                            string_ids.append(match.group())

            for i, unit in enumerate(DATA.civs[1].units):
                try:
                    if str(unit.language_dll_name) in string_ids:
                        return i
                except:
                    pass

def get_unit_categories(name):
    # Switch name to id
    if int(name) != name:
        unit_index = get_unit_id(name)
    else:
        unit_index = name

    # Grab the unit
    unit_object = DATA.civs[1].units[unit_index]

    # Create the empty categories list
    categories = []

    # Add categories from description
    try:
        description_categories = ["Foot Archer", "Skirmisher", "Mounted Archer", "Mounted", "Trade", "Infantry", "Cavalry", "Light Horseman", "Heavy Cavalry", "Warship", "Gunpowder", "Siege"]

        # Separate the first sentence of the second line
        description_line = get_string(unit_object.language_dll_name + 21000)
        description_line = ''.join(description_line.split(rf'\n')[1]).split('.')
        description_line = description_line[0]

        # Get the categories from the description
        for desc_cat in description_categories:
            if desc_cat in description_line:
                categories.append(desc_cat)

                if desc_cat == 'Light Horseman':
                    categories.append('Cavalry')
    except Exception as e:
        pass

    # Add category for creation location
    creation_locations = {87: 'Archery Range', 12: 'Barracks', 101: 'Stable', 49: 'Siege Workshop', 82: 'Castle', 45: 'Dock'}
    try:
        if unit_object.creatable.train_location_id in creation_locations:
            categories.append(creation_locations[unit_object.creatable.train_location_id])
    except:
        pass

    # Add category for lines
    if get_unit_line(unit_index):
        categories.append(get_unit_line(unit_index))

    # Add category for ranged units
    try:
        if unit_object.type_50.max_range > 1:
            categories.append('Ranged')
    except:
        pass

    # Add category for elephant units
    try:
        if 'elephant' in get_unit_name(unit_index).lower():
            categories.append('Elephant')

        # Add category for camel units
        if 'camel' in get_unit_name(unit_index).lower():
            categories.append('Camel')

        # Add category for siege units
        if 'siege' in get_unit_name(unit_index).lower():
            categories.append('Siege')
    except:
        pass

    # Return the categories
    return categories
        
def get_tech_id(name):
    # Search with internal_name
    for i, tech in enumerate(DATA.techs):
        if tech.name == name:
            return i
        
    # As a backup, search for name elsewhere
    string_id = -1
    with open(ORIGINAL_STRINGS, 'r') as file:
        get_tech_id_lines = file.readlines()
        for line in get_tech_id_lines:
            if name in line.lower():
                string_id = re.sub(r'^\d+\s+', '', line)

    for i, tech in enumerate(DATA.techs):
        if tech.language_dll_name == string_id:
            return i
        
def get_string(code):
    with open(ORIGINAL_STRINGS, 'r') as original_file:
        original_lines = original_file.readlines()

        for line in original_lines:
            try:
                if re.match(r'\d+', line).group() == str(code):
                    return re.search(r'"(.*?)"', line).group(1)
            except:
                pass
            
        return ''
        
def change_string(index, new_string):
    string_line = ''

    # Get the original line
    with open(ORIGINAL_STRINGS, 'r') as original_file:
        original_lines = original_file.readlines()
        for i, line in enumerate(original_lines):
            if line.startswith(f'{index} '):
                string_line = line

    # Find modded line if it exists
    with open(MOD_STRINGS, 'r+') as mod_file:
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

def get_unit_line(unit_id, civ_index=None):
    final_unit = None
    visited_ids = set()

    # Convert name to ID if a string is passed
    if isinstance(unit_id, str):
        unit_id = get_unit_id(unit_id) 

    while unit_id != -1 and unit_id not in visited_ids:
        visited_ids.add(unit_id)
        found = False

        # Choose civ to search in
        civs_to_search = [CIV_OBJECTS[civ_index]] if civ_index is not None else CIV_OBJECTS

        for civ in civs_to_search:
            for unit in civ.units:
                if unit.get("Node ID") == unit_id:
                    final_unit = unit
                    unit_id = unit.get("Link ID", -1)
                    found = True
                    break
            if found:
                break

        if not found:
            break

    if final_unit:
        return f'{final_unit.get('Name')}-'
    else:
        return None
    
def get_unit_line_ids(name):
    # Convert to unit index
    if str(name).isdigit():
        unit_index = int(name)
    else:
        unit_index = get_unit_id(name)

    # Search for unit lines in the forest
    node_ids = []
    visited = set()

    def dfs(current_id):
        for unit in FOREST:
            if unit.get("Link ID") == current_id:
                next_id = unit.get("Node ID")
                if next_id not in visited:
                    node_ids.append(next_id)
                    visited.add(next_id)
                    dfs(next_id)

    # Include the starting ID itself
    node_ids.append(unit_index)
    visited.add(unit_index)
    dfs(unit_index)

    return node_ids

# Complete text
def make_completer(options_list):
    def completer(text, state):
        matches = [s for s in options_list if s.lower().startswith(text.lower())]
        return matches[state] if state < len(matches) else None
    return completer

# Create bonuses
def create_bonus(bonus_string_original, civ_id):
    # Bonus object
    class bonus_object:
        def __init__(self, name=None, number=None, stat=None, age_stat=None):
            self.name = name
            self.number = number
            self.stat = stat
            self.age_stat = age_stat

    # Create an empty list for bonus objects
    bonus_items = []

    # Lowercase the bonus string
    bonus_string = bonus_string_original.lower()

    # Create the tech and effect, set the civilisation and names
    final_techs = [genieutils.tech.Tech(required_techs=(0, 0, 0, 0, 0, 0), resource_costs=(ResearchResourceCost(type=0, amount=0, flag=0), ResearchResourceCost(type=0, amount=0, flag=0), ResearchResourceCost(type=0, amount=0, flag=0)), required_tech_count=0, civ=civ_id + 1, full_tech_mode=0, research_location=-1, language_dll_name=7000, language_dll_description=8000, research_time=0, effect_id=-1, type=0, icon_id=-1, button_id=0, language_dll_help=107000, language_dll_tech_tree=157000, hot_key=-1, name=f'{DATA.civs[civ_id + 1].name.upper()}: {bonus_string_original}', repeatable=1)]
    final_effects = [genieutils.effect.Effect(name=f'{DATA.civs[civ_id + 1].name.upper()}: {bonus_string_original}', effect_commands=[])]

    # Split the bonus string into words
    words = bonus_string.lower().split()

    # Stat dictionary
    stat_dictionary = {'carry': ['S14'], 'hit points': ['S0'], 'hp': ['S0'], 'line of sight': ['S1', 'S23'], 'los': ['S1', 'S23'], 'move': ['S5'], 'pierce armor': ['S8.0768'], 'armor vs. cavalry archers': ['S8.7168'], 'armor vs. elephants': ['S8.128'], 'armor vs. infantry': ['S8.0256'], 'armor vs. cavalry': ['S8.2048'], 'armor vs. archers': ['S8.384'], 'armor vs. ships': ['S8.4096'], 'armor vs. siege': ['S8.512'], 'armor vs. gunpowder': ['S8.5888'], 'armor vs. spearmen': ['S8.6912'], 'armor vs. eagles': ['S8.7424'], 'armor vs. camels': ['S8.768'], 'armor': ['S8.1024'], 'attack': ['S9'], 'range': ['S1', 'S12', 'S23'], 'minimum range': ['S20'], 'train': ['S101'], 'work': ['S13']}

    # Resource dictionary
    resource_dictionary = {'food': ['R0', 'R103'], 'wood': ['R1', 'R104'], 'gold': ['R3', 'R105'], 'stone': ['R2', 'R106']}

    # Declare exception
    exception = ''

    # Precompute at the start of the function
    unit_name_map = {}
    for unit in DATA.civs[1].units:
        try:
            name = get_unit_name(unit.id).lower()
            unit_name_map.setdefault(name, []).append(f"U{unit.id}")
        except:
            continue

    i = 0
    while i < len(words):
        word = words[i]

        # Skip useless words
        if word in ['and', 'but', 'have', 'has']:
            i += 1
            continue

        # Search for exception
        if '(' in word:
            exception = '-'

        matched = False

        # === Unit Categories ===
        phrase = ''
        best_match = ''

        # Expand word by word from index i
        for j in range(i, len(words)):
            phrase = f"{phrase} {words[j]}".strip()
            if phrase in UNIT_CATEGORIES:
                best_match = phrase

        # If a match was found, add its values
        if best_match:
            bonus_items.append(UNIT_CATEGORIES[best_match])
            i += len(best_match.split())
            continue  # Continue to next word after processing best match

        # === Individual Units ===
        def normalise_variants(p):
            variants = {p}
            if p.endswith('ies'):
                variants.add(p[:-3] + 'y')
            if p.endswith('s') and not p.endswith('ss'):
                variants.add(p[:-1])
            if 'men' in p:
                variants.add(p.replace('men', 'man'))
            return variants

        best_unit_match = []
        best_unit_match_length = 0

        for j in range(i, len(words)):
            phrase = ' '.join(words[i:j+1]).strip().lower()
            variants = normalise_variants(phrase)

            for variant in variants:
                if variant in unit_name_map:
                    best_unit_match = unit_name_map[variant]
                    best_unit_match_length = j - i + 1
                    break  # take the first good match for performance
            if best_unit_match:
                break  # stop expanding once a match is found
            
        if best_unit_match:
            bonus_items.append(best_unit_match)
            i += best_unit_match_length
            continue

        # === Numbers ===
        if any(char.isdigit() for char in word):
            old_numbers = word.split('/')
            negative = '-' in word
            percent = '%' in word

            temp_numbers = []
            for number in old_numbers:
                number = number.strip('-+%')
                number = int(number)

                if percent and not negative:
                    number = float(number / 100 + 1)
                elif percent and negative:
                    number = float((100 - number) / 100)
                else:
                    if negative:
                        number *= -1
                temp_numbers.append(f'N{number}')

            bonus_items.append(temp_numbers)
            i += 1
            continue

        # === Ages ===
        if any(age in word for age in ('dark', 'feudal', 'castle', 'imperial')):
            old_ages = word.split('/')
            temp_ages = []
            for age in old_ages:
                if age == 'dark':
                    temp_ages.append('A104')
                elif age == 'feudal':
                    temp_ages.append('A101')
                elif age == 'castle':
                    temp_ages.append('A102')
                elif age == 'imperial':
                    temp_ages.append('A103')
            bonus_items.append(temp_ages)
            i += 1
            continue

        # === Resources ===
        try:
            bonus_items.append(resource_dictionary[word])
        except:
            if word == 'cost' or word == 'costs':
                resources_added = 0
                for word_ in words[i+1:]:
                    try:
                        # If another cost is announced, break up searching for resources
                        if word_ == 'cost' or word_ == 'costs':
                            break

                        bonus_items.append(resource_dictionary[word_])
                        resources_added += 1
                    except:
                        pass
                    
                # Add all resources if no resource is specified
                if resources_added == 0:
                    for val in resource_dictionary.values():
                        if val not in bonus_items:
                            bonus_items.append(val)

                i += 1
                continue

        # === Stats ===
        for key in stat_dictionary:
            key_words = key.split()
            if word == key_words[0]:
                following = words[i:i+len(key_words)]
                if following == key_words:
                    bonus_items.append(stat_dictionary[key])
                    i += len(key_words)
                    matched = True
                    break
        if matched:
            continue

        # Reset exception
        if ')' in word:
            exception = '-'

        i += 1

    # Print the result
    print(f'{bonus_string_original}: {bonus_items}')

    # Set up the list
    #bonus_effect_commands = []
    #bonus_string = bonus_string.lower()

    # Bonus unit lines bank
    '''bonus_unit_lines = {
        # Categories
        'all units': [0.5, 6.5, 12.5, 13.5, 18.5, 43.5, 19.5, 22.5, 2.5, 36.5, 51.5, 44.5, 54.5, 55.5, 35.5],
        'military': [0.5, 35.5, 6.5, 36.5, 47.5, 12.5, 44.5, 23.5],
        'infantry': [6.5],
        #'villager': [4.5],
        #'monk': [18.5, 43.5],
        'all archers': [0.5],
        'cavalry': [12.5, 23.5, 47.5, 36.5],
        'cavalry archers': [36.5],
        'ships': [2.5, 21.5, 22.5, 20.5, 53.5],
        'boats': [2.5, 21.5, 22.5, 20.5, 53.5],
        'stable': [12.5, 47.5],
        'tower': [52.5],
        'building': [3.5],

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
        'dromons' : [1795],
        'cannon galleons' : [420, 691],
        'cannon galleon line' : [420, 691],
        'cannon galleon-line' : [420, 691],
        'warrior priest' : [1811, 1831],
        'monk' : [1811, 1826, 1827],
        'non-unique barracks units' : [74, 75, 76, 473, 567, 93, 358, 359, 1786, 1787, 1788, 751, 753, 752],
        'scouts' : [448, 546, 441, 1707],
        'scout-line' : [448, 546, 441, 1707],
        'scout line' : [448, 546, 441, 1707],
        'steppe lancers' : [1370, 1372],
        'rathas' : [1738, 1740, 1759, 1761],
        'trade units' : [17, 128, 204],
        'canoes' : [],
        'canoe-line' : [],
        'canoe line' : [],
        'camels' : [282, 556, 1755, 329, 330, 207, 1007, 1009, 1263],
        'camel units' : [282, 556, 1755, 329, 330, 207, 1007, 1009, 1263],
        'villagers' : [83, 293, 590, 592, 123, 218, 122, 216, 56, 57, 120, 124, 354, 118, 212, 156, 220, 222, 214, 259, 579, 581],
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
    bonus_buildng_lines = {
    # Buildings
        
    }

    
    # Extract units
    primary_units = []
    secondary_units = []
    def get_bonus_units():
        nonlocal primary_units, secondary_units
        excluded_units = []

        # Get the indexes of the parentheses
        parentheses_positions = [bonus_string.find('('), bonus_string.find(')')]

        # Check unit lines first
        for unit_line in bonus_unit_lines:
            # Get the index of the word
            unit_line_index = bonus_string.find(unit_line)

            if unit_line in bonus_string:
                # Check for redundancies and false flags
                if unit_line == 'archers' and bonus_string.find('cavalry archers') == unit_line_index - 8:
                    continue
                elif unit_line == 'cavalry' and bonus_string.find('cavalry archers') == unit_line_index:
                    continue
                
                # Skip mentions of armour against a specific unit
                elif bonus_string.find('against') == unit_line_index - len(unit_line) - 1:
                    print(f'skipping {unit_line}')
                    continue

                # Add primary unit
                if unit_line_index < parentheses_positions[0] or parentheses_positions == [-1, -1]:
                    primary_units.extend(bonus_unit_lines[unit_line])

                # Add secondary unit
                elif unit_line_index > parentheses_positions[1]:
                    secondary_units.extend(bonus_unit_lines[unit_line])

        # Check for individual units
        for i, unit in enumerate(DATA.civs[1].units):
            try:
                # Get the index of the word
                unit_index = bonus_string.find(unit.name.lower())

                # Singularise the unit name
                current_unit_names = [get_unit_name(i).lower()]
                if current_unit_names[0].endswith('ies'):
                    current_unit_names.append(f'{current_unit_names[0][-3]}y')
                elif current_unit_names[0].endswith('s'):
                    current_unit_names.append(f'{current_unit_names[0][-1]}')
                elif current_unit_names[0] == 'villager' or current_unit_names[0] == 'villagers':
                    current_unit_names.append('villager (male)')

                for name in current_unit_names:
                    if name in bonus_string and name != '':
                        # Add primary unit
                        if unit_index < parentheses_positions[0] or parentheses_positions == [-1, -1]:
                            primary_units.append(i)

                        # Add secondary unit
                        elif unit_index > parentheses_positions[1]:
                            secondary_units.append(i)
            except:
                pass

        # Add exception units
        for i, unit in enumerate(DATA.civs[1].units):
            try:
                if get_unit_name(i).lower() in bonus_string and get_unit_name(i) != '':
                    unit_line_index = bonus_string.find(get_unit_name(i).lower())

                    if unit_line_index > parentheses_positions[0] and unit_line_index < parentheses_positions[1]:
                        excluded_units.append(i)
            except:
                pass

        #print('excluded units:', excluded_units)

        # Remove duplicates
        primary_units = list(set(primary_units))

        # Remove excluded units
        primary_units[:] = [x for x in primary_units if x not in excluded_units]

    # Extract all buildings
    bonus_buildings = []
    def get_bonus_buildings():
        # Set up buildings
        for i, building in enumerate(bonus_buildng_lines):
            if building in bonus_string:
                bonus_buildings.extend(bonus_buildng_lines[building])

    # Extract all technologies
    bonus_techs = []
    def get_bonus_techs():
        for i, tech in enumerate(DATA.techs):
            if tech.name.lower() in bonus_string and tech.name != '':
                bonus_techs.append(i)

    # Extract the number
    bonus_number = [0, '+'] # Set default number to 0 and addition
    def get_bonus_number():
        for i, word in enumerate(bonus_string.split(' ')):
            try:
                bonus_number[0] = int(word.strip('%'))

                # Change the percent into a usable number and set type of number
                if '%' in word:
                    bonus_number[0] = bonus_number[0] / 100
                    bonus_number[1] = '*'
                else:
                    bonus_number[1] = '+'

                # Look for 'more'/'less'
                if (bonus_string.split(' ')[i + 1] == 'more' or bonus_string.split(' ')[i + 1] == 'faster') and bonus_number[1] == '*':
                    bonus_number[0] = abs(bonus_number[0]) + 1
                elif bonus_string.split(' ')[i + 1] == 'less' and bonus_number[1] == '+':
                    bonus_number[0] = abs(bonus_number[0]) * -1
                elif (bonus_string.split(' ')[i + 1] == 'less' or bonus_string.split(' ')[i + 1] == 'slower') and bonus_number[1] == '*':
                    bonus_number[0] = 1 - bonus_number[0]

                break
            except:
                continue

    # Extract the tech resources
    bonus_tech_resource = []
    def get_bonus_tech_resource():
        for word in bonus_string.split(' '):
            if word == 'food':
                bonus_tech_resource.append(0)
            elif word == 'wood':
                bonus_tech_resource.append(1)
            elif word == 'stone':
                bonus_tech_resource.append(2)
            elif word == 'gold':
                bonus_tech_resource.append(3)
        
        # Add all resources if none were found
        if len(bonus_tech_resource) == 0:
            bonus_tech_resource.append(0)
            bonus_tech_resource.append(1)
            bonus_tech_resource.append(2)
            bonus_tech_resource.append(3)

    # Extract the unit resource
    bonus_unit_resource = []
    def get_bonus_unit_resource():
        for word in bonus_string.split(' '):
            if word == 'food':
                bonus_tech_resource.append(103)
            elif word == 'wood':
                bonus_tech_resource.append(104)
            elif word == 'gold':
                bonus_tech_resource.append(105)
            elif word == 'stone':
                bonus_tech_resource.append(106)
        
        # Add all resources if none were found
        if len(bonus_unit_resource) == 0:
            bonus_unit_resource.append(100)

    # Extract the age
    #total_ages = 0
    def get_bonus_age():
        if 'feudal' in bonus_string:
            new_tuple = list(bonus_technology[0].required_techs)
            new_tuple[0] = 101
            bonus_technology[0].required_techs = new_tuple
            bonus_technology[0].required_tech_count = 1
            #total_ages += 1
        if 'castle' in bonus_string:
            new_tuple = list(bonus_technology[0].required_techs)
            new_tuple[0] = 102
            bonus_technology[0].required_techs = new_tuple
            bonus_technology[0].required_tech_count = 1
            #total_ages += 1
        if 'imperial' in bonus_string:
            new_tuple = list(bonus_technology[0].required_techs)
            new_tuple[0] = 103
            bonus_technology[0].required_techs = new_tuple
            bonus_technology[0].required_tech_count = 1
            #total_ages += 1

    # Extract the stats
    bonus_stats = []
    def get_bonus_stats():
        if 'hp' in bonus_string:
            bonus_stats.append(0)
        elif 'los' in bonus_string or 'line of sight' in bonus_string:
            bonus_stats.append(1)
            bonus_stats.append(23)
        elif 'movement' in bonus_string or 'move' in bonus_string:
            bonus_stats.append(5)
        elif 'armor' in bonus_string or 'armour' in bonus_string:
            armour_number = 8

            # Get the specific kind of armour change
            if 'pierce' in bonus_string:
                armour_number += 0.0768
            elif 'against cavalry archers' in bonus_string:
                armour_number += 0.7168
            elif 'against elephants' in bonus_string:
                armour_number += 0.1280
            elif 'against infantry' in bonus_string:
                armour_number += 0.0256
            elif 'against cavalry' in bonus_string:
                armour_number += 0.2048
            elif 'against archers' in bonus_string:
                armour_number += 0.3840
            elif 'against ships' in bonus_string or 'against warships' in bonus_string:
                armour_number += 0.4096
            elif 'against siege' in bonus_string:
                armour_number += 0.5120
            elif 'against gunpowder' in bonus_string:
                armour_number += 0.5888
            elif 'against spearmen' in bonus_string:
                armour_number += 0.6912
            elif 'against eagles' in bonus_string or 'against eagle' in bonus_string:
                armour_number += 0.7424
            elif 'against camel' in bonus_string:
                armour_number += 0.7680

                # Add Mamelukes to the category of camels
                bonus_stats.append(8.8960 + bonus_number[0] / 10000)
            else:
                armour_number += 0.1024

            # Add the number value to the armour
            armour_number += bonus_number[0] / 10000

            # Add the complex armour to the list
            bonus_stats.append(armour_number)
        elif 'attack' in bonus_string:
            bonus_stats.append(9)
        elif 'range' in bonus_string:
            bonus_stats.append(12)
            bonus_stats.append(23)
        elif 'minimum range' in bonus_string or 'min range' in bonus_string:
            bonus_stats.append(20)
        elif 'train' in bonus_string or 'built' in bonus_string:
            bonus_stats.append(101)

        # Remove duplicates
        #bonus_stats = list(dict.fromkeys(bonus_stats))

    ## BONUS PROMPTS ##

    # First [Fortified Church/Monastery] receives a free Relic
    if 'first fortified church receives a free relic' in bonus_string or 'first monastery receives a free relic' in bonus_string:
        # Create effect commands
        bonus_effect_commands.append(genieutils.effect.EffectCommand(1, 234, 0, -1, 1))
        bonus_effect_commands.append(genieutils.effect.EffectCommand(1, 283, 0, -1, 1))
        bonus_effect_commands.append(genieutils.effect.EffectCommand(7, 285, 104, 1, 0))
        bonus_effect_commands.append(genieutils.effect.EffectCommand(1, 283, 0, -1, 0))
    
    # [Unit] [#/%] blast radius
    elif 'blast radius' in bonus_string:
        # Get items
        get_bonus_units()
        get_bonus_number()

        # Break if no items were found
        if len(primary_units) == 0 or bonus_number[0] == 0:
            print("\033[31mERROR: Invalid bonus description.\033[0m")
            print("\033[31mTry using the format: [Unit] [%] blast radius\033[0m")
            return [], []
        
        # Get effect ID
        if bonus_number[1] == '+':
            effect_id = 4
        elif bonus_number[1] == '*':
            effect_id = 5

        # Create effect commands
        for unit_id in primary_units:
            # Check for unit category
            if int(unit_id) != unit_id:
                unit_category_id = int(unit_id)
                unit_id_post = -1
            else:
                unit_category_id = -1
                unit_id_post = unit_id

            # Add blast damage
            bonus_effect_commands.append(genieutils.effect.EffectCommand(effect_id, unit_id_post, unit_category_id, 22, bonus_number[0]))

    # [Technology] free
    elif 'free' in bonus_string:
        # Get items
        get_bonus_techs()

        # Break if no items were found
        if len(bonus_techs) == 0:
            print("\033[31mERROR: Invalid bonus description.\033[0m")
            print("\033[31mTry using the format: [Technology] free\033[0m")
            return [], []

        # Create effect commands
        for tech_id in bonus_techs:
            # Remove cost
            bonus_effect_commands.append(genieutils.effect.EffectCommand(101, tech_id, 0, 0, 0))
            bonus_effect_commands.append(genieutils.effect.EffectCommand(101, tech_id, 1, 0, 0))
            bonus_effect_commands.append(genieutils.effect.EffectCommand(101, tech_id, 2, 0, 0))
            bonus_effect_commands.append(genieutils.effect.EffectCommand(101, tech_id, 3, 0, 0))

            # Remove time
            bonus_effect_commands.append(genieutils.effect.EffectCommand(103, tech_id, 0, 0, 0))

    # [Unit/Building] cost [%] ++ [Resource] ++ starting in the [Age]
    elif 'cost' in bonus_string:
        # Get items
        get_bonus_units()
        get_bonus_buildings()
        get_bonus_number()
        get_bonus_unit_resource()
        get_bonus_age()

        # Break if no items were found
        if len(bonus_unit_lines) == 0 or bonus_number[0] == 0:
            print("\033[31mERROR: Invalid bonus description.\033[0m")
            print("\033[31mTry using the format: [Unit/Building] cost [%] ++ [Resource] ++ starting in the [Age]\033[0m")
            return [], []

        # Get effect ID
        if bonus_number[1] == '+':
            effect_id = 4
        elif bonus_number[1] == '*':
            effect_id = 5

        # Create effect commands
        for unit_id in primary_units:
            # Check for unit category
            if int(unit_id) != unit_id:
                unit_category_id = int(unit_id)
                unit_id_post = -1
            else:
                unit_category_id = -1
                unit_id_post = unit_id

            # Change cost
            for resource in bonus_unit_resource:
                bonus_effect_commands.append(genieutils.effect.EffectCommand(effect_id, unit_id_post, unit_category_id, resource, bonus_number[0]))

    # [Villager/Building] work [%] faster
    elif 'work' in bonus_string or 'works' in bonus_string:
        # Get items
        get_bonus_units()
        get_bonus_buildings()
        get_bonus_number()

        # Break if no items were found
        if bonus_number[0] == 0:
            print("\033[31mERROR: Invalid bonus description.\033[0m")
            print("\033[31mTry using the format: [Villager/Building] work [%] faster\033[0m")
            return [], []

        # Get effect ID
        if bonus_number[1] == '+':
            effect_id = 4
        elif bonus_number[1] == '*':
            effect_id = 5

        # Create effect commands
        for unit_id in (primary_units + bonus_buildings):
            # Check for unit category
            if int(unit_id) != unit_id:
                unit_category_id = int(unit_id)
                unit_id_post = -1
            else:
                unit_category_id = -1
                unit_id_post = unit_id

            # Change work rate
            bonus_effect_commands.append(genieutils.effect.EffectCommand(effect_id, unit_id_post, unit_category_id, 13, bonus_number[0]))

    # [Villager] carry [#/%] more
    elif 'carry' in bonus_string or 'carries' in bonus_string:
        # Get items
        get_bonus_units()
        get_bonus_number()

        # Break if no items were found
        if bonus_number[0] == 0:
            print("\033[31mERROR: Invalid bonus description.\033[0m")
            print("\033[31mTry using the format: [Villager] carry [#/%] more\033[0m")
            return [], []

        # Get effect ID
        if bonus_number[1] == '+':
            effect_id = 4
        elif bonus_number[1] == '*':
            effect_id = 5

        # Create effect commands
        for unit_id in primary_units:
            # Change work rate
            bonus_effect_commands.append(genieutils.effect.EffectCommand(effect_id, unit_id, -1, 14, bonus_number[0]))

    # Start with [#] [Resource]
    elif 'start with' in bonus_string or 'starts with' in bonus_string:
        # Get items
        get_bonus_tech_resource()
        get_bonus_number()

        # Break if no items were found
        if bonus_number[0] == 0:
            print("\033[31mERROR: Invalid bonus description.\033[0m")
            print("\033[31mTry using the format: Start with [#] [Resource]\033[0m")
            return [], []

        # Get effect ID
        if bonus_number[1] == '+':
            effect_id = 1
        elif bonus_number[1] == '*':
            effect_id = 6

        # Create effect commands
        for resource_id in bonus_tech_resource:
            # Change work rate
            bonus_effect_commands.append(genieutils.effect.EffectCommand(effect_id, 91 + resource_id, 1, -1, bonus_number[0]))

    # Relics generate [%] gold
    elif 'relics generate' in bonus_string or 'relic generates' in bonus_string:
        # Get items
        get_bonus_number()

        # Break if no items were found
        if bonus_number[0] == 0:
            print("\033[31mERROR: Invalid bonus description.\033[0m")
            print("\033[31mTry using the format: Relics generate [%] gold\033[0m")
            return [], []

        # Get effect ID
        if bonus_number[1] == '+':
            effect_id = 1
        elif bonus_number[1] == '*':
            effect_id = 6

        # Create effect commands
        bonus_effect_commands.append(genieutils.effect.EffectCommand(effect_id, 191, 0, -1, bonus_number[0]))

    # [Unit/Building] receive [%] less bonus damage
    elif 'receive' in bonus_string and 'bonus damage' in bonus_string:
        # Get items
        get_bonus_units()
        get_bonus_buildings()
        get_bonus_number()

        # Break if no items were found
        if bonus_number[0] == 0 or len(primary_units) == 0:
            print("\033[31mERROR: Invalid bonus description.\033[0m")
            print("\033[31mTry using the format: [Unit] receive [%] less bonus damage\033[0m")
            return [], []

        # Create effect commands
        for i, unit_id in enumerate(primary_units + bonus_buildings):
            # Check for unit category
            if int(unit_id) != unit_id:
                unit_category_id = int(unit_id)
                unit_id_post = -1
            else:
                unit_category_id = -1
                unit_id_post = unit_id

            bonus_effect_commands.append(genieutils.effect.EffectCommand(0, unit_id_post, unit_category_id, 24, 1 - bonus_number[0]))

    # Town Centers spawn [#] villagers when the next Age is reached INACTIVE
    elif 'spawn' in bonus_string and 'villagers when the next age is reached' in bonus_string:
        # Get items
        get_bonus_number()

        # Break if no items were found
        if bonus_number[0] == 0:
            print("\033[31mERROR: Invalid bonus description.\033[0m")
            print("\033[31mTry using the format: Town Centers spawn [#] villagers when the next age is reached\033[0m")
            return [], []
        
        # Create a tech for each age
        bonus_technology.append(bonus_technology[0])
        bonus_technology.append(bonus_technology[0])
        bonus_technology[0].required_techs = 101
        bonus_technology[0].required_tech_count = 1
        bonus_technology[1].required_techs = 102
        bonus_technology[1].required_tech_count = 1
        bonus_technology[2].required_techs = 103
        bonus_technology[2].required_tech_count = 1

        # Create effect commands
        bonus_effect_commands.append(genieutils.effect.EffectCommand(7, 83, 109, 2, 0))

    # Town Centers spawn [#] villagers when reaching the [Age] INACTIVE
    elif 'spawn' in bonus_string and 'villagers when reaching the' in bonus_string:
        # Get items
        get_bonus_number()
        get_bonus_age()

        # Break if no items were found
        if bonus_number[0] == 0:
            print("\033[31mERROR: Invalid bonus description.\033[0m")
            print("\033[31mTry using the format: Town Centers spawn [#] villagers when reaching the [Age]\033[0m")
            return [], []

        # Create effect commands
        bonus_effect_commands.append(genieutils.effect.EffectCommand(7, 83, 109, bonus_number[0], 0))

    # [Unit] have [#/%][Stat] ++ in the [Age]
    else:
        try:
            # Get items
            get_bonus_units()
            get_bonus_buildings()
            get_bonus_number()
            get_bonus_stats()
            get_bonus_age()

            # Break if no items were found
            if len(bonus_unit_lines) == 0 or bonus_number[0] == 0 or bonus_stats == []:
                print("\033[31mERROR: Invalid bonus description.\033[0m")
                print("\033[31mTry using the format: [Unit] have [#/%][Stat] ++ in the [Age]\033[0m")
                return [], []

            # Get effect ID
            if bonus_number[1] == '+':
                effect_id = 4
            elif bonus_number[1] == '*':
                effect_id = 5

            # Create effect commands
            for unit_id in (primary_units + bonus_buildings):
                # Check for unit category
                if int(unit_id) != unit_id:
                    unit_category_id = int(unit_id)
                    unit_id_post = -1
                else:
                    unit_category_id = -1
                    unit_id_post = unit_id

                # Change stat
                for stat in bonus_stats:
                    # Get advanced armour information
                    if int(stat) == 8:
                        armour = int(str(stat)[2:6])
                        bonus_effect_commands.append(genieutils.effect.EffectCommand(effect_id, unit_id_post, unit_category_id, int(stat), armour))
                    else:
                        bonus_effect_commands.append(genieutils.effect.EffectCommand(effect_id, unit_id_post, unit_category_id, stat, bonus_number[0]))
        except Exception as e:
            # Error out
            print(e)
            print("\033[31mERROR: Invalid bonus description.\033[0m")
            return [], []'''
        
    # Add the effect commands to the bonus
    #bonus_effect.effect_commands = bonus_effect_commands

    # Return the effect commands
    #return final_techs, final_effects

def toggle_unit(unit_index, mode, tech_tree_index, selected_civ_name):
    # Get unit name or tech name
    is_tech = '_' in str(unit_index)
    if is_tech:
        unit = DATA.techs[int(unit_index[1:])].name.lower()
    else:
        unit = get_unit_name(unit_index).lower()

    # Determine whether enabling or disabling
    if mode == 'toggle' and TECH_TREE[unit] == 0:
        mode = 'enable'
    elif mode == 'toggle' and TECH_TREE[unit] == 1:
        mode = 'disable'

    # Update JSON file
    trigger_tech_id = -1
    json_line_start = 0
    with open(rf'{MOD_FOLDER}/resources/_common/dat/civTechTrees.json', 'r+') as file:
        if unit in TECH_TREE:
            lines = file.readlines()

            # Find the line where the current civ starts
            for i, line in enumerate(lines):
                if f'"civ_id": "{selected_civ_name.upper()}"' in line:
                    json_line_start = i

            # Change the lines in the file
            for i in range(json_line_start, len(lines)):
                if f'\"Name\": \"{unit.title()}\"' in lines[i]:
                    if mode == 'enable':
                        lines[i + 3] = f'          "Node Status": "ResearchedCompleted",\n'
                    elif mode == 'disable':
                        lines[i + 3] = f'          "Node Status\": "NotAvailable",\n'
                    break

            # Save the file
            file.seek(0)
            file.writelines(lines)
            file.truncate()

    # Get tech index
    if not is_tech:
        found = False
        for i, tech in enumerate(DATA.techs):
            for ec in DATA.effects[tech.effect_id].effect_commands:
                if (ec.type == 2 and ec.a == unit_index) or (ec.type == 3 and ec.b == unit_index):
                    tech_index = i
                    found = True
                    break
            if found:
                break
    else:
        tech_index = int(unit_index[1:])
        
    # Update .dat file
    if mode == 'enable':
        for i, effect_command in enumerate(DATA.effects[tech_tree_index].effect_commands):
            if effect_command.type == 102 and effect_command.d == tech_index:
                DATA.effects[tech_tree_index].effect_commands.pop(i)
    elif mode == 'disable':
        DATA.effects[tech_tree_index].effect_commands.append(genieutils.effect.EffectCommand(102, 0, 0, 0, tech_index))

def open_mod(mod_folder):
    with_real_progress(lambda progress: load_dat(progress, rf'{mod_folder}/resources/_common/dat/empires2_x2_p1.dat'), 'Loading Mod', total_steps=100)
    #global DATA
    #DATA = DatFile.parse(rf'{mod_folder}/resources/_common/dat/empires2_x2_p1.dat')
    global MOD_STRINGS
    MOD_STRINGS = rf'{mod_folder}/resources/en/strings/key-value/key-value-modded-strings-utf8.txt'
    global ORIGINAL_STRINGS
    ORIGINAL_STRINGS = rf'{mod_folder}/resources/en/strings/key-value/key-value-strings-utf8.txt'
    global MOD_FOLDER
    MOD_FOLDER = mod_folder
    global MOD_NAME
    MOD_NAME = mod_folder.split('/')[-1]

    # Import tech trees
    import_tech_tree()

    # Save program settings
    with open('settings.pkl', 'wb') as settings:
        pickle.dump(mod_folder, settings)

    # Load important links
    global ORIGINAL_FOLDER
    with open(f'{MOD_FOLDER}/links.pkl', 'rb') as file:
        data = pickle.load(file)  # Unpickle the file
        if isinstance(data, str):  # Ensure it's a string before splitting
            lines = data.splitlines()  # Split by newlines
            if lines:  # Check if the list is not empty
                ORIGINAL_FOLDER = lines[0]  # Set to the first line
            else:
                ORIGINAL_FOLDER = ""  # Set to empty if no lines exist

    # Load architecture sets
    global ARCHITECTURE_SETS
    ARCHITECTURE_SETS = []
    with open(f'{MOD_FOLDER}/{mod_folder.split("/")[-1]}.pkl', 'rb') as file:
        while True:
            try:
                units = pickle.load(file)
                ARCHITECTURE_SETS.append(units)
            except EOFError:
                break

    # Define the base unit categories
    global UNIT_CATEGORIES
    UNIT_CATEGORIES = {"foot archers": ['C0', 'U-7', 'U-6', 'U-1155'], "skirmishers": ['U7', 'U6', 'U1155'], "mounted archers": ['C36'], "mounted": ['C36', 'C12', 'C23'], "trade": ['C2', 'C19'], "infantry": ['C6'], "cavalry": ['C12'], "light horseman": ['C12'], "heavy cavalry": ['C12'], "warships": ['C22'], "gunpowder": ['C44', 'C23'], "siege": ['C13'], 'villagers': ['C4'], 'camel units': ['U282', 'U556'], 'mule carts': ['U1808'], 'military units': ['C0', 'C55', 'C35', 'C6', 'C54', 'C13', 'C51', 'C36', 'C12']}

    # Define the base technologies
    global TECH_CATEGORIES
    TECH_CATEGORIES = {}

    # Add additional units
    for unit in DATA.civs[1].units:
        try:
            unit_buildings = {
                87: 'archery range units', 12: 'barracks units', 101: 'stable units',
                104: 'monastery units', 49: 'siege workshop units', 45: 'dock units', 82: 'castle units'
            }

            if unit.creatable.train_location_id in unit_buildings:
                key = unit_buildings[unit.creatable.train_location_id]
                UNIT_CATEGORIES.setdefault(key, []).append(f'U{unit.id}')

            # Unit lines
            unit_line = get_unit_line(unit.id).lower()
            if unit_line and unit.creatable.train_location_id != 82:
                UNIT_CATEGORIES.setdefault(unit_line, []).append(f'U{unit.id}')
                UNIT_CATEGORIES.setdefault(unit_line + 'line', []).append(f'U{unit.id}')

            # Add the unit-line upgrades
            unit_line_ids = get_unit_line_ids(unit_line[:-1])
            tech_ids = {
                unit.get("Trigger Tech ID")
                for unit in FOREST
                if unit.get("Node ID") in unit_line_ids and unit.get("Trigger Tech ID") is not None
            }

            # Clean the list of blanks
            tech_ids = [f'T{x}' for x in tech_ids if x != -1]

            if tech_ids:
                TECH_CATEGORIES.setdefault(f"{unit_line}line upgrades", []).extend(tech_ids)

            # Elephants and Camels
            name = get_unit_name(unit.id).lower()
            if 'elephant' in name:
                UNIT_CATEGORIES.setdefault('elephant units', []).append(f'U{unit.id}')
            if 'camel' in name:
                UNIT_CATEGORIES.setdefault('camel units', []).append(f'U{unit.id}')
        except:
            pass

    # Convert 2 item lists
    for key in list(UNIT_CATEGORIES.keys()):
        if len(UNIT_CATEGORIES[key]) == 2 and key.endswith('-'):
            new_key = key[:-1] + 's'
            UNIT_CATEGORIES[new_key] = UNIT_CATEGORIES.pop(key)

    # Load tech categories
    for tech in DATA.techs:
        try:
            tech_buildings = {
                87: 'archery range technologies', 12: 'barracks technologies', 101: 'stable technologies',
                104: 'monastery technologies', 49: 'siege workshop technologies', 45: 'dock technologies', 82: 'castle technologies',
                103: 'blacksmith technologies', 209: 'university technologies', 109: 'town center technologies',
                584: 'mining camp technologies', 562: 'lumber camp technologies', 68: 'mill technologies', 84: 'market technologies'
            }

            if tech.research_location in tech_buildings:
                key = tech_buildings[tech.research_location]
                TECH_CATEGORIES.setdefault(key, []).append(f'T{DATA.techs.index(tech)}')
        except:
            pass

    # Add combined technology lists
    TECH_CATEGORIES.setdefault('mule cart technologies', []).extend(TECH_CATEGORIES['mining camp technologies'] + TECH_CATEGORIES['lumber camp technologies'])
    TECH_CATEGORIES.setdefault('economic technologies', []).extend(TECH_CATEGORIES['mining camp technologies'] + TECH_CATEGORIES['lumber camp technologies'] + TECH_CATEGORIES['mill technologies'] + ['T22', 'T213', 'T85'])

    # Combine the dictionaries
    UNIT_CATEGORIES = UNIT_CATEGORIES | TECH_CATEGORIES

    # Remove duplicated items
    UNIT_CATEGORIES = {k: list(dict.fromkeys(v)) for k, v in UNIT_CATEGORIES.items()}

    # Remove entries with one or fewer items
    UNIT_CATEGORIES = {k: v for k, v in UNIT_CATEGORIES.items() if isinstance(v, list) and len(v) > 1}

    # DEBUG: Print dictionary
    #for key, value in UNIT_CATEGORIES.items():
    #    print(f'{key}: {value}')

    # Tell the user that the mod was loaded
    print('Mod loaded!')

    # DEBUG: Print attributes of the unit
    #unit = DATA.civs[1].units[8].creatable.train_location_id
    #attributes = [attr for attr in dir(unit) if not attr.startswith('_') and not callable(getattr(unit, attr))]
    #for attr in attributes:
    #    value = getattr(unit, attr)
    #    print(f"{attr}: {value}")
    time.sleep(1)
    
def new_mod(_mod_folder, _aoe2_folder, _mod_name, revert):
    # Announce revert
    if revert:
        print(f'Reverting {_mod_name}...')

        os.chdir(_mod_folder)
        os.chdir('..')

        # Delete existing mod folder
        shutil.rmtree(_mod_folder)

        # Move back a folder
        _mod_folder = os.path.dirname(_mod_folder)

    # Get local mods folder
    if _mod_folder == '':
        local_mods_folder = input("\nEnter local mods folder location: ")
        if local_mods_folder == '':
            local_mods_folder = '/home/xommon/snap/steam/common/.local/share/Steam/steamapps/compatdata/813780/pfx/drive_c/users/steamuser/Games/Age of Empires 2 DE/76561198021486964/mods/local'
    else:
        local_mods_folder = _mod_folder

    # Get original AoE2DE folder
    if _aoe2_folder == '':
        aoe2_folder = input("Select original \"AoE2DE\" folder location: ")
        if aoe2_folder == '':
            aoe2_folder = '/home/xommon/snap/steam/common/.local/share/Steam/steamapps/common/AoE2DE'
    else:
        aoe2_folder = _aoe2_folder

    # Get name for mod
    if _mod_name == '':
        mod_name = input("Enter new mod name: ")
        if mod_name == '':
            mod_name = 'Test'
    else:
        mod_name = _mod_name

    mod_folder = local_mods_folder + '/' + mod_name

    # Create new folder and change directory to it
    os.makedirs(mod_name, exist_ok=True)
    os.chdir(mod_name)
    MOD_FOLDER = os.path.abspath(os.path.join(local_mods_folder, mod_name))

    # Ensure the mod folder exists
    os.makedirs(MOD_FOLDER, exist_ok=True)

    # Save important links
    with open(f'{MOD_FOLDER}/links.pkl', 'wb') as file:
        pickle.dump(aoe2_folder, file)
        file.write(b'\n')

    # Copy base files into the new mod folder
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
        source_path = os.path.join(aoe2_folder, item)
        destination_path = os.path.join(MOD_FOLDER, item)

        # Ensure destination directory exists
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)

        # Check if source is a file or a folder
        if os.path.isfile(source_path):
            shutil.copy(source_path, destination_path)  # Copy file

    # Open .dat file
    with_real_progress(lambda progress: load_dat(progress, rf'{mod_folder}/resources/_common/dat/empires2_x2_p1.dat'), 'Creating Mod', total_steps=100)

    # Clean-up JSON file
    with open(rf'{MOD_FOLDER}/resources/_common/dat/civTechTrees.json', 'r', encoding='utf-8') as file:
        raw = file.read()

    # Remove comma after a closing brace if it's followed by just whitespace/newlines and a closing bracket
    cleaned = re.sub(r'(})\s*,\s*(\])', r'\1\n\2', raw)
    with open(rf'{MOD_FOLDER}/resources/_common/dat/civTechTrees.json', 'w', encoding='utf-8') as file:
        file.write(cleaned)

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

    # Reformat the default sounds
    sound_ids = {303: 'Villager_Male_Select_4', 301: 'Villager_Male_Move_4', 295: 'Villager_Male_Build_1', 299: 'Villager_Male_Chop_1', 455: 'Villager_Male_Farm_1', 448: 'Villager_Male_Fish_1', 297: 'Villager_Male_Forage_1', 298: 'Villager_Male_Hunt_1', 300: 'Villager_Male_Mine_1', 302: 'Villager_Male_Repair_1', 435: 'Villager_Female_Select_4', 434: 'Villager_Female_Move_4', 437: 'Villager_Female_Build_1', 442: 'Villager_Female_Chop_1', 438: 'Villager_Female_Farm_1', 487: 'Villager_Female_Fish_1', 440: 'Villager_Female_Forage_1', 441: 'Villager_Female_Hunt_1', 443: 'Villager_Female_Mine_1', 444: 'Villager_Female_Repair_1', 420: 'Soldier_Select_3', 421: 'Soldier_Move_3', 422: 'Soldier_Attack_3', 423: 'Monk_Select_3', 424: 'Monk_Move_3', 479: 'King_Select_3', 480: 'King_Move_3'}
    
    # Remove all previous sound items
    for sound_id in sound_ids:
        DATA.sounds[sound_id].items.clear()

    # Set defaults for each civilization
    for civ in DATA.civs[1:]:
        for sound_id in sound_ids:
            # Get the amount of sound items to add
            sound_count = int(sound_ids[sound_id][-1])

            # Add the sound items to the sound
            for i in range(sound_count):
                # Correct the name
                correct_name = civ.name
                if correct_name == 'British':
                    correct_name = 'Britons'
                elif correct_name == 'French':
                    correct_name = 'Franks'

                # Skip certain civilizations
                if correct_name == 'Athenians' or correct_name == 'Spartans' or correct_name == 'Achaemenids':
                    continue

                # Create new name
                if sound_count == 1:
                    new_sound_name = f'{correct_name}_{sound_ids[sound_id][:-2]}'
                else:
                    new_sound_name = f'{correct_name}_{sound_ids[sound_id][:-2]}_{i + 1}'

                # Determine probability
                new_sound_probability = int(100 / sound_count)

                # Create new sound item
                new_sound = genieutils.sound.SoundItem(new_sound_name, 0, new_sound_probability, DATA.civs.index(civ), -1)

                # Add sound item to the sound
                DATA.sounds[sound_id].items.append(new_sound)

    # Copy over custom graphics
    graphics_source_folder = os.path.join(os.path.dirname(__file__), 'graphics')  # Path to the original 'graphics' folder
    graphics_destination_folder = os.path.join(MOD_FOLDER, 'resources/_common/drs/graphics')  # Path to the new 'graphics' folder in the mod folder

    # Ensure the destination directory exists
    os.makedirs(graphics_destination_folder, exist_ok=True)

    # Copy all files from the source 'graphics' folder to the destination
    if os.path.exists(graphics_source_folder):
        for item in os.listdir(graphics_source_folder):
            source_path = os.path.join(graphics_source_folder, item)
            destination_path = os.path.join(graphics_destination_folder, item)

            if os.path.isfile(source_path):
                shutil.copy2(source_path, destination_path)  # Copy file
            elif os.path.isdir(source_path):
                shutil.copytree(source_path, destination_path, dirs_exist_ok=True)  # Copy directory
    else:
        print(f"Warning: Source graphics folder '{graphics_source_folder}' does not exist.")

    # Add the graphics to the .dat file
    starting_graphic_index = len(DATA.graphics)
    DATA.graphics.append(Graphic(name='SEE_Dock2', file_name='None', particle_effect_name='', slp=6067, is_loaded=0, old_color_flag=1, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=60, angle_count=1, speed_multiplier=0.0, frame_duration=0.15000000596046448, replay_delay=0.0, sequence_type=5, id=12733, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=220, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12734, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=4411, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=-120, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Dock2(Base)', file_name='b_byzantinedock_x1', particle_effect_name='', slp=6067, is_loaded=0, old_color_flag=1, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12734, mirroring_mode=0, editor_flag=0, deltas=[], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_ArcheryRange2', file_name='b_feudalarcherybyz_x1', particle_effect_name='', slp=6064, is_loaded=0, old_color_flag=0, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12735, mirroring_mode=0, editor_flag=0, deltas=[], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_ArcheryRange3', file_name='b_castlearcherybyz_x1', particle_effect_name='', slp=6019, is_loaded=0, old_color_flag=0, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12736, mirroring_mode=0, editor_flag=0, deltas=[], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_BombardTower', file_name='b_bombaredtowerbyz_x1', particle_effect_name='', slp=6035, is_loaded=0, old_color_flag=0, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12737, mirroring_mode=0, editor_flag=0, deltas=[], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Barracks3', file_name='b_castlebarracksbyz_x1', particle_effect_name='', slp=6066, is_loaded=0, old_color_flag=0, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12738, mirroring_mode=0, editor_flag=0, deltas=[], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Barracks2', file_name='b_feudalbarracksbyz_x1', particle_effect_name='', slp=6066, is_loaded=0, old_color_flag=0, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12739, mirroring_mode=0, editor_flag=0, deltas=[], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Blacksmith2', file_name='b_feudalblacksmithbyz_x1', particle_effect_name='', slp=6065, is_loaded=0, old_color_flag=0, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12740, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=5314, padding_1=0, sprite_ptr=0, offset_x=-86, offset_y=-110, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Blacksmith3', file_name='b_castleblacksmithbyz_x1', particle_effect_name='', slp=100, is_loaded=0, old_color_flag=0, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12741, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=5314, padding_1=0, sprite_ptr=0, offset_x=-86, offset_y=-110, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_SiegeWorkshop', file_name='b_castlesiegeworkshopbyz_x1', particle_effect_name='', slp=6017, is_loaded=0, old_color_flag=0, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12742, mirroring_mode=0, editor_flag=0, deltas=[], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Stable2', file_name='b_feudalstablebyz_x1', particle_effect_name='', slp=6066, is_loaded=0, old_color_flag=0, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12743, mirroring_mode=0, editor_flag=0, deltas=[], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Stable3', file_name='b_castlestablebyz_x1', particle_effect_name='', slp=6022, is_loaded=0, old_color_flag=0, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12744, mirroring_mode=0, editor_flag=0, deltas=[], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_University3', file_name='b_castleuniversitybyz_x1', particle_effect_name='', slp=1362, is_loaded=0, old_color_flag=0, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12745, mirroring_mode=0, editor_flag=0, deltas=[], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_University4', file_name='b_imperialuniversitybyz_x1', particle_effect_name='', slp=0, is_loaded=0, old_color_flag=0, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12746, mirroring_mode=0, editor_flag=0, deltas=[], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Market2', file_name='b_feudalmarketbyz_x1', particle_effect_name='', slp=6071, is_loaded=0, old_color_flag=0, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12747, mirroring_mode=0, editor_flag=0, deltas=[], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Monastary', file_name='b_monasterybyz_x1', particle_effect_name='', slp=6027, is_loaded=0, old_color_flag=0, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12748, mirroring_mode=0, editor_flag=0, deltas=[], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_WatchTower', file_name='b_towerbyz_x1', particle_effect_name='', slp=6028, is_loaded=0, old_color_flag=0, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12749, mirroring_mode=0, editor_flag=0, deltas=[], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_GuardTower', file_name='b_guardtowerbyz_x1', particle_effect_name='', slp=6031, is_loaded=0, old_color_flag=0, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12750, mirroring_mode=0, editor_flag=0, deltas=[], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Keep', file_name='b_keeptowerbyz_x1', particle_effect_name='', slp=6033, is_loaded=0, old_color_flag=0, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12751, mirroring_mode=0, editor_flag=0, deltas=[], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Market4', file_name='b_imperialmarketbyz_x1', particle_effect_name='', slp=6020, is_loaded=0, old_color_flag=0, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12752, mirroring_mode=0, editor_flag=0, deltas=[], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_House2', file_name='b_feudalhouse_x1', particle_effect_name='', slp=6068, is_loaded=0, old_color_flag=1, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=3, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=6, id=12753, mirroring_mode=0, editor_flag=0, deltas=[], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_House3', file_name='b_imperialhouses_x1', particle_effect_name='', slp=6025, is_loaded=0, old_color_flag=1, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=3, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=6, id=12754, mirroring_mode=0, editor_flag=0, deltas=[], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Mill2', file_name='b_feudalmill_x1', particle_effect_name='', slp=6069, is_loaded=0, old_color_flag=1, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=1, frame_count=12, angle_count=1, speed_multiplier=0.0, frame_duration=0.25, replay_delay=0.0, sequence_type=5, id=12755, mirroring_mode=0, editor_flag=0, deltas=[], angle_sounds=[GraphicAngleSound(frame_num=10, sound_id=307, wwise_sound_id=-1994566283, frame_num_2=55, sound_id_2=307, wwise_sound_id_2=-1994566283, frame_num_3=-1, sound_id_3=-1, wwise_sound_id_3=0)]))
    DATA.graphics.append(Graphic(name='SEE_Mill3', file_name='b_millcastle_x1', particle_effect_name='', slp=748, is_loaded=0, old_color_flag=1, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=1, frame_count=12, angle_count=1, speed_multiplier=0.0, frame_duration=0.25, replay_delay=0.0, sequence_type=5, id=12756, mirroring_mode=0, editor_flag=0, deltas=[], angle_sounds=[GraphicAngleSound(frame_num=10, sound_id=307, wwise_sound_id=-1994566283, frame_num_2=55, sound_id_2=307, wwise_sound_id_2=-1994566283, frame_num_3=-1, sound_id_3=-1, wwise_sound_id_3=0)]))
    DATA.graphics.append(Graphic(name='SEE_StoneWall', file_name='b_normalwallframes_x1', particle_effect_name='', slp=7124, is_loaded=0, old_color_flag=1, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=1, angle_count=5, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=2, id=12757, mirroring_mode=0, editor_flag=0, deltas=[], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_FortifiedWall', file_name='b_fortifiedwall_x1', particle_effect_name='', slp=7126, is_loaded=0, old_color_flag=1, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=1, angle_count=5, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=2, id=12758, mirroring_mode=0, editor_flag=0, deltas=[], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_StoneWall(Construction)', file_name='b_stonewallconstruction_x1', particle_effect_name='', slp=7129, is_loaded=0, old_color_flag=1, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=4, angle_count=5, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=2, id=12759, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12211, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_FortifiedWall(Construction)', file_name='b_fortifiedwallconstruction_x1', particle_effect_name='', slp=7131, is_loaded=0, old_color_flag=1, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=4, angle_count=5, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=2, id=12760, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12211, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Dock3', file_name='None', particle_effect_name='', slp=2260, is_loaded=0, old_color_flag=1, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=60, angle_count=1, speed_multiplier=0.0, frame_duration=0.15000000596046448, replay_delay=0.0, sequence_type=5, id=12761, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=241, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12762, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=4411, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=-120, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Dock3(Base)', file_name='b_castledockbyz_x1', particle_effect_name='', slp=6012, is_loaded=0, old_color_flag=1, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12762, mirroring_mode=0, editor_flag=0, deltas=[], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_House3(Rubble)', file_name='b_medi_house_age3_rubble_x1', particle_effect_name='', slp=2238, is_loaded=0, old_color_flag=0, layer=6, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=678, wwise_sound_id=1668689960, angle_sounds_used=0, frame_count=1, angle_count=3, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=2, id=12763, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12180, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12181, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_House2(Rubble)', file_name='b_medi_house_age2_rubble_x1', particle_effect_name='', slp=2238, is_loaded=0, old_color_flag=0, layer=6, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=678, wwise_sound_id=1668689960, angle_sounds_used=0, frame_count=1, angle_count=3, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=2, id=12764, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12180, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12181, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Stable3(Rubble)', file_name='b_medi_stable_age3_rubble_x1', particle_effect_name='', slp=1012, is_loaded=0, old_color_flag=0, layer=6, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=678, wwise_sound_id=1668689960, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12765, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12182, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12183, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Stable2(Rubble)', file_name='b_medi_stable_age2_rubble_x1', particle_effect_name='', slp=1012, is_loaded=0, old_color_flag=0, layer=6, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=678, wwise_sound_id=1668689960, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12766, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12182, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12183, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Barracks3(Rubble)', file_name='b_medi_barracks_age3_rubble_x1', particle_effect_name='', slp=136, is_loaded=0, old_color_flag=0, layer=6, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=678, wwise_sound_id=1668689960, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12767, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12182, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12183, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Barracks2(Rubble)', file_name='b_medi_barracks_age2_rubble_x1', particle_effect_name='', slp=136, is_loaded=0, old_color_flag=0, layer=6, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=678, wwise_sound_id=1668689960, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12768, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12182, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12183, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_ArcheryRange3(Rubble)', file_name='b_medi_archery_range_age3_rubble_x1', particle_effect_name='', slp=27, is_loaded=0, old_color_flag=0, layer=6, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=678, wwise_sound_id=1668689960, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12769, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12182, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12183, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_ArcheryRange2(Rubble)', file_name='b_medi_archery_range_age2_rubble_x1', particle_effect_name='', slp=27, is_loaded=0, old_color_flag=0, layer=6, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=678, wwise_sound_id=1668689960, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12770, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12182, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12183, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_SiegeWorkshop(Rubble)', file_name='b_medi_siege_workshop_age3_rubble_x1', particle_effect_name='', slp=949, is_loaded=0, old_color_flag=0, layer=6, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=678, wwise_sound_id=1668689960, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12771, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12184, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12185, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Market3(Rubble)', file_name='b_medi_market_age3_rubble_x1', particle_effect_name='', slp=811, is_loaded=0, old_color_flag=0, layer=6, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=678, wwise_sound_id=1668689960, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12772, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12184, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12185, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Market2(Rubble)', file_name='b_medi_market_age2_rubble_x1', particle_effect_name='', slp=811, is_loaded=0, old_color_flag=0, layer=6, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=678, wwise_sound_id=1668689960, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12773, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12184, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12185, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Market4(Rubble)', file_name='b_medi_market_age4_rubble_x1', particle_effect_name='', slp=2270, is_loaded=0, old_color_flag=0, layer=6, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=678, wwise_sound_id=1668689960, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12774, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12184, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12185, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Blacksmith3(Rubble)', file_name='b_medi_blacksmith_age3_rubble_x1', particle_effect_name='', slp=6010, is_loaded=0, old_color_flag=0, layer=6, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=678, wwise_sound_id=1668689960, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12775, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12182, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12183, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Blacksmith2(Rubble)', file_name='b_medi_blacksmith_age2_rubble_x1', particle_effect_name='', slp=6210, is_loaded=0, old_color_flag=0, layer=6, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=678, wwise_sound_id=1668689960, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12776, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12182, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12183, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Mill3(Rubble)', file_name='b_medi_mill_age3_rubble_x1', particle_effect_name='', slp=744, is_loaded=0, old_color_flag=0, layer=6, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=678, wwise_sound_id=1668689960, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12777, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12180, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12181, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Mill2(Rubble)', file_name='b_medi_mill_age2_rubble_x1', particle_effect_name='', slp=744, is_loaded=0, old_color_flag=0, layer=6, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=678, wwise_sound_id=1668689960, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12778, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12180, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12181, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Monastery(Rubble)', file_name='b_medi_monastery_age3_rubble_x1', particle_effect_name='', slp=276, is_loaded=0, old_color_flag=0, layer=6, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=678, wwise_sound_id=1668689960, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12779, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12182, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12183, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_University3(Rubble)', file_name='b_medi_university_age3_rubble_x1', particle_effect_name='', slp=1358, is_loaded=0, old_color_flag=0, layer=6, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=678, wwise_sound_id=1668689960, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12780, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12180, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12181, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_University4(Rubble)', file_name='b_medi_university_age4_rubble_x1', particle_effect_name='', slp=1370, is_loaded=0, old_color_flag=0, layer=6, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=678, wwise_sound_id=1668689960, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12781, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12180, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12181, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Castle3(Rubble)', file_name='b_medi_castle_age3_rubble_x1', particle_effect_name='', slp=298, is_loaded=0, old_color_flag=0, layer=6, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=678, wwise_sound_id=1668689960, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12782, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12180, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12181, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Tower3(Rubble)', file_name='b_medi_tower_age3_rubble_x1', particle_effect_name='', slp=6029, is_loaded=0, old_color_flag=0, layer=6, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=678, wwise_sound_id=1668689960, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12783, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12178, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12179, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Tower2(Rubble)', file_name='b_medi_tower_age2_rubble_x1', particle_effect_name='', slp=6030, is_loaded=0, old_color_flag=0, layer=6, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=678, wwise_sound_id=1668689960, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12784, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12178, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12179, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Tower4(Rubble)', file_name='b_medi_tower_age4_rubble_x1', particle_effect_name='', slp=6032, is_loaded=0, old_color_flag=0, layer=6, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=678, wwise_sound_id=1668689960, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12785, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12178, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12179, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_BombardTower(Rubble)', file_name='b_medi_tower_bombard_rubble_x1', particle_effect_name='', slp=6034, is_loaded=0, old_color_flag=0, layer=6, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=678, wwise_sound_id=1668689960, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12786, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=-1, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12178, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12179, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0)], angle_sounds=[]))
    DATA.graphics.append(Graphic(name='SEE_Castle', file_name='b_byzantinecastle_x1', particle_effect_name='', slp=6021, is_loaded=0, old_color_flag=0, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=1, angle_count=1, speed_multiplier=0.0, frame_duration=0.0, replay_delay=0.0, sequence_type=0, id=12732, mirroring_mode=0, editor_flag=0, deltas=[], angle_sounds=[]))

    # Change the Byzantines to this new architecture style
    southeast_european_graphics = {
        87:[2,37], 10:[3,36], 14:[3,36], # Archery Range
        20:[5,35], 132:[5,35], 498:[6,34], # Barracks
        86:[11,33], 101:[10,32], 153:[11,33], # Stable
        49:[9,38], 150:[9,38], # Siege Workshop
        103:[7,43], 105:[7,43], 18:[8,42], 19:[8,42], # Blacksmith
        133:[0,-1], 806:[0,-1], 807:[0,-1], 47:[28,-1], 51:[28,-1], 808:[28,-1], # Dock
        209:[12,48], 210:[13,47], # University
        79:[16,50], 234:[17,51], 235:[18,52], 236: [4,53], # Towers
        117:[24,-1], 115:[25,-1], 99117:26, 99115:27, # Walls
        82:[54,49], # Castles
        30:[15,46], 31:[15,46], 32:[15,46], 104:[15,46], # Monasteries
        463:[20,31], 191:[21,30], 192:[21,30], 464:[21,30], 465:[21,30], # Houses
        129:[22,45], 130:[23,44], 131:[23,44], # Mills
        84:[14,40], 116:[19,39], 137:[19,41], # Markets
    }
    for i, unit in enumerate(DATA.civs[7].units):
        if i in southeast_european_graphics:
            #graphics = southeast_european_graphics[i]
            #unit.standing_graphic = set([graphics[0] + starting_graphic_index, -1])
            #unit.dying_graphic = graphics[1] + starting_graphic_index
            # DEBUG
            pass

    # Add new strings for unit names
    ORIGINAL_STRINGS = rf'{mod_folder}/resources/en/strings/key-value/key-value-strings-utf8.txt'
    with open(ORIGINAL_STRINGS, 'r+') as file:
        lines = file.readlines()
        for line in lines:
            if '400042' in line:
                # Add header
                lines.append('\n')
                lines.append('// Talofa strings\n')

                # Add the lines
                #"cretan archer", "scimitar warrior", "drengr", "qizilbash warrior", "axe cavalry", "sun warrior", "island sentinel"]
                #894 - Scimitar Warrior (Eastern Swordsman)
                #361 - Norse Warrior
                #1817,1829 - Qizilbash Warrior
                #2320 - Rhodian Slinger
                #2323 - Axe Cavalry (Elite Persian Cavalry/Scythian Axe Cavalry)
                #749 - (Cusi Yupanqui)
                #1157 - (Gajah Mada)
                #1067 - Skull Knight (Itzcoatl)
                #188 - Flamethrower
                #1574 - ??? (Sosso Guard)
                line_count = 0
                unit_bank = [
                    ['Amazon Warrior', 'Amazon Warriors', r'Fast-moving infantry unit. Strong vs. buildings and siege weapons. Weak vs. archers and cavalry. <i> Upgrades: attack, armor (Blacksmith); speed (Barracks); creation speed (Castle); more resistant to Monks (Monastery).<i>\n<hp> <attack> <armor> <piercearmor> <range>'],
                    ['Amazon Archer', 'Amazon Archers', r'Fast-moving archer. Strong vs. infantry. Weak vs. cavalry.<i> Upgrades: attack, range, armor (Blacksmith); accuracy (Archery Range); attack, accuracy (University); creation speed (Castle); more resistant to Monks (Monastery).<i>\n<hp> <attack> <armor> <piercearmor> <range>'],
                    ['Camel Raider', 'Camel Raiders', r'Anti-cavalry unit that generates gold when fighting other units. Strong vs. cavalry. Weak vs. Spearmen, Monks, and archers.<i> Upgrades: attack, armor (Blacksmith); speed, to Elite Camel Raider 325F, 360G (Castle); creation speed (Castle); more resistant to Monks (Monastery).<i>\n<hp> <attack> <armor> <piercearmor> <range>'],
                    ['Crusader', 'Crusaders', r'Powerful but slow-moving cavalry. Strong vs. melee and slow ranged units. Weak vs. Halberdiers. Cannot be converted by enemy Monks.<i> Upgrades: attack, armor (Blacksmith); speed, hit points (Stable).<i>\n<hp> <attack> <armor> <piercearmor> <range>'],
                    ['Tomahawk Warrior', 'Tomahawk Warriors', r'Quick infantry with ranged melee attack. Strong vs. cavalry and infantry. <i> Upgrades: attack, armor (Blacksmith); speed (Barracks); creation speed (Castle); more resistant to Monks (Monastery).<i>\n<hp> <attack> <armor> <piercearmor> <range>'],
                    ['Ninja', 'Ninjas', r'All-purpose infantry with a quick, powerful attack. Weak vs. Archers.<i> Upgrades: attack, armor (Blacksmith); speed (Barracks); creation speed (Castle); more resistant to Monks (Monastery).<i>\n<hp> <attack> <armor> <piercearmor> <range>'],
                    ['Scimitar Warrior', 'Scimitar Warriors', r'Infantry that resists attacks from Camel and Elephant units. Strong vs. camels and elephants. Weak vs. archers at long range.<i> Upgrades: attack, armor (Blacksmith); speed (Barracks); creation speed (Castle); more resistant to Monks (Monastery).<i>\n<hp> <attack> <armor> <piercearmor> <range>'],
                    ['Drengr', 'Drengrs', r'All-purpose infantry unit. Strong vs. buildings and infantry. Weak vs. archers at long range.<i> Upgrades: attack, armor (Blacksmith); speed (Barracks); creation speed (Castle); more resistant to Monks (Monastery).<i>\n<hp> <attack> <armor> <piercearmor> <range>'],
                    ['Qizilbash', 'Qizilbash', r'Powerful all-purpose cavalry. Strong vs. infantry, archers, and camelry.<i> Upgrades: attack, armor (Blacksmith); speed, hit points (Stable); creation speed, to Elite Qizilbash 850F, 600G (Castle); more resistant to Monks (Monastery).<i>\n<hp> <attack> <armor> <piercearmor> <range>'],
                    ['Axe Cavalry', 'Axe Cavalry', r'Ranged cavalry with a melee attack. Strong vs. infantry and arhcers.<i> Upgrades: attack, armor (Blacksmith); speed, hit points (Stable); creation speed, to Elite Axe Cavalry 850F, 600G (Castle); more resistant to Monks (Monastery).<i>\n<hp> <attack> <armor> <piercearmor> <range>'],
                    ['Sun Warrior', 'Sun Warriors', r'Light and quick skirmisher. Strong vs. archers and cavalry. Weak vs. skirmishers.<i> Upgrades: attack, armor (Blacksmith); speed (Barracks); creation speed (Castle); more resistant to Monks (Monastery).<i>\n<hp> <attack> <armor> <piercearmor> <range>'],
                    ['Island Sentinel', 'Island Sentinels', r'Light and quick infantry. Strong vs. infantry.<i> Upgrades: attack, armor (Blacksmith); speed (Barracks); creation speed (Castle); more resistant to Monks (Monastery).<i>\n<hp> <attack> <armor> <piercearmor> <range>']
                    ]
                for unit in unit_bank:
                    lines.append(rf'{90000 + line_count + 0} "{unit[0]}"' + '\n')
                    lines.append(rf'{90000 + line_count + 1} "Create {unit[0]}"' + '\n')
                    lines.append(rf'{90000 + line_count + 2} "Create <b>{unit[0]}<b> (<cost>)\n{unit[2]}"' + '\n')
                    lines.append(rf'{90000 + line_count + 3} "Upgrade to Elite {unit[0]}"' + '\n')
                    lines.append(rf'{90000 + line_count + 4} "Upgrade to Elite <b>{unit[0]}<b> (<cost>)\nUpgrades your {unit[1]} and lets you build Elite {unit[1]}, which are stronger."' + '\n')
                    lines.append(rf'{90000 + line_count + 5} "Elite {unit[0]}"' + '\n')
                    lines.append(rf'{90000 + line_count + 6} "Create Elite {unit[0]}"' + '\n')
                    lines.append(rf'{90000 + line_count + 7} "Create <b>Elite {unit[0]}<b> (<cost>)\n{unit[2]}"' + '\n')
                    line_count += 10
                break
            
        file.seek(0)         # Go back to start of file
        file.writelines(lines)
        file.truncate()      # Remove any extra content after the new end

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

    # Create new units
    unit_id = len(DATA.civs)
    for civ in DATA.civs:
        #civ.units.append(Unit(type=70, id=unit_id, language_dll_name=90000, language_dll_creation=90001, class_=6, standing_graphic=(8332, -1), dying_graphic=8331, undead_graphic=-1, undead_mode=0, hit_points=40, line_of_sight=6.0, garrison_capacity=0, collision_size_x=0.20000000298023224, collision_size_y=0.20000000298023224, collision_size_z=2.0, train_sound=600, damage_sound=-1, dead_unit_id=1324, blood_unit_id=-1, sort_number=5, can_be_built_on=0, icon_id=166, hide_in_editor=0, old_portrait_pict=-1, enabled=0, disabled=0, placement_side_terrain=(-1, -1), placement_terrain=(-1, -1), clearance_size=(0.20000000298023224, 0.20000000298023224), hill_mode=0, fog_visibility=0, terrain_restriction=7, fly_mode=0, resource_capacity=25, resource_decay=25.0, blast_defense_level=3, combat_level=4, interation_mode=4, minimap_mode=1, interface_kind=4, multiple_attribute_mode=1.0, minimap_color=0, language_dll_help=105303, language_dll_hotkey_text=155303, hot_key=16107, recyclable=0, enable_auto_gather=0, create_doppelganger_on_death=0, resource_gather_group=0, occlusion_mode=1, obstruction_type=5, obstruction_class=2, trait=0, civilization=0, nothing=0, selection_effect=0, editor_selection_colour=0, outline_size_x=0.20000000298023224, outline_size_y=0.20000000298023224, outline_size_z=2.0, scenario_triggers_1=-2, scenario_triggers_2=0, resource_storages=(ResourceStorage(type=4, amount=-1.0, flag=2), ResourceStorage(type=11, amount=1.0, flag=2), ResourceStorage(type=19, amount=1.0, flag=1)), damage_graphics=[], selection_sound=435, dying_sound=-1, wwise_train_sound_id=1091801433, wwise_damage_sound_id=0, wwise_selection_sound_id=349416654, wwise_dying_sound_id=0, old_attack_reaction=0, convert_terrain=0, name='Amazon Warrior', copy_id=2382, base_id=2382, speed=1.2999999523162842, dead_fish=DeadFish(walking_graphic=8334, running_graphic=-1, rotation_speed=0.0, old_size_class=0, tracking_unit=-1, tracking_unit_mode=0, tracking_unit_density=0.0, old_move_algorithm=0, turn_radius=0.0, turn_radius_speed=3.4028234663852886e+38, max_yaw_per_second_moving=3.4028234663852886e+38, stationary_yaw_revolution_time=0.0, max_yaw_per_second_stationary=3.4028234663852886e+38, min_collision_size_multiplier=0.800000011920929), bird=Bird(default_task_id=-1, search_radius=6.0, work_rate=1.0, drop_sites=[], task_swap_group=0, attack_sound=434, move_sound=434, wwise_attack_sound_id=-1015897558, wwise_move_sound_id=-378983899, run_pattern=0, tasks=[Task(task_type=1, id=0, is_default=0, action_type=7, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=1, combat_level_flag=1, gather_type=1, work_flag_2=0, target_diplomacy=5, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=1, is_default=0, action_type=3, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=2, is_default=0, action_type=109, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=3, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=4, is_default=0, action_type=3, class_id=3, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=5, is_default=0, action_type=3, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=6, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=7, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=5.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=8, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=9, is_default=0, action_type=154, class_id=19, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=10, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=11, is_default=0, action_type=154, class_id=-1, unit_id=1811, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0)]), type_50=Type50(base_armor=10000, attacks=[AttackOrArmor(class_=29, amount=2), AttackOrArmor(class_=21, amount=6), AttackOrArmor(class_=4, amount=9), AttackOrArmor(class_=8, amount=0), AttackOrArmor(class_=30, amount=0), AttackOrArmor(class_=20, amount=6)], armours=[AttackOrArmor(class_=1, amount=0), AttackOrArmor(class_=4, amount=0), AttackOrArmor(class_=3, amount=0), AttackOrArmor(class_=31, amount=0)], defense_terrain_bonus=-1, bonus_damage_resistance=0.0, max_range=0.0, blast_width=0.0, reload_time=2.0, projectile_unit_id=-1, accuracy_percent=100, break_off_combat=0, frame_delay=0, graphic_displacement=(0.0, 0.0, 0.0), blast_attack_level=2, min_range=0.0, accuracy_dispersion=0.0, attack_graphic=8330, displayed_melee_armour=0, displayed_attack=9, displayed_range=0.0, displayed_reload_time=2.0, blast_damage=-5.0), projectile=None, creatable=Creatable(resource_costs=(ResourceCost(type=0, amount=40, flag=1), ResourceCost(type=1, amount=60, flag=1), ResourceCost(type=4, amount=1, flag=0)), train_time=16, train_location_id=82, button_id=1, rear_attack_modifier=0.0, flank_attack_modifier=1.0, creatable_type=2, hero_mode=0, garrison_graphic=-1, spawning_graphic=12262, upgrade_graphic=12263, hero_glow_graphic=12218, max_charge=0.0, recharge_rate=0.0, charge_event=0, charge_type=0, min_conversion_time_mod=0.0, max_conversion_time_mod=0.0, conversion_chance_mod=0.0, total_projectiles=1.0, max_total_projectiles=1, projectile_spawning_area=(1.0, 1.0, 1.0), secondary_projectile_unit=-1, special_graphic=-1, special_ability=0, displayed_pierce_armor=0), building=None)),
        #civ.units.append(Unit(type=70, id=unit_id + 1, language_dll_name=90005, language_dll_creation=90006, class_=6, standing_graphic=(8332, -1), dying_graphic=8331, undead_graphic=-1, undead_mode=0, hit_points=50, line_of_sight=6.0, garrison_capacity=0, collision_size_x=0.20000000298023224, collision_size_y=0.20000000298023224, collision_size_z=2.0, train_sound=600, damage_sound=-1, dead_unit_id=1324, blood_unit_id=-1, sort_number=5, can_be_built_on=0, icon_id=166, hide_in_editor=0, old_portrait_pict=-1, enabled=0, disabled=0, placement_side_terrain=(-1, -1), placement_terrain=(-1, -1), clearance_size=(0.20000000298023224, 0.20000000298023224), hill_mode=0, fog_visibility=0, terrain_restriction=7, fly_mode=0, resource_capacity=25, resource_decay=25.0, blast_defense_level=3, combat_level=4, interation_mode=4, minimap_mode=1, interface_kind=4, multiple_attribute_mode=1.0, minimap_color=0, language_dll_help=105303, language_dll_hotkey_text=155303, hot_key=16107, recyclable=0, enable_auto_gather=0, create_doppelganger_on_death=0, resource_gather_group=0, occlusion_mode=1, obstruction_type=5, obstruction_class=2, trait=0, civilization=0, nothing=0, selection_effect=0, editor_selection_colour=0, outline_size_x=0.20000000298023224, outline_size_y=0.20000000298023224, outline_size_z=2.0, scenario_triggers_1=-2, scenario_triggers_2=0, resource_storages=(ResourceStorage(type=4, amount=-1.0, flag=2), ResourceStorage(type=11, amount=1.0, flag=2), ResourceStorage(type=19, amount=1.0, flag=1)), damage_graphics=[], selection_sound=435, dying_sound=-1, wwise_train_sound_id=1091801433, wwise_damage_sound_id=0, wwise_selection_sound_id=349416654, wwise_dying_sound_id=0, old_attack_reaction=0, convert_terrain=0, name='Elite Amazon Warrior', copy_id=2383, base_id=2383, speed=1.350000023841858, dead_fish=DeadFish(walking_graphic=8334, running_graphic=-1, rotation_speed=0.0, old_size_class=0, tracking_unit=-1, tracking_unit_mode=0, tracking_unit_density=0.0, old_move_algorithm=0, turn_radius=0.0, turn_radius_speed=3.4028234663852886e+38, max_yaw_per_second_moving=3.4028234663852886e+38, stationary_yaw_revolution_time=0.0, max_yaw_per_second_stationary=3.4028234663852886e+38, min_collision_size_multiplier=0.800000011920929), bird=Bird(default_task_id=-1, search_radius=6.0, work_rate=1.0, drop_sites=[], task_swap_group=0, attack_sound=434, move_sound=434, wwise_attack_sound_id=-1015897558, wwise_move_sound_id=-378983899, run_pattern=0, tasks=[Task(task_type=1, id=0, is_default=0, action_type=7, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=1, combat_level_flag=1, gather_type=1, work_flag_2=0, target_diplomacy=5, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=1, is_default=0, action_type=3, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=2, is_default=0, action_type=109, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=3, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=4, is_default=0, action_type=3, class_id=3, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=5, is_default=0, action_type=3, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=6, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=7, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=5.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=8, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=9, is_default=0, action_type=154, class_id=19, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=10, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=11, is_default=0, action_type=154, class_id=-1, unit_id=1811, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0)]), type_50=Type50(base_armor=10000, attacks=[AttackOrArmor(class_=29, amount=2), AttackOrArmor(class_=21, amount=7), AttackOrArmor(class_=4, amount=10), AttackOrArmor(class_=8, amount=0), AttackOrArmor(class_=30, amount=0), AttackOrArmor(class_=20, amount=7)], armours=[AttackOrArmor(class_=1, amount=0), AttackOrArmor(class_=4, amount=0), AttackOrArmor(class_=3, amount=0), AttackOrArmor(class_=31, amount=0)], defense_terrain_bonus=-1, bonus_damage_resistance=0.0, max_range=0.0, blast_width=0.0, reload_time=2.0, projectile_unit_id=-1, accuracy_percent=100, break_off_combat=0, frame_delay=0, graphic_displacement=(0.0, 0.0, 0.0), blast_attack_level=2, min_range=0.0, accuracy_dispersion=0.0, attack_graphic=8330, displayed_melee_armour=0, displayed_attack=10, displayed_range=0.0, displayed_reload_time=2.0, blast_damage=-5.0), projectile=None, creatable=Creatable(resource_costs=(ResourceCost(type=0, amount=40, flag=1), ResourceCost(type=1, amount=60, flag=1), ResourceCost(type=4, amount=1, flag=0)), train_time=16, train_location_id=82, button_id=1, rear_attack_modifier=0.0, flank_attack_modifier=1.0, creatable_type=2, hero_mode=0, garrison_graphic=-1, spawning_graphic=12262, upgrade_graphic=12263, hero_glow_graphic=12218, max_charge=0.0, recharge_rate=0.0, charge_event=0, charge_type=0, min_conversion_time_mod=0.0, max_conversion_time_mod=0.0, conversion_chance_mod=0.0, total_projectiles=1.0, max_total_projectiles=1, projectile_spawning_area=(1.0, 1.0, 1.0), secondary_projectile_unit=-1, special_graphic=-1, special_ability=0, displayed_pierce_armor=0), building=None)),
        #civ.units.append(Unit(type=70, id=unit_id + 2, language_dll_name=90010, language_dll_creation=90011, class_=0, standing_graphic=(8327, -1), dying_graphic=8326, undead_graphic=-1, undead_mode=0, hit_points=35, line_of_sight=6.0, garrison_capacity=0, collision_size_x=0.20000000298023224, collision_size_y=0.20000000298023224, collision_size_z=2.0, train_sound=601, damage_sound=-1, dead_unit_id=1325, blood_unit_id=-1, sort_number=5, can_be_built_on=0, icon_id=165, hide_in_editor=0, old_portrait_pict=-1, enabled=0, disabled=0, placement_side_terrain=(-1, -1), placement_terrain=(-1, -1), clearance_size=(0.20000000298023224, 0.20000000298023224), hill_mode=0, fog_visibility=0, terrain_restriction=7, fly_mode=0, resource_capacity=25, resource_decay=25.0, blast_defense_level=3, combat_level=4, interation_mode=4, minimap_mode=1, interface_kind=4, multiple_attribute_mode=1.0, minimap_color=0, language_dll_help=105304, language_dll_hotkey_text=155304, hot_key=16107, recyclable=0, enable_auto_gather=0, create_doppelganger_on_death=0, resource_gather_group=0, occlusion_mode=1, obstruction_type=5, obstruction_class=2, trait=0, civilization=0, nothing=0, selection_effect=0, editor_selection_colour=0, outline_size_x=0.20000000298023224, outline_size_y=0.20000000298023224, outline_size_z=2.0, scenario_triggers_1=-2, scenario_triggers_2=0, resource_storages=(ResourceStorage(type=4, amount=-1.0, flag=2), ResourceStorage(type=11, amount=1.0, flag=2), ResourceStorage(type=19, amount=1.0, flag=1)), damage_graphics=[], selection_sound=435, dying_sound=-1, wwise_train_sound_id=-1823148159, wwise_damage_sound_id=0, wwise_selection_sound_id=349416654, wwise_dying_sound_id=0, old_attack_reaction=0, convert_terrain=0, name='Amazon Archer', copy_id=2384, base_id=2384, speed=1.399999976158142, dead_fish=DeadFish(walking_graphic=8329, running_graphic=-1, rotation_speed=0.0, old_size_class=0, tracking_unit=-1, tracking_unit_mode=0, tracking_unit_density=0.0, old_move_algorithm=0, turn_radius=0.0, turn_radius_speed=3.4028234663852886e+38, max_yaw_per_second_moving=3.4028234663852886e+38, stationary_yaw_revolution_time=0.0, max_yaw_per_second_stationary=3.4028234663852886e+38, min_collision_size_multiplier=1.0), bird=Bird(default_task_id=-1, search_radius=6.0, work_rate=1.0, drop_sites=[], task_swap_group=0, attack_sound=434, move_sound=434, wwise_attack_sound_id=-1015897558, wwise_move_sound_id=-378983899, run_pattern=0, tasks=[Task(task_type=1, id=0, is_default=0, action_type=7, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=1, combat_level_flag=1, gather_type=1, work_flag_2=0, target_diplomacy=5, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=1, is_default=0, action_type=3, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=2, is_default=0, action_type=109, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=3, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=4, is_default=0, action_type=3, class_id=3, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=5, is_default=0, action_type=3, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0)]), type_50=Type50(base_armor=10000, attacks=[AttackOrArmor(class_=27, amount=4), AttackOrArmor(class_=21, amount=0), AttackOrArmor(class_=1, amount=6), AttackOrArmor(class_=3, amount=7), AttackOrArmor(class_=17, amount=0), AttackOrArmor(class_=32, amount=1)], armours=[AttackOrArmor(class_=4, amount=0), AttackOrArmor(class_=15, amount=0), AttackOrArmor(class_=3, amount=1), AttackOrArmor(class_=31, amount=0)], defense_terrain_bonus=-1, bonus_damage_resistance=0.0, max_range=4.0, blast_width=0.0, reload_time=1.899999976158142, projectile_unit_id=511, accuracy_percent=90, break_off_combat=0, frame_delay=10, graphic_displacement=(0.0, 0.5, 1.5), blast_attack_level=3, min_range=0.0, accuracy_dispersion=0.33000001311302185, attack_graphic=8325, displayed_melee_armour=0, displayed_attack=7, displayed_range=4.0, displayed_reload_time=1.899999976158142, blast_damage=1.0), projectile=None, creatable=Creatable(resource_costs=(ResourceCost(type=0, amount=50, flag=1), ResourceCost(type=1, amount=50, flag=1), ResourceCost(type=4, amount=1, flag=0)), train_time=16, train_location_id=82, button_id=1, rear_attack_modifier=0.0, flank_attack_modifier=1.0, creatable_type=3, hero_mode=0, garrison_graphic=-1, spawning_graphic=12262, upgrade_graphic=12263, hero_glow_graphic=12218, max_charge=0.0, recharge_rate=0.0, charge_event=0, charge_type=0, min_conversion_time_mod=0.0, max_conversion_time_mod=0.0, conversion_chance_mod=0.0, total_projectiles=1.0, max_total_projectiles=1, projectile_spawning_area=(1.0, 1.0, 1.0), secondary_projectile_unit=-1, special_graphic=-1, special_ability=0, displayed_pierce_armor=1), building=None)),
        #civ.units.append(Unit(type=70, id=unit_id + 3, language_dll_name=90015, language_dll_creation=90016, class_=0, standing_graphic=(8327, -1), dying_graphic=8326, undead_graphic=-1, undead_mode=0, hit_points=45, line_of_sight=6.0, garrison_capacity=0, collision_size_x=0.20000000298023224, collision_size_y=0.20000000298023224, collision_size_z=2.0, train_sound=601, damage_sound=-1, dead_unit_id=1325, blood_unit_id=-1, sort_number=5, can_be_built_on=0, icon_id=165, hide_in_editor=0, old_portrait_pict=-1, enabled=0, disabled=0, placement_side_terrain=(-1, -1), placement_terrain=(-1, -1), clearance_size=(0.20000000298023224, 0.20000000298023224), hill_mode=0, fog_visibility=0, terrain_restriction=7, fly_mode=0, resource_capacity=25, resource_decay=25.0, blast_defense_level=3, combat_level=4, interation_mode=4, minimap_mode=1, interface_kind=4, multiple_attribute_mode=1.0, minimap_color=0, language_dll_help=105304, language_dll_hotkey_text=155304, hot_key=16107, recyclable=0, enable_auto_gather=0, create_doppelganger_on_death=0, resource_gather_group=0, occlusion_mode=1, obstruction_type=5, obstruction_class=2, trait=0, civilization=0, nothing=0, selection_effect=0, editor_selection_colour=0, outline_size_x=0.20000000298023224, outline_size_y=0.20000000298023224, outline_size_z=2.0, scenario_triggers_1=-2, scenario_triggers_2=0, resource_storages=(ResourceStorage(type=4, amount=-1.0, flag=2), ResourceStorage(type=11, amount=1.0, flag=2), ResourceStorage(type=19, amount=1.0, flag=1)), damage_graphics=[], selection_sound=435, dying_sound=-1, wwise_train_sound_id=-1823148159, wwise_damage_sound_id=0, wwise_selection_sound_id=349416654, wwise_dying_sound_id=0, old_attack_reaction=0, convert_terrain=0, name='Elite Amazon Archer', copy_id=2385, base_id=2385, speed=1.4500000476837158, dead_fish=DeadFish(walking_graphic=8329, running_graphic=-1, rotation_speed=0.0, old_size_class=0, tracking_unit=-1, tracking_unit_mode=0, tracking_unit_density=0.0, old_move_algorithm=0, turn_radius=0.0, turn_radius_speed=3.4028234663852886e+38, max_yaw_per_second_moving=3.4028234663852886e+38, stationary_yaw_revolution_time=0.0, max_yaw_per_second_stationary=3.4028234663852886e+38, min_collision_size_multiplier=1.0), bird=Bird(default_task_id=-1, search_radius=6.0, work_rate=1.0, drop_sites=[], task_swap_group=0, attack_sound=434, move_sound=434, wwise_attack_sound_id=-1015897558, wwise_move_sound_id=-378983899, run_pattern=0, tasks=[Task(task_type=1, id=0, is_default=0, action_type=7, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=1, combat_level_flag=1, gather_type=1, work_flag_2=0, target_diplomacy=5, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=1, is_default=0, action_type=3, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=2, is_default=0, action_type=109, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=3, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=4, is_default=0, action_type=3, class_id=3, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=5, is_default=0, action_type=3, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0)]), type_50=Type50(base_armor=10000, attacks=[AttackOrArmor(class_=27, amount=5), AttackOrArmor(class_=21, amount=0), AttackOrArmor(class_=1, amount=7), AttackOrArmor(class_=3, amount=8), AttackOrArmor(class_=17, amount=0), AttackOrArmor(class_=32, amount=1)], armours=[AttackOrArmor(class_=4, amount=0), AttackOrArmor(class_=15, amount=0), AttackOrArmor(class_=3, amount=1), AttackOrArmor(class_=31, amount=0)], defense_terrain_bonus=-1, bonus_damage_resistance=0.0, max_range=4.0, blast_width=0.0, reload_time=1.899999976158142, projectile_unit_id=511, accuracy_percent=90, break_off_combat=0, frame_delay=10, graphic_displacement=(0.0, 0.5, 1.5), blast_attack_level=3, min_range=0.0, accuracy_dispersion=0.33000001311302185, attack_graphic=8325, displayed_melee_armour=0, displayed_attack=8, displayed_range=4.0, displayed_reload_time=1.899999976158142, blast_damage=1.0), projectile=None, creatable=Creatable(resource_costs=(ResourceCost(type=0, amount=50, flag=1), ResourceCost(type=1, amount=50, flag=1), ResourceCost(type=4, amount=1, flag=0)), train_time=16, train_location_id=82, button_id=1, rear_attack_modifier=0.0, flank_attack_modifier=1.0, creatable_type=3, hero_mode=0, garrison_graphic=-1, spawning_graphic=12262, upgrade_graphic=12263, hero_glow_graphic=12218, max_charge=0.0, recharge_rate=0.0, charge_event=0, charge_type=0, min_conversion_time_mod=0.0, max_conversion_time_mod=0.0, conversion_chance_mod=0.0, total_projectiles=1.0, max_total_projectiles=1, projectile_spawning_area=(1.0, 1.0, 1.0), secondary_projectile_unit=-1, special_graphic=-1, special_ability=0, displayed_pierce_armor=1), building=None)),
        #civ.units.append(Unit(type=70, id=unit_id + 4, language_dll_name=90020, language_dll_creation=90021, class_=12, standing_graphic=(15662, -1), dying_graphic=15661, undead_graphic=-1, undead_mode=0, hit_points=90, line_of_sight=4.0, garrison_capacity=1, collision_size_x=0.25, collision_size_y=0.25, collision_size_z=2.0, train_sound=430, damage_sound=-1, dead_unit_id=2368, blood_unit_id=-1, sort_number=5, can_be_built_on=0, icon_id=681, hide_in_editor=0, old_portrait_pict=-1, enabled=0, disabled=0, placement_side_terrain=(-1, -1), placement_terrain=(-1, -1), clearance_size=(0.25, 0.25), hill_mode=0, fog_visibility=0, terrain_restriction=28, fly_mode=0, resource_capacity=25, resource_decay=25.0, blast_defense_level=3, combat_level=4, interation_mode=4, minimap_mode=1, interface_kind=4, multiple_attribute_mode=1.0, minimap_color=0, language_dll_help=90022, language_dll_hotkey_text=139999, hot_key=16107, recyclable=0, enable_auto_gather=0, create_doppelganger_on_death=0, resource_gather_group=0, occlusion_mode=1, obstruction_type=5, obstruction_class=2, trait=0, civilization=0, nothing=0, selection_effect=0, editor_selection_colour=0, outline_size_x=0.4000000059604645, outline_size_y=0.4000000059604645, outline_size_z=2.0, scenario_triggers_1=-2, scenario_triggers_2=0, resource_storages=(ResourceStorage(type=4, amount=-1.0, flag=2), ResourceStorage(type=11, amount=1.0, flag=2), ResourceStorage(type=19, amount=1.0, flag=1)), damage_graphics=[], selection_sound=430, dying_sound=-1, wwise_train_sound_id=215634376, wwise_damage_sound_id=0, wwise_selection_sound_id=-660807332, wwise_dying_sound_id=0, old_attack_reaction=0, convert_terrain=0, name='Camel Raider', copy_id=2386, base_id=2386, speed=1.5, dead_fish=DeadFish(walking_graphic=15664, running_graphic=-1, rotation_speed=0.0, old_size_class=0, tracking_unit=-1, tracking_unit_mode=0, tracking_unit_density=0.0, old_move_algorithm=0, turn_radius=0.0, turn_radius_speed=3.4028234663852886e+38, max_yaw_per_second_moving=3.4028234663852886e+38, stationary_yaw_revolution_time=0.0, max_yaw_per_second_stationary=3.4028234663852886e+38, min_collision_size_multiplier=0.5), bird=Bird(default_task_id=-1, search_radius=4.0, work_rate=1.0, drop_sites=[], task_swap_group=0, attack_sound=326, move_sound=326, wwise_attack_sound_id=1562378686, wwise_move_sound_id=1562378686, run_pattern=0, tasks=[Task(task_type=1, id=0, is_default=0, action_type=7, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=1, combat_level_flag=1, gather_type=1, work_flag_2=0, target_diplomacy=5, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=1, is_default=0, action_type=3, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=2, is_default=0, action_type=109, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=3, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=4, is_default=0, action_type=3, class_id=3, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=5, is_default=0, action_type=154, class_id=0, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=6, is_default=0, action_type=154, class_id=6, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=7, is_default=0, action_type=154, class_id=12, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=8, is_default=0, action_type=154, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=9, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=10, is_default=0, action_type=154, class_id=22, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=11, is_default=0, action_type=154, class_id=23, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=12, is_default=0, action_type=154, class_id=35, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=13, is_default=0, action_type=154, class_id=36, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=14, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=15, is_default=0, action_type=154, class_id=44, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=16, is_default=0, action_type=154, class_id=47, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=17, is_default=0, action_type=154, class_id=54, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=18, is_default=0, action_type=154, class_id=55, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=19, is_default=0, action_type=154, class_id=0, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=20, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=21, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=22, is_default=0, action_type=154, class_id=6, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=23, is_default=0, action_type=154, class_id=12, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=24, is_default=0, action_type=154, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=25, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=26, is_default=0, action_type=154, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=27, is_default=0, action_type=154, class_id=21, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=28, is_default=1, action_type=154, class_id=22, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=29, is_default=0, action_type=154, class_id=23, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=30, is_default=0, action_type=154, class_id=35, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=31, is_default=0, action_type=154, class_id=36, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=32, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=33, is_default=0, action_type=154, class_id=44, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=34, is_default=0, action_type=154, class_id=47, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=35, is_default=0, action_type=154, class_id=54, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=36, is_default=0, action_type=154, class_id=55, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0)]), type_50=Type50(base_armor=10000, attacks=[AttackOrArmor(class_=4, amount=10), AttackOrArmor(class_=8, amount=17), AttackOrArmor(class_=16, amount=9), AttackOrArmor(class_=11, amount=0), AttackOrArmor(class_=30, amount=9), AttackOrArmor(class_=21, amount=0), AttackOrArmor(class_=34, amount=9), AttackOrArmor(class_=38, amount=0), AttackOrArmor(class_=39, amount=-3), AttackOrArmor(class_=35, amount=7)], armours=[AttackOrArmor(class_=4, amount=0), AttackOrArmor(class_=3, amount=1), AttackOrArmor(class_=30, amount=0), AttackOrArmor(class_=31, amount=0), AttackOrArmor(class_=39, amount=-3)], defense_terrain_bonus=-1, bonus_damage_resistance=0.0, max_range=0.0, blast_width=0.0, reload_time=2.0, projectile_unit_id=-1, accuracy_percent=100, break_off_combat=0, frame_delay=0, graphic_displacement=(0.0, 0.0, 0.0), blast_attack_level=0, min_range=0.0, accuracy_dispersion=0.0, attack_graphic=15660, displayed_melee_armour=0, displayed_attack=10, displayed_range=0.0, displayed_reload_time=2.0, blast_damage=1.0), projectile=None, creatable=Creatable(resource_costs=(ResourceCost(type=0, amount=55, flag=1), ResourceCost(type=3, amount=60, flag=1), ResourceCost(type=4, amount=1, flag=0)), train_time=30, train_location_id=82, button_id=1, rear_attack_modifier=0.0, flank_attack_modifier=1.25, creatable_type=1, hero_mode=0, garrison_graphic=-1, spawning_graphic=12262, upgrade_graphic=12263, hero_glow_graphic=12219, max_charge=0.0, recharge_rate=0.0, charge_event=0, charge_type=0, min_conversion_time_mod=0.0, max_conversion_time_mod=0.0, conversion_chance_mod=0.0, total_projectiles=1.0, max_total_projectiles=1, projectile_spawning_area=(1.0, 1.0, 1.0), secondary_projectile_unit=-1, special_graphic=15665, special_ability=0, displayed_pierce_armor=1), building=None)),
        #civ.units.append(Unit(type=70, id=unit_id + 5, language_dll_name=90025, language_dll_creation=90026, class_=12, standing_graphic=(15662, -1), dying_graphic=15661, undead_graphic=-1, undead_mode=0, hit_points=100, line_of_sight=4.0, garrison_capacity=1, collision_size_x=0.25, collision_size_y=0.25, collision_size_z=2.0, train_sound=430, damage_sound=-1, dead_unit_id=2368, blood_unit_id=-1, sort_number=5, can_be_built_on=0, icon_id=681, hide_in_editor=0, old_portrait_pict=-1, enabled=0, disabled=0, placement_side_terrain=(-1, -1), placement_terrain=(-1, -1), clearance_size=(0.25, 0.25), hill_mode=0, fog_visibility=0, terrain_restriction=28, fly_mode=0, resource_capacity=25, resource_decay=25.0, blast_defense_level=3, combat_level=4, interation_mode=4, minimap_mode=1, interface_kind=4, multiple_attribute_mode=1.0, minimap_color=0, language_dll_help=90027, language_dll_hotkey_text=139999, hot_key=16107, recyclable=0, enable_auto_gather=0, create_doppelganger_on_death=0, resource_gather_group=0, occlusion_mode=1, obstruction_type=5, obstruction_class=2, trait=0, civilization=0, nothing=0, selection_effect=0, editor_selection_colour=0, outline_size_x=0.4000000059604645, outline_size_y=0.4000000059604645, outline_size_z=2.0, scenario_triggers_1=-2, scenario_triggers_2=0, resource_storages=(ResourceStorage(type=4, amount=-1.0, flag=2), ResourceStorage(type=11, amount=1.0, flag=2), ResourceStorage(type=19, amount=1.0, flag=1)), damage_graphics=[], selection_sound=430, dying_sound=-1, wwise_train_sound_id=215634376, wwise_damage_sound_id=0, wwise_selection_sound_id=-660807332, wwise_dying_sound_id=0, old_attack_reaction=0, convert_terrain=0, name='Elite Camel Raider', copy_id=2387, base_id=2387, speed=1.5, dead_fish=DeadFish(walking_graphic=15664, running_graphic=-1, rotation_speed=0.0, old_size_class=0, tracking_unit=-1, tracking_unit_mode=0, tracking_unit_density=0.0, old_move_algorithm=0, turn_radius=0.0, turn_radius_speed=3.4028234663852886e+38, max_yaw_per_second_moving=3.4028234663852886e+38, stationary_yaw_revolution_time=0.0, max_yaw_per_second_stationary=3.4028234663852886e+38, min_collision_size_multiplier=0.5), bird=Bird(default_task_id=-1, search_radius=4.0, work_rate=1.0, drop_sites=[], task_swap_group=0, attack_sound=326, move_sound=326, wwise_attack_sound_id=1562378686, wwise_move_sound_id=1562378686, run_pattern=0, tasks=[Task(task_type=1, id=0, is_default=0, action_type=7, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=1, combat_level_flag=1, gather_type=1, work_flag_2=0, target_diplomacy=5, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=1, is_default=0, action_type=3, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=2, is_default=0, action_type=109, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=3, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=4, is_default=0, action_type=3, class_id=3, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=5, is_default=0, action_type=154, class_id=0, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=6, is_default=0, action_type=154, class_id=6, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=7, is_default=0, action_type=154, class_id=12, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=8, is_default=0, action_type=154, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=9, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=10, is_default=0, action_type=154, class_id=22, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=11, is_default=0, action_type=154, class_id=23, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=12, is_default=0, action_type=154, class_id=35, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=13, is_default=0, action_type=154, class_id=36, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=14, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=15, is_default=0, action_type=154, class_id=44, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=16, is_default=0, action_type=154, class_id=47, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=17, is_default=0, action_type=154, class_id=54, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=18, is_default=0, action_type=154, class_id=55, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=550, resource_out=3, unused_resource=-1, work_value_1=2.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=19, is_default=0, action_type=154, class_id=0, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=20, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=21, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=22, is_default=0, action_type=154, class_id=6, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=23, is_default=0, action_type=154, class_id=12, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=24, is_default=0, action_type=154, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=25, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=26, is_default=0, action_type=154, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=27, is_default=0, action_type=154, class_id=21, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=28, is_default=1, action_type=154, class_id=22, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=29, is_default=0, action_type=154, class_id=23, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=30, is_default=0, action_type=154, class_id=35, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=31, is_default=0, action_type=154, class_id=36, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=32, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=33, is_default=0, action_type=154, class_id=44, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=34, is_default=0, action_type=154, class_id=47, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=35, is_default=0, action_type=154, class_id=54, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=36, is_default=0, action_type=154, class_id=55, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0)]), type_50=Type50(base_armor=10000, attacks=[AttackOrArmor(class_=4, amount=11), AttackOrArmor(class_=8, amount=19), AttackOrArmor(class_=16, amount=9), AttackOrArmor(class_=11, amount=0), AttackOrArmor(class_=30, amount=10), AttackOrArmor(class_=21, amount=0), AttackOrArmor(class_=34, amount=9), AttackOrArmor(class_=38, amount=0), AttackOrArmor(class_=39, amount=-3), AttackOrArmor(class_=35, amount=8)], armours=[AttackOrArmor(class_=4, amount=0), AttackOrArmor(class_=3, amount=1), AttackOrArmor(class_=30, amount=0), AttackOrArmor(class_=31, amount=0), AttackOrArmor(class_=39, amount=-3)], defense_terrain_bonus=-1, bonus_damage_resistance=0.0, max_range=0.0, blast_width=0.0, reload_time=2.0, projectile_unit_id=-1, accuracy_percent=100, break_off_combat=0, frame_delay=0, graphic_displacement=(0.0, 0.0, 0.0), blast_attack_level=0, min_range=0.0, accuracy_dispersion=0.0, attack_graphic=15660, displayed_melee_armour=0, displayed_attack=11, displayed_range=0.0, displayed_reload_time=2.0, blast_damage=1.0), projectile=None, creatable=Creatable(resource_costs=(ResourceCost(type=0, amount=55, flag=1), ResourceCost(type=3, amount=60, flag=1), ResourceCost(type=4, amount=1, flag=0)), train_time=30, train_location_id=82, button_id=1, rear_attack_modifier=0.0, flank_attack_modifier=1.25, creatable_type=1, hero_mode=0, garrison_graphic=-1, spawning_graphic=12262, upgrade_graphic=12263, hero_glow_graphic=12219, max_charge=0.0, recharge_rate=0.0, charge_event=0, charge_type=0, min_conversion_time_mod=0.0, max_conversion_time_mod=0.0, conversion_chance_mod=0.0, total_projectiles=1.0, max_total_projectiles=1, projectile_spawning_area=(1.0, 1.0, 1.0), secondary_projectile_unit=-1, special_graphic=15665, special_ability=0, displayed_pierce_armor=1), building=None)),
        #civ.units.append(Unit(type=70, id=unit_id + 6, language_dll_name=90030, language_dll_creation=90031, class_=12, standing_graphic=(12381, 12380), dying_graphic=12379, undead_graphic=-1, undead_mode=0, hit_points=100, line_of_sight=5.0, garrison_capacity=0, collision_size_x=0.25, collision_size_y=0.25, collision_size_z=2.0, train_sound=604, damage_sound=-1, dead_unit_id=1724, blood_unit_id=-1, sort_number=5, can_be_built_on=0, icon_id=377, hide_in_editor=0, old_portrait_pict=-1, enabled=0, disabled=0, placement_side_terrain=(-1, -1), placement_terrain=(-1, -1), clearance_size=(0.25, 0.25), hill_mode=0, fog_visibility=0, terrain_restriction=28, fly_mode=0, resource_capacity=25, resource_decay=25.0, blast_defense_level=3, combat_level=4, interation_mode=4, minimap_mode=1, interface_kind=4, multiple_attribute_mode=1.0, minimap_color=0, language_dll_help=90032, language_dll_hotkey_text=155610, hot_key=16730, recyclable=0, enable_auto_gather=0, create_doppelganger_on_death=0, resource_gather_group=0, occlusion_mode=1, obstruction_type=5, obstruction_class=2, trait=0, civilization=0, nothing=0, selection_effect=0, editor_selection_colour=0, outline_size_x=0.4000000059604645, outline_size_y=0.4000000059604645, outline_size_z=2.0, scenario_triggers_1=-2, scenario_triggers_2=0, resource_storages=(ResourceStorage(type=4, amount=-1.0, flag=2), ResourceStorage(type=11, amount=1.0, flag=2), ResourceStorage(type=19, amount=1.0, flag=1)), damage_graphics=[], selection_sound=325, dying_sound=-1, wwise_train_sound_id=-2110013473, wwise_damage_sound_id=0, wwise_selection_sound_id=442791689, wwise_dying_sound_id=0, old_attack_reaction=0, convert_terrain=0, name='Crusader', copy_id=2388, base_id=2388, speed=1.100000023841858, dead_fish=DeadFish(walking_graphic=12383, running_graphic=-1, rotation_speed=0.0, old_size_class=0, tracking_unit=-1, tracking_unit_mode=0, tracking_unit_density=0.0, old_move_algorithm=0, turn_radius=0.0, turn_radius_speed=3.4028234663852886e+38, max_yaw_per_second_moving=3.4028234663852886e+38, stationary_yaw_revolution_time=0.0, max_yaw_per_second_stationary=3.4028234663852886e+38, min_collision_size_multiplier=0.5), bird=Bird(default_task_id=-1, search_radius=5.0, work_rate=1.0, drop_sites=[], task_swap_group=0, attack_sound=326, move_sound=326, wwise_attack_sound_id=-1155057397, wwise_move_sound_id=-1155057397, run_pattern=0, tasks=[Task(task_type=1, id=0, is_default=0, action_type=7, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=1, combat_level_flag=1, gather_type=1, work_flag_2=0, target_diplomacy=5, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=1, is_default=0, action_type=3, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=2, is_default=0, action_type=109, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=3, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=4, is_default=0, action_type=3, class_id=3, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=5, is_default=0, action_type=154, class_id=0, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=6, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=7, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=8, is_default=0, action_type=154, class_id=6, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=9, is_default=0, action_type=154, class_id=12, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=10, is_default=0, action_type=154, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=11, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=12, is_default=0, action_type=154, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=13, is_default=0, action_type=154, class_id=21, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=14, is_default=1, action_type=154, class_id=22, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=15, is_default=0, action_type=154, class_id=23, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=16, is_default=0, action_type=154, class_id=35, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=17, is_default=0, action_type=154, class_id=36, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=18, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=19, is_default=0, action_type=154, class_id=44, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=20, is_default=0, action_type=154, class_id=47, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=21, is_default=0, action_type=154, class_id=54, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=22, is_default=0, action_type=154, class_id=55, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0)]), type_50=Type50(base_armor=10000, attacks=[AttackOrArmor(class_=4, amount=15), AttackOrArmor(class_=15, amount=0), AttackOrArmor(class_=11, amount=0), AttackOrArmor(class_=21, amount=0), AttackOrArmor(class_=38, amount=0), AttackOrArmor(class_=39, amount=-3)], armours=[AttackOrArmor(class_=4, amount=4), AttackOrArmor(class_=8, amount=0), AttackOrArmor(class_=3, amount=4), AttackOrArmor(class_=31, amount=0)], defense_terrain_bonus=-1, bonus_damage_resistance=0.0, max_range=0.0, blast_width=0.0, reload_time=2.0, projectile_unit_id=-1, accuracy_percent=100, break_off_combat=0, frame_delay=0, graphic_displacement=(0.0, 0.0, 0.0), blast_attack_level=0, min_range=0.0, accuracy_dispersion=0.0, attack_graphic=12378, displayed_melee_armour=4, displayed_attack=15, displayed_range=0.0, displayed_reload_time=2.0, blast_damage=1.0), projectile=None, creatable=Creatable(resource_costs=(ResourceCost(type=0, amount=80, flag=1), ResourceCost(type=3, amount=60, flag=1), ResourceCost(type=4, amount=1, flag=0)), train_time=30, train_location_id=82, button_id=4, rear_attack_modifier=0.0, flank_attack_modifier=1.25, creatable_type=1, hero_mode=2, garrison_graphic=-1, spawning_graphic=12262, upgrade_graphic=12263, hero_glow_graphic=12219, max_charge=0.0, recharge_rate=0.0, charge_event=0, charge_type=0, min_conversion_time_mod=0.0, max_conversion_time_mod=0.0, conversion_chance_mod=0.0, total_projectiles=1.0, max_total_projectiles=1, projectile_spawning_area=(1.0, 1.0, 1.0), secondary_projectile_unit=-1, special_graphic=-1, special_ability=0, displayed_pierce_armor=4), building=None)),
        #civ.units.append(Unit(type=70, id=unit_id + 7, language_dll_name=90035, language_dll_creation=90036, class_=12, standing_graphic=(12381, 12380), dying_graphic=12379, undead_graphic=-1, undead_mode=0, hit_points=120, line_of_sight=5.0, garrison_capacity=0, collision_size_x=0.25, collision_size_y=0.25, collision_size_z=2.0, train_sound=604, damage_sound=-1, dead_unit_id=1724, blood_unit_id=-1, sort_number=5, can_be_built_on=0, icon_id=377, hide_in_editor=0, old_portrait_pict=-1, enabled=0, disabled=0, placement_side_terrain=(-1, -1), placement_terrain=(-1, -1), clearance_size=(0.25, 0.25), hill_mode=0, fog_visibility=0, terrain_restriction=28, fly_mode=0, resource_capacity=25, resource_decay=25.0, blast_defense_level=3, combat_level=4, interation_mode=4, minimap_mode=1, interface_kind=4, multiple_attribute_mode=1.0, minimap_color=0, language_dll_help=90037, language_dll_hotkey_text=155610, hot_key=16730, recyclable=0, enable_auto_gather=0, create_doppelganger_on_death=0, resource_gather_group=0, occlusion_mode=1, obstruction_type=5, obstruction_class=2, trait=0, civilization=0, nothing=0, selection_effect=0, editor_selection_colour=0, outline_size_x=0.4000000059604645, outline_size_y=0.4000000059604645, outline_size_z=2.0, scenario_triggers_1=-2, scenario_triggers_2=0, resource_storages=(ResourceStorage(type=4, amount=-1.0, flag=2), ResourceStorage(type=11, amount=1.0, flag=2), ResourceStorage(type=19, amount=1.0, flag=1)), damage_graphics=[], selection_sound=325, dying_sound=-1, wwise_train_sound_id=-2110013473, wwise_damage_sound_id=0, wwise_selection_sound_id=442791689, wwise_dying_sound_id=0, old_attack_reaction=0, convert_terrain=0, name='Crusader', copy_id=2389, base_id=2389, speed=1.100000023841858, dead_fish=DeadFish(walking_graphic=12383, running_graphic=-1, rotation_speed=0.0, old_size_class=0, tracking_unit=-1, tracking_unit_mode=0, tracking_unit_density=0.0, old_move_algorithm=0, turn_radius=0.0, turn_radius_speed=3.4028234663852886e+38, max_yaw_per_second_moving=3.4028234663852886e+38, stationary_yaw_revolution_time=0.0, max_yaw_per_second_stationary=3.4028234663852886e+38, min_collision_size_multiplier=0.5), bird=Bird(default_task_id=-1, search_radius=5.0, work_rate=1.0, drop_sites=[], task_swap_group=0, attack_sound=326, move_sound=326, wwise_attack_sound_id=-1155057397, wwise_move_sound_id=-1155057397, run_pattern=0, tasks=[Task(task_type=1, id=0, is_default=0, action_type=7, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=1, combat_level_flag=1, gather_type=1, work_flag_2=0, target_diplomacy=5, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=1, is_default=0, action_type=3, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=2, is_default=0, action_type=109, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=3, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=4, is_default=0, action_type=3, class_id=3, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=5, is_default=0, action_type=154, class_id=0, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=6, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=7, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=8, is_default=0, action_type=154, class_id=6, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=9, is_default=0, action_type=154, class_id=12, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=10, is_default=0, action_type=154, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=11, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=12, is_default=0, action_type=154, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=13, is_default=0, action_type=154, class_id=21, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=14, is_default=1, action_type=154, class_id=22, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=15, is_default=0, action_type=154, class_id=23, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=16, is_default=0, action_type=154, class_id=35, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=17, is_default=0, action_type=154, class_id=36, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=18, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=19, is_default=0, action_type=154, class_id=44, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=20, is_default=0, action_type=154, class_id=47, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=21, is_default=0, action_type=154, class_id=54, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=22, is_default=0, action_type=154, class_id=55, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0)]), type_50=Type50(base_armor=10000, attacks=[AttackOrArmor(class_=4, amount=16), AttackOrArmor(class_=15, amount=0), AttackOrArmor(class_=11, amount=0), AttackOrArmor(class_=21, amount=0), AttackOrArmor(class_=38, amount=0), AttackOrArmor(class_=39, amount=-3)], armours=[AttackOrArmor(class_=4, amount=4), AttackOrArmor(class_=8, amount=0), AttackOrArmor(class_=3, amount=4), AttackOrArmor(class_=31, amount=0)], defense_terrain_bonus=-1, bonus_damage_resistance=0.0, max_range=0.0, blast_width=0.0, reload_time=2.0, projectile_unit_id=-1, accuracy_percent=100, break_off_combat=0, frame_delay=0, graphic_displacement=(0.0, 0.0, 0.0), blast_attack_level=0, min_range=0.0, accuracy_dispersion=0.0, attack_graphic=12378, displayed_melee_armour=4, displayed_attack=16, displayed_range=0.0, displayed_reload_time=2.0, blast_damage=1.0), projectile=None, creatable=Creatable(resource_costs=(ResourceCost(type=0, amount=80, flag=1), ResourceCost(type=3, amount=60, flag=1), ResourceCost(type=4, amount=1, flag=0)), train_time=30, train_location_id=82, button_id=4, rear_attack_modifier=0.0, flank_attack_modifier=1.25, creatable_type=1, hero_mode=2, garrison_graphic=-1, spawning_graphic=12262, upgrade_graphic=12263, hero_glow_graphic=12219, max_charge=0.0, recharge_rate=0.0, charge_event=0, charge_type=0, min_conversion_time_mod=0.0, max_conversion_time_mod=0.0, conversion_chance_mod=0.0, total_projectiles=1.0, max_total_projectiles=1, projectile_spawning_area=(1.0, 1.0, 1.0), secondary_projectile_unit=-1, special_graphic=-1, special_ability=0, displayed_pierce_armor=4), building=None)),
        #civ.units.append(Unit(type=70, id=unit_id + 8, language_dll_name=90040, language_dll_creation=90041, class_=6, standing_graphic=(1414, -1), dying_graphic=1411, undead_graphic=-1, undead_mode=0, hit_points=65, line_of_sight=3.0, garrison_capacity=0, collision_size_x=0.20000000298023224, collision_size_y=0.20000000298023224, collision_size_z=2.0, train_sound=600, damage_sound=-1, dead_unit_id=1375, blood_unit_id=-1, sort_number=5, can_be_built_on=0, icon_id=297, hide_in_editor=0, old_portrait_pict=-1, enabled=0, disabled=0, placement_side_terrain=(-1, -1), placement_terrain=(-1, -1), clearance_size=(0.20000000298023224, 0.20000000298023224), hill_mode=0, fog_visibility=0, terrain_restriction=7, fly_mode=0, resource_capacity=25, resource_decay=25.0, blast_defense_level=3, combat_level=4, interation_mode=4, minimap_mode=1, interface_kind=4, multiple_attribute_mode=1.0, minimap_color=0, language_dll_help=105011, language_dll_hotkey_text=155011, hot_key=16113, recyclable=0, enable_auto_gather=0, create_doppelganger_on_death=0, resource_gather_group=0, occlusion_mode=1, obstruction_type=5, obstruction_class=2, trait=0, civilization=0, nothing=0, selection_effect=0, editor_selection_colour=0, outline_size_x=0.20000000298023224, outline_size_y=0.20000000298023224, outline_size_z=2.0, scenario_triggers_1=-2, scenario_triggers_2=0, resource_storages=(ResourceStorage(type=4, amount=-1.0, flag=2), ResourceStorage(type=11, amount=1.0, flag=2), ResourceStorage(type=19, amount=1.0, flag=1)), damage_graphics=[], selection_sound=420, dying_sound=-1, wwise_train_sound_id=1091801433, wwise_damage_sound_id=0, wwise_selection_sound_id=-1993334441, wwise_dying_sound_id=0, old_attack_reaction=0, convert_terrain=0, name='Tomahawk Warrior', copy_id=2390, base_id=2390, speed=1.2999999523162842, dead_fish=DeadFish(walking_graphic=1418, running_graphic=-1, rotation_speed=0.0, old_size_class=0, tracking_unit=-1, tracking_unit_mode=0, tracking_unit_density=0.0, old_move_algorithm=0, turn_radius=0.0, turn_radius_speed=3.4028234663852886e+38, max_yaw_per_second_moving=3.4028234663852886e+38, stationary_yaw_revolution_time=0.0, max_yaw_per_second_stationary=3.4028234663852886e+38, min_collision_size_multiplier=0.800000011920929), bird=Bird(default_task_id=-1, search_radius=3.0, work_rate=1.0, drop_sites=[], task_swap_group=0, attack_sound=422, move_sound=421, wwise_attack_sound_id=-533257881, wwise_move_sound_id=-514951588, run_pattern=0, tasks=[Task(task_type=1, id=0, is_default=0, action_type=7, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=1, combat_level_flag=1, gather_type=1, work_flag_2=0, target_diplomacy=5, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=1, is_default=0, action_type=3, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=2, is_default=0, action_type=109, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=3, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=4, is_default=0, action_type=3, class_id=3, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=5, is_default=0, action_type=3, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=6, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=7, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=5.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=8, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=9, is_default=0, action_type=154, class_id=19, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=10, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=11, is_default=0, action_type=154, class_id=-1, unit_id=1811, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=12, is_default=0, action_type=154, class_id=0, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=13, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=14, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=15, is_default=0, action_type=154, class_id=6, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=16, is_default=0, action_type=154, class_id=12, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=17, is_default=0, action_type=154, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=18, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=19, is_default=0, action_type=154, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=20, is_default=0, action_type=154, class_id=21, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=21, is_default=1, action_type=154, class_id=22, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=22, is_default=0, action_type=154, class_id=23, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=23, is_default=0, action_type=154, class_id=35, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=24, is_default=0, action_type=154, class_id=36, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=25, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=26, is_default=0, action_type=154, class_id=44, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=27, is_default=0, action_type=154, class_id=47, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=28, is_default=0, action_type=154, class_id=54, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=29, is_default=0, action_type=154, class_id=55, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0)]), type_50=Type50(base_armor=10000, attacks=[AttackOrArmor(class_=29, amount=2), AttackOrArmor(class_=21, amount=2), AttackOrArmor(class_=4, amount=8), AttackOrArmor(class_=8, amount=8), AttackOrArmor(class_=30, amount=0), AttackOrArmor(class_=1, amount=6)], armours=[AttackOrArmor(class_=1, amount=0), AttackOrArmor(class_=4, amount=0), AttackOrArmor(class_=3, amount=1), AttackOrArmor(class_=19, amount=0), AttackOrArmor(class_=31, amount=0)], defense_terrain_bonus=-1, bonus_damage_resistance=0.0, max_range=3.0, blast_width=0.0, reload_time=2.0, projectile_unit_id=515, accuracy_percent=100, break_off_combat=0, frame_delay=0, graphic_displacement=(0.0, 0.0, 0.0), blast_attack_level=2, min_range=0.0, accuracy_dispersion=0.0, attack_graphic=1408, displayed_melee_armour=0, displayed_attack=8, displayed_range=3.0, displayed_reload_time=2.0, blast_damage=-5.0), projectile=None, creatable=Creatable(resource_costs=(ResourceCost(type=0, amount=65, flag=1), ResourceCost(type=3, amount=25, flag=1), ResourceCost(type=4, amount=1, flag=0)), train_time=15, train_location_id=82, button_id=1, rear_attack_modifier=0.0, flank_attack_modifier=1.0, creatable_type=2, hero_mode=0, garrison_graphic=-1, spawning_graphic=12262, upgrade_graphic=12263, hero_glow_graphic=12218, max_charge=0.0, recharge_rate=0.0, charge_event=0, charge_type=0, min_conversion_time_mod=0.0, max_conversion_time_mod=0.0, conversion_chance_mod=0.0, total_projectiles=1.0, max_total_projectiles=1, projectile_spawning_area=(1.0, 1.0, 1.0), secondary_projectile_unit=-1, special_graphic=-1, special_ability=0, displayed_pierce_armor=1), building=None)),
        #civ.units.append(Unit(type=70, id=unit_id + 9, language_dll_name=90045, language_dll_creation=90046, class_=6, standing_graphic=(1414, -1), dying_graphic=1411, undead_graphic=-1, undead_mode=0, hit_points=70, line_of_sight=3.0, garrison_capacity=0, collision_size_x=0.20000000298023224, collision_size_y=0.20000000298023224, collision_size_z=2.0, train_sound=600, damage_sound=-1, dead_unit_id=1375, blood_unit_id=-1, sort_number=5, can_be_built_on=0, icon_id=297, hide_in_editor=0, old_portrait_pict=-1, enabled=0, disabled=0, placement_side_terrain=(-1, -1), placement_terrain=(-1, -1), clearance_size=(0.20000000298023224, 0.20000000298023224), hill_mode=0, fog_visibility=0, terrain_restriction=7, fly_mode=0, resource_capacity=25, resource_decay=25.0, blast_defense_level=3, combat_level=4, interation_mode=4, minimap_mode=1, interface_kind=4, multiple_attribute_mode=1.0, minimap_color=0, language_dll_help=105011, language_dll_hotkey_text=155011, hot_key=16113, recyclable=0, enable_auto_gather=0, create_doppelganger_on_death=0, resource_gather_group=0, occlusion_mode=1, obstruction_type=5, obstruction_class=2, trait=0, civilization=0, nothing=0, selection_effect=0, editor_selection_colour=0, outline_size_x=0.20000000298023224, outline_size_y=0.20000000298023224, outline_size_z=2.0, scenario_triggers_1=-2, scenario_triggers_2=0, resource_storages=(ResourceStorage(type=4, amount=-1.0, flag=2), ResourceStorage(type=11, amount=1.0, flag=2), ResourceStorage(type=19, amount=1.0, flag=1)), damage_graphics=[], selection_sound=420, dying_sound=-1, wwise_train_sound_id=1091801433, wwise_damage_sound_id=0, wwise_selection_sound_id=-1993334441, wwise_dying_sound_id=0, old_attack_reaction=0, convert_terrain=0, name='Elite Tomahawk Warrior', copy_id=2391, base_id=2391, speed=1.350000023841858, dead_fish=DeadFish(walking_graphic=1418, running_graphic=-1, rotation_speed=0.0, old_size_class=0, tracking_unit=-1, tracking_unit_mode=0, tracking_unit_density=0.0, old_move_algorithm=0, turn_radius=0.0, turn_radius_speed=3.4028234663852886e+38, max_yaw_per_second_moving=3.4028234663852886e+38, stationary_yaw_revolution_time=0.0, max_yaw_per_second_stationary=3.4028234663852886e+38, min_collision_size_multiplier=0.800000011920929), bird=Bird(default_task_id=-1, search_radius=3.0, work_rate=1.0, drop_sites=[], task_swap_group=0, attack_sound=422, move_sound=421, wwise_attack_sound_id=-533257881, wwise_move_sound_id=-514951588, run_pattern=0, tasks=[Task(task_type=1, id=0, is_default=0, action_type=7, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=1, combat_level_flag=1, gather_type=1, work_flag_2=0, target_diplomacy=5, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=1, is_default=0, action_type=3, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=2, is_default=0, action_type=109, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=3, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=4, is_default=0, action_type=3, class_id=3, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=5, is_default=0, action_type=3, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=6, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=7, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=5.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=8, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=9, is_default=0, action_type=154, class_id=19, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=10, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=11, is_default=0, action_type=154, class_id=-1, unit_id=1811, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=12, is_default=0, action_type=154, class_id=0, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=13, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=14, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=15, is_default=0, action_type=154, class_id=6, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=16, is_default=0, action_type=154, class_id=12, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=17, is_default=0, action_type=154, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=18, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=19, is_default=0, action_type=154, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=20, is_default=0, action_type=154, class_id=21, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=21, is_default=1, action_type=154, class_id=22, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=22, is_default=0, action_type=154, class_id=23, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=23, is_default=0, action_type=154, class_id=35, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=24, is_default=0, action_type=154, class_id=36, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=25, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=26, is_default=0, action_type=154, class_id=44, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=27, is_default=0, action_type=154, class_id=47, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=28, is_default=0, action_type=154, class_id=54, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=29, is_default=0, action_type=154, class_id=55, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0)]), type_50=Type50(base_armor=10000, attacks=[AttackOrArmor(class_=29, amount=2), AttackOrArmor(class_=21, amount=2), AttackOrArmor(class_=4, amount=9), AttackOrArmor(class_=8, amount=9), AttackOrArmor(class_=30, amount=0), AttackOrArmor(class_=1, amount=7)], armours=[AttackOrArmor(class_=1, amount=0), AttackOrArmor(class_=4, amount=0), AttackOrArmor(class_=3, amount=1), AttackOrArmor(class_=19, amount=0), AttackOrArmor(class_=31, amount=0)], defense_terrain_bonus=-1, bonus_damage_resistance=0.0, max_range=4.0, blast_width=0.0, reload_time=2.0, projectile_unit_id=515, accuracy_percent=100, break_off_combat=0, frame_delay=0, graphic_displacement=(0.0, 0.0, 0.0), blast_attack_level=2, min_range=0.0, accuracy_dispersion=0.0, attack_graphic=1408, displayed_melee_armour=0, displayed_attack=9, displayed_range=4.0, displayed_reload_time=2.0, blast_damage=-5.0), projectile=None, creatable=Creatable(resource_costs=(ResourceCost(type=0, amount=65, flag=1), ResourceCost(type=3, amount=25, flag=1), ResourceCost(type=4, amount=1, flag=0)), train_time=15, train_location_id=82, button_id=1, rear_attack_modifier=0.0, flank_attack_modifier=1.0, creatable_type=2, hero_mode=0, garrison_graphic=-1, spawning_graphic=12262, upgrade_graphic=12263, hero_glow_graphic=12218, max_charge=0.0, recharge_rate=0.0, charge_event=0, charge_type=0, min_conversion_time_mod=0.0, max_conversion_time_mod=0.0, conversion_chance_mod=0.0, total_projectiles=1.0, max_total_projectiles=1, projectile_spawning_area=(1.0, 1.0, 1.0), secondary_projectile_unit=-1, special_graphic=-1, special_ability=0, displayed_pierce_armor=1), building=None)),
        #civ.units.append(Unit(type=70, id=unit_id + 10, language_dll_name=90050, language_dll_creation=90051, class_=6, standing_graphic=(1037, -1), dying_graphic=1034, undead_graphic=-1, undead_mode=0, hit_points=30, line_of_sight=4.0, garrison_capacity=0, collision_size_x=0.20000000298023224, collision_size_y=0.20000000298023224, collision_size_z=2.0, train_sound=600, damage_sound=-1, dead_unit_id=1147, blood_unit_id=-1, sort_number=5, can_be_built_on=0, icon_id=299, hide_in_editor=0, old_portrait_pict=-1, enabled=0, disabled=0, placement_side_terrain=(-1, -1), placement_terrain=(-1, -1), clearance_size=(0.20000000298023224, 0.20000000298023224), hill_mode=0, fog_visibility=0, terrain_restriction=7, fly_mode=0, resource_capacity=25, resource_decay=25.0, blast_defense_level=3, combat_level=4, interation_mode=4, minimap_mode=1, interface_kind=4, multiple_attribute_mode=1.0, minimap_color=0, language_dll_help=105016, language_dll_hotkey_text=155016, hot_key=16110, recyclable=0, enable_auto_gather=0, create_doppelganger_on_death=0, resource_gather_group=0, occlusion_mode=1, obstruction_type=5, obstruction_class=2, trait=0, civilization=0, nothing=0, selection_effect=0, editor_selection_colour=0, outline_size_x=0.20000000298023224, outline_size_y=0.20000000298023224, outline_size_z=2.0, scenario_triggers_1=-2, scenario_triggers_2=0, resource_storages=(ResourceStorage(type=4, amount=-1.0, flag=2), ResourceStorage(type=11, amount=1.0, flag=2), ResourceStorage(type=19, amount=1.0, flag=1)), damage_graphics=[], selection_sound=420, dying_sound=-1, wwise_train_sound_id=1091801433, wwise_damage_sound_id=0, wwise_selection_sound_id=-1993334441, wwise_dying_sound_id=0, old_attack_reaction=0, convert_terrain=0, name='Ninja', copy_id=2392, base_id=2392, speed=1.5, dead_fish=DeadFish(walking_graphic=1041, running_graphic=-1, rotation_speed=0.0, old_size_class=0, tracking_unit=-1, tracking_unit_mode=0, tracking_unit_density=0.0, old_move_algorithm=0, turn_radius=0.0, turn_radius_speed=3.4028234663852886e+38, max_yaw_per_second_moving=3.4028234663852886e+38, stationary_yaw_revolution_time=0.0, max_yaw_per_second_stationary=3.4028234663852886e+38, min_collision_size_multiplier=0.800000011920929), bird=Bird(default_task_id=-1, search_radius=4.0, work_rate=1.0, drop_sites=[], task_swap_group=0, attack_sound=422, move_sound=421, wwise_attack_sound_id=-533257881, wwise_move_sound_id=-514951588, run_pattern=0, tasks=[Task(task_type=1, id=0, is_default=0, action_type=7, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=1, combat_level_flag=1, gather_type=1, work_flag_2=0, target_diplomacy=5, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=1, is_default=0, action_type=3, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=2, is_default=0, action_type=109, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=3, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=4, is_default=0, action_type=3, class_id=3, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=5, is_default=0, action_type=3, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=6, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=7, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=5.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=8, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=9, is_default=0, action_type=154, class_id=19, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=10, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=11, is_default=0, action_type=154, class_id=-1, unit_id=1811, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0)]), type_50=Type50(base_armor=10000, attacks=[AttackOrArmor(class_=29, amount=2), AttackOrArmor(class_=21, amount=2), AttackOrArmor(class_=4, amount=13), AttackOrArmor(class_=8, amount=0), AttackOrArmor(class_=30, amount=0)], armours=[AttackOrArmor(class_=1, amount=0), AttackOrArmor(class_=4, amount=0), AttackOrArmor(class_=3, amount=0), AttackOrArmor(class_=31, amount=0)], defense_terrain_bonus=-1, bonus_damage_resistance=0.0, max_range=0.0, blast_width=0.0, reload_time=1.2000000476837158, projectile_unit_id=-1, accuracy_percent=100, break_off_combat=0, frame_delay=0, graphic_displacement=(0.0, 0.0, 0.0), blast_attack_level=2, min_range=0.0, accuracy_dispersion=0.0, attack_graphic=1031, displayed_melee_armour=0, displayed_attack=13, displayed_range=0.0, displayed_reload_time=1.2000000476837158, blast_damage=-5.0), projectile=None, creatable=Creatable(resource_costs=(ResourceCost(type=0, amount=30, flag=1), ResourceCost(type=3, amount=60, flag=1), ResourceCost(type=4, amount=1, flag=0)), train_time=9, train_location_id=82, button_id=1, rear_attack_modifier=0.0, flank_attack_modifier=1.0, creatable_type=2, hero_mode=0, garrison_graphic=-1, spawning_graphic=12262, upgrade_graphic=12263, hero_glow_graphic=12218, max_charge=0.0, recharge_rate=0.0, charge_event=0, charge_type=0, min_conversion_time_mod=0.0, max_conversion_time_mod=0.0, conversion_chance_mod=0.0, total_projectiles=1.0, max_total_projectiles=1, projectile_spawning_area=(1.0, 1.0, 1.0), secondary_projectile_unit=-1, special_graphic=-1, special_ability=0, displayed_pierce_armor=0), building=None)),
        #civ.units.append(Unit(type=70, id=unit_id + 11, language_dll_name=90055, language_dll_creation=90056, class_=6, standing_graphic=(1037, -1), dying_graphic=1034, undead_graphic=-1, undead_mode=0, hit_points=35, line_of_sight=4.0, garrison_capacity=0, collision_size_x=0.20000000298023224, collision_size_y=0.20000000298023224, collision_size_z=2.0, train_sound=600, damage_sound=-1, dead_unit_id=1147, blood_unit_id=-1, sort_number=5, can_be_built_on=0, icon_id=299, hide_in_editor=0, old_portrait_pict=-1, enabled=0, disabled=0, placement_side_terrain=(-1, -1), placement_terrain=(-1, -1), clearance_size=(0.20000000298023224, 0.20000000298023224), hill_mode=0, fog_visibility=0, terrain_restriction=7, fly_mode=0, resource_capacity=25, resource_decay=25.0, blast_defense_level=3, combat_level=4, interation_mode=4, minimap_mode=1, interface_kind=4, multiple_attribute_mode=1.0, minimap_color=0, language_dll_help=105016, language_dll_hotkey_text=155016, hot_key=16110, recyclable=0, enable_auto_gather=0, create_doppelganger_on_death=0, resource_gather_group=0, occlusion_mode=1, obstruction_type=5, obstruction_class=2, trait=0, civilization=0, nothing=0, selection_effect=0, editor_selection_colour=0, outline_size_x=0.20000000298023224, outline_size_y=0.20000000298023224, outline_size_z=2.0, scenario_triggers_1=-2, scenario_triggers_2=0, resource_storages=(ResourceStorage(type=4, amount=-1.0, flag=2), ResourceStorage(type=11, amount=1.0, flag=2), ResourceStorage(type=19, amount=1.0, flag=1)), damage_graphics=[], selection_sound=420, dying_sound=-1, wwise_train_sound_id=1091801433, wwise_damage_sound_id=0, wwise_selection_sound_id=-1993334441, wwise_dying_sound_id=0, old_attack_reaction=0, convert_terrain=0, name='Elite Ninja', copy_id=2393, base_id=2393, speed=1.5499999523162842, dead_fish=DeadFish(walking_graphic=1041, running_graphic=-1, rotation_speed=0.0, old_size_class=0, tracking_unit=-1, tracking_unit_mode=0, tracking_unit_density=0.0, old_move_algorithm=0, turn_radius=0.0, turn_radius_speed=3.4028234663852886e+38, max_yaw_per_second_moving=3.4028234663852886e+38, stationary_yaw_revolution_time=0.0, max_yaw_per_second_stationary=3.4028234663852886e+38, min_collision_size_multiplier=0.800000011920929), bird=Bird(default_task_id=-1, search_radius=4.0, work_rate=1.0, drop_sites=[], task_swap_group=0, attack_sound=422, move_sound=421, wwise_attack_sound_id=-533257881, wwise_move_sound_id=-514951588, run_pattern=0, tasks=[Task(task_type=1, id=0, is_default=0, action_type=7, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=1, combat_level_flag=1, gather_type=1, work_flag_2=0, target_diplomacy=5, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=1, is_default=0, action_type=3, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=2, is_default=0, action_type=109, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=3, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=4, is_default=0, action_type=3, class_id=3, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=5, is_default=0, action_type=3, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=6, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=7, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=5.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=8, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=9, is_default=0, action_type=154, class_id=19, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=10, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=11, is_default=0, action_type=154, class_id=-1, unit_id=1811, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0)]), type_50=Type50(base_armor=10000, attacks=[AttackOrArmor(class_=29, amount=2), AttackOrArmor(class_=21, amount=2), AttackOrArmor(class_=4, amount=15), AttackOrArmor(class_=36, amount=9), AttackOrArmor(class_=8, amount=0), AttackOrArmor(class_=30, amount=0)], armours=[AttackOrArmor(class_=1, amount=0), AttackOrArmor(class_=4, amount=1), AttackOrArmor(class_=3, amount=1), AttackOrArmor(class_=31, amount=0)], defense_terrain_bonus=-1, bonus_damage_resistance=0.0, max_range=0.0, blast_width=0.0, reload_time=1.5, projectile_unit_id=-1, accuracy_percent=100, break_off_combat=0, frame_delay=0, graphic_displacement=(0.0, 0.0, 0.0), blast_attack_level=2, min_range=0.0, accuracy_dispersion=0.0, attack_graphic=1031, displayed_melee_armour=1, displayed_attack=15, displayed_range=0.0, displayed_reload_time=1.5, blast_damage=-5.0), projectile=None, creatable=Creatable(resource_costs=(ResourceCost(type=0, amount=30, flag=1), ResourceCost(type=3, amount=60, flag=1), ResourceCost(type=4, amount=1, flag=0)), train_time=9, train_location_id=82, button_id=1, rear_attack_modifier=0.0, flank_attack_modifier=1.0, creatable_type=2, hero_mode=0, garrison_graphic=-1, spawning_graphic=12262, upgrade_graphic=12263, hero_glow_graphic=12218, max_charge=0.0, recharge_rate=0.0, charge_event=0, charge_type=0, min_conversion_time_mod=0.0, max_conversion_time_mod=0.0, conversion_chance_mod=0.0, total_projectiles=1.0, max_total_projectiles=1, projectile_spawning_area=(1.0, 1.0, 1.0), secondary_projectile_unit=-1, special_graphic=-1, special_ability=0, displayed_pierce_armor=1), building=None)),
        #civ.units.append(Unit(type=70, id=unit_id + 12, language_dll_name=90060, language_dll_creation=90061, class_=6, standing_graphic=(7623, -1), dying_graphic=7622, undead_graphic=-1, undead_mode=0, hit_points=60, line_of_sight=4.0, garrison_capacity=0, collision_size_x=0.20000000298023224, collision_size_y=0.20000000298023224, collision_size_z=2.0, train_sound=600, damage_sound=-1, dead_unit_id=895, blood_unit_id=-1, sort_number=5, can_be_built_on=0, icon_id=186, hide_in_editor=0, old_portrait_pict=-1, enabled=0, disabled=0, placement_side_terrain=(-1, -1), placement_terrain=(-1, -1), clearance_size=(0.20000000298023224, 0.20000000298023224), hill_mode=0, fog_visibility=0, terrain_restriction=7, fly_mode=0, resource_capacity=25, resource_decay=25.0, blast_defense_level=3, combat_level=4, interation_mode=4, minimap_mode=1, interface_kind=4, multiple_attribute_mode=1.0, minimap_color=0, language_dll_help=105116, language_dll_hotkey_text=155116, hot_key=16081, recyclable=0, enable_auto_gather=0, create_doppelganger_on_death=0, resource_gather_group=0, occlusion_mode=1, obstruction_type=5, obstruction_class=2, trait=0, civilization=0, nothing=0, selection_effect=0, editor_selection_colour=0, outline_size_x=0.20000000298023224, outline_size_y=0.20000000298023224, outline_size_z=2.0, scenario_triggers_1=-2, scenario_triggers_2=0, resource_storages=(ResourceStorage(type=4, amount=-1.0, flag=2), ResourceStorage(type=11, amount=1.0, flag=2), ResourceStorage(type=19, amount=1.0, flag=1)), damage_graphics=[], selection_sound=420, dying_sound=-1, wwise_train_sound_id=1091801433, wwise_damage_sound_id=0, wwise_selection_sound_id=-1993334441, wwise_dying_sound_id=0, old_attack_reaction=0, convert_terrain=0, name='Scimitar Warrior', copy_id=2394, base_id=2394, speed=0.8999999761581421, dead_fish=DeadFish(walking_graphic=7625, running_graphic=-1, rotation_speed=0.0, old_size_class=0, tracking_unit=-1, tracking_unit_mode=0, tracking_unit_density=0.0, old_move_algorithm=0, turn_radius=0.0, turn_radius_speed=3.4028234663852886e+38, max_yaw_per_second_moving=3.4028234663852886e+38, stationary_yaw_revolution_time=0.0, max_yaw_per_second_stationary=3.4028234663852886e+38, min_collision_size_multiplier=0.800000011920929), bird=Bird(default_task_id=-1, search_radius=4.0, work_rate=1.0, drop_sites=[], task_swap_group=0, attack_sound=422, move_sound=421, wwise_attack_sound_id=-533257881, wwise_move_sound_id=-514951588, run_pattern=0, tasks=[Task(task_type=1, id=0, is_default=0, action_type=7, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=1, combat_level_flag=1, gather_type=1, work_flag_2=0, target_diplomacy=5, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=1, is_default=0, action_type=3, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=2, is_default=0, action_type=109, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=3, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=4, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=5, is_default=0, action_type=3, class_id=3, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=6, is_default=0, action_type=3, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=7, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=8, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=5.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=9, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=10, is_default=0, action_type=154, class_id=19, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=11, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=12, is_default=0, action_type=154, class_id=-1, unit_id=1811, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=13, is_default=0, action_type=154, class_id=0, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=14, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=15, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=16, is_default=0, action_type=154, class_id=6, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=17, is_default=0, action_type=154, class_id=12, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=18, is_default=0, action_type=154, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=19, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=20, is_default=0, action_type=154, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=21, is_default=0, action_type=154, class_id=21, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=22, is_default=1, action_type=154, class_id=22, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=23, is_default=0, action_type=154, class_id=23, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=24, is_default=0, action_type=154, class_id=35, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=25, is_default=0, action_type=154, class_id=36, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=26, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=27, is_default=0, action_type=154, class_id=44, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=28, is_default=0, action_type=154, class_id=47, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=29, is_default=0, action_type=154, class_id=54, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=30, is_default=0, action_type=154, class_id=55, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0)]), type_50=Type50(base_armor=10000, attacks=[AttackOrArmor(class_=4, amount=9), AttackOrArmor(class_=8, amount=0), AttackOrArmor(class_=0, amount=0), AttackOrArmor(class_=30, amount=0)], armours=[AttackOrArmor(class_=1, amount=0), AttackOrArmor(class_=4, amount=1), AttackOrArmor(class_=3, amount=1), AttackOrArmor(class_=31, amount=0), AttackOrArmor(class_=30, amount=8), AttackOrArmor(class_=35, amount=5), AttackOrArmor(class_=5, amount=9)], defense_terrain_bonus=-1, bonus_damage_resistance=0.0, max_range=0.0, blast_width=0.0, reload_time=2.0, projectile_unit_id=-1, accuracy_percent=100, break_off_combat=0, frame_delay=0, graphic_displacement=(0.0, 0.0, 0.0), blast_attack_level=2, min_range=0.0, accuracy_dispersion=0.0, attack_graphic=7621, displayed_melee_armour=1, displayed_attack=9, displayed_range=0.0, displayed_reload_time=2.0, blast_damage=-5.0), projectile=None, creatable=Creatable(resource_costs=(ResourceCost(type=0, amount=60, flag=1), ResourceCost(type=3, amount=20, flag=1), ResourceCost(type=4, amount=1, flag=0)), train_time=21, train_location_id=82, button_id=1, rear_attack_modifier=0.0, flank_attack_modifier=1.0, creatable_type=2, hero_mode=0, garrison_graphic=-1, spawning_graphic=12262, upgrade_graphic=12263, hero_glow_graphic=12218, max_charge=0.0, recharge_rate=0.0, charge_event=0, charge_type=0, min_conversion_time_mod=0.0, max_conversion_time_mod=0.0, conversion_chance_mod=0.0, total_projectiles=1.0, max_total_projectiles=1, projectile_spawning_area=(1.0, 1.0, 1.0), secondary_projectile_unit=-1, special_graphic=-1, special_ability=0, displayed_pierce_armor=1), building=None)),
        #civ.units.append(Unit(type=70, id=unit_id + 13, language_dll_name=90065, language_dll_creation=90066, class_=6, standing_graphic=(7623, -1), dying_graphic=7622, undead_graphic=-1, undead_mode=0, hit_points=70, line_of_sight=4.0, garrison_capacity=0, collision_size_x=0.20000000298023224, collision_size_y=0.20000000298023224, collision_size_z=2.0, train_sound=600, damage_sound=-1, dead_unit_id=895, blood_unit_id=-1, sort_number=5, can_be_built_on=0, icon_id=186, hide_in_editor=0, old_portrait_pict=-1, enabled=0, disabled=0, placement_side_terrain=(-1, -1), placement_terrain=(-1, -1), clearance_size=(0.20000000298023224, 0.20000000298023224), hill_mode=0, fog_visibility=0, terrain_restriction=7, fly_mode=0, resource_capacity=25, resource_decay=25.0, blast_defense_level=3, combat_level=4, interation_mode=4, minimap_mode=1, interface_kind=4, multiple_attribute_mode=1.0, minimap_color=0, language_dll_help=105116, language_dll_hotkey_text=155116, hot_key=16081, recyclable=0, enable_auto_gather=0, create_doppelganger_on_death=0, resource_gather_group=0, occlusion_mode=1, obstruction_type=5, obstruction_class=2, trait=0, civilization=0, nothing=0, selection_effect=0, editor_selection_colour=0, outline_size_x=0.20000000298023224, outline_size_y=0.20000000298023224, outline_size_z=2.0, scenario_triggers_1=-2, scenario_triggers_2=0, resource_storages=(ResourceStorage(type=4, amount=-1.0, flag=2), ResourceStorage(type=11, amount=1.0, flag=2), ResourceStorage(type=19, amount=1.0, flag=1)), damage_graphics=[], selection_sound=420, dying_sound=-1, wwise_train_sound_id=1091801433, wwise_damage_sound_id=0, wwise_selection_sound_id=-1993334441, wwise_dying_sound_id=0, old_attack_reaction=0, convert_terrain=0, name='Elite Scimitar Warrior', copy_id=2395, base_id=2395, speed=0.8999999761581421, dead_fish=DeadFish(walking_graphic=7625, running_graphic=-1, rotation_speed=0.0, old_size_class=0, tracking_unit=-1, tracking_unit_mode=0, tracking_unit_density=0.0, old_move_algorithm=0, turn_radius=0.0, turn_radius_speed=3.4028234663852886e+38, max_yaw_per_second_moving=3.4028234663852886e+38, stationary_yaw_revolution_time=0.0, max_yaw_per_second_stationary=3.4028234663852886e+38, min_collision_size_multiplier=0.800000011920929), bird=Bird(default_task_id=-1, search_radius=4.0, work_rate=1.0, drop_sites=[], task_swap_group=0, attack_sound=422, move_sound=421, wwise_attack_sound_id=-533257881, wwise_move_sound_id=-514951588, run_pattern=0, tasks=[Task(task_type=1, id=0, is_default=0, action_type=7, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=1, combat_level_flag=1, gather_type=1, work_flag_2=0, target_diplomacy=5, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=1, is_default=0, action_type=3, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=2, is_default=0, action_type=109, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=3, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=4, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=5, is_default=0, action_type=3, class_id=3, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=6, is_default=0, action_type=3, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=7, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=8, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=5.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=9, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=10, is_default=0, action_type=154, class_id=19, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=11, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=12, is_default=0, action_type=154, class_id=-1, unit_id=1811, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=13, is_default=0, action_type=154, class_id=0, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=14, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=15, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=16, is_default=0, action_type=154, class_id=6, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=17, is_default=0, action_type=154, class_id=12, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=18, is_default=0, action_type=154, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=19, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=20, is_default=0, action_type=154, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=21, is_default=0, action_type=154, class_id=21, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=22, is_default=1, action_type=154, class_id=22, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=23, is_default=0, action_type=154, class_id=23, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=24, is_default=0, action_type=154, class_id=35, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=25, is_default=0, action_type=154, class_id=36, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=26, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=27, is_default=0, action_type=154, class_id=44, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=28, is_default=0, action_type=154, class_id=47, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=29, is_default=0, action_type=154, class_id=54, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=30, is_default=0, action_type=154, class_id=55, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0)]), type_50=Type50(base_armor=10000, attacks=[AttackOrArmor(class_=4, amount=10), AttackOrArmor(class_=8, amount=0), AttackOrArmor(class_=0, amount=0), AttackOrArmor(class_=30, amount=0)], armours=[AttackOrArmor(class_=1, amount=0), AttackOrArmor(class_=4, amount=2), AttackOrArmor(class_=3, amount=2), AttackOrArmor(class_=31, amount=0), AttackOrArmor(class_=30, amount=10), AttackOrArmor(class_=35, amount=7), AttackOrArmor(class_=5, amount=11)], defense_terrain_bonus=-1, bonus_damage_resistance=0.0, max_range=0.0, blast_width=0.0, reload_time=2.0, projectile_unit_id=-1, accuracy_percent=100, break_off_combat=0, frame_delay=0, graphic_displacement=(0.0, 0.0, 0.0), blast_attack_level=2, min_range=0.0, accuracy_dispersion=0.0, attack_graphic=7621, displayed_melee_armour=2, displayed_attack=10, displayed_range=0.0, displayed_reload_time=2.0, blast_damage=-5.0), projectile=None, creatable=Creatable(resource_costs=(ResourceCost(type=0, amount=60, flag=1), ResourceCost(type=3, amount=20, flag=1), ResourceCost(type=4, amount=1, flag=0)), train_time=21, train_location_id=82, button_id=1, rear_attack_modifier=0.0, flank_attack_modifier=1.0, creatable_type=2, hero_mode=0, garrison_graphic=-1, spawning_graphic=12262, upgrade_graphic=12263, hero_glow_graphic=12218, max_charge=0.0, recharge_rate=0.0, charge_event=0, charge_type=0, min_conversion_time_mod=0.0, max_conversion_time_mod=0.0, conversion_chance_mod=0.0, total_projectiles=1.0, max_total_projectiles=1, projectile_spawning_area=(1.0, 1.0, 1.0), secondary_projectile_unit=-1, special_graphic=-1, special_ability=0, displayed_pierce_armor=2), building=None)),
        #civ.units.append(Unit(type=70, id=unit_id + 14, language_dll_name=90070, language_dll_creation=90071, class_=6, standing_graphic=(7628, -1), dying_graphic=7627, undead_graphic=-1, undead_mode=0, hit_points=60, line_of_sight=4.0, garrison_capacity=0, collision_size_x=0.20000000298023224, collision_size_y=0.20000000298023224, collision_size_z=2.0, train_sound=600, damage_sound=-1, dead_unit_id=362, blood_unit_id=-1, sort_number=5, can_be_built_on=0, icon_id=140, hide_in_editor=0, old_portrait_pict=-1, enabled=0, disabled=0, placement_side_terrain=(-1, -1), placement_terrain=(-1, -1), clearance_size=(0.20000000298023224, 0.20000000298023224), hill_mode=0, fog_visibility=0, terrain_restriction=7, fly_mode=0, resource_capacity=25, resource_decay=25.0, blast_defense_level=3, combat_level=4, interation_mode=4, minimap_mode=1, interface_kind=4, multiple_attribute_mode=1.0, minimap_color=0, language_dll_help=105117, language_dll_hotkey_text=155117, hot_key=16081, recyclable=0, enable_auto_gather=0, create_doppelganger_on_death=0, resource_gather_group=0, occlusion_mode=1, obstruction_type=5, obstruction_class=2, trait=0, civilization=0, nothing=0, selection_effect=0, editor_selection_colour=0, outline_size_x=0.20000000298023224, outline_size_y=0.20000000298023224, outline_size_z=2.0, scenario_triggers_1=-2, scenario_triggers_2=0, resource_storages=(ResourceStorage(type=4, amount=-1.0, flag=2), ResourceStorage(type=11, amount=1.0, flag=2), ResourceStorage(type=19, amount=1.0, flag=1)), damage_graphics=[], selection_sound=420, dying_sound=-1, wwise_train_sound_id=1091801433, wwise_damage_sound_id=0, wwise_selection_sound_id=-1993334441, wwise_dying_sound_id=0, old_attack_reaction=0, convert_terrain=0, name='Drengr', copy_id=2396, base_id=2396, speed=0.8999999761581421, dead_fish=DeadFish(walking_graphic=7630, running_graphic=-1, rotation_speed=0.0, old_size_class=0, tracking_unit=-1, tracking_unit_mode=0, tracking_unit_density=0.0, old_move_algorithm=0, turn_radius=0.0, turn_radius_speed=3.4028234663852886e+38, max_yaw_per_second_moving=3.4028234663852886e+38, stationary_yaw_revolution_time=0.0, max_yaw_per_second_stationary=3.4028234663852886e+38, min_collision_size_multiplier=0.800000011920929), bird=Bird(default_task_id=-1, search_radius=4.0, work_rate=1.0, drop_sites=[], task_swap_group=0, attack_sound=422, move_sound=421, wwise_attack_sound_id=-533257881, wwise_move_sound_id=-514951588, run_pattern=0, tasks=[Task(task_type=1, id=0, is_default=0, action_type=7, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=1, combat_level_flag=1, gather_type=1, work_flag_2=0, target_diplomacy=5, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=1, is_default=0, action_type=3, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=2, is_default=0, action_type=109, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=3, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=4, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=5, is_default=0, action_type=3, class_id=3, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=6, is_default=0, action_type=3, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=7, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=8, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=5.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=9, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=10, is_default=0, action_type=154, class_id=19, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=11, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=12, is_default=0, action_type=154, class_id=-1, unit_id=1811, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=13, is_default=0, action_type=154, class_id=0, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=14, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=15, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=16, is_default=0, action_type=154, class_id=6, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=17, is_default=0, action_type=154, class_id=12, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=18, is_default=0, action_type=154, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=19, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=20, is_default=0, action_type=154, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=21, is_default=0, action_type=154, class_id=21, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=22, is_default=1, action_type=154, class_id=22, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=23, is_default=0, action_type=154, class_id=23, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=24, is_default=0, action_type=154, class_id=35, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=25, is_default=0, action_type=154, class_id=36, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=26, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=27, is_default=0, action_type=154, class_id=44, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=28, is_default=0, action_type=154, class_id=47, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=29, is_default=0, action_type=154, class_id=54, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=30, is_default=0, action_type=154, class_id=55, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0)]), type_50=Type50(base_armor=10000, attacks=[AttackOrArmor(class_=1, amount=6), AttackOrArmor(class_=4, amount=10), AttackOrArmor(class_=8, amount=0), AttackOrArmor(class_=0, amount=9), AttackOrArmor(class_=30, amount=0)], armours=[AttackOrArmor(class_=1, amount=0), AttackOrArmor(class_=4, amount=1), AttackOrArmor(class_=3, amount=3), AttackOrArmor(class_=31, amount=0)], defense_terrain_bonus=-1, bonus_damage_resistance=0.0, max_range=0.0, blast_width=0.0, reload_time=2.0, projectile_unit_id=-1, accuracy_percent=100, break_off_combat=0, frame_delay=0, graphic_displacement=(0.0, 0.0, 0.0), blast_attack_level=2, min_range=0.0, accuracy_dispersion=0.0, attack_graphic=7626, displayed_melee_armour=1, displayed_attack=10, displayed_range=0.0, displayed_reload_time=2.0, blast_damage=-5.0), projectile=None, creatable=Creatable(resource_costs=(ResourceCost(type=1, amount=60, flag=1), ResourceCost(type=3, amount=20, flag=1), ResourceCost(type=4, amount=1, flag=0)), train_time=21, train_location_id=82, button_id=1, rear_attack_modifier=0.0, flank_attack_modifier=1.0, creatable_type=2, hero_mode=0, garrison_graphic=-1, spawning_graphic=12262, upgrade_graphic=12263, hero_glow_graphic=12218, max_charge=0.0, recharge_rate=0.0, charge_event=0, charge_type=0, min_conversion_time_mod=0.0, max_conversion_time_mod=0.0, conversion_chance_mod=0.0, total_projectiles=1.0, max_total_projectiles=1, projectile_spawning_area=(1.0, 1.0, 1.0), secondary_projectile_unit=-1, special_graphic=-1, special_ability=0, displayed_pierce_armor=3), building=None)),
        #civ.units.append(Unit(type=70, id=unit_id + 15, language_dll_name=90075, language_dll_creation=90076, class_=6, standing_graphic=(7628, -1), dying_graphic=7627, undead_graphic=-1, undead_mode=0, hit_points=70, line_of_sight=4.0, garrison_capacity=0, collision_size_x=0.20000000298023224, collision_size_y=0.20000000298023224, collision_size_z=2.0, train_sound=600, damage_sound=-1, dead_unit_id=362, blood_unit_id=-1, sort_number=5, can_be_built_on=0, icon_id=140, hide_in_editor=0, old_portrait_pict=-1, enabled=0, disabled=0, placement_side_terrain=(-1, -1), placement_terrain=(-1, -1), clearance_size=(0.20000000298023224, 0.20000000298023224), hill_mode=0, fog_visibility=0, terrain_restriction=7, fly_mode=0, resource_capacity=25, resource_decay=25.0, blast_defense_level=3, combat_level=4, interation_mode=4, minimap_mode=1, interface_kind=4, multiple_attribute_mode=1.0, minimap_color=0, language_dll_help=105117, language_dll_hotkey_text=155117, hot_key=16081, recyclable=0, enable_auto_gather=0, create_doppelganger_on_death=0, resource_gather_group=0, occlusion_mode=1, obstruction_type=5, obstruction_class=2, trait=0, civilization=0, nothing=0, selection_effect=0, editor_selection_colour=0, outline_size_x=0.20000000298023224, outline_size_y=0.20000000298023224, outline_size_z=2.0, scenario_triggers_1=-2, scenario_triggers_2=0, resource_storages=(ResourceStorage(type=4, amount=-1.0, flag=2), ResourceStorage(type=11, amount=1.0, flag=2), ResourceStorage(type=19, amount=1.0, flag=1)), damage_graphics=[], selection_sound=420, dying_sound=-1, wwise_train_sound_id=1091801433, wwise_damage_sound_id=0, wwise_selection_sound_id=-1993334441, wwise_dying_sound_id=0, old_attack_reaction=0, convert_terrain=0, name='Elite Drengr', copy_id=2397, base_id=2397, speed=0.8999999761581421, dead_fish=DeadFish(walking_graphic=7630, running_graphic=-1, rotation_speed=0.0, old_size_class=0, tracking_unit=-1, tracking_unit_mode=0, tracking_unit_density=0.0, old_move_algorithm=0, turn_radius=0.0, turn_radius_speed=3.4028234663852886e+38, max_yaw_per_second_moving=3.4028234663852886e+38, stationary_yaw_revolution_time=0.0, max_yaw_per_second_stationary=3.4028234663852886e+38, min_collision_size_multiplier=0.800000011920929), bird=Bird(default_task_id=-1, search_radius=4.0, work_rate=1.0, drop_sites=[], task_swap_group=0, attack_sound=422, move_sound=421, wwise_attack_sound_id=-533257881, wwise_move_sound_id=-514951588, run_pattern=0, tasks=[Task(task_type=1, id=0, is_default=0, action_type=7, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=1, combat_level_flag=1, gather_type=1, work_flag_2=0, target_diplomacy=5, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=1, is_default=0, action_type=3, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=2, is_default=0, action_type=109, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=3, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=4, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=5, is_default=0, action_type=3, class_id=3, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=6, is_default=0, action_type=3, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=7, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=8, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=5.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=9, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=10, is_default=0, action_type=154, class_id=19, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=11, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=12, is_default=0, action_type=154, class_id=-1, unit_id=1811, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=13, is_default=0, action_type=154, class_id=0, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=14, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=15, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=16, is_default=0, action_type=154, class_id=6, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=17, is_default=0, action_type=154, class_id=12, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=18, is_default=0, action_type=154, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=19, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=20, is_default=0, action_type=154, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=21, is_default=0, action_type=154, class_id=21, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=22, is_default=1, action_type=154, class_id=22, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=23, is_default=0, action_type=154, class_id=23, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=24, is_default=0, action_type=154, class_id=35, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=25, is_default=0, action_type=154, class_id=36, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=26, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=27, is_default=0, action_type=154, class_id=44, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=28, is_default=0, action_type=154, class_id=47, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=29, is_default=0, action_type=154, class_id=54, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=30, is_default=0, action_type=154, class_id=55, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0)]), type_50=Type50(base_armor=10000, attacks=[AttackOrArmor(class_=1, amount=6), AttackOrArmor(class_=4, amount=11), AttackOrArmor(class_=8, amount=0), AttackOrArmor(class_=0, amount=12), AttackOrArmor(class_=30, amount=0)], armours=[AttackOrArmor(class_=1, amount=0), AttackOrArmor(class_=4, amount=2), AttackOrArmor(class_=3, amount=4), AttackOrArmor(class_=31, amount=0)], defense_terrain_bonus=-1, bonus_damage_resistance=0.0, max_range=0.0, blast_width=0.0, reload_time=2.0, projectile_unit_id=-1, accuracy_percent=100, break_off_combat=0, frame_delay=0, graphic_displacement=(0.0, 0.0, 0.0), blast_attack_level=2, min_range=0.0, accuracy_dispersion=0.0, attack_graphic=7626, displayed_melee_armour=2, displayed_attack=11, displayed_range=0.0, displayed_reload_time=2.0, blast_damage=-5.0), projectile=None, creatable=Creatable(resource_costs=(ResourceCost(type=1, amount=60, flag=1), ResourceCost(type=3, amount=20, flag=1), ResourceCost(type=4, amount=1, flag=0)), train_time=21, train_location_id=82, button_id=1, rear_attack_modifier=0.0, flank_attack_modifier=1.0, creatable_type=2, hero_mode=0, garrison_graphic=-1, spawning_graphic=12262, upgrade_graphic=12263, hero_glow_graphic=12218, max_charge=0.0, recharge_rate=0.0, charge_event=0, charge_type=0, min_conversion_time_mod=0.0, max_conversion_time_mod=0.0, conversion_chance_mod=0.0, total_projectiles=1.0, max_total_projectiles=1, projectile_spawning_area=(1.0, 1.0, 1.0), secondary_projectile_unit=-1, special_graphic=-1, special_ability=0, displayed_pierce_armor=4), building=None)),
        #civ.units.append(Unit(type=70, id=unit_id + 16, language_dll_name=90090, language_dll_creation=90091, class_=12, standing_graphic=(15760, -1), dying_graphic=15759, undead_graphic=-1, undead_mode=0, hit_points=130, line_of_sight=5.0, garrison_capacity=0, collision_size_x=0.25, collision_size_y=0.25, collision_size_z=2.0, train_sound=604, damage_sound=-1, dead_unit_id=2374, blood_unit_id=-1, sort_number=5, can_be_built_on=0, icon_id=687, hide_in_editor=0, old_portrait_pict=-1, enabled=0, disabled=0, placement_side_terrain=(-1, -1), placement_terrain=(-1, -1), clearance_size=(0.25, 0.25), hill_mode=0, fog_visibility=0, terrain_restriction=28, fly_mode=0, resource_capacity=25, resource_decay=25.0, blast_defense_level=3, combat_level=4, interation_mode=4, minimap_mode=1, interface_kind=4, multiple_attribute_mode=1.0, minimap_color=0, language_dll_help=505072, language_dll_hotkey_text=139999, hot_key=416016, recyclable=0, enable_auto_gather=0, create_doppelganger_on_death=0, resource_gather_group=0, occlusion_mode=1, obstruction_type=5, obstruction_class=2, trait=0, civilization=0, nothing=0, selection_effect=0, editor_selection_colour=0, outline_size_x=0.4000000059604645, outline_size_y=0.4000000059604645, outline_size_z=2.0, scenario_triggers_1=-2, scenario_triggers_2=0, resource_storages=(ResourceStorage(type=4, amount=-1.0, flag=2), ResourceStorage(type=11, amount=1.0, flag=2), ResourceStorage(type=19, amount=1.0, flag=1)), damage_graphics=[], selection_sound=325, dying_sound=-1, wwise_train_sound_id=-2110013473, wwise_damage_sound_id=0, wwise_selection_sound_id=442791689, wwise_dying_sound_id=0, old_attack_reaction=0, convert_terrain=0, name='Axe Cavalry', copy_id=2398, base_id=2398, speed=1.5, dead_fish=DeadFish(walking_graphic=15762, running_graphic=-1, rotation_speed=0.0, old_size_class=0, tracking_unit=-1, tracking_unit_mode=0, tracking_unit_density=0.0, old_move_algorithm=0, turn_radius=0.0, turn_radius_speed=3.4028234663852886e+38, max_yaw_per_second_moving=3.4028234663852886e+38, stationary_yaw_revolution_time=0.0, max_yaw_per_second_stationary=3.4028234663852886e+38, min_collision_size_multiplier=0.5), bird=Bird(default_task_id=-1, search_radius=5.0, work_rate=1.0, drop_sites=[], task_swap_group=0, attack_sound=326, move_sound=326, wwise_attack_sound_id=-1155057397, wwise_move_sound_id=-1155057397, run_pattern=0, tasks=[Task(task_type=1, id=0, is_default=0, action_type=7, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=1, combat_level_flag=1, gather_type=1, work_flag_2=0, target_diplomacy=5, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=1, is_default=0, action_type=3, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=2, is_default=0, action_type=109, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=3, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=4, is_default=0, action_type=3, class_id=3, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=5, is_default=0, action_type=154, class_id=0, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=6, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=7, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=8, is_default=0, action_type=154, class_id=6, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=9, is_default=0, action_type=154, class_id=12, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=10, is_default=0, action_type=154, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=11, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=12, is_default=0, action_type=154, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=13, is_default=0, action_type=154, class_id=21, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=14, is_default=1, action_type=154, class_id=22, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=15, is_default=0, action_type=154, class_id=23, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=16, is_default=0, action_type=154, class_id=35, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=17, is_default=0, action_type=154, class_id=36, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=18, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=19, is_default=0, action_type=154, class_id=44, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=20, is_default=0, action_type=154, class_id=47, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=21, is_default=0, action_type=154, class_id=54, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=22, is_default=0, action_type=154, class_id=55, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0)]), type_50=Type50(base_armor=10000, attacks=[AttackOrArmor(class_=4, amount=10), AttackOrArmor(class_=15, amount=0), AttackOrArmor(class_=11, amount=0), AttackOrArmor(class_=21, amount=0), AttackOrArmor(class_=38, amount=0), AttackOrArmor(class_=39, amount=-3)], armours=[AttackOrArmor(class_=4, amount=2), AttackOrArmor(class_=8, amount=0), AttackOrArmor(class_=3, amount=3), AttackOrArmor(class_=31, amount=0)], defense_terrain_bonus=-1, bonus_damage_resistance=0.0, max_range=4.0, blast_width=0.0, reload_time=1.899999976158142, projectile_unit_id=515, accuracy_percent=100, break_off_combat=0, frame_delay=0, graphic_displacement=(0.0, 0.0, 0.0), blast_attack_level=0, min_range=0.0, accuracy_dispersion=0.0, attack_graphic=15758, displayed_melee_armour=2, displayed_attack=10, displayed_range=4.0, displayed_reload_time=1.899999976158142, blast_damage=1.0), projectile=None, creatable=Creatable(resource_costs=(ResourceCost(type=0, amount=70, flag=1), ResourceCost(type=3, amount=85, flag=1), ResourceCost(type=4, amount=1, flag=0)), train_time=30, train_location_id=82, button_id=1, rear_attack_modifier=0.0, flank_attack_modifier=1.25, creatable_type=1, hero_mode=0, garrison_graphic=-1, spawning_graphic=12262, upgrade_graphic=12263, hero_glow_graphic=12219, max_charge=3.0, recharge_rate=0.10000000149011612, charge_event=1, charge_type=1, min_conversion_time_mod=0.0, max_conversion_time_mod=0.0, conversion_chance_mod=0.0, total_projectiles=1.0, max_total_projectiles=1, projectile_spawning_area=(1.0, 1.0, 1.0), secondary_projectile_unit=-1, special_graphic=15763, special_ability=0, displayed_pierce_armor=3), building=None)),
        #civ.units.append(Unit(type=70, id=unit_id + 17, language_dll_name=90095, language_dll_creation=90096, class_=12, standing_graphic=(15760, -1), dying_graphic=15759, undead_graphic=-1, undead_mode=0, hit_points=140, line_of_sight=5.0, garrison_capacity=0, collision_size_x=0.25, collision_size_y=0.25, collision_size_z=2.0, train_sound=604, damage_sound=-1, dead_unit_id=2374, blood_unit_id=-1, sort_number=5, can_be_built_on=0, icon_id=687, hide_in_editor=0, old_portrait_pict=-1, enabled=0, disabled=0, placement_side_terrain=(-1, -1), placement_terrain=(-1, -1), clearance_size=(0.25, 0.25), hill_mode=0, fog_visibility=0, terrain_restriction=28, fly_mode=0, resource_capacity=25, resource_decay=25.0, blast_defense_level=3, combat_level=4, interation_mode=4, minimap_mode=1, interface_kind=4, multiple_attribute_mode=1.0, minimap_color=0, language_dll_help=505072, language_dll_hotkey_text=139999, hot_key=416016, recyclable=0, enable_auto_gather=0, create_doppelganger_on_death=0, resource_gather_group=0, occlusion_mode=1, obstruction_type=5, obstruction_class=2, trait=0, civilization=0, nothing=0, selection_effect=0, editor_selection_colour=0, outline_size_x=0.4000000059604645, outline_size_y=0.4000000059604645, outline_size_z=2.0, scenario_triggers_1=-2, scenario_triggers_2=0, resource_storages=(ResourceStorage(type=4, amount=-1.0, flag=2), ResourceStorage(type=11, amount=1.0, flag=2), ResourceStorage(type=19, amount=1.0, flag=1)), damage_graphics=[], selection_sound=325, dying_sound=-1, wwise_train_sound_id=-2110013473, wwise_damage_sound_id=0, wwise_selection_sound_id=442791689, wwise_dying_sound_id=0, old_attack_reaction=0, convert_terrain=0, name='Elite Axe Cavalry', copy_id=2399, base_id=2399, speed=1.5, dead_fish=DeadFish(walking_graphic=15762, running_graphic=-1, rotation_speed=0.0, old_size_class=0, tracking_unit=-1, tracking_unit_mode=0, tracking_unit_density=0.0, old_move_algorithm=0, turn_radius=0.0, turn_radius_speed=3.4028234663852886e+38, max_yaw_per_second_moving=3.4028234663852886e+38, stationary_yaw_revolution_time=0.0, max_yaw_per_second_stationary=3.4028234663852886e+38, min_collision_size_multiplier=0.5), bird=Bird(default_task_id=-1, search_radius=5.0, work_rate=1.0, drop_sites=[], task_swap_group=0, attack_sound=326, move_sound=326, wwise_attack_sound_id=-1155057397, wwise_move_sound_id=-1155057397, run_pattern=0, tasks=[Task(task_type=1, id=0, is_default=0, action_type=7, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=1, combat_level_flag=1, gather_type=1, work_flag_2=0, target_diplomacy=5, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=1, is_default=0, action_type=3, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=2, is_default=0, action_type=109, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=3, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=4, is_default=0, action_type=3, class_id=3, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=5, is_default=0, action_type=154, class_id=0, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=6, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=7, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=8, is_default=0, action_type=154, class_id=6, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=9, is_default=0, action_type=154, class_id=12, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=10, is_default=0, action_type=154, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=11, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=12, is_default=0, action_type=154, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=13, is_default=0, action_type=154, class_id=21, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=14, is_default=1, action_type=154, class_id=22, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=15, is_default=0, action_type=154, class_id=23, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=16, is_default=0, action_type=154, class_id=35, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=17, is_default=0, action_type=154, class_id=36, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=18, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=19, is_default=0, action_type=154, class_id=44, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=20, is_default=0, action_type=154, class_id=47, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=21, is_default=0, action_type=154, class_id=54, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=22, is_default=0, action_type=154, class_id=55, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=551, resource_out=3, unused_resource=-1, work_value_1=3.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0)]), type_50=Type50(base_armor=10000, attacks=[AttackOrArmor(class_=4, amount=12), AttackOrArmor(class_=15, amount=0), AttackOrArmor(class_=11, amount=0), AttackOrArmor(class_=21, amount=0), AttackOrArmor(class_=38, amount=0), AttackOrArmor(class_=39, amount=-3)], armours=[AttackOrArmor(class_=4, amount=2), AttackOrArmor(class_=8, amount=0), AttackOrArmor(class_=3, amount=3), AttackOrArmor(class_=31, amount=0)], defense_terrain_bonus=-1, bonus_damage_resistance=0.0, max_range=4.0, blast_width=0.0, reload_time=1.899999976158142, projectile_unit_id=515, accuracy_percent=100, break_off_combat=0, frame_delay=0, graphic_displacement=(0.0, 0.0, 0.0), blast_attack_level=0, min_range=0.0, accuracy_dispersion=0.0, attack_graphic=15758, displayed_melee_armour=2, displayed_attack=12, displayed_range=4.0, displayed_reload_time=1.899999976158142, blast_damage=1.0), projectile=None, creatable=Creatable(resource_costs=(ResourceCost(type=0, amount=70, flag=1), ResourceCost(type=3, amount=85, flag=1), ResourceCost(type=4, amount=1, flag=0)), train_time=30, train_location_id=82, button_id=1, rear_attack_modifier=0.0, flank_attack_modifier=1.25, creatable_type=1, hero_mode=0, garrison_graphic=-1, spawning_graphic=12262, upgrade_graphic=12263, hero_glow_graphic=12219, max_charge=3.0, recharge_rate=0.10000000149011612, charge_event=1, charge_type=1, min_conversion_time_mod=0.0, max_conversion_time_mod=0.0, conversion_chance_mod=0.0, total_projectiles=1.0, max_total_projectiles=1, projectile_spawning_area=(1.0, 1.0, 1.0), secondary_projectile_unit=-1, special_graphic=15763, special_ability=0, displayed_pierce_armor=3), building=None)),
        #civ.units.append(Unit(type=70, id=unit_id + 18, language_dll_name=90100, language_dll_creation=90101, class_=6, standing_graphic=(3908, -1), dying_graphic=3907, undead_graphic=-1, undead_mode=0, hit_points=40, line_of_sight=7.0, garrison_capacity=0, collision_size_x=0.20000000298023224, collision_size_y=0.20000000298023224, collision_size_z=2.0, train_sound=600, damage_sound=-1, dead_unit_id=1626, blood_unit_id=-1, sort_number=5, can_be_built_on=0, icon_id=306, hide_in_editor=0, old_portrait_pict=-1, enabled=0, disabled=0, placement_side_terrain=(-1, -1), placement_terrain=(-1, -1), clearance_size=(0.20000000298023224, 0.20000000298023224), hill_mode=0, fog_visibility=0, terrain_restriction=7, fly_mode=0, resource_capacity=25, resource_decay=25.0, blast_defense_level=3, combat_level=4, interation_mode=4, minimap_mode=1, interface_kind=4, multiple_attribute_mode=1.0, minimap_color=0, language_dll_help=105000, language_dll_hotkey_text=155000, hot_key=16671, recyclable=0, enable_auto_gather=0, create_doppelganger_on_death=0, resource_gather_group=0, occlusion_mode=1, obstruction_type=5, obstruction_class=2, trait=0, civilization=0, nothing=0, selection_effect=0, editor_selection_colour=0, outline_size_x=0.20000000298023224, outline_size_y=0.20000000298023224, outline_size_z=2.0, scenario_triggers_1=-2, scenario_triggers_2=0, resource_storages=(ResourceStorage(type=4, amount=-1.0, flag=2), ResourceStorage(type=11, amount=1.0, flag=2), ResourceStorage(type=19, amount=1.0, flag=1)), damage_graphics=[], selection_sound=420, dying_sound=-1, wwise_train_sound_id=1091801433, wwise_damage_sound_id=0, wwise_selection_sound_id=-1993334441, wwise_dying_sound_id=0, old_attack_reaction=0, convert_terrain=0, name='Sun Warrior', copy_id=2400, base_id=2400, speed=1.399999976158142, dead_fish=DeadFish(walking_graphic=3910, running_graphic=-1, rotation_speed=0.0, old_size_class=0, tracking_unit=-1, tracking_unit_mode=0, tracking_unit_density=0.0, old_move_algorithm=0, turn_radius=0.0, turn_radius_speed=3.4028234663852886e+38, max_yaw_per_second_moving=3.4028234663852886e+38, stationary_yaw_revolution_time=0.0, max_yaw_per_second_stationary=3.4028234663852886e+38, min_collision_size_multiplier=0.800000011920929), bird=Bird(default_task_id=-1, search_radius=7.0, work_rate=1.0, drop_sites=[], task_swap_group=0, attack_sound=422, move_sound=421, wwise_attack_sound_id=-533257881, wwise_move_sound_id=-514951588, run_pattern=0, tasks=[Task(task_type=1, id=0, is_default=0, action_type=7, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=1, combat_level_flag=1, gather_type=1, work_flag_2=0, target_diplomacy=5, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=1, is_default=0, action_type=3, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=2, is_default=0, action_type=109, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=3, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=4, is_default=0, action_type=3, class_id=3, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=5, is_default=0, action_type=3, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=6, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=7, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=5.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=8, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=9, is_default=0, action_type=154, class_id=19, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=10, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=11, is_default=0, action_type=154, class_id=-1, unit_id=1811, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0)]), type_50=Type50(base_armor=10000, attacks=[AttackOrArmor(class_=3, amount=5), AttackOrArmor(class_=8, amount=12), AttackOrArmor(class_=16, amount=0), AttackOrArmor(class_=21, amount=0), AttackOrArmor(class_=30, amount=5), AttackOrArmor(class_=29, amount=5)], armours=[AttackOrArmor(class_=29, amount=0), AttackOrArmor(class_=1, amount=0), AttackOrArmor(class_=4, amount=0), AttackOrArmor(class_=3, amount=1), AttackOrArmor(class_=31, amount=0), AttackOrArmor(class_=36, amount=0)], defense_terrain_bonus=-1, bonus_damage_resistance=0.0, max_range=4.0, blast_width=0.0, reload_time=2.0, projectile_unit_id=366, accuracy_percent=100, break_off_combat=0, frame_delay=0, graphic_displacement=(0.0, 0.0, 0.0), blast_attack_level=0, min_range=0.0, accuracy_dispersion=0.0, attack_graphic=3906, displayed_melee_armour=0, displayed_attack=5, displayed_range=4.0, displayed_reload_time=2.0, blast_damage=0.0), projectile=None, creatable=Creatable(resource_costs=(ResourceCost(type=0, amount=20, flag=1), ResourceCost(type=3, amount=50, flag=1), ResourceCost(type=4, amount=1, flag=0)), train_time=18, train_location_id=82, button_id=1, rear_attack_modifier=0.0, flank_attack_modifier=1.0, creatable_type=2, hero_mode=0, garrison_graphic=-1, spawning_graphic=12262, upgrade_graphic=12263, hero_glow_graphic=12218, max_charge=0.0, recharge_rate=0.0, charge_event=0, charge_type=0, min_conversion_time_mod=0.0, max_conversion_time_mod=0.0, conversion_chance_mod=0.0, total_projectiles=1.0, max_total_projectiles=1, projectile_spawning_area=(1.0, 1.0, 1.0), secondary_projectile_unit=366, special_graphic=-1, special_ability=0, displayed_pierce_armor=1), building=None)),
        #civ.units.append(Unit(type=70, id=unit_id + 19, language_dll_name=90105, language_dll_creation=90106, class_=6, standing_graphic=(3908, -1), dying_graphic=3907, undead_graphic=-1, undead_mode=0, hit_points=45, line_of_sight=7.0, garrison_capacity=0, collision_size_x=0.20000000298023224, collision_size_y=0.20000000298023224, collision_size_z=2.0, train_sound=600, damage_sound=-1, dead_unit_id=1626, blood_unit_id=-1, sort_number=5, can_be_built_on=0, icon_id=306, hide_in_editor=0, old_portrait_pict=-1, enabled=0, disabled=0, placement_side_terrain=(-1, -1), placement_terrain=(-1, -1), clearance_size=(0.20000000298023224, 0.20000000298023224), hill_mode=0, fog_visibility=0, terrain_restriction=7, fly_mode=0, resource_capacity=25, resource_decay=25.0, blast_defense_level=3, combat_level=4, interation_mode=4, minimap_mode=1, interface_kind=4, multiple_attribute_mode=1.0, minimap_color=0, language_dll_help=105000, language_dll_hotkey_text=155000, hot_key=16671, recyclable=0, enable_auto_gather=0, create_doppelganger_on_death=0, resource_gather_group=0, occlusion_mode=1, obstruction_type=5, obstruction_class=2, trait=0, civilization=0, nothing=0, selection_effect=0, editor_selection_colour=0, outline_size_x=0.20000000298023224, outline_size_y=0.20000000298023224, outline_size_z=2.0, scenario_triggers_1=-2, scenario_triggers_2=0, resource_storages=(ResourceStorage(type=4, amount=-1.0, flag=2), ResourceStorage(type=11, amount=1.0, flag=2), ResourceStorage(type=19, amount=1.0, flag=1)), damage_graphics=[], selection_sound=420, dying_sound=-1, wwise_train_sound_id=1091801433, wwise_damage_sound_id=0, wwise_selection_sound_id=-1993334441, wwise_dying_sound_id=0, old_attack_reaction=0, convert_terrain=0, name='Sun Warrior', copy_id=2401, base_id=2401, speed=1.4500000476837158, dead_fish=DeadFish(walking_graphic=3910, running_graphic=-1, rotation_speed=0.0, old_size_class=0, tracking_unit=-1, tracking_unit_mode=0, tracking_unit_density=0.0, old_move_algorithm=0, turn_radius=0.0, turn_radius_speed=3.4028234663852886e+38, max_yaw_per_second_moving=3.4028234663852886e+38, stationary_yaw_revolution_time=0.0, max_yaw_per_second_stationary=3.4028234663852886e+38, min_collision_size_multiplier=0.800000011920929), bird=Bird(default_task_id=-1, search_radius=7.0, work_rate=1.0, drop_sites=[], task_swap_group=0, attack_sound=422, move_sound=421, wwise_attack_sound_id=-533257881, wwise_move_sound_id=-514951588, run_pattern=0, tasks=[Task(task_type=1, id=0, is_default=0, action_type=7, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=1, combat_level_flag=1, gather_type=1, work_flag_2=0, target_diplomacy=5, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=1, is_default=0, action_type=3, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=2, is_default=0, action_type=109, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=3, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=4, is_default=0, action_type=3, class_id=3, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=5, is_default=0, action_type=3, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=6, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=7, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=5.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=8, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=9, is_default=0, action_type=154, class_id=19, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=10, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=11, is_default=0, action_type=154, class_id=-1, unit_id=1811, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0)]), type_50=Type50(base_armor=10000, attacks=[AttackOrArmor(class_=3, amount=7), AttackOrArmor(class_=8, amount=15), AttackOrArmor(class_=16, amount=0), AttackOrArmor(class_=21, amount=0), AttackOrArmor(class_=30, amount=7), AttackOrArmor(class_=29, amount=7)], armours=[AttackOrArmor(class_=29, amount=0), AttackOrArmor(class_=1, amount=0), AttackOrArmor(class_=4, amount=0), AttackOrArmor(class_=3, amount=1), AttackOrArmor(class_=31, amount=0), AttackOrArmor(class_=36, amount=0)], defense_terrain_bonus=-1, bonus_damage_resistance=0.0, max_range=4.0, blast_width=0.0, reload_time=2.0, projectile_unit_id=366, accuracy_percent=100, break_off_combat=0, frame_delay=0, graphic_displacement=(0.0, 0.0, 0.0), blast_attack_level=0, min_range=0.0, accuracy_dispersion=0.0, attack_graphic=3906, displayed_melee_armour=0, displayed_attack=7, displayed_range=4.0, displayed_reload_time=2.0, blast_damage=0.0), projectile=None, creatable=Creatable(resource_costs=(ResourceCost(type=0, amount=20, flag=1), ResourceCost(type=3, amount=50, flag=1), ResourceCost(type=4, amount=1, flag=0)), train_time=18, train_location_id=82, button_id=1, rear_attack_modifier=0.0, flank_attack_modifier=1.0, creatable_type=2, hero_mode=0, garrison_graphic=-1, spawning_graphic=12262, upgrade_graphic=12263, hero_glow_graphic=12218, max_charge=0.0, recharge_rate=0.0, charge_event=0, charge_type=0, min_conversion_time_mod=0.0, max_conversion_time_mod=0.0, conversion_chance_mod=0.0, total_projectiles=1.0, max_total_projectiles=1, projectile_spawning_area=(1.0, 1.0, 1.0), secondary_projectile_unit=366, special_graphic=-1, special_ability=0, displayed_pierce_armor=1), building=None)),
        #civ.units.append(Unit(type=70, id=unit_id + 20, language_dll_name=90110, language_dll_creation=90111, class_=6, standing_graphic=(10272, -1), dying_graphic=10271, undead_graphic=-1, undead_mode=0, hit_points=65, line_of_sight=5.0, garrison_capacity=0, collision_size_x=0.20000000298023224, collision_size_y=0.20000000298023224, collision_size_z=2.0, train_sound=600, damage_sound=-1, dead_unit_id=1190, blood_unit_id=-1, sort_number=5, can_be_built_on=0, icon_id=220, hide_in_editor=0, old_portrait_pict=-1, enabled=0, disabled=0, placement_side_terrain=(-1, -1), placement_terrain=(-1, -1), clearance_size=(0.20000000298023224, 0.20000000298023224), hill_mode=0, fog_visibility=0, terrain_restriction=7, fly_mode=0, resource_capacity=25, resource_decay=25.0, blast_defense_level=3, combat_level=4, interation_mode=4, minimap_mode=1, interface_kind=4, multiple_attribute_mode=1.0, minimap_color=0, language_dll_help=901112, language_dll_hotkey_text=155000, hot_key=16469, recyclable=0, enable_auto_gather=0, create_doppelganger_on_death=0, resource_gather_group=0, occlusion_mode=1, obstruction_type=5, obstruction_class=2, trait=0, civilization=0, nothing=0, selection_effect=0, editor_selection_colour=0, outline_size_x=0.20000000298023224, outline_size_y=0.20000000298023224, outline_size_z=2.0, scenario_triggers_1=-2, scenario_triggers_2=0, resource_storages=(ResourceStorage(type=4, amount=-1.0, flag=2), ResourceStorage(type=11, amount=1.0, flag=2), ResourceStorage(type=19, amount=1.0, flag=1)), damage_graphics=[], selection_sound=420, dying_sound=-1, wwise_train_sound_id=1091801433, wwise_damage_sound_id=0, wwise_selection_sound_id=-1993334441, wwise_dying_sound_id=0, old_attack_reaction=0, convert_terrain=0, name='Island Sentinel', copy_id=2402, base_id=2402, speed=1.149999976158142, dead_fish=DeadFish(walking_graphic=10274, running_graphic=-1, rotation_speed=0.0, old_size_class=0, tracking_unit=-1, tracking_unit_mode=0, tracking_unit_density=0.0, old_move_algorithm=0, turn_radius=0.0, turn_radius_speed=3.4028234663852886e+38, max_yaw_per_second_moving=3.4028234663852886e+38, stationary_yaw_revolution_time=0.0, max_yaw_per_second_stationary=3.4028234663852886e+38, min_collision_size_multiplier=0.800000011920929), bird=Bird(default_task_id=-1, search_radius=5.0, work_rate=1.0, drop_sites=[], task_swap_group=0, attack_sound=422, move_sound=421, wwise_attack_sound_id=-533257881, wwise_move_sound_id=-514951588, run_pattern=0, tasks=[Task(task_type=1, id=0, is_default=0, action_type=7, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=1, combat_level_flag=1, gather_type=1, work_flag_2=0, target_diplomacy=5, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=1, is_default=0, action_type=3, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=2, is_default=0, action_type=109, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=3, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=4, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=5, is_default=0, action_type=3, class_id=3, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=6, is_default=0, action_type=3, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=7, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=8, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=5.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=9, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=10, is_default=0, action_type=154, class_id=19, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=11, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=12, is_default=0, action_type=154, class_id=-1, unit_id=1811, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0)]), type_50=Type50(base_armor=10000, attacks=[AttackOrArmor(class_=29, amount=3), AttackOrArmor(class_=21, amount=4), AttackOrArmor(class_=4, amount=9), AttackOrArmor(class_=1, amount=5), AttackOrArmor(class_=30, amount=0)], armours=[AttackOrArmor(class_=1, amount=0), AttackOrArmor(class_=4, amount=2), AttackOrArmor(class_=3, amount=0), AttackOrArmor(class_=31, amount=0), AttackOrArmor(class_=36, amount=0)], defense_terrain_bonus=-1, bonus_damage_resistance=0.0, max_range=0.0, blast_width=0.0, reload_time=2.0, projectile_unit_id=-1, accuracy_percent=100, break_off_combat=0, frame_delay=0, graphic_displacement=(0.0, 0.0, 0.0), blast_attack_level=0, min_range=0.0, accuracy_dispersion=0.0, attack_graphic=10270, displayed_melee_armour=2, displayed_attack=9, displayed_range=0.0, displayed_reload_time=2.0, blast_damage=0.0), projectile=None, creatable=Creatable(resource_costs=(ResourceCost(type=0, amount=60, flag=1), ResourceCost(type=3, amount=50, flag=1), ResourceCost(type=4, amount=1, flag=0)), train_time=21, train_location_id=82, button_id=1, rear_attack_modifier=0.0, flank_attack_modifier=1.0, creatable_type=2, hero_mode=1, garrison_graphic=-1, spawning_graphic=12262, upgrade_graphic=12263, hero_glow_graphic=12218, max_charge=0.0, recharge_rate=0.0, charge_event=0, charge_type=0, min_conversion_time_mod=0.0, max_conversion_time_mod=0.0, conversion_chance_mod=0.0, total_projectiles=1.0, max_total_projectiles=1, projectile_spawning_area=(1.0, 1.0, 1.0), secondary_projectile_unit=-1, special_graphic=10270, special_ability=0, displayed_pierce_armor=0), building=None)),
        #civ.units.append(Unit(type=70, id=unit_id + 21, language_dll_name=90115, language_dll_creation=90116, class_=6, standing_graphic=(10272, -1), dying_graphic=10271, undead_graphic=-1, undead_mode=0, hit_points=75, line_of_sight=5.0, garrison_capacity=0, collision_size_x=0.20000000298023224, collision_size_y=0.20000000298023224, collision_size_z=2.0, train_sound=600, damage_sound=-1, dead_unit_id=1190, blood_unit_id=-1, sort_number=5, can_be_built_on=0, icon_id=220, hide_in_editor=0, old_portrait_pict=-1, enabled=0, disabled=0, placement_side_terrain=(-1, -1), placement_terrain=(-1, -1), clearance_size=(0.20000000298023224, 0.20000000298023224), hill_mode=0, fog_visibility=0, terrain_restriction=7, fly_mode=0, resource_capacity=25, resource_decay=25.0, blast_defense_level=3, combat_level=4, interation_mode=4, minimap_mode=1, interface_kind=4, multiple_attribute_mode=1.0, minimap_color=0, language_dll_help=901117, language_dll_hotkey_text=155000, hot_key=16469, recyclable=0, enable_auto_gather=0, create_doppelganger_on_death=0, resource_gather_group=0, occlusion_mode=1, obstruction_type=5, obstruction_class=2, trait=0, civilization=0, nothing=0, selection_effect=0, editor_selection_colour=0, outline_size_x=0.20000000298023224, outline_size_y=0.20000000298023224, outline_size_z=2.0, scenario_triggers_1=-2, scenario_triggers_2=0, resource_storages=(ResourceStorage(type=4, amount=-1.0, flag=2), ResourceStorage(type=11, amount=1.0, flag=2), ResourceStorage(type=19, amount=1.0, flag=1)), damage_graphics=[], selection_sound=420, dying_sound=-1, wwise_train_sound_id=1091801433, wwise_damage_sound_id=0, wwise_selection_sound_id=-1993334441, wwise_dying_sound_id=0, old_attack_reaction=0, convert_terrain=0, name='Island Sentinel', copy_id=2403, base_id=2403, speed=1.2000000476837158, dead_fish=DeadFish(walking_graphic=10274, running_graphic=-1, rotation_speed=0.0, old_size_class=0, tracking_unit=-1, tracking_unit_mode=0, tracking_unit_density=0.0, old_move_algorithm=0, turn_radius=0.0, turn_radius_speed=3.4028234663852886e+38, max_yaw_per_second_moving=3.4028234663852886e+38, stationary_yaw_revolution_time=0.0, max_yaw_per_second_stationary=3.4028234663852886e+38, min_collision_size_multiplier=0.800000011920929), bird=Bird(default_task_id=-1, search_radius=5.0, work_rate=1.0, drop_sites=[], task_swap_group=0, attack_sound=422, move_sound=421, wwise_attack_sound_id=-533257881, wwise_move_sound_id=-514951588, run_pattern=0, tasks=[Task(task_type=1, id=0, is_default=0, action_type=7, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=1, combat_level_flag=1, gather_type=1, work_flag_2=0, target_diplomacy=5, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=1, is_default=0, action_type=3, class_id=20, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=2, is_default=0, action_type=109, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=1, search_wait_time=3.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=0, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=3, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=4, is_default=0, action_type=13, class_id=-1, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=5, is_default=0, action_type=3, class_id=3, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=4, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=6, is_default=0, action_type=3, class_id=13, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=-1, resource_out=-1, unused_resource=-1, work_value_1=0.0, work_value_2=0.0, work_range=1.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=7, is_default=0, action_type=154, class_id=2, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=8, is_default=0, action_type=154, class_id=4, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=5.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=9, is_default=0, action_type=154, class_id=18, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=10, is_default=0, action_type=154, class_id=19, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=11, is_default=0, action_type=154, class_id=43, unit_id=-1, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0), Task(task_type=1, id=12, is_default=0, action_type=154, class_id=-1, unit_id=1811, terrain_id=-1, resource_in=-1, resource_multiplier=274, resource_out=3, unused_resource=-1, work_value_1=20.0, work_value_2=0.0, work_range=0.0, auto_search_targets=0, search_wait_time=0.0, enable_targeting=0, combat_level_flag=0, gather_type=0, work_flag_2=0, target_diplomacy=1, carry_check=0, pick_for_construction=0, moving_graphic_id=-1, proceeding_graphic_id=-1, working_graphic_id=-1, carrying_graphic_id=-1, resource_gathering_sound_id=-1, resource_deposit_sound_id=-1, wwise_resource_gathering_sound_id=0, wwise_resource_deposit_sound_id=0)]), type_50=Type50(base_armor=10000, attacks=[AttackOrArmor(class_=29, amount=5), AttackOrArmor(class_=21, amount=6), AttackOrArmor(class_=4, amount=11), AttackOrArmor(class_=1, amount=7), AttackOrArmor(class_=30, amount=0)], armours=[AttackOrArmor(class_=1, amount=0), AttackOrArmor(class_=4, amount=2), AttackOrArmor(class_=3, amount=0), AttackOrArmor(class_=31, amount=0), AttackOrArmor(class_=36, amount=0)], defense_terrain_bonus=-1, bonus_damage_resistance=0.0, max_range=0.0, blast_width=0.0, reload_time=2.0, projectile_unit_id=-1, accuracy_percent=100, break_off_combat=0, frame_delay=0, graphic_displacement=(0.0, 0.0, 0.0), blast_attack_level=0, min_range=0.0, accuracy_dispersion=0.0, attack_graphic=10270, displayed_melee_armour=2, displayed_attack=11, displayed_range=0.0, displayed_reload_time=2.0, blast_damage=0.0), projectile=None, creatable=Creatable(resource_costs=(ResourceCost(type=0, amount=60, flag=1), ResourceCost(type=3, amount=50, flag=1), ResourceCost(type=4, amount=1, flag=0)), train_time=21, train_location_id=82, button_id=1, rear_attack_modifier=0.0, flank_attack_modifier=1.0, creatable_type=2, hero_mode=1, garrison_graphic=-1, spawning_graphic=12262, upgrade_graphic=12263, hero_glow_graphic=12218, max_charge=0.0, recharge_rate=0.0, charge_event=0, charge_type=0, min_conversion_time_mod=0.0, max_conversion_time_mod=0.0, conversion_chance_mod=0.0, total_projectiles=1.0, max_total_projectiles=1, projectile_spawning_area=(1.0, 1.0, 1.0), secondary_projectile_unit=-1, special_graphic=10270, special_ability=0, displayed_pierce_armor=0), building=None)),
        pass

    # Copy and filter original strings
    global MOD_STRINGS
    MOD_STRINGS = rf'{local_mods_folder}/{mod_name}/resources/en/strings/key-value/key-value-modded-strings-utf8.txt'
    original_strings = rf'{local_mods_folder}/{mod_name}/resources/en/strings/key-value/key-value-strings-utf8.txt'

    # Convert the lines with codes into a dictionary
    line_dictionary = {}
    with open(original_strings, 'r') as original_file:
        original_strings_list = original_file.readlines()
        for line in original_strings_list:
            match = re.match(r'^(\d+)', line)
            if match:
                key = int(match.group(1))
                line_dictionary[key] = line

    # Write modded strings based on filter conditions
    with open(MOD_STRINGS, 'w') as modded_file:
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

    # Change the Monastery and Monk graphics for the Vikings and Lithuanians
    graphic_replacements = [1712, 1712, 1712, 1712, 1526, 1940, 1941, 1941, 1941, 1941]
    unit_ids = [30, 31, 32, 104, 1421, 125, 286, 922, 1025, 1327]

    for civ_id in [11, 35]:
        for unit_id, replacement_id in zip(unit_ids, graphic_replacements):
            target_unit = DATA.civs[civ_id].units[unit_id]
            source_unit = DATA.civs[civ_id].units[replacement_id]

            # Change icon
            if unit_id >= 125 and unit_id <= 1327:
                target_unit.icon_id = source_unit.icon_id

            attributes = [
                ("standing_graphic",),
                ("dying_graphic",),
                ("undead_graphic",),
                ("damage_graphics",),
                ("type_50", "attack_graphic"),
                ("dead_fish", "walking_graphic"),
                ("dead_fish", "running_graphic")
            ]

            for attr_path in attributes:
                try:
                    src = source_unit
                    tgt = target_unit

                    for attr in attr_path[:-1]:
                        src = getattr(src, attr)
                        tgt = getattr(tgt, attr)

                    setattr(tgt, attr_path[-1], getattr(src, attr_path[-1]))
                except:
                    pass

    # Enable the pasture for Mongols, Berbers, Huns, and Cumans
    DATA.techs[1008].civ = -1
    for effect in [effect_ for effect_ in DATA.effects if "tech tree" in effect_.name.lower()]:
        name = effect.name.lower()
        if any(group in name for group in ['mongols', 'berbers', 'huns', 'cumans']):
            # Disable farms and farm upgrades
            effect.effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 216))
            effect.effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 12))
            effect.effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 13))
            effect.effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 14))
        else:
            # Disable pasture
            effect.effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 1008))

    # Write the architecture sets to a file
    with open(f'{MOD_FOLDER}/{mod_name}.pkl', 'wb') as file:
        for civ in DATA.civs:
            if civ.name != 'Gaia' and civ.name != 'Spartans' and civ.name != 'Athenians' and civ.name != 'Achaemenids':
                pickle.dump(civ.units, file)

    # Remove the Dragon Ship upgrade for the Chinese
    DATA.techs[1010].effect_id = -1
    for i, ec in enumerate(DATA.effects[257].effect_commands):
        if ec.type == 102 and ec.d == 246:
            DATA.effects[257].effect_commands.pop(i)
            break

    # Create the Canoe, War Canoe, and Elite War Canoe units, techs, and effects
    '''base_unit = DATA.civs[1].units[778]
    for civ in DATA.civs:
        # Canoe
        civ.units.append(base_unit)
        civ.units[-1].creatable.train_location_id = 45
        civ.units[-1].creatable.button_id = 4

        # War Canoe
        civ.units.append(base_unit)
        civ.units[-1].creatable.train_location_id = 45
        civ.units[-1].creatable.button_id = 4
        civ.units[-1].standing_graphic = civ.units[1302].standing_graphic
        civ.units[-1].dying_graphic = civ.units[1302].dying_graphic
        civ.units[-1].undead_graphic = civ.units[1302].undead_graphic
        civ.units[-1].dead_fish.walking_graphic = civ.units[1302].dead_fish.walking_graphic
        civ.units[-1].dead_fish.running_graphic = civ.units[1302].dead_fish.running_graphic
        civ.units[-1].icon_id = civ.units[1302].icon_id

        # Elite War Canoe
        civ.units.append(base_unit)
        civ.units[-1].creatable.train_location_id = 45
        civ.units[-1].creatable.button_id = 4
        civ.units[-1].standing_graphic = civ.units[1302].standing_graphic
        civ.units[-1].dying_graphic = civ.units[1302].dying_graphic
        civ.units[-1].undead_graphic = civ.units[1302].undead_graphic
        civ.units[-1].dead_fish.walking_graphic = civ.units[1302].dead_fish.walking_graphic
        civ.units[-1].dead_fish.running_graphic = civ.units[1302].dead_fish.running_graphic
        civ.units[-1].icon_id = civ.units[1302].icon_id

    # Set civilisations to canoe docks by disabling all other warships
    for effect_id in [447, 489, 3]:
        for tech_id in [232, 235, 631, 233, 173, 374]:
            DATA.effects[effect_id].effect_commands.append(genieutils.effect.EffectCommand(type=102, a=-1, b=-1, c=-1, d=tech_id))

        # Swap galley-line for canoe-line
        DATA.effects[effect_id].effect_commands.append(genieutils.effect.EffectCommand(type=3, a=539 , b=len(DATA.civs[1].units)-3, c=-1, d=-1))
        DATA.effects[effect_id].effect_commands.append(genieutils.effect.EffectCommand(type=3, a=21 , b=len(DATA.civs[1].units)-2, c=-1, d=-1))
        DATA.effects[effect_id].effect_commands.append(genieutils.effect.EffectCommand(type=3, a=442 , b=len(DATA.civs[1].units)-1, c=-1, d=-1))'''

    # Correct name mistakes
    DATA.civs[1].name = 'Britons'
    DATA.civs[2].name = 'Franks'
    DATA.civs[16].name = 'Maya'
    DATA.effects[449].name = 'Maya Tech Tree'
    DATA.effects[489].name = 'Maya Team Bonus'
    DATA.civs[21].name = 'Inca'
    DATA.effects[3].name = 'Inca Tech Tree'
    DATA.effects[4].name = 'Inca Team Bonus'

    # Rename existing civ bonuses
    for i, tech in enumerate(DATA.techs):
        if tech.name.startswith(('C-Bonus,', 'C-Bonus')):
            tech.name = tech.name.replace('C-Bonus,', f'#{DATA.civs[tech.civ].name.upper()}:').replace('C-Bonus', f'#{DATA.civs[tech.civ].name.upper()}:')

        # Try to rename the effect as well
        DATA.effects[tech.effect_id].name = DATA.effects[tech.effect_id].name.replace('C-Bonus,', f'#{DATA.civs[tech.civ].name.upper()}:').replace('C-Bonus', f'#{DATA.civs[tech.civ].name.upper()}:')

    '''preexisting_bonuses = [381, 382, 403, 383]
    new_existing_bonus_names = [
        r'BRITONS: Town Centers cost -50% wood starting in the Castle Age',
        r'BRITONS: Foot archers (except skirmishers) +1 range in Castle Age',
        r'BRITONS: Foot archers (except skirmishers) +1 range in Imperial Age',
        r'BRITONS: Shepherds work 25% faster'
        ]
    for i, tech_id in enumerate(preexisting_bonuses):
        DATA.techs[tech_id].name = new_existing_bonus_names[i]
        DATA.effects[DATA.techs[tech_id].effect_id].name = new_existing_bonus_names[i]'''

    # Fix the Tech Tree JSON names
    with open(f'{MOD_FOLDER}/resources/_common/dat/civTechTrees.json', 'r+') as file:
        lines = file.readlines()
        file.seek(0)              # Go back to the start of the file
        file.truncate()           # Clear the file content

        for line in lines:
            if line.strip() == '"civ_id": "INDIANS",':
                line = '      "civ_id": "HINDUSTANIS",\n'
            elif line.strip() == '"civ_id": "MAGYAR",':
                line = '      "civ_id": "MAGYARS",\n'
            file.write(line)

    # Save changes
    with_real_progress(lambda progress: save_dat(progress, rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat'), 'Formatting Mod', total_steps=100)

    # Open the new mod
    if revert:
        print(f"{mod_name} reverted successfully!")
    else:
        print(mod_name, "created!")
    open_mod(MOD_FOLDER)

def main():
    # Import settings
    previous_mod_folder = ''
    previous_mod_name = ''
    try:
        with open('settings.pkl', 'rb') as file:
            previous_mod_folder = pickle.load(file)
            previous_mod_name = previous_mod_folder.split('/')[-1]
    except:
        pass

    # Main menu
    while True:
        print(colour(Back.CYAN, Style.BRIGHT, '🌺🌺🌺 Talofa - Age of Empires II Civilisation Editor 🌺🌺🌺'))
        global MOD_FOLDER
        if os.path.exists(previous_mod_folder + '/' + previous_mod_name + '.pkl'):
            print(colour(Fore.WHITE ,f'0️⃣  Open "{previous_mod_name}"'))
        else:
            print(colour(Fore.LIGHTBLACK_EX ,f'0️⃣  Open Previous Mod'))
        print(colour(Fore.WHITE ,f'1️⃣  Open Mod...'))
        print(colour(Fore.WHITE ,f'2️⃣  New Mod...'))
        selection = input(colour(Fore.CYAN, 'Selection: '))

        if selection == '0': # Open last mod
            if os.path.exists(previous_mod_folder + '/' + previous_mod_name + '.pkl'):
                open_mod(previous_mod_folder)
                break
            else:
                print(colour(Fore.RED, 'ERROR: No previous mod found.\n'))
        elif selection == '1': # Open mod
            MOD_FOLDER = input("\nMod folder location: ")
            open_mod(MOD_FOLDER)
            break
        elif selection == '2': # New mod
            new_mod('', '', '', False)
            break
        else:
            continue

    # Mod menu
    mod_name = MOD_FOLDER.split('/')[-1]
    while True:
        # TEST BONUS
        create_bonus(rf'Mule Carts cost -25%', 0)
        #create_bonus(rf'Mule Cart technologies are +40% more effective', 0)
        #create_bonus(rf'Spearman- and Militia-line upgrades (except Man-at-Arms) available one age earlier', 0)
        #create_bonus(rf'First Fortified Church receives a free Relic', 0)
        #create_bonus(rf'Galley-line and Dromons fire an additional projectile', 0)
        #create_bonus(rf'Start with +50 gold', 0)
        #create_bonus("Villagers carry +3", 0)
        #create_bonus("Military Units train +15% faster", 0)
        #create_bonus("Monks gain +5 HP for each researched Monastery technology", 0)

        # Display selected mod menu
        print(colour(Back.CYAN, Style.BRIGHT, f'\n🌺🌺🌺 {mod_name} Menu 🌺🌺🌺'))
        print(colour(Fore.WHITE, "0️⃣  Edit Civilization"))
        print(colour(Fore.WHITE, "1️⃣  Revert Mod"))
        print(colour(Fore.WHITE, "2️⃣  Open Mod Directory"))
        mod_menu_selection = input(colour(Fore.CYAN, "Selection: "))

        # Open Mod Directory
        if mod_menu_selection == '2':
            try:
                system = platform.system()
                if system == "Windows":
                    os.startfile(previous_mod_folder)
                elif system == "Darwin":  # macOS
                    subprocess.Popen(["open", previous_mod_folder])
                else:  # Linux
                    subprocess.Popen(["xdg-open", previous_mod_folder])
            except:
                print("\033[31mERROR: Mod directory not found in local mods folder.\033[0m")

        # Revert Mod
        elif mod_menu_selection == '1':
            print("\n\033[31mWARNING: Reverting the mod will completely erase all changes made to the modded files. THIS CHANGE IS IRREVERSIBLE.\033[0m")
            time.sleep(0.5)
            yes = input("Enter 'Y' to continue: ")

            if yes:
                new_mod(MOD_FOLDER, ORIGINAL_FOLDER, MOD_NAME, True)
            else:
                print("Mod was not reverted.\n")
            time.sleep(1)

        # Edit Civilisation
        elif mod_menu_selection == '0':
            # Display all civilisations
            selected_civ_index = -1
            all_civs = []
            with open(MOD_STRINGS, 'r') as file:
                lines = file.readlines()
                for civ in DATA.civs:
                    if civ.name != 'Gaia' and civ.name != 'Athenians' and civ.name != 'Spartans' and civ.name != 'Achaemenids':
                        all_civs.append(civ.name)

                while True:
                    while True:
                        readline.set_completer(make_completer(all_civs))
                        readline.parse_and_bind("tab: complete")
                        selection = input("\nEnter civilization ID or name: ").lower()

                        # Convert word to index
                        if selection in [opt.lower() for opt in all_civs]:
                            selection = int([opt.lower() for opt in all_civs].index(selection))
                            break

                        # Help
                        elif selection == '?':
                            for i, allciv in enumerate(all_civs):
                                print(f"{i}: {allciv}")
                            continue

                        # Check to break loop
                        elif int(selection) < len(DATA.civs) - 4:
                            break
                        elif selection == '':
                            continue
                        else:
                            print(colour(Fore.RED, 'ERROR: Invalid entry.'))
                            continue
                        
                    if int(selection) < len(DATA.civs):
                        # Use the civilization ID
                        selected_civ_index = int(selection)
                        if selected_civ_index > 44:
                            selected_civ_index += 3
                        selected_civ_name = lines[selected_civ_index][7:-2]
                        break
                    else:
                        # If no match is found, continue the while loop
                        print("\033[31mERROR: Invalid civilization ID.\033[0m")
                        continue

            # Separate the description to be edited later
            with open(MOD_STRINGS, 'r') as file:
                lines = file.readlines()
                line_index = selected_civ_index + len(DATA.civs) - 1
                line = lines[line_index]
                description_code = line[:6]
                description_lines = line[8:].split(r'\n')

                # Remove any unnecessary characters from the strings
                description_lines = [s.replace('"', '') for s in description_lines]
                description_lines = [s.replace('\n', '') for s in description_lines]

            # Edit civilisation
            try:
                edit_civ_index = int(selection)
                if int(selection) > 44:
                    edit_civ_index += 3
                if 0 <= edit_civ_index < len(DATA.civs) - 1:
                    # Edit civilisation menu
                    while True:
                        # Get current unique unit
                        for i, line in enumerate(description_lines):
                            if 'unique unit' in line.lower():
                                current_unique_unit = description_lines[i + 1].split(',')[0]

                        # Get current unique techs
                        current_unique_techs = ''
                        for word in description_lines[-5].strip('•').split(' '):
                            if '(' in word:
                                break
                            current_unique_techs += word + ' '

                        current_unique_techs += '/'

                        for word in description_lines[-4].strip('•').split(' '):
                            if '(' in word:
                                break
                            current_unique_techs += word + ' '

                        # Get current architecture
                        def get_architecture_list(unit_id):
                            # Get the graphic of the unit
                            unit_id = int(DATA.civs[edit_civ_index + 1].units[unit_id].standing_graphic[0])

                            # Determine which architecture set is currently being used
                            # KEY: (university: 209, castle: 82, wonder: 276)
                            architecture_sets = {'African': [9084, 8747], 'Central Asian': [12084, 11747], 'Central European': [566, 171], 'East Asian': [567, 172], 'Eastern European': [8084, 7747], 'Mediterranean': [593, 177], 'Middle Eastern': [568, 173], 'Mesoamerican': [7084, 6747], 'South Asian': [10084, 12477], 'Southeast Asian': [11084, 10747], 'Southeast European': [15806, 15848], 'Western European': [569, 174]}
                            for arch, ids in architecture_sets.items():
                                if unit_id in ids:
                                    return arch
                            return ''  # or 'Unknown' if you prefer a string

                        # Get current language
                        current_language = ''
                        for sound_item in DATA.sounds[301].items:
                            if sound_item.civilization == selected_civ_index + 1:
                                current_language = sound_item.filename.split('_')[0]

                        # Print the civilization menu
                        print(colour(Back.CYAN, Style.BRIGHT, f'\n🌺🌺🌺 Edit {selected_civ_name} 🌺🌺🌺'))
                        print(colour(Fore.WHITE, f"0️⃣  Name") + f" -- {colour(Fore.BLUE, selected_civ_name)}")
                        print(colour(Fore.WHITE, f"1️⃣  Title") + f" -- {colour(Fore.BLUE, description_lines[0])}")
                        print(colour(Fore.WHITE, f"2️⃣  Bonuses"))
                        print(colour(Fore.WHITE, f"3️⃣  Unique Unit") + f" -- {colour(Fore.BLUE, current_unique_unit)}")
                        print(colour(Fore.WHITE, f"4️⃣  Unique Techs") + f" -- {colour(Fore.BLUE, current_unique_techs)}")
                        print(colour(Fore.WHITE, f"5️⃣  Architecture") + f" -- {colour(Fore.BLUE, get_architecture_list(209))}")
                        print(colour(Fore.WHITE, f"6️⃣  Language") + f" -- {colour(Fore.BLUE, current_language)}")
                        print(colour(Fore.WHITE, f"7️⃣  Tech Tree"))
                        selection = input(colour(Fore.BLUE, "Selection: "))

                        # Exit
                        if selection == '':
                            break

                        # Read description
                        with open(MOD_STRINGS, 'r+') as file:
                            # Read and separate the lines
                            lines = file.readlines()
                            line_index = selected_civ_index + len(DATA.civs) - 1
                            line = lines[line_index]
                            line_code = line[:6]
                            split_lines = line.split(r'\n')

                        # Info
                        if selection == '?':
                            print('0: Change the name of the civilization.')
                            print('1: Change the title of the civilization in its description (ex. Archer civilization).')
                            print('2: Add, remove, or change the civilization bonuses and the team bonus.')
                            print('3: Change the unique unit that can be trained from the civilization\'s castle')
                            print('4: Change the civilization\'s graphics for the general architecture, castle, wonder, and monk.')
                            print('5: Change the language spoken by the units of the civilization.')
                            print('6: Enable or disable units, buildings, and technologies for the civilization. Add additional unique/regional units.')

                        # Name
                        if selection == '0':
                            new_name = input(f"\nEnter new name for {selected_civ_name}: ")
                            old_name = selected_civ_name

                            # Check to see if name already exists
                            name_exists = False
                            for civ in DATA.civs:
                                if civ.name.lower() == new_name.lower():
                                    print("\033[31mERROR: Civilization name already assigned to another civilization.\033[0m")
                                    name_exists = True
                                    break

                            if new_name != '' and new_name != selected_civ_name and not name_exists:
                                # Change name
                                DATA.civs[edit_civ_index + 1].name = new_name
                                with open(MOD_STRINGS, 'r+') as file:
                                    lines = file.readlines()  # Read all lines
                                    lines[selected_civ_index] = lines[selected_civ_index][:5] + f' "{new_name}"\n'  # Modify the specific line
                                    selected_civ_name = new_name  # Update the selected civ name

                                    file.seek(0)  # Move to the beginning of the file
                                    file.writelines(lines)  # Write all lines back

                                # Change name of tech tree, team bonus, and civilization bonus effects
                                for i, effect in enumerate(DATA.effects):
                                    if effect.name == f'{old_name.title()} Tech Tree':
                                        effect.name = f'{selected_civ_name.title()} Tech Tree'
                                    elif effect.name == f'{old_name.title()} Team Bonus':
                                        effect.name = f'{selected_civ_name.title()} Team Bonus'
                                    elif f'{old_name.upper()}' in effect.name:
                                        name_list = effect.name.split(':')
                                        name_list[0] = new_name.upper()
                                        effect.name = ':'.join(name_list)

                                # Change the name of the bonus techs
                                for i, tech in enumerate(DATA.techs):
                                    if f'{old_name.upper()}' in tech.name:
                                        name_list = tech.name.split(':')
                                        name_list[0] = new_name.upper()
                                        tech.name = ':'.join(name_list)

                                # Update the name
                                #with_real_progress(lambda progress: save_dat(progress, rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat'), 'Saving Mod', total_steps=100)
                                print(f'Civilization name changed from {old_name} to {selected_civ_name}.')
                            elif not name_exists:
                                # Do not update the name
                                print(f'Civilization name not changed for {selected_civ_name}.')
                            time.sleep(1)

                        # Title
                        if selection == '1':
                            # Get user input
                            new_title = input(f"\nEnter new civilization title for {selected_civ_name}: ")

                            # Quit if blank
                            if new_title == '':
                                continue

                            # Replace the title
                            if new_title.endswith('civilization') or new_title.endswith('civilisation'):
                                new_title = new_title[:-12].strip()

                            # Apply the Civilization ending
                            description_lines[0] = new_title + ' civilization'

                            # Update the description
                            save_description(description_code, description_lines)
                            print(f'Title updated for {selected_civ_name} to {description_lines[0]}')
                            time.sleep(1)

                        # Bonuses
                        elif selection == '2':
                            while True:
                                with open(MOD_STRINGS, 'r+') as file:
                                    # Read and separate the lines
                                    lines = file.readlines()
                                    line_index = selected_civ_index + len(DATA.civs) - 1
                                    line = lines[line_index]
                                    line_code = line[:6]
                                    split_lines = line.split(r'\n')

                                    # Show the bonuses menu
                                    print("\033[32m\n--- Bonuses Menu ---\033[0m")
                                    bonus_count = 0
                                    searching_for_dots = True
                                    next_line = False
                                    for line in split_lines:
                                        if 'Unique' in line:
                                            searching_for_dots = False
                                        elif '•' in line and searching_for_dots:
                                            print(f"\033[33m{str(bonus_count)}: {line[2:]}\033[0m")
                                            bonus_count += 1
                                        elif 'Team Bonus' in line:
                                            next_line = True
                                        elif next_line:
                                            print(f"\033[33mTeam Bonus: {line[:-2]}\033[0m")
                                    bonus_selection = input("Bonus action: ")

                                    # Show instructions
                                    if bonus_selection == '?':
                                        print('\n\x1b[35mEnter bonus description to add a new bonus.\x1b[0m')
                                        print('\x1b[35mEnter existing bonus index number to remove that bonus.\x1b[0m')
                                        print('\x1b[35mEnter existing bonus index, a colon (:), and then the bonus description to change an existing bonus.\x1b[0m')
                                        print('\x1b[35mEnter "Team bonus: " followed by the bonus description to change the team bonus.\x1b[0m')
                                        time.sleep(1)
                                        continue
                                    
                                    # Quit menu
                                    if bonus_selection == '':
                                        time.sleep(1)
                                        break

                                    # Remove bonus
                                    elif bonus_selection.isdigit():
                                        # Check to make sure
                                        remove_check = input(f'\nAre you sure you want to remove bonus {int(bonus_selection)}: {description_lines[2 + int(bonus_selection)][2:]}? (y/n): ')

                                        if remove_check.lower() == 'y' or remove_check.lower() == 'yes' or remove_check.lower() == 'ye':
                                            # Get current bonuses
                                            bonus_count = 0
                                            searching_for_dots = True
                                            options = []
                                            for line in split_lines:
                                                if 'Unique' in line:
                                                    searching_for_dots = False
                                                elif '•' in line and searching_for_dots:
                                                    options.append(line[2:])
                                                    bonus_count += 1

                                            # Unpair the effect from the tech to disable it
                                            remove_bonus_selection = int(bonus_selection)
                                            if remove_bonus_selection != '':
                                                for tech in DATA.techs:
                                                    if tech.name == f'{selected_civ_name.upper()}: {options[int(remove_bonus_selection)]}':
                                                        tech.effect_id = -1

                                                # Remove from the description
                                                for line in description_lines:
                                                    if options[int(remove_bonus_selection)] in line:
                                                        description_lines.remove(line)
                                                        save_description(description_code, description_lines)

                                                # Save changes
                                                with_real_progress(lambda progress: save_dat(progress, rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat'), 'Saving Mod', total_steps=100)
                                                print(f'Bonus removed for {selected_civ_name}: {options[int(remove_bonus_selection)]}')
                                                time.sleep(1)

                                    # Team bonus
                                    elif bonus_selection.lower().startswith('team bonus:') or bonus_selection.lower().startswith('t:') or bonus_selection.lower().startswith('team:'):
                                        # Get user prompt
                                        bonus_to_add_ORIGINAL = bonus_selection.split(':')[1].strip().capitalize()
                                        bonus_to_add = bonus_to_add_ORIGINAL.lower()

                                        # Generate the bonus
                                        bonus_tech, bonus_effect = create_bonus(bonus_to_add, selected_civ_index)

                                        # Exit if nothing was found
                                        if bonus_effect == []:
                                            break

                                        # Find the previous team effect
                                        team_bonus_effect = None
                                        for i, effect in enumerate(DATA.effects):
                                            if effect.name == f'{selected_civ_name.title()} Team Bonus':
                                                team_bonus_effect = effect

                                        # Update the team bonus
                                        team_bonus_effect.effect_commands = bonus_effect.effect_commands

                                        # Change team bonus in description
                                        bonus_found = False
                                        description_lines[-1] = bonus_to_add_ORIGINAL
#   
                                        # Update the description
                                        save_description(description_code, description_lines)

                                        # Save changes
                                        with_real_progress(lambda progress: save_dat(progress, rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat'), 'Saving Mod', total_steps=100)
                                        print(f'Team bonus changed for {selected_civ_name}.')
                                        time.sleep(1)

                                    # Change bonus
                                    elif bonus_selection[0].isdigit() and bonus_selection[1] == ':':
                                        # Get starting variables
                                        bonus_change_index = int(bonus_selection[0])
                                        bonus_change_from = description_lines[2 + bonus_change_index][2:]
                                        bonus_change_to = bonus_selection[2:].strip()

                                        # Generate the new bonus
                                        bonus_tech, bonus_effect = create_bonus(bonus_change_to, selected_civ_index)

                                        # Exit if nothing was found
                                        if bonus_effect == []:
                                            break

                                        # Unpair the effect from the original tech to disable it
                                        remove_bonus_selection = int(bonus_selection[0])
                                        if remove_bonus_selection != '':
                                            for tech in DATA.techs:
                                                if tech.name == f'{selected_civ_name.upper()}: {options[int(remove_bonus_selection)]}':
                                                    tech.effect_id = -1

                                        # Find the existing bonus effect and give it the new bonus effect commands
                                        for i, effect in enumerate(DATA.effects):
                                            if selected_civ_name.lower() in effect.name.lower() and bonus_change_from in effect.name:
                                                DATA.effects[i] = bonus_effect
                                                DATA.effects[i].name = f'{selected_civ_name.upper()}: {bonus_change_to}'
                                                break

                                        # Find the existing bonus tech
                                        for j, tech in enumerate(DATA.techs):
                                            if tech.civ == selected_civ_index + 1 and bonus_change_from in tech.name:
                                                DATA.techs[j] = bonus_tech[0]
                                                DATA.techs[j].name = f'{selected_civ_name.upper()}: {bonus_change_to}'
                                                DATA.techs[j].effect_id = i
                                                break

                                        # Update the description
                                        description_lines[2 + bonus_change_index] = f'• {bonus_change_to}'
                                        save_description(description_code, description_lines)

                                        # Save changes
                                        with_real_progress(lambda progress: save_dat(progress, rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat'), 'Saving Mod', total_steps=100)
                                        print(f'Bonus {bonus_change_index} changed for {selected_civ_name}.')
                                        time.sleep(1)

                                    # Add bonus
                                    else:
                                        # Get user prompt
                                        bonus_to_add_ORIGINAL = bonus_selection
                                        bonus_to_add = bonus_to_add_ORIGINAL.lower()

                                        # Generate the bonus
                                        bonus_techs, bonus_effect = create_bonus(bonus_to_add, selected_civ_index)

                                        # Use the old tech if it exists
                                        if bonus_effect != []:
                                            tech_found = False
                                            for bonus_tech in bonus_techs:
                                                for tech in DATA.techs:
                                                    if tech.name == bonus_tech.name:
                                                        bonus_tech = tech
                                                        tech.effect_id = DATA.effects.index(bonus_effect)
                                                        tech_found = True
                                                        break

                                                if not tech_found:
                                                    # Add the tech if it didn't exist before
                                                    DATA.techs.append(bonus_tech)

                                                # Add the new effect if it doesn't already exist
                                                effect_found = False
                                                for i, effect in enumerate(DATA.effects):
                                                    if effect.name == bonus_effect.name:
                                                        # Give the new effect commands to the old effect
                                                        effect.effect_commands = bonus_effect.effect_commands
                                                        bonus_tech.effect_id = i
                                                        effect_found = True
                                                        break
                                                    
                                                if not effect_found:
                                                    # Add the effect if it didn't exist before
                                                    DATA.effects.append(bonus_effect)

                                                # Connect the effect to the tech
                                                bonus_tech.effect_id = DATA.effects.index(bonus_effect)

                                            # Append bonus to description
                                            bonus_found = False
                                            for i, line in enumerate(description_lines):
                                                # Add new bonus to the end of the bonuses list
                                                if bonus_to_add_ORIGINAL.lower() in description_lines[i].lower():
                                                    break
                                                if '•' in description_lines[i]:
                                                    bonus_found = True
                                                elif description_lines[i] == '' and bonus_found:
                                                    description_lines.insert(i, f'• {bonus_to_add_ORIGINAL}')
                                                    break
#       
                                            # Update the description
                                            save_description(description_code, description_lines)

                                            # Save changes
                                            with_real_progress(lambda progress: save_dat(progress, rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat'), 'Saving Mod', total_steps=100)
                                            print(f'Bonus added for {selected_civ_name}: {bonus_to_add_ORIGINAL}')
                                            time.sleep(1)

                        # Unique Unit
                        elif selection == '3':
                            # Populate all castle units
                            all_castle_units = ["longbowman", "throwing axeman", "berserk", "teutonic knight", "samurai", "chu ko nu", "cataphract", "war elephant", "mameluke", "janissary", "huskarl", "mangudai", "woad raider", "conquistador", "jaguar warrior", "plumed archer", "tarkan", "war wagon", "genoese crossbowman", "ghulam", "kamayuk", "magyar huszar", "boyar", "organ gun", "shotel warrior", "gbeto", "camel archer", "ballista elephant", "karambit warrior", "arambai", "rattan archer", "konnik", "keshik", "kipchak", "leitis", "coustillier", "serjeant", "obuch", "hussite wagon", "urumi swordsman", "ratha", "chakram thrower", "centurion", "composite bowman", "monaspa", "amazon warrior", "amazon archer", "camel raider", "crusader", "tomahawk warrior", "ninja", "scimitar warrior", "drengr", "qizilbash warrior", "axe cavalry", "sun warrior", "island sentinel"]
                            new_castle_unit = '?'

                            # Get user input
                            while new_castle_unit == '?':
                                new_castle_unit = input(f"\nEnter unique Castle unit for {selected_civ_name}: ").lower()

                                if new_castle_unit == '':
                                    break
                                elif new_castle_unit not in all_castle_units:
                                    new_castle_unit = '?'
                                    print("\033[31mERROR: Unit not found.\033[0m")
                                elif new_castle_unit == '?':
                                    print(all_castle_units)
                                    continue

                            # Get elite upgrade tech
                            elite_upgrade_tech = None
                            for tech in DATA.techs:
                                if tech.civ == selected_civ_index + 1 and 'elite' in tech.name.lower():
                                    elite_upgrade_tech = tech

                            # Get the original costs from the .dat file
                            elite_upgrade_cost = [0, 0, 0] # Food, Wood, Gold
                            for resource_cost in elite_upgrade_tech.resource_costs:
                                # Correct for gold index
                                resource_index = resource_cost.type
                                if resource_index == -1:
                                    continue
                                elif resource_index == 3:
                                    resource_index = 2

                                elite_upgrade_cost[resource_index] = resource_cost.amount

                            # Get user input
                            def get_resource_cost(resource_name: str, default: int) -> int:
                                while True:
                                    value = prompt(f"Change {resource_name} cost for elite upgrade: ", default=str(default))

                                    if value.strip() == '':
                                        return default

                                    try:
                                        value = int(value)
                                        if 0 <= value <= 9999:
                                            return value
                                    except:
                                        pass
                                    
                                    print(f'\033[31mERROR: Entry must be a whole number from 0 to 9999.\n\033[0m')

                            # Use the function for each cost
                            elite_upgrade_cost[0] = get_resource_cost("food", elite_upgrade_cost[0])
                            elite_upgrade_cost[1] = get_resource_cost("wood", elite_upgrade_cost[1])
                            elite_upgrade_cost[2] = get_resource_cost("gold", elite_upgrade_cost[2])

                            # Clear the previous costs
                            for resource_cost in elite_upgrade_tech.resource_costs:
                                resource_cost.type = -1
                                resource_cost.amount = 0
                                resource_cost.flag = 0

                            # Set the costs for the .dat file
                            resource_cost_index = 0
                            for i, cost in enumerate(elite_upgrade_cost):
                                if cost > 0:
                                    gold_correction = 0
                                    if i == 2:
                                        gold_correction = 1

                                    elite_upgrade_tech.resource_costs[i].type = i + gold_correction
                                    elite_upgrade_tech.resource_costs[i].amount = cost
                                    elite_upgrade_tech.resource_costs[i].flag = 1
                                    resource_cost_index += 1

                            # Change research time
                            while True:
                                try:
                                    new_time = int(prompt(f"Enter research time in seconds for elite upgrade: ", default=str(elite_upgrade_tech.research_time)))
                                    if new_time == '':
                                        new_time = elite_upgrade_tech.research_time
                                    elite_upgrade_tech.research_time = new_time
                                    break
                                except:
                                    print(f'\033[31mERROR: Invalid research time entry.\n\033[0m\n')

                            # Get unit indexes
                            castle_unit_indexes = [-1, -1, -1, -1]
                            with open(ORIGINAL_STRINGS, 'r') as file:
                                lines = file.readlines()
                                for i, unit in enumerate(DATA.civs[selected_civ_index + 1].units):
                                    try:
                                        # Get the name of the unit
                                        unit_name_id = int(unit.language_dll_name)
                                        unit_name = None

                                        # Extract unit name from ORIGINAL_STRINGS
                                        for line in lines:
                                            if line.startswith(f"{unit_name_id} "):
                                                unit_name = line.split('"')[1].lower()
                                                break
                                            
                                        # Get the units IDs
                                        if unit_name:
                                            if unit_name == all_castle_units[selected_civ_index]:
                                                castle_unit_indexes[0] = i
                                            elif unit_name == f'elite {all_castle_units[selected_civ_index]}':
                                                castle_unit_indexes[1] = i
                                            elif unit_name == new_castle_unit:
                                                castle_unit_indexes[2] = i
                                            elif unit_name == f'elite {new_castle_unit}':
                                                castle_unit_indexes[3] = i
                                    except:
                                        pass

                            # Change Castle Unit
                            effect_commands = [
                                genieutils.effect.EffectCommand(3, castle_unit_indexes[0], castle_unit_indexes[2], -1, 0),
                                genieutils.effect.EffectCommand(3, castle_unit_indexes[1], castle_unit_indexes[3], -1, 0)
                            ]

                            effect_found = False
                            effect_name = selected_civ_name + " (Castle Unit)"

                            for i, effect in enumerate(DATA.effects):
                                if effect.name == effect_name:
                                    effect.effect_commands = effect_commands
                                    effect_found = True
                                    effect_index = i
                                    break
                                
                            if not effect_found:
                                new_effect = genieutils.effect.Effect(effect_name, effect_commands)
                                DATA.effects.append(new_effect)
                                effect_index = len(DATA.effects) - 1

                            # Create the tech that replaces the old unit
                            new_tech = DATA.techs[1101]
                            new_tech.effect_id = effect_index
                            new_tech.name = effect_name
                            new_tech.civ = selected_civ_index + 1

                            for tech in DATA.techs:
                                if tech.name == effect_name:
                                    DATA.techs.remove(tech)
                            DATA.techs.append(new_tech)

                            # Assemble unit classes
                            classes = {0: 'archer', 6: 'infantry', 12: 'cavalry', 13: 'siege', 18: 'monk', 23: 'mounted hand cannoneer', 36: 'cavalry archer', 38: 'archer', 44: 'hand cannoneer', 55: 'siege weapon'}
                            try:
                                unit_class = classes[DATA.civs[1].units[castle_unit_indexes[2]].class_]
                            except:
                                unit_class = 'unknown'
                                print(DATA.civs[1].units[castle_unit_indexes[2]].class_)

                            # Update description
                            new_unit_description = f'{new_castle_unit.title()} ({unit_class})'
                            for i, line in enumerate(description_lines):
                                if 'unique unit' in line.lower():
                                    description_lines[i + 1] = new_unit_description
                                    save_description(line_code, description_lines)

                            # Save changes
                            with_real_progress(lambda progress: save_dat(progress, rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat'), 'Saving Mod', total_steps=100)
                            print(f"{selected_civ_name.title()} unique unit set to {new_castle_unit.title()}.")
                            time.sleep(1)

                        # Unique Techs
                        elif selection == '4':
                            # Get current techs information
                            unique_techs_names = current_unique_techs.split(' / ')
                            unique_techs_ids = [-1, -1]
                            for i, tech in enumerate(DATA.techs):
                                if tech.civ == selected_civ_index + 1 and tech.required_techs[0] == 102 and tech.research_location == 82:
                                    unique_techs_ids[0] = i
                                elif tech.civ == selected_civ_index + 1 and tech.required_techs[0] == 103 and tech.research_location == 82:
                                    unique_techs_ids[1] = i

                            # Prompt the user for Castle Age tech
                            new_castle_tech_name = prompt(f"\nChange Castle Age tech name: ", default=unique_techs_names[0])
                            if new_castle_tech_name == '':
                                new_castle_tech_name = unique_techs_names[0]
                            while True:
                                prompt_default_text = description_lines[-5].split('(')[1].strip(')')
                                new_castle_tech_description = prompt(f"Change Castle Age tech description: ", default=prompt_default_text)

                                new_castle_tech, new_castle_effect = create_bonus(new_castle_tech_description, selected_civ_index)
                                if len(new_castle_effect.effect_commands) == 0:
                                    print(f'\033[31mERROR: Invalid tech description.\n\033[0m\n')
                                    continue
                                else:
                                    DATA.effects[DATA.techs[unique_techs_ids[0]].effect_id].name = new_castle_tech_description
                                    DATA.effects[DATA.techs[unique_techs_ids[0]].effect_id].effect_commands = new_castle_effect.effect_commands
                                    break


                            new_imperial_tech_name = prompt(f"Change Imperial Age tech name: ", default=unique_techs_names[1])
                            if new_imperial_tech_name == '':
                                new_imperial_tech_name = unique_techs_names[1]
                            while True:
                                prompt_default_text = description_lines[-4].split('(')[1].strip(')')
                                new_imperial_tech_description = prompt(f"Change Imperial Age tech description: ", default=prompt_default_text)

                                new_imperial_tech, new_imperial_effect = create_bonus(new_imperial_tech_description, selected_civ_index)
                                if len(new_imperial_effect.effect_commands) == 0:
                                    print(f'\033[31mERROR: Invalid tech description.\n\033[0m\n')
                                    continue
                                else:
                                    DATA.effects[DATA.techs[unique_techs_ids[1]].effect_id].name = new_imperial_tech_description
                                    DATA.effects[DATA.techs[unique_techs_ids[1]].effect_id].effect_commands = new_imperial_effect.effect_commands
                                    break
                                
                            # Change the names
                            change_string(DATA.techs[unique_techs_ids[0]].language_dll_name, new_castle_tech_name)
                            change_string(DATA.techs[unique_techs_ids[1]].language_dll_name, new_imperial_tech_name)
                            DATA.techs[unique_techs_ids[0]].name = new_castle_tech_name
                            DATA.techs[unique_techs_ids[1]].name = new_imperial_tech_name

                            # Update the description
                            description_lines[-5] = f'• {new_castle_tech_name} ({new_castle_tech_description})'
                            description_lines[-4] = f'• {new_imperial_tech_name} ({new_imperial_tech_description})'
                            save_description(description_code, description_lines)

                            # Save file
                            with_real_progress(lambda progress: save_dat(progress, rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat'), 'Saving Mod', total_steps=100)
                            print(f'Unique techs changed for {selected_civ_name}.')
                            time.sleep(1)

                        # Architecture
                        elif selection == '5':
                            # Gather base architectures
                            base_architectures = []
                            for civ in DATA.civs:
                                if civ.name != 'Spartans' and civ.name != 'Athenians' and civ.name != 'Achaemenids' and civ.name != 'Gaia':
                                    base_architectures.append(civ.name)

                            # Gather custom architectures
                            custom_arcs = [
                                [],
                                ['Poenari Castle'],
                                ['Aachen Cathedral', 'Dome of the Rock', 'Dormition Cathedral', 'Gol Gumbaz', 'Minaret of Jam', 'Pyramid', 'Quimper Cathedral', 'Sankore Madrasah', 'Tower of London'],
                                [],
                                [],
                            ]

                            # User prompts
                            architecture_types = ["General", "Castle", "Wonder", 'Monk', 'Monastery'] # Add types to here
                            architecture_changes = [-1] * len(architecture_types)
                            
                            for i in range(len(architecture_types)):
                                # Assemble all architecture options
                                all_architectures = base_architectures + custom_arcs[i]

                                while True:
                                    # Get user input
                                    readline.set_completer(make_completer(all_architectures))
                                    readline.parse_and_bind("tab: complete")
                                    architecture_selection = input(f"Enter {architecture_types[i]} architecture for {selected_civ_name}: ").lower()

                                    # Help
                                    if architecture_selection == '?':
                                        # Print all available options
                                        for j, arc in enumerate(all_architectures):
                                            print(f'{j}: {arc}')
                                        print('Leave blank to leave the architecture type unchanged.\n')
                                        #print('Type \'default\' to switch back to the Civilization\'s original architecture.')
                                        continue

                                    # Try to convert to an integer
                                    try:
                                        # Convert word to index
                                        if architecture_selection in [opt.lower() for opt in all_architectures]:
                                            architecture_selection = int([opt.lower() for opt in all_architectures].index(architecture_selection))
                                        elif architecture_selection == '':
                                            architecture_selection = -1
                                        else:
                                            architecture_selection = int(architecture_selection)
                                    except:
                                        print(f'\033[31mERROR: {architecture_types[i]} architecture index not valid.\n\033[0m')
                                        continue

                                    # Check against architecture options
                                    if architecture_selection >= -1 and architecture_selection < len(all_architectures):
                                        architecture_changes[i] = architecture_selection
                                        break
                                    else:
                                        # Print error
                                        if i == 3:
                                            print(f'\033[31mERROR: {architecture_types[i]} graphic index not valid.\n\033[0m')
                                        else:
                                            print(f'\033[31mERROR: {architecture_types[i]} architecture index not valid.\n\033[0m')

                            #print(architecture_changes)
                            for i in range(len(architecture_types)):
                                # Skip if unspecified
                                if architecture_changes[i] == -1:
                                    continue

                                # Specify which unit IDs need to change
                                unit_bank = {0: range(0, len(DATA.civs[1].units)), 1: [82, 1430], 2: [276, 1445], 3: [125, 286, 922, 1025, 1327], 4: [30, 31, 32, 104, 1421], 5: [13, 1103, 529, 532, 545, 17, 420, 691, 1104, 527, 528, 539, 21, 442]}
                                all_units_to_change = unit_bank[i]
                                
                                try:
                                    for y, unit_id in enumerate(all_units_to_change):
                                        # Replace the unit or the graphics
                                        if architecture_changes[i] < len(base_architectures):
                                            # Base units
                                            if i == 0 or i == 3:
                                                DATA.civs[selected_civ_index + 1].units[unit_id] = ARCHITECTURE_SETS[architecture_changes[i]][unit_id]
                                            else:
                                                DATA.civs[selected_civ_index + 1].units[unit_id].standing_graphic = ARCHITECTURE_SETS[architecture_changes[i]][unit_id].standing_graphic
                                                DATA.civs[selected_civ_index + 1].units[unit_id].dying_graphic = ARCHITECTURE_SETS[architecture_changes[i]][unit_id].dying_graphic
                                                DATA.civs[selected_civ_index + 1].units[unit_id].damage_graphics = ARCHITECTURE_SETS[architecture_changes[i]][unit_id].damage_graphics
                                        else:
                                            # Custom units
                                            try:
                                                # Find the custom unit
                                                if y == 0:
                                                    # Built unit
                                                    custom_unit_id = get_unit_id(custom_arcs[i][architecture_changes[i] - len(base_architectures)])
                                                elif y == 1:
                                                    # Rubble unit
                                                    custom_rubbles = {'Poenari Castle': 1488, 'Aachen Cathedral': 1517, 'Dome of the Rock': 1482, 'Dormition Cathedral': 1493, 'Gol Gumbaz': 1487, 'Minaret of Jam': 1530, 'Pyramid': 1515, 'Quimper Cathedral': 1489, 'Sankore Madrasah': 1491, 'Tower of London': 1492}
                                                    custom_unit_id = custom_rubbles[custom_arcs[i][architecture_changes[i] - len(base_architectures)]]

                                                DATA.civs[selected_civ_index + 1].units[unit_id].standing_graphic = DATA.civs[1].units[custom_unit_id].standing_graphic
                                                DATA.civs[selected_civ_index + 1].units[unit_id].dying_graphic = DATA.civs[1].units[custom_unit_id].dying_graphic
                                                DATA.civs[selected_civ_index + 1].units[unit_id].damage_graphics = DATA.civs[1].units[custom_unit_id].damage_graphics
                                            except Exception as e:
                                                print(str(e))
                                except Exception as e:
                                    print(str(e))

                            # Save changes
                            if architecture_changes != [-1] * len(architecture_types):
                                with_real_progress(lambda progress: save_dat(progress, rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat'), 'Saving Mod', total_steps=100)
                                print(f"Architecture changed for {selected_civ_name}.")
                            else:
                                print(f"Architecture was not changed for {selected_civ_name}.")
                            time.sleep(1)

                        # Language
                        elif selection == '6':
                            # Assemble all of the language options
                            all_languages = []
                            for civ in DATA.civs[1:]:
                                if civ.name == 'British':
                                    all_languages.append('Britons')
                                elif civ.name == 'French':
                                    all_languages.append('Franks')
                                else:
                                    all_languages.append(civ.name)
                            all_languages.append('Greek')

                            # Change language
                            while True:
                                new_language = input(f"\nEnter new language for {selected_civ_name}: ").title()

                                if new_language == '':
                                    break
                                elif new_language == '?':
                                    print(', '.join(all_languages))
                                elif new_language.title() in all_languages:
                                    # Change sounds
                                    sound_ids = {303: 'Villager_Male_Select_4', 301: 'Villager_Male_Move_4', 295: 'Villager_Male_Build_1', 299: 'Villager_Male_Chop_1', 455: 'Villager_Male_Farm_1', 448: 'Villager_Male_Fish_1', 297: 'Villager_Male_Forage_1', 298: 'Villager_Male_Hunt_1', 300: 'Villager_Male_Mine_1', 302: 'Villager_Male_Repair_1', 435: 'Villager_Female_Select_4', 434: 'Villager_Female_Move_4', 437: 'Villager_Female_Build_1', 442: 'Villager_Female_Chop_1', 438: 'Villager_Female_Farm_1', 487: 'Villager_Female_Fish_1', 440: 'Villager_Female_Forage_1', 441: 'Villager_Female_Hunt_1', 443: 'Villager_Female_Mine_1', 444: 'Villager_Female_Repair_1', 420: 'Soldier_Select_3', 421: 'Soldier_Move_3', 422: 'Soldier_Attack_3', 423: 'Monk_Select_3', 424: 'Monk_Move_3', 479: 'King_Select_3', 480: 'King_Move_3'}

                                    # Change the sounds in the .dat file
                                    for civ in DATA.civs[1:]:
                                        for sound_id in sound_ids:
                                            # Get the amount of sound items to add
                                            sound_count = int(sound_ids[sound_id][-1])

                                            # Change the sound items in the sound
                                            for i, item in enumerate(DATA.sounds[sound_id].items):
                                                if item.civilization == selected_civ_index + 1:
                                                    new_name = item.filename.split('_')
                                                    new_name[0] = new_language
                                                    item.filename = '_'.join(new_name)

                                    # Save changes
                                    with_real_progress(lambda progress: save_dat(progress, rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat'), 'Saving Mod', total_steps=100)
                                    print(f"Language for {selected_civ_name} changed to {new_language}.")
                                    break
                                else:
                                    print("\033[31mERROR: Language not found.\033[0m")
                            pass

                        # Tech Tree
                        elif selection == '7':
                            # Import the tech tree
                            while True:
                                # Tech tree main menu
                                print(colour(Back.CYAN, Style.BRIGHT, f'\n🌺🌺🌺 Tech Tree Menu 🌺🌺🌺'))
                                print(colour(Fore.WHITE, "0️⃣  Barracks"))
                                print(colour(Fore.WHITE, "1️⃣  Archery Range"))
                                print(colour(Fore.WHITE, "2️⃣  Stable"))
                                print(colour(Fore.WHITE, "3️⃣  Blacksmith"))
                                print(colour(Fore.WHITE, "4️⃣  Market"))
                                print(colour(Fore.WHITE, "5️⃣  Dock"))
                                print(colour(Fore.WHITE, "6️⃣  Siege Workshop"))
                                print(colour(Fore.WHITE, "7️⃣  University"))
                                print(colour(Fore.WHITE, "8️⃣  Monastery"))
                                print(colour(Fore.WHITE, "9️⃣  Castle and Defensive"))
                                print(colour(Fore.WHITE, "🔟 Economic"))
                                tech_tree_selection = input(colour(Fore.BLUE, "Selection: "))

                                # Set the tree
                                building_ids = [12, 87, 101, 103, 84, 45, 49, 209, [104, 1806], [72, 117, 82, 1251, 1665], [70, 109, 584, 562, 68, 1734, 1808, 1754, 1021]]
                                try:
                                    selected = building_ids[int(tech_tree_selection)]

                                    if isinstance(selected, list):
                                        tree = []
                                        for sub_id in selected:
                                            tree.extend([entry for entry in FOREST if entry.get("Building ID") == sub_id])
                                    else:
                                        tree = [entry for entry in FOREST if entry.get("Building ID") == selected]
                                except:
                                    continue

                                while True:
                                    # Build mappings
                                    link_map = {unit.get("Link ID"): unit for unit in tree if unit.get("Link ID") is not None}
                                    node_map = {unit.get("Node ID"): unit for unit in tree if unit.get("Node ID") is not None}

                                    # Identify all end-of-line units
                                    end_units = [unit for unit in tree if unit.get("Link ID") == -1]

                                    # Track printed lines to avoid duplicates
                                    seen = set()
                                    print(colour(Back.CYAN, Style.BRIGHT, f'\n🌺🌺🌺 Tech Tree Branch Menu 🌺🌺🌺'))

                                    # Add the host building
                                    current_building_id = building_ids[int(tech_tree_selection)]

                                    # Find the host building (first match with this Building ID and a Use Type of "Building" if needed)
                                    host_building = next((entry for entry in FOREST if entry.get("Node ID") == current_building_id), None)
                                    if host_building:
                                        building_colour = Fore.GREEN if host_building.get("Node Status") == "ResearchedCompleted" or host_building.get('Node Status') == 'ResearchRequired' else Fore.RED
                                        print(colour(building_colour, f"{host_building.get('Name')}"))

                                    for end_unit in end_units:
                                        line = [end_unit]
                                        current = end_unit

                                        # Walk backward in the upgrade chain
                                        while True:
                                            next_unit = next(
                                                (unit for unit in tree if unit.get("Link ID") == current.get("Node ID")), None
                                            )
                                            if next_unit:
                                                line.append(next_unit)
                                                current = next_unit
                                            else:
                                                break
                                            
                                        # Skip if already printed
                                        if line[0].get("Node ID") in seen:
                                            continue
                                        
                                        seen.update(unit.get("Node ID") for unit in line)

                                        # Print it
                                        CIV_OBJECTS
                                        line_display = []

                                        for unit in line:
                                            node_id = unit.get("Node ID")

                                            # Find matching civ unit entry
                                            civ_unit = next((u for u in CIV_OBJECTS[selected_civ_index].units if u.get("Node ID") == node_id), None)

                                            # Set the colour for the item
                                            unit_colour = Fore.BLACK
                                            if civ_unit and civ_unit.get("Node Status") == "ResearchedCompleted" or civ_unit and civ_unit.get("Node Status") == "ResearchRequired":
                                                unit_colour = Fore.GREEN
                                            elif civ_unit and civ_unit.get("Node Status") == "NotAvailable":
                                                unit_colour = Fore.RED

                                            line_display.append(colour(unit_colour, unit.get("Name")))

                                        print(" → ".join(line_display))

                                    # Get user input
                                    branch_action = input(colour(Fore.BLUE, 'Tech Tree Branch action: '))

                                    # Exit
                                    if branch_action == '':
                                        break

                                '''while True:
                                    global TECH_TREE
                                    TECH_TREE = {}
                                    with open(f'{MOD_FOLDER}/resources/_common/dat/civTechTrees.json', 'r') as file:
                                        # Get the line of the selected civ
                                        lines = file.readlines()
                                        civ_id_line_indexes = [i for i, line in enumerate(lines) if '"civ_id":' in line]
                                        index = civ_id_line_indexes[selected_civ_index] + 1

                                        # Get the tech tree of the selected civ
                                        for line in lines[index:]:
                                            if '\"Name\":' in line:
                                                selected_unit = line.split('\"Name\": "')[1].split('",')[0].lower()
                                            elif '\"Node Status\":' in line:
                                                selected_status = line.split('\"Node Status\": "')[1].split('",')[0]

                                                # Convert status to integer
                                                if selected_status == 'NotAvailable':
                                                    selected_status = 0
                                                elif selected_status == 'ResearchedCompleted':
                                                    selected_status = 1
                                                elif selected_status == 'ResearchRequired':
                                                    selected_status = 2

                                                # Add to tech tree
                                                TECH_TREE[selected_unit] = selected_status

                                            # Check for the end of the tech tree section
                                            if 'civ_id' in line:
                                                break

                                    # Print the respective branch of the tree
                                    print(f"\033[32m\n--- {selected_civ_name} {branch_title} Branch Menu ---\033[0m")
                                    tree_string = ''
                                    for i, branch in enumerate(tree):
                                        twig_string = ''
                                        for letter, twig in zip(string.ascii_uppercase, branch):
                                            try:
                                                if (TECH_TREE[re.sub(r'\s*\([^)]*\)', '', twig).lower()] == 0):
                                                    twig_string += f'[{i}{letter}] \033[31m{twig[:-4]}\033[0m --> '
                                                else:
                                                    twig_string += f'[{i}{letter}] \033[32m{twig[:-4]}\033[0m --> '
                                            except:
                                                pass
                                        tree_string += twig_string
                                        print(twig_string[:-4])
                                    toggle_selection = input("Addresses: ")

                                    # Exit
                                    if toggle_selection == '':
                                        break

                                    # Help
                                    elif toggle_selection == '?':
                                        print('\n\x1b[35mGreen items are enabled. Red items are disabled.\x1b[0m')
                                        print('\x1b[35mType any address to toggle enable/disable the item.\x1b[0m')
                                        print('\x1b[35mYou may stack several addresses in one line, separated by a space.\x1b[0m')

                                    # Toggle units
                                    else:
                                        toggle_addresses = toggle_selection.split(' ')

                                        # Toggle each unit
                                        for address in toggle_addresses:
                                            try:
                                                # Convert the address into the unit's name
                                                unit_to_toggle = tree[int(address[:-1])][ord(address[-1].upper()) - ord('A')][:-4]

                                                # Toggle the unit's value in the tree between 0 and 1
                                                TECH_TREE[unit_to_toggle.lower()] = abs(TECH_TREE[unit_to_toggle.lower()])

                                                # Get the tech tree effect index
                                                for i, effect in enumerate(DATA.effects):
                                                    if 'tech tree' in effect.name.lower() and selected_civ_name.lower() in effect.name.lower():
                                                        tech_tree_index = i
                                                        break

                                                # Determine whether it's a unit or a tech
                                                if get_unit_id(unit_to_toggle) is None:
                                                    item_index = f'_{get_tech_id(unit_to_toggle)}'
                                                else:
                                                    item_index = get_unit_id(unit_to_toggle)

                                                # Toggle the unit
                                                toggle_unit(item_index, 'toggle', tech_tree_index, selected_civ_name)

                                                # Follow toggle rules
                                                #for branch in tree:
                                                    # If disabling, disable all non-X units that are higher


                                                # If enabling, enable all non-X units that are lower
                                                # If enabling an X unit, disable all non-X that are higher
                                                # If enabling a tiered unit, disable all units in the same tier on the same branch

                                            except Exception as e:
                                                print(e)
                                                #print(f'Invalid address: {address.upper()}')

                                        # Save the .dat file and tell the user the update is complete
                                        with_real_progress(lambda progress: save_dat(progress, rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat'), 'Saving Mod', total_steps=100)
                                        print(f'{selected_civ_name} Tech Tree updated.')
                                        time.sleep(1)'''
                else:
                    print("Invalid selection. Try again.")
            except Exception as e:
                print(str(e))
                print("Please enter a valid number.")

if __name__ == "__main__":
    main()