import os
import sys
from enum import Enum

import keyboard
import mss
import mss.tools
import win32clipboard
from PIL import Image
from PyQt5.QtCore import Qt, QTimer, QPoint, QBuffer
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QIcon, QPen, QPainterPath
from PyQt5.QtWidgets import QMainWindow, QApplication, QSystemTrayIcon, QGridLayout

from main_canvas import ScreenShotCanvas
from rectangle_drawer import RectangleDrawer



class MouseAction(Enum):
    Select = 'select'
    Pencil = 'pencil'
    Line = 'line'
    Rectangle = 'rectangle'


class ScreenshotApp(QMainWindow):

    def __init__(self):
        super().__init__()

        self.action = MouseAction.Select.value

        self.pencil_drawing = False
        self.pencil_points = []

        self.line_drawing = False
        self.line_points = []

        self.current_path = None

        self.current_line = None
        self.line_start = None # При mouse move постоянно перемешаемся туда

        self.current_rect = None
        self.rect_start = None

        self.drawing_buffer = QPixmap()


        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('tray_icon.ico'))
        self.tray_icon.activated.connect(self.make_screenshot)
        self.tray_icon.show()

        self.screenshot_label = ScreenShotCanvas(self)
        self.screenshot_label.tools_signal.connect(self.change_action)
        self.screenshot_label.tools_panel.hide()
        self.screenshot_image = None

        self.is_screening = False
        self.rect_drawer = RectangleDrawer(self.screenshot_label)

        layout = QGridLayout()
        layout.addWidget(self.screenshot_label, 0, 0)

        self.setLayout(layout)

        keyboard.add_hotkey('f3', self.make_screenshot)
        keyboard.add_hotkey('esc', self.close_screenshot)
        keyboard.add_hotkey('ctrl + c', self.clip_screenshot)

    def make_screenshot(self):
        self.screenshot_label.show()
        self.rect_drawer.enable = True
        self.is_screening = True
        self.drawing_buffer = QPixmap()
        self.current_path = None
        self.current_line = None
        self.current_rect = None
        self.screenshot_label.tools_panel.hide()
        self.screenshot_label.tools_panel.clear_action()

        with mss.mss() as sct:
            monitors = sct.monitors[1]
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
        self.show()

    def save_screenshot(self):
        print('Сохранено в буфер обмена')

    def close_screenshot(self):
        if not self.is_screening:
            return
        self.rect_drawer.clear()
        self.screenshot_label.tools_panel.clear_action()
        # self.screenshot_label.tools_panel.hide()
        self.action = MouseAction.Select.value
        self.is_screening = False
        self.screenshot_label.clear()
        self.hide()
        # Очищаем ресурсы
        if hasattr(self, 'screenshot_image'):
            del self.screenshot_image


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

        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)

        if hasattr(self, 'screenshot_image') and self.screenshot_image:
            screenshot_qimage = QImage(
                self.screenshot_image.tobytes(),
                self.screenshot_image.width,
                self.screenshot_image.height,
                QImage.Format_RGB888
            )
            painter.drawImage(0, 0, screenshot_qimage)

        if not self.drawing_buffer.isNull():
            painter.drawPixmap(0, 0, self.drawing_buffer)

        if self.current_path:
            painter.setPen(QPen(QColor(255, 0, 0), 3))
            painter.drawPath(self.current_path)

        if self.current_line:
            painter.setPen(QPen(QColor(255, 0, 0), 3))
            painter.drawPath(self.current_line)

        painter.end()

        cropped_pixmap = pixmap.copy(x, y, w, h)
        cropped_image = cropped_pixmap.toImage()
        cropped_image = cropped_image.convertToFormat(QImage.Format_RGB32)


        buffer = QBuffer()
        buffer.open(QBuffer.ReadWrite)
        cropped_image.save(buffer, "BMP")

        data = buffer.data()[14:]
        buffer.close()

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()

        self.close_screenshot()
        self.show_screenshot_notification()

    def change_action(self, action):
        self.action = action

    def is_cursor_in_tools_panel(self, pos):
        """Проверяет, находится ли курсор в области панели инструментов"""
        if not self.screenshot_label.tools_panel.isVisible():
            return False

        tools_geometry = self.screenshot_label.tools_panel.geometry()
        return tools_geometry.contains(pos)

    def mouseDoubleClickEvent(self, event):
        match self.action:
            case MouseAction.Select.value:
                if self.rect_drawer.enable:
                    self.rect_drawer.mouse_double_click(event)
            case MouseAction.Pencil.value:
                pass
            case MouseAction.Line.value:
                pass
            case MouseAction.Rectangle.value:
                pass

    def mousePressEvent(self, event):
        match self.action:
            case MouseAction.Select.value:
                if self.rect_drawer.enable:
                    self.rect_drawer.mouse_press(event)
                    self.update()
            case MouseAction.Pencil.value:
                self.current_path = QPainterPath()
                self.current_path.moveTo(event.pos())
            case MouseAction.Line.value:
                self.current_line = QPainterPath()
                self.current_line.moveTo(event.pos())
                self.line_start = event.pos()
            case MouseAction.Rectangle.value:
                self.current_rect = QPainterPath()
                self.rect_start = event.pos()

    def mouseMoveEvent(self, event):
        match self.action:
            case MouseAction.Select.value:
                if self.rect_drawer.enable:
                    self.rect_drawer.mouse_move(event)
                    self.update()

                if self.rect_drawer.current_rect:
                    # self.screenshot_label.tools_panel.show()
                    self.screenshot_label.tools_panel.move(QPoint(self.rect_drawer.current_rect.right(), self.rect_drawer.current_rect.bottom() - 680))
            case MouseAction.Pencil.value:
                if self.current_path:
                    self.current_path.lineTo(event.pos())
                    self.update()
            case MouseAction.Line.value:
                if self.current_line:
                    self.current_line = QPainterPath()
                    self.current_line.moveTo(self.line_start)
                    self.current_line.lineTo(event.pos())
                    self.update()
            case MouseAction.Rectangle.value:
                if self.current_rect:
                    self.current_rect = QPainterPath()
                    self.current_rect.addRect(self.rect_start.x(), self.rect_start.y(), event.pos().x() - self.rect_start.x(), event.pos().y() - self.rect_start.y())
                    print(self.rect_start.x(), self.rect_start.y(), event.pos().x(), event.pos().y())
                    self.update()

    def mouseReleaseEvent(self, event):
        match self.action:
            case MouseAction.Select.value:
                if self.rect_drawer.enable:
                    self.rect_drawer.mouse_release(event)
                    self.update()

                    if self.rect_drawer.current_rect:
                        self.screenshot_label.tools_panel.show()
                        self.screenshot_label.tools_panel.qpoint_panel = QPoint(self.rect_drawer.current_rect.right(), self.rect_drawer.current_rect.bottom() - 680)
                        self.screenshot_label.tools_panel.move(self.screenshot_label.tools_panel.qpoint_panel)
            case MouseAction.Pencil.value:
                if self.current_path:
                    self.finalize_drawing(self.current_path)
                    # self.current_path = None
                self.pencil_drawing = False
            case MouseAction.Line.value:
                if self.current_line:
                    self.finalize_drawing(self.current_line)
                self.line_drawing = False
            case MouseAction.Rectangle.value:
                if self.current_rect:
                    self.finalize_drawing(self.current_rect)

    def finalize_drawing(self, path):
        if not self.drawing_buffer.size().isValid():
            self.drawing_buffer = QPixmap(self.size())
            self.drawing_buffer.fill(Qt.transparent)

        temp = self.drawing_buffer.copy()
        self.drawing_buffer = QPixmap(self.size())
        self.drawing_buffer.fill(Qt.transparent)

        buffer_painter = QPainter(self.drawing_buffer)
        buffer_painter.drawPixmap(0, 0, temp)
        buffer_painter.setPen(QPen(QColor(255, 0, 0), 3))
        buffer_painter.drawPath(path)
        buffer_painter.end()

    def paintEvent(self, event):
        if self.rect_drawer.enable:
            super().paintEvent(event)
            painter = QPainter(self)
            self.rect_drawer.paint(painter)

        painter_drawing = QPainter(self)
        if not self.drawing_buffer.isNull():
            painter_drawing.drawPixmap(0, 0, self.drawing_buffer)

        if self.current_path:
            painter_drawing.setPen(QPen(QColor(255, 0, 0), 3))
            painter_drawing.drawPath(self.current_path)

        if self.current_line:
            painter_drawing.setPen(QPen(QColor(255, 0, 0), 3))
            painter_drawing.drawPath(self.current_line)

        if self.current_rect:
            painter_drawing.setPen(QPen(QColor(255, 0, 0), 3))
            painter_drawing.drawPath(self.current_rect)

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
