match = re.search(r"Unique Unit:\s*<b>?\s*([\w\s]+)\s*\(", civ.description)
            if match:
                unique_unit = match.group(1).strip()
            else:
                print("Unique Unit not found.")
            for block in unit_blocks:
                if block.name == 'Unique Unit':
                    getattr(MAIN_WINDOW, f"{file_name}_4").setText(unique_unit)
                    getattr(MAIN_WINDOW, f"{file_name}_2").setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/{unique_unit}.png"))
                if block.name == 'Elite Unique Unit':
                    getattr(MAIN_WINDOW, f"{file_name}_4").setText(rf'Elite {unique_unit}')
                    getattr(MAIN_WINDOW, f"{file_name}_2").setPixmap(QtGui.QPixmap(rf"{os.path.dirname(os.path.abspath(__file__))}/Images/TechTree/{unique_unit}.png"))