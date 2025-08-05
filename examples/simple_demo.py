#!/usr/bin/env python3
"""
Simple demo of PixelFlow Studio node system.

This demo creates a simple graph:
SolidColor -> Blur -> Save

It demonstrates the core functionality without GUI.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from pixelflow_studio.core.application import Application
from pixelflow_studio.core.types import Position
from loguru import logger


async def main():
    """Run the simple demo."""
    logger.info("🚀 Starting PixelFlow Studio Demo")
    
    # Create application
    app = Application()
    
    logger.info("📊 Application Statistics:")
    stats = app.get_stats()
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")
    
    # Show available node types
    logger.info("\n🧩 Available Node Types:")
    categories = app.get_node_categories()
    for category, nodes in categories.items():
        logger.info(f"  📁 {category}:")
        for node_info in nodes:
            logger.info(f"    - {node_info['name']}: {node_info['description']}")
    
    try:
        # Create nodes
        logger.info("\n🏗️  Building Node Graph...")
        
        # Create a solid color generator
        color_node = app.create_node("SolidColorNode")
        color_node.position = Position(0, 0)
        app.graph.add_node(color_node)
        
        # Set color to a nice blue
        color_node.get_input_pin("red")._cached_value = 100
        color_node.get_input_pin("green")._cached_value = 150
        color_node.get_input_pin("blue")._cached_value = 255
        color_node.get_input_pin("width")._cached_value = 800
        color_node.get_input_pin("height")._cached_value = 600
        
        # Create a blur filter
        blur_node = app.create_node("BlurNode")
        blur_node.position = Position(200, 0)
        app.graph.add_node(blur_node)
        
        # Set blur radius
        blur_node.get_input_pin("radius")._cached_value = 5.0
        
        # Create a save node
        save_node = app.create_node("SaveImageNode")
        save_node.position = Position(400, 0)
        app.graph.add_node(save_node)
        
        # Set output path
        output_path = project_root / "demo_output.png"
        save_node.get_input_pin("path")._cached_value = str(output_path)
        
        # Connect the nodes
        logger.info("🔗 Connecting Nodes...")
        
        # Connect solid color -> blur
        color_output = color_node.get_output_pin("image")
        blur_input = blur_node.get_input_pin("image")
        app.graph.connect_pins(color_output, blur_input)
        
        # Connect blur -> save
        blur_output = blur_node.get_output_pin("image")
        save_input = save_node.get_input_pin("image")
        app.graph.connect_pins(blur_output, save_input)
        
        # Show graph statistics
        logger.info("\n📈 Graph Statistics:")
        graph_stats = app.graph.get_stats()
        for key, value in graph_stats.items():
            logger.info(f"  {key}: {value}")
        
        # Validate the graph
        logger.info("\n✅ Validating Graph...")
        validation_result = app.graph.validate()
        if validation_result.is_valid:
            logger.info("  ✅ Graph is valid!")
        else:
            logger.error("  ❌ Graph validation failed:")
            for error in validation_result.errors:
                logger.error(f"    - {error.message}")
            return
        
        if validation_result.warnings:
            logger.warning("  ⚠️  Warnings:")
            for warning in validation_result.warnings:
                logger.warning(f"    - {warning.message}")
        
        # Execute the graph
        logger.info("\n⚡ Executing Graph...")
        
        def on_progress(progress: float):
            percent = int(progress * 100)
            logger.info(f"  Progress: {percent}%")
        
        # Connect progress signal
        app.graph.execution_progress.connect(on_progress)
        
        # Execute
        await app.graph.execute_all()
        
        logger.info(f"✅ Graph execution completed!")
        logger.info(f"📁 Output saved to: {output_path}")
        
        # Check if file was created
        if output_path.exists():
            size = output_path.stat().st_size
            logger.info(f"📏 File size: {size} bytes")
        else:
            logger.error("❌ Output file was not created")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        raise
    finally:
        app.shutdown()
    
    logger.info("\n🎉 Demo completed successfully!")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main()) 