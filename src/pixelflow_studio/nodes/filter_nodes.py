"""
Filter nodes for image processing.
"""

from __future__ import annotations

from PIL import Image, ImageFilter

from ..core.types import ExecutionContext, PinType
from .base import FilterNode


class BlurNode(FilterNode):
    """Node for applying Gaussian blur to images."""

    def __init__(self) -> None:
        super().__init__(
            name="Blur",
            description="Apply Gaussian blur to an image",
            category="Filter"
        )

    def setup_pins(self) -> None:
        """Setup blur-specific pins."""
        super().setup_pins()
        self.add_input_pin("radius", PinType.FLOAT, "Blur radius", default_value=2.0)

    async def process_image(self, context: ExecutionContext) -> None:
        """Apply blur filter to the image."""
        image = await self.validate_image_input("image")
        if image is None:
            return

        radius = await self.get_input_value("radius")
        radius = self.clamp_value(radius, 0.0, 50.0)

        try:
            await self.report_progress(context, 0.3)
            
            # Apply Gaussian blur
            blurred_image = image.filter(ImageFilter.GaussianBlur(radius=radius))
            
            await self.report_progress(context, 0.8)
            await self.set_output_value("image", blurred_image)
            await self.report_progress(context, 1.0)
            
        except Exception as e:
            raise RuntimeError(f"Failed to apply blur: {e}") from e


class SharpenNode(FilterNode):
    """Node for sharpening images."""

    def __init__(self) -> None:
        super().__init__(
            name="Sharpen",
            description="Sharpen an image",
            category="Filter"
        )

    def setup_pins(self) -> None:
        """Setup sharpen-specific pins."""
        super().setup_pins()
        self.add_input_pin("strength", PinType.FLOAT, "Sharpen strength", default_value=1.0)

    async def process_image(self, context: ExecutionContext) -> None:
        """Apply sharpen filter to the image."""
        image = await self.validate_image_input("image")
        if image is None:
            return

        strength = await self.get_input_value("strength")
        strength = self.clamp_value(strength, 0.0, 5.0)

        try:
            await self.report_progress(context, 0.3)
            
            if strength == 0:
                # No sharpening
                result = image
            else:
                # Apply sharpening filter
                sharpened = image.filter(ImageFilter.SHARPEN)
                
                # Blend with original based on strength
                if strength >= 1.0:
                    result = sharpened
                else:
                    result = Image.blend(image, sharpened, strength)
            
            await self.report_progress(context, 0.8)
            await self.set_output_value("image", result)
            await self.report_progress(context, 1.0)
            
        except Exception as e:
            raise RuntimeError(f"Failed to apply sharpen: {e}") from e 