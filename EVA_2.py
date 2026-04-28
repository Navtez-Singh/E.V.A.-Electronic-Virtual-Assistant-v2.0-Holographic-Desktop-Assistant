import sys
import os
import speech_recognition as sr
import pyttsx3
from groq import Groq
from datetime import datetime
import re
import webbrowser
import sqlite3

from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QMovie

# --- 1. LINUX WAYLAND FIX ---
if sys.platform.startswith('linux'):
    os.environ["QT_QPA_PLATFORM"] = "xcb"

# --- 2. CONFIGURATION ---
# >>> PUT YOUR GROQ API KEY HERE <<<
API_KEY = "ENTER API KEY " 
client = Groq(api_key=API_KEY)

# --- 3. CROSS-PLATFORM FILE PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'eva_memory.db')
GIF_PATH = os.path.join(BASE_DIR, 'hud.gif')

def setup_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            content TEXT
        )
    ''')
    conn.commit()
    return conn

# --- 4. BACKEND AI & VOICE THREAD ---
class EvaBackend(QThread):
    status_signal = pyqtSignal(str)
    subtitle_signal = pyqtSignal(str)
    animation_signal = pyqtSignal(str) 

    def run(self):
        self.db_conn = setup_database()
        self.engine = pyttsx3.init()
        self.setup_voice()
        self.run_eva()

    def setup_voice(self):
        voices = self.engine.getProperty('voices')
        voice_found = False
        
        # Looks for Indian female (Windows) or Linux female (+f3/+f4)
        target_keywords = ['india', 'hindi', 'kalpana', 'zira', 'female', '+f3', '+f4']
        
        for voice in voices:
            name_id = (voice.name + " " + voice.id).lower()
            if any(key in name_id for key in target_keywords):
                self.engine.setProperty('voice', voice.id)
                voice_found = True
                break
        
        if not voice_found and len(voices) > 1:
            self.engine.setProperty('voice', voices[1].id)
            
        self.engine.setProperty('rate', 175) 

    def speak(self, text):
        clean_text = re.sub(r'[^\w\s.,!?\'"-]', '', text)
        self.status_signal.emit("E.V.A. is speaking...")
        self.subtitle_signal.emit(clean_text)
        
        self.animation_signal.emit("speaking") 
        self.engine.say(clean_text)
        self.engine.runAndWait()
        self.animation_signal.emit("standby")

    def get_ai_response(self, question):
        try:
            self.status_signal.emit("E.V.A. is thinking...")
            
            system_instruction = """
            You are E.V.A., a highly advanced AI assistant. 
            CRITICAL RULE: You MUST mirror the exact language the user speaks to you. 
            - If the user speaks pure English, reply in pure English.
            - If the user speaks pure Hindi or Punjabi, reply in that language.
            - If the user mixes them (Hinglish), reply in Hinglish.
            IMPORTANT: When speaking Hindi, Punjabi, or Hinglish, ALWAYS use the Latin/English alphabet (Romanized script, e.g., 'Main samajh gayi Sir'). NEVER output Devanagari or Gurmukhi script.
            Keep your tone highly capable, professional, and analytical. Address the user as 'Sir'. Keep answers concise (1-2 sentences). Do NOT use emojis.
            """
            
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": question}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.6,
                max_tokens=100
            )
            return response.choices[0].message.content
        except Exception:
            return "Mainframe connection failed, Sir. Network error."

    def run_eva(self):
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 400 
        recognizer.dynamic_energy_threshold = True 
        
        wake_words = ["eva", "hey eva", "suno eva", "uth ja eva"]
        close_words = ["shut down eva", "band ho ja", "power off"]
        sleep_words = ["standby eva", "chup kar", "shant ho ja"]
        
        is_awake = False 
        self.status_signal.emit("System Online (Standby)")
        self.subtitle_signal.emit("Say 'Hey E.V.A.' to begin.")
        self.animation_signal.emit("standby")

        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            
            while True:
                try:
                    if is_awake:
                        self.status_signal.emit("Listening (Online)")
                        self.animation_signal.emit("listening")
                    else:
                        self.status_signal.emit("Listening (Standby)")
                        self.animation_signal.emit("standby")
                    
                    audio = recognizer.listen(source, timeout=None, phrase_time_limit=8)
                    self.status_signal.emit("Processing Audio...")
                    
                    input_text = recognizer.recognize_google(audio, language="en-IN").lower()
                    self.subtitle_signal.emit(f"You: '{input_text}'")

                    if any(word in input_text for word in close_words):
                        self.speak("Shutting down core systems. Alvida, Sir.")
                        self.db_conn.close()
                        QApplication.quit() 
                        break 
                    
                    if not is_awake:
                        for word in wake_words:
                            if word in input_text:
                                is_awake = True
                                command = input_text.split(word, 1)[-1].strip()
                                if command:
                                    self.speak(self.get_ai_response(command))
                                else:
                                    self.speak("Systems online. I am listening, Sir.")
                                break 

                    else:
                        if any(word in input_text for word in sleep_words):
                            is_awake = False
                            self.speak("Entering standby mode, Sir.")
                        
                        elif 'remember' in input_text or 'yaad rakhna' in input_text:
                            note = input_text.replace('eva', '').replace('remember', '').replace('that', '').replace('yaad rakhna', '').strip()
                            if note:
                                cursor = self.db_conn.cursor()
                                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                cursor.execute("INSERT INTO notes (timestamp, content) VALUES (?, ?)", (timestamp, note))
                                self.db_conn.commit()
                                self.speak("I have logged that into my database, Sir.")
                            else:
                                self.speak("What would you like me to remember, Sir?")

                        elif 'my notes' in input_text or 'kya yaad' in input_text or 'what did i ask' in input_text:
                            cursor = self.db_conn.cursor()
                            cursor.execute("SELECT content FROM notes ORDER BY id DESC LIMIT 3") 
                            records = cursor.fetchall()
                            if records:
                                self.speak("Here are your most recent records, Sir.")
                                for record in records:
                                    self.speak(record[0])
                            else:
                                self.speak("Your database is currently empty, Sir.")

                        elif any(cmd in input_text for cmd in ['open youtube', 'youtube khol']):
                            self.speak("Accessing YouTube now, Sir.")
                            webbrowser.open("https://www.youtube.com")
                        
                        elif any(cmd in input_text for cmd in ['open google', 'google khol']):
                            self.speak("Bringing up Google.")
                            webbrowser.open("https://www.google.com")

                        elif any(cmd in input_text for cmd in ['open notepad', 'notepad khol']):
                            self.speak("Opening text editor.")
                            if sys.platform.startswith('linux'):
                                os.system("gedit &") 
                            elif sys.platform == 'darwin': 
                                os.system("open -a TextEdit")
                            else:
                                os.system("notepad") 
                        
                        elif any(cmd in input_text for cmd in ['open calculator', 'calculator khol', 'hisaab']):
                            self.speak("Launching calculator.")
                            if sys.platform.startswith('linux'):
                                os.system("gnome-calculator &") 
                            elif sys.platform == 'darwin':
                                os.system("open -a Calculator")
                            else:
                                os.system("calc")

                        elif any(cmd in input_text for cmd in ['lock my pc', 'lock kar', 'screen lock']):
                            self.speak("Securing your workstation now, Sir.")
                            if sys.platform.startswith('linux'):
                                os.system("xdg-screensaver lock") 
                            elif sys.platform == 'darwin':
                                os.system("pmset displaysleepnow")
                            else:
                                os.system("rundll32.exe user32.dll,LockWorkStation")
                        
                        else:
                            self.speak(self.get_ai_response(input_text))

                except sr.UnknownValueError:
                    pass 
                except sr.RequestError:
                    self.status_signal.emit("Network Error")
                except Exception as e:
                    print(f"Error: {e}")

# --- 5. FRONTEND UI ---
class EvaWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(450, 450) 
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)

        nav_layout = QHBoxLayout()
        nav_layout.addStretch() 
        
        self.min_btn = QPushButton("—")
        self.min_btn.setFixedSize(30, 30)
        self.min_btn.setStyleSheet("QPushButton { color: white; background: rgba(50, 50, 50, 150); border-radius: 15px; font-weight: bold; } QPushButton:hover { background: rgba(100, 100, 100, 200); }")
        self.min_btn.clicked.connect(self.showMinimized)
        
        self.close_btn = QPushButton("X")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setStyleSheet("QPushButton { color: white; background: rgba(200, 50, 50, 150); border-radius: 15px; font-weight: bold; } QPushButton:hover { background: rgba(255, 50, 50, 200); }")
        self.close_btn.clicked.connect(self.close_app)

        nav_layout.addWidget(self.min_btn)
        nav_layout.addWidget(self.close_btn)
        main_layout.addLayout(nav_layout)

        self.gif_label = QLabel(self)
        
        # Failsafe if the GIF is missing
        if os.path.exists(GIF_PATH):
            self.movie = QMovie(GIF_PATH) 
            self.gif_label.setMovie(self.movie)
            self.movie.start()
        else:
            self.gif_label.setText("[HUD.GIF NOT FOUND]")
            self.gif_label.setStyleSheet("color: red; font-size: 20px;")
            
        main_layout.addWidget(self.gif_label, alignment=Qt.AlignCenter)

        self.status_label = QLabel("Initializing Systems...", self)
        self.status_label.setStyleSheet("color: #00FFCC; font-size: 16px; font-weight: bold; font-family: Courier; background: rgba(0,0,0,150); border-radius: 5px; padding: 2px;")
        main_layout.addWidget(self.status_label, alignment=Qt.AlignCenter)

        self.subtitle_label = QLabel("", self)
        self.subtitle_label.setStyleSheet("color: white; font-size: 14px; font-family: Courier; background: rgba(0,0,0,150); border-radius: 5px; padding: 2px;")
        self.subtitle_label.setWordWrap(True)
        main_layout.addWidget(self.subtitle_label, alignment=Qt.AlignCenter)

        self.setLayout(main_layout)

        self.backend = EvaBackend()
        self.backend.status_signal.connect(self.update_status)
        self.backend.subtitle_signal.connect(self.update_subtitle)
        self.backend.animation_signal.connect(self.sync_animation)
        self.backend.start()

    def update_status(self, text):
        self.status_label.setText(text)

    def update_subtitle(self, text):
        self.subtitle_label.setText(text)

    def sync_animation(self, state):
        if hasattr(self, 'movie'):
            if state == "standby":
                self.movie.setSpeed(50) 
            elif state == "listening":
                self.movie.setSpeed(100) 
            elif state == "speaking":
                self.movie.setSpeed(250) 

    def close_app(self):
        QApplication.quit()

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = event.globalPos() - self.oldPos
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = EvaWidget()
    window.show()
    sys.exit(app.exec_())

#IMPORTANT NOTICE
'''copy and paste given line below in terminal to run the code 

#If you are on Windows :
pip install SpeechRecognition pyttsx3 groq PyQt5 PyAudio

#If you are on Linux :
Linux sometimes requires you to use pip3 instead of pip. 
pip3 install SpeechRecognition pyttsx3 groq PyQt5 PyAudio'''




"""
PROJECT: E.V.A. (Electronic Virtual Assistant)
AUTHOR: Navtez Singh
VERSION: 2.0 (Full Stack Holographic Edition)

DESCRIPTION:
A multi-threaded Windows Desktop Assistant featuring:
- Speech Recognition with Hinglish/Punglish support.
- Llama 3.3 70B LLM integration via Groq for high-reasoning logic.
- SQLite3 Persistent Database for localized note-taking and memory.
- PyQt5 GUI with a frameless, transparent holographic HUD.
- Multi-threading architecture to separate UI rendering from AI processing.
"""

# --- LIBRARY EXPLANATIONS ---
# sys, os, webbrowser: Handle system-level operations and web navigation.
# speech_recognition (sr): Converts microphone input into string data.
# pyttsx3: Offline Text-to-Speech engine for system responses.
# Groq: Client for high-speed inference of the Llama 3.3 model.
# sqlite3: Lightweight relational database for the 'Remember' feature.
# PyQt5: Professional UI toolkit used to create the animated desktop overlay.