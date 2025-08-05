#!/usr/bin/env python3
"""
CLI EXECUTOR - Запуск проектов без GUI
Позволяет выполнять проекты PixelFlow Studio из командной строки.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional
import argparse

from loguru import logger

# Добавляем путь к корню проекта
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from pixelflow_studio.core.application import Application
from pixelflow_studio.core.types import ExecutionContext


class CLIExecutor:
    """CLI исполнитель проектов без GUI."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.app = None
        self.execution_start_time = None
        
        # Настройка логирования
        if verbose:
            logger.remove()
            logger.add(sys.stdout, level="INFO", 
                      format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | {message}")
        else:
            logger.remove()
            logger.add(sys.stdout, level="WARNING",
                      format="<level>{level}</level> | {message}")
    
    def log_info(self, message: str) -> None:
        """Логирует информационное сообщение."""
        if self.verbose:
            logger.info(message)
    
    def log_error(self, message: str) -> None:
        """Логирует ошибку."""
        logger.error(message)
    
    def log_success(self, message: str) -> None:
        """Логирует успех."""
        logger.success(message)
    
    async def load_project(self, project_path: str) -> bool:
        """Загружает проект из файла."""
        try:
            self.log_info(f"📂 Loading project: {project_path}")
            
            if not os.path.exists(project_path):
                self.log_error(f"Project file not found: {project_path}")
                return False
            
            # Создаем приложение без GUI
            self.app = Application()
            self.log_info("🔧 Application initialized")
            
            # Загружаем проект
            with open(project_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # Восстанавливаем граф
            self.app.graph.from_dict(project_data, self.app.node_registry)
            
            nodes_count = len(self.app.graph.nodes)
            connections_count = len(self.app.graph._connections)
            
            self.log_info(f"📊 Project loaded: {nodes_count} nodes, {connections_count} connections")
            
            if nodes_count == 0:
                self.log_error("❌ Project contains no nodes to execute")
                return False
            
            return True
            
        except json.JSONDecodeError as e:
            self.log_error(f"Invalid JSON in project file: {e}")
            return False
        except Exception as e:
            self.log_error(f"Failed to load project: {e}")
            return False
    
    async def execute_project(self) -> bool:
        """Выполняет загруженный проект."""
        if not self.app:
            self.log_error("No project loaded")
            return False
        
        try:
            self.log_info("🚀 Starting project execution...")
            self.execution_start_time = time.time()
            
            # Выполняем граф
            await self.app.execute_graph_async()
            
            execution_time = time.time() - self.execution_start_time
            self.log_success(f"✅ Project executed successfully in {execution_time:.3f} seconds")
            
            return True
            
        except Exception as e:
            execution_time = time.time() - self.execution_start_time if self.execution_start_time else 0
            self.log_error(f"❌ Project execution failed after {execution_time:.3f}s: {e}")
            return False
    
    async def run_project(self, project_path: str) -> bool:
        """Загружает и выполняет проект."""
        success = await self.load_project(project_path)
        if not success:
            return False
        
        return await self.execute_project()
    
    def analyze_project(self, project_path: str) -> bool:
        """Анализирует проект без выполнения."""
        try:
            self.log_info(f"🔍 Analyzing project: {project_path}")
            
            if not os.path.exists(project_path):
                self.log_error(f"Project file not found: {project_path}")
                return False
            
            with open(project_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # Анализ структуры
            version = project_data.get('version', 'unknown')
            nodes = project_data.get('nodes', [])
            connections = project_data.get('connections', [])
            
            print(f"📋 PROJECT ANALYSIS")
            print(f"   Version: {version}")
            print(f"   Nodes: {len(nodes)}")
            print(f"   Connections: {len(connections)}")
            print()
            
            # Анализ нод
            if nodes:
                print("🔧 NODES:")
                for i, node in enumerate(nodes, 1):
                    node_type = node.get('class_name', 'Unknown')
                    node_name = node.get('name', 'Unnamed')
                    position = node.get('position', {})
                    x, y = position.get('x', 0), position.get('y', 0)
                    print(f"   {i}. {node_type}: '{node_name}' at ({x}, {y})")
                print()
            
            # Анализ соединений
            if connections:
                print("🔗 CONNECTIONS:")
                for i, conn in enumerate(connections, 1):
                    output_pin = conn.get('output_pin_name', 'unknown')
                    input_pin = conn.get('input_pin_name', 'unknown')
                    print(f"   {i}. {output_pin} → {input_pin}")
                print()
            
            self.log_success("✅ Project analysis completed")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to analyze project: {e}")
            return False


def main():
    """Главная функция CLI."""
    parser = argparse.ArgumentParser(
        description="PixelFlow Studio CLI Executor",
        epilog="Examples:\n"
               "  python cli_executor.py --execute project.pfp\n"
               "  python cli_executor.py --analyze project.pfp --verbose\n"
               "  python cli_executor.py --execute project.pfp --verbose",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('project', nargs='?', help='Project file (.pfp) to process')
    parser.add_argument('--execute', '-e', metavar='PROJECT', help='Execute the specified project')
    parser.add_argument('--analyze', '-a', metavar='PROJECT', help='Analyze the specified project')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--version', action='version', version='PixelFlow Studio CLI 1.0.0')
    
    args = parser.parse_args()
    
    # Определяем что делать
    project_file = args.execute or args.analyze or args.project
    
    if not project_file:
        parser.print_help()
        return 1
    
    # Создаем исполнитель
    executor = CLIExecutor(verbose=args.verbose)
    
    try:
        if args.analyze:
            # Анализ проекта
            success = executor.analyze_project(args.analyze)
            return 0 if success else 1
        
        else:
            # Выполнение проекта
            success = asyncio.run(executor.run_project(project_file))
            return 0 if success else 1
            
    except KeyboardInterrupt:
        executor.log_error("❌ Execution interrupted by user")
        return 130
    except Exception as e:
        executor.log_error(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())