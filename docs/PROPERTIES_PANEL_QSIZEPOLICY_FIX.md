# 🔧 Properties Panel QSizePolicy Fix

## 🚨 Ошибка исправлена

### ❌ Проблема:
```
AttributeError: 'PySide6.QtWidgets.QSizePolicy' object has no attribute 'Expanding'
```

### 🔍 Причина:
Неправильный синтаксис для QSizePolicy в PySide6/Qt6. Использовался старый синтаксис Qt5.

### ✅ Решение:

#### 1. Добавлен импорт QSizePolicy:
```python
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QSlider, QTextEdit,
    QPushButton, QFrame, QScrollArea, QGroupBox, QTabWidget, QSplitter,
    QListWidget, QListWidgetItem, QMessageBox, QSizePolicy  # ← Добавлено
)
```

#### 2. Исправлен синтаксис QSizePolicy:

**❌ Было (неправильно):**
```python
self.node_info_group.setSizePolicy(
    self.node_info_group.sizePolicy().Expanding, 
    self.node_info_group.sizePolicy().Preferred
)
```

**✅ Стало (правильно для PySide6):**
```python
self.node_info_group.setSizePolicy(
    QSizePolicy.Policy.Expanding, 
    QSizePolicy.Policy.Preferred
)
```

#### 3. Исправлен синтаксис QFormLayout:

**❌ Было:**
```python
self.node_info_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
```

**✅ Стало:**
```python
self.node_info_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
```

## 🎯 Технические детали

### PySide6/Qt6 Enums:
В Qt6 многие enum'ы были перенесены в отдельные пространства имен:

- **QSizePolicy.Expanding** → **QSizePolicy.Policy.Expanding**
- **QSizePolicy.Preferred** → **QSizePolicy.Policy.Preferred**
- **QFormLayout.ExpandingFieldsGrow** → **QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow**

### Применено к группам:
- ✅ Node Information
- ✅ Node Properties
- ✅ Pin Properties
- ✅ Connection Information

## 🧪 Результат

### До исправления:
```
❌ AttributeError: 'PySide6.QtWidgets.QSizePolicy' object has no attribute 'Expanding'
❌ GUI не запускается
```

### После исправления:
```
✅ Корректный синтаксис PySide6
✅ GUI запускается без ошибок
✅ Properties panel работает правильно
✅ Группы растягиваются на всю ширину
```

## 📚 Совместимость

### Qt5 vs Qt6:
| Компонент | Qt5 | Qt6 |
|-----------|-----|-----|
| **QSizePolicy** | `QSizePolicy.Expanding` | `QSizePolicy.Policy.Expanding` |
| **QFormLayout** | `QFormLayout.ExpandingFieldsGrow` | `QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow` |

### PySide2 vs PySide6:
- **PySide2:** Старый синтаксис enum'ов
- **PySide6:** Новый синтаксис с полными путями к enum'ам

---

**🎉 Properties Panel теперь работает корректно с PySide6!**