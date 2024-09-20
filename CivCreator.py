import os
import json
import tkinter as tk
from tkinter import Tk, Menu, Label
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter import messagebox
from cryptography.fernet import Fernet

# Generate a key for encryption/decryption. This key should be stored securely.
encryption_key = Fernet.generate_key()
cipher_suite = Fernet(encryption_key)

# Function to open the file explorer and load the selected .a2cp file
def openA2CPFile():
    fileName = askopenfilename(filetypes=[("A2CP files", "*.a2cp")])
    if not fileName:
        return  # No file selected

    if not fileName.endswith(".a2cp"):
        messagebox.showerror("Invalid File", "ERROR: File must have a .a2cp extension.")
        return

    try:
        # Open and read the encrypted content from the file
        with open(fileName, 'rb') as file:
            encrypted_data = file.read()

        # Decrypt the content
        decrypted_data = cipher_suite.decrypt(encrypted_data).decode()

        # Display the decrypted message
        messagebox.showinfo("Decrypted Message", f"Decrypted content: {decrypted_data}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while decrypting the file: {e}")

# Function to create and save a new .a2cp file
def saveAsA2CPFile():
    fileName = asksaveasfilename(defaultextension=".a2cp", filetypes=[("A2CP files", "*.a2cp")])
    if not fileName:
        return  # No file selected

    if not fileName.endswith(".a2cp"):
        messagebox.showerror("Invalid File", "ERROR: File must have a .a2cp extension.")
        return

    # Example: Prepare some text data to be encrypted and saved
    data_to_encrypt = "This is a test message that will be encrypted."

    # Encrypt the data
    encrypted_data = cipher_suite.encrypt(data_to_encrypt.encode())

    try:
        # Save the encrypted data to the file
        with open(fileName, 'wb') as file:
            file.write(encrypted_data)
        messagebox.showinfo("Success", "File saved and encrypted successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

# Create the main application window
root = Tk()
root.title("Age of Empires II: Definitive Edition Civilization Editor")
root.geometry("800x500")  # Set the window size

# Create a menu bar
menuBar = Menu(root)
root.config(menu=menuBar)

# Create a "File" menu
fileMenu = Menu(menuBar, tearoff=0)
menuBar.add_cascade(label="File", menu=fileMenu)
fileMenu.add_command(label="New Project...", command=saveAsA2CPFile)
fileMenu.add_command(label="Open Project...", command=openA2CPFile)

# Create a label to display centered text
label = Label(root, text="Open original civTechTrees.json file or create a new .a2cp file", font=("Arial", 16))
label.pack(expand=True)  # Expands to center the text vertically and horizontally

# Run the GUI main loop
root.mainloop()
