# 🏗️ План рефакторинга PixelFlow Studio

## 🎯 **ЦЕЛИ РЕФАКТОРИНГА**

1. **Внедрить правильную MVVM архитектуру**
2. **Устранить нарушения принципов SOLID**
3. **Улучшить типизацию и безопасность типов**
4. **Оптимизировать производительность**
5. **Упростить тестирование**

## 🚨 **КРИТИЧЕСКИЕ ПРОБЛЕМЫ (ВЫСОКИЙ ПРИОРИТЕТ)**

### 1. **PropertiesPanel - монстр-класс (978 строк)**

**ПРОБЛЕМЫ:**
- Смешивание UI и бизнес-логики
- Прямые обращения к другим компонентам через parent()
- Слабая типизация
- Нарушение Single Responsibility Principle

**РЕШЕНИЕ:**
```python
# Разбить на компоненты:
class NodeInfoWidget(QWidget)      # ~100 строк
class NodePropertiesWidget(QWidget) # ~150 строк  
class PinPropertiesWidget(QWidget)  # ~120 строк
class PropertiesPanel(QWidget)      # ~80 строк (композитный)
```

### 2. **Отсутствие ViewModels**

**ПРОБЛЕМЫ:**
- UI напрямую обращается к моделям
- Нет координации между компонентами
- Сложно тестировать

**РЕШЕНИЕ:**
```python
class PropertiesViewModel(QObject):
    node_selected = Signal(NodeInfo)
    property_updated = Signal(str, object)
    
    def update_variable(self, var_id: str, prop: str, value: Any):
        # Бизнес-логика здесь
        pass
```

### 3. **Слабая типизация**

**ПРОБЛЕМЫ:**
```python
# ❌ ПЛОХО
def get_variable_by_id(self, var_id: str) -> dict:

# ✅ ХОРОШО  
def get_variable_by_id(self, var_id: str) -> VariableData:
```

## 📋 **ПЛАН РЕАЛИЗАЦИИ**

### **ЭТАП 1: Фундамент (1-2 недели)**

#### 1.1 Создать систему событий
- [x] `EventBus` - централизованная система событий
- [x] `SettingsManager` - управление конфигурацией
- [ ] `LoggerManager` - централизованное логирование

#### 1.2 Создать базовые ViewModels
- [x] `PropertiesViewModel` - для PropertiesPanel
- [ ] `NodeEditorViewModel` - для NodeEditor
- [ ] `VariablesViewModel` - для VariablesPanel

#### 1.3 Улучшить типизацию
- [ ] `TypedDict` для всех структур данных
- [ ] `Protocol` для интерфейсов
- [ ] Строгая типизация для всех публичных API

### **ЭТАП 2: Рефакторинг UI (2-3 недели)**

#### 2.1 Разбить PropertiesPanel
```python
# Новые компоненты:
src/pixelflow_studio/views/properties/
├── __init__.py
├── node_info_widget.py
├── node_properties_widget.py
├── pin_properties_widget.py
├── variable_properties_widget.py
└── properties_panel.py  # композитный
```

#### 2.2 Создать базовые виджеты
- [ ] `BasePropertyWidget` - базовый класс для всех property виджетов
- [ ] `PropertyEditorFactory` - фабрика для создания редакторов
- [ ] `PropertyBinding` - система привязки данных

#### 2.3 Рефакторинг NodeEditor
- [ ] Вынести логику в ViewModel
- [ ] Создать отдельные виджеты для разных частей
- [ ] Улучшить обработку событий

### **ЭТАП 3: Оптимизация производительности (1 неделя)**

#### 3.1 Кэширование
- [ ] `ImageCache` - кэш для изображений
- [ ] `NodeCache` - кэш для нодов
- [ ] `PropertyCache` - кэш для свойств

#### 3.2 Асинхронность
- [ ] `AsyncImageProcessor` - асинхронная обработка
- [ ] `BackgroundWorker` - фоновые задачи
- [ ] `ProgressManager` - управление прогрессом

### **ЭТАП 4: Тестирование (1 неделя)**

#### 4.1 Unit тесты
- [ ] Тесты для всех ViewModels
- [ ] Тесты для EventBus
- [ ] Тесты для SettingsManager

#### 4.2 Integration тесты
- [ ] Тесты UI компонентов
- [ ] Тесты workflows
- [ ] Тесты производительности

## 🎨 **НОВАЯ АРХИТЕКТУРА**

### **Структура после рефакторинга:**

```
src/pixelflow_studio/
├── core/
│   ├── application.py
│   ├── event_bus.py          # ✅ НОВОЕ
│   ├── settings_manager.py   # ✅ НОВОЕ
│   └── types.py
├── models/
│   ├── graph.py
│   ├── node.py
│   └── variable.py
├── viewmodels/               # ✅ НОВАЯ ПАПКА
│   ├── properties_viewmodel.py
│   ├── node_editor_viewmodel.py
│   └── variables_viewmodel.py
├── views/
│   ├── properties/           # ✅ РЕСТРУКТУРИЗОВАНО
│   │   ├── node_info_widget.py
│   │   ├── node_properties_widget.py
│   │   └── properties_panel.py
│   ├── node_editor.py
│   └── variables_panel.py
└── config/                   # ✅ НОВАЯ ПАПКА
    ├── settings.py
    ├── themes.py
    └── shortcuts.py
```

### **Поток данных:**

```
User Action → View → ViewModel → Model → EventBus → Other ViewModels
     ↑                                                      ↓
     └─────────────── UI Update ←──────────────────────────┘
```

## 🔧 **ИНСТРУМЕНТЫ И ПРАКТИКИ**

### **1. Типизация**
```python
# mypy.ini
[mypy]
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
warn_return_any = True
```

### **2. Линтинг**
```python
# pre-commit hooks
- black
- isort  
- mypy
- flake8
```

### **3. Тестирование**
```python
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
addopts = -v --tb=short --strict-markers
markers = [unit, integration, slow]
```

## 📊 **МЕТРИКИ УСПЕХА**

### **До рефакторинга:**
- PropertiesPanel: 978 строк
- Связанность: Высокая (прямые обращения)
- Тестируемость: Низкая
- Типизация: Слабая

### **После рефакторинга:**
- PropertiesPanel: ~80 строк
- Компоненты: 100-150 строк каждый
- Связанность: Низкая (через EventBus)
- Тестируемость: Высокая
- Типизация: Строгая

## 🚀 **СЛЕДУЮЩИЕ ШАГИ**

1. **Немедленно:**
   - Создать EventBus и SettingsManager ✅
   - Начать рефакторинг PropertiesPanel
   - Добавить строгую типизацию

2. **В течение недели:**
   - Завершить ViewModels
   - Разбить PropertiesPanel на компоненты
   - Добавить unit тесты

3. **В течение месяца:**
   - Полный рефакторинг UI
   - Оптимизация производительности
   - Comprehensive testing

## 💡 **РЕКОМЕНДАЦИИ**

### **1. Постепенный рефакторинг**
- Не переписывать все сразу
- Тестировать каждый этап
- Сохранять работоспособность

### **2. Приоритеты**
- Сначала критичные проблемы
- Потом оптимизация
- В конце polish

### **3. Документация**
- Обновлять документацию после каждого этапа
- Создавать примеры использования
- Ведение changelog

---

**🎯 Цель: Создать профессиональную, масштабируемую архитектуру, которая выдержит рост проекта и упростит разработку новых функций.** 