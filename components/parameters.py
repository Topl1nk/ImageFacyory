# parameters.py
from PyQt5.QtWidgets import QDockWidget, QLabel

class ParametersDock(QDockWidget):
    def __init__(self):
        super().__init__("Parameters")
        self.setWidget(QLabel("Parameters"))