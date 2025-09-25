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
import ollama
import traceback
import sys
import unicodedata
from pathlib import Path

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

def get_unit_enabling_tech_id(unit_id):
    # Find the effect that enables this unit
    enabling_effect_id = -1
    for i, effect in enumerate(DATA.effects):
        try:
            for ec in effect.effect_commands:
                if (ec.type == 2 and ec.a == unit_id) or (ec.type == 3 and ec.b == unit_id):
                    enabling_effect_id = i
                    break
        except:
            pass

    for i, tech in enumerate(DATA.techs):
        try:
            if tech.effect_id == enabling_effect_id:
                return i
        except:
            pass
    return -1

def update_tech_tree_graphic(current_civ_name):
    # Find current civ index
    for i, civ in enumerate(DATA.civs):
        if civ.name.lower() == current_civ_name.lower():
            current_civ_index = i
            break

    # Find unique Castle unit
    for i, effect in enumerate(DATA.effects):
        if effect.name.lower() == f'{current_civ_name.lower()}: (imperial unit)':
            castle_unit_id = effect.effect_commands[0].a
            imperial_unit_id = effect.effect_commands[0].b
            break

    # Find unique Castle techs
    for i, tech in enumerate(DATA.techs):
        castle_tech_id, imperial_tech_id = -1, -1
        if tech.research_locations[0].location_id == 82 and tech.civ == current_civ_index and tech.research_locations[0].button_id == 7:
            if tech.required_techs[0] == 102:
                castle_tech_id = i
            elif tech.required_techs[0] == 103:
                imperial_tech_id = i

    # Load the reference JSON
    with open(rf'{MOD_FOLDER}/resources/_common/dat/civTechTrees.json', 'r', encoding="utf-8") as file:
        json_tree = json.load(file)

    # Build an entry bank of ALL variants per Node ID
    # Node ID -> [entry, entry, ...], each entry keeps its originating section in _section
    entry_bank = defaultdict(list)
    for i, civ in enumerate(json_tree.get("civs", [])):
        if i in [45, 46, 47]:
            continue

        for section in ("civ_techs_buildings", "civ_techs_units"):
            for entry in civ.get(section, []):
                nid = entry.get("Node ID")
                if nid is None:
                    continue
                try:
                    nid_key = int(nid)
                except Exception:
                    nid_key = nid
                e = copy.deepcopy(entry)
                e["_section"] = section
                entry_bank[nid_key].append(e)

    def clone_entry(node_id, picture_index, overrides=None):
        candidates = entry_bank.get(node_id, [])
        for c in candidates:
            try:
                c_pic = int(c.get("Picture Index", -1))
            except Exception:
                c_pic = -1
            if c_pic == picture_index:
                new_entry = copy.deepcopy(c)
                if overrides:
                    for k, v in overrides.items():
                        new_entry[k] = v
                # Make sure it goes into the same Node ID bucket
                entry_bank[node_id].append(new_entry)
                return new_entry
        return None
    
    # Create additional units
    clone_entry(539, 87, {"Name": "Canoe", "Picture Index": 164, 'Help String ID': 105119, 'Name String ID': 5119})
    clone_entry(21, 25, {"Name": "War Canoe", "Picture Index": 178, 'Help String ID': 105119, 'Name String ID': 90000})
    clone_entry(442, 60, {"Name": "Elite War Canoe", "Picture Index": 178, 'Help String ID': 105119, 'Name String ID': 92000})

    # Find the tech-tree effect for this civ
    tech_tree_id = -1
    target_name = f'{current_civ_name.lower()} tech tree'
    for i, effect in enumerate(DATA.effects):
        if effect.name.lower() == target_name:
            tech_tree_id = i
            break
    if tech_tree_id == -1:
        print(f"Tech tree effect not found for civ '{current_civ_name}'")
        return

    # Collect disabled tech triggers
    disabled_triggers = set()
    for ec in DATA.effects[tech_tree_id].effect_commands:
        try:
            d_val = int(ec.d)
        except Exception:
            d_val = ec.d
        disabled_triggers.add(d_val)
    # print('disabled triggers:', disabled_triggers)

    # Map building names to the tech trigger that disables/enables them
    trigger_dictionary = {
        'stable': 25,
        'watch tower': 127,
        'guard tower': 140,
        'keep': 63,
        'bombard tower': 64,
        'stone wall': 189,
        'fortified wall': 194,
        'krepost': 695,
        'donjon': 775,
        'caravanserai': 518,
        'feitoria': 570,
        # 'house': -1,  # not controlled directly by a trigger
    }

    # ---- Helpers -------------------------------------------------------------
    def _to_int_safe(v, default=-1):
        try:
            return int(v)
        except Exception:
            return default

    def _find_block(node_spec):
        if isinstance(node_spec, tuple) and len(node_spec) == 2:
            nid_key = _to_int_safe(node_spec[0], node_spec[0])
            pic_idx = _to_int_safe(node_spec[1], node_spec[1])
        else:
            nid_key = _to_int_safe(node_spec, node_spec)
            pic_idx = None

        candidates = entry_bank.get(nid_key, [])
        if not candidates:
            return None

        if pic_idx is None:
            return copy.deepcopy(candidates[0])

        for c in candidates:
            c_pic = _to_int_safe(c.get("Picture Index", -1), -1)
            if c_pic == pic_idx:
                return copy.deepcopy(c)

        return None

    def get_building_blocks(node_specs):
        final_blocks, missing = [], []
        for spec in node_specs:
            block = _find_block(spec)
            if block is None:
                missing.append(spec)
                continue

            # Determine building availability from your name→trigger map (if present)
            name_key = str(block.get('Name', '')).lower()
            trigger = trigger_dictionary.get(name_key, -1)
            block['Node Status'] = 'NotAvailable' if trigger in disabled_triggers else 'ResearchedCompleted'

            final_blocks.append(block)

        if missing:
            print(f"Missing building node(s): {missing}")
        return final_blocks

    def get_tech_blocks(node_specs):
        final_blocks, missing = [], []

        for spec in node_specs:
            block = _find_block(spec)
            if block is None:
                missing.append(spec)
                continue

            # Prefer your custom resolver; fall back to the block's own Trigger Tech ID
            if 'Unit' in block['Node Type']:
                # Unit
                unit_id = get_unit_id(block['Name'], False)
                trigger = get_unit_enabling_tech_id(unit_id)
            else:
                # Tech
                trigger = block['Node ID']

            # Disable/Enable unit/tech based on the trigger tech
            if trigger not in disabled_triggers or trigger < 1:
                block['Node Status'] = 'ResearchedCompleted'
            else:
                block['Node Status'] = 'NotAvailable'

            # Add block to final list
            final_blocks.append(block)

        if missing:
            print(f"Missing tech/unit node(s): {missing}")
        return final_blocks
    # -------------------------------------------------------------------------

    # Create a fresh civ block
    new_civ_block = {
        "civ_id": current_civ_name.upper(),
        "civ_techs_buildings": [],
        "civ_techs_units": [],
    }

    # -------- BUILDINGS -------------------------------------------------------
    building_ids = [(87, 0), (12, 2)]

    if 25 not in disabled_triggers:
        building_ids.append((101, 23))  # Stable

    building_ids += [
        (49, 22), (103, 4), (45, 13), (209, 33), (598, 38),
        (79, 25), (234, 27), (235, 26), (236, 42), (72, 30),
        (792, 44), (487, 36), (117, 31), (155, 32), (82, 7)
    ]

    if 695 not in disabled_triggers:
        building_ids.append((1251, 55))   # Krepost

    if 775 not in disabled_triggers:
        building_ids.append((1665, 84))   # Donjon

    if 929 in disabled_triggers:
        building_ids.append((104, 10))    # Monastery
        monastery_id = 104
    else:
        building_ids.append((1806, 88))   # Fortified Church
        monastery_id = 1806

    building_ids += [(109, 28), (70, 34), (621, 28), (276, 37)]

    if 570 not in disabled_triggers:
        building_ids.append((1021, 53))   # Feitoria

    if 518 not in disabled_triggers:
        building_ids.append((1754, 87))   # Caravanserai

    if 932 in disabled_triggers:
        building_ids += [(584, 39), (562, 40)]  # Mining/Lumber Camp
        mining_camp_id, lumber_camp_id = 584, 562
    else:
        building_ids.append((1808, 89))   # Mule Cart
        mining_camp_id = lumber_camp_id = 1808

    building_ids.append((84, 16))  # Market

    if 793 in disabled_triggers:
        building_ids.append((68, 19))     # Mill
        mill_id = 68
    else:
        building_ids.append((1734, 86))   # Folwark
        mill_id = 1734

    if 1008 in disabled_triggers:
        building_ids.append((50, 35))     # Farm
        farm_id = 50
    else:
        building_ids.append((1889, 96))   # Pasture
        farm_id = 1889

    # Add all building blocks at once
    blocks = get_building_blocks(building_ids)

    

    # Add blocks to the tech tree
    if blocks:
        new_civ_block["civ_techs_buildings"].extend(blocks)

    # -------- TECHS / UNITS ---------------------------------------------------
    tech_ids = [(4, 17), (24, 18), (492, 90), (7, 20), (6, 21)]

    if 655 not in disabled_triggers:
        tech_ids.append((1155, 229))  # Imperial Skirmisher

    # Slinger / Hand Cannoneer
    tech_ids.append((185, 143) if 528 not in disabled_triggers else (5, 22))

    # Elephant Archer / Cavalry Archer
    if 480 not in disabled_triggers:
        tech_ids += [(873, 393), (875, 93)]
    else:
        tech_ids += [(39, 19), (474, 71)]

    # Genitours / Grenadier / Xianbei Raider
    if 598 not in disabled_triggers:
        tech_ids += [(1010, 201), (1012, 499)]
    elif 992 not in disabled_triggers:
        tech_ids += [(1911, 462)]
    elif 1037 not in disabled_triggers:
        tech_ids += [(1952, 433)]

    # Thumb Ring thru Long Swordsman
    tech_ids += [(437, 112), (436, 111), (74, 8), (75, 10), (77, 13)]

    # Legionary / Two-Handed Swordsman, Champion
    if 885 not in disabled_triggers:
        tech_ids += [(1793, 139)]
    else:
        tech_ids += [(473, 12), (567, 72)]

    # Spearman thru Pikeman
    tech_ids += [(93, 31), (358, 11), (359, 104)]

    # Eagle-line (or Condottiero)
    if 433 not in disabled_triggers:
        tech_ids += [(751, 109), (753, 148), (752, 149)]
    elif 522 not in disabled_triggers:
        tech_ids += [(882, 134)]

    # Fire Lancer-line / Jian Swordsman / Flemish Militia
    if 981 not in disabled_triggers:
        tech_ids += [(1901, 457), (1903, 458)]
    elif 1075 not in disabled_triggers:
        tech_ids += [(1974, 437)]
    elif 773 not in disabled_triggers:
        tech_ids += [(1699, 354)]

    # Arson, Gambesons, Squires
    tech_ids += [(602, 118), (875, 116), (215, 80)]

    # Stable line (if Stable available)
    if 25 not in disabled_triggers:
        # Scout Cavalry, Light Cavalry
        tech_ids += [(448, 64), (546, 91)]

        # Hussar / Winged Hussar
        if 786 not in disabled_triggers:
            tech_ids += [(1707, 371)]
        else:
            tech_ids += [(441, 103)]

        # Shrivamsha Riders / Hei Guang / Knight line
        if 842 not in disabled_triggers:
            tech_ids += [(1751, 391), (1753, 519)]
        elif 1032 not in disabled_triggers:
            tech_ids += [(1944, 429), (1946, 430)]
        else:
            tech_ids += [(38, 1), (283, 49)]  # Knight, Cavalier
            if 526 not in disabled_triggers:
                tech_ids += [(1813, 410)]     # Paladin
            else:
                tech_ids += [(569, 2)]        # Savar

        # Camel Riders
        if 235 not in disabled_triggers:
            # If civ uses Camel Scout as scout unit
            for civ in DATA.civs:
                if civ.name == current_civ_name and getattr(civ, "resources", [None]*264)[263] == 1755:
                    tech_ids += [(1755, 392)]
                    break
            tech_ids += [(329, 78), (330, 79)]
            if 521 not in disabled_triggers:
                tech_ids += [(207, 185)]

        # Steppe Lancers or Battle Elephants
        if 714 not in disabled_triggers:
            tech_ids += [(1370, 273), (1372, 274)]
        elif 630 not in disabled_triggers:
            tech_ids += [(1132, 228), (1134, 246)]

        # Bloodlines, Husbandry
        tech_ids += [(435, 110), (39, 10)]

    # Battering Ram / Armoured Elephant
    if 837 not in disabled_triggers:
        tech_ids += [(1744, 394), (1746, 395)]
    else:
        tech_ids += [(1258, 74), (422, 63), (548, 73)]

    # Rocket Cart / Mangonel
    if 979 not in disabled_triggers:
        tech_ids += [(1904, 459), (1907, 460)]
    else:
        tech_ids += [(280, 27), (550, 101), (588, 102)]

    # Scorpion / War Chariot
    if 1065 not in disabled_triggers:
        tech_ids += [(2150, 627), (2151, 628)]
    else:
        tech_ids += [(279, 80), (542, 89)]

    # Flaming Camel
    if 703 not in disabled_triggers:
        tech_ids += [(1263, 270)]

    # Siege Tower
    tech_ids += [(1105, 212)]

    # Trebuchet family (Traction / Mounted / Bombard Cannon fallback)
    if 1025 not in disabled_triggers:
        tech_ids += [(1942, 428)]
    elif 1005 not in disabled_triggers:
        tech_ids += [(1923, 464)]
    else:
        tech_ids += [(36, 30)]  # Bombard Cannon

    # Houfnice
    if 787 not in disabled_triggers:
        tech_ids += [(1709, 372)]

    # Blacksmith armour/range upgrades and ships
    tech_ids += [
        (211, 49), (212, 50), (219, 51),
        (199, 34), (200, 35), (201, 37),
        (67, 17), (68, 18), (75, 21),
        (81, 66), (82, 23), (80, 65),
        (74, 63), (76, 22), (77, 64),
        (13, 24), (199, 41), (545, 95),
        (65, 41), (374, 98), (375, 99), (373, 97),
        (1103, 203), (529, 86), (532, 85), (1104, 202),
        (527, 84), (528, 83)
    ]

    # Canoes / Galleys
    if get_tech_id('canoe (make avail)') not in disabled_triggers:
        tech_ids += [(539, 164), (21, 178), (442, 178)] # Canoes
    else:
        tech_ids += [(539, 87), (21, 25), (442, 60)] # Galleys

    # Trade Cog / Junks
    tech_ids += [(17, 23)] # Trade Cog / Junk

    # Harbor (Malay)
    if current_civ_name == 'Malay':
        tech_ids += [(1189, 56)]

    # Dromon / Lou Chuan / Cannon Galleon
    if 886 not in disabled_triggers:
        tech_ids += [(1795, 406)]
    elif 1034 not in disabled_triggers:
        tech_ids += [(1948, 431)]
    else:
        tech_ids += [(420, 55), (691, 298)]

    # Turtle Ship / Longboat / Caravel / Thirisadai
    if 447 not in disabled_triggers:
        tech_ids += [(831, 116), (832, 491)]
    elif 272 not in disabled_triggers:
        tech_ids += [(250, 40), (533, 474)]
    elif 596 not in disabled_triggers:
        tech_ids += [(1004, 198), (1006, 497)]
    elif 841 not in disabled_triggers:
        tech_ids += [(1750, 387)]

    # University techs, unique unit, castle units, unique techs, monk
    tech_ids += [
        (50, 13), (51, 14), (194, 46),
        (47, 12), (64, 47), (93, 25), (377, 101),
        (140, 76), (63, 16), (380, 104), (608, 119),
        (322, 61), (54, 60),
        (1735, 386), (1737, 515),  # UU (Castle/Imp)
        (440, 113), (331, 29),     # Treb / Petard
        (833, 33), (834, 107),     # UTs (Castle/Imp)
        (379, 103), (315, 91), (321, 5), (408, 19), (125, 290)
    ]

    # Missionary / Warrior Priest
    if 84 not in disabled_triggers:
        tech_ids += [(775, 107)]
    elif 948 not in disabled_triggers:
        tech_ids += [(1811, 409)]

    # Monastery & Town Center & Camps & Market techs
    tech_ids += [
        (46, 131), (45, 11), (316, 92), (233, 84), (319, 93),
        (230, 82), (441, 114), (438, 109), (439, 108), (231, 83),
        (252, 73), (83, 15), (8, 69), (280, 89), (101, 30), (102, 31),
        (103, 32), (22, 6), (213, 79), (249, 42), (55, 15), (182, 62),
        (278, 87), (279, 88), (202, 70), (203, 71), (221, 81),
        (128, 34), (48, 113), (23, 7), (17, 3), (15, 58)
    ]

    # Mill techs
    if 1008 in disabled_triggers:
        tech_ids += [(14, 2), (13, 1), (12, 0)]
    else:
        tech_ids += [(1014, 138), (1013, 137), (1012, 136)]

    # Add all tech/unit blocks at once
    blocks = get_tech_blocks(tech_ids)

    # Edit a few blocks
    for block in blocks:
        # Monastery techs
        if block['Building ID'] == 104 or block['Building ID'] == 1806:
            block['Building ID'] = monastery_id
        # Mill techs
        if block['Building ID'] == 68 or block['Building ID'] == 1734:
            block['Building ID'] = mill_id
        # Lumber Camp techs
        if block['Building ID'] == 562 or block['Building ID'] == 1808:
            block['Building ID'] = lumber_camp_id
        # Mining Camp techs
        if block['Building ID'] == 584 or block['Building ID'] == 1808:
            block['Building ID'] = mining_camp_id
        # Camel Scout
        if DATA.civs[current_civ_index].resources[263] == 1755 and block['Node ID'] == 329 and block['Picture Index'] == 78:
            block['Link ID'] = 1755
        # Trebuchet (Packed)
        if block['Name'] == "Trebuchet (Packed)" and 256 in disabled_triggers:
            block['Node Status'] = 'NotAvailable'
        # Monk graphic
        monk_sprites = {998: 33, 7338: 131, 4491: 291, 8342: 218, 4483: 290, 8264: 169, 4475: 293, 4462: 122, 4844: 292, 5626: 349}
        if block['Name'] == "Monk":
            block['Picture Index'] = monk_sprites[DATA.civs[current_civ_index].units[125].standing_graphic[0]]
         # Trade Cart graphic
        trade_cart_sprites = {1141: 34, 7360: 287, 4863: 289, 4855: 288, 4871: 155}
        if block['Name'] == "Trade Cart":
            block['Picture Index'] = trade_cart_sprites[DATA.civs[current_civ_index].units[128].standing_graphic[0]]
        # Unique Castle Unit
        if block['Name'] == 'Urumi Swordsman':
            castle_unit = DATA.civs[current_civ_index].units[castle_unit_id]
            block['Name'] = get_string(castle_unit.language_dll_name)
            block['Picture Index'] = castle_unit.icon_id
            block['Name String ID'] = castle_unit.language_dll_name
            block['Help String ID'] = castle_unit.language_dll_name + 100000
        elif block['Name'] == 'Elite Urumi Swordsman':
            imperial_unit = DATA.civs[current_civ_index].units[imperial_unit_id]
            block['Name'] = get_string(imperial_unit.language_dll_name)
            block['Picture Index'] = imperial_unit.icon_id
            block['Name String ID'] = imperial_unit.language_dll_name
            block['Help String ID'] = imperial_unit.language_dll_name + 100000
        # Unique Castle Techs
        if block['Name'] == 'Paiks':
            castle_tech = DATA.techs[castle_tech_id]
            block['Name'] = get_string(castle_tech.language_dll_name)
            block['Name String ID'] = castle_tech.language_dll_name
            block['Help String ID'] = castle_tech.language_dll_name + 100000
        elif block['Name'] == 'Mahayana':
            imperial_tech = DATA.techs[imperial_tech_id]
            block['Name'] = get_string(imperial_tech.language_dll_name)
            block['Name String ID'] = imperial_tech.language_dll_name + 10000
            block['Help String ID'] = imperial_tech.language_dll_name + 100000
        # Demolition ships
        if 605 in disabled_triggers and (block['Name'] == 'Demolition Raft' or block['Name'] == 'Demolition Ship' or block['Name'] == 'Heavy Demolition Ship'):
            block['Node Status'] = 'NotAvailable'
        # Transport Ship
        if block['Name'] == 'Transport Ship':
            block['Node Status'] = 'ResearchedCompleted'
        # Junk
        if get_tech_id('junk (make avail)') not in disabled_triggers and block['Name'] == 'Trade Cog':
            block['Name'] = 'Junk'
            block['Picture Index'] = 211
            block['Name String ID'] = 5092
            block['Help String ID'] = 105092
            block['Node Type'] = 'RegionalUnit'

    # Add blocks to the tech tree
    if blocks:
        new_civ_block["civ_techs_units"].extend(blocks)

    # Replace civ in JSON and save
    replaced = False
    for i, civ in enumerate(json_tree.get("civs", [])):
        if civ.get("civ_id") == current_civ_name.upper():
            json_tree["civs"][i] = new_civ_block
            replaced = True
            break
    if not replaced:
        json_tree.setdefault("civs", []).append(new_civ_block)

    with open(rf'{MOD_FOLDER}/resources/_common/dat/civTechTrees.json', 'w', encoding="utf-8") as file:
        json.dump(json_tree, file, ensure_ascii=False, indent=2)

def get_effect_id(name):
    for i, effect in enumerate(DATA.effects):
        if effect.name.lower() == name.lower():
            return i
    return -1
        
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

def remove_accents(s: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )
        
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
import requests
def create_bonus(bonus_string, civ_id):
    try:
        unit_lines = {
            'archer-line': [4, 24, 492],
            'skirmishers': [7, 6, 1155],
            'cavalry archers': [39, 474],
            'elephant archers': [873, 875, get_unit_id('imperial elephant archer', False)],
            'genitours': [583, 596],
            'militia-line': [74, 75, 77, 473, 567, 1793],
            'spearman-line': [93, 358, 359],
            'eagle warriors': [751, 753, 752],
            'fire lancers': [1901, 1903],
            'scout cavalry-line': [448, 546, 441, 1707],
            'shrivamsha riders': [1751, 1753],
            'knight-line': [38, 283, 569, 1813],
            'steppe lancers': [1370, 1372],
            'camel riders': [1755, 329, 330, 207],
            'battle elephants': [1132, 1134],
            'hei guang cavalry': [1944, 1946],
            'battering rams': [35, 422, 548, 1258],
            'armored elephants': [1744, 1746],
            'mangonel-line': [280, 550, 588],
            'traction trebuchets': [1942],
            'rocket carts': [1904, 1907],
            'scorpions': [279, 542],
            'fishing ships': [13],
            'bombard cannons': [36, 1709],
            'fire ships': [1103, 529, 532],
            'demolition ships': [1104, 527, 528],
            'galleys': [539, 21, 442],
            'canoes': [778, 2383, 2384],
            'cannon galleons': [420, 691],
            'turtle ships': [831, 832],
            'longboats': [250, 533],
            'caravels': [1004, 1006],
            'lou chuans': [1948],
            'camel units': [282, 556, 1755, 329, 330, 207, 1007, 1009, 1263, 1923, get_unit_id('naasiri', False), get_unit_id('elite naasiri', False)],
            'elephant units': [239, 558, 873, 875, 1120, 1122, 1132, 1134, 1744, 1746, 1923, get_unit_id('imperial elephant archer', False)],
            'gunpowder units': [5, 36, 420, 46, 691, 771, 773, 557, 1001, 1003, 831, 832, 1709, 1704, 1706, 1904, 1907, 1901, 1903, 1911],
            'shock infantry': [751, 752, 753, 1901, 1903, 1974, 1976],
            'mule carts': [1808],
            'warrior priests': [1811, 1831],
            'archery range units': [4, 24, 492, 7, 6, 1155, 39, 474, 873, 875, get_unit_id('imperial elephant archer', False), 583, 596],
            'barracks units': [74, 75, 77, 473, 567, 1793, 93, 358, 359, 751, 753, 752, 1901, 1903],
            'stable units': [448, 546, 441, 1707, 1751, 1753, 38, 283, 569, 1813, 1370, 1372, 1755, 329, 330, 207, 1132, 1134, 1944, 1946],
            'siege workshop units': [35, 422, 548, 1258, 280, 550, 588, 1904, 1907, 1744, 1746, 36, 1709, 1105],
            'town centers': [109, 71, 141, 142],
            'builders': get_unit_id('builder', True),
            'shepherds': get_unit_id('shepherd', True),
            'hunters': get_unit_id('hunter', True),
            'fishermen': get_unit_id('fisherman', True),
            'farmers': get_unit_id('farmer', True) + get_unit_id('herder', True),
            'lumberjacks': get_unit_id('lumberjack', True),
            'gold miners': get_unit_id('gold miner', True),
            'stone miners': get_unit_id('stone miner', True),
            'miners': get_unit_id('gold miner', True) + get_unit_id('stone miner', True),
            'repairers': get_unit_id('repairer', True),
            'fortifications': [82, 71, 109, 141, 142],
        }

        # If you need to keep your existing unit_lines contents, don't recreate it.
        # But make sure every value will be treated as a list.
        def ensure_list_slot(d, k):
            v = d.get(k)
            if isinstance(v, list):
                return
            if v in (None, -1):
                d[k] = []
            else:
                d[k] = [v]

        def to_variants(name: str):
            name = name.strip().lower()
            out = set()
            if name.endswith('y'):
                out.add(name[:-1] + 'ies')
            elif name.endswith('ch'):
                out.add(name + 'es')
            elif not name.endswith('s'):
                out.add(name + 's')
            else:
                out.add(name)  # only include singular if it ends in 's'
            return list(out)

        for i, unit in enumerate(DATA.civs[1].units):
            try:
                creatable = getattr(unit, 'creatable', None)
                if not creatable or not getattr(creatable, 'train_locations', None):
                    continue
                if not creatable.train_locations:
                    continue
                if creatable.train_locations[0].unit_id != 118: # Get only buildings
                    continue

                # Safely get the display name
                dll_id = getattr(unit, 'language_dll_name', None)
                unit_name = get_unit_name(i)
                if not unit_name:
                    continue

                for variant in to_variants(unit_name):
                    ensure_list_slot(unit_lines, variant)   # make sure it's a list
                    if i not in unit_lines[variant]:        # avoid duplicates
                        unit_lines[variant].append(i)

            except Exception:
                pass

        '''for key, value in unit_lines.items():
            print(f"{key}: {value}")'''

        #print(unit_lines)
        categories = {
            'foot archers': [0],
            'buildings': [3],
            'villagers': [4],
            'infantry': [6],
            'cavalry': [12],
            'siege weapons': [13],
            'monks': [18],
            'trade units': [2, 19],
            'warships': [22],
            'ships': [2, 21, 22, 20, 53],
            'walls': [27],
            'mounted archers': [36],
            'towers': [52],
            'livestock': [58],
            'military units': [0, 35, 6, 36, 47, 12, 44, 23],
            'all military units': [0, 55, 22, 35, 6, 54, 13, 51, 36, 12],
            'fortifications': [27, 52, 39],
        }
        technologies = {
            'castle technologies': [321, 379],
            'town center technologies': [8, 22, 101, 102, 103, 213, 249, 280, 1193, 1194, 1195, 1200, 1201, 1202, 1221, 1222, 1223, 1224],
            'mill technologies': [12, 13, 14, 1012, 1013, 1014],
            'market technologies': [15, 17, 19, 23, 48],
            'dock technologies': [34, 35, 65, 244, 246, 372, 373, 374, 375, 376, 448, 597, 1010, 1261, 1262, 1263],
            'stable technologies': [39, 209, 236, 254, 265, 428, 435, 521, 526, 631, 715, 786, 843, 1033, 1169],
            'monastery technologies': [45, 46, 230, 231, 233, 252, 316, 319, 438, 439, 441],
            'university technologies': [47, 50, 51, 54, 63, 64, 93, 140, 194, 322, 377, 380, 608],
            'mining camp technologies': [55, 182, 278, 279],
            'blacksmith technologies': [67, 68, 74, 75, 76, 77, 80, 81, 82, 199, 200, 201, 211, 212, 219],
            'siege workshop technologies': [96, 239, 255, 257, 320, 787, 838, 980],
            'archery range technologies': [98, 100, 218, 237, 436, 437, 481, 599, 655],
            'barracks technologies': [197, 207, 215, 217, 222, 264, 384, 429, 434, 602, 716, 875, 885, 982, 1135, 1171, 1172],
            'lumber camp technologies': [202, 203, 221],
            'mule cart technologies': [55, 182, 278, 279, 202, 203, 221],
            'economic technologies': [55, 182, 278, 279, 202, 203, 221, 12, 13, 14, 1012, 1013, 1014, 22, 213, 85],
            'technologies': [85],
            'pasture upgrades': [1014, 1013, 1012],
            'farm upgrades': [14, 13, 12],
        }
        '''for i, tech in enumerate(DATA.techs):
            if tech.research_locations[0].location_id in [87, 12, 101, 103, 84, 82, 109, 65, 209, 49, 104, 562, 68, 584] and tech.effect_id != -1 and (tech.civ < 46 or tech.civ > 48):
                tech_name = get_string(tech.language_dll_name)
                technologies[tech_name[tech.language_dll_name].lower()] = [i]'''

        # Sample stat patterns with detection and stat_id
        stat_patterns = [
            (re.compile(r'([-+]?\d+%?)\s+hit points', re.IGNORECASE), [0]),
            #(re.compile(r'([-+]?\d+%?)\s+HP', re.IGNORECASE), [0]),
            (re.compile(r'([-+]?\d+%?)\s+line of sight', re.IGNORECASE), [1, 23]),
            (re.compile(r'([-+]?\d+%?)\s+LOS', re.IGNORECASE), [1, 23]),
            (re.compile(r'([-+]?\d+%?)\s+garrison capacity', re.IGNORECASE), [2]),
            (re.compile(r'move\s+([-+]?\d+%?)\s+faster', re.IGNORECASE), [5]),
            (re.compile(r'([-+]?\d+%?)\s+attack(?!s)', re.IGNORECASE), [9]),
            (re.compile(r'attack[s]?\s+([-+]?\d+%?)\s+faster', re.IGNORECASE), [10]),  # Invert value!
            (re.compile(r'have\s+([-+]?\d+%?)\s+accuracy', re.IGNORECASE), [11]),
            (re.compile(r'([-+]?\d+%?)\s+range', re.IGNORECASE), [12, 1, 23]),
            (re.compile(r'work\s+([-+]?\d+%?)\s+faster', re.IGNORECASE), [13]),
            (re.compile(r'carry\s+([-+]?\d+)', re.IGNORECASE), [14]),
            (re.compile(r'receive\s+([-+]?\d+%?)\s+bonus damage', re.IGNORECASE), [24]),
            (re.compile(r'fire[s]? an additional projectile', re.IGNORECASE), [102, 107]),
            (re.compile(r'cost\s+([-+]?\d+%?)\s+food', re.IGNORECASE), [103]),
            (re.compile(r'cost\s+([-+]?\d+%?)\s+wood', re.IGNORECASE), [104]),
            (re.compile(r'cost\s+([-+]?\d+%?)\s+gold', re.IGNORECASE), [105]),
            (re.compile(r'cost\s+([-+]?\d+%?)\s+stone', re.IGNORECASE), [106]),
            (re.compile(r'cost\s+([-+]?\d+)', re.IGNORECASE), [100]),
            (re.compile(r'regenerate\s+([-+]?\d+%?)\s+HP per minute', re.IGNORECASE), [109]),
            (re.compile(r'([-+]?\d+%?)\s+pierce armor', re.IGNORECASE), [8.768]),
            (re.compile(r'([-+]?\d+%?)\s+armor', re.IGNORECASE), [8.1024]),
            (re.compile(r'receive\s+([-+]?\d+%?)\s+friendly fire damage', re.IGNORECASE), [119]),
        ]

        def parse_number(text):
            if '%' in text:
                value = int(text.replace('%', ''))
                return round(1 + (value / 100), 2), True
            return int(text), False

        def build_modifiers(bonus_string, unit_lines, categories):
            s = bonus_string.lower()
            output = []

            # 1) Collect ALL targets present in the string (unit-lines and categories)
            targets = []
            for name, ids in unit_lines.items():
                if name.lower() in s:
                    targets.append(("unit", ids))
            for name, ids in categories.items():
                if name.lower() in s:
                    targets.append(("category", ids))

            # De-dup targets (same group may be found more than once)
            seen = set()
            unique_targets = []
            for ttype, ids in targets:
                key = (ttype, tuple(ids))
                if key not in seen:
                    seen.add(key)
                    unique_targets.append((ttype, ids))

            if not unique_targets:
                return ''  # No valid target found

            # 2) Walk all stat patterns and apply to ALL collected targets
            for pattern, stat_ids in stat_patterns:
                for match in pattern.finditer(s):
                    number_str = match.group(1) if match.lastindex else "+1"
                    num, is_percent = parse_number(number_str)

                    for stat_id in stat_ids:
                        if stat_id in [10] and isinstance(num, float): # Invert the number
                            final_value = round(1 - (num - 1), 2)
                        elif not is_percent and isinstance(num, float):
                            final_value = stat_id - int(stat_id) + num
                        else:
                            final_value = num

                        marker = "E4" if isinstance(final_value, int) else "E5"

                        for ttype, ids in unique_targets:
                            for tid in ids:
                                unit_id = tid if ttype == "unit" else -1
                                category_id = tid if ttype == "category" else -1
                                output.append(f"{marker}~{unit_id}~{category_id}~{int(stat_id)}~{final_value}")

            return "|".join(output)

        # Build the bonus response
        bonus_response = ''
        if bonus_string.lower() == 'start with two scouts':
            bonus_response = rf"T(639, 307, -1, -1, -1, -1)~2|E1~234~0~-1~1|E7~{int(DATA.civs[civ_id + 1].resources[263])}~619~1~-1"
        elif bonus_string.lower() == 'start with three scouts':
            bonus_response = rf"T(639, 307, -1, -1, -1, -1)~2|E1~234~0~-1~1|E7~{int(DATA.civs[civ_id + 1].resources[263])}~619~2~-1"
        elif re.search(r'^(.*?)\s+free\b', bonus_string, re.IGNORECASE):
            # Free techs
            tech_names = [
                t.strip()
                for t in re.search(r"^(.*?)\s+free", bonus_string, re.IGNORECASE).group(1).replace('and', ',').split(',')]

            tech_ids = []
            for tech_name in tech_names:
                tech_ids.append(get_tech_id(tech_name))

            for tech_id in tech_ids:
                bonus_response += f'E101~{tech_id}~0~0~0|E101~{tech_id}~1~0~0|E101~{tech_id}~2~0~0|E101~{tech_id}~3~0~0|E103~{tech_id}~0~0~0|'
        elif re.search(r'^(.*?)\s+available one age earlier\b', bonus_string, re.IGNORECASE):
            # Units available one age earlier
            tech_names = [
                t.strip()
                for t in re.search(r'^(.*?)\s+available one age earlier', bonus_string, re.IGNORECASE).group(1).replace('and', ',').split(',')]
            
            tech_ids = []
            for tech_name in tech_names:
                tech_ids.append(get_tech_id(tech_name))

            for tech_id in tech_ids:
                required_techs = []
                for rt in DATA.techs[tech_id].required_techs:
                    required_techs.append(rt)
            
            bonus_response += f'T({required_techs[0]}, {required_techs[1]}, {required_techs[2]}, {required_techs[3]}, {required_techs[4]}, {required_techs[5]}'
            #bonus_response += f'E101~{tech_id}~0~0~0|E101~{tech_id}~1~0~0|E101~{tech_id}~2~0~0|E101~{tech_id}~3~0~0|E103~{tech_id}~0~0~0|'
        elif bonus_string.lower() == "rocket carts, grenadiers and lou chuans detonate when defeated; projectiles produce additional explosions":
            # Thunderclap Bombs effect
            bonus_response = (
                "E0~1911~-1~66~1917|"
                "E0~1913~-1~57~1887|E0~1913~-1~68~2|"
                "E0~1906~-1~57~1928|E0~1904~-1~66~1919|E0~1907~-1~66~1919|E0~1906~-1~68~2|"
                "E0~1913~-1~73~12833|E0~1938~-1~57~1883|E0~1939~-1~57~1883|"
                "E0~1938~-1~67~1|E0~1939~-1~67~1|E0~1938~-1~68~2|E0~1939~-1~68~2|"
                "E0~1938~-1~75~13112|E0~1939~-1~75~13112|E0~1938~-1~71~13112|E0~1939~-1~71~13112|"
                "E0~1948~-1~77~13016|E0~1948~-1~107~11|E0~1948~-1~62~7|E0~1948~-1~57~1881|"
                "E0~1948~-1~73~1751|E0~1948~-1~66~1882|E0~1948~-1~125~1938|E0~1948~-1~65~1936|"
                "E0~1948~-1~63~26|E0~1911~-1~73~1751|E0~1911~-1~74~12739|E0~1911~-1~57~1916|"
                "E0~1904~-1~73~1751|E0~1904~-1~74~12734|E0~1904~-1~57~1918|"
                "E0~1907~-1~73~1751|E0~1907~-1~74~13102|E0~1907~-1~57~1895"
            )
        else:
            # Edit unit/building attribute
            bonus_response = build_modifiers(bonus_string, unit_lines, categories)

        # Create the final techs and the final effects
        final_techs = [genieutils.tech.Tech(required_techs=(0, 0, 0, 0, 0, 0), research_locations=[ResearchLocation(0, 0, 0, 0)], resource_costs=(ResearchResourceCost(type=0, amount=0, flag=0), ResearchResourceCost(type=0, amount=0, flag=0), ResearchResourceCost(type=0, amount=0, flag=0)), required_tech_count=0, civ=civ_id + 1, full_tech_mode=0, research_location=-1, language_dll_name=7000, language_dll_description=8000, research_time=0, effect_id=len(DATA.effects), type=0, icon_id=-1, button_id=0, language_dll_help=107000, language_dll_tech_tree=157000, hot_key=-1, name=f'{DATA.civs[civ_id + 1].name.upper()}: {bonus_string}', repeatable=1)]
        final_effects = [genieutils.effect.Effect(name=f'{DATA.civs[civ_id + 1].name.upper()}: {bonus_string}', effect_commands=[])]

        # Error out if bonus text is invalid
        '''if bonus_response == '':
            print(colour(Fore.RED, 'ERROR: Bonus text invalid.'))
            return final_techs, final_effects'''

        # Split the response into parts
        bonus_parts = bonus_response.split('|')

        # Create a tech or effect based on the bonus parts
        def parse_num(token: str):
            token = token.strip()
            if token.endswith('%'):
                # convert +25% → 1.25, -20% → 0.80
                val = float(token[:-1])
                return round(1 + (val / 100), 4)  # float
            if '.' in token:
                return float(token)
            return int(token)

        for part in bonus_parts:
            if not part:
                continue

            if part[0] == 'T':
            # Create tech
                final_techs[0].required_techs = set(part[1:].split('~')[0])
                final_techs[0].required_tech_count = int(part[1:].split('~')[1])
            elif part[0] == 'E':
                toks = part[1:].split('~')
                if len(toks) != 5:
                    raise ValueError(f"Invalid E-part format: {part}")

                ec_parts = [parse_num(p) for p in toks]
                bonus_type = int(ec_parts[0])  # ensure int here
                if 'team' in bonus_string.lower():
                    bonus_type += 10

                final_effects[0].effect_commands.append(
                    genieutils.effect.EffectCommand(
                        bonus_type,
                        int(ec_parts[1]),
                        int(ec_parts[2]),
                        int(ec_parts[3]),
                        ec_parts[4]  # can be int or float
                    )
                )

        # Get the starting age
        if 'starting in the feudal age' in bonus_string.lower():
            final_techs[0].required_techs = (101, 0, 0, 0, 0, 0)
            final_techs[0].required_tech_count = 1
        elif 'starting in the castle age' in bonus_string.lower():
            final_techs[0].required_techs = (102, 0, 0, 0, 0, 0)
            final_techs[0].required_tech_count = 1
        elif 'starting in the imperial age' in bonus_string.lower():
            final_techs[0].required_techs = (103, 0, 0, 0, 0, 0)
            final_techs[0].required_tech_count = 1

        # Return the final tech and final effect
        return final_techs, final_effects
    
    except Exception as e:
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {e}")
        traceback.print_exc(file=sys.stdout)

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
                #UNIT_CATEGORIES.setdefault(get_unit_name(unit_line[0]) + '-', []).append(f'U{unit.id}')

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
    def collect_castle_units(DATA, civ_id=1):
        units = DATA.civs[civ_id].units

        # Precompute names once
        idx_to_name = {}
        name_set = set()
        for i, _u in enumerate(units):
            try:
                nm = get_unit_name(i)
                if not nm:
                    continue
                nm_l = nm.lower()
                idx_to_name[i] = nm_l
                name_set.add(nm_l)
            except Exception:
                continue

        # Build a quick lookup of which base names have an Elite variant
        # (i.e., "elite {base}" exists)
        has_elite = set()
        for nm in name_set:
            if nm.startswith("elite "):
                base = nm[6:].strip()
                if base:
                    has_elite.add(base)

        # Helper: is trainable at Castle?
        def trainable_at_castle(u):
            creatable = getattr(u, "creatable", None)
            if not creatable:
                return False
            locs = getattr(creatable, "train_locations", None)
            if not locs:
                return False
            # Castle: unit_id == 82, button_id == 1
            return any(getattr(loc, "unit_id", None) == 82 and getattr(loc, "button_id", None) == 1
                    for loc in locs)

        # Collect base (non-elite) castle-trainable units that have an elite
        result = []
        for i, u in enumerate(units):
            base_name = idx_to_name.get(i)
            if not base_name or base_name.startswith("elite "):
                continue
            if base_name in has_elite and trainable_at_castle(u):
                result.append(base_name.title())

        return sorted(set(result))

    # If you still want the global filled:
    global ALL_CASTLE_UNITS
    ALL_CASTLE_UNITS = collect_castle_units(DATA, civ_id=1)

    # DEBUG: Print dictionary
    #for key, value in UNIT_CATEGORIES.items():
    #    print(f'{key}: {value}')
    #print(UNIT_CATEGORIES)

    # Update the tech trees
    for civ in DATA.civs:
        if civ.name not in ['Achaemenids', 'Athenians', 'Spartans', 'Gaia']:
            update_tech_tree_graphic(civ.name)

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
        _mod_name = _mod_name.split('/')[-1]
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
    for civ_id, civ in enumerate(DATA.civs):
        for sound_id in sound_ids:
            # Get the amount of sound items to add
            sound_count = int(sound_ids[sound_id][-1])

            # Add the sound items to the sound
            language_presets = {1: "English", 2: "French", 3: "Gothic", 4: "German", 5: "Japanese", 6: "Mandarin", 7: "Greek", 8: "Persian", 9: "Arabic", 10: "Turkish", 11: "Norse", 12: "Mongolian", 13: "Gaelic", 14: "Spanish", 15: "Yucatec", 16: "Kaqchikel", 17: "Chuvash", 18: "Korean", 19: "Italian", 20: "Hindustani", 21: "Quechua", 22: "Hungarian", 23: "Russian", 24: "Portuguese", 25: "Amharic", 26: "Maninka", 27: "Taqbaylit", 28: "Khmer", 29: "Malaysian", 30: "Burmese", 31: "Vietnamese", 32: "Bulgarian", 33: "Chagatai", 34: "Cuman", 35: "Lithuanian", 36: "Burgundian", 37: "Sicilian", 38: "Polish", 39: "Czech", 40: "Tamil", 41: "Bengali", 42: "Gujarati", 43: "Vulgar Latin", 44: "Armenian", 45: "Georgian", 49: "Mandarin", 50: "Cantonese", 51: "Mandarin", 52: "Jurchen", 53: "Khitan"}
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

    # Add the graphics to the .dat file
    '''starting_graphic_index = len(DATA.graphics)
    DATA.graphics.append(Graphic(name='SEE_Dock2', file_name='b_byzantinedock_x1', particle_effect_name='', slp=6067, is_loaded=0, old_color_flag=1, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=60, angle_count=1, speed_multiplier=0.0, frame_duration=0.15000000596046448, replay_delay=0.0, sequence_type=5, id=12733, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=220, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12734, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=4411, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=-120, display_angle=-1, padding_2=0)], angle_sounds=[]))
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
    DATA.graphics.append(Graphic(name='SEE_Dock3', file_name='b_castledockbyz_x1', particle_effect_name='', slp=2260, is_loaded=0, old_color_flag=1, layer=20, player_color=-1, transparent_selection=1, coordinates=(0, 0, 0, 0), sound_id=-1, wwise_sound_id=0, angle_sounds_used=0, frame_count=60, angle_count=1, speed_multiplier=0.0, frame_duration=0.15000000596046448, replay_delay=0.0, sequence_type=5, id=12761, mirroring_mode=0, editor_flag=0, deltas=[GraphicDelta(graphic_id=241, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=12762, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=0, display_angle=-1, padding_2=0), GraphicDelta(graphic_id=4411, padding_1=0, sprite_ptr=0, offset_x=0, offset_y=-120, display_angle=-1, padding_2=0)], angle_sounds=[]))
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
    
    # Damage Graphics
    base_see_graphics = []
    for graphic in base_see_graphics:
        pass

    # Change the Byzantines to this new architecture style
    southeast_european_graphics = {
        # Archery Range
        87: [2, 37],   # AR2, AR2 rubble
        10: [3, 36],   # AR3, AR3 rubble
        14: [3, 36],

        # Barracks
        20:  [5, 34],
        132: [5, 34],
        498: [6, 35],

        # Stable
        86:  [11, 32],
        101: [10, 33],
        153: [11, 32],

        # Siege Workshop
        49:  [9, 38],
        150: [9, 38],

        # Blacksmith
        103: [7, 43],  # BS2, BS2 rubble
        105: [8, 42],  # BS3, BS3 rubble
        18:  [8, 42],
        19:  [8, 42],

        # Dock (animated standing; no rubble)
        133: [1, -1],   # Age 2
        806: [1, -1],   # Age 2
        2120: [1, -1],  # Age 2
        2144: [1, -1],  # Age 2
        47:  [29, -1],  # Age 3
        51:  [29, -1],  # Age 3
        807: [29, -1],  # Age 3
        808: [29, -1],  # Age 3
        2121: [29, -1], # Age 3
        2122: [29, -1], # Age 3
        2145: [29, -1], # Age 3
        2146: [29, -1], # Age 3

        # University (fixed)
        209: [12, 47], # Uni3, Uni3 rubble
        210: [13, 48], # Uni4, Uni4 rubble

        # Towers (fixed)
        79:  [16, 51], # Watch → Tower2 rubble
        234: [17, 50], # Guard → Tower3 rubble
        235: [18, 52], # Keep → Tower4 rubble
        236: [4,  53], # Bombard → Bombard rubble

        # Walls (standing only)
        117: [24, -1], # Stone Wall frames
        115: [25, -1], # Fortified Wall

        # Castle
        82:  [54, 49], # Castle, Castle rubble

        # Monastery
        30:  [15, 46],
        31:  [15, 46],
        32:  [15, 46],
        104: [15, 46],

        # House
        191: [21, 30],
        192: [21, 30],
        463: [20, 31],
        464: [21, 30],
        465: [21, 30],

        # Mill
        129: [22, 45], # Mill2, Mill2 rubble
        130: [23, 44], # Mill3, Mill3 rubble
        131: [23, 44],

        # Market
        84:  [14, 40], # Market2, Market2 rubble
        116: [14, 39],  # Market3 needs a standing SEE_Market3
        137: [19, 41], # Market4, Market4 rubble
    }

    for i, unit in enumerate(DATA.civs[7].units):
        if i in southeast_european_graphics:
            g0, g1 = southeast_european_graphics[i]

            if g0 > -1:
                unit.standing_graphic = (g0 + starting_graphic_index, -1)  # ordered tuple

            if g1 > -1:
                unit.dying_graphic = g1 + starting_graphic_index'''

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

    # Remove the Pasture text for the Khitans
    with open(MOD_STRINGS, 'r+', encoding='utf-8') as modded_file:
        modded_strings = modded_file.readlines()
        modded_file.seek(0)  # rewind to start
        for line in modded_strings:
            line = line.replace(r'• Pastures replace Farms\n', '')
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

    '''# Make the Imperial Skirmisher potentially available to all civs
    DATA.techs[656].effect_id = -1
    DATA.techs[655].research_locations[0].button_id = 7
    for civ in DATA.civs:
        for effect in DATA.effects:
            if effect.name.lower() == f'{civ.name.lower()} tech tree' and 'vietnamese' not in effect.name.lower():
                effect.effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 655))'''

    # Make other unique units potentially available to all civs
    tech_tree_indexes = []
    for civ in DATA.civs:
        # Skip Chronicles civs
        if (civ.name.lower() == ['gaia', 'spartans', 'athenians', 'achaemenids']):
            tech_tree_indexes.append(-1)
            continue

        # Find the tech tree effect
        for i, effect in enumerate(DATA.effects):
            if effect.name == f'{civ.name.title()} Tech Tree':
                tech_tree_indexes.append(i)
                break

    # Make the Fortified Church potentially available to all civs
    DATA.techs[941].effect_id = -1
    DATA.techs[941].name = 'Fortified Church (DISABLED)'
    DATA.techs[930].effect_id = -1
    DATA.techs[930].name = 'Fortified Church (DISABLED)'
    DATA.effects[941].name = 'Fortified Church'
    DATA.techs[929].name = 'Fortified Church'
    DATA.techs[929].effect_id = 941
    for tt in tech_tree_indexes:
        if tt not in [925, 927]:
            DATA.effects[tt].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 929))

    # Make the Mule Cart potentially available to all civs
    DATA.techs[940].effect_id = -1
    DATA.techs[940].name = 'Mule Cart (DISABLED)'
    DATA.techs[940].civ = -1
    DATA.techs[932].civ = -1
    for tt in tech_tree_indexes:
        if tt not in [925, 927]:
            DATA.effects[tt].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 932))

    # Define the unit techs that need to be expanded
    unique_techs_indexes = [84, 272, 447, 448, 521, 522, 526, 528, 570, 596, 597, 598, 599, 655, 695, 703, 773, 775, 787, 790, 793, 841, 842, 843, 885, 930, 941, 948, 992, 1005, 1037, 1065, 1075]
    for tech_id in unique_techs_indexes:
        # Find the original civ that had the tech
        excluded_civ_id = DATA.techs[tech_id].civ
        if excluded_civ_id == -1:
            hidden_civs = {522: 19, 599: 27, 655: 31}
            excluded_civ_id = hidden_civs[tech_id]

        # Decouple the civ ID from the tech
        DATA.techs[tech_id].civ = -1

        # Disable it for every civ except for the excluded civ
        for i, index in enumerate(tech_tree_indexes):
            #print(tech_id, i)
            if index == -1:
                continue
            elif index != tech_tree_indexes[excluded_civ_id]:
                DATA.effects[index].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, tech_id))

    # Disable redundant techs
    techs_to_disable = [0]
    for tech_id in techs_to_disable:
        DATA.techs[tech_id].effect_id = -1
        DATA.techs[tech_id].civ = -1

    # Saracens start with Camel Scout
    DATA.civs[9].resources[263] = 1755

    # Enable Dromon for Vikings and Bulgarians
    for tech_tree in [276, 706]:
        DATA.effects[tech_tree].effect_commands.remove(genieutils.effect.EffectCommand(102, -1, -1, -1, 886))
        DATA.effects[tech_tree].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 37))
        DATA.effects[tech_tree].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 376))

    # Enable Lou Chuan for Vietnamese
    for tech_tree in [652]:
        DATA.effects[tech_tree].effect_commands.remove(genieutils.effect.EffectCommand(102, -1, -1, -1, 1034))
        DATA.effects[tech_tree].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 37))
        DATA.effects[tech_tree].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 376))

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

    # Change the Monastery graphics for the Chinese, Koreans, and Jurchens
    graphic_replacements = [2060, 2060, 2060, 2060, 145]
    unit_ids = [30, 31, 32, 104, 1421]

    for civ_id in [6, 18, 52]:
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

    '''# Create an Islander architecture from the feudal African buildings and temporarily assign it to the Ethiopians
    islander_changes = {
        #Archery Range
        87: [10, 14],
        1415: [1416],

        #Barracks
        498: [20, 132],
        1413: [1414],

        #Stable
        101: [86, 153],
        1417: [1418],

        #Blacksmith
        103: [18, 19, 105],
        1419: [1420],

        #Dock
        133: [47, 51, 133, 806, 807, 808, 2120, 2121, 2122, 2144, 2145, 2146],

        # University
        209: [210],
        1427: [1428],

        # Town Centre Back
        71: [141, 142],

        # Town Centre Main
        614: [481, 611],

        # Town Centre Centre
        615: [482, 612],

        # Town Centre Front
        616: [483, 613],

        # Town Centre Preview
        617: [484, 497],

        # House
        1082: [191, 192, 463, 464, 465],
        1455: [1434, 1435],

        # Mill
        1081: [129, 130, 131],
        1484: [1411, 1412],

        # Market
        84: [116, 137],
        1422: [1423, 1424]
    }

    for change_key, change_value in islander_changes.items():
        for unit_id in change_value:
            DATA.civs[25].units[unit_id].standing_graphic = DATA.civs[25].units[change_key].standing_graphic
            DATA.civs[25].units[unit_id].dying_graphic = DATA.civs[25].units[change_key].dying_graphic
            DATA.civs[25].units[unit_id].damage_graphics = DATA.civs[25].units[change_key].damage_graphics'''

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

    # Enable the Pasture for Mongols, Berbers, Huns, Cumans, and Khitans
    DATA.techs[1008].civ = -1
    DATA.techs[1014].civ = -1
    DATA.techs[1013].civ = -1
    DATA.techs[1012].civ = -1
    DATA.techs[1008].name = 'Pasture'
    DATA.effects[1008].name = 'Pasture'
    DATA.effects[1008].effect_commands[0] = genieutils.effect.EffectCommand(3, 50, 1889, -1, -1)
    for effect in [effect_ for effect_ in DATA.effects if "tech tree" in effect_.name.lower()]:
        name = effect.name.lower()
        if any(group in name for group in ['mongols', 'berbers', 'huns', 'cumans', 'khitans']):
            # Disable farms and farm upgrades
            effect.effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 12))
            effect.effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 13))
            effect.effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 14))
        else:
            # Disable pasture and pasture upgrades
            effect.effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 1008))
            effect.effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 1012))
            effect.effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 1013))
            effect.effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, 1014))

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

    # Uncouple the older, existing, unique Castle unit techs
    '''old_tech_costs = []
    old_tech_research_locations = []
    for tech_id in [263, 360, 275, 363, 399, 398, 276, 364, 262, 366, 268, 362, 267, 361, 274, 367, 269, 368, 271, 369, 446, 365, 273, 371, 277, 370, 58, 60, 431, 432, 26, 27, 1, 2, 449, 450, 467, 468, 839, 840, 508, 509, 471, 472, 503, 504, 562, 563, 568, 569, 566, 567, 564, 565, 614, 615, 616, 617, 618, 619, 620, 621, 677, 678, 679, 680, 681, 682, 683, 684, 750, 751, 752, 753, 778, 779, 780, 781, 825, 826, 827, 828, 829, 830, 881, 882, 917, 918, 919, 920, 990, 991, 1001, 1002, 1063, 1064, 1035, 1036, 1073, 1074]:
        DATA.techs[tech_id].effect_id = -1
        DATA.techs[tech_id].required_tech_count = 6

        if DATA.techs[tech_id].resource_costs[0].type != -1:
            old_tech_costs.append(DATA.techs[tech_id].resource_costs)
            old_tech_research_locations.append(DATA.techs[tech_id].research_locations)'''

    # Create units unique to Talofa
    for civ in DATA.civs:
        # Change sound for dock to port
        for unit_id in [45, 47, 51, 113, 805, 806, 807, 808, 2120, 2121, 2122, 2144, 2145, 2146, 2173]:
            civ.units[unit_id].selection_sound = 708
            civ.units[unit_id].train_sound = 708

        # Canoe
        custom_unit_starting_index = len(civ.units)
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
        war_canoe.type_50.attacks[0].amount = 12
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
        elite_war_canoe.type_50.attacks[0].amount = 16
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
        naasiri.creatable.train_locations[0].hot_key_id = 16107
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
        elephant_gunner.creatable.train_locations[0].train_time = 28
        elephant_gunner.creatable.resource_costs = (ResourceCost(type=0, amount=80, flag=1), ResourceCost(type=3, amount=100, flag=1), ResourceCost(type=4, amount=1, flag=0))
        elephant_gunner.type_50.projectile_unit_id = 380
        elephant_gunner.creatable.train_locations[0].hot_key_id = 16107
        elephant_gunner.class_ = 23
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
        elite_elephant_gunner.class_ = 23
        civ.units.append(elite_elephant_gunner)

        # Flamethrower
        flamethrower = copy.deepcopy(DATA.civs[1].units[188])
        flamethrower.creatable.train_locations[0].unit_id = 82
        flamethrower.creatable.train_locations[0].button_id = 1
        flamethrower.type_50.attacks[1].amount = 6
        flamethrower.type_50.displayed_attack = 6
        flamethrower.creatable.train_locations[0].hot_key_id = 16107
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
        weichafe.creatable.train_locations[0].hot_key_id = 16107
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

        # Crusader
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

        # Elite Crusader
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

        # Tomahawk Warrior
        tomahawk_warrior = copy.deepcopy(DATA.civs[1].units[1374])
        change_string(112000, 'Tomahawk Warrior')
        change_string(113000, 'Create Tomahawk Warrior')
        tomahawk_warrior.language_dll_name = 112000
        tomahawk_warrior.language_dll_creation = 113000
        tomahawk_warrior.type_50.attacks[3].amount = 10
        tomahawk_warrior.name = 'Tomahawk Warrior'
        tomahawk_warrior.creatable.train_locations[0].hot_key_id = 16107
        civ.units.append(tomahawk_warrior)

        # Elite Tomahawk Warrior
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

        # Imperial Elephant Archer
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

        # Lightning Warrior
        '''lightning_warrior = copy.deepcopy(DATA.civs[1].units[749])
        change_string(118000, 'Lightning Warrior')
        change_string(119000, 'Create Lightning Warrior')
        lightning_warrior.language_dll_name = 118000
        lightning_warrior.language_dll_creation = 119000

        lightning_warrior.type_50.attacks.clear()
        lightning_warrior.type_50.attacks.append(AttackOrArmor(4, 5
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

        # Elite Lightning Warrior
        elite_lightning_warrior = copy.deepcopy(lightning_warrior)
        change_string(120000, 'Elite Lightning Warrior')
        change_string(121000, 'Create Elite Lightning Warrior')
        elite_lightning_warrior.language_dll_name = 120000
        elite_lightning_warrior.language_dll_creation = 121000
        elite_lightning_warrior.type_50.attacks[0] = 6
        elite_lightning_warrior.type_50.displayed_attack = 6
        elite_lightning_warrior.hit_points = 45
        elite_lightning_warrior.name = 'Elite Lightning Warrior'
        civ.units.append(elite_lightning_warrior)'''

        # Destroyer
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

        # Elite Destroyer
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

        # Cossack
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

        # Elite Cossack
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

        # Fire Tower
        fire_tower = copy.deepcopy(DATA.civs[1].units[190])
        fire_tower.line_of_sight = 10
        fire_tower.bird.search_radius = 10
        fire_tower.type_50.attacks.append(AttackOrArmor(20, 15))
        fire_tower.creatable.train_locations[0].button_id = 10
        fire_tower.creatable.train_locations[0].hot_key_id = 16156
        fire_tower.name = 'Fire Tower'
        civ.units.append(fire_tower)

        # Junk
        junk = copy.deepcopy(DATA.civs[1].units[15])
        junk.creatable.train_locations = DATA.civs[1].units[17].creatable.train_locations
        junk.creatable.resource_costs = DATA.civs[1].units[17].creatable.resource_costs
        junk.speed = 1.45
        junk.line_of_sight = 6
        junk.bird.search_radius = 6
        junk.type_50.armours[1].amount = 6
        junk.creatable.displayed_pierce_armor = 6
        junk.name = 'Junk'
        civ.units.append(junk)

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

    # Create techs unique to Talofa
    custom_tech_starting_index = len(DATA.techs)
    custom_effect_starting_index = len(DATA.effects)

    # 0: Canoe
    canoe_tech = copy.deepcopy(DATA.techs[151])
    canoe_tech.name = 'Canoe (make avail)'
    canoe_effect = genieutils.effect.Effect(name='Canoe (make avail)', effect_commands=[genieutils.effect.EffectCommand(3, 539, custom_unit_starting_index, -1, -1)])
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
    war_canoe_effect = genieutils.effect.Effect(name='War Canoe', effect_commands=[genieutils.effect.EffectCommand(3, 539, custom_unit_starting_index+1, -1, -1), genieutils.effect.EffectCommand(3, custom_unit_starting_index, custom_unit_starting_index+1, -1, -1)])
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
    elite_war_canoe_effect = genieutils.effect.Effect(name='Elite War Canoe', effect_commands=[genieutils.effect.EffectCommand(3, 539, custom_unit_starting_index+2, -1, -1), genieutils.effect.EffectCommand(3, custom_unit_starting_index, custom_unit_starting_index+2, -1, -1), genieutils.effect.EffectCommand(3, custom_unit_starting_index+1, custom_unit_starting_index+2, -1, -1)])
    DATA.effects.append(elite_war_canoe_effect)
    elite_war_canoe_tech.effect_id = len(DATA.effects)-1
    DATA.techs.append(elite_war_canoe_tech)

    # 3: Junk
    junk_tech = copy.deepcopy(DATA.techs[0])
    junk_tech.name = 'Junk (make avail)'
    junk_effect = genieutils.effect.Effect(name='Junk (make avail)', effect_commands=[genieutils.effect.EffectCommand(3, 17, custom_unit_starting_index+21, -1, -1)])
    DATA.effects.append(junk_effect)
    junk_tech.effect_id = len(DATA.effects)-1
    DATA.techs.append(junk_tech)
    DATA.effects[482].effect_commands.append(genieutils.effect.EffectCommand(5, custom_unit_starting_index+21, -1, 5, 1.2))
    DATA.effects[482].effect_commands.append(genieutils.effect.EffectCommand(5, custom_unit_starting_index+21, -1, 13, 1.2))
    for effect in DATA.effects:
        if "tech tree" in effect.name.lower() and not any(ex in effect.name.lower() for ex in ["chinese", "japanese", "koreans", "jurchens", "wu", "wei", "shu", "vietnamese", "malay", "burmese", "khmer", "mongols"]):
            effect.effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, custom_tech_starting_index+3))

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

    '''fire_tower_tech = copy.deepcopy(DATA.techs[64])
    change_string(84000, 'Fire Tower')
    change_string(85000, 'Upgrade to Fire Tower')
    change_string(86000, r'Build <b>Fire Tower<b> (<cost>)\Fire tower with a powerful ranged attack. Units can garrison inside for protection. Strong vs. everything in range. Weak vs. long range Siege Weapons.')
    fire_tower_tech.language_dll_name = 84000
    fire_tower_tech.language_dll_description = 85000
    fire_tower_effect = genieutils.effect.Effect(name='Fire Tower', effect_commands=[genieutils.effect.EffectCommand(2, get_unit_id('Canoe')+22, 1, -1, -1)])
    DATA.effects.append(fire_tower_effect)
    fire_tower_tech.effect_id = len(DATA.effects)-1
    DATA.techs.append(fire_tower_tech)'''

    # Create new unique Castle unit techs and effects
    for i, tech_id in enumerate([263, 360, 275, 363, 399, 398, 276, 364, 262, 366, 268, 362, 267, 361, 274, 367, 269, 368, 271, 369, 446, 365, 273, 371, 277, 370, 58, 60, 431, 432, 26, 27, 1, 2, 449, 450, 467, 468, 839, 840, 508, 509, 471, 472, 503, 504, 562, 563, 568, 569, 566, 567, 564, 565, 614, 615, 616, 617, 618, 619, 620, 621, 677, 678, 679, 680, 681, 682, 683, 684, 750, 751, 752, 753, 778, 779, 780, 781, 825, 826, 827, 828, 829, 830, 881, 882, 917, 918, 919, 920, 990, 991, 1001, 1002, 1063, 1064, 1035, 1036, 1073, 1074]):
        if i % 2 == 0: # Castle unit techs
            DATA.techs[tech_id].name = f'{DATA.civs[DATA.techs[tech_id].civ].name.upper()}: (Castle Unit)'
            DATA.effects[DATA.techs[tech_id].effect_id].name = f'{DATA.civs[DATA.techs[tech_id].civ].name.upper()}: (Castle Unit)'
        else: # Imperial unit techs
            DATA.techs[tech_id].name = f'{DATA.civs[DATA.techs[tech_id].civ].name.upper()}: (Imperial Unit)'
            DATA.effects[DATA.techs[tech_id].effect_id].name = f'{DATA.civs[DATA.techs[tech_id].civ].name.upper()}: (Imperial Unit)'

    # Set civilisations to canoe docks by disabling all other warships
    for tech_tree_effect_id in tech_tree_indexes:
        if tech_tree_effect_id in [447, 449, 3, 648, 42, 710, 646]: # Canoe dock
            for tech_id in [604, 243, 246, 605, 244, 37, 376]:
                DATA.effects[tech_tree_effect_id].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, float(tech_id)))
            #for tech_id in [240, 34, 35]:
            #    DATA.effects[tech_tree_effect_id].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, float(tech_id)))
        else: # Ship dock
            for tech_id in [custom_tech_starting_index, custom_tech_starting_index+1, custom_tech_starting_index+2]:
                DATA.effects[tech_tree_effect_id].effect_commands.append(genieutils.effect.EffectCommand(102, -1, -1, -1, float(tech_id)))
                
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
    base_tech = genieutils.tech.Tech(name='', required_techs=(0, 0, 0, 0, 0, 0), resource_costs=(ResearchResourceCost(0, 0, 0), ResearchResourceCost(0, 0, 0), ResearchResourceCost(0, 0, 0)), required_tech_count=0, civ=0, full_tech_mode=0, research_location=0, language_dll_name=7000, language_dll_description=8000, research_time=0, effect_id=-1, type=0, icon_id=-1, button_id=0, language_dll_help=107000, language_dll_tech_tree=157000, research_locations=[ResearchLocation(0, 0, 0, 0)], hot_key=-1, repeatable=1)
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
        missed_tech.civ == i
        DATA.techs.append(missed_tech)
        DATA.effects.append(missed_effect)
            

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

    # Write the architecture sets to a file
    with open(f'{MOD_FOLDER}/{mod_name}.pkl', 'wb') as file:
        for civ in DATA.civs:
            pickle.dump(civ.units, file)

    # --- Graphic set maps (same as your menu version) ---
    general_architecture_sets = {
        'West African': 26, 'Austronesian': 29, 'Central Asian': 33,
        'Central European': 4, 'East Asian': 5, 'Eastern European': 23,# 'Islander': 25,
        'Mediterranean': 14, 'Middle Eastern': 9, 'Mesoamerican': 15,
        'South Asian': 20, 'Southeast Asian': 28, 'Southeast European': 47, 'Western European': 1,
        'Mespotamian': 46,
    }
    monk_sets = {
        'Christian': 0, 'Mesoamerican': 15, 'Catholic': 14, 'Buddhist': 5, 'Hindu': 40,
        'Muslim': 9, 'Tengri': 12, 'African': 25, 'Orthodox': 23, 'Pagan': 35
    }
    monastery_sets = {
        'West African': 26, 'Central Asian': 33, 'Central European': 4, 'East Asian': 6,
        'Eastern European': 23, 'Mediterranean': 14, 'Middle Eastern': 9, 'Mesoamerican': 15,
        'South Asian': 40, 'Southeast Asian': 28, 'Western European': 1, 'Eastern African': 25,
        'Southeast European': 7, 'Tengri': 12, 'Pagan': 35, 'Mespotamian': 46, 'Shinto': 5
    }
    trade_cart_sets = {'Horse': 1, 'Human': 15, 'Camel': 9, 'Water Buffalo': 5, 'Ox': 25}
    ship_sets = {"West African": 25, "Central Asian": 33, "Central European": 4, "East Asian": 5,
                "Eastern European": 23, "Mediterranean": 14, "Mesoamerican": 15, "Middle Eastern": 9,
                "Southeast Asian": 28, "Western European": 1}

    # Castle/Wonder sets — reuse your menu version (by civ label)
    castle_sets = {"Britons": 1, "Franks": 2, "Goths": 3, "Teutons": 4, "Japanese": 5, "Chinese": 6,
                "Byzantines": 7, "Persians": 8, "Saracens": 9, "Turks": 10, "Vikings": 11,
                "Mongols": 12, "Celts": 13, "Spanish": 14, "Aztecs": 15, "Maya": 16, "Huns": 17,
                "Koreans": 18, "Italians": 19, "Hindustanis": 20, "Inca": 21, "Magyars": 22,
                "Slavs": 23, "Portuguese": 24, "Ethiopians": 25, "Malians": 26, "Berbers": 27,
                "Khmer": 28, "Malay": 29, "Burmese": 30, "Vietnamese": 31, "Bulgarians": 32,
                "Tatars": 33, "Cumans": 34, "Lithuanians": 35, "Burgundians": 36, "Sicilians": 37,
                "Poles": 38, "Bohemians": 39, "Dravidians": 40, "Bengalis": 41, "Gurjaras": 42,
                "Romans": 43, "Armenians": 44, "Georgians": 45, "Shu": 49, "Wu": 50,
                "Wei": 51, "Jurchens": 52, "Khitans": 53}
    wonder_sets = dict(castle_sets)  # if your template indices align for wonders

    # Keep the order aligned with unit_bank below:
    graphic_titles = ["General", "Castle", "Wonder", "Monk", "Monastery", "Trade Cart", "Ships"]
    graphic_sets = [general_architecture_sets, castle_sets, wonder_sets,
                    monk_sets, monastery_sets, trade_cart_sets, ship_sets]

    # Units affected by each group (same as your menu)
    unit_banks = {
        0: [20, 132, 498, 1413, 1414, 10, 14, 87, 1415, 1416, 86, 101, 153, 1417, 1418, 49, 150, 1425, 1426, 18, 19, 103, 105, 1419, 1420, 47, 51, 133, 806, 807, 808, 2120, 2121, 2122, 2144, 2145, 2146, 209, 210, 1427, 1428, 79, 190, 234, 236, 235, 82, 1430, 191, 192, 463, 464, 465, 1434, 1435, 71, 141, 142, 444, 481, 482, 483, 484, 597, 611, 612, 613, 614, 615, 616, 617, 584, 585, 586, 587, 562, 563, 564, 565, 84, 116, 137, 1422, 1423, 1424, 1646, 129, 130, 131, 1411, 1412, 117, 155, 1508, 1509, 63, 64, 67, 78, 80, 81, 85, 88, 90, 91, 92, 95, 487, 488, 490, 491, 659, 660, 661, 662, 663, 664, 665, 666, 667, 668, 669, 670, 671, 672, 673, 674, 1192, 1406, 1500, 1501, 1502, 1503, 1504, 1505, 1506, 1507, 110, 179, 1647],            # General (all)
        1: [82, 1430],                                   # Castle units (building and rubble)
        2: [276, 1445],                                  # Wonder units
        3: [125, 286, 922, 1025, 1327],                  # Monk units (variants)
        4: [30, 31, 32, 104, 1421],                      # Monastery buildings
        5: [128, 204],                                   # Trade carts
        6: [1103, 529, 532, 545, 17, 420, 691,           # Ships: fire, galley, demo, transport, fish, CG, etc.
            1104, 527, 528, 539, 21, 442]
    }

    # Your presets now need 7 fields (General, Castle, Wonder, Monk, Monastery, Trade Cart, Ships)
    # Empty string means "no change"
    civ_presets = {
        1:  [-1, -1, -1, -1, -1, -1, -1],
        2:  [-1, -1, -1, 19, -1, -1, -1],
        3:  [19, -1, -1, -1, 19, -1, 19],
        4:  [-1, -1, -1, -1, -1, -1, -1],
        5:  [-1, -1, -1, -1, -1, -1, -1],
        6:  [-1, -1, -1, -1, -1, -1, -1],
        7:  [47, -1, -1, -1, -1, -1, -1],
        8:  [33, -1, -1, -1, 33, 1, 33],
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
        20: [9, -1, -1, -1, 9, 9, 9],
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
        31: [-1, -1, -1, 5, -1, -1, 28],
        32: [-1, -1, -1, -1, -1, -1, -1],
        33: [-1, -1, -1, -1, -1, 1, -1],
        34: [-1, -1, -1, -1, -1, 1, -1],
        35: [4, -1, -1, -1, -1, -1, 4],
        36: [-1, -1, -1, -1, -1, -1, -1],
        37: [-1, -1, -1, -1, -1, -1, -1],
        38: [4, -1, -1, -1, 4, -1, 4],
        39: [-1, -1, -1, -1, -1, -1, -1],
        40: [-1, -1, -1, -1, -1, 6, -1],
        41: [-1, -1, -1, 9, -1, -1, -1],
        42: [-1, -1, -1, 40, -1, 9, -1],
        43: [-1, -1, -1, -1, -1, -1, -1],
        44: [47, -1, -1, -1, -1, -1, -1],
        45: [47, -1, -1, -1, -1, -1, -1],
        49: [-1, -1, -1, -1, -1, -1, -1],
        50: [-1, -1, -1, -1, -1, -1, -1],
        51: [-1, -1, -1, -1, -1, -1, -1],
        52: [-1, -1, -1, -1, -1, 1, -1],
        53: [-1, -1, -1, -1, -1, 1, -1],
    }

    # Define the special units
    special_unit_ids = [uid for key, ids in unit_banks.items() if 1 <= key <= 6 for uid in ids]

    for civ_id, civ in enumerate(DATA.civs):
        # Skip civs that don't have a preset
        if civ_id not in civ_presets:
            continue

        # Define the presets
        presets = civ_presets[civ_id]

        for key, unit_bank in unit_banks.items():
            for unit_id in unit_bank:
                if presets[key] == -1:
                    break

                if (key == 0 and unit_id not in special_unit_ids) or key > 0:
                    # General units: apply to all except special units
                    DATA.civs[civ_id].units[unit_id] = DATA.civs[presets[key]].units[unit_id]

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
    edit_tech_tree(get_effect_id('Vietnamese Tech Tree'), [-162, -96, -255, 837, 838])
    edit_tech_tree(get_effect_id('Persians Tech Tree'), [630, 631])

    # Reorder tech trees
    for civ in DATA.civs:
        civ_tech_tree_index = -1
        for i, effect in enumerate(DATA.effects):
            if effect.name.lower() == f'{civ.name} tech tree'.lower():
                civ_tech_tree_index = i

        if civ_tech_tree_index == -1:
            continue

        DATA.effects[civ_tech_tree_index].effect_commands.sort(key=lambda ec: ec.d)

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
        import os
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
        print(colour(Fore.WHITE, "1️⃣  Save Civilization"))
        print(colour(Fore.WHITE, "2️⃣  Load Civilization"))
        print(colour(Fore.WHITE, "3️⃣  Open Mod Directory"))
        print(colour(Fore.WHITE, "4️⃣  Revert Mod"))
        mod_menu_selection = input(colour(Fore.CYAN, "Selection: "))

        # Save Civilisation
        if mod_menu_selection == '1':
            # Display all civilisations
            selected_civ_index = -1
            all_civs = []
            with open(MOD_STRINGS, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                for civ in DATA.civs:
                    if civ.name not in ('Gaia', 'Athenians', 'Spartans', 'Achaemenids'):
                        all_civs.append(civ.name)

                while True:
                    while True:
                        readline.set_completer(make_completer(all_civs))
                        readline.parse_and_bind("tab: complete")
                        selection = input("\nEnter Civilization ID/Name to save: ").lower()

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
                            continue

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
                    description_lines = file.readlines()

                    # Get the index of the  civ
                    for i, line in enumerate(description_lines):
                        if selected_civ_name.lower() in line.lower():
                            description_index = i

                    # Find the description
                    description = description_lines[description_index + len(DATA.civs) - 1].split(' "')[1].replace('"', '').replace('\n', '')

                # Make sure "civs" folder exists
                civs_dir = Path("civs")
                civs_dir.mkdir(parents=True, exist_ok=True)

                # Build your file path inside that folder
                outfile = civs_dir / f'{selected_civ_name}.txt'

                # Check to see if the file already exists and warn the user about overwriting the file
                if outfile.exists():
                    overwrite = input(colour(Fore.YELLOW, f'WARNING: "{selected_civ_name}" already exists. Overwrite? (y/n): '))
                    if overwrite.lower() != 'y':
                        print('File not overwritten.\n')
                        continue

                # Get the componets to save
                save_name = selected_civ_name
                save_the_description = description
                save_techs = [tech for tech in DATA.techs if tech.name.startswith(selected_civ_name.upper())]
                save_effects = [effect for effect in DATA.effects if effect.name.startswith(selected_civ_name.upper())]
                save_tech_tree = [effect for effect in DATA.effects if effect.name.lower() == f'{selected_civ_name} tech tree'.lower()][0]
                save_team_bonus = [effect for effect in DATA.effects if effect.name.lower() == f'{selected_civ_name} team bonus'.lower()][0]
                save_scout = DATA.civs[selected_civ_index].resources[263]
                save_language = 'NONE'
                for sound_item in DATA.sounds[303].items:
                    if sound_item.civilization == selected_civ_index + 1:
                        save_language = sound_item.filename.split('_')[0]
                        break
                save_graphics = DATA.civs[selected_civ_index].units
                
                # Create the file unpickled
                with open(outfile, "wb") as file:
                    file.write(f'{save_name}\n'.encode('utf-8'))
                    file.write(f'{save_the_description}\n'.encode('utf-8'))
                    file.write(f'{save_techs}\n'.encode('utf-8'))
                    file.write(f'{save_effects}\n'.encode('utf-8'))
                    file.write(f'{save_tech_tree}\n'.encode('utf-8'))
                    file.write(f'{save_team_bonus}\n'.encode('utf-8'))
                    file.write(f'{save_scout}\n'.encode('utf-8'))
                    file.write(f'{save_language}\n'.encode('utf-8'))
                    file.write(f'{save_graphics}\n'.encode('utf-8'))

                print(colour(Fore.GREEN, f'"{selected_civ_name}.txt" saved successfully!\n'))
                time.sleep(1)

        # Load Civilisation
        if mod_menu_selection == '2':
            # Load the civs from the folder
            loaded_civs = []
            civs_dir = Path("civs")
            if civs_dir.exists() and civs_dir.is_dir():
                for file in civs_dir.iterdir():
                    if file.suffix in (".txt", ".pkl"):
                        loaded_civs.append(file.stem)  # stem = filename without extension

            # Check if there are no civs
            if len(loaded_civs) == 0:
                print(colour(Fore.RED, 'ERROR: There are no civilization files to load.'))
                return
            
            # Prompt user input
            while True:
                readline.set_completer(make_completer(loaded_civs))
                readline.parse_and_bind("tab: complete")
                loaded_civ = input('\nEnter civilization name to load: ').title()

                if loaded_civ == '':
                    break

                if loaded_civ not in loaded_civs:
                    print(colour(Fore.RED, f'ERROR: No civilization file named {loaded_civ} found!'))
                    continue

                # Check if the civ already exists in the dataset
                if loaded_civ.lower() in [civ.name.lower() for civ in DATA.civs]:
                    replace_response = input(colour(Fore.RED, f'WARNING: A civilization named {loaded_civ} already exists. It will be replaced. Continue? y/n: '))
                    if replace_response.lower() != 'y':
                        # Go back to prompt loop if user declines
                        continue

                else:
                    # Ask for which civ to map over
                    all_civs = []
                    for civ in DATA.civs:
                        all_civs.append(civ.name)
                    while True:
                        map_over_civ = input('Enter current civilization to map over: ')

                        # Show all civs
                        if map_over_civ == '?':
                            for i, civ in enumerate(all_civs):
                                print(f'{i}: {civ.title()}')
                            print('\n')
                        elif map_over_civ == '':
                            break

                        try:
                            # Take the index of the civilization
                            map_over_civ = int(map_over_civ)

                            if map_over_civ < 0 or map_over_civ > len(all_civs):
                                print(colour(Fore.RED, 'ERROR: Invalid civilization index.'))
                                continue

                            # Convert index to name
                            map_over_civ = all_civs[map_over_civ + 1]
                            break
                        except:
                            # Take the name of the civilization
                            if map_over_civ.lower() not in [c.lower() for c in all_civs]:
                                print(colour(Fore.RED, 'ERROR: Invalid civilization name.'))
                                continue

                            # Prevent overwriting with itself
                            if map_over_civ.lower() == loaded_civ.lower():
                                print(colour(Fore.RED, f'ERROR: Civilization named {loaded_civ} is the one being loaded. You must choose a different civ to map over.'))
                                continue
                            break

                    # Separate the description to be edited later
                    selected_civ_index = all_civs.index(map_over_civ)
                    with open(MOD_STRINGS, 'r', encoding='utf-8') as file:
                        lines = file.readlines()
                        line_index = selected_civ_index + len(DATA.civs) - 1
                        line = lines[line_index]
                        description_code = line[:6]
                        description_lines = line[8:].split(r'\n')

                        # Remove any unnecessary characters from the strings
                        description_lines = [s.replace('"', '') for s in description_lines]
                        description_lines = [s.replace('\n', '') for s in description_lines]

                    # Open the saved civilisation file
                    civs_dir = Path("civs")
                    file_path = civs_dir / f"{loaded_civ}.txt"
                    with open(file_path, "r", encoding="utf-8") as file:
                        loaded_civ_lines = [line.strip() for line in file.readlines()]

                    # Map over the civilisation
                    map_over_response = input(colour(Fore.RED, f'WARNING: Once the {loaded_civ} is saved, the {map_over_civ} will no longer be playable. Do you wish to continue? y/n: '))
                    if map_over_response == 'y':
                        # Name
                        DATA.civs[selected_civ_index].name = loaded_civ
                        with open(MOD_STRINGS, 'r+', encoding='utf-8') as file:
                            lines = file.readlines()  # Read all lines

                            # Replace the Name and Description
                            for i, line in enumerate(lines):
                                if map_over_civ.lower() in line.lower():
                                    lines[i] = lines[i].replace(map_over_civ, loaded_civ)
                                    parts = lines[i + len(DATA.civs) - 1].split('"')
                                    lines[i + len(DATA.civs) - 1] = f'{parts[0]}"{loaded_civ_lines[1].strip()}"\n'
                                    break

                            file.seek(0)  # Move to the beginning of the file
                            file.writelines(lines)  # Write all lines back

                        # Change name of tech tree, team bonus, civilization bonus effects, and unique units
                        for i, effect in enumerate(DATA.effects):
                            if effect.name == f'{map_over_civ.title()} Tech Tree':
                                effect.name = f'{loaded_civ.title()} Tech Tree'
                            elif effect.name == f'{map_over_civ.title()} Team Bonus':
                                effect.name = f'{loaded_civ.title()} Team Bonus'
                            elif f'{map_over_civ.upper()}' in effect.name:
                                name_list = effect.name.split(':')
                                name_list[0] = loaded_civ.upper()
                                effect.name = ':'.join(name_list)

                        # Change the name of the bonus techs and unique units
                        for i, tech in enumerate(DATA.techs):
                            if f'{map_over_civ.upper()}' in tech.name:
                                name_list = tech.name.split(':')
                                name_list[0] = loaded_civ.upper()
                                tech.name = ':'.join(name_list)

                        # Disable the old techs
                        for old_tech in [tech for tech in DATA.techs if tech.name.startswith(map_over_civ.upper())]:
                            if 'Castle Unit' not in old_tech.name and 'Imperial Unit' not in old_tech.name:
                                old_tech.effect_id = -1

                        # Add the new effects
                        for new_tech in loaded_civ_lines[3]:
                            pass

                        # Add the new techs and pair them to the new effects
                        for new_tech in loaded_civ_lines[2]:
                            pass

                        '''# Replace the tech tree and team bonus
                        for effect in DATA.effects:
                            if effect.name.lower() == f'{map_over_civ} tech tree'.lower():
                                effect = loaded_civ_lines[4]
                            elif effect.name.lower() == f'{map_over_civ} team bonus'.lower():
                                effect = loaded_civ_lines[5]

                        # Change the scout unit
                        DATA.civs[selected_civ_index].resources = float(loaded_civ_lines[6])

                        # Change the language
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
                                        new_name[0] = loaded_civ_lines[7]
                                        item.filename = '_'.join(new_name)

                        # Change the graphics
                        for i, unit in enumerate(DATA.civs[selected_civ_index].units):
                            unit = loaded_civ_lines[8][i]'''
                    else:
                        return
                '''else:
                    print(colour(Fore.RED, f'ERROR: No civilization file named {loaded_civ.title()} found!'))'''

                # Save changes
                with_real_progress(lambda progress: save_dat(progress, rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat'), 'Saving Mod', total_steps=100)
                print(f"{loaded_civ} loaded.")
                time.sleep(1)
                break

        # Open Mod Directory
        if mod_menu_selection == '3':
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
        elif mod_menu_selection == '4':
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
                        selection = input("\nEnter Civilization ID/Name to edit: ").lower()

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
                            continue

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
                            # KEY: (house: 463)
                            architecture_sets = {8916: 'West African', 10909: 'Austronesian', 11909: 'Central Asian', 2206: 'Central European', 2207: 'East Asian', 7909: 'Eastern European', 9202: 'Mediterranean', 2208: 'Middle Eastern', 6909: 'Mesoamerican', 9909: 'South Asian', 10916: 'Southeast Asian', 14251: 'Southeast European', 2209: 'Western European', 14728: 'Persian'}
                            try:
                                if DATA.civs[selected_civ_index + 1].units[463].standing_graphic[0] in architecture_sets:
                                    return architecture_sets[DATA.civs[selected_civ_index + 1].units[463].standing_graphic[0]]
                                else:
                                    return '' 
                            except Exception as e:
                                pass

                        # Get current language
                        current_language = ''
                        for sound_item in DATA.sounds[301].items:
                            if sound_item.civilization == selected_civ_index + 1:
                                try:
                                    current_language = sound_item.filename.split('_')[0]
                                except:
                                    print(sound_item.filename.split('_'))
                                    current_language = 'FAILED'
                                break

                        # Print the civilization menu
                        print(colour(Back.CYAN, Style.BRIGHT, f'\n{title_emoji} Edit {selected_civ_name} {title_emoji}'))
                        print(colour(Fore.WHITE, f"0️⃣  Name") + f" -- {colour(Fore.BLUE, selected_civ_name)}")
                        print(colour(Fore.WHITE, f"1️⃣  Title") + f" -- {colour(Fore.BLUE, description_lines[0])}")
                        print(colour(Fore.WHITE, f"2️⃣  Bonuses"))
                        print(colour(Fore.WHITE, f"3️⃣  Unique Unit") + f" -- {colour(Fore.BLUE, current_unique_unit)}")
                        print(colour(Fore.WHITE, f"4️⃣  Unique Techs") + f" -- {colour(Fore.BLUE, current_unique_techs)}")
                        print(colour(Fore.WHITE, f"5️⃣  Graphics"))
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
                                if remove_accents(civ.name.lower()) == remove_accents(new_name.lower()):
                                    print("\033[31mERROR: Civilization name already assigned to another civilization.\033[0m")
                                    name_exists = True
                                    break

                            if new_name != '' and new_name != selected_civ_name and not name_exists:
                                # Change name
                                DATA.civs[edit_civ_index + 1].name = new_name
                                with open(MOD_STRINGS, 'r+', encoding='utf-8') as file:
                                    lines = file.readlines()  # Read all lines
                                    lines[selected_civ_index] = lines[selected_civ_index][:5] + f' "{new_name}"\n'  # Modify the specific line
                                    selected_civ_name = remove_accents(new_name)  # Update the selected civ name

                                    file.seek(0)  # Move to the beginning of the file
                                    file.writelines(lines)  # Write all lines back

                                # Change name of tech tree, team bonus, civilization bonus effects, and unique units
                                for i, effect in enumerate(DATA.effects):
                                    if effect.name == f'{old_name.title()} Tech Tree':
                                        effect.name = f'{selected_civ_name.title()} Tech Tree'
                                    elif effect.name == f'{old_name.title()} Team Bonus':
                                        effect.name = f'{selected_civ_name.title()} Team Bonus'
                                    elif f'{old_name.upper()}' in effect.name:
                                        name_list = effect.name.split(':')
                                        name_list[0] = new_name.upper()
                                        effect.name = ':'.join(name_list)

                                # Change the name of the bonus techs and unique units
                                for i, tech in enumerate(DATA.techs):
                                    if f'{old_name.upper()}' in tech.name:
                                        name_list = tech.name.split(':')
                                        name_list[0] = new_name.upper()
                                        tech.name = ':'.join(name_list)

                                # Update the name
                                with_real_progress(lambda progress: save_dat(progress, rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat'), 'Saving Mod', total_steps=100)
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
                            if new_title.lower().endswith('civilization') or new_title.lower().endswith('civilisation'):
                                new_title = new_title[:-12].strip()

                            # Apply the Civilization ending
                            description_lines[0] = new_title + ' civilization'

                            # Update the description
                            save_description(description_code, description_lines)
                            print(f'Title updated for {selected_civ_name} to {description_lines[0]}')
                            time.sleep(1)

                        # Bonuses
                        elif selection == '2':
                            save = ''

                            # Make a working copy of the description lines for live preview/editing
                            # (assumes description_code and description_lines are already defined above)
                            original_description = list(description_lines)
                            working_description = list(description_lines)

                            while True:
                                with open(MOD_STRINGS, 'r+', encoding='utf-8') as file:
                                    # Build the visible menu from the working copy (not from disk)
                                    # working_description is already a list of lines like:
                                    # [<civ name>, '', '• bonus 0', '• bonus 1', ..., '', 'Team Bonus', 'Team bonus text']
                                    print(colour(Back.CYAN, Style.BRIGHT, f'\n{title_emoji} Bonuses Menu{save} {title_emoji}'))

                                    # Render current bonuses from working_description
                                    # Bonuses start at index 2 until we hit an empty line / "Unique" / "Team Bonus"
                                    bonus_indices = []
                                    searching_for_dots = True
                                    next_line_is_team = False
                                    for i, line in enumerate(working_description):
                                        if 'Unique' in line:
                                            searching_for_dots = False
                                        elif line.startswith('•') and searching_for_dots:
                                            print(f"\033[33m{len(bonus_indices)}: {line[2:]}\033[0m")
                                            bonus_indices.append(i)
                                        elif 'Team Bonus' in line:
                                            next_line_is_team = True
                                        elif next_line_is_team:
                                            # Show current team bonus
                                            print(f"\033[33mTeam Bonus: {line}\033[0m")
                                            next_line_is_team = False

                                    bonus_selection = input("Bonus action: ")

                                    # Help
                                    if bonus_selection == '?':
                                        print('\n\x1b[35mEnter bonus description to add a new bonus.\x1b[0m')
                                        print('\x1b[35mEnter existing bonus index number to remove that bonus.\x1b[0m')
                                        print('\x1b[35mEnter existing bonus index, a colon (:), and then the bonus description to change an existing bonus.\x1b[0m')
                                        print('\x1b[35mEnter \"t:\" followed by the bonus description to change the team bonus.\x1b[0m')
                                        time.sleep(1)
                                        continue

                                    # Quit — only persist if we have pending changes
                                    if bonus_selection == '':
                                        if save == '*':
                                            # Persist description text once, now
                                            save_description(description_code, working_description)

                                            # Persist .dat
                                            with_real_progress(
                                                lambda progress: save_dat(progress, rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat'),
                                                'Saving Mod',
                                                total_steps=100
                                            )
                                            print('Tech tree updated.')
                                            time.sleep(1)

                                            # Update the in-memory baseline to match file
                                            description_lines[:] = working_description
                                        else:
                                            # Revert in-memory description if user quits without saving
                                            working_description = list(original_description)
                                        break

                                    # Remove bonus by index
                                    elif bonus_selection.isdigit():
                                        if len(bonus_indices) <= 1:
                                            print(colour(Fore.RED, 'ERROR: Civilization must have at least 1 civilization bonus.'))
                                            time.sleep(1)
                                            continue

                                        idx_num = int(bonus_selection)
                                        if idx_num < 0 or idx_num >= len(bonus_indices):
                                            print(colour(Fore.RED, 'ERROR: Invalid bonus index.'))
                                            time.sleep(1)
                                            continue

                                        # Resolve the actual line index inside working_description
                                        line_idx = bonus_indices[idx_num]
                                        bonus_text = working_description[line_idx][2:]  # strip "• "

                                        remove_check = input(f'\nAre you sure you want to remove bonus {idx_num}: {bonus_text}? (y/n): ')
                                        if remove_check.lower() in ('y', 'yes', 'ye'):
                                            # Unpair effect from tech
                                            for tech in DATA.techs:
                                                if tech.name.lower() == f'{selected_civ_name.upper()}: {bonus_text}'.lower():
                                                    tech.effect_id = -1

                                            # Remove from working description (visual preview)
                                            working_description.pop(line_idx)

                                            print(f'Bonus removed for {selected_civ_name}: {bonus_text}')
                                            save = '*'
                                            time.sleep(1)

                                    # Team bonus: t:<desc> / team bonus:<desc> / team:<desc>
                                    elif bonus_selection.lower().startswith(('team bonus:', 't:', 'team:')):
                                        team_text_original = bonus_selection.split(':', 1)[1].strip()
                                        team_text = team_text_original.lower()

                                        # Generate team bonus effect
                                        bonus_tech, bonus_effect = create_bonus(team_text, selected_civ_index)

                                        # Only bail if create_bonus returned nothing at all
                                        if not bonus_effect:
                                            print(colour(Fore.RED, 'ERROR: Could not generate team bonus effect.'))
                                            break

                                        if ' age' in team_text_original.lower():
                                            print(colour(Fore.RED, 'ERROR: Team Bonus cannot contain Age parameters.'))
                                            break

                                        # Find the existing team effect (case-insensitive match)
                                        team_bonus_effect = None
                                        for effect in DATA.effects:
                                            if effect.name.lower() == f'{selected_civ_name.lower()} team bonus':
                                                team_bonus_effect = effect
                                                break

                                        # Update effect in memory
                                        if team_bonus_effect:
                                            team_bonus_effect.effect_commands = bonus_effect[0].effect_commands
                                        else:
                                            print(colour(Fore.YELLOW, f'WARNING: No effect found for {selected_civ_name} Team Bonus'))

                                        # Update team bonus text in working_description
                                        team_label_idx = None
                                        for i, line in enumerate(working_description):
                                            if line.strip().lower().startswith('team bonus'):
                                                team_label_idx = i
                                                break

                                        if team_label_idx is not None and team_label_idx + 1 < len(working_description):
                                            working_description[team_label_idx + 1] = team_text_original.capitalize()

                                            # Persist change to MOD_STRINGS
                                            with open(MOD_STRINGS, 'r+', encoding='utf-8') as f:
                                                lines = f.readlines()
                                                line_index = selected_civ_index + len(DATA.civs) - 1

                                                # Debug: show which line is about to be replaced
                                                print(f'Updating MOD_STRINGS line {line_index}: {lines[line_index]}')

                                                lines[line_index] = f'{lines[line_index][:6]}"{"\\\\n".join(working_description)}"\n'
                                                f.seek(0)
                                                f.writelines(lines)
                                                f.truncate()

                                        print(f'Team bonus changed for {selected_civ_name}.')
                                        save = '*'
                                        time.sleep(1)

                                    # Change existing bonus: "<index>:<new text>"
                                    elif len(bonus_selection) > 2 and bonus_selection[0].isdigit() and bonus_selection[1] == ':':
                                        idx_num = int(bonus_selection[0])
                                        if idx_num < 0 or idx_num >= len(bonus_indices):
                                            print(colour(Fore.RED, 'ERROR: Invalid bonus index.'))
                                            time.sleep(1)
                                            continue

                                        new_text = bonus_selection[2:].strip()
                                        line_idx = bonus_indices[idx_num]
                                        old_text = working_description[line_idx][2:]  # strip "• "

                                        # Generate the new bonus
                                        bonus_tech, bonus_effect = create_bonus(new_text.lower(), selected_civ_index)
                                        if bonus_effect == []:
                                            break

                                        # Disable old effect
                                        for tech in DATA.techs:
                                            if tech.name == f'{selected_civ_name.upper()}: {old_text}':
                                                tech.effect_id = -1

                                        # Replace effect
                                        effect_index = None
                                        for i, effect in enumerate(DATA.effects):
                                            if selected_civ_name.lower() in effect.name.lower() and old_text in effect.name:
                                                effect_index = i
                                                break
                                        if effect_index is not None:
                                            DATA.effects[effect_index] = bonus_effect
                                            DATA.effects[effect_index].name = f'{selected_civ_name.upper()}: {new_text}'

                                        # Replace tech
                                        for j, tech in enumerate(DATA.techs):
                                            if tech.civ == selected_civ_index + 1 and old_text in tech.name:
                                                DATA.techs[j] = bonus_tech[0]
                                                DATA.techs[j].name = f'{selected_civ_name.upper()}: {new_text}'
                                                if effect_index is not None:
                                                    DATA.techs[j].effect_id = effect_index
                                                break

                                        # Update preview text
                                        working_description[line_idx] = f'• {new_text}'

                                        print(f'Bonus {idx_num} changed for {selected_civ_name}.')
                                        save = '*'
                                        time.sleep(1)

                                    # Add new bonus (free text)
                                    else:
                                        bonus_text_original = bonus_selection
                                        bonus_text = bonus_text_original.lower()

                                        # Generate bonus
                                        bonus_techs, bonus_effects = create_bonus(bonus_text, selected_civ_index)

                                        # Add tech/effects in memory
                                        for effect in bonus_effects:
                                            DATA.effects.append(effect)
                                        for tech in bonus_techs:
                                            DATA.techs.append(tech)

                                        # Insert new bullet line into bonuses block in preview
                                        inserted = False
                                        seen_bullets = False
                                        for i, line in enumerate(working_description):
                                            if line.startswith('•'):
                                                seen_bullets = True
                                            elif line == '' and seen_bullets:
                                                working_description.insert(i, f'• {bonus_text_original}')
                                                inserted = True
                                                break
                                        if not inserted:
                                            # Fallback: append near top if structure is unexpected
                                            working_description.insert(2, f'• {bonus_text_original}')

                                        print('Bonus added.')
                                        save = '*'
                                        time.sleep(1)

                        # Unique Unit
                        elif selection == '3':
                            # Populate all castle units
                            ALL_CASTLE_UNITS = ["longbowman", "throwing axeman", "berserk", "teutonic knight", "samurai", "chu ko nu", "cataphract", "war elephant", "mameluke", "janissary", "huskarl", "mangudai", "woad raider", "conquistador", "jaguar warrior", "plumed archer", "tarkan", "war wagon", "genoese crossbowman", "ghulam", "kamayuk", "magyar huszar", "boyar", "organ gun", "shotel warrior", "gbeto", "camel archer", "ballista elephant", "karambit warrior", "arambai", "rattan archer", "konnik", "keshik", "kipchak", "leitis", "coustillier", "serjeant", "obuch", "hussite wagon", "urumi swordsman", "ratha (melee)", "chakram thrower", "centurion", "composite bowman", "monaspa", 'iron pagoda', 'liao dao', 'white feather guard', 'tiger cavalry', 'fire archer', "amazon warrior", "amazon archer", "camel raider", "crusader", "tomahawk warrior", "ninja", "scimitar warrior", "drengr", "qizilbash warrior", 'genitour', 'naasiri', 'elephant gunner', 'flamethrower', 'weichafe', 'destroyer', 'lightning warrior', 'cossack']

                            # Get user input
                            while True:
                                new_castle_unit = input(f"\nEnter unique Castle unit for {selected_civ_name}: ").lower()

                                if new_castle_unit == '?':
                                    print(ALL_CASTLE_UNITS)
                                elif new_castle_unit == '':
                                    break
                                elif new_castle_unit not in ALL_CASTLE_UNITS:
                                    print("\033[31mERROR: Unit not found.\033[0m")
                                else:
                                    break

                            # Get castle unit and imperial unit (upgrade) techs and effects
                            castle_unit_tech = DATA.techs[get_tech_id(f'{selected_civ_name}: (Castle Unit)')]
                            castle_unit_effect = DATA.effects[castle_unit_tech.effect_id]
                            imperial_unit_tech = DATA.techs[get_tech_id(f'{selected_civ_name}: (Imperial Unit)')]
                            imperial_unit_effect = DATA.effects[imperial_unit_tech.effect_id]

                            # Get the original costs from the .dat file
                            elite_upgrade_cost = [0, 0, 0] # Food, Wood, Gold
                            for resource_cost in imperial_unit_tech.resource_costs:
                                # Correct for gold index
                                resource_index = resource_cost.type
                                if resource_index == -1:
                                    continue
                                elif resource_index == 3:
                                    resource_index = 2

                                elite_upgrade_cost[resource_index] = resource_cost.amount

                            # Rename the upgrade tech and effect
                            change_string(imperial_unit_tech.language_dll_name, f'Elite {new_castle_unit.title()}')
                            change_string(imperial_unit_tech.language_dll_description, f'Upgrade to Elite {new_castle_unit.title()}')
                            change_string(imperial_unit_tech.language_dll_help, rf'Upgrade to <b>Elite {new_castle_unit.title()}<b> (<cost>)\nUpgrades your {new_castle_unit.title()} and lets you create Elite {new_castle_unit.title()}, which are stronger and better armored.')

                            # Get user input for cost
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
                            for resource_cost in imperial_unit_tech.resource_costs:
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

                                    imperial_unit_tech.resource_costs[i].type = i + gold_correction
                                    imperial_unit_tech.resource_costs[i].amount = cost
                                    imperial_unit_tech.resource_costs[i].flag = 1
                                    resource_cost_index += 1

                            # Change research time
                            while True:
                                try:
                                    new_time = int(prompt(f"Enter research time in seconds for elite upgrade: ", default=str(imperial_unit_tech.research_time)))
                                    if new_time == '':
                                        new_time = imperial_unit_tech.research_locations[0].research_time
                                    imperial_unit_tech.research_locations[0].research_time = new_time
                                    break
                                except:
                                    print(f'\033[31mERROR: Invalid research time entry.\n\033[0m\n')

                            # Get unit indexes
                            castle_unit_id = get_unit_id(new_castle_unit, False)
                            imperial_unit_id = get_unit_id(f'elite {new_castle_unit}', False)

                            # Correct for inccorect unit ID assignment
                            if castle_unit_id == 886:
                                castle_unit_id = 755
                            elif castle_unit_id == 188:
                                castle_unit_id = 2389
                            elif imperial_unit_id == 887:
                                imperial_unit_id = 757

                            # Change the effect commands
                            for effect in DATA.effects:
                                if effect.name == f'{selected_civ_name.upper()}: (Castle Unit)':
                                    castle_unit_effect.effect_commands[0].a = castle_unit_id
                                elif effect.name == f'{selected_civ_name.upper()}: (Imperial Unit)':
                                    imperial_unit_effect.effect_commands[0].a = castle_unit_id
                                    imperial_unit_effect.effect_commands[0].b = imperial_unit_id

                            # Change units in elite upgrade effect
                            #elite_upgrade_effect.effect_commands.clear()
                            #elite_upgrade_effect.effect_commands.append(genieutils.effect.EffectCommand(3, castle_unit_indexes[2], castle_unit_indexes[3], -1, 0))

                            # Assemble unit classes
                            classes = {0: 'archer', 6: 'infantry', 12: 'cavalry', 13: 'siege', 18: 'monk', 23: 'mounted gunner', 36: 'mounted archer', 38: 'archer', 44: 'hand cannoneer', 55: 'siege weapon'}
                            try:
                                unit_class = classes[DATA.civs[1].units[castle_unit_id].class_]
                            except:
                                unit_class = 'unknown'
                                print(DATA.civs[1].units[castle_unit_id].class_)

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
                            # ---------- helpers ----------
                            def read_costs_from_tech(tech_obj):
                                """Return [food, wood, gold, time] from a DATA.techs[*] object."""
                                food = wood = gold = 0
                                # Try both common time field names
                                time_val = getattr(tech_obj, "research_time", None)
                                if time_val is None:
                                    time_val = getattr(tech_obj, "research", 0)

                                # resource_cost.type : 0=Food, 1=Wood, 3=Gold in your codebase
                                for rc in getattr(tech_obj, "resource_costs", []):
                                    try:
                                        t = int(getattr(rc, "type", -1))
                                        amt = int(getattr(rc, "amount", 0))
                                    except Exception:
                                        continue
                                    if t == 0:
                                        food = amt
                                    elif t == 1:
                                        wood = amt
                                    elif t == 3:
                                        gold = amt
                                return [food, wood, gold, int(time_val or 0)]

                            def write_costs_to_tech(tech_obj, costs):
                                """Apply [food, wood, gold, time] to a DATA.techs[*] object."""
                                f, w, g, t = costs
                                # Update resource costs if entries exist
                                types_seen = set()
                                for rc in getattr(tech_obj, "resource_costs", []):
                                    tcode = getattr(rc, "type", None)
                                    if tcode == 0:
                                        rc.amount = int(f); types_seen.add(0)
                                    elif tcode == 1:
                                        rc.amount = int(w); types_seen.add(1)
                                    elif tcode == 3:
                                        rc.amount = int(g); types_seen.add(3)

                                # If any of Food/Wood/Gold entries are missing, we won't synthesize new rc objects
                                # (your data model likely defines a specific class/constructor). Safe no-op.

                                # Research time (try both common attributes)
                                if hasattr(tech_obj, "research_time"):
                                    setattr(tech_obj, "research_time", int(t))
                                elif hasattr(tech_obj, "research"):
                                    setattr(tech_obj, "research", int(t))

                            def prompt_costs(label, defaults):
                                """Prompt with defaults; require exactly 4 ints; clamp negatives to 0; return list of 4 ints."""
                                df, dw, dg, dt = list(defaults)  # copy to list
                                while True:
                                    raw = prompt(
                                        f'Enter {label} tech costs [Food Wood Gold Time]: ',
                                        default=f'{df} {dw} {dg} {dt}'
                                    ).strip()

                                    # Keep defaults
                                    if raw == '':
                                        return [df, dw, dg, dt]

                                    # Parse user input
                                    parts = raw.replace(',', ' ').split()
                                    if len(parts) != 4:
                                        print('\033[31mERROR: Please enter exactly 4 integers [Food Wood Gold Time].\033[0m')
                                        continue

                                    try:
                                        vals = [max(0, int(p)) for p in parts]  # clamp negatives to 0
                                    except ValueError:
                                        print('\033[31mERROR: All values must be integers.\033[0m')
                                        continue

                                    return vals

                            # ---------- locate current unique techs ----------
                            unique_techs_names = current_unique_techs.split(' / ')
                            unique_techs_ids = [-1, -1]
                            for i, tech in enumerate(DATA.techs):
                                if tech.civ == selected_civ_index + 1 and tech.required_techs[0] == 102 and tech.research_location == 82:
                                    unique_techs_ids[0] = i  # Castle
                                elif tech.civ == selected_civ_index + 1 and tech.required_techs[0] == 103 and tech.research_location == 82:
                                    unique_techs_ids[1] = i  # Imperial

                            # Clone and assign unique effects for each tech (so changes are isolated)
                            # Castle
                            castle_effect_clone = copy.deepcopy(DATA.effects[DATA.techs[unique_techs_ids[0]].effect_id])
                            castle_effect_id = len(DATA.effects)
                            DATA.effects.append(castle_effect_clone)
                            DATA.techs[unique_techs_ids[0]].effect_id = castle_effect_id

                            # Imperial
                            imperial_effect_clone = copy.deepcopy(DATA.effects[DATA.techs[unique_techs_ids[1]].effect_id])
                            imperial_effect_id = len(DATA.effects)
                            DATA.effects.append(imperial_effect_clone)
                            DATA.techs[unique_techs_ids[1]].effect_id = imperial_effect_id

                            # ---------- Castle tech name & description ----------
                            new_castle_tech_name = input(f"\nChange Castle Age tech name: ")
                            if new_castle_tech_name == '':
                                new_castle_tech_name = unique_techs_names[0]

                            prompt_default_text_castle = description_lines[-5].split('(')[1].strip(')')

                            while True:
                                new_castle_tech_description = input(f"Change Castle Age tech description: ")
                                new_castle_tech, new_castle_effect = create_bonus(new_castle_tech_description, selected_civ_index)
                                if len(new_castle_effect[0].effect_commands) == 0 and '*' not in new_castle_tech_description:
                                    print(f'\033[31mERROR: Invalid tech description.\n\033[0m\n')
                                    continue
                                else:
                                    DATA.effects[castle_effect_id].name = new_castle_tech_name
                                    DATA.effects[castle_effect_id].effect_commands = new_castle_effect[0].effect_commands
                                    new_castle_tech_description = new_castle_tech_description.replace('*', '')
                                    break

                            # ---------- Imperial tech name & description ----------
                            new_imperial_tech_name = prompt(f"Change Imperial Age tech name: ")
                            if new_imperial_tech_name == '':
                                new_imperial_tech_name = unique_techs_names[1]

                            prompt_default_text_imperial = description_lines[-4].split('(')[1].strip(')')

                            while True:
                                new_imperial_tech_description = input(f"Change Imperial Age tech description: ")
                                new_imperial_tech, new_imperial_effect = create_bonus(new_imperial_tech_description, selected_civ_index)
                                if len(new_imperial_effect[0].effect_commands) == 0 and '*' not in new_imperial_tech_description:
                                    print(f'\033[31mERROR: Invalid tech description.\n\033[0m\n')
                                    continue
                                else:
                                    DATA.effects[imperial_effect_id].name = new_imperial_tech_name
                                    DATA.effects[imperial_effect_id].effect_commands = new_imperial_effect[0].effect_commands
                                    new_imperial_tech_description = new_imperial_tech_description.replace('*', '')
                                    break

                            # ---------- Costs: prompt with defaults, validate, clamp ----------
                            castle_tech = DATA.techs[unique_techs_ids[0]]
                            imperial_tech = DATA.techs[unique_techs_ids[1]]

                            castle_defaults = read_costs_from_tech(castle_tech)
                            imperial_defaults = read_costs_from_tech(imperial_tech)

                            castle_costs = prompt_costs("Castle", castle_defaults)
                            imperial_costs = prompt_costs("Imperial", imperial_defaults)

                            write_costs_to_tech(castle_tech, castle_costs)
                            write_costs_to_tech(imperial_tech, imperial_costs)

                            # ---------- Strings ----------
                            change_string(DATA.techs[unique_techs_ids[0]].language_dll_name, new_castle_tech_name)
                            change_string(DATA.techs[unique_techs_ids[0]].language_dll_name + 10000, new_castle_tech_name)
                            change_string(DATA.techs[unique_techs_ids[0]].language_dll_description, f"Research {new_castle_tech_name} ({new_castle_tech_description})")
                            change_string(DATA.techs[unique_techs_ids[0]].language_dll_description + 20000, rf"Research <b>{new_castle_tech_name}<b> (<cost>)\n{new_castle_tech_description}.")
                            change_string(DATA.techs[unique_techs_ids[1]].language_dll_name, new_imperial_tech_name)
                            change_string(DATA.techs[unique_techs_ids[1]].language_dll_name + 10000, new_imperial_tech_name)
                            change_string(DATA.techs[unique_techs_ids[1]].language_dll_description, f"Research {new_imperial_tech_name} ({new_imperial_tech_description})")
                            change_string(DATA.techs[unique_techs_ids[1]].language_dll_description + 20000, rf"Research <b>{new_imperial_tech_name}<b> (<cost>)\n{new_imperial_tech_description}.")

                            # ---------- Internal names ----------
                            DATA.techs[unique_techs_ids[0]].name = new_castle_tech_name
                            DATA.techs[unique_techs_ids[1]].name = new_imperial_tech_name

                            # ---------- Update description file ----------
                            description_lines[-5] = f'• {new_castle_tech_name} ({new_castle_tech_description})'
                            description_lines[-4] = f'• {new_imperial_tech_name} ({new_imperial_tech_description})'
                            save_description(description_code, description_lines)

                            # ---------- Save ----------
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

                        # Graphics
                        elif selection == '5':
                            save = ''
                            # Gather all graphics
                            general_architecture_sets = {'Southeast European': 47, 'West African': 26, 'Austronesian': 29, 'Central Asian': 33, 'Central European': 4, 'East Asian': 5, 'Eastern European': 23, 'Mediterranean': 14, 'Middle Eastern': 9, 'Mesoamerican': 15, 'South Asian': 20, 'Southeast Asian': 28, 'Western European': 1, 'Mesopotamian': 46}
                            monk_sets = {'Christian': 0, 'Mesoamerican': 15, 'Catholic': 14, 'Buddhist': 5, 'Hindu': 40, 'Muslim': 9, 'Tengri': 12, 'African': 25, 'Orthodox': 23, 'Pagan': 35}
                            monastery_sets = {'Shinto': 5, 'West African': 26, 'Central Asian': 33, 'Central European': 4, 'East Asian': 6, 'Eastern European': 23, 'Mediterranean': 14, 'Middle Eastern': 9, 'Mesoamerican': 15, 'South Asian': 40, 'Southeast Asian': 28, 'Western European': 1, 'Eastern African': 25, 'Southeast European': 7, 'Tengri': 12, 'Pagan': 35, 'Mesopotamian': 46}
                            trade_cart_sets = {'Horse': 1, 'Human': 15, 'Camel': 9, 'Water Buffalo': 5, 'Ox': 25}
                            ship_sets = {"West African": 25, "Central Asian": 33, "Central European": 4, "East Asian": 5, "Eastern European": 23, "Mediterranean": 14, "Mesoamerican": 15, "Middle Eastern": 9, "Southeast Asian": 28, "Western European": 1}
                            castle_sets = {"Britons": 1, "Franks": 2, "Goths": 3, "Teutons": 4, "Japanese": 5, "Chinese": 6, "Byzantines": 7, "Persians": 8, "Saracens": 9, "Turks": 10, "Vikings": 11, "Mongols": 12, "Celts": 13, "Spanish": 14, "Aztecs": 15, "Maya": 16, "Huns": 17, "Koreans": 18, "Italians": 19, "Hindustanis": 20, "Inca": 21, "Magyars": 22, "Slavs": 23, "Portuguese": 24, "Ethiopians": 25, "Malians": 26, "Berbers": 27, "Khmer": 28, "Malay": 29, "Burmese": 30, "Vietnamese": 31, "Bulgarians": 32, "Tatars": 33, "Cumans": 34, "Lithuanians": 35, "Burgundians": 36, "Sicilians": 37, "Poles": 38, "Bohemians": 39, "Dravidians": 40, "Bengalis": 41, "Gurjaras": 42, "Romans": 43, "Armenians": 44, "Georgians": 45, 'Athenians': 47, 'Achaemenids': 46, "Shu": 49, "Wu": 50, "Wei": 51, "Jurchens": 52, "Khitans": 53}
                            wonder_sets = {"Britons": 1, "Franks": 2, "Goths": 3, "Teutons": 4, "Japanese": 5, "Chinese": 6, "Byzantines": 7, "Persians": 8, "Saracens": 9, "Turks": 10, "Vikings": 11, "Mongols": 12, "Celts": 13, "Spanish": 14, "Aztecs": 15, "Maya": 16, "Huns": 17, "Koreans": 18, "Italians": 19, "Hindustanis": 20, "Inca": 21, "Magyars": 22, "Slavs": 23, "Portuguese": 24, "Ethiopians": 25, "Malians": 26, "Berbers": 27, "Khmer": 28, "Malay": 29, "Burmese": 30, "Vietnamese": 31, "Bulgarians": 32, "Tatars": 33, "Cumans": 34, "Lithuanians": 35, "Burgundians": 36, "Sicilians": 37, "Poles": 38, "Bohemians": 39, "Dravidians": 40, "Bengalis": 41, "Gurjaras": 42, "Romans": 43, "Armenians": 44, "Georgians": 45, 'Athenians': 47, 'Achaemenids': 46, "Shu": 49, "Wu": 50, "Wei": 51, "Jurchens": 52, "Khitans": 53}
                            
                            # Custom Castles
                            for custom_castle in ['Poenari Castle']:
                                castle_sets[custom_castle] = len(castle_sets)

                            # Custom Wonders
                            for custom_wonder in ['Aachen Cathedral', 'Dome of the Rock', 'Dormition Cathedral', 'Gol Gumbaz', 'Minaret of Jam', 'Pyramid', 'Quimper Cathedral', 'Sankore Madrasah', 'Tower of London']:
                                wonder_sets[custom_wonder] = len(wonder_sets)

                            # Combine all dictionaries
                            graphic_sets = [general_architecture_sets, castle_sets, wonder_sets, monk_sets, monastery_sets, trade_cart_sets, ship_sets]

                            # Sort each dictionary by key alphabetically
                            graphic_sets = [dict(sorted(g.items())) for g in graphic_sets]

                            # Get current graphics
                            graphic_titles = ["General", "Castle", "Wonder", 'Monk', 'Monastery', 'Trade Cart', 'Ships']
                            unit_bank = {0: [20, 132, 498, 1413, 1414, 10, 14, 87, 1415, 1416, 86, 101, 153, 1417, 1418, 49, 150, 1425, 1426, 18, 19, 103, 105, 1419, 1420, 47, 51, 133, 806, 807, 808, 2120, 2121, 2122, 2144, 2145, 2146, 209, 210, 1427, 1428, 79, 190, 234, 236, 235, 82, 1430, 191, 192, 463, 464, 465, 1434, 1435, 71, 141, 142, 444, 481, 482, 483, 484, 597, 611, 612, 613, 614, 615, 616, 617, 584, 585, 586, 587, 562, 563, 564, 565, 84, 116, 137, 1422, 1423, 1424, 1646, 129, 130, 131, 1411, 1412, 117, 155, 1508, 1509, 63, 64, 67, 78, 80, 81, 85, 88, 90, 91, 92, 95, 487, 488, 490, 491, 659, 660, 661, 662, 663, 664, 665, 666, 667, 668, 669, 670, 671, 672, 673, 674, 1192, 1406, 1500, 1501, 1502, 1503, 1504, 1505, 1506, 1507, 110, 179, 1647], 1: [82, 1430], 2: [276, 1445], 3: [125, 286, 922, 1025, 1327], 4: [30, 31, 32, 104, 1421], 5: [128, 204], 6: [1103, 529, 532, 545, 17, 420, 691, 1104, 527, 528, 539, 21, 442]}
                            current_graphics = [''] * len(graphic_titles)

                            while True:
                                # Scan the units for their graphics
                                try:
                                    for i, graphic_set in enumerate(graphic_sets):
                                        try:
                                            test_unit = unit_bank[i][0]

                                            for key, value in graphic_set.items():
                                                if DATA.civs[selected_civ_index + 1].units[test_unit].standing_graphic == ARCHITECTURE_SETS[value][test_unit].standing_graphic:
                                                    current_graphics[i] = key
                                                    break
                                        except Exception as e:
                                            etype, evalue, etb = sys.exc_info()
                                            print(f"[ERROR] {etype.__name__}: {e}")
                                            print("Traceback:")
                                            print("".join(traceback.format_exception(etype, evalue, etb)))
                                except:
                                    pass

                                # Show graphics menu
                                print(colour(Back.CYAN, Style.BRIGHT, f'\n{title_emoji} Graphics{save} {title_emoji}'))
                                print(colour(Fore.WHITE, f"0️⃣  Architecture") + f" -- {colour(Fore.GREEN, current_graphics[0])}")
                                print(colour(Fore.WHITE, f"1️⃣  Castle") + f" -- {colour(Fore.GREEN, current_graphics[1])}")
                                print(colour(Fore.WHITE, f"2️⃣  Wonder") + f" -- {colour(Fore.GREEN, current_graphics[2])}")
                                print(colour(Fore.WHITE, f"3️⃣  Monk") + f" -- {colour(Fore.GREEN, current_graphics[3])}")
                                print(colour(Fore.WHITE, f"4️⃣  Monastery") + f" -- {colour(Fore.GREEN, current_graphics[4])}")
                                print(colour(Fore.WHITE, f"5️⃣  Trade Cart") + f" -- {colour(Fore.GREEN, current_graphics[5])}")
                                print(colour(Fore.WHITE, f"6️⃣  Ships") + f" -- {colour(Fore.GREEN, current_graphics[6])}")
                                selection = input(colour(Fore.BLUE, "Selection: "))

                                # Read selection
                                if selection == '':
                                    if save == '*':
                                        with_real_progress(lambda progress: save_dat(progress, rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat'), 'Saving Mod', total_steps=100)
                                        print(f'Graphics for {selected_civ_name} saved.')
                                        time.sleep(1)
                                    break
                                try:
                                    if int(selection) > -1 and int(selection) < len(graphic_sets):
                                        selection = int(selection)
                                    else:
                                        print(f'\033[31mERROR: Invalid selection.\n\033[0m')
                                        continue
                                except:
                                    print(f'\033[31mERROR: Invalid selection.\n\033[0m')
                                    continue

                                # Prompt user
                                change = -1
                                while True:
                                    # Get user input
                                    readline.set_completer(make_completer(graphic_sets[selection]))
                                    readline.parse_and_bind("tab: complete")
                                    if selection in [3, 5, 6]: # Graphics
                                        graphic_selection = input(f"\nEnter {graphic_titles[selection]} graphic for {selected_civ_name}: ").lower()
                                    else: # Architecture
                                        graphic_selection = input(f"\nEnter {graphic_titles[selection]} architecture for {selected_civ_name}: ").lower()

                                    # Help
                                    if graphic_selection == '?':
                                        # Print all available options
                                        for j, arc in enumerate(graphic_sets[selection]):
                                            print(f'{j}: {arc}')
                                        print('Leave blank to default to general graphic.\n')
                                        continue
                                    elif graphic_selection == '':
                                        change = -1
                                        break
                                    else:
                                        # Convert to integer
                                        try:
                                            # Try numeric index
                                            if int(graphic_selection) < len(graphic_sets[selection]):
                                                change = list(graphic_sets[selection].values())[int(graphic_selection)]
                                                break
                                            else:
                                                print(f'\033[31mERROR: {graphic_titles[selection]} graphic index not valid.\n\033[0m')
                                        except ValueError:
                                            # Normalize dictionary for case-insensitive key lookup
                                            normalized_dict = {k.lower(): v for k, v in graphic_sets[selection].items()}
                                            key = graphic_selection.lower()
                                            if key in normalized_dict:
                                                change = normalized_dict[key]
                                                break
                                            else:
                                                print(f'\033[31mERROR: {graphic_titles[selection]} graphic name not valid.\n\033[0m')

                                #print('change:', change)
                                # Convert unit graphics
                                if change > -1:
                                    for unit_id in unit_bank[selection]:
                                        # list of attributes you want to copy
                                        ATTRS = [
                                            "standing_graphic",
                                            "damage_graphics",
                                            "dying_graphic",
                                            "undead_graphic",
                                            "garrison_graphic",
                                            "spawning_graphic",
                                            "upgrade_graphic",
                                            "hero_glow_graphic",
                                            "idle_attack_graphic",
                                            "special_graphic",
                                            "attack_graphic",
                                            "attack_graphic_2",
                                            "working_graphic_id",
                                            "carrying_graphic_id",
                                            "moving_graphic_id",
                                            "proceeding_graphic_id",
                                            "selection_graphics",
                                            "building",
                                        ]

                                        if selection > 0 or unit_id not in [item for key in sorted(unit_bank) if key >= 1 for item in unit_bank[key]]:
                                            for attr in ATTRS:
                                                try:
                                                    setattr(
                                                        DATA.civs[selected_civ_index + 1].units[unit_id],
                                                        attr,
                                                        getattr(ARCHITECTURE_SETS[change][unit_id], attr)
                                                    )
                                                except:
                                                    pass

                                        # Change icon
                                        if selection > 0:
                                            DATA.civs[selected_civ_index + 1].units[unit_id].icon_id = ARCHITECTURE_SETS[change][unit_id].icon_id

                                    print(f"Graphics changed for {selected_civ_name}.")
                                    save = '*'

                                # Update changes
                                else:
                                    print(f"Graphics not changed for {selected_civ_name}.")
                                time.sleep(1)

                        # Language
                        elif selection == '6':
                            while True:
                                # Get input
                                readline.set_completer(make_completer(ALL_LANGUAGES))
                                readline.parse_and_bind("tab: complete")
                                new_language = input(f"\nEnter new language for {selected_civ_name}: ").title()

                                if new_language == '':
                                    print(f"Language for {selected_civ_name} not changed.")
                                    time.sleep(1)
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
                                    time.sleep(1)
                                    break
                                else:
                                    print("\033[31mERROR: Language not found.\033[0m")
                            pass

                        # Tech Tree
                        elif selection == '7':
                            # Import the tech tree
                            save = ''

                            def clear_console():
                                # ANSI clear + home. Works on most terminals.
                                print('\033[2J\033[H', end='')

                            def current_scout_name():
                                scout_bank = {'Scout Cavalry': 448, 'Eagle Scout': 751, 'Camel Scout': 1755}
                                cur_val = DATA.civs[selected_civ_index + 1].resources[263]
                                for k, v in scout_bank.items():
                                    if v == cur_val:
                                        return k
                                return 'Unknown'

                            def render_tree():
                                # Get current disabled list
                                tech_tree_effect_id = -1
                                for i, effect in enumerate(DATA.effects):
                                    if effect.name.lower() == f'{selected_civ_name.lower()} tech tree':
                                        tech_tree_effect_id = i
                                        break

                                if tech_tree_effect_id == -1:
                                    clear_console()
                                    print(colour(Fore.RED, f'ERROR: Cannot find tech tree effect for {selected_civ_name}'))
                                    return None, None

                                disabled_ids = [ec.d for ec in DATA.effects[tech_tree_effect_id].effect_commands]

                                # === Build text (copied from your logic; unchanged) ===
                                branch_text = ''

                                branches = {
                                    'ARCHERY RANGE': [-1],
                                    'Archer/Crossbowman/Arbalester': [151, 100, 237],
                                    'Skirmisher/Elite Skirmisher/Imperial Skirmisher': [99, 98, 655],
                                    'Slinger*0': [528],
                                    'Hand Cannoneer*0': [85],
                                    'Xianbei Raider*1': [1037],
                                    'Elephant Archer*1/Elite Elephant Archer*1': [480, 481],
                                    'Cavalry Archer*1/Heavy Cavalry Archer*1': [192, 218],
                                    'Grenadier': [992],
                                    'Genitour/Elite Genitour': [598, 599],
                                    'Parthian Tactics': [436],
                                    'Thumb Ring': [437],

                                    'BARRACKS': [-1],
                                    'Militia/Man-at-Arms/Long Swordsman/Two-Handed Swordsman*1/Champion*1': [-1, 222, 207, 217, 264],
                                    'Militia/Man-at-Arms/Long Swordsman/Legionary*1': [-1, 222, 207, 885],
                                    'Spearman/Pikeman/Halberdier': [87, 197, 429],
                                    'Eagle Scout/Eagle Warrior/Elite Eagle Warrior': [433, 384, 434],
                                    'Fire Lancer*2/Elite Fire Lancer*2': [981, 982],
                                    'Jian Swordsman*2': [1075],
                                    'Condottiero*2': [522],
                                    'Arson': [602],
                                    'Gambesons': [875],
                                    'Squires': [215],

                                    'STABLE': [25],
                                    'Scout Cavalry/Light Cavalry/Hussar*3': [204, 254, 428],
                                    'Scout Cavalry/Light Cavalry/Winged Hussar*3': [204, 254, 786],
                                    'Xolotl Warrior*3': [318],
                                    'Hei Guang Cavalry*4/Heavy Hei Guang Cavalry*4': [1032, 1033],
                                    'Knight*4/Cavalier*4/Savar*4': [166, 209, 526],
                                    'Knight*4/Cavalier*4/Paladin*4': [166, 209, 265],
                                    'Camel Rider/Heavy Camel Rider/Imperial Camel Rider': [235, 236, 521],
                                    'Steppe Lancer*5/Elite Steppe Lancer*5': [714, 715],
                                    'Battle Elephant*5/Elite Battle Elephant*5': [630, 631],
                                    'Bloodlines': [435],
                                    'Husbandry': [39],

                                    'SIEGE WORKSHOP': [-1],
                                    'Battering Ram*6/Capped Ram*6/Siege Ram*6': [162, 96, 255],
                                    'Armored Elephant*6/Siege Elephant*6': [837, 838],
                                    'Mangonel*7/Onager*7/Siege Onager*7': [358, 257, 320],
                                    'Rocket Cart*7/Heavy Rocket Cart*7': [979, 980],
                                    'Scorpion*8/Heavy Scorpion*8': [94, 239],
                                    'War Chariot*8': [1962],
                                    'Siege Tower': [603],
                                    'Flaming Camel*9': [703],
                                    'Traction Trebuchet*9': [1025],
                                    'Mounted Trebuchet*9': [1005],
                                    'Bombard Cannon*9/Houfnice*9': [188, 787],

                                    'BLACKSMITH': [281],
                                    'Padded Archer Armor/Leather Archer Armor/Ring Archer Armor': [211, 212, 219],
                                    'Fletching/Bodkin Arrow/Bracer': [199, 200, 201],
                                    'Forging/Iron Casting/Blast Furnace': [67, 68, 75],
                                    'Scale Barding Armor/Chain Barding Armor/Plate Barding Armor': [81, 82, 80],
                                    'Scale Mail Armor/Chain Mail Armor/Plate Mail Armor': [74, 76, 77],

                                    'DOCK': [-1],
                                    'Canoe*10/War Canoe*10/Elite War Canoe*10': [get_tech_id('Canoe (make avail)'), get_tech_id('War Canoe'), get_tech_id('Elite War Canoe')],
                                    'Galley*10/War Galley*10/Galleon*10': [240, 34, 35],
                                    'Fire Galley/Fire Ship/Fast Fire Ship': [604, 243, 246],
                                    'Demolition Galley/Demolition Ship/Heavy Demolition Ship': [605, -1, 244],
                                    'Cannon Galleon*11/Elite Cannon Galleon*11': [37, 376],
                                    'Dromon*11': [886],
                                    'Lou Chuan*11': [1034],
                                    'Turtle Ship*12/Elite Turtle Ship*12': [447, 448],
                                    'Thirisadai*12': [841],
                                    'Longboat*12/Elite Longboat*12': [272, 372],
                                    'Caravel*12/Elite Caravel*12': [596, 597],
                                    'Gillnets': [65],
                                    'Careening/Dry Dock': [374, 375],
                                    'Shipwright': [373],

                                    'UNIVERSITY': [-1],
                                    'Masonry/Architecture': [50, 51],
                                    'Palisade Wall/Stone Wall/Fortified Wall': [523, 189, 194],
                                    'Ballistics': [93],
                                    'Watch Tower/Guard Tower/Keep': [127, 140, 63],
                                    'Heated Shot': [380],
                                    'Murder Holes': [322],
                                    'Treadmill Crane': [54],
                                    'Chemistry/Bombard Tower': [47, 64],
                                    'Siege Engineers': [377],
                                    'Arrowslits': [608],
                                    'Krepost*13': [695],
                                    'Donjon*13': [775],

                                    'CASTLE': [-1],
                                    'Trebuchet': [256],
                                    'Petard': [426],
                                    'Hoardings': [379],
                                    'Sappers': [321],
                                    'Conscription': [315],

                                    'FORTIFIED CHURCH*14': [929],
                                    'MONASTERY*14': [-1],
                                    'Monk': [157],
                                    'Missionary*15': [84],
                                    'Warrior Priest*15': [948],
                                    'Devotion/Faith': [46, 45],
                                    'Redemption': [316],
                                    'Atonement': [319],
                                    'Herbal Medicine': [441],
                                    'Heresy': [439],
                                    'Sanctity': [231],
                                    'Fervor': [252],
                                    'Illumination': [233],
                                    'Block Printing': [230],
                                    'Theocracy': [438],

                                    'TOWN CENTER': [-1],
                                    'Loom': [22],
                                    'Town Watch/Town Patrol': [8, 280],
                                    'Wheelbarrow/Hand Cart': [213, 249],

                                    'House': [-1],
                                    'Caravanserai*16': [518],
                                    'Feitoria*16': [570],
                                    'Mining & Lumber Camp*21': [-1],
                                    'Mule Cart*21': [932],
                                    'Mill*18': [-1],
                                    'Folwark*18': [793],
                                    'Farm*19': [216],
                                    'Pasture*19': [1008],
                                    'Gold Mining/Gold Shaft Mining': [55, 182],
                                    'Stone Mining/Stone Shaft Mining': [278, 279],
                                    'Double-Bit Axe/Bow Saw/Two-Man Saw': [202, 203, 221],
                                    'Horse Collar*20/Heavy Plow*20/Crop Rotation*20': [14, 13, 12],
                                    'Domestication*20/Pastoralism*20/Transhumance*20': [1014, 1013, 1012],

                                    'MARKET': [-1],
                                    'Coinage/Banking': [23, 17],
                                    'Caravan': [48],
                                    'Guilds': [15]
                                }

                                keys = list(branches.keys())
                                building_items = []

                                def branch_progress(ids):
                                    length = 0
                                    for u in ids:
                                        if u == -1:
                                            length += 1
                                            continue
                                        if u in disabled_ids:
                                            break
                                        length += 1
                                    return length, len(ids)

                                def pretty_item(items, length, total):
                                    if length == 0:
                                        return colour(Fore.RED, items[length - 1]) + (f'[{length}/{total}]' if total > 1 else '')
                                    return colour(Fore.GREEN, items[length - 1]) + (f'[{length}/{total}]' if total > 1 else '')

                                def base_labels(branch_key):
                                    items = branch_key.split('/')
                                    if '*' in branch_key:
                                        items = [it.split('*')[0] + '*' for it in items]
                                    return items

                                def star_index(branch_key):
                                    if '*' not in branch_key:
                                        return None
                                    tail = branch_key.rsplit('*', 1)[-1]
                                    return int(tail) if tail.isdigit() else None

                                i = 0
                                while i < len(keys):
                                    name = keys[i]
                                    ids = branches[name]

                                    # Building header
                                    if name.isupper():
                                        if building_items:
                                            branch_text += ', '.join(building_items)
                                            building_items = []
                                        if branch_text:
                                            branch_text += '\n'

                                        sidx = star_index(name)
                                        if sidx is None:
                                            hdr_disabled = any(u in disabled_ids for u in ids if u != -1)
                                            hdr_color = Fore.RED if hdr_disabled else Fore.GREEN
                                            branch_text += (colour(hdr_color, name.split('*')[0]) + ': ')
                                            i += 1
                                            continue

                                        group_keys = [name]
                                        j = i + 1
                                        while j < len(keys):
                                            nxt = keys[j]
                                            if not nxt.isupper():
                                                break
                                            if star_index(nxt) != sidx:
                                                break
                                            group_keys.append(nxt)
                                            j += 1

                                        chosen_key = group_keys[-1]
                                        for k in group_keys:
                                            blen, _ = branch_progress(branches[k])
                                            if blen > 0:
                                                chosen_key = k
                                                break

                                        chosen_ids = branches[chosen_key]
                                        hdr_disabled = any(u in disabled_ids for u in chosen_ids if u != -1)
                                        hdr_color = Fore.RED if hdr_disabled else Fore.GREEN
                                        branch_text += (colour(hdr_color, chosen_key.split('*')[0]) + ': ')
                                        i = j
                                        continue

                                    sidx = star_index(name)
                                    if sidx is None:
                                        labels = base_labels(name)
                                        length, total = branch_progress(ids)
                                        building_items.append(pretty_item(labels, length, total))
                                        i += 1
                                        continue

                                    group_keys = [name]
                                    j = i + 1
                                    while j < len(keys):
                                        nxt = keys[j]
                                        if nxt.isupper():
                                            break
                                        if star_index(nxt) != sidx:
                                            break
                                        group_keys.append(nxt)
                                        j += 1

                                    best_key = group_keys[0]
                                    best_len, best_tot = branch_progress(branches[best_key])
                                    for k in group_keys[1:]:
                                        blen, btot = branch_progress(branches[k])
                                        if blen > best_len or (blen == best_len and btot >= best_tot):
                                            best_key, best_len, best_tot = k, blen, btot

                                    labels = base_labels(best_key)
                                    building_items.append(pretty_item(labels, best_len, best_tot))
                                    i = j

                                if building_items:
                                    branch_text += ', '.join(building_items)

                                clear_console()
                                print(colour(Back.CYAN, Style.BRIGHT, f'\n{title_emoji} Tech Tree Menu{save} {title_emoji}'))
                                print(colour(Fore.WHITE, f"Scout: {current_scout_name()}"))  # <-- requested white line
                                print(branch_text)
                                print(colour(Fore.MAGENTA,
                                            "\nType a unit/tech name to toggle/progress that branch, "
                                            "or 'scout: <name|id>' to change scout, 'default' to reset, "
                                            "Enter to quit."))

                                return branches, tech_tree_effect_id

                            # === Main loop: print immediately, then accept actions ===
                            while True:
                                result = render_tree()
                                if result is None:
                                    time.sleep(1)
                                    break
                                branches, tech_tree_effect_id = result

                                tech_tree_actions = input('Action: ')
                                if tech_tree_actions == '':
                                    if save == '*':
                                        with_real_progress(lambda progress: save_dat(progress, rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat'), 'Saving Mod', total_steps=100)
                                        update_tech_tree_graphic(selected_civ_name)
                                        print('Tech tree saved.')
                                        time.sleep(1)
                                    break

                                # Parse multi-actions separated by commas
                                for action in tech_tree_actions.split(','):
                                    act = action.strip()
                                    if not act:
                                        continue

                                    # Reset to default
                                    if act.lower() == 'default':
                                        DATA.effects[tech_tree_effect_id].effect_commands.clear()
                                        for tech_id in [84, 272, 447, 448, 521, 522, 526, 528, 570, 598, 599, 655, 695, 703, 773, 775, 787, 790, 793, 842, 843, 885, 930, 932, 940, 941, 948, 992, 1005, 1037, 1065, 1075, 1136, 1142, 1065, 1167, 1168, 1169]:
                                            DATA.effects[tech_tree_indexes[selected_civ_index]].effect_commands.append(
                                                genieutils.effect.EffectCommand(102, -1, -1, -1, tech_id)
                                            )
                                        save = '*'
                                        continue

                                    # Change Scout: "scout: Camel Scout" or "scout: 1"
                                    if act.lower().startswith('scout:') or act.lower().startswith('s:'):
                                        scout_bank = {'Scout Cavalry': 448, 'Eagle Scout': 751, 'Camel Scout': 1755}
                                        choice = act.split(':', 1)[1].strip()
                                        if choice.isdigit():
                                            idx = int(choice)
                                            keys = list(scout_bank.keys())
                                            if 0 <= idx < len(keys):
                                                name = keys[idx]
                                                DATA.civs[selected_civ_index + 1].resources[263] = scout_bank[name]
                                                save = '*'
                                            else:
                                                print(colour(Fore.RED, 'ERROR: Invalid scout index.'))
                                                time.sleep(1)
                                        else:
                                            # name
                                            low = {k.lower(): v for k, v in scout_bank.items()}
                                            if choice.lower() in low:
                                                DATA.civs[selected_civ_index + 1].resources[263] = low[choice.lower()]
                                                save = '*'
                                            else:
                                                print(colour(Fore.RED, 'ERROR: Invalid scout name.'))
                                                time.sleep(1)
                                        continue

                                    # Otherwise treat as unit/tech toggle on a branch
                                    # (same logic you had previously)
                                    for branch_key, ids in branches.items():
                                        target = act.strip().lower().replace('*', '')
                                        labels = [t.split('*')[0].strip().lower() for t in branch_key.split('/')]
                                        if target not in labels:
                                            continue

                                        golden_index = labels.index(target)

                                        ec_list = DATA.effects[tech_tree_effect_id].effect_commands
                                        disabled_set = {ec.d for ec in ec_list if getattr(ec, "type", None) == 102}

                                        # compute current progress on this line
                                        length = 0
                                        for u in ids:
                                            if u == -1:
                                                length += 1
                                                continue
                                            if u in disabled_set:
                                                break
                                            length += 1
                                        fully_disabled = (length == 0)
                                        current_enabled_index = (length - 1) if length > 0 else None

                                        if (not fully_disabled) and (current_enabled_index == golden_index):
                                            # disable whole line
                                            for tid in ids:
                                                if tid == -1:
                                                    continue
                                                if tid not in disabled_set:
                                                    ec_list.append(genieutils.effect.EffectCommand(102, -1, -1, -1, tid))
                                            save = '*'
                                        else:
                                            # enable <= golden, disable > golden
                                            to_enable = {tid for idx, tid in enumerate(ids) if tid != -1 and idx <= golden_index}
                                            if to_enable:
                                                for ec in ec_list[::-1]:
                                                    if getattr(ec, "type", None) == 102 and ec.d in to_enable:
                                                        ec_list.remove(ec)

                                            disabled_set = {ec.d for ec in ec_list if getattr(ec, "type", None) == 102}
                                            for idx, tid in enumerate(ids):
                                                if tid == -1 or idx <= golden_index:
                                                    continue
                                                if tid not in disabled_set:
                                                    ec_list.append(genieutils.effect.EffectCommand(102, -1, -1, -1, tid))
                                            save = '*'

                                            # If this branch is part of a starred group, disable conflicting siblings
                                            def star_index_local(bk):
                                                if '*' not in bk:
                                                    return None
                                                t = bk.rsplit('*', 1)[-1]
                                                return int(t) if t.isdigit() else None

                                            sidx = star_index_local(branch_key)
                                            if sidx is not None:
                                                # rebuild siblings in same starred group
                                                group_keys = []
                                                started = False
                                                for kname in list(branches.keys()):
                                                    if kname.isupper():
                                                        started = False
                                                    if star_index_local(kname) == sidx and not kname.isupper():
                                                        if not started:
                                                            started = True
                                                        group_keys.append(kname)
                                                    elif started:
                                                        break

                                                ec_list = DATA.effects[tech_tree_effect_id].effect_commands
                                                disabled_set = {ec.d for ec in ec_list if getattr(ec, "type", None) == 102}

                                                for sib in group_keys:
                                                    if sib == branch_key:
                                                        continue
                                                    for tid in branches[sib]:
                                                        if tid == -1 or tid in to_enable:
                                                            continue
                                                        if tid not in disabled_set:
                                                            ec_list.append(genieutils.effect.EffectCommand(102, -1, -1, -1, tid))
                                                            disabled_set.add(tid)
                                        break  # handled one action on a matching branch
                else:
                    pass
            except Exception as e:
                print(str(e))

if __name__ == "__main__":
    main()