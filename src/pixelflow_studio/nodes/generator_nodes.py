"""Generator nodes for creating images."""

import numpy as np
from PIL import Image
from ..core.types import ExecutionContext, PinType
from .base import GeneratorNode

class SolidColorNode(GeneratorNode):
    def __init__(self) -> None:
        super().__init__(name="Solid Color", description="Generate solid color image", category="Generator")
    
    def setup_pins(self) -> None:
        super().setup_pins()
        self.add_input_pin("width", PinType.INT, "Image width", default_value=512)
        self.add_input_pin("height", PinType.INT, "Image height", default_value=512)
        self.add_input_pin("red", PinType.INT, "Red component (0-255)", default_value=255)
        self.add_input_pin("green", PinType.INT, "Green component (0-255)", default_value=255)
        self.add_input_pin("blue", PinType.INT, "Blue component (0-255)", default_value=255)
    
    async def process_image(self, context: ExecutionContext) -> None:
        width = max(1, await self.get_input_value("width"))
        height = max(1, await self.get_input_value("height"))
        red = self.clamp_value(await self.get_input_value("red"), 0, 255)
        green = self.clamp_value(await self.get_input_value("green"), 0, 255)
        blue = self.clamp_value(await self.get_input_value("blue"), 0, 255)
        
        color = (int(red), int(green), int(blue))
        image = Image.new('RGB', (width, height), color)
        await self.set_output_value("image", image)

class NoiseNode(GeneratorNode):
    def __init__(self) -> None:
        super().__init__(name="Noise", description="Generate random noise", category="Generator")
    
    def setup_pins(self) -> None:
        super().setup_pins()
        self.add_input_pin("width", PinType.INT, "Image width", default_value=512)
        self.add_input_pin("height", PinType.INT, "Image height", default_value=512)
        self.add_input_pin("seed", PinType.INT, "Random seed", default_value=42)
    
    async def process_image(self, context: ExecutionContext) -> None:
        width = max(1, await self.get_input_value("width"))
        height = max(1, await self.get_input_value("height"))
        seed = await self.get_input_value("seed")
        
        np.random.seed(seed)
        noise_array = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        image = Image.fromarray(noise_array)
        await self.set_output_value("image", image) 