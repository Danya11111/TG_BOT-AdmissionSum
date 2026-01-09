# Инструкция по развертыванию на сервере

## Требования

- Python 3.11+
- Docker и Docker Compose
- Минимум 4GB RAM (для работы с embeddings моделями)

## Шаг 1: Установка зависимостей

```bash
pip install -r requirements.txt
```

## Шаг 2: Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните:

```bash
cp .env.example .env
nano .env  # или используйте любой редактор
```

Заполните:
- `TELEGRAM_BOT_TOKEN` - токен вашего Telegram бота
- `GIGACHAT_AUTH_BASIC` - Base64 кодированные credentials для GigaChat API
- `GIGACHAT_SCOPE` - обычно `GIGACHAT_PERS`
- Остальные параметры можно оставить по умолчанию

## Шаг 3: Запуск Qdrant

```bash
docker-compose up -d
```

Проверьте, что Qdrant запущен:
```bash
docker ps | grep qdrant
```

## Шаг 4: Миграция данных

### 4.1. Загрузка документов из веб-сайта (опционально)

```bash
python rag_build.py --max-pages 200
python rag_build_vector.py
```

### 4.2. Обработка документов из папки GUU_docs

```bash
python process_guu_docs.py
```

Это обработает все PDF, DOCX и XLSX файлы из папки `GUU_docs` и загрузит их в Qdrant.

## Шаг 5: Запуск бота

### Вариант 1: Прямой запуск

```bash
python main.py
```

### Вариант 2: Через systemd (для Linux)

Создайте файл `/etc/systemd/system/guu-bot.service`:

```ini
[Unit]
Description=GUU Telegram Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/TG_BOT-AdmissionSum
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Затем:
```bash
sudo systemctl enable guu-bot
sudo systemctl start guu-bot
sudo systemctl status guu-bot
```

### Вариант 3: Через screen/tmux

```bash
screen -S guu-bot
python main.py
# Нажмите Ctrl+A, затем D для отсоединения
```

## Структура проекта

```
TG_BOT-AdmissionSum/
├── main.py                    # Главный файл бота
├── gigachat_client.py         # Клиент для GigaChat API
├── embeddings_local.py        # Локальная модель embeddings
├── rag_search_vector.py       # Векторный поиск
├── rag_build_vector.py        # Миграция данных в Qdrant
├── user_queries_storage.py    # Хранение запросов пользователей
├── process_guu_docs.py        # Обработка документов из GUU_docs
├── stats_analyzer.py          # Анализ статистики
├── stats_predictor.py         # Прогнозирование баллов
├── utils.py                   # Вспомогательные функции
├── prompts.py                 # Промпты для GigaChat
├── keyboards.py               # Клавиатуры для Telegram
├── docker-compose.yml         # Конфигурация Qdrant
├── requirements.txt           # Зависимости Python
├── .env.example               # Пример конфигурации
├── .gitignore                 # Игнорируемые файлы
├── README.md                  # Основная документация
├── DEPLOYMENT.md              # Этот файл
├── MIGRATION_INSTRUCTIONS.md  # Инструкции по миграции
├── USER_QUERIES_AND_DOCS_SETUP.md  # Настройка запросов и документов
├── GUU_docs/                  # Документы для обработки
├── data/                      # Данные (индексы, чанки)
└── qdrant_storage/            # Данные Qdrant (создается автоматически)
```

## Мониторинг

### Логи

Логи сохраняются в `bot.log`. Для просмотра в реальном времени:

```bash
tail -f bot.log
```

### Проверка работы Qdrant

Откройте в браузере: http://localhost:6333/dashboard

### Проверка работы бота

Отправьте команду `/start` боту в Telegram.

## Обновление

1. Остановите бота
2. Обновите код
3. Обновите зависимости: `pip install -r requirements.txt`
4. При необходимости перезапустите миграцию данных
5. Запустите бота заново

## Резервное копирование

Важные данные для резервного копирования:
- `qdrant_storage/` - векторная база данных
- `.env` - конфигурация (храните в безопасном месте)
- `data/guu/index.json` - индекс документов

## Устранение проблем

### Бот не отвечает

1. Проверьте логи: `tail -f bot.log`
2. Проверьте, что Qdrant запущен: `docker ps | grep qdrant`
3. Проверьте переменные окружения в `.env`

### Ошибки при миграции данных

1. Убедитесь, что Qdrant запущен
2. Проверьте доступность порта 6333
3. Проверьте логи миграции

### Проблемы с памятью

Если не хватает памяти для embeddings модели:
- Используйте более легкую модель в `embeddings_local.py`
- Увеличьте RAM сервера
- Используйте GPU если доступно
