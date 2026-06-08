# 📚 Vanadium Archiver — Документация / Documentation

Добро пожаловать в техническую документацию **Vanadium Archiver v1.1.0**.  
Welcome to the technical documentation for **Vanadium Archiver v1.1.0**.

---

## 🇷🇺 Структура документации

Эта папка содержит подробное описание архитектуры, компонентов и ресурсов проекта. Каждый файл предназначен для разработчиков, форкающих репозиторий или желающих глубже понять внутреннее устройство программы.

| Файл | Описание |
|------|----------|
| [main.py](main.md) | Ядро приложения: бизнес-логика, работа с архивами, навигация, безопасность |
| [design.py](design.md) | Визуальный слой: темы, локализация, диалоговые окна, ресурсы |
| [resources.md](resources.md) | Вспомогательные файлы: иконки, QSS-темы, JSON-переводы |

### Для кого эта документация?
-   **Разработчики**, планирующие форк или модификацию кода
-   **Контрибьюторы**, добавляющие новые функции или языки
-   **Исследователи**, изучающие архитектуру PyQt6-приложений с разделением логики и UI

### Ключевые архитектурные решения
-   **Полное разделение ответственности**: `main.py` не содержит ни строк текста, ни стилей. Весь UI вынесен в `design.py` и внешние файлы.
-   **Fallback-локализация**: Русский язык является базовым словарём. При отсутствии ключа в целевом языке автоматически подставляется русский текст — программа никогда не упадёт из-за неполного перевода.
-   **Динамическая загрузка тем**: Стили читаются из `.qss` файлов во время выполнения. Новые темы можно добавлять без перекомпиляции Python-кода.
-   **Безопасность операций**: Удаление файлов через временный `.tmp` архив с проверкой целостности; защита от самоархивирования через `Path.resolve()`; мультикодировочный парсер (UTF-8 → CP866) для старых архивов.

---

## 🇬 Documentation Structure

This folder contains detailed descriptions of the project's architecture, components, and resources. Each file is intended for developers forking the repository or wishing to understand the program's internals in depth.

| File | Description |
|------|-------------|
| [main.py](main.md) | Application core: business logic, archive operations, navigation, safety |
| [design.py](design.md) | Visual layer: themes, localization, dialogs, resources |
| [resources.md](resources.md) | Auxiliary files: icons, QSS themes, JSON translations |

### Who is this documentation for?
-   **Developers** planning to fork or modify the code
-   **Contributors** adding new features or languages
-   **Researchers** studying PyQt6 application architecture with separated logic and UI

### Key architectural decisions
-   **Complete separation of concerns**: `main.py` contains no text strings or styles. All UI is externalized to `design.py` and external files.
-   **Fallback localization**: Russian is the base dictionary. Missing keys in the target language automatically fall back to Russian text — the program never crashes due to incomplete translation.
-   **Dynamic theme loading**: Styles are read from `.qss` files at runtime. New themes can be added without recompiling Python code.
-   **Operation safety**: File deletion via temporary `.tmp` archive with integrity verification; self-archiving protection via `Path.resolve()`; multi-encoding parser (UTF-8 → CP866) for legacy archives.

---

> 💡 **Совет / Tip:** Начинайте чтение с [`main.py`](main.md), чтобы понять общую архитектуру, затем переходите к [`design.py`](design.md) для изучения визуального слоя, и завершайте [`resources.md`](resources.md) для работы с ресурсами.  
> 💡 **Tip:** Start with [`main.py`](main.md) to understand the overall architecture, then proceed to [`design.py`](design.md) for the visual layer, and finish with [`resources.md`](resources.md) for resource management.

---

<p align="center">
  Made with 💎 by <a href="https://github.com/bandopila122">bandopila122</a> • <a href="../README.md">← Назад в README / Back to README</a>
</p>