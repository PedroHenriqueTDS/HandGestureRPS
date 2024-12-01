import sys
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QMenuBar, QMenu, QAction, QHBoxLayout, QMainWindow
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, QPropertyAnimation, QRect, Qt
import cv2


class HandGestureRPSAPP(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

    def init_ui(self):
        self.setWindowTitle("HandGestureRPS")
        self.setGeometry(100, 100, 900, 700)
        
        # Menu Bar
        self.menu_bar = self.menuBar()
        
        # Criar o menu 'Jogo'
        jogo_menu = QMenu("Jogo", self)
        self.menu_bar.addMenu(jogo_menu)
        
        # Adicionar modos de jogo no menu 'Jogo'
        modo_jogo_action = QAction("Escolher Modo de Jogo", self)
        jogo_menu.addAction(modo_jogo_action)
        modo_jogo_action.triggered.connect(self.show_game_modes)
        
        # Criar o menu 'Opções'
        opcoes_menu = QMenu("Opções", self)
        self.menu_bar.addMenu(opcoes_menu)
        
        # Adicionar opções ao menu 'Opções'
        config_action = QAction("Configurações", self)
        opcoes_menu.addAction(config_action)
        config_action.triggered.connect(self.show_configurations)

        # Alterado o gradiente de fundo
        self.setStyleSheet(
            "background: qlineargradient(spread:pad, x1:0.5, y1:0, x2:0.5, y2:1, stop:0 #4e54c8, stop:1 #8f94fb);"
        )

        # Video Label
        self.video_label = QLabel(self)
        self.video_label.setFixedSize(640, 480)
        self.video_label.setStyleSheet(
            "border: 5px solid #16a085; border-radius: 10px; background-color: white;"
        )

        # Result Labels
        self.resultado_label = QLabel("Resultado: ")
        self.resultado_label.setStyleSheet(
            """
            font-size: 24px; 
            font-weight: bold; 
            color: #ffffff;
            background-color: rgba(0, 0, 0, 0.4); 
            padding: 10px; 
            border-radius: 10px;
            """
        )

        self.computador_label = QLabel("Computador: ")
        self.computador_label.setStyleSheet(
            """
            font-size: 20px; 
            color: #ecf0f1; 
            background-color: rgba(0, 0, 0, 0.4); 
            padding: 8px; 
            border-radius: 8px;
            """
        )

        self.placar_label = QLabel("Vitórias: 0 | Derrotas: 0 | Empates: 0")
        self.placar_label.setStyleSheet(
            """
            font-size: 18px; 
            color: #bdc3c7; 
            background-color: rgba(0, 0, 0, 0.4); 
            padding: 8px; 
            border-radius: 8px;
            """
        )

        # Buttons
        self.start_button = QPushButton("Iniciar Jogo")
        self.start_button.setStyleSheet(
            """
            QPushButton {
                font-size: 20px; 
                padding: 12px 24px; 
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #1d976c, stop:1 #93f9b9); 
                color: white; 
                border: none; 
                border-radius: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #93f9b9, stop:1 #1d976c);
            }
            QPushButton:pressed {
                background-color: #16a085;
            }
            """
        )
        self.start_button.clicked.connect(self.start_game)

        self.quit_button = QPushButton("Sair")
        self.quit_button.setStyleSheet(
            """
            QPushButton {
                font-size: 20px; 
                padding: 12px 24px; 
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #f953c6, stop:1 #b91d73); 
                color: white; 
                border: none; 
                border-radius: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #b91d73, stop:1 #f953c6);
            }
            QPushButton:pressed {
                background-color: #8e44ad;
            }
            """
        )
        self.quit_button.clicked.connect(self.close)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.video_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.resultado_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.computador_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.placar_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.start_button, alignment=Qt.AlignCenter)
        layout.addWidget(self.quit_button, alignment=Qt.AlignCenter)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def start_game(self):
        self.timer.start(30)
        self.animate_label(self.resultado_label)

    def animate_label(self, label):
        animation = QPropertyAnimation(label, b"geometry")
        animation.setDuration(600)
        animation.setStartValue(QRect(label.x(), label.y(), label.width(), label.height()))
        animation.setEndValue(QRect(label.x(), label.y() - 10, label.width(), label.height()))
        animation.setLoopCount(4)
        animation.start()

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

    def show_game_modes(self):
        # Função para mostrar modos de jogo
        print("Modo de Jogo Selecionado")

    def show_configurations(self):
        # Função para exibir configurações
        print("Configurações do Jogo")

    def closeEvent(self, event):
        self.cap.release()
        cv2.destroyAllWindows()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HandGestureRPSAPP()
    window.show()
    sys.exit(app.exec_()