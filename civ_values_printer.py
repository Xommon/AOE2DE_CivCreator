# Micheal Quentin
# 22. March 2025
# Print AOE2DE .dat file values

import genieutils
from genieutils.datfile import DatFile
import genieutils.graphic
from genieutils.graphic import Graphic
from genieutils.graphic import GraphicDelta
from genieutils.graphic import GraphicAngleSound
import time
import genieutils.unit
import pyperclip

# Open file
print('Values Printer Running...')
#path = input('Give path to .dat file: ')
path = r'/home/xommon/snap/steam/common/.local/share/Steam/steamapps/compatdata/813780/pfx/drive_c/users/steamuser/Games/Age of Empires 2 DE/76561198021486964/mods/local/Test/resources/_common/dat/empires2_x2_p1.dat'
DATA = DatFile.parse(path)
print('File opened')
time.sleep(1)

def get_all_attributes(obj, prefix=''):
    attributes = []
    for attr in dir(obj):
        if attr.startswith('_'):
            continue
        try:
            value = getattr(obj, attr)
        except:
            continue

        if callable(value):
            continue

        full_attr = f"{prefix}.{attr}" if prefix else attr

        # Recurse into nested objects
        if hasattr(value, '__dict__') or isinstance(value, (tuple, list)):
            attributes.extend(get_all_attributes(value, full_attr))
        else:
            attributes.append(full_attr)
    return attributes


def get_deep_attr(obj, path):
    """Safely get nested attribute using dot notation path."""
    parts = path.split('.')
    for part in parts:
        obj = getattr(obj, part, None)
        if obj is None:
            return None
    return obj


model = DATA.civs[1].units[1920]

# Step 1: Gather all attribute paths from model (including sub-objects)
attribute_paths = get_all_attributes(model)

# Step 2: Loop through every unit and compare values
for unit in DATA.civs[1].units:
    if unit is model or unit is DATA.civs[1].units[1922]:
        print('skip')
        continue

    for path in attribute_paths[:]:  # Work on a copy
        try:
            model_val = get_deep_attr(model, path)
            unit_val = get_deep_attr(unit, path)
            if model_val == unit_val:
                attribute_paths.remove(path)
        except:
            pass

# Step 3: Print what remains unique to model
print('Unique attribute paths:', attribute_paths)

print('--- Unique Attributes and Values ---')
for path in attribute_paths:
    try:
        value = get_deep_attr(model, path)
        print(f"{path} = {value}")
    except:
        print(f"{path} = <unreadable>")
