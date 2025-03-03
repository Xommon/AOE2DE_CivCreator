# Micheal Quentin
# 02. March 2025
# 2025 Civilisation Creator

import os
import shutil
#import genieutils

def open_mod():
    mod_folder = input("Mod folder location: ")
    
def new_mod():
    # Get local mods folder
    local_mods_folder = input("Enter local mods folder location: ")
    if local_mods_folder == '':
        local_mods_folder = '/home/xommon/snap/steam/common/.local/share/Steam/steamapps/compatdata/813780/pfx/drive_c/users/steamuser/Games/Age of Empires 2 DE/76561198021486964/mods/local'
    
    # Get original AoE2DE folder
    aoe2_folder = input("Select original \"AoE2DE\" folder location: ")
    if aoe2_folder == '':
        aoe2_folder = '/home/xommon/snap/steam/common/.local/share/Steam/steamapps/common/AoE2DE'

    # Get name for mod
    mod_name = input("Enter new mod name: ")

    # Start creating new mod
    print("Creating new mod:", mod_name)

    # Create new folder and change directory to it
    os.makedirs(mod_name, exist_ok=True)
    os.chdir(mod_name)
    mod_folder = os.path.join(local_mods_folder, mod_name)

    # Ensure the mod folder exists
    os.makedirs(mod_folder, exist_ok=True)

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
        destination_path = os.path.join(mod_folder, item)

        # Ensure destination directory exists
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)

        # Check if source is a file or a folder
        if os.path.isfile(source_path):
            shutil.copy(source_path, destination_path)  # Copy file
            print(f"Copied file: {source_path} → {destination_path}")
        elif os.path.isdir(source_path):
            shutil.copytree(source_path, destination_path, dirs_exist_ok=True)  # Copy folder
            print(f"Copied folder: {source_path} → {destination_path}")
        else:
            print(f"Warning: {source_path} not found.")

    print("Mod created.")

def main():
    # Main menu
    print('-- AOE2DE Civilisation Creator --')
    print('1: Open')
    print('2: New')
    selection = input("Selection: ")

    # Open
    if selection == "1":
        open_mod()
    # New
    elif selection == "2":
        new_mod()

if __name__ == "__main__":
    main()