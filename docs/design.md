
## 🇷🇺 design.py — Визуальный слой и ресурсы / Visual Layer & Resources

### Для чего нужен этот файл
`design.py` является **централизованным хранилищем всех визуальных и текстовых ресурсов** Vanadium Archiver. Этот файл полностью отделён от бизнес-логики (`main.py`) и отвечает исключительно за внешний вид, локализацию и диалоговые окна. Такая архитектура позволяет менять темы, добавлять языки или редактировать интерфейс без риска сломать функциональность программы.

### Что он содержит
-   **Класс `Translator`**: Движок локализации, который загружает JSON-файлы из папки `locales/`, обеспечивает fallback на русский язык при отсутствии ключа и поддерживает динамическую смену языка через метод `set_language()`.
-   **Класс `ThemeManager`**: Менеджер тем, который считывает QSS-стили из папки `themes/` и применяет соответствующий шрифт (Segoe UI, Tahoma или MS Sans Serif) в зависимости от выбранной темы.
-   **Диалоговые окна**:
    -   `WelcomeDialog`: Приветственное окно со списком возможностей, советами и чекбоксом «Больше не показывать».
    -   `MigrationDialog`: Окно миграции настроек с выбором между конвертацией старых данных и чистым стартом.
    -   `SettingsDialog`: Полноценное окно настроек с переключателями скрытых файлов, радио-кнопками тем и языков, кнопкой очистки темпа и блоком «О программе».
-   **Константа `TEMP_DIR`**: Глобальная переменная пути к временной папке `%USERPROFILE%/VanadiumTemp`.

### Как использовать при форке
1.  **Добавление новой темы**: Создайте файл `mytheme.qss` в папке `themes/`, добавьте запись `'mytheme': 'theme_mytheme'` в словарь `THEMES` класса `ThemeManager` и переведите название темы в обоих JSON-файлах.
2.  **Добавление нового языка**: Скопируйте `ru.json` как `fr.json`, переведите значения ключей и добавьте пару `('fr', 'lang_fr')` в группу языков внутри `SettingsDialog`.
3.  **Изменение интерфейса**: Редактируйте HTML-разметку приветственного окна или стили QSS прямо в этом файле. Все изменения мгновенно отражаются после перезапуска.
4.  **Расширение переводов**: Добавьте новые ключи в оба JSON-файла одновременно, чтобы избежать ошибок `KeyError` при переключении языка.

### Примеры использования
```python
# Инициализация переводчика
translator = Translator(base_path, language='en')

# Получение локализованной строки
title = translator.t("app_title")  # Вернёт "Vanadium Archiver"

# Применение темы
ThemeManager.apply(window, theme_name='winxp', base_path=base_path, translator=translator)

# Открытие настроек
dlg = SettingsDialog(parent=self, translator=translator, current_theme='win10', current_lang='ru')
if dlg.exec() == QDialog.DialogCode.Accepted:
    new_theme = dlg.get_selected_theme()
    new_lang = dlg.get_selected_language()
```

### Технические усложнения
-   **Fallback-система локализации**: При загрузке языка сначала читается `ru.json` как базовый словарь, затем поверх него накладывается целевой язык. Это гарантирует, что даже если в новом переводе пропущен какой-то ключ, программа не упадёт, а покажет текст на русском.
-   **Динамическая загрузка QSS**: Стили не захардкожены в Python-коде, а читаются из внешних `.qss` файлов во время выполнения. Это позволяет пользователям самостоятельно создавать и устанавливать темы без перекомпиляции программы.
-   **Изоляция состояния диалогов**: Все диалоги принимают `translator` как зависимость, но не хранят глобальное состояние. Выбор темы и языка возвращается через геттеры (`get_selected_theme()`, `get_selected_language()`), а не через прямое изменение атрибутов родителя.
-   **Безопасная очистка темпа**: Метод `clean_temp_now()` использует `rglob('*')` с предварительным приведением к списку и отдельными блоками `try/except` для каждого файла, чтобы заблокированные процессы не прерывали очистку остальных элементов.
-   **Адаптивная типографика**: `ThemeManager` меняет не только stylesheet, но и глобальный шрифт приложения через `setFont()`, обеспечивая аутентичность каждой эпохи Windows (8pt для 9X/XP, 9pt для Win10).

---

## 🇬 design.py — Visual Layer & Resources

### Purpose of this file
`design.py` serves as the **centralized repository for all visual and textual resources** in Vanadium Archiver. This file is completely decoupled from business logic (`main.py`) and handles exclusively appearance, localization, and dialog windows. Such architecture allows changing themes, adding languages, or editing the interface without risking breaking program functionality.

### What it contains
-   **`Translator` class**: Localization engine that loads JSON files from `locales/`, provides Russian fallback for missing keys, and supports dynamic language switching via `set_language()`.
-   **`ThemeManager` class**: Theme manager that reads QSS styles from `themes/` and applies the corresponding font (Segoe UI, Tahoma, or MS Sans Serif) based on the selected theme.
-   **Dialog windows**:
    -   `WelcomeDialog`: Welcome screen with feature list, tips, and "Don't show again" checkbox.
    -   `MigrationDialog`: Settings migration dialog with choice between converting old data and fresh start.
    -   `SettingsDialog`: Full settings window with hidden file toggles, theme/language radio buttons, temp cleanup button, and About section.
-   **`TEMP_DIR` constant**: Global variable for the temporary folder path `%USERPROFILE%/VanadiumTemp`.

### How to use when forking
1.  **Adding a new theme**: Create `mytheme.qss` in `themes/`, add `'mytheme': 'theme_mytheme'` to `ThemeManager.THEMES`, and translate the theme name in both JSON files.
2.  **Adding a new language**: Copy `ru.json` as `fr.json`, translate key values, and add `('fr', 'lang_fr')` to the language group inside `SettingsDialog`.
3.  **Editing the interface**: Modify welcome dialog HTML markup or QSS styles directly in this file. All changes take effect immediately after restart.
4.  **Extending translations**: Add new keys to both JSON files simultaneously to avoid `KeyError` exceptions during language switching.

### Usage examples
```python
# Initialize translator
translator = Translator(base_path, language='en')

# Get localized string
title = translator.t("app_title")  # Returns "Vanadium Archiver"

# Apply theme
ThemeManager.apply(window, theme_name='winxp', base_path=base_path, translator=translator)

# Open settings
dlg = SettingsDialog(parent=self, translator=translator, current_theme='win10', current_lang='ru')
if dlg.exec() == QDialog.DialogCode.Accepted:
    new_theme = dlg.get_selected_theme()
    new_lang = dlg.get_selected_language()
```

### Technical complexities
-   **Localization fallback system**: When loading a language, `ru.json` is read first as the base dictionary, then the target language is overlaid on top. This guarantees that even if a key is missing in the new translation, the program won't crash and will display Russian text instead.
-   **Dynamic QSS loading**: Styles are not hardcoded in Python code but read from external `.qss` files at runtime. This allows users to create and install custom themes without recompiling the program.
-   **Dialog state isolation**: All dialogs accept `translator` as a dependency but do not store global state. Theme and language selections are returned through getters (`get_selected_theme()`, `get_selected_language()`) rather than directly modifying parent attributes.
-   **Safe temp cleanup**: The `clean_temp_now()` method uses `rglob('*')` pre-converted to a list with individual `try/except` blocks per file, ensuring locked processes don't interrupt cleanup of remaining items.
-   **Adaptive typography**: `ThemeManager` changes not only the stylesheet but also the application's global font via `setFont()`, ensuring authenticity of each Windows era (8pt for 9X/XP, 9pt for Win10).