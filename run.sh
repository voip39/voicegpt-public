#!/bin/bash
# Запускает Flask-сервер в виртуальном окружении
# Используется для разработки и отладки (Dev-stage)

# 1. Активируем виртуальное окружение
source /root/voicegpt-env/bin/activate

# 2. Переходим в папку с проектом
cd /root/voicegpt

# 3. Запускаем Flask-сервер
# Он будет слушать порт 5000
python3 app.py
