import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QListWidget
from PyQt6.QtCore import Qt


class TestWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Drag and Drop Test")
        self.setGeometry(100, 100, 300, 200)

        layout = QVBoxLayout()
        self.list_widget = QListWidget(self)
        self.list_widget.setAcceptDrops(True)
        self.list_widget.setDragEnabled(True)  # ドラッグも許可
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

        self.list_widget.dragEnterEvent = self.dragEnterEvent
        self.list_widget.dropEvent = self.dropEvent

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        for url in urls:
            file_path = url.toLocalFile()
            self.list_widget.addItem(file_path)
        event.acceptProposedAction()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = TestWidget()
    ex.show()
    sys.exit(app.exec())
