from PyQt5.QtWidgets import QGraphicsPathItem
from PyQt5.QtGui import QPainterPath, QPen, QColor

class Connection (QGraphicsPathItem):
    def __init__(self, start_point):
        super().__init__()
        self.start_point = start_point
        self.end_point = None
        self.target_pos = start_point.scenePos()
        self.setPen(QPen(QColor(0, 0, 0), 2))

    def set_target_pos(self, pos):
        self.target_pos = pos
        self.update_path()

    def set_target_point(self, end_point):
        self.end_point = end_point
        self.update_path()

    def update_path(self):
        path = QPainterPath()
        start_pos = self.start_point.scenePos()
        end_pos = self.target_pos if self.end_point is None else self.end_point.scenePos()
        path.moveTo(start_pos)
        dx = (end_pos.x() - start_pos.x()) / 2
        path.cubicTo(start_pos.x() + dx, start_pos.y(), end_pos.x() - dx, end_pos.y(), end_pos.x(), end_pos.y())
        self.setPath(path)
