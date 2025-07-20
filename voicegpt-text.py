from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/text", methods=["POST"])
def text_chat():
    data = request.get_json()
    user_input = data.get("message", "")
    response = f"Вы сказали: {user_input}"
    return jsonify({"response": response})

@app.route("/", methods=["GET"])
def home():
    return "Текстовый интерфейс VoiceGPT работает!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
