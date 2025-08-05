"""Color adjustment nodes."""

from PIL import Image, ImageEnhance
from ..core.types import ExecutionContext, PinType
from .base import ColorNode

class BrightnessContrastNode(ColorNode):
    def __init__(self) -> None:
        super().__init__(name="Brightness/Contrast", description="Adjust brightness and contrast", category="Color")
    
    def setup_pins(self) -> None:
        super().setup_pins()
        self.add_input_pin("brightness", PinType.FLOAT, "Brightness factor", default_value=1.0)
        self.add_input_pin("contrast", PinType.FLOAT, "Contrast factor", default_value=1.0)
    
    async def process_image(self, context: ExecutionContext) -> None:
        image = await self.validate_image_input("image")
        if image is None: return
        
        brightness = self.clamp_value(await self.get_input_value("brightness"), 0.0, 3.0)
        contrast = self.clamp_value(await self.get_input_value("contrast"), 0.0, 3.0)
        
        result = image
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(result)
            result = enhancer.enhance(brightness)
        
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(result)
            result = enhancer.enhance(contrast)
        
        await self.set_output_value("image", result)

class HSVAdjustNode(ColorNode):
    def __init__(self) -> None:
        super().__init__(name="HSV Adjust", description="Adjust HSV values", category="Color")
    
    def setup_pins(self) -> None:
        super().setup_pins()
        self.add_input_pin("saturation", PinType.FLOAT, "Saturation factor", default_value=1.0)
    
    async def process_image(self, context: ExecutionContext) -> None:
        image = await self.validate_image_input("image")
        if image is None: return
        
        saturation = self.clamp_value(await self.get_input_value("saturation"), 0.0, 3.0)
        
        if saturation != 1.0:
            enhancer = ImageEnhance.Color(image)
            result = enhancer.enhance(saturation)
        else:
            result = image
        
        await self.set_output_value("image", result) 