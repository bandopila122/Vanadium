import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton,
    QDialogButtonBox, QRadioButton, QButtonGroup, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QFont


TEMP_DIR = Path.home() / "VanadiumTemp"


class Translator:
    def __init__(self, base_path, language='ru'):
        self.base_path = Path(base_path)
        self.locales_path = self.base_path / "locales"
        self.language = language
        self.strings = {}
        self._load()

    def _load(self):
        fallback = self.locales_path / "ru.json"
        target = self.locales_path / f"{self.language}.json"

        if fallback.exists():
            try:
                with open(fallback, 'r', encoding='utf-8') as f:
                    self.strings = json.load(f)
            except Exception:
                self.strings = {}

        if target.exists() and target != fallback:
            try:
                with open(target, 'r', encoding='utf-8') as f:
                    override = json.load(f)
                    self.strings.update(override)
            except Exception:
                pass

    def t(self, key, *args):
        text = self.strings.get(key, key)
        if args:
            try:
                return text.format(*args)
            except Exception:
                return text
        return text

    def set_language(self, language):
        self.language = language
        self._load()


class ThemeManager:
    THEMES = {
        'win10': 'theme_win10',
        'winxp': 'theme_winxp',
        'win9x': 'theme_win9x'
    }

    @staticmethod
    def apply(window, theme_name, base_path, translator=None):
        themes_path = Path(base_path) / "themes"
        qss_file = themes_path / f"{theme_name}.qss"

        stylesheet = ""
        if qss_file.exists():
            try:
                with open(qss_file, 'r', encoding='utf-8') as f:
                    stylesheet = f.read()
            except Exception:
                stylesheet = ""

        window.setStyleSheet(stylesheet)

        if theme_name == 'win10':
            window.setFont(QFont("Segoe UI", 9))
        elif theme_name == 'winxp':
            window.setFont(QFont("Tahoma", 8))
        elif theme_name == 'win9x':
            window.setFont(QFont("MS Sans Serif", 8))
        else:
            window.setFont(QFont("Segoe UI", 9))


class WelcomeDialog(QDialog):
    def __init__(self, parent=None, translator=None):
        super().__init__(parent)
        self.tr = translator
        self.setWindowTitle(self.tr.t("welcome_title"))
        self.setFixedSize(620, 560)

        layout = QVBoxLayout(self)

        title = QLabel(f"🎉 {self.tr.t('welcome_title')}")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #0078D4; margin: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        intro = QLabel(self.tr.t("welcome_intro"))
        intro.setStyleSheet("font-size: 10pt; margin: 5px;")
        layout.addWidget(intro)

        features = [
            ("📦", "welcome_f1", "welcome_f1_desc"),
            ("📂", "welcome_f2", "welcome_f2_desc"),
            ("🔍", "welcome_f3", "welcome_f3_desc"),
            ("🎨", "welcome_f4", "welcome_f4_desc"),
            ("🖱️", "welcome_f5", "welcome_f5_desc"),
            ("⬆️", "welcome_f6", "welcome_f6_desc"),
            ("🌙", "welcome_f7", "welcome_f7_desc"),
            ("🔒", "welcome_f8", "welcome_f8_desc"),
            ("🗑️", "welcome_f9", "welcome_f9_desc"),
            ("🛡️", "welcome_f10", "welcome_f10_desc"),
        ]

        features_html = "<table style='font-size: 10pt; margin: 10px;'>"
        for icon, title_key, desc_key in features:
            features_html += f"<tr><td style='padding: 4px 8px;'>{icon}</td><td><b>{self.tr.t(title_key)}</b> — {self.tr.t(desc_key)}</td></tr>"
        features_html += "</table>"

        features_label = QLabel(features_html)
        features_label.setStyleSheet("background-color: #F5F5F5; border: 1px solid #DDD; border-radius: 4px; padding: 10px;")
        layout.addWidget(features_label)

        tips = QLabel(f"<b>💡 {self.tr.t('welcome_tip')}</b>")
        tips.setStyleSheet("font-size: 9pt; color: #555; margin: 5px;")
        tips.setWordWrap(True)
        layout.addWidget(tips)

        luck = QLabel(
            f"<b>🍀 {self.tr.t('welcome_luck')}</b><br>"
            f"<i>{self.tr.t('welcome_luck_sub')}</i>"
        )
        luck.setStyleSheet("font-size: 11pt; color: #0078D4; margin: 10px;")
        luck.setAlignment(Qt.AlignmentFlag.AlignCenter)
        luck.setWordWrap(True)
        layout.addWidget(luck)

        self.dont_show_again = QCheckBox(self.tr.t("welcome_dont_show"))
        layout.addWidget(self.dont_show_again)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def should_not_show_again(self):
        return self.dont_show_again.isChecked()


class MigrationDialog(QDialog):
    def __init__(self, parent=None, translator=None):
        super().__init__(parent)
        self.tr = translator
        self.setWindowTitle(self.tr.t("migration_title"))
        self.setFixedSize(450, 260)

        layout = QVBoxLayout(self)

        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet("font-size: 40pt;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        msg = QLabel(f"<b>{self.tr.t('migration_title')}</b><br><br>{self.tr.t('migration_msg')}")
        msg.setStyleSheet("font-size: 11pt; margin: 10px;")
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg)

        layout.addSpacing(10)

        migrate_btn = QPushButton(f"🔄 {self.tr.t('migration_convert')}")
        migrate_btn.setStyleSheet("background-color: #0078D4; color: white; padding: 8px; border-radius: 4px; font-weight: bold;")
        migrate_btn.clicked.connect(lambda: self.done(1))
        layout.addWidget(migrate_btn)

        fresh_btn = QPushButton(f"🆕 {self.tr.t('migration_fresh')}")
        fresh_btn.setStyleSheet("background-color: #D83B01; color: white; padding: 8px; border-radius: 4px; font-weight: bold;")
        fresh_btn.clicked.connect(lambda: self.done(2))
        layout.addWidget(fresh_btn)

        layout.addSpacing(5)

        note = QLabel(f"<i>{self.tr.t('migration_note')}</i>")
        note.setStyleSheet("color: #666; font-size: 9pt;")
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(note)

        self.choice = 0

    def done(self, result):
        self.choice = result
        super().done(result)

    def get_choice(self):
        return self.choice


class SettingsDialog(QDialog):
    def __init__(self, parent=None, translator=None, current_theme='win10', current_lang='ru'):
        super().__init__(parent)
        self.tr = translator
        self.setWindowTitle(self.tr.t("settings_title"))
        self.setFixedSize(480, 620)
        self.current_theme = current_theme
        self.current_lang = current_lang

        layout = QVBoxLayout(self)

        display_header = QLabel(self.tr.t("settings_display"))
        display_header.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(display_header)

        self.show_hidden_checkbox = QCheckBox(self.tr.t("settings_hidden"))
        self.show_system_checkbox = QCheckBox(self.tr.t("settings_system"))
        layout.addWidget(self.show_hidden_checkbox)
        layout.addWidget(self.show_system_checkbox)

        layout.addSpacing(10)

        theme_header = QLabel(self.tr.t("settings_theme"))
        theme_header.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(theme_header)

        self.theme_group = QButtonGroup()
        theme_box = QFrame()
        theme_box_layout = QVBoxLayout(theme_box)
        for key, label_key in ThemeManager.THEMES.items():
            rb = QRadioButton(self.tr.t(label_key))
            rb.setProperty('theme_key', key)
            if key == current_theme:
                rb.setChecked(True)
            self.theme_group.addButton(rb)
            theme_box_layout.addWidget(rb)
        layout.addWidget(theme_box)

        theme_note = QLabel(f"<i>{self.tr.t('settings_theme_note')}</i>")
        theme_note.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(theme_note)

        layout.addSpacing(10)

        lang_header = QLabel(self.tr.t("settings_language"))
        lang_header.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(lang_header)

        self.lang_group = QButtonGroup()
        lang_box = QFrame()
        lang_box_layout = QVBoxLayout(lang_box)
        for key, label_key in [('ru', 'lang_ru'), ('en', 'lang_en')]:
            rb = QRadioButton(self.tr.t(label_key))
            rb.setProperty('lang_key', key)
            if key == current_lang:
                rb.setChecked(True)
            self.lang_group.addButton(rb)
            lang_box_layout.addWidget(rb)
        layout.addWidget(lang_box)

        lang_note = QLabel(f"<i>{self.tr.t('settings_language_note')}</i>")
        lang_note.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(lang_note)

        layout.addSpacing(10)

        temp_header = QLabel(self.tr.t("settings_temp"))
        temp_header.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(temp_header)

        temp_btn = QPushButton(self.tr.t("settings_clean_temp"))
        temp_btn.clicked.connect(self.clean_temp_now)
        layout.addWidget(temp_btn)

        temp_info = QLabel(f"{TEMP_DIR}")
        temp_info.setStyleSheet("color: #666; font-size: 9pt;")
        temp_info.setWordWrap(True)
        layout.addWidget(temp_info)

        layout.addSpacing(10)

        about_header = QLabel(self.tr.t("settings_about"))
        about_header.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(about_header)

        about_text = QLabel(
            "<b>Vanadium Archiver v1.1.0</b><br><br>"
            "Форматы: ZIP, TAR, GZ, BZ2<br><br>"
            "Лицензия: MIT | Python 3.14 | PyQt6<br><br>"
            "<a href='https://github.com/bandopila122/Vanadium'>GitHub</a> | "
            "<a href='https://github.com/bandopila122/Vanadium/blob/main/README.md'>README</a> | "
            "<a href='https://github.com/bandopila122/Vanadium/blob/main/LICENSE'>LICENSE</a>"
        )
        about_text.setOpenExternalLinks(True)
        about_text.setWordWrap(True)
        about_text.setStyleSheet("padding: 8px; background-color: #F5F5F5; border-radius: 4px;")
        layout.addWidget(about_text)

        layout.addStretch()

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.load_settings()

    def load_settings(self):
        settings = QSettings("VanaArchiver", "Settings")
        self.show_hidden_checkbox.setChecked(settings.value("show_hidden_files", False, type=bool))
        self.show_system_checkbox.setChecked(settings.value("show_system_files", False, type=bool))

    def get_selected_theme(self):
        btn = self.theme_group.checkedButton()
        if btn:
            return btn.property('theme_key')
        return self.current_theme

    def get_selected_language(self):
        btn = self.lang_group.checkedButton()
        if btn:
            return btn.property('lang_key')
        return self.current_lang

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
                for item in list(TEMP_DIR.rglob('*')):
                    try:
                        if item.is_dir() and not any(item.iterdir()):
                            item.rmdir()
                    except:
                        pass
                if failed > 0:
                    QMessageBox.warning(self, self.tr.t("warning"), self.tr.t("temp_partial", failed))
                else:
                    QMessageBox.information(self, self.tr.t("success"), self.tr.t("temp_cleaned"))
        except Exception as e:
            QMessageBox.critical(self, self.tr.t("error"), str(e))

    def save_settings(self):
        settings = QSettings("VanaArchiver", "Settings")
        settings.setValue("show_hidden_files", self.show_hidden_checkbox.isChecked())
        settings.setValue("show_system_files", self.show_system_checkbox.isChecked())
        settings.setValue("theme", self.get_selected_theme())
        settings.setValue("language", self.get_selected_language())