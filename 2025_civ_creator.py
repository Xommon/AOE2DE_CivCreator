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

def save_description(description_code_, description_lines_):
    with open(MOD_STRINGS, 'r+') as file:
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
    global MOD_NAME
    MOD_NAME = mod_folder.split('/')[-1]

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
    with open(f'{MOD_FOLDER}/{mod_folder.split("/")[-1]}.pkl', 'rb') as file:
        while True:
            try:
                architecture_set = pickle.load(file)
                ARCHITECTURE_SETS.append(architecture_set)
                file.readline()  # Read the newline character
            except EOFError:
                break
    print('Mod loaded!')
    
def new_mod(mod_folder, aoe2_folder, mod_name, revert):
    # Announce revert
    if revert:
        print(f'Reverting {mod_name}...')

        os.chdir(mod_folder)
        os.chdir('..')

        # Delete existing mod folder
        shutil.rmtree(mod_folder)

        # Ensure the working directory is set correctly before creating a new folder
        #os.chdir(mod_folder.split('/'))  # Go to the parent mods folder
        #os.chdir('..')  # Go to the parent folder
        print(os.getcwd())
        return

    # Get local mods folder
    if mod_folder == '':
        local_mods_folder = input("\nEnter local mods folder location: ")
        if local_mods_folder == '':
            local_mods_folder = '/home/xommon/snap/steam/common/.local/share/Steam/steamapps/compatdata/813780/pfx/drive_c/users/steamuser/Games/Age of Empires 2 DE/76561198021486964/mods/local'
    else:
        local_mods_folder = mod_folder

    # Get original AoE2DE folder
    if aoe2_folder == '':
        aoe2_folder = input("Select original \"AoE2DE\" folder location: ")
        if aoe2_folder == '':
            aoe2_folder = '/home/xommon/snap/steam/common/.local/share/Steam/steamapps/common/AoE2DE'
    else:
        aoe2_folder = aoe2_folder

    # Get name for mod
    if mod_name == '':
        mod_name = input("Enter new mod name: ")
    else:
        mod_name = mod_name

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
    if revert:
        print(f"{mod_name} reverted successfully!\n")
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
            previous_mod_name = previous_mod_folder.split('/')[-1]
    except:
        pass

    # Main menu
    print("\033[32m--- AOE2DE Civilization Creator ---\033[0m")
    global MOD_FOLDER
    if os.path.exists(previous_mod_folder + '/' + previous_mod_name + '.pkl'):
        print(f"\033[33m0: Open {previous_mod_name}\033[0m")
        print("\033[33m1: Open Mod...\033[0m")
        print("\033[33m2: New Mod...\033[0m")
    else:
        print("\033[33m0: Open Mod...\033[0m")
        print("\033[33m1: New Mod...\033[0m")
    selection = input("Selection: ")

    
    if os.path.exists(previous_mod_folder + '/' + previous_mod_name + '.pkl'):
        if selection == '0': # Open last mod
            open_mod(previous_mod_folder)
        elif selection == '1': # Open mod
            MOD_FOLDER = input("\nMod folder location: ")
            open_mod(MOD_FOLDER)
        elif selection == '2': # New mod
            new_mod('', '', '', False)
    else:
        if selection == '0': # Open mod
            MOD_FOLDER = input("\nMod folder location: ")
            open_mod(MOD_FOLDER)
        elif selection == '1': # New mod
            new_mod('', '', '', False)

    # Mod menu
    mod_name = MOD_FOLDER.split('/')[-1]
    while True:
        # Display all of the civilisations
        time.sleep(1)
        print(f"\033[32m\n--- {mod_name} Menu ---\033[0m")
        print("\033[33m0: Edit Civilization\033[0m")
        print("\033[33m1: Revert Mod\033[0m")
        mod_menu_selection = input("Selection: ")

        # Edit Civilisation
        print('\n')
        if mod_menu_selection == '0':
            selected_civ_index = -1
            with open (MOD_STRINGS, 'r') as file:
                lines = file.readlines()
                for i in range(len(DATA.civs) - 1):
                    print(rf'{i}: {lines[i][7:-2]}')
            selection = input("Selection: ")
            selected_civ_index = int(selection)
            selected_civ_name = lines[selected_civ_index][7:-2]

            # Separate the description to be edited later
            with open(MOD_STRINGS, 'r') as file:
                lines = file.readlines()
                line_index = selected_civ_index + len(DATA.civs) - 1
                line = lines[line_index]
                description_code = line[:6]
                description_lines = line[8:].split(r'\n')

                # Remove any unnecessary characters from the strings
                description_lines = [s.replace('"', '') for s in description_lines]
                description_lines = [s.replace('\n', '') for s in description_lines]

        # Revert Mod
        elif mod_menu_selection == '1':
            print("\033[31mWARNING: Reverting the mod will completely erase all changes made to the modded files. THIS CHANGE IS IRREVERSIBLE.\033[0m")
            time.sleep(0.5)
            yes = input("Enter 'Y' to continue: ")

            new_mod(MOD_FOLDER, ORIGINAL_FOLDER, MOD_NAME, True)

            print("Mod reverted successfully!\n")

        # Edit civilisation
        try:
            edit_civ_index = int(selection)
            if 0 <= edit_civ_index < len(DATA.civs):
                while True:
                    print(f"\033[32m\n--- Edit {selected_civ_name} ---\033[0m")
                    print("\033[33m0: Name\033[0m")
                    print("\033[33m1: Title\033[0m")
                    print("\033[33m2: Bonuses\033[0m")
                    print("\033[33m3: Unique Unit\033[0m")
                    print("\033[33m4: Architecture\033[0m")
                    print("\033[33m5: Language\033[0m")
                    print("\033[33m6: Tech Tree\033[0m")
                    selection = input("Selection: ")

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

                        # Change name
                        DATA.civs[edit_civ_index + 1].name = new_name
                        with open(MOD_STRINGS, 'r+') as file:
                            lines = file.readlines()  # Read all lines
                            lines[selected_civ_index] = lines[selected_civ_index][:5] + f' "{new_name}"\n'  # Modify the specific line
                            selected_civ_name = new_name  # Update the selected civ name

                            file.seek(0)  # Move to the beginning of the file
                            file.writelines(lines)  # Write all lines back

                    # Title
                    if selection == '1':
                        # Get user input
                        new_title = input(f"\nEnter new civilization title for {selected_civ_name} (ex. Infantry and Monk): ").lower()

                        # Replace the title
                        if 'civilization' in new_title or 'civilisation' in new_title:
                            description_lines[0] = new_title
                        else:
                            description_lines[0] = description_lines[0] = new_title + ' civilization'
                        description_lines[0] = description_lines[0].title()

                        # Update the description
                        save_description(description_code, description_lines)
                        print(f'Title updated for {selected_civ_name} to {description_lines[0]}')
                        time.sleep(1)

                    # Bonuses
                    elif selection == '2':
                        bonus_selection = '?'
                        while bonus_selection != '':
                            print("\033[32m\n--- Bonuses Menu ---\033[0m")
                            print("\033[33m0: View Bonuses\033[0m")
                            print("\033[33m1: Add Bonus\033[0m")
                            print("\033[33m2: Remove Bonus\033[0m")
                            bonus_selection = input("Selection: ")

                            with open(MOD_STRINGS, 'r+') as file:
                                # Read and separate the lines
                                lines = file.readlines()
                                line_index = selected_civ_index + len(DATA.civs) - 1
                                line = lines[line_index]
                                line_code = line[:6]
                                split_lines = line.split(r'\n')

                                # View Bonuses
                                if bonus_selection == '0':
                                    bonus_count = 0
                                    searching_for_dots = True
                                    next_line = False
                                    print('\n')
                                    for line in split_lines:
                                        if 'Unique' in line:
                                            searching_for_dots = False
                                        elif '•' in line and searching_for_dots:
                                            print(str(bonus_count) + ': ' + line[2:])
                                            bonus_count += 1
                                        elif 'Team Bonus' in line:
                                            next_line = True
                                        elif next_line:
                                            print('Team Bonus:', line[:-1])

                                # Add bonus
                                elif bonus_selection == '1':
                                    # Get user prompt
                                    bonus_to_add_ORIGINAL = input('\nType a bonus to add: ')
                                    bonus_to_add = bonus_to_add_ORIGINAL.lower()
                                    effect_commands = []

                                    # [Technology] free
                                    if 'free' in bonus_to_add:
                                        # Strip useless words using regex
                                        useless_words = ["free", "is", "are", "upgrade", "upgrades"]
                                        cleaned_bonus = re.sub(r'\b(?:' + '|'.join(useless_words) + r')\b', '', bonus_to_add).strip()

                                        # Extract the interactable parts
                                        bonus_parts = re.split(r',\s*|\s+and\s+', cleaned_bonus)

                                        # Remove any empty strings from the list
                                        bonus_parts = [part.strip() for part in bonus_parts if part.strip()]

                                        # Extract the techs from the description
                                        tech_ids = []
                                        for i, tech_id in enumerate(DATA.techs):
                                            for part in bonus_parts:
                                                if part == DATA.techs[i].name.lower():
                                                    tech_ids.append(i)

                                        # Exit if nothing was found
                                        if len(tech_ids) == 0:
                                            print("\033[31mERROR: No techs with the names given found.\033[0m")
                                            break

                                        # Create effect commands
                                        for id in tech_ids:
                                            # Remove cost
                                            effect_commands.append(genieutils.effect.EffectCommand(101, id, 0, 0, 0))
                                            effect_commands.append(genieutils.effect.EffectCommand(101, id, 1, 0, 0))
                                            effect_commands.append(genieutils.effect.EffectCommand(101, id, 2, 0, 0))
                                            effect_commands.append(genieutils.effect.EffectCommand(101, id, 3, 0, 0))

                                            # Remove time
                                            effect_commands.append(genieutils.effect.EffectCommand(103, id, 0, 0, 0))

                                        # Exit if nothing was found
                                        if len(effect_commands) == 0:
                                            print("\033[31mERROR: No techs with the names given found.\033[0m")
                                            break

                                        # Create new effect if it doesn't already exist
                                        effect_found = False
                                        effect_name = selected_civ_name.upper() + ": " + bonus_to_add_ORIGINAL
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

                                        # Create the tech that replaces the old unit
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
                                        print(f"Added new bonus.")
                                        time.sleep(0.5)

                                # Add Bonus
                                elif bonus_selection == '1':
                                    print("\033[32m\n--- Bonus Prompts ---\033[0m")
                                    print("\033[33m0: \033[4mTechnology\033[0m\033[33m free\033[0m")
                                    prompt_selection = input('Select a bonus prompt: ')

                                    # Prompts
                                    if prompt_selection == '0':
                                        technology_names = []
                                        technology_ids = []
                                        while True:
                                            tech_to_add = input('\nEnter a technology name (leave blank to finish): ').lower()
                                            if tech_to_add == '':
                                                break
                                            elif tech_to_add == '?':
                                                pass
                                            elif tech_to_add not in technology_names:
                                                with open(ORIGINAL_STRINGS, 'r') as file:
                                                    lines = file.readlines()
                                                    for i, tech in enumerate(DATA.techs):
                                                        try:
                                                            # Get the name of the technology
                                                            tech_name_id = int(tech.language_dll_name)
                                                            tech_name = None

                                                            # Extract tech name from ORIGINAL_STRINGS
                                                            for line in lines:
                                                                if line.startswith(f"{tech_name_id} "):
                                                                    tech_name = line.split('"')[1].lower()
                                                                    break
                                                            
                                                            if tech_name:
                                                                if tech_name == tech_to_add:
                                                                    technology_names.append(tech_to_add)
                                                                    technology_ids.append(i)
                                                        except:
                                                            print('Passing')
                                                            pass
                                            elif tech_to_add in technology_names:
                                                print("\033[4;31mERROR: Technology already added.\033[0m")

                                        # Add technology bonus
                                        if len(technology_names) == 0:
                                            print("\033[4;31mERROR: Bonus not added. Must specify at least 1 technology.\033[0m")
                                        else:
                                            for i, tech_id in enumerate(technology_ids):
                                                # Create a new effect
                                                effect_commands = []
                                                for tech in technology_ids:
                                                    # Remove cost
                                                    effect_commands.append(genieutils.effect.EffectCommand(101, {tech}, 0, 0, 0))
                                                    effect_commands.append(genieutils.effect.EffectCommand(101, {tech}, 1, 0, 0))
                                                    effect_commands.append(genieutils.effect.EffectCommand(101, {tech}, 2, 0, 0))
                                                    effect_commands.append(genieutils.effect.EffectCommand(101, {tech}, 3, 0, 0))

                                                    # Remove time
                                                    effect_commands.append(genieutils.effect.EffectCommand(103, {tech}, 0, 0, 0))

                                                # Create new effect if it doesn't exist
                                                effect_found = False
                                                effect_name = selected_civ_name.title() + " Bonus: Free" + tech_to_add.title()

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

                                                # Create the tech that replaces the old unit
                                                new_tech = DATA.techs[1101]
                                                new_tech.effect_id = effect_index
                                                new_tech.name = effect_name
                                                new_tech.civ = selected_civ_index + 1

                                                for tech in DATA.techs:
                                                    if tech.name == effect_name:
                                                        DATA.techs.remove(tech)
                                                DATA.techs.append(new_tech)

                                                # Edit the description
                                                with open(MOD_STRINGS, 'r+') as file:
                                                    # Read and separate the lines
                                                    lines = file.readlines()
                                                    line_index = selected_civ_index + len(DATA.civs) - 1
                                                    line = lines[line_index]
                                                    line_code = line[:6]
                                                    split_lines = line.split(r'\n')

                                                    # Extract the relevant portion of the description
                                                    description = line
                                                    parts = description.split("\n\n", 2)  # Split into three parts: before, target, and after

                                                    if len(parts) > 0:
                                                        before, target, after = parts  # Extract the parts
                                                        target_lines = target.split("\n")  # Split the target portion into an array of strings

                                                        # Check if bonus already exists
                                                        if (f"• {bonus_to_add_ORIGINAL}") in target_lines:
                                                            print("\033[31mERROR: Bonus already exists.\033[0m")
                                                            break

                                                        # Add the new bonus to the array
                                                        target_lines.append(f"• {bonus_to_add_ORIGINAL}")

                                                        # Rejoin the modified target portion
                                                        modified_target = "\n".join(target_lines)

                                                        # Reconstruct the full description
                                                        updated_description = f"{before}\n\n{modified_target}\n\n{after}"

                                                        # Write the updated description back to the file or data structure
                                                        line = updated_description

                                                    # Overwrite the file with modified content
                                                    file.seek(0)
                                                    file.writelines(lines)
                                                    file.truncate()  # Ensure remaining old content is removed

                                                # Save changes
                                                print(f"Added new bonus.")
                                                DATA.save(rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat')

                    # Unique Unit
                    elif selection == '3':
                        # Populate all castle units
                        all_castle_units = ["longbowman", "throwing axeman", "berserk", "teutonic knight", "samurai", "chu ko nu", "cataphract", "war elephant", "mameluke", "janissary", "huskarl", "mangudai", "woad raider", "conquistador", "jaguar warrior", "plumed archer", "tarkan", "war wagon", "genoese crossbowman", "ghulam", "kamayuk", "magyar huszar", "boyar", "organ gun", "shotel warrior", "gbeto", "camel archer", "ballista elephant", "karambit warrior", "arambai", "rattan archer", "konnik", "keshik", "kipchak", "leitis", "coustillier", "serjeant", "obuch", "hussite wagon", "urumi swordsman", "ratha", "chakram thrower", "centurion", "composite bowman", "monaspa", "amazon warrior", "amazon archer", "camel raider", "cretan archer", "crusader knight", "tomahawk warrior", "ninja", "scimitar warrior", "drengr", "qizilbash warrior", "axe cavalry", "xolotl warrior", "sun warrior", "island sentinel"]
                        new_castle_unit = '?'
                        while new_castle_unit == '?':
                            new_castle_unit = input(f"\nEnter unique Castle unit for {selected_civ_name} (leave blank for original): ").lower()

                            if new_castle_unit not in all_castle_units:
                                new_castle_unit = '?'
                                print("\033[31mERROR: Unit not found.")
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
                        
                        # Create the tech that replaces the old unit
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
                        # Gather base architectures
                        base_architectures = []
                        for i in range(1, len(DATA.civs)):
                            base_architectures.append(DATA.civs[i].name)

                        # Gather custom architectures
                        custom_arcs = [
                            [],
                            ['Poenari Castle'],
                            ['Aachen Cathedral', 'Dome of the Rock', 'Dormition Cathedral', 'Gol Gumbaz', 'Minaret of Jam', 'Pyramid', 'Quimper Cathedral', 'Sankore Madrasah', 'Tower of London']
                        ]

                        # User prompts
                        architecture_types = ["General", "Castle", "Wonder"]
                        architecture_changes = [-1, -1, -1]
                        print('\n')
                        for i in range(3):
                            # Assemble all architecture options
                            all_architectures = base_architectures + custom_arcs[i]

                            architecture_selection = '?'
                            while architecture_selection == '?':
                                architecture_selection = input(f"Enter {architecture_types[i]} architecture for {selected_civ_name}: ").lower()
                                
                                if architecture_selection == '?':
                                    # Print all available options
                                    print(', '.join(all_architectures))
                                    print('Leave blank to leave the architecture type unchanged')
                                    print('Type \'default\' to switch back to the Civilization\'s original architecture.')
                                    continue
                                
                                # Check against architecture options
                                for i2 in range(len(all_architectures)):
                                    if architecture_selection == all_architectures[i2].lower():
                                        architecture_changes[i] = i2
                                        break
                                
                                # Use previous architecture if blank
                                if architecture_selection == '':
                                    architecture_changes[i] = -1

                                # Use default architecture
                                elif architecture_selection == 'default':
                                    architecture_changes[i] = selected_civ_index

                                # Check if architecture is invalid
                                elif architecture_changes[i] == -1:
                                    architecture_selection = '?'
                                    print(f'\033[31mERROR: {architecture_types[i]} architecture type not valid.\n\033[0m')
                        print(architecture_changes)

                        for i in range(3):
                            # Skip if unspecified
                            if architecture_changes[i] == -1:
                                continue

                            # Load architecture graphics
                            try:
                                original_units = ARCHITECTURE_SETS[architecture_changes[i] + 1]
                            except:
                                original_units = ARCHITECTURE_SETS[architecture_changes[1]]

                            # Specify which unit IDs need to change
                            if i == 0:
                                all_units_to_change = range(0, len(DATA.civs[1].units))
                            elif i == 1:
                                all_units_to_change = [82, 1430]
                            elif i == 2:
                                all_units_to_change = [276, 1445]

                            for unit_id in all_units_to_change:
                                # Select which unit will be the basis for change
                                if (architecture_changes[i] < len(DATA.civs) - 1):
                                    unit_to_change_to = original_units[unit_id]
                                else:
                                    # Custom unit
                                    custom_ids = [
                                        [],
                                        [[445, 1488]],
                                        [[1622, 1517], [690, 1482], [1369, 1493], [1217, 1487], [1773, 1530], [689, 1515], [873, 1489], [1367, 1491], [1368, 1492]]
                                    ]

                                    custom_unit_id = custom_ids[i][architecture_changes[i] - len(DATA.civs) + 1][all_units_to_change.index(unit_id)]
                                    unit_to_change_to = original_units[custom_unit_id]

                                # Look for custom unit
                                if len(custom_arcs[i]) > 0:
                                    for j, custom_arc in enumerate(custom_arcs[i]):
                                        if architecture_selection == custom_arc:
                                            unit_to_change_to = DATA.civs[selected_civ_index].units.index(custom_arc)
                                            print(unit_to_change_to)
                                            break

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
                        time.sleep(1)

                    # Language / Sound
                    elif selection == '5':
                        #all_languages = ', '.join([civ.name for civ in DATA.civs])
#
                        ## Change language
                        #while True:
                        #    new_language = input(f"\nEnter new language for {selected_civ_name}: ").lower()
#
                        #    if new_language == '':
                        #        break
                        #    elif new_language == '?':
                        #        print(all_languages)
                        #    elif new_language.title() in all_languages:
#
                        #        # Save changes
                        #        #DATA.save(rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat')
                        #        print(f"Language for {selected_civ_name} changed to {new_language.title()}.")
                        #        time.sleep(1)
                        #        break
                        #    else:
                        #        print('ERROR: Language not found.')
                        #pass

                        # DEBUG

                        # Copy language sound items of the civilization we want
                        #genieutils.sound.SoundItem.
                        DATA.sounds[303].items[1].civilization = 1
                        DATA.sounds[303].items[2].civilization = 1
                        DATA.sounds[303].items[3].civilization = 1

                        DATA.sounds[303].items[4].civilization = 15
                        DATA.sounds[303].items[5].civilization = 15
                        DATA.sounds[303].items[6].civilization = 15
                        DATA.sounds[303].items[7].civilization = 15
                        
                        

                        DATA.save(rf'{MOD_FOLDER}/resources/_common/dat/empires2_x2_p1.dat')

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
                                print("\033[32m\n--- Tech Tree Menu ---\033[0m")
                                print("\033[33m0: View Tech Tree\033[0m")
                                print("\033[33m1: Enable Items\033[0m")
                                print("\033[33m2: Disable Items\033[0m")
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
