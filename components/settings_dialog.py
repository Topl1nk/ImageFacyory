from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QFileDialog, QLineEdit, QHBoxLayout, QSpacerItem, \
    QSizePolicy
import configparser
import os


class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Настройки")

        # Установите размер окна настроек
        self.resize(400, 300)  # Измените размеры на необходимые

        # Добавляем виджеты настроек
        layout = QVBoxLayout()

        # Виджет для выбора пути к папке
        self.folder_path_line_edit = QLineEdit(self)
        self.folder_path_line_edit.setPlaceholderText("Путь к папке со скриптами")
        browse_button = QPushButton("Обзор...", self)
        browse_button.clicked.connect(self.select_folder)

        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.folder_path_line_edit)
        folder_layout.addWidget(browse_button)

        layout.addLayout(folder_layout)
        layout.addWidget(QLabel("Настройки вашего приложения здесь"))

        # Кнопка "Сохранить настройки"
        save_button = QPushButton("Сохранить настройки", self)
        save_button.clicked.connect(self.save_settings)

        # Расположим кнопку в левом нижнем углу
        button_layout = QHBoxLayout()
        button_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        button_layout.addWidget(save_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Загружаем настройки при инициализации
        self.load_settings()

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Выбрать папку")
        if folder_path:
            self.folder_path_line_edit.setText(folder_path)

    def save_settings(self):
        config = configparser.ConfigParser()
        config['Settings'] = {
            'scripts_folder': self.folder_path_line_edit.text()
        }

        with open('user.cfg', 'w') as configfile:
            config.write(configfile)

        self.accept()  # Закрыть диалоговое окно после сохранения

    def load_settings(self):
        config = configparser.ConfigParser()
        if os.path.exists('user.cfg'):
            config.read('user.cfg')
            if 'Settings' in config:
                self.folder_path_line_edit.setText(config['Settings'].get('scripts_folder', ''))


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    settings_dialog = SettingsDialog()
    settings_dialog.show()
    sys.exit(app.exec_())
