"""
Main application class for PixelFlow Studio.
"""

from __future__ import annotations

import asyncio
import sys
from typing import Optional

from loguru import logger
from PySide6.QtWidgets import QApplication

from .graph import Graph
from ..nodes import get_all_node_classes


class Application:
    """
    Main application class that manages the lifecycle of PixelFlow Studio.
    
    This class provides:
    - Application initialization and shutdown
    - Graph management
    - Node registry
    - Event coordination
    """

    def __init__(self) -> None:
        self._qt_app: Optional[QApplication] = None
        self._graph = Graph()
        self._is_running = False
        
        # Initialize node registry
        self._node_classes = {}
        self._load_node_classes()

    def _load_node_classes(self) -> None:
        """Load all available node classes."""
        try:
            node_classes = get_all_node_classes()
            for node_class in node_classes:
                # Create temporary instance to get class info
                temp_instance = node_class()
                class_name = node_class.__name__
                self._node_classes[class_name] = {
                    'class': node_class,
                    'name': temp_instance.name,
                    'category': temp_instance.category,
                    'description': temp_instance.description,
                }
            
            logger.info(f"Loaded {len(self._node_classes)} node classes")
            
        except Exception as e:
            logger.error(f"Failed to load node classes: {e}")

    @property
    def graph(self) -> Graph:
        """Get the main graph instance."""
        return self._graph

    @property
    def node_classes(self) -> dict:
        """Get available node classes."""
        return self._node_classes.copy()
    
    @property
    def node_registry(self) -> dict:
        """Get node registry (alias for node_classes for backward compatibility)."""
        return {name: info['class'] for name, info in self._node_classes.items()}

    def get_node_categories(self) -> dict:
        """Get nodes organized by category."""
        categories = {}
        for class_name, info in self._node_classes.items():
            category = info['category']
            # Исключаем Variable ноды из Node Palette - они теперь в Variables Panel
            if category == "Variables":
                continue
            if category not in categories:
                categories[category] = []
            categories[category].append(info)
        return categories

    def create_node(self, class_name: str):
        """Create a new node instance by class name."""
        if class_name not in self._node_classes:
            raise ValueError(f"Unknown node class: {class_name}")
        
        node_class = self._node_classes[class_name]['class']
        return node_class()

    def initialize_qt(self) -> QApplication:
        """Initialize Qt application if not already done."""
        if self._qt_app is None:
            self._qt_app = QApplication.instance()
            if self._qt_app is None:
                self._qt_app = QApplication(sys.argv)
                self._qt_app.setApplicationName("PixelFlow Studio")
                self._qt_app.setApplicationVersion("1.0.0")
                self._qt_app.setOrganizationName("PixelFlow")
                self._qt_app.setOrganizationDomain("pixelflow.studio")
        
        return self._qt_app

    def run_headless(self) -> None:
        """Run the application in headless mode (no GUI)."""
        logger.info("Starting PixelFlow Studio in headless mode")
        self._is_running = True
        
        # Keep the application running
        try:
            while self._is_running:
                import time
                time.sleep(0.1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            self.shutdown()

    def run_gui(self) -> int:
        """Run the application with GUI."""
        qt_app = self.initialize_qt()
        logger.info("Starting PixelFlow Studio with GUI")
        
        # Create and show main window
        from ..views.main_window import MainWindow
        main_window = MainWindow(self)
        
        # НЕ вызываем sync_with_graph здесь - граф пустой на старте
        # sync_with_graph будет вызван автоматически при добавлении нод
        
        main_window.show()
        
        self._is_running = True
        return qt_app.exec()

    def shutdown(self) -> None:
        """Shutdown the application."""
        logger.info("Shutting down PixelFlow Studio")
        self._is_running = False
        
        # Cancel any running graph execution
        if self._graph.is_executing:
            self._graph.cancel_execution()
        
        # Clear the graph
        self._graph.clear()

    async def execute_graph_async(self) -> None:
        """Execute the current graph asynchronously."""
        if not self._graph.nodes:
            logger.warning("No nodes in graph to execute")
            return
        
        try:
            await self._graph.execute_all()
        except Exception as e:
            logger.error(f"Graph execution failed: {e}")
            raise

    def get_stats(self) -> dict:
        """Get application statistics."""
        return {
            'available_nodes': len(self._node_classes),
            'graph_stats': self._graph.get_stats(),
            'is_running': self._is_running,
        } 