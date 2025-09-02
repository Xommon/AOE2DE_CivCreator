#!/usr/bin/env python3
import sys
from PyQt5 import QtCore, QtGui, QtWidgets

class Overlay(QtWidgets.QWidget):
    def __init__(self, image_path, opacity=0.6, x=100, y=100, w=800, h=600, angle=0):
        super().__init__()
        self.image_path = image_path
        self.pixmap = QtGui.QPixmap(image_path)
        self.angle = angle
        if self.pixmap.isNull():
            raise FileNotFoundError(f"Could not load {image_path}")

        # Borderless + always on top
        flags = QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint

        platform = QtWidgets.QApplication.platformName().lower()
        if "wayland" in platform:
            # Wayland: try a 'tool' window type so it can overlap panels
            flags |= QtCore.Qt.Tool
        else:
            # X11: we can bypass WM constraints entirely
            flags |= QtCore.Qt.X11BypassWindowManagerHint

        self.setWindowFlags(flags)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # Resize and move
        self.resize(w, h)
        self.move(x, y)

        # Set opacity
        self.opacity = opacity
        self.setWindowOpacity(self.opacity)

        # For dragging
        self._drag_pos = None

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)

        # Scale the pixmap first
        scaled = self.pixmap.scaled(self.size(), QtCore.Qt.KeepAspectRatio,
                                    QtCore.Qt.SmoothTransformation)

        # Rotate 45 degrees
        transform = QtGui.QTransform().rotate(45)
        rotated = scaled.transformed(transform, QtCore.Qt.SmoothTransformation)

        # Center the rotated image in the window
        x = (self.width() - rotated.width()) // 2
        y = (self.height() - rotated.height()) // 2
        painter.drawPixmap(x, y, rotated)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
        elif event.button() == QtCore.Qt.RightButton:
            QtWidgets.qApp.quit()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            QtWidgets.qApp.quit()
        elif event.key() == QtCore.Qt.Key_BracketLeft:   # [
            self.opacity = max(0.1, self.opacity - 0.1)
            self.setWindowOpacity(self.opacity)
        elif event.key() == QtCore.Qt.Key_BracketRight:  # ]
            self.opacity = min(1.0, self.opacity + 0.1)
            self.setWindowOpacity(self.opacity)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 overlay.py /path/to/image [opacity]")
        sys.exit(1)

    image_path = sys.argv[1]
    opacity = float(sys.argv[2]) if len(sys.argv) > 2 else 0.6

    app = QtWidgets.QApplication(sys.argv)
    overlay = Overlay(image_path, opacity)
    overlay.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
