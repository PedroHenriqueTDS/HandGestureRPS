import sys
import cv2
import mediapipe as mp
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QMenu, QAction, QHBoxLayout, QMainWindow, QMessageBox, QDialog
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtCore import QTimer, Qt, QPropertyAnimation, QPoint
import random

class JanelaMenu(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Menu de Opções")
        self.setGeometry(100, 100, 400, 300)
        self.setStyleSheet("background-color: #34495e; color: white;")

        # Botões de opções
        self.botao_reiniciar = QPushButton("Reiniciar Jogo")
        self.botao_reiniciar.setFont(QFont("Arial", 16))
        self.botao_reiniciar.setStyleSheet(
            "background-color: #1abc9c; color: white; padding: 10px; border-radius: 10px;")
        self.botao_reiniciar.clicked.connect(self.reiniciar_jogo)

        self.botao_estatisticas = QPushButton("Estatísticas")
        self.botao_estatisticas.setFont(QFont("Arial", 16))
        self.botao_estatisticas.setStyleSheet(
            "background-color: #3498db; color: white; padding: 10px; border-radius: 10px;")
        self.botao_estatisticas.clicked.connect(self.mostrar_estatisticas)

        self.botao_sair = QPushButton("Sair do Jogo")
        self.botao_sair.setFont(QFont("Arial", 16))
        self.botao_sair.setStyleSheet(
            "background-color: #e74c3c; color: white; padding: 10px; border-radius: 10px;")
        self.botao_sair.clicked.connect(self.fechar_jogo)

        # Layout da janela
        layout = QVBoxLayout()
        layout.addWidget(self.botao_reiniciar)
        layout.addWidget(self.botao_estatisticas)
        layout.addWidget(self.botao_sair)

        self.setLayout(layout)

    def reiniciar_jogo(self):
        # Função para reiniciar o jogo
        janela.iniciar_rodada()
        self.accept()  # Fecha a janela do menu

    def mostrar_estatisticas(self):
        # Função para mostrar as estatísticas do jogo
        estatisticas = f"Vitórias: {janela.placar['Vitórias']}\n" \
                       f"Derrotas: {janela.placar['Derrotas']}\n" \
                       f"Empates: {janela.placar['Empates']}"
        QMessageBox.information(self, "Estatísticas", estatisticas)

    def fechar_jogo(self):
        # Função para sair do jogo
        janela.close()
        self.accept()


class HandGestureRPSApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.iniciar_ui()
        self.cap = cv2.VideoCapture(0)  # A câmera é ativada aqui
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.atualizar_frame)
        self.timer.start(30)  # Atualiza o frame da câmera a cada 30ms (~33fps)
        self.resultado = None
        self.placar = {"Vitórias": 0, "Derrotas": 0, "Empates": 0}

        # Inicializando MediaPipe para detecção de mãos
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)
        self.mp_draw = mp.solutions.drawing_utils

    def iniciar_ui(self):
        self.setWindowTitle("HandGestureRPS")
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet("background-color: #2c3e50; color: white;")

        # Menu
        self.bar_menu = self.menuBar()
        self.bar_menu.setStyleSheet("background-color: #34495e; color: white;")
        menu_jogo = QMenu("Jogo", self)
        self.bar_menu.addMenu(menu_jogo)
        acao_sair = QAction("Sair", self)
        menu_jogo.addAction(acao_sair)
        acao_sair.triggered.connect(self.close)

        # Botão de Regras
        acao_regras = QAction("Regras", self)
        menu_jogo.addAction(acao_regras)
        acao_regras.triggered.connect(self.exibir_regras)

        # Botão de Menu
        acao_menu = QAction("Menu", self)
        menu_jogo.addAction(acao_menu)
        acao_menu.triggered.connect(self.abrir_menu)

        # Feedback
        self.rotulo_video = QLabel(self)
        self.rotulo_video.setFixedSize(640, 480)
        self.rotulo_video.setStyleSheet("border: 5px solid #1abc9c; border-radius: 15px; background-color: #ecf0f1;")

        self.rotulo_contagem = QLabel("")
        self.rotulo_contagem.setAlignment(Qt.AlignCenter)
        self.rotulo_contagem.setFont(QFont("Arial", 40, QFont.Bold))
        self.rotulo_contagem.setStyleSheet("color: #e74c3c;")

        self.rotulo_resultado = QLabel("Bem-vindo ao HandGestureRPS!")
        self.rotulo_resultado.setAlignment(Qt.AlignCenter)
        self.rotulo_resultado.setFont(QFont("Arial", 20, QFont.Bold))
        self.rotulo_resultado.setStyleSheet("color: #1abc9c;")

        self.rotulo_placar = QLabel("Vitórias: 0 | Derrotas: 0 | Empates: 0")
        self.rotulo_placar.setAlignment(Qt.AlignCenter)
        self.rotulo_placar.setFont(QFont("Arial", 16))
        self.rotulo_placar.setStyleSheet("color: #f1c40f;")

        # Feedback Visual Animado
        self.feedback_animado = QLabel(self)
        self.feedback_animado.setAlignment(Qt.AlignCenter)
        self.feedback_animado.setFont(QFont("Arial", 30, QFont.Bold))
        self.feedback_animado.setStyleSheet("color: #f39c12;")
        self.feedback_animado.hide()

        # Botões
        self.botao_iniciar = QPushButton("Nova Rodada")
        self.botao_iniciar.setFont(QFont("Arial", 18))
        self.botao_iniciar.setStyleSheet(
            "background-color: #1abc9c; color: white; padding: 10px; border-radius: 10px;")
        self.botao_iniciar.clicked.connect(self.iniciar_rodada)

        self.botao_menu = QPushButton("Menu")
        self.botao_menu.setFont(QFont("Arial", 18))
        self.botao_menu.setStyleSheet(
            "background-color: #3498db; color: white; padding: 10px; border-radius: 10px;")
        self.botao_menu.clicked.connect(self.abrir_menu)

        self.botao_sair = QPushButton("Sair")
        self.botao_sair.setFont(QFont("Arial", 18))
        self.botao_sair.setStyleSheet(
            "background-color: #e74c3c; color: white; padding: 10px; border-radius: 10px;")
        self.botao_sair.clicked.connect(self.close)

        layout_botoes = QHBoxLayout()
        layout_botoes.addWidget(self.botao_iniciar)
        layout_botoes.addWidget(self.botao_menu)
        layout_botoes.addWidget(self.botao_sair)

        layout = QVBoxLayout()
        layout.addWidget(self.rotulo_video, alignment=Qt.AlignCenter)
        layout.addWidget(self.rotulo_contagem, alignment=Qt.AlignCenter)
        layout.addWidget(self.rotulo_resultado, alignment=Qt.AlignCenter)
        layout.addWidget(self.rotulo_placar, alignment=Qt.AlignCenter)
        layout.addLayout(layout_botoes)
        layout.addWidget(self.feedback_animado)

        widget_central = QWidget()
        widget_central.setLayout(layout)
        self.setCentralWidget(widget_central)

    def abrir_menu(self):
        self.menu = JanelaMenu()
        self.menu.exec_()

    def exibir_regras(self):
        regras = (
            "Regras do Jogo:\n\n"
            "1. Pedra vence Tesoura.\n"
            "2. Tesoura vence Papel.\n"
            "3. Papel vence Pedra.\n\n"
            "Objetivo: Escolher o gesto correto para vencer o computador.\n"
            "O jogo utiliza a contagem de dedos para determinar a escolha."
        )
        QMessageBox.information(self, "Regras do Jogo", regras)

    def iniciar_rodada(self):
        self.resultado = None
        self.rotulo_resultado.setText("Prepare-se...")
        self.rotulo_contagem.setText("5")
        self.contagem = 5
        self.timer_contagem = QTimer(self)
        self.timer_contagem.timeout.connect(self.atualizar_contagem)
        self.timer_contagem.start(1000)

    def atualizar_contagem(self):
        self.contagem -= 1
        if self.contagem == 0:
            self.timer_contagem.stop()
            self.rotulo_contagem.setText("")
            self.detectar_gesto()
        else:
            self.rotulo_contagem.setText(str(self.contagem))

    def detectar_gesto(self):
        ret, frame = self.cap.read()
        if not ret:
            self.rotulo_resultado.setText("Erro ao capturar a câmera.")
            return

        # Conversão para BGR
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Detecção de mãos
        resultados = self.hands.process(frame_bgr)

        if resultados.multi_hand_landmarks:
            for hand_landmarks in resultados.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

            # Aqui, estamos usando a contagem de dedos para identificar o gesto.
            gesto_usuario = self.detectar_dedos(frame_bgr)
            gesto_computador = random.choice(["Pedra", "Papel", "Tesoura"])
            self.calcular_resultado(gesto_usuario, gesto_computador)

        # Atualizando o vídeo na interface
        altura, largura, canal = frame.shape
        bytes_por_linha = canal * largura
        imagem_qt = QImage(frame.data, largura, altura, bytes_por_linha, QImage.Format_BGR888)
        pixmap = QPixmap.fromImage(imagem_qt)
        self.rotulo_video.setPixmap(pixmap)

    def detectar_dedos(self, frame):
        # Detecção simples: contagem de dedos levantados (exemplo básico)
        dedos = 0
        resultados = self.hands.process(frame)

        if resultados.multi_hand_landmarks:
            for hand_landmarks in resultados.multi_hand_landmarks:
                dedos = sum(1 for i in [4, 8, 12, 16, 20] if hand_landmarks.landmark[i].y < hand_landmarks.landmark[i-2].y)
        
        # Identificando o gesto baseado na contagem de dedos
        if dedos == 1:
            return "Pedra"
        elif dedos == 3:
            return "Tesoura"
        elif dedos == 5:
            return "Papel"
        else:
            return "Desconhecido"

    def calcular_resultado(self, gesto_usuario, gesto_computador):
        if gesto_usuario == gesto_computador:
            self.resultado = "Empate"
            self.placar["Empates"] += 1
        elif (gesto_usuario == "Pedra" and gesto_computador == "Tesoura") or \
             (gesto_usuario == "Papel" and gesto_computador == "Pedra") or \
             (gesto_usuario == "Tesoura" and gesto_computador == "Papel"):
            self.resultado = "Vitória"
            self.placar["Vitórias"] += 1
        else:
            self.resultado = "Derrota"
            self.placar["Derrotas"] += 1

        self.rotulo_resultado.setText(f"Você: {gesto_usuario} | Computador: {gesto_computador} | Resultado: {self.resultado}")
        self.rotulo_placar.setText(f"Vitórias: {self.placar['Vitórias']} | Derrotas: {self.placar['Derrotas']} | Empates: {self.placar['Empates']}")

        # Exibindo o feedback visual animado
        self.feedback_animado.setText(self.resultado)
        self.feedback_animado.show()

        # Animação de feedback
        animacao = QPropertyAnimation(self.feedback_animado, b"pos")
        animacao.setStartValue(QPoint(0, 300))
        animacao.setEndValue(QPoint(0, 250))
        animacao.setDuration(1000)
        animacao.finished.connect(self.feedback_animado.hide)
        animacao.start()

    def atualizar_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        altura, largura, canal = frame.shape
        bytes_por_linha = canal * largura
        imagem_qt = QImage(frame.data, largura, altura, bytes_por_linha, QImage.Format_BGR888)
        pixmap = QPixmap.fromImage(imagem_qt)
        self.rotulo_video.setPixmap(pixmap)


app = QApplication(sys.argv)
janela = HandGestureRPSApp()
janela.show()
sys.exit(app.exec_())