import sys
import numpy as np
import pyaudio
import wave
import threading
import queue
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QLabel, QMessageBox, QFrame, QTabWidget, QComboBox)
from PyQt6.QtCore import Qt

class OrbitStudio(QWidget):
    def __init__(self):
        super().__init__()
        self.author = "Krystian Woś (Chris)"
        self.version = "2.0 Gold Master"
        
        # --- JĘZYKI ---
        self.lang_data = {
            "PL": {"header": "SILNIK MUZYCZNY ORBIT", "reset": "RESETUJ", "stats": "Nuty: ", "tab_rel": "RELAKSUJĄCE", "tab_norm": "NORMALNE", "tab_bass": "BASOWE", "save": "GENERUJ MASTER WAV", "info_btn": "O TWÓRCY"},
            "EN": {"header": "ORBIT MUSIC ENGINE", "reset": "RESET", "stats": "Notes: ", "tab_rel": "RELAXING", "tab_norm": "NORMAL", "tab_bass": "BASS", "save": "GENERATE MASTER WAV", "info_btn": "ABOUT AUTHOR"},
            "UA": {"header": "МУЗИЧНИЙ ДВИГУН ORBIT", "reset": "СКИДАННЯ", "stats": "Ноти: ", "tab_rel": "РЕЛАКС", "tab_norm": "НОРМАЛЬНІ", "tab_bass": "БАСИ", "save": "ЗГЕНЕРУВАТИ WAV", "info_btn": "ПРО АВТОРА"}
        }
        self.current_lang = "PL"

        # --- MOTYWY ---
        self.themes = {
            "Spokojna Czerń": "QWidget { background-color: #0d1117; color: #c9d1d9; } QPushButton { background-color: #21262d; border: 1px solid #30363d; }",
            "Spokojny Błękit": "QWidget { background-color: #eef2f7; color: #334455; } QPushButton { background-color: #d0e1f9; border: 1px solid #b0c4de; }",
            "Spokojna Zieleń": "QWidget { background-color: #f0f4f0; color: #2d3a2d; } QPushButton { background-color: #d5e8d5; border: 1px solid #b8cfb8; }",
            "Spokojna Biel": "QWidget { background-color: #ffffff; color: #333333; } QPushButton { background-color: #f5f5f5; border: 1px solid #dddddd; }"
        }

        # Silnik Audio
        self.audio_queue = queue.Queue()
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paFloat32, channels=1, rate=44100, output=True)
        threading.Thread(target=self._audio_worker, daemon=True).start()
        
        self.recorded_samples = []
        self.scale = {'1': ('C4', 261.63), '2': ('D4', 293.66), '3': ('E4', 329.63), '4': ('F4', 349.23),
                      '5': ('G4', 392.00), '6': ('A4', 440.00), '7': ('B4', 493.88), '8': ('C5', 523.25)}
        
        self.init_ui()
        self.change_theme("Spokojna Czerń")

    def init_ui(self):
        self.main_layout = QVBoxLayout()
        control_bar = QHBoxLayout()
        self.theme_combo = QComboBox(); self.theme_combo.addItems(list(self.themes.keys())); self.theme_combo.currentTextChanged.connect(self.change_theme)
        self.lang_combo = QComboBox(); self.lang_combo.addItems(["PL", "EN", "UA"]); self.lang_combo.currentTextChanged.connect(self.change_lang)
        control_bar.addWidget(QLabel("Motyw:")); control_bar.addWidget(self.theme_combo); control_bar.addStretch(); control_bar.addWidget(QLabel("Język:")); control_bar.addWidget(self.lang_combo)
        self.main_layout.addLayout(control_bar)

        top_bar = QHBoxLayout()
        self.header_label = QLabel(); self.header_label.setStyleSheet("font-size: 22px; font-weight: bold;")
        self.btn_reset = QPushButton(); self.btn_reset.setStyleSheet("background-color: #ff4444; color: white;"); self.btn_reset.clicked.connect(self.clear_notes)
        top_bar.addWidget(self.header_label); top_bar.addStretch(); top_bar.addWidget(self.btn_reset)
        self.main_layout.addLayout(top_bar)

        self.tabs = QTabWidget()
        self.tab_rel = self.create_keyboard_tab("relaks"); self.tab_norm = self.create_keyboard_tab("normal"); self.tab_bass = self.create_keyboard_tab("bass")
        self.tabs.addTab(self.tab_rel, ""); self.tabs.addTab(self.tab_norm, ""); self.tabs.addTab(self.tab_bass, "")
        self.main_layout.addWidget(self.tabs)
        
        self.list_widget = QListWidget(); self.main_layout.addWidget(self.list_widget)
        self.stats_label = QLabel(); self.main_layout.addWidget(self.stats_label)
        
        footer_bar = QHBoxLayout()
        self.btn_info = QPushButton(); self.btn_info.clicked.connect(self.show_info)
        self.btn_save = QPushButton(); self.btn_save.clicked.connect(self.save_to_wav)
        footer_bar.addWidget(self.btn_info); footer_bar.addWidget(self.btn_save)
        self.main_layout.addLayout(footer_bar)
        self.setLayout(self.main_layout); self.update_texts()

    def change_theme(self, t): self.setStyleSheet(self.themes[t] + "QPushButton { border-radius: 6px; padding: 10px; font-weight: bold; }")
    def change_lang(self, l): self.current_lang = l; self.update_texts()
    def update_texts(self):
        d = self.lang_data[self.current_lang]
        self.header_label.setText(d["header"]); self.btn_reset.setText(d["reset"]); self.tabs.setTabText(0, d["tab_rel"]); self.tabs.setTabText(1, d["tab_norm"]); self.tabs.setTabText(2, d["tab_bass"]); self.btn_save.setText(d["save"]); self.btn_info.setText(d["info_btn"]); self.stats_label.setText(f"{d['stats']} {self.list_widget.count()}")

    def create_keyboard_tab(self, mode):
        tab = QWidget(); layout = QHBoxLayout()
        for key, (name, freq) in self.scale.items():
            btn = QPushButton(f"{name}\n[{key}]"); btn.clicked.connect(lambda checked, k=key, m=mode: self.add_note(k, m)); layout.addWidget(btn)
        tab.setLayout(layout); return tab

    def _audio_worker(self):
        while True:
            sample = self.audio_queue.get()
            if sample is None: break
            self.stream.write(sample.tobytes()); self.audio_queue.task_done()

    def add_note(self, key, mode):
        note_name, freq = self.scale[key]
        duration = 0.4
        t = np.linspace(0, duration, int(44100 * duration), False)
        
        # Generowanie czystej bazy
        if mode == "relaks":
            s = 0.4 * np.sin(2 * np.pi * t * freq) + np.random.uniform(-0.015, 0.015, len(t))
        elif mode == "bass":
            s = 0.5 * np.sign(np.sin(2 * np.pi * t * (freq / 2)))
        else:
            s = 0.5 * np.sin(2 * np.pi * t * freq)

        # --- NOWY SILNIK CLARITY ---
        # 1. Envelope (wyciszanie trzasków)
        fade = int(44100 * 0.05) # 50ms fade
        envelope = np.ones(len(t))
        envelope[:fade] = np.linspace(0, 1, fade)
        envelope[-fade:] = np.linspace(1, 0, fade)
        s *= envelope

        # 2. 4-bit Dithering (poprawa wyrazistości)
        s = (np.round(s * 8) / 8) 
        
        sample = s.astype(np.float32)
        self.recorded_samples.extend(sample)
        self.list_widget.addItem(f"[{mode.upper()}] {note_name}")
        self.list_widget.scrollToBottom(); self.update_texts()
        self.audio_queue.put(sample)

    def keyPressEvent(self, event):
        key = event.text()
        if key in self.scale:
            m = ["relaks", "normal", "bass"][self.tabs.currentIndex()]
            self.add_note(key, m)

    def show_info(self): QMessageBox.about(self, "Orbit OS", f"Twórca: {self.author}\nOrbit Studio 2.0 Gold")
    
    def save_to_wav(self):
        if not self.recorded_samples: return
        fn = "orbit_gold_render.wav"
        out = (np.array(self.recorded_samples) * 32767).astype(np.int16)
        with wave.open(fn, 'wb') as f:
            f.setnchannels(1); f.setsampwidth(2); f.setframerate(44100); f.writeframes(out.tobytes())
        QMessageBox.information(self, "Orbit OS", f"Zapisano wyraźny render: {fn}")

    def clear_notes(self):
        self.recorded_samples = []; self.list_widget.clear(); self.update_texts()

if __name__ == "__main__":
    app = QApplication(sys.argv); window = OrbitStudio(); window.show(); sys.exit(app.exec())
