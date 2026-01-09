"""
Скрипт для миграции данных из JSON индекса в векторную БД Qdrant.

Использование:
    python rag_build_vector.py

Требования:
    - Qdrant должен быть запущен (docker-compose up или отдельно)
    - GigaChat credentials в .env
    - Существующий index.json в data/guu/index.json
"""

import argparse
import json
import logging
import os
import time
from typing import Dict, List, Optional

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from embeddings_local import get_embeddings, get_vector_size

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

INDEX_PATH = os.path.join("data", "guu", "index.json")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "guu_documents")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
VECTOR_SIZE = get_vector_size()  # Размерность локальных embeddings (384 для multilingual-MiniLM)
BATCH_SIZE = 20  # Количество текстов для векторизации за раз (можно больше, т.к. локально)


def load_index(index_path: str) -> List[Dict]:
    """Загружает индекс из JSON файла."""
    logger.info(f"Загрузка индекса из {index_path}")
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
        logger.info(f"Загружено {len(index)} чанков")
        return index
    except FileNotFoundError:
        logger.error(f"Файл {index_path} не найден")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON: {e}")
        raise


def create_collection(client: QdrantClient, collection_name: str, vector_size: int) -> None:
    """Создает коллекцию в Qdrant, если её нет."""
    logger.info(f"Проверка коллекции {collection_name}...")
    
    # Проверка существования коллекции через список коллекций
    try:
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if collection_name in collection_names:
            # Коллекция существует - удаляем её для пересоздания
            logger.warning(f"Коллекция {collection_name} уже существует")
            logger.info(f"Удаление существующей коллекции {collection_name}...")
            try:
                client.delete_collection(collection_name)
                logger.info("Коллекция удалена")
            except Exception as e:
                logger.warning(f"Ошибка при удалении коллекции: {e}")
                # Продолжаем попытку создания - возможно коллекция уже удалена
    except Exception as e:
        logger.debug(f"Ошибка при проверке коллекций: {e}")
        # Продолжаем - попробуем создать коллекцию
    
    # Создание коллекции
    logger.info(f"Создание коллекции {collection_name}...")
    try:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )
        logger.info(f"Коллекция {collection_name} создана")
    except Exception as e:
        # Если коллекция уже существует, это нормально
        if "already exists" in str(e).lower() or "409" in str(e):
            logger.info(f"Коллекция {collection_name} уже существует, используем её")
        else:
            raise


def vectorize_and_upload(
    client: QdrantClient,
    index: List[Dict],
    collection_name: str,
    batch_size: int = BATCH_SIZE,
) -> None:
    """Векторизует чанки и загружает их в Qdrant."""
    total = len(index)
    logger.info(f"Начало векторизации и загрузки {total} чанков...")
    
    points = []
    processed = 0
    
    for i in range(0, total, batch_size):
        batch = index[i:i + batch_size]
        batch_texts = [item["content"] for item in batch]
        
        try:
            # Векторизация батча через локальную модель
            logger.info(f"Векторизация батча {i // batch_size + 1} ({len(batch)} текстов)...")
            embeddings = get_embeddings(batch_texts)
            
            # Формирование точек для Qdrant
            for j, (item, embedding) in enumerate(zip(batch, embeddings)):
                # Преобразуем строковый ID в числовой (Qdrant требует int или UUID)
                # Извлекаем число из "chunk000001" -> 1
                chunk_id_str = item["id"]
                try:
                    # Пытаемся извлечь число из строки типа "chunk000001"
                    chunk_num = int(chunk_id_str.replace("chunk", ""))
                except (ValueError, AttributeError):
                    # Если не получилось, используем хеш строки
                    chunk_num = hash(chunk_id_str) & 0x7FFFFFFF  # Положительное число
                
                point = PointStruct(
                    id=chunk_num,  # Используем числовой ID
                    vector=embedding,
                    payload={
                        "content": item["content"],
                        "title": item.get("title", ""),
                        "source": item.get("source", ""),
                        "date": item.get("date", ""),
                        "chunk_id": item["id"],  # Сохраняем оригинальный ID в payload
                    },
                )
                points.append(point)
            
            processed += len(batch)
            logger.info(f"Обработано {processed}/{total} чанков ({processed * 100 // total}%)")
                
        except Exception as e:
            logger.error(f"Ошибка при обработке батча {i // batch_size + 1}: {e}")
            logger.error("Продолжаем со следующим батчем...")
            continue
    
    # Загрузка всех точек в Qdrant
    if points:
        logger.info(f"Загрузка {len(points)} точек в Qdrant...")
        try:
            client.upsert(
                collection_name=collection_name,
                points=points,
            )
            logger.info(f"Успешно загружено {len(points)} точек в Qdrant")
        except Exception as e:
            logger.error(f"Ошибка при загрузке в Qdrant: {e}")
            raise
    else:
        logger.warning("Нет точек для загрузки")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Миграция данных из JSON индекса в векторную БД Qdrant"
    )
    parser.add_argument(
        "--index-path",
        type=str,
        default=INDEX_PATH,
        help="Путь к JSON индексу",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default=COLLECTION_NAME,
        help="Название коллекции в Qdrant",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=QDRANT_HOST,
        help="Хост Qdrant",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=QDRANT_PORT,
        help="Порт Qdrant",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help="Размер батча для векторизации",
    )
    args = parser.parse_args()
    
    # Инициализация локальной модели embeddings
    logger.info("Инициализация локальной модели embeddings...")
    try:
        # Предзагрузка модели (чтобы проверить, что она работает)
        from embeddings_local import get_model
        model = get_model()
        logger.info(f"Локальная модель embeddings готова (размерность: {get_vector_size()})")
    except Exception as e:
        logger.error(f"Ошибка инициализации локальной модели: {e}")
        logger.error("Убедитесь, что установлен sentence-transformers: pip install sentence-transformers")
        raise
    
    logger.info(f"Подключение к Qdrant {args.host}:{args.port}...")
    try:
        qdrant_client = QdrantClient(host=args.host, port=args.port)
        # Проверка подключения
        qdrant_client.get_collections()
        logger.info("Подключение к Qdrant успешно")
    except Exception as e:
        logger.error(f"Ошибка подключения к Qdrant: {e}")
        logger.error("Убедитесь, что Qdrant запущен (docker-compose up или отдельно)")
        raise
    
    # Загрузка индекса
    index = load_index(args.index_path)
    
    # Создание коллекции
    create_collection(qdrant_client, args.collection, VECTOR_SIZE)
    
    # Векторизация и загрузка
    vectorize_and_upload(
        qdrant_client,
        index,
        args.collection,
        args.batch_size,
    )
    
    # Проверка результата
    try:
        collection_info = qdrant_client.get_collection(args.collection)
        points_count = collection_info.points_count
        vector_size = collection_info.config.params.vectors.size
    except Exception as e:
        logger.warning(f"Не удалось получить информацию о коллекции: {e}")
        logger.info("Попробуйте проверить коллекцию через веб-интерфейс: http://localhost:6333/dashboard")
        points_count = "неизвестно"
        vector_size = VECTOR_SIZE
    
    logger.info(f"✅ Миграция завершена!")
    logger.info(f"   Коллекция: {args.collection}")
    logger.info(f"   Точек в коллекции: {points_count}")
    logger.info(f"   Размерность векторов: {vector_size}")


if __name__ == "__main__":
    main()
