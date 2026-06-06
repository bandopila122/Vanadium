import sys
import os
import zipfile
import tempfile
import shutil
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
                             QToolBar, QAbstractItemView, QHeaderView, QStatusBar, 
                             QFileDialog, QMessageBox, QLineEdit, QVBoxLayout, QWidget)
from PyQt6.QtGui import QIcon, QDragEnterEvent, QDropEvent
from PyQt6.QtCore import Qt, QSize

class VanadiumApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vanadium")
        self.setMinimumSize(1000, 650)
        
        self.icon_dir = "icons"
        main_icon_path = os.path.join(self.icon_dir, "archive.ico")
        if os.path.exists(main_icon_path):
            self.setWindowIcon(QIcon(main_icon_path))

        self.current_archive = None  
        self.archive_path = ""       
        self.local_dir = os.path.expanduser("~")  
        
        if not os.path.exists(self.local_dir):
            self.local_dir = os.path.abspath(os.sep)

        self.setup_ui()
        self.update_view()

    def setup_ui(self):
        self.toolbar = QToolBar("Панель управления Vanadium")
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(self.toolbar)

        self.action_add = self.toolbar.addAction(self.get_icon("Add.ico"), "Добавить")
        self.action_add.triggered.connect(self.handle_add)
        
        self.action_extract = self.toolbar.addAction(self.get_icon("Extract.ico"), "Извлечь...")
        self.action_extract.triggered.connect(self.handle_extract)
        
        self.action_delete = self.toolbar.addAction(self.get_icon("Delete.ico"), "Удалить")
        self.action_delete.triggered.connect(self.handle_delete)
        
        self.action_info = self.toolbar.addAction(self.get_icon("Info.ico"), "Информация")
        self.action_info.triggered.connect(self.handle_info)

        self.toolbar.addSeparator()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Поиск файлов в текущей папке...")
        self.search_bar.setFixedWidth(280)
        self.search_bar.textChanged.connect(self.filter_files)
        self.toolbar.addWidget(self.search_bar)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Имя", "Размер", "Тип", "Дата изменения"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSortingEnabled(False)  
        
        self.table.cellDoubleClicked.connect(self.handle_double_click)

        self.setAcceptDrops(True)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table)
        self.setCentralWidget(container)

        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Vanadium запущен успешно.")

    def get_icon(self, icon_name):
        path = os.path.join(self.icon_dir, icon_name)
        if os.path.exists(path):
            return QIcon(path)
        return QIcon() 

    def update_view(self):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        self.search_bar.clear()

        if self.current_archive:
            self.setWindowTitle(f"Vanadium - [Архив] {os.path.basename(self.current_archive)}:/{self.archive_path}")
            self.statusBar().showMessage(f"Просмотр архива: {self.current_archive}")
            self.action_extract.setEnabled(True)
            self.action_delete.setEnabled(True)
            self.action_info.setEnabled(True)
            self.render_archive_view()
        else:
            self.setWindowTitle(f"Vanadium - [Проводник] {self.local_dir}")
            self.statusBar().showMessage(f"Локальный каталог: {self.local_dir}")
            self.action_extract.setEnabled(False) 
            self.action_delete.setEnabled(True)
            self.action_info.setEnabled(False)
            self.render_local_view()
            
        self.table.setSortingEnabled(True)

    def render_local_view(self):
        try:
            parent_dir = os.path.dirname(self.local_dir)
            if parent_dir != self.local_dir:
                self.add_table_row("..", "", "Папка", "", is_up_dir=True)

            items = os.listdir(self.local_dir)
            
            folders = []
            files = []
            for item in items:
                full_path = os.path.join(self.local_dir, item)
                try:
                    if os.path.isdir(full_path):
                        folders.append(item)
                    else:
                        files.append(item)
                except OSError:
                    continue
                    
            folders.sort(key=str.lower)
            files.sort(key=str.lower)

            for folder in folders:
                full_path = os.path.join(self.local_dir, folder)
                mtime = os.path.getmtime(full_path)
                date_str = self.format_timestamp(mtime)
                self.add_table_row(folder, "", "Папка", date_str, icon_name="Folder.ico")

            for file in files:
                full_path = os.path.join(self.local_dir, file)
                size = os.path.getsize(full_path)
                size_str = f"{size:,}".replace(',', ' ') + " Б"
                mtime = os.path.getmtime(full_path)
                date_str = self.format_timestamp(mtime)
                
                if file.lower().endswith('.zip'):
                    self.add_table_row(file, size_str, "Архив ZIP", date_str, icon_name="archive.ico")
                else:
                    self.add_table_row(file, size_str, "Файл", date_str, icon_name="Computer.ico")
        except Exception as e:
            self.statusBar().showMessage(f"Ошибка доступа к директории: {e}")

    def render_archive_view(self):
        self.add_table_row("..", "", "Папка", "", is_up_dir=True)

        try:
            with zipfile.ZipFile(self.current_archive, 'r') as z:
                infolist = z.infolist()
                
                current_level_dirs = set()
                current_level_files = []

                for info in infolist:
                    name = info.filename
                    if name.startswith(self.archive_path) and name != self.archive_path:
                        relative_name = name[len(self.archive_path):]
                        parts = relative_name.split('/')
                        
                        if len(parts) > 1 and parts[1] != '':
                            current_level_dirs.add(parts[0] + '/')
                        elif parts[0] != '':
                            if info.is_dir():
                                current_level_dirs.add(parts[0] + '/')
                            else:
                                current_level_files.append(info)

                for folder in sorted(current_level_dirs):
                    clean_folder_name = folder.rstrip('/')
                    self.add_table_row(clean_folder_name, "", "Папка внутри архива", "", icon_name="Folder.ico")

                for file_info in sorted(current_level_files, key=lambda x: x.filename):
                    filename = os.path.basename(file_info.filename.rstrip('/'))
                    size_str = f"{file_info.file_size:,}".replace(',', ' ') + " Б"
                    date_str = f"{file_info.date_time[0]:04d}-{file_info.date_time[1]:02d}-{file_info.date_time[2]:02d} {file_info.date_time[3]:02d}:{file_info.date_time[4]:02d}"
                    self.add_table_row(filename, size_str, "Файл архива", date_str, icon_name="Computer.ico")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось прочитать структуру архива: {e}")
            self.current_archive = None
            self.update_view()

    def add_table_row(self, name, size, item_type, date_str, icon_name=None, is_up_dir=False):
        row = self.table.rowCount()
        self.table.insertRow(row)

        name_item = QTableWidgetItem(name)
        if is_up_dir:
            name_item.setIcon(self.get_icon("Folder.ico")) 
        elif icon_name:
            name_item.setIcon(self.get_icon(icon_name))
            
        name_item.setData(Qt.ItemDataRole.UserRole, {"is_up": is_up_dir, "type": item_type})

        self.table.setItem(row, 0, name_item)
        self.table.setItem(row, 1, QTableWidgetItem(size))
        self.table.setItem(row, 2, QTableWidgetItem(item_type))
        self.table.setItem(row, 3, QTableWidgetItem(date_str))

    def handle_double_click(self, row, column):
        name_item = self.table.item(row, 0)
        if not name_item: return
        
        data = name_item.data(Qt.ItemDataRole.UserRole)
        item_name = name_item.text()

        if data.get("is_up"):
            if self.current_archive:
                if self.archive_path == "":
                    self.current_archive = None
                    self.update_view()
                else:
                    parts = self.archive_path.rstrip('/').split('/')
                    parts.pop()
                    self.archive_path = "/".join(parts) + "/" if parts else ""
                    self.update_view()
            else:
                self.local_dir = os.path.dirname(self.local_dir)
                self.update_view()
            return

        if self.current_archive:
            if "Папка" in data.get("type"):
                self.archive_path += item_name + "/"
                self.update_view()
        else:
            full_path = os.path.join(self.local_dir, item_name)
            if os.path.isdir(full_path):
                self.local_dir = full_path
                self.update_view()
            elif item_name.lower().endswith('.zip'):
                self.current_archive = full_path
                self.archive_path = ""
                self.update_view()

    def handle_add(self):
        if self.current_archive:
            files, _ = QFileDialog.getOpenFileNames(self, "Выбрать файлы для добавления в архив")
            if files:
                self.inject_files_into_zip(files)
        else:
            selected_rows = set(item.row() for item in self.table.selectedItems())
            if not selected_rows:
                QMessageBox.warning(self, "Vanadium", "Выдели файлы в списке, которые хочешь запаковать!")
                return
                
            files_to_pack = []
            for r in selected_rows:
                name = self.table.item(r, 0).text()
                if name == "..": continue
                files_to_pack.append(os.path.join(self.local_dir, name))

            save_path, _ = QFileDialog.getSaveFileName(self, "Создать новый архив ZIP", self.local_dir, "ZIP Архивы (*.zip)")
            if save_path:
                try:
                    with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as z:
                        for f in files_to_pack:
                            if os.path.isdir(f):
                                for root, _, filenames in os.walk(f):
                                    for filename in filenames:
                                        filepath = os.path.join(root, filename)
                                        arcname = os.path.relpath(filepath, os.path.dirname(f))
                                        z.write(filepath, arcname)
                            else:
                                z.write(f, os.path.basename(f))
                    QMessageBox.information(self, "Успех", "Архив успешно создан!")
                    self.update_view()
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка упаковки", str(e))

    def handle_extract(self):
        if not self.current_archive: return
        
        selected_rows = set(item.row() for item in self.table.selectedItems())
        if not selected_rows:
            QMessageBox.warning(self, "Vanadium", "Выдели файлы внутри архива для распаковки!")
            return

        dest_dir = QFileDialog.getExistingDirectory(self, "Выберите папку для извлечения", self.local_dir)
        if not dest_dir: return

        try:
            with zipfile.ZipFile(self.current_archive, 'r') as z:
                for r in selected_rows:
                    name = self.table.item(r, 0).text()
                    if name == "..": continue
                    
                    full_internal_prefix = self.archive_path + name
                    
                    for member in z.infolist():
                        if member.filename.startswith(full_internal_prefix):
                            z.extract(member, dest_dir)
                            
            QMessageBox.information(self, "Успех", f"Успешно извлечено в каталог:\n{dest_dir}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка извлечения", str(e))

    def handle_delete(self):
        selected_rows = set(item.row() for item in self.table.selectedItems())
        if not selected_rows:
            QMessageBox.warning(self, "Vanadium", "Выдели элементы для удаления!")
            return

        names_to_delete = [self.table.item(r, 0).text() for r in selected_rows if self.table.item(r, 0).text() != ".."]
        if not names_to_delete: return

        reply = QMessageBox.question(
            self, 'Подтверждение удаления', 
            f"Уничтожить выделенные объекты ({len(names_to_delete)} шт.) безвозвратно?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No: return

        if self.current_archive:
            temp_fd, temp_path = tempfile.mkstemp(suffix='.zip')
            os.close(temp_fd)
            try:
                full_prefixes_to_delete = [self.archive_path + n for n in names_to_delete]
                
                with zipfile.ZipFile(self.current_archive, 'r') as zin:
                    with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zout:
                        for item in zin.infolist():
                            should_delete = False
                            for prefix in full_prefixes_to_delete:
                                if item.filename.startswith(prefix):
                                    should_delete = True
                                    break
                            if not should_delete:
                                zout.writestr(item, zin.read(item.filename))
                
                shutil.move(temp_path, self.current_archive)
                self.update_view()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка удаления из архива", str(e))
                if os.path.exists(temp_path): os.remove(temp_path)
        else:
            try:
                for name in names_to_delete:
                    full_path = os.path.join(self.local_dir, name)
                    if os.path.isdir(full_path):
                        shutil.rmtree(full_path)
                    else:
                        os.remove(full_path)
                self.update_view()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка удаления", str(e))

    def handle_info(self):
        if not self.current_archive: return
        try:
            with zipfile.ZipFile(self.current_archive, 'r') as z:
                infolist = z.infolist()
                files = [i for i in infolist if not i.is_dir()]
                dirs = [i for i in infolist if i.is_dir()]
                raw_size = sum(i.file_size for i in files)
                compressed_size = sum(i.compress_size for i in files)
                ratio = (100 - (compressed_size * 100 / raw_size)) if raw_size > 0 else 0
                
                msg = (
                    f"<b>Архив:</b> {os.path.basename(self.current_archive)}<br>"
                    f"<b>Местоположение:</b> {self.current_archive}<br><br>"
                    f"<b>Всего файлов:</b> {len(files)}<br>"
                    f"<b>Всего папок:</b> {len(dirs)}<br>"
                    f"<b>Исходный вес файлов:</b> {raw_size:,} Б<br>"
                    f"<b>Размер после сжатия:</b> {compressed_size:,} Б<br>"
                    f"<b>Эффективность компрессии:</b> {ratio:.2f}%"
                )
                QMessageBox.information(self, "Параметры архива Vanadium", msg)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка анализа", str(e))

    def inject_files_into_zip(self, file_paths):
        try:
            with zipfile.ZipFile(self.current_archive, 'a', zipfile.ZIP_DEFLATED) as z:
                for f in file_paths:
                    if os.path.isdir(f):
                        for root, _, filenames in os.walk(f):
                            for filename in filenames:
                                filepath = os.path.join(root, filename)
                                rel_path = os.path.relpath(filepath, os.path.dirname(f))
                                internal_target = self.archive_path + rel_path
                                z.write(filepath, internal_target)
                    else:
                        internal_target = self.archive_path + os.path.basename(f)
                        z.write(f, internal_target)
            self.update_view()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка добавления", str(e))

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        files = [u.toLocalFile() for u in urls if u.isLocalFile()]
        if not files: return

        if self.current_archive:
            self.inject_files_into_zip(files)
        else:
            if len(files) == 1 and files[0].lower().endswith('.zip'):
                self.current_archive = files[0]
                self.archive_path = ""
                self.update_view()
            else:
                reply = QMessageBox.question(
                    self, 'Создание архива', 
                    f"Создать новый ZIP-архив из перетащенных элементов ({len(files)} шт.)?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    save_path, _ = QFileDialog.getSaveFileName(self, "Создать новый архив ZIP", self.local_dir, "ZIP Архивы (*.zip)")
                    if save_path:
                        try:
                            with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as z:
                                for f in files:
                                    if os.path.isdir(f):
                                        for root, _, filenames in os.walk(f):
                                            for filename in filenames:
                                                filepath = os.path.join(root, filename)
                                                arcname = os.path.relpath(filepath, os.path.dirname(f))
                                                z.write(filepath, arcname)
                                    else:
                                        z.write(f, os.path.basename(f))
                            self.update_view()
                        except Exception as e:
                            QMessageBox.critical(self, "Ошибка", str(e))

    def filter_files(self, text):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                if item.text() == "..":
                    self.table.setRowHidden(row, False)
                    continue
                self.table.setRowHidden(row, text.lower() not in item.text().lower())

    @staticmethod
    def format_timestamp(timestamp):
        import datetime
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = VanadiumApp()
    window.show()
    sys.exit(app.exec())
