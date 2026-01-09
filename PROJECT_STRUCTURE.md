# Структура проекта

## 📁 Основные файлы

### Запуск и конфигурация
- `main.py` - Главный файл бота
- `requirements.txt` - Зависимости Python
- `docker-compose.yml` - Конфигурация Qdrant
- `.env.example` - Пример конфигурации (скопируйте в `.env`)

### Основные модули
- `gigachat_client.py` - Клиент для GigaChat API
- `embeddings_local.py` - Локальная модель embeddings (Sentence Transformers)
- `rag_search_vector.py` - Векторный поиск в Qdrant
- `rag_build_vector.py` - Миграция данных в Qdrant
- `user_queries_storage.py` - Хранение запросов пользователей
- `process_guu_docs.py` - Обработка документов из папки GUU_docs

### Вспомогательные модули
- `stats_analyzer.py` - Анализ статистики поступления
- `stats_predictor.py` - Прогнозирование проходных баллов
- `utils.py` - Вспомогательные функции
- `prompts.py` - Промпты для GigaChat
- `keyboards.py` - Клавиатуры для Telegram

## 📚 Документация

- `README.md` - Основная документация
- `DEPLOYMENT.md` - Инструкция по развертыванию на сервере
- `MIGRATION_INSTRUCTIONS.md` - Инструкции по миграции данных
- `USER_QUERIES_AND_DOCS_SETUP.md` - Настройка запросов и документов
- `PROJECT_STRUCTURE.md` - Этот файл

## 📂 Папки

### `GUU_docs/`
Содержит документы для обработки:
- PDF файлы (программы ВИ, правила приема, договоры)
- DOCX файлы (договоры)
- XLSX файлы (статистика)

**Важно:** Все файлы из этой папки обрабатываются скриптом `process_guu_docs.py` и загружаются в Qdrant.

### `data/guu/`
Содержит обработанные данные:
- `index.json` - Индекс документов (создается при краулинге сайта)
- `chunks/` - Текстовые чанки документов
- `raw/` - Сырые тексты документов
- `stats/` - CSV файлы со статистикой проходных баллов

### `qdrant_storage/`
Создается автоматически Qdrant:
- Векторная база данных
- Коллекции `guu_documents` и `user_queries`

**Важно:** Эта папка может быть большой. Рекомендуется добавить в `.gitignore` или делать резервные копии.

## 🚀 Быстрый старт

1. Установите зависимости: `pip install -r requirements.txt`
2. Настройте `.env` из `.env.example`
3. Запустите Qdrant: `docker-compose up -d`
4. Обработайте документы: `python process_guu_docs.py`
5. Запустите бота: `python main.py`

## 📝 Примечания

- Файлы в `reports/` и `__pycache__/` игнорируются Git
- Логи сохраняются в `bot.log`
- Все конфиденциальные данные хранятся в `.env` (не коммитится)
