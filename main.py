import os
import sys
import random
from pathlib import Path
from PySide6 import QtCore, QtWidgets, QtGui
from widgetgallery import WidgetGallery

def main():
    app = QtWidgets.QApplication()
    gallery = WidgetGallery()
    gallery.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()