import os
import sys

import keyboard
import mss
import mss.tools
import win32clipboard
from PIL import Image
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QIcon
from PyQt5.QtWidgets import QMainWindow, QApplication, QVBoxLayout, QLabel, QSystemTrayIcon
from isort import io

from rectangle_drawer import RectangleDrawer


class ScreenshotApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('tray_icon.ico'))
        self.tray_icon.activated.connect(self.make_screenshot)
        self.tray_icon.show()

        self.screenshot_label = QLabel(self)
        self.screenshot_image = None
        self.screenshot_label.setStyleSheet("background: transparent;")

        self.is_screening = False

        self.rect_drawer = RectangleDrawer(self.screenshot_label)

        layout = QVBoxLayout()

        layout.addWidget(self.screenshot_label)

        keyboard.add_hotkey('f3', self.make_screenshot)
        keyboard.add_hotkey('esc', self.close_screenshot)
        keyboard.add_hotkey('ctrl + c', self.clip_screenshot)

    def make_screenshot(self):
        self.screenshot_label.show()
        self.rect_drawer.enable = True
        self.is_screening = True
        with mss.mss() as sct:
            monitors = sct.monitors[0]
            screenshot = sct.grab(monitors)
            combined_rect = monitors

            # Получаем геометрию окна
            self.setGeometry(
                combined_rect['left'],
                combined_rect['top'],
                combined_rect['width'],
                combined_rect['height'],
            )

        self.screenshot_image = Image.frombytes(
            'RGB',
            screenshot.size,
            screenshot.rgb
        )
        self.show_screenshot(screenshot)

    def show_screenshot(self, screenshot):
        img = QImage(screenshot.rgb, screenshot.width, screenshot.height, QImage.Format_RGB888)

        # Делаем затемнение окна
        dark_img = QImage(img.size(), QImage.Format_ARGB32)
        dark_img.fill(QColor(0, 0, 0, 150))  # 180 = уровень затемнения

        painter = QPainter(dark_img)
        painter.setOpacity(0.5)
        painter.drawImage(0, 0, img)
        painter.end()

        # Отображаем в окне
        self.screenshot_label.setGeometry(0, 0, self.width(), self.height())
        self.screenshot_label.setPixmap(QPixmap.fromImage(dark_img))
        # self.screenshot_label.showFullScreen()

        # mss.tools.to_png(screenshot.rgb, screenshot.size, output="all_monitors_screenshot.png")

        self.show()

    def save_screenshot(self):
        print('Сохранено в буфер обмена')

    def close_screenshot(self):
        if not self.is_screening:
            return

        self.is_screening = False
        self.screenshot_label.clear()
        self.hide()
        # Очищаем ресурсы
        if hasattr(self, 'screenshot_image'):
            del self.screenshot_image
        self.rect_drawer.enable = False
        self.rect_drawer.clear()

    def clip_screenshot(self):
        if not self.is_screening:
            return

        rect = self.rect_drawer.current_rect
        x, y, w, h = (
            rect.x(),
            rect.y(),
            rect.width(),
            rect.height()
        )

        cropped_screenshot = self.screenshot_image.crop((x, y, x + w, y + h))

        output = io.BytesIO()

        cropped_screenshot.save(output, format='BMP')
        data = output.getvalue()[14:]  # Пропускаем заголовок BMP
        output.close()

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()


        self.close_screenshot()
        self.show_screenshot_notification()

        print('Скриншот скопирован в буфер обмена')

    def mouseDoubleClickEvent(self, event):
        if self.rect_drawer.enable:
            self.rect_drawer.mouse_double_click(event)

    def mousePressEvent(self, event):
        if self.rect_drawer.enable:
            self.rect_drawer.mouse_press(event)
            self.update()

    def mouseMoveEvent(self, event):
        if self.rect_drawer.enable:
            self.rect_drawer.mouse_move(event)
            self.update()

    def mouseReleaseEvent(self, event):
        if self.rect_drawer.enable:
            self.rect_drawer.mouse_release(event)
            self.update()

    def paintEvent(self, event):
        if self.rect_drawer.enable:
            super().paintEvent(event)
            painter = QPainter(self)
            self.rect_drawer.paint(painter)

    def show_screenshot_notification(self, is_cropped=False):
        tray = QSystemTrayIcon(self)

        # Установите иконку (если есть)
        if os.path.exists("screenshot_icon.ico"):
            tray.setIcon(QIcon("screenshot_icon.ico"))
        else:
            tray.setIcon(QApplication.windowIcon())
        tray.show()
        tray.showMessage(
            "Скриншот сохранён в буфер!",
            "Область экрана скопирована.",
            QSystemTrayIcon.Information,
            3000  # 3 секунды
        )
        # Автоматически удаляем иконку после показа
        QTimer.singleShot(3000, tray.hide)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    main_window = ScreenshotApp()
    main_window.show()
    sys.exit(app.exec_())
