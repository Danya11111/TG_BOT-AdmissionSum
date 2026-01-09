# 🔧 Исправление ошибки dpkg

## Проблема

Вы видите ошибку:
```
E: dpkg was interrupted, you must manually run 'sudo dpkg --configure -a' to correct the problem.
```

Это означает, что процесс установки пакетов был прерван и нужно его восстановить.

## Решение

Выполните на сервере следующие команды по порядку:

### Шаг 1: Восстановление dpkg

```bash
sudo dpkg --configure -a
```

Эта команда завершит прерванную установку пакетов. Может занять несколько минут.

### Шаг 2: Исправление зависимостей (если нужно)

```bash
sudo apt --fix-broken install
```

### Шаг 3: Обновление списка пакетов

```bash
sudo apt update
```

### Шаг 4: Продолжение развертывания

После исправления dpkg, запустите скрипт развертывания снова:

```bash
cd ~/projects/TG_BOT-AdmissionSum
bash QUICK_DEPLOY.sh
```

## Если скрипт все еще не работает

Если после исправления dpkg скрипт не может продолжить, выполните шаги вручную:

### 1. Установка зависимостей

```bash
sudo apt install -y python3.11 python3.11-venv python3-pip git curl wget docker.io docker-compose
```

### 2. Запуск Docker

```bash
sudo systemctl start docker
sudo systemctl enable docker
```

### 3. Создание виртуального окружения

```bash
cd ~/projects/TG_BOT-AdmissionSum
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Настройка .env

```bash
cp .env.example .env
nano .env
# Заполните токены
```

### 5. Запуск Qdrant

```bash
docker-compose up -d
```

### 6. Миграция данных

```bash
source venv/bin/activate
python process_guu_docs.py
```

### 7. Создание systemd сервиса

```bash
sudo nano /etc/systemd/system/guu-bot.service
```

Вставьте (замените `root` на вашего пользователя, если нужно):

```ini
[Unit]
Description=GUU Telegram Bot
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/root/projects/TG_BOT-AdmissionSum
Environment="PATH=/root/projects/TG_BOT-AdmissionSum/venv/bin"
ExecStart=/root/projects/TG_BOT-AdmissionSum/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Сохраните: `Ctrl+O`, `Enter`, `Ctrl+X`

### 8. Запуск сервиса

```bash
sudo systemctl daemon-reload
sudo systemctl enable guu-bot
sudo systemctl start guu-bot
sudo systemctl status guu-bot
```

## Проверка работы

```bash
# Логи
sudo journalctl -u guu-bot -f

# Статус
sudo systemctl status guu-bot
```

## Если проблемы продолжаются

1. Проверьте логи: `sudo journalctl -u guu-bot -n 50`
2. Убедитесь, что .env файл заполнен правильно
3. Проверьте, что Qdrant запущен: `docker ps | grep qdrant`
4. Проверьте права доступа к файлам
