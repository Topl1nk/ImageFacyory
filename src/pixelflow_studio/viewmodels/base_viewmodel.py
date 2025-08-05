"""
Base ViewModel class for PixelFlow Studio.

This module provides a base class that all ViewModels should inherit from,
ensuring consistent behavior and common functionality across the application.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Dict, TYPE_CHECKING

from PySide6.QtCore import QObject, Signal

from ..core.logging_config import get_logger

if TYPE_CHECKING:
    from ..core.application import Application


class BaseViewModel(QObject):
    """
    Base class for all ViewModels in PixelFlow Studio.
    
    This class provides common functionality for all ViewModels:
    - Logging
    - Error handling
    - State management
    - Signal management
    - Application reference
    """
    
    # Common signals that all ViewModels might need
    error_occurred = Signal(str, str)  # error_type, message
    state_changed = Signal(str, object)  # state_name, new_value
    loading_started = Signal()
    loading_finished = Signal()
    
    def __init__(self, app: Application, name: str):
        """
        Initialize the base ViewModel.
        
        Args:
            app: Reference to the main application
            name: Name of this ViewModel for logging
        """
        super().__init__()
        
        self.app = app
        self.name = name
        self.logger = get_logger(f"viewmodel.{name}")
        
        # State management
        self._state: Dict[str, Any] = {}
        self._is_loading = False
        self._is_initialized = False
        
        self.logger.info(f"Initializing {name} ViewModel")
        
        # Initialize the ViewModel
        self._initialize()
        self._is_initialized = True
        
        self.logger.info(f"{name} ViewModel initialized successfully")
    
    @abstractmethod
    def _initialize(self) -> None:
        """
        Initialize the ViewModel-specific functionality.
        
        This method should be implemented by subclasses to set up
        their specific functionality, signal connections, etc.
        """
        pass
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the ViewModel's state.
        
        Args:
            key: State key
            default: Default value if key doesn't exist
            
        Returns:
            State value or default
        """
        return self._state.get(key, default)
    
    def set_state(self, key: str, value: Any) -> None:
        """
        Set a value in the ViewModel's state.
        
        Args:
            key: State key
            value: New value
        """
        old_value = self._state.get(key)
        self._state[key] = value
        
        # Emit state changed signal if value actually changed
        if old_value != value:
            self.state_changed.emit(key, value)
            self.logger.debug(f"State changed: {key} = {value}")
    
    def update_state(self, updates: Dict[str, Any]) -> None:
        """
        Update multiple state values at once.
        
        Args:
            updates: Dictionary of state updates
        """
        for key, value in updates.items():
            self.set_state(key, value)
    
    @property
    def is_loading(self) -> bool:
        """Check if the ViewModel is in loading state."""
        return self._is_loading
    
    @property
    def is_initialized(self) -> bool:
        """Check if the ViewModel has been initialized."""
        return self._is_initialized
    
    def set_loading(self, loading: bool) -> None:
        """
        Set the loading state.
        
        Args:
            loading: Whether the ViewModel is loading
        """
        if self._is_loading != loading:
            self._is_loading = loading
            if loading:
                self.loading_started.emit()
                self.logger.debug("Loading started")
            else:
                self.loading_finished.emit()
                self.logger.debug("Loading finished")
    
    def handle_error(self, error: Exception, context: str = "") -> None:
        """
        Handle errors in a consistent way.
        
        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
        """
        error_message = str(error)
        error_type = type(error).__name__
        
        self.logger.error(f"Error in {self.name}: {error_message}")
        if context:
            self.logger.error(f"Context: {context}")
        
        # Emit error signal
        self.error_occurred.emit(error_type, error_message)
    
    def cleanup(self) -> None:
        """
        Clean up resources used by the ViewModel.
        
        This method should be called when the ViewModel is no longer needed.
        """
        self.logger.info(f"Cleaning up {self.name} ViewModel")
        
        # Disconnect all signals
        try:
            self.disconnect()
        except Exception as e:
            self.logger.warning(f"Error disconnecting signals: {e}")
        
        # Clear state
        self._state.clear()
        
        self.logger.info(f"{self.name} ViewModel cleanup completed")
    
    def validate_state(self) -> bool:
        """
        Validate the current state of the ViewModel.
        
        Returns:
            True if state is valid, False otherwise
        """
        # Base implementation - always valid
        # Subclasses should override this method
        return True
    
    def get_state_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current state.
        
        Returns:
            Dictionary containing state summary
        """
        return {
            "name": self.name,
            "is_loading": self._is_loading,
            "is_initialized": self._is_initialized,
            "state_keys": list(self._state.keys()),
            "state_count": len(self._state)
        }
    
    def __str__(self) -> str:
        """String representation of the ViewModel."""
        return f"{self.__class__.__name__}(name='{self.name}')"
    
    def __repr__(self) -> str:
        """Detailed string representation of the ViewModel."""
        return (f"{self.__class__.__name__}(name='{self.name}', "
                f"loading={self._is_loading}, "
                f"initialized={self._is_initialized})") 