import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify
from whisper_handler import transcribe_audio
from llm import generate_response
from tts import synthesize_speech
import requests

# Загрузка допустимых токенов из .env
from dotenv import load_dotenv
load_dotenv()
ALLOWED_TOKENS = os.getenv("API_TOKENS", "").split(",")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Создание директорий логов
os.makedirs("logs", exist_ok=True)

# Настройка логгера
log_formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")

file_handler = RotatingFileHandler("logs/voicegpt.log", maxBytes=1000000, backupCount=5)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(log_formatter)

error_handler = RotatingFileHandler("logs/errors.log", maxBytes=1000000, backupCount=5)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(log_formatter)

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.addHandler(error_handler)

# Вспомогательная функция для логирования ошибок вручную
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
