from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import logging
from components.custom_item import AddNodeMenu, PointBase, InputPoint, OutputPoint, Connection

logging.basicConfig(level=logging.DEBUG)

class CanvasView(QGraphicsView):
    MIN_SCALE = 0.1  # Минимальный коэффициент масштабирования
    MAX_SCALE = 10.0  # Максимальный коэффициент масштабирования

    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.middle_mouse_pressed = False
        self.last_pan_point = QPointF()
        self.current_connection = None
        self.add_node_menu = AddNodeMenu(self)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def wheelEvent(self, event):
        angle = event.angleDelta().y()
        factor = 1.25 if angle > 0 else 0.8
        new_scale = self.transform().m11() * factor
        if self.MIN_SCALE <= new_scale <= self.MAX_SCALE:
            self.scale(factor, factor)

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, (InputPoint, OutputPoint)):
            self.current_connection = Connection(item)
            self.scene().addItem(self.current_connection)
            self.setCursor(QCursor(Qt.CrossCursor))
            logging.debug(f"Started dragging from {item.name}")
        elif event.button() == Qt.MiddleButton:
            self.middle_mouse_pressed = True
            self.last_pan_point = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        elif event.button() == Qt.RightButton:
            self.add_node_menu.show_context_menu(event.pos())
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.middle_mouse_pressed:
            delta = self.mapToScene(event.pos()) - self.mapToScene(self.last_pan_point)
            scale_factor = self.transform().m11()
            self.last_pan_point = event.pos()
            self.horizontalScrollBar().setValue(int(self.horizontalScrollBar().value() - delta.x() * scale_factor))
            self.verticalScrollBar().setValue(int(self.verticalScrollBar().value() - delta.y() * scale_factor))
            event.accept()
        elif self.current_connection:
            self.current_connection.set_target_pos(self.mapToScene(event.pos()))
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.current_connection:
            scene_pos = self.mapToScene(event.pos())
            target_item = self.scene().itemAt(scene_pos, self.transform())
            logging.debug(f"Mouse released at {event.pos()}, target item: {target_item}")
            if isinstance(target_item, (InputPoint, OutputPoint)) and target_item != self.current_connection.start_point:
                self.current_connection.set_target_point(target_item)
                logging.debug(f"Connected {self.current_connection.start_point.name} to {target_item.name}")
            else:
                self.scene().removeItem(self.current_connection)
                logging.debug(f"Connection from {self.current_connection.start_point.name} was canceled")
            self.current_connection = None
            self.setCursor(QCursor(Qt.ArrowCursor))
        elif event.button() == Qt.MiddleButton:
            self.middle_mouse_pressed = False
            self.setCursor(Qt.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)

    def drawBackground(self, painter, rect):
        left = int(rect.left())
        right = int(rect.right())
        top = int(rect.top())
        bottom = int(rect.bottom())
        first_left = left - (left % 100)
        first_top = top - (top % 100)
        lines = []
        x = first_left
        while x < right:
            lines.append(QLineF(x, top, x, bottom))
            x += 100
        y = first_top
        while y < bottom:
            lines.append(QLineF(left, y, right, y))
            y += 100
        painter.setPen(QPen(Qt.gray, 1))
        painter.drawLines(lines)
        small_lines = []
        x = first_left
        while x < right:
            for i in range(1, 10):
                small_x = x + i * 10
                small_lines.append(QLineF(small_x, top, small_x, bottom))
            x += 100
        y = first_top
        while y < bottom:
            for i in range(1, 10):
                small_y = y + i * 10
                small_lines.append(QLineF(left, small_y, right, small_y))
            y += 100
        painter.setPen(QPen(Qt.lightGray, 0.1))
        painter.drawLines(small_lines)

class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.label = QLabel("Custom Title Bar")  # Добавление QLabel
        self.layout.addWidget(self.label)

        # Создание кнопки меню и добавление её в layout
        self.menu_button = QPushButton("☰", self)
        self.menu_button.setFixedSize(30, 30)  # Установка фиксированного размера
        self.menu_button.setStyleSheet(
            "QPushButton {border: none; background-color: white; margin: 0px; padding: 0px;}")
        self.layout.addWidget(self.menu_button)

        # Создание меню и добавление в него пары действий для демонстрации
        self.menu = QMenu(self)
        self.menu.addAction("Action 1")
        self.menu.addAction("Action 2")

        # Подключение сигнала нажатия кнопки к функции открытия меню
        self.menu_button.clicked.connect(self.show_menu)

    def show_menu(self):
        # Открытие меню под кнопкой
        self.menu.exec_(self.menu_button.mapToGlobal(QPoint(0, self.menu_button.height())))

    def sizeHint(self) -> QSize:
        return QSize(100, 30)  # Установка предпочитаемого размера


class CanvasDock(QDockWidget):
    def __init__(self):
        super().__init__("Canvas")
        self.setTitleBarWidget(CustomTitleBar(self))  # Установить кастомный заголовок
        self.scene = QGraphicsScene(self)
        self.view = CanvasView(self.scene)
        self.setWidget(self.view)
        self.scene.setSceneRect(-1e6, -1e6, 2e6, 2e6)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    main_window = QMainWindow()
    dock = CanvasDock()
    main_window.addDockWidget(Qt.RightDockWidgetArea, dock)
    main_window.setCentralWidget(QWidget())  # Установка пустого центрального виджета
    main_window.show()
    sys.exit(app.exec_())
