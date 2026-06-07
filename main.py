import os
import sys
import zipfile
import tarfile
import gzip
import bz2
import ctypes
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QTableWidget, QTableWidgetItem, QHeaderView,
    QStatusBar, QFileDialog, QMessageBox, QAbstractItemView,
    QMenu, QTreeWidget, QTreeWidgetItem, QSplitter, QLabel, QFrame,
    QInputDialog, QLineEdit, QToolButton, QPushButton, QFileIconProvider,
    QDialog, QCheckBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QSize, QSettings, QFileInfo
from PyQt6.QtGui import QIcon, QAction, QFont, QDragEnterEvent, QDropEvent


TEMP_DIR = Path.home() / "VanadiumTemp"


def is_hidden_or_system(filepath):
    try:
        if sys.platform == 'win32':
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(filepath))
            if attrs == -1:
                return False
            return bool(attrs & 2) or bool(attrs & 4)
        else:
            return Path(filepath).name.startswith('.')
    except:
        return False


def cleanup_temp_folder():
    try:
        if not TEMP_DIR.exists():
            return
        now = datetime.now()
        failed_files = 0
        for item in list(TEMP_DIR.rglob('*')):
            try:
                mtime = datetime.fromtimestamp(item.stat().st_mtime)
                if (now - mtime) <= timedelta(hours=24):
                    continue
                if item.is_file() or item.is_symlink():
                    try:
                        item.unlink()
                    except (PermissionError, OSError):
                        failed_files += 1
                    except:
                        failed_files += 1
            except (PermissionError, OSError):
                failed_files += 1
            except:
                pass
        for item in list(TEMP_DIR.rglob('*')):
            try:
                if item.is_dir() and not any(item.iterdir()):
                    item.rmdir()
            except:
                pass
        if failed_files > 0:
            print(f"Пропущено занятых файлов: {failed_files}")
    except Exception as e:
        print(f"Ошибка очистки темпа: {e}")


def remove_empty_parent_dirs(file_path, stop_at_dir):
    try:
        parent = Path(file_path).parent
        while parent != stop_at_dir and parent.exists():
            try:
                contents = list(parent.iterdir())
                if contents:
                    break
                parent.rmdir()
                parent = parent.parent
            except (PermissionError, OSError):
                break
            except:
                break
    except:
        pass


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setFixedSize(450, 420)
        self.setStyleSheet("""
            QDialog { background-color: #F3F3F3; }
            QLabel { font-family: 'Segoe UI'; font-size: 10pt; color: #333; }
            QCheckBox { font-family: 'Segoe UI'; font-size: 10pt; spacing: 10px; padding: 5px; }
            QPushButton {
                background-color: #0078D4; color: white; border: none;
                padding: 8px 16px; border-radius: 4px; font-family: 'Segoe UI';
            }
            QPushButton:hover { background-color: #006CBE; }
        """)
        layout = QVBoxLayout(self)
        header = QLabel("Параметры отображения")
        header.setStyleSheet("font-weight: bold; font-size: 12pt; margin-bottom: 10px;")
        layout.addWidget(header)
        self.show_hidden_checkbox = QCheckBox("Показывать скрытые файлы и папки")
        self.show_system_checkbox = QCheckBox("Показывать системные файлы")
        layout.addWidget(self.show_hidden_checkbox)
        layout.addWidget(self.show_system_checkbox)
        layout.addSpacing(10)
        temp_header = QLabel("Временные файлы")
        temp_header.setStyleSheet("font-weight: bold; font-size: 11pt; margin-top: 5px;")
        layout.addWidget(temp_header)
        temp_btn = QPushButton("Очистить временную папку")
        temp_btn.clicked.connect(self.clean_temp_now)
        layout.addWidget(temp_btn)
        temp_info = QLabel(f"Папка: {TEMP_DIR}")
        temp_info.setStyleSheet("color: #666; font-size: 9pt;")
        temp_info.setWordWrap(True)
        layout.addWidget(temp_info)
        layout.addSpacing(10)
        about_header = QLabel("О программе")
        about_header.setStyleSheet("font-weight: bold; font-size: 11pt; margin-top: 10px;")
        layout.addWidget(about_header)
        about_text = QLabel(
            "<b>Vanadium Archiver v1.0.4</b><br><br>"
            "Простой архиватор<br>"
            "Поддерживаемые форматы: ZIP, TAR, GZ, BZ2<br><br>"
            "Лицензия: MIT<br>"
            "Python 3.14 (PSF License)<br>"
            "PyQt6 (GNU GPL v3)<br><br>"
            "Подробнее:<br>"
            "<a href='https://github.com/bandopila122/Vanadium'>GitHub Repository</a><br>"
            "<a href='https://github.com/bandopila122/Vanadium/blob/main/README.md'>README</a><br>"
            "<a href='https://github.com/bandopila122/Vanadium/blob/main/LICENSE'>LICENSE</a>"
        )
        about_text.setOpenExternalLinks(True)
        about_text.setWordWrap(True)
        about_text.setStyleSheet("padding: 10px; background-color: white; border-radius: 4px;")
        layout.addWidget(about_text)
        layout.addStretch()
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.load_settings()

    def clean_temp_now(self):
        try:
            if TEMP_DIR.exists():
                failed = 0
                for item in list(TEMP_DIR.rglob('*')):
                    try:
                        if item.is_file() or item.is_symlink():
                            item.unlink()
                    except (PermissionError, OSError):
                        failed += 1
                    except:
                        pass
                for item in list(TEMP_DIR.rglob('*')):
                    try:
                        if item.is_dir() and not any(item.iterdir()):
                            item.rmdir()
                    except:
                        pass
                if failed > 0:
                    QMessageBox.warning(self, "Частично", f"Очищено, но {failed} файлов заняты процессами")
                else:
                    QMessageBox.information(self, "Успех", "Временная папка очищена")
            else:
                QMessageBox.information(self, "Информация", "Папка пуста")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def load_settings(self):
        settings = QSettings("VanaArchiver", "Settings")
        self.show_hidden_checkbox.setChecked(settings.value("show_hidden_files", False, type=bool))
        self.show_system_checkbox.setChecked(settings.value("show_system_files", False, type=bool))

    def save_settings(self):
        settings = QSettings("VanaArchiver", "Settings")
        settings.setValue("show_hidden_files", self.show_hidden_checkbox.isChecked())
        settings.setValue("show_system_files", self.show_system_checkbox.isChecked())


class VanadiumArchiver(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vanadium Archiver")
        self.setGeometry(100, 100, 1200, 800)
        self.setAcceptDrops(True)
        self.base_path = Path(sys.argv[0]).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
        self.icons_path = self.base_path / "icons"
        self.icon_provider = QFileIconProvider()
        icon_path = self.icons_path / "networkplace.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.current_archive = None
        self.archive_type = None
        self.files_list = []
        self.current_virtual_path = ""
        self.navigation_history = []
        self.current_history_index = -1
        self.is_navigating = False
        self.setup_style()
        self.setup_icons()
        self.create_ui()
        self.create_menus()
        self.create_toolbar()
        self.settings = QSettings("VanaArchiver", "Settings")
        self.show_hidden_files = self.settings.value("show_hidden_files", False, type=bool)
        self.show_system_files = self.settings.value("show_system_files", False, type=bool)
        self.open_folder(Path.home())

    def setup_style(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #F3F3F3; }
            QToolBar { background-color: #F3F3F3; border: none; padding: 4px; spacing: 5px; }
            QToolButton { background-color: transparent; border: 1px solid transparent; padding: 6px; border-radius: 4px; font-family: 'Segoe UI'; }
            QToolButton:hover { background-color: #E5E5E5; border: 1px solid #D0D0D0; }
            QTableWidget { background-color: white; border: 1px solid #E0E0E0; gridline-color: #F0F0F0; selection-background-color: #0078D4; selection-color: white; font-family: 'Segoe UI'; font-size: 9pt; }
            QHeaderView::section { background-color: #F3F3F3; border: none; border-right: 1px solid #E0E0E0; padding: 4px; font-weight: 600; color: #444; font-family: 'Segoe UI'; }
            QTreeWidget { background-color: white; border: 1px solid #E0E0E0; selection-background-color: #0078D4; selection-color: white; font-family: 'Segoe UI'; font-size: 9pt; }
            QStatusBar { background-color: #F3F3F3; border-top: 1px solid #E0E0E0; color: #555; font-family: 'Segoe UI'; }
            QLineEdit { background-color: white; border: 1px solid #D0D0D0; padding: 4px 8px; border-radius: 4px; font-family: 'Segoe UI'; font-size: 9pt; }
            QLineEdit:focus { border: 1px solid #0078D4; }
            QPushButton { background-color: #0078D4; color: white; border: none; padding: 4px 12px; border-radius: 4px; font-family: 'Segoe UI'; }
            QPushButton:hover { background-color: #006CBE; }
            QMenu { background-color: white; border: 1px solid #E0E0E0; font-family: 'Segoe UI'; font-size: 9pt; }
            QMenu::item:selected { background-color: #0078D4; color: white; }
        """)
        font = QFont("Segoe UI", 9)
        self.setFont(font)

    def setup_icons(self):
        self.icons = {}
        icon_names = ['add', 'extract', 'folder', 'delete', 'settings', 'search']
        if not self.icons_path.exists():
            return
        for icon_name in icon_names:
            icon_loaded = False
            for ext in ['.ico', '.png', '.gif']:
                if icon_loaded:
                    break
                for name_variant in [icon_name, icon_name.capitalize(), icon_name.upper(), icon_name.title()]:
                    icon_path = self.icons_path / f"{name_variant}{ext}"
                    if icon_path.exists():
                        icon = QIcon(str(icon_path))
                        if not icon.isNull():
                            self.icons[icon_name] = icon
                            icon_loaded = True
                            break

    def create_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        address_frame = QFrame()
        address_frame.setFixedHeight(36)
        address_frame.setStyleSheet("background-color: #F3F3F3; border-bottom: 1px solid #E0E0E0;")
        address_layout = QHBoxLayout(address_frame)
        address_layout.setContentsMargins(8, 4, 8, 4)
        address_layout.setSpacing(6)
        up_btn = QToolButton()
        up_btn.setText("⬆")
        up_btn.setFixedSize(28, 28)
        up_btn.setToolTip("На уровень выше")
        up_btn.clicked.connect(self.go_up_folder)
        address_layout.addWidget(up_btn)
        self.address_entry = QLineEdit()
        self.address_entry.returnPressed.connect(self.go_to_path)
        address_layout.addWidget(self.address_entry, 1)
        go_btn = QPushButton("Перейти")
        go_btn.clicked.connect(self.go_to_path)
        address_layout.addWidget(go_btn)
        main_layout.addWidget(address_frame)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderLabel("Папки")
        self.folder_tree.header().hide()
        self.folder_tree.setMinimumWidth(220)
        self.folder_tree.setIconSize(QSize(16, 16))
        splitter.addWidget(self.folder_tree)
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(5)
        self.file_table.setHorizontalHeaderLabels(['', 'Имя', 'Размер', 'Тип', 'Изменён'])
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.file_table.setColumnWidth(0, 30)
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.file_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.file_table.setIconSize(QSize(20, 20))
        self.file_table.setAcceptDrops(True)
        self.file_table.viewport().setAcceptDrops(True)
        splitter.addWidget(self.file_table)
        splitter.setSizes([250, 950])
        main_layout.addWidget(splitter)
        self.statusBar().showMessage("Готов")
        self.file_table.doubleClicked.connect(self.on_file_double_click)
        self.file_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_table.customContextMenuRequested.connect(self.show_context_menu)
        self.folder_tree.itemDoubleClicked.connect(self.on_folder_double_click)

    def create_menus(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")
        file_menu.addAction("Открыть архив...", self.open_archive_dialog)
        file_menu.addAction("Открыть папку...", self.open_folder_dialog)
        file_menu.addSeparator()
        file_menu.addAction("Выход", self.close)
        archive_menu = menubar.addMenu("Архив")
        archive_menu.addAction("Добавить файлы...", self.add_files)
        archive_menu.addAction("Добавить папку...", self.add_folder)
        archive_menu.addAction("Извлечь...", self.extract_files)
        archive_menu.addAction("Тест архива", self.test_archive)
        archive_menu.addSeparator()
        archive_menu.addAction("Удалить", self.delete_files)
        tools_menu = menubar.addMenu("Сервис")
        settings_action = QAction("Настройки...", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)

    def create_toolbar(self):
        toolbar = QToolBar()
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(toolbar)
        buttons = [
            ('add', 'Добавить', self.add_files),
            ('extract', 'Извлечь', self.extract_files),
            ('folder', 'Открыть', self.open_folder_dialog),
            ('delete', 'Удалить', self.delete_files),
            ('search', 'Поиск', self.search_files),
        ]
        for icon_name, text, command in buttons:
            action = QAction(text, self)
            if icon_name in self.icons:
                action.setIcon(self.icons[icon_name])
            else:
                if icon_name == 'add':
                    action.setIcon(self.icon_provider.icon(QFileIconProvider.IconType.File))
                elif icon_name == 'extract':
                    action.setIcon(self.icon_provider.icon(QFileIconProvider.IconType.Folder))
                elif icon_name == 'folder':
                    action.setIcon(self.icon_provider.icon(QFileIconProvider.IconType.Folder))
                elif icon_name == 'delete':
                    action.setIcon(self.icon_provider.icon(QFileIconProvider.IconType.File))
            action.triggered.connect(command)
            toolbar.addAction(action)

    def open_archive_dialog(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Открыть архив",
            str(Path.home()),
            "Архивы (*.zip *.rar *.7z *.tar *.tar.gz *.tgz *.tar.bz2 *.gz *.bz2);;Все файлы (*)"
        )
        if filename:
            self.open_archive(Path(filename))

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        files = [url.toLocalFile() for url in event.mimeData().urls() if url.toLocalFile()]
        if files:
            if self.current_archive:
                self.add_files_to_archive(files)
            else:
                first_file = Path(files[0])
                if first_file.is_dir():
                    self.open_folder(first_file)
                elif first_file.suffix.lower() in ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.tgz']:
                    self.open_archive(first_file)
                else:
                    self.open_folder(first_file.parent)

    def open_folder_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку", str(Path.home()))
        if folder:
            self.open_folder(Path(folder))

    def open_folder(self, folder_path):
        try:
            folder_path = Path(folder_path)
            if not folder_path.exists():
                return
            self.address_entry.setText(str(folder_path))
            self.current_archive = None
            self.archive_type = None
            self.files_list = []
            self.current_virtual_path = ""
            self.file_table.setRowCount(0)
            self.folder_tree.clear()
            if not self.is_navigating:
                self.add_to_history(str(folder_path))
            self.populate_folder_tree(folder_path)
            items = sorted(list(folder_path.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
            for item in items:
                if not self.show_hidden_files and is_hidden_or_system(item):
                    continue
                self.add_file_to_table(item)
            self.statusBar().showMessage(f"Папка: {folder_path.name}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def open_archive(self, filepath):
        try:
            filepath = Path(filepath)
            if not filepath.exists():
                return
            self.address_entry.setText(str(filepath))
            self.file_table.setRowCount(0)
            self.folder_tree.clear()
            self.files_list = []
            self.current_virtual_path = ""
            self.current_archive_path = filepath
            if not self.is_navigating:
                self.add_to_history(str(filepath))
            suffix = filepath.suffix.lower()
            if suffix == '.zip':
                self.archive_type = 'zip'
                with zipfile.ZipFile(filepath, 'r') as z:
                    for info in z.infolist():
                        self.parse_archive_item(info.filename, info.file_size, info.date_time, info.is_dir())
            elif suffix in ['.tar', '.tar.gz', '.tgz', '.tar.bz2']:
                self.archive_type = 'tar'
                mode = 'r:*' if suffix in ['.tar.gz', '.tgz'] else 'r:bz2' if suffix == '.tar.bz2' else 'r:'
                with tarfile.open(filepath, mode) as t:
                    for member in t.getmembers():
                        self.parse_archive_item(member.name, member.size, datetime.fromtimestamp(member.mtime), member.isdir())
            self.create_virtual_folders()
            self.refresh_current_view()
            self.current_archive = filepath
            self.statusBar().showMessage(f"Архив: {filepath.name} ({len(self.files_list)} объектов)")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def parse_archive_item(self, name, size, date_mod, is_dir):
        try:
            original_name = name
            decoded_name = name
            try:
                name_bytes = name.encode('cp437')
                try:
                    decoded_name = name_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        decoded_name = name_bytes.decode('cp866')
                    except:
                        decoded_name = name
            except:
                pass
            display_name = decoded_name.split('/')[-1] if '/' in decoded_name else decoded_name
            self.files_list.append({
                'original_path': original_name,
                'full_path': decoded_name.rstrip('/'),
                'name': display_name,
                'size': size,
                'type': 'Папка' if is_dir else self.get_file_type(decoded_name),
                'modified': datetime(*date_mod).strftime('%Y-%m-%d %H:%M') if isinstance(date_mod, tuple) else date_mod.strftime('%Y-%m-%d %H:%M'),
                'is_dir': is_dir
            })
        except:
            pass

    def create_virtual_folders(self):
        existing_paths = {item['full_path'] for item in self.files_list}
        virtual_folders = set()
        for item in self.files_list:
            path = item['full_path']
            if '/' in path:
                parts = path.split('/')
                for i in range(1, len(parts)):
                    folder_path = '/'.join(parts[:i])
                    if folder_path and folder_path not in existing_paths:
                        virtual_folders.add(folder_path)
        for folder_path in virtual_folders:
            self.files_list.append({
                'original_path': folder_path,
                'full_path': folder_path,
                'name': folder_path.split('/')[-1],
                'size': 0,
                'type': 'Папка',
                'modified': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'is_dir': True
            })

    def refresh_current_view(self):
        self.file_table.setRowCount(0)
        prefix = self.current_virtual_path.rstrip('/')
        visible_items = []
        seen_folders = set()
        for item in self.files_list:
            item_path = item['full_path']
            if item['is_dir']:
                if prefix == "":
                    if '/' not in item_path and item_path:
                        if item_path not in seen_folders:
                            seen_folders.add(item_path)
                            visible_items.append(item)
                else:
                    if item_path.startswith(prefix + '/'):
                        remaining = item_path[len(prefix) + 1:]
                        if '/' not in remaining and remaining:
                            if remaining not in seen_folders:
                                seen_folders.add(remaining)
                                visible_items.append(item)
            else:
                if prefix == "":
                    if '/' not in item_path:
                        visible_items.append(item)
                else:
                    file_dir = '/'.join(item_path.split('/')[:-1])
                    if file_dir == prefix:
                        visible_items.append(item)
        visible_items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
        for item in visible_items:
            self.add_file_to_table_row(item)

    def add_to_history(self, path):
        if self.current_history_index < len(self.navigation_history) - 1:
            self.navigation_history = self.navigation_history[:self.current_history_index + 1]
        if not self.navigation_history or self.navigation_history[-1] != path:
            self.navigation_history.append(path)
            self.current_history_index = len(self.navigation_history) - 1

    def add_file_to_table(self, item):
        self.add_file_to_table_row({
            'original_path': str(item),
            'full_path': str(item),
            'name': item.name,
            'size': item.stat().st_size,
            'type': 'Папка' if item.is_dir() else self.get_file_type(item.name),
            'modified': datetime.fromtimestamp(item.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
            'is_dir': item.is_dir(),
            'real_path': str(item)
        })

    def add_file_to_table_row(self, file_info):
        row = self.file_table.rowCount()
        self.file_table.insertRow(row)
        icon_item = QTableWidgetItem()
        if 'real_path' in file_info and file_info.get('real_path'):
            icon = self.icon_provider.icon(QFileInfo(file_info['real_path']))
        else:
            if file_info['is_dir']:
                icon = self.icon_provider.icon(QFileIconProvider.IconType.Folder)
            else:
                file_name = file_info['name']
                ext = Path(file_name).suffix.lower()
                temp_path = f"temp{ext}"
                icon = self.icon_provider.icon(QFileInfo(temp_path))
                if icon.isNull():
                    icon = self.icon_provider.icon(QFileIconProvider.IconType.File)
        icon_item.setIcon(icon)
        icon_item.setFlags(icon_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        icon_item.setData(Qt.ItemDataRole.UserRole, file_info)
        name_item = QTableWidgetItem(file_info['name'])
        name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        name_item.setData(Qt.ItemDataRole.UserRole, file_info)
        size_item = QTableWidgetItem(self.format_size(file_info['size']))
        size_item.setFlags(size_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        type_item = QTableWidgetItem(file_info['type'])
        type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        mod_item = QTableWidgetItem(file_info['modified'])
        mod_item.setFlags(mod_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.file_table.setItem(row, 0, icon_item)
        self.file_table.setItem(row, 1, name_item)
        self.file_table.setItem(row, 2, size_item)
        self.file_table.setItem(row, 3, type_item)
        self.file_table.setItem(row, 4, mod_item)

    def get_file_info_at_row(self, row):
        if row < 0 or row >= self.file_table.rowCount():
            return None
        for col in (0, 1):
            item = self.file_table.item(row, col)
            if item is not None:
                data = item.data(Qt.ItemDataRole.UserRole)
                if data:
                    return data
        return None

    def get_file_type(self, filename):
        ext = Path(filename).suffix.lower()
        types = {
            '.txt': 'Текст', '.pdf': 'PDF', '.doc': 'Word', '.docx': 'Word',
            '.xls': 'Excel', '.xlsx': 'Excel', '.jpg': 'JPEG', '.jpeg': 'JPEG',
            '.png': 'PNG', '.gif': 'GIF', '.mp3': 'MP3', '.mp4': 'MP4',
            '.avi': 'AVI', '.exe': 'EXE', '.py': 'Python', '.js': 'JavaScript',
            '.html': 'HTML', '.css': 'CSS', '.zip': 'ZIP', '.rar': 'RAR',
            '.7z': '7Z', '.tar': 'TAR', '.gz': 'GZIP', '.bz2': 'BZIP2'
        }
        return types.get(ext, 'Файл')

    def format_size(self, size):
        if size == 0:
            return "0 B"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def on_file_double_click(self, index):
        row = index.row()
        file_info = self.get_file_info_at_row(row)
        if not file_info:
            return
        if self.current_archive:
            if file_info['is_dir']:
                self.current_virtual_path = file_info['full_path']
                self.refresh_current_view()
            else:
                self.extract_single_file(file_info)
        else:
            full_path = Path(self.address_entry.text()) / file_info['name']
            if full_path.is_dir():
                self.open_folder(full_path)
            elif full_path.suffix.lower() in ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2']:
                self.open_archive(full_path)
            else:
                try:
                    os.startfile(full_path)
                except:
                    pass

    def extract_single_file(self, file_info):
        try:
            TEMP_DIR.mkdir(exist_ok=True)
            original_path = file_info['original_path']
            target = TEMP_DIR / file_info['name']
            if self.archive_type == 'zip':
                with zipfile.ZipFile(self.current_archive, 'r') as z:
                    z.extract(original_path, TEMP_DIR)
                    extracted = TEMP_DIR / original_path
                    if extracted != target and extracted.exists():
                        if target.exists():
                            target.unlink()
                        shutil.move(str(extracted), str(target))
                        remove_empty_parent_dirs(extracted, TEMP_DIR)
            elif self.archive_type == 'tar':
                with tarfile.open(self.current_archive, 'r:*') as t:
                    t.extract(original_path, TEMP_DIR)
                    extracted = TEMP_DIR / original_path
                    if extracted != target and extracted.exists():
                        if target.exists():
                            target.unlink()
                        shutil.move(str(extracted), str(target))
                        remove_empty_parent_dirs(extracted, TEMP_DIR)
            if target.exists():
                if target.suffix.lower() in ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2']:
                    self.open_archive(target)
                else:
                    os.startfile(target)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def go_up_folder(self):
        if self.current_archive:
            if self.current_virtual_path:
                parts = self.current_virtual_path.rstrip('/').split('/')
                if len(parts) > 1:
                    self.current_virtual_path = '/'.join(parts[:-1])
                else:
                    self.current_virtual_path = ""
                self.refresh_current_view()
            else:
                if self.navigation_history and self.current_history_index > 0:
                    self.current_history_index -= 1
                    path = Path(self.navigation_history[self.current_history_index])
                    self.is_navigating = True
                    if path.is_dir():
                        self.open_folder(path)
                    else:
                        self.open_archive(path)
                    self.is_navigating = False
                else:
                    self.current_archive = None
                    self.current_virtual_path = ""
                    self.current_archive_path = None
                    self.archive_type = None
                    self.files_list = []
                    self.statusBar().showMessage("Выход из архива")
        else:
            current_path = Path(self.address_entry.text())
            if current_path.parent != current_path:
                self.open_folder(current_path.parent)

    def go_to_path(self):
        path = Path(self.address_entry.text())
        if path.exists():
            if path.is_dir():
                self.open_folder(path)
            else:
                self.open_archive(path)

    def show_context_menu(self, position):
        menu = QMenu(self)
        row = self.file_table.rowAt(position.y())
        if row >= 0:
            menu.addAction("Открыть", lambda: self.on_file_double_click(self.file_table.model().index(row, 0)))
            menu.addAction("Извлечь", self.extract_files)
            if self.current_archive:
                menu.addAction("Удалить", self.delete_files)
            menu.addSeparator()
            menu.addAction("Свойства", lambda: self.show_properties(row))
        else:
            if self.current_archive:
                menu.addAction("Свойства архива", self.show_archive_properties)
        menu.exec(self.file_table.viewport().mapToGlobal(position))

    def show_properties(self, row):
        file_info = self.get_file_info_at_row(row)
        if not file_info:
            return
        name = file_info['name']
        size = self.format_size(file_info['size'])
        ftype = file_info['type']
        full_path = file_info['full_path']
        QMessageBox.information(self, "Свойства", f"Имя: {name}\nПуть в архиве: {full_path}\nРазмер: {size}\nТип: {ftype}")

    def show_archive_properties(self):
        if not self.current_archive:
            return
        stats = self.current_archive.stat()
        QMessageBox.information(self, "Свойства архива",
                                f"Имя: {self.current_archive.name}\nРазмер: {self.format_size(stats.st_size)}\nОбъектов: {len(self.files_list)}")

    def add_files(self):
        if not self.current_archive:
            QMessageBox.warning(self, "Внимание", "Сначала откройте или создайте архив")
            return
        files, _ = QFileDialog.getOpenFileNames(self, "Выберите файлы")
        if files:
            self.add_files_to_archive(files)

    def add_folder(self):
        if not self.current_archive:
            QMessageBox.warning(self, "Внимание", "Сначала откройте или создайте архив")
            return
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if folder:
            self.add_files_to_archive([folder])

    def add_files_to_archive(self, files):
        """Добавление файлов/папок в архив с защитой от самоархивирования"""
        try:
            current_archive_resolved = None
            if self.current_archive:
                try:
                    current_archive_resolved = Path(self.current_archive).resolve()
                except:
                    current_archive_resolved = Path(self.current_archive)

            if self.archive_type == 'zip':
                with zipfile.ZipFile(self.current_archive, 'a') as z:
                    for f in files:
                        p = Path(f)
                        try:
                            p_resolved = p.resolve()
                        except:
                            p_resolved = p
                        
                        if current_archive_resolved and p_resolved == current_archive_resolved:
                            QMessageBox.warning(self, "Внимание", f"Пропущен файл: {p.name}\nНельзя архивировать файл в самого себя")
                            continue
                        
                        if p.is_dir():
                            self._add_directory_to_zip(z, p, current_archive_resolved)
                        else:
                            z.write(f, p.name)
            
            elif self.archive_type == 'tar':
                with tarfile.open(self.current_archive, 'a') as t:
                    for f in files:
                        p = Path(f)
                        try:
                            p_resolved = p.resolve()
                        except:
                            p_resolved = p
                        
                        if current_archive_resolved and p_resolved == current_archive_resolved:
                            QMessageBox.warning(self, "Внимание", f"Пропущен файл: {p.name}\nНельзя архивировать файл в самого себя")
                            continue
                        
                        def tar_filter(tarinfo):
                            """Фильтр для исключения текущего архива из TAR"""
                            try:
                                item_path = Path(tarinfo.name).resolve()
                                if current_archive_resolved and item_path == current_archive_resolved:
                                    return None
                            except:
                                pass
                            return tarinfo
                        
                        if p.is_dir():
                            t.add(str(p), arcname=p.name, filter=tar_filter)
                        else:
                            t.add(str(p), arcname=p.name)
            
            self.open_archive(self.current_archive)
            QMessageBox.information(self, "Успех", f"Добавлено: {len(files)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _add_directory_to_zip(self, zip_ref, dir_path, current_archive_resolved):
        """Рекурсивное добавление папки в ZIP с проверкой на самоархивирование"""
        for root, dirs, filenames in os.walk(dir_path):
            for filename in filenames:
                file_path = Path(root) / filename
                try:
                    file_resolved = file_path.resolve()
                except:
                    file_resolved = file_path
                
                if current_archive_resolved and file_resolved == current_archive_resolved:
                    continue
                
                arcname = str(file_path.relative_to(dir_path.parent))
                zip_ref.write(file_path, arcname)

    def extract_files(self):
        """Массовое извлечение с сохранением структуры архива"""
        selected = self.file_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Внимание", "Выберите файлы для извлечения")
            return
        
        dest = QFileDialog.getExistingDirectory(self, "Куда извлечь?")
        if not dest:
            return

        try:
            for idx in selected:
                file_info = self.get_file_info_at_row(idx.row())
                if not file_info:
                    continue
                original_path = file_info['original_path']

                if self.archive_type == 'zip':
                    with zipfile.ZipFile(self.current_archive, 'r') as z:
                        z.extract(original_path, dest)
                elif self.archive_type == 'tar':
                    with tarfile.open(self.current_archive, 'r:*') as t:
                        t.extract(original_path, dest)
            QMessageBox.information(self, "Успех", f"Извлечено: {len(selected)} файлов/папок")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def delete_files(self):
        """Безопасное удаление файлов из ZIP с проверкой целостности"""
        if not self.current_archive or self.archive_type != 'zip':
            QMessageBox.warning(self, "Внимание", "Удаление поддерживается только для ZIP")
            return
        selected = self.file_table.selectionModel().selectedRows()
        if not selected:
            return
        if QMessageBox.question(self, "Удалить?", "Удалить выбранные файлы?") == QMessageBox.StandardButton.Yes:
            to_delete_original = set()
            for idx in selected:
                file_info = self.get_file_info_at_row(idx.row())
                if file_info:
                    to_delete_original.add(file_info['original_path'])
            
            new_arc = self.current_archive.with_suffix('.tmp')
            
            try:
                # Шаг 1: Создаём новый архив
                with zipfile.ZipFile(new_arc, 'w') as nz:
                    with zipfile.ZipFile(self.current_archive, 'r') as oz:
                        for item in oz.infolist():
                            if item.filename not in to_delete_original:
                                nz.writestr(item, oz.read(item.filename))
                
                # Шаг 2: Проверяем, что новый архив создан и не пустой
                if not new_arc.exists() or new_arc.stat().st_size == 0:
                    raise Exception("Новый архив пуст или не создан")
                
                # Шаг 3: Безопасная замена - сначала удаляем старый, потом переименовываем новый
                self.current_archive.unlink()
                new_arc.rename(self.current_archive)
                
                self.open_archive(self.current_archive)
                QMessageBox.information(self, "Успех", "Файлы удалены")
                
            except Exception as e:
                # Если что-то пошло не так, пытаемся восстановить
                if new_arc.exists():
                    try:
                        new_arc.unlink()
                    except:
                        pass
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить файлы:\n{e}\n\nСтарый архив сохранён.")

    def test_archive(self):
        if not self.current_archive:
            return
        try:
            if self.archive_type == 'zip':
                res = zipfile.ZipFile(self.current_archive, 'r').testzip()
                QMessageBox.information(self, "Тест", "Архив цел" if not res else f"Битый файл: {res}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def search_files(self):
        term, ok = QInputDialog.getText(self, "Поиск", "Имя файла:")
        if not ok or not term:
            return
        term_lower = term.lower()
        found_rows = []
        for r in range(self.file_table.rowCount()):
            file_info = self.get_file_info_at_row(r)
            if not file_info:
                continue
            name = file_info.get('name', '')
            if name and term_lower in name.lower():
                found_rows.append(r)
        if found_rows:
            self.file_table.clearSelection()
            for r in found_rows:
                self.file_table.selectRow(r)
            self.file_table.scrollToItem(
                self.file_table.item(found_rows[0], 1),
                QAbstractItemView.ScrollHint.PositionAtCenter
            )
            self.file_table.setFocus(Qt.FocusReason.OtherFocusReason)
            self.file_table.setCurrentCell(found_rows[0], 1)
            QMessageBox.information(self, "Поиск", f"Найдено: {len(found_rows)}")
        else:
            QMessageBox.information(self, "Поиск", "Ничего не найдено")

    def show_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dlg.save_settings()
            self.show_hidden_files = dlg.show_hidden_checkbox.isChecked()
            self.show_system_files = dlg.show_system_checkbox.isChecked()
            if not self.current_archive:
                self.open_folder(Path(self.address_entry.text()))

    def populate_folder_tree(self, folder_path):
        root_item = QTreeWidgetItem([folder_path.name])
        root_item.setData(0, Qt.ItemDataRole.UserRole, str(folder_path))
        root_icon = self.icon_provider.icon(QFileInfo(str(folder_path)))
        root_item.setIcon(0, root_icon)
        self.folder_tree.addTopLevelItem(root_item)
        for item in folder_path.iterdir():
            if item.is_dir():
                child = QTreeWidgetItem([item.name])
                child.setData(0, Qt.ItemDataRole.UserRole, str(item))
                child_icon = self.icon_provider.icon(QFileInfo(str(item)))
                child.setIcon(0, child_icon)
                root_item.addChild(child)

    def on_folder_double_click(self, item, col):
        self.open_folder(Path(item.data(0, Qt.ItemDataRole.UserRole)))


def main():
    cleanup_temp_folder()
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = VanadiumArchiver()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
