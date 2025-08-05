"""
Graphics items for node editor.
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any
from PIL import Image
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QPropertyAnimation, QEasingCurve, QObject
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QFontMetrics, QPainterPath, QLinearGradient,
    QMouseEvent, QHoverEvent, QDragEnterEvent, QDropEvent, QRadialGradient
)
from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem, QGraphicsEllipseItem,
    QGraphicsPathItem, QGraphicsDropShadowEffect, QStyleOptionGraphicsItem,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QSlider, QGraphicsProxyWidget, QStyle
)

from ..core.types import NodeID, PinID, PinType, Position
from ..core.node import Node, Pin


class NodeGraphicsItem(QGraphicsRectItem):
    """
    КАРДИНАЛЬНО УЛУЧШЕННАЯ нода с современным дизайном в стиле топовых редакторов.
    """
    
    def __init__(self, node: Node, editor_view):
        super().__init__()
        self.node = node
        self.editor_view = editor_view
        self.node_id: Optional[NodeID] = node.id
        
        # 🎨 СОВРЕМЕННАЯ ЦВЕТОВАЯ ПАЛИТРА (GitHub Copilot / JetBrains style)
        self.colors = {
            'background': QColor(42, 45, 51),       # Темно-серый основа
            'background_selected': QColor(52, 55, 61),  # Светлее при выделении
            'border': QColor(78, 84, 92),           # Нейтральная граница
            'border_selected': QColor(0, 122, 255), # Синий акцент
            'title_bg': QColor(32, 35, 41),         # Темнее для заголовка
            'title_bg_selected': QColor(0, 102, 204), # Синий заголовок при выделении
            'text': QColor(248, 248, 242),          # Почти белый текст
            'text_secondary': QColor(166, 176, 187), # Серый для второстепенного
            'shadow': QColor(0, 0, 0, 80),          # Более глубокая тень
            'hover_overlay': QColor(255, 255, 255, 15), # Тонкий hover эффект
        }
        
        # 📐 ТОЧНЫЕ РАЗМЕРЫ И ОТСТУПЫ
        self.metrics = {
            'corner_radius': 6,        # Современные скругления
            'title_height': 32,        # Оптимальная высота заголовка
            'padding': 12,             # Внутренние отступы
            'pin_size': 7,             # Размер пинов
            'pin_spacing': 22,         # Расстояние между пинами
            'min_width': 160,          # Минимальная ширина
            'border_width': 1.2,       # Толщина границы
            'selected_border_width': 2, # Толщина границы при выделении
        }
        
        # 🎯 СОСТОЯНИЯ
        self.is_hovered = False
        self.animation_progress = 0.0
        
        # 🔧 НАСТРОЙКИ ЭЛЕМЕНТА
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(1)
        
        # ✨ СОВРЕМЕННАЯ ТЕНЬ
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setColor(self.colors['shadow'])
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        # 📊 ВЫЧИСЛЯЕМ РАЗМЕРЫ
        self.calculate_optimal_layout()
        
        # 🔌 СОЗДАЕМ ПИНЫ
        self.input_pins: List[PinGraphicsItem] = []
        self.output_pins: List[PinGraphicsItem] = []
        self.create_modern_pins()
        
        # 🎨 ФИНАЛЬНАЯ НАСТРОЙКА
        self.update_visual_state()
        
    def calculate_optimal_layout(self) -> None:
        """ТОЧНЫЙ расчет размеров с современными пропорциями."""
        # 📝 РАЗМЕРЫ ТЕКСТА
        title_font = QFont("Segoe UI", 10, QFont.Weight.DemiBold)
        title_metrics = QFontMetrics(title_font)
        title_width = title_metrics.horizontalAdvance(self.node.name) + (self.metrics['padding'] * 2)
        
        pin_font = QFont("Segoe UI", 8)
        pin_metrics = QFontMetrics(pin_font)
        
        # 📏 РАЗМЕРЫ ПИНОВ (считаем только NON-EXEC пины для высоты)
        max_input_width = 0
        max_output_width = 0
        regular_input_count = 0
        regular_output_count = 0
        
        from ..core.types import PinType
        
        for pin in self.node.input_pins.values():
            if pin.info.pin_type != PinType.EXEC:  # Исключаем exec пины из расчета
                width = pin_metrics.horizontalAdvance(pin.info.name)
                max_input_width = max(max_input_width, width)
                regular_input_count += 1
            
        for pin in self.node.output_pins.values():
            if pin.info.pin_type != PinType.EXEC:  # Исключаем exec пины из расчета
                width = pin_metrics.horizontalAdvance(pin.info.name)
                max_output_width = max(max_output_width, width)
                regular_output_count += 1
        
        # 🎯 ФИНАЛЬНЫЕ РАЗМЕРЫ
        content_width = max_input_width + max_output_width + (self.metrics['pin_size'] * 2) + (self.metrics['padding'] * 3)
        
        self.width = max(title_width, content_width, self.metrics['min_width'])
        
        # Считаем высоту только по обычным пинам (exec в шапке)
        max_regular_pins = max(regular_input_count, regular_output_count, 1)
        content_height = max_regular_pins * self.metrics['pin_spacing'] + self.metrics['padding']
        
        # 🖼️ ДОПОЛНИТЕЛЬНОЕ МЕСТО ДЛЯ ПРЕВЬЮ ИЗОБРАЖЕНИЯ
        preview_height = 0
        if self._is_preview_node():
            preview_height = 140  # Увеличенная высота для превью
            self.width = max(self.width, 220)  # Увеличенная ширина для превью
            # Добавляем место для кнопки обновления
            preview_height += 25
        
        self.height = self.metrics['title_height'] + content_height + preview_height + self.metrics['padding']
        
        # 🖼️ УСТАНАВЛИВАЕМ ПРЯМОУГОЛЬНИК
        self.setRect(0, 0, self.width, self.height)
    
    def _is_preview_node(self) -> bool:
        """Проверяет, является ли эта нода предварительным просмотром изображения."""
        return self.node.__class__.__name__ == "ImagePreviewNode"
    
    def _has_preview_image(self) -> bool:
        """Проверяет, есть ли у ноды изображение для превью."""
        if not self._is_preview_node():
            return False
        return hasattr(self.node, 'has_preview_image') and self.node.has_preview_image()
    
    def update_preview(self) -> None:
        """Обновляет превью изображения (вызывается при изменении изображения)."""
        if self._is_preview_node():
            # Пересчитываем размеры ноды
            self.calculate_optimal_layout()
            # Обновляем отображение
            self.update()
        
    def create_modern_pins(self) -> None:
        """Создание современных пинов с правильным позиционированием."""
        # 🧹 ОЧИСТКА
        for pin in self.input_pins + self.output_pins:
            if pin.scene():
                pin.scene().removeItem(pin)
        self.input_pins.clear()
        self.output_pins.clear()
        
        # 📍 СТАРТОВЫЕ ПОЗИЦИИ
        input_y = self.metrics['title_height'] + self.metrics['padding']
        output_y = self.metrics['title_height'] + self.metrics['padding']
        
        # 🎯 СНАЧАЛА СОЗДАЕМ EXEC ПИНЫ В ШАПКЕ
        exec_input_pins = []
        exec_output_pins = []
        regular_input_pins = []
        regular_output_pins = []
        
        # Разделяем пины на exec и обычные
        from ..core.types import PinType
        
        for pin in self.node.input_pins.values():
            if pin.info.pin_type == PinType.EXEC:
                exec_input_pins.append(pin)
            else:
                regular_input_pins.append(pin)
                
        for pin in self.node.output_pins.values():
            if pin.info.pin_type == PinType.EXEC:
                exec_output_pins.append(pin)
            else:
                regular_output_pins.append(pin)
        
        # 🔥 EXEC ПИНЫ В ШАПКЕ (input exec слева, output exec справа)
        exec_y = self.metrics['title_height'] / 2  # В центре шапки
        
        for pin in exec_input_pins:
            pin_item = ModernPinGraphicsItem(pin, self, False)
            pin_item.setPos(0, exec_y)  # НА САМОМ КРАЮ слева - равноправие!
            pin_item.setParentItem(self)
            # Не создаем лейбл для exec пинов в шапке
            self.input_pins.append(pin_item)
            
        for pin in exec_output_pins:
            pin_item = ModernPinGraphicsItem(pin, self, True)
            pin_item.setPos(self.width, exec_y)  # НА САМОМ КРАЮ справа - равноправие!
            pin_item.setParentItem(self)
            # Не создаем лейбл для exec пинов в шапке
            self.output_pins.append(pin_item)
        
        # 🔌 ОБЫЧНЫЕ ВХОДНЫЕ ПИНЫ (слева, под шапкой)
        for pin in regular_input_pins:
            pin_item = ModernPinGraphicsItem(pin, self, False)
            pin_item.setPos(0, input_y)
            pin_item.setParentItem(self)
            pin_item.create_modern_label()
            self.input_pins.append(pin_item)
            input_y += self.metrics['pin_spacing']
            
        # 🔌 ОБЫЧНЫЕ ВЫХОДНЫЕ ПИНЫ (справа, под шапкой)
        for pin in regular_output_pins:
            pin_item = ModernPinGraphicsItem(pin, self, True)
            pin_item.setPos(self.width, output_y)
            pin_item.setParentItem(self)
            pin_item.create_modern_label()
            self.output_pins.append(pin_item)
            output_y += self.metrics['pin_spacing']
            
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None) -> None:
        """СОВРЕМЕННАЯ отрисовка с профессиональным качеством."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # 🚫 ОТКЛЮЧАЕМ стандартное выделение Qt
        option.state &= ~QStyle.StateFlag.State_Selected
        
        rect = self.rect()
        radius = self.metrics['corner_radius']
        
        # 🎨 ОСНОВНОЙ ФОН
        main_path = QPainterPath()
        main_path.addRoundedRect(rect, radius, radius)
        
        bg_color = self.colors['background_selected'] if self.isSelected() else self.colors['background']
        if self.is_hovered and not self.isSelected():
            # 🌟 HOVER эффект
            bg_color = bg_color.lighter(110)
        
        # 📈 ГРАДИЕНТ ФОНА
        bg_gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        bg_gradient.setColorAt(0, bg_color.lighter(105))
        bg_gradient.setColorAt(0.1, bg_color)
        bg_gradient.setColorAt(0.9, bg_color)
        bg_gradient.setColorAt(1, bg_color.darker(105))
        
        painter.fillPath(main_path, QBrush(bg_gradient))
        
        # 🎯 ЗАГОЛОВОК с цветами по категориям
        title_rect = QRectF(rect.x(), rect.y(), rect.width(), self.metrics['title_height'])
        title_path = QPainterPath()
        title_path.addRoundedRect(title_rect, radius, radius)
        # Обрезаем нижние углы
        title_path.addRect(QRectF(rect.x(), rect.y() + radius, rect.width(), self.metrics['title_height'] - radius))
        
        # Получаем цвета по категории
        title_color_light, title_color_dark = self.get_category_colors()
        
        # Градиент заголовка с цветами категории
        title_gradient = QLinearGradient(title_rect.topLeft(), title_rect.bottomLeft())
        if self.isSelected():
            # При выделении делаем ярче
            title_gradient.setColorAt(0, title_color_light.lighter(130))
            title_gradient.setColorAt(1, title_color_dark.lighter(110))
        else:
            title_gradient.setColorAt(0, title_color_light.lighter(110))
            title_gradient.setColorAt(1, title_color_dark)
        
        painter.fillPath(title_path, QBrush(title_gradient))
        
        # 📝 ТЕКСТ ЗАГОЛОВКА
        painter.setPen(QPen(self.colors['text'], 1))
        title_font = QFont("Segoe UI", 10, QFont.Weight.DemiBold)
        painter.setFont(title_font)
        
        text_rect = QRectF(
            rect.x() + self.metrics['padding'], 
            rect.y() + 4, 
            rect.width() - (self.metrics['padding'] * 2), 
            self.metrics['title_height'] - 8
        )
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.node.name)
        
        # 🔲 ГРАНИЦА
        border_color = self.colors['border_selected'] if self.isSelected() else self.colors['border']
        border_width = self.metrics['selected_border_width'] if self.isSelected() else self.metrics['border_width']
        
        painter.setPen(QPen(border_color, border_width))
        painter.drawPath(main_path)
        
        # ✨ ДОПОЛНИТЕЛЬНЫЕ ЭФФЕКТЫ
        if self.isSelected():
            # 🌟 ВНУТРЕННИЙ GLOW
            inner_rect = rect.adjusted(1.5, 1.5, -1.5, -1.5)
            inner_path = QPainterPath()
            inner_path.addRoundedRect(inner_rect, radius - 1, radius - 1)
            
            glow_gradient = QLinearGradient(inner_rect.topLeft(), inner_rect.bottomLeft())
            glow_color = self.colors['border_selected']
            glow_gradient.setColorAt(0, QColor(glow_color.red(), glow_color.green(), glow_color.blue(), 30))
            glow_gradient.setColorAt(0.5, QColor(0, 0, 0, 0))
            glow_gradient.setColorAt(1, QColor(0, 0, 0, 0))
            
            painter.fillPath(inner_path, QBrush(glow_gradient))
            
        # 📏 РАЗДЕЛИТЕЛЬНАЯ ЛИНИЯ
        separator_y = rect.y() + self.metrics['title_height']
        separator_color = self.colors['border'].lighter(140)
        painter.setPen(QPen(separator_color, 0.8))
        painter.drawLine(
            QPointF(rect.x() + 1, separator_y),
            QPointF(rect.x() + rect.width() - 1, separator_y)
        )
        
        # 🖼️ ОТРИСОВКА ПРЕВЬЮ ИЗОБРАЖЕНИЯ (всегда для Preview Node)
        if self._is_preview_node():
            self._paint_image_preview(painter, rect)
    
    def _paint_image_preview(self, painter: QPainter, rect: QRectF) -> None:
        """Отрисовка превью изображения внутри ноды."""
        # Всегда рассчитываем область для превью (под пинами)
        pins_area_height = len([p for p in self.node.input_pins.values() if p.info.pin_type.name != 'EXEC']) * self.metrics['pin_spacing'] + self.metrics['padding']
        preview_y = rect.y() + self.metrics['title_height'] + pins_area_height + 8
        preview_height = 130  # Увеличенная высота для превью
        preview_width = rect.width() - (self.metrics['padding'] * 2)
        
        preview_rect = QRectF(
            rect.x() + self.metrics['padding'],
            preview_y,
            preview_width,
            preview_height
        )
        
        # Получаем изображение для превью
        preview_image = self.node.get_preview_image()
        
        try:
            # 🖼️ РАМКА ДЛЯ ПРЕВЬЮ (всегда отображается)
            preview_bg_color = QColor(25, 27, 30)  # Темнее основного фона
            preview_border_color = self.colors['border'].lighter(120)
            
            # Фон превью
            painter.fillRect(preview_rect, QBrush(preview_bg_color))
            
            # Рамка превью
            painter.setPen(QPen(preview_border_color, 1))
            painter.drawRect(preview_rect)
            
            if not preview_image:
                # Показываем заглушку когда нет изображения
                painter.setPen(QPen(QColor(150, 150, 150), 1))
                painter.drawText(preview_rect, Qt.AlignmentFlag.AlignCenter, "No Image\nClick refresh after execution")
                
                # Кнопка обновления (всегда)
                self._paint_refresh_button(painter, preview_rect)
                return
            
            from PySide6.QtGui import QPixmap
            from PIL.ImageQt import ImageQt
            
            # 🎨 КОНВЕРТИРУЕМ И МАСШТАБИРУЕМ ИЗОБРАЖЕНИЕ
            # Создаем копию изображения для масштабирования
            img_copy = preview_image.copy()
            
            # Вычисляем размеры с сохранением пропорций
            content_rect = preview_rect.adjusted(4, 4, -4, -4)  # Отступы внутри рамки
            img_width, img_height = img_copy.size
            scale_x = content_rect.width() / img_width
            scale_y = content_rect.height() / img_height
            scale = min(scale_x, scale_y)
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # Масштабируем изображение
            img_copy = img_copy.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Конвертируем в QPixmap
            qt_image = ImageQt(img_copy)
            pixmap = QPixmap.fromImage(qt_image)
            
            # Центрируем изображение в области превью
            image_x = content_rect.x() + (content_rect.width() - new_width) / 2
            image_y = content_rect.y() + (content_rect.height() - new_height) / 2
            
            # Рисуем изображение
            painter.drawPixmap(int(image_x), int(image_y), pixmap)
            
            # 📝 ИНФОРМАЦИЯ ОБ ИЗОБРАЖЕНИИ
            info_text = f"{img_width}×{img_height}"
            info_font = QFont("Segoe UI", 7)
            painter.setFont(info_font)
            painter.setPen(QPen(self.colors['text_secondary'], 1))
            
            info_rect = QRectF(
                preview_rect.x() + 4,
                preview_rect.bottom() - 15,
                preview_rect.width() - 80,  # Оставляем место для кнопки
                12
            )
            painter.drawText(info_rect, Qt.AlignmentFlag.AlignLeft, info_text)
            
            # 🔄 КНОПКА ОБНОВЛЕНИЯ
            self._paint_refresh_button(painter, preview_rect)
            
        except Exception as e:
            # В случае ошибки рисуем заглушку
            painter.fillRect(preview_rect, QBrush(QColor(50, 50, 50)))
            painter.setPen(QPen(QColor(150, 150, 150), 1))
            painter.drawText(preview_rect, Qt.AlignmentFlag.AlignCenter, "Preview Error")
    
    def _paint_refresh_button(self, painter: QPainter, preview_rect: QRectF) -> None:
        """Отрисовка кнопки обновления превью."""
        # 🔄 РАЗМЕРЫ И ПОЗИЦИЯ КНОПКИ
        button_width = 70
        button_height = 18
        button_x = preview_rect.right() - button_width - 4
        button_y = preview_rect.bottom() - button_height - 2
        
        self.refresh_button_rect = QRectF(button_x, button_y, button_width, button_height)
        
        # 🎨 ЦВЕТА КНОПКИ
        button_bg = QColor(0, 122, 255) if self.is_refresh_button_hovered() else QColor(70, 130, 180)
        button_text_color = QColor(255, 255, 255)
        button_border = QColor(0, 100, 200)
        
        # 🖼️ ФОНОВЫЙ ПРЯМОУГОЛЬНИК
        button_path = QPainterPath()
        button_path.addRoundedRect(self.refresh_button_rect, 3, 3)
        
        # Градиент фона кнопки
        button_gradient = QLinearGradient(self.refresh_button_rect.topLeft(), self.refresh_button_rect.bottomLeft())
        button_gradient.setColorAt(0, button_bg.lighter(110))
        button_gradient.setColorAt(1, button_bg.darker(110))
        
        painter.fillPath(button_path, QBrush(button_gradient))
        
        # Рамка кнопки
        painter.setPen(QPen(button_border, 1))
        painter.drawPath(button_path)
        
        # 📝 ТЕКСТ КНОПКИ
        painter.setPen(QPen(button_text_color, 1))
        button_font = QFont("Segoe UI", 7, QFont.Weight.DemiBold)
        painter.setFont(button_font)
        painter.drawText(self.refresh_button_rect, Qt.AlignmentFlag.AlignCenter, "🔄 Refresh")
    
    def is_refresh_button_hovered(self) -> bool:
        """Проверка, наведена ли мышь на кнопку обновления."""
        return hasattr(self, '_refresh_button_hovered') and self._refresh_button_hovered
    
    def get_refresh_button_rect(self) -> QRectF:
        """Получение области кнопки обновления для обработки кликов."""
        return getattr(self, 'refresh_button_rect', QRectF())
    
    def _check_refresh_button_hover(self, pos: QPointF) -> None:
        """Проверка, находится ли мышь над кнопкой обновления."""
        button_rect = self.get_refresh_button_rect()
        was_hovered = self.is_refresh_button_hovered()
        self._refresh_button_hovered = button_rect.contains(pos)
        
        # Обновляем только если состояние изменилось
        if was_hovered != self._refresh_button_hovered:
            self.update()
    
    def _is_click_on_refresh_button(self, pos: QPointF) -> bool:
        """Проверка, был ли клик по кнопке обновления."""
        button_rect = self.get_refresh_button_rect()
        return button_rect.contains(pos)
    
    def _handle_refresh_button_click(self) -> None:
        """Обработка клика по кнопке обновления."""
        from loguru import logger
        import asyncio
        import threading
        
        logger.info("🔄 Refresh button clicked - refreshing preview")
        
        # Принудительно обновляем превью ноды
        if hasattr(self.node, 'get_preview_image'):
            try:
                # Пытаемся перевыполнить ноду если есть входящее изображение
                if self.node.input_pins and 'image' in self.node.input_pins:
                    input_pin = self.node.input_pins['image']
                    if input_pin.is_connected() and input_pin._cached_value is not None:
                        # Есть подключенное изображение, переобрабатываем его
                        def refresh_async():
                            try:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                
                                # Создаем минимальный контекст
                                from ..core.types import ExecutionContext
                                from asyncio import Event
                                context = ExecutionContext(
                                    cancelled=Event(),
                                    progress_callback=None
                                )
                                
                                # Перевыполняем ноду
                                loop.run_until_complete(self.node.process_image(context))
                                
                                # Обновляем UI в главном потоке
                                from PySide6.QtCore import QTimer
                                QTimer.singleShot(0, lambda: self._update_preview_ui())
                                
                                loop.close()
                            except Exception as e:
                                logger.error(f"Failed to refresh preview: {e}")
                        
                        # Запускаем в отдельном потоке
                        thread = threading.Thread(target=refresh_async, daemon=True)
                        thread.start()
                    else:
                        logger.warning("No connected image to refresh")
                        self._show_no_input_message()
                else:
                    logger.warning("No image input pin found")
                    
            except Exception as e:
                logger.error(f"Error during preview refresh: {e}")
                
            # Пересчитываем размеры и обновляем отображение
            self.calculate_optimal_layout()
            self.update()
            
            # Уведомляем пользователя о обновлении (визуальная обратная связь)
            self._show_refresh_feedback()
    
    def _update_preview_ui(self) -> None:
        """Обновляет UI превью в главном потоке."""
        self.calculate_optimal_layout()
        self.update()
        from loguru import logger
        logger.info("Preview UI updated successfully")
    
    def _show_no_input_message(self) -> None:
        """Показывает сообщение о отсутствии входных данных."""
        from loguru import logger
        logger.warning("No input image connected - connect an image first")
    
    def _show_refresh_feedback(self) -> None:
        """Показываем визуальную обратную связь об обновлении."""
        # Можно добавить анимацию или эффект
        # Пока просто логируем
        from loguru import logger
        logger.debug("Preview refreshed successfully")
        
    def hoverEnterEvent(self, event: QHoverEvent) -> None:
        """Улучшенный hover эффект."""
        self.is_hovered = True
        # Проверяем hover над кнопкой обновления
        if self._is_preview_node():
            self._check_refresh_button_hover(event.pos())
        self.update()
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event: QHoverEvent) -> None:
        """Убираем hover эффект."""
        self.is_hovered = False
        self._refresh_button_hovered = False
        self.update()
        super().hoverLeaveEvent(event)
    
    def hoverMoveEvent(self, event: QHoverEvent) -> None:
        """Обработка движения мыши."""
        if self._is_preview_node():
            self._check_refresh_button_hover(event.pos())
            self.update()
        super().hoverMoveEvent(event)
        
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Обработка клика с визуальным откликом."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Проверяем клик по кнопке обновления
            if self._is_preview_node() and self._is_click_on_refresh_button(event.pos()):
                self._handle_refresh_button_click()
                event.accept()
                return
            self.setSelected(True)
        super().mousePressEvent(event)
        
    def update_visual_state(self) -> None:
        """Обновление визуального состояния."""
        self.update()
        
    def get_node_icon(self) -> str:
        """Получение иконки для типа ноды."""
        icon_map = {
            'SolidColorNode': '🎨',
            'BlurNode': '🌀', 
            'BrightnessContrastNode': '☀️',
            'SharpenNode': '⚡',
            'LoadImageNode': '📁',
            'SaveImageNode': '💾',
        }
        return icon_map.get(self.node.__class__.__name__, '⚙️')
        
    def get_category_colors(self) -> tuple:
        """Получение цветов заголовка по категории ноды."""
        # Определяем категорию по базовому классу
        node_class_name = self.node.__class__.__name__
        base_classes = [cls.__name__ for cls in self.node.__class__.__mro__]
        
        # Цветовая схема по категориям
        if 'FilterNode' in base_classes:
            # 🔵 Синие тона для фильтров
            return QColor(45, 85, 135), QColor(35, 65, 105)
        elif 'ColorNode' in base_classes:
            # 🟡 Желто-оранжевые тона для цветовых нод
            return QColor(165, 110, 30), QColor(135, 85, 20)
        elif 'GeneratorNode' in base_classes:
            # 🟢 Зеленые тона для генераторов
            return QColor(65, 125, 65), QColor(45, 95, 45)
        elif 'IONode' in base_classes:
            # 🟣 Фиолетовые тона для ввода/вывода
            return QColor(125, 65, 125), QColor(95, 45, 95)
        elif 'TransformNode' in base_classes:
            # 🔴 Красноватые тона для трансформаций
            return QColor(135, 75, 75), QColor(105, 55, 55)
        else:
            # 🔘 Нейтральные тона для остальных
            return self.colors['title_bg'], self.colors['title_bg']
    
    def get_pin_at_position(self, pos: QPointF) -> Optional[PinGraphicsItem]:
        """Получение пина в указанной позиции."""
        for pin in self.input_pins + self.output_pins:
            if pin.contains(pin.mapFromParent(pos)):
                return pin
        return None
        
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        """Обработка изменений элемента."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            self.update_visual_state()
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Обновляем все соединения при перемещении ноды
            self.update_connections()
        return super().itemChange(change, value)
        
    def update_connections(self) -> None:
        """Обновление всех соединений связанных с этой нодой."""
        if hasattr(self.editor_view, 'scene'):
            # Ищем все соединения на сцене и обновляем те, что связаны с этой нодой
            for item in self.editor_view.scene.items():
                if hasattr(item, 'start_pin') and hasattr(item, 'end_pin'):
                    # Проверяем, связано ли соединение с этой нодой
                    start_node_id = getattr(item.start_pin, 'node_id', None) if item.start_pin else None
                    end_node_id = getattr(item.end_pin, 'node_id', None) if item.end_pin else None
                    
                    if start_node_id == self.node_id or end_node_id == self.node_id:
                        # Обновляем путь соединения
                        if hasattr(item, 'update_path'):
                            item.update_path()
        
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Обработка перемещения мыши."""
        super().mouseMoveEvent(event)
        # Можно добавить логику для уведомления о перемещении 


class ModernPinGraphicsItem(QGraphicsItem):
    """
    🔌 СОВРЕМЕННЫЙ ПИН с профессиональным дизайном и анимациями.
    """
    
    def __init__(self, pin: Pin, parent_node: NodeGraphicsItem, is_output: bool):
        super().__init__()
        self.pin = pin
        self.parent_node = parent_node
        self.is_output = is_output
        self.pin_type = pin.info.pin_type
        self.node_id = parent_node.node.id
        self.pin_id = pin.info.id
        
        # 📐 РАЗМЕРЫ И НАСТРОЙКИ
        from ..core.types import PinType
        if self.pin_type == PinType.EXEC:
            # 🔺 EXEC пины - треугольные стрелочки (БОЛЬШЕ!)
            self.radius = 6
            self.hover_radius = 7
            self.triangle_size = 12  # Увеличиваем с 8 до 12
        else:
            # ⭕ Обычные пины - круглые
            self.radius = 4.5
            self.hover_radius = 6
            
        self.active_radius = 5.5
        self.current_radius = self.radius
        
        # 🎯 СОСТОЯНИЯ
        self.is_hovered = False
        self.is_connected = False
        
        # 🔧 НАСТРОЙКИ ЭЛЕМЕНТА
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setAcceptHoverEvents(True)
        self.setZValue(10)  # Поверх всего остального
        
        # 🎨 ЦВЕТА - используем старую схему
        self.setup_colors()
        
        # 📝 ЛЕЙБЛ (создается позже)
        self.label_item = None
        
    def boundingRect(self) -> QRectF:
        """Возвращает ограничивающий прямоугольник пина."""
        from ..core.types import PinType
        if self.pin_type == PinType.EXEC:
            # Треугольник
            return QRectF(-self.triangle_size/2, -self.triangle_size/2, self.triangle_size, self.triangle_size)
        else:
            # Круг
            return QRectF(-self.current_radius, -self.current_radius, self.current_radius * 2, self.current_radius * 2)
    
    def setup_colors(self) -> None:
        """Настройка цветов для текущего типа пина."""
        # Получаем тип пина из pin.info
        pin_type = self.pin.info.pin_type
        
        # Используем цвет из PinType enum
        self.base_color = pin_type.color
        
    def create_modern_label(self) -> None:
        """Создание современного лейбла с правильным позиционированием."""
        if self.label_item is not None:
            return
            
        self.label_item = QGraphicsTextItem(self.pin.info.name, self.parent_node)
        
        # 🎨 СТИЛЬ ТЕКСТА
        self.label_item.setDefaultTextColor(self.parent_node.colors['text_secondary'])
        label_font = QFont("Segoe UI", 8, QFont.Weight.Normal)
        self.label_item.setFont(label_font)
        
        # 📍 ПОЗИЦИОНИРОВАНИЕ
        pin_pos = self.pos()
        label_rect = self.label_item.boundingRect()
        
        if self.is_output:
            # Выходной пин - лейбл слева
            label_x = pin_pos.x() - label_rect.width() - 10
            label_y = pin_pos.y() - (label_rect.height() / 2) + 1
        else:
            # Входной пин - лейбл справа  
            label_x = pin_pos.x() + 10
            label_y = pin_pos.y() - (label_rect.height() / 2) + 1
            
        self.label_item.setPos(label_x, label_y)
        
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None) -> None:
        """ПРОФЕССИОНАЛЬНАЯ отрисовка пина с разными формами для разных типов."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        from ..core.types import PinType
        
        if self.pin_type == PinType.EXEC:
            # 🔺 РИСУЕМ ТРЕУГОЛЬНУЮ СТРЕЛОЧКУ для exec пинов
            self._paint_exec_triangle(painter)
        else:
            # ⭕ РИСУЕМ КРУГ для обычных пинов
            self._paint_regular_circle(painter)
            
    def _paint_exec_triangle(self, painter: QPainter) -> None:
        """Отрисовка треугольной стрелочки для exec пинов."""
        # 🔺 СОЗДАЕМ ТРЕУГОЛЬНИК
        triangle = QPainterPath()
        size = self.triangle_size / 2
        
        if self.is_output:
            # Стрелочка вправо для output exec (ИЗ ноды) ▶️
            triangle.moveTo(size, 0)      # Острие справа
            triangle.lineTo(-size, -size)  # Верхний левый угол
            triangle.lineTo(-size, size)   # Нижний левый угол
        else:
            # Стрелочка вправо для input exec (В ноду) ▶️ 
            triangle.moveTo(size, 0)      # Острие справа
            triangle.lineTo(-size, -size)  # Верхний левый угол
            triangle.lineTo(-size, size)   # Нижний левый угол
        triangle.closeSubpath()
        
        # 🎨 ЦВЕТ И ЗАЛИВКА - серое заполнение для пустых пинов!
        if self.is_connected:
            # 🔗 СОЕДИНЕННЫЙ ПИН - цветная заливка
            if self.is_hovered:
                fill_color = self.base_color.lighter(120)
            else:
                fill_color = self.base_color
        else:
            # 📍 НЕ СОЕДИНЕННЫЙ ПИН - серая заливка с тем же дизайном!
            gray_base = QColor(120, 120, 120)  # Средне-серый цвет
            if self.is_hovered:
                fill_color = gray_base.lighter(130)  # Светлее при hover
            else:
                fill_color = gray_base
                
        painter.setBrush(QBrush(fill_color))
        
        # 🔲 ГРАНИЦА - ВСЕГДА цветная, только заливка меняется!
        border_color = self.base_color.darker(130)
        border_width = 1.0 if not self.is_hovered else 1.3
        painter.setPen(QPen(border_color, border_width))
        
        # 🎯 РИСУЕМ ТРЕУГОЛЬНИК
        painter.drawPath(triangle)
        
    def _paint_regular_circle(self, painter: QPainter) -> None:
        """Отрисовка обычного круглого пина - новая логика пустых пинов!"""
        rect = self.boundingRect()
        center = rect.center()
        
        # 🎨 РАДИАЛЬНЫЙ ГРАДИЕНТ для всех пинов!
        gradient = QRadialGradient(center, self.current_radius)
        
        if self.is_connected:
            # 🔗 СОЕДИНЕННЫЙ ПИН - цветной градиент
            if self.is_hovered:
                # 🌟 HOVER состояние
                gradient.setColorAt(0, self.base_color.lighter(180))
                gradient.setColorAt(0.3, self.base_color.lighter(140))
                gradient.setColorAt(0.7, self.base_color)
                gradient.setColorAt(1, self.base_color.darker(130))
            else:
                # 🔗 ПОДКЛЮЧЕННОЕ состояние
                gradient.setColorAt(0, self.base_color.lighter(160))
                gradient.setColorAt(0.4, self.base_color.lighter(120))
                gradient.setColorAt(0.8, self.base_color)
                gradient.setColorAt(1, self.base_color.darker(120))
        else:
            # 📍 НЕ СОЕДИНЕННЫЙ ПИН - серый градиент с тем же дизайном!
            gray_base = QColor(120, 120, 120)  # Средне-серый цвет
            if self.is_hovered:
                # 🌟 HOVER состояние - серый
                gradient.setColorAt(0, gray_base.lighter(180))
                gradient.setColorAt(0.3, gray_base.lighter(140))
                gradient.setColorAt(0.7, gray_base)
                gradient.setColorAt(1, gray_base.darker(130))
            else:
                # 📍 ОБЫЧНОЕ состояние - серый
                gradient.setColorAt(0, gray_base.lighter(160))
                gradient.setColorAt(0.4, gray_base.lighter(120))
                gradient.setColorAt(0.8, gray_base)
                gradient.setColorAt(1, gray_base.darker(120))
        
        painter.setBrush(QBrush(gradient))
        
        # 🔲 ГРАНИЦА - ВСЕГДА цветная, только заливка меняется!
        border_color = self.base_color.darker(150) if not self.is_hovered else self.base_color.darker(120)
        border_width = 1.2 if not self.is_hovered else 1.5
        painter.setPen(QPen(border_color, border_width))
        
        # 🎯 РИСУЕМ КРУГ
        painter.drawEllipse(rect)
        
        # ✨ БЛИК ДЛЯ HOVER - для всех пинов!
        if self.is_hovered:
            highlight_gradient = QRadialGradient(
                center + QPointF(-self.current_radius * 0.3, -self.current_radius * 0.3), 
                self.current_radius * 0.4
            )
            highlight_gradient.setColorAt(0, QColor(255, 255, 255, 60))
            highlight_gradient.setColorAt(0.7, QColor(255, 255, 255, 20))
            highlight_gradient.setColorAt(1, QColor(255, 255, 255, 0))
            
            painter.setBrush(QBrush(highlight_gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            highlight_rect = QRectF(
                center.x() - self.current_radius * 0.6,
                center.y() - self.current_radius * 0.6,
                self.current_radius * 1.2,
                self.current_radius * 1.2
            )
            painter.drawEllipse(highlight_rect)
        
    def hoverEnterEvent(self, event: QHoverEvent) -> None:
        """Анимация при наведении."""
        self.is_hovered = True
        self.current_radius = self.hover_radius
        # Обновляем отображение 
        self.prepareGeometryChange()
        self.update()
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event: QHoverEvent) -> None:
        """Анимация при уходе курсора."""
        self.is_hovered = False
        self.current_radius = self.radius
        # Обновляем отображение
        self.prepareGeometryChange()
        self.update()
        super().hoverLeaveEvent(event)
        
    def set_connected(self, connected: bool) -> None:
        """Установка состояния подключения."""
        self.is_connected = connected
        self.update()
        
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Обработка клика для создания соединений."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Эмитируем сигнал выбора пина для PropertiesViewModel
            self.parent_node.editor_view.pin_selected.emit(self.pin_id)
            # Начинаем создание соединения через editor_view
            self.parent_node.editor_view.start_connection_creation(self)
        super().mousePressEvent(event)


class ConnectionGraphicsItem(QGraphicsPathItem):
    """
    🔗 СОВРЕМЕННОЕ СОЕДИНЕНИЕ с профессиональными градиентами и анимациями.
    """
    
    def __init__(self, start_pin: PinGraphicsItem, end_pin: Optional[PinGraphicsItem], 
                 connection_id: Optional[str], editor_view, is_temporary: bool = False):
        super().__init__()
        self.start_pin = start_pin
        self.end_pin = end_pin
        self.connection_id = connection_id
        self.editor_view = editor_view
        self.is_temporary = is_temporary
        
        # 🎯 СОСТОЯНИЯ
        self.is_hovered = False
        self.is_selected = False
        
        # 🎨 ВИЗУАЛЬНЫЕ НАСТРОЙКИ
        self.visual_config = {
            'temp_width': 4,          # Толщина временного соединения
            'normal_width': 2.5,      # Толщина обычного соединения
            'hover_width': 3.5,       # Толщина при hover
            'temp_color': QColor(0, 122, 255),     # Синий для временных
            'curve_factor': 0.3,      # Коэффициент кривизны
            'glow_radius': 8,         # Радиус свечения
        }
        
        # 🔧 НАСТРОЙКИ ЭЛЕМЕНТА
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        
        # ⚡ Z-VALUE для правильного отображения слоев
        if is_temporary:
            self.setZValue(150)  # Поверх всего
        else:
            self.setZValue(5)    # Между нодами и пинами
        
        # 🎨 НАСТРОЙКА ЦВЕТОВ И ГРАДИЕНТОВ
        self.setup_visual_properties()
        
        # 📍 ОБНОВЛЕНИЕ ПУТИ
        self.update_path()
        
    def setup_visual_properties(self) -> None:
        """Настройка визуальных свойств соединения."""
        if self.is_temporary:
            self.base_color = self.visual_config['temp_color']
            self.current_width = self.visual_config['temp_width']
        else:
            # Получаем цвет от типа пина - ИСПОЛЬЗУЕМ СТАРУЮ СХЕМУ
            if hasattr(self.start_pin, 'pin_type') and hasattr(self.start_pin.pin_type, 'color'):
                self.base_color = self.start_pin.pin_type.color
            else:
                self.base_color = QColor(120, 120, 120)  # Fallback
            self.current_width = self.visual_config['normal_width']
            
        # Устанавливаем состояние подключения для пинов
        if not self.is_temporary:
            self.start_pin.set_connected(True)
            if self.end_pin:
                self.end_pin.set_connected(True)
                
    def create_smooth_path(self, start_pos: QPointF, end_pos: QPointF) -> QPainterPath:
        """Создание плавного пути соединения."""
        path = QPainterPath()
        path.moveTo(start_pos)
        
        # 📏 ВЫЧИСЛЯЕМ РАССТОЯНИЕ И КОНТРОЛЬНЫЕ ТОЧКИ
        dx = end_pos.x() - start_pos.x()
        dy = end_pos.y() - start_pos.y()
        distance = (dx ** 2 + dy ** 2) ** 0.5
        
        # �� ДИНАМИЧЕСКИЙ КОЭФФИЦИЕНТ КРИВИЗНЫ
        curve_strength = min(distance * self.visual_config['curve_factor'], 150)
        
        # Проверяем настройку редактора на тип соединений
        use_curves = getattr(self.editor_view, 'use_curved_connections', True)
        
        if use_curves and not self.is_temporary:
            # 🌊 ПЛАВНЫЕ КРИВЫЕ (по умолчанию)
            ctrl1_x = start_pos.x() + curve_strength
            ctrl1_y = start_pos.y()
            
            ctrl2_x = end_pos.x() - curve_strength
            ctrl2_y = end_pos.y()
            
            # Создаем Bezier кривую
            path.cubicTo(
                QPointF(ctrl1_x, ctrl1_y),
                QPointF(ctrl2_x, ctrl2_y),
                end_pos
            )
        else:
            # 📏 ПРЯМЫЕ ЛИНИИ
            path.lineTo(end_pos)
            
        return path
        
    def update_path(self) -> None:
        """Обновление пути соединения с учетом типа и состояния."""
        if not self.start_pin:
            return
            
        # 📍 ПОЛУЧАЕМ ПОЗИЦИИ
        start_pos = self.start_pin.scenePos()
        
        if self.end_pin:
            # Обычное соединение
            end_pos = self.end_pin.scenePos()
        elif self.is_temporary and hasattr(self, 'temp_end_pos'):
            # Временное соединение - следует за мышью
            end_pos = self.temp_end_pos
        else:
            # Fallback
            end_pos = start_pos
            
        # 🎨 СОЗДАЕМ ПУТЬ
        path = self.create_smooth_path(start_pos, end_pos)
        self.setPath(path)
        
    def update_end_point(self, end_pos: QPointF) -> None:
        """Обновление конечной точки для временного соединения."""
        if self.is_temporary:
            self.temp_end_pos = end_pos
            self.update_path()
            
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None) -> None:
        """Современная отрисовка с градиентами и эффектами."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        path = self.path()
        if path.isEmpty():
            return
            
        # 🎨 НАСТРОЙКА ЦВЕТОВ
        current_color = self.base_color
        if self.is_hovered:
            current_color = current_color.lighter(130)
        elif self.isSelected():
            current_color = current_color.lighter(150)
            
        # 📏 ДИНАМИЧЕСКАЯ ТОЛЩИНА
        width = self.current_width
        if self.is_hovered:
            width = self.visual_config['hover_width']
        elif self.isSelected():
            width = self.visual_config['hover_width'] + 0.5
            
        # ✨ ЭФФЕКТ СВЕЧЕНИЯ при hover/select
        if self.is_hovered or self.isSelected():
            glow_color = QColor(current_color)
            glow_color.setAlpha(60)
            
            for i in range(3):
                glow_width = width + (i + 1) * 1.5
                glow_pen = QPen(glow_color, glow_width)
                glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                glow_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                painter.setPen(glow_pen)
                painter.drawPath(path)
                glow_color.setAlpha(glow_color.alpha() // 2)
                
        # 🎯 ОСНОВНАЯ ЛИНИЯ
        main_pen = QPen(current_color, width)
        main_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        main_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        
        # 🌈 ГРАДИЕНТ для разных типов пинов
        if not self.is_temporary and self.end_pin and hasattr(self.end_pin, 'pin_type'):
            if self.start_pin.pin_type != self.end_pin.pin_type:
                # Создаем градиент между разными типами - ИСПОЛЬЗУЕМ СТАРЫЕ ЦВЕТА
                start_scene = self.start_pin.scenePos()
                end_scene = self.end_pin.scenePos()
                
                gradient = QLinearGradient(start_scene, end_scene)
                gradient.setColorAt(0, self.start_pin.pin_type.color.lighter(120))
                gradient.setColorAt(1, self.end_pin.pin_type.color.lighter(120))
                
                main_pen.setBrush(QBrush(gradient))
                
        painter.setPen(main_pen)
        painter.drawPath(path)
        
        # 💫 АНИМАЦИОННЫЕ ТОЧКИ для временных соединений
        if self.is_temporary:
            self.draw_flow_animation(painter, path, current_color)
            
    def draw_flow_animation(self, painter: QPainter, path: QPainterPath, color: QColor) -> None:
        """Рисование анимационного эффекта потока для временных соединений."""
        # Простые движущиеся точки
        dot_count = 3
        path_length = path.length()
        
        for i in range(dot_count):
            # Создаем эффект движения (можно будет добавить реальную анимацию позже)
            position = (i / dot_count) % 1.0
            point = path.pointAtPercent(position)
            
            # Рисуем светящуюся точку
            dot_color = QColor(color)
            dot_color.setAlpha(180)
            
            painter.setPen(QPen(dot_color, 6))
            painter.setBrush(QBrush(dot_color))
            painter.drawEllipse(point, 2, 2)
            
    def hoverEnterEvent(self, event: QHoverEvent) -> None:
        """Улучшенный hover эффект."""
        self.is_hovered = True
        self.update()
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event: QHoverEvent) -> None:
        """Убираем hover эффект."""
        self.is_hovered = False
        self.update()
        super().hoverLeaveEvent(event)
        
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press event."""
        if event.button() == Qt.RightButton:
            # Show context menu for deletion
            self.editor_view.show_connection_context_menu(self, event.screenPos())
        super().mousePressEvent(event) 

# Обновляем старый PinGraphicsItem для совместимости
class PinGraphicsItem(ModernPinGraphicsItem):
    """Совместимость со старым PinGraphicsItem - наследуется от современного."""
    
    def __init__(self, pin: Pin, parent_node: NodeGraphicsItem, is_output: bool):
        super().__init__(pin, parent_node, is_output)
        
    def create_label(self) -> None:
        """Совместимость - вызывает современный метод."""
        self.create_modern_label()
        
    def set_brush_color(self) -> None:
        """Совместимость - цвета устанавливаются автоматически."""
        pass
        
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Обработка клика для создания соединений."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Эмитируем сигнал выбора пина для PropertiesViewModel
            self.parent_node.editor_view.pin_selected.emit(self.pin_id)
            # Начинаем создание соединения через editor_view
            self.parent_node.editor_view.start_connection_creation(self)
        super().mousePressEvent(event) 