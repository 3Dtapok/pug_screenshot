from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel


class MainMenu(QWidget):
    def __init__(self):
        super().__init__()

        settings = Settings()
        config = settings.get_config()

        self.setWindowTitle('Настройки')

        layout = QVBoxLayout()

        layout.addWidget(QLabel())
