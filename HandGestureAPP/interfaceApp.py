import sys
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QMenuBar, QMenu, QAction, QHBoxLayout, QMainWindow
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, QPropertyAnimation, QRect, Qt
import cv2


# Segunda versão da interface
class HandGestureRPSAPP(QMainWindow):
    def __init__(self):
        super().__init__()
        self.iniciar_ui()
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.atualizar_frame)

    def iniciar_ui(self):
        self.setWindowTitle("HandGestureRPS")
        self.setGeometry(100, 100, 900, 700)
        
        self.bar_menu = self.menuBar()
        
        menu_jogo = QMenu("Jogo", self)
        self.bar_menu.addMenu(menu_jogo)
        
        acao_modo_jogo = QAction("Escolher Modo de Jogo", self)
        menu_jogo.addAction(acao_modo_jogo)
        acao_modo_jogo.triggered.connect(self.mostrar_modos_de_jogo)
        
        menu_opcoes = QMenu("Opções", self)
        self.bar_menu.addMenu(menu_opcoes)
        
        acao_config = QAction("Configurações", self)
        menu_opcoes.addAction(acao_config)
        acao_config.triggered.connect(self.mostrar_configuracoes)

        self.setStyleSheet(
            "background: qlineargradient(spread:pad, x1:0.5, y1:0, x2:0.5, y2:1, stop:0 #4e54c8, stop:1 #8f94fb);"
        )

        self.rotulo_video = QLabel(self)
        self.rotulo_video.setFixedSize(640, 480)
        self.rotulo_video.setStyleSheet(
            "border: 5px solid #16a085; border-radius: 10px; background-color: white;"
        )

        self.rotulo_resultado = QLabel("Resultado: ")
        self.rotulo_resultado.setStyleSheet(
            """
            font-size: 24px; 
            font-weight: bold; 
            color: #ffffff;
            background-color: rgba(0, 0, 0, 0.4); 
            padding: 10px; 
            border-radius: 10px;
            """
        )

        self.rotulo_computador = QLabel("Computador: ")
        self.rotulo_computador.setStyleSheet(
            """
            font-size: 20px; 
            color: #ecf0f1; 
            background-color: rgba(0, 0, 0, 0.4); 
            padding: 8px; 
            border-radius: 8px;
            """
        )

        self.rotulo_placar = QLabel("Vitórias: 0 | Derrotas: 0 | Empates: 0")
        self.rotulo_placar.setStyleSheet(
            """
            font-size: 18px; 
            color: #bdc3c7; 
            background-color: rgba(0, 0, 0, 0.4); 
            padding: 8px; 
            border-radius: 8px;
            """
        )

        self.botao_iniciar = QPushButton("Iniciar Jogo")
        self.botao_iniciar.setStyleSheet(
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
        self.botao_iniciar.clicked.connect(self.iniciar_jogo)

        self.botao_sair = QPushButton("Sair")
        self.botao_sair.setStyleSheet(
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
        self.botao_sair.clicked.connect(self.close)

        layout = QVBoxLayout()
        layout.addWidget(self.rotulo_video, alignment=Qt.AlignCenter)
        layout.addWidget(self.rotulo_resultado, alignment=Qt.AlignCenter)
        layout.addWidget(self.rotulo_computador, alignment=Qt.AlignCenter)
        layout.addWidget(self.rotulo_placar, alignment=Qt.AlignCenter)
        layout.addWidget(self.botao_iniciar, alignment=Qt.AlignCenter)
        layout.addWidget(self.botao_sair, alignment=Qt.AlignCenter)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        widget_central = QWidget()
        widget_central.setLayout(layout)
        self.setCentralWidget(widget_central)

    def iniciar_jogo(self):
        self.timer.start(30)
        self.animar_rotulo(self.rotulo_resultado)

    def animar_rotulo(self, rotulo):
        animacao = QPropertyAnimation(rotulo, b"geometry")
        animacao.setDuration(600)
        animacao.setStartValue(QRect(rotulo.x(), rotulo.y(), rotulo.width(), rotulo.height()))
        animacao.setEndValue(QRect(rotulo.x(), rotulo.y() - 10, rotulo.width(), rotulo.height()))
        animacao.setLoopCount(4)
        animacao.start()

    def atualizar_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        altura, largura, canal = frame.shape
        bytes_por_linha = canal * largura
        imagem_qt = QImage(frame.data, largura, altura, bytes_por_linha, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(imagem_qt)
        self.rotulo_video.setPixmap(pixmap)

    def mostrar_modos_de_jogo(self):
        print("Modo de Jogo Selecionado")

    def mostrar_configuracoes(self):
        print("Configurações do Jogo")

    def closeEvent(self, event):
        self.cap.release()
        cv2.destroyAllWindows()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = HandGestureRPSAPP()
    janela.show()
    sys.exit(app.exec_())
