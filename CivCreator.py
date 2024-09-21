import os
import shutil
import tkinter as tk
from tkinter import Tk, Menu, Label, ttk, Canvas, Toplevel, Entry
from tkinter.filedialog import askdirectory, askopenfilename
from tkinter import messagebox
import sys
import json
import string

# Civilisation object
class Civilisation:
    def __init__(self, name):
        self.name = name
        self.units = {}

# Global variables to store the selected AoE2DE folder path and mod save path
selected_folder_path = None
mod_save_path = None

# Function to count files in specified folders and files
def count_files_in_specified_items(folder_path, items_to_copy):
    total_files = 0
    for item in items_to_copy:
        full_item_path = os.path.join(folder_path, item)
        if os.path.isfile(full_item_path):  # If it's a file
            total_files += 1
        elif os.path.isdir(full_item_path):  # If it's a folder
            for _, _, filenames in os.walk(full_item_path):
                total_files += len(filenames)
    return total_files

# Function to copy specified folders and files with progress tracking
def copy_specified_items_with_progress(src_base_folder, items_to_copy, dst_base_folder, progress_bar, total_files, progress_window, progress_label):
    files_copied = 0
    for item in items_to_copy:
        src_item_path = os.path.join(src_base_folder, item)
        if os.path.isfile(src_item_path):  # If it's a file
            dst_item_path = os.path.join(dst_base_folder, item)
            os.makedirs(os.path.dirname(dst_item_path), exist_ok=True)
            shutil.copy2(src_item_path, dst_item_path)
            files_copied += 1
        elif os.path.isdir(src_item_path):  # If it's a folder
            for dirpath, _, filenames in os.walk(src_item_path):
                relative_path = os.path.relpath(dirpath, src_item_path)
                dst_dirpath = os.path.join(dst_base_folder, relative_path)
                os.makedirs(dst_dirpath, exist_ok=True)

                for filename in filenames:
                    src_file = os.path.join(dirpath, filename)
                    dst_file = os.path.join(dst_dirpath, filename)
                    shutil.copy2(src_file, dst_file)
                    files_copied += 1
        
        # Update progress bar and label
        progress_percentage = (files_copied / total_files) * 100
        progress_bar['value'] = progress_percentage
        progress_label.config(text=f"Saving: {progress_percentage:.2f}%")
        progress_window.update_idletasks()  # Update the UI

# Function to save a .txt file inside the mod folder
def save_txt_file(project_name, original_path, mod_path):
    try:
        txt_content = f"{original_path}\n{mod_path}"
        
        # Save the .txt file inside the project folder with the same name as the project
        txt_file_path = os.path.join(mod_save_path, f"{project_name}.txt")
        with open(txt_file_path, 'w') as file:
            file.write(txt_content)
        
        messagebox.showinfo("Success", f"{project_name}.txt file saved successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save .txt file: {e}")

# Function to open a .txt file and read it
def open_txt_file():
    global current_txt_file_path  # Declare global to store the file path
    txt_file_path = askopenfilename(filetypes=[("Text files", "*.txt")])

    if not txt_file_path:
        return  # User canceled file selection

    try:
        # Debug: Print file path
        print(f"Opening file: {txt_file_path}")

        # Read the .txt file
        with open(txt_file_path, 'r') as file:
            txt_content = file.read()

        # Debug: Check if file read was successful
        print(f"File read successfully, length: {len(txt_content)} characters")

        # The .txt content is in the format: original_path\nmod_path
        original_path, mod_path = txt_content.split('\n')

        # Check if both paths exist
        if not os.path.exists(original_path) or not os.path.exists(mod_path):
            messagebox.showerror("Error", "One or both of the paths no longer exist.")
            sys.exit("Error: Missing paths.")

        # Store the path of the opened .txt file
        current_txt_file_path = txt_file_path

        # Update the title of the main window with the project name (without .txt)
        project_name = os.path.basename(txt_file_path).replace(".txt", "")
        root.title(f"{original_title} - {project_name}")

        # Import tech trees
        techTrees = ''
        currentCiv = None
        currentUnit = ''
        civilisations = []
        with open(f'{mod_path}/resources/_common/dat/civTechTrees.json', 'r') as file:
            techTrees = file.read()
            dropdown_values = []
            for line in techTrees.splitlines():
                if '\"civ_id\":' in line:
                    # Enter new civilisation
                    newCiv = line[16:].replace('"', '').replace(',', '')
                    formatted_civ = newCiv[0].upper() + newCiv[1:].lower()
                    dropdown_values.append(formatted_civ)
                    currentCiv = Civilisation(formatted_civ)
                    civilisations.append(currentCiv)
                elif '\"Name\":' in line:
                    # Enter new unit name
                    currentUnit = line[18:].replace('"', '').replace(',', '')
                elif '\"Node Status\":' in line:
                    status = line[25:].replace('"', '').replace(',', '')
                    if status == "ResearchedCompleted":
                        currentCiv.units[currentUnit] = 1
                    elif status == "NotAvailable":
                        currentCiv.units[currentUnit] = 2
                    elif status == "ResearchRequired":
                        currentCiv.units[currentUnit] = 3

            # Update the dropdown with the new values
            dropdown['values'] = dropdown_values
            dropdown.current(0)

            # Function to print the units of the selected civilization when a new item is selected in the dropdown
            def on_dropdown_change(event):
                selected_civ_name = dropdown.get()  # Get the selected item from the dropdown

                # Find the corresponding Civilisation object in the civilisations list
                selected_civ = next((civ for civ in civilisations if civ.name == selected_civ_name), None)

                if selected_civ:
                    print(f"Units for {selected_civ.name}:")
                    for unit, status in selected_civ.units.items():
                        print(f"  {unit}: {status}")
                else:
                    print(f"No civilization found for {selected_civ_name}")

            # Bind the dropdown selection event to the function
            dropdown.bind("<<ComboboxSelected>>", on_dropdown_change)
        
    except Exception as e:
        print(f"Error: {e}")
        messagebox.showerror("Error", f"Failed to open .txt file: {e}")
        sys.exit("Error: Failed to open .txt file.")

# Function to open the file explorer and validate the AoE2DE folder
def selectAoE2DEFolder(entry_field):
    global selected_folder_path
    folder_path = askdirectory()

    if not folder_path:
        return
    
    if not os.path.basename(folder_path) == "AoE2DE":
        messagebox.showerror("Invalid Folder", "ERROR: Folder must be named 'AoE2DE'.")
    else:
        selected_folder_path = folder_path
        entry_field.config(state="normal")
        entry_field.delete(0, tk.END)
        entry_field.insert(0, folder_path)
        entry_field.config(state="readonly")

# Function to open the file explorer for mod save location
def selectModPathway(entry_field, project_name):
    global mod_save_path
    target_folder = askdirectory()

    if not target_folder:
        return

    new_folder_name = project_name
    new_mod_path = os.path.join(target_folder, new_folder_name)

    mod_save_path = new_mod_path
    entry_field.config(state="normal")
    entry_field.delete(0, tk.END)
    entry_field.insert(0, new_mod_path)
    entry_field.config(state="readonly")

# Function to center a window relative to the main window
def center_window(window, width, height):
    # Get the dimensions of the main window (root)
    root.update_idletasks()  # Ensure root has been fully rendered
    root_width = root.winfo_width()
    root_height = root.winfo_height()
    root_x = root.winfo_x()
    root_y = root.winfo_y()

    # Calculate the position to center the new window
    x = root_x + (root_width // 2) - (width // 2)
    y = root_y + (root_height // 2) - (height // 2)

    # Set the geometry of the new window
    window.geometry(f"{width}x{height}+{x}+{y}")

# Function to create the new project with specified folders/files
def createNewProject(project_name):
    global mod_save_path
    
    if not project_name:
        messagebox.showerror("Error", "Project name cannot be empty.")
        return
    
    original_path = original_path_entry.get()
    mod_path = mod_path_entry.get()

    # Check if both pathways are filled
    if not original_path or not mod_path:
        messagebox.showerror("Error", "You must select both the original pathway and mod pathway.")
        return

    # Check if the values are still the default placeholders, and allow them if true
    if original_path == r"C:\Program Files (x86)\Steam\steamapps\common\AoE2DE" and mod_path == r"C:\Users\Micheal Q\Games\Age of Empires 2 DE\76561198021486964\mods\local":
        selected_folder_path = original_path
        mod_save_path = mod_path

    # Create the project folder inside the mod path (with the project name)
    mod_save_path = os.path.join(mod_path, project_name)
    if not os.path.exists(mod_save_path):
        os.makedirs(mod_save_path)

    # Specify which folders and files you want to copy
    resources_items_to_copy = ['_common/dat/civilizations.json', '_common/dat/civTechTrees.json', '_common/wpfg/resources/civ_techtree', '_common/wpfg/resources/uniticons', 'en/strings/key_value']  # Example: specify resources
    widgetui_items_to_copy = ['textures/menu/civs']   # Example: specify widgetui

    # Count total files in both resources and widgetui
    total_files_resources = count_files_in_specified_items(os.path.join(selected_folder_path, 'resources'), resources_items_to_copy)
    total_files_widgetui = count_files_in_specified_items(os.path.join(selected_folder_path, 'widgetui'), widgetui_items_to_copy)
    total_files = total_files_resources + total_files_widgetui

    try:
        # Create the main project folder if it doesn't exist
        os.makedirs(mod_save_path, exist_ok=True)

        # Create a new window for progress bar
        progress_window = Toplevel(root)
        progress_window.title("Saving Mod...")
        center_window(progress_window, 400, 150)  # Center the progress window

        # Create a progress bar inside the popup window
        progress_bar = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="determinate")
        progress_bar.pack(pady=20)

        # Create a label to indicate the saving status inside the popup window
        progress_label = Label(progress_window, text="Starting...")
        progress_label.pack()

        # Copy the specified folders and files for resources
        copy_specified_items_with_progress(
            os.path.join(selected_folder_path, 'resources'),
            resources_items_to_copy,
            os.path.join(mod_save_path, 'resources'),
            progress_bar, total_files, progress_window, progress_label
        )

        # Copy the specified folders and files for widgetui
        copy_specified_items_with_progress(
            os.path.join(selected_folder_path, 'widgetui'),
            widgetui_items_to_copy,
            os.path.join(mod_save_path, 'widgetui'),
            progress_bar, total_files, progress_window, progress_label
        )

        progress_label.config(text="Save Completed!")
        messagebox.showinfo("Success", f"Mod successfully saved to '{mod_save_path}'!")

        # Save the .txt file
        save_txt_file(project_name, selected_folder_path, mod_save_path)

        # Close the popup window after the saving is complete
        progress_window.after(1000, progress_window.destroy)

        # Close the project creation window
        project_creation_window.destroy()

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while saving the mod: {e}")

# Add this variable globally to track if the window is open
project_creation_window = None

def new_project_flow():
    global project_creation_window, original_path_entry, mod_path_entry  # Make entries global
    
    # If the window already exists, just bring it to the front
    if project_creation_window is not None and tk.Toplevel.winfo_exists(project_creation_window):
        project_creation_window.lift()
        return

    # Create a new window for project creation
    project_creation_window = Toplevel(root)
    
    # Make sure the "Create Project" window is a child of the main window and stays on top of it
    project_creation_window.transient(root)
    
    project_creation_window.geometry("500x350")
    project_creation_window.title("New Project")
    center_window(project_creation_window, 500, 350)  # Center the project creation window

    # Project name label and entry
    Label(project_creation_window, text="Project Name").pack(pady=10)
    project_name_entry = Entry(project_creation_window)
    project_name_entry.pack()

    # Original Pathway label and entry field
    Label(project_creation_window, text="Original Pathway").pack(pady=10)
    original_path_entry = Entry(project_creation_window, state="readonly")
    original_path_entry.pack()
    original_path_entry.config(state="normal")  # Enable the entry to insert the value
    original_path_entry.insert(0, r"C:\Program Files (x86)\Steam\steamapps\common\AoE2DE")  # Insert the default value at position 0
    original_path_entry.config(state="readonly")  # Set it back to readonly after inserting

    # Mod Pathway label and entry field
    Label(project_creation_window, text="Mod Pathway").pack(pady=10)
    mod_path_entry = Entry(project_creation_window, state="readonly")
    mod_path_entry.pack()
    default_mod_path = r"C:\Users\Micheal Q\Games\Age of Empires 2 DE\76561198021486964\mods\local"  # Example default value
    mod_path_entry.config(state="normal")  # Enable the entry to insert the value
    mod_path_entry.insert(0, default_mod_path)  # Insert the default value at position 0
    mod_path_entry.config(state="readonly")  # Set it back to readonly after inserting
    mod_path_button = ttk.Button(project_creation_window, text="Browse", command=lambda: selectModPathway(mod_path_entry, project_name_entry.get()))
    mod_path_button.pack()

    # Submit button to start the mod saving process
    submit_button = ttk.Button(project_creation_window, text="Create Project", command=lambda: createNewProject(project_name_entry.get()))
    submit_button.pack(pady=20)

    # Make sure the window is cleaned up properly when closed
    project_creation_window.protocol("WM_DELETE_WINDOW", on_close_project_window)

def on_close_project_window():
    global project_creation_window
    project_creation_window.destroy()
    project_creation_window = None  # Reset to None when the window is closed

# Main application window
root = Tk()
original_title = "Age of Empires II: Definitive Edition Civ Editor"
root.title(original_title)
root.geometry("800x500")

# Create a menu bar
menuBar = Menu(root)
root.config(menu=menuBar)

# Create a "File" menu
fileMenu = Menu(menuBar, tearoff=0)
menuBar.add_cascade(label="File", menu=fileMenu)
fileMenu.add_command(label="New Project", command=new_project_flow, accelerator="Ctrl + N")
fileMenu.add_command(label="Open Project...", command=open_txt_file, accelerator="Ctrl + O")
fileMenu.add_separator()

# Create a separator (line) between the menu bar and the rest of the program
separator = ttk.Separator(root, orient='horizontal')
separator.pack(fill='x', padx=1, pady=0)

# Create a dropdown (ComboBox) in the top left corner
dropdown = ttk.Combobox(root, values=[])
dropdown.place(x=10, y=10)

# Create a grey circle next to the dropdown
canvas = Canvas(root, width=104, height=104, bg="black", highlightthickness=0)
canvas.place(x=150, y=10)
canvas.create_oval(2, 2, 102, 102, fill="grey")

# Run the GUI main loop
root.mainloop()