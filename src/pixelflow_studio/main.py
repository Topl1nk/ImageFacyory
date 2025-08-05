#!/usr/bin/env python3
"""
Main entry point for PixelFlow Studio.
"""

import argparse
import sys
from pathlib import Path

from loguru import logger

from .core.application import Application
from .core.universal_logger import setup_universal_logging


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    logger.remove()
    
    log_level = "DEBUG" if verbose else "INFO"
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    logger.add(sys.stderr, format=log_format, level=log_level)


def auto_test_functionality(app) -> bool:
    """Автоматически тестирует основную функциональность после запуска."""
    logger.info("🧪 АВТОМАТИЧЕСКОЕ ТЕСТИРОВАНИЕ ФУНКЦИОНАЛЬНОСТИ...")
    
    errors = []
    
    try:
        # Тест 1: Создание ноды
        logger.info("Тест 1: Создание SolidColorNode...")
        solid_node = app.create_node("SolidColorNode")
        if solid_node:
            logger.info("✅ Создание ноды работает")
        else:
            errors.append("❌ Не удалось создать ноду")
    except Exception as e:
        errors.append(f"❌ Ошибка создания ноды: {e}")
    
    try:
        # Тест 2: Добавление в граф
        logger.info("Тест 2: Добавление в граф...")
        app.graph.add_node(solid_node)
        if solid_node.id in [n.id for n in app.graph.nodes]:
            logger.info("✅ Добавление в граф работает")
        else:
            errors.append("❌ Нода не добавилась в граф")
    except Exception as e:
        errors.append(f"❌ Ошибка добавления в граф: {e}")
    
    try:
        # Тест 3: Получение пинов
        logger.info("Тест 3: Проверка пинов...")
        input_pins = list(solid_node.input_pins.values())
        output_pins = list(solid_node.output_pins.values())
        logger.info(f"Найдено пинов: входных={len(input_pins)}, выходных={len(output_pins)}")
        if output_pins:
            logger.info("✅ Пины доступны")
        else:
            errors.append("❌ Нет выходных пинов")
    except Exception as e:
        errors.append(f"❌ Ошибка проверки пинов: {e}")
    
    # Очищаем граф после тестов - не оставляем тестовые ноды в рабочем графе
    try:
        if solid_node and solid_node.id in [n.id for n in app.graph.nodes]:
            app.graph.remove_node(solid_node)
            logger.info("🧹 Тестовая нода удалена из графа")
    except Exception as e:
        logger.warning(f"Не удалось очистить тестовую ноду: {e}")
    
    # Показать результаты
    if errors:
        logger.error("🚨 НАЙДЕНЫ ПРОБЛЕМЫ:")
        for error in errors:
            logger.error(f"  {error}")
        return False
    else:
        logger.info("✅ ВСЕ БАЗОВЫЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        return True


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="PixelFlow Studio - Professional Node-Based Image Processing"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (no GUI)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--no-auto-test",
        action="store_true",
        help="Skip automatic functionality testing"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="PixelFlow Studio 1.0.0"
    )
    
    args = parser.parse_args()
    setup_logging(args.verbose)
    
    app = Application()
    
    # Настраиваем тотальное логирование
    universal_logger = setup_universal_logging(app)
    universal_logger.log_system_state("application_started", {
        "args": vars(args),
        "headless": args.headless,
        "verbose": args.verbose
    })
    
    try:
        # Автоматическое тестирование (если не отключено)
        if not args.no_auto_test:
            universal_logger.log_system_state("auto_test_started", {})
            auto_test_functionality(app)
            universal_logger.log_system_state("auto_test_completed", {})
        
        if args.headless:
            logger.info("Starting PixelFlow Studio in headless mode")
            app.run_headless()
            return 0
        else:
            logger.info("Starting PixelFlow Studio with GUI")
            return app.run_gui()
    
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        return 0
    except Exception as e:
        logger.error(f"Application failed: {e}")
        import traceback
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        return 1
    finally:
        app.shutdown()


if __name__ == "__main__":
    sys.exit(main()) 