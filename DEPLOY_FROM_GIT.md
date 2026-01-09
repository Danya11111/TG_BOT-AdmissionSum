# 🚀 Быстрое развертывание с GitHub

## Самый простой способ - через Git

Проект находится на GitHub: https://github.com/Danya11111/TG_BOT-AdmissionSum (ветка `develop`)

### На сервере выполните:

```bash
# 1. Подключитесь к серверу
ssh root@82.202.169.214

# 2. Создайте директорию и клонируйте проект
mkdir -p ~/projects
cd ~/projects
git clone -b develop https://github.com/Danya11111/TG_BOT-AdmissionSum.git TG_BOT-AdmissionSum
cd TG_BOT-AdmissionSum

# 3. Запустите скрипт автоматического развертывания
bash QUICK_DEPLOY.sh

# 4. Настройте .env файл
nano .env
# Заполните:
# - TELEGRAM_BOT_TOKEN (от @BotFather)
# - GIGACHAT_AUTH_BASIC (Base64 credentials)

# 5. Перезапустите бота
sudo systemctl restart guu-bot

# 6. Проверьте статус
sudo systemctl status guu-bot
```

## Обновление проекта

Когда нужно обновить код с GitHub:

```bash
cd ~/projects/TG_BOT-AdmissionSum
git pull origin develop
sudo systemctl restart guu-bot
```

## Что делает QUICK_DEPLOY.sh

1. ✅ Обновляет систему
2. ✅ Устанавливает Python 3.11, Docker, Git и другие зависимости
3. ✅ Создает виртуальное окружение Python
4. ✅ Устанавливает все Python пакеты из requirements.txt
5. ✅ Настраивает .env файл (создает из .env.example)
6. ✅ Запускает Qdrant через Docker
7. ✅ Мигрирует данные в Qdrant (process_guu_docs.py)
8. ✅ Создает systemd сервис для автозапуска
9. ✅ Запускает бота

## Полезные команды

```bash
# Просмотр логов
sudo journalctl -u guu-bot -f

# Статус бота
sudo systemctl status guu-bot

# Перезапуск
sudo systemctl restart guu-bot

# Остановка
sudo systemctl stop guu-bot

# Проверка Qdrant
docker ps | grep qdrant
curl http://localhost:6333/health
```

## Если что-то пошло не так

1. Проверьте логи: `sudo journalctl -u guu-bot -n 50`
2. Убедитесь, что .env файл заполнен правильно
3. Проверьте, что Qdrant запущен: `docker ps | grep qdrant`
4. Проверьте, что виртуальное окружение активировано в systemd сервисе
