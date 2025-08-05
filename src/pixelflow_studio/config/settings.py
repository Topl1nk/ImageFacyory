"""
Система конфигурации для PixelFlow Studio.

Централизованное управление настройками приложения.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field, asdict
from PySide6.QtCore import QObject, Signal


@dataclass
class UISettings:
    """Настройки пользовательского интерфейса."""
    
    # Размеры окон
    main_window_width: int = 1200
    main_window_height: int = 800
    main_window_x: int = 100
    main_window_y: int = 100
    
    # Панели
    properties_panel_width: int = 300
    variables_panel_width: int = 250
    node_palette_width: int = 200
    
    # Темы
    theme: str = "dark"
    accent_color: str = "#007acc"
    
    # Масштабирование
    canvas_zoom_min: float = 0.1
    canvas_zoom_max: float = 5.0
    canvas_zoom_default: float = 1.0
    
    # Сетка
    grid_enabled: bool = True
    grid_size: int = 20
    grid_color: str = "#333333"
    
    # Соединения
    connection_style: str = "bezier"  # bezier, straight, orthogonal
    connection_width: int = 2
    connection_color: str = "#ffffff"


@dataclass
class NodeSettings:
    """Настройки нодов."""
    
    # Размеры нодов
    node_width: int = 150
    node_height: int = 100
    node_padding: int = 10
    
    # Цвета нодов по категориям
    node_colors: Dict[str, str] = field(default_factory=lambda: {
        "Generator": "#4CAF50",
        "Filter": "#2196F3", 
        "Transform": "#FF9800",
        "Color": "#9C27B0",
        "IO": "#607D8B",
        "Variable": "#795548"
    })
    
    # Пины
    pin_radius: int = 4
    pin_spacing: int = 25
    pin_label_offset: int = 15


@dataclass
class PerformanceSettings:
    """Настройки производительности."""
    
    # Обработка изображений
    max_image_size: int = 4096
    image_cache_size: int = 100
    enable_image_compression: bool = True
    
    # Многопоточность
    max_threads: int = 4
    enable_async_processing: bool = True
    
    # Автосохранение
    auto_save_interval: int = 300  # секунды
    auto_save_enabled: bool = True
    
    # Предварительный просмотр
    preview_quality: str = "medium"  # low, medium, high
    preview_update_delay: int = 500  # миллисекунды


@dataclass
class ProjectSettings:
    """Настройки проектов."""
    
    # Пути
    default_project_path: str = str(Path.home() / "PixelFlow Projects")
    recent_projects_max: int = 10
    
    # Форматы
    default_image_format: str = "PNG"
    default_project_format: str = "pfp"
    
    # Версионирование
    enable_versioning: bool = True
    max_versions: int = 10


@dataclass
class ApplicationSettings:
    """Основные настройки приложения."""
    
    # Общие
    language: str = "ru"
    enable_logging: bool = True
    log_level: str = "INFO"
    
    # UI
    ui: UISettings = field(default_factory=UISettings)
    
    # Ноды
    nodes: NodeSettings = field(default_factory=NodeSettings)
    
    # Производительность
    performance: PerformanceSettings = field(default_factory=PerformanceSettings)
    
    # Проекты
    projects: ProjectSettings = field(default_factory=ProjectSettings)


class SettingsManager(QObject):
    """
    Менеджер настроек приложения.
    
    Обеспечивает загрузку, сохранение и управление настройками.
    """
    
    settings_changed = Signal(str, object)  # setting_name, new_value
    
    def __init__(self):
        super().__init__()
        self._settings = ApplicationSettings()
        self._config_file = self._get_config_path()
        self._load_settings()
    
    @property
    def settings(self) -> ApplicationSettings:
        """Возвращает текущие настройки."""
        return self._settings
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Получает значение настройки по пути.
        
        Args:
            path: Путь к настройке (например, "ui.theme")
            default: Значение по умолчанию
            
        Returns:
            Значение настройки
        """
        try:
            value = self._settings
            for key in path.split('.'):
                value = getattr(value, key)
            return value
        except AttributeError:
            return default
    
    def set(self, path: str, value: Any) -> bool:
        """
        Устанавливает значение настройки по пути.
        
        Args:
            path: Путь к настройке (например, "ui.theme")
            value: Новое значение
            
        Returns:
            True если успешно, False иначе
        """
        try:
            obj = self._settings
            keys = path.split('.')
            
            # Проходим до предпоследнего элемента
            for key in keys[:-1]:
                obj = getattr(obj, key)
            
            # Устанавливаем значение
            setattr(obj, keys[-1], value)
            
            # Уведомляем об изменении
            self.settings_changed.emit(path, value)
            
            return True
        except AttributeError:
            return False
    
    def reset_to_defaults(self) -> None:
        """Сбрасывает настройки к значениям по умолчанию."""
        self._settings = ApplicationSettings()
        self._save_settings()
        self.settings_changed.emit("all", self._settings)
    
    def _get_config_path(self) -> Path:
        """Возвращает путь к файлу конфигурации."""
        config_dir = Path.home() / ".pixelflow_studio"
        config_dir.mkdir(exist_ok=True)
        return config_dir / "settings.json"
    
    def _load_settings(self) -> None:
        """Загружает настройки из файла."""
        if self._config_file.exists():
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._settings = self._dict_to_settings(data)
            except Exception as e:
                print(f"Error loading settings: {e}")
                # Используем настройки по умолчанию
    
    def _save_settings(self) -> None:
        """Сохраняет настройки в файл."""
        try:
            data = self._settings_to_dict(self._settings)
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def _settings_to_dict(self, settings: Any) -> Dict[str, Any]:
        """Конвертирует настройки в словарь."""
        if hasattr(settings, '__dataclass_fields__'):
            result = {}
            for field_name, field_info in settings.__dataclass_fields__.items():
                value = getattr(settings, field_name)
                if hasattr(value, '__dataclass_fields__'):
                    result[field_name] = self._settings_to_dict(value)
                else:
                    result[field_name] = value
            return result
        return settings
    
    def _dict_to_settings(self, data: Dict[str, Any]) -> ApplicationSettings:
        """Конвертирует словарь в настройки."""
        # Создаем настройки по умолчанию
        settings = ApplicationSettings()
        
        # Обновляем из данных
        if 'ui' in data:
            for key, value in data['ui'].items():
                if hasattr(settings.ui, key):
                    setattr(settings.ui, key, value)
        
        if 'nodes' in data:
            for key, value in data['nodes'].items():
                if hasattr(settings.nodes, key):
                    setattr(settings.nodes, key, value)
        
        if 'performance' in data:
            for key, value in data['performance'].items():
                if hasattr(settings.performance, key):
                    setattr(settings.performance, key, value)
        
        if 'projects' in data:
            for key, value in data['projects'].items():
                if hasattr(settings.projects, key):
                    setattr(settings.projects, key, value)
        
        # Общие настройки
        for key, value in data.items():
            if key not in ['ui', 'nodes', 'performance', 'projects']:
                if hasattr(settings, key):
                    setattr(settings, key, value)
        
        return settings


# Глобальный экземпляр менеджера настроек
settings_manager = SettingsManager() 