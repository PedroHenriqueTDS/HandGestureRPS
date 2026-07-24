from enum import Enum
from dataclasses import dataclass
from typing import Dict

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
    camera_index: int = 0
    theme: str = "dark"
    language: str = "pt_BR"
    sound_enabled: bool = True
    fullscreen: bool = False
    difficulty: Difficulty = Difficulty.MEDIUM
    game_mode: GameMode = GameMode.SINGLE_PLAYER
    auto_save: bool = True
    show_landmarks: bool = True
