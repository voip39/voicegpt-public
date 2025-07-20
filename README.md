# VoiceGPT

Голосовой API-ассистент на Flask, с возможностью распознавания речи, генерации ответа и озвучивания результата.

---

## 🔧 Установка

### 1. Клонируйте проект с GitHub:

```bash
git clone https://github.com/voip39/voice39.git
cd voice39
```

### 2. Создайте виртуальное окружение (если ещё нет):

```bash
python3 -m venv ../voicegpt-env
source ../voicegpt-env/bin/activate
```

### 3. Установите зависимости:

```bash
pip install -r requirements.txt
```

---

## 🚀 Запуск

### Вручную (для разработки):

```bash
bash run.sh
```

### В фоне (например, на VPS):

```bash
nohup bash run.sh > flask.log 2>&1 &
```

---

## 🧪 Тестирование API

### 🔹 POST /text

```bash
curl -X POST http://<your_server_ip>:5000/text \
-H "Content-Type: application/json" \
-d '{"message": "Привет, кто ты?"}'
```

### 🔹 POST /api/voice

Отправка аудиофайла (например, test.m4a):

```bash
curl -X POST http://<your_server_ip>:5000/api/voice \
-F "file=@test.m4a"
```

---

## 📦 Зависимости (requirements.txt)

- flask
- openai-whisper
- boto3
- requests

---

## 📌 Замечания

- На текущем этапе функции Whisper, OpenAI и Polly реализованы как заглушки.
- Функциональность постепенно расширяется.
- Для продакшн-режима планируется поддержка gunicorn и systemd.
