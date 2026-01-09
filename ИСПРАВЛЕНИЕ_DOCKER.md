# 🔧 Исправление конфликта Docker (containerd)

## Проблема

Вы видите ошибку:
```
containerd.io: Conflicts: containerd
E: Error, pkgProblemResolver::Resolve generated breaks
```

Это конфликт между `containerd.io` (из Docker репозитория) и `containerd` (из системных репозиториев Ubuntu).

## Решение

### Вариант 1: Автоматическое исправление (рекомендуется)

Выполните на сервере:

```bash
# 1. Удаление конфликтующих пакетов
sudo apt remove -y containerd docker.io docker-doc docker-compose-plugin docker-compose-v2 podman-docker containerd.io runc 2>/dev/null || true

# 2. Очистка
sudo apt autoremove -y
sudo apt autoclean

# 3. Установка Docker из официального репозитория
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Добавление репозитория Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 4. Установка Docker
sudo apt update
export DEBIAN_FRONTEND=noninteractive
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 5. Запуск Docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

### Вариант 2: Использование системного Docker (проще)

Если не нужна последняя версия Docker:

```bash
# Удаление конфликтующих пакетов
sudo apt remove -y containerd.io 2>/dev/null || true

# Установка системного Docker
export DEBIAN_FRONTEND=noninteractive
sudo apt update
sudo apt install -y docker.io docker-compose

# Запуск Docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

### Вариант 3: Исправление через скрипт

Обновленный скрипт `QUICK_DEPLOY.sh` теперь автоматически исправляет эту проблему.

## Проверка установки

```bash
# Проверка версии Docker
docker --version

# Проверка статуса
sudo systemctl status docker

# Тест запуска контейнера
sudo docker run hello-world
```

## Продолжение развертывания

После исправления Docker:

```bash
cd ~/projects/TG_BOT-AdmissionSum

# Запуск Qdrant
docker-compose up -d

# Проверка
docker ps
```

## Примечание

- `containerd.io` - это пакет из официального Docker репозитория
- `containerd` - это пакет из системных репозиториев Ubuntu
- Они конфликтуют, поэтому нужно использовать только один из них
- Docker из официального репозитория использует `containerd.io`
- Системный Docker использует `containerd`
