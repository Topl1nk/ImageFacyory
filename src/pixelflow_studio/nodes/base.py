"""
Base classes for image processing nodes.

This module provides base classes that image processing nodes can inherit from
to get common functionality and patterns.
"""

from __future__ import annotations

import asyncio
from abc import abstractmethod
from typing import Optional

import numpy as np
from PIL import Image

from ..core.node import Node
from ..core.types import ExecutionContext, PinType


class ImageProcessingNode(Node):
    """
    Base class for nodes that process images.
    
    This class provides common functionality for image processing nodes:
    - Execution pin handling
    - Progress reporting
    - Error handling for image operations
    """

    def __init__(
        self,
        name: str = "Image Node",
        description: str = "",
        category: str = "Image Processing",
    ) -> None:
        super().__init__(name, description, category)

    def setup_pins(self) -> None:
        """Default pin setup - can be overridden by subclasses."""
        # Most image processing nodes have these basic pins
        self.add_input_pin("exec", PinType.EXEC, "Execute this node")
        self.add_output_pin("exec", PinType.EXEC, "Execution output")

    async def execute(self, context: ExecutionContext) -> None:
        """
        Execute the image processing logic.
        
        This method handles the execution pin flow and calls process_image
        which should be implemented by subclasses.
        """
        try:
            # Check if we have an execution input connection
            exec_pin = self.get_input_pin("exec")
            if exec_pin and len(exec_pin.connections) > 0:
                # Wait for execution signal
                await self.get_input_value("exec")

            # Process the image
            await self.process_image(context)

            # Signal execution completion
            exec_output = self.get_output_pin("exec")
            if exec_output:
                await self.set_output_value("exec", True)

        except Exception as e:
            # Re-raise with context
            raise RuntimeError(f"Error in {self.name}: {e}") from e

    @abstractmethod
    async def process_image(self, context: ExecutionContext) -> None:
        """
        Process the image - must be implemented by subclasses.
        
        Args:
            context: Execution context for progress tracking and cancellation
        """
        pass

    async def validate_image_input(self, pin_name: str) -> Optional[Image.Image]:
        """
        Validate and get an image input.
        
        Args:
            pin_name: Name of the input pin containing the image
            
        Returns:
            PIL Image or None if not valid
            
        Raises:
            ValueError: If the input is not a valid image
        """
        image = await self.get_input_value(pin_name)
        
        if image is None:
            return None
            
        if not isinstance(image, Image.Image):
            raise ValueError(f"Input '{pin_name}' must be a PIL Image, got {type(image)}")
            
        return image

    def clamp_value(self, value: float, min_val: float, max_val: float) -> float:
        """Clamp a value between min and max."""
        return max(min_val, min(max_val, value))

    def ensure_rgb(self, image: Image.Image) -> Image.Image:
        """Ensure image is in RGB mode."""
        if image.mode != 'RGB':
            return image.convert('RGB')
        return image

    def ensure_rgba(self, image: Image.Image) -> Image.Image:
        """Ensure image is in RGBA mode."""
        if image.mode != 'RGBA':
            return image.convert('RGBA')
        return image

    def pil_to_numpy(self, image: Image.Image) -> np.ndarray:
        """Convert PIL image to numpy array."""
        return np.array(image)

    def numpy_to_pil(self, array: np.ndarray) -> Image.Image:
        """Convert numpy array to PIL image."""
        # Ensure the array is in the right format
        if array.dtype != np.uint8:
            array = np.clip(array, 0, 255).astype(np.uint8)
        return Image.fromarray(array)

    async def report_progress(self, context: ExecutionContext, progress: float) -> None:
        """Report progress and check for cancellation."""
        context.set_progress(progress)
        
        # Yield control to allow cancellation
        await asyncio.sleep(0)
        
        if context.is_cancelled:
            raise asyncio.CancelledError("Operation was cancelled")


class FilterNode(ImageProcessingNode):
    """Base class for filter nodes that modify images."""

    def __init__(
        self,
        name: str = "Filter",
        description: str = "",
        category: str = "Filter",
    ) -> None:
        super().__init__(name, description, category)

    def setup_pins(self) -> None:
        """Setup common filter pins."""
        super().setup_pins()
        self.add_input_pin("image", PinType.IMAGE, "Input image")
        self.add_output_pin("image", PinType.IMAGE, "Filtered image")


class TransformNode(ImageProcessingNode):
    """Base class for nodes that transform images (resize, rotate, etc.)."""

    def __init__(
        self,
        name: str = "Transform",
        description: str = "",
        category: str = "Transform",
    ) -> None:
        super().__init__(name, description, category)

    def setup_pins(self) -> None:
        """Setup common transform pins."""
        super().setup_pins()
        self.add_input_pin("image", PinType.IMAGE, "Input image")
        self.add_output_pin("image", PinType.IMAGE, "Transformed image")


class ColorNode(ImageProcessingNode):
    """Base class for nodes that adjust image colors."""

    def __init__(
        self,
        name: str = "Color",
        description: str = "",
        category: str = "Color",
    ) -> None:
        super().__init__(name, description, category)

    def setup_pins(self) -> None:
        """Setup common color adjustment pins."""
        super().setup_pins()
        self.add_input_pin("image", PinType.IMAGE, "Input image")
        self.add_output_pin("image", PinType.IMAGE, "Color-adjusted image")


class GeneratorNode(ImageProcessingNode):
    """Base class for nodes that generate images."""

    def __init__(
        self,
        name: str = "Generator",
        description: str = "",
        category: str = "Generator",
    ) -> None:
        super().__init__(name, description, category)

    def setup_pins(self) -> None:
        """Setup common generator pins."""
        super().setup_pins()
        # Generators typically don't have image inputs
        self.add_output_pin("image", PinType.IMAGE, "Generated image")


class IONode(ImageProcessingNode):
    """Base class for input/output nodes."""

    def __init__(
        self,
        name: str = "I/O",
        description: str = "",
        category: str = "Input/Output",
    ) -> None:
        super().__init__(name, description, category) 