import sys
import os
import json
import random
from dataclasses import asdict
from PyQt5.QtWidgets import (
    QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QMenu, QAction,
    QHBoxLayout, QMainWindow, QMessageBox, QDialog, QSlider, QComboBox, QCheckBox,
    QSpinBox, QGroupBox, QGridLayout, QFrame
)
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtCore import QTimer, Qt, QCoreApplication, QTranslator, QLocale, QThread, pyqtSignal, QSettings

from models.game_models import GameSettings, GameStats, Gesture
from utils.theme_manager import ThemeManager
from utils.sound_manager import SoundManager
from controllers.gesture_detector import GestureDetector
from controllers.ai_logic import MarkovChainAI
from views.dialogs import StatsDialog, SettingsDialog

class HandsGestureRPS(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = GameSettings()
        self.stats = GameStats()
        self.sound_manager = SoundManager(self.settings.sound_enabled)
        self.gesture_detector = None
        self.game_state = "waiting"
        self.countdown_timer = QTimer()
        self.countdown_value = 0
        self.player_gesture = None
        self.opponent_gesture = None
        self.game_result = None
        self.translator = QTranslator()
        self.last_finger_count = 0
        
        history_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "historico.json")
        self.ai = MarkovChainAI(history_file=history_path)
        
        self.setup_ui()
        self.setup_connections()
        self.load_settings()
        self.apply_theme()
        self.load_language()
        
    def load_language(self):
        if self.settings.language == "pt_BR":
            QCoreApplication.installTranslator(self.translator)
        elif self.settings.language == "en":
            QCoreApplication.removeTranslator(self.translator)
        self.retranslate_ui()
        
    def retranslate_ui(self):
        self.setWindowTitle(QCoreApplication.translate("Main", "HandsGestureRPS - Reconhecimento de Gestos"))
        self.camera_label.setText(QCoreApplication.translate("Main", "Feed da Câmera"))
        self.start_camera_btn.setText(QCoreApplication.translate("Main", "Iniciar Câmera") if self.gesture_detector is None else QCoreApplication.translate("Main", "Parar Câmera"))
        self.play_btn.setText(QCoreApplication.translate("Main", "Jogar Rodada"))
        self.reset_btn.setText(QCoreApplication.translate("Main", "Reiniciar Jogo"))
        self.status_label.setText(QCoreApplication.translate("Main", "Pronto para jogar!"))
        self.gesture_label.setText(QCoreApplication.translate("Main", "Nenhum gesto detectado"))
        self.fingers_label.setText(QCoreApplication.translate("Main", f"Dedos detectados: {self.last_finger_count}"))
        
        self.menuBar().clear()
        self.create_menu_bar()
        
        self.wins_label.setText(str(self.stats.wins))
        self.losses_label.setText(str(self.stats.losses))
        self.draws_label.setText(str(self.stats.draws))
        
    def setup_ui(self):
        self.setWindowTitle(QCoreApplication.translate("Main", "HandsGestureRPS - Reconhecimento de Gestos"))
        self.setGeometry(100, 100, 1000, 700)
        
        self.create_menu_bar()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        
        left_panel = self.create_camera_panel()
        main_layout.addWidget(left_panel, 2)
        
        right_panel = self.create_game_panel()
        main_layout.addWidget(right_panel, 1)
        
        central_widget.setLayout(main_layout)
        
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        game_menu = menubar.addMenu(QCoreApplication.translate("Main", "Jogo"))
        
        new_game_action = QAction(QCoreApplication.translate("Main", "Novo Jogo"), self)
        new_game_action.triggered.connect(self.new_game)
        game_menu.addAction(new_game_action)
        
        game_menu.addSeparator()
        
        stats_action = QAction(QCoreApplication.translate("Main", "Estatísticas"), self)
        stats_action.triggered.connect(self.show_stats)
        game_menu.addAction(stats_action)
        
        settings_action = QAction(QCoreApplication.translate("Main", "Configurações"), self)
        settings_action.triggered.connect(self.show_settings)
        game_menu.addAction(settings_action)
        
        game_menu.addSeparator()
        
        exit_action = QAction(QCoreApplication.translate("Main", "Sair"), self)
        exit_action.triggered.connect(self.close)
        game_menu.addAction(exit_action)
        
    def create_camera_panel(self):
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout()
        
        self.camera_label = QLabel(QCoreApplication.translate("Main", "Feed da Câmera"))
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setMinimumSize(640, 480)
        self.camera_label.setObjectName("CameraFeed")
        layout.addWidget(self.camera_label)
        
        camera_controls = QHBoxLayout()
        
        self.camera_combo = QComboBox()
        self.camera_combo.addItems([f"Câmera {i}" for i in range(5)])
        self.camera_combo.currentIndexChanged.connect(self.change_camera)
        camera_controls.addWidget(self.camera_combo)
        
        self.start_camera_btn = QPushButton(QCoreApplication.translate("Main", "Iniciar Câmera"))
        self.start_camera_btn.clicked.connect(self.toggle_camera)
        camera_controls.addWidget(self.start_camera_btn)
        
        layout.addLayout(camera_controls)
        panel.setLayout(layout)
        return panel
        
    def create_game_panel(self):
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout()
        
        title = QLabel(QCoreApplication.translate("Main", "🤖 HandsGesture AI"))
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 28, QFont.Bold))
        title.setStyleSheet("color: #00e5ff;")
        layout.addWidget(title)
        
        score_group = QGroupBox(QCoreApplication.translate("Main", "Placar"))
        score_layout = QGridLayout()
        
        lbl_win = QLabel(QCoreApplication.translate("Main", "Vitórias:"))
        lbl_win.setFont(QFont("Segoe UI", 14))
        score_layout.addWidget(lbl_win, 0, 0)
        self.wins_label = QLabel(str(self.stats.wins))
        self.wins_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.wins_label.setStyleSheet("color: #4ade80;")
        score_layout.addWidget(self.wins_label, 0, 1)
        
        lbl_loss = QLabel(QCoreApplication.translate("Main", "Derrotas:"))
        lbl_loss.setFont(QFont("Segoe UI", 14))
        score_layout.addWidget(lbl_loss, 1, 0)
        self.losses_label = QLabel(str(self.stats.losses))
        self.losses_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.losses_label.setStyleSheet("color: #f87171;")
        score_layout.addWidget(self.losses_label, 1, 1)
        
        lbl_draw = QLabel(QCoreApplication.translate("Main", "Empates:"))
        lbl_draw.setFont(QFont("Segoe UI", 14))
        score_layout.addWidget(lbl_draw, 2, 0)
        self.draws_label = QLabel(str(self.stats.draws))
        self.draws_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.draws_label.setStyleSheet("color: #94a3b8;")
        score_layout.addWidget(self.draws_label, 2, 1)
        
        score_group.setLayout(score_layout)
        layout.addWidget(score_group)
        
        self.status_label = QLabel(QCoreApplication.translate("Main", "▶️ Pronto para jogar!"))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.status_label.setStyleSheet("color: #fbbf24;")
        layout.addWidget(self.status_label)
        
        gesture_group = QGroupBox(QCoreApplication.translate("Main", "Gesto Atual"))
        gesture_layout = QVBoxLayout()
        
        self.gesture_label = QLabel(QCoreApplication.translate("Main", "Nenhum gesto detectado"))
        self.gesture_label.setAlignment(Qt.AlignCenter)
        self.gesture_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        gesture_layout.addWidget(self.gesture_label)
        
        self.fingers_label = QLabel(QCoreApplication.translate("Main", f"Dedos detectados: {self.last_finger_count}"))
        self.fingers_label.setAlignment(Qt.AlignCenter)
        self.fingers_label.setFont(QFont("Segoe UI", 14))
        gesture_layout.addWidget(self.fingers_label)
        
        gesture_group.setLayout(gesture_layout)
        layout.addWidget(gesture_group)
        
        controls_group = QGroupBox(QCoreApplication.translate("Main", "Controles do Jogo"))
        controls_layout = QVBoxLayout()
        
        self.play_btn = QPushButton(QCoreApplication.translate("Main", "Jogar Rodada"))
        self.play_btn.clicked.connect(self.start_round)
        self.play_btn.setEnabled(False)
        controls_layout.addWidget(self.play_btn)
        
        self.reset_btn = QPushButton(QCoreApplication.translate("Main", "Reiniciar Jogo"))
        self.reset_btn.clicked.connect(self.reset_game)
        controls_layout.addWidget(self.reset_btn)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
        
    def setup_connections(self):
        self.countdown_timer.timeout.connect(self.update_countdown)
        
    def toggle_camera(self):
        if self.gesture_detector is None:
            self.start_camera()
        else:
            self.stop_camera()
            
    def change_camera(self, index):
        self.settings.camera_index = index
        if self.gesture_detector:
            self.stop_camera()
            self.start_camera()
            
    def start_camera(self):
        self.gesture_detector = GestureDetector(self.settings)
        self.gesture_detector.gesture_detected.connect(self.on_gesture_detected)
        self.gesture_detector.frame_processed.connect(self.update_camera_feed)
        
        if self.gesture_detector.start_detection():
            self.start_camera_btn.setText(QCoreApplication.translate("Main", "Parar Câmera"))
            self.play_btn.setEnabled(True)
            self.status_label.setText(QCoreApplication.translate("Main", "Câmera iniciada - Pronto para jogar!"))
        else:
            QMessageBox.warning(self, QCoreApplication.translate("Main", "Erro na Câmera"), QCoreApplication.translate("Main", "Não foi possível iniciar a câmera!"))
            self.gesture_detector = None
            
    def stop_camera(self):
        if self.gesture_detector:
            self.gesture_detector.stop_detection()
            self.gesture_detector = None
            
        self.start_camera_btn.setText(QCoreApplication.translate("Main", "Iniciar Câmera"))
        self.play_btn.setEnabled(False)
        self.camera_label.setText(QCoreApplication.translate("Main", "Câmera parada"))
        self.status_label.setText(QCoreApplication.translate("Main", "Câmera parada"))
        
    def update_camera_feed(self, frame):
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_image)
        
        scaled_pixmap = pixmap.scaled(
            self.camera_label.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        self.camera_label.setPixmap(scaled_pixmap)
        
    def on_gesture_detected(self, gesture, confidence, finger_count):
        gesture_translated = {
            "rock": QCoreApplication.translate("Main", "✊ Pedra"),
            "paper": QCoreApplication.translate("Main", "✋ Papel"),
            "scissors": QCoreApplication.translate("Main", "✌️ Tesoura"),
            "unknown": QCoreApplication.translate("Main", "❓ Desconhecido")
        }.get(gesture, gesture)
        self.gesture_label.setText(f"{gesture_translated} ({confidence:.2f})")
        self.fingers_label.setText(QCoreApplication.translate("Main", f"Dedos detectados: {finger_count}"))
        self.last_finger_count = finger_count
        
        if self.game_state == "playing":
            self.player_gesture = gesture
            self.end_round()
            
    def start_round(self):
        if self.game_state != "waiting":
            return
            
        self.game_state = "countdown"
        self.countdown_value = self.settings.countdown_duration
        self.player_gesture = None
        self.opponent_gesture = None
        
        self.play_btn.setEnabled(False)
        self.status_label.setText(QCoreApplication.translate("Main", f"Prepare-se... {self.countdown_value}"))
        
        self.countdown_timer.start(1000)
        
    def update_countdown(self):
        self.countdown_value -= 1
        
        if self.countdown_value > 0:
            self.status_label.setText(QCoreApplication.translate("Main", f"Prepare-se... {self.countdown_value}"))
        else:
            self.countdown_timer.stop()
            self.game_state = "playing"
            self.status_label.setText(QCoreApplication.translate("Main", "Mostre seu gesto!"))
            
            QTimer.singleShot(3000, self.end_round)
            
    def end_round(self):
        if self.game_state != "playing":
            return
            
        self.game_state = "result"
        
        self.opponent_gesture = self.ai.get_counter_move()
        
        if self.player_gesture is None:
            self.player_gesture = Gesture.UNKNOWN.value
            
        if self.player_gesture != Gesture.UNKNOWN.value:
            self.ai.update_history(self.player_gesture)
            
        result = self.determine_winner(self.player_gesture, self.opponent_gesture)
        
        self.update_stats(result)
        
        self.show_result(result)
        
        QTimer.singleShot(3000, self.reset_for_next_round)
        
    def determine_winner(self, player, opponent):
        if player == Gesture.UNKNOWN.value:
            return "loss"
            
        if player == opponent:
            return "draw"
            
        winning_combinations = {
            (Gesture.ROCK.value, Gesture.SCISSORS.value): "win",
            (Gesture.PAPER.value, Gesture.ROCK.value): "win",
            (Gesture.SCISSORS.value, Gesture.PAPER.value): "win"
        }
        
        if (player, opponent) in winning_combinations:
            return "win"
        else:
            return "loss"
            
    def update_stats(self, result):
        self.stats.total_games += 1
        
        if result == "win":
            self.stats.wins += 1
            self.stats.win_streak += 1
            self.sound_manager.play("win")
        elif result == "loss":
            self.stats.losses += 1
            self.stats.win_streak = 0
            self.sound_manager.play("lose")
        else:
            self.stats.draws += 1
            self.stats.win_streak = 0
            self.sound_manager.play("draw")
            
        self.stats.best_streak = max(self.stats.best_streak, self.stats.win_streak)
        
        if self.player_gesture != Gesture.UNKNOWN.value:
            self.stats.gestures_detected[self.player_gesture] += 1
            
        self.wins_label.setText(str(self.stats.wins))
        self.losses_label.setText(str(self.stats.losses))
        self.draws_label.setText(str(self.stats.draws))
        
        if self.settings.auto_save:
            self.save_stats()
            
    def show_result(self, result):
        gesture_translated = {
            "rock": QCoreApplication.translate("Main", "✊ Pedra"),
            "paper": QCoreApplication.translate("Main", "✋ Papel"),
            "scissors": QCoreApplication.translate("Main", "✌️ Tesoura"),
            "unknown": QCoreApplication.translate("Main", "❓ Desconhecido")
        }
        opponent = gesture_translated.get(self.opponent_gesture, self.opponent_gesture)
        player = gesture_translated.get(self.player_gesture, self.player_gesture)
        
        if result == "win":
            message = QCoreApplication.translate("Main", f"Você venceu! {player} vence {opponent}")
        elif result == "loss":
            message = QCoreApplication.translate("Main", f"Você perdeu! {opponent} vence {player}")
        else:
            message = QCoreApplication.translate("Main", f"Empate! Ambos escolheram {player}")
            
        self.status_label.setText(message)
        
    def reset_for_next_round(self):
        self.game_state = "waiting"
        self.player_gesture = None
        self.opponent_gesture = None
        self.status_label.setText(QCoreApplication.translate("Main", "Pronto para jogar!"))
        self.play_btn.setEnabled(True)
        
    def new_game(self):
        self.reset_game()
        self.status_label.setText(QCoreApplication.translate("Main", "Novo jogo iniciado!"))
        
    def reset_game(self):
        self.stats = GameStats()
        self.game_state = "waiting"
        self.player_gesture = None
        self.opponent_gesture = None
        self.wins_label.setText(str(self.stats.wins))
        self.losses_label.setText(str(self.stats.losses))
        self.draws_label.setText(str(self.stats.draws))
        self.status_label.setText(QCoreApplication.translate("Main", "Jogo reiniciado!"))
        self.gesture_label.setText(QCoreApplication.translate("Main", "Nenhum gesto detectado"))
        self.fingers_label.setText(QCoreApplication.translate("Main", f"Dedos detectados: 0"))
        self.last_finger_count = 0
        
        if self.settings.auto_save:
            self.save_stats()
            
    def show_stats(self):
        dialog = StatsDialog(self.stats, self)
        dialog.exec_()
        
    def show_settings(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec_():
            self.apply_settings()
            if self.settings.auto_save:
                self.save_settings()
            self.load_language()
                
    def apply_settings(self):
        self.sound_manager.enabled = self.settings.sound_enabled
        if self.gesture_detector:
            self.gesture_detector.settings = self.settings
            self.stop_camera()
            self.start_camera()
            
    def load_settings(self):
        settings = QSettings("xAI", "HandsGestureRPS")
        self.settings.detection_confidence = settings.value("detection_confidence", 0.7, float)
        self.settings.countdown_duration = settings.value("countdown_duration", 3, int)
        self.settings.sound_enabled = settings.value("sound_enabled", True, bool)
        self.settings.show_landmarks = settings.value("show_landmarks", True, bool)
        self.settings.language = settings.value("language", "pt_BR", str)
        self.settings.camera_index = settings.value("camera_index", 0, int)
        
        if hasattr(self, 'camera_combo'):
            self.camera_combo.blockSignals(True)
            self.camera_combo.setCurrentIndex(self.settings.camera_index)
            self.camera_combo.blockSignals(False)
        
    def save_settings(self):
        settings = QSettings("xAI", "HandsGestureRPS")
        settings.setValue("detection_confidence", self.settings.detection_confidence)
        settings.setValue("countdown_duration", self.settings.countdown_duration)
        settings.setValue("sound_enabled", self.settings.sound_enabled)
        settings.setValue("show_landmarks", self.settings.show_landmarks)
        settings.setValue("language", self.settings.language)
        settings.setValue("camera_index", self.settings.camera_index)
        
    def save_stats(self):
        try:
            with open("game_stats.json", "w") as f:
                json.dump(asdict(self.stats), f)
        except Exception as e:
            print(f"Failed to save stats: {e}")
            
    def apply_theme(self):
        self.setStyleSheet(ThemeManager.get_dark_theme())
        
    def closeEvent(self, event):
        if self.gesture_detector:
            self.stop_camera()
        if self.settings.auto_save:
            self.save_settings()
            self.save_stats()
        event.accept()

