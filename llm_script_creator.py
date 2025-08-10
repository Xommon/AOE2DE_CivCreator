# Micheal Quentin
# 02. August 2025
# Create training guide for LLM

import genieutils
from genieutils.datfile import DatFile
import genieutils.graphic
from genieutils.graphic import Graphic
from genieutils.graphic import GraphicDelta
from genieutils.graphic import GraphicAngleSound
import time
import genieutils.unit
import pyperclip
import json
import os
from copy import deepcopy
import random
from itertools import combinations

# Open file
print('Values Printer Running...')
path = r'/home/xommon/snap/steam/common/.local/share/Steam/steamapps/compatdata/813780/pfx/drive_c/users/steamuser/Games/Age of Empires 2 DE/76561198021486964/mods/local/Test/resources/_common/dat/empires2_x2_p1.dat'
DATA = DatFile.parse(path)
print('File opened')
time.sleep(1)

# Paths
input_path = '/home/xommon/snap/steam/common/.local/share/Steam/steamapps/compatdata/813780/pfx/drive_c/users/steamuser/Games/Age of Empires 2 DE/76561198021486964/mods/local/Test/resources/en/strings/key-value/key-value-strings-utf8.txt'
output_path = '/home/xommon/Documents/GitHub/AOE2DE_CivCreator/LLM_Training.json'

# Ensure directory exists
os.makedirs(os.path.dirname(output_path), exist_ok=True)
max_length = 200

# Get units
def get_unit(unit_name):
    for i, unit in enumerate(DATA.units):
        if unit.name.lower() == unit_name.lower():
            return i
    return -1

# Step 1: Read and parse the string file
string_dictionary = {}
with open(input_path, 'r') as file:
    for line in file.readlines():
        line = line.strip()
        if not line or '"' not in line:
            continue  # Skip empty or malformed lines
        try:
            key_str, value_str = line.split(' ', 1)
            key = int(key_str)
            value = value_str.strip('"')
            if value in ['Tent A', ''] or any(
                phrase in value for phrase in [
                    'which are stronger',
                    'Unique',
                    'Improves your civilization',
                    'Lets you build',
                    'Lets your create'
                ]
            ):
                continue  # Skip unhelpful entries
            try:
                value = value.split(r'\n')[1]  # Take 2nd line if exists
            except IndexError:
                pass
            string_dictionary[key] = value.strip()
        except ValueError:
            continue  # Skip lines that can't be parsed

'''for key, value in string_dictionary.items():
    print(f"{key}: {value}")'''

# Step 2: Create custom entries
unit_lines = {
    'archer-line': [4, 24, 492],
    'skirmishers': [7, 6, 1155],
    'cavalry archers': [39, 474],
    'elephant archers': [873, 875],
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
    'battering rams': [35, 422, 548],
    'armored elephants': [1744, 1746],
    'mangonel-line': [280, 550, 588],
    'rocket carts': [1904, 1907],
    'fire ships': [1103, 529, 532],
    'demolition ships': [1104, 527, 528],
    'galleys': [539, 21, 442],
    'canoes': [778, 2383, 2384],
    'cannon galleons': [420, 691],
    'turtle ships': [831, 832],
    'longboats': [250, 533],
    'caravels': [1004, 1006],
    'camel units': [282, 556, 1755, 329, 330, 207, 1007, 1009, 1263, 1923],
    'elephant units': [239, 558, 873, 875, 1120, 1122, 1132, 1134, 1744, 1746, 1923],
    'gunpowder units': [5, 36, 420, 46, 691, 771, 773, 557, 1001, 1003, 831, 832, 1709, 1704, 1706, 1904, 1907, 1901, 1903, 1911],
    'mounted archers': [39, 474, 1231, 1233, 1260],
    'shock infantry': [751, 752, 753, 1901, 1903, 1974, 1976],
    'mule carts': [1808],
    'warrior priests': [1811, 1831],
}
import re
from collections import defaultdict

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
        unit_name = string_dictionary.get(dll_id, getattr(unit, 'name', '')).lower()
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
    'towers': [52],
    'livestock': [58],
    'military units': [0, 35, 6, 36, 47, 12, 44, 23],
    'all military units': [0, 55, 22, 35, 6, 54, 13, 51, 36, 12],
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
    'technologies': [85]
}
for i, tech in enumerate(DATA.techs):
    if tech.research_locations[0].location_id in [87, 12, 101, 103, 84, 82, 109, 65, 209, 49, 104, 562, 68, 584] and tech.effect_id != -1 and (tech.civ < 46 or tech.civ > 48):
        if tech.language_dll_name in string_dictionary:
            technologies[string_dictionary[tech.language_dll_name].lower()] = [i]

'''for tech in technologies:
    print(tech)'''

stats = {
    r"$ # hit points": [0],
    r"$ # HP": [0],
    r"$ # line of sight": [1, 23],
    r"$ # LOS": [1, 23],
    r"$ # garrison capacity": [2],
    r"$ move # faster": [5],
    #r"$ # armor": [8],
    r"$ # attack": [9],
    r"$ attack # faster": [10],
    r"$ have # accuracy": [11],
    r"$ # range": [12, 1, 23],
    r"$ work # faster": [13],
    r"$ carry #": [14],
    #r"Base Armor (types 50-80)": [15],
    #r"Projectile Unit (types 50-80)": [16],
    #r"Min Range": [20],
    #r"Blast Width": [22],
    r"$ receive # bonus damage": [24], # Normally set to 0
    r"$ fire an additional projectile": [102, 107],
    r"$ cost # food": [103],
    r"$ cost # wood": [104],
    r"$ cost # gold": [105],
    r"$ cost # stone": [106],
    r"$ cost #": [103, 104, 105, 106],
    #r'Min Conversion': [111],
    #r'Max Conversion': [112],
    r"$ regenerate # HP per minute": [109],
    r"$ take # population space": [110],
    #r"Conversion Chance Modifier (types 70-80)": [113],
    #r"Formation Category (types 70-80)": [114],
    #r"Area Damage (types 50-80)": [115]
}

# Function to get random number divisible by 5, excluding 0
def get_random_num():
    while True:
        n = random.randint(-100, 100)
        if n != 0 and n % 5 == 0:
            break

    is_percent = random.random() < 0.5  # 50% chance

    if is_percent:
        real_number = round(1 + (n / 100), 2)  # two decimal points
        display_string = f"{n:+d}%"
    else:
        real_number = n  # keep as int
        display_string = f"{n:+d}"

    return real_number, display_string

# Prepare data list
training_data = []

for i in range(5):
    # Pair every unit_line with every stat
    for keyU, valueU in unit_lines.items():
        for keyS, valueS in stats.items():
            # Generate number
            number, number_string = get_random_num()

            # Generate input
            input = keyS.replace('$', keyU).replace('#', number_string)
            output = ''
            for unit_id in valueU:
                for stat_id in valueS:
                    output += f'|E{"4" if isinstance(number, int) else "5"}~{unit_id}~-1~0~{stat_id}~{number}'

            # Add the training data
            if len(input) <= max_length and len(output) <= max_length:
                training_data.append({"input": input, "output": output[1:]})

    # Pair every category with every stat
    for keyC, valueC in categories.items():
        for keyS, valueS in stats.items():
            # Generate number
            number, number_string = get_random_num()

            # Generate input
            input = keyS.replace('$', keyC).replace('#', number_string)
            output = ''
            for category_id in valueC:
                for stat_id in valueS:
                    output += f'|E{"4" if isinstance(number, int) else "5"}~-1~{category_id}~0~{stat_id}~{number}'

            # Add the training data
            if len(input) <= max_length and len(output) <= max_length:
                training_data.append({"input": input, "output": output[1:]})

# Write to JSON
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(training_data, f, ensure_ascii=False, indent=2)

print(f"JSON saved with {len(training_data)} entries.")