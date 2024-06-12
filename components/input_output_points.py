from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsItem
from PyQt5.QtGui import QBrush, QColor, QPen
from PyQt5.QtCore import Qt
from components.connection import Connection

class Point(QGraphicsEllipseItem):
    def __init__(self, parent, name, color):
        super().__init__(-5, -5, 10, 10, parent)
        self.setBrush(QBrush(color))
        self.setPen(QPen(QColor(0, 0, 0)))
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
        self.setAcceptHoverEvents(True)
        self.name = name
        self.connection = None

    def hoverEnterEvent(self, event):
        self.setRect(-7, -7, 14, 14)
        self.setBrush(QBrush(self.brush().color().lighter(150)))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setRect(-5, -5, 10, 10)
        self.setBrush(QBrush(self.brush().color().darker(100)))
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.connection = Connection(self)
            self.scene().addItem(self.connection)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.connection:
            self.connection.set_target_pos(event.scenePos())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.connection:
            target_point = self.scene().itemAt(event.scenePos(), self.scene().views()[0].transform())
            if isinstance(target_point, Point):
                self.connection.set_target_point(target_point)
            else:
                self.scene().removeItem(self.connection)
            self.connection = None
        super().mouseReleaseEvent(event)

class InputPoint(Point):
    def __init__(self, parent, name):
        super().__init__(parent, name, QColor(255, 0, 0))

class OutputPoint(Point):
    def __init__(self, parent, name):
        super().__init__(parent, name, QColor(0, 255, 0))
