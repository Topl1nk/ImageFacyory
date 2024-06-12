from PyQt5.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QMenu, QAction, QStyle
from PyQt5.QtGui import QPen, QBrush, QColor, QPainter, QCursor
from PyQt5.QtCore import QRectF, QPointF, Qt
import os
import sys
import configparser
import importlib
from .input_output_points import InputPoint, OutputPoint


class CustomItem(QGraphicsItem):
    GRID_SIZE = 10  # Размер ячейки сетки

    def __init__(self, node_class):
        super().__init__()
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        self.start_pos = QPointF()
        self.mouse_start_pos = QPointF()
        self.selected_items_start_pos = {}
        self.node_instance = node_class()
        self.input_points = []
        self.output_points = []
        self.width = 150
        self.height = 100

        self.update_size()
        self.create_input_output_points()

    def create_input_output_points(self):
        self.input_points.clear()
        self.output_points.clear()
        self._create_points(self.node_instance.get_inputs(), self.input_points, QPointF(0, 40))
        self._create_points(self.node_instance.get_outputs(), self.output_points, QPointF(self.width - 10, 40))

    def _create_points(self, slots, points_list, initial_pos):
        slot_y = initial_pos.y()
        for slot in slots:
            point = InputPoint(self, slot) if points_list == self.input_points else OutputPoint(self, slot)
            point.setPos(QPointF(initial_pos.x(), slot_y))
            points_list.append(point)
            slot_y += 20

    def update_size(self):
        painter = QPainter()
        font_metrics = painter.fontMetrics()

        max_input_width = max([font_metrics.width(text) for text in self.node_instance.get_inputs()] or [0])
        max_output_width = max([font_metrics.width(text) for text in self.node_instance.get_outputs()] or [0])
        node_name_width = font_metrics.width(self.node_instance.name)

        self.width = max(max_input_width + max_output_width + 40, node_name_width + 20)
        self.height = max(len(self.node_instance.get_inputs()), len(self.node_instance.get_outputs())) * 20 + 40
        self.update()

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None):
        self._set_painter_brush_and_pen(painter, option)
        painter.drawRect(self.boundingRect())
        self._draw_texts(painter)

    def _set_painter_brush_and_pen(self, painter, option):
        if option.state & QStyle.State_Selected:
            painter.setBrush(QBrush(QColor(100, 100, 250)))
            painter.setPen(QPen(QColor(0, 0, 0), 2))
        else:
            painter.setBrush(QBrush(QColor(200, 200, 200)))
            painter.setPen(QPen(QColor(0, 0, 0), 1))

    def _draw_texts(self, painter):
        painter.drawText(QRectF(0, 0, self.width, 20), Qt.AlignCenter, self.node_instance.name)
        self._draw_slot_texts(painter, self.node_instance.get_inputs(), QPointF(10, 40))
        self._draw_slot_texts(painter, self.node_instance.get_outputs(), QPointF(self.width - 10, 40), align_right=True)

    def _draw_slot_texts(self, painter, slots, initial_pos, align_right=False):
        slot_y = initial_pos.y()
        for slot in slots:
            text_pos = QPointF(initial_pos.x() - painter.boundingRect(QRectF(0, 0, self.width / 2, 20), Qt.AlignLeft, slot).width(), slot_y + 5) if align_right else QPointF(initial_pos.x(), slot_y + 5)
            painter.drawText(text_pos, slot)
            slot_y += 20

    def add_input(self, name):
        self.node_instance.add_input(name)
        self.update_size()
        self.create_input_output_points()
        self.update()

    def add_output(self, name):
        self.node_instance.add_output(name)
        self.update_size()
        self.create_input_output_points()
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._handle_left_button_press(event)
        super().mousePressEvent(event)

    def _handle_left_button_press(self, event):
        if not self.isSelected():
            for item in self.scene().selectedItems():
                item.setSelected(False)
        self.setSelected(True)
        self.start_pos = self.pos()
        self.mouse_start_pos = self.mapToScene(event.pos())
        self.selected_items_start_pos = {item: item.pos() for item in self.scene().selectedItems() if item != self}

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self._handle_left_button_move(event)
        else:
            super().mouseMoveEvent(event)

    def _handle_left_button_move(self, event):
        delta = self.mapToScene(event.pos()) - self.mouse_start_pos
        new_pos = self._get_snapped_position(self.start_pos + delta)
        self.setPos(new_pos)
        for item, start_pos in self.selected_items_start_pos.items():
            item.setPos(self._get_snapped_position(start_pos + (new_pos - self.start_pos)))

    def _get_snapped_position(self, pos):
        return QPointF(round(pos.x() / self.GRID_SIZE) * self.GRID_SIZE, round(pos.y() / self.GRID_SIZE) * self.GRID_SIZE)


class AddNodeMenu:
    def __init__(self, view):
        self.view = view
        self.node_base_class = None
        self.node_classes = self.load_node_classes()

    def load_node_classes(self):
        node_classes = {}
        config = configparser.ConfigParser()
        config.read('user.cfg')
        script_dir = config.get('Settings', 'scripts_folder', fallback='')

        if not script_dir or not os.path.exists(script_dir):
            print(f"Invalid script directory: {script_dir}")
            return node_classes

        print(f"Script directory: {script_dir}")
        sys.path.append(script_dir)

        self._load_node_base_class()
        self._load_node_classes_from_scripts(node_classes, script_dir)

        print(f"Total loaded node classes: {len(node_classes)}")
        return node_classes

    def _load_node_base_class(self):
        try:
            node_base_module = importlib.import_module('node_base')
            self.node_base_class = node_base_module.NodeBase
            print(f"Loaded NodeBase from {node_base_module.__file__}")
        except ModuleNotFoundError:
            print("Base node class 'NodeBase' not found in script directory.")

    def _load_node_classes_from_scripts(self, node_classes, script_dir):
        for filename in os.listdir(script_dir):
            if filename.endswith(".py") and filename != 'node_base.py':
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(module_name)
                    self._check_and_add_node_classes(module, node_classes)
                except ModuleNotFoundError as e:
                    print(f"Failed to import module {module_name}: {e}")

    def _check_and_add_node_classes(self, module, node_classes):
        for name, obj in module.__dict__.items():
            print(f"Checking {name} in {module.__name__}")
            if isinstance(obj, type) and issubclass(obj, self.node_base_class) and obj is not self.node_base_class:
                node_classes[name] = obj
                print(f"Loaded node class {name} from {module.__file__}")

    def show_context_menu(self, position):
        context_menu = QMenu(self.view)
        for node_class in self.node_classes.values():
            action = QAction(node_class.__name__, self.view)
            action.triggered.connect(lambda checked, nc=node_class: self.add_node(nc))
            context_menu.addAction(action)

        global_position = self.view.mapToGlobal(position)
        print(f"Global position for context menu: {global_position}")
        context_menu.exec_(global_position)
        print("Context menu displayed")

    def add_node(self, node_class):
        item = CustomItem(node_class)
        item.setPos(self.view.mapToScene(self.view.mapFromGlobal(QCursor.pos())))
        self.view.scene().addItem(item)
