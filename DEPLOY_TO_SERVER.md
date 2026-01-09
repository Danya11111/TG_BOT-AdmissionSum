# Пошаговая инструкция по загрузке и запуску бота на сервере

Эта инструкция поможет вам развернуть Telegram бота на сервере Ubuntu 24.04.

## Предварительные требования

- Сервер Ubuntu 24.04 с доступом по SSH
- Минимум 4GB RAM (рекомендуется 8GB)
- Минимум 20GB свободного места на диске
- Доступ к интернету для установки пакетов

## Шаг 1: Подключение к серверу

Подключитесь к серверу по SSH:

```bash
ssh root@82.202.169.214
# или
ssh ваш_пользователь@82.202.169.214
```

## Шаг 2: Обновление системы и установка базовых пакетов

```bash
# Обновление списка пакетов
sudo apt update
sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y python3.11 python3.11-venv python3-pip git curl wget
sudo apt install -y docker.io docker-compose

# Запуск Docker
sudo systemctl start docker
sudo systemctl enable docker

# Добавление текущего пользователя в группу docker (чтобы не использовать sudo)
sudo usermod -aG docker $USER
# Выйдите и войдите снова, чтобы изменения вступили в силу
```

## Шаг 3: Создание директории для проекта

```bash
# Создайте директорию для проекта
mkdir -p ~/projects
cd ~/projects
```

## Шаг 4: Загрузка проекта на сервер

### Вариант А: Через Git (если проект в репозитории)

```bash
git clone <ваш_репозиторий_url> TG_BOT-AdmissionSum
cd TG_BOT-AdmissionSum
```

### Вариант Б: Через SCP (с вашего локального компьютера)

На вашем локальном компьютере (Windows PowerShell):

```powershell
# Перейдите в директорию с проектом
cd "C:\Users\Daniil Arkhipov\Desktop\TG_bot"

# Загрузите проект на сервер
scp -r TG_BOT-AdmissionSum root@82.202.169.214:~/projects/
```

Затем на сервере:

```bash
cd ~/projects/TG_BOT-AdmissionSum
```

### Вариант В: Через SFTP или WinSCP

1. Откройте WinSCP или другой SFTP клиент
2. Подключитесь к серверу (82.202.169.214)
3. Загрузите папку `TG_BOT-AdmissionSum` в `~/projects/`

## Шаг 5: Создание виртуального окружения Python

```bash
cd ~/projects/TG_BOT-AdmissionSum

# Создание виртуального окружения
python3.11 -m venv venv

# Активация виртуального окружения
source venv/bin/activate

# Обновление pip
pip install --upgrade pip
```

## Шаг 6: Установка зависимостей

```bash
# Установка Python пакетов
pip install -r requirements.txt
```

**Примечание:** Установка `sentence-transformers` может занять несколько минут, так как она загружает модели.

## Шаг 7: Настройка переменных окружения

```bash
# Создание файла .env из примера
cp .env.example .env

# Редактирование .env файла
nano .env
```

Заполните следующие переменные:

```env
# Telegram Bot Token (получите у @BotFather в Telegram)
TELEGRAM_BOT_TOKEN=ваш_токен_бота

# GigaChat API credentials
# 1. Зарегистрируйтесь на https://developers.sber.ru/
# 2. Создайте приложение и получите client_id и client_secret
# 3. Закодируйте их в Base64:
#    echo -n "client_id:client_secret" | base64
GIGACHAT_AUTH_BASIC=ваш_base64_код
GIGACHAT_SCOPE=GIGACHAT_API_PERS
GIGACHAT_VERIFY_TLS=true

# Qdrant настройки (обычно не нужно менять)
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=guu_documents
```

Сохраните файл: `Ctrl+O`, затем `Enter`, затем `Ctrl+X`.

## Шаг 8: Запуск Qdrant (векторная база данных)

```bash
# Запуск Qdrant через Docker Compose
docker-compose up -d

# Проверка, что Qdrant запущен
docker ps | grep qdrant

# Проверка доступности Qdrant
curl http://localhost:6333/health
```

Должен вернуться ответ `{"title":"qdrant - vector search engine"}`.

## Шаг 9: Миграция данных в Qdrant

```bash
# Убедитесь, что виртуальное окружение активировано
source venv/bin/activate

# Обработка документов из папки GUU_docs
python process_guu_docs.py

# Это может занять несколько минут, так как:
# - Документы разбиваются на чанки
# - Каждый чанк векторизуется
# - Векторы загружаются в Qdrant
```

**Важно:** Убедитесь, что папка `GUU_docs/` содержит все необходимые документы (PDF, DOCX, XLSX).

## Шаг 10: Проверка работы бота (тестовый запуск)

```bash
# Убедитесь, что виртуальное окружение активировано
source venv/bin/activate

# Запуск бота
python main.py
```

Бот должен запуститься и начать отвечать на сообщения. Проверьте логи на наличие ошибок.

Для остановки нажмите `Ctrl+C`.

## Шаг 11: Настройка автозапуска через systemd

Создайте файл сервиса:

```bash
sudo nano /etc/systemd/system/guu-bot.service
```

Вставьте следующее содержимое (замените `ваш_пользователь` на ваше имя пользователя):

```ini
[Unit]
Description=GUU Telegram Bot
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=ваш_пользователь
Group=ваш_пользователь
WorkingDirectory=/home/ваш_пользователь/projects/TG_BOT-AdmissionSum
Environment="PATH=/home/ваш_пользователь/projects/TG_BOT-AdmissionSum/venv/bin"
ExecStart=/home/ваш_пользователь/projects/TG_BOT-AdmissionSum/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Важно:** Замените `ваш_пользователь` на реальное имя пользователя (например, `root` или ваше имя).

Сохраните файл и активируйте сервис:

```bash
# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable guu-bot

# Запуск сервиса
sudo systemctl start guu-bot

# Проверка статуса
sudo systemctl status guu-bot
```

## Шаг 12: Полезные команды для управления

### Просмотр логов

```bash
# Логи systemd
sudo journalctl -u guu-bot -f

# Логи из файла
tail -f ~/projects/TG_BOT-AdmissionSum/bot.log
```

### Управление сервисом

```bash
# Остановка
sudo systemctl stop guu-bot

# Запуск
sudo systemctl start guu-bot

# Перезапуск
sudo systemctl restart guu-bot

# Статус
sudo systemctl status guu-bot
```

### Управление Qdrant

```bash
# Остановка
docker-compose down

# Запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f qdrant
```

## Шаг 13: Проверка работы

1. Откройте Telegram и найдите вашего бота
2. Отправьте команду `/start`
3. Бот должен ответить и начать работать

## Устранение проблем

### Бот не запускается

1. Проверьте логи: `sudo journalctl -u guu-bot -n 50`
2. Проверьте, что `.env` файл заполнен правильно
3. Проверьте, что виртуальное окружение активировано при запуске

### Ошибки подключения к Qdrant

```bash
# Проверьте, что Qdrant запущен
docker ps | grep qdrant

# Проверьте доступность
curl http://localhost:6333/health

# Перезапустите Qdrant
docker-compose restart
```

### Ошибки при миграции данных

1. Убедитесь, что Qdrant запущен
2. Проверьте, что в папке `GUU_docs/` есть документы
3. Проверьте логи миграции

### Нехватка памяти

Если серверу не хватает памяти:

1. Увеличьте swap файл:
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

2. Или используйте более легкую модель embeddings в `embeddings_local.py`

## Обновление бота

Когда нужно обновить код:

```bash
# Остановите бота
sudo systemctl stop guu-bot

# Обновите код (через git pull или загрузите новые файлы)
cd ~/projects/TG_BOT-AdmissionSum
# git pull  # если используете git

# Обновите зависимости (если изменились)
source venv/bin/activate
pip install -r requirements.txt

# Запустите бота снова
sudo systemctl start guu-bot
```

## Резервное копирование

Важные данные для резервного копирования:

```bash
# Создайте архив важных данных
tar -czf backup-$(date +%Y%m%d).tar.gz \
  ~/projects/TG_BOT-AdmissionSum/qdrant_storage \
  ~/projects/TG_BOT-AdmissionSum/data \
  ~/projects/TG_BOT-AdmissionSum/.env
```

## Безопасность

1. **Не делитесь файлом `.env`** - он содержит секретные ключи
2. Используйте файрвол для ограничения доступа к портам
3. Регулярно обновляйте систему и зависимости
4. Используйте SSH ключи вместо паролей

## Готово!

Ваш бот должен быть запущен и работать. Проверьте его в Telegram, отправив команду `/start`.
