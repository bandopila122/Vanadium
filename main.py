#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import zipfile
import tarfile
import shutil
import ctypes
from pathlib import Path
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QTableWidget, QTableWidgetItem, QHeaderView,
    QStatusBar, QFileDialog, QMessageBox, QAbstractItemView,
    QMenu, QTreeWidget, QTreeWidgetItem, QSplitter, QLabel, QFrame,
    QInputDialog, QLineEdit, QToolButton, QPushButton, QFileIconProvider,
    QDialog
)
from PyQt6.QtCore import Qt, QSize, QSettings, QFileInfo
from PyQt6.QtGui import QIcon, QAction, QFont, QDragEnterEvent, QDropEvent

from design import ThemeManager, WelcomeDialog, MigrationDialog, SettingsDialog, Translator


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
    except Exception:
        pass


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


class VanadiumArchiver(QMainWindow):
    def __init__(self, translator):
        super().__init__()
        self.tr = translator
        self.setWindowTitle(self.tr.t("app_title"))
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

        self.settings = QSettings("VanaArchiver", "Settings")

        self._handle_migration()

        self.show_hidden_files = self.settings.value("show_hidden_files", False, type=bool)
        self.show_system_files = self.settings.value("show_system_files", False, type=bool)
        self.current_theme = self.settings.value("theme", "win10", type=str)
        self.current_lang = self.settings.value("language", "ru", type=str)

        self.setup_icons()
        self.create_ui()
        self.create_menus()
        self.create_toolbar()

        ThemeManager.apply(self, self.current_theme, self.base_path)

        self._show_welcome_if_needed()

        self.open_folder(Path.home())

    def _handle_migration(self):
        if self.settings.contains("migration_done"):
            return

        old_keys = [k for k in self.settings.allKeys() if k not in ['migration_done']]
        if not old_keys:
            self.settings.setValue("migration_done", True)
            self.settings.setValue("welcome_shown", False)
            return

        dialog = MigrationDialog(self, self.tr)
        dialog.exec()
        choice = dialog.get_choice()

        if choice == 2:
            self.settings.clear()
            self.settings.sync()
            self.settings = QSettings("VanaArchiver", "Settings")

        self.settings.setValue("migration_done", True)

    def _show_welcome_if_needed(self):
        if not self.settings.value("welcome_shown", False, type=bool):
            dlg = WelcomeDialog(self, self.tr)
            dlg.exec()
            if dlg.should_not_show_again():
                self.settings.setValue("welcome_shown", True)

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
        address_frame.setObjectName("addressFrame")
        address_layout = QHBoxLayout(address_frame)
        address_layout.setContentsMargins(8, 4, 8, 4)
        address_layout.setSpacing(6)

        up_btn = QToolButton()
        up_btn.setText("⬆")
        up_btn.setFixedSize(28, 28)
        up_btn.setToolTip(self.tr.t("tooltip_up"))
        up_btn.clicked.connect(self.go_up_folder)
        address_layout.addWidget(up_btn)

        self.address_entry = QLineEdit()
        self.address_entry.returnPressed.connect(self.go_to_path)
        address_layout.addWidget(self.address_entry, 1)

        go_btn = QPushButton(self.tr.t("button_go"))
        go_btn.clicked.connect(self.go_to_path)
        address_layout.addWidget(go_btn)

        main_layout.addWidget(address_frame)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderLabel(self.tr.t("tree_folders"))
        self.folder_tree.header().hide()
        self.folder_tree.setMinimumWidth(220)
        self.folder_tree.setIconSize(QSize(16, 16))
        splitter.addWidget(self.folder_tree)

        self.file_table = QTableWidget()
        self.file_table.setColumnCount(5)
        self.file_table.setHorizontalHeaderLabels([
            '',
            self.tr.t("column_name"),
            self.tr.t("column_size"),
            self.tr.t("column_type"),
            self.tr.t("column_modified")
        ])
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

        self.statusBar().showMessage(self.tr.t("status_ready"))

        self.file_table.doubleClicked.connect(self.on_file_double_click)
        self.file_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_table.customContextMenuRequested.connect(self.show_context_menu)
        self.folder_tree.itemDoubleClicked.connect(self.on_folder_double_click)

    def create_menus(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu(self.tr.t("menu_file"))
        file_menu.addAction(self.tr.t("action_open_archive"), self.open_archive_dialog)
        file_menu.addAction(self.tr.t("action_open_folder"), self.open_folder_dialog)
        file_menu.addSeparator()
        file_menu.addAction(self.tr.t("action_exit"), self.close)

        archive_menu = menubar.addMenu(self.tr.t("menu_archive"))
        archive_menu.addAction(self.tr.t("action_add_files"), self.add_files)
        archive_menu.addAction(self.tr.t("action_add_folder"), self.add_folder)
        archive_menu.addAction(self.tr.t("action_extract"), self.extract_files)
        archive_menu.addAction(self.tr.t("action_test"), self.test_archive)
        archive_menu.addSeparator()
        archive_menu.addAction(self.tr.t("action_delete"), self.delete_files)

        tools_menu = menubar.addMenu(self.tr.t("menu_tools"))
        settings_action = QAction(self.tr.t("action_settings"), self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)

    def create_toolbar(self):
        toolbar = QToolBar()
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(toolbar)

        buttons = [
            ('add', self.tr.t("toolbar_add"), self.add_files),
            ('extract', self.tr.t("toolbar_extract"), self.extract_files),
            ('folder', self.tr.t("toolbar_open"), self.open_folder_dialog),
            ('delete', self.tr.t("toolbar_delete"), self.delete_files),
            ('search', self.tr.t("toolbar_search"), self.search_files),
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
            self.tr.t("dialog_open_archive"),
            str(Path.home()),
            self.tr.t("filter_archives") + ";;" + self.tr.t("filter_all")
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
        folder = QFileDialog.getExistingDirectory(self, self.tr.t("dialog_open_folder"), str(Path.home()))
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
            self.statusBar().showMessage(f"{self.tr.t('status_folder')}: {folder_path.name}")
        except Exception as e:
            QMessageBox.critical(self, self.tr.t("error"), str(e))

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
            self.statusBar().showMessage(f"{self.tr.t('status_archive')}: {filepath.name} ({len(self.files_list)})")
        except Exception as e:
            QMessageBox.critical(self, self.tr.t("error"), str(e))

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
                'type': self.tr.t('type_folder') if is_dir else self.get_file_type(decoded_name),
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
                'type': self.tr.t('type_folder'),
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
            'type': self.tr.t('type_folder') if item.is_dir() else self.get_file_type(item.name),
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
            '.txt': self.tr.t('type_text'), '.pdf': 'PDF', '.doc': 'Word', '.docx': 'Word',
            '.xls': 'Excel', '.xlsx': 'Excel', '.jpg': 'JPEG', '.jpeg': 'JPEG',
            '.png': 'PNG', '.gif': 'GIF', '.mp3': 'MP3', '.mp4': 'MP4',
            '.avi': 'AVI', '.exe': 'EXE', '.py': 'Python', '.js': 'JavaScript',
            '.html': 'HTML', '.css': 'CSS', '.zip': 'ZIP', '.rar': 'RAR',
            '.7z': '7Z', '.tar': 'TAR', '.gz': 'GZIP', '.bz2': 'BZIP2'
        }
        return types.get(ext, self.tr.t('type_file'))

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
            QMessageBox.critical(self, self.tr.t("error"), str(e))

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
                    self.statusBar().showMessage(self.tr.t("status_exit_archive"))
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
            menu.addAction(self.tr.t("ctx_open"), lambda: self.on_file_double_click(self.file_table.model().index(row, 0)))
            menu.addAction(self.tr.t("ctx_extract"), self.extract_files)
            if self.current_archive:
                menu.addAction(self.tr.t("ctx_delete"), self.delete_files)
            menu.addSeparator()
            menu.addAction(self.tr.t("ctx_properties"), lambda: self.show_properties(row))
        else:
            if self.current_archive:
                menu.addAction(self.tr.t("ctx_archive_properties"), self.show_archive_properties)
        menu.exec(self.file_table.viewport().mapToGlobal(position))

    def show_properties(self, row):
        file_info = self.get_file_info_at_row(row)
        if not file_info:
            return
        name = file_info['name']
        size = self.format_size(file_info['size'])
        ftype = file_info['type']
        full_path = file_info['full_path']
        text = f"{self.tr.t('prop_name')}: {name}\n{self.tr.t('prop_path')}: {full_path}\n{self.tr.t('prop_size')}: {size}\n{self.tr.t('prop_type')}: {ftype}"
        QMessageBox.information(self, self.tr.t("ctx_properties"), text)

    def show_archive_properties(self):
        if not self.current_archive:
            return
        stats = self.current_archive.stat()
        text = f"{self.tr.t('prop_name')}: {self.current_archive.name}\n{self.tr.t('prop_size')}: {self.format_size(stats.st_size)}\n{self.tr.t('prop_objects')}: {len(self.files_list)}"
        QMessageBox.information(self, self.tr.t("ctx_archive_properties"), text)

    def add_files(self):
        if not self.current_archive:
            QMessageBox.warning(self, self.tr.t("warning"), self.tr.t("msg_open_archive_first"))
            return
        files, _ = QFileDialog.getOpenFileNames(self, self.tr.t("dialog_select_files"))
        if files:
            self.add_files_to_archive(files)

    def add_folder(self):
        if not self.current_archive:
            QMessageBox.warning(self, self.tr.t("warning"), self.tr.t("msg_open_archive_first"))
            return
        folder = QFileDialog.getExistingDirectory(self, self.tr.t("dialog_select_folder"))
        if folder:
            self.add_files_to_archive([folder])

    def add_files_to_archive(self, files):
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
                            QMessageBox.warning(self, self.tr.t("warning"), f"{self.tr.t('msg_skip_self')}: {p.name}")
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
                            QMessageBox.warning(self, self.tr.t("warning"), f"{self.tr.t('msg_skip_self')}: {p.name}")
                            continue

                        def tar_filter(tarinfo):
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
            QMessageBox.information(self, self.tr.t("success"), f"{self.tr.t('msg_added')}: {len(files)}")
        except Exception as e:
            QMessageBox.critical(self, self.tr.t("error"), str(e))

    def _add_directory_to_zip(self, zip_ref, dir_path, current_archive_resolved):
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
        selected = self.file_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, self.tr.t("warning"), self.tr.t("msg_select_files"))
            return
        dest = QFileDialog.getExistingDirectory(self, self.tr.t("dialog_extract_to"))
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
            QMessageBox.information(self, self.tr.t("success"), f"{self.tr.t('msg_extracted')}: {len(selected)}")
        except Exception as e:
            QMessageBox.critical(self, self.tr.t("error"), str(e))

    def delete_files(self):
        if not self.current_archive or self.archive_type != 'zip':
            QMessageBox.warning(self, self.tr.t("warning"), self.tr.t("msg_zip_only"))
            return
        selected = self.file_table.selectionModel().selectedRows()
        if not selected:
            return
        if QMessageBox.question(self, self.tr.t("confirm"), self.tr.t("msg_delete_confirm")) == QMessageBox.StandardButton.Yes:
            to_delete_original = set()
            for idx in selected:
                file_info = self.get_file_info_at_row(idx.row())
                if file_info:
                    to_delete_original.add(file_info['original_path'])
            new_arc = self.current_archive.with_suffix('.tmp')
            try:
                with zipfile.ZipFile(new_arc, 'w') as nz:
                    with zipfile.ZipFile(self.current_archive, 'r') as oz:
                        for item in oz.infolist():
                            if item.filename not in to_delete_original:
                                nz.writestr(item, oz.read(item.filename))
                if not new_arc.exists() or new_arc.stat().st_size == 0:
                    raise Exception("New archive empty")
                self.current_archive.unlink()
                new_arc.rename(self.current_archive)
                self.open_archive(self.current_archive)
                QMessageBox.information(self, self.tr.t("success"), self.tr.t("msg_deleted"))
            except Exception as e:
                if new_arc.exists():
                    try:
                        new_arc.unlink()
                    except:
                        pass
                QMessageBox.critical(self, self.tr.t("error"), f"{self.tr.t('msg_delete_fail')}\n{e}")

    def test_archive(self):
        if not self.current_archive:
            return
        try:
            if self.archive_type == 'zip':
                res = zipfile.ZipFile(self.current_archive, 'r').testzip()
                QMessageBox.information(self, self.tr.t("action_test"), self.tr.t("msg_archive_ok") if not res else f"{self.tr.t('msg_archive_bad')}: {res}")
        except Exception as e:
            QMessageBox.critical(self, self.tr.t("error"), str(e))

    def search_files(self):
        term, ok = QInputDialog.getText(self, self.tr.t("toolbar_search"), self.tr.t("dialog_search_prompt"))
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
            QMessageBox.information(self, self.tr.t("toolbar_search"), f"{self.tr.t('msg_found')}: {len(found_rows)}")
        else:
            QMessageBox.information(self, self.tr.t("toolbar_search"), self.tr.t("msg_not_found"))

    def show_settings(self):
        dlg = SettingsDialog(self, self.tr, self.current_theme, self.current_lang)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dlg.save_settings()
            self.show_hidden_files = dlg.show_hidden_checkbox.isChecked()
            self.show_system_files = dlg.show_system_checkbox.isChecked()

            new_theme = dlg.get_selected_theme()
            if new_theme != self.current_theme:
                self.current_theme = new_theme
                ThemeManager.apply(self, self.current_theme, self.base_path, self.tr)
                QMessageBox.information(self, self.tr.t("action_settings"), self.tr.t("msg_theme_changed"))

            new_lang = dlg.get_selected_language()
            if new_lang != self.current_lang:
                self.current_lang = new_lang
                QMessageBox.information(self, self.tr.t("action_settings"), self.tr.t("msg_restart_lang"))

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

    base_path = Path(sys.argv[0]).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
    settings = QSettings("VanaArchiver", "Settings")
    current_lang = settings.value("language", "ru", type=str)
    translator = Translator(base_path, current_lang)

    window = VanadiumArchiver(translator)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
