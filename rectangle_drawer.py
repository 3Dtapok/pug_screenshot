from PyQt5.QtCore import QRect, QPoint
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


class RectangleDrawer:
    def __init__(self, widget):
        self.widget = widget

        self.start_pos = 0
        self.end_pos = 0
        self.dragging = False
        self.moving_rect = False
        self.resizing = True
        self.current_rect = None
        self.drag_offset = None
        self.resize_side = None

        self.margin = 8 # pixels

        self.widget.setMouseTracking(True)
        self.enable = True

    def clear(self):
        self.start_pos = 0
        self.end_pos = 0
        self.dragging = False
        self.moving_rect = False
        self.resizing = True
        self.current_rect = None
        self.drag_offset = None
        self.resize_side = None

        self.margin = 8  # pixels

    def get_resize_side(self, pos):
        rect = self.current_rect

        # Сначала проверяем углы (они имеют приоритет)
        corners = {
            'top_left': QRect(rect.left(), rect.top(), self.margin, self.margin),
            'top_right': QRect(rect.right() - self.margin, rect.top(), self.margin, self.margin),
            'bottom_left': QRect(rect.left(), rect.bottom() - self.margin, self.margin, self.margin),
            'bottom_right': QRect(rect.right() - self.margin, rect.bottom() - self.margin, self.margin, self.margin)
        }

        for corner, area in corners.items():
            if area.contains(pos):
                return corner

        # Затем проверяем стороны (только если не попали в угол)
        sides = {
            'top': QRect(rect.left() + self.margin, rect.top(), rect.width() - 2 * self.margin, self.margin),
            'bottom': QRect(rect.left() + self.margin, rect.bottom() - self.margin, rect.width() - 2 * self.margin, self.margin),
            'left': QRect(rect.left(), rect.top() + self.margin, self.margin, rect.height() - 2 * self.margin),
            'right': QRect(rect.right() - self.margin, rect.top() + self.margin, self.margin, rect.height() - 2 * self.margin)
        }

        for side, area in sides.items():
            if area.contains(pos):
                return side

        return None

    def mouse_double_click(self, event):
        if event.button() == Qt.LeftButton:
            if self.current_rect and self.current_rect.contains(event.pos()):
                self.current_rect = self.widget.rect()
                self.widget.update()
    def mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            if self.current_rect and self.current_rect.contains(event.pos()):
                inner_rect = self.current_rect.adjusted(self.margin, self.margin, - self.margin, - self.margin)
                if not inner_rect.contains(event.pos()):
                    self.resize_side = self.get_resize_side(event.pos())
                    self.resizing = True
                else:
                    self.drag_offset = event.pos() - self.current_rect.topLeft()
                    self.moving_rect = True
            else:
                self.start_pos = event.pos()
                self.end_pos = event.pos()
                self.dragging = True
                self.current_rect = QRect(self.start_pos, self.end_pos)

        elif event.button() == Qt.RightButton and self.current_rect:
            self.current_rect = None
            self.widget.update()

    def mouse_move(self, event):
        if self.dragging:
            self.end_pos = event.pos()
            self.current_rect = QRect(
                min(self.start_pos.x(), self.end_pos.x()),
                min(self.start_pos.y(), self.end_pos.y()),
                abs(self.start_pos.x() - self.end_pos.x()),
                abs(self.start_pos.y() - self.end_pos.y())
            )
            self.widget.update()
        elif self.moving_rect and self.current_rect:
            new_pos = event.pos() - self.drag_offset
            screen_rect = self.widget.rect()
            new_pos.setX(max(0, min(new_pos.x(), screen_rect.width() - self.current_rect.width())))
            new_pos.setY(max(0, min(new_pos.y(), screen_rect.height() - self.current_rect.height())))

            self.current_rect.moveTo(new_pos)
            self.widget.update()
        elif self.resizing and self.resize_side:
            self.resize_rect(event.pos())

    def resize_rect(self, pos):
        old = self.current_rect
        new = QRect(old)

        match self.resize_side:
            case 'top':
                new_y = pos.y()
                old_y = new.bottom()
                if new_y > old_y:
                    self.resize_side = 'bottom'
                else:
                    new.setTop(new_y)
            case 'bottom':
                new_y = pos.y()
                old_y = new.top()
                if new_y < old_y:
                    self.resize_side = 'top'
                else:
                    new.setBottom(new_y)
            case 'left':
                new_x = pos.x()
                old_x = new.right()
                if new_x > old_x:
                    self.resize_side = 'right'
                else:
                    new.setLeft(new_x)
            case 'right':
                new_x = pos.x()
                old_x = new.left()
                if new_x < old_x:
                    self.resize_side = 'left'
                else:
                    new.setRight(new_x)

                if new.width() < 0:
                    new.setLeft(new.right())
            case 'top_left':
                new.setTopLeft(pos)

                new_x = pos.x()
                old_x = new.left()
                new_y = pos.y()
                old_y = new.bottom()

                if new_x > old_x or new_y > old_y:
                    self.resize_side = 'bottom_right'

            case 'top_right':
                new.setTopRight(pos)

                new_x = pos.x()
                old_x = new.right()
                new_y = pos.y()
                old_y = new.bottom()

                if new_x > old_x or new_y > old_y:
                    self.resize_side = 'bottom_left'

            case 'bottom_left':
                new.setBottomLeft(pos)

                new_x = pos.x()
                old_x = new.right()
                new_y = pos.y()
                old_y = new.bottom()

                if new_x > old_x or new_y > old_y:
                    self.resize_side = 'top_right'
            case 'bottom_right':
                new.setBottomRight(pos)

                new_x = pos.x()
                old_x = new.left()
                new_y = pos.y()
                old_y = new.bottom()

                if new_x < old_x or new_y < old_y:
                    self.resize_side = 'top_left'

        self.current_rect = new

    def mouse_release(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.moving_rect = False

    def paint(self, painter):
        if self.current_rect:
            painter.setPen(QColor(220, 190, 230, 120))
            painter.setBrush(QColor(220, 190, 230, 120))
            painter.drawRect(self.current_rect)


    def get_selection(self):
        return self.current_rect


