import sys
import cv2
import mediapipe as mp
import numpy as np
import json
import random
from PyQt5.QtWidgets import (QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QMenu, QAction, QHBoxLayout, 
                             QMainWindow, QMessageBox, QDialog, QSlider, QWizard, QWizardPage)
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtCore import QTimer, Qt, QPropertyAnimation, QPoint
from PyQt5.QtMultimedia import QSound

class JanelaMenu(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Menu de Opções")
        self.setGeometry(100, 100, 400, 300)
        self.setStyleSheet("background-color: #34495e; color: white;")

        self.botao_reiniciar = QPushButton("Reiniciar Jogo")
        self.botao_reiniciar.setFont(QFont("Arial", 16))
        self.botao_reiniciar.setStyleSheet("background-color: #1abc9c; color: white; padding: 10px; border-radius: 10px;")
        self.botao_reiniciar.clicked.connect(self.reiniciar_jogo)

        self.botao_estatisticas = QPushButton("Estatísticas")
        self.botao_estatisticas.setFont(QFont("Arial", 16))
        self.botao_estatisticas.setStyleSheet("background-color: #3498db; color: white; padding: 10px; border-radius: 10px;")
        self.botao_estatisticas.clicked.connect(self.mostrar_estatisticas)

        self.botao_sair = QPushButton("Sair do Jogo")
        self.botao_sair.setFont(QFont("Arial", 16))
        self.botao_sair.setStyleSheet("background-color: #e74c3c; color: white; padding: 10px; border-radius: 10px;")
        self.botao_sair.clicked.connect(self.fechar_jogo)

        layout = QVBoxLayout()
        layout.addWidget(self.botao_reiniciar)
        layout.addWidget(self.botao_estatisticas)
        layout.addWidget(self.botao_sair)
        self.setLayout(layout)

    def reiniciar_jogo(self):
        janela.iniciar_rodada()
        self.accept()

    def mostrar_estatisticas(self):
        estatisticas = f"Vitórias: {janela.placar['Vitórias']}\nDerrotas: {janela.placar['Derrotas']}\nEmpates: {janela.placar['Empates']}"
        QMessageBox.information(self, "Estatísticas", estatisticas)

    def fechar_jogo(self):
        janela.close()
        self.accept()

class JanelaConfiguracoes(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configurações")
        self.setGeometry(150, 150, 300, 200)
        self.setStyleSheet("background-color: #34495e; color: white;")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Sensibilidade de Detecção (50-90%)"))
        self.sensibilidade = QSlider(Qt.Horizontal)
        self.sensibilidade.setRange(50, 90)
        self.sensibilidade.setValue(70)
        layout.addWidget(self.sensibilidade)

        self.botao_salvar = QPushButton("Salvar")
        self.botao_salvar.setStyleSheet("background-color: #1abc9c; color: white; padding: 5px;")
        self.botao_salvar.clicked.connect(self.salvar)
        layout.addWidget(self.botao_salvar)
        self.setLayout(layout)

    def salvar(self):
        sensibilidade = self.sensibilidade.value() / 100
        janela.hands = mp.solutions.hands.Hands(min_detection_confidence=sensibilidade, min_tracking_confidence=sensibilidade)
        self.accept()

class HandGestureRPSApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.placar = {"Vitórias": 0, "Derrotas": 0, "Empates": 0}
        self.resultado = None
        self.em_rodada = False
        self.modo_treinamento = False
        self.iniciar_ui()

        # Configuração da câmera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            QMessageBox.critical(self, "Erro", "Não foi possível acessar a câmera.")
            sys.exit(1)

        # Configuração do MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)
        self.mp_draw = mp.solutions.drawing_utils

        # Placeholder para modelo de Machine Learning (requer treinamento prévio)
        try:
            import tensorflow as tf
            self.modelo_gestos = tf.keras.models.load_model("modelo_gestos.h5")
        except:
            self.modelo_gestos = None
            print("Modelo ML não encontrado. Usando detecção simples.")

        # Sons (arquivos devem existir no diretório)
        self.som_vitoria = QSound("sons/vitoria.wav")
        self.som_derrota = QSound("sons/derrota.wav")
        self.som_empate = QSound("sons/empate.wav")
        self.som_contagem = QSound("sons/tick.wav")

        # Timer para frames
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.atualizar_frame)
        self.timer.start(30)

        # Mostrar tutorial na primeira execução
        self.mostrar_tutorial()

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
        acao_regras = QAction("Regras", self)
        acao_menu = QAction("Menu", self)
        acao_config = QAction("Configurações", self)
        menu_jogo.addAction(acao_sair)
        menu_jogo.addAction(acao_regras)
        menu_jogo.addAction(acao_menu)
        menu_jogo.addAction(acao_config)
        acao_sair.triggered.connect(self.close)
        acao_regras.triggered.connect(self.exibir_regras)
        acao_menu.triggered.connect(self.abrir_menu)
        acao_config.triggered.connect(self.abrir_configuracoes)

        # Interface
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

        self.feedback_animado = QLabel(self)
        self.feedback_animado.setAlignment(Qt.AlignCenter)
        self.feedback_animado.setFont(QFont("Arial", 30, QFont.Bold))
        self.feedback_animado.setStyleSheet("color: #f39c12;")
        self.feedback_animado.hide()

        # Botões
        self.botao_iniciar = QPushButton("Nova Rodada")
        self.botao_iniciar.setFont(QFont("Arial", 18))
        self.botao_iniciar.setStyleSheet("background-color: #1abc9c; color: white; padding: 10px; border-radius: 10px;")
        self.botao_iniciar.clicked.connect(self.iniciar_rodada)

        self.botao_treinar = QPushButton("Treinar")
        self.botao_treinar.setFont(QFont("Arial", 18))
        self.botao_treinar.setStyleSheet("background-color: #9b59b6; color: white; padding: 10px; border-radius: 10px;")
        self.botao_treinar.clicked.connect(self.iniciar_treinamento)

        self.botao_menu = QPushButton("Menu")
        self.botao_menu.setFont(QFont("Arial", 18))
        self.botao_menu.setStyleSheet("background-color: #3498db; color: white; padding: 10px; border-radius: 10px;")
        self.botao_menu.clicked.connect(self.abrir_menu)

        self.botao_sair = QPushButton("Sair")
        self.botao_sair.setFont(QFont("Arial", 18))
        self.botao_sair.setStyleSheet("background-color: #e74c3c; color: white; padding: 10px; border-radius: 10px;")
        self.botao_sair.clicked.connect(self.close)

        layout_botoes = QHBoxLayout()
        layout_botoes.addWidget(self.botao_iniciar)
        layout_botoes.addWidget(self.botao_treinar)
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

    def abrir_configuracoes(self):
        config = JanelaConfiguracoes()
        config.exec_()

    def exibir_regras(self):
        regras = (
            "Regras do Jogo:\n\n"
            "1. Pedra vence Tesoura.\n"
            "2. Tesoura vence Papel.\n"
            "3. Papel vence Pedra.\n\n"
            "Mostre o gesto: 0 dedos (Pedra), 2 dedos (Tesoura), 5 dedos (Papel)."
        )
        QMessageBox.information(self, "Regras do Jogo", regras)

    def mostrar_tutorial(self):
        wizard = QWizard()
        wizard.setWindowTitle("Tutorial")
        pagina1 = QWizardPage()
        pagina1.setTitle("Bem-vindo!")
        label = QLabel("Mostre 0 dedos para Pedra.\nMostre 2 dedos para Tesoura.\nMostre 5 dedos para Papel.")
        layout = QVBoxLayout()
        layout.addWidget(label)
        pagina1.setLayout(layout)
        wizard.addPage(pagina1)
        wizard.exec_()

    def iniciar_rodada(self):
        self.em_rodada = True
        self.modo_treinamento = False
        self.resultado = None
        self.rotulo_resultado.setText("Prepare-se...")
        self.rotulo_contagem.setText("5")
        self.contagem = 5
        self.timer_contagem = QTimer(self)
        self.timer_contagem.timeout.connect(self.atualizar_contagem)
        self.timer_contagem.start(1000)

    def iniciar_treinamento(self):
        self.modo_treinamento = True
        self.em_rodada = True
        self.rotulo_resultado.setText("Pratique seus gestos!")
        self.timer_treinamento = QTimer(self)
        self.timer_treinamento.timeout.connect(self.treinar_gesto)
        self.timer_treinamento.start(1000)

    def atualizar_contagem(self):
        self.som_contagem.play()
        self.contagem -= 1
        if self.contagem == 0:
            self.timer_contagem.stop()
            self.rotulo_contagem.setText("")
            self.detectar_gesto()
            self.em_rodada = False
        else:
            self.rotulo_contagem.setText(str(self.contagem))

    def treinar_gesto(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        resultados = self.hands.process(frame_bgr)
        if resultados.multi_hand_landmarks:
            gesto = self.detectar_dedos(frame_bgr if self.modelo_gestos else resultados.multi_hand_landmarks[0])
            self.rotulo_resultado.setText(f"Gesto detectado: {gesto}")
        self.exibir_frame(frame)

    def detectar_gesto(self):
        ret, frame = self.cap.read()
        if not ret:
            QMessageBox.critical(self, "Erro", "Não foi possível capturar a câmera.")
            self.close()
            return

        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        resultados = self.hands.process(frame_bgr)
        gestos = []

        if resultados.multi_hand_landmarks:
            for hand_landmarks in resultados.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                gesto = self.detectar_dedos(frame_bgr if self.modelo_gestos else hand_landmarks)
                gestos.append(gesto)
            
            if len(gestos) > 1:  # Multiplayer
                self.calcular_resultado(gestos[0], gestos[1])
                self.rotulo_resultado.setText(f"Jogador 1: {gestos[0]} | Jogador 2: {gestos[1]} | {self.resultado}")
            else:  # Single player
                gesto_computador = random.choice(["Pedra", "Papel", "Tesoura"])
                self.calcular_resultado(gestos[0], gesto_computador)
        
        self.exibir_frame(frame)

    def detectar_dedos(self, dados):
        """Detecta gestos com ML ou contagem de dedos."""
        if self.modelo_gestos:  # Uso de Machine Learning
            img = cv2.resize(dados, (224, 224))  # Ajustar ao tamanho do modelo
            img = img / 255.0
            img = np.expand_dims(img, axis=0)
            predicao = self.modelo_gestos.predict(img)
            gestos = ["Pedra", "Papel", "Tesoura"]
            return gestos[np.argmax(predicao)]
        else:  # Método simples
            dedos = sum(1 for i in [4, 8, 12, 16, 20] if dados.landmark[i].y < dados.landmark[i-2].y)
            if dedos == 0:
                return "Pedra"
            elif dedos == 2:
                return "Tesoura"
            elif dedos == 5:
                return "Papel"
            else:
                return "Desconhecido"

    def calcular_resultado(self, gesto_usuario, gesto_computador):
        """Calcula o resultado e salva no histórico."""
        if gesto_usuario == "Desconhecido" or gesto_computador == "Desconhecido":
            self.rotulo_resultado.setText("Gesto inválido! Tente novamente.")
            return

        if gesto_usuario == gesto_computador:
            self.resultado = "Empate"
            self.placar["Empates"] += 1
            self.som_empate.play()
        elif (gesto_usuario == "Pedra" and gesto_computador == "Tesoura") or \
             (gesto_usuario == "Papel" and gesto_computador == "Pedra") or \
             (gesto_usuario == "Tesoura" and gesto_computador == "Papel"):
            self.resultado = "Vitória"
            self.placar["Vitórias"] += 1
            self.som_vitoria.play()
        else:
            self.resultado = "Derrota"
            self.placar["Derrotas"] += 1
            self.som_derrota.play()

        self.rotulo_resultado.setText(f"Você: {gesto_usuario} | Oponente: {gesto_computador} | Resultado: {self.resultado}")
        self.rotulo_placar.setText(f"Vitórias: {self.placar['Vitórias']} | Derrotas: {self.placar['Derrotas']} | Empates: {self.placar['Empates']}")

        # Salvar histórico
        with open("historico.json", "a") as f:
            jogada = {"usuario": gesto_usuario, "oponente": gesto_computador, "resultado": self.resultado}
            json.dump(jogada, f)
            f.write("\n")

        self.feedback_animado.setText(self.resultado)
        self.feedback_animado.show()
        animacao = QPropertyAnimation(self.feedback_animado, b"pos")
        animacao.setStartValue(QPoint(0, 300))
        animacao.setEndValue(QPoint(0, 250))
        animacao.setDuration(1000)
        animacao.finished.connect(self.feedback_animado.hide)
        animacao.start()

    def atualizar_frame(self):
        """Atualiza o frame da câmera."""
        ret, frame = self.cap.read()
        if not ret:
            return
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        if self.em_rodada:
            resultados = self.hands.process(frame_bgr)
            if resultados.multi_hand_landmarks:
                for hand_landmarks in resultados.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
        
        self.exibir_frame(frame)

    def exibir_frame(self, frame):
        """Exibe o frame no rótulo de vídeo."""
        altura, largura, canal = frame.shape
        bytes_por_linha = canal * largura
        imagem_qt = QImage(frame.data, largura, altura, bytes_por_linha, QImage.Format_BGR888)
        pixmap = QPixmap.fromImage(imagem_qt)
        self.rotulo_video.setPixmap(pixmap)

    def closeEvent(self, event):
        """Libera recursos ao fechar."""
        self.cap.release()
        self.hands.close()
        event.accept()

app = QApplication(sys.argv)
janela = HandGestureRPSApp()
janela.show()
sys.exit(app.exec_())