# -*- coding: utf-8 -*-
"""
自訂區域截圖應用 - PyQt5
使用拖曳設定螢幕截圖區域，按熱鍵即可截圖。
"""

import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QGroupBox, QFileDialog, QMessageBox,
    QDesktopWidget,
)
from PyQt5.QtCore import Qt, QRect, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from pynput import keyboard
from PIL import ImageGrab


# --- 區域選擇覆蓋視窗（拖曳設定截圖範圍）---
class RegionSelector(QWidget):
    """全螢幕半透明覆蓋，使用者拖曳畫出矩形區域。"""
    region_selected = pyqtSignal(int, int, int, int)  # x, y, w, h

    def __init__(self):
        super().__init__()
        self.start_pos = None
        self.end_pos = None
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        # Windows 上使用不透明視窗 + 整體透明度，較穩定
        self.setWindowOpacity(0.55)
        self.setStyleSheet("background-color: black;")
        self.setCursor(Qt.CrossCursor)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_AcceptTouchEvents, False)
        # 拖曳說明（固定顯示在畫面上方）
        self.hint = QLabel("拖曳滑鼠選取截圖區域 → 放開完成 | Esc 取消", self)
        self.hint.setStyleSheet(
            "color: white; font-size: 18px; font-weight: bold; "
            "background: rgba(0,0,0,120); padding: 12px 24px; border-radius: 8px;"
        )
        self.hint.setAlignment(Qt.AlignCenter)
        self.hint.adjustSize()

    def show_fullscreen(self):
        """覆蓋整個虛擬桌面（含多螢幕）。"""
        desktop = QApplication.desktop()
        self.setGeometry(desktop.rect())
        self.showNormal()
        self.raise_()
        self.activateWindow()
        # 說明文字置中偏上
        self.hint.move(
            (desktop.rect().width() - self.hint.width()) // 2,
            desktop.rect().height() // 6,
        )
        self.hint.show()
        QApplication.processEvents()

    def get_rect(self):
        if self.start_pos is None or self.end_pos is None:
            return None
        x1, y1 = self.start_pos.x(), self.start_pos.y()
        x2, y2 = self.end_pos.x(), self.end_pos.y()
        x = min(x1, x2)
        y = min(y1, y2)
        w = abs(x2 - x1)
        h = abs(y2 - y1)
        if w < 10 or h < 10:
            return None
        return (x, y, w, h)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        r = self.get_rect()
        if r:
            x, y, w, h = r
            pen = QPen(QColor(0, 200, 255), 3, Qt.SolidLine)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(x, y, w, h)
            # 選區內稍微挖空顯示（用較淺色框出選區）
            painter.setPen(QPen(QColor(255, 255, 255), 1, Qt.DashLine))
            painter.drawRect(x + 2, y + 2, w - 4, h - 4)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()
            self.end_pos = event.pos()
            self.update()

    def mouseMoveEvent(self, event):
        if self.start_pos is not None:
            self.end_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.start_pos is not None:
            self.end_pos = event.pos()
            r = self.get_rect()
            self.start_pos = None
            self.end_pos = None
            if r:
                self.region_selected.emit(*r)
            self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.start_pos = None
            self.end_pos = None
            self.close()


# --- 熱鍵監聽執行緒 ---
# 熱鍵對應表（供下拉選單與監聽使用）
HOTKEY_KEYS = [
    (keyboard.Key.f8, "F8"),
    (keyboard.Key.f9, "F9"),
    (keyboard.Key.f10, "F10"),
    (keyboard.Key.f11, "F11"),
    (keyboard.Key.f12, "F12"),
]


class HotkeyListenerThread(QThread):
    """在背景監聽全域熱鍵，觸發時發送訊號。"""
    hotkey_pressed = pyqtSignal()

    def __init__(self, hotkey_index=0):
        super().__init__()
        self.hotkey_index = hotkey_index
        self._listener = None
        self._running = False

    def set_hotkey_index(self, index):
        self.hotkey_index = max(0, min(index, len(HOTKEY_KEYS) - 1))

    def run(self):
        self._running = True
        with keyboard.Listener(on_press=self._on_press) as self._listener:
            self._listener.join()

    def _on_press(self, key):
        if not self._running:
            return
        try:
            target = HOTKEY_KEYS[self.hotkey_index][0]
            if key == target:
                self.hotkey_pressed.emit()
        except (AttributeError, IndexError):
            pass

    def stop(self):
        self._running = False
        if self._listener:
            self._listener.stop()


# --- 主視窗 ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.region = None  # (x, y, w, h)
        self.save_folder = os.path.expanduser("~/Pictures")
        self.hotkey_thread = None
        self.selector = RegionSelector()
        self.selector.region_selected.connect(self.on_region_selected)
        self.setup_ui()
        self.start_hotkey_listener()

    def setup_ui(self):
        self.setWindowTitle("ZoneShot")
        self.setMinimumSize(400, 320)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 區域設定
        grp_region = QGroupBox("截圖區域")
        grp_layout = QVBoxLayout(grp_region)
        self.btn_select_region = QPushButton("拖曳設定截圖區域")
        self.btn_select_region.setMinimumHeight(44)
        self.btn_select_region.clicked.connect(self.open_region_selector)
        grp_layout.addWidget(self.btn_select_region)
        self.lbl_region = QLabel("尚未設定區域（請按上方按鈕後在螢幕上拖曳選取）")
        self.lbl_region.setWordWrap(True)
        self.lbl_region.setStyleSheet("color: #666;")
        grp_layout.addWidget(self.lbl_region)
        layout.addWidget(grp_region)

        # 熱鍵
        grp_hotkey = QGroupBox("截圖熱鍵")
        hotkey_layout = QHBoxLayout(grp_hotkey)
        hotkey_layout.addWidget(QLabel("按鍵："))
        self.hotkey_combo = QComboBox()
        for _, name in HOTKEY_KEYS:
            self.hotkey_combo.addItem(name)
        hotkey_layout.addWidget(self.hotkey_combo)
        hotkey_layout.addWidget(QLabel("（程式在背景時也可觸發）"))
        hotkey_layout.addStretch()
        layout.addWidget(grp_hotkey)

        # 儲存路徑
        grp_save = QGroupBox("儲存位置")
        save_layout = QVBoxLayout(grp_save)
        self.lbl_save_path = QLabel(self.save_folder)
        self.lbl_save_path.setWordWrap(True)
        save_layout.addWidget(self.lbl_save_path)
        btn_browse = QPushButton("選擇資料夾")
        btn_browse.clicked.connect(self.choose_save_folder)
        save_layout.addWidget(btn_browse)
        layout.addWidget(grp_save)

        # 說明
        hint = QLabel("設定好區域後，按下熱鍵即可截圖並儲存。")
        hint.setStyleSheet("color: #555; font-size: 12px;")
        layout.addWidget(hint)
        layout.addStretch()

    def open_region_selector(self):
        self.hide()
        QApplication.processEvents()
        self.selector.show_fullscreen()

    def on_region_selected(self, x, y, w, h):
        self.region = (x, y, w, h)
        self.lbl_region.setText(f"已設定：X={x}, Y={y}, 寬={w}, 高={h}")
        self.lbl_region.setStyleSheet("color: #0a0;")
        self.show()
        self.raise_()
        self.activateWindow()

    def choose_save_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "選擇儲存資料夾", self.save_folder)
        if folder:
            self.save_folder = folder
            self.lbl_save_path.setText(self.save_folder)

    def start_hotkey_listener(self):
        idx = self.hotkey_combo.currentIndex()
        self.hotkey_thread = HotkeyListenerThread(idx)
        self.hotkey_thread.hotkey_pressed.connect(self.capture_region)
        self.hotkey_thread.start()
        self.hotkey_combo.currentIndexChanged.connect(self._on_hotkey_changed)

    def _on_hotkey_changed(self, index):
        if self.hotkey_thread and self.hotkey_thread.isRunning():
            self.hotkey_thread.set_hotkey_index(index)

    def capture_region(self):
        if not self.region:
            return
        x, y, w, h = self.region
        # 使用 PIL 截圖（座標為螢幕絕對座標）
        bbox = (x, y, x + w, y + h)
        img = ImageGrab.grab(bbox=bbox)
        name = datetime.now().strftime("screenshot_%Y%m%d_%H%M%S.png")
        path = os.path.join(self.save_folder, name)
        try:
            img.save(path)
            # 可選：顯示提示（若主視窗存在）
            if self.isVisible():
                QMessageBox.information(self, "截圖完成", f"已儲存至：\n{path}")
        except Exception as e:
            if self.isVisible():
                QMessageBox.warning(self, "儲存失敗", str(e))

    def closeEvent(self, event):
        if self.hotkey_thread and self.hotkey_thread.isRunning():
            self.hotkey_thread.stop()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
