"""
Input/Output nodes for loading and saving images.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Dict, Any

from PIL import Image
from loguru import logger

from ..core.types import ExecutionContext, PinType
from .base import IONode


class LoadImageNode(IONode):
    """Node for loading images from files."""

    def __init__(self) -> None:
        super().__init__(
            name="Load Image",
            description="Load an image from a file path",
            category="Input/Output"
        )

    def setup_pins(self) -> None:
        """Setup pins for loading images."""
        super().setup_pins()
        self.add_input_pin("path", PinType.STRING, "File path to image", default_value="")
        self.add_output_pin("image", PinType.IMAGE, "Loaded image")
        self.add_output_pin("width", PinType.INT, "Image width")
        self.add_output_pin("height", PinType.INT, "Image height")
        self.add_output_pin("filename", PinType.STRING, "Filename without path")

    async def process_image(self, context: ExecutionContext) -> None:
        """Load the image from the specified path."""
        file_path = await self.get_input_value("path")
        
        if not file_path:
            logger.warning("No file path provided to LoadImageNode")
            return

        file_path = str(file_path).strip()
        if not file_path:
            logger.warning("Empty file path provided to LoadImageNode")
            return

        try:
            # Resolve the path
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            if not path.is_file():
                raise ValueError(f"Path is not a file: {file_path}")

            # Report progress
            await self.report_progress(context, 0.2)

            # Load the image
            logger.info(f"Loading image: {file_path}")
            image = Image.open(path)

            # Convert to RGB if needed (removes alpha channel complications)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparency
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if 'A' in image.mode else None)
                image = background

            await self.report_progress(context, 0.8)

            # Set outputs
            await self.set_output_value("image", image)
            await self.set_output_value("width", image.width)
            await self.set_output_value("height", image.height)
            await self.set_output_value("filename", path.name)

            await self.report_progress(context, 1.0)
            logger.info(f"Successfully loaded image: {image.width}x{image.height}")

        except Exception as e:
            logger.error(f"Failed to load image '{file_path}': {e}")
            raise


class SaveImageNode(IONode):
    """Node for saving images to files."""

    def __init__(self) -> None:
        super().__init__(
            name="Save Image",
            description="Save an image to a file path",
            category="Input/Output"
        )

    def setup_pins(self) -> None:
        """Setup pins for saving images."""
        super().setup_pins()
        self.add_input_pin("image", PinType.IMAGE, "Image to save")
        self.add_input_pin("path", PinType.STRING, "File path to save to", default_value="output.png")
        self.add_input_pin("quality", PinType.INT, "JPEG quality (1-100)", default_value=95)
        self.add_input_pin("format", PinType.STRING, "Image format (PNG, JPEG, etc.)", default_value="PNG")
        self.add_output_pin("success", PinType.BOOL, "True if saved successfully")
        self.add_output_pin("saved_path", PinType.STRING, "Actual path where file was saved")

    async def process_image(self, context: ExecutionContext) -> None:
        """Save the image to the specified path."""
        image = await self.validate_image_input("image")
        if image is None:
            logger.warning("No image provided to SaveImageNode")
            await self.set_output_value("success", False)
            return

        file_path = await self.get_input_value("path")
        quality = await self.get_input_value("quality")
        format_str = await self.get_input_value("format")

        if not file_path:
            logger.warning("No file path provided to SaveImageNode")
            await self.set_output_value("success", False)
            return

        try:
            # Prepare the path
            path = Path(str(file_path).strip())
            
            # Create directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)

            await self.report_progress(context, 0.2)

            # Determine format
            if format_str:
                image_format = format_str.upper()
            else:
                # Infer from extension
                ext = path.suffix.lower()
                format_map = {
                    '.png': 'PNG',
                    '.jpg': 'JPEG', 
                    '.jpeg': 'JPEG',
                    '.bmp': 'BMP',
                    '.tiff': 'TIFF',
                    '.tif': 'TIFF',
                    '.webp': 'WEBP',
                }
                image_format = format_map.get(ext, 'PNG')

            await self.report_progress(context, 0.5)

            # Prepare save parameters
            save_kwargs = {}
            if image_format == 'JPEG':
                # Convert to RGB for JPEG (no alpha channel)
                if image.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[-1])
                    image = background
                elif image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Add quality parameter
                quality = self.clamp_value(quality, 1, 100)
                save_kwargs['quality'] = int(quality)
                save_kwargs['optimize'] = True

            elif image_format == 'PNG':
                # PNG supports RGBA
                if image.mode not in ('RGB', 'RGBA', 'L', 'LA'):
                    image = image.convert('RGBA')
                save_kwargs['optimize'] = True

            await self.report_progress(context, 0.8)

            # Save the image
            logger.info(f"Saving image to: {path} (format: {image_format})")
            image.save(path, format=image_format, **save_kwargs)

            await self.set_output_value("success", True)
            await self.set_output_value("saved_path", str(path))

            await self.report_progress(context, 1.0)
            logger.info(f"Successfully saved image: {path}")

        except Exception as e:
            logger.error(f"Failed to save image to '{file_path}': {e}")
            await self.set_output_value("success", False)
            await self.set_output_value("saved_path", "")
            raise


class ImageInfoNode(IONode):
    """Node for getting information about an image."""

    def __init__(self) -> None:
        super().__init__(
            name="Image Info",
            description="Get information about an image",
            category="Input/Output"
        )

    def setup_pins(self) -> None:
        """Setup pins for image information."""
        super().setup_pins()
        self.add_input_pin("image", PinType.IMAGE, "Input image")
        self.add_output_pin("width", PinType.INT, "Image width")
        self.add_output_pin("height", PinType.INT, "Image height")
        self.add_output_pin("mode", PinType.STRING, "Color mode (RGB, RGBA, etc.)")
        self.add_output_pin("channels", PinType.INT, "Number of color channels")
        self.add_output_pin("aspect_ratio", PinType.FLOAT, "Width/Height ratio")

    async def process_image(self, context: ExecutionContext) -> None:
        """Extract information from the image."""
        image = await self.validate_image_input("image")
        if image is None:
            logger.warning("No image provided to ImageInfoNode")
            return

        try:
            # Get image properties
            width = image.width
            height = image.height
            mode = image.mode
            
            # Calculate channels
            channels = len(image.getbands())
            
            # Calculate aspect ratio
            aspect_ratio = width / height if height > 0 else 0.0

            # Set outputs
            await self.set_output_value("width", width)
            await self.set_output_value("height", height)
            await self.set_output_value("mode", mode)
            await self.set_output_value("channels", channels)
            await self.set_output_value("aspect_ratio", aspect_ratio)

            logger.debug(f"Image info: {width}x{height}, mode={mode}, channels={channels}")

        except Exception as e:
            logger.error(f"Failed to get image info: {e}")
            raise


class ImagePreviewNode(IONode):
    """Node for displaying image preview directly in the node editor."""

    def __init__(self) -> None:
        super().__init__(
            name="Image Preview",
            description="Display an image preview directly in the node",
            category="Input/Output"
        )
        self._preview_image: Optional[Image.Image] = None

    def setup_pins(self) -> None:
        """Setup pins for image preview."""
        super().setup_pins()
        self.add_input_pin("image", PinType.IMAGE, "Image to preview")
        # Опциональный выход для проброса изображения дальше
        self.add_output_pin("image", PinType.IMAGE, "Passthrough image")

    async def process_image(self, context: ExecutionContext) -> None:
        """Process and store the image for preview."""
        image = await self.validate_image_input("image")
        
        if image is None:
            logger.warning("No image provided to ImagePreviewNode")
            self._preview_image = None
            # Обновляем графический элемент при отсутствии изображения
            self._notify_graphics_update()
            return

        try:
            # Сохраняем изображение для preview
            self._preview_image = image.copy()
            
            # Пробрасываем изображение на выход (passthrough)
            await self.set_output_value("image", image)
            
            # Обновляем графический элемент
            self._notify_graphics_update()
            
            logger.debug(f"Preview updated: {image.width}x{image.height}")

        except Exception as e:
            logger.error(f"Failed to process image in preview node: {e}")
            self._preview_image = None
            self._notify_graphics_update()
            raise
    
    def _notify_graphics_update(self) -> None:
        """Уведомляет графический элемент об обновлении превью."""
        # Этот метод будет вызван из контекста выполнения нод
        # Графический элемент должен сам проверять изменения при обновлении
        pass

    def get_preview_image(self) -> Optional[Image.Image]:
        """Get the current preview image."""
        return self._preview_image

    def has_preview_image(self) -> bool:
        """Check if there's an image to preview."""
        return self._preview_image is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize node to dictionary, excluding the preview image."""
        # Получаем базовую сериализацию
        data = super().to_dict()
        
        # НЕ сохраняем _preview_image - это runtime данные
        # Изображение будет восстановлено при следующем выполнении
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], node_classes: Dict[str, type]) -> 'ImagePreviewNode':
        """Deserialize node from dictionary."""
        # Создаем ноду используя базовый метод
        node = super().from_dict(data, node_classes)
        
        # Инициализируем _preview_image как None
        # Изображение будет установлено при выполнении
        node._preview_image = None
        
        return node 