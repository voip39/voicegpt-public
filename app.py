import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from whisper_handler import transcribe_audio
from llm import generate_response
from tts import synthesize_speech
import requests
import tempfile

from dotenv import load_dotenv
load_dotenv()
ALLOWED_TOKENS = os.getenv("API_TOKENS", "").split(",")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

os.makedirs("logs", exist_ok=True)

log_formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")

file_handler = RotatingFileHandler("logs/voicegpt.log", maxBytes=1000000, backupCount=5)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(log_formatter)

error_handler = RotatingFileHandler("logs/errors.log", maxBytes=1000000, backupCount=5)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(log_formatter)

app = Flask(__name__)
CORS(app)

app.logger.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.addHandler(error_handler)

error_logger = logging.getLogger("error_logger")
error_logger.setLevel(logging.ERROR)
error_logger.addHandler(error_handler)

def send_telegram_message(message):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
            response = requests.post(url, data=data)
            response.raise_for_status()
        except Exception as e:
            error_logger.error(f"Ошибка отправки в Telegram: {str(e)}")

def log_error_manual(message):
    error_logger.error(message)
    send_telegram_message(f"🚨 {message}")

def check_auth(request):
    token = request.headers.get("Authorization")
    if token not in ALLOWED_TOKENS:
        msg = "🔒 Запрос без токена или с неверным токеном"
        app.logger.error(msg)
        log_error_manual(msg)
        return False
    return True

@app.route("/api/voice", methods=["POST"])
def handle_voice():
    if not check_auth(request):
        return jsonify({"error": "Unauthorized"}), 401

    app.logger.info("🔊 Получен запрос на /api/voice")

    if 'file' not in request.files:
        msg = "❌ Ошибка в /api/voice: файл не передан"
        app.logger.error(msg)
        log_error_manual(msg)
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['file']
    if audio_file.filename == '':
        msg = "❌ Ошибка в /api/voice: пустое имя файла"
        app.logger.error(msg)
        log_error_manual(msg)
        return jsonify({"error": "Empty filename"}), 400

    try:
        text = transcribe_audio(audio_file)
        app.logger.info(f"📝 Распознано: {text}")

        reply = generate_response(text)
        app.logger.info(f"💬 Ответ: {reply}")

        audio_url = synthesize_speech(reply)
        app.logger.info(f"🎧 Аудио сгенерировано: {audio_url}")

        return jsonify({
            "transcript": text,
            "reply": reply,
            "audio_url": audio_url
        })
    except Exception as e:
        msg = f"❌ Исключение в /api/voice: {str(e)}"
        app.logger.exception(msg)
        log_error_manual(msg)
        return jsonify({"error": str(e)}), 500

@app.route("/text", methods=["POST"])
def handle_text():
    if not check_auth(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    user_text = data.get("message", "")
    if not user_text:
        msg = "❌ Ошибка в /text: Empty message"
        app.logger.error(msg)
        log_error_manual(msg)
        return jsonify({"error": "Empty message"}), 400

    try:
        app.logger.info(f"Запрос на /text: {user_text}")
        reply = generate_response(user_text)
        app.logger.info("Ответ сгенерирован для /text")

        audio_url = synthesize_speech(reply)

        return jsonify({
            "reply": reply,
            "audio_url": audio_url
        })
    except Exception as e:
        msg = f"❌ Исключение в /text: {str(e)}"
        app.logger.exception(msg)
        log_error_manual(msg)
        return jsonify({"error": str(e)}), 500

@app.route("/api/tts", methods=["POST"])
def elevenlabs_tts():
    if not check_auth(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    text = data.get("text", "")
    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
        headers = {
            'Accept': 'audio/mpeg',
            'xi-api-key': ELEVENLABS_API_KEY,
            'Content-Type': 'application/json'
        }
        payload = {
            'text': text,
            'voice_settings': { 'stability': 0.5, 'similarity_boost': 0.75 }
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            app.logger.error(f"Ошибка ElevenLabs TTS: {response.text}")
            return jsonify({"error": "TTS generation failed"}), 500

        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
            f.write(response.content)
            filepath = f.name

        return send_file(filepath, mimetype='audio/mpeg', as_attachment=False)
    except Exception as e:
        msg = f"❌ Ошибка в /api/tts: {str(e)}"
        app.logger.exception(msg)
        log_error_manual(msg)
        return jsonify({"error": str(e)}), 500

@app.route("/api/stt", methods=["POST"])
def elevenlabs_stt():
    if not check_auth(request):
        return jsonify({"error": "Unauthorized"}), 401

    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']
    try:
        url = "https://api.elevenlabs.io/v1/speech-to-text"
        headers = {
            'xi-api-key': ELEVENLABS_API_KEY
        }
        payload = {
            'model_id': 'eleven_multilingual_v2'
        }
        files = {
            'audio': (audio_file.filename, audio_file.stream, audio_file.mimetype)
        }
        response = requests.post(url, headers=headers, data=payload, files=files)
        if response.status_code != 200:
            app.logger.error(f"Ошибка ElevenLabs STT: {response.text}")
            return jsonify({"error": "STT failed"}), 500

        return jsonify(response.json())
    except Exception as e:
        msg = f"❌ Ошибка в /api/stt: {str(e)}"
        app.logger.exception(msg)
        log_error_manual(msg)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

