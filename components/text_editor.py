# image_viewer.py
from PyQt5.QtWidgets import QDockWidget, QTextEdit

class TextEditorDock(QDockWidget):
    def __init__(self):
        super().__init__("Text Editor")
        self.setWidget(QTextEdit("Text Editor"))