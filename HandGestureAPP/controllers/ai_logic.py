import json
import random
import os
import logging

logger = logging.getLogger(__name__)

class MarkovChainAI:
    def __init__(self, history_file="../historico.json"):
        # main.py is run from HandGestureAPP usually, but we need to resolve the path correctly.
        # It's better to use an absolute path or relative to the current working dir.
        # Let's assume history_file is passed from main.py
        self.history_file = history_file
        # transitions[prev_move][next_move] = count
        self.transitions = {
            "rock": {"rock": 0, "paper": 0, "scissors": 0},
            "paper": {"rock": 0, "paper": 0, "scissors": 0},
            "scissors": {"rock": 0, "paper": 0, "scissors": 0}
        }
        self.translation_map = {
            "Pedra": "rock",
            "Papel": "paper",
            "Tesoura": "scissors"
        }
        self.last_player_move = None
        self.load_history()

    def load_history(self):
        if not os.path.exists(self.history_file):
            return
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            prev_move = None
            for line in lines:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    user_move_pt = data.get("usuario")
                    user_move = self.translation_map.get(user_move_pt)
                    
                    if user_move:
                        if prev_move:
                            self.transitions[prev_move][user_move] += 1
                        prev_move = user_move
                except json.JSONDecodeError:
                    continue
            
            logger.info("MarkovChainAI history loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading history for AI: {e}")

    def update_history(self, new_move):
        """Update the transition matrix with a new move during gameplay."""
        if new_move not in ["rock", "paper", "scissors"]:
            return
            
        if self.last_player_move:
            self.transitions[self.last_player_move][new_move] += 1
            
        self.last_player_move = new_move

    def predict_next_move(self):
        """Predicts what the player will play next based on their last move."""
        if not self.last_player_move:
            return random.choice(["rock", "paper", "scissors"])
            
        next_moves = self.transitions[self.last_player_move]
        total_transitions = sum(next_moves.values())
        
        if total_transitions == 0:
            return random.choice(["rock", "paper", "scissors"])
            
        # Find the move with the highest probability
        predicted_move = max(next_moves, key=next_moves.get)
        
        return predicted_move

    def get_counter_move(self):
        """Returns the move that defeats the predicted player's move."""
        prediction = self.predict_next_move()
        
        counters = {
            "rock": "paper",
            "paper": "scissors",
            "scissors": "rock"
        }
        
        return counters.get(prediction, random.choice(["rock", "paper", "scissors"]))
