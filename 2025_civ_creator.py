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
import genieutils.tech
import genieutils.unit
import genieutils.effect
import pickle
import json
import re

def open_mod(mod_folder):
    print('\nLoading mod...')
    global DATA
    DATA = DatFile.parse(rf'{mod_folder}/resources/_common/dat/empires2_x2_p1.dat')
    global MOD_STRINGS
    MOD_STRINGS = rf'{mod_folder}/resources/en/strings/key-value/key-value-modded-strings-utf8.txt'
    global ORIGINAL_STRINGS
    ORIGINAL_STRINGS = rf'{mod_folder}/resources/en/strings/key-value/key-value-strings-utf8.txt'
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

def revert():
    print('\nWARNING: Reverting the mod will completely erase all changes made to the modded files. THIS CHANGE IS IRREVERSIBLE.')
    yes = input("Enter 'yes' to continue: ")
    
    if yes.lower() == 'yes':
        # Get the original AoE2DE folder from the user
        modded_folder = input('Enter the mod folder location: ').strip()
        if not modded_folder:
            modded_folder = '/home/xommon/snap/steam/common/.local/share/Steam/steamapps/compatdata/813780/pfx/drive_c/users/steamuser/Games/Age of Empires 2 DE/76561198021486964/mods/local/Test'
        aoe2_folder = input("Enter the original 'AoE2DE' folder location: ").strip()
        if not aoe2_folder:
            aoe2_folder = '/home/xommon/snap/steam/common/.local/share/Steam/steamapps/common/AoE2DE'

        # List of files to restore
        files_to_restore = [
            'resources/_common/dat/civilizations.json', 
            'resources/_common/dat/civTechTrees.json', 
            'resources/_common/dat/empires2_x2_p1.dat', 
            'resources/_common/wpfg/resources/civ_techtree',
            'resources/_common/wpfg/resources/uniticons',
            'resources/en/strings/key-value/key-value-strings-utf8.txt',
            'resources/en/strings/key-value/key-value-modded-strings-utf8.txt',
            'widgetui/textures/menu/civs'
        ]

        # Delete current modded files
        for item in files_to_restore:
            modded_path = os.path.join(modded_folder, item)

            if os.path.exists(modded_path):
                if os.path.isfile(modded_path):
                    os.remove(modded_path)  # Delete file
                elif os.path.isdir(modded_path):
                    shutil.rmtree(modded_path)  # Delete folder
            
        # Reinstall original files
        for item in files_to_restore:
            source_path = os.path.join(aoe2_folder, item)
            destination_path = os.path.join(modded_folder, item)

            # Ensure destination directory exists
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)

            if os.path.exists(source_path):
                if os.path.isfile(source_path):
                    shutil.copy(source_path, destination_path)  # Restore file
                elif os.path.isdir(source_path):
                    shutil.copytree(source_path, destination_path)  # Restore folder

        print("Mod reverted successfully!\n")
        main()

def main():
    # Main menu
    print('---- AOE2DE Civilisation Creator ----')
    print('0: Open Mod')
    print('1: New Mod')
    print('2: Revert Mod')
    selection = input("Selection: ")

    # Open
    if selection == "0":
        global MOD_FOLDER
        # DEBUG
        MOD_FOLDER = '/home/xommon/snap/steam/common/.local/share/Steam/steamapps/compatdata/813780/pfx/drive_c/users/steamuser/Games/Age of Empires 2 DE/76561198021486964/mods/local/Test'
        #MOD_FOLDER = input("\nMod folder location: ")
        open_mod(MOD_FOLDER)
    # New
    elif selection == "1":
        new_mod()
    # Revert
    elif selection == "2":
        revert()

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
                print('1: Title')
                print('2: Bonuses')
                print('3: Unique Unit')
                print('4: Architecture')
                print('5: Language')
                print('6: Tech Tree')
                selection = input("Selection: ")

                # Name
                if selection == '0':
                    new_name = input(f"Enter new name for {selected_civ_name}: ")

                    # Change name
                    DATA.civs[edit_civ_index + 1].name = new_name
                    with open(MOD_STRINGS, 'r+') as file:
                        lines = file.readlines()  # Read all lines
                        lines[selected_civ_index] = lines[selected_civ_index][:5] + f' "{new_name}"\n'  # Modify the specific line

                        file.seek(0)  # Move to the beginning of the file
                        file.writelines(lines)  # Overwrite the file with modified lines
                        file.truncate()  # Ensure any remaining old content is removed

                # Title
                if selection == '1':
                    # Get user input
                    new_title = input(f"\nEnter new civilization title for {selected_civ_name} (ex. Infantry and Monk): ")

                    with open(MOD_STRINGS, 'r+') as file:
                        # Read and separate the lines
                        lines = file.readlines()
                        line_index = selected_civ_index + len(DATA.civs) - 1
                        line = lines[line_index]
                        line_code = line[:6]
                        split_lines = line.split(r'\n')
                        
                        # Replace the title
                        split_lines[0] = f'{line_code} \"{new_title.title()} civilization'
                        lines[line_index] = rf'\n'.join(split_lines)

                        # Overwrite the file with modified content
                        file.seek(0)
                        file.writelines(lines)
                        file.truncate()  # Ensure remaining old content is removed

                # Unique Unit
                elif selection == '3':
                    # Populate all castle units
                    all_castle_units = ["longbowman", "throwing axeman", "berserk", "teutonic knight", "samurai", "chu ko nu", "cataphract", "war elephant", "mameluke", "janissary", "huskarl", "mangudai", "woad raider", "conquistador", "jaguar warrior", "plumed archer", "tarkan", "war wagon", "genoese crossbowman", "ghulam", "kamayuk", "magyar huszar", "boyar", "organ gun", "shotel warrior", "gbeto", "camel archer", "ballista elephant", "karambit warrior", "arambai", "rattan archer", "konnik", "keshik", "kipchak", "leitis", "coustillier", "serjeant", "obuch", "hussite wagon", "urumi swordsman", "ratha", "chakram thrower", "centurion", "composite bowman", "monaspa", "amazon warrior", "amazon archer", "camel raider", "cretan archer", "crusader knight", "tomahawk warrior", "ninja", "scimitar warrior", "drengr", "qizilbash warrior", "axe cavalry", "xolotl warrior", "sun warrior", "island sentinel"]
                    new_castle_unit = '?'
                    while new_castle_unit == '?':
                        new_castle_unit = input(f"\nEnter unique Castle unit for {selected_civ_name} (leave blank for original): ").lower()

                        if new_castle_unit not in all_castle_units:
                            new_castle_unit = '?'
                            print('ERROR: Unit not found.')
                        elif new_castle_unit == '?':
                            print(all_castle_units)
                            continue

                    # Get unit indexes
                    castle_unit_indexes = [-1, -1, -1, -1]
                    with open(ORIGINAL_STRINGS, 'r') as file:
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
                                    
                                if unit_name:
                                    if unit_name == all_castle_units[selected_civ_index]:
                                        castle_unit_indexes[0] = i
                                    elif unit_name == f'elite {all_castle_units[selected_civ_index]}':
                                        castle_unit_indexes[1] = i
                                    elif unit_name == new_castle_unit:
                                        castle_unit_indexes[2] = i
                                    elif unit_name == f'elite {new_castle_unit}':
                                        castle_unit_indexes[3] = i
                            except:
                                pass

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
                    
                    new_tech = DATA.techs[1101]
                    new_tech.effect_id = effect_index
                    new_tech.name = effect_name
                    new_tech.civ = selected_civ_index + 1

                    for tech in DATA.techs:
                        if tech.name == effect_name:
                            DATA.techs.remove(tech)
                    DATA.techs.append(new_tech)

                    # Save changes
                    DATA.save(rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat')
                    print(f"{selected_civ_name.title()} unique unit set to {new_castle_unit.title()}.")

                # Architecture
                elif selection == '4':
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
                    custom_arcs = [
                        [],
                        ['poenari castle'],
                        ['aachen cathedral', 'dome of the rock', 'dormition cathedral', 'gol gumbaz', 'minaret of jam', 'pyramid', 'quimper cathedral', 'sankore madrasah', 'tower of london']
                    ]

                    # User prompts
                    architecture_types = ["General", "Castle", "Wonder"]
                    architecture_changes = [-1, -1, -1]
                    print('\n')
                    for i in range(3):
                        architecture_selection = '?'
                        while architecture_selection == '?':
                            architecture_selection = input(f"Enter {architecture_types[i]} architecture for {selected_civ_name} (leave blank for original): ").lower()
                            if architecture_selection == '?':
                                additional_arcs = ''
                                if i == 0:
                                    additional_arcs += ''
                                elif i == 1:
                                    additional_arcs += ', poenari castle'
                                elif i == 2:
                                    additional_arcs += ', aachen cathedral, dome of the rock, dormition cathedral, gol gumbaz, minaret of jam, pyramid, quimper cathedral, sankore madrasah, tower of london'
                                print(all_arcs + additional_arcs)
                                continue
                            for i_arc in range(len(architecture_names)):
                                if architecture_selection.lower() == architecture_names[i_arc].lower():
                                    architecture_changes[i] = architecture_names.index(architecture_selection.lower())
                                    break

                            if architecture_selection == '':
                                architecture_changes[i] = selected_civ_index
                            elif architecture_changes[i] == -1:
                                architecture_selection = '?'
                                print(f'ERROR: {architecture_types[i]} architecture type not valid.\n')

                    print(architecture_changes)

                    for arc_db in range(3):
                        # Skip if unspecified
                        if architecture_changes[arc_db] == -1:
                            continue
                        
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
                            # Select which unit will be the basis for change
                            unit_to_change_to = -1
                            for j in enumerate(custom_arcs[arc_db]):
                                if architecture_selection == custom_arcs[arc_db][j]:
                                    unit_to_change_to = DATA.civs[selected_civ_index].units.index(custom_arcs[arc_db][j])
                                    print(unit_to_change_to)
                                    break
                            if unit_to_change_to == -1:
                                unit_to_change_to = original_units[unit_id]
                            
                            # Standing graphic
                            try:
                                standing_graphic_list = list(DATA.civs[selected_civ_index + 1].units[unit_id].standing_graphic)  # Convert to list for modification
                                standing_graphic_list[0] = int(unit_to_change_to.standing_graphic[0])  # Ensure it's an integer
                                DATA.civs[selected_civ_index + 1].units[unit_id].standing_graphic = tuple(standing_graphic_list)  # Convert back to tuple
                            except:
                                pass

                            # Dying graphic
                            try:
                                DATA.civs[selected_civ_index + 1].units[unit_id].dying_graphic = unit_to_change_to.dying_graphic  # Ensure it's an integer
                            except:
                                pass

                            # Damage graphics
                            try:
                                for j in range(3):  # Loop through the first 3 damage graphics
                                    if j < len(DATA.civs[selected_civ_index + 1].units[unit_id].damage_graphics):
                                        DATA.civs[selected_civ_index + 1].units[unit_id].damage_graphics[j].graphic_id = unit_to_change_to.damage_graphics[j].graphic_id # Ensure it's an integer
                            except:
                                pass

                    # Save changes
                    DATA.save(rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat')
                    print(f"Architecture changed.")

                # Language
                elif selection == '5':
                    pass

                # Tech Tree
                elif selection == '6':
                    # Import the tech tree
                    tech_tree = {}
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
                                tech_tree[selected_unit] = selected_status

                            # Check for the end of the tech tree section
                            if 'civ_id' in line:
                                break

                    # Tech tree menu
                    while selection != 3:
                        with open(f'{MOD_FOLDER}/resources/_common/dat/civTechTrees.json', 'r+') as file:
                            # Get index of selected civ
                            lines = file.readlines()
                            tech_tree_indexes = []
                            for i, line in enumerate(lines):
                                if "civ_id" in line:
                                    tech_tree_indexes.append(i)
                            tech_tree_index = tech_tree_indexes[selected_civ_index]
                            tech_tree_indexes = [254, 258, 259, 262, 255, 257, 256, 260, 261, 263, 276, 277, 275, 446, 447, 449, 448, 504, 10, 1, 3, 5, 7, 31, 48, 42, 37, 646, 648, 650, 652, 706, 708, 710, 712, 782, 784, 801, 803, 838, 840, 842, 890, 925, 927]

                            # Show menu
                            print(f'\n- Tech Tree Menu -')
                            print('0: View Tech Tree')
                            print('1: Enable Items')
                            print('2: Disable Items')
                            selection = input("Selection: ")

                            # Exit
                            if selection == '':
                                break

                            # Enable or Disable Items
                            elif selection == '1' or selection == '2':
                                # Choose whether enabling or disabling
                                if selection == '1':
                                    enable_disable = 'enable'
                                else:
                                    enable_disable = 'disable'

                                unit = 'X'
                                while unit != '':
                                    unit = input(f'\nEnter the unit, building, or technology name to {enable_disable}: ').lower()
                                    if unit in tech_tree:
                                        # Update .json file
                                        for i in range(tech_tree_index, len(lines)):
                                            if f'\"Name\": \"{unit.title()}\"' in lines[i]:
                                                if enable_disable == 'enable':
                                                    lines[i + 3] = f'          \"Node Status\": \"ResearchedCompleted\",\n'
                                                else:
                                                    lines[i + 3] = f'          \"Node Status\": \"NotAvailable\",\n'
                                                break
                                        file.seek(0)
                                        file.writelines(lines)
                                        file.truncate()

                                        # Get unit index
                                        match = re.search(r'\d+', lines[i + 2])
                                        if match:
                                            unit_index = int(match.group())

                                        # Get tech index
                                        found = False
                                        for i, tech in enumerate(DATA.techs):
                                            for ec in DATA.effects[tech.effect_id].effect_commands:
                                                if (ec.type == 2 and ec.a == unit_index) or (ec.type == 3 and ec.b == unit_index):
                                                    tech_index = i
                                                    print(tech_index)
                                                    found = True
                                                    break
                                            if found:
                                                break

                                        # Update .dat file
                                        unit_changed = False
                                        if enable_disable == 'enable':
                                            for i, effect_command in enumerate(DATA.effects[tech_tree_indexes[selected_civ_index + 1]].effect_commands):
                                                if effect_command.type == 102 and effect_command.d == tech_index:
                                                    DATA.effects[tech_tree_indexes[selected_civ_index + 1]].effect_commands.pop(i)
                                                    unit_changed = True
                                        elif enable_disable == 'disable':
                                            DATA.effects[tech_tree_indexes[selected_civ_index]].effect_commands.append(genieutils.effect.EffectCommand(102, 0, 0, 0, tech_index))
                                            unit_changed = True

                                        if unit_changed:
                                            DATA.save(rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat')
                                            print(f'{unit.title()} {enable_disable}d.')
                                        else:
                                            print(f'{unit.title()} was already {enable_disable}d.')
                                    elif unit != '':
                                        print(f'{unit.title()} not found.')

                            # View Tech Tree
                            if selection == '0':
                                print('\nKEY: 0 = Disabled, 1 = Enabled, 2 = Enabled (Research Required)')
                                time.sleep(2)
                                print(f'\n-- ARCHERY RANGE -- [{tech_tree["Archery Range"]}]')
                                print(f'Archer [{tech_tree["Archer"]}] --> Crossbowman [{tech_tree["Crossbowman"]}] --> Arbalester [{tech_tree["Arbalester"]}]')
                                print(f'Skirmisher [{tech_tree["Skirmisher"]}] --> Elite Skirmisher [{tech_tree["Elite Skirmisher"]}]')
                                print(f'Hand Cannoneer [{tech_tree["Hand Cannoneer"]}]')
                                print(f'Cavalry Archer [{tech_tree["Cavalry Archer"]}] --> Heavy Cavalry Archer [{tech_tree["Heavy Cavalry Archer"]}]')
                                print(f'Elephant Archer [{tech_tree["Elephant Archer"]}] --> Elite Elephant Archer [{tech_tree["Elite Elephant Archer"]}]')
                                print(f'Thumb Ring [{tech_tree["Thumb Ring"]}]')
                                print(f'Parthian Tactics [{tech_tree["Parthian Tactics"]}]')

                                time.sleep(1)
                                print(f'\n-- BARRACKS -- [{tech_tree["Barracks"]}]')
                                print(f'Militia [{tech_tree["Militia"]}] --> Man-at-Arms [{tech_tree["Man-at-Arms"]}] --> Long Swordsman [{tech_tree["Long Swordsman"]}] --> Two-Handed Swordsman [{tech_tree["Two-Handed Swordsman"]}] --> Champion [{tech_tree["Champion"]}]')
                                print(f'Supplies [{tech_tree["Supplies"]}] --> Gambesons [{tech_tree["Gambesons"]}]')
                                print(f'Spearman [{tech_tree["Spearman"]}] --> Pikeman [{tech_tree["Pikeman"]}] --> Halberdier [{tech_tree["Halberdier"]}]')
                                print(f'Eagle Scout [{tech_tree["Eagle Scout"]}] --> Eagle Warrior [{tech_tree["Eagle Warrior"]}] --> Elite Eagle Warrior [{tech_tree["Elite Eagle Warrior"]}]')
                                print(f'Squires [{tech_tree["Squires"]}]')
                                print(f'Arson [{tech_tree["Arson"]}]')

                                time.sleep(1)
                                print(f'\n-- STABLE -- [{tech_tree["Stable"]}]')
                                print(f'Scout Cavalry [{tech_tree["Scout Cavalry"]}] --> Light Cavalry [{tech_tree["Light Cavalry"]}] --> Hussar [{tech_tree["Hussar"]}]')
                                print(f'Bloodlines [{tech_tree["Bloodlines"]}]')
                                print(f'Knight [{tech_tree["Knight"]}] --> Cavalier [{tech_tree["Cavalier"]}] --> Paladin [{tech_tree["Paladin"]}]')
                                print(f'Steppe Lancer [{tech_tree["Steppe Lancer"]}] --> Elite Steppe Lancer [{tech_tree["Elite Steppe Lancer"]}]')
                                print(f'Camel Rider [{tech_tree["Camel Rider"]}] --> Heavy Camel Rider [{tech_tree["Heavy Camel Rider"]}]')
                                print(f'Battle Elephant [{tech_tree["Battle Elephant"]}] --> Elite Battle Elephant [{tech_tree["Elite Battle Elephant"]}]')
                                print(f'Husbandry [{tech_tree["Husbandry"]}]')

                                time.sleep(1)
                                print(f'\n-- SIEGE WORKSHOP -- [{tech_tree["Siege Workshop"]}]')
                                print(f'Battering Ram [{tech_tree["Battering Ram"]}] --> Capped Ram [{tech_tree["Capped Ram"]}] --> Siege Ram [{tech_tree["Siege Ram"]}]')
                                print(f'Armored Elephant [{tech_tree["Armored Elephant"]}] --> Siege Elephant [{tech_tree["Siege Elephant"]}]')
                                print(f'Mangonel [{tech_tree["Mangonel"]}] --> Onager [{tech_tree["Onager"]}] --> Siege Onager [{tech_tree["Siege Onager"]}]')
                                print(f'Scorpion [{tech_tree["Scorpion"]}] --> Heavy Scorpion [{tech_tree["Heavy Scorpion"]}]')
                                print(f'Siege Tower [{tech_tree["Siege Tower"]}]')
                                print(f'Bombard Cannon [{tech_tree["Bombard Cannon"]}]')

                                time.sleep(1)
                                print(f'\n-- BLACKSMITH -- [{tech_tree["Blacksmith"]}]')
                                print(f'Padded Archer Armor [{tech_tree["Padded Archer Armor"]}] --> Leather Archer Armor [{tech_tree["Leather Archer Armor"]}] --> Ring Archer Armor [{tech_tree["Ring Archer Armor"]}]')
                                print(f'Fletching [{tech_tree["Fletching"]}] --> Bodkin Arrow [{tech_tree["Bodkin Arrow"]}] --> Bracer [{tech_tree["Bracer"]}]')
                                print(f'Forging [{tech_tree["Forging"]}] --> Iron Casting [{tech_tree["Iron Casting"]}] --> Blast Furnace [{tech_tree["Blast Furnace"]}]')
                                print(f'Scale Barding Armor [{tech_tree["Scale Barding Armor"]}] --> Chain Barding Armor [{tech_tree["Chain Barding Armor"]}] --> Plate Barding Armor [{tech_tree["Plate Barding Armor"]}]')
                                print(f'Scale Mail Armor [{tech_tree["Scale Mail Armor"]}] --> Chain Mail Armor [{tech_tree["Chain Mail Armor"]}] --> Plate Mail Armor [{tech_tree["Plate Mail Armor"]}]')

                                time.sleep(1)
                                print(f'\n-- DOCK -- [{tech_tree["Dock"]}]')
                                print(f'Fishing Ship [{tech_tree["Fishing Ship"]}]')
                                print(f'Transport Ship [{tech_tree["Transport Ship"]}]')
                                print(f'Fire Galley [{tech_tree["Fire Galley"]}] --> Fire Ship [{tech_tree["Fire Ship"]}] --> Fast Fire Ship [{tech_tree["Fast Fire Ship"]}]')
                                print(f'Trade Cog [{tech_tree["Trade Cog"]}]')
                                print(f'Gillnets [{tech_tree["Gillnets"]}]')
                                print(f'Cannon Galleon [{tech_tree["Cannon Galleon"]}] --> Elite Cannon Galleon [{tech_tree["Elite Cannon Galleon"]}]')
                                print(f'Demolition Raft [{tech_tree["Demolition Raft"]}] --> Demolition Ship [{tech_tree["Demolition Ship"]}] --> Heavy Demolition Ship [{tech_tree["Heavy Demolition Ship"]}]')
                                print(f'Galley [{tech_tree["Galley"]}] --> War Galley [{tech_tree["War Galley"]}] --> Galleon [{tech_tree["Galleon"]}]')
                                print(f'Dromon [{tech_tree["Dromon"]}]')
                                print(f'Careening [{tech_tree["Careening"]}] --> Dry Dock [{tech_tree["Dry Dock"]}]')
                                print(f'Shipwright [{tech_tree["Shipwright"]}]')
                                print(f'Fish Trap [{tech_tree["Fish Trap"]}]')

                                time.sleep(1)
                                print(f'\n-- UNIVERSITY -- [{tech_tree["University"]}]')
                                print(f'Masonry [{tech_tree["Masonry"]}] --> Architecture [{tech_tree["Architecture"]}]')
                                print(f'Fortified Wall [{tech_tree["Fortified Wall"]}]')
                                print(f'Chemistry [{tech_tree["Chemistry"]}] --> Bombard Tower [{tech_tree["Bombard Tower"]}]')
                                print(f'Ballistics [{tech_tree["Ballistics"]}]')
                                print(f'Siege Engineers [{tech_tree["Siege Engineers"]}]')
                                print(f'Guard Tower [{tech_tree["Guard Tower"]}] --> Keep [{tech_tree["Keep"]}]')
                                print(f'Heated Shot [{tech_tree["Heated Shot"]}]')
                                print(f'Arrowslits [{tech_tree["Arrowslits"]}]')
                                print(f'Murder Holes [{tech_tree["Murder Holes"]}]')
                                print(f'Treadmill Crane [{tech_tree["Treadmill Crane"]}]')

                                time.sleep(1)
                                print(f'OUTPOST [{tech_tree["Outpost"]}]')
                                print(f'WATCH TOWER [{tech_tree["Watch Tower"]}]')
                                print(f'GUARD TOWER [{tech_tree["Guard Tower"]}]')
                                print(f'KEEP [{tech_tree["Keep"]}]')
                                print(f'BOMBARD TOWER [{tech_tree["Bombard Tower"]}]')
                                print(f'PALISADE WALL [{tech_tree["Palisade Wall"]}]')
                                print(f'STONE WALL [{tech_tree["Stone Wall"]}]')

                                time.sleep(1)
                                print(f'\n-- CASTLE -- [{tech_tree["Castle"]}]')
                                print(f'Petard [{tech_tree["Petard"]}]')
                                print(f'Trebuchet [{tech_tree["Trebuchet (Packed)"]}]')
                                print(f'Hoardings [{tech_tree["Hoardings"]}]')
                                print(f'Sappers [{tech_tree["Sappers"]}]')
                                print(f'Conscription [{tech_tree["Conscription"]}]')
                                print(f'Spies/Treason [{tech_tree["Spies/Treason"]}]')

                                time.sleep(1)
                                print(f'\n-- MONASTERY -- [{tech_tree["Monastery"]}]')
                                print(f'Monk [{tech_tree["Monk"]}]')
                                print(f'Illumination [{tech_tree["Illumination"]}]')
                                print(f'Block Printing [{tech_tree["Block Printing"]}]')
                                print(f'Devotion [{tech_tree["Devotion"]}] --> Faith [{tech_tree["Faith"]}]')
                                print(f'Redemption [{tech_tree["Redemption"]}]')
                                print(f'Theocracy [{tech_tree["Theocracy"]}]')
                                print(f'Atonement [{tech_tree["Atonement"]}]')
                                print(f'Herbal Medicine [{tech_tree["Herbal Medicine"]}]')
                                print(f'Heresy [{tech_tree["Heresy"]}]')
                                print(f'Sanctity [{tech_tree["Sanctity"]}]')
                                print(f'Fervor [{tech_tree["Fervor"]}]')

                                time.sleep(1)
                                print(f'HOUSE [{tech_tree["House"]}]')
                                print(f'\n-- TOWN CENTER -- [{tech_tree["Town Center"]}]')
                                print(f'Villager [{tech_tree["Villager"]}]')
                                print(f'Town Watch [{tech_tree["Town Watch"]}] --> Town Patrol [{tech_tree["Town Patrol"]}]')
                                print(f'Loom [{tech_tree["Loom"]}]')
                                print(f'Wheelbarrow [{tech_tree["Wheelbarrow"]}] --> Hand Cart [{tech_tree["Hand Cart"]}]')

                                time.sleep(1)
                                print(f'\n-- MINING CAMP -- [{tech_tree["Mining Camp"]}]')
                                print(f'Gold Mining [{tech_tree["Gold Mining"]}] --> Gold Shaft Mining [{tech_tree["Gold Shaft Mining"]}]')
                                print(f'Stone Mining [{tech_tree["Stone Mining"]}] --> Stone Shaft Mining [{tech_tree["Stone Shaft Mining"]}]')

                                time.sleep(1)
                                print(f'\n-- LUMBER CAMP -- [{tech_tree["Lumber Camp"]}]')
                                print(f'Double-Bit Axe [{tech_tree["Double-Bit Axe"]}] --> Bow Saw [{tech_tree["Bow Saw"]}] --> Two-Man Saw [{tech_tree["Two-Man Saw"]}]')

                                time.sleep(1)
                                print(f'\n-- MARKET -- [{tech_tree["Market"]}]')
                                print(f'Trade Cart [{tech_tree["Trade Cart"]}]')
                                print(f'Coinage [{tech_tree["Coinage"]}] --> Banking [{tech_tree["Banking"]}]')
                                print(f'Caravan [{tech_tree["Caravan"]}]')
                                print(f'Guilds [{tech_tree["Guilds"]}]')

                                time.sleep(1)
                                print(f'\n-- MILL -- [{tech_tree["Mill"]}]')
                                print(f'Farm [{tech_tree["Farm"]}]')
                                print(f'Horse Collar [{tech_tree["Horse Collar"]}] --> Heavy Plow [{tech_tree["Heavy Plow"]}] --> Crop Rotation [{tech_tree["Crop Rotation"]}]')

                            else:
                                print("Invalid selection. Try again.")
            else:
                print("Invalid selection. Try again.")
        except ValueError:
            print("Please enter a valid number.")

if __name__ == "__main__":
    main()