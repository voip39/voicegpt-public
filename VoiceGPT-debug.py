проверь сначала правильный ли код я выбрал:
print("VoiceGPT-debug loaded — ready for debugging!")

# Простой тест для voicegpt-text.py
print("VoiceGPT-text работает!")

# --- voicegpt-text.py ---

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/text", methods=["POST"])
def text_chat():
    data = request.get_json()
    user_input = data.get("message", "")

    # Временная заглушка (позже подключим OpenAI API или локальный ИИ)
    response = f"Вы сказали: {user_input}"

    return jsonify({"response": response})

@app.route("/", methods=["GET"])
def home():
    return "Текстовый интерфейс VoiceGPT работает!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
