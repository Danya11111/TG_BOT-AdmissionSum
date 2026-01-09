# 🚨 Решение проблемы с Docker прямо сейчас

## Текущая ошибка

```
containerd.io: Conflicts: containerd
E: Error, pkgProblemResolver::Resolve generated breaks
```

## Быстрое решение (выполните на сервере)

```bash
# 1. Удаление конфликтующего пакета
sudo apt remove -y containerd.io

# 2. Обновление списка пакетов
export DEBIAN_FRONTEND=noninteractive
sudo apt update

# 3. Установка Docker (системный пакет, без конфликтов)
sudo apt install -y docker.io docker-compose

# 4. Запуск Docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# 5. Проверка
docker --version
sudo systemctl status docker
```

## Продолжение развертывания

После исправления Docker:

```bash
cd ~/projects/TG_BOT-AdmissionSum

# Обновите скрипт (если нужно)
git pull origin develop

# Запустите скрипт снова
bash QUICK_DEPLOY.sh
```

Обновленный скрипт теперь автоматически:
- ✅ Удаляет конфликтующий `containerd.io` перед установкой Docker
- ✅ Устанавливает системный `docker.io` (без конфликтов)
- ✅ Настраивает и запускает Docker

## Если скрипт все еще не работает

Выполните установку вручную:

```bash
cd ~/projects/TG_BOT-AdmissionSum

# 1. Установка Python и базовых пакетов
export DEBIAN_FRONTEND=noninteractive
sudo apt install -y python3.12 python3.12-venv python3-pip git curl wget

# 2. Установка Docker (после удаления containerd.io)
sudo apt remove -y containerd.io
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker

# 3. Создание виртуального окружения
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Настройка .env
cp .env.example .env
nano .env

# 5. Запуск Qdrant
docker-compose up -d

# 6. Миграция данных
python process_guu_docs.py

# 7. Создание systemd сервиса (см. DEPLOY_TO_SERVER.md)
# 8. Запуск бота
```

## Объяснение проблемы

- `containerd.io` - пакет из официального Docker репозитория
- `containerd` - системный пакет Ubuntu
- Они конфликтуют, так как оба предоставляют одну и ту же функциональность
- Решение: использовать системный `docker.io`, который работает с системным `containerd`

## Проверка

```bash
# Docker работает?
docker ps

# Qdrant запущен?
docker-compose ps

# Бот запущен?
sudo systemctl status guu-bot
```
