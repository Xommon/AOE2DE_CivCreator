from PyQt5 import QtWidgets, QtCore, QtGui

class CivilisationDropdown(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super(CivilisationDropdown, self).__init__(parent)

        # Track the currently red item
        self.red_item_index = -1  # No item is red initially

        # Install event filter on the QComboBox's internal view
        self.view().viewport().installEventFilter(self)

    def eventFilter(self, source, event):
        # Check if the event is happening on the dropdown view (list of items)
        if source == self.view().viewport() and event.type() == QtCore.QEvent.MouseButtonRelease:
            if event.button() == QtCore.Qt.RightButton:
                index = self.view().indexAt(event.pos()).row()
                if index >= 0:  # Ensure that the index is valid
                    if self.red_item_index == -1:  # No red item yet
                        self.turn_item_red(index)
                    else:
                        # Swap with the currently red item
                        self.swap_items(index, self.red_item_index)
                        # Reset all items to black after swap
                        self.reset_item_colors()

                    return True  # Prevent the dropdown from closing

        return super(CivilisationDropdown, self).eventFilter(source, event)

    def turn_item_red(self, index):
        self.setItemData(index, QtGui.QColor(QtCore.Qt.red), QtCore.Qt.ForegroundRole)
        self.red_item_index = index  # Mark this item as the red one

    def reset_item_colors(self):
        count = self.count()
        for i in range(count):
            self.setItemData(i, QtGui.QColor(QtCore.Qt.black), QtCore.Qt.ForegroundRole)
        self.red_item_index = -1  # No item is red anymore

    def swap_items(self, index1, index2):
        # Get the text of both items
        text1 = self.itemText(index1)
        text2 = self.itemText(index2)

        # Swap the items' text
        self.setItemText(index1, text2)
        self.setItemText(index2, text1)

# Example usage of the custom combo box
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)

    window = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(window)

    combo = CivilisationDropdown()
    combo.addItems(["Britons", "Franks", "Teutons"])  # Add sample items
    combo.insertSeparator(combo.count())
    combo.addItems(["Zapotecs", "Javanese"])

    layout.addWidget(combo)
    window.setLayout(layout)

    window.show()
    sys.exit(app.exec_())