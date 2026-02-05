import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QListWidget, QPushButton, QSplitter
)
from PySide6.QtCore import Qt, QTimer, QDateTime

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Motherload")
        self.resize(1400, 900)

        root = QWidget()
        self.setCentralWidget(root)

        # Left: Agent panel
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("Agent (chat + actions rapides)"))
        left_layout.addWidget(QListWidget())
        left_layout.addWidget(QPushButton("Run: Data Mining (Legal)"))
        left_layout.addWidget(QPushButton("Daily 3 papers (preview)"))

        # Center: News + Stats + Notes/Calendar/Todo placeholders
        center = QWidget()
        center_layout = QVBoxLayout(center)
        self.clock = QLabel("")
        self.clock.setAlignment(Qt.AlignRight)
        center_layout.addWidget(self.clock)

        center_layout.addWidget(QLabel("News / Daily Briefing (3 papers)"))
        center_layout.addWidget(QListWidget())

        center_layout.addWidget(QLabel("Notes (liées aux PDFs)"))
        center_layout.addWidget(QListWidget())

        # Right: Task board
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(QLabel("Task Board / Projects"))
        right_layout.addWidget(QListWidget())
        right_layout.addWidget(QPushButton("Add task"))

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(center)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)

        layout = QHBoxLayout(root)
        layout.addWidget(splitter)

        # Simple clock tick
        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(1000)
        self._tick()

    def _tick(self):
        self.clock.setText(QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss"))

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
