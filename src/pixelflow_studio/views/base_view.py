"""
Base View class for PixelFlow Studio.

This module provides a base class that all View components should inherit from,
ensuring consistent behavior and common functionality across the application.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Dict, Optional, TYPE_CHECKING

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt

from ..core.logging_config import get_logger
from ..core.constants import UI

if TYPE_CHECKING:
    from ..viewmodels.base_viewmodel import BaseViewModel


class BaseView(QWidget):
    """
    Base class for all View components in PixelFlow Studio.
    
    This class provides common functionality for all Views:
    - Logging
    - Error handling
    - Styling
    - ViewModel integration
    - Common UI patterns
    """
    
    def __init__(self, viewmodel: Optional[BaseViewModel] = None, name: str = ""):
        """
        Initialize the base View.
        
        Args:
            viewmodel: Optional ViewModel for this View
            name: Name of this View for logging
        """
        super().__init__()
        
        self.viewmodel = viewmodel
        self.name = name or self.__class__.__name__
        self.logger = get_logger(f"view.{self.name}")
        
        # State management
        self._is_initialized = False
        self._is_visible = False
        
        self.logger.info(f"Initializing {self.name} View")
        
        # Setup the View
        self._setup_view()
        self._setup_connections()
        self._apply_styling()
        
        self._is_initialized = True
        self.logger.info(f"{self.name} View initialized successfully")
    
    @abstractmethod
    def _setup_view(self) -> None:
        """
        Setup the View-specific UI components.
        
        This method should be implemented by subclasses to create
        their specific UI components, layouts, etc.
        """
        pass
    
    def _setup_connections(self) -> None:
        """
        Setup signal connections between View and ViewModel.
        
        This method can be overridden by subclasses to set up
        specific signal connections.
        """
        if self.viewmodel:
            # Connect common signals
            self.viewmodel.error_occurred.connect(self._on_viewmodel_error)
            self.viewmodel.state_changed.connect(self._on_viewmodel_state_changed)
            self.viewmodel.loading_started.connect(self._on_viewmodel_loading_started)
            self.viewmodel.loading_finished.connect(self._on_viewmodel_loading_finished)
    
    def _apply_styling(self) -> None:
        """
        Apply common styling to the View.
        
        This method can be overridden by subclasses to apply
        specific styling.
        """
        # Apply common styling
        self.setMinimumSize(UI.MAIN_WINDOW_MIN_WIDTH, UI.MAIN_WINDOW_MIN_HEIGHT)
        
        # Set common properties
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setWindowTitle(self.name)
    
    def _on_viewmodel_error(self, error_type: str, message: str) -> None:
        """
        Handle errors from the ViewModel.
        
        Args:
            error_type: Type of error
            message: Error message
        """
        self.logger.error(f"ViewModel error ({error_type}): {message}")
        # Subclasses can override this to show error dialogs, etc.
    
    def _on_viewmodel_state_changed(self, state_name: str, new_value: Any) -> None:
        """
        Handle state changes from the ViewModel.
        
        Args:
            state_name: Name of the state that changed
            new_value: New value of the state
        """
        self.logger.debug(f"ViewModel state changed: {state_name} = {new_value}")
        # Subclasses can override this to update UI based on state changes
    
    def _on_viewmodel_loading_started(self) -> None:
        """Handle loading started from the ViewModel."""
        self.logger.debug("ViewModel loading started")
        # Subclasses can override this to show loading indicators
    
    def _on_viewmodel_loading_finished(self) -> None:
        """Handle loading finished from the ViewModel."""
        self.logger.debug("ViewModel loading finished")
        # Subclasses can override this to hide loading indicators
    
    def showEvent(self, event) -> None:
        """Handle show events."""
        super().showEvent(event)
        if not self._is_visible:
            self._is_visible = True
            self.logger.debug(f"{self.name} View became visible")
    
    def hideEvent(self, event) -> None:
        """Handle hide events."""
        super().hideEvent(event)
        if self._is_visible:
            self._is_visible = False
            self.logger.debug(f"{self.name} View became hidden")
    
    def closeEvent(self, event) -> None:
        """Handle close events."""
        self.logger.info(f"Closing {self.name} View")
        
        # Cleanup ViewModel if it exists
        if self.viewmodel:
            self.viewmodel.cleanup()
        
        super().closeEvent(event)
    
    @property
    def is_initialized(self) -> bool:
        """Check if the View has been initialized."""
        return self._is_initialized
    
    @property
    def is_visible(self) -> bool:
        """Check if the View is currently visible."""
        return self._is_visible
    
    def get_view_info(self) -> Dict[str, Any]:
        """
        Get information about the View.
        
        Returns:
            Dictionary containing View information
        """
        return {
            "name": self.name,
            "class": self.__class__.__name__,
            "is_initialized": self._is_initialized,
            "is_visible": self._is_visible,
            "has_viewmodel": self.viewmodel is not None,
            "size": (self.width(), self.height()),
            "position": (self.x(), self.y())
        }
    
    def __str__(self) -> str:
        """String representation of the View."""
        return f"{self.__class__.__name__}(name='{self.name}')"
    
    def __repr__(self) -> str:
        """Detailed string representation of the View."""
        return (f"{self.__class__.__name__}(name='{self.name}', "
                f"initialized={self._is_initialized}, visible={self._is_visible})") 