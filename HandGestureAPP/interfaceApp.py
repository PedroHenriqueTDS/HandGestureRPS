import sys
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
import cv2


class HandGestureRPSAPP(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

    def init_ui(self):
        self.setWindowTitle("HandGestureRPS")
        self.setGeometry(100, 100, 800, 600)

        self.video_label = QLabel(self)
        self.video_label.setFixedSize(640, 480)

        self.resultado_label = QLabel("Resultado: ")
        self.resultado_label.setStyleSheet("font-size: 16px;")

        self.computador_label = QLabel("Computador: ")
        self.computador_label.setStyleSheet("font-size: 16px;")

        self.placar_label = QLabel("Vitórias: 0 | Derrotas: 0 | Empates: 0")
        self.placar_label.setStyleSheet("font-size: 16px;")

        self.start_button = QPushButton("Iniciar Jogo")
        self.start_button.clicked.connect(self.start_game)

        self.quit_button = QPushButton("Sair")
        self.quit_button.clicked.connect(self.close)

        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        layout.addWidget(self.resultado_label)
        layout.addWidget(self.computador_label)
        layout.addWidget(self.placar_label)
        layout.addWidget(self.start_button)
        layout.addWidget(self.quit_button)

        self.setLayout(layout)

    def start_game(self):
        self.timer.start(30)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        height, width, channel = frame.shape
        bytes_per_line = channel * width
        qt_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        self.video_label.setPixmap(pixmap)

    def closeEvent(self, event):
        self.cap.release()
        cv2.destroyAllWindows()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HandGestureRPSAPP()
    window.show()
    sys.exit(app.exec_())
