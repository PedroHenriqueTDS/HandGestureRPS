from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QGridLayout, QLabel, QPushButton,
    QHBoxLayout, QSlider, QSpinBox, QCheckBox, QComboBox
)
from PyQt5.QtCore import Qt, QCoreApplication

from models.game_models import GameStats, GameSettings

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
