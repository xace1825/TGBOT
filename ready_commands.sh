#!/bin/bash
# Готовые команды для настройки бота на сервере
# Копируйте и вставляйте эти команды в веб-консоль Timeweb по порядку

echo "🔧 Шаг 1: Обновление системы"
apt update && apt upgrade -y

echo "🐍 Шаг 2: Установка Python и утилит"
apt install python3.11 python3.11-venv python3-pip wget unzip nano -y

echo "📁 Шаг 3: Создание папки проекта"
mkdir -p /home/mafia_bot
cd /home/mafia_bot

echo "📝 Шаг 4: Создание requirements.txt"
cat > requirements.txt << 'EOF'
python-telegram-bot==21.7
yookassa==3.1.0
apscheduler==3.10.4
python-dotenv==1.0.1
requests==2.32.3
EOF

echo "📝 Шаг 5: Создание runtime.txt"
echo "python-3.11.0" > runtime.txt

echo "📝 Шаг 6: Создание Procfile"
echo "web: python mafia_bot.py" > Procfile

echo "🌐 Шаг 7: Создание виртуального окружения"
python3.11 -m venv venv
source venv/bin/activate

echo "📦 Шаг 8: Установка зависимостей"
pip install --upgrade pip
pip install -r requirements.txt

echo "⚙️ Шаг 9: Создание сервиса для автозапуска"
cat > /etc/systemd/system/mafia-bot.service << 'EOF'
[Unit]
Description=Mafia Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/mafia_bot
Environment=PATH=/home/mafia_bot/venv/bin
ExecStart=/home/mafia_bot/venv/bin/python mafia_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Базовая настройка завершена!"
echo "📋 Дальше нужно:"
echo "1. Создать файлы mafia_bot.py и premium_database.py"
echo "2. Создать файл .env с токенами"
echo "3. Запустить сервис: systemctl enable mafia-bot && systemctl start mafia-bot" 