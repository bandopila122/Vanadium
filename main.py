import os
import sys
import zipfile
import tarfile
import gzip
import bz2
import shutil
import ctypes
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QTableWidget, QTableWidgetItem, QHeaderView,
    QStatusBar, QFileDialog, QMessageBox, QAbstractItemView,
    QMenu, QTreeWidget, QTreeWidgetItem, QSplitter, QLabel, QFrame,
    QInputDialog, QLineEdit, QToolButton, QPushButton, QFileIconProvider,
    QDialog, QCheckBox, QDialogButtonBox, QFormLayout
)
from PyQt6.QtCore import Qt, QSize, QSettings, QFileInfo
from PyQt6.QtGui import QIcon, QAction, QFont, QDragEnterEvent, QDropEvent


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


class SettingsDialog(QDialog):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setGeometry(200, 200, 400, 200)
        
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.show_hidden_checkbox = QCheckBox("Отображать скрытые файлы")
        form_layout.addRow(self.show_hidden_checkbox)
        
        self.show_system_checkbox = QCheckBox("Отображать системные файлы")
        form_layout.addRow(self.show_system_checkbox)
        
        layout.addLayout(form_layout)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.load_settings()
    
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
        
        self.set_style()
        
        self.base_path = Path(sys.argv[0]).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
        self.icons_path = self.base_path / "icons"
        
        self.icon_provider = QFileIconProvider()
        
        self.current_archive = None
        self.archive_type = None
        self.files_list = []
        self.current_archive_path = None
        
        self.navigation_history = []
        self.current_history_index = -1
        self.is_navigating = False
        
        self.setup_icons()
        self.create_ui()
        self.create_menus()
        self.create_toolbar()
        
        self.load_settings()
        
        self.open_folder(Path.home())
    
    def set_style(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f0f0f0; }
            QToolBar { background-color: #f0f0f0; border: 1px solid #c0c0c0; padding: 2px; }
            QTableWidget { background-color: white; border: 1px solid #c0c0c0; gridline-color: #e0e0e0; }
            QTableWidget::item:selected { background-color: #3399ff; color: white; }
            QHeaderView::section { background-color: #e0e0e0; border: 1px solid #c0c0c0; padding: 4px; font-weight: bold; }
            QTreeWidget { background-color: white; border: 1px solid #c0c0c0; }
            QTreeWidget::item:selected { background-color: #3399ff; color: white; }
            QStatusBar { background-color: #e0e0e0; border-top: 1px solid #c0c0c0; }
            QToolButton { background-color: #f0f0f0; border: 1px solid #f0f0f0; padding: 4px; margin: 2px; border-radius: 3px; }
            QToolButton:hover { background-color: #e0e0e0; border: 1px solid #c0c0c0; }
            QPushButton { padding: 4px 8px; }
        """)
        font = QFont("Tahoma", 9)
        self.setFont(font)
    
    def setup_icons(self):
        self.icons = {}
        icon_names = ['add', 'extract', 'folder', 'delete', 'info', 'settings', 'networkplace', 'search', 'help']
        
        if not self.icons_path.exists():
            return
        
        for icon_name in icon_names:
            for ext in ['.ico', '.png', '.gif']:
                for name_variant in [icon_name, icon_name.capitalize(), icon_name.upper()]:
                    icon_path = self.icons_path / f"{name_variant}{ext}"
                    if icon_path.exists():
                        icon = QIcon(str(icon_path))
                        if not icon.isNull():
                            self.icons[icon_name] = icon
                            break
                if icon_name in self.icons:
                    break
        
        if 'networkplace' in self.icons:
            self.setWindowIcon(self.icons['networkplace'])
    
    def create_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        address_frame = QFrame()
        address_frame.setFixedHeight(32)
        address_frame.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #c0c0c0;")
        address_layout = QHBoxLayout(address_frame)
        address_layout.setContentsMargins(2, 2, 2, 2)
        address_layout.setSpacing(3)
        
        self.back_btn = QToolButton()
        self.back_btn.setText("◀")
        self.back_btn.setFixedSize(26, 26)
        self.back_btn.setToolTip("Назад")
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setEnabled(False)
        address_layout.addWidget(self.back_btn)
        
        self.forward_btn = QToolButton()
        self.forward_btn.setText("▶")
        self.forward_btn.setFixedSize(26, 26)
        self.forward_btn.setToolTip("Вперёд")
        self.forward_btn.clicked.connect(self.go_forward)
        self.forward_btn.setEnabled(False)
        address_layout.addWidget(self.forward_btn)
        
        up_btn = QToolButton()
        up_btn.setText("⬆")
        up_btn.setFixedSize(26, 26)
        up_btn.setToolTip("На уровень выше")
        up_btn.clicked.connect(self.go_up_folder)
        address_layout.addWidget(up_btn)
        
        folder_icon_label = QLabel()
        folder_icon_pixmap = self.icon_provider.icon(QFileIconProvider.IconType.Folder).pixmap(16, 16)
        folder_icon_label.setPixmap(folder_icon_pixmap)
        folder_icon_label.setFixedSize(20, 20)
        folder_icon_label.setToolTip("Нажмите чтобы выбрать папку")
        folder_icon_label.setCursor(Qt.CursorShape.PointingHandCursor)
        folder_icon_label.mousePressEvent = lambda e: self.open_folder_dialog()
        address_layout.addWidget(folder_icon_label)
        
        self.address_entry = QLineEdit()
        self.address_entry.setFixedHeight(26)
        self.address_entry.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #c0c0c0;
                padding: 2px 4px;
                font-family: 'Segoe UI';
                font-size: 9pt;
            }
            QLineEdit:focus {
                border: 1px solid #3399ff;
            }
        """)
        self.address_entry.returnPressed.connect(self.go_to_path)
        address_layout.addWidget(self.address_entry, 1)
        
        go_btn = QPushButton("Перейти")
        go_btn.setFixedHeight(26)
        go_btn.setToolTip("Перейти по пути")
        go_btn.clicked.connect(self.go_to_path)
        address_layout.addWidget(go_btn)
        
        main_layout.addWidget(address_frame)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderLabel(" Папки")
        self.folder_tree.header().hide()
        self.folder_tree.setMinimumWidth(200)
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
        self.file_table.setIconSize(QSize(16, 16))
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
        open_action = QAction("Открыть архив...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_archive_dialog)
        file_menu.addAction(open_action)
        
        folder_action = QAction("Открыть папку...", self)
        folder_action.setShortcut("Ctrl+D")
        folder_action.triggered.connect(self.open_folder_dialog)
        file_menu.addAction(folder_action)
        
        file_menu.addSeparator()
        create_action = QAction("Создать архив...", self)
        create_action.triggered.connect(self.create_archive)
        file_menu.addAction(create_action)
        
        file_menu.addSeparator()
        exit_action = QAction("Выход", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        archive_menu = menubar.addMenu("Архив")
        add_action = QAction("Добавить файлы...", self)
        add_action.triggered.connect(self.add_files)
        archive_menu.addAction(add_action)
        
        add_folder_action = QAction("Добавить папку...", self)
        add_folder_action.triggered.connect(self.add_folder)
        archive_menu.addAction(add_folder_action)
        
        extract_action = QAction("Извлечь...", self)
        extract_action.triggered.connect(self.extract_files)
        archive_menu.addAction(extract_action)
        
        test_action = QAction("Тест архива", self)
        test_action.triggered.connect(self.test_archive)
        archive_menu.addAction(test_action)
        
        archive_menu.addSeparator()
        delete_action = QAction("Удалить", self)
        delete_action.setShortcut("Del")
        delete_action.triggered.connect(self.delete_files)
        archive_menu.addAction(delete_action)
        
        settings_menu = menubar.addMenu("Настройки")
        settings_action = QAction("Настройки...", self)
        settings_action.triggered.connect(self.show_settings)
        settings_menu.addAction(settings_action)
        
        help_menu = menubar.addMenu("Справка")
        search_action = QAction("Поиск...", self)
        search_action.setShortcut("F3")
        search_action.triggered.connect(self.search_files)
        help_menu.addAction(search_action)
        
        help_menu.addSeparator()
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        toolbar = QToolBar("Инструменты")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.addToolBar(toolbar)
        
        buttons = [
            ('add', 'Добавить', self.add_files),
            ('extract', 'Извлечь', self.extract_files),
            ('folder', 'Открыть', self.open_folder_dialog),
            ('delete', 'Удалить', self.delete_files),
            ('info', 'Инфо', self.show_info),
            ('settings', 'Настройки', self.show_settings),
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
    
    def load_settings(self):
        self.settings = QSettings("VanaArchiver", "Settings")
        self.show_hidden_files = self.settings.value("show_hidden_files", False, type=bool)
        self.show_system_files = self.settings.value("show_system_files", False, type=bool)
    
    def save_settings(self):
        self.settings.setValue("show_hidden_files", self.show_hidden_files)
        self.settings.setValue("show_system_files", self.show_system_files)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path:
                files.append(file_path)
        
        if files:
            if self.current_archive:
                self.add_files_to_archive(files)
            else:
                first_file = Path(files[0])
                if first_file.is_dir():
                    self.open_folder(first_file)
                elif first_file.suffix.lower() in ['.zip', '.rar', '.7z', '.tar', '.tar.gz', '.tgz', '.tar.bz2']:
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
                QMessageBox.warning(self, "Ошибка", f"Папка не существует:\n{folder_path}")
                return
            
            self.address_entry.setText(str(folder_path))
            self.current_archive = None
            self.archive_type = None
            self.files_list = []
            self.current_archive_path = None
            self.file_table.setRowCount(0)
            self.folder_tree.clear()
            
            if not self.is_navigating:
                self.add_to_history(str(folder_path))
            
            self.populate_folder_tree(folder_path)
            
            items = list(folder_path.iterdir())
            items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for item in items:
                if not self.show_hidden_files and is_hidden_or_system(item):
                    continue
                
                self.add_file_to_table(item)
            
            self.statusBar().showMessage(f"Открыта папка: {folder_path.name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def open_archive(self, filepath):
        try:
            filepath = Path(filepath)
            if not filepath.exists():
                QMessageBox.warning(self, "Ошибка", f"Файл не существует:\n{filepath}")
                return
            
            self.address_entry.setText(str(filepath))
            suffix = filepath.suffix.lower()
            
            self.file_table.setRowCount(0)
            self.folder_tree.clear()
            self.files_list = []
            self.current_archive_path = filepath
            
            if not self.is_navigating:
                self.add_to_history(str(filepath))
            
            if suffix == '.zip':
                self.archive_type = 'zip'
                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                    for info in zip_ref.infolist():
                        self.add_file_to_list(info)
            
            elif suffix in ['.tar', '.tar.gz', '.tgz', '.tar.bz2']:
                self.archive_type = 'tar'
                mode = 'r:*' if suffix in ['.tar.gz', '.tgz'] else 'r:bz2' if suffix == '.tar.bz2' else 'r:'
                with tarfile.open(filepath, mode) as tar_ref:
                    for member in tar_ref.getmembers():
                        self.add_tar_file_to_list(member)
            
            elif suffix == '.gz':
                self.archive_type = 'gzip'
                size = filepath.stat().st_size
                self.files_list.append({
                    'name': filepath.stem,
                    'size': size,
                    'type': 'Gzip',
                    'modified': datetime.fromtimestamp(filepath.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                    'icon_path': str(filepath)
                })
            
            elif suffix == '.bz2':
                self.archive_type = 'bz2'
                size = filepath.stat().st_size
                self.files_list.append({
                    'name': filepath.stem,
                    'size': size,
                    'type': 'Bzip2',
                    'modified': datetime.fromtimestamp(filepath.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                    'icon_path': str(filepath)
                })
            
            for file_info in self.files_list:
                self.add_file_to_table_row(file_info)
            
            self.current_archive = filepath
            self.statusBar().showMessage(f"Открыт: {filepath.name} ({len(self.files_list)} файлов)")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def add_to_history(self, path):
        if self.current_history_index < len(self.navigation_history) - 1:
            self.navigation_history = self.navigation_history[:self.current_history_index + 1]
        
        if not self.navigation_history or self.navigation_history[-1] != path:
            self.navigation_history.append(path)
            self.current_history_index = len(self.navigation_history) - 1
        
        self.back_btn.setEnabled(self.current_history_index > 0)
        self.forward_btn.setEnabled(self.current_history_index < len(self.navigation_history) - 1)
    
    def go_back(self):
        if self.current_history_index > 0:
            self.current_history_index -= 1
            path = Path(self.navigation_history[self.current_history_index])
            self.address_entry.setText(str(path))
            
            self.is_navigating = True
            if path.is_dir():
                self.open_folder(path)
            else:
                self.open_archive(path)
            self.is_navigating = False
    
    def go_forward(self):
        if self.current_history_index < len(self.navigation_history) - 1:
            self.current_history_index += 1
            path = Path(self.navigation_history[self.current_history_index])
            self.address_entry.setText(str(path))
            
            self.is_navigating = True
            if path.is_dir():
                self.open_folder(path)
            else:
                self.open_archive(path)
            self.is_navigating = False
    
    def add_file_to_list(self, zip_info):
        is_dir = zip_info.is_dir() if hasattr(zip_info, 'is_dir') else False
        self.files_list.append({
            'name': zip_info.filename,
            'size': zip_info.file_size,
            'type': 'Папка' if is_dir else self.get_file_type(zip_info.filename),
            'modified': datetime(*zip_info.date_time).strftime('%Y-%m-%d %H:%M')
        })
    
    def add_tar_file_to_list(self, tar_info):
        self.files_list.append({
            'name': tar_info.name,
            'size': tar_info.size,
            'type': 'Папка' if tar_info.isdir() else self.get_file_type(tar_info.name),
            'modified': datetime.fromtimestamp(tar_info.mtime).strftime('%Y-%m-%d %H:%M')
        })
    
    def populate_folder_tree(self, folder_path):
        try:
            root_info = QFileInfo(str(folder_path))
            root_icon = self.icon_provider.icon(root_info)
            root_item = QTreeWidgetItem([folder_path.name])
            root_item.setIcon(0, root_icon)
            root_item.setData(0, Qt.ItemDataRole.UserRole, str(folder_path))
            self.folder_tree.addTopLevelItem(root_item)
            
            for item in folder_path.iterdir():
                if item.is_dir():
                    if not self.show_hidden_files and is_hidden_or_system(item):
                        continue
                    try:
                        item_info = QFileInfo(str(item))
                        item_icon = self.icon_provider.icon(item_info)
                        tree_item = QTreeWidgetItem([item.name])
                        tree_item.setIcon(0, item_icon)
                        tree_item.setData(0, Qt.ItemDataRole.UserRole, str(item))
                        root_item.addChild(tree_item)
                    except:
                        pass
        except PermissionError:
            pass
    
    def on_folder_double_click(self, item, column):
        folder_path = item.data(0, Qt.ItemDataRole.UserRole)
        if folder_path:
            self.open_folder(Path(folder_path))
    
    def open_archive_dialog(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Открыть архив",
            str(Path.home()),
            "Архивы (*.zip *.tar *.tar.gz *.tar.bz2 *.gz *.bz2);;Все файлы (*)"
        )
        if filename:
            self.open_archive(Path(filename))
    
    def add_file_to_table(self, item):
        try:
            stat = item.stat()
            file_info = {
                'name': item.name,
                'size': stat.st_size,
                'type': 'Папка' if item.is_dir() else self.get_file_type(item.name),
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                'icon_path': str(item)
            }
            self.add_file_to_table_row(file_info)
        except:
            pass
    
    def add_file_to_table_row(self, file_info):
        row = self.file_table.rowCount()
        self.file_table.insertRow(row)
        
        icon_item = QTableWidgetItem()
        if 'icon_path' in file_info and file_info['icon_path']:
            try:
                file_info_obj = QFileInfo(file_info['icon_path'])
                icon = self.icon_provider.icon(file_info_obj)
                icon_item.setIcon(icon)
            except:
                pass
        elif file_info['type'] == 'Папка':
            icon = self.icon_provider.icon(QFileIconProvider.IconType.Folder)
            icon_item.setIcon(icon)
        
        self.file_table.setItem(row, 0, icon_item)
        self.file_table.setItem(row, 1, QTableWidgetItem(file_info['name']))
        self.file_table.setItem(row, 2, QTableWidgetItem(self.format_size(file_info['size'])))
        self.file_table.setItem(row, 3, QTableWidgetItem(file_info['type']))
        self.file_table.setItem(row, 4, QTableWidgetItem(file_info['modified']))
    
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
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    def add_files(self):
        if not self.current_archive:
            QMessageBox.warning(self, "Внимание", "Сначала откройте или создайте архив")
            return
        
        files, _ = QFileDialog.getOpenFileNames(self, "Выберите файлы")
        if not files:
            return
        
        self.add_files_to_archive(files)
    
    def add_folder(self):
        if not self.current_archive:
            QMessageBox.warning(self, "Внимание", "Сначала откройте или создайте архив")
            return
        
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if not folder:
            return
        
        self.add_files_to_archive([folder])
    
    def add_files_to_archive(self, files):
        try:
            if self.archive_type == 'zip':
                with zipfile.ZipFile(self.current_archive, 'a') as zip_ref:
                    for file_path in files:
                        path = Path(file_path)
                        if path.is_dir():
                            for root, dirs, filenames in os.walk(path):
                                for filename in filenames:
                                    file = Path(root) / filename
                                    arcname = str(file.relative_to(path.parent))
                                    zip_ref.write(file, arcname)
                        else:
                            zip_ref.write(file_path, path.name)
            QMessageBox.information(self, "Успех", f"Добавлено: {len(files)}")
            self.open_archive(self.current_archive)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def extract_files(self):
        selected_rows = self.file_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Внимание", "Выберите файлы")
            return
        
        extract_path = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if not extract_path:
            return
        
        try:
            for index in selected_rows:
                row = index.row()
                filename = self.file_table.item(row, 1).text()
                
                if self.archive_type == 'zip':
                    with zipfile.ZipFile(self.current_archive, 'r') as zip_ref:
                        zip_ref.extract(filename, extract_path)
                elif self.archive_type == 'tar':
                    with tarfile.open(self.current_archive, 'r:*') as tar_ref:
                        tar_ref.extract(filename, extract_path)
            
            QMessageBox.information(self, "Успех", "Файлы извлечены")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def test_archive(self):
        if not self.current_archive:
            QMessageBox.warning(self, "Внимание", "Откройте архив")
            return
        try:
            if self.archive_type == 'zip':
                with zipfile.ZipFile(self.current_archive, 'r') as zip_ref:
                    result = zip_ref.testzip()
                    if result:
                        QMessageBox.warning(self, "Ошибка", f"Повреждён: {result}")
                    else:
                        QMessageBox.information(self, "Успех", "Архив цел")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def delete_files(self):
        if not self.current_archive or self.archive_type != 'zip':
            QMessageBox.warning(self, "Внимание", "Удаление поддерживается только для ZIP")
            return
        
        selected_rows = self.file_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Удалить выбранные файлы?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                files_to_delete = [self.file_table.item(index.row(), 1).text() for index in selected_rows]
                new_archive = self.current_archive.with_suffix('.tmp')
                
                with zipfile.ZipFile(new_archive, 'w') as new_zip:
                    with zipfile.ZipFile(self.current_archive, 'r') as old_zip:
                        for item in old_zip.infolist():
                            if item.filename not in files_to_delete:
                                new_zip.writestr(item, old_zip.read(item.filename))
                
                self.current_archive.unlink()
                new_archive.rename(self.current_archive)
                self.open_archive(self.current_archive)
                QMessageBox.information(self, "Успех", "Файлы удалены")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))
    
    def create_archive(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Выберите файлы")
        if not files:
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Создать архив",
            str(Path.home() / "new_archive.zip"),
            "Архивы (*.zip *.tar *.tar.gz *.tar.bz2);;Все файлы (*)"
        )
        if not filename:
            return
        
        try:
            suffix = Path(filename).suffix.lower()
            
            if suffix == '.zip':
                with zipfile.ZipFile(filename, 'w') as zip_ref:
                    for file_path in files:
                        path = Path(file_path)
                        if path.is_dir():
                            for root, dirs, filenames in os.walk(path):
                                for filename in filenames:
                                    file = Path(root) / filename
                                    arcname = str(file.relative_to(path.parent))
                                    zip_ref.write(file, arcname)
                        else:
                            zip_ref.write(file_path, path.name)
            elif suffix in ['.tar', '.tar.gz', '.tgz', '.tar.bz2']:
                mode = 'w' if suffix == '.tar' else 'w:gz' if suffix in ['.tar.gz', '.tgz'] else 'w:bz2'
                with tarfile.open(filename, mode) as tar_ref:
                    for file_path in files:
                        path = Path(file_path)
                        if path.is_dir():
                            tar_ref.add(file_path, path.name)
                        else:
                            tar_ref.add(file_path, path.name)
            
            QMessageBox.information(self, "Успех", f"Архив создан:\n{filename}")
            self.open_archive(Path(filename))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def search_files(self):
        search_term, ok = QInputDialog.getText(self, "Поиск", "Введите имя:")
        if not ok or not search_term:
            return
        
        found = []
        for row in range(self.file_table.rowCount()):
            name_item = self.file_table.item(row, 1)
            if name_item and search_term.lower() in name_item.text().lower():
                found.append(row)
        
        if found:
            self.file_table.clearSelection()
            for row in found:
                self.file_table.selectRow(row)
            QMessageBox.information(self, "Найдено", f"Файлов: {len(found)}")
    
    def show_info(self):
        if self.current_archive:
            stats = self.current_archive.stat()
            info = f"Имя: {self.current_archive.name}\nРазмер: {self.format_size(stats.st_size)}\nФайлов: {len(self.files_list)}"
            QMessageBox.information(self, "Информация", info)
        else:
            QMessageBox.information(self, "Информация", "Архив не открыт")
    
    def show_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            dialog.save_settings()
            self.load_settings()
            
            current_path = Path(self.address_entry.text())
            if current_path.exists() and current_path.is_dir():
                self.open_folder(current_path)
    
    def show_about(self):
        QMessageBox.about(
            self,
            "О Vanadium Archiver",
            "Vanadium Archiver v0.7.7 Beta\n Сделанно на Python 3.14\n\n build nt1026314"
        )
    
    def on_file_double_click(self, index):
        row = index.row()
        filename = self.file_table.item(row, 1).text()
        file_type = self.file_table.item(row, 3).text()
        
        if self.current_archive:
            if file_type == 'Папка':
                self.show_archive_folder(filename)
            elif Path(filename).suffix.lower() in ['.zip', '.rar', '.7z', '.tar', '.tar.gz', '.tgz', '.tar.bz2']:
                self.extract_and_open(filename)
        else:
            if Path(filename).suffix.lower() in ['.zip', '.rar', '.7z', '.tar', '.tar.gz', '.tgz', '.tar.bz2']:
                filepath = Path(self.address_entry.text()) / filename
                if filepath.exists():
                    self.open_archive(filepath)
                return
            
            if file_type == 'Папка':
                folder_path = Path(self.address_entry.text()) / filename
                if folder_path.exists():
                    self.open_folder(folder_path)
    
    def show_archive_folder(self, folder_name):
        self.file_table.setRowCount(0)
        self.files_list = []
        
        prefix = folder_name if folder_name.endswith('/') else folder_name + '/'
        
        for file_info in self.files_list:
            if file_info['name'].startswith(prefix):
                relative_name = file_info['name'][len(prefix):]
                if '/' in relative_name:
                    subfolder = relative_name.split('/')[0]
                    subfolder_path = prefix + subfolder
                    if not any(f['name'] == subfolder_path for f in self.files_list):
                        self.files_list.append({
                            'name': subfolder_path,
                            'size': 0,
                            'type': 'Папка',
                            'modified': file_info['modified']
                        })
                else:
                    self.files_list.append(file_info)
        
        seen = set()
        unique_files = []
        for f in self.files_list:
            if f['name'] not in seen:
                seen.add(f['name'])
                unique_files.append(f)
        
        self.files_list = unique_files
        
        for file_info in self.files_list:
            self.add_file_to_table_row(file_info)
        
        self.statusBar().showMessage(f"Папка: {folder_name}")
    
    def extract_and_open(self, filename):
        temp_dir = Path.home() / "VanadiumTemp"
        temp_dir.mkdir(exist_ok=True)
        temp_file = temp_dir / filename
        
        try:
            if self.archive_type == 'zip':
                with zipfile.ZipFile(self.current_archive, 'r') as zip_ref:
                    zip_ref.extract(filename, temp_dir)
            self.open_archive(temp_file)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def go_up_folder(self):
        if self.current_archive:
            return
        
        current_path = Path(self.address_entry.text())
        parent_path = current_path.parent
        
        if parent_path.exists() and parent_path != current_path:
            self.open_folder(parent_path)
    
    def go_to_path(self):
        path = Path(self.address_entry.text())
        if path.exists():
            if path.is_dir():
                self.open_folder(path)
            else:
                self.open_archive(path)
        else:
            QMessageBox.warning(self, "Ошибка", f"Путь не существует:\n{path}")
    
    def show_context_menu(self, position):
        menu = QMenu(self)
        
        if self.current_archive:
            extract_action = menu.addAction("Извлечь")
            extract_action.triggered.connect(self.extract_files)
            
            delete_action = menu.addAction("Удалить")
            delete_action.triggered.connect(self.delete_files)
        else:
            open_action = menu.addAction("Открыть")
            open_action.triggered.connect(lambda: self.on_file_double_click(self.file_table.currentIndex()))
        
        menu.exec(self.file_table.viewport().mapToGlobal(position))


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = VanadiumArchiver()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
