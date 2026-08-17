"""Sound effects for FluidSim Linux interactions."""
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtCore import QUrl
from pathlib import Path


class SoundManager:
    """Manages sound effects for UI interactions."""
    
    def __init__(self, parent=None):
        self._parent = parent
        self._sounds = {}
        self._enabled = True
        self._load_sounds()
    
    def _load_sounds(self):
        """Load sound effects from assets/sounds/ directory."""
        sound_dir = Path(__file__).parent.parent.parent / "assets" / "sounds"
        if not sound_dir.exists():
            return
        
        for wav_file in sound_dir.glob("*.wav"):
            name = wav_file.stem
            sound = QSoundEffect()
            sound.setSource(QUrl.fromLocalFile(str(wav_file)))
            self._sounds[name] = sound
    
    def play(self, sound_name: str, volume: float = 0.5):
        """Play a named sound effect."""
        if not self._enabled:
            return
        sound = self._sounds.get(sound_name)
        if sound:
            sound.setVolume(volume)
            sound.play()
    
    def place(self):
        self.play("place", 0.6)
    
    def wire(self):
        self.play("wire", 0.5)
    
    def toggle(self):
        self.play("toggle", 0.5)
    
    def delete(self):
        self.play("delete", 0.4)
    
    def error(self):
        self.play("error", 0.7)
    
    def sim_start(self):
        # Quick positive chirp
        self.play("place", 0.4)
    
    def sim_stop(self):
        self.play("toggle", 0.3)
