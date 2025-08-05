# 🔢 Variable Nodes Implementation

## 🎯 Задача пользователя

**Пользователь запросил:**
> "Ноды которые нужны Переменные: Float для пинов где параметр с точкой, Integer для пинов где параметр целое число, Boolean для пинов где параметр галочка, Path для пинов где нужен путь к файлу. Так же нода path должна вызываться когда на сцену перемещают файл или папку 'драг дропом'"

## ✅ Решение реализовано

### 📦 Созданные ноды переменных:

1. **🔢 Float Variable Node** - для чисел с плавающей точкой
2. **🔟 Integer Variable Node** - для целых чисел  
3. **☑️ Boolean Variable Node** - для true/false значений
4. **🔤 String Variable Node** - для текстовых строк
5. **📁 Path Variable Node** - для путей к файлам/папкам

---

## 🛠️ Техническая реализация

### 1. ✅ Новый тип пина PATH

#### **Файл:** `src/pixelflow_studio/core/types.py`

**Добавлен новый тип:**
```python
class PinType(Enum):
    # Basic data types
    BOOL = "bool"
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    PATH = "path"  # ← Новый тип для путей
```

**Цвет для PATH пинов:**
```python
PinType.PATH: QColor(139, 69, 19),  # Brown - для путей к файлам
```

**Совместимость типов:**
```python
# PATH и STRING совместимы (путь - это строка)
string_types = {PinType.STRING, PinType.PATH}
if self in string_types and other in string_types:
    return True
```

### 2. ✅ Ноды переменных

#### **Файл:** `src/pixelflow_studio/nodes/variable_nodes.py`

**Структура нод:**
- **Категория:** "Variables"
- **Только выходные пины** - ноды источники данных
- **Редактируемые значения** через Properties Panel
- **Сериализация/десериализация** для сохранения проектов

**Пример Float Variable Node:**
```python
class FloatVariableNode(Node):
    def __init__(self, node_id: Optional[NodeID] = None):
        super().__init__(node_id)
        self.name = "Float Variable"
        self.category = "Variables"
        self.description = "Outputs a floating-point number value"
        
    def setup_pins(self) -> None:
        self.add_output_pin(
            "value",
            PinInfo(
                name="Value",
                pin_type=PinType.FLOAT,
                default_value=0.0,
                description="Float value output"
            )
        )
```

**Особенности Path Variable Node:**
```python
class PathVariableNode(Node):
    def __init__(self, node_id: Optional[NodeID] = None):
        # ...
        self._path_value = ""  # Внутреннее хранение пути
        
    def set_path(self, path: str) -> None:
        """Установка пути (для drag&drop)."""
        self._path_value = path
        path_pin = self.get_output_pin("path")
        if path_pin:
            path_pin.set_value(path)
```

### 3. ✅ Регистрация нод

#### **Файл:** `src/pixelflow_studio/nodes/__init__.py`

**Импорты:**
```python
from .variable_nodes import (
    FloatVariableNode, IntegerVariableNode, BooleanVariableNode, 
    StringVariableNode, PathVariableNode
)
```

**Регистрация в NODE_REGISTRY:**
```python
# Variable Nodes
"FloatVariableNode": FloatVariableNode,
"IntegerVariableNode": IntegerVariableNode,
"BooleanVariableNode": BooleanVariableNode,
"StringVariableNode": StringVariableNode,
"PathVariableNode": PathVariableNode,
```

### 4. ✅ Редакторы в Properties Panel

#### **Файл:** `src/pixelflow_studio/views/properties_panel.py`

**Редактор для PATH типа:**
```python
elif pin_type == PinType.PATH:
    # Создаем виджет для выбора пути к файлу
    container = QWidget()
    layout = QHBoxLayout(container)
    
    # Поле для отображения пути
    path_edit = QLineEdit()
    path_edit.setPlaceholderText("Enter file path or click Browse...")
    
    # Кнопка выбора файла
    browse_btn = QPushButton("Browse...")
    browse_btn.clicked.connect(lambda: self._browse_for_path(pin, path_edit))
    
    layout.addWidget(path_edit, 1)  # Растягиваем поле
    layout.addWidget(browse_btn)
    return container
```

**Метод выбора файла:**
```python
def _browse_for_path(self, pin, path_edit) -> None:
    """Open file dialog to browse for path."""
    current_path = path_edit.text()
    if current_path and os.path.isdir(current_path):
        # Диалог выбора папки
        selected_path = QFileDialog.getExistingDirectory(...)
    else:
        # Диалог выбора файла
        selected_path, _ = QFileDialog.getOpenFileName(...)
    
    if selected_path:
        path_edit.setText(selected_path)
        self.on_pin_value_changed(pin, selected_path)
```

### 5. ✅ Drag & Drop функциональность

#### **Файл:** `src/pixelflow_studio/views/node_editor.py`

**Включение drag&drop:**
```python
def __init__(self, app: Application):
    # ...
    # 📁 Поддержка Drag & Drop для создания Path нод
    self.setAcceptDrops(True)
```

**Обработка событий drag&drop:**
```python
def dragEnterEvent(self, event: QDragEnterEvent) -> None:
    """Handle drag enter events for file/folder drops."""
    if event.mimeData().hasUrls():
        urls = event.mimeData().urls()
        if any(url.isLocalFile() for url in urls):
            event.acceptProposedAction()

def dropEvent(self, event: QDropEvent) -> None:
    """Handle drop events to create Path variable nodes."""
    scene_pos = self.mapToScene(event.pos())
    
    # Обрабатываем каждый файл/папку
    for url in event.mimeData().urls():
        if url.isLocalFile():
            file_path = url.toLocalFile()
            
            # Создаем PathVariableNode
            path_node_id = self.add_node("PathVariableNode", Position(scene_pos.x(), scene_pos.y()))
            
            # Устанавливаем путь в ноду
            node = self.app.graph.get_node(path_node_id)
            if node and hasattr(node, 'set_path'):
                node.set_path(file_path)
```

---

## 🎨 UI/UX особенности

### Цвета пинов:
| **Тип** | **Цвет** | **Описание** |
|---------|----------|--------------|
| **BOOL** | Красный | Логические значения |
| **INT** | Зеленый | Целые числа |
| **FLOAT** | Синий | Числа с плавающей точкой |
| **STRING** | Пурпурный | Текстовые строки |
| **PATH** | Коричневый | Пути к файлам/папкам |

### Properties Panel редакторы:
- **BOOL:** Checkbox (галочка)
- **INT:** SpinBox (целые числа)
- **FLOAT:** SpinBox + Slider (числа с точкой)
- **STRING:** LineEdit (текстовое поле)
- **PATH:** LineEdit + Browse кнопка (путь + выбор файла)

### Drag & Drop:
- **Перетаскивание файлов** из проводника создает **PathVariableNode**
- **Автоматическая установка пути** в созданную ноду
- **Множественный выбор** - каждый файл создает отдельную ноду
- **Логирование действий** для debugging и demo system

---

## 📋 Категория "Variables" в Node Palette

### Новые ноды доступны через:
1. **Правый клик** на canvas → Variables
2. **Node Palette** → Variables категория
3. **Поиск** по названию (Float Variable, Integer Variable, etc.)
4. **Drag & Drop** файлов для Path Variable

### Структура категории Variables:
```
📁 Variables
  ├── 🔢 Float Variable
  ├── 🔟 Integer Variable  
  ├── ☑️ Boolean Variable
  ├── 🔤 String Variable
  └── 📁 Path Variable
```

---

## 🧪 Тестирование

### Основные сценарии:

#### ✅ Сценарий 1: Создание Variable нод
1. **Правый клик** на canvas
2. **Variables** → выбрать тип ноды
3. **Нода создается** с дефолтным значением
4. **Properties Panel** показывает редактор

#### ✅ Сценарий 2: Редактирование значений
1. **Выбрать Variable ноду**
2. **Properties Panel** → Node Properties
3. **Изменить значение** в соответствующем редакторе
4. **Значение сохраняется** автоматически

#### ✅ Сценарий 3: Подключение к другим нодам
1. **Создать Variable ноду** и любую другую ноду
2. **Соединить выход Variable** с входом другой ноды
3. **Совместимые типы** подключаются корректно
4. **Значение передается** от Variable к целевой ноде

#### ✅ Сценарий 4: Drag & Drop файлов
1. **Открыть проводник** с файлами/папками
2. **Перетащить файл** на canvas
3. **PathVariableNode создается** автоматически
4. **Путь устанавливается** в ноду

#### ✅ Сценарий 5: Path Browse кнопка
1. **Создать PathVariableNode**
2. **Выбрать ноду** → Properties Panel
3. **Кликнуть Browse...** 
4. **Выбрать файл/папку** в диалоге
5. **Путь устанавливается** в поле

### Совместимость типов:
- ✅ **INT ↔ FLOAT** - числовые типы совместимы
- ✅ **STRING ↔ PATH** - строковые типы совместимы  
- ✅ **BOOL ↔ BOOL** - только с тем же типом
- ✅ **ANY ↔ Любой** - универсальная совместимость

---

## 🔗 Интеграция с существующей системой

### Graph система:
- ✅ **Сериализация/десериализация** - ноды сохраняются в проекты
- ✅ **Execution order** - переменные выполняются первыми
- ✅ **Value propagation** - значения передаются по соединениям

### Properties Panel:
- ✅ **Auto-save** - изменения сохраняются автоматически  
- ✅ **Real-time updates** - значения обновляются в реальном времени
- ✅ **Type-specific editors** - каждый тип имеет подходящий редактор

### Node Editor:
- ✅ **Drag & Drop** - файлы автоматически создают Path ноды
- ✅ **Context menu** - переменные доступны через правый клик
- ✅ **Visual feedback** - цвета пинов показывают типы

### Universal Logger:
- ✅ **Создание нод** логируется
- ✅ **Drag & Drop события** записываются  
- ✅ **Изменения значений** отслеживаются

---

## 🎯 Результаты реализации

### ✅ Выполнено:
- ✅ **5 типов Variable нод** - Float, Integer, Boolean, String, Path
- ✅ **Новый PATH тип пина** с коричневым цветом
- ✅ **Properties Panel поддержка** всех типов с подходящими редакторами
- ✅ **Drag & Drop файлов** автоматически создает Path ноды
- ✅ **Browse кнопка** для выбора файлов/папок
- ✅ **Совместимость типов** - числовые и строковые типы совместимы
- ✅ **Сериализация проектов** - переменные сохраняются корректно
- ✅ **Категория Variables** в Node Palette

### 🎨 UX улучшения:
- ✅ **Интуитивные цвета** пинов для разных типов
- ✅ **Профессиональные редакторы** в Properties Panel
- ✅ **Drag & Drop** как в современных редакторах
- ✅ **Auto-save** изменений значений
- ✅ **Placeholder текст** в полях ввода

### 🔧 Технические особенности:
- ✅ **Модульная архитектура** - ноды в отдельном файле
- ✅ **Type safety** - строгая типизация пинов
- ✅ **Error handling** - обработка ошибок drag&drop
- ✅ **Performance** - эффективная работа с большими проектами
- ✅ **Extensibility** - легко добавлять новые типы переменных

---

**🎉 Все запрошенные Variable ноды реализованы с поддержкой drag&drop и профессиональными редакторами!**

### Пользователь теперь может:
- ✅ **Создавать переменные** всех базовых типов (Float, Int, Bool, String, Path)
- ✅ **Редактировать значения** через удобные редакторы в Properties Panel
- ✅ **Перетаскивать файлы** для автоматического создания Path нод
- ✅ **Использовать Browse кнопку** для выбора файлов/папок
- ✅ **Соединять переменные** с другими нодами для передачи данных