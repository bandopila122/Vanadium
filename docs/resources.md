

## 🇷🇺 Вспомогательные ресурсы / Auxiliary Resources

### 📁 icons/ — Иконки приложения
**Назначение:** Хранилище графических ресурсов интерфейса. Все иконки хранятся в формате `.ico` или `.png` и загружаются динамически через `QFileIconProvider` или прямые пути.

**Содержимое:**
-   `NetworkPlace.ico` — основная иконка окна приложения (отображается в заголовке и на панели задач)
-   `add.ico`, `extract.ico`, `folder.ico`, `delete.ico`, `search.ico`, `settings.ico` — иконки для кнопок панели инструментов

**Использование при форке:** Замените файлы с сохранением оригинальных имён, чтобы не менять код. Рекомендуемый размер: 32×32 px для тулбара, 16×16 px для дерева папок. Для добавления новых иконок обновите словарь `icon_names` в методе `setup_icons()` класса `VanadiumArchiver`.

---

### 📁 themes/ — Файлы тем оформления
**Назначение:** Внешние таблицы стилей Qt Style Sheets (QSS), определяющие внешний вид всех элементов интерфейса. Позволяют менять оформление без перекомпиляции Python-кода.

**Содержимое:**
-   `win10.qss` — современный стиль с плоскими элементами, скруглёнными углами и акцентным синим цветом (#0078D4)
-   `winxp.qss` — ностальгический стиль с градиентами, объёмными рамками и тёплой бежевой палитрой
-   `win9x.qss` — ретро-стиль с классическими серыми кнопками, рельефными границами и шрифтом MS Sans Serif

**Технические особенности:**
-   Стили загружаются из файла во время выполнения через `ThemeManager.apply()`
-   Каждый QSS-файл должен содержать стили для всех ключевых виджетов: `QMainWindow`, `QToolBar`, `QTableWidget`, `QPushButton`, `QLineEdit`, `QMenu`, `QDialog`
-   Шрифт задаётся отдельно в Python-коде (`ThemeManager`), а не в QSS, для корректной работы `setFont()`
-   Градиенты XP-темы используют синтаксис `qlineargradient(x1:0, y1:0, x2:0, y2:1, ...)`

**Добавление новой темы:** Создайте файл `mytheme.qss`, добавьте запись в `ThemeManager.THEMES` и переведите название в JSON-файлах локализации.

---

### 📁 locales/ — Файлы локализации
**Назначение:** JSON-словари переводов пользовательского интерфейса. Отделяют текстовый контент от кода, позволяя добавлять языки без изменения Python-файлов.

**Содержимое:**
-   `ru.json` — русский язык (базовый fallback-словарь)
-   `en.json` — английский язык

**Структура JSON:**
```json
{
    "app_title": "Vanadium Archiver",
    "menu_file": "Файл",
    "msg_added": "Добавлено"
}
```

**Технические особенности:**
-   При загрузке языка сначала читается `ru.json`, затем поверх накладывается целевой язык. Это гарантирует отсутствие `KeyError` при неполном переводе
-   Поддержка форматирования строк через `translator.t("key", arg1, arg2)` с использованием `{}` плейсхолдеров
-   Кодировка файлов: UTF-8 без BOM
-   Ключи должны быть идентичны во всех языковых файлах; отсутствующие ключи автоматически подставляются из русского словаря

**Добавление нового языка:** Скопируйте `ru.json` → `fr.json`, переведите значения, добавьте пару `('fr', 'lang_fr')` в группу языков `SettingsDialog` и ключ `"lang_fr": "Français"` во все существующие JSON-файлы.

---

## 🇬 Auxiliary Resources

### 📁 icons/ — Application Icons
**Purpose:** Storage of interface graphic resources. All icons are stored in `.ico` or `.png` format and loaded dynamically via `QFileIconProvider` or direct paths.

**Contents:**
-   `NetworkPlace.ico` — main application window icon (displayed in title bar and taskbar)
-   `add.ico`, `extract.ico`, `folder.ico`, `delete.ico`, `search.ico`, `settings.ico` — toolbar button icons

**Usage when forking:** Replace files while keeping original names to avoid code changes. Recommended size: 32×32 px for toolbar, 16×16 px for folder tree. To add new icons, update the `icon_names` dictionary in `VanadiumArchiver.setup_icons()`.

---

### 📁 themes/ — Theme Files
**Purpose:** External Qt Style Sheets (QSS) defining the appearance of all interface elements. Allows changing the look without recompiling Python code.

**Contents:**
-   `win10.qss` — modern style with flat elements, rounded corners, and accent blue (#0078D4)
-   `winxp.qss` — nostalgic style with gradients, raised borders, and warm beige palette
-   `win9x.qss` — retro style with classic grey buttons, beveled edges, and MS Sans Serif font

**Technical details:**
-   Styles are loaded from file at runtime via `ThemeManager.apply()`
-   Each QSS file must contain styles for all key widgets: `QMainWindow`, `QToolBar`, `QTableWidget`, `QPushButton`, `QLineEdit`, `QMenu`, `QDialog`
-   Font is set separately in Python code (`ThemeManager`), not in QSS, for correct `setFont()` operation
-   XP theme gradients use syntax `qlineargradient(x1:0, y1:0, x2:0, y2:1, ...)`

**Adding a new theme:** Create `mytheme.qss`, add entry to `ThemeManager.THEMES`, and translate the name in localization JSON files.

---

### 📁 locales/ — Localization Files
**Purpose:** JSON translation dictionaries for the user interface. Separate textual content from code, enabling language additions without modifying Python files.

**Contents:**
-   `ru.json` — Russian language (base fallback dictionary)
-   `en.json` — English language

**JSON structure:**
```json
{
    "app_title": "Vanadium Archiver",
    "menu_file": "File",
    "msg_added": "Added"
}
```

**Technical details:**
-   When loading a language, `ru.json` is read first, then the target language is overlaid on top. This guarantees no `KeyError` with incomplete translations
-   String formatting supported via `translator.t("key", arg1, arg2)` using `{}` placeholders
-   File encoding: UTF-8 without BOM
-   Keys must be identical across all language files; missing keys automatically fall back to the Russian dictionary

**Adding a new language:** Copy `ru.json` → `fr.json`, translate values, add `('fr', 'lang_fr')` pair to `SettingsDialog` language group, and add `"lang_fr": "Français"` key to all existing JSON files.