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
