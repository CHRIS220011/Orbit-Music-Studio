import sys
import numpy as np
import pyaudio
import wave
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QLabel, QMessageBox, QFrame)
from PyQt6.QtCore import Qt

class OrbitStudio(QWidget):
    def __init__(self):
        super().__init__()
        # --- PERSONALIZACJA ---
        self.author = "Krystian Woś (Chris)"
        self.version = "1.0 (Ferie 2026 Edition)"
        
        self.setWindowTitle(f"Orbit Music Studio - Created by {self.author}")
        self.setGeometry(100, 100, 700, 500)
        
        # Stylizacja "Dark Orbit"
        self.setStyleSheet("""
            QWidget {
                background-color: #0d1117;
                color: #c9d1d9;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #30363d;
                border-color: #8b949e;
            }
            QListWidget {
                background-color: #010409;
                border: 1px solid #30363d;
                border-radius: 6px;
            }
        """)
        
        self.recorded_samples = []
        self.scale = {
            'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23,
            'G4': 392.00, 'A4': 440.00, 'B4': 493.88, 'C5': 523.25
        }
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("ORBIT MUSIC ENGINE")
        header.setStyleSheet("font-size: 24px; color: #58a6ff; font-weight: bold;")
        layout.addWidget(header, alignment=Qt.AlignmentFlag.AlignCenter)
        
        sub_header = QLabel(f"Wersja: {self.version}")
        layout.addWidget(sub_header, alignment=Qt.AlignmentFlag.AlignCenter)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #30363d;")
        layout.addWidget(line)
        
        # Lista nut
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
        # Statystyki
        self.stats_label = QLabel("Nuty: 0 | Długość: 0.0s")
        layout.addWidget(self.stats_label)
        
        # Klawiatura
        keys_layout = QHBoxLayout()
        for note_name in self.scale.keys():
            btn = QPushButton(note_name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, n=note_name: self.add_note(n))
            keys_layout.addWidget(btn)
        layout.addLayout(keys_layout)
        
        # Dolne przyciski
        bottom_layout = QHBoxLayout()
        
        self.btn_save = QPushButton("EKSPORTUJ .WAV")
        self.btn_save.setStyleSheet("background-color: #238636; color: white;")
        self.btn_save.clicked.connect(self.save_to_wav)
        
        self.btn_info = QPushButton("O TWÓRCY")
        self.btn_info.clicked.connect(self.show_info)
        
        self.btn_clear = QPushButton("RESET")
        self.btn_clear.clicked.connect(self.clear_notes)
        
        bottom_layout.addWidget(self.btn_info)
        bottom_layout.addWidget(self.btn_clear)
        bottom_layout.addWidget(self.btn_save)
        layout.addLayout(bottom_layout)
        
        self.setLayout(layout)

    def generate_square_wave(self, freq, duration=0.3):
        t = np.arange(44100 * duration)
        samples = (np.sin(2 * np.pi * t * freq / 44100) > 0).astype(np.float32)
        return samples * 0.5

    def add_note(self, note_name):
        sample = self.generate_square_wave(self.scale[note_name])
        self.recorded_samples.extend(sample)
        self.list_widget.addItem(f"Nuta {note_name}")
        self.list_widget.scrollToBottom()
        
        # Aktualizacja statystyk
        count = len(self.list_widget)
        self.stats_label.setText(f"Nuty: {count} | Długość: {round(count * 0.3, 1)}s")
        
        # Odtwarzanie (uproszczone dla szybkości)
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paFloat32, channels=1, rate=44100, output=True)
        stream.write(sample.tobytes())
        stream.close()
        p.terminate()

    def show_info(self):
        QMessageBox.about(self, "O programie", 
            f"Orbit Music Studio v1.0\n\n"
            f"Program napisany przez:\n{self.author}\n\n"
            "System operacyjny: Orbit OS\nRok produkcji: 2026")

    def save_to_wav(self):
        if not self.recorded_samples: return
        filename = "orbit_song_by_chris.wav"
        out_samples = (np.array(self.recorded_samples) * 32767).astype(np.int16)
        with wave.open(filename, 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(44100)
            f.writeframes(out_samples.tobytes())
        QMessageBox.information(self, "Sukces!", f"Utwór zapisany jako {filename}")

    def clear_notes(self):
        self.recorded_samples = []
        self.list_widget.clear()
        self.stats_label.setText("Nuty: 0 | Długość: 0.0s")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OrbitStudio()
    window.show()
    sys.exit(app.exec())
