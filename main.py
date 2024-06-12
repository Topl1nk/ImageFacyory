from PyQt5.QtWidgets import QApplication, QMainWindow, QAction
from PyQt5.QtCore import Qt
from functools import partial
import sys
import os
from components.settings_dialog import SettingsDialog
from components.parameters import ParametersDock
from components.image_viewer import ImageViewerDock
from components.text_editor import TextEditorDock
from components.canvas import CanvasDock


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Image Factory")
        self.setGeometry(100, 100, 800, 600)

        self.frame_states = {'Parameters': True, 'Canvas': True, 'Text Editor': True, 'Image Viewer': True}

        # Menu Bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        window_menu = menubar.addMenu('Window')

        new_factory_action = QAction('New Factory', self)
        new_factory_action.triggered.connect(self.new_factory)
        file_menu.addAction(new_factory_action)

        new_node_action = QAction('New Node', self)
        new_node_action.triggered.connect(self.new_node)
        file_menu.addAction(new_node_action)

        # Добавьте пункт меню "Настройки"
        settings_action = QAction('Settings', self)
        settings_action.triggered.connect(self.open_settings_dialog)
        file_menu.addAction(settings_action)

        # Dock Widgets
        self.frames = {
            'Parameters': ParametersDock(),
            'Image Viewer': ImageViewerDock(),
            'Text Editor': TextEditorDock(),
            'Canvas': CanvasDock(),
        }

        # Add Dock Widgets to specific areas
        self.addDockWidget(Qt.LeftDockWidgetArea, self.frames['Parameters'])
        self.addDockWidget(Qt.RightDockWidgetArea, self.frames['Canvas'])
        self.addDockWidget(Qt.LeftDockWidgetArea, self.frames['Image Viewer'])
        self.addDockWidget(Qt.RightDockWidgetArea, self.frames['Text Editor'])

        # Window Menu Items
        self.window_actions = {}
        for frame_name in self.frame_states.keys():
            action = QAction(frame_name, self)
            action.setCheckable(True)  # Make the menu item "checkable"
            action.setChecked(
                self.frame_states[frame_name])  # Set the initial state of the checkbox based on frame_states
            action.triggered.connect(partial(self.toggle_frame, frame_name))
            window_menu.addAction(action)
            self.window_actions[frame_name] = action

        # Connect visibilityChanged signal to update_menu
        for frame_name, frame in self.frames.items():
            frame.visibilityChanged.connect(self.update_menu)

    def update_menu(self):
        for frame_name, action in self.window_actions.items():
            action.setChecked(self.frames[frame_name].isVisible())

    def showEvent(self, event):
        super().showEvent(event)
        # Update the state of checkboxes based on the visibility of dock widgets
        for frame_name, action in self.window_actions.items():
            action.setChecked(self.frames[frame_name].isVisible())

    def new_factory(self):
        print("New Factory clicked")

    def new_node(self):
        print("New Node clicked")

    def open_settings_dialog(self):
        settings_dialog = SettingsDialog()
        settings_dialog.exec_()

    def toggle_frame(self, frame_name):
        frame = self.frames[frame_name]
        frame.setVisible(not frame.isVisible())
        self.frame_states[frame_name] = frame.isVisible()

        # Update menu
        action = self.window_actions[frame_name]
        action.setChecked(frame.isVisible())


# Получите путь к директории, в которой находится текущий скрипт
script_directory = os.path.dirname(os.path.abspath(__file__))

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Загрузка стиля из файла style.qss с использованием относительного пути
    script_directory = os.path.dirname(os.path.abspath(__file__))
    stylesheet_path = os.path.join(script_directory, 'style.qss')
    with open(stylesheet_path, 'r') as stylesheet_file:
        app.setStyleSheet(stylesheet_file.read())

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())