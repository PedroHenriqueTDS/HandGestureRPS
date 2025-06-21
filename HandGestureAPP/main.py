import sys
import cv2
import mediapipe as mp
import numpy as np
import json
import random
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from PyQt5.QtWidgets import (
    QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QMenu, QAction, 
    QHBoxLayout, QMainWindow, QMessageBox, QDialog, QSlider, QComboBox, QCheckBox, 
    QSpinBox, QGroupBox, QGridLayout, QFrame
)
from PyQt5.QtGui import (
    QImage, QPixmap, QFont
)
from PyQt5.QtCore import (
    QTimer, Qt, QCoreApplication, QTranslator, QLocale, QThread, pyqtSignal, QSettings
)
from PyQt5.QtMultimedia import QSoundEffect

def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / f"handsgesturerps_{datetime.now().strftime('%Y%m%d')}.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class GameMode(Enum):
    SINGLE_PLAYER = "single_player"
    MULTIPLAYER_LOCAL = "multiplayer_local"
    MULTIPLAYER_ONLINE = "multiplayer_online"
    TRAINING = "training"
    TOURNAMENT = "tournament"

class Gesture(Enum):
    ROCK = "rock"
    PAPER = "paper"
    SCISSORS = "scissors"
    UNKNOWN = "unknown"

class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"

@dataclass
class GameStats:
    wins: int = 0
    losses: int = 0
    draws: int = 0
    total_games: int = 0
    win_streak: int = 0
    best_streak: int = 0
    accuracy: float = 0.0
    avg_reaction_time: float = 0.0
    gestures_detected: Dict[str, int] = None
    
    def __post_init__(self):
        if self.gestures_detected is None:
            self.gestures_detected = {g.value: 0 for g in Gesture}

@dataclass
class GameSettings:
    detection_confidence: float = 0.7
    tracking_confidence: float = 0.5
    countdown_duration: int = 3
    theme: str = "dark"
    language: str = "pt_BR"
    sound_enabled: bool = True
    fullscreen: bool = False
    difficulty: Difficulty = Difficulty.MEDIUM
    game_mode: GameMode = GameMode.SINGLE_PLAYER
    auto_save: bool = True
    show_landmarks: bool = True

class GestureDetector(QThread):
    gesture_detected = pyqtSignal(str, float, int)
    frame_processed = pyqtSignal(np.ndarray)
    
    def __init__(self, settings: GameSettings):
        super().__init__()
        self.settings = settings
        self.running = False
        self.cap = None
        self.mp_hands = mp.solutions.hands
        self.hands = None
        self.mp_draw = mp.solutions.drawing_utils
        self.gesture_history = []
        
    def initialize_camera(self):
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                for i in range(1, 5):
                    self.cap = cv2.VideoCapture(i)
                    if self.cap.isOpened():
                        break
                        
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                logger.info("Camera initialized successfully")
                return True
        except Exception as e:
            logger.error(f"Camera initialization failed: {e}")
        return False
        
    def start_detection(self):
        if not self.initialize_camera():
            logger.error("Failed to start detection due to camera error")
            return False
            
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=self.settings.detection_confidence,
            min_tracking_confidence=self.settings.tracking_confidence
        )
        
        self.running = True
        self.start()
        logger.info("Gesture detection started")
        return True
        
    def stop_detection(self):
        self.running = False
        if self.isRunning():
            self.quit()
            self.wait()
        if self.cap:
            self.cap.release()
        if self.hands:
            self.hands.close()
        logger.info("Gesture detection stopped")
            
    def run(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                logger.warning("Failed to capture frame")
                continue
                
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    if self.settings.show_landmarks:
                        self.mp_draw.draw_landmarks(
                            frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
                        )
                    
                    gesture, confidence, finger_count = self.rule_based_classify(hand_landmarks)
                    logger.debug(f"Detected gesture: {gesture}, confidence: {confidence}, fingers: {finger_count}")
                    self.filter_gesture(gesture, confidence, finger_count)
                    
            self.frame_processed.emit(frame)
            self.msleep(33)
            
    def rule_based_classify(self, landmarks) -> Tuple[str, float, int]:
        try:
            points = np.array([[lm.x, lm.y] for lm in landmarks.landmark])
            
            finger_tips = [4, 8, 12, 16, 20]
            finger_pips = [3, 6, 10, 14, 18]
            
            extended_fingers = 0
            
            for i in range(1, 5):
                tip_y = points[finger_tips[i]][1]
                pip_y = points[finger_pips[i]][1]
                if tip_y < pip_y:
                    extended_fingers += 1
                logger.debug(f"Finger {i}: tip_y={tip_y:.3f}, pip_y={pip_y:.3f}, extended={tip_y < pip_y}")
            
            thumb_tip_x = points[4][0]
            thumb_pip_x = points[3][0]
            wrist_x = points[0][0]
            thumb_extended = abs(thumb_tip_x - wrist_x) > abs(thumb_pip_x - wrist_x) * 1.5
            if thumb_extended:
                extended_fingers += 1
            logger.debug(f"Thumb: tip_x={thumb_tip_x:.3f}, pip_x={thumb_pip_x:.3f}, wrist_x={wrist_x:.3f}, extended={thumb_extended}")
            
            logger.debug(f"Total extended fingers: {extended_fingers}")
            
            if extended_fingers == 0 or extended_fingers == 1:
                return Gesture.ROCK.value, 0.9, extended_fingers
            elif extended_fingers == 2 or extended_fingers == 3:
                return Gesture.SCISSORS.value, 0.85, extended_fingers
            elif extended_fingers >= 4:
                return Gesture.PAPER.value, 0.9, extended_fingers
            else:
                return Gesture.UNKNOWN.value, 0.5, extended_fingers
                
        except Exception as e:
            logger.error(f"Rule-based classification error: {e}")
            return Gesture.UNKNOWN.value, 0.0, 0
            
    def filter_gesture(self, gesture: str, confidence: float, finger_count: int):
        self.gesture_history.append((gesture, confidence, time.time(), finger_count))
        
        current_time = time.time()
        self.gesture_history = [(g, c, t, f) for g, c, t, f in self.gesture_history 
                               if current_time - t < 1.0]
        
        if len(self.gesture_history) >= 3:
            recent_gestures = [g for g, c, t, f in self.gesture_history[-5:]]
            if recent_gestures.count(gesture) >= 3 and confidence > 0.7:
                self.gesture_detected.emit(gesture, confidence, finger_count)
                logger.info(f"Stable gesture emitted: {gesture}, confidence: {confidence}, fingers: {finger_count}")

class SoundManager:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.sounds = {}
        
    def play(self, sound_name: str):
        if self.enabled:
            if sound_name == "win":
                print("🎉 SOM DE VITÓRIA!")
            elif sound_name == "lose":
                print("😞 SOM DE DERROTA!")
            elif sound_name == "draw":
                print("🤝 SOM DE EMPATE!")

class ThemeManager:
    @staticmethod
    def get_dark_theme() -> str:
        return """
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                stop:0 #1a1a2e, stop:0.5 #16213e, stop:1 #0f3460);
            color: #ffffff;
        }
        
        QMenuBar {
            background-color: #16213e;
            color: #ffffff;
            border-bottom: 2px solid #0066cc;
            padding: 4px;
        }
        
        QMenuBar::item {
            background: transparent;
            padding: 8px 12px;
            border-radius: 4px;
        }
        
        QMenuBar::item:selected {
            background-color: #0066cc;
        }
        
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #0066cc, stop:1 #004499);
            color: white;
            border: 2px solid #0088ff;
            border-radius: 12px;
            padding: 12px 24px;
            font: bold 14px 'Segoe UI';
            min-width: 120px;
        }
        
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #0088ff, stop:1 #0066cc);
            border-color: #00aaff;
        }
        
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #004499, stop:1 #003366);
        }
        
        QPushButton:disabled {
            background: #333333;
            color: #666666;
            border-color: #444444;
        }
        
        QLabel {
            color: #ffffff;
            background: transparent;
        }
        
        QDialog {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #1a1a2e, stop:1 #16213e);
            border: 2px solid #0066cc;
            border-radius: 15px;
        }
        
        QSlider::groove:horizontal {
            height: 8px;
            background: #333366;
            border-radius: 4px;
        }
        
        QSlider::handle:horizontal {
            background: #0066cc;
            border: 2px solid #0088ff;
            width: 20px;
            margin: -6px 0;
            border-radius: 10px;
        }
        
        QSlider::handle:horizontal:hover {
            background: #0088ff;
        }
        
        QComboBox {
            background: #16213e;
            color: white;
            border: 2px solid #0066cc;
            border-radius: 6px;
            padding: 6px;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        
        QComboBox::down-arrow {
            image: none;
            background: #0066cc;
        }
        
        QCheckBox {
            color: white;
        }
        
        QSpinBox {
            background: #16213e;
            color: white;
            border: 2px solid #0066cc;
            border-radius: 6px;
            padding: 4px;
        }
        
        QGroupBox {
            font: bold 14px;
            color: #00aaff;
            border: 2px solid #0066cc;
            border-radius: 8px;
            margin: 10px 0;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px 0 8px;
        }
        """

class StatsDialog(QDialog):
    def __init__(self, stats: GameStats, parent=None):
        super().__init__(parent)
        self.stats = stats
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle(QCoreApplication.translate("Main", "Estatísticas do Jogo"))
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        stats_group = QGroupBox(QCoreApplication.translate("Main", "Estatísticas"))
        stats_layout = QGridLayout()
        
        win_rate = (self.stats.wins/max(1, self.stats.total_games)*100)
        
        stats_data = [
            (QCoreApplication.translate("Main", "Total de Jogos:"), str(self.stats.total_games)),
            (QCoreApplication.translate("Main", "Vitórias:"), str(self.stats.wins)),
            (QCoreApplication.translate("Main", "Derrotas:"), str(self.stats.losses)),
            (QCoreApplication.translate("Main", "Empates:"), str(self.stats.draws)),
            (QCoreApplication.translate("Main", "Taxa de Vitórias:"), f"{win_rate:.1f}%"),
            (QCoreApplication.translate("Main", "Sequência Atual:"), str(self.stats.win_streak)),
            (QCoreApplication.translate("Main", "Melhor Sequência:"), str(self.stats.best_streak)),
        ]
        
        for i, (label, value) in enumerate(stats_data):
            stats_layout.addWidget(QLabel(label), i, 0)
            stats_layout.addWidget(QLabel(value), i, 1)
            
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        close_btn = QPushButton(QCoreApplication.translate("Main", "Fechar"))
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

class SettingsDialog(QDialog):
    def __init__(self, settings: GameSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle(QCoreApplication.translate("Main", "Configurações"))
        self.setFixedSize(400, 400)
        
        layout = QVBoxLayout()
        
        conf_group = QGroupBox(QCoreApplication.translate("Main", "Confiança de Detecção"))
        conf_layout = QVBoxLayout()
        
        self.detection_slider = QSlider(Qt.Horizontal)
        self.detection_slider.setRange(50, 95)
        self.detection_slider.setValue(int(self.settings.detection_confidence * 100))
        
        self.detection_label = QLabel(f"{self.settings.detection_confidence:.2f}")
        self.detection_slider.valueChanged.connect(
            lambda v: self.detection_label.setText(f"{v/100:.2f}")
        )
        
        conf_layout.addWidget(self.detection_slider)
        conf_layout.addWidget(self.detection_label)
        conf_group.setLayout(conf_layout)
        layout.addWidget(conf_group)
        
        countdown_group = QGroupBox(QCoreApplication.translate("Main", "Duração da Contagem Regressiva"))
        countdown_layout = QHBoxLayout()
        
        self.countdown_spin = QSpinBox()
        self.countdown_spin.setRange(1, 10)
        self.countdown_spin.setValue(self.settings.countdown_duration)
        self.countdown_spin.setSuffix(QCoreApplication.translate("Main", " segundos"))
        
        countdown_layout.addWidget(self.countdown_spin)
        countdown_group.setLayout(countdown_layout)
        layout.addWidget(countdown_group)
        
        self.landmarks_checkbox = QCheckBox(QCoreApplication.translate("Main", "Mostrar Pontos de Mão"))
        self.landmarks_checkbox.setChecked(self.settings.show_landmarks)
        layout.addWidget(self.landmarks_checkbox)
        
        self.sound_checkbox = QCheckBox(QCoreApplication.translate("Main", "Ativar Efeitos Sonoros"))
        self.sound_checkbox.setChecked(self.settings.sound_enabled)
        layout.addWidget(self.sound_checkbox)
        
        language_group = QGroupBox(QCoreApplication.translate("Main", "Idioma"))
        language_layout = QHBoxLayout()
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Português (BR)", "English"])
        self.language_combo.setCurrentText("Português (BR)" if self.settings.language == "pt_BR" else "English")
        language_layout.addWidget(self.language_combo)
        
        language_group.setLayout(language_layout)
        layout.addWidget(language_group)
        
        button_layout = QHBoxLayout()
        save_btn = QPushButton(QCoreApplication.translate("Main", "Salvar"))
        cancel_btn = QPushButton(QCoreApplication.translate("Main", "Cancelar"))
        
        save_btn.clicked.connect(self.save_settings)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def save_settings(self):
        self.settings.detection_confidence = self.detection_slider.value() / 100
        self.settings.countdown_duration = self.countdown_spin.value()
        self.settings.show_landmarks = self.landmarks_checkbox.isChecked()
        self.settings.sound_enabled = self.sound_checkbox.isChecked()
        self.settings.language = "pt_BR" if self.language_combo.currentText() == "Português (BR)" else "en"
        self.accept()

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
        self.camera_label.setStyleSheet("border: 2px solid #0066cc; background: #000000;")
        layout.addWidget(self.camera_label)
        
        camera_controls = QHBoxLayout()
        
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
        
        title = QLabel(QCoreApplication.translate("Main", "HandsGestureRPS"))
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 24, QFont.Bold))
        layout.addWidget(title)
        
        score_group = QGroupBox(QCoreApplication.translate("Main", "Placar"))
        score_layout = QGridLayout()
        
        score_layout.addWidget(QLabel(QCoreApplication.translate("Main", "Vitórias:")), 0, 0)
        self.wins_label = QLabel(str(self.stats.wins))
        score_layout.addWidget(self.wins_label, 0, 1)
        
        score_layout.addWidget(QLabel(QCoreApplication.translate("Main", "Derrotas:")), 1, 0)
        self.losses_label = QLabel(str(self.stats.losses))
        score_layout.addWidget(self.losses_label, 1, 1)
        
        score_layout.addWidget(QLabel(QCoreApplication.translate("Main", "Empates:")), 2, 0)
        self.draws_label = QLabel(str(self.stats.draws))
        score_layout.addWidget(self.draws_label, 2, 1)
        
        score_group.setLayout(score_layout)
        layout.addWidget(score_group)
        
        self.status_label = QLabel(QCoreApplication.translate("Main", "Pronto para jogar!"))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 16))
        layout.addWidget(self.status_label)
        
        gesture_group = QGroupBox(QCoreApplication.translate("Main", "Gesto Atual"))
        gesture_layout = QVBoxLayout()
        
        self.gesture_label = QLabel(QCoreApplication.translate("Main", "Nenhum gesto detectado"))
        self.gesture_label.setAlignment(Qt.AlignCenter)
        self.gesture_label.setFont(QFont("Arial", 14))
        gesture_layout.addWidget(self.gesture_label)
        
        self.fingers_label = QLabel(QCoreApplication.translate("Main", f"Dedos detectados: {self.last_finger_count}"))
        self.fingers_label.setAlignment(Qt.AlignCenter)
        self.fingers_label.setFont(QFont("Arial", 12))
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
            "rock": QCoreApplication.translate("Main", "Pedra"),
            "paper": QCoreApplication.translate("Main", "Papel"),
            "scissors": QCoreApplication.translate("Main", "Tesoura"),
            "unknown": QCoreApplication.translate("Main", "Desconhecido")
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
        
        self.opponent_gesture = random.choice([Gesture.ROCK.value, Gesture.PAPER.value, Gesture.SCISSORS.value])
        
        if self.player_gesture is None:
            self.player_gesture = Gesture.UNKNOWN.value
            
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
            "rock": QCoreApplication.translate("Main", "Pedra"),
            "paper": QCoreApplication.translate("Main", "Papel"),
            "scissors": QCoreApplication.translate("Main", "Tesoura"),
            "unknown": QCoreApplication.translate("Main", "Desconhecido")
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
        
    def save_settings(self):
        settings = QSettings("xAI", "HandsGestureRPS")
        settings.setValue("detection_confidence", self.settings.detection_confidence)
        settings.setValue("countdown_duration", self.settings.countdown_duration)
        settings.setValue("sound_enabled", self.settings.sound_enabled)
        settings.setValue("show_landmarks", self.settings.show_landmarks)
        settings.setValue("language", self.settings.language)
        
    def save_stats(self):
        try:
            with open("game_stats.json", "w") as f:
                json.dump(asdict(self.stats), f)
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")
            
    def apply_theme(self):
        self.setStyleSheet(ThemeManager.get_dark_theme())
        
    def closeEvent(self, event):
        if self.gesture_detector:
            self.stop_camera()
        if self.settings.auto_save:
            self.save_settings()
            self.save_stats()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    game = HandsGestureRPS()
    game.show()
    sys.exit(app.exec_())