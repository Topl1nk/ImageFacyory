#!/usr/bin/env python3
"""
Демонстрация улучшенного GUI PixelFlow Studio.

Этот скрипт запускает графический интерфейс с предзагруженными нодами
для демонстрации возможностей системы.
"""

import sys
import os
from pathlib import Path

# Добавляем путь к исходному коду
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pixelflow_studio.core.application import Application
from pixelflow_studio.core.types import Position
from pixelflow_studio.core.graph import Graph
from loguru import logger


def create_demo_graph(app: Application) -> None:
    """Создает демонстрационный граф с несколькими нодами."""
    try:
        # Создаем ноды
        solid_color_node = app.create_node("SolidColorNode")
        solid_color_node.position = Position(100, 100)
        app.graph.add_node(solid_color_node)
        
        blur_node = app.create_node("BlurNode")
        blur_node.position = Position(350, 100)
        app.graph.add_node(blur_node)
        
        brightness_node = app.create_node("BrightnessContrastNode")
        brightness_node.position = Position(600, 100)
        app.graph.add_node(brightness_node)
        
        save_node = app.create_node("SaveImageNode")
        save_node.position = Position(850, 100)
        app.graph.add_node(save_node)
        
        # Создаем соединения
        app.graph.connect_pins(
            solid_color_node.get_output_pin("image"),
            blur_node.get_input_pin("image")
        )
        app.graph.connect_pins(
            blur_node.get_output_pin("image"),
            brightness_node.get_input_pin("image")
        )
        app.graph.connect_pins(
            brightness_node.get_output_pin("image"),
            save_node.get_input_pin("image")
        )
        
        # Устанавливаем параметры
        solid_color_node.get_input_pin("red")._cached_value = 100
        solid_color_node.get_input_pin("green")._cached_value = 150
        solid_color_node.get_input_pin("blue")._cached_value = 255
        solid_color_node.get_input_pin("width")._cached_value = 800
        solid_color_node.get_input_pin("height")._cached_value = 600
        
        blur_node.get_input_pin("radius")._cached_value = 5.0
        
        brightness_node.get_input_pin("brightness")._cached_value = 0.2
        brightness_node.get_input_pin("contrast")._cached_value = 1.1
        
        save_node.get_input_pin("path")._cached_value = "demo_output.png"
        
        logger.info("Демонстрационный граф создан успешно!")
        logger.info("Попробуйте:")
        logger.info("- Правый клик на канвасе для добавления нод")
        logger.info("- Ctrl+колесико для зума")
        logger.info("- Перетаскивание нод")
        logger.info("- Соединение сокетов")
        
    except Exception as e:
        logger.error(f"Ошибка при создании демо графа: {e}")


def main():
    """Главная функция демонстрации."""
    logger.info("Запуск демонстрации PixelFlow Studio GUI")
    
    # Создаем приложение
    app = Application()
    
    try:
        # Создаем демонстрационный граф
        create_demo_graph(app)
        
        # Запускаем GUI
        logger.info("Запуск графического интерфейса...")
        return app.run_gui()
        
    except KeyboardInterrupt:
        logger.info("Демонстрация прервана пользователем")
    except Exception as e:
        logger.error(f"Ошибка в демонстрации: {e}")
        return 1
    finally:
        app.shutdown()
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 