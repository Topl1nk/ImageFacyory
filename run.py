#!/usr/bin/env python3
"""
ЕДИНСТВЕННЫЙ ФАЙЛ ДЛЯ ЗАПУСКА PIXELFLOW STUDIO
Автоматически проверяет зависимости и запускает приложение с тестированием.
"""

import subprocess
import sys
import importlib.util
from pathlib import Path

def check_and_install_dependencies():
    """Проверяет и при необходимости устанавливает зависимости."""
    required_packages = {
        'PySide6': 'PySide6',
        'PIL': 'Pillow',
        'numpy': 'numpy',
        'loguru': 'loguru'
    }
    
    missing = []
    for module_name, package_name in required_packages.items():
        if importlib.util.find_spec(module_name) is None:
            missing.append(package_name)
    
    if missing:
        print(f"📦 Устанавливаю недостающие зависимости: {', '.join(missing)}")
        for package in missing:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", package], 
                             check=True, capture_output=True)
                print(f"✅ {package} установлен")
            except subprocess.CalledProcessError as e:
                print(f"❌ Ошибка установки {package}: {e}")
                return False
    
    return True

def main():
    """Главная функция запуска."""
    import argparse
    
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(
        description="PixelFlow Studio - Node-based Image Processing",
        epilog="Examples:\n"
               "  python run.py                           # Start GUI\n"
               "  python run.py -pr project.pfp -ex       # Execute project without GUI\n"
               "  python run.py -pr project.pfp -an       # Analyze project structure\n"
               "  python run.py -pr project.pfp -ex -v    # Execute with verbose output\n"
               "  python run.py --project project.pfp --execute  # Long form\n"
               "  python run.py --help                    # Show help",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Основной файл проекта
    parser.add_argument('-pr', '--project', metavar='FILE', 
                       help='Project file (.pfp) to process')
    
    # Действия
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument('-ex', '--execute', action='store_true',
                             help='Execute the project')
    action_group.add_argument('-an', '--analyze', action='store_true',
                             help='Analyze project structure')
    
    # Дополнительные опции
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output (for CLI mode)')
    
    # Устаревшие параметры (для совместимости)
    parser.add_argument('--old-execute', metavar='PROJECT', dest='old_execute',
                       help=argparse.SUPPRESS)  # Скрываем из help
    parser.add_argument('--old-analyze', metavar='PROJECT', dest='old_analyze', 
                       help=argparse.SUPPRESS)  # Скрываем из help
    
    args = parser.parse_args()
    
    print("🚀 PIXELFLOW STUDIO LAUNCHER")
    print("=" * 40)
    
    # Проверка зависимостей
    if not check_and_install_dependencies():
        print("❌ Не удалось установить зависимости!")
        return 1
    
    # Определяем режим работы
    cli_mode = False
    project_file = None
    action = None
    
    # Новый формат: -pr project.pfp -ex/-an
    if args.project:
        project_file = args.project
        if args.execute:
            action = "execute"
            cli_mode = True
        elif args.analyze:
            action = "analyze"
            cli_mode = True
        else:
            print("❌ Укажите действие: -ex (execute) или -an (analyze)")
            return 1
    
    # Поддержка старого формата для совместимости
    elif args.old_execute:
        project_file = args.old_execute
        action = "execute"
        cli_mode = True
    elif args.old_analyze:
        project_file = args.old_analyze
        action = "analyze"
        cli_mode = True
    
    # CLI режим
    if cli_mode:
        cli_file = Path("src/pixelflow_studio/cli_executor.py")
        if not cli_file.exists():
            print(f"❌ CLI executor not found: {cli_file}")
            return 1
        
        # Выполнить CLI команду
        cli_args = [sys.executable, str(cli_file)]
        
        if action == "execute":
            cli_args.extend(["--execute", project_file])
        elif action == "analyze":
            cli_args.extend(["--analyze", project_file])
        
        if args.verbose:
            cli_args.append("--verbose")
        
        print("🖥️  CLI MODE")
        print(f"📁 Project: {project_file}")
        print(f"⚡ Action: {action}")
        print("-" * 40)
        
        try:
            result = subprocess.run(cli_args, cwd=Path.cwd())
            return result.returncode
        except Exception as e:
            print(f"❌ CLI execution error: {e}")
            return 1
    
    # GUI режим (по умолчанию)
    main_file = Path("src/pixelflow_studio/main.py")
    if not main_file.exists():
        print(f"❌ Не найден главный файл: {main_file}")
        return 1
    
    print("✅ Все готово! Запускаю приложение...")
    print("🧪 Автоматическое тестирование включено")
    print("🖥️  GUI MODE")
    print("-" * 40)
    
    # Запуск GUI приложения
    try:
        result = subprocess.run([
            sys.executable, "-m", "src.pixelflow_studio.main"
        ], cwd=Path.cwd())
        return result.returncode
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 