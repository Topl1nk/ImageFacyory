"""Transform nodes for image processing."""

from PIL import Image, ImageOps
from ..core.types import ExecutionContext, PinType
from .base import TransformNode

class ResizeNode(TransformNode):
    def __init__(self) -> None:
        super().__init__(name="Resize", description="Resize an image", category="Transform")
    
    def setup_pins(self) -> None:
        super().setup_pins()
        self.add_input_pin("width", PinType.INT, "Target width", default_value=800)
        self.add_input_pin("height", PinType.INT, "Target height", default_value=600)
    
    async def process_image(self, context: ExecutionContext) -> None:
        image = await self.validate_image_input("image")
        if image is None: return
        
        width = max(1, await self.get_input_value("width"))
        height = max(1, await self.get_input_value("height"))
        
        resized = image.resize((width, height), Image.Resampling.LANCZOS)
        await self.set_output_value("image", resized)

class RotateNode(TransformNode):
    def __init__(self) -> None:
        super().__init__(name="Rotate", description="Rotate an image", category="Transform")
    
    def setup_pins(self) -> None:
        super().setup_pins()
        self.add_input_pin("angle", PinType.FLOAT, "Rotation angle", default_value=0.0)
    
    async def process_image(self, context: ExecutionContext) -> None:
        image = await self.validate_image_input("image")
        if image is None: return
        
        angle = await self.get_input_value("angle")
        rotated = image.rotate(angle, expand=True, fillcolor=(255, 255, 255))
        await self.set_output_value("image", rotated)

class FlipNode(TransformNode):
    def __init__(self) -> None:
        super().__init__(name="Flip", description="Flip an image", category="Transform")
    
    def setup_pins(self) -> None:
        super().setup_pins()
        self.add_input_pin("horizontal", PinType.BOOL, "Flip horizontally", default_value=False)
        self.add_input_pin("vertical", PinType.BOOL, "Flip vertically", default_value=False)
    
    async def process_image(self, context: ExecutionContext) -> None:
        image = await self.validate_image_input("image")
        if image is None: return
        
        horizontal = await self.get_input_value("horizontal")
        vertical = await self.get_input_value("vertical")
        
        result = image
        if horizontal:
            result = ImageOps.mirror(result)
        if vertical:
            result = ImageOps.flip(result)
        
        await self.set_output_value("image", result) 