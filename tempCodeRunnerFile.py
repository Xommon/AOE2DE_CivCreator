def open_project(path):
    global civilisation_objects
    civilisation_objects = []
    if path == '':
        PROJECT_FILE = path
    else:
        PROJECT_FILE = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])

    if PROJECT_FILE:
        with open(PROJECT_FILE, 'r') as file:
            # Set all the file and folder pathways
            lines = file.read().splitlines()
            ORIGINAL_FOLDER = lines[0]
            MOD_FOLDER = lines[1]
            ORIGINAL_STRINGS_FILE = rf'{MOD_FOLDER}\resources\en\strings\key-value\key-value-strings-utf8.txt'
            MODDED_STRINGS_FILE = rf'{MOD_FOLDER}\resources\en\strings\key-value\key-value-modded-strings-utf8.txt'
            CIV_TECH_TREES_FILE = rf'{MOD_FOLDER}\resources\_common\dat\civTechTrees.json'
            CIV_IMAGE_FOLDER = rf'{MOD_FOLDER}\widgetui\textures\menu\civs'
        
        # Import civilisations and create an object for them and give values for their units
        with open(CIV_TECH_TREES_FILE, 'r', encoding='utf-8') as file:
            lines = file.read().splitlines()
            ui.civilisation_dropdown.clear()

            # Create new civilisation
            for line in lines:
                if '\"civ_id\":' in line:
                    # Get the name and add it to the dropdown
                    new_name = line[16:].replace('"', '').replace(',', '').capitalize()
                    ui.civilisation_dropdown.addItem(new_name)
                    
                    # Get the name ID
                    with open(MODDED_STRINGS_FILE, 'r', encoding='utf-8') as strings_file:
                        strings_lines = strings_file.read().splitlines()

                        for i, string_line in enumerate(strings_lines):
                                if new_name in string_line:
                                        new_name_id = strings_lines[i][:6]
                                        new_index = i

                    # Create Civilisation object
                    current_civilisation = Civilisation(new_index, new_name, '', new_name_id, '', rf'{CIV_IMAGE_FOLDER}/{new_name.lower()}.png', {})
                    civilisation_objects.append(current_civilisation)

                    # Populate unit dictionary
                elif '\"Name\":' in line:
                    # Enter new unit name
                    currentUnit = line[18:].replace('"', '').replace(',', '')
                elif '\"Node Status\":' in line:
                    status = line[25:].replace('"', '').replace(',', '')
                    if status == "ResearchedCompleted":
                        current_civilisation.units[currentUnit] = 1
                    elif status == "NotAvailable":
                        current_civilisation.units[currentUnit] = 2
                    elif status == "ResearchRequired":
                        current_civilisation.units[currentUnit] = 3

        # Get the description and description ID
        with open(MODDED_STRINGS_FILE, 'r', encoding='utf-8') as strings_file:
            strings_lines = strings_file.read().splitlines()
            total_civ_count = len(civilisation_objects)
            for i in range(total_civ_count):
                civilisation_objects[i].desc_id = strings_lines[total_civ_count + i][:6]
                civilisation_objects[i].description = strings_lines[total_civ_count + i][7:]