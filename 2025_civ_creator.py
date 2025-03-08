# Micheal Quentin
# 02. March 2025
# 2025 Civilisation Creator
# DEBUG: wine /home/xommon/snap/steam/common/.local/share/Steam/steamapps/common/AoE2DE/Tools_Builds/AdvancedGenieEditor3.exe

import os
import shutil
import time
import pickle
import io
import ast
import genieutils
from genieutils.datfile import DatFile
import genieutils.sound
import genieutils.unit
import pickle

def open_mod(mod_folder):
    print('\nLoading mod...')
    global DATA
    DATA = DatFile.parse(rf'{mod_folder}/resources/_common/dat/empires2_x2_p1.dat')
    global MOD_STRINGS
    MOD_STRINGS = rf'{mod_folder}/resources/en/strings/key-value/key-value-modded-strings-utf8.txt'
    global MOD_FOLDER
    MOD_FOLDER = mod_folder

    # Load architecture sets
    global ARCHITECTURE_SETS
    ARCHITECTURE_SETS = []
    with open(f'{MOD_FOLDER}/{mod_folder.split("/")[-1]}.pkl', 'rb') as file:
        while True:
            try:
                architecture_set = pickle.load(file)
                ARCHITECTURE_SETS.append(architecture_set)
                file.readline()  # Read the newline character
            except EOFError:
                break
    print('Mod loaded!')
    
def new_mod():
    # Get local mods folder
    local_mods_folder = input("\nEnter local mods folder location: ")
    if local_mods_folder == '':
        local_mods_folder = '/home/xommon/snap/steam/common/.local/share/Steam/steamapps/compatdata/813780/pfx/drive_c/users/steamuser/Games/Age of Empires 2 DE/76561198021486964/mods/local'
    
    # Get original AoE2DE folder
    aoe2_folder = input("Select original \"AoE2DE\" folder location: ")
    if aoe2_folder == '':
        aoe2_folder = '/home/xommon/snap/steam/common/.local/share/Steam/steamapps/common/AoE2DE'

    # Get name for mod
    mod_name = input("Enter new mod name: ")

    # Create new folder and change directory to it
    os.makedirs(mod_name, exist_ok=True)
    os.chdir(mod_name)
    global MOD_FOLDER
    MOD_FOLDER = os.path.join(local_mods_folder, mod_name)

    # Ensure the mod folder exists
    os.makedirs(MOD_FOLDER, exist_ok=True)

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
    global DATA
    DATA = DatFile.parse(rf'{local_mods_folder}/{mod_name}/resources/_common/dat/empires2_x2_p1.dat')

    # Copy and filter original strings
    global MOD_STRINGS
    MOD_STRINGS = rf'{local_mods_folder}/{mod_name}/resources/en/strings/key-value/key-value-modded-strings-utf8.txt'
    original_strings = rf'{local_mods_folder}/{mod_name}/resources/en/strings/key-value/key-value-strings-utf8.txt'

    with open(original_strings, 'r') as original_file:
        original_strings_list = original_file.readlines()

    # Write modded strings based on filter conditions
    with open(MOD_STRINGS, 'w') as modded_file:
        write_lines = False  # Flag to start writing when a target key is found

        for line in original_strings_list:
            if any(key in line for key in ['10271', '120150', '120177', '120181', '120185', 
                                           '120187', '120189', '120192', '120193', '120195', 
                                           '120196', '120197']):
                write_lines = True  # Start writing

            if write_lines and line.strip():  # Write only if the line is not empty
                modded_file.write(line)

            if write_lines and line.strip() == "":  # Stop at empty line
                write_lines = False

    # Write the architecture sets to a file
    with open(f'{MOD_FOLDER}/{mod_name}.pkl', 'wb') as file:
        for civ in DATA.civs:
            pickle.dump(civ.units, file)
            file.write(b'\n')

    # Open the new mod
    print(mod_name, "created!")
    open_mod(MOD_FOLDER)

def main():
    # Main menu
    print('---- AOE2DE Civilisation Creator ----')
    print('1: Open Mod')
    print('2: New Mod')
    selection = input("Selection: ")

    # Open
    if selection == "1":
        global MOD_FOLDER
        MOD_FOLDER = input("\nMod folder location: ")
        open_mod(MOD_FOLDER)
    # New
    elif selection == "2":
        new_mod()

    # Mod menu
    mod_name = MOD_FOLDER.split('/')[-1]
    while True:
        # Display all of the civilisations
        time.sleep(2)
        print(f'\n--- {mod_name} Menu ---')
        selected_civ_index = -1
        with open (MOD_STRINGS, 'r') as file:
            lines = file.readlines()
            for i in range(len(DATA.civs) - 1):
                print(rf'{i}: {lines[i][7:-2]}')
        selection = input("Selection: ")
        selected_civ_index = int(selection)
        selected_civ_name = lines[selected_civ_index][7:-2]

        # Edit civilisation
        try:
            edit_civ_index = int(selection)
            if 0 <= edit_civ_index < len(DATA.civs):
                print(f'\n-- Edit {selected_civ_name} --')
                print('0: Name')
                print('1: Description')
                print('2: Architecture')
                print('3: Language')
                print('4: Tech Tree')
                selection = input("Selection: ")

                # Name
                if selection == "0":
                    new_name = input(f"Enter new name for {selected_civ_name}: ")

                    # Change name
                    DATA.civs[edit_civ_index + 1].name = new_name
                    with open(MOD_STRINGS, 'r+') as file:
                        lines = file.readlines()  # Read all lines
                        lines[selected_civ_index] = lines[selected_civ_index][:5] + f' "{new_name}"\n'  # Modify the specific line

                        file.seek(0)  # Move to the beginning of the file
                        file.writelines(lines)  # Overwrite the file with modified lines
                        file.truncate()  # Ensure any remaining old content is removed

                # Description
                elif selection == "1":
                    new_description = input(f"Enter new description for {selected_civ_name}: ")

                    # Change description
                    with open(MOD_STRINGS, 'r+') as file:
                        lines = file.readlines()  # Read all lines
                        lines[selected_civ_index + len(DATA.civs) - 1] = lines[selected_civ_index + len(DATA.civs) - 1][:6] + f' "{new_description}"\n'  # Modify the specific line

                        file.seek(0)  # Move to the beginning of the file
                        file.writelines(lines)  # Overwrite the file with modified lines
                        file.truncate()  # Ensure any remaining old content is removed

                # Architecture
                elif selection == "2":
                    # Populate architecture names
                    architecture_names = []
                    for i in range(1, len(DATA.civs)):
                        architecture_names.append(DATA.civs[i].name.lower())
                    
                    # Assemble all architecture names
                    all_arcs = ''
                    for i in range(1, len(DATA.civs)):
                        all_arcs += DATA.civs[i].name.lower()
                        if i < len(DATA.civs) - 1:
                            all_arcs += ', '

                    # User prompts
                    architecture_types = ["General", "Castle", "Wonder"]
                    architecture_changes = [-1, -1, -1]
                    print('\n')
                    for i in range(3):
                        architecture_selection = '?'
                        while architecture_selection == '?':
                            architecture_selection = input(f"Enter {architecture_types[i]} architecture for {selected_civ_name} (leave blank for original): ").lower()
                            if architecture_selection == '?':
                                print(all_arcs)
                                continue
                            for i_arc in range(len(architecture_names)):
                                if architecture_selection.lower() == architecture_names[i_arc].lower():
                                    architecture_changes[i] = architecture_names.index(architecture_selection.lower())
                                    break

                            if architecture_selection == '':
                                architecture_changes[i] = selected_civ_index
                            elif architecture_changes[i] == -1:
                                architecture_selection = '?'
                                print(f'{architecture_types[i]} architecture type not valid.\n')

                    for arc_db in range(3):
                        # Load architecture graphics
                        original_units = ARCHITECTURE_SETS[architecture_changes[arc_db] + 1]

                        # Change architecture
                        if arc_db == 0:
                            all_units_to_change = range(0, len(DATA.civs[1].units))
                        elif arc_db == 1:
                            all_units_to_change = [82, 1430]
                        elif arc_db == 2:
                            all_units_to_change = [276, 1445]

                        for unit_id in all_units_to_change:
                            # Standing graphic
                            try:
                                standing_graphic_list = list(DATA.civs[selected_civ_index + 1].units[unit_id].standing_graphic)  # Convert to list for modification
                                standing_graphic_list[0] = int(original_units[unit_id].standing_graphic[0])  # Ensure it's an integer
                                DATA.civs[selected_civ_index + 1].units[unit_id].standing_graphic = tuple(standing_graphic_list)  # Convert back to tuple
                            except:
                                pass

                            # Dying graphic
                            try:
                                DATA.civs[selected_civ_index + 1].units[unit_id].dying_graphic = original_units[unit_id].dying_graphic  # Ensure it's an integer
                            except:
                                pass

                            # Damage graphics
                            try:
                                for j in range(3):  # Loop through the first 3 damage graphics
                                    if j < len(DATA.civs[selected_civ_index + 1].units[unit_id].damage_graphics):
                                        DATA.civs[selected_civ_index + 1].units[unit_id].damage_graphics[j].graphic_id = original_units[unit_id].damage_graphics[j].graphic_id # Ensure it's an integer
                            except:
                                pass

                    # Save changes
                    DATA.save(rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat')
                    print(f"Architecture changed.")

                # Language
                elif selection == "3":
                    pass
            else:
                print("Invalid selection. Try again.")
        except ValueError:
            print("Please enter a valid number.")

if __name__ == "__main__":
    main()