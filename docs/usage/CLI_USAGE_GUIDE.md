# 🖥️ CLI Usage Guide - PixelFlow Studio

## 📋 Обзор

PixelFlow Studio теперь поддерживает **режим командной строки (CLI)** для запуска проектов без GUI интерфейса. Это идеально подходит для:

- **Автоматизации** обработки изображений
- **Batch обработки** множества проектов
- **CI/CD пайплайнов** 
- **Серверных сред** без графического интерфейса
- **Скриптинга** и автоматизации

## 🚀 Быстрый старт

### Запуск GUI (по умолчанию)
```bash
python run.py
```

### Выполнение проекта без GUI
```bash
python run.py -pr project.pfp -ex
```

### Анализ структуры проекта  
```bash
python run.py -pr project.pfp -an
```

### Подробный вывод
```bash
python run.py -pr project.pfp -ex -v
```

## 📖 Полное руководство

### 🔧 Параметры командной строки

| Параметр | Короткий | Описание |
|----------|----------|----------|
| `--project FILE` | `-pr` | Файл проекта (.pfp) для обработки |
| `--execute` | `-ex` | Выполнить проект |
| `--analyze` | `-an` | Проанализировать структуру проекта |
| `--verbose` | `-v` | Подробный вывод (для CLI режима) |
| `--help` | `-h` | Показать справку |

#### 🆕 Новая логичная схема:
1. **Указываем проект:** `-pr project.pfp`
2. **Выбираем действие:** `-ex` (execute) или `-an` (analyze)  
3. **Добавляем опции:** `-v` (verbose)

### 📊 Режим анализа

Анализирует структуру проекта без выполнения:

```bash
python run.py -pr saves/test_save.pfp -an
```

**Вывод:**
```
📋 PROJECT ANALYSIS
   Version: 1.0
   Nodes: 3
   Connections: 4

🔧 NODES:
   1. BrightnessContrastNode: 'Brightness/Contrast' at (-418, 15)
   2. LoadImageNode: 'Load Image' at (-551, 59) 
   3. SaveImageNode: 'Save Image' at (45, 44)

🔗 CONNECTIONS:
   1. exec → exec
   2. image → image
   3. exec → exec
   4. image → image
```

### ⚡ Режим выполнения

Выполняет проект полностью:

```bash
python run.py -pr saves/test_save.pfp -ex -v
```

**Подробный вывод:**
```
00:21:02 | INFO     | 📂 Loading project: saves/test_save.pfp
00:21:02 | INFO     | 🔧 Application initialized
00:21:02 | INFO     | 📊 Project loaded: 3 nodes, 4 connections
00:21:02 | INFO     | 🚀 Starting project execution...
00:21:02 | INFO     | Loading image: path/to/image.png
00:21:02 | INFO     | Successfully loaded image: 2048x2048
00:21:03 | INFO     | Saving image to: output.png (format: PNG)
00:21:04 | INFO     | Successfully saved image: output.png
00:21:04 | SUCCESS  | ✅ Project executed successfully in 2.052 seconds
```

## 🎯 Примеры использования

### 1. Простое выполнение
```bash
# Выполнить проект с минимальным выводом
python run.py -pr my_project.pfp -ex
```

### 2. Подробное выполнение
```bash
# Выполнить с подробной информацией
python run.py -pr my_project.pfp -ex -v
```

### 3. Анализ перед выполнением
```bash
# Сначала проанализировать
python run.py -pr my_project.pfp -an

# Затем выполнить
python run.py -pr my_project.pfp -ex -v
```

### 4. Batch обработка (пример скрипта)
```bash
#!/bin/bash
# process_all.sh - обработка всех проектов в папке

for project in projects/*.pfp; do
    echo "Processing: $project"
    python run.py -pr "$project" -ex -v
    if [ $? -eq 0 ]; then
        echo "✅ Success: $project"
    else
        echo "❌ Failed: $project"
    fi
done
```

### 5. CI/CD интеграция
```yaml
# .github/workflows/image-processing.yml
name: Process Images
on: [push]
jobs:
  process:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - name: Process project
      run: python run.py -pr project.pfp -ex -v
```

## 🔧 Коды возврата

| Код | Описание |
|-----|----------|
| `0` | Успешное выполнение |
| `1` | Общая ошибка |
| `130` | Прервано пользователем (Ctrl+C) |

## 📝 Логирование

### Обычный режим
- Показывает только **WARNING** и **ERROR**
- Минимальный вывод для скриптинга

### Verbose режим (`--verbose`)
- Показывает **INFO**, **SUCCESS**, **WARNING**, **ERROR**
- Подробная информация о процессе
- Временные метки

## ⚠️ Важные особенности

### 🔄 Разделение GUI и CLI
- **GUI режим**: Полный интерфейс с редактором нод
- **CLI режим**: Только выполнение, без графики
- **Общий код**: Одна и та же логика выполнения

### 📁 Рабочая директория
CLI executor работает относительно директории откуда запущен скрипт.

### 🚫 Ограничения CLI режима
- ❌ Нельзя редактировать проекты
- ❌ Нет визуального интерфейса  
- ❌ Нет интерактивной отладки
- ✅ Только выполнение и анализ

## 🛠️ Отладка

### Проблемы с файлами
```bash
# Проверить существование файла
ls -la saves/test_save.pfp

# Проанализировать структуру
python run.py -pr saves/test_save.pfp -an
```

### Проблемы выполнения
```bash
# Запустить с подробным выводом
python run.py -pr project.pfp -ex -v

# Проверить логи
tail -f logs/pixelflow_*.log
```

### Проблемы с зависимостями
```bash
# run.py автоматически проверяет и устанавливает зависимости
python run.py --help
```

## 🎬 Интеграция с профессиональным тестированием

CLI режим отлично работает с нашей системой тестирования:

```bash
# Сначала создаем тестовое изображение
python -c "from test_creation import create_test_image; create_test_image()"

# Анализируем проект
python run.py -pr saves/test_save.pfp -an

# Выполняем с подробным выводом
python run.py -pr saves/test_save.pfp -ex -v
```

## 📈 Производительность

**Сравнение режимов:**

| Режим | Время запуска | Память | Подходит для |
|-------|---------------|--------|--------------|
| GUI | ~3-5 секунд | ~200MB | Разработка, отладка |
| CLI | ~0.5-1 секунда | ~50MB | Автоматизация, продакшн |

## 🎯 Заключение

CLI режим PixelFlow Studio обеспечивает:

- ✅ **Быстрое выполнение** проектов
- ✅ **Автоматизацию** обработки
- ✅ **Интеграцию** в скрипты и CI/CD
- ✅ **Профессиональный** подход к обработке изображений

**Теперь PixelFlow Studio готов как для разработки (GUI), так и для продакшена (CLI)!**