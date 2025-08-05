# PixelFlow Studio 🎨

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![PySide6](https://img.shields.io/badge/PySide6-6.6+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Tests](https://img.shields.io/badge/tests-pytest-orange.svg)

**Профессиональная студия для обработки изображений с нодовым интерфейсом**

PixelFlow Studio - это современное приложение для обработки изображений, построенное на принципах визуального программирования. Вдохновленное лучшими практиками Blender, Unreal Engine и Substance Designer.

## ✨ Особенности

- 🎯 **Современная архитектура MVVM** - четкое разделение бизнес-логики и UI
- 🔧 **Типизированная система нодов** - безопасные соединения с проверкой типов
- 🎨 **Профессиональный интерфейс** - современный UI с поддержкой тем
- 🔌 **Система плагинов** - легкое создание пользовательских нодов
- ⚡ **Асинхронное выполнение** - неблокирующая обработка изображений
- 🧪 **Полное тестирование** - unit и integration тесты
- 📚 **Подробная документация** - comprehensive API reference

## 🚀 Быстрый старт

### Требования

- Python 3.10+
- PySide6 6.6+
- pip или poetry

### Установка

```bash
# Клонируем репозиторий
git clone https://github.com/pixelflow/studio.git
cd studio

# Устанавливаем зависимости
pip install -e .

# Для разработки
pip install -e ".[dev]"
```

### Запуск

```bash
# Запуск приложения
pixelflow

# Или через Python
python -m pixelflow_studio
```

## 🏗️ Архитектура

```
src/pixelflow_studio/
├── core/           # Ядро системы - базовые абстракции
├── models/         # Модели данных и бизнес-логика
├── views/          # UI компоненты и виджеты
├── viewmodels/     # Связующий слой между моделями и видами
├── nodes/          # Встроенные ноды для обработки изображений
├── plugins/        # Система плагинов и пользовательские ноды
├── utils/          # Утилиты и вспомогательные функции
└── resources/      # Ресурсы (иконки, темы, переводы)
```

### Основные принципы

1. **MVVM архитектура** - четкое разделение ответственности
2. **Type Safety** - полная типизация с mypy
3. **Async/Await** - неблокирующие операции
4. **Signal/Slot** - слабая связанность компонентов
5. **Plugin Architecture** - расширяемость без изменения ядра
6. **Comprehensive Testing** - высокое покрытие тестами

## 🎨 Создание пользовательских нодов

```python
from pixelflow_studio.nodes.base import ImageProcessingNode
from pixelflow_studio.core.types import PinType
from PIL import Image, ImageFilter

class BlurNode(ImageProcessingNode):
    """Нод для размытия изображения"""
    
    def __init__(self) -> None:
        super().__init__(
            name="Blur Effect",
            description="Применяет гауссово размытие к изображению",
            category="Filter"
        )
    
    def setup_pins(self) -> None:
        # Входы
        self.add_input_pin("image", PinType.IMAGE, "Входное изображение")
        self.add_input_pin("radius", PinType.FLOAT, "Радиус размытия", default=2.0)
        
        # Выходы  
        self.add_output_pin("result", PinType.IMAGE, "Размытое изображение")
    
    async def process(self) -> None:
        image = await self.get_input_value("image")
        radius = await self.get_input_value("radius")
        
        if image is not None:
            blurred = image.filter(ImageFilter.GaussianBlur(radius=radius))
            await self.set_output_value("result", blurred)
```

## 🧪 Тестирование

```bash
# Запуск всех тестов
pytest

# Только unit тесты
pytest tests/unit

# С покрытием
pytest --cov=pixelflow_studio

# Конкретный тест
pytest tests/unit/test_nodes.py::test_blur_node
```

## 📖 Документация

- [Руководство пользователя](docs/user_guide.md)
- [API Reference](docs/api_reference.md)
- [Создание плагинов](docs/plugin_development.md)
- [Архитектура](docs/architecture.md)

## 🤝 Вклад в проект

Мы приветствуем вклад сообщества! Пожалуйста, ознакомьтесь с [CONTRIBUTING.md](CONTRIBUTING.md).

### Для разработчиков

```bash
# Клонируем и настраиваем среду разработки
git clone https://github.com/pixelflow/studio.git
cd studio

# Устанавливаем pre-commit hooks
pre-commit install

# Запускаем линтеры
black src tests
isort src tests
mypy src

# Запускаем тесты
pytest
```

## 📊 Производительность

- ⚡ Асинхронная обработка изображений
- 🧵 Многопоточность для CPU-intensive операций
- 💾 Ленивая загрузка и умное кэширование
- 🔄 Инкрементальное обновление графа

## 🎯 Roadmap

- [ ] **v1.1**: Поддержка видео обработки
- [ ] **v1.2**: Интеграция с AI/ML моделями
- [ ] **v1.3**: Облачная синхронизация проектов
- [ ] **v1.4**: Collaborative editing
- [ ] **v2.0**: Веб-версия приложения

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. [LICENSE](LICENSE) файл.

## 🙏 Благодарности

- Qt Team за отличный фреймворк
- Blender Foundation за вдохновение в UX
- Открытое сообщество Python за amazing ecosystem

---

**🌟 Если проект полезен, поставьте звездочку!**
