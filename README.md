# E.V.A.-Electronic-Virtual-Assistant-v2.0-Holographic-Desktop-Assistant
E.V.A. is a high-performance, multi-threaded desktop AI assistant designed for seamless human-computer interaction. It features a futuristic, frameless "holographic" HUD built with PyQt5 and is powered by the Llama 3.3 70B model for advanced reasoning and multi-lingual support (English, Hindi, and Punjabi).

# E.V.A. (Electronic Virtual Assistant) - Version 2.0 🌐

E.V.A. is a highly advanced, multi-threaded desktop virtual assistant built with Python. Designed with a transparent, frameless holographic HUD, E.V.A. utilizes the high-reasoning logic of the Llama 3.3 70B model via the Groq API to provide intelligent, concise, and context-aware responses. 

Unlike standard assistants, E.V.A. features robust native support for English, Hindi, Punjabi, and mixed-language inputs (Hinglish/Punglish).

## ✨ Key Features
* **Advanced AI Logic:** Powered by Llama-3.3-70b-versatile via Groq for rapid, highly analytical responses.
* **Holographic UI:** A frameless, draggable PyQt5 interface with dynamic animations synced to E.V.A.'s current state (Standby, Listening, Speaking).
* **Multi-Threaded Architecture:** Separates the UI rendering from the heavy AI processing and audio listening, ensuring the desktop overlay never freezes.
* **Multilingual Speech Recognition:** Dynamic ambient noise adjustment and wake-word detection tuned for Indian accents and regional languages.
* **Persistent Memory:** Integrated SQLite3 database allows E.V.A. to take notes and remember user requests across sessions.
* **Cross-Platform:** Built-in OS detection ensures web browsing, application launching (Notepad/Calculator), and screen locking work seamlessly across Windows, Linux, and macOS.

## 🛠️ Tech Stack
* **Language:** Python 3
* **LLM Engine:** Groq API (Llama 3.3 70B)
* **GUI Toolkit:** PyQt5
* **Audio & Speech:** SpeechRecognition, pyttsx3, PyAudio
* **Database:** SQLite3

## 🚀 Quick Start
1. Clone the repository.
2. Install the required dependencies:
   ```bash
   pip install SpeechRecognition pyttsx3 groq PyQt5 PyAudio
