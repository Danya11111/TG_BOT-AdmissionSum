#!/bin/bash
# Быстрый скрипт для развертывания бота на сервере Ubuntu
# Использование: bash QUICK_DEPLOY.sh [путь_к_проекту]
# Если путь не указан, скрипт попытается клонировать проект из GitHub

set -e  # Остановка при ошибке

echo "🚀 Начало развертывания Telegram бота..."

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Проверка, что скрипт запущен от правильного пользователя
if [ "$EUID" -eq 0 ]; then 
   echo -e "${YELLOW}⚠️  Рекомендуется запускать не от root пользователя${NC}"
fi

# Определение пути к проекту
if [ -n "$1" ]; then
    PROJECT_DIR="$1"
    echo -e "${GREEN}Используется указанный путь: $PROJECT_DIR${NC}"
    cd "$PROJECT_DIR"
elif [ -f "main.py" ] && [ -f "requirements.txt" ]; then
    PROJECT_DIR=$(pwd)
    echo -e "${GREEN}Проект найден в текущей директории: $PROJECT_DIR${NC}"
else
    # Попытка клонировать проект
    echo -e "${YELLOW}Проект не найден. Клонирование из GitHub...${NC}"
    mkdir -p ~/projects
    cd ~/projects
    if [ -d "TG_BOT-AdmissionSum" ]; then
        echo -e "${YELLOW}Директория уже существует. Используется существующая.${NC}"
        cd TG_BOT-AdmissionSum
        git pull origin develop || true
    else
        git clone -b develop https://github.com/Danya11111/TG_BOT-AdmissionSum.git TG_BOT-AdmissionSum
        cd TG_BOT-AdmissionSum
    fi
    PROJECT_DIR=$(pwd)
fi

echo -e "${GREEN}Рабочая директория: $PROJECT_DIR${NC}"

# Шаг 0: Проверка и исправление dpkg (если нужно)
echo -e "\n${GREEN}[0/9]${NC} Проверка состояния dpkg..."
if dpkg -l | grep -q "^..r"; then
    echo -e "${YELLOW}⚠️  Обнаружены проблемы с dpkg. Исправление...${NC}"
    sudo dpkg --configure -a || true
    sudo apt --fix-broken install -y || true
fi

# Шаг 1: Обновление системы
echo -e "\n${GREEN}[1/9]${NC} Обновление системы..."
sudo apt update
if [ $? -ne 0 ]; then
    echo -e "${RED}✗${NC} Ошибка при обновлении пакетов. Попробуйте выполнить:"
    echo -e "  ${YELLOW}sudo dpkg --configure -a${NC}"
    echo -e "  ${YELLOW}sudo apt --fix-broken install${NC}"
    exit 1
fi
sudo apt upgrade -y

# Шаг 2: Установка зависимостей
echo -e "\n${GREEN}[2/9]${NC} Установка зависимостей..."
sudo apt install -y python3.11 python3.11-venv python3-pip git curl wget docker.io docker-compose

# Запуск Docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Шаг 3: Создание виртуального окружения
echo -e "\n${GREEN}[3/9]${NC} Создание виртуального окружения Python..."
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
    echo -e "${GREEN}✓${NC} Виртуальное окружение создано"
else
    echo -e "${YELLOW}⚠️  Виртуальное окружение уже существует${NC}"
fi

# Активация и установка пакетов
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Шаг 4: Настройка .env
echo -e "\n${GREEN}[4/9]${NC} Настройка переменных окружения..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}⚠️  Создан файл .env из примера. Не забудьте заполнить его!${NC}"
        echo -e "${YELLOW}   Отредактируйте: nano .env${NC}"
    else
        echo -e "${RED}✗${NC} Файл .env.example не найден!"
        exit 1
    fi
else
    echo -e "${GREEN}✓${NC} Файл .env уже существует"
fi

# Шаг 5: Запуск Qdrant
echo -e "\n${GREEN}[5/9]${NC} Запуск Qdrant..."
docker-compose up -d

# Проверка Qdrant
sleep 5
if curl -s http://localhost:6333/health > /dev/null; then
    echo -e "${GREEN}✓${NC} Qdrant запущен и работает"
else
    echo -e "${RED}✗${NC} Qdrant не отвечает. Проверьте: docker-compose logs qdrant"
fi

# Шаг 6: Миграция данных
echo -e "\n${GREEN}[6/9]${NC} Миграция данных в Qdrant..."
if [ -f "process_guu_docs.py" ]; then
    echo -e "${YELLOW}   Запуск process_guu_docs.py...${NC}"
    python process_guu_docs.py
    echo -e "${GREEN}✓${NC} Миграция данных завершена"
else
    echo -e "${YELLOW}⚠️  Файл process_guu_docs.py не найден, пропускаем миграцию${NC}"
fi

# Шаг 7: Создание systemd сервиса
echo -e "\n${GREEN}[7/9]${NC} Создание systemd сервиса..."
SERVICE_FILE="/etc/systemd/system/guu-bot.service"
CURRENT_USER=$(whoami)
CURRENT_DIR=$(pwd)

if [ ! -f "$SERVICE_FILE" ]; then
    sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=GUU Telegram Bot
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
Environment="PATH=$CURRENT_DIR/venv/bin"
ExecStart=$CURRENT_DIR/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    echo -e "${GREEN}✓${NC} Systemd сервис создан"
else
    echo -e "${YELLOW}⚠️  Systemd сервис уже существует${NC}"
fi

# Шаг 8: Обновление проекта из Git (если это Git репозиторий)
if [ -d ".git" ]; then
    echo -e "\n${GREEN}[8/9]${NC} Обновление проекта из Git..."
    git fetch origin
    git checkout develop
    git pull origin develop || echo -e "${YELLOW}⚠️  Не удалось обновить из Git (возможно, есть локальные изменения)${NC}"
    echo -e "${GREEN}✓${NC} Проект обновлен"
fi

# Шаг 9: Запуск сервиса
echo -e "\n${GREEN}[9/9]${NC} Запуск бота через systemd..."
sudo systemctl daemon-reload
sudo systemctl enable guu-bot
sudo systemctl start guu-bot

# Проверка статуса
sleep 3
if sudo systemctl is-active --quiet guu-bot; then
    echo -e "${GREEN}✓${NC} Бот успешно запущен!"
    echo -e "\n${GREEN}✅ Развертывание завершено!${NC}"
    echo -e "\nПолезные команды:"
    echo -e "  Просмотр логов: ${YELLOW}sudo journalctl -u guu-bot -f${NC}"
    echo -e "  Статус бота:   ${YELLOW}sudo systemctl status guu-bot${NC}"
    echo -e "  Перезапуск:    ${YELLOW}sudo systemctl restart guu-bot${NC}"
else
    echo -e "${RED}✗${NC} Бот не запустился. Проверьте логи:"
    echo -e "  ${YELLOW}sudo journalctl -u guu-bot -n 50${NC}"
    exit 1
fi

echo -e "\n${YELLOW}⚠️  Не забудьте:${NC}"
echo -e "  1. Заполнить файл .env с вашими токенами"
echo -e "  2. Перезапустить бота после настройки: ${YELLOW}sudo systemctl restart guu-bot${NC}"
