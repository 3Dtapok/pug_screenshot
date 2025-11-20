from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QLabel, QVBoxLayout

from tools_panel import PanelTools


class ScreenShotCanvas(QLabel):
    tools_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.screenshot_image = None
        self.is_screening = False

        self.tools_panel = PanelTools()
        self.tools_panel.change_action.connect(self.tools_signal.emit)

        layout = QVBoxLayout()
        layout.addWidget(self.tools_panel)
        self.setLayout(layout)


