

## 🇷🇺 main.py — Ядро приложения / Application Core

### Для чего нужен этот файл
`main.py` является **точкой входа** и **логическим ядром** Vanadium Archiver. Он отвечает за всю бизнес-логику программы: работу с файловой системой, управление архивами, навигацию, обработку событий интерфейса и взаимодействие с пользователем. В отличие от `design.py`, этот файл не содержит визуальных стилей или текстовых строк — он оперирует только данными и действиями.

### Что он содержит
-   **Класс `VanadiumArchiver(QMainWindow)`**: Основной класс окна приложения, включающий создание UI, меню, панели инструментов и таблицы файлов.
-   **Функции утилиты**: `is_hidden_or_system()` (проверка атрибутов файлов), `cleanup_temp_folder()` (автоматическая очистка временных файлов), `remove_empty_parent_dirs()` (удаление пустых папок после извлечения).
-   **Логика работы с архивами**: Методы `open_archive()`, `parse_archive_item()`, `create_virtual_folders()`, `refresh_current_view()` для построения виртуальной файловой системы внутри ZIP/TAR.
-   **Операции над файлами**: Добавление (`add_files_to_archive`), извлечение (`extract_files`, `extract_single_file`), удаление (`delete_files`) и тестирование целостности.
-   **Навигация и история**: Управление стеком переходов, кнопками «Вверх/Назад/Вперёд» и адресной строкой.
-   **Защита от ошибок**: Проверки на самоархивирование, безопасная замена файлов при удалении через `.tmp`, обработка кодировок CP866/UTF-8 для старых архивов.
-   **Точка входа `main()`**: Инициализация `QApplication`, загрузка настроек, создание экземпляра `Translator` и запуск главного цикла.

### Как использовать при форке
1.  Убедитесь, что рядом с `main.py` находятся папки `icons/`, `themes/`, `locales/` и файл `design.py`.
2.  Установите зависимости: `pip install PyQt6`.
3.  Запустите: `python main.py`.
4.  При модификации логики обращайтесь к методам класса `VanadiumArchiver`. Все тексты и стили вынесены во внешние файлы и `design.py` — не хардкодьте строки в этом файле.
5.  Если добавляете новые операции с архивами, расширяйте методы `add_files_to_archive()` и `extract_files()`, сохраняя существующие проверки безопасности.

### Примеры использования
```bash
# Запуск из исходного кода
cd Vanadium
python main.py

# Сборка в исполняемый файл
pyinstaller --onefile --windowed --add-data "icons;icons" --add-data "themes;themes" --add-data "locales;locales" main.py
```

### Технические усложнения
-   **Виртуальная файловая система**: Архивы не распаковываются на диск целиком. Программа парсит плоский список путей из заголовка архива и динамически строит дерево папок в памяти. Это позволяет работать с гигабайтными архивами без заполнения диска.
-   **Безопасное удаление**: Операция удаления файлов из ZIP реализована через создание временного `.tmp` архива с проверкой его целостности перед заменой оригинала. Это предотвращает потерю данных при сбоях питания или нехватке места.
-   **Защита от рекурсии**: Перед добавлением папки в архив каждый файл проверяется через `Path.resolve()` на совпадение с путём текущего открытого архива. Для TAR используется специальный `filter`-колбэк, отсекающий сам архив при рекурсивном обходе.
-   **Мультикодировочный парсер**: Имена файлов декодируются сначала как UTF-8, затем как CP866 (для совместимости со старыми Windows-архиваторами). Сырые байты пути сохраняются отдельно для корректного извлечения и удаления.
-   **Разделение ответственности**: Весь UI-код, темы и переводы вынесены в `design.py` и JSON/QSS файлы. `main.py` остаётся чистым слоем бизнес-логики, что упрощает поддержку и локализацию.

---

## 🇬 main.py — Application Core

### Purpose of this file
`main.py` serves as the **entry point** and **logical core** of Vanadium Archiver. It handles all business logic: file system operations, archive management, navigation, event processing, and user interaction. Unlike `design.py`, this file contains no visual styles or text strings — it operates solely on data and actions.

### What it contains
-   **`VanadiumArchiver(QMainWindow)` class**: The main application window class, including UI creation, menus, toolbar, and file table.
-   **Utility functions**: `is_hidden_or_system()` (file attribute check), `cleanup_temp_folder()` (automatic temp cleanup), `remove_empty_parent_dirs()` (empty folder removal after extraction).
-   **Archive logic**: Methods `open_archive()`, `parse_archive_item()`, `create_virtual_folders()`, `refresh_current_view()` for building a virtual file system inside ZIP/TAR archives.
-   **File operations**: Adding (`add_files_to_archive`), extracting (`extract_files`, `extract_single_file`), deleting (`delete_files`), and integrity testing.
-   **Navigation & history**: Management of the navigation stack, Up/Back/Forward buttons, and address bar.
-   **Error protection**: Self-archiving checks, safe file replacement via `.tmp` during deletion, CP866/UTF-8 encoding handling for legacy archives.
-   **`main()` entry point**: `QApplication` initialization, settings loading, `Translator` instantiation, and main loop execution.

### How to use when forking
1.  Ensure `icons/`, `themes/`, `locales/` folders and `design.py` are present alongside `main.py`.
2.  Install dependencies: `pip install PyQt6`.
3.  Run: `python main.py`.
4.  When modifying logic, refer to `VanadiumArchiver` class methods. All texts and styles are externalized — do not hardcode strings in this file.
5.  If adding new archive operations, extend `add_files_to_archive()` and `extract_files()` while preserving existing safety checks.

### Usage examples
```bash
# Run from source
cd Vanadium
python main.py

# Build executable
pyinstaller --onefile --windowed --add-data "icons;icons" --add-data "themes;themes" --add-data "locales;locales" main.py
```

### Technical complexities
-   **Virtual file system**: Archives are never fully extracted to disk. The program parses the flat path list from the archive header and dynamically builds a folder tree in memory. This enables working with multi-gigabyte archives without filling the disk.
-   **Safe deletion**: File deletion from ZIP is implemented by creating a temporary `.tmp` archive with integrity verification before replacing the original. This prevents data loss during power failures or disk full scenarios.
-   **Recursion protection**: Before adding a folder to an archive, every file is checked via `Path.resolve()` against the current archive's path. For TAR, a special `filter` callback excludes the archive itself during recursive traversal.
-   **Multi-encoding parser**: File names are decoded first as UTF-8, then as CP866 (for compatibility with legacy Windows archivers). Raw path bytes are stored separately for correct extraction and deletion.
-   **Separation of concerns**: All UI code, themes, and translations are externalized to `design.py` and JSON/QSS files. `main.py` remains a clean business logic layer, simplifying maintenance and localization.
