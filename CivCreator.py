import os
import shutil
import tkinter as tk
from tkinter import Tk, Menu, Label, ttk, Canvas, Toplevel, Entry
from tkinter.filedialog import askdirectory, askopenfilename
from tkinter import messagebox
import sys
from cryptography.fernet import Fernet

# Global variables to store the selected AoE2DE folder path and mod save path
selected_folder_path = None
mod_save_path = None

# Generate a key for encryption/decryption (In a real application, store this securely)
encryption_key = Fernet.generate_key()
cipher_suite = Fernet(encryption_key)

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

# Function to save a .a2cp file inside the mod folder
def save_a2cp_file(project_name, original_path, mod_path):
    try:
        a2cp_content = f"{original_path};{mod_path}"
        encrypted_content = cipher_suite.encrypt(a2cp_content.encode())
        
        # Save the .a2cp file inside the project folder with the same name as the project
        a2cp_file_path = os.path.join(mod_save_path, f"{project_name}.a2cp")
        with open(a2cp_file_path, 'wb') as file:
            file.write(encrypted_content)
        
        messagebox.showinfo("Success", f"{project_name}.a2cp file saved successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save .a2cp file: {e}")

# Function to open a .a2cp file and decrypt it
def open_a2cp_file():
    a2cp_file_path = askopenfilename(filetypes=[("A2CP files", "*.a2cp")])
    if not a2cp_file_path:
        return  # User canceled file selection

    try:
        # Read and decrypt the .a2cp file
        with open(a2cp_file_path, 'rb') as file:
            encrypted_data = file.read()
        decrypted_content = cipher_suite.decrypt(encrypted_data).decode()

        # The .a2cp content is in the format: original_path;mod_path
        original_path, mod_path = decrypted_content.split(';')

        # Check if both paths exist
        if not os.path.exists(original_path) or not os.path.exists(mod_path):
            messagebox.showerror("Error", "One or both of the paths no longer exist.")
            sys.exit("Error: Missing paths.")

        # Update the title of the main window with the project name (without .a2cp)
        project_name = os.path.basename(a2cp_file_path).replace(".a2cp", "")
        root.title(f"{original_title} - {project_name}")

        messagebox.showinfo("Success", f"Project '{project_name}' opened successfully!")
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open .a2cp file: {e}")
        sys.exit("Error: Failed to open .a2cp file.")

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

# Function to create the new project with specified folders/files
# Function to create the new project with specified folders/files
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
        progress_window.geometry("400x150")

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

        # Save the .a2cp file
        save_a2cp_file(project_name, selected_folder_path, mod_save_path)

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
original_title = "Age of Empires II: Definitive Edition Civilization Editor"
root.title(original_title)
root.geometry("800x500")

# Create a menu bar
menuBar = Menu(root)
root.config(menu=menuBar)

# Create a "File" menu
fileMenu = Menu(menuBar, tearoff=0)
menuBar.add_cascade(label="File", menu=fileMenu)
fileMenu.add_command(label="New Project", command=new_project_flow, accelerator="Ctrl + N")
fileMenu.add_command(label="Open Project...", command=open_a2cp_file, accelerator="Ctrl + O")
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