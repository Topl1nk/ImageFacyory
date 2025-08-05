"""
Output panel for PixelFlow Studio.
"""

from __future__ import annotations

from typing import Optional, List
from PySide6.QtCore import Qt, Signal, QTimer, QThread
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTextEdit, QLabel,
    QPushButton, QSplitter, QListWidget, QListWidgetItem, QProgressBar,
    QFrame, QScrollArea, QGroupBox, QCheckBox, QComboBox
)

from ..core.application import Application


class OutputPanel(QWidget):
    """
    Panel for displaying output, logs, and execution results.
    
    Features:
    - Log output display
    - Execution progress
    - Error reporting
    - Result preview
    """
    
    def __init__(self, app: Application):
        super().__init__()
        self.app = app
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Title
        title_label = QLabel("Output")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #ffffff;
                padding: 5px;
                background-color: #404040;
                border-radius: 3px;
            }
        """)
        layout.addWidget(title_label)
        
        # Tab widget for different output types
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Log tab
        self.setup_log_tab()
        
        # Progress tab
        self.setup_progress_tab()
        
        # Results tab
        self.setup_results_tab()
        
        # Control buttons
        self.setup_control_buttons(layout)
        
    def setup_log_tab(self) -> None:
        """Setup the log output tab."""
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.setContentsMargins(0, 0, 0, 0)
        
        # Log level filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Log Level:"))
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["All", "DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        filter_layout.addWidget(self.log_level_combo)
        
        self.clear_log_btn = QPushButton("Clear")
        self.clear_log_btn.clicked.connect(self.clear_log)
        filter_layout.addWidget(self.clear_log_btn)
        
        self.save_log_btn = QPushButton("Save")
        self.save_log_btn.clicked.connect(self.save_log)
        filter_layout.addWidget(self.save_log_btn)
        
        filter_layout.addStretch()
        log_layout.addLayout(filter_layout)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #cccccc;
                border: 1px solid #404040;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        self.tab_widget.addTab(log_widget, "Log")
        
    def setup_progress_tab(self) -> None:
        """Setup the progress tab."""
        progress_widget = QWidget()
        progress_layout = QVBoxLayout(progress_widget)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        # Execution status
        self.execution_status_label = QLabel("Ready")
        self.execution_status_label.setStyleSheet("""
            QLabel {
                color: #00ff00;
                font-weight: bold;
                padding: 5px;
                background-color: #2a2a2a;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.execution_status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        # Node execution list
        self.node_list_label = QLabel("Node Execution Order:")
        progress_layout.addWidget(self.node_list_label)
        
        self.node_list = QListWidget()
        self.node_list.setMaximumHeight(150)
        progress_layout.addWidget(self.node_list)
        
        # Execution info
        self.execution_info_label = QLabel("No execution in progress")
        self.execution_info_label.setStyleSheet("color: #888888; font-style: italic;")
        progress_layout.addWidget(self.execution_info_label)
        
        self.tab_widget.addTab(progress_widget, "Progress")
        
    def setup_results_tab(self) -> None:
        """Setup the results tab."""
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        results_layout.setContentsMargins(0, 0, 0, 0)
        
        # Results list
        self.results_label = QLabel("Execution Results:")
        results_layout.addWidget(self.results_label)
        
        self.results_list = QListWidget()
        results_layout.addWidget(self.results_list)
        
        # Result preview
        self.preview_label = QLabel("Preview:")
        results_layout.addWidget(self.preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(100)
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #cccccc;
                border: 1px solid #404040;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
            }
        """)
        results_layout.addWidget(self.preview_text)
        
        self.tab_widget.addTab(results_widget, "Results")
        
    def setup_control_buttons(self, layout) -> None:
        """Setup control buttons."""
        button_layout = QHBoxLayout()
        
        self.clear_all_btn = QPushButton("Clear All")
        self.clear_all_btn.clicked.connect(self.clear_all)
        button_layout.addWidget(self.clear_all_btn)
        
        self.export_results_btn = QPushButton("Export Results")
        self.export_results_btn.clicked.connect(self.export_results)
        button_layout.addWidget(self.export_results_btn)
        
        button_layout.addStretch()
        
        # Auto-scroll checkbox
        self.auto_scroll_checkbox = QCheckBox("Auto-scroll")
        self.auto_scroll_checkbox.setChecked(True)
        button_layout.addWidget(self.auto_scroll_checkbox)
        
        layout.addLayout(button_layout)
        
    def setup_connections(self) -> None:
        """Setup signal connections."""
        self.log_level_combo.currentTextChanged.connect(self.filter_log)
        
        # Update timer for progress
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_progress)
        self.update_timer.start(100)  # Update every 100ms
        
    def add_log_message(self, level: str, message: str, node_name: str = "") -> None:
        """Add a log message to the output."""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color coding for log levels
        color_map = {
            "DEBUG": "#888888",
            "INFO": "#ffffff",
            "WARNING": "#ffff00",
            "ERROR": "#ff0000"
        }
        
        color = color_map.get(level, "#ffffff")
        
        # Format message
        if node_name:
            formatted_message = f'<span style="color: {color}">[{timestamp}] [{level}] [{node_name}] {message}</span>'
        else:
            formatted_message = f'<span style="color: {color}">[{timestamp}] [{level}] {message}</span>'
            
        # Add to text area
        self.log_text.append(formatted_message)
        
        # Auto-scroll if enabled
        if self.auto_scroll_checkbox.isChecked():
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
    def clear_log(self) -> None:
        """Clear the log output."""
        self.log_text.clear()
        
    def save_log(self) -> None:
        """Save the log to a file."""
        from PySide6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Log", "", "Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                self.add_log_message("INFO", f"Log saved to {filename}")
            except Exception as e:
                self.add_log_message("ERROR", f"Failed to save log: {e}")
                
    def filter_log(self) -> None:
        """Filter log messages by level."""
        # This would filter the log display based on the selected level
        # For now, we'll just log the filter change
        level = self.log_level_combo.currentText()
        self.add_log_message("INFO", f"Log filter changed to: {level}")
        
    def update_progress(self) -> None:
        """Update the progress display."""
        if self.app.graph.is_executing:
            self.execution_status_label.setText("Executing...")
            self.execution_status_label.setStyleSheet("""
                QLabel {
                    color: #ffff00;
                    font-weight: bold;
                    padding: 5px;
                    background-color: #2a2a2a;
                    border-radius: 3px;
                }
            """)
            
            # Show progress bar
            self.progress_bar.setVisible(True)
            
            # Update node list
            self.update_node_execution_list()
            
        else:
            self.execution_status_label.setText("Ready")
            self.execution_status_label.setStyleSheet("""
                QLabel {
                    color: #00ff00;
                    font-weight: bold;
                    padding: 5px;
                    background-color: #2a2a2a;
                    border-radius: 3px;
                }
            """)
            
            # Hide progress bar
            self.progress_bar.setVisible(False)
            
    def update_node_execution_list(self) -> None:
        """Update the node execution order list."""
        try:
            # Get execution order from graph
            execution_order = self.app.graph.calculate_execution_order()
            
            self.node_list.clear()
            for i, node in enumerate(execution_order):
                if node:
                    item = QListWidgetItem(f"{i+1}. {node.name}")
                    self.node_list.addItem(item)
                    
        except Exception as e:
            self.add_log_message("ERROR", f"Failed to update execution list: {e}")
            
    def add_execution_result(self, node_name: str, result: str, success: bool = True) -> None:
        """Add an execution result."""
        item = QListWidgetItem(f"{node_name}: {'✓' if success else '✗'} {result}")
        
        if success:
            item.setBackground(Qt.green)
        else:
            item.setBackground(Qt.red)
            
        self.results_list.addItem(item)
        
        # Update preview
        self.preview_text.append(f"[{node_name}] {result}")
        
    def clear_all(self) -> None:
        """Clear all output."""
        self.log_text.clear()
        self.node_list.clear()
        self.results_list.clear()
        self.preview_text.clear()
        self.execution_info_label.setText("No execution in progress")
        
    def export_results(self) -> None:
        """Export results to a file."""
        from PySide6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Results", "", "Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("=== PixelFlow Studio Execution Results ===\n\n")
                    
                    # Write log
                    f.write("=== Log ===\n")
                    f.write(self.log_text.toPlainText())
                    f.write("\n\n")
                    
                    # Write results
                    f.write("=== Results ===\n")
                    for i in range(self.results_list.count()):
                        item = self.results_list.item(i)
                        f.write(f"{item.text()}\n")
                        
                self.add_log_message("INFO", f"Results exported to {filename}")
            except Exception as e:
                self.add_log_message("ERROR", f"Failed to export results: {e}")
                
    def show_error(self, error: str) -> None:
        """Show an error message."""
        self.add_log_message("ERROR", error)
        self.tab_widget.setCurrentIndex(0)  # Switch to log tab
        
    def show_warning(self, warning: str) -> None:
        """Show a warning message."""
        self.add_log_message("WARNING", warning)
        
    def show_info(self, info: str) -> None:
        """Show an info message."""
        self.add_log_message("INFO", info)
        
    def show_debug(self, debug: str) -> None:
        """Show a debug message."""
        self.add_log_message("DEBUG", debug) 