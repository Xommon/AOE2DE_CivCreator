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
import copy
from datetime import datetime
from math import ceil
from genieutils.tech import Tech, ResearchResourceCost, ResearchLocation
from genieutils.versions import Version

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
    with open(MOD_STRINGS, 'r+', encoding='utf-8') as file:
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
    name = name.lower()
    names = [name]

    final_ids = []

    # Try to depluralise the word
    if name[:-1] == 's':
        names.append(name[-1])
    if name[:-3] == 'ies':
        names.append(f'{name[-3]}y')
    if 'men' in name:
        names.append(name.replace('men', 'man'))

    for name_type in names:
        try:
            for i, unit in enumerate(DATA.civs[1].units):
                if unit.name.lower() == name_type.lower():
                    if i == 778:
                        continue
                    elif list_ids == True:
                        final_ids.append(i)
                    else:
                        return i
        except:
            # As a backup, search for name in the strings JSON file
            string_ids = []
            with open(ORIGINAL_STRINGS, 'r', encoding='utf-8') as file:
                get_unit_id_lines = file.readlines()
                for line in get_unit_id_lines:
                    if f'"{name_type.lower()}"' in line.lower():
                        match = re.match(r'\d+', line)
                        if match:
                            string_ids.append(match.group())

            for i, unit in enumerate(DATA.civs[1].units):
                try:
                    if str(unit.language_dll_name) in string_ids:
                        if i == 778:
                            continue
                        elif list_ids == True:
                            final_ids.append(i)
                        else:
                            return i
                except:
                    pass

    return list(set(final_ids))

def update_tech_tree_graphic(current_civ_name, tech_tree_id):
    # Load the JSON
    with open(rf'{MOD_FOLDER}/resources/_common/dat/civTechTrees.json', 'r', encoding="utf-8") as file:
        json_tree = json.load(file)

    # Collect disabled Node IDs from effect commands
    '''disabled_ids = set()
    for i, tech in enumerate(DATA.techs):
        if "Tech Tree" in tech.name:
            for cmd in DATA.effects[i].effect_commands:
                if cmd.type == 4:
                    disabled_ids.add(cmd.a)'''

    # Gather all unique entries across all civs by Node ID
    entry_bank = {}
    for civ in json_tree["civs"]:
        for key in ["civ_techs_buildings", "civ_techs_units", "civ_techs_researches"]:
            for entry in civ.get(key, []):
                node_id = entry.get("Node ID")
                if node_id is not None and node_id not in entry_bank:
                    entry_bank[node_id] = entry

    # Find the specific civ in the JSON tree
    selected_civ = next((civ for civ in json_tree["civs"] if civ.get("civ_id") == current_civ_name.upper()), None)

    # Match the disabled effect commands with entry bank
    entry_bank_disabled = {}
    for effect_command in DATA.effects[tech_tree_id].effect_commands:
        if effect_command.type == 102:
            # Search in entry_bank for entries with matching Trigger Tech ID
            for node_id, entry in entry_bank.items():
                if entry.get("Trigger Tech ID") == effect_command.d:
                    entry_bank_disabled[node_id] = entry

    print("Disabled entries:")
    for k, v in entry_bank_disabled.items():
        print(f"- Node ID {k}: {v.get('Name')}")




'''def get_unit_categories(name):
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
    return categories'''
        
def get_tech_id(name):
    # Search with internal_name
    for i, tech in enumerate(DATA.techs):
        if tech.name.lower() == name.lower():
            return i

    # As a backup, search for name elsewhere
    string_id = None
    with open(ORIGINAL_STRINGS, 'r', encoding='utf-8') as file:
        for line in file:
            if name.lower() in line.lower():
                string_id = re.sub(r'^\d+\s+', '', line)
                break

    if string_id:
        for i, tech in enumerate(DATA.techs):
            if tech.language_dll_name == string_id:
                return i

    return -1
        
def get_string(code):
    with open(ORIGINAL_STRINGS, 'r', encoding='utf-8') as original_file:
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
    with open(ORIGINAL_STRINGS, 'r', encoding='utf-8') as original_file:
        original_lines = original_file.readlines()
        for i, line in enumerate(original_lines):
            if line.startswith(f'{index} '):
                string_line = line

    # Find modded line if it exists
    with open(MOD_STRINGS, 'r+', encoding='utf-8') as mod_file:
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

def get_unit_line(unit_id):
    # Convert name to ID if needed
    if isinstance(unit_id, str):
        unit_id = get_unit_id(unit_id, False)

    # Step 1: Walk down to the base unit
    base_unit = None
    current_id = unit_id
    visited_ids = set()

    while True:
        unit = next((u for u in FOREST if u.get("Node ID") == current_id), None)
        if not unit or current_id in visited_ids:
            break

        visited_ids.add(current_id)
        link_id = unit.get("Link ID", -1)
        if link_id == -1:
            base_unit = unit
            break
        else:
            current_id = link_id

    if not base_unit:
        return []

    # Start the result list with the base unit's Node ID
    unit_line = [base_unit.get("Node ID")]

    # Step 2: Walk up from the base unit
    queue = [base_unit.get("Node ID")]
    while queue:
        current = queue.pop(0)
        for unit in FOREST:
            if unit.get("Link ID") == current:
                trigger_tech_id = unit.get("Trigger Tech ID", -1)
                if trigger_tech_id != -1:
                    node_id = unit.get("Node ID")
                    if node_id not in unit_line:
                        unit_line.append(node_id)
                        queue.append(node_id)

    return unit_line
    
def get_unit_line_ids(name):
    # Convert to unit index
    if str(name).isdigit():
        unit_index = int(name)
    else:
        unit_index = get_unit_id(name, False)

    base_id = DATA.civs[1].units[unit_index].base_id
    node_ids = []

    for unit in DATA.civs[1].units:
        if unit.base_id == base_id:
            trigger_tech_id = unit.get("Trigger Tech ID", -1)
            link_id = unit.get("Link ID", -1)

            if trigger_tech_id != -1 or link_id == -1:
                node_ids.append(unit.id)

    return node_ids

# Complete text
def make_completer(options_list):
    def completer(text, state):
        matches = [s for s in options_list if s.lower().startswith(text.lower())]
        return matches[state] if state < len(matches) else None
    return completer

# Create bonuses
def create_bonus(bonus_string_original, civ_id):
    def get_units_and_categories(string):
        # Split units into a list
        string = string.replace('and', ',')
        units = string.split(',')

        # Clean up the strings
        units = [unit.strip() for unit in units if unit.strip()]

        # Final output lists
        unit_ids = set()
        category_ids = set()

        def generate_variants(p):
            variants = set(p.lower())
            if p.endswith('ies'):
                variants.add(p[:-3] + 'y')
            if p.endswith('s') and not p.endswith('ss'):
                variants.add(p[:-1])
            if 'men' in p:
                variants.add(p.replace('men', 'man'))
            variants = list(variants)
            return variants

        for unit in units:
            found_category = False
            for variant in generate_variants(unit):
                if variant in UNIT_CATEGORIES:
                    for value in UNIT_CATEGORIES[variant]:
                        if 'C' in value:
                            category_ids.add(int(value[1:]))
                        elif 'U' in value:
                            unit_ids.add(int(value[1:]))
                    found_category = True
                    break

            # Only try get_unit_id if not matched as category
            if not found_category:
                for variant in generate_variants(unit):
                    new_units = get_unit_id(variant, True)
                    for new_unit in new_units:
                        unit_ids.add(new_unit)

        return ([x for x in unit_ids if x not in (-1, None)], [x for x in category_ids if x not in (-1, None)])

    def get_numbers(string, inverse=False):
        # Clean the string
        string = string.strip()

        # Determine if percent
        percent = '%' in string
        string = string.replace('%', '')

        # Determine if positive or negative
        negative = '-' in string
        negative = '+' not in string
        string = string.replace('-', '').replace('+', '')

        # Influence by inverse
        if inverse:
            negative = not inverse

        # Split into a list
        numbers = string.split('/')

        # Bonus numbers
        bonus_numbers = []

        # Convert to int or float
        for number in numbers:
            number = number.strip()
            if not number:
                continue

            # Check if the number is a percentage
            if percent:
                if negative:
                    number = float((100 - float(number)) / 100)
                else:
                    number = float(float(number) / 100 + 1)
            else:
                number = int(number)
                if negative:
                    number *= -1

            # Return the number
            bonus_numbers.append(number)

        return bonus_numbers

    # Get ages
    ages_dictionary = {'dark': 104, 'feudal': 101, 'castle': 102, 'imperial': 103}

    def get_ages(string):
        # Normalize string
        string = string.lower()
        result_ages = []

        # Check for specific age phrases
        if 'starting in the' in string:
            for key in ages_dictionary:
                if key in string:
                    result_ages.append(ages_dictionary[key])

        # Check for phrases like "in the dark/feudal/castle/imperial age"
        elif 'age' in string:
            for key in ages_dictionary:
                if key in string:
                    result_ages.append(ages_dictionary[key])

        # Remove duplicates while preserving order
        seen = set()
        result_ages = [age for age in result_ages if not (age in seen or seen.add(age))]

        return result_ages
    
    # Get techs
    def get_techs(string):
        # Split techs into a list
        string = string.replace('and', ',')
        techs = string.split(',')

        # Clean up the strings
        techs = [tech.strip() for tech in techs if tech.strip()]

        # Final output lists
        techs_ids = set()

        for tech_id in techs:
            if get_tech_id(tech_id) != -1:
                techs_ids.add(get_tech_id(tech_id))

        return techs_ids
    
    # Get resources
    def get_resources(string):
        resources_dictionary = {'food': 0, 'wood': 1, 'gold': 2, 'stone': 3}

        resources = []

        for key in resources_dictionary:
            if key in string:
                resources.append(resources_dictionary[key])

        return resources
    
    # Get tech cost
    def get_tech_cost(tech_id, gold_then_stone):
        tech_costs = [0, 0, 0, 0]

        for cost in DATA.techs[tech_id].resource_costs:
            if cost.flag == 1:
                tech_costs[cost.type] = cost.amount

        # Make the gold appear first, then stone second
        if gold_then_stone:
            temp_stone_cost = tech_costs[2]
            tech_costs[2] = tech_costs [3]
            tech_costs[3] = temp_stone_cost

        return tech_costs
    
    # Get stats
    stat_dictionary = {'an additional projectile': [107, 102], 'blast radius': [22], 'additional projectiles': [107, 102], 'carry': [14], 'hit points': [0], 'hp': [0], 'line of sight': [1, 23], 'los': [1, 23], 'move': [5], 'pierce armor': [8.0768], 'armor vs. cavalry archers': [8.7168], 'armor vs. elephants': [8.128], 'armor vs. infantry': [8.0256], 'armor vs. cavalry': [8.2048], 'armor vs. archers': [8.384], 'armor vs. ships': [8.4096], 'armor vs. siege': [8.512], 'armor vs. gunpowder': [8.5888], 'armor vs. spearmen': [8.6912], 'armor vs. eagles': [8.7424], 'armor vs. camels': [8.768], 'armor': [8.1024], 'attack': [9.1026, 9.77], 'range': [1, 12, 23], 'minimum range': [20], 'train': [101], 'work': [13], 'heal': [13]}
    def get_stats(string):
        final_stats = []
        for key in stat_dictionary:
            if key in string:
                final_stats.extend(stat_dictionary[key])

        return list(set(final_stats))

    # Prepare final techs and effects
    final_techs = [genieutils.tech.Tech(required_techs=(0, 0, 0, 0, 0, 0), research_locations=[ResearchLocation(0, 0, 0, 0)], resource_costs=(ResearchResourceCost(type=0, amount=0, flag=0), ResearchResourceCost(type=0, amount=0, flag=0), ResearchResourceCost(type=0, amount=0, flag=0)), required_tech_count=0, civ=civ_id + 1, full_tech_mode=0, research_location=-1, language_dll_name=7000, language_dll_description=8000, research_time=0, effect_id=-1, type=0, icon_id=-1, button_id=0, language_dll_help=107000, language_dll_tech_tree=157000, hot_key=-1, name=f'{DATA.civs[civ_id + 1].name.upper()}: {bonus_string_original.replace('*', '')}', repeatable=1)]
    final_effects = [genieutils.effect.Effect(name=f'{DATA.civs[civ_id + 1].name.upper()}: {bonus_string_original.replace('*', '')}', effect_commands=[])]

    # Cosmetic break
    if '*' in bonus_string_original:
        return final_techs, final_effects

    # Lowercase the bonus string
    bonus_string = bonus_string_original.lower()

    # Separate the bonus string into clauses
    bonus_strings = bonus_string.split(';')

    # Read each clause
    for bonus in bonus_strings:
        # Clean up the clause
        bonus = bonus.strip()

        # [Unit] work [Number] faster
        if ('work' in bonus or 'works' in bonus) and ('faster' in bonus or 'slower' in bonus):
            # Extract units, numbers, and ages
            bonus = bonus.replace('works', 'work')
            temp_bonus = bonus.replace('work', '|').replace('faster', '|').replace('slower', '|').split('|')
            bonus_numbers = get_numbers(temp_bonus[1], False)
            bonus_units, bonus_categories = get_units_and_categories(temp_bonus[0])
            bonus_ages = get_ages(bonus)

            # Create the techs
            for age in bonus_ages:
                if final_techs[0].required_techs == (0, 0, 0, 0, 0, 0):
                    final_techs[0].required_techs = (age, 0, 0, 0, 0, 0)
                    final_techs[0].required_tech_count = 1
                else:
                    final_techs.append(copy.deepcopy(final_techs[-1]))
                    final_techs[-1].required_techs = (age, 0, 0, 0, 0, 0)
                    final_techs[-1].required_tech_count = 1

            # Create the effect commands
            commands = []
            for number in bonus_numbers:
                # Create total list of effect commands
                for category_id in bonus_categories:
                    commands.append(genieutils.effect.EffectCommand(5 if isinstance(number, float) else 4, -1, category_id, 13, number))
                for unit_id in bonus_units:
                    commands.append(genieutils.effect.EffectCommand(5 if isinstance(number, float) else 4, unit_id, -1, 13, number))

            # Set the first effect as the base effect
            base_effect = copy.deepcopy(final_effects[0])

            # Assign effect commands to effects
            if len(bonus_ages) > 1:
                # Make the amount of techs match the effects
                while len(final_effects) < len(final_techs):
                    final_effects.append(copy.deepcopy(base_effect))

                per_age = int(ceil(len(commands) / len(final_effects)))
                command_index = 0

                # Add the effect commands to each effect
                for effect in final_effects:
                    for i in range(per_age):
                        if command_index < len(commands):
                            effect.effect_commands.append(commands[command_index])
                            command_index += 1
                        else:
                            break
            else:
                final_effects[0].effect_commands.extend(commands)

            # Attach the effects to the tech
            for i, tech in enumerate(final_techs):
                tech.effect_id = len(DATA.effects) + i

        # [Unit] cost [Number] [Resource]
        if 'cost' in bonus or 'costs' in bonus:
            bonus = bonus.replace('costs', 'cost')
            # Extract parts
            temp_bonus = bonus.replace('cost', '|').replace('more', '|').replace('less', '|').split('|')
            bonus_numbers = get_numbers(temp_bonus[1], False)
            bonus_resources = get_resources(temp_bonus[1])
            bonus_units, bonus_categories = get_units_and_categories(temp_bonus[0])
            bonus_techs = get_techs(temp_bonus[0])
            bonus_ages = get_ages(bonus)

            # Create the techs
            for age in bonus_ages:
                if final_techs[0].required_techs == (0, 0, 0, 0, 0, 0):
                    final_techs[0].required_techs = (age, 0, 0, 0, 0, 0)
                    final_techs[0].required_tech_count = 1
                else:
                    final_techs.append(copy.deepcopy(final_techs[-1]))
                    final_techs[-1].required_techs = (age, 0, 0, 0, 0, 0)
                    final_techs[-1].required_tech_count = 1

            # Breaks
            if len(bonus_resources) == 0:
                bonus_resources.extend([0, 1, 2, 3])

            # Create the effect commands
            commands = []
            for number in bonus_numbers:
                for resource in bonus_resources:
                    # Create total list of effect commands
                    for category_id in bonus_categories:
                        commands.append(genieutils.effect.EffectCommand(5 if isinstance(number, float) else 4, -1, category_id, 103, number))
                    for unit_id in bonus_units:
                        commands.append(genieutils.effect.EffectCommand(5 if isinstance(number, float) else 4, unit_id, -1, 103, number))
                    for tech_id in bonus_techs:
                        starting_resource_int = get_tech_cost(tech_id, False)[resource]
                        commands.append(genieutils.effect.EffectCommand(101, tech_id, resource, 0, int(starting_resource_int + number) if isinstance(number, int) else int(starting_resource_int * number)))
            
            commands = list(dict.fromkeys(copy.deepcopy(commands)))

            # Set the first effect as the base effect
            base_effect = copy.deepcopy(final_effects[0])

            # Assign effect commands to effects
            if len(bonus_ages) > 1:
                # Make the amount of techs match the effects
                while len(final_effects) < len(final_techs):
                    final_effects.append(copy.deepcopy(base_effect))

                per_age = int(ceil(len(commands) / len(final_effects)))
                command_index = 0

                # Add the effect commands to each effect
                for effect in final_effects:
                    for i in range(per_age):
                        if command_index < len(commands):
                            effect.effect_commands.append(commands[command_index])
                            command_index += 1
                        else:
                            break
            else:
                final_effects[0].effect_commands.extend(commands)

            # Attach the effects to the tech
            for i, tech in enumerate(final_techs):
                tech.effect_id = len(DATA.effects) + i

        # Change attribute
        temp_bonus_words = bonus.split(' ')
        temp_bonus = bonus
        for word in temp_bonus_words:
            if len(get_numbers(bonus)) > 0:
                temp_bonus = bonus.split(word)

                bonus_units, bonus_categories = get_units_and_categories(temp_bonus[0])
        
        ## Infantry +2 attack
        ## Infantry and Cavalry +50 hit points
        '''temp_bonus_words = bonus.split(' ')
        required_number = False
        required_unitcategorytechs = False
        required_stat = False
        for word in temp_bonus_words:
            # Unit/Category/Tech
            if not required_unitcategorytechs:
                t_units, t_categories = get_units_and_categories(word)
                t_techs = get_techs(word)
                required_unitcategorytechs = len(t_units) + len(t_categories) + len(t_techs) > 0
            # Number
            if not required_number:
                required_number = len(get_numbers(word, False)) > 0
            # Stat
            if not required_stat:
                required_stat = len(get_stats(word)) > 0

        if required_number and required_unitcategorytechs and required_stat:
            # Extract parts
            bonus_ages = get_ages(bonus)
            for word in temp_bonus_words:

                bonus_numbers = get_numbers(temp_bonus[1], False)
                bonus_resources = get_resources(temp_bonus[1])
                bonus_units, bonus_categories = get_units_and_categories(temp_bonus[0])
                bonus_techs = get_techs(temp_bonus[0])
                bonus_ages = get_ages(bonus)0

            # Create the techs
            for age in bonus_ages:
                if final_techs[0].required_techs == (0, 0, 0, 0, 0, 0):
                    final_techs[0].required_techs = (age, 0, 0, 0, 0, 0)
                    final_techs[0].required_tech_count = 1
                else:
                    final_techs.append(copy.deepcopy(final_techs[-1]))
                    final_techs[-1].required_techs = (age, 0, 0, 0, 0, 0)
                    final_techs[-1].required_tech_count = 1

            # Breaks
            if len(bonus_resources) == 0:
                bonus_resources.extend([0, 1, 2, 3])

            # Create the effect commands
            commands = []
            for number in bonus_numbers:
                for resource in bonus_resources:
                    # Create total list of effect commands
                    for category_id in bonus_categories:
                        commands.append(genieutils.effect.EffectCommand(5 if isinstance(number, float) else 4, -1, category_id, 103, number))
                    for unit_id in bonus_units:
                        commands.append(genieutils.effect.EffectCommand(5 if isinstance(number, float) else 4, unit_id, -1, 103, number))
                    for tech_id in bonus_techs:
                        starting_resource_int = get_tech_cost(tech_id, False)[resource]
                        commands.append(genieutils.effect.EffectCommand(101, tech_id, resource, 0, int(starting_resource_int + number) if isinstance(number, int) else int(starting_resource_int * number)))
            
            commands = list(dict.fromkeys(copy.deepcopy(commands)))

            # Set the first effect as the base effect
            base_effect = copy.deepcopy(final_effects[0])

            # Assign effect commands to effects
            if len(bonus_ages) > 1:
                # Make the amount of techs match the effects
                while len(final_effects) < len(final_techs):
                    final_effects.append(copy.deepcopy(base_effect))

                per_age = int(ceil(len(commands) / len(final_effects)))
                command_index = 0

                # Add the effect commands to each effect
                for effect in final_effects:
                    for i in range(per_age):
                        if command_index < len(commands):
                            effect.effect_commands.append(commands[command_index])
                            command_index += 1
                        else:
                            break
            else:
                final_effects[0].effect_commands.extend(commands)

            # Attach the effects to the tech
            for i, tech in enumerate(final_techs):
                tech.effect_id = len(DATA.effects) + i'''

        if True:
            pass

    # Return the final techs and final effects
    return final_techs, final_effects

'''def create_bonus(bonus_string_original, civ_id):
    # Clean up string and check for cosmetic
    bonus_string_original = bonus_string_original.strip()
    cosmetic = bonus_string_original.startswith('*')
    if cosmetic:
        bonus_string_original = bonus_string_original[1:].strip()

    # Create the tech and effect, set the civilisation and names
    final_techs = [genieutils.tech.Tech(required_techs=(0, 0, 0, 0, 0, 0), resource_costs=(ResearchResourceCost(type=0, amount=0, flag=0), ResearchResourceCost(type=0, amount=0, flag=0), ResearchResourceCost(type=0, amount=0, flag=0)), required_tech_count=0, civ=civ_id + 1, full_tech_mode=0, research_location=-1, language_dll_name=7000, language_dll_description=8000, research_time=0, effect_id=-1, type=0, icon_id=-1, button_id=0, language_dll_help=107000, language_dll_tech_tree=157000, hot_key=-1, name=f'{DATA.civs[civ_id + 1].name.upper()}: {bonus_string_original}', repeatable=1)]
    final_effects = [genieutils.effect.Effect(name=f'{DATA.civs[civ_id + 1].name.upper()}: {bonus_string_original}', effect_commands=[])]

    # Check for cosmetic bonus
    if cosmetic:
        return final_techs, final_effects
    
    # Lowercase the bonus string
    bonus_string = bonus_string_original.lower()

    # Split the bonus string into words
    words = bonus_string.lower().split()

    # Stat dictionary
    stat_dictionary = {'an additional projectile': ['N1', 'S107', 'S102'], 'blast radius': 'S22', 'additional projectiles': ['S107', 'S102'], 'carry': ['S14'], 'hit points': ['S0'], 'hp': ['S0'], 'line of sight': ['S1', 'S23'], 'los': ['S1', 'S23'], 'move': ['S5'], 'pierce armor': ['S8.0768'], 'armor vs. cavalry archers': ['S8.7168'], 'armor vs. elephants': ['S8.128'], 'armor vs. infantry': ['S8.0256'], 'armor vs. cavalry': ['S8.2048'], 'armor vs. archers': ['S8.384'], 'armor vs. ships': ['S8.4096'], 'armor vs. siege': ['S8.512'], 'armor vs. gunpowder': ['S8.5888'], 'armor vs. spearmen': ['S8.6912'], 'armor vs. eagles': ['S8.7424'], 'armor vs. camels': ['S8.768'], 'armor': ['S8.1024'], 'attack': ['S9.1026', 'S9.770'], 'range': ['S1', 'S12', 'S23'], 'minimum range': ['S20'], 'train': ['S101'], 'work': ['S13'], 'heal': ['S13']}

    # Resource dictionary
    resource_dictionary = {'food': ['R0'], 'wood': ['R1'], 'gold': ['R3'], 'stone': ['R2']}

    # Trigger dictionary
    trigger_directionary = {'more effective': 'Xmore effective',
                            'available one age earlier': 'Xone age earlier',
                            'free relic': 'Xfree relic',
                            'do not need houses': 'Xdo not need houses',
                            'does not need houses': 'Xdo not need houses',
                            'start with': 'Xstart with',
                            }

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

    # Add extra words to clarify meaning
    for i, word in enumerate(words):
        if str(word).endswith('-'):
            if 'upgrade' in bonus_string or 'upgrades' in bonus_string:
                words[i] = word + 'line upgrades'

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

        # === Trigger Phrases ===
        phrase = ''
        best_match = ''
        best_len = 0
        for j in range(i, len(words)):
            phrase = f"{phrase} {words[j]}".strip()
            if phrase in trigger_directionary:
                best_match = phrase
                best_len = j - i + 1
        if best_match:
            bonus_items.append(trigger_directionary[best_match])
            i += best_len
            continue

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

    # Flatten bonus items into one array
    flat_bonus_items = []
    stack = list(bonus_items)
    while stack:
        item = stack.pop(0)
        if isinstance(item, list):
            stack = list(item) + stack
        else:
            flat_bonus_items.append(item)
    bonus_items = flat_bonus_items

    # DEBUG: Print bonus items
    print(f'{colour(Fore.BLUE, (bonus_string_original + ':'))} {bonus_items}')

    # Create bonus lines
    class Bonus_Line:
        def __init__(
            self,
            category=-1,
            unit=-1,
            number=-1,
            resource=-1,
            stat=-1,
            substat=-1,
            age=-1,
            trigger=''
        ):
            self.category = category
            self.unit = unit
            self.number = number
            self.resource = resource
            self.stat = stat
            self.substat = substat
            self.age = age
            self.trigger = trigger

    # Convert bonus items into bonus lines
    bonus_lines = []
    selected_lines = 0

    for item in bonus_items:
        # Category
        if item[0] == 'C':
            bonus_lines.append(Bonus_Line(category=int(item[1:])))
            selected_lines += 1

        # Unit
        elif item[0] == 'U':
            bonus_lines.append(Bonus_Line(unit=int(item[1:])))
            selected_lines += 1

        # Age
        elif item[0] == 'A':
            # Choose when the age is set
            start_index = 0
            for i, line in enumerate(bonus_lines):
                if line.category == bonus_lines[-1].category and line.unit == bonus_lines[-1].unit and line.age == -1:
                    start_index = i
                    break

            # Set the age for the first line
            bonus_lines[start_index].age = int(item[1:])

        # Stat
        elif item.startswith('S'):
            # Parse stat and substat
            if '.' in item:
                stat = int(item[1:].split('.')[0])
                substat = int(item[1:].split('.')[1])
            else:
                stat = int(item[1:])
                substat = -1

            if not bonus_lines:
                # No lines yet: create a new one
                bonus_lines.append(Bonus_Line(stat=stat, substat=substat))
                selected_lines = 1

            else:
                # Grab the recent group
                recent = bonus_lines[-selected_lines:]

                # Choose when the stat is set
                start_index = 0
                for i, line in enumerate(bonus_lines):
                    if line.category == bonus_lines[-1].category and line.unit == bonus_lines[-1].unit and line.stat == -1:
                        start_index = i
                        break

                # Set the stat for the first line
                bonus_lines[start_index].stat = int(item[1:])

                any_unset = any(line.stat == -1 for line in recent)

                if any_unset:
                    # Just set stat/substat on all
                    for line in recent:
                        line.stat = stat
                        line.substat = substat
                else:
                    # Clone each with the new stat
                    clones = []
                    for line in recent:
                        new_line = Bonus_Line(
                            category=line.category,
                            unit=line.unit,
                            number=line.number,
                            resource=line.resource,
                            stat=stat,
                            substat=substat,
                            age=line.age,
                            trigger=line.trigger
                        )
                        clones.append(new_line)
                    bonus_lines.extend(clones)

        # Unified handler for Resource, Number, Age, and Trigger
        elif item[0] in {'R', 'N', 'A', 'X'}:
            kind = item[0]
            raw = item[1:]

            # Parse the value
            if kind == 'R':
                value = int(raw)
                attr = 'resource'
                default = -1
            elif kind == 'N':
                value = float(raw) if '.' in raw else int(raw)
                attr = 'number'
                default = -1
            elif kind == 'A':
                value = int(raw)
                attr = 'age'
                default = -1
            elif kind == 'X':
                value = raw
                attr = 'trigger'
                default = ''

            # No previous lines: create new
            if not bonus_lines:
                kwargs = {attr: value}
                bonus_lines.append(Bonus_Line(**kwargs))
                selected_lines = 1
            else:
                recent = bonus_lines[-selected_lines:]
                any_unset = any(getattr(line, attr) == default for line in recent)
                if any_unset:
                    for line in recent:
                        setattr(line, attr, value)
                else:
                    clones = []
                    for line in recent:
                        new_line = Bonus_Line(
                            category=line.category,
                            unit=line.unit,
                            number=line.number,
                            resource=line.resource,
                            stat=line.stat,
                            substat=line.substat,
                            age=line.age,
                            trigger=line.trigger
                        )
                        setattr(new_line, attr, value)
                        clones.append(new_line)
                    bonus_lines.extend(clones)

    # DEBUG: Print bonus lines
    for b in bonus_lines:
        print(
            f"Bonus_Line(category={b.category}, "
            f"unit={b.unit}, "
            f"number={b.number}, "
            f"resource={b.resource}, "
            f"stat={b.stat}, "
            f"substat={b.substat}, "
            f"age={b.age}, "
            f"trigger='{b.trigger}')"
        )

    # Turn bonus lines into techs and effects
    for bonus_line in bonus_lines:
        # Age
        if bonus_line.age != -1:
            if final_techs[-1].required_techs != (0, 0, 0, 0, 0, 0):
                # Create a new tech for the age
                final_techs.append(copy.deepcopy(final_techs[-1]))

            # Add the age to the tech
            final_techs[-1].required_techs = (bonus_line.age, 0, 0, 0, 0, 0)
            final_techs[-1].required_tech_count = 1

        # Triggers
        if bonus_line.trigger == 'do not need houses' or bonus_line.trigger == 'does not need houses':
            final_effects[0].effect_commands.append(genieutils.effect.EffectCommand(1, 4, 1, -1, 2000))
            final_effects[0].effect_commands.append(genieutils.effect.EffectCommand(2, 70, 0, -1, 0))
        elif bonus_line.trigger == 'start with':
            final_effects[0].effect_commands.append(genieutils.effect.EffectCommand(1, bonus_line.resource + 91, 1, -1, bonus_line.number))

        # General edit stat of unit
        else:
            if isinstance(bonus_line.number, float):
                final_effects[0].effect_commands.append(genieutils.effect.EffectCommand(5, bonus_line.unit, bonus_line.category, bonus_line.stat, bonus_line.number))
            elif isinstance(bonus_line.number, int):
                final_effects[0].effect_commands.append(genieutils.effect.EffectCommand(4, bonus_line.unit, bonus_line.category, bonus_line.stat, bonus_line.number))
            pass

    # Pass on the tech and the effect
    return final_techs, final_effects
'''
'''def toggle_unit(unit_index, mode, tech_tree_index, selected_civ_name):
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
        DATA.effects[tech_tree_index].effect_commands.append(genieutils.effect.EffectCommand(102, 0, 0, 0, tech_index))'''

def open_mod(mod_folder):
    with_real_progress(lambda progress: load_dat(progress, rf'{mod_folder}/resources/_common/dat/empires2_x2_p1.dat'), 'Loading Mod', total_steps=100)
    global DATA
    DATA = DatFile.parse(rf'{mod_folder}/resources/_common/dat/empires2_x2_p1.dat')
    global MOD_STRINGS
    MOD_STRINGS = rf'{mod_folder}/resources/en/strings/key-value/key-value-modded-strings-utf8.txt'
    global ORIGINAL_STRINGS
    ORIGINAL_STRINGS = rf'{mod_folder}/resources/en/strings/key-value/key-value-strings-utf8.txt'
    global MOD_FOLDER
    MOD_FOLDER = mod_folder.replace('\\\\', '/').rstrip('/')
    global MOD_NAME
    MOD_NAME = mod_folder.split('\\')[-1]

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
    with open(f'{MOD_NAME}/{MOD_NAME.split('/')[-1]}.pkl', 'rb') as file:
        while True:
            try:
                units = pickle.load(file)
                ARCHITECTURE_SETS.append(units)
            except EOFError:
                break

    # Define the base unit categories
    global UNIT_CATEGORIES
    UNIT_CATEGORIES = {}

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
            unit_line = get_unit_line(unit.id)
            if unit.id in unit_line and unit.creatable.train_location_id != 82:
                UNIT_CATEGORIES.setdefault(get_unit_name(unit_line[0]) + '-line', []).append(f'U{unit.id}')
                UNIT_CATEGORIES.setdefault(get_unit_name(unit_line[0]) + '-', []).append(f'U{unit.id}')

            # Add the unit-line upgrades
            unit_line_ids = get_unit_line_ids(unit_line[:-1])
            tech_ids = {
                unit.get("Trigger Tech ID")
                for unit in FOREST
                if unit.get("Node ID") in unit_line_ids and unit.get("Trigger Tech ID") is not None
            }

            # Clean the list of blanks
            try:
                tech_ids = [f'T{x}' for x in tech_ids if x != -1]

                if tech_ids:
                    TECH_CATEGORIES.setdefault(f"{unit_line}line upgrades", []).extend(tech_ids)
            except:
                pass

            # Elephants and Camels
            name = get_unit_name(unit.id).lower()
            if 'elephant' in name:
                UNIT_CATEGORIES.setdefault('elephant units', []).append(f'U{unit.id}')
            if 'camel' in name:
                UNIT_CATEGORIES.setdefault('camel units', []).append(f'U{unit.id}')
        except Exception as e:
            #print(str(e))
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

    # Add manual items
    new_entries = {
        'demolition ships': ['U1104', 'U527', 'U528'],
        'fortified church': 'U1806',
        "foot archers": ['C0', 'U-7', 'U-6', 'U-1155'],
        "skirmishers": ['U7', 'U6', 'U1155'],
        "mounted archers": ['C36'],
        "mounted": ['C36', 'C12', 'C23'],
        "trade units": ['C2', 'C19'],
        "infantry": ['C6'],
        "cavalry": ['C12'],
        "light horseman": ['C12'],
        "heavy cavalry": ['C12'],
        "warships": ['C22'],
        "gunpowder": ['C44', 'C23'],
        "siege": ['C13'],
        'villagers': ['C4'],
        'camel units': ['U282', 'U556', 'U1263', f'U{get_unit_id('Naasiri', False)}', f'U{get_unit_id('Elite Naasiri', False)}'],
        'mule carts': ['U1808'],
        'military units': ['C0', 'C55', 'C35', 'C6', 'C54', 'C13', 'C51', 'C36', 'C12'],
        'shock infantry' : ['U751', 'U752', 'U753', 'U1901', 'U1903', 'U1974', 'U1976']
    }

    for k, v in new_entries.items():
        if k in UNIT_CATEGORIES:
            old = UNIT_CATEGORIES[k]
            if isinstance(old, list):
                if isinstance(v, list):
                    UNIT_CATEGORIES[k] = old + v
                else:
                    UNIT_CATEGORIES[k] = old + [v]
            else:
                if isinstance(v, list):
                    UNIT_CATEGORIES[k] = [old] + v
                else:
                    UNIT_CATEGORIES[k] = [old, v]
        else:
            UNIT_CATEGORIES[k] = v

    # Send the unit categories to the LLM
    '''with open(f'{os.path.dirname(os.path.abspath(__file__))}/Modelfile', 'r+', encoding='utf-8') as LLM_file:
        # Read all lines
        LLM_lines = LLM_file.readlines()
        if len(LLM_lines) > 1:
            # Modify the second-to-last line
            LLM_lines[-2] = f'{LLM_lines[-2].strip()} {UNIT_CATEGORIES}\n'

            # Go back to the start
            LLM_file.seek(0)
            # Write back all lines
            LLM_file.writelines(LLM_lines)
            # Truncate to remove any leftover content
            LLM_file.truncate()'''
    
    # Load all languages
    global ALL_LANGUAGES
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
    
    # Assemble all castle units
    global ALL_CASTLE_UNITS
    ALL_CASTLE_UNITS = []
    for i, unit in enumerate(DATA.civs[1].units):
        try:
            for location in unit.creatable.train_locations:
                if location.unit_id == 82 and location.button_id == 1:
                    # Check if there is a regular version and an elite version
                    if 'elite' not in get_unit_name(i).lower() and get_unit_id(f'elite {get_unit_name(i)}', False) != None:
                        ALL_CASTLE_UNITS.append(get_unit_name(i))
                        break
        except:
            pass

    # DEBUG: Print dictionary
    #for key, value in UNIT_CATEGORIES.items():
    #    print(f'{key}: {value}')

    # Tell the user that the mod was loaded
    print('Mod loaded!')
    #update_tech_tree_graphic('Britons', 254)
    #print(get_unit_line(473))

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
    import platform
    if _mod_folder == '':
        local_mods_folder = input("\nEnter local mods folder location: ")
        if local_mods_folder == '':
            if platform.system() == 'Windows':
                local_mods_folder = r'C:/Users/mquen/Games/Age of Empires 2 DE/76561198021486964/mods/local'
            elif platform.system() == 'Linux':
                local_mods_folder = r'/home/xommon/snap/steam/common/.local/share/Steam/steamapps/compatdata/813780/pfx/drive_c/users/steamuser/Games/Age of Empires 2 DE/76561198021486964/mods/local'
    else:
        local_mods_folder = _mod_folder

    # Get original AoE2DE folder
    if _aoe2_folder == '':
        aoe2_folder = input("Select original \"AoE2DE\" folder location: ")
        if aoe2_folder == '':
            if platform.system() == 'Windows':
                aoe2_folder = r'D:/SteamLibrary/steamapps/common/AoE2DE'
            elif platform.system() == 'Linux':
                aoe2_folder = r'/home/xommon/snap/steam/common/.local/share/Steam/steamapps/common/AoE2DE'
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

    # Files or folders to copy
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

    # Copy each file or folder
    for item in files_to_copy:
        source_path = os.path.join(aoe2_folder, item)
        destination_path = os.path.join(MOD_FOLDER, item)

        # Make sure the destination directory exists
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)

        if os.path.isfile(source_path):
            shutil.copy(source_path, destination_path)
        elif os.path.isdir(source_path):
            shutil.copytree(source_path, destination_path, dirs_exist_ok=True)

    # Define original strings
    global ORIGINAL_STRINGS
    ORIGINAL_STRINGS = rf'{mod_folder}/resources/en/strings/key-value/key-value-strings-utf8.txt'

    # Open .dat file
    with_real_progress(lambda progress: load_dat(progress, rf'{mod_folder}/resources/_common/dat/empires2_x2_p1.dat'), 'Creating Mod', total_steps=100)

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
    for civ_id, civ in enumerate(DATA.civs[1:]):
        for sound_id in sound_ids:
            # Get the amount of sound items to add
            sound_count = int(sound_ids[sound_id][-1])

            # Add the sound items to the sound
            language_presets = {1: "English", 2: "French", 3: "Gothic", 4: "German", 5: "Japanese", 6: "Mandarin", 7: "Latin", 8: "Persian", 9: "Arabic", 10: "Turkish", 11: "Norse", 12: "Mongolian", 13: "Gaelic", 14: "Spanish", 15: "Yucatec", 16: "Kaqchikel", 17: "Mongolian", 18: "Korean", 19: "Latin", 20: "Hindustani", 21: "Quechua", 22: "Hungarian", 23: "Russian", 24: "Portuguese", 25: "Amharic", 26: "Maninka", 27: "Taqbaylit", 28: "Khmer", 29: "Malaysian", 30: "Burmese", 31: "Vietnamese", 32: "Bulgarian", 33: "Chagatai", 34: "Cuman", 35: "Lithuanian", 36: "Burgundian", 37: "Sicilian", 38: "Polish", 39: "Czech", 40: "Tamil", 41: "Bengali", 42: "Gujarati", 43: "Vulgar Latin", 44: "Armenian", 45: "Georgian", 49: "Mandarin", 50: "Cantonese", 51: "Mandarin", 52: "Mandarin", 53: "Mongolian"}
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
    '''with open(ORIGINAL_STRINGS, 'r+') as file:
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
        file.truncate()      # Remove any extra content after the new end'''

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

    # Copy and filter original strings
    global MOD_STRINGS
    MOD_STRINGS = rf'{local_mods_folder}/{mod_name}/resources/en/strings/key-value/key-value-modded-strings-utf8.txt'
    original_strings = rf'{local_mods_folder}/{mod_name}/resources/en/strings/key-value/key-value-strings-utf8.txt'

    # Convert the lines with codes into a dictionary
    line_dictionary = {}
    with open(original_strings, 'r', encoding='utf-8') as original_file:
        original_strings_list = original_file.readlines()
        for line in original_strings_list:
            match = re.match(r'^(\d+)', line)
            if match:
                key = int(match.group(1))
                line_dictionary[key] = line

    # Write modded strings based on filter conditions
    with open(MOD_STRINGS, 'w+', encoding='utf-8') as modded_file:
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
    with open(MOD_STRINGS, 'r+', encoding='utf-8') as modded_file:
        modded_strings = modded_file.readlines()
        modded_file.seek(0)  # rewind to start
        for line in modded_strings:
            line = line.replace(r'• Can build Caravanserai in Imperial Age\n', '')
            modded_file.write(line)
        modded_file.truncate()

    # Make the Caravanserai potentially available to all civs
    DATA.techs[518].civ = -1
    DATA.techs[552].effect_id = -1
    DATA.techs[552].name = 'Caravanserai (DISABLED)'
    for effect in [effect for effect in DATA.effects if 'tech tree' in effect.name.lower()]:
        if 'persians' not in effect.name.lower() and 'hindustanis' not in effect.name.lower():
            effect.effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 518))

    # Make the Winged Hussar potentially available to all civs
    DATA.techs[786].required_techs = (103, 254, -1, -1, -1, -1)
    DATA.techs[786].required_tech_count = 2
    for tech_id in [788, 789, 791]:
        DATA.techs[tech_id].effect_id = -1

    # Make other unique units potentially available to all civs
    '''tech_tree_indexes = [254, 258, 259, 262, 255, 257, 256, 260, 261, 263, 275, 277, 276, 446, 447, 449, 448, 504, 20, 1, 3, 5, 7, 31, 28, 42, 27, 646, 648, 650, 652, 706, 708, 710, 712, 782, 784, 801, 803, 808, 840, 842, 890, 923, 927, 1101, 1107, 1129, 1030, 1031, 1028, 986, 988]
    unique_techs_indexes = [521, 858, 655, 598, 599, 528, 992, 1037, 522, 773, 885, 1075, 272, 447, 448, 948, 84, 703, 787, 1005, 1065, 790, 842, 843, 526]
    excluded_civs = ['spartans', 'achaemenids', 'athenians']

    for tech_id in unique_techs_indexes:
        tech = DATA.techs[tech_id]
        original_civ = tech.civ

        for i, civ in enumerate(DATA.civs):
            # Skip Gaia and Chronicles civs
            if i == 0 or civ.name.lower() in excluded_civs:
                continue

            # Adjust civ index for tech_tree_indexes lookup
            adjusted_index = i - 1 if i - 1 < 45 else i - 4

            if adjusted_index < 0 or adjusted_index >= len(tech_tree_indexes):
                print(f"Warning: adjusted_index {adjusted_index} out of bounds for civ {civ.name}")
                continue

            # Only disable tech for civs that are not the original owner
            if i != original_civ:
                tech_tree_id = tech_tree_indexes[adjusted_index]
                effect_id = DATA.techs[tech_tree_id].effect_id

                DATA.effects[effect_id].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, tech_id))

    # After assigning disable commands, make the tech non-unique
    tech.civ = -1'''

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
                ("type_50", "attack_graphic_2"),
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

    # Give the Berbers the African graphics
    for i, unit in enumerate(DATA.civs[27].units):
        try:
            if 'ORIE' in DATA.graphics[unit.standing_graphic[0]].name:
                unit.standing_graphic = DATA.civs[26].units[i].standing_graphic
            if 'ORIE' in DATA.graphics[unit.dying_graphic].name:
                unit.dying_graphic = DATA.civs[26].units[i].dying_graphic
        except:
            pass

    # Split the architecture sets for West Africans
    for civ in DATA.civs:
        if civ.name not in ['Malians', 'Ethiopians', 'Berbers']:
            continue

        if civ.name == 'Berbers':
            # For Berbers: replace Age3 and Age4 with Age2
            target_ages = ['Age3', 'Age4']
            replacement_age = 'Age2'
        else:
            # For Malians/Ethiopians: replace Age2 with Age3
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

            if 'AFRI' not in current_standing_name or not age_pattern.search(current_standing_name):
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


    # Enable the pasture for Mongols, Berbers, Huns, and Cumans
    DATA.techs[1008].civ = -1
    DATA.techs[1014].civ = -1
    DATA.techs[1013].civ = -1
    DATA.techs[1012].civ = -1
    for effect in [effect_ for effect_ in DATA.effects if "tech tree" in effect_.name.lower()]:
        name = effect.name.lower()
        if any(group in name for group in ['mongols', 'berbers', 'huns', 'cumans']):
            # Disable farms and farm upgrades
            #effect.effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 216))
            effect.effect_commands.append(genieutils.effect.EffectCommand(3, 50, 1889, -1, -1))
            effect.effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 12))
            effect.effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 13))
            effect.effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 14))
        else:
            # Disable pasture and pasture upgrades
            effect.effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 1008))
            effect.effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 1012))
            effect.effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 1013))
            effect.effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 1014))

    # Write the architecture sets to a file
    with open(f'{MOD_FOLDER}/{mod_name}.pkl', 'wb') as file:
        for civ in DATA.civs:
            if civ.name != 'Gaia' and civ.name != 'Spartans' and civ.name != 'Athenians' and civ.name != 'Achaemenids':
                pickle.dump(civ.units, file)

    # Set the Dock selection sound to the Port selection sound
    '''for civ in DATA.civs:
        for unit_id in [45, 47, 51, 133, 805, 806, 807, 808, 2120, 2121, 2122, 2144, 2145, 2146, 2173]:
            civ.units[unit_id].selection_sound = 708'''

    # Remove the Dragon Ship upgrade for the Chinese
    DATA.techs[1010].effect_id = -1
    for i, ec in enumerate(DATA.effects[257].effect_commands):
        if ec.type == 102 and ec.d == 246:
            DATA.effects[257].effect_commands.pop(i)
            break

    # Create the Canoe, War Canoe, and Elite War Canoe units, techs, and effects
    for civ in DATA.civs:
        # Canoe
        canoe_id = len(civ.units)
        canoe = copy.deepcopy(DATA.civs[1].units[778])
        canoe.creatable.train_locations[0].unit_id = 45
        canoe.creatable.train_locations[0].button_id = 4
        canoe.type_50.attacks[0].amount = 8
        canoe.type_50.reload_time = 2
        canoe.type_50.displayed_reload_time = 2
        canoe.line_of_sight = 7
        canoe.bird.search_radius = 7
        civ.units.append(canoe)

        # War Canoe
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
        war_canoe.type_50.max_range = 7
        war_canoe.type_50.displayed_range = 7
        war_canoe.line_of_sight = 9
        war_canoe.bird.search_radius = 9
        war_canoe.type_50.attacks[2].amount = 8
        war_canoe.type_50.displayed_attack = 8
        war_canoe.hit_points = 90
        war_canoe.type_50.attacks[0].amount = 10
        war_canoe.type_50.reload_time = 2
        war_canoe.type_50.displayed_reload_time = 2
        civ.units.append(war_canoe)

        # Elite War Canoe
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
        elite_war_canoe.type_50.max_range = 9
        elite_war_canoe.type_50.displayed_range = 9
        elite_war_canoe.line_of_sight = 11
        elite_war_canoe.bird.search_radius = 11
        elite_war_canoe.type_50.attacks[2].amount = 9
        elite_war_canoe.type_50.displayed_attack = 9
        elite_war_canoe.creatable.total_projectiles = 3
        elite_war_canoe.creatable.max_total_projectiles = 3
        elite_war_canoe.hit_points = 110
        elite_war_canoe.type_50.attacks[0].amount = 12
        elite_war_canoe.type_50.reload_time = 2
        elite_war_canoe.type_50.displayed_reload_time = 2
        civ.units.append(elite_war_canoe)

        # Naasiri
        naasiri = copy.deepcopy(DATA.civs[1].units[2327])
        change_string(94000, 'Naasiri')
        change_string(95000, 'Create Naasiri')
        naasiri.language_dll_name = 94000
        naasiri.language_dll_creation = 95000
        naasiri.name = 'Naasiri'
        naasiri.creatable.train_locations[0].unit_id = 82
        naasiri.creatable.train_locations[0].button_id = 1
        naasiri.creatable.train_locations[0].train_time = 24
        naasiri.type_50.attacks[0].amount = 7
        naasiri.type_50.displayed_attack = 7
        naasiri.creatable.train_time = 22
        civ.units.append(naasiri)

        # Elite Naasiri
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

        # Elephant Gunner
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
        elephant_gunner.creatable.train_time = 28
        elephant_gunner.creatable.resource_costs = (ResourceCost(type=0, amount=80, flag=1), ResourceCost(type=3, amount=100, flag=1), ResourceCost(type=4, amount=1, flag=0))
        elephant_gunner.type_50.projectile_unit_id = 380
        civ.units.append(elephant_gunner)

        # Elite Elephant Gunner
        elite_elephant_gunner = copy.deepcopy(elephant_gunner)
        change_string(100000, 'Elite Elephant Gunner')
        change_string(101000, 'Create Elite Elephant Gunner')
        elite_elephant_gunner.language_dll_name = 100000
        elite_elephant_gunner.language_dll_creation = 101000
        elite_elephant_gunner.name = 'Elite Elephant Gunner'
        elite_elephant_gunner.type_50.attacks[1].amount = 21
        elite_elephant_gunner.type_50.displayed_attack = 21
        elite_elephant_gunner.hit_points = 250
        civ.units.append(elite_elephant_gunner)

        # Flamethrower
        flamethrower = copy.deepcopy(DATA.civs[1].units[188])
        flamethrower.creatable.train_locations[0].unit_id = 82
        flamethrower.creatable.train_locations[0].button_id = 1
        flamethrower.type_50.attacks[1].amount = 6
        flamethrower.type_50.displayed_attack = 6
        civ.units.append(flamethrower)

        # Elite Flamethrower
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

        # Weichafe
        weichafe = copy.deepcopy(DATA.civs[1].units[2320])
        change_string(104000, 'Weichafe')
        change_string(105000, 'Create Weichafe')
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
        weichafe.name = 'Weichafe'
        civ.units.append(weichafe)

        # Elite Weichafe
        elite_weichafe = copy.deepcopy(weichafe)
        change_string(106000, 'Elite Weichafe')
        change_string(107000, 'Create Elite Weichafe')
        elite_weichafe.language_dll_name = 106000
        elite_weichafe.language_dll_creation = 107000
        elite_weichafe.class_ = 0
        elite_weichafe.type_50.attacks[0].amount = 5
        elite_weichafe.type_50.displayed_attack = 5
        elite_weichafe.type_50.max_range = 5
        elite_weichafe.type_50.displayed_range = 5
        elite_weichafe.line_of_sight = 7
        elite_weichafe.bird.search_radius = 7
        elite_weichafe.name = 'Elite Weichafe'
        civ.units.append(elite_weichafe)

    # Set civilisations to canoe docks by disabling all other warships
    for effect_id in [447, 489, 3, 648, 42, 710, 448, 227, 708, 652, 646]:
        # Disable the warships
        for tech_id in [604, 243, 246, 605, 244, 37, 376]:
            DATA.effects[effect_id].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, float(tech_id)))

        # Swap galley-line for canoe-line
        DATA.effects[effect_id].effect_commands.append(genieutils.effect.EffectCommand(3, 539 , canoe_id, -1, -1))
        DATA.effects[effect_id].effect_commands.append(genieutils.effect.EffectCommand(3, 21 , canoe_id+1, -1, -1))
        DATA.effects[effect_id].effect_commands.append(genieutils.effect.EffectCommand(3, 442 , canoe_id+2, -1, -1))

        # Allow every canoe civ to train the Elite War Canoe
        for i, ec in enumerate(DATA.effects[effect_id].effect_commands):
            if ec.type == 102 and ec.d == 35:
                DATA.effects[effect_id].effect_commands.pop(i)

    # Enable gun canoes for civs with canoes and hand cannoneers
    #DATA.techs.append(copy.deepcopy(DATA.techs[1250]))
    #DATA.techs[-1].name = 'Gun Canoe'
    #DATA.effects.append(genieutils.effect.Effect(name='Gun Canoe', effect_commands=[]))
    #DATA.techs[-1].effect_id = len(DATA.effects) - 1
    #DATA.effects[-1].effect_commands.append(genieutils.effect.EffectCommand(3, canoe_arrow_id, canoe_arrow_id+1, -1, 0))
    for i in range (3):
        pass
        #DATA.effects[174].effect_commands.append(genieutils.effect.EffectCommand(0, canoe_id+i, -1, 16, 380))
        #DATA.effects[174].effect_commands.append(genieutils.effect.EffectCommand(0, canoe_id+i, -1, 65, 380))
        #DATA.effects[174].effect_commands.append(genieutils.effect.EffectCommand(0, canoe_id+i, -1, 10, 3.45))
        #DATA.effects[174].effect_commands.append(genieutils.effect.EffectCommand(0, canoe_id+i, -1, 9, 785))

    # Correct name mistakes
    DATA.civs[1].name = 'Britons'
    DATA.civs[2].name = 'Franks'
    DATA.civs[16].name = 'Maya'
    DATA.effects[449].name = 'Maya Tech Tree'
    DATA.effects[489].name = 'Maya Team Bonus'
    DATA.civs[21].name = 'Inca'
    DATA.effects[3].name = 'Inca Tech Tree'
    DATA.effects[4].name = 'Inca Team Bonus'

    # Group existing civ bonuses into age-based techs and effects
    base_tech = genieutils.tech.Tech(
        required_techs=(0, 0, 0, 0, 0, 0),
        resource_costs=(
            ResearchResourceCost(type=0, amount=0, flag=0),
            ResearchResourceCost(type=0, amount=0, flag=0),
            ResearchResourceCost(type=0, amount=0, flag=0),
        ),
        required_tech_count=0,
        civ=civ_id + 1,
        full_tech_mode=0,
        research_location=-1,
        language_dll_name=7000,
        language_dll_description=8000,
        research_time=0,
        effect_id=-1,
        type=0,
        icon_id=-1,
        button_id=0,
        language_dll_help=107000,
        language_dll_tech_tree=157000,
        research_locations=[ResearchLocation(0, 0, 0, 0)],
        hot_key=-1,
        name='',
        repeatable=1
    )

    base_effect = genieutils.effect.Effect(name='', effect_commands=[])

    ages_dictionary = {'Dark': 104, 'Feudal': 101, 'Castle': 102, 'Imperial': 103}
    age_names = ['Dark', 'Feudal', 'Castle', 'Imperial']

    for i, civ in enumerate(DATA.civs, start=1):
        '''for age_name in age_names:
            # Create bonus effect holder
            bonus_effect = copy.deepcopy(base_effect)
            bonus_effect.name = f'{civ.name.upper()}: {age_name} Age Bonuses'
            DATA.effects.append(bonus_effect)

            # Create bonus tech holder
            bonus_tech = copy.deepcopy(base_tech)
            bonus_tech.name = f'{civ.name.upper()}: {age_name} Age Bonuses'
            bonus_tech.required_techs = (ages_dictionary[age_name], 0, 0, 0, 0, 0)
            bonus_tech.required_tech_count = 1
            bonus_tech.effect_id = len(DATA.effects) - 1
            DATA.techs.append(bonus_tech)'''

    # Rename existing bonuses (DELETE ONCE NEXT BLOCK IS COMPLETE)
    for i, tech in enumerate(DATA.techs):
        if tech.name.startswith(('C-Bonus,', 'C-Bonus')):
            tech.name = tech.name.replace('C-Bonus,', f'{DATA.civs[tech.civ].name.upper()}:').replace('C-Bonus', f'{DATA.civs[tech.civ].name.upper()}:')

        # Try to rename the effect as well
        DATA.effects[tech.effect_id].name = DATA.effects[tech.effect_id].name.replace('C-Bonus,', f'{DATA.civs[tech.civ].name.upper()}:').replace('C-Bonus', f'{DATA.civs[tech.civ].name.upper()}:')

    # Update the names of preexisting bonuses
    preexisting_bonuses = {
        # Britons
        383: r'BRITONS: shepherds work 25% faster',
        381: 'BRITONS: town Centers cost -50% wood starting in the castle age',
        382: 'BRITONS: foot archers +1/+2 range in the castle/imperial age',
        403: 'BRITONS: foot archers +1/+2 range in the castle/imperial age',
        # Huns
        225: 'HUNS: Do not need houses, but start with -100 wood',
        458: 'HUNS: Cavalry Archers cost -10/20% in Castle/Imperial Age',
        459: 'HUNS: Cavalry Archers cost -10/20% in Castle/Imperial Age',
    }

    for key, value in preexisting_bonuses.items():
        DATA.techs[key].name = value
        DATA.effects[DATA.techs[key].effect_id].name = value

    # Add bonuses techs and effects that didn't previously exist
    DATA.techs.append(genieutils.tech.Tech(
        required_techs=(0, 0, 0, 0, 0, 0),
        resource_costs=(
            ResearchResourceCost(type=0, amount=0, flag=0),
            ResearchResourceCost(type=0, amount=0, flag=0),
            ResearchResourceCost(type=0, amount=0, flag=0)
        ),
        required_tech_count=0,
        civ=civ_id + 1,
        full_tech_mode=0,
        research_location=0,  # legacy field, still required
        language_dll_name=7000,
        language_dll_description=8000,
        research_time=0,
        effect_id=-1,
        type=0,
        icon_id=-1,
        button_id=0,
        language_dll_help=107000,
        language_dll_tech_tree=157000,
        research_locations=[
            ResearchLocation(location_id=0, research_time=0, button_id=0, hot_key_id=0)
        ],
        hot_key=-1,
        name='HUNS: Trebuchets fire more accurately at units and small targets',
        repeatable=1
    ))

    DATA.effects.append(genieutils.effect.Effect(name='HUNS: Trebuchets fire more accurately at units and small targets', effect_commands=[genieutils.effect.EffectCommand(4, 42, -1, 11, 35)]))

    # Remake the bonuses so that they're compact
    # HUNS
    DATA.effects[214].effect_commands.append(genieutils.effect.EffectCommand(1, 4, 1, -1, 2000)) # Huns: Do not need houses, but start with -100 wood
    DATA.effects[214].effect_commands.append(genieutils.effect.EffectCommand(2, 70, 0, -1, 0))
    DATA.effects[448].effect_commands.remove(genieutils.effect.EffectCommand(2, 70, 0, -1, 0))
    DATA.effects[448].effect_commands.remove(genieutils.effect.EffectCommand(1, 4, 1, -1, 2000))
    DATA.effects[448].effect_commands.remove(genieutils.effect.EffectCommand(4, 42, -1, 11, 35))

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
            print(previous_mod_folder)
            previous_mod_name = previous_mod_folder.split('/')[-1]
    except Exception as e:
        print(str(e))
        pass

    # Switch emoji based on the month
    emoji_bank = {1: '⛄', 2: '💝', 3: '🍀', 4: '🌷', 5: '👒', 6: '🌺', 7: '🌴', 8: '🌻', 9: '🌾', 10: '🎃', 11: '🍂', 12: '🌲'}
    title_emoji = emoji_bank[datetime.now().month] * 3

    # Define tech tree IDs
    tech_tree_indexes = [254, 258, 259, 262, 255, 257, 256, 260, 261, 263, 275, 277, 276, 446, 447, 449, 448, 504, 20, 1, 3, 5, 7, 31, 28, 42, 27, 646, 648, 650, 652, 706, 708, 710, 712, 782, 784, 801, 803, 808, 840, 842, 890, 923, 927, 1101, 1107, 1129, 1030, 1031, 1028, 986, 988]

    # Main menu
    while True:
        print(colour(Back.BLUE, Style.BRIGHT, f'{title_emoji} Talofa - Age of Empires II Civilization Editor {title_emoji}'))
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
            if MOD_FOLDER == '':
                MOD_FOLDER = r'C:\Users\mquen\Games\Age of Empires 2 DE\76561198021486964\mods\local\Test'
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
        #create_bonus(rf'Mule Cart technologies are +40% more effective', 0)
        #create_bonus(rf'Spearman- and Militia-line upgrades (except Man-at-Arms) available one age earlier', 0)
        #create_bonus(rf'First Fortified Church receives a free Relic', 0)
        #create_bonus(rf'Galley-line and Dromons fire an additional projectile', 0)
        #create_bonus(rf'Demolition Ships +20% blast radius; Galley-line and Dromons +1 range', 0)
        #create_bonus(rf'Infantry (except Spearman-line) +30 HP; Warrior Priests heal +100% faster', 0)
        #create_bonus(rf'Infantry and Cavalry have +2 attack in the Feudal Age', 0)

        # Display selected mod menu
        print(colour(Back.CYAN, Style.BRIGHT, f'\n{title_emoji} {mod_name} Menu {title_emoji}'))
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

            if yes.lower() == 'y' or yes.lower() == 'yes':
                new_mod(MOD_FOLDER, ORIGINAL_FOLDER, MOD_NAME, True)
            else:
                print("Mod was not reverted.\n")
            time.sleep(1)

        # Edit Civilisation
        elif mod_menu_selection == '0':
            # Display all civilisations
            selected_civ_index = -1
            all_civs = []
            with open(MOD_STRINGS, 'r', encoding='utf-8') as file:
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

                        # Back
                        elif selection == '':
                            break

                        else:
                            # Catch error
                            try:
                                int(selection)
                            except:
                                print("\033[31mERROR: Invalid civilization ID.\033[0m")
                                continue

                            # Check to break loop
                            if int(selection) < len(DATA.civs) - 4:
                                break
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
            with open(MOD_STRINGS, 'r', encoding='utf-8') as file:
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
                            architecture_sets = {'African': [9084, 8747], 'Austronesian': [10084, 12477], 'Central Asian': [12084, 11747], 'Central European': [566, 171], 'East Asian': [567, 172], 'Eastern European': [8084, 7747], 'Mediterranean': [593, 177], 'Middle Eastern': [568, 173], 'Mesoamerican': [7084, 6747], 'South Asian': [10084, 12477], 'Southeast Asian': [11084, 10747], 'Southeast European': [15806, 15848], 'Western European': [569, 174]}
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
                        print(colour(Back.CYAN, Style.BRIGHT, f'\n{title_emoji} Edit {selected_civ_name} {title_emoji}'))
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
                        with open(MOD_STRINGS, 'r+', encoding='utf-8') as file:
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
                                with open(MOD_STRINGS, 'r+', encoding='utf-8') as file:
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
                                with open(MOD_STRINGS, 'r+', encoding='utf-8') as file:
                                    # Read and separate the lines
                                    lines = file.readlines()
                                    line_index = selected_civ_index + len(DATA.civs) - 1
                                    line = lines[line_index]
                                    line_code = line[:6]
                                    split_lines = line.split(r'\n')

                                    # Show the bonuses menu
                                    print(colour(Back.CYAN, Style.BRIGHT, f'\n{title_emoji} Bonuses Menu {title_emoji}'))
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
                                        print('\x1b[35mEnter "t:" followed by the bonus description to change the team bonus.\x1b[0m')
                                        time.sleep(1)
                                        continue
                                    
                                    # Quit menu
                                    if bonus_selection == '':
                                        with_real_progress(lambda progress: save_dat(progress, rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat'), 'Saving Mod', total_steps=100)
                                        print('Tech tree updated.')
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
                                                    if tech.name.lower() == f'{selected_civ_name.upper()}: {options[int(remove_bonus_selection)]}'.lower():
                                                        tech.effect_id = -1

                                                # Remove from the description
                                                for line in description_lines:
                                                    if options[int(remove_bonus_selection)] in line:
                                                        description_lines.remove(line)
                                                        save_description(description_code, description_lines)

                                                # Save changes
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
                                        if bonus_effect[0].effect_commands == []:
                                            break
                                        elif 'age' in bonus_to_add_ORIGINAL.lower():
                                            print(colour(Fore.RED, 'ERROR: Team Bonus cannot contain Age parameters.'))
                                            break

                                        # Find the previous team effect
                                        team_bonus_effect = None
                                        for i, effect in enumerate(DATA.effects):
                                            if effect.name == f'{selected_civ_name.title()} Team Bonus':
                                                team_bonus_effect = effect

                                        # Update the team bonus
                                        team_bonus_effect.effect_commands = bonus_effect[0].effect_commands

                                        # Change team bonus in description
                                        bonus_found = False
                                        description_lines[-1] = bonus_to_add_ORIGINAL
#   
                                        # Update the description
                                        save_description(description_code, description_lines)

                                        # Save changes
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
                                        print(f'Bonus {bonus_change_index} changed for {selected_civ_name}.')
                                        time.sleep(1)

                                    # Add bonus
                                    else:
                                        # Get user prompt
                                        bonus_to_add_ORIGINAL = bonus_selection
                                        bonus_to_add = bonus_to_add_ORIGINAL.lower()

                                        # Generate the bonus
                                        bonus_techs, bonus_effects = create_bonus(bonus_to_add, selected_civ_index)

                                        # Add the techs and effects to the .dat
                                        for effect in bonus_effects:
                                            DATA.effects.append(effect)
                                        for tech in bonus_techs:
                                            #tech.effect_id = len(DATA.effects) - 1
                                            DATA.techs.append(tech)

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
                                        print(f'Bonus added for {selected_civ_name}: {bonus_to_add_ORIGINAL}')
                                        time.sleep(1)

                        # Unique Unit
                        elif selection == '3':
                            # Populate all castle units
                            ALL_CASTLE_UNITS = ["longbowman", "throwing axeman", "berserk", "teutonic knight", "samurai", "chu ko nu", "cataphract", "war elephant", "mameluke", "janissary", "huskarl", "mangudai", "woad raider", "conquistador", "jaguar warrior", "plumed archer", "tarkan", "war wagon", "genoese crossbowman", "ghulam", "kamayuk", "magyar huszar", "boyar", "organ gun", "shotel warrior", "gbeto", "camel archer", "ballista elephant", "karambit warrior", "arambai", "rattan archer", "konnik", "keshik", "kipchak", "leitis", "coustillier", "serjeant", "obuch", "hussite wagon", "urumi swordsman", "ratha", "chakram thrower", "centurion", "composite bowman", "monaspa", 'iron pagoda', 'liao diao', 'white feather guard', 'tiger cavalry', 'fire archer', "amazon warrior", "amazon archer", "camel raider", "crusader", "tomahawk warrior", "ninja", "scimitar warrior", "drengr", "qizilbash warrior", "axe cavalry", "sun warrior", "island sentinel", 'naasiri', 'elephant gunner', 'flamethrower', 'weichafe']

                            # Get user input
                            while True:
                                new_castle_unit = input(f"\nEnter unique Castle unit for {selected_civ_name}: ").lower()

                                if new_castle_unit == '?':
                                    print(ALL_CASTLE_UNITS)
                                elif new_castle_unit not in ALL_CASTLE_UNITS:
                                    print("\033[31mERROR: Unit not found.\033[0m")
                                else:
                                    break

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
                            with open(ORIGINAL_STRINGS, 'r', encoding='utf-8') as file:
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
                                            if unit_name == ALL_CASTLE_UNITS[selected_civ_index]:
                                                castle_unit_indexes[0] = i
                                            elif unit_name == f'elite {ALL_CASTLE_UNITS[selected_civ_index]}':
                                                castle_unit_indexes[1] = i
                                            elif unit_name == new_castle_unit:
                                                castle_unit_indexes[2] = i
                                            elif unit_name == f'elite {new_castle_unit}':
                                                castle_unit_indexes[3] = i
                                    except:
                                        pass

                            # Change values for mistake units
                            for i in range(4):
                                if castle_unit_indexes[i] == 886:
                                    castle_unit_indexes[i] == 755
                                elif castle_unit_indexes[i] == 887:
                                    castle_unit_indexes[i] == 757

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

                            # Clone and assign unique effects for each tech
                            # Castle Age
                            castle_effect_clone = copy.deepcopy(DATA.effects[DATA.techs[unique_techs_ids[0]].effect_id])
                            castle_effect_id = len(DATA.effects)
                            DATA.effects.append(castle_effect_clone)
                            DATA.techs[unique_techs_ids[0]].effect_id = castle_effect_id

                            # Imperial Age
                            imperial_effect_clone = copy.deepcopy(DATA.effects[DATA.techs[unique_techs_ids[1]].effect_id])
                            imperial_effect_id = len(DATA.effects)
                            DATA.effects.append(imperial_effect_clone)
                            DATA.techs[unique_techs_ids[1]].effect_id = imperial_effect_id

                            # Prompt the user for Castle Age tech
                            new_castle_tech_name = prompt(f"\nChange Castle Age tech name: ", default=unique_techs_names[0].strip())
                            if new_castle_tech_name == '':
                                new_castle_tech_name = unique_techs_names[0]

                            # Get default description
                            prompt_default_text_castle = description_lines[-5].split('(')[1].strip(')')

                            while True:
                                new_castle_tech_description = prompt(
                                    f"Change Castle Age tech description: ",
                                    default=prompt_default_text_castle.strip()
                                )
                                new_castle_tech, new_castle_effect = create_bonus(new_castle_tech_description, selected_civ_index)
                                if len(new_castle_effect[0].effect_commands) == 0 and '*' not in new_castle_tech_description:
                                    print(f'\033[31mERROR: Invalid tech description.\n\033[0m\n')
                                    continue
                                else:
                                    DATA.effects[castle_effect_id].name = new_castle_tech_name
                                    DATA.effects[castle_effect_id].effect_commands = new_castle_effect[0].effect_commands
                                    new_castle_tech_description = new_castle_tech_description.replace('*', '')
                                    break

                            # Prompt the user for Imperial Age tech
                            new_imperial_tech_name = prompt(f"Change Imperial Age tech name: ", default=unique_techs_names[1].strip())
                            if new_imperial_tech_name == '':
                                new_imperial_tech_name = unique_techs_names[1]

                            # Get default description
                            prompt_default_text_imperial = description_lines[-4].split('(')[1].strip(')')

                            while True:
                                new_imperial_tech_description = prompt(
                                    f"Change Imperial Age tech description: ",
                                    default=prompt_default_text_imperial.strip()
                                )
                                new_imperial_tech, new_imperial_effect = create_bonus(new_imperial_tech_description, selected_civ_index)
                                if len(new_imperial_effect[0].effect_commands) == 0 and '*' not in new_imperial_tech_description:
                                    print(f'\033[31mERROR: Invalid tech description.\n\033[0m\n')
                                    continue
                                else:
                                    DATA.effects[imperial_effect_id].name = new_imperial_tech_name
                                    DATA.effects[imperial_effect_id].effect_commands = new_imperial_effect[0].effect_commands
                                    new_imperial_tech_description = new_imperial_tech_description.replace('*', '')
                                    break

                            # Change the names in string resources
                            change_string(DATA.techs[unique_techs_ids[0]].language_dll_name, new_castle_tech_name)
                            change_string(DATA.techs[unique_techs_ids[0]].language_dll_name + 10000, new_castle_tech_name)
                            change_string(DATA.techs[unique_techs_ids[0]].language_dll_description, f"Research {new_castle_tech_name} ({new_castle_tech_description})")
                            change_string(DATA.techs[unique_techs_ids[0]].language_dll_description + 20000, rf"Research <b>{new_castle_tech_name}<b> (<cost>)\n{new_castle_tech_description}.")
                            change_string(DATA.techs[unique_techs_ids[1]].language_dll_name, new_imperial_tech_name)
                            change_string(DATA.techs[unique_techs_ids[1]].language_dll_name + 10000, new_imperial_tech_name)
                            change_string(DATA.techs[unique_techs_ids[1]].language_dll_description, f"Research {new_imperial_tech_name} ({new_imperial_tech_description})")
                            change_string(DATA.techs[unique_techs_ids[1]].language_dll_description + 20000, rf"Research <b>{new_imperial_tech_name}<b> (<cost>)\n{new_imperial_tech_description}.")

                            # Update the internal tech names
                            DATA.techs[unique_techs_ids[0]].name = new_castle_tech_name
                            DATA.techs[unique_techs_ids[1]].name = new_imperial_tech_name

                            # Update description file
                            description_lines[-5] = f'• {new_castle_tech_name} ({new_castle_tech_description})'
                            description_lines[-4] = f'• {new_imperial_tech_name} ({new_imperial_tech_description})'
                            save_description(description_code, description_lines)

                            # Save file
                            with_real_progress(
                                lambda progress: save_dat(
                                    progress,
                                    rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat'
                                ),
                                'Saving Mod',
                                total_steps=100
                            )
                            print(f'Unique techs changed for {selected_civ_name}.')
                            time.sleep(1)

                        # Architecture
                        elif selection == '5':
                            # Gather base architectures
                            general_architecture_sets = {'West African': 26, 'Central Asian': 33, 'Central European': 22, 'East Asian': 5, 'Eastern European': 23, 'Mediterranean': 14, 'Middle Eastern': 9, 'Mesoamerican': 15, 'South Asian': 20, 'Southeast Asian': 28, 'Western European': 1}
                            monk_sets = {'Generic': 0, 'Native American': 15, 'Catholic': 14, 'Buddhist': 5, 'Hindu': 40, 'Muslim': 9, 'Tengri': 12, 'African': 25, 'Orthodox': 23, 'Pagan': 35}
                            monastery_sets = {'West African': 26, 'Central Asian': 33, 'Central European': 22, 'East Asian': 5, 'Eastern European': 23, 'Mediterranean': 14, 'Middle Eastern': 9, 'Mesoamerican': 15, 'South Asian': 40, 'Southeast Asian': 28, 'Western European': 1, 'Eastern African': 25, 'Southeast European': 7, 'Nomadic': 12, 'Pagan': 35}

                            base_architectures = [
                                list(general_architecture_sets.keys()),
                                [],
                                [],
                                list(monk_sets.keys()),
                                list(monastery_sets.keys()),
                            ]
                            for civ in DATA.civs:
                                if civ.name.lower() not in ['achaemenids', 'spartans', 'athenians', 'gaia']:
                                    base_architectures[1].append(civ.name)
                                    base_architectures[2].append(civ.name)

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
                                all_architectures = base_architectures[i] + custom_arcs[i]

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
                                        print('Leave blank to default to general architecture graphic.\n')
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
                                        if -1 <= architecture_selection < len(all_architectures):
                                            # Castle or Wonder → use index directly into custom_arcs
                                            if i in [1, 2]:
                                                architecture_changes[i] = architecture_selection

                                            # General, Monk, Monastery → use corresponding dict to map name/index to civ_id
                                            elif i == 0:
                                                key = list(general_architecture_sets.keys())[architecture_selection]
                                                architecture_changes[i] = general_architecture_sets[key]
                                            elif i == 3:
                                                key = list(monk_sets.keys())[architecture_selection]
                                                architecture_changes[i] = monk_sets[key]
                                            elif i == 4:
                                                key = list(monastery_sets.keys())[architecture_selection]
                                                architecture_changes[i] = monastery_sets[key]
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
                                                    custom_unit_id = get_unit_id(custom_arcs[i][architecture_changes[i] - len(base_architectures)], False)
                                                elif y == 1:
                                                    # Rubble unit
                                                    custom_rubbles = {'Poenari Castle': 1488, 'Aachen Cathedral': 1517, 'Dome of the Rock': 1482, 'Dormition Cathedral': 1493, 'Gol Gumbaz': 1487, 'Minaret of Jam': 1530, 'Pyramid': 1515, 'Quimper Cathedral': 1489, 'Sankore Madrasah': 1491, 'Tower of London': 1492}
                                                    custom_unit_id = custom_rubbles[custom_arcs[i][architecture_changes[i] - len(base_architectures)]]

                                                DATA.civs[selected_civ_index + 1].units[unit_id].standing_graphic = DATA.civs[1].units[custom_unit_id].standing_graphic
                                                DATA.civs[selected_civ_index + 1].units[unit_id].dying_graphic = DATA.civs[1].units[custom_unit_id].dying_graphic
                                                DATA.civs[selected_civ_index + 1].units[unit_id].damage_graphics = DATA.civs[1].units[custom_unit_id].damage_graphics
                                            except Exception as e:
                                                pass
                                                #print(str(e))
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
                            # Change language
                            while True:
                                new_language = input(f"\nEnter new language for {selected_civ_name}: ").title()

                                if new_language == '':
                                    break
                                elif new_language == '?':
                                    print(', '.join(ALL_LANGUAGES))
                                elif new_language.title() in ALL_LANGUAGES:
                                    # Change sounds
                                    sound_ids = {303: 'Villager-Male_Select_4', 301: 'Villager-Male_Move_4', 295: 'Villager-Male_Build_1', 299: 'Villager-Male_Chop_1', 455: 'Villager-Male_Farm_1', 448: 'Villager-Male_Fish_1', 297: 'Villager-Male_Forage_1', 298: 'Villager-Male_Hunt_1', 300: 'Villager-Male_Mine_1', 302: 'Villager-Male_Repair_1', 435: 'Villager-Female_Select_4', 434: 'Villager-Female_Move_4', 437: 'Villager-Female_Build_1', 442: 'Villager-Female_Chop_1', 438: 'Villager-Female_Farm_1', 487: 'Villager-Female_Fish_1', 440: 'Villager-Female_Forage_1', 441: 'Villager-Female_Hunt_1', 443: 'Villager-Female_Mine_1', 444: 'Villager-Female_Repair_1', 420: 'Soldier_Select_3', 421: 'Soldier_Move_3', 422: 'Soldier_Attack_3', 423: 'Monk_Select_3', 424: 'Monk_Move_3', 479: 'King_Select_3', 480: 'King_Move_3'}

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
                                try:
                                    # Prompt user for action
                                    tech_tree_action = input('\nSpecify units (start line with * to enable units): ').lower()

                                    # Get tech tree effect ID
                                    tech_tree_indexes = [254, 258, 259, 262, 255, 257, 256, 260, 261, 263, 275, 277, 276, 446, 447, 449, 448, 504, 20, 1, 3, 5, 7, 31, 28, 42, 27, 646, 648, 650, 652, 706, 708, 710, 712, 782, 784, 801, 803, 808, 840, 842, 890, 923, 927, 1101, 1107, 1129, 1030, 1031, 1028, 986, 988]

                                    # React to responses
                                    if tech_tree_action == '':
                                        # Save data
                                        with_real_progress(lambda progress: save_dat(progress, rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat'), 'Saving Mod', total_steps=100)
                                        print('Tech tree saved.')
                                        time.sleep(1)
                                        break
                                    elif tech_tree_action in ['all', 'clear']:
                                        # Clear the tech tree
                                        DATA.effects[tech_tree_indexes[selected_civ_index]].effect_commands.clear()
                                        print('Tech tree completely cleared.')
                                        time.sleep(1)
                                    elif tech_tree_action in ['reset', 'default']:
                                        # Clear the tech tree
                                        DATA.effects[tech_tree_indexes[selected_civ_index]].effect_commands.clear()
                                        # Disable all unique units
                                        for tech_id in [84, 272, 447, 448, 518, 521, 522, 528, 574, 598, 599, 655, 703, 773, 786, 787, 790, 842, 843, 858, 885, 948, 992, 1005, 1008, 1012, 1013, 1014, 1037, 1065, 1075]:
                                            DATA.effects[tech_tree_indexes[selected_civ_index]].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, tech_id))
                                        print('Tech tree set to default.')
                                        time.sleep(1)
                                    else:
                                        # Check if enable or disable
                                        enable = '*' in tech_tree_action
                                        tech_tree_action = tech_tree_action.replace('*', '').strip()

                                        # Separate items into a list
                                        items_to_disable = tech_tree_action.replace(', ', ',').split(',')

                                        # Disable tech tree items
                                        for item in items_to_disable:
                                            # Disable tech
                                            if item == 'stable':
                                                # Disable stable units
                                                DATA.effects[tech_tree_indexes[selected_civ_index]].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 25))
                                                for tech_id in [204, 254, 428, 521, 858, 1065, 790, 842, 843, 166, 209, 265, 526, 236, 235, 435, 714, 715, 630, 631, 1033, 1032, 39]:
                                                    DATA.effects[tech_tree_indexes[selected_civ_index]].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, tech_id))
                                                continue
                                            elif item == 'ship dock':
                                                # Disable all ships and enable canoes
                                                for tech_id in [604, 243, 246, 605, 244, 37, 376, 886, 1034]:
                                                    DATA.effects[tech_tree_indexes[selected_civ_index]].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, tech_id))
                                                
                                                # Enable canoe-line
                                                DATA.effects[tech_tree_indexes[selected_civ_index]].effect_commands.append(genieutils.effect.EffectCommand(3, 539, get_unit_id('canoe', False), -1, -1))
                                                DATA.effects[tech_tree_indexes[selected_civ_index]].effect_commands.append(genieutils.effect.EffectCommand(3, 21, get_unit_id('canoe', False)+1, -1, -1))
                                                DATA.effects[tech_tree_indexes[selected_civ_index]].effect_commands.append(genieutils.effect.EffectCommand(3, 442, get_unit_id('canoe', False)+2, -1, -1))
                                                continue

                                            # Correct mistakes
                                            if item == 'trebuchet':
                                                item = 'trebuchet (packed)'

                                            #print('Trying for:', item)
                                            # Determine the item ID
                                            tech_id = -1
                                            unit_id = get_unit_id(item, False)
                                            if unit_id == -1 or unit_id == None:
                                                tech_id = get_tech_id(item)
                                                #print('technology id for', item, ':', tech_id)

                                            if unit_id == -1 and tech_id == -1:
                                                print(colour(Fore.RED, f'ERROR: Cannot find item: {item}'))
                                                continue
                                            elif not enable:
                                                for i, tech in enumerate(DATA.techs):
                                                    if tech_id != -1 and tech.name.lower() == item.lower():
                                                        DATA.effects[tech_tree_indexes[selected_civ_index]].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, tech_id))
                                                        #print(f'Tech for technology ({item}):', i)
                                                        continue

                                                    # Disable unit
                                                    elif unit_id != -1:
                                                        try:
                                                            if (DATA.effects[tech.effect_id].effect_commands[0].a == unit_id and DATA.effects[tech.effect_id].effect_commands[0].type == 2) or (DATA.effects[tech.effect_id].effect_commands[0].b == unit_id and DATA.effects[tech.effect_id].effect_commands[0].type == 3):
                                                                # Add the effect command to the tech tree effect
                                                                DATA.effects[tech_tree_indexes[selected_civ_index]].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, i))
                                                                #print(f'Tech for unit ({item}):', i)
                                                                continue
                                                        except:
                                                            pass
                                            elif enable:
                                                # Gather all techs to enable
                                                items_to_enable = []
                                                for item in items_to_disable:
                                                    if item == 'trebuchet':
                                                        item = 'trebuchet (packed)'
                                                    
                                                    if get_tech_id(item) != -1:
                                                        items_to_enable.append(get_tech_id(item))
                                                    elif get_unit_id(item, False) != -1:
                                                        items_to_enable.append(get_unit_id(item), False)

                                                # Enable unit or tech
                                                for ec in DATA.effects[tech_tree_indexes[selected_civ_index]].effect_commands[::-1]:
                                                    if ec.type == 102 and ec.d in items_to_enable:
                                                        # Remove the effect command from the tech tree
                                                        DATA.effects[tech_tree_indexes[selected_civ_index]].effect_commands.remove(ec)
                                                        #print(f'Removed effect command for {ec.d}.')
                                        
                                        # Set scout based on tech tree
                                        if genieutils.effect.EffectCommand(102, -1, -1, -1, 858.0) not in DATA.effects[tech_tree_indexes[selected_civ_index]].effect_commands:
                                            scout_id = 1755
                                            print('Scout set to Camel Scout')
                                        elif genieutils.effect.EffectCommand(102, -1, -1, -1, 433.0) not in DATA.effects[tech_tree_indexes[selected_civ_index]].effect_commands:
                                            scout_id = 751
                                            print('Scout set to Eagle Scout')
                                        else:
                                            scout_id = 448
                                            print('Scout set to Scout Cavalry')
                                        DATA.civs[selected_civ_index + 1].resources[263] = scout_id

                                        # Print results
                                        print('Units enabled.' if enable else 'Units disabled.')
                                except Exception as e:
                                    print(str(e))

                            '''while True:
                                # Tech tree main menu
                                print(colour(Back.CYAN, Style.BRIGHT, f'\n{title_emoji} Tech Tree Menu {title_emoji}'))
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
                                    # Tech tree unit bank
                                    tech_tree_unit_bank = []

                                    # Build mappings
                                    link_map = {unit.get("Link ID"): unit for unit in tree if unit.get("Link ID") is not None}
                                    node_map = {unit.get("Node ID"): unit for unit in tree if unit.get("Node ID") is not None}

                                    # Identify all end-of-line units
                                    end_units = [unit for unit in tree if unit.get("Link ID") == -1]

                                    # Track printed lines to avoid duplicates
                                    seen = set()
                                    print(colour(Back.CYAN, Style.BRIGHT, f'\n{title_emoji} Tech Tree Branch Menu {title_emoji}'))

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
                                    else:
                                        pass

                                while True:
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