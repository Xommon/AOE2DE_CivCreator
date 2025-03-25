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
path = input('Give path to .dat file: ')
DATA = DatFile.parse(path)
print('File opened')
time.sleep(1)

# Print the data
for i in range(22):
    pyperclip.copy(DATA.civs[1].units[2382 + i])
    print(f'Unit {i} copied.')
    input('Press Enter to continue.')