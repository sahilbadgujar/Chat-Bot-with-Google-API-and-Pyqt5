import sys
import os
import json
import speech_recognition as sr
import pyttsx3
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

def load_api_key(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)
        return config['api_key']

api_key = load_api_key('config.json')
genai.configure(api_key=api_key)

# Create the model with default generation config
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

chat_session = model.start_chat(
    history=[]
)

engine = pyttsx3.init()  # Initialize text-to-speech engine

class VoiceRecognitionThread(QThread):
    recognized_text = pyqtSignal(str)

    def run(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)
            try:
                text = recognizer.recognize_google(audio)
                self.recognized_text.emit(text)
            except sr.UnknownValueError:
                self.recognized_text.emit("Could not understand the audio")
            except sr.RequestError:
                self.recognized_text.emit("Could not request results; check your network connection")

class ChatBot(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.resize(1200, 900)
        self.setWindowTitle('Simple Chatbot')

        # Chat box
        self.chat_box = QTextEdit()
        self.chat_box.setReadOnly(True)
        self.chat_box.setStyleSheet("font-size: 30px;")

        # Input box
        self.input_box = QLineEdit()
        self.input_box.returnPressed.connect(self.send_message)
        self.input_box.setFixedHeight(60)
        self.input_box.setStyleSheet("font-size: 20px;")

        # Submit button
        self.submit_button = QPushButton('Send')
        self.submit_button.setFixedHeight(60)
        self.submit_button.setStyleSheet("font-size: 20px;")
        self.submit_button.clicked.connect(self.send_message)

        # Voice command button
        self.voice_button = QPushButton('Voice Command')
        self.voice_button.setFixedHeight(60)
        self.voice_button.setStyleSheet("font-size: 20px;")
        self.voice_button.clicked.connect(self.start_voice_recognition)

        # Layout
        vbox = QVBoxLayout()
        vbox.addWidget(self.chat_box)

        hbox = QHBoxLayout()
        hbox.addWidget(self.input_box)
        hbox.addWidget(self.submit_button)
        hbox.addWidget(self.voice_button)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

        # Voice recognition thread
        self.voice_thread = VoiceRecognitionThread()
        self.voice_thread.recognized_text.connect(self.update_input_box)

    def send_message(self):
        user_text = self.input_box.text()
        if user_text == "":
            self.input_box.setText("Listening...")
            return

        self.chat_box.append(f"<div style='text-align: right; color: blue;'>You: {user_text}</div>")
        self.input_box.setText("")

        # Call the API to get the bot response
        try:
            response = chat_session.send_message(user_text)
            bot_response = response.text
        except Exception as e:
            bot_response = f"An error occurred: {e}"

        # Show the bot response in the chatbox
        self.chat_box.append(f"<div style='text-align: left; color: green;'>Bot: {bot_response}</div>")

        # Use QTimer to delay the speech synthesis
        QTimer.singleShot(100, lambda: self.speak_response(bot_response))

    def start_voice_recognition(self):
        self.input_box.setText("Listening...")
        self.voice_thread.start()

    def update_input_box(self, text):
        self.input_box.setText(text)

    def speak_response(self, response):
        engine.say(response)
        engine.runAndWait()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    chatbot = ChatBot()
    chatbot.show()
    sys.exit(app.exec_())
