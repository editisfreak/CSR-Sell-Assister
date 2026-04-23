import json
import http.client
import requests
import sys
import os
import random
import io
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QScrollArea, 
                             QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, 
                             QGridLayout, QSizePolicy, QLineEdit, QDialog, QShortcut,
                             QGraphicsOpacityEffect, QComboBox, QDoubleSpinBox, QSpinBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QVariantAnimation, QEvent, QTimer, QPropertyAnimation, QSize
from PyQt5.QtGui import QPixmap, QImage, QFont, QCursor, QFontMetrics, QFontDatabase, QPainter, QKeySequence, QColor, QLinearGradient, QStandardItemModel, QStandardItem, QIcon, QIntValidator, QPen
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtCore import QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

# --- ПОДКЛЮЧАЕМ PILLOW ДЛЯ ЖЕСТКОЙ КОНВЕРТАЦИИ ---
try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    ASSETS_DIR = os.path.join(sys._MEIPASS, 'assets')
    USER_DATA_DIR = os.path.join(os.getenv('LOCALAPPDATA', os.path.expanduser('~')), 'CSR_Assister')
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ASSETS_DIR = os.path.join(BASE_DIR, "assets")
    USER_DATA_DIR = os.path.join(BASE_DIR, "cache")

os.makedirs(USER_DATA_DIR, exist_ok=True)
if not getattr(sys, 'frozen', False):
    os.makedirs(ASSETS_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(USER_DATA_DIR, "config.json")
CONFIG = {}

def load_config():
    global CONFIG
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                CONFIG = json.load(f)
        except:
            CONFIG = {"mod": "none"}
    else:
        CONFIG = {"mod": "none"}

def save_config():
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(CONFIG, f, indent=4)

TRANSLATIONS = {
    "en": {
        "auth_req": "Authorization Required", "enter_cookie": "Enter your cookie from CS:R", "paste_cookie": "Paste cookie here...",
        "exit": "Exit", "login": "Log in", "how_to_use": "How to use", "welcome_csr": "Welcome to CS:R Sell Assister",
        "main_inst": "How to use the app:\n\n• Left Click: Select single item.\n• Right Click: View item details.\n• Shift + Left Click: Select all items of same type.\n• Ctrl + Mouse Wheel: Zoom.\n• F1: Open this help.\n\nSelect items and click sell!",
        "got_it": "Got it", "how_to_cookie": "How to find your cookie",
        "cookie_inst": "1. Go to <a href='https://csrestored.fun/app/inventory' style='color: #5e98d9; text-decoration: none;'>csrestored.fun/app/inventory</a><br><br>2. Open DevTools (F12) -> Network.<br><br>3. Refresh page. Your cookie is in 'Request Headers'.",
        "sell_items": "Sell Items", "selling": "Selling...", "sell_count": "Sell Items ({})", "warning_title": "Attention!",
        "warning_text": "This program is an experiment.\n\nMany things might change.\n\nHowever, it can be extremely useful for mass selling.",
        "search_ph": "Search (e.g. ak red)...", "filters": "Filters", "f_rarity": "Rarity", "f_cond": "Condition", "f_float": "Float Range",
        "f_nametag": "Nametag", "f_stattrak": "StatTrak™", "f_type": "Weapon Type", "f_all": "All", "f_yes": "Yes", "f_no": "No",
        "f_apply": "Apply", "f_reset": "Reset Filters",
        "cond_fn": "Factory New", "cond_mw": "Minimal Wear", "cond_ft": "Field-Tested", "cond_ww": "Well-Worn", "cond_bs": "Battle-Scarred",
        "rarity_6": "Consumer Grade", "rarity_5": "Industrial Grade", "rarity_4": "Mil-Spec", "rarity_3": "Restricted", "rarity_2": "Classified", "rarity_1": "Covert", "rarity_0": "Contraband/Melee",
        "btn_cases": "Cases", "btn_inventory": "Inventory", "btn_back": "< Back", "btn_max": "Max", "btn_buy": "Buy", "buying": "Buying...", "unavailable": "Unavailable",
        "weapon_details": "Weapon Details", "pattern": "Pattern", "update_nametag": "Update nametag", "quick_sell": "Quick Sell", "item_float": "Item float:", "wear": "Wear", "updating": "Updating...",
        "confirm_title": "Confirm", "confirm_sell": "Are you sure you want to sell {} item(s)?", "yes": "Yes", "no": "No"
    },
    "ru": {
        "auth_req": "Требуется авторизация", "enter_cookie": "Введите ваш cookie от CS:R", "paste_cookie": "Вставьте cookie сюда...",
        "exit": "Выйти", "login": "Войти", "how_to_use": "Управление", "welcome_csr": "Добро пожаловать в CS:R Sell Assister",
        "main_inst": "Как пользоваться:\n\n• ЛКМ: Выбрать предмет.\n• ПКМ: Инфа о скине.\n• Shift + ЛКМ: Выбрать все предметы типа.\n• Ctrl + Колесико: Масштаб.\n• F1: Подсказки.",
        "got_it": "Понятно", "how_to_cookie": "Как получить cookie",
        "cookie_inst": "1. Зайдите на <a href='https://csrestored.fun/app/inventory' style='color: #5e98d9; text-decoration: none;'>csrestored.fun/app/inventory</a><br><br>2. F12 -> Network.<br><br>3. Обновите страницу. Скопируйте cookie из 'Request Headers'.",
        "sell_items": "Продать", "selling": "Продажа...", "sell_count": "Продать ({})", "warning_title": "Внимание!",
        "warning_text": "Программа является экспериментом.\n\nМногое может измениться.",
        "search_ph": "Поиск (напр. ak red)...", "filters": "Фильтры", "f_rarity": "Редкость", "f_cond": "Качество", "f_float": "Флоат",
        "f_nametag": "Неймтег", "f_stattrak": "StatTrak™", "f_type": "Тип оружия", "f_all": "Все", "f_yes": "Да", "f_no": "Нет",
        "f_apply": "Применить", "f_reset": "Сбросить",
        "cond_fn": "Прямо с завода", "cond_mw": "Немного поношенное", "cond_ft": "После полевых испытаний", "cond_ww": "Поношенное", "cond_bs": "Закаленное в боях",
        "rarity_6": "Ширпотреб", "rarity_5": "Промышленное", "rarity_4": "Армейское", "rarity_3": "Запрещенное", "rarity_2": "Засекреченное", "rarity_1": "Тайное", "rarity_0": "Ножи/Перчатки",
        "btn_cases": "Кейсы", "btn_inventory": "Инвентарь", "btn_back": "< Назад", "btn_max": "Макс", "btn_buy": "Купить", "buying": "Покупка...", "unavailable": "Недоступно",
        "weapon_details": "Детали оружия", "pattern": "Паттерн", "update_nametag": "Обновить неймтег", "quick_sell": "Быстрая продажа", "item_float": "Флоат предмета:", "wear": "Износ", "updating": "Обновление...",
        "confirm_title": "Подтверждение", "confirm_sell": "Вы уверены, что хотите продать {} предмет(ов)?", "yes": "Да", "no": "Нет"
    }
}

RARITY_COLORS = { "6": "#b0c3d9", "5": "#5e98d9", "4": "#4b69ff", "3": "#8847ff", "2": "#d32ce6", "1": "#eb4b4b", "0": "#e4ae39" }
DEFAULT_RARITY_COLOR = "#ffffff"

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6: return 255, 255, 255
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def ensure_font_downloaded():
    font_filename = "ApercuPro-Medium.ttf"
    font_path = os.path.join(ASSETS_DIR, font_filename)
    if not os.path.exists(font_path):
        font_path = os.path.join(USER_DATA_DIR, font_filename)
        if not os.path.exists(font_path):
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get("https://bestfonts.pro/fonts_files/5cbded95465f40fe806ab3e9/files/ApercuPro-Medium.ttf", headers=headers, timeout=15)
                if response.status_code == 200:
                    with open(font_path, 'wb') as f:
                        f.write(response.content)
            except Exception:
                pass
    return font_path

def get_weapon_category(name):
    w_name = name.split(" | ")[0].replace("StatTrak™ ", "").replace("★ ", "").strip()
    if any(x in name for x in ["Knife", "Bayonet", "Karambit", "Daggers", "Butterfly", "Talon", "Navaja", "Stiletto", "Ursus", "Bowie", "Falchion", "Huntsman", "Gut"]):
        return "Gloves" if any(x in name for x in ["Gloves", "Wraps", "Bloodhound", "Hand"]) else "Knife"
    if w_name in ["Glock-18", "USP-S", "P2000", "P250", "Dual Berettas", "Tec-9", "Five-SeveN", "CZ75-Auto", "Desert Eagle", "R8 Revolver"]: return "Pistol"
    if w_name in ["MAC-10", "MP7", "MP9", "UMP-45", "P90", "PP-Bizon", "MP5-SD"]: return "SMG"
    if w_name in ["AK-47", "M4A4", "M4A1-S", "FAMAS", "Galil AR", "AUG", "SG 553"]: return "Rifle"
    if w_name in ["AWP", "SSG 08", "G3SG1", "SCAR-20"]: return "Sniper Rifle"
    if w_name in ["Nova", "XM1014", "Sawed-Off", "MAG-7"]: return "Shotgun"
    if w_name in ["M249", "Negev"]: return "Machinegun"
    return w_name

# ================= ВИДЖЕТЫ И UI КОМПОНЕНТЫ =================

class AspectRatioPixmapLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pixmap = None
    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        self.update()
    def paintEvent(self, event):
        if self._pixmap and not self._pixmap.isNull():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            scaled = self._pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap((self.width() - scaled.width()) // 2, (self.height() - scaled.height()) // 2, scaled)
        else:
            super().paintEvent(event)

class ElidedLabel(QLabel):
    def __init__(self, text, weight=QFont.Normal, *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._text = text
        self.font_weight = weight
    def set_font_size(self, size):
        font = self.font()
        font.setPointSize(size)
        font.setWeight(self.font_weight)
        font.setStyleStrategy(QFont.PreferAntialias)
        self.setFont(font)
        self.update()
    def setText(self, text):
        self._text = text
        self.update()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setRenderHint(QPainter.Antialiasing)
        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(self._text, Qt.ElideRight, self.width())
        painter.drawText(self.rect(), self.alignment(), elided)

class FloatBarWidget(QWidget):
    def __init__(self, float_val, parent=None):
        super().__init__(parent)
        self.float_val = float_val if float_val is not None else 0.0
        self.setFixedHeight(14)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        
        grad = QLinearGradient(0, 0, rect.width(), 0)
        grad.setColorAt(0.0, QColor("#00a1ff"))
        grad.setColorAt(0.07, QColor("#00a1ff"))
        grad.setColorAt(0.071, QColor("#4ade80"))
        grad.setColorAt(0.15, QColor("#4ade80"))
        grad.setColorAt(0.151, QColor("#facc15"))
        grad.setColorAt(0.38, QColor("#facc15"))
        grad.setColorAt(0.381, QColor("#f97316"))
        grad.setColorAt(0.45, QColor("#f97316"))
        grad.setColorAt(0.451, QColor("#ef4444"))
        grad.setColorAt(1.0, QColor("#ef4444"))
        
        painter.setBrush(grad)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 5, rect.width(), 4, 2, 2)
        
        x = int(self.float_val * rect.width())
        x = max(4, min(x, rect.width() - 4))
        
        painter.setBrush(Qt.white)
        painter.drawEllipse(x - 5, 2, 10, 10)

class CheckableComboBox(QComboBox):
    def __init__(self, placeholder, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().installEventFilter(self) 
        self.placeholder = placeholder
        self.lineEdit().setText(self.placeholder)
        self.model = QStandardItemModel(self)
        self.setModel(self.model)
        self.view().setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view().viewport().installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.lineEdit() and event.type() == QEvent.MouseButtonRelease:
            self.showPopup()
            return True
        if obj == self.view().viewport() and event.type() == QEvent.MouseButtonRelease:
            index = self.view().indexAt(event.pos())
            if index.isValid():
                item = self.model.itemFromIndex(index)
                item.setCheckState(Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked)
                self.update_text()
            return True 
        return False

    def update_text(self):
        checked = self.get_checked_texts()
        if not checked:
            self.lineEdit().setText(self.placeholder)
        else:
            self.lineEdit().setText(", ".join(checked))

    def add_item(self, text, text_color_hex, data=None):
        item = QStandardItem(text)
        item.setData(data or text, Qt.UserRole)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Unchecked)
        item.setForeground(QColor(text_color_hex))
        self.model.appendRow(item)

    def get_checked_data(self):
        return [self.model.item(i).data(Qt.UserRole) for i in range(self.model.rowCount()) if self.model.item(i).checkState() == Qt.Checked]

    def get_checked_texts(self):
        return [self.model.item(i).text() for i in range(self.model.rowCount()) if self.model.item(i).checkState() == Qt.Checked]

    def set_checked_data(self, data_list):
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            item.setCheckState(Qt.Checked if item.data(Qt.UserRole) in data_list else Qt.Unchecked)
        self.update_text()

class ResponsiveGridWidget(QWidget):
    def __init__(self, parent=None, scroll_area=None):
        super().__init__(parent)
        self.scroll_area = scroll_area
        self.grid = QGridLayout(self)
        self.grid.setSpacing(12)
        self.grid.setContentsMargins(15, 15, 15, 15)
        self.cards = []
        self.base_card_width = 180
        self.current_cols = 0
    
    def set_cards(self, visible_cards):
        for i in reversed(range(self.grid.count())):
            item = self.grid.itemAt(i)
            if item.widget():
                item.widget().hide()
                self.grid.removeWidget(item.widget())
        
        for i in range(self.grid.rowCount() + 5):
            self.grid.setRowStretch(i, 0)
        for i in range(self.grid.columnCount() + 5):
            self.grid.setColumnStretch(i, 0)
                
        self.cards = visible_cards
        self.reorganize()
        for card in self.cards:
            card.show()
            
    def remove_card(self, widget):
        if widget in self.cards:
            self.cards.remove(widget)
        widget.hide()
        self.grid.removeWidget(widget)
        widget.setParent(None)
        widget.deleteLater()
        self.reorganize()
        QApplication.processEvents()

    def zoom(self, direction):
        new_width = self.base_card_width + direction * 25
        if 100 <= new_width <= 400:
            self.base_card_width = new_width
            self.reorganize()
        
    def resizeEvent(self, event):
        self.reorganize()
        super().resizeEvent(event)
    
    def reorganize(self):
        if not self.cards: return
        w = max(self.scroll_area.viewport().width(), 100) if self.scroll_area else max(self.width(), 100)
        avail_w = w - 30
        cols = max(1, (avail_w + 12) // (self.base_card_width + 12))
        card_w = (avail_w - (12 * (cols - 1))) // cols
        card_h = int(card_w * 1.33) 
        
        for card in self.cards:
            card.setFixedSize(card_w, card_h)
        self.current_cols = cols
        
        for i in reversed(range(self.grid.count())):
            item = self.grid.itemAt(i)
            if item.widget():
                self.grid.removeWidget(item.widget())
            
        for idx, card in enumerate(self.cards):
            self.grid.addWidget(card, idx // cols, idx % cols, Qt.AlignLeft | Qt.AlignTop)
        for i in range(cols):
            self.grid.setColumnMinimumWidth(i, card_w)
            self.grid.setColumnStretch(i, 0)
        rows = (len(self.cards) + cols - 1) // cols
        self.grid.setRowStretch(rows, 1)

class SnowOverlay(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.flakes = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_flakes)
        self.is_running = False

    def start(self):
        self.resize(self.parent().size())
        self.show()
        self.raise_()
        self.flakes = [[random.randint(0, self.width()), random.randint(0, self.height()), random.uniform(1, 3), random.randint(2, 5)] for _ in range(100)]
        self.timer.start(30)
        self.is_running = True

    def stop(self):
        self.timer.stop()
        self.hide()
        self.is_running = False

    def update_flakes(self):
        for f in self.flakes:
            f[1] += f[2]
            f[0] += random.uniform(-0.5, 0.5) 
            if f[1] > self.height():
                f[1] = -10
                f[0] = random.randint(0, self.width())
        self.update()

    def paintEvent(self, event):
        if not self.is_running: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 200))
        for f in self.flakes:
            painter.drawEllipse(int(f[0]), int(f[1]), f[3], f[3])

class RainOverlay(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.flakes = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_flakes)
        self.is_running = False

    def start(self):
        self.resize(self.parent().size())
        self.show()
        self.raise_()
        self.flakes = [[random.randint(-50, self.width()+50), random.randint(-50, self.height()), random.uniform(1, 3), random.uniform(15, 25)] for _ in range(150)]
        self.timer.start(30)
        self.is_running = True

    def stop(self):
        self.timer.stop()
        self.hide()
        self.is_running = False

    def update_flakes(self):
        for f in self.flakes:
            f[1] += f[3]
            f[0] += f[2]
            if f[1] > self.height():
                f[1] = -20
                f[0] = random.randint(-50, self.width()+50)
        self.update()

    def paintEvent(self, event):
        if not self.is_running: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(150, 150, 170, 200), 2))
        for f in self.flakes:
            painter.drawLine(int(f[0]), int(f[1]), int(f[0] - f[2]*2), int(f[1] - f[3]*2))


# ================= ПОТОКИ API =================

class UserFetcher(QThread):
    data_ready = pyqtSignal(int)
    def __init__(self, cookie):
        super().__init__()
        self.cookie = cookie
    def run(self):
        try:
            conn = http.client.HTTPSConnection('api.csrestored.fun')
            headers = {'accept': '*/*', 'origin': 'https://csrestored.fun', 'referer': 'https://csrestored.fun/', 'user-agent': 'Mozilla/5.0', 'cookie': self.cookie}
            conn.request('GET', '/users/@me', headers=headers)
            data = json.loads(conn.getresponse().read().decode('utf-8'))
            self.data_ready.emit(data.get("coins", 0))
        except Exception: pass

class InventoryFetcher(QThread):
    data_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    def __init__(self, cookie):
        super().__init__()
        self.cookie = cookie
    def run(self):
        try:
            conn = http.client.HTTPSConnection('api.csrestored.fun')
            headers = {'accept': '*/*', 'origin': 'https://csrestored.fun', 'referer': 'https://csrestored.fun/', 'user-agent': 'Mozilla/5.0', 'cookie': self.cookie}
            conn.request('GET', '/inventory/', headers=headers)
            data = json.loads(conn.getresponse().read().decode('utf-8'))
            self.data_ready.emit(data if isinstance(data, list) else [])
        except Exception as e:
            self.error_occurred.emit(str(e))

class CasesFetcher(QThread):
    data_ready = pyqtSignal(list)
    def __init__(self, cookie):
        super().__init__()
        self.cookie = cookie
    def run(self):
        try:
            conn = http.client.HTTPSConnection('api.csrestored.fun')
            headers = {'accept': '*/*', 'origin': 'https://csrestored.fun', 'referer': 'https://csrestored.fun/', 'user-agent': 'Mozilla/5.0', 'cookie': self.cookie}
            conn.request('GET', '/inventory/cases', headers=headers)
            data = json.loads(conn.getresponse().read().decode('utf-8'))
            self.data_ready.emit(data if isinstance(data, list) else [])
        except Exception: pass

class CaseDetailFetcher(QThread):
    data_ready = pyqtSignal(list)
    def __init__(self, cookie, case_id):
        super().__init__()
        self.cookie = cookie
        self.case_id = case_id
    def run(self):
        try:
            conn = http.client.HTTPSConnection('api.csrestored.fun')
            headers = {'accept': '*/*', 'origin': 'https://csrestored.fun', 'referer': 'https://csrestored.fun/', 'user-agent': 'Mozilla/5.0', 'cookie': self.cookie}
            conn.request('GET', f'/inventory/cases/{self.case_id}', headers=headers)
            data = json.loads(conn.getresponse().read().decode('utf-8'))
            items = data.get("items", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            self.data_ready.emit(items)
        except Exception: pass

class SellerThread(QThread):
    item_sold = pyqtSignal(object)
    sell_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    def __init__(self, weapon_ids, cookie):
        super().__init__()
        self.weapon_ids = weapon_ids
        self.cookie = cookie
    def run(self):
        headers = {'content-type': 'application/json', 'origin': 'https://csrestored.fun', 'user-agent': 'Mozilla/5.0', 'cookie': self.cookie}
        for wid in self.weapon_ids:
            try:
                conn = http.client.HTTPSConnection('api.csrestored.fun')
                conn.request('POST', f'/inventory/sell/{wid}', json.dumps({'weapon_id': wid}), headers)
                conn.getresponse().read()
                conn.close()
                self.item_sold.emit(wid)
            except Exception as e:
                self.error_occurred.emit(str(e))
        self.sell_finished.emit()

class CaseBuyerThread(QThread):
    buy_finished = pyqtSignal()
    def __init__(self, case_id, amount, cookie):
        super().__init__()
        self.case_id = case_id
        self.amount = amount
        self.cookie = cookie
    def run(self):
        try:
            headers = {'content-type': 'application/json', 'origin': 'https://csrestored.fun', 'user-agent': 'Mozilla/5.0', 'cookie': self.cookie}
            conn = http.client.HTTPSConnection('api.csrestored.fun')
            for _ in range(self.amount):
                conn.request('POST', f'/inventory/cases/buy/{self.case_id}', '{}', headers)
                conn.getresponse().read()
            self.buy_finished.emit()
        except Exception:
            self.buy_finished.emit()

class NametagUpdateThread(QThread):
    finished_signal = pyqtSignal(bool, str)
    def __init__(self, weapon_id, nametag, cookie):
        super().__init__()
        self.weapon_id = weapon_id
        self.nametag = nametag
        self.cookie = cookie
    def run(self):
        try:
            headers = {'content-type': 'application/json', 'origin': 'https://csrestored.fun', 'user-agent': 'Mozilla/5.0', 'cookie': self.cookie}
            conn = http.client.HTTPSConnection('api.csrestored.fun')
            payload = json.dumps({"weapon_id": self.weapon_id, "nametag": self.nametag})
            conn.request('POST', '/inventory/nametag', payload, headers)
            res = conn.getresponse()
            if res.status in [200, 201]:
                self.finished_signal.emit(True, self.nametag)
            else:
                self.finished_signal.emit(False, "Failed to update")
        except Exception as e:
            self.finished_signal.emit(False, str(e))


# ================= ДИАЛОГИ =================

class ConfirmDialog(QDialog):
    def __init__(self, count, t, font_family, mod, parent=None):
        super().__init__(parent)
        
        if parent:
            self.resize(parent.size())
            self.move(parent.mapToGlobal(parent.rect().topLeft()))
        else:
            self.setFixedSize(1100, 800)
            
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        wrapper_layout = QVBoxLayout(self)
        wrapper_layout.setAlignment(Qt.AlignCenter)
        
        self.main_frame = QFrame(self)
        self.main_frame.setFixedSize(450, 250)
        
        bg = "#121212"
        border = "#333333"
        text_color = "#ffffff"
        
        if mod == "femboy":
            bg, border, text_color = "#ffe4e1", "#ff69b4", "#333333"
        elif mod == "lgbt":
            bg, border, text_color = "rgba(255, 255, 255, 230)", "#aaaaaa", "#333333"
        elif mod == "evil":
            bg, border, text_color = "#0d0000", "#ff0000", "#ffcccc"
        elif mod == "420":
            bg, border, text_color = "#0f1a0f", "#228b22", "#e6ffe6"
        elif mod in ["snow", "rain", "none"]:
            bg, border, text_color = "#080808", "#333333", "#ffffff"
            
        self.main_frame.setStyleSheet(f"background-color: {bg}; border: 1px solid {border}; border-radius: 12px;")
        
        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(30, 30, 30, 30)
        
        lbl = QLabel(t["confirm_sell"].format(count))
        lbl.setFont(QFont(font_family, 14, QFont.Bold))
        lbl.setStyleSheet(f"color: {text_color}; border: none; background: transparent;")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        lbl.setMinimumHeight(100)
        
        layout.addWidget(lbl)
        
        btn_lay = QHBoxLayout()
        btn_no = QPushButton(t["no"])
        btn_no.setFont(QFont(font_family, 12, QFont.Bold))
        btn_no.setCursor(QCursor(Qt.PointingHandCursor))
        btn_no.setStyleSheet(f"background-color: transparent; color: {text_color}; border: 1px solid {border}; border-radius: 6px; padding: 10px;")
        btn_no.clicked.connect(self.reject)
        
        btn_yes = QPushButton(t["yes"])
        btn_yes.setFont(QFont(font_family, 12, QFont.Bold))
        btn_yes.setCursor(QCursor(Qt.PointingHandCursor))
        btn_yes.setStyleSheet("background-color: #eb4b4b; color: white; border: none; border-radius: 6px; padding: 10px;")
        btn_yes.clicked.connect(self.accept)
        
        btn_lay.addWidget(btn_no)
        btn_lay.addWidget(btn_yes)
        layout.addLayout(btn_lay)
        
        wrapper_layout.addWidget(self.main_frame)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))

    def mousePressEvent(self, event):
        if not self.main_frame.geometry().contains(event.pos()):
            self.reject()

class FilterDialog(QDialog):
    def __init__(self, current_filters, weapon_types, t, font_family, mod, parent=None):
        super().__init__(parent)
        self.t = t
        self.font_family = font_family
        self.mod = mod
        self.setWindowTitle("CS:R Sell Assister")
        
        if parent:
            self.resize(parent.size())
            self.move(parent.mapToGlobal(parent.rect().topLeft()))
        else:
            self.setFixedSize(1100, 800)
            
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.result_filters = {
            "types": list(current_filters.get("types", [])),
            "rarities": list(current_filters.get("rarities", [])),
            "conditions": list(current_filters.get("conditions", [])),
            "min_float": current_filters.get("min_float", 0.0),
            "max_float": current_filters.get("max_float", 1.0),
            "nametag": current_filters.get("nametag", t["f_all"]),
            "stattrak": current_filters.get("stattrak", t["f_all"])
        }
        
        wrapper_layout = QVBoxLayout(self)
        wrapper_layout.setAlignment(Qt.AlignCenter)
        
        self.main_frame = QFrame(self)
        self.main_frame.setFixedSize(500, 550)
        
        if mod == "femboy":
            bg, border, text_color, input_bg = "#ffe4e1", "#ff69b4", "#333333", "#ffb6c1"
        elif mod == "lgbt":
            bg, border, text_color, input_bg = "#f0f0f0", "#aaaaaa", "#333333", "#ffffff"
        elif mod == "evil":
            bg, border, text_color, input_bg = "#1a0000", "#ff0000", "#ffcccc", "#2a0000"
        elif mod == "420":
            bg, border, text_color, input_bg = "#0f1a0f", "#228b22", "#e6ffe6", "#172b17"
        elif mod == "rain":
            bg, border, text_color, input_bg = "#121212", "#333333", "#ffffff", "#1a1a1a"
        else:
            bg, border, text_color, input_bg = "#121212", "#333333", "#ffffff", "#1a1a1a"
            
        self.main_frame.setStyleSheet(f"background-color: {bg}; border: 1px solid {border}; border-radius: 12px;")
        
        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        title = QLabel(t["filters"])
        title.setFont(QFont(font_family, 16, QFont.Bold))
        title.setStyleSheet(f"color: {text_color}; border: none; background: transparent;")
        layout.addWidget(title, alignment=Qt.AlignCenter)
        
        form_layout = QGridLayout()
        form_layout.setSpacing(15)
        label_style = f"color: {text_color}; border: none; background: transparent;"
        
        combo_style = f"""
            QComboBox {{ background-color: {input_bg}; color: {text_color}; border: 1px solid {border}; border-radius: 6px; padding: 5px 10px; }}
            QComboBox::drop-down {{ border: none; width: 0px; }} QComboBox::down-arrow {{ image: none; }}
            QComboBox QAbstractItemView {{ background-color: {input_bg}; color: {text_color}; selection-background-color: {border}; border: 1px solid {border}; border-radius: 6px; outline: none; }}
            QLineEdit {{ background: transparent; border: none; color: {text_color}; padding: 0; }}
        """
        spin_style = f"QDoubleSpinBox {{ background-color: {input_bg}; color: {text_color}; border: 1px solid {border}; border-radius: 6px; padding: 5px 10px; }}"
        
        form_layout.addWidget(QLabel(t["f_type"], styleSheet=label_style, font=QFont(font_family, 11)), 0, 0)
        self.cb_type = CheckableComboBox(t["f_all"])
        self.cb_type.setStyleSheet(combo_style)
        self.cb_type.setFont(QFont(font_family, 10))
        for w in sorted(weapon_types):
            self.cb_type.add_item(w, text_color, w)
        self.cb_type.set_checked_data(self.result_filters["types"])
        form_layout.addWidget(self.cb_type, 0, 1)
        
        form_layout.addWidget(QLabel(t["f_rarity"], styleSheet=label_style, font=QFont(font_family, 11)), 1, 0)
        self.cb_rarity = CheckableComboBox(t["f_all"])
        self.cb_rarity.setStyleSheet(combo_style)
        self.cb_rarity.setFont(QFont(font_family, 10))
        for key in ["6", "5", "4", "3", "2", "1", "0"]:
            self.cb_rarity.add_item(t[f"rarity_{key}"], text_color, key)
        self.cb_rarity.set_checked_data(self.result_filters["rarities"])
        form_layout.addWidget(self.cb_rarity, 1, 1)

        form_layout.addWidget(QLabel(t["f_cond"], styleSheet=label_style, font=QFont(font_family, 11)), 2, 0)
        self.cb_cond = CheckableComboBox(t["f_all"])
        self.cb_cond.setStyleSheet(combo_style)
        self.cb_cond.setFont(QFont(font_family, 10))
        for key in ["fn", "mw", "ft", "ww", "bs"]:
            self.cb_cond.add_item(t[f"cond_{key}"], text_color, key)
        self.cb_cond.set_checked_data(self.result_filters["conditions"])
        form_layout.addWidget(self.cb_cond, 2, 1)

        form_layout.addWidget(QLabel(t["f_float"], styleSheet=label_style, font=QFont(font_family, 11)), 3, 0)
        float_lay = QHBoxLayout()
        self.spin_min = QDoubleSpinBox()
        self.spin_min.setRange(0.0, 1.0)
        self.spin_min.setSingleStep(0.01)
        self.spin_min.setDecimals(5)
        self.spin_min.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.spin_max = QDoubleSpinBox()
        self.spin_max.setRange(0.0, 1.0)
        self.spin_max.setSingleStep(0.01)
        self.spin_max.setDecimals(5)
        self.spin_max.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.spin_min.setStyleSheet(spin_style)
        self.spin_max.setStyleSheet(spin_style)
        self.spin_min.setFont(QFont(font_family, 10))
        self.spin_max.setFont(QFont(font_family, 10))
        self.spin_min.setValue(self.result_filters["min_float"])
        self.spin_max.setValue(self.result_filters["max_float"])
        float_lay.addWidget(self.spin_min)
        float_lay.addWidget(QLabel("-", styleSheet=label_style))
        float_lay.addWidget(self.spin_max)
        form_layout.addLayout(float_lay, 3, 1)

        form_layout.addWidget(QLabel(t["f_nametag"], styleSheet=label_style, font=QFont(font_family, 11)), 4, 0)
        self.cb_nt = QComboBox()
        self.cb_nt.setStyleSheet(combo_style)
        self.cb_nt.setFont(QFont(font_family, 10))
        self.cb_nt.view().setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cb_nt.addItems([t["f_all"], t["f_yes"], t["f_no"]])
        self.cb_nt.setCurrentText(self.result_filters["nametag"])
        form_layout.addWidget(self.cb_nt, 4, 1)

        form_layout.addWidget(QLabel(t["f_stattrak"], styleSheet=label_style, font=QFont(font_family, 11)), 5, 0)
        self.cb_st = QComboBox()
        self.cb_st.setStyleSheet(combo_style)
        self.cb_st.setFont(QFont(font_family, 10))
        self.cb_st.view().setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cb_st.addItems([t["f_all"], t["f_yes"], t["f_no"]])
        self.cb_st.setCurrentText(self.result_filters["stattrak"])
        form_layout.addWidget(self.cb_st, 5, 1)

        layout.addLayout(form_layout)
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_font = QFont(font_family, 11, QFont.Bold)
        reset_bg = "#ffb6c1" if mod == "femboy" else ("#d9d9d9" if mod == "lgbt" else ("#4d0000" if mod == "evil" else ("#172b17" if mod == "420" else "#2a2a2a")))
        apply_bg = "#ff69b4" if mod == "femboy" else ("#4d0000" if mod == "evil" else ("#2e8b57" if mod == "420" else "#5c8a47"))
        
        self.reset_btn = QPushButton(t["f_reset"])
        self.reset_btn.setFont(btn_font)
        self.reset_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.reset_btn.setStyleSheet(f"background-color: {reset_bg}; color: {text_color}; border-radius: 6px; padding: 10px; border: none;")
        self.reset_btn.clicked.connect(self.reset_filters)
        
        self.apply_btn = QPushButton(t["f_apply"])
        self.apply_btn.setFont(btn_font)
        self.apply_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.apply_btn.setStyleSheet(f"background-color: {apply_bg}; color: white; border-radius: 6px; padding: 10px; border: none;")
        self.apply_btn.clicked.connect(self.apply_filters)
        
        btn_layout.addWidget(self.reset_btn)
        btn_layout.addWidget(self.apply_btn)
        layout.addLayout(btn_layout)
        
        wrapper_layout.addWidget(self.main_frame)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))

    def mousePressEvent(self, event):
        if not self.main_frame.geometry().contains(event.pos()):
            self.reject()

    def reset_filters(self):
        self.cb_type.set_checked_data([])
        self.cb_rarity.set_checked_data([])
        self.cb_cond.set_checked_data([])
        self.spin_min.setValue(0.0)
        self.spin_max.setValue(1.0)
        self.cb_nt.setCurrentIndex(0)
        self.cb_st.setCurrentIndex(0)

    def apply_filters(self):
        self.result_filters = {
            "types": self.cb_type.get_checked_data(),
            "rarities": self.cb_rarity.get_checked_data(),
            "conditions": self.cb_cond.get_checked_data(),
            "min_float": self.spin_min.value(),
            "max_float": self.spin_max.value(),
            "nametag": self.cb_nt.currentText(),
            "stattrak": self.cb_st.currentText()
        }
        self.accept()

class LanguageDialog(QDialog):
    def __init__(self, font_family="Arial", parent=None):
        super().__init__(parent)
        self.setWindowTitle("CS:R Sell Assister")
        self.selected_lang = None
        if parent:
            self.resize(parent.size())
            self.move(parent.mapToGlobal(parent.rect().topLeft()))
        else:
            self.setFixedSize(1100, 800)
            
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        wrapper_layout = QVBoxLayout(self)
        wrapper_layout.setAlignment(Qt.AlignCenter)
        
        self.main_frame = QFrame(self)
        self.main_frame.setFixedSize(300, 120)
        self.main_frame.setStyleSheet("background-color: #121212; border: 1px solid #333333; border-radius: 12px;")
        layout = QHBoxLayout(self.main_frame)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        btn_font = QFont(font_family, 18, QFont.Bold)
        btn_font.setStyleStrategy(QFont.PreferAntialias)
        
        self.ru_btn = QPushButton("RU")
        self.ru_btn.setFont(btn_font)
        self.ru_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.ru_btn.setStyleSheet("QPushButton { background-color: #2a2a2a; color: white; border-radius: 8px; border: none; height: 60px; } QPushButton:hover { background-color: #5c8a47; }")
        self.ru_btn.clicked.connect(lambda: self.select_lang("ru"))
        
        self.en_btn = QPushButton("EN")
        self.en_btn.setFont(btn_font)
        self.en_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.en_btn.setStyleSheet("QPushButton { background-color: #2a2a2a; color: white; border-radius: 8px; border: none; height: 60px; } QPushButton:hover { background-color: #5c8a47; }")
        self.en_btn.clicked.connect(lambda: self.select_lang("en"))
        
        layout.addWidget(self.ru_btn)
        layout.addWidget(self.en_btn)
        
        wrapper_layout.addWidget(self.main_frame)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))

    def select_lang(self, lang):
        self.selected_lang = lang
        self.accept()

class MainHelpDialog(QDialog):
    def __init__(self, t, font_family="Arial", parent=None):
        super().__init__(parent)
        self.setWindowTitle("CS:R Sell Assister")
        if parent:
            self.resize(parent.size())
            self.move(parent.mapToGlobal(parent.rect().topLeft()))
        else:
            self.setFixedSize(1100, 800)
            
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        wrapper_layout = QVBoxLayout(self)
        wrapper_layout.setAlignment(Qt.AlignCenter)
        
        self.main_frame = QFrame(self)
        self.main_frame.setFixedSize(450, 320)
        self.main_frame.setStyleSheet("background-color: #161616; border: 1px solid #3a3a3a; border-radius: 12px;")
        
        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        title_font = QFont(font_family, 16, QFont.Bold)
        title_font.setStyleStrategy(QFont.PreferAntialias)
        title = QLabel(t["welcome_csr"])
        title.setFont(title_font)
        title.setStyleSheet("color: #ffffff; border: none; background: transparent;")
        layout.addWidget(title, alignment=Qt.AlignCenter)
        
        desc_font = QFont(font_family, 11)
        desc_font.setStyleStrategy(QFont.PreferAntialias)
        desc = QLabel(t["main_inst"])
        desc.setFont(desc_font)
        desc.setStyleSheet("color: #aaaaaa; border: none; background: transparent; line-height: 1.5;")
        layout.addWidget(desc)
        layout.addStretch()
        
        btn_font = QFont(font_family, 11, QFont.Bold)
        btn_font.setStyleStrategy(QFont.PreferAntialias)
        self.close_btn = QPushButton(t["got_it"])
        self.close_btn.setFont(btn_font)
        self.close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.close_btn.setStyleSheet("QPushButton { background-color: #5c8a47; color: white; border-radius: 6px; padding: 10px; border: none; } QPushButton:hover { background-color: #6da354; }")
        self.close_btn.clicked.connect(self.accept)
        layout.addWidget(self.close_btn)
        
        wrapper_layout.addWidget(self.main_frame)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))

    def mousePressEvent(self, event):
        if not self.main_frame.geometry().contains(event.pos()):
            self.reject()

class CookieHelpDialog(QDialog):
    def __init__(self, t, font_family="Arial", parent=None):
        super().__init__(parent)
        self.setWindowTitle("CS:R Sell Assister")
        if parent:
            self.resize(parent.size())
            self.move(parent.mapToGlobal(parent.rect().topLeft()))
        else:
            self.setFixedSize(1100, 800)
            
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        wrapper_layout = QVBoxLayout(self)
        wrapper_layout.setAlignment(Qt.AlignCenter)
        
        self.main_frame = QFrame(self)
        self.main_frame.setFixedSize(420, 340)
        self.main_frame.setStyleSheet("background-color: #161616; border: 1px solid #3a3a3a; border-radius: 12px;")
        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        title_font = QFont(font_family, 14, QFont.Bold)
        title_font.setStyleStrategy(QFont.PreferAntialias)
        title = QLabel(t["how_to_cookie"])
        title.setFont(title_font)
        title.setStyleSheet("color: #ffffff; border: none; background: transparent;")
        layout.addWidget(title, alignment=Qt.AlignCenter)
        
        desc_font = QFont(font_family, 11)
        desc_font.setStyleStrategy(QFont.PreferAntialias)
        desc = QLabel(t["cookie_inst"])
        desc.setFont(desc_font)
        desc.setWordWrap(True)
        desc.setTextFormat(Qt.RichText)
        desc.setOpenExternalLinks(True)
        desc.setStyleSheet("color: #aaaaaa; border: none; background: transparent; line-height: 1.5;")
        layout.addWidget(desc)
        layout.addStretch()
        
        btn_font = QFont(font_family, 11, QFont.Bold)
        btn_font.setStyleStrategy(QFont.PreferAntialias)
        self.close_btn = QPushButton(t["got_it"])
        self.close_btn.setFont(btn_font)
        self.close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.close_btn.setStyleSheet("QPushButton { background-color: #2a2a2a; color: white; border-radius: 6px; padding: 8px; border: none; } QPushButton:hover { background-color: #3a3a3a; }")
        self.close_btn.clicked.connect(self.accept)
        layout.addWidget(self.close_btn)
        
        wrapper_layout.addWidget(self.main_frame)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))

    def mousePressEvent(self, event):
        if not self.main_frame.geometry().contains(event.pos()):
            self.reject()

class CookieDialog(QDialog):
    def __init__(self, t, font_family="Arial", parent=None):
        super().__init__(parent)
        self.setWindowTitle("CS:R Sell Assister")
        self.font_family = font_family
        self.t = t
        if parent:
            self.resize(parent.size())
            self.move(parent.mapToGlobal(parent.rect().topLeft()))
        else:
            self.setFixedSize(1100, 800)
            
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        wrapper_layout = QVBoxLayout(self)
        wrapper_layout.setAlignment(Qt.AlignCenter)
        
        self.main_frame = QFrame(self)
        self.main_frame.setFixedSize(450, 230)
        self.main_frame.setStyleSheet("background-color: #121212; border: 1px solid #333333; border-radius: 12px;")
        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        title_font = QFont(self.font_family, 16, QFont.Bold)
        title_font.setStyleStrategy(QFont.PreferAntialias)
        title = QLabel(t["auth_req"])
        title.setFont(title_font)
        title.setStyleSheet("color: #ffffff; border: none; background: transparent;")
        layout.addWidget(title, alignment=Qt.AlignCenter)
        
        lbl_layout = QHBoxLayout()
        lbl_layout.setSpacing(2)
        dummy = QLabel()
        dummy.setFixedSize(12, 12)
        dummy.setStyleSheet("background: transparent; border: none;")
        
        desc_font = QFont(self.font_family, 11)
        desc_font.setStyleStrategy(QFont.PreferAntialias)
        desc = QLabel(t["enter_cookie"])
        desc.setFont(desc_font)
        desc.setStyleSheet("color: #aaaaaa; border: none; background: transparent; padding-bottom: 2px;")
        desc.setAlignment(Qt.AlignCenter)
        
        help_font = QFont(self.font_family, 7, QFont.Bold)
        help_font.setStyleStrategy(QFont.PreferAntialias)
        self.help_btn = QPushButton("?")
        self.help_btn.setFixedSize(12, 12)
        self.help_btn.setFont(help_font)
        self.help_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.help_btn.setStyleSheet("QPushButton { background-color: #2a2a2a; color: #888888; border-radius: 6px; border: none; padding: 0px; margin: 0px; text-align: center; } QPushButton:hover { background-color: #444444; color: #ffffff; }")
        self.help_btn.clicked.connect(lambda: CookieHelpDialog(self.t, self.font_family, self).exec_())
        
        lbl_layout.addStretch()
        lbl_layout.addWidget(dummy, alignment=Qt.AlignTop)
        lbl_layout.addWidget(desc, alignment=Qt.AlignCenter)
        lbl_layout.addWidget(self.help_btn, alignment=Qt.AlignTop)
        lbl_layout.addStretch()
        layout.addLayout(lbl_layout)
        
        input_font = QFont(self.font_family, 11)
        input_font.setStyleStrategy(QFont.PreferAntialias)
        self.input_field = QLineEdit()
        self.input_field.setFont(input_font)
        self.input_field.setPlaceholderText(t["paste_cookie"])
        self.input_field.setEchoMode(QLineEdit.Password)
        self.input_field.setStyleSheet("QLineEdit { background-color: #1a1a1a; color: #ffffff; border: 1px solid #444444; border-radius: 6px; padding: 0 10px; min-height: 40px; } QLineEdit:focus { border: 1px solid #5c8a47; }")
        layout.addWidget(self.input_field)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        btn_font = QFont(self.font_family, 11, QFont.Bold)
        btn_font.setStyleStrategy(QFont.PreferAntialias)
        
        self.exit_btn = QPushButton(t["exit"])
        self.exit_btn.setFont(btn_font)
        self.exit_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.exit_btn.setStyleSheet("QPushButton { background-color: #2a2a2a; color: white; border-radius: 6px; padding: 10px; border: none; } QPushButton:hover { background-color: #3a3a3a; }")
        self.exit_btn.clicked.connect(self.reject)
        
        self.save_btn = QPushButton(t["login"])
        self.save_btn.setFont(btn_font)
        self.save_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.save_btn.setStyleSheet("QPushButton { background-color: #5c8a47; color: white; border-radius: 6px; padding: 10px; border: none; } QPushButton:hover { background-color: #6da354; }")
        self.save_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.exit_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)
        
        wrapper_layout.addWidget(self.main_frame)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))

class ItemDetailDialog(QDialog):
    sell_requested = pyqtSignal(int)
    nametag_requested = pyqtSignal(int, str)

    def __init__(self, item_data, network_manager, t, font_family, mod, is_selling=False, parent=None):
        super().__init__(parent)
        self.t = t
        self.font_family = font_family
        self.mod = mod
        self.item_data = item_data
        self.network_manager = network_manager
        self.is_selling = is_selling
        
        if parent:
            self.resize(parent.size())
            self.move(parent.mapToGlobal(parent.rect().topLeft()))
        else:
            self.setFixedSize(1100, 800)
            
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.weapon_id = item_data.get("weapon_id")
        self.item_id = item_data.get("item_id") or item_data.get("id")
        self.name = item_data.get("name", "Unknown Item")
        self.float_val = item_data.get("float", 0.0)
        if self.float_val is None:
            self.float_val = 0.0
            
        raw_pat = item_data.get("seed", item_data.get("paint_seed", item_data.get("pattern", 0)))
        try:
            self.pattern = int(float(raw_pat))
        except:
            self.pattern = 0
            
        self.is_stattrak = item_data.get("stattrak", False)
        self.nametag = item_data.get("nametag", "")
        self.rarity = str(item_data.get("rarity", "6"))
        self.rarity_color = RARITY_COLORS.get(self.rarity, DEFAULT_RARITY_COLOR)
        
        self.weapon_type = get_weapon_category(self.name)
        
        self.setup_ui()

    def get_wear_string(self, f):
        if f <= 0.07: return self.t["cond_fn"]
        if f <= 0.15: return self.t["cond_mw"]
        if f <= 0.38: return self.t["cond_ft"]
        if f <= 0.45: return self.t["cond_ww"]
        return self.t["cond_bs"]

    def setup_ui(self):
        wrapper_layout = QVBoxLayout(self)
        wrapper_layout.setAlignment(Qt.AlignCenter)
        
        self.main_frame = QFrame(self)
        self.main_frame.setFixedSize(700, 420)
        
        if self.mod == "femboy":
            bg, border, text_color, input_bg = "#ffe4e1", "#ff69b4", "#333333", "#ffb6c1"
        elif self.mod == "lgbt":
            bg, border, text_color, input_bg = "rgba(255, 255, 255, 230)", "#aaaaaa", "#333333", "#ffffff"
        elif self.mod == "evil":
            bg, border, text_color, input_bg = "#0d0000", "#ff0000", "#ffcccc", "#2a0000"
        elif self.mod == "420":
            bg, border, text_color, input_bg = "#0f1a0f", "#228b22", "#e6ffe6", "#172b17"
        elif self.mod in ["snow", "rain", "none"]:
            bg, border, text_color, input_bg = "#080808", "#333333", "#ffffff", "#1a1a1a"
            
        self.main_frame.setStyleSheet(f"background-color: {bg}; border: 1px solid {border}; border-radius: 12px;")
        
        main_layout = QVBoxLayout(self.main_frame)
        main_layout.setContentsMargins(25, 25, 25, 25)
        
        top_bar = QHBoxLayout()
        title_lbl = QLabel(self.t["weapon_details"])
        title_lbl.setFont(QFont(self.font_family, 14, QFont.Bold))
        title_lbl.setStyleSheet(f"color: {text_color}; border: none; background: transparent;")
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setFont(QFont(self.font_family, 14, QFont.Bold))
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet(f"QPushButton {{ background: transparent; color: {text_color}; border: none; }} QPushButton:hover {{ color: #eb4b4b; }}")
        close_btn.clicked.connect(self.reject)
        
        top_bar.addWidget(title_lbl)
        top_bar.addStretch()
        top_bar.addWidget(close_btn)
        main_layout.addLayout(top_bar)
        
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        left_frame = QFrame()
        left_frame.setFixedSize(280, 280)
        r, g, b = hex_to_rgb(self.rarity_color)
        bot_r, bot_g, bot_b = int(r * 0.12), int(g * 0.12), int(b * 0.12)
        top_grad = 18
        card_bg = f"qlineargradient(x1:0, y1:1, x2:0, y2:0, stop:0 rgb({bot_r}, {bot_g}, {bot_b}), stop:1 rgb({top_grad}, {top_grad}, {top_grad}))"
        
        if self.mod not in ["none", "snow", "rain"]:
            card_bg = input_bg
            
        left_frame.setStyleSheet(f"background: {card_bg}; border: 1px solid {border}; border-radius: 8px;")
        
        top_line = QFrame(left_frame)
        top_line.setFixedSize(56, 3)
        top_line.setStyleSheet(f"background-color: {self.rarity_color}; border: none;")
        top_line.move((280 - 56) // 2, 0)
        
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(10, 10, 10, 10)
        
        self.image_lbl = AspectRatioPixmapLabel()
        self.image_lbl.setStyleSheet("background: transparent; border: none;")
        
        name_bottom = QLabel(self.name)
        name_bottom.setFont(QFont(self.font_family, 9))
        name_bottom.setStyleSheet("color: #888888; background: transparent; border: none;")
        name_bottom.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        left_layout.addWidget(self.image_lbl, stretch=1)
        left_layout.addWidget(name_bottom)
        
        if self.item_id:
            url = "https://csrestored.fun/_next/image?url=%2Fspecial.png&w=3840&q=75" if self.item_id == "special_item" else f"https://cdn.csrestored.fun/skins/{self.item_id}.png"
            req = QNetworkRequest(QUrl(url))
            req.setRawHeader(b"User-Agent", b"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            self.reply = self.network_manager.get(req)
            self.reply.finished.connect(self.on_image_downloaded)
            
        content_layout.addWidget(left_frame)
        
        right_layout = QVBoxLayout()
        right_layout.setSpacing(12)
        
        name_title = QLabel(self.name)
        name_title.setFont(QFont(self.font_family, 16, QFont.Bold))
        name_title.setStyleSheet(f"color: {text_color}; border: none; background: transparent;")
        name_title.setWordWrap(True)
        right_layout.addWidget(name_title)
        
        badges_lay = QHBoxLayout()
        r_badge = QLabel(self.t[f"rarity_{self.rarity}"].split(" ")[0])
        r_badge.setFont(QFont(self.font_family, 9, QFont.Bold))
        
        dark_bg = f"rgba({r}, {g}, {b}, 30)"
        r_badge.setStyleSheet(f"background-color: {dark_bg}; color: {self.rarity_color}; border: 1px solid {self.rarity_color}; border-radius: 4px; padding: 4px 8px;")
        
        t_badge = QLabel(self.weapon_type)
        t_badge.setFont(QFont(self.font_family, 9))
        t_badge.setStyleSheet(f"color: {text_color}; background: transparent; border: 1px solid {border}; border-radius: 4px; padding: 4px 8px;")
        
        badges_lay.addWidget(r_badge)
        badges_lay.addWidget(t_badge)
        badges_lay.addStretch()
        right_layout.addLayout(badges_lay)
        
        stats_grid = QGridLayout()
        stats_grid.setSpacing(10)
        lbl_style = "color: #888888; border: none; background: transparent; font-size: 10px;"
        val_style = f"color: {text_color}; border: none; background: transparent; font-size: 12px; font-weight: bold;"
        
        stats_grid.addWidget(QLabel(self.t["wear"], styleSheet=lbl_style), 0, 0)
        stats_grid.addWidget(QLabel(self.t["f_float"].replace(" (От - До)", "").replace(" Range", ""), styleSheet=lbl_style), 0, 1)
        stats_grid.addWidget(QLabel(self.t["pattern"], styleSheet=lbl_style), 0, 2)
        stats_grid.addWidget(QLabel(self.t["f_stattrak"], styleSheet=lbl_style), 0, 3)
        
        stats_grid.addWidget(QLabel(self.get_wear_string(self.float_val), styleSheet=val_style), 1, 0)
        stats_grid.addWidget(QLabel(f"{self.float_val:.6f}", styleSheet=val_style), 1, 1)
        stats_grid.addWidget(QLabel(str(self.pattern), styleSheet=val_style), 1, 2)
        stats_grid.addWidget(QLabel(self.t["f_yes"] if self.is_stattrak else self.t["f_no"], styleSheet=val_style), 1, 3)
        
        right_layout.addLayout(stats_grid)
        
        right_layout.addWidget(QLabel(self.t["item_float"], styleSheet=lbl_style))
        right_layout.addWidget(FloatBarWidget(self.float_val))
        right_layout.addWidget(QLabel(f"{self.float_val:.6f} ({self.float_val*100:.3f}%) - {self.get_wear_string(self.float_val).split(' - ')[-1]}", styleSheet=lbl_style))
        
        self.nt_container = QFrame()
        self.nt_container.setFixedHeight(38)
        self.nt_container.setStyleSheet(f"QFrame {{ background-color: {input_bg}; border: 1px solid {border}; border-radius: 6px; }}")
        nt_lay = QHBoxLayout(self.nt_container)
        nt_lay.setContentsMargins(10, 0, 10, 0)
        nt_lay.setSpacing(5)
        
        self.nt_input = QLineEdit()
        self.nt_input.setText(self.nametag)
        self.nt_input.setMaxLength(20) # Максимум 20 символов
        self.nt_input.setPlaceholderText("Nametag...")
        self.nt_input.setFont(QFont(self.font_family, 11))
        self.nt_input.setStyleSheet(f"QLineEdit {{ background: transparent; color: {text_color}; border: none; }}")
        self.nt_input.textChanged.connect(self.on_nt_changed)
        
        self.nt_cost_widget = QWidget()
        self.nt_cost_widget.setStyleSheet("background: transparent; border: none;")
        cost_lay = QHBoxLayout(self.nt_cost_widget)
        cost_lay.setContentsMargins(0,0,0,0)
        cost_lay.setSpacing(4)
        
        icon_lbl = QLabel()
        coin_path = os.path.join(USER_DATA_DIR, "coins.png") if os.path.exists(os.path.join(USER_DATA_DIR, "coins.png")) else os.path.join(ASSETS_DIR, "coins.png")
        if os.path.exists(coin_path):
            icon_lbl.setPixmap(QIcon(coin_path).pixmap(14, 14))
            
        coin_color = "#d97706" if self.mod in ["femboy", "lgbt"] else "#fef08a"
        cost_lbl = QLabel("100")
        cost_lbl.setFont(QFont(self.font_family, 10, QFont.Bold))
        cost_lbl.setStyleSheet(f"color: {coin_color}; border: none; background: transparent;")
        
        cost_lay.addWidget(icon_lbl)
        cost_lay.addWidget(cost_lbl)
        
        self.nt_cost_eff = QGraphicsOpacityEffect()
        self.nt_cost_widget.setGraphicsEffect(self.nt_cost_eff)
        self.nt_cost_eff.setOpacity(0.0)
        self.nt_anim = QPropertyAnimation(self.nt_cost_eff, b"opacity")
        self.nt_anim.setDuration(200)
        
        nt_lay.addWidget(self.nt_input, stretch=1)
        nt_lay.addWidget(self.nt_cost_widget)
        right_layout.addWidget(self.nt_container)
        
        btn_lay = QHBoxLayout()
        btn_font = QFont(self.font_family, 11, QFont.Bold)
        
        self.nt_btn = QPushButton(self.t["update_nametag"])
        self.nt_btn.setFont(btn_font)
        self.nt_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.nt_btn.setStyleSheet(f"QPushButton {{ background-color: {input_bg}; color: {text_color}; border: 1px solid {border}; border-radius: 6px; height: 40px; }} QPushButton:hover {{ background-color: {border}; }}")
        self.nt_btn.clicked.connect(self.update_nametag)
        
        self.sell_btn = QPushButton(self.t["quick_sell"])
        self.sell_btn.setFont(btn_font)
        
        if self.is_selling:
            self.sell_btn.setEnabled(False)
            self.sell_btn.setText(self.t["selling"])
            self.sell_btn.setStyleSheet(f"QPushButton {{ background-color: #555555; color: #aaaaaa; border: none; border-radius: 6px; height: 40px; }}")
        else:
            self.sell_btn.setCursor(QCursor(Qt.PointingHandCursor))
            self.sell_btn.setStyleSheet("QPushButton { background-color: #eb4b4b; color: white; border: none; border-radius: 6px; height: 40px; } QPushButton:hover { background-color: #c93e3e; }")
            self.sell_btn.clicked.connect(self.quick_sell)
        
        btn_lay.addWidget(self.nt_btn)
        btn_lay.addWidget(self.sell_btn)
        right_layout.addLayout(btn_lay)
        
        right_layout.addStretch()
        content_layout.addLayout(right_layout, stretch=1)
        main_layout.addLayout(content_layout)
        
        wrapper_layout.addWidget(self.main_frame)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))

    def mousePressEvent(self, event):
        if not self.main_frame.geometry().contains(event.pos()):
            self.reject()

    def on_nt_changed(self, text):
        new_text = text.strip()
        old_text = self.nametag or ""
        target = 1.0 if new_text != old_text else 0.0
        
        current_target = getattr(self, '_nt_target', -1.0)
        if current_target != target:
            self._nt_target = target
            self.nt_anim.stop()
            self.nt_anim.setStartValue(self.nt_cost_eff.opacity())
            self.nt_anim.setEndValue(target)
            self.nt_anim.start()

    def on_image_downloaded(self):
        reply = self.sender()
        if reply and reply.error() == QNetworkReply.NoError: 
            data = reply.readAll()
            px = QPixmap()
            loaded = False
            if HAS_PILLOW:
                try:
                    temp_name = "temp_special" if self.item_id == "special_item" else f"temp_skin_{self.item_id}"
                    webp_path = os.path.join(USER_DATA_DIR, f"{temp_name}.webp")
                    png_path = os.path.join(USER_DATA_DIR, f"{temp_name}.png")
                    with open(webp_path, "wb") as f:
                        f.write(data.data())
                    img = Image.open(webp_path)
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    img.save(png_path, "PNG")
                    px.load(png_path)
                    loaded = True
                except Exception:
                    pass
            if not loaded:
                px.loadFromData(data)
            self.image_lbl.setPixmap(px)
        if reply: reply.deleteLater()

    def update_nametag(self):
        new_tag = self.nt_input.text().strip()
        self.nt_btn.setText(self.t["updating"])
        self.nt_btn.setEnabled(False)
        self.nametag_requested.emit(self.weapon_id, new_tag)

    def quick_sell(self):
        if self.is_selling: return
        confirm = ConfirmDialog(1, self.t, self.font_family, self.mod, self)
        if confirm.exec_() == QDialog.Accepted:
            self.accept()
            self.sell_requested.emit(self.weapon_id)

# ================= КАРТОЧКИ =================
class ItemCard(QFrame):
    selection_toggled = pyqtSignal(object, bool, bool) 
    detail_requested = pyqtSignal(object) 

    def __init__(self, item_data, network_manager, is_case_content=False, parent=None):
        super().__init__(parent)
        self.network_manager = network_manager
        self.selectable = not is_case_content
        if self.selectable:
            self.setCursor(QCursor(Qt.PointingHandCursor))
            
        self.item_data = item_data
        self.item_id = item_data.get("item_id") or item_data.get("id")
        self.weapon_id = item_data.get("weapon_id")
        self.name = item_data.get("name", "Unknown Item")
        self.float_val = item_data.get("float", 0.0)
        self.is_stattrak = item_data.get("stattrak", False)
        self.stattrak_count = item_data.get("stattrak_count", 0)
        self.nametag = item_data.get("nametag")
        self.rarity = str(item_data.get("rarity", "6")) 
        self.rarity_color = RARITY_COLORS.get(self.rarity, DEFAULT_RARITY_COLOR)
        
        self.is_selected = False
        self._hover_val = 0
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(150)
        self._anim.valueChanged.connect(self._on_hover_animate)

        self.init_ui()
        self.apply_stylesheet()
        
        if is_case_content:
            self.float_label.hide()
            self.st_label.hide()
            
        self.load_image()

    def init_ui(self):
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(2)
        
        self.top_line = QFrame(self)
        self.top_line.setStyleSheet(f"background-color: {self.rarity_color}; border: none;")
        
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        self.st_label = ElidedLabel(f"ST™ {self.stattrak_count}" if self.is_stattrak else "", weight=QFont.Bold)
        self.st_label.setStyleSheet("color: #cf6a32; background: transparent;")
        
        self.float_label = ElidedLabel(f"{self.float_val:.5f}" if self.float_val is not None else "0.00000", weight=QFont.Bold)
        self.float_label.setStyleSheet("color: #cccccc; background: transparent;")
        
        top_layout.addWidget(self.st_label, alignment=Qt.AlignLeft | Qt.AlignTop)
        top_layout.addWidget(self.float_label, alignment=Qt.AlignRight | Qt.AlignTop)
        layout.addLayout(top_layout)
        
        self.image_label = AspectRatioPixmapLabel()
        self.image_label.setStyleSheet("background: transparent;")
        layout.addWidget(self.image_label, stretch=1)
        
        bottom_layout = QVBoxLayout()
        bottom_layout.setSpacing(0) 
        
        weapon_name, skin_name = self.name.split(" | ", 1) if " | " in self.name else (self.name, "")

        self.tag_label = ElidedLabel(f'"{self.nametag}"' if self.nametag else "", weight=QFont.StyleItalic)
        self.tag_label.setStyleSheet("color: #999999; background: transparent;")
        if not self.nametag:
            self.tag_label.hide()
        bottom_layout.addWidget(self.tag_label)

        self.weapon_label = ElidedLabel(weapon_name, weight=QFont.Bold)
        self.weapon_label.setStyleSheet("color: #ffffff; background: transparent;")
        bottom_layout.addWidget(self.weapon_label)
        
        if skin_name:
            self.skin_label = ElidedLabel(skin_name, weight=QFont.Black)
            self.skin_label.setStyleSheet(f"color: {self.rarity_color}; background: transparent;")
            bottom_layout.addWidget(self.skin_label)
            
        layout.addLayout(bottom_layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = self.width()
        self.st_label.set_font_size(max(7, int(w * 0.055)))
        self.float_label.set_font_size(max(7, int(w * 0.055)))
        if hasattr(self, 'tag_label'):
            self.tag_label.set_font_size(max(7, int(w * 0.045)))
        self.weapon_label.set_font_size(max(8, int(w * 0.055)))
        if hasattr(self, 'skin_label'):
            self.skin_label.set_font_size(max(10, int(w * 0.08)))
        self.top_line.setFixedSize(int(w * 0.2), max(2, int(w * 0.01)))
        self.top_line.move((w - self.top_line.width()) // 2, 0)

    def load_image(self):
        if not self.item_id: return
        url = "https://csrestored.fun/_next/image?url=%2Fspecial.png&w=3840&q=75" if self.item_id == "special_item" else f"https://cdn.csrestored.fun/skins/{self.item_id}.png"
        req = QNetworkRequest(QUrl(url))
        req.setRawHeader(b"User-Agent", b"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        self.reply = self.network_manager.get(req)
        self.reply.finished.connect(self.on_image_downloaded)
        
    def on_image_downloaded(self):
        reply = self.sender()
        if reply and reply.error() == QNetworkReply.NoError: 
            data = reply.readAll()
            px = QPixmap()
            loaded = False
            if HAS_PILLOW and self.item_id == "special_item":
                try:
                    temp_name = "temp_special"
                    webp_path = os.path.join(USER_DATA_DIR, f"{temp_name}.webp")
                    png_path = os.path.join(USER_DATA_DIR, f"{temp_name}.png")
                    with open(webp_path, "wb") as f:
                        f.write(data.data())
                    img = Image.open(webp_path)
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    img.save(png_path, "PNG")
                    px.load(png_path)
                    loaded = True
                except Exception:
                    pass
            if not loaded:
                px.loadFromData(data)
            self.image_label.setPixmap(px)
        if reply: reply.deleteLater()

    def enterEvent(self, event): 
        if self.selectable:
            self._anim.stop()
            self._anim.setStartValue(self._hover_val)
            self._anim.setEndValue(5)
            self._anim.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event): 
        if self.selectable:
            self._anim.stop()
            self._anim.setStartValue(self._hover_val)
            self._anim.setEndValue(0)
            self._anim.start()
        super().leaveEvent(event)
        
    def _on_hover_animate(self, val):
        self._hover_val = val
        self.apply_stylesheet()
        
    def mousePressEvent(self, event):
        if self.selectable and event.button() == Qt.LeftButton:
            self.is_selected = not self.is_selected
            self.apply_stylesheet()
            self.selection_toggled.emit(self, self.is_selected, bool(event.modifiers() & Qt.ShiftModifier))
        elif self.selectable and event.button() == Qt.RightButton:
            self.detail_requested.emit(self.item_data)

    def apply_stylesheet(self):
        mod = CONFIG.get("mod", "none")
        r, g, b = hex_to_rgb(self.rarity_color)
        
        if mod == "femboy":
            bg_color = "qlineargradient(x1:0, y1:1, x2:0, y2:0, stop:0 rgba(255, 182, 193, 200), stop:1 rgba(255, 228, 225, 200))"
            border = "1px solid rgba(255, 105, 180, 200)" if self.is_selected else "1px solid rgba(255, 182, 193, 200)"
            self.weapon_label.setStyleSheet("color: #333333; background: transparent;")
            self.float_label.setStyleSheet("color: #d147a3; background: transparent;")
            if hasattr(self, 'tag_label'): self.tag_label.setStyleSheet("color: #999999; background: transparent;")
        elif mod == "lgbt":
            bg_color = "qlineargradient(x1:0, y1:1, x2:0, y2:0, stop:0 rgba(224, 224, 224, 180), stop:1 rgba(255, 255, 255, 180))"
            border = "1px solid rgba(0, 0, 0, 200)" if self.is_selected else "1px solid rgba(204, 204, 204, 150)"
            self.weapon_label.setStyleSheet("color: #333333; background: transparent;")
            self.float_label.setStyleSheet("color: #555555; background: transparent;")
            if hasattr(self, 'tag_label'): self.tag_label.setStyleSheet("color: #777777; background: transparent;")
        elif mod == "evil":
            t = 2 if self.is_selected else 0
            top = 18 + t + self._hover_val
            bot_r = int(r * 0.12) + t + (self._hover_val * 2) 
            bg_color = f"qlineargradient(x1:0, y1:1, x2:0, y2:0, stop:0 rgb({bot_r}, 0, 0), stop:1 rgb({top}, 0, 0))"
            border = "1px solid #ff0000" if self.is_selected else "1px solid #330000"
            self.weapon_label.setStyleSheet("color: #ffcccc; background: transparent;")
            self.float_label.setStyleSheet("color: #ff6666; background: transparent;")
            if hasattr(self, 'tag_label'): self.tag_label.setStyleSheet("color: #cc0000; background: transparent;")
        elif mod == "420":
            t = 2 if self.is_selected else 0
            top = 15 + t + self._hover_val
            bot_g = int(g * 0.15) + t + (self._hover_val * 2)
            bg_color = f"qlineargradient(x1:0, y1:1, x2:0, y2:0, stop:0 rgb(0, {bot_g}, 0), stop:1 rgb({top}, {top+10}, {top}))"
            border = "1px solid #32cd32" if self.is_selected else "1px solid #1a4d1a"
            self.weapon_label.setStyleSheet("color: #e6ffe6; background: transparent;")
            self.float_label.setStyleSheet("color: #98fb98; background: transparent;")
            if hasattr(self, 'tag_label'): self.tag_label.setStyleSheet("color: #8fbc8f; background: transparent;")
        else:
            t = 2 if self.is_selected else 0
            top = 18 + t + self._hover_val
            bot_r = int(r * 0.12) + t + (self._hover_val * 2)
            bg_color = f"qlineargradient(x1:0, y1:1, x2:0, y2:0, stop:0 rgb({bot_r}, {int(g*0.12)+t+(self._hover_val*2)}, {int(b*0.12)+t+(self._hover_val*2)}), stop:1 rgb({top}, {top}, {top}))"
            border = "1px solid #5c8a47" if self.is_selected else "1px solid #1a1a1a"
            self.weapon_label.setStyleSheet("color: #ffffff; background: transparent;")
            self.float_label.setStyleSheet("color: #cccccc; background: transparent;")
            if hasattr(self, 'tag_label'): self.tag_label.setStyleSheet("color: #999999; background: transparent;")
        self.setStyleSheet(f"#card {{ background: {bg_color}; border: {border}; border-radius: 8px; }}")

class CaseCard(QFrame):
    case_clicked = pyqtSignal(str, str, int)

    def __init__(self, case_data, network_manager, parent=None):
        super().__init__(parent)
        self.network_manager = network_manager
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.item_data = case_data
        self.case_id = case_data.get("id") or case_data.get("item_id")
        self.name = case_data.get("name", "Unknown Case")
        self.price = int(case_data.get("price", 0))
        self._hover_val = 0
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(150)
        self._anim.valueChanged.connect(self._on_hover_animate)
        
        coin_path = os.path.join(ASSETS_DIR, "coins.png")
        if not os.path.exists(coin_path): coin_path = os.path.join(USER_DATA_DIR, "coins.png")
        self.coin_icon_path = coin_path
        
        self.init_ui()
        self.apply_stylesheet()
        self.load_image()

    def init_ui(self):
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(2)
        
        self.top_line = QFrame(self)
        self.top_line.setStyleSheet("background-color: #888888; border: none;")
        
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        self.price_widget = QWidget()
        self.price_widget.setStyleSheet("background: transparent;")
        price_lay = QHBoxLayout(self.price_widget)
        price_lay.setContentsMargins(0,0,0,0)
        price_lay.setSpacing(4)
        
        self.coin_icon_label = QLabel()
        if os.path.exists(self.coin_icon_path):
            self.coin_icon_label.setPixmap(QIcon(self.coin_icon_path).pixmap(16, 16))
            
        self.price_label = QLabel(str(self.price))
        
        price_lay.addWidget(self.coin_icon_label, alignment=Qt.AlignVCenter)
        price_lay.addWidget(self.price_label, alignment=Qt.AlignVCenter)
        
        top_layout.addStretch()
        top_layout.addWidget(self.price_widget, alignment=Qt.AlignRight | Qt.AlignTop)
        layout.addLayout(top_layout)
        
        self.image_label = AspectRatioPixmapLabel()
        self.image_label.setStyleSheet("background: transparent;")
        layout.addWidget(self.image_label, stretch=1)
        
        bottom_layout = QVBoxLayout()
        bottom_layout.setSpacing(0) 
        self.name_label = ElidedLabel(self.name, weight=QFont.Bold)
        self.name_label.setStyleSheet("color: #ffffff; background: transparent;")
        bottom_layout.addWidget(self.name_label)
        layout.addLayout(bottom_layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = self.width()
        font = self.price_label.font()
        font.setPointSize(max(8, int(w * 0.06)))
        self.price_label.setFont(font)
        self.name_label.set_font_size(max(9, int(w * 0.06)))
        self.top_line.setFixedSize(int(w * 0.2), max(2, int(w * 0.01)))
        self.top_line.move((w - self.top_line.width()) // 2, 0)

    def load_image(self):
        url = f"https://cdn.csrestored.fun/cases/{self.case_id}.webp"
        req = QNetworkRequest(QUrl(url))
        req.setRawHeader(b"User-Agent", b"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        self.reply = self.network_manager.get(req)
        self.reply.finished.connect(self.on_image_downloaded)
        
    def on_image_downloaded(self):
        reply = self.sender()
        if reply and reply.error() == QNetworkReply.NoError: 
            data = reply.readAll()
            px = QPixmap()
            loaded = False
            if HAS_PILLOW:
                try:
                    webp_path = os.path.join(USER_DATA_DIR, f"temp_case_{self.case_id}.webp")
                    png_path = os.path.join(USER_DATA_DIR, f"temp_case_{self.case_id}.png")
                    with open(webp_path, "wb") as f:
                        f.write(data.data())
                    img = Image.open(webp_path)
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    img.save(png_path, "PNG")
                    px.load(png_path)
                    loaded = True
                except Exception:
                    pass
            if not loaded:
                px.loadFromData(data)
            self.image_label.setPixmap(px)
        if reply: reply.deleteLater()

    def enterEvent(self, event):
        self._anim.stop()
        self._anim.setStartValue(self._hover_val)
        self._anim.setEndValue(5)
        self._anim.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self._anim.stop()
        self._anim.setStartValue(self._hover_val)
        self._anim.setEndValue(0)
        self._anim.start()
        super().leaveEvent(event)
        
    def _on_hover_animate(self, val):
        self._hover_val = val
        self.apply_stylesheet()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.case_clicked.emit(str(self.case_id), self.name, self.price)

    def apply_stylesheet(self):
        mod = CONFIG.get("mod", "none")
        coin_col = "#d97706" if mod in ["femboy", "lgbt"] else "#fef08a"
        self.price_label.setStyleSheet(f"color: {coin_col}; background: transparent; font-weight: bold;")
        
        if mod == "femboy":
            bg_color = "qlineargradient(x1:0, y1:1, x2:0, y2:0, stop:0 rgba(255, 182, 193, 200), stop:1 rgba(255, 228, 225, 200))"
            border = "1px solid rgba(255, 182, 193, 200)"
            self.name_label.setStyleSheet("color: #333333; background: transparent;")
        elif mod == "lgbt":
            bg_color = "qlineargradient(x1:0, y1:1, x2:0, y2:0, stop:0 rgba(224, 224, 224, 180), stop:1 rgba(255, 255, 255, 180))"
            border = "1px solid rgba(204, 204, 204, 150)"
            self.name_label.setStyleSheet("color: #333333; background: transparent;")
        elif mod == "evil":
            top = 18 + self._hover_val
            bot_r = int(136 * 0.12) + (self._hover_val * 2) 
            bg_color = f"qlineargradient(x1:0, y1:1, x2:0, y2:0, stop:0 rgb({bot_r}, 0, 0), stop:1 rgb({top}, 0, 0))"
            border = "1px solid #4d0000"
            self.name_label.setStyleSheet("color: #ffcccc; background: transparent;")
        elif mod == "420":
            top = 15 + self._hover_val
            bot_g = int(136 * 0.15) + (self._hover_val * 2)
            bg_color = f"qlineargradient(x1:0, y1:1, x2:0, y2:0, stop:0 rgb(0, {bot_g}, 0), stop:1 rgb({top}, {top+10}, {top}))"
            border = "1px solid #1a4d1a"
            self.name_label.setStyleSheet("color: #e6ffe6; background: transparent;")
        else:
            top = 18 + self._hover_val
            bot_r = int(136 * 0.12) + (self._hover_val * 2)
            bg_color = f"qlineargradient(x1:0, y1:1, x2:0, y2:0, stop:0 rgb({bot_r}, {bot_r}, {bot_r}), stop:1 rgb({top}, {top}, {top}))"
            border = "1px solid #1a1a1a"
            self.name_label.setStyleSheet("color: #ffffff; background: transparent;")
        self.setStyleSheet(f"#card {{ background: {bg_color}; border: {border}; border-radius: 8px; }}")

# ================= ОСНОВНОЕ ОКНО ПРОГРАММЫ =================
class MainWindow(QMainWindow):
    def __init__(self, font_family):
        super().__init__()
        self.font_family = font_family
        self.t = TRANSLATIONS[CONFIG.get("lang", "en")]
        self.current_title = "CS:R Sell Assister"
        self.setWindowTitle(self.current_title)
        self.resize(1100, 800)
        
        icon_path = os.path.join(ASSETS_DIR, "icon.png")
        if not os.path.exists(icon_path): icon_path = os.path.join(ASSETS_DIR, "icon.ico")
        if os.path.exists(icon_path): self.setWindowIcon(QIcon(icon_path))
            
        self.network_manager = QNetworkAccessManager(self)
        self.inv_cards = []
        self.cases_cards = []
        self.detail_cards = []
        
        self.active_threads = set()
        
        self.last_inventory_state = None
        self.last_cases_state = None
        
        self.is_selling = False
        self.is_buying = False
        self.user_coins = 0
        self.current_mode = "inventory"
        self.active_case_id = None
        self.active_case_price = 0
        
        self.current_filters = {
            "types": [], "rarities": [], "conditions": [], "min_float": 0.0, "max_float": 1.0,
            "nametag": self.t["f_all"], "stattrak": self.t["f_all"]
        }
        
        self.key_buffer = ""
        self.player = QMediaPlayer()
        self.player.setVolume(15) 
        
        coin_path = os.path.join(ASSETS_DIR, "coins.png")
        if not os.path.exists(coin_path): coin_path = os.path.join(USER_DATA_DIR, "coins.png")
        self.coin_icon_path = coin_path
        
        self.flash_overlay = QWidget(self)
        self.flash_overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.flash_overlay.setStyleSheet("background-color: white;")
        self.flash_overlay.hide()
        self.opacity_effect = QGraphicsOpacityEffect()
        self.flash_overlay.setGraphicsEffect(self.opacity_effect)
        self.flash_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.flash_anim.setDuration(2000)
        self.flash_anim.finished.connect(self.flash_overlay.hide)

        self.title_timer = QTimer(self)
        self.title_timer.timeout.connect(self.animate_title_step)
        self.target_title = ""
        self.title_anim_state = 0

        self.lgbt_timer = QTimer(self)
        self.lgbt_timer.timeout.connect(self.update_lgbt_mod)
        self.lgbt_offset = 0
        self.snow_overlay = SnowOverlay(self)
        self.rain_overlay = RainOverlay(self)

        self.selected_cards = set()
        self.visible_cards = []

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.top_bar = QWidget()
        self.top_bar.hide() 
        top_bar_layout = QHBoxLayout(self.top_bar)
        top_bar_layout.setContentsMargins(15, 15, 15, 10)
        self.search_input = QLineEdit()
        self.search_input.setFont(QFont(self.font_family, 11))
        self.search_input.textChanged.connect(self.apply_filters)
        
        self.filter_btn = QPushButton()
        self.filter_btn.setFont(QFont(self.font_family, 11, QFont.Bold))
        self.filter_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.filter_btn.setFixedSize(120, 38)
        self.filter_btn.clicked.connect(self.open_filters)
        
        top_bar_layout.addWidget(self.search_input)
        top_bar_layout.addWidget(self.filter_btn)
        main_layout.addWidget(self.top_bar)
        
        self.case_top_bar = QWidget()
        self.case_top_bar.hide()
        case_top_layout = QHBoxLayout(self.case_top_bar)
        case_top_layout.setContentsMargins(15, 15, 15, 10)
        self.back_btn = QPushButton()
        self.back_btn.setFont(QFont(self.font_family, 11, QFont.Bold))
        self.back_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.back_btn.setFixedSize(100, 38)
        self.back_btn.clicked.connect(self.go_back_to_cases)
        
        self.case_name_label = QLabel()
        self.case_name_label.setFont(QFont(self.font_family, 14, QFont.Bold))
        
        self.qty_input = QLineEdit()
        self.qty_input.setValidator(QIntValidator(1, 9999))
        self.qty_input.setText("1")
        self.qty_input.setFixedSize(80, 38)
        self.qty_input.setFont(QFont(self.font_family, 11))
        self.qty_input.setAlignment(Qt.AlignCenter)
        self.qty_input.textChanged.connect(self.update_buy_button)
        
        self.max_btn = QPushButton()
        self.max_btn.setFont(QFont(self.font_family, 11, QFont.Bold))
        self.max_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.max_btn.setFixedSize(60, 38)
        self.max_btn.clicked.connect(self.set_max_cases)
        
        self.buy_case_btn = QPushButton()
        self.buy_case_btn.setFont(QFont(self.font_family, 11, QFont.Bold))
        self.buy_case_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.buy_case_btn.setFixedSize(180, 38)
        self.buy_case_btn.clicked.connect(self.buy_cases)
        
        case_top_layout.addWidget(self.back_btn)
        case_top_layout.addSpacing(15)
        case_top_layout.addWidget(self.case_name_label)
        case_top_layout.addStretch()
        case_top_layout.addWidget(self.qty_input)
        case_top_layout.addWidget(self.max_btn)
        case_top_layout.addSpacing(10)
        case_top_layout.addWidget(self.buy_case_btn)
        main_layout.addWidget(self.case_top_bar)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame) 
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.viewport().installEventFilter(self)
        
        self.content_widget = QWidget()
        self.content_widget.setObjectName("scrollContent")
        self.grid_layout = ResponsiveGridWidget(self.content_widget, scroll_area=self.scroll_area)
        grid_v_layout = QVBoxLayout(self.content_widget)
        grid_v_layout.setContentsMargins(0,0,0,0)
        grid_v_layout.addWidget(self.grid_layout)
        grid_v_layout.addStretch() 
        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)
        
        self.bottom_bar = QWidget()
        self.bottom_bar.setFixedHeight(70) 
        self.bottom_bar.hide()
        bottom_bar_layout = QHBoxLayout(self.bottom_bar)
        bottom_bar_layout.setContentsMargins(15, 10, 15, 15)
        
        self.coins_widget = QWidget()
        self.coins_widget.setStyleSheet("background: transparent;")
        cl = QHBoxLayout(self.coins_widget)
        cl.setContentsMargins(0,0,0,0)
        cl.setSpacing(6)
        
        self.coin_icon_label = QLabel()
        if os.path.exists(self.coin_icon_path):
            self.coin_icon_label.setPixmap(QIcon(self.coin_icon_path).pixmap(16, 16))
        
        self.coins_label = QLabel("0")
        self.coins_label.setFont(QFont(self.font_family, 12, QFont.Bold))
        self.coins_label.setStyleSheet("color: #fef08a; background: transparent;")
        
        cl.addWidget(self.coin_icon_label, alignment=Qt.AlignVCenter)
        cl.addWidget(self.coins_label, alignment=Qt.AlignVCenter)
        
        self.cases_btn = QPushButton()
        self.cases_btn.setFont(QFont(self.font_family, 11, QFont.Bold))
        self.cases_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.cases_btn.setFixedSize(120, 38)
        self.cases_btn.clicked.connect(self.toggle_cases_view)
        
        self.sell_btn = QPushButton()
        self.sell_btn.setFixedSize(220, 50) 
        self.sell_btn.setFont(QFont(self.font_family, 12, QFont.Bold))
        self.sell_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.sell_btn.hide()
        self.sell_btn.clicked.connect(self.start_selling)
        
        bottom_bar_layout.addWidget(self.coins_widget)
        bottom_bar_layout.addSpacing(15)
        bottom_bar_layout.addWidget(self.cases_btn)
        bottom_bar_layout.addStretch(1)
        bottom_bar_layout.addWidget(self.sell_btn)
        main_layout.addWidget(self.bottom_bar)
        
        self.dim_overlay = QWidget(self)
        self.dim_overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.7);")
        self.dim_overlay.hide()
        
        self.setCentralWidget(central_widget)
        self.help_shortcut = QShortcut(QKeySequence("F1"), self)
        self.help_shortcut.activated.connect(self.show_main_help)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.fetch_data)

        self.apply_global_theme() 
        QTimer.singleShot(100, self.startup_sequence)

    def closeEvent(self, event):
        try:
            for f in os.listdir(USER_DATA_DIR):
                if f.startswith("temp_case_") or f.startswith("temp_special") or f.startswith("temp_skin_"):
                    os.remove(os.path.join(USER_DATA_DIR, f))
        except Exception:
            pass
        super().closeEvent(event)

    def toggle_cases_view(self):
        self.selected_cards.clear()
        if self.current_mode == "inventory":
            self.current_mode = "cases"
            self.cases_btn.setText(self.t["btn_inventory"])
            self.filter_btn.hide()
            self.case_top_bar.hide()
            self.sell_btn.hide()
            self.apply_filters()
            self.fetch_data()
        elif self.current_mode in ["cases", "case_detail"]:
            self.current_mode = "inventory"
            self.cases_btn.setText(self.t["btn_cases"])
            self.top_bar.show()
            self.filter_btn.show()
            self.case_top_bar.hide()
            self.update_sell_button()
            self.apply_filters()
            self.fetch_data()
            
    def go_back_to_cases(self):
        self.current_mode = "cases"
        self.case_top_bar.hide()
        self.top_bar.show()
        self.apply_filters()

    def show_dialog(self, dialog):
        self.dim_overlay.raise_()
        self.dim_overlay.show()
        res = dialog.exec_()
        self.dim_overlay.hide()
        return res

    def open_case_detail(self, case_id, name, price):
        self.current_mode = "case_detail"
        self.active_case_id = case_id
        self.active_case_price = price
        self.case_name_label.setText(name)
        self.qty_input.setText("1")
        self.update_buy_button()
        
        self.top_bar.hide()
        self.case_top_bar.show()
        
        for c in self.detail_cards:
            c.hide()
            c.deleteLater()
        self.detail_cards = []
        self.grid_layout.set_cards([])
        
        th = CaseDetailFetcher(CONFIG["cookie"], case_id)
        self.active_threads.add(th)
        th.data_ready.connect(self.process_case_contents)
        th.finished.connect(lambda t=th: self.active_threads.discard(t))
        th.start()

    def update_buy_button(self):
        qty_text = self.qty_input.text()
        qty = int(qty_text) if qty_text.isdigit() else 0
        cost = qty * self.active_case_price
        
        if qty > 0 and self.user_coins >= cost and not self.is_buying:
            self.buy_case_btn.setEnabled(True)
            if os.path.exists(self.coin_icon_path):
                self.buy_case_btn.setIcon(QIcon(self.coin_icon_path))
                self.buy_case_btn.setIconSize(QSize(16, 16))
            self.buy_case_btn.setText(f" {cost}")
        else:
            self.buy_case_btn.setEnabled(False)
            self.buy_case_btn.setIcon(QIcon())
            if self.is_buying:
                self.buy_case_btn.setText(self.t["buying"])
            else:
                self.buy_case_btn.setText(self.t["unavailable"])

    def set_max_cases(self):
        if self.active_case_price > 0:
            max_qty = max(1, self.user_coins // self.active_case_price)
            self.qty_input.setText(str(max_qty))

    def buy_cases(self):
        if self.is_buying: return
        qty_text = self.qty_input.text()
        qty = int(qty_text) if qty_text.isdigit() else 0
        if qty <= 0: return
        
        self.is_buying = True
        self.buy_case_btn.setEnabled(False)
        self.buy_case_btn.setIcon(QIcon())
        self.buy_case_btn.setText(self.t["buying"])
        self.max_btn.setEnabled(False)
        self.qty_input.setEnabled(False)
        
        th = CaseBuyerThread(self.active_case_id, qty, CONFIG["cookie"])
        self.active_threads.add(th)
        th.buy_finished.connect(self.on_buy_finished)
        th.finished.connect(lambda t=th: self.active_threads.discard(t))
        th.start()

    def on_buy_finished(self):
        self.is_buying = False
        self.max_btn.setEnabled(True)
        self.qty_input.setEnabled(True)
        self.fetch_users() 
        self.update_buy_button()

    def open_filters(self):
        weapon_types = set()
        for card in self.inv_cards:
            name_parts = card.name.split(" | ")
            if name_parts:
                weapon_types.add(name_parts[0].replace("★ ", ""))
                
        dialog = FilterDialog(self.current_filters, weapon_types, self.t, self.font_family, CONFIG.get("mod"), self)
        if self.show_dialog(dialog) == QDialog.Accepted:
            self.current_filters = dialog.result_filters
            self.apply_filters()

    def apply_filters(self):
        search_text = self.search_input.text().lower().split()
        filtered = []
        
        if self.current_mode == "cases":
            for card in self.cases_cards:
                if search_text and not all(word in card.name.lower() for word in search_text): continue
                filtered.append(card)
        elif self.current_mode == "case_detail":
            for card in self.detail_cards:
                filtered.append(card) 
        else:
            for card in self.inv_cards:
                item = card.item_data
                name = item.get("name", "").lower()
                nametag = item.get("nametag", "").lower() if item.get("nametag") else ""
                search_target = f"{name} {nametag}"
                
                if search_text and not all(word in search_target for word in search_text): continue
                w_type = item.get("name", "").split(" | ")[0].replace("★ ", "")
                if self.current_filters["types"] and w_type not in self.current_filters["types"]: continue
                if self.current_filters["rarities"] and str(item.get("rarity")) not in self.current_filters["rarities"]: continue
                    
                fl = item.get("float", 0.0)
                fl = 0.0 if fl is None else fl
                if self.current_filters["conditions"]:
                    cond_match = False
                    for cond in self.current_filters["conditions"]:
                        if cond == "fn" and 0.0 <= fl <= 0.07: cond_match = True
                        elif cond == "mw" and 0.07 < fl <= 0.15: cond_match = True
                        elif cond == "ft" and 0.15 < fl <= 0.38: cond_match = True
                        elif cond == "ww" and 0.38 < fl <= 0.45: cond_match = True
                        elif cond == "bs" and 0.45 < fl <= 1.0: cond_match = True
                    if not cond_match: continue
                if not (self.current_filters["min_float"] <= fl <= self.current_filters["max_float"]): continue
                    
                has_nt = bool(item.get("nametag"))
                if self.current_filters["nametag"] == self.t["f_yes"] and not has_nt: continue
                if self.current_filters["nametag"] == self.t["f_no"] and has_nt: continue
                
                has_st = bool(item.get("stattrak"))
                if self.current_filters["stattrak"] == self.t["f_yes"] and not has_st: continue
                if self.current_filters["stattrak"] == self.t["f_no"] and has_st: continue
                
                filtered.append(card)
            
        self.visible_cards = filtered
        self.grid_layout.set_cards(filtered)

    def paintEvent(self, event):
        if CONFIG.get("mod") == "lgbt":
            painter = QPainter(self)
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            c1 = QColor.fromHsv(self.lgbt_offset, 150, 255)
            c2 = QColor.fromHsv((self.lgbt_offset + 180) % 360, 150, 255)
            gradient.setColorAt(0, c1)
            gradient.setColorAt(1, c2)
            painter.fillRect(self.rect(), gradient)
        super().paintEvent(event)

    def keyPressEvent(self, event):
        if event.text():
            char = event.text().lower()
            ru_to_en = str.maketrans("йцукенгшщзхъфывапролджэячсмитьбю", "qwertyuiop[]asdfghjkl;'zxcvbnm,.")
            char = char.translate(ru_to_en)
            self.key_buffer += char
            if len(self.key_buffer) > 20:
                self.key_buffer = self.key_buffer[-20:]
            
            current_mod = CONFIG.get("mod", "none")
            
            if self.key_buffer.endswith("femboy"):
                self.key_buffer = ""
                self.activate_mod("femboy" if current_mod != "femboy" else "none")
            elif self.key_buffer.endswith("lgbt"):
                self.key_buffer = ""
                self.activate_mod("lgbt" if current_mod != "lgbt" else "none")
            elif self.key_buffer.endswith("snow"):
                self.key_buffer = ""
                self.activate_mod("snow" if current_mod != "snow" else "none")
            elif self.key_buffer.endswith("evil"):
                self.key_buffer = ""
                self.activate_mod("evil" if current_mod != "evil" else "none")
            elif self.key_buffer.endswith("rain"):
                self.key_buffer = ""
                self.activate_mod("rain" if current_mod != "rain" else "none")
            elif self.key_buffer.endswith("420"):
                self.key_buffer = ""
                self.activate_mod("420" if current_mod != "420" else "none")
        super().keyPressEvent(event)

    def activate_mod(self, mod_name):
        CONFIG["mod"] = mod_name
        save_config()
        self.apply_global_theme()
        
        self.flash_anim.stop()
        self.opacity_effect.setOpacity(1.0)
        self.flash_overlay.setStyleSheet("background-color: white;")
        self.flash_overlay.resize(self.size())
        self.flash_overlay.show()
        self.flash_overlay.raise_()
        self.flash_anim.setStartValue(1.0)
        self.flash_anim.setEndValue(0.0)
        self.flash_anim.start()
        
        audio_file = None
        if mod_name == "femboy": self.target_title = "CS:R Femboy Sell Assister :3"; audio_file = "nya.mp3"
        elif mod_name == "lgbt": self.target_title = "CS:R LGBT Sell Assister :D"; audio_file = "yippee.mp3"
        elif mod_name == "snow": self.target_title = "CS:R Snowy Sell Assister"; audio_file = "okno.mp3"
        elif mod_name == "evil": self.target_title = "EVIL CS:R SELL ASSISTER"; audio_file = "zloy.mp3"
        elif mod_name == "rain": self.target_title = "CS:R Rainy Sell Assister"; audio_file = "sad.mp3"
        elif mod_name == "420": self.target_title = "CS:R 420 Sell Assister"; audio_file = "weed.mp3"
        else: self.target_title = "CS:R Sell Assister"
            
        if audio_file:
            audio_path = os.path.join(ASSETS_DIR, audio_file)
            if not os.path.exists(audio_path):
                audio_path = os.path.join(USER_DATA_DIR, audio_file)
            if os.path.exists(audio_path):
                self.player.setMedia(QMediaContent(QUrl.fromLocalFile(audio_path)))
                self.player.setVolume(15)
                self.player.play()
                
        self.title_anim_state = 0
        self.title_timer.start(50)
        for card in self.inv_cards + self.cases_cards + self.detail_cards:
            card.apply_stylesheet()
        self.update_sell_button()

    def animate_title_step(self):
        curr = self.windowTitle()
        if self.title_anim_state == 0:
            if len(curr) > 1:
                self.setWindowTitle(curr[:-1])
            else:
                self.setWindowTitle(" ")
                self.title_anim_state = 1
        else:
            if len(curr) < len(self.target_title):
                self.setWindowTitle(self.target_title[:len(curr)+1])
            else:
                self.title_timer.stop()

    def update_lgbt_mod(self):
        if CONFIG.get("mod") != "lgbt":
            self.lgbt_timer.stop()
            return
        self.lgbt_offset = (self.lgbt_offset + 2) % 360
        self.update() 

    def apply_global_theme(self):
        mod = CONFIG.get("mod", "none")
        coin_color = "#d97706" if mod in ["femboy", "lgbt"] else "#fef08a"
        self.coins_label.setStyleSheet(f"color: {coin_color}; background: transparent;")
        
        if mod == "femboy":
            self.lgbt_timer.stop()
            self.snow_overlay.stop()
            self.rain_overlay.stop()
            self.setStyleSheet("""
                QMainWindow, QScrollArea { background-color: #ffe4e1; border: none; }
                QWidget#scrollContent { background-color: #ffe4e1; }
                QScrollBar:vertical { border: none; background: transparent; width: 8px; border-radius: 4px; margin: 0px; }
                QScrollBar::handle:vertical { background: #ff69b4; min-height: 30px; border-radius: 4px; }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; border: none; }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { background: transparent; border: none; height: 0px; }
            """)
            self.scroll_area.viewport().setStyleSheet("background-color: #ffe4e1;")
            self.top_bar.setStyleSheet("background-color: #ffe4e1;")
            self.case_top_bar.setStyleSheet("background-color: #ffe4e1;")
            self.bottom_bar.setStyleSheet("background-color: #ffe4e1;")
            self.case_name_label.setStyleSheet("color: #ff69b4; border: none;")
            input_style = "QLineEdit { background-color: #ffb6c1; color: #333; border: 1px solid #ff69b4; border-radius: 19px; padding: 0 15px; height: 38px; } QLineEdit:focus { border: 1px solid #ff1493; }"
            self.search_input.setStyleSheet(input_style)
            self.qty_input.setStyleSheet(input_style)
            btn_style = "QPushButton { background-color: #ff69b4; color: white; border-radius: 19px; border: none; } QPushButton:hover { background-color: #ff1493; }"
            self.filter_btn.setStyleSheet(btn_style)
            self.cases_btn.setStyleSheet(btn_style)
            self.back_btn.setStyleSheet(btn_style)
            self.max_btn.setStyleSheet(btn_style)
            self.sell_btn.setStyleSheet("QPushButton { background-color: #ff69b4; color: white; border-radius: 25px; border: 1px solid #ff1493; } QPushButton:hover { background-color: #ff1493; } QPushButton:disabled { background-color: #ffb6c1; color: #ffffff; border: none; }")
            self.buy_case_btn.setStyleSheet("QPushButton { background-color: #ff69b4; color: white; border-radius: 19px; border: 1px solid #ff1493; padding: 0 15px; } QPushButton:hover { background-color: #ff1493; } QPushButton:disabled { background-color: #ffb6c1; color: #ffffff; border: none; }")
            
        elif mod == "lgbt":
            self.snow_overlay.stop()
            self.rain_overlay.stop()
            self.lgbt_timer.start(30)
            self.setStyleSheet("""
                QMainWindow, QScrollArea { background-color: transparent; border: none; }
                QWidget#scrollContent { background-color: transparent; }
                QScrollBar:vertical { border: none; background: transparent; width: 8px; border-radius: 4px; margin: 0px; }
                QScrollBar::handle:vertical { background: rgba(0,0,0,100); min-height: 30px; border-radius: 4px; }
                QScrollBar::handle:vertical:hover { background: rgba(0,0,0,150); }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; border: none; }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { background: transparent; border: none; height: 0px; }
            """)
            self.scroll_area.viewport().setStyleSheet("background-color: transparent;")
            self.top_bar.setStyleSheet("background-color: transparent;")
            self.case_top_bar.setStyleSheet("background-color: transparent;")
            self.bottom_bar.setStyleSheet("background-color: transparent;")
            self.case_name_label.setStyleSheet("color: #333333; border: none;")
            input_style = "QLineEdit { background-color: rgba(255,255,255,180); color: #333; border: 1px solid rgba(0,0,0,100); border-radius: 19px; padding: 0 15px; height: 38px; } QLineEdit:focus { border: 1px solid #000; }"
            self.search_input.setStyleSheet(input_style)
            self.qty_input.setStyleSheet(input_style)
            btn_style = "QPushButton { background-color: rgba(0,0,0,150); color: white; border-radius: 19px; border: none; } QPushButton:hover { background-color: rgba(0,0,0,200); }"
            self.filter_btn.setStyleSheet(btn_style)
            self.cases_btn.setStyleSheet(btn_style)
            self.back_btn.setStyleSheet(btn_style)
            self.max_btn.setStyleSheet(btn_style)
            self.sell_btn.setStyleSheet("QPushButton { background-color: #333333; color: white; border-radius: 25px; border: 1px solid #000000; } QPushButton:hover { background-color: #555555; } QPushButton:disabled { background-color: #999999; color: #dddddd; border: none; }")
            self.buy_case_btn.setStyleSheet("QPushButton { background-color: #333333; color: white; border-radius: 19px; border: 1px solid #000000; padding: 0 15px; } QPushButton:hover { background-color: #555555; } QPushButton:disabled { background-color: #999999; color: #dddddd; border: none; }")
            
        elif mod == "evil":
            self.lgbt_timer.stop()
            self.snow_overlay.stop()
            self.rain_overlay.stop()
            self.setStyleSheet("""
                QMainWindow, QScrollArea { background-color: #0d0000; border: none; }
                QWidget#scrollContent { background-color: #0d0000; }
                QScrollBar:vertical { border: none; background: transparent; width: 8px; border-radius: 4px; margin: 0px; }
                QScrollBar::handle:vertical { background: #4d0000; min-height: 30px; border-radius: 4px; }
                QScrollBar::handle:vertical:hover { background: #ff0000; }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; border: none; }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { background: transparent; border: none; height: 0px; }
            """)
            self.scroll_area.viewport().setStyleSheet("background-color: #0d0000;")
            self.top_bar.setStyleSheet("background-color: #0d0000;")
            self.case_top_bar.setStyleSheet("background-color: #0d0000;")
            self.bottom_bar.setStyleSheet("background-color: #0d0000;")
            self.case_name_label.setStyleSheet("color: #ffcccc; border: none;")
            input_style = "QLineEdit { background-color: #1a0000; color: #ffcccc; border: 1px solid #4d0000; border-radius: 19px; padding: 0 15px; height: 38px; } QLineEdit:focus { border: 1px solid #ff0000; }"
            self.search_input.setStyleSheet(input_style)
            self.qty_input.setStyleSheet(input_style)
            btn_style = "QPushButton { background-color: #2a0000; color: #ffcccc; border-radius: 19px; border: 1px solid #4d0000; } QPushButton:hover { background-color: #4d0000; }"
            self.filter_btn.setStyleSheet(btn_style)
            self.cases_btn.setStyleSheet(btn_style)
            self.back_btn.setStyleSheet(btn_style)
            self.max_btn.setStyleSheet(btn_style)
            self.sell_btn.setStyleSheet("QPushButton { background-color: #4d0000; color: white; border-radius: 25px; border: 1px solid #ff0000; } QPushButton:hover { background-color: #800000; } QPushButton:disabled { background-color: #1a0000; color: #660000; border: none; }")
            self.buy_case_btn.setStyleSheet("QPushButton { background-color: #4d0000; color: white; border-radius: 19px; border: 1px solid #ff0000; padding: 0 15px; } QPushButton:hover { background-color: #800000; } QPushButton:disabled { background-color: #1a0000; color: #660000; border: none; }")

        elif mod == "420":
            self.lgbt_timer.stop()
            self.snow_overlay.stop()
            self.rain_overlay.stop()
            self.setStyleSheet("""
                QMainWindow, QScrollArea { background-color: #0f1a0f; border: none; }
                QWidget#scrollContent { background-color: #0f1a0f; }
                QScrollBar:vertical { border: none; background: transparent; width: 8px; border-radius: 4px; margin: 0px; }
                QScrollBar::handle:vertical { background: #228b22; min-height: 30px; border-radius: 4px; }
                QScrollBar::handle:vertical:hover { background: #2e8b57; }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; border: none; }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { background: transparent; border: none; height: 0px; }
            """)
            self.scroll_area.viewport().setStyleSheet("background-color: #0f1a0f;")
            self.top_bar.setStyleSheet("background-color: #0f1a0f;")
            self.case_top_bar.setStyleSheet("background-color: #0f1a0f;")
            self.bottom_bar.setStyleSheet("background-color: #0f1a0f;")
            self.case_name_label.setStyleSheet("color: #e6ffe6; border: none;")
            input_style = "QLineEdit { background-color: #172b17; color: #e6ffe6; border: 1px solid #228b22; border-radius: 19px; padding: 0 15px; height: 38px; } QLineEdit:focus { border: 1px solid #32cd32; }"
            self.search_input.setStyleSheet(input_style)
            self.qty_input.setStyleSheet(input_style)
            btn_style = "QPushButton { background-color: #172b17; color: #e6ffe6; border-radius: 19px; border: 1px solid #228b22; } QPushButton:hover { background-color: #228b22; }"
            self.filter_btn.setStyleSheet(btn_style)
            self.cases_btn.setStyleSheet(btn_style)
            self.back_btn.setStyleSheet(btn_style)
            self.max_btn.setStyleSheet(btn_style)
            self.sell_btn.setStyleSheet("QPushButton { background-color: #228b22; color: white; border-radius: 25px; border: 1px solid #32cd32; } QPushButton:hover { background-color: #2e8b57; } QPushButton:disabled { background-color: #0f1a0f; color: #556b2f; border: none; }")
            self.buy_case_btn.setStyleSheet("QPushButton { background-color: #228b22; color: white; border-radius: 19px; border: 1px solid #32cd32; padding: 0 15px; } QPushButton:hover { background-color: #2e8b57; } QPushButton:disabled { background-color: #0f1a0f; color: #556b2f; border: none; }")

        else:
            self.lgbt_timer.stop()
            if mod == "snow":
                self.snow_overlay.start()
                self.rain_overlay.stop()
            elif mod == "rain":
                self.rain_overlay.start()
                self.snow_overlay.stop()
            else:
                self.snow_overlay.stop()
                self.rain_overlay.stop()
            
            self.setStyleSheet("""
                QMainWindow, QScrollArea { background-color: #080808; border: none; }
                QWidget#scrollContent { background-color: #080808; }
                QScrollBar:vertical { border: none; background: transparent; width: 8px; border-radius: 4px; margin: 0px; }
                QScrollBar::handle:vertical { background: #3a3a3a; min-height: 30px; border-radius: 4px; }
                QScrollBar::handle:vertical:hover { background: #5c8a47; }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; border: none; }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { background: transparent; border: none; height: 0px; }
            """)
            self.scroll_area.viewport().setStyleSheet("background-color: #080808;")
            self.top_bar.setStyleSheet("background-color: #080808;")
            self.case_top_bar.setStyleSheet("background-color: #080808;")
            self.bottom_bar.setStyleSheet("background-color: #080808;")
            self.case_name_label.setStyleSheet("color: #ffffff; border: none;")
            input_style = "QLineEdit { background-color: #1a1a1a; color: white; border: 1px solid #333; border-radius: 19px; padding: 0 15px; height: 38px; } QLineEdit:focus { border: 1px solid #5c8a47; }"
            self.search_input.setStyleSheet(input_style)
            self.qty_input.setStyleSheet(input_style)
            btn_style = "QPushButton { background-color: #2a2a2a; color: white; border-radius: 19px; border: none; } QPushButton:hover { background-color: #3a3a3a; }"
            self.filter_btn.setStyleSheet(btn_style)
            self.cases_btn.setStyleSheet(btn_style)
            self.back_btn.setStyleSheet(btn_style)
            self.max_btn.setStyleSheet(btn_style)
            self.sell_btn.setStyleSheet("QPushButton { background-color: #5c8a47; color: white; border-radius: 25px; border: 1px solid #71a957; } QPushButton:hover { background-color: #6da354; } QPushButton:disabled { background-color: #3a3a3a; color: #777777; border: none; }")
            self.buy_case_btn.setStyleSheet("QPushButton { background-color: #5c8a47; color: white; border-radius: 19px; border: 1px solid #71a957; padding: 0 15px; } QPushButton:hover { background-color: #6da354; } QPushButton:disabled { background-color: #3a3a3a; color: #777777; border: none; }")
            
        self.update_buy_button()

    def startup_sequence(self):
        if not CONFIG.get("lang"):
            lang_dialog = LanguageDialog(self.font_family, self)
            if lang_dialog.exec_() == QDialog.Accepted:
                CONFIG["lang"] = lang_dialog.selected_lang
                save_config()
                self.t = TRANSLATIONS[CONFIG["lang"]]
            else:
                sys.exit()
                
        self.t = TRANSLATIONS[CONFIG["lang"]]
        self.search_input.setPlaceholderText(self.t["search_ph"])
        self.filter_btn.setText(self.t["filters"])
        self.cases_btn.setText(self.t["btn_cases"])
        self.back_btn.setText(self.t["btn_back"])
        self.max_btn.setText(self.t["btn_max"])
        self.current_filters["nametag"] = self.t["f_all"]
        self.current_filters["stattrak"] = self.t["f_all"]
        
        if not CONFIG.get("cookie"):
            auth_dialog = CookieDialog(self.t, self.font_family, self)
            if auth_dialog.exec_() == QDialog.Accepted:
                cookie_data = auth_dialog.input_field.text().strip()
                if cookie_data:
                    CONFIG["cookie"] = cookie_data
                    save_config()
                else:
                    sys.exit()
            else:
                sys.exit()
                
        if not CONFIG.get("first_launch_done"):
            CONFIG["first_launch_done"] = True
            save_config()
            self.show_main_help()
            
        current_mod = CONFIG.get("mod")
        if current_mod == "femboy":
            self.setWindowTitle("CS:R Femboy Sell Assister :3")
        elif current_mod == "lgbt":
            self.setWindowTitle("CS:R LGBT Sell Assister :D")
        elif current_mod == "snow":
            self.setWindowTitle("CS:R Snowy Sell Assister")
        elif current_mod == "evil":
            self.setWindowTitle("EVIL CS:R SELL ASSISTER")
        elif current_mod == "rain":
            self.setWindowTitle("CS:R Rainy Sell Assister")
        elif current_mod == "420":
            self.setWindowTitle("CS:R 420 Sell Assister")
            
        self.update_sell_button()
        self.top_bar.show()
        self.bottom_bar.show()
        
        self.fetch_data()
        self.refresh_timer.start(10000) 

    def show_main_help(self):
        MainHelpDialog(self.t, self.font_family, self).exec_()

    def eventFilter(self, obj, event):
        if obj == self.scroll_area.viewport() and event.type() == QEvent.Wheel:
            if event.modifiers() == Qt.ControlModifier:
                if event.angleDelta().y() > 0:
                    self.grid_layout.zoom(1) 
                else:
                    self.grid_layout.zoom(-1) 
                return True 
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.flash_overlay.isVisible():
            self.flash_overlay.resize(self.size())
        if self.snow_overlay.is_running:
            self.snow_overlay.resize(self.size())
        if self.rain_overlay.is_running:
            self.rain_overlay.resize(self.size())
        self.dim_overlay.resize(self.size())

    def fetch_users(self):
        th = UserFetcher(CONFIG["cookie"])
        self.active_threads.add(th)
        th.data_ready.connect(self.on_coins_fetched)
        th.finished.connect(lambda t=th: self.active_threads.discard(t))
        th.start()

    def on_coins_fetched(self, coins):
        self.user_coins = coins
        self.coins_label.setText(str(coins))
        if self.current_mode == "case_detail":
            self.update_buy_button()

    def fetch_data(self):
        if self.is_selling: return
        self.fetch_users()
        
        if self.current_mode == "inventory":
            th = InventoryFetcher(CONFIG["cookie"])
            self.active_threads.add(th)
            th.data_ready.connect(self.process_inventory)
            th.finished.connect(lambda t=th: self.active_threads.discard(t))
            th.start()
        elif self.current_mode == "cases":
            th = CasesFetcher(CONFIG["cookie"])
            self.active_threads.add(th)
            th.data_ready.connect(self.process_cases)
            th.finished.connect(lambda t=th: self.active_threads.discard(t))
            th.start()

    def process_cases(self, data):
        if not isinstance(data, list): return
        data = [c for c in data if c.get("item_id") is not None]
        data.sort(key=lambda x: int(x.get("price", 0)), reverse=True)
        
        new_state = json.dumps(data, sort_keys=True)
        if getattr(self, 'last_cases_state', None) == new_state: return
        self.last_cases_state = new_state
        
        existing_cards = {c.case_id: c for c in self.cases_cards}
        new_cards = []
        for item in data:
            cid = item.get("item_id")
            if cid in existing_cards:
                new_cards.append(existing_cards.pop(cid))
            else:
                card = CaseCard(item, self.network_manager)
                card.case_clicked.connect(self.open_case_detail)
                new_cards.append(card)
                
        for card in existing_cards.values():
            card.hide()
            card.deleteLater()
            
        self.cases_cards = new_cards
        if self.current_mode == "cases":
            self.apply_filters()

    def process_case_contents(self, data):
        if not isinstance(data, list): return
        
        no_gold_cases = {"81", "82", "83", "84", "80", "67", "68", "55", "69", "59", "63", "48", "49", "62", "64", "47", "38", "56", "57", "36", "30", "51", "72", "77", "76", "28", "34", "46", "27", "45", "33", "43", "26", "31", "39", "42", "29", "37", "44", "40", "41", "32"}
        
        if str(self.active_case_id) not in no_gold_cases:
            if not any(str(x.get("rarity", "")) == "0" for x in data):
                data.append({"name": "Special | Rare Item", "rarity": "0", "item_id": "special_item"})
            
        data.sort(key=lambda x: int(x.get("rarity", 6)))
        
        for c in self.detail_cards:
            c.hide()
            c.deleteLater()
            
        new_cards = []
        for item in data:
            try:
                card = ItemCard(item, self.network_manager, is_case_content=True)
                new_cards.append(card)
            except:
                pass
            
        self.detail_cards = new_cards
        if self.current_mode == "case_detail":
            self.apply_filters()

    def process_inventory(self, data):
        if not isinstance(data, list): return
        filtered_data = [item for item in data if str(item.get("item_type", "")) != "8"]
        
        new_state = json.dumps(filtered_data, sort_keys=True)
        if self.last_inventory_state == new_state: return 
        self.last_inventory_state = new_state
        
        existing_cards = {c.weapon_id: c for c in self.inv_cards}
        new_cards = []
        
        for item in filtered_data:
            wid = item.get("weapon_id")
            if wid in existing_cards:
                card = existing_cards.pop(wid)
                card.item_data = item
                card.nametag = item.get("nametag", "")
                if card.nametag:
                    card.tag_label.setText(f'"{card.nametag}"')
                    card.tag_label.show()
                else:
                    card.tag_label.hide()
                new_cards.append(card)
            else:
                card = ItemCard(item, self.network_manager)
                card.selection_toggled.connect(self.on_card_selection_changed)
                card.detail_requested.connect(self.open_item_details)
                if wid in [c.weapon_id for c in self.selected_cards if hasattr(c, 'weapon_id')]:
                    card.is_selected = True
                    card.apply_stylesheet()
                    self.selected_cards.add(card)
                new_cards.append(card)
                
        for card in existing_cards.values():
            self.selected_cards.discard(card)
            card.hide()
            card.deleteLater()
            
        self.inv_cards = new_cards
        if self.current_mode == "inventory":
            self.apply_filters()

    def on_card_selection_changed(self, clicked_card, is_selected, is_shift):
        if self.is_selling:
            clicked_card.is_selected = not is_selected
            clicked_card.apply_stylesheet()
            return
            
        if hasattr(self, 'visible_cards'):
            if is_shift:
                target_name = clicked_card.name
                for card in self.visible_cards:
                    if card.name == target_name and card != clicked_card:
                        card.is_selected = is_selected
                        card.apply_stylesheet()
                        if is_selected:
                            self.selected_cards.add(card)
                        else:
                            self.selected_cards.discard(card)
                            
        if is_selected:
            self.selected_cards.add(clicked_card)
        else:
            self.selected_cards.discard(clicked_card)
            
        self.update_sell_button()

    def update_sell_button(self):
        count = len(self.selected_cards)
        if count > 0 and self.current_mode == "inventory":
            mod = CONFIG.get("mod", "none")
            if mod == "femboy":
                self.sell_btn.setText(f"kawaii sell >< ({count})")
            elif mod == "evil":
                self.sell_btn.setText(f"evil sell ({count})")
            else:
                self.sell_btn.setText(self.t["sell_count"].format(count))
            self.sell_btn.show()
            self.sell_btn.raise_()
        else:
            self.sell_btn.hide()

    def start_selling(self):
        if not self.selected_cards: return
        confirm = ConfirmDialog(len(self.selected_cards), self.t, self.font_family, CONFIG.get("mod", "none"), self)
        res = self.show_dialog(confirm)
        
        if res == QDialog.Accepted:
            self.is_selling = True
            self.refresh_timer.stop()
            self.sell_btn.setEnabled(False)
            self.sell_btn.setText(self.t["selling"])
            weapon_ids = [card.weapon_id for card in self.selected_cards if hasattr(card, 'weapon_id')]
            
            th = SellerThread(weapon_ids, CONFIG["cookie"])
            self.active_threads.add(th)
            th.item_sold.connect(self.on_item_sold)
            th.sell_finished.connect(lambda t=th: self.on_sell_finished(t))
            th.finished.connect(lambda t=th: self.active_threads.discard(t))
            th.start()

    def on_item_sold(self, weapon_id):
        card_to_remove = None
        for card in list(self.selected_cards):
            if hasattr(card, 'weapon_id') and card.weapon_id == weapon_id:
                card_to_remove = card
                self.selected_cards.remove(card)
                break
        
        if card_to_remove:
            if card_to_remove in self.inv_cards:
                self.inv_cards.remove(card_to_remove)
            if hasattr(self, 'visible_cards') and card_to_remove in self.visible_cards: 
                self.visible_cards.remove(card_to_remove)
            self.grid_layout.remove_card(card_to_remove)
            
        self.update_sell_button()

    def on_sell_finished(self, th):
        if th in self.active_threads:
            self.active_threads.remove(th)
        self.sell_btn.setEnabled(True)
        self.selected_cards.clear()
        self.update_sell_button()
        self.is_selling = False
        self.fetch_data()
        self.refresh_timer.start(10000)

    def open_item_details(self, item_data):
        dialog = ItemDetailDialog(item_data, self.network_manager, self.t, self.font_family, CONFIG.get("mod", "none"), self.is_selling, self)
        dialog.sell_requested.connect(self.handle_quick_sell)
        dialog.nametag_requested.connect(self.handle_nametag_update)
        self.show_dialog(dialog)

    def handle_quick_sell(self, weapon_id):
        if self.is_selling: return
        self._execute_quick_sell(weapon_id)
        
    def _execute_quick_sell(self, weapon_id):
        th = SellerThread([weapon_id], CONFIG["cookie"])
        self.active_threads.add(th)
        th.item_sold.connect(self.on_item_sold)
        th.item_sold.connect(lambda wid, t=th: self.on_quick_sell_sold(wid, t))
        th.finished.connect(lambda t=th: self.active_threads.discard(t))
        th.start()
        
    def on_quick_sell_sold(self, weapon_id, th):
        if th in self.active_threads:
            self.active_threads.remove(th)
        self.fetch_users()

    def handle_nametag_update(self, weapon_id, nametag):
        th = NametagUpdateThread(weapon_id, nametag, CONFIG["cookie"])
        self.active_threads.add(th)
        th.finished_signal.connect(lambda s, m, w=weapon_id, n=nametag, t=th: self.on_nametag_finished(s, m, w, n, t))
        th.finished.connect(lambda t=th: self.active_threads.discard(t))
        th.start()
        
    def on_nametag_finished(self, success, msg, weapon_id, nametag, th):
        if th in self.active_threads:
            self.active_threads.remove(th)
            
        if success:
            for card in self.inv_cards:
                if getattr(card, 'weapon_id', None) == weapon_id:
                    card.nametag = nametag
                    card.tag_label.setText(f'"{nametag}"' if nametag else "")
                    card.tag_label.setVisible(bool(nametag))
                    if isinstance(card.item_data, dict):
                        card.item_data["nametag"] = nametag
                    break
                    
        self.fetch_users() 
        for window in QApplication.topLevelWidgets():
            if isinstance(window, ItemDetailDialog):
                window.accept()

if __name__ == "__main__":
    if os.name == 'nt':
        import ctypes
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('csr.sell.assister')
        except:
            pass
        
    app = QApplication(sys.argv)
    load_config()
    
    font_path = ensure_font_downloaded()
    font_family = "Arial"
    if os.path.exists(font_path):
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]

    app_font = QFont(font_family, 10)
    app_font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(app_font)
    
    window = MainWindow(font_family)
    window.show()
    sys.exit(app.exec_())