# Age of Empires II: Definitive Edition Unit Code Extractor

from genieutils.datfile import DatFile
import os
import pyperclip

# Get the path
path = input('Enter path for .dat file or leave blank for default: ')
if path == '':
    print('Loading .dat file...')
    DATA = DatFile.parse(rf'C:\Users\Micheal Q\Games\Age of Empires 2 DE\76561198021486964\mods\local\15eFq\resources\_common\dat\empires2_x2_p1.dat')
else:
    print('Loading .dat file...')
    DATA = DatFile.parse(path)

# Display the unit
while True:
    index = input('Enter the unit index to show: ')

    try:
        result = DATA.civs[0].units[int(index)]
        pyperclip.copy(str(result))
        print(DATA.civs[0].units[int(index)])
    except Exception as e:
        print('ERROR:', str(e))