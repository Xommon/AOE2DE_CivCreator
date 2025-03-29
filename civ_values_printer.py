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
import pyperclip

# Open file
print('Values Printer Running...')
#path = input('Give path to .dat file: ')
path = r'/home/xommon/snap/steam/common/.local/share/Steam/steamapps/compatdata/813780/pfx/drive_c/users/steamuser/Games/Age of Empires 2 DE/76561198021486964/mods/local/Test/resources/_common/dat/empires2_x2_p1.dat'
DATA = DatFile.parse(path)
print('File opened')
time.sleep(1)

# Print the data
print(DATA.effects[866].effect_commands[1])