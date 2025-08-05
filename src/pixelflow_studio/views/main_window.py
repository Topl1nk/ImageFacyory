"""
Main window for PixelFlow Studio.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeyEvent
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, 
    QSplitter, QDockWidget, QToolBar, QMenu,
    QLabel, QPushButton, QFrame, QMessageBox
)

from ..core.application import Application
from ..core.logging_config import get_logger
from ..viewmodels.properties_viewmodel import PropertiesViewModel
from .node_editor import NodeEditorView
from .node_palette import NodePaletteWidget
from .properties.properties_panel import PropertiesPanel
from .output_panel import OutputPanel
from .global_search import show_global_search

logger = get_logger("main_window")


class MainWindow(QMainWindow):
    """
    Main window for PixelFlow Studio.
    
    Features:
    - Node editor with canvas
    - Node palette for adding nodes
    - Properties panel for node editing
    - Output panel for logs and results
    - Menu bar with standard operations
    - Toolbar with common actions
    - Status bar with information
    """
    
    def __init__(self, app: Application):
        super().__init__()
        self.app = app
        
        # ViewModels
        self.properties_viewmodel: Optional[PropertiesViewModel] = None
        
        # Views
        self.node_editor: Optional[NodeEditorView] = None
        self.node_palette: Optional[NodePaletteWidget] = None
        self.properties_panel: Optional[PropertiesPanel] = None
        self.output_panel: Optional[OutputPanel] = None
        
        # Dock widgets для меню окон
        self.palette_dock: Optional[QDockWidget] = None
        self.properties_dock: Optional[QDockWidget] = None
        self.output_dock: Optional[QDockWidget] = None
        
        # Menu actions для синхронизации
        self.palette_action: Optional[QAction] = None
        self.properties_action: Optional[QAction] = None
        self.output_action: Optional[QAction] = None
        self.windows_action: Optional[QAction] = None
        self.windows_menu: Optional[QMenu] = None
        
        self.setup_ui()
        self.setup_toolbar()
        self.setup_status_bar()
        self.setup_connections()
        self.setup_shortcuts()
        
        # Auto-save timer
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(30000)  # Auto-save every 30 seconds
        
    def setup_ui(self) -> None:
        """Setup the main user interface."""
        self.setWindowTitle("PixelFlow Studio - Professional Node-Based Image Processing")
        self.setMinimumSize(1200, 800)
        # Открываем окно на весь экран (максимизированно)
        self.showMaximized()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create splitter for resizable panels
        self.main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        # Left panel - Node Palette
        self.node_palette = NodePaletteWidget(self.app)
        self.palette_dock = QDockWidget("Node Palette", self)
        self.palette_dock.setWidget(self.node_palette)
        self.palette_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        # Устанавливаем нормальную ширину Node Palette
        self.palette_dock.setMinimumWidth(280)
        self.palette_dock.setMaximumWidth(400)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.palette_dock)
        
        # Center - Node Editor
        self.node_editor = NodeEditorView(self.app)
        self.main_splitter.addWidget(self.node_editor)
        
        # Right panel - Properties (с MVVM архитектурой)
        self.properties_viewmodel = PropertiesViewModel(self.app)
        self.properties_panel = PropertiesPanel(self.properties_viewmodel, self.node_editor)
        self.properties_dock = QDockWidget("Properties", self)
        self.properties_dock.setWidget(self.properties_panel)
        self.properties_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        # Устанавливаем нормальную ширину Properties panel
        self.properties_dock.setMinimumWidth(350)
        self.properties_dock.setMaximumWidth(500)
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)
        
        # Output panel - теперь свободная панель!
        self.output_panel = OutputPanel(self.app)
        self.output_dock = QDockWidget("Output", self)
        self.output_dock.setWidget(self.output_panel)
        self.output_dock.setAllowedAreas(Qt.AllDockWidgetAreas)  # СВОБОДА ПАНЕЛЯМ!
        # Устанавливаем нормальную высоту Output panel
        self.output_dock.setMinimumHeight(200)
        self.output_dock.setMaximumHeight(400)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.output_dock)
        
        # Variables panel - список переменных как в Unreal Engine!
        from .variables_panel import VariablesPanel
        self.variables_panel = VariablesPanel(self.app, self.node_editor)
        self.variables_dock = QDockWidget("Variables", self)
        self.variables_dock.setWidget(self.variables_panel)
        self.variables_dock.setAllowedAreas(Qt.AllDockWidgetAreas)  # РАВНОПРАВИЕ!
        # Устанавливаем размеры Variables panel
        self.variables_dock.setMinimumWidth(280)
        self.variables_dock.setMaximumWidth(400)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.variables_dock)
        

        
        # Размеры dock widgets настроены через setMinimumWidth/setMaximumWidth
        
    def setup_toolbar(self) -> None:
        """Setup toolbar."""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(False)
        
        # Files menu - объединяем New, Open, Save в одно меню
        self.files_action = QAction("Files", self)
        self.files_action.setToolTip("File Operations")
        
        # Create popup menu for files
        self.files_menu = QMenu(self)
        
        # New project
        new_action = QAction("New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.setToolTip("New Project (Ctrl+N)")
        new_action.triggered.connect(self.new_project)
        self.files_menu.addAction(new_action)
        
        # Open project
        open_action = QAction("Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setToolTip("Open Project (Ctrl+O)")
        open_action.triggered.connect(self.open_project)
        self.files_menu.addAction(open_action)
        
        # Save project
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.setToolTip("Save Project (Ctrl+S)")
        save_action.triggered.connect(self.save_project)
        self.files_menu.addAction(save_action)
        
        # Set menu to action and connect trigger
        self.files_action.setMenu(self.files_menu)
        self.files_action.triggered.connect(self._show_files_menu)
        toolbar.addAction(self.files_action)
        
        toolbar.addSeparator()
        
        # Execute
        execute_action = QAction("Execute", self)
        execute_action.setToolTip("Execute Graph (F5)")
        execute_action.triggered.connect(self.execute_graph)
        toolbar.addAction(execute_action)
        
        # Stop
        stop_action = QAction("Stop", self)
        stop_action.setToolTip("Stop Execution (F7)")
        stop_action.triggered.connect(self.stop_execution)
        toolbar.addAction(stop_action)
        
        # Separator
        toolbar.addSeparator()
        
        # Windows button as proper QAction
        self.windows_action = QAction("Windows", self)
        self.windows_action.setToolTip("Show/Hide Panels")
        
        # Create popup menu for windows
        self.windows_menu = QMenu(self)
        
        # Node Palette
        palette_action = QAction("Node Palette", self)
        palette_action.setCheckable(True)
        palette_action.setChecked(True)
        palette_action.triggered.connect(
            lambda checked: self._toggle_dock_widget(self.palette_dock, checked)
        )
        self.windows_menu.addAction(palette_action)
        self.palette_action = palette_action
        
        # Properties Panel
        properties_action = QAction("Properties", self)
        properties_action.setCheckable(True)
        properties_action.setChecked(True)
        properties_action.triggered.connect(
            lambda checked: self._toggle_dock_widget(self.properties_dock, checked)
        )
        self.windows_menu.addAction(properties_action)
        self.properties_action = properties_action
        
        # Output Panel
        output_action = QAction("Output", self)
        output_action.setCheckable(True)
        output_action.setChecked(True)
        output_action.triggered.connect(
            lambda checked: self._toggle_dock_widget(self.output_dock, checked)
        )
        self.windows_menu.addAction(output_action)
        self.output_action = output_action
        
        # Variables Panel - список переменных как в Unreal Engine!
        variables_action = QAction("Variables", self)
        variables_action.setCheckable(True)
        variables_action.setChecked(True)
        variables_action.triggered.connect(
            lambda checked: self._toggle_dock_widget(self.variables_dock, checked)
        )
        self.windows_menu.addAction(variables_action)
        self.variables_action = variables_action
        

        
        self.windows_menu.addSeparator()
        
        # Reset layout
        reset_layout_action = QAction("Reset Layout", self)
        reset_layout_action.triggered.connect(self._reset_window_layout)
        self.windows_menu.addAction(reset_layout_action)
        
        # Set menu to action and connect trigger
        self.windows_action.setMenu(self.windows_menu)
        self.windows_action.triggered.connect(self._show_windows_menu)
        toolbar.addAction(self.windows_action)
        
    def setup_menus(self) -> None:
        """Setup menu bar."""
        # For now, no additional menus needed
        pass
        
    def _show_files_menu(self) -> None:
        """Show files menu at cursor position."""
        if self.files_menu:
            # Получаем позицию кнопки Files на toolbar
            toolbar = self.findChild(QToolBar)
            if toolbar:
                # Показываем меню под кнопкой
                button_rect = toolbar.actionGeometry(self.files_action)
                menu_position = toolbar.mapToGlobal(button_rect.bottomLeft())
                self.files_menu.exec_(menu_position)
            else:
                # Fallback - показать в позиции курсора
                from PySide6.QtGui import QCursor
                self.files_menu.exec_(QCursor.pos())
    
    def _show_windows_menu(self) -> None:
        """Show windows menu at cursor position."""
        if self.windows_menu:
            # Получаем позицию кнопки Windows на toolbar
            toolbar = self.findChild(QToolBar)
            if toolbar:
                # Показываем меню под кнопкой
                button_rect = toolbar.actionGeometry(self.windows_action)
                menu_position = toolbar.mapToGlobal(button_rect.bottomLeft())
                self.windows_menu.exec_(menu_position)
            else:
                # Fallback - показать в позиции курсора
                from PySide6.QtGui import QCursor
                self.windows_menu.exec_(QCursor.pos())
    
    def _toggle_dock_widget(self, dock_widget: QDockWidget, visible: bool) -> None:
        """Show/hide dock widget."""
        if dock_widget:
            dock_widget.setVisible(visible)
            
    def _reset_window_layout(self) -> None:
        """Reset window layout to default."""
        # Show all panels
        if self.palette_dock:
            self.palette_dock.setVisible(True)
            self.addDockWidget(Qt.LeftDockWidgetArea, self.palette_dock)
            
        if self.properties_dock:
            self.properties_dock.setVisible(True)
            self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)
            
        if self.output_dock:
            self.output_dock.setVisible(True)
            self.addDockWidget(Qt.BottomDockWidgetArea, self.output_dock)
            
        if self.variables_dock:
            self.variables_dock.setVisible(True)
            self.addDockWidget(Qt.LeftDockWidgetArea, self.variables_dock)
            
        # Update sizes
        if hasattr(self, 'main_splitter'):
            self.main_splitter.setSizes([300, 1000, 300])
        
    def setup_status_bar(self) -> None:
        """Setup status bar."""
        status_bar = self.statusBar()
        
        # Node count
        self.node_count_label = QLabel("Nodes: 0")
        status_bar.addPermanentWidget(self.node_count_label)
        
        # Connection count
        self.connection_count_label = QLabel("Connections: 0")
        status_bar.addPermanentWidget(self.connection_count_label)
        
        # Execution status
        self.execution_status_label = QLabel("Ready")
        status_bar.addPermanentWidget(self.execution_status_label)
        
        # Update status
        self.update_status()
        
    def setup_connections(self) -> None:
        """Setup signal connections."""
        if self.node_editor:
            self.node_editor.selection_changed.connect(self.on_selection_changed)
            self.node_editor.graph_changed.connect(self.on_graph_changed)
            
        if self.node_palette:
            self.node_palette.node_selected.connect(self.on_node_selected)
            
        # Connect PropertiesViewModel to NodeEditor selection
        if self.properties_viewmodel and self.node_editor:
            # Подключаем сигналы выбора нод к ViewModel
            self.node_editor.node_selected.connect(self.properties_viewmodel.select_node)
            self.node_editor.node_deselected.connect(self.properties_viewmodel.clear_selection)
            # Подключаем сигнал выбора пинов
            self.node_editor.pin_selected.connect(self.properties_viewmodel.select_pin_by_id)
            
        # Connect dock widget visibility with Windows button states
        if self.palette_dock and self.palette_action:
            self.palette_dock.visibilityChanged.connect(
                lambda visible: self.palette_action.setChecked(visible)
            )
        if self.properties_dock and self.properties_action:
            self.properties_dock.visibilityChanged.connect(
                lambda visible: self.properties_action.setChecked(visible)
            )
        if self.output_dock and self.output_action:
            self.output_dock.visibilityChanged.connect(
                lambda visible: self.output_action.setChecked(visible)
            )
            
    def setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        # Global search shortcut
        from PySide6.QtGui import QShortcut, QKeySequence
        global_search_shortcut = QShortcut(QKeySequence("Ctrl+Shift+P"), self)
        global_search_shortcut.activated.connect(self.show_global_search)
        
        # Other shortcuts
        undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        undo_shortcut.activated.connect(self.undo)
        
        redo_shortcut = QShortcut(QKeySequence("Ctrl+Y"), self)
        redo_shortcut.activated.connect(self.redo)
        
        new_project_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        new_project_shortcut.activated.connect(self.new_project)
        
        open_project_shortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        open_project_shortcut.activated.connect(self.open_project)
        
        save_project_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_project_shortcut.activated.connect(self.save_project)
        
        execute_shortcut = QShortcut(QKeySequence("F5"), self)
        execute_shortcut.activated.connect(self.execute_graph)
        
        logger.info("Keyboard shortcuts setup completed")
        
    def show_global_search(self) -> None:
        """Show the global search widget."""
        show_global_search(self)
            
    def update_status(self) -> None:
        """Update status bar information."""
        graph_stats = self.app.graph.get_stats()
        self.node_count_label.setText(f"Nodes: {graph_stats['nodes']}")
        self.connection_count_label.setText(f"Connections: {graph_stats['connections']}")
        
        if self.app.graph.is_executing:
            self.execution_status_label.setText("Executing...")
        else:
            self.execution_status_label.setText("Ready")
            
    def on_selection_changed(self) -> None:
        """Handle node selection changes."""
        if self.properties_viewmodel and self.node_editor:
            # Получаем выбранные ноды из редактора
            selected_nodes = self.node_editor.selected_nodes
            if selected_nodes:
                # Показываем свойства первой выбранной ноды через ViewModel
                first_node = selected_nodes[0]
                self.properties_viewmodel.select_node(first_node.node.id)
            else:
                # Нет выбранных нод - очищаем выбор через ViewModel
                self.properties_viewmodel.clear_selection()
            
    def on_graph_changed(self) -> None:
        """Handle graph changes."""
        self.update_status()
        
    def on_node_selected(self, node_class_name: str) -> None:
        """Handle node selection from palette."""
        if self.node_editor:
            self.node_editor.add_node(node_class_name)
            
    # Menu actions
    def new_project(self) -> None:
        """Create a new project."""
        if self.app.graph.nodes:
            reply = QMessageBox.question(
                self, "New Project", 
                "Current project has unsaved changes. Create new project anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
                
        self.app.graph.clear()
        
        # Clear graphics after clearing graph
        if hasattr(self, 'node_editor') and self.node_editor:
            self.node_editor.refresh_graphics()
        
        self.update_status()
        
    def open_project(self) -> None:
        """Open a project file."""
        from PySide6.QtWidgets import QFileDialog
        import json
        
        # Check for unsaved changes
        if self.app.graph.nodes:
            reply = QMessageBox.question(
                self, "Open Project", 
                "Current project has unsaved changes. Open new project anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Project",
            "",
            "PixelFlow Project (*.pfp);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # Get node classes for deserialization
            node_classes = self.app.node_registry
            
            # Load the graph
            self.app.graph.from_dict(project_data, node_classes)
            
            # Refresh graphics
            if hasattr(self, 'node_editor') and self.node_editor:
                self.node_editor.refresh_graphics()
            
            # Update Properties Panel if there's a current node
            if hasattr(self, 'properties_panel') and self.properties_panel and self.properties_panel.current_node_id:
                self.properties_panel.update_node_properties(self.properties_panel.current_node_id)
            
            # Update UI
            self.update_status()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open project:\n{str(e)}")
        
    def save_project(self) -> None:
        """Save the current project."""
        # For now, always show save dialog (in future, remember last file path)
        self.save_project_as()
        
    def save_project_as(self) -> None:
        """Save the current project with a new name."""
        from PySide6.QtWidgets import QFileDialog
        import json
        
        if not self.app.graph.nodes:
            QMessageBox.information(self, "Info", "No nodes to save")
            return
        
        # Show file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Project",
            "",
            "PixelFlow Project (*.pfp);;All Files (*)"
        )
        
        if not file_path:
            return
            
        # Add extension if not present
        if not file_path.endswith('.pfp'):
            file_path += '.pfp'
            
        try:
            # Serialize the graph
            project_data = self.app.graph.to_dict()
            
            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save project:\n{str(e)}")
        
    def export_image(self) -> None:
        """Export the result image."""
        # TODO: Implement image export
        QMessageBox.information(self, "Info", "Image export not implemented yet")
        
    def undo(self) -> None:
        """Undo last action."""
        if self.node_editor:
            self.node_editor.undo()
            
    def redo(self) -> None:
        """Redo last action."""
        if self.node_editor:
            self.node_editor.redo()
            
    def select_all(self) -> None:
        """Select all nodes."""
        if self.node_editor:
            self.node_editor.select_all()
            
    def delete_selected(self) -> None:
        """Delete selected nodes."""
        if self.node_editor:
            self.node_editor.delete_selected()
            
    def zoom_in(self) -> None:
        """Zoom in."""
        if self.node_editor:
            self.node_editor.zoom_in()
            
    def zoom_out(self) -> None:
        """Zoom out."""
        if self.node_editor:
            self.node_editor.zoom_out()
            
    def fit_to_view(self) -> None:
        """Fit all nodes to view."""
        if self.node_editor:
            self.node_editor.fit_to_view()
            
    def execute_graph(self) -> None:
        """Execute the entire graph."""
        # Используем QTimer для запуска async функции в Qt event loop
        QTimer.singleShot(0, self._start_graph_execution)
    
    def _start_graph_execution(self) -> None:
        """Start graph execution in proper async context."""
        import asyncio
        import threading
        
        # Выводим сообщение о начале выполнения
        if hasattr(self, 'output_panel') and self.output_panel:
            self.output_panel.add_log_message("INFO", "🚀 Starting graph execution...")
        
        def run_graph_async():
            """Run graph execution in separate thread with asyncio."""
            try:
                # Создаем новый event loop для этого потока
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Запускаем выполнение графа
                loop.run_until_complete(self.app.execute_graph_async())
                
                # Сигнализируем об успешном завершении
                QTimer.singleShot(0, lambda: self._on_execution_completed(True, None))
                
            except Exception as e:
                # Сигнализируем об ошибке
                QTimer.singleShot(0, lambda: self._on_execution_completed(False, str(e)))
            finally:
                loop.close()
        
        # Запускаем в отдельном потоке
        execution_thread = threading.Thread(target=run_graph_async, daemon=True)
        execution_thread.start()
    
    def _on_execution_completed(self, success: bool, error: str = None) -> None:
        """Handle completion of graph execution."""
        if hasattr(self, 'output_panel') and self.output_panel:
            if success:
                self.output_panel.add_log_message("INFO", "✅ Graph execution completed successfully!")
            else:
                self.output_panel.add_log_message("ERROR", f"❌ Graph execution failed: {error}")
        
    def execute_selected(self) -> None:
        """Execute selected nodes."""
        if self.node_editor:
            self.node_editor.execute_selected()
            
    def stop_execution(self) -> None:
        """Stop graph execution."""
        if self.app.graph.is_executing:
            self.app.graph.cancel_execution()
            
    def show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self, "About PixelFlow Studio",
            "PixelFlow Studio 1.0.0\n\n"
            "Professional Node-Based Image Processing\n"
            "Built with PySide6 and modern Python\n\n"
            "🎬 Advanced Demo Recording System:\n"
            "- Records every user action\n"
            "- Replays demos for testing\n"
            "- Prophetic rules prevent bugs\n"
            "- 'Laws before blood' philosophy"
        )
    
    def auto_save(self) -> None:
        """Auto-save the project."""
        # TODO: Implement auto-save
        pass
        
    def closeEvent(self, event) -> None:
        """Stop recording and save demo."""
        demo_system = self.node_editor.demo_system
        if demo_system and demo_system.recorder.recording:
            demo_path = demo_system.stop_recording_and_save()
            self.statusBar().showMessage(f"⏹️ Demo saved: {demo_path.name}", 5000)
            
            QMessageBox.information(
                self,
                "Demo Saved",
                f"Demo recorded and saved to:\n{demo_path}\n\n"
                f"Actions recorded: {len(demo_system.recorder.current_demo)}"
            )
        else:
            QMessageBox.warning(self, "Warning", "No active recording to stop.")
    
    def play_demo(self) -> None:
        """Load and play a demo."""
        from PySide6.QtWidgets import QFileDialog
        from pathlib import Path
        
        demo_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Demo to Play",
            str(Path("demos")),
            "Demo Files (*.json)"
        )
        
        if demo_path:
            demo_system = self.node_editor.demo_system
            if demo_system:
                self.statusBar().showMessage("▶️ Playing demo...", 0)
                
                try:
                    results = demo_system.play_demo_and_verify(Path(demo_path))
                    
                    if results["success"]:
                        success_rate = (results["successful_actions"] / results["total_actions"]) * 100
                        message = (
                            f"Demo playback completed!\n\n"
                            f"Success rate: {success_rate:.1f}%\n"
                            f"Successful actions: {results['successful_actions']}/{results['total_actions']}\n"
                            f"Rule violations: {results.get('total_violations', 0)}"
                        )
                        QMessageBox.information(self, "Demo Playback", message)
                    else:
                        QMessageBox.warning(self, "Demo Playback Failed", f"Error: {results.get('error', 'Unknown error')}")
                    
                    self.statusBar().showMessage("Demo playback finished", 3000)
                    
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to play demo:\n{e}")
                    self.statusBar().showMessage("Demo playback failed", 3000)
    
    def verify_demo(self) -> None:
        """Verify a demo with detailed analysis."""
        from PySide6.QtWidgets import QFileDialog, QTextEdit, QDialog, QVBoxLayout
        from pathlib import Path
        
        demo_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Demo to Verify",
            str(Path("demos")),
            "Demo Files (*.json)"
        )
        
        if demo_path:
            demo_system = self.node_editor.demo_system
            if demo_system:
                self.statusBar().showMessage("🔍 Verifying demo...", 0)
                
                try:
                    results = demo_system.play_demo_and_verify(Path(demo_path))
                    
                    # Создать детальный отчет
                    report = self._generate_verification_report(results)
                    
                    # Показать отчет в отдельном окне
                    dialog = QDialog(self)
                    dialog.setWindowTitle("Demo Verification Report")
                    dialog.resize(800, 600)
                    
                    layout = QVBoxLayout(dialog)
                    text_edit = QTextEdit()
                    text_edit.setPlainText(report)
                    text_edit.setReadOnly(True)
                    layout.addWidget(text_edit)
                    
                    dialog.exec()
                    
                    self.statusBar().showMessage("Demo verification completed", 3000)
                    
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to verify demo:\n{e}")
                    self.statusBar().showMessage("Demo verification failed", 3000)
    
    def _generate_verification_report(self, results) -> str:
        """Generate detailed verification report."""
        from typing import Dict, Any
        
        report_lines = [
            "🔍 DEMO VERIFICATION REPORT",
            "=" * 50,
            "",
            f"Demo: {results.get('demo_path', 'Unknown')}",
            f"Total Actions: {results.get('total_actions', 0)}",
            f"Successful Actions: {results.get('successful_actions', 0)}",
            f"Failed Actions: {results.get('failed_actions', 0)}",
            f"Success Rate: {(results.get('successful_actions', 0) / max(results.get('total_actions', 1), 1)) * 100:.1f}%",
            "",
            f"Total Rule Violations: {results.get('total_violations', 0)}",
            "",
        ]
        
        # Добавить ошибки
        if results.get("errors"):
            report_lines.extend([
                "❌ ERRORS:",
                "-" * 20,
            ])
            for error in results["errors"]:
                if isinstance(error, dict):
                    report_lines.append(f"  Action {error.get('action_index', '?')}: {error.get('error', str(error))}")
                else:
                    report_lines.append(f"  {error}")
            report_lines.append("")
        
        # Статус
        report_lines.extend([
            "🎯 SUMMARY:",
            "-" * 20,
            f"  Overall Status: {'✅ PASSED' if results.get('success') and results.get('total_violations', 0) == 0 else '❌ FAILED'}",
            f"  Recommendation: {'Demo is stable and reliable' if results.get('success') and results.get('total_violations', 0) == 0 else 'Review errors and violations'}",
        ])
        
        return "\n".join(report_lines)
        
    def auto_save(self) -> None:
        """Auto-save the project."""
        # TODO: Implement auto-save
        pass
    

        
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        if self.app.graph.nodes:
            reply = QMessageBox.question(
                self, "Exit", 
                "Save changes before exiting?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Save:
                self.save_project()
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept() 