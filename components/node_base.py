# node_base.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog

class NodeBase(QWidget):
    def __init__(self):
        super().__init__()
        self.inputs = []
        self.outputs = []

    def get_inputs(self):
        raise NotImplementedError

    def execute(self):
        raise NotImplementedError
