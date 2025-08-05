"""
PixelFlow Studio - Professional Node-Based Image Processing Studio.

A modern, extensible image processing application built with PySide6,
following MVVM architecture and best practices.
"""

__version__ = "1.0.0"
__author__ = "PixelFlow Team"
__email__ = "team@pixelflow.studio"

from loguru import logger
import sys

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

# Export key classes for easy importing
from .core.types import PinType, ConnectionType
from .core.node import Node
from .core.graph import Graph
from .core.application import Application

__all__ = [
    "__version__",
    "__author__", 
    "__email__",
    "PinType",
    "ConnectionType", 
    "Node",
    "Graph",
    "Application",
] 