#!/bin/bash

export DEBIAN_FRONTEND=noninteractive
set -e

echo "🔄 Updating system..."
sudo apt update && sudo apt upgrade -y

echo "🧹 Removing old Python versions..."
sudo rm -rf /opt/python* /usr/local/bin/python* /usr/local/lib/python* ~/.pyenv
sudo apt remove python3.11 python3.10 python3-pip -y || true

echo "📦 Installing dependencies..."
sudo apt install -y software-properties-common gcc make curl git build-essential libssl-dev zlib1g-dev \
  libbz2-dev libreadline-dev libsqlite3-dev wget llvm libncursesw5-dev xz-utils tk-dev libxml2-dev \
  libxmlsec1-dev libffi-dev liblzma-dev ufw

echo "🐍 Installing Python 3.11.8 with SSL support..."
cd /usr/src
sudo wget https://www.python.org/ftp/python/3.11.8/Python-3.11.8.tgz
sudo tar xzf Python-3.11.8.tgz
cd Python-3.11.8
sudo ./configure --enable-optimizations
sudo make -j$(nproc)
sudo make altinstall

echo "✅ Setting up pip and venv..."
sudo ln -sf /usr/local/bin/python3.11 /usr/bin/python3
sudo ln -sf /usr/local/bin/pip3.11 /usr/bin/pip3
python3 -m ensurepip --upgrade
python3 -m pip install --upgrade pip
python3 -m pip install virtualenv

echo "🧪 Creating project and virtual environment..."
mkdir -p ~/voicegpt && cd ~/voicegpt
python3 -m venv venv
source venv/bin/activate

echo "📦 Installing Flask and Whisper..."
pip install flask openai-whisper torch

echo "📝 Creating app.py..."
cat <<EOF > app.py
from flask import Flask, request, jsonify
import whisper

app = Flask(__name__)
model = whisper.load_model("base")

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    result = model.transcribe(file)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF

echo "🧷 Creating systemd service..."
cat <<EOF | sudo tee /etc/systemd/system/voicegpt.service
[Unit]
Description=VoiceGPT Flask Server
After=network.target

[Service]
User=$USER
WorkingDirectory=/home/$USER/voicegpt
ExecStart=/home/$USER/voicegpt/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "🌐 Opening port 5000..."
sudo ufw allow 5000 || true

echo "🚀 Starting and enabling service..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable voicegpt
sudo systemctl start voicegpt

echo "✅ Setup complete! Server running at http://<your-server-ip>:5000"
