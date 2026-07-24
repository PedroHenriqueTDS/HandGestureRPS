import os
import time
import joblib
import cv2
import mediapipe as mp
import numpy as np
from typing import Tuple
from PyQt5.QtCore import QThread, pyqtSignal

from utils.logger import setup_logging
from models.game_models import GameSettings, Gesture

logger = setup_logging()

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
        self.model = None
        try:
            model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "gesture_model.pkl")
            if os.path.exists(model_path):
                self.model = joblib.load(model_path)
                logger.info("Modelo ML carregado com sucesso!")
        except Exception as e:
            logger.error(f"Erro ao carregar modelo ML: {e}")
        
    def initialize_camera(self):
        try:
            self.cap = cv2.VideoCapture(self.settings.camera_index)
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera {self.settings.camera_index}")
                return False
                        
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
            
    def extract_features(self, landmarks):
        points = np.array([[lm.x, lm.y] for lm in landmarks.landmark])
        base = points[0]
        points = points - base
        max_dist = np.max(np.linalg.norm(points, axis=1))
        if max_dist > 0:
            points = points / max_dist
        return points.flatten().tolist()
            
    def rule_based_classify(self, landmarks) -> Tuple[str, float, int]:
        if self.model is not None:
            try:
                features = self.extract_features(landmarks)
                gesture = self.model.predict([features])[0]
                return gesture, 1.0, 0
            except Exception as e:
                logger.error(f"ML classification error: {e}")
                
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
