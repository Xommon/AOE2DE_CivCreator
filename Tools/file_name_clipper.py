# Rename ornery files

import os

def rename_files(folder_path, old, new):
    for filename in os.listdir(folder_path):
        if filename.startswith(old):
            new_filename = filename.replace(old, new)
            # Get the full paths for the original and new filenames
            original_file = os.path.join(folder_path, filename)
            new_file = os.path.join(folder_path, new_filename)
            # Rename the file
            os.rename(original_file, new_file)
            print(f'Renamed: {filename} -> {new_filename}')

# Specify the folder containing the files to rename
rename_files(r'C:\Users\Micheal Q\Games\Age of Empires 2 DE\76561198021486964\mods\local\15eFq\resources\_common\drs\sounds', "Indians_", "Hindustanis_")