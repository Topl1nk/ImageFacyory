"""
Constants for PixelFlow Studio.

This module defines all constants used throughout the application,
replacing magic numbers and strings with named constants.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class UIConstants:
    """Constants for user interface."""
    
    # Main window
    MAIN_WINDOW_MIN_WIDTH: Final[int] = 1200
    MAIN_WINDOW_MIN_HEIGHT: Final[int] = 800
    MAIN_WINDOW_DEFAULT_WIDTH: Final[int] = 1400
    MAIN_WINDOW_DEFAULT_HEIGHT: Final[int] = 900
    
    # Dock widgets
    PALETTE_MIN_WIDTH: Final[int] = 280
    PALETTE_MAX_WIDTH: Final[int] = 400
    PROPERTIES_MIN_WIDTH: Final[int] = 350
    PROPERTIES_MAX_WIDTH: Final[int] = 500
    OUTPUT_MIN_HEIGHT: Final[int] = 200
    OUTPUT_MAX_HEIGHT: Final[int] = 400
    VARIABLES_MIN_WIDTH: Final[int] = 280
    VARIABLES_MAX_WIDTH: Final[int] = 400
    
    # Splitter sizes
    SPLITTER_LEFT_SIZE: Final[int] = 300
    SPLITTER_CENTER_SIZE: Final[int] = 1000
    SPLITTER_RIGHT_SIZE: Final[int] = 300
    
    # Margins and spacing
    DEFAULT_MARGIN: Final[int] = 5
    DEFAULT_SPACING: Final[int] = 8
    GROUP_MARGIN: Final[int] = 10
    GROUP_SPACING: Final[int] = 5
    
    # Widget sizes
    BUTTON_MIN_WIDTH: Final[int] = 60
    BUTTON_MAX_WIDTH: Final[int] = 80
    SPINBOX_MIN_WIDTH: Final[int] = 80
    COPY_BUTTON_SIZE: Final[int] = 20
    
    # Status bar message duration (ms)
    STATUS_MESSAGE_DURATION: Final[int] = 3000
    STATUS_MESSAGE_LONG_DURATION: Final[int] = 5000


@dataclass(frozen=True)
class TimingConstants:
    """Constants for timing and intervals."""
    
    # Auto-save
    AUTO_SAVE_INTERVAL_MS: Final[int] = 30000  # 30 seconds
    
    # UI updates
    UI_UPDATE_DELAY_MS: Final[int] = 500
    ANIMATION_DURATION_MS: Final[int] = 200
    
    # Demo playback
    DEMO_PLAYBACK_DELAY_MS: Final[int] = 1000
    DEMO_VERIFICATION_TIMEOUT_MS: Final[int] = 10000


@dataclass(frozen=True)
class ValidationConstants:
    """Constants for validation and limits."""
    
    # Numeric limits
    SPINBOX_MAX_VALUE: Final[int] = 999999
    SPINBOX_MIN_VALUE: Final[int] = -999999
    FLOAT_SPINBOX_MAX_VALUE: Final[float] = 999999.0
    FLOAT_SPINBOX_MIN_VALUE: Final[float] = -999999.0
    
    # Precision
    FLOAT_PRECISION: Final[int] = 2
    FLOAT_STEP: Final[float] = 1.0
    FLOAT_STEP_SMALL: Final[float] = 0.1
    
    # String limits
    MAX_STRING_LENGTH: Final[int] = 255
    MAX_DESCRIPTION_LENGTH: Final[int] = 1000
    
    # Image limits
    MAX_IMAGE_SIZE: Final[int] = 8192  # 8K
    MIN_IMAGE_SIZE: Final[int] = 1
    
    # Brightness/Contrast ranges
    BRIGHTNESS_MIN: Final[float] = 0.0
    BRIGHTNESS_MAX: Final[float] = 3.0
    BRIGHTNESS_DEFAULT: Final[float] = 1.0
    BRIGHTNESS_STEP: Final[float] = 0.1
    
    CONTRAST_MIN: Final[float] = 0.0
    CONTRAST_MAX: Final[float] = 3.0
    CONTRAST_DEFAULT: Final[float] = 1.0
    CONTRAST_STEP: Final[float] = 0.1


@dataclass(frozen=True)
class ColorConstants:
    """Constants for colors and styling."""
    
    # Primary colors
    PRIMARY_COLOR: Final[str] = "#0078d4"
    PRIMARY_DARK_COLOR: Final[str] = "#005f99"
    SUCCESS_COLOR: Final[str] = "#4CAF50"
    SUCCESS_DARK_COLOR: Final[str] = "#45a049"
    SUCCESS_LIGHT_COLOR: Final[str] = "#3d8b40"
    ERROR_COLOR: Final[str] = "#f44336"
    ERROR_DARK_COLOR: Final[str] = "#da190b"
    ERROR_LIGHT_COLOR: Final[str] = "#c12719"
    WARNING_COLOR: Final[str] = "#FF9800"
    
    # UI colors
    BACKGROUND_COLOR: Final[str] = "#383838"
    BACKGROUND_LIGHT_COLOR: Final[str] = "#404040"
    BORDER_COLOR: Final[str] = "#555"
    TEXT_COLOR: Final[str] = "#ffffff"
    TEXT_SECONDARY_COLOR: Final[str] = "#888888"
    TEXT_MUTED_COLOR: Final[str] = "#666666"
    
    # Pin type colors
    PIN_EXEC_COLOR: Final[str] = "#ffffff"
    PIN_BOOL_COLOR: Final[str] = "#dc3030"
    PIN_INT_COLOR: Final[str] = "#30dc30"
    PIN_FLOAT_COLOR: Final[str] = "#3030dc"
    PIN_STRING_COLOR: Final[str] = "#dc30dc"
    PIN_PATH_COLOR: Final[str] = "#8b4513"
    PIN_IMAGE_COLOR: Final[str] = "#ffa500"
    PIN_COLOR_COLOR: Final[str] = "#ffff00"
    PIN_VECTOR2_COLOR: Final[str] = "#ff8000"
    PIN_VECTOR3_COLOR: Final[str] = "#80ff80"
    PIN_MATRIX_COLOR: Final[str] = "#8080ff"
    PIN_ARRAY_COLOR: Final[str] = "#c0c0c0"
    PIN_DICT_COLOR: Final[str] = "#40e0d0"
    PIN_ANY_COLOR: Final[str] = "#808080"


@dataclass(frozen=True)
class FileConstants:
    """Constants for file operations."""
    
    # File extensions
    PROJECT_EXTENSION: Final[str] = ".pfp"
    IMAGE_EXTENSIONS: Final[tuple] = (".png", ".jpg", ".jpeg", ".bmp", ".tiff")
    DEMO_EXTENSION: Final[str] = ".demo"
    
    # File size limits
    MAX_PROJECT_SIZE_MB: Final[int] = 100
    MAX_IMAGE_SIZE_MB: Final[int] = 50
    
    # Default paths
    DEFAULT_SAVE_DIR: Final[str] = "saves"
    DEFAULT_EXPORT_DIR: Final[str] = "exports"
    DEFAULT_DEMO_DIR: Final[str] = "demos"


@dataclass(frozen=True)
class NodeConstants:
    """Constants for node operations."""
    
    # Node creation
    DEFAULT_NODE_POSITION_X: Final[int] = 0
    DEFAULT_NODE_POSITION_Y: Final[int] = 0
    NODE_SPACING: Final[int] = 50
    
    # Pin limits
    MAX_PINS_PER_NODE: Final[int] = 20
    MAX_CONNECTIONS_PER_PIN: Final[int] = 10
    
    # Execution
    MAX_EXECUTION_TIME_SEC: Final[int] = 300  # 5 minutes
    EXECUTION_TIMEOUT_SEC: Final[int] = 60
    
    # Graph limits
    MAX_NODES_PER_GRAPH: Final[int] = 1000
    MAX_CONNECTIONS_PER_GRAPH: Final[int] = 2000


# Global instances
UI = UIConstants()
TIMING = TimingConstants()
VALIDATION = ValidationConstants()
COLORS = ColorConstants()
FILES = FileConstants()
NODES = NodeConstants() 