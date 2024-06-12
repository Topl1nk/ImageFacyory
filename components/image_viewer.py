# image_viewer.py
from PyQt5.QtWidgets import QDockWidget, QLabel

class ImageViewerDock(QDockWidget):
    def __init__(self):
        super().__init__("Image Viewer")
        self.setWidget(QLabel("Image Viewer"))