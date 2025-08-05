"""
Global Search (Command Palette) for PixelFlow Studio.

This module provides a modern command palette similar to VS Code, Sublime Text,
and other professional applications. It allows users to quickly search and
execute any action in the application.
"""

from __future__ import annotations

import time
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QLabel, QFrame, QGraphicsDropShadowEffect, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QRect, QPoint
from PySide6.QtGui import QFont, QPalette, QColor, QKeyEvent, QPainter, QBrush, QPen

from ..core.logging_config import get_logger
from ..core.constants import UIConstants, ColorConstants

logger = get_logger("global_search")


@dataclass
class SearchResult:
    """A single search result item."""
    
    id: str
    title: str
    description: str
    category: str
    icon: str = ""
    action: Optional[Callable] = None
    keywords: List[str] = None
    priority: int = 0
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


class GlobalSearchWidget(QWidget):
    """
    Modern global search widget with command palette functionality.
    
    Features:
    - Real-time search with fuzzy matching
    - Categorized results
    - Keyboard navigation
    - Action execution
    - Search history
    - Smart suggestions
    """
    
    action_triggered = Signal(str, object)  # action_id, data
    search_completed = Signal(list)  # list of results
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # Search data
        self.search_results: List[SearchResult] = []
        self.filtered_results: List[SearchResult] = []
        self.search_history: List[str] = []
        self.recent_actions: List[str] = []
        
        # UI state
        self.current_index = 0
        self.is_visible = False
        
        # Setup UI
        self.setup_ui()
        self.setup_animations()
        self.setup_connections()
        
        # Populate initial data
        self.populate_search_data()
        
        logger.info("Global search widget initialized")
    
    def setup_ui(self) -> None:
        """Setup the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Container frame with shadow
        self.container = QFrame()
        self.container.setObjectName("globalSearchContainer")
        self.container.setStyleSheet(f"""
            QFrame#globalSearchContainer {{
                background-color: {ColorConstants.BACKGROUND_COLOR};
                border: 2px solid {ColorConstants.PRIMARY_COLOR};
                border-radius: 12px;
                min-width: 600px;
                max-width: 800px;
            }}
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(16, 16, 16, 16)
        container_layout.setSpacing(12)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Search icon and label
        self.search_label = QLabel("🔍")
        self.search_label.setFont(QFont("Segoe UI", 16))
        header_layout.addWidget(self.search_label)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search nodes, actions, settings... (Ctrl+Shift+P)")
        self.search_input.setFont(QFont("Segoe UI", 12))
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {ColorConstants.BACKGROUND_LIGHT_COLOR};
                border: 1px solid {ColorConstants.BORDER_COLOR};
                border-radius: 6px;
                padding: 8px 12px;
                color: {ColorConstants.TEXT_COLOR};
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {ColorConstants.PRIMARY_COLOR};
                background-color: {ColorConstants.BACKGROUND_COLOR};
            }}
        """)
        header_layout.addWidget(self.search_input)
        
        # Results count
        self.results_count = QLabel("0 results")
        self.results_count.setStyleSheet(f"""
            QLabel {{
                color: {ColorConstants.TEXT_SECONDARY_COLOR};
                font-size: 12px;
                padding: 4px 8px;
            }}
        """)
        header_layout.addWidget(self.results_count)
        
        container_layout.addLayout(header_layout)
        
        # Results list
        self.results_list = QListWidget()
        self.results_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {ColorConstants.BACKGROUND_COLOR};
                border: 1px solid {ColorConstants.BORDER_COLOR};
                border-radius: 6px;
                outline: none;
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border-bottom: 1px solid {ColorConstants.BORDER_COLOR};
                color: {ColorConstants.TEXT_COLOR};
            }}
            QListWidget::item:selected {{
                background-color: {ColorConstants.PRIMARY_COLOR};
                color: white;
            }}
            QListWidget::item:hover {{
                background-color: {ColorConstants.BACKGROUND_LIGHT_COLOR};
            }}
        """)
        self.results_list.setMaximumHeight(400)
        container_layout.addWidget(self.results_list)
        
        # Footer with keyboard shortcuts
        footer_layout = QHBoxLayout()
        
        shortcuts_info = QLabel("↑↓ Navigate • Enter Execute • Esc Close • Ctrl+N New Node")
        shortcuts_info.setStyleSheet(f"""
            QLabel {{
                color: {ColorConstants.TEXT_SECONDARY_COLOR};
                font-size: 11px;
                padding: 4px 8px;
            }}
        """)
        footer_layout.addWidget(shortcuts_info)
        
        container_layout.addLayout(footer_layout)
        
        layout.addWidget(self.container)
    
    def setup_animations(self) -> None:
        """Setup animations for smooth show/hide transitions."""
        # Fade in animation
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Scale animation
        self.scale_animation = QPropertyAnimation(self.container, b"geometry")
        self.scale_animation.setDuration(200)
        self.scale_animation.setEasingCurve(QEasingCurve.OutBack)
    
    def setup_connections(self) -> None:
        """Setup signal connections."""
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.search_input.returnPressed.connect(self.execute_current_action)
        self.results_list.itemClicked.connect(self.on_item_clicked)
        self.results_list.itemDoubleClicked.connect(self.execute_current_action)
    
    def populate_search_data(self) -> None:
        """Populate the search data with available actions and nodes."""
        # Node categories
        self.search_results.extend([
            SearchResult(
                id="node_generator",
                title="Generator Node",
                description="Create a new generator node for image generation",
                category="Nodes",
                icon="🎨",
                keywords=["generator", "create", "new", "image"],
                priority=10
            ),
            SearchResult(
                id="node_filter",
                title="Filter Node",
                description="Apply filters and effects to images",
                category="Nodes",
                icon="🔧",
                keywords=["filter", "effect", "blur", "sharpen"],
                priority=9
            ),
            SearchResult(
                id="node_transform",
                title="Transform Node",
                description="Transform, scale, rotate images",
                category="Nodes",
                icon="🔄",
                keywords=["transform", "scale", "rotate", "move"],
                priority=8
            ),
            SearchResult(
                id="node_output",
                title="Output Node",
                description="Save or display the final result",
                category="Nodes",
                icon="💾",
                keywords=["output", "save", "export", "display"],
                priority=7
            ),
        ])
        
        # Actions
        self.search_results.extend([
            SearchResult(
                id="action_new_project",
                title="New Project",
                description="Create a new empty project",
                category="Actions",
                icon="📄",
                keywords=["new", "project", "create", "start"],
                priority=10
            ),
            SearchResult(
                id="action_open_project",
                title="Open Project",
                description="Open an existing project file",
                category="Actions",
                icon="📂",
                keywords=["open", "load", "file", "project"],
                priority=9
            ),
            SearchResult(
                id="action_save_project",
                title="Save Project",
                description="Save the current project",
                category="Actions",
                icon="💾",
                keywords=["save", "store", "project"],
                priority=8
            ),
            SearchResult(
                id="action_execute_graph",
                title="Execute Graph",
                description="Run the entire node graph",
                category="Actions",
                icon="▶️",
                keywords=["execute", "run", "start", "process"],
                priority=9
            ),
            SearchResult(
                id="action_undo",
                title="Undo",
                description="Undo the last action",
                category="Actions",
                icon="↶",
                keywords=["undo", "back", "reverse"],
                priority=7
            ),
            SearchResult(
                id="action_redo",
                title="Redo",
                description="Redo the last undone action",
                category="Actions",
                icon="↷",
                keywords=["redo", "forward", "repeat"],
                priority=7
            ),
        ])
        
        # Settings
        self.search_results.extend([
            SearchResult(
                id="settings_theme",
                title="Change Theme",
                description="Switch between light and dark themes",
                category="Settings",
                icon="🎨",
                keywords=["theme", "dark", "light", "color"],
                priority=6
            ),
            SearchResult(
                id="settings_preferences",
                title="Preferences",
                description="Open application preferences",
                category="Settings",
                icon="⚙️",
                keywords=["preferences", "settings", "options", "configure"],
                priority=5
            ),
        ])
        
        logger.info(f"Populated {len(self.search_results)} search results")
    
    def show_search(self, position: Optional[QPoint] = None) -> None:
        """Show the global search widget."""
        if self.is_visible:
            return
        
        # Position the widget
        if position is None:
            # Center on screen
            screen = QApplication.primaryScreen().geometry()
            widget_rect = self.geometry()
            x = (screen.width() - widget_rect.width()) // 2
            y = (screen.height() - widget_rect.height()) // 3
            self.move(x, y)
        else:
            self.move(position)
        
        # Clear and focus
        self.search_input.clear()
        self.search_input.setFocus()
        self.current_index = 0
        
        # Show with animation
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self.activateWindow()
        
        # Animate in
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
        
        self.is_visible = True
        logger.info("Global search widget shown")
    
    def hide_search(self) -> None:
        """Hide the global search widget."""
        if not self.is_visible:
            return
        
        # Animate out
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self.hide)
        self.fade_animation.start()
        
        self.is_visible = False
        logger.info("Global search widget hidden")
    
    def on_search_text_changed(self, text: str) -> None:
        """Handle search text changes."""
        if not text:
            self.show_recent_actions()
        else:
            self.perform_search(text)
    
    def perform_search(self, query: str) -> None:
        """Perform the search and update results."""
        query_lower = query.lower()
        self.filtered_results = []
        
        for result in self.search_results:
            # Calculate relevance score
            score = 0
            
            # Exact matches get highest priority
            if query_lower in result.title.lower():
                score += 100
            if query_lower in result.description.lower():
                score += 50
            if query_lower in result.category.lower():
                score += 30
            
            # Keyword matches
            for keyword in result.keywords:
                if query_lower in keyword.lower():
                    score += 20
            
            # Priority bonus
            score += result.priority
            
            if score > 0:
                result.score = score
                self.filtered_results.append(result)
        
        # Sort by relevance
        self.filtered_results.sort(key=lambda x: x.score, reverse=True)
        
        # Update UI
        self.update_results_list()
        self.search_completed.emit(self.filtered_results)
        
        logger.debug(f"Search for '{query}' returned {len(self.filtered_results)} results")
    
    def show_recent_actions(self) -> None:
        """Show recent actions when search is empty."""
        # Get recent actions from history
        recent_results = []
        for action_id in self.recent_actions[:10]:
            for result in self.search_results:
                if result.id == action_id:
                    recent_results.append(result)
                    break
        
        self.filtered_results = recent_results
        self.update_results_list()
    
    def update_results_list(self) -> None:
        """Update the results list widget."""
        self.results_list.clear()
        
        current_category = ""
        for i, result in enumerate(self.filtered_results):
            # Add category header if needed
            if result.category != current_category:
                category_item = QListWidgetItem(f"📁 {result.category}")
                category_item.setFlags(Qt.NoItemFlags)  # Non-selectable
                category_item.setBackground(QColor(ColorConstants.BACKGROUND_LIGHT_COLOR))
                category_item.setForeground(QColor(ColorConstants.TEXT_SECONDARY_COLOR))
                self.results_list.addItem(category_item)
                current_category = result.category
            
            # Add result item
            item = QListWidgetItem(f"{result.icon} {result.title}")
            item.setData(Qt.UserRole, result)
            
            # Add description as tooltip
            item.setToolTip(f"{result.description}\n\nCategory: {result.category}")
            
            self.results_list.addItem(item)
        
        # Update count
        self.results_count.setText(f"{len(self.filtered_results)} results")
        
        # Select first item
        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)
    
    def on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle item click in results list."""
        result = item.data(Qt.UserRole)
        if result:
            self.execute_action(result)
    
    def execute_current_action(self) -> None:
        """Execute the currently selected action."""
        current_item = self.results_list.currentItem()
        if current_item:
            result = current_item.data(Qt.UserRole)
            if result:
                self.execute_action(result)
    
    def execute_action(self, result: SearchResult) -> None:
        """Execute a search result action."""
        # Add to recent actions
        if result.id in self.recent_actions:
            self.recent_actions.remove(result.id)
        self.recent_actions.insert(0, result.id)
        
        # Keep only last 20 actions
        self.recent_actions = self.recent_actions[:20]
        
        # Emit signal
        self.action_triggered.emit(result.id, result)
        
        # Hide search
        self.hide_search()
        
        logger.info(f"Executed action: {result.title} ({result.id})")
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events."""
        if event.key() == Qt.Key_Escape:
            self.hide_search()
        elif event.key() == Qt.Key_Up:
            self.navigate_up()
        elif event.key() == Qt.Key_Down:
            self.navigate_down()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.execute_current_action()
        else:
            super().keyPressEvent(event)
    
    def navigate_up(self) -> None:
        """Navigate to previous item."""
        current_row = self.results_list.currentRow()
        if current_row > 0:
            self.results_list.setCurrentRow(current_row - 1)
    
    def navigate_down(self) -> None:
        """Navigate to next item."""
        current_row = self.results_list.currentRow()
        if current_row < self.results_list.count() - 1:
            self.results_list.setCurrentRow(current_row + 1)
    
    def focusOutEvent(self, event) -> None:
        """Handle focus out event."""
        # Hide after a short delay to allow for clicks
        QTimer.singleShot(100, self.hide_search)
        super().focusOutEvent(event)


class GlobalSearchManager:
    """
    Manager for global search functionality.
    
    Provides easy access to global search from anywhere in the application.
    """
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.search_widget = GlobalSearchWidget(main_window)
        self.setup_connections()
        
        logger.info("Global search manager initialized")
    
    def setup_connections(self) -> None:
        """Setup connections between search and main window."""
        self.search_widget.action_triggered.connect(self.handle_action)
    
    def show_search(self, position: Optional[QPoint] = None) -> None:
        """Show the global search widget."""
        self.search_widget.show_search(position)
    
    def handle_action(self, action_id: str, result: SearchResult) -> None:
        """Handle action execution from search results."""
        try:
            if action_id.startswith("node_"):
                self.handle_node_action(action_id)
            elif action_id.startswith("action_"):
                self.handle_action_action(action_id)
            elif action_id.startswith("settings_"):
                self.handle_settings_action(action_id)
            else:
                logger.warning(f"Unknown action: {action_id}")
        except Exception as e:
            logger.error(f"Error executing action {action_id}: {e}")
    
    def handle_node_action(self, action_id: str) -> None:
        """Handle node creation actions."""
        node_type_map = {
            "node_generator": "GeneratorNode",
            "node_filter": "FilterNode", 
            "node_transform": "TransformNode",
            "node_output": "OutputNode"
        }
        
        if action_id in node_type_map:
            node_class = node_type_map[action_id]
            # Add node to the center of the view
            if hasattr(self.main_window, 'node_editor'):
                self.main_window.node_editor.add_node(node_class)
    
    def handle_action_action(self, action_id: str) -> None:
        """Handle general actions."""
        action_map = {
            "action_new_project": self.main_window.new_project,
            "action_open_project": self.main_window.open_project,
            "action_save_project": self.main_window.save_project,
            "action_execute_graph": self.main_window.execute_graph,
            "action_undo": self.main_window.undo,
            "action_redo": self.main_window.redo,
        }
        
        if action_id in action_map:
            action_map[action_id]()
    
    def handle_settings_action(self, action_id: str) -> None:
        """Handle settings actions."""
        if action_id == "settings_theme":
            # TODO: Implement theme switching
            logger.info("Theme switching not implemented yet")
        elif action_id == "settings_preferences":
            # TODO: Implement preferences dialog
            logger.info("Preferences dialog not implemented yet")


# Global instance
_global_search_manager: Optional[GlobalSearchManager] = None


def get_global_search_manager(main_window=None) -> GlobalSearchManager:
    """Get the global search manager instance."""
    global _global_search_manager
    if _global_search_manager is None and main_window:
        _global_search_manager = GlobalSearchManager(main_window)
    return _global_search_manager


def show_global_search(main_window, position: Optional[QPoint] = None) -> None:
    """Show the global search widget."""
    manager = get_global_search_manager(main_window)
    if manager:
        manager.show_search(position) 