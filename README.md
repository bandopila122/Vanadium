
<p align="center">
  <img src="icons/NetworkPlace.ico" width="84" alt="Vanadium Logo">
</p>

<h1 align="center">Vanadium Archiver</h1>

<p align="center">
  <b>Современный архиватор с интерфейсом в стиле Windows</b><br>
  <i>A modern archive manager with Windows-style interface</i>
</p>

<p align="center">
  <a href="#-описание--about">🇷🇺 Русский</a> • <a href="#-about">🇬 English</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.1.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/python-3.14-yellow" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/platform-Windows-lightgrey" alt="Platform">
</p>

---

## 🇷🇺 Описание -- About

**Vanadium Archiver** — это современный архиватор с открытым исходным кодом, написанный на Python с использованием PyQt6. Программа сочетает в себе функциональность классических архиваторов и эстетику интерфейсов Windows разных эпох.

### ✨ Возможности

- 📦 **Работа с архивами**: ZIP, TAR, GZ, BZ2, TGZ, TAR.BZ2
- 📂 **Виртуальная навигация** — заходите внутрь папок в архивах двойным кликом
- 🎨 **Настраиваемые темы оформления** в ретро и современном стилях
- 🌍 **Локализация**: русский и английский языки
- 🔍 **Быстрый поиск** файлов по имени
- 🖱️ **Drag & Drop** — перетаскивание файлов прямо в окно
- 🎯 **Системные иконки Windows** — как в проводнике
- ⬆️ **Навигация** — кнопки Вверх, Назад, Вперёд
- 🔒 **Скрытие файлов** — скрытые и системные по умолчанию не видны
- 🗑️ **Автоочистка** — временные файлы удаляются автоматически
- 🛡️ **Защита** — нельзя случайно заархивировать архив в самого себя

### 🚀 Установка

#### Из исходного кода

```bash
git clone https://github.com/bandopila122/Vanadium.git
cd Vanadium
pip install PyQt6
python main.py
```

#### Из релиза

Скачайте последнюю версию со страницы [Releases](https://github.com/bandopila122/Vanadium/releases).

### 📁 Структура проекта

```
Vanadium/
├── main.py              # Логика приложения
├── design.py            # UI-компоненты, темы, диалоги, локализация
├── icons/               # Иконки приложения
│   └── NetworkPlace.ico
├── themes/              # Файлы тем (.qss)
│   ├── win10.qss
│   ├── winxp.qss
│   └── win9x.qss
├── locales/             # Локализация (.json)
│   ├── ru.json
│   └── en.json
```
└── [docs](https://github.com/bandopila122/Vanadium/tree/main/docs)


### 🛠️ Технологии и зависимости

- **[Python 3.14](https://www.python.org/)** — основной язык программирования ([PSF License v2](https://docs.python.org/3/license.html))
- **[PyQt6](https://www.riverbankcomputing.com/software/pyqt/)** — графический интерфейс ([GNU GPL v3](https://www.gnu.org/licenses/gpl-3.0.html))
- **Стандартные библиотеки Python** (`zipfile`, `tarfile`, `ctypes`, `shutil`)

> ⚠️ **Важно:** PyQt6 распространяется под GNU GPL v3. Сам Vanadium Archiver остаётся под лицензией MIT, но при дистрибуции бинарных файлов необходимо учитывать условия GPL.

---

## 🇬 About

**Vanadium Archiver** is a modern open-source archive manager written in Python using PyQt6. It combines the functionality of classic archivers with the aesthetics of different Windows eras.

### ✨ Features

- 📦 **Archive support**: ZIP, TAR, GZ, BZ2, TGZ, TAR.BZ2
- 📂 **Virtual navigation** — enter folders inside archives with double-click
- 🎨 **Customizable themes** in retro and modern styles
- 🌍 **Localization**: Russian and English
- 🔍 **Fast search** by file name
- 🖱️ **Drag & Drop** — drop files right into the window
- 🎯 **Windows system icons** — just like in Explorer
- ⬆️ **Navigation** — Up, Back, Forward buttons
- 🔒 **Hidden files** — hidden and system files hidden by default
- 🗑️ **Auto-clean** — temp files removed automatically
- 🛡️ **Protection** — can't accidentally archive an archive into itself

### 🚀 Installation

#### From source

```bash
git clone https://github.com/bandopila122/Vanadium.git
cd Vanadium
pip install PyQt6
python main.py
```

#### From release

Download the latest version from the [Releases](https://github.com/bandopila122/Vanadium/releases) page.

### 📁 Project Structure

```
Vanadium/
├── main.py              # Application logic
├── design.py            # UI components, themes, dialogs, localization
├── icons/               # Application icons
│   └── NetworkPlace.ico
├── themes/              # Theme files (.qss)
│   ├── win10.qss
│   ├── winxp.qss
│   └── win9x.qss
└── locales/             # Localization (.json)
│   ├── ru.json
│   └── en.json
```
└── [docs](https://github.com/bandopila122/Vanadium/tree/main/docs)


### 🛠️ Technologies and Dependencies

- **[Python 3.14](https://www.python.org/)** — main programming language ([PSF License v2](https://docs.python.org/3/license.html))
- **[PyQt6](https://www.riverbankcomputing.com/software/pyqt/)** — GUI framework ([GNU GPL v3](https://www.gnu.org/licenses/gpl-3.0.html))
- **Python standard libraries** (`zipfile`, `tarfile`, `ctypes`, `shutil`)

> ⚠️ **Important:** PyQt6 is distributed under GNU GPL v3. Vanadium Archiver itself remains under the MIT license, but binary distribution must comply with GPL requirements.

---

## 📜 License / Лицензия

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

Этот проект распространяется по лицензии **MIT**. Подробности в файле [LICENSE](LICENSE).

---

<p align="center">
  Made with 💎 by <a href="https://github.com/bandopila122">bandopila122</a>
</p>

