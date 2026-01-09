# 🔧 Исправление проблемы с Python

## Проблема

Вы видите ошибки:
```
E: Unable to locate package python3.11
E: Unable to locate package python3.11-venv
```

Это означает, что Python 3.11 недоступен в стандартных репозиториях Ubuntu 24.04.

## Решение

### Вариант 1: Использовать Python 3.12 (рекомендуется для Ubuntu 24.04)

Ubuntu 24.04 обычно поставляется с Python 3.12. Обновленный скрипт автоматически определит доступную версию.

Если скрипт все еще не работает, выполните вручную:

```bash
# Установка Python 3.12 и зависимостей
export DEBIAN_FRONTEND=noninteractive
sudo apt install -y python3.12 python3.12-venv python3-pip git curl wget docker.io docker-compose

# Создание виртуального окружения
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Вариант 2: Добавить deadsnakes PPA для Python 3.11

Если вам нужна именно версия 3.11:

```bash
# Добавление PPA
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update

# Установка Python 3.11
export DEBIAN_FRONTEND=noninteractive
sudo apt install -y python3.11 python3.11-venv python3-pip git curl wget docker.io docker-compose

# Создание виртуального окружения
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Вариант 3: Использовать системный Python3

Если доступна только общая версия python3:

```bash
# Установка системного Python
export DEBIAN_FRONTEND=noninteractive
sudo apt install -y python3 python3-venv python3-pip git curl wget docker.io docker-compose

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Обработка PAM диалога

Если появляется диалог PAM configuration:

1. **Автоматически:** Скрипт теперь использует `DEBIAN_FRONTEND=noninteractive` для автоматического ответа
2. **Вручную:** Выберите "Yes" в диалоге, чтобы использовать системную конфигурацию

## Проверка версии Python

После установки проверьте версию:

```bash
python3 --version
# или
python3.12 --version
# или
python3.11 --version
```

## Продолжение развертывания

После установки Python выполните остальные шаги:

```bash
cd ~/projects/TG_BOT-AdmissionSum

# Настройка .env
cp .env.example .env
nano .env

# Запуск Qdrant
docker-compose up -d

# Миграция данных
source venv/bin/activate
python process_guu_docs.py

# Создание systemd сервиса (см. DEPLOY_TO_SERVER.md)
# Запуск бота
sudo systemctl start guu-bot
```

## Примечание

Проект требует Python 3.11+, но обычно работает и с Python 3.12. Все зависимости из `requirements.txt` совместимы с обеими версиями.
