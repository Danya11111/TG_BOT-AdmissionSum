"""
Модуль для сохранения запросов пользователей в Qdrant.
"""

import logging
import os
import time
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from embeddings_local import get_embeddings, get_vector_size

logger = logging.getLogger(__name__)
load_dotenv()

COLLECTION_NAME = os.getenv("QDRANT_USER_QUERIES_COLLECTION", "user_queries")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
VECTOR_SIZE = get_vector_size()


class UserQueriesStorage:
    """Класс для сохранения и поиска запросов пользователей."""
    
    def __init__(
        self,
        qdrant_host: Optional[str] = None,
        qdrant_port: Optional[int] = None,
        collection_name: Optional[str] = None,
    ) -> None:
        """Инициализация хранилища запросов пользователей."""
        self.qdrant_host = qdrant_host or QDRANT_HOST
        self.qdrant_port = qdrant_port or QDRANT_PORT
        self.collection_name = collection_name or COLLECTION_NAME
        
        logger.info(f"Инициализация UserQueriesStorage: {self.qdrant_host}:{self.qdrant_port}, коллекция: {self.collection_name}")
        
        # Подключение к Qdrant
        try:
            self.client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
            # Проверка подключения
            collections = self.client.get_collections()
            logger.info(f"Подключение к Qdrant успешно. Доступные коллекции: {[c.name for c in collections.collections]}")
        except Exception as e:
            logger.error(f"Ошибка подключения к Qdrant: {e}")
            raise
        
        # Создание коллекции, если её нет
        self._ensure_collection()
    
    def _ensure_collection(self) -> None:
        """Создает коллекцию для запросов пользователей, если её нет."""
        try:
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Создание коллекции {self.collection_name}...")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=VECTOR_SIZE,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"Коллекция {self.collection_name} создана")
            else:
                logger.info(f"Коллекция {self.collection_name} уже существует")
        except Exception as e:
            logger.error(f"Ошибка при создании коллекции: {e}")
            raise
    
    def save_query(
        self,
        user_id: int,
        query: str,
        response: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> bool:
        """
        Сохраняет запрос пользователя в Qdrant.
        
        Args:
            user_id: ID пользователя Telegram
            query: Текст запроса
            response: Ответ бота (опционально)
            metadata: Дополнительные метаданные (опционально)
        
        Returns:
            True если успешно сохранено, False иначе
        """
        try:
            # Векторизация запроса
            query_vectors = get_embeddings([query])
            if not query_vectors:
                logger.error("Не удалось получить вектор для запроса")
                return False
            
            query_vector = query_vectors[0]
            
            # Подготовка метаданных
            payload = {
                "user_id": user_id,
                "query": query,
                "response": response or "",
                "timestamp": datetime.now().isoformat(),
                "type": "user_query",
            }
            
            if metadata:
                payload.update(metadata)
            
            # Генерация уникального ID на основе времени и user_id
            point_id = int(time.time() * 1000000) + user_id  # Микросекунды + user_id для уникальности
            
            # Сохранение в Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=query_vector,
                        payload=payload,
                    )
                ],
            )
            
            logger.info(f"Запрос пользователя {user_id} сохранен в коллекцию {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении запроса: {e}", exc_info=True)
            return False
    
    def search_similar_queries(
        self,
        query: str,
        top_k: int = 5,
        user_id: Optional[int] = None,
    ) -> list:
        """
        Ищет похожие запросы пользователей.
        
        Args:
            query: Текст запроса для поиска
            top_k: Количество результатов
            user_id: Фильтр по ID пользователя (опционально)
        
        Returns:
            Список похожих запросов с метаданными
        """
        try:
            # Векторизация запроса
            query_vectors = get_embeddings([query])
            if not query_vectors:
                logger.error("Не удалось получить вектор для запроса")
                return []
            
            query_vector = query_vectors[0]
            
            # Поиск похожих запросов
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
            )
            
            results = []
            for result in search_results:
                payload = result.payload
                if user_id is None or payload.get("user_id") == user_id:
                    results.append({
                        "query": payload.get("query", ""),
                        "response": payload.get("response", ""),
                        "user_id": payload.get("user_id"),
                        "timestamp": payload.get("timestamp", ""),
                        "score": float(result.score),
                        "metadata": {k: v for k, v in payload.items() if k not in ["query", "response", "user_id", "timestamp", "type"]},
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Ошибка при поиске похожих запросов: {e}", exc_info=True)
            return []
