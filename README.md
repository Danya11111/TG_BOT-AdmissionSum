# TG_BOT-AdmissionSum 🤖

Интеллектуальный Telegram-бот для абитуриентов Государственного университета управления (ГУУ).

## 🎯 Основные возможности

- **Прогноз поступления** - подбор направлений по предметам ЕГЭ и форме обучения
- **RAG-система** - ответы на вопросы на основе официальных документов ГУУ
- **Векторный поиск** - семантический поиск по базе знаний через Qdrant
- **Сохранение запросов** - все вопросы пользователей сохраняются для улучшения ответов
- **Анализ статистики** - прогнозирование проходных баллов и оценка шансов

## 🚀 Быстрый старт

### Требования

- Python 3.11+
- Docker и Docker Compose
- Telegram Bot Token
- GigaChat API credentials

### Установка

1. **Клонируйте репозиторий и установите зависимости:**

```bash
pip install -r requirements.txt
```

2. **Настройте переменные окружения:**

```bash
cp .env.example .env
# Отредактируйте .env и заполните необходимые параметры
```

3. **Запустите Qdrant:**

```bash
docker-compose up -d
```

4. **Загрузите данные в векторную базу:**

```bash
# Обработка документов из папки GUU_docs
python process_guu_docs.py

# Или загрузка данных с веб-сайта (опционально)
python rag_build.py --max-pages 200
python rag_build_vector.py
```

5. **Запустите бота:**

```bash
python main.py
```

## 📁 Структура проекта

```
TG_BOT-AdmissionSum/
├── main.py                    # Главный файл бота
├── gigachat_client.py         # Клиент для GigaChat API
├── embeddings_local.py        # Локальная модель embeddings
├── rag_search_vector.py       # Векторный поиск в Qdrant
├── rag_build_vector.py        # Миграция данных в Qdrant
├── user_queries_storage.py    # Хранение запросов пользователей
├── process_guu_docs.py        # Обработка документов из GUU_docs
├── stats_analyzer.py          # Анализ статистики поступления
├── stats_predictor.py         # Прогнозирование проходных баллов
├── utils.py                   # Вспомогательные функции
├── prompts.py                 # Промпты для GigaChat
├── keyboards.py               # Клавиатуры для Telegram
├── docker-compose.yml         # Конфигурация Qdrant
├── requirements.txt           # Зависимости Python
├── .env.example               # Пример конфигурации
├── README.md                  # Этот файл
├── DEPLOYMENT.md              # Инструкция по развертыванию
├── MIGRATION_INSTRUCTIONS.md  # Инструкции по миграции данных
├── USER_QUERIES_AND_DOCS_SETUP.md  # Настройка запросов и документов
├── GUU_docs/                  # Документы для обработки (PDF, DOCX, XLSX)
├── data/                      # Данные (индексы, чанки)
└── qdrant_storage/            # Данные Qdrant (создается автоматически)
```

## 🔧 Основные компоненты

### RAG-система

- **Векторный поиск** через Qdrant с локальными embeddings (Sentence Transformers)
- **Генерация ответов** через GigaChat на основе найденных документов
- **Сохранение запросов** пользователей для улучшения контекста

### Обработка документов

- Поддержка PDF, DOCX, XLSX файлов
- Автоматическое разбиение на чанки
- Векторизация и загрузка в Qdrant

### Прогноз поступления

- Подбор направлений по предметам ЕГЭ
- Расчет конкурсного балла с учетом достижений
- Прогнозирование проходных баллов
- Оценка шансов поступления

## 📚 Документация

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Подробная инструкция по развертыванию на сервере
- **[MIGRATION_INSTRUCTIONS.md](MIGRATION_INSTRUCTIONS.md)** - Инструкции по миграции данных
- **[USER_QUERIES_AND_DOCS_SETUP.md](USER_QUERIES_AND_DOCS_SETUP.md)** - Настройка сохранения запросов и обработки документов

## ⚙️ Конфигурация

Основные переменные окружения (см. `.env.example`):

- `TELEGRAM_BOT_TOKEN` - токен Telegram бота
- `GIGACHAT_AUTH_BASIC` - Base64 кодированные credentials для GigaChat
- `GIGACHAT_SCOPE` - область доступа GigaChat (обычно `GIGACHAT_PERS`)
- `QDRANT_HOST` - хост Qdrant (по умолчанию `localhost`)
- `QDRANT_PORT` - порт Qdrant (по умолчанию `6333`)

## 🛠 Технологии

- **pyTelegramBotAPI** - работа с Telegram Bot API
- **Qdrant** - векторная база данных
- **Sentence Transformers** - локальная генерация embeddings
- **GigaChat API** - генерация ответов
- **PyPDF2, python-docx** - обработка документов
- **pandas, openpyxl** - работа с Excel файлами

## 📝 Лицензия

Проект разработан для Государственного университета управления (ГУУ).

## 🤝 Поддержка

При возникновении проблем:
1. Проверьте логи в `bot.log`
2. Убедитесь, что Qdrant запущен: `docker ps | grep qdrant`
3. Проверьте переменные окружения в `.env`
4. См. раздел "Устранение проблем" в [DEPLOYMENT.md](DEPLOYMENT.md)
