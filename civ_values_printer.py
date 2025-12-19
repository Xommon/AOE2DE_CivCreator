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
import genieutils.tech
import genieutils.unit
import pyperclip
from genieutils.tech import Tech

# Open file
print('Values Printer Running...')
#path = input('Give path to .dat file: ')
path = r'/home/xommon/snap/steam/common/.local/share/Steam/steamapps/compatdata/813780/pfx/drive_c/users/steamuser/Games/Age of Empires 2 DE/76561198021486964/mods/local/Test/resources/_common/dat/empires2_x2_p1.dat'
DATA = DatFile.parse(path)
print('File opened')
time.sleep(1)

# Edit code after here

def swapGraphics(swap_civ, civ_reference):
    for unit_id in [20, 132, 498, 1413, 1414, 10, 14, 87, 1415, 1416, 86, 101, 153, 1417, 1418, 49, 150, 1425, 1426, 18, 19, 103, 105, 1419, 1420, 47, 51, 133, 806, 807, 808, 2120, 2121, 2122, 2144, 2145, 2146, 209, 210, 1427, 1428, 79, 190, 234, 236, 235, 1430, 191, 192, 463, 464, 465, 1434, 1435, 71, 141, 142, 444, 481, 482, 483, 484, 597, 611, 612, 613, 614, 615, 616, 617, 584, 585, 586, 587, 562, 563, 564, 565, 84, 116, 137, 1422, 1423, 1424, 1646, 129, 130, 131, 1411, 1412, 117, 155, 1508, 1509, 63, 64, 67, 78, 80, 81, 85, 88, 90, 91, 92, 95, 487, 488, 490, 491, 659, 660, 661, 662, 663, 664, 665, 666, 667, 668, 669, 670, 671, 672, 673, 674, 1192, 1406, 1500, 1501, 1502, 1503, 1504, 1505, 1506, 1507, 110, 179, 1647]:
        '''attributes = [
            "standing_graphic", "damage_graphics", "dying_graphic", "undead_graphic",
            "garrison_graphic", "spawning_graphic", "upgrade_graphic", "hero_glow_graphic",
            "idle_attack_graphic", "special_graphic", "attack_graphic", "attack_graphic_2",
            "working_graphic_id", "carrying_graphic_id", "moving_graphic_id",
            "proceeding_graphic_id", "selection_graphics", "building"
        ]'''
        attributes = [
            "standing_graphic", "damage_graphics"
        ]

        for attr in attributes:
            try:
                setattr(DATA.civs[swap_civ].units[unit_id], attr, getattr(DATA.civs[civ_reference].units[unit_id], attr))
            except:
                pass

swapGraphics(31, 55) # Bulgarians (Caucasian)
swapGraphics(44, 55) # Armenians (Caucasian)
swapGraphics(45, 55) # Georgians (Caucasian)
swapGraphics(40, 56) # Dravidians (South Indian)
swapGraphics(41, 56) # Bengalis (South Indian)
DATA.save(path)
print('Done swapping graphics')