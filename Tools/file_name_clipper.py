# Rename ornery files

import os

def rename_files():
    # Prompt user for input
    folder_path = input("Enter the folder path: ")
    old_text = input("Enter the text to replace: ")
    new_text = input("Enter the replacement text: ")

    # Check if the folder path is valid
    if not os.path.isdir(folder_path):
        print("Invalid folder path. Please try again.")
        return

    # Iterate through files in the folder and rename them
    for filename in os.listdir(folder_path):
        if old_text in filename:
            new_filename = filename.replace(old_text, new_text)
            # Get the full paths for the original and new filenames
            original_file = os.path.join(folder_path, filename)
            new_file = os.path.join(folder_path, new_filename)
            # Rename the file
            os.rename(original_file, new_file)
            print(f'Renamed: {filename} -> {new_filename}')

# Run the rename function
rename_files()