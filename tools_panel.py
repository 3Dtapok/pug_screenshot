from PyQt5.QtCore import pyqtSignal, QPoint
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QGraphicsGridLayout, QGridLayout


class PanelTools(QWidget):
    change_action = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.action = None

        self.button_style_main = """
        QPushButton {
            background-color: rgba(100, 100, 100, 50);
            min-width: 50px;
            min-height: 50px;
            border-radius: 10px;
        }
        
        QPushButton:hover {
            background-color: rgba(180, 180, 180, 50);
        }
        
        QPushButton:pressed {
            background-color: rgba(255, 255, 255, 50);
        }
        
        QPushButton:checked {
            background-color: rgba(235, 235, 235, 50);
        }
        
        QPushButton:checked:hover {
            background-color: rgba(235, 235, 235, 50);
        }
        
        QPushButton:checked:pressed {
            background-color: rgba(255, 255, 255, 50);
        }
        """


        self.setStyleSheet(self.button_style_main)
        self.qpoint_panel = QPoint()

        self.btn_pencil = QPushButton()
        self.btn_pencil.setCheckable(True)
        self.btn_pencil.setIcon(QIcon("tool_panel_icons/pen_icon.png"))
        self.btn_pencil.clicked.connect(lambda: self.change_mouse_action('pencil', self.btn_pencil))

        self.btn_line = QPushButton()
        self.btn_line.setCheckable(True)
        self.btn_line.setIcon(QIcon("tool_panel_icons/line_icon.png"))
        self.btn_line.clicked.connect(lambda: self.change_mouse_action('line', self.btn_line))

        self.btn_rectangle = QPushButton()
        self.btn_rectangle.setCheckable(True)
        self.btn_rectangle.setIcon(QIcon("tool_panel_icons/rectangle_icon.png"))
        self.btn_rectangle.clicked.connect(lambda: self.change_mouse_action('rectangle', self.btn_rectangle))

        self.menu_layout = QVBoxLayout()
        self.menu_layout.addWidget(self.btn_pencil)
        self.menu_layout.addWidget(self.btn_line)
        self.menu_layout.addWidget(self.btn_rectangle)

        layout = QGridLayout()
        layout.addLayout(self.menu_layout, 1, 1)
        self.setLayout(layout)
        self.setFixedWidth(70)

    def change_mouse_action(self, action, active_button):
        current_pos = self.pos()
        for button in [self.btn_pencil, self.btn_line, self.btn_rectangle]:
            if button != active_button:
                button.setChecked(False)

        if self.action != action:
            self.action = action
        else:
            self.action = None

        self.move(current_pos)
        self.change_action.emit(action)

    def clear_action(self):
        self.action = None
        # self.change_action.emit(self.action)


