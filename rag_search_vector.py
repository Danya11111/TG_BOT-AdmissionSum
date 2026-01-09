"""
Модуль векторного поиска с использованием Qdrant и GigaChat embeddings.
"""

import logging
import os
from dataclasses import dataclass
from typing import List, Optional

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from embeddings_local import get_embeddings

logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()


@dataclass
class RagHit:
    """Результат поиска."""
    id: str
    title: str
    source: str
    content: str
    score: float


class VectorRagSearcher:
    """Векторный поиск с использованием Qdrant и GigaChat embeddings."""
    
    def __init__(
        self,
        qdrant_host: str = None,
        qdrant_port: int = None,
        collection_name: str = None,
    ) -> None:
        """
        Инициализация векторного поиска.
        
        Args:
            qdrant_host: Хост Qdrant (по умолчанию из .env)
            qdrant_port: Порт Qdrant (по умолчанию из .env)
            collection_name: Название коллекции (по умолчанию из .env)
        """
        self.qdrant_host = qdrant_host or os.getenv("QDRANT_HOST", "localhost")
        self.qdrant_port = qdrant_port or int(os.getenv("QDRANT_PORT", "6333"))
        self.collection_name = collection_name or os.getenv("QDRANT_COLLECTION_NAME", "guu_documents")
        
        logger.info(f"Инициализация VectorRagSearcher: {self.qdrant_host}:{self.qdrant_port}, коллекция: {self.collection_name}")
        
        # Подключение к Qdrant
        try:
            self.client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
            # Проверка подключения
            collections = self.client.get_collections()
            logger.info(f"Подключение к Qdrant успешно. Доступные коллекции: {[c.name for c in collections.collections]}")
        except Exception as e:
            logger.error(f"Ошибка подключения к Qdrant: {e}")
            raise
        
        # Проверка существования коллекции через список коллекций
        try:
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            if self.collection_name not in collection_names:
                logger.error(f"Коллекция {self.collection_name} не найдена")
                logger.error("Запустите скрипт миграции: python rag_build_vector.py")
                raise RuntimeError(f"Коллекция {self.collection_name} не найдена. Запустите миграцию данных.")
            logger.info(f"Коллекция {self.collection_name} найдена")
        except RuntimeError:
            raise
        except Exception as e:
            logger.error(f"Ошибка при проверке коллекции: {e}")
            logger.error("Запустите скрипт миграции: python rag_build_vector.py")
            raise RuntimeError(f"Коллекция {self.collection_name} не найдена. Запустите миграцию данных.")
        
        # Предзагрузка локальной модели embeddings
        try:
            from embeddings_local import get_model
            get_model()  # Загружаем модель при инициализации
            logger.info("Локальная модель embeddings готова")
        except Exception as e:
            logger.warning(f"Не удалось загрузить локальную модель embeddings: {e}")
            logger.warning("Векторизация запросов может быть недоступна")
        
        logger.info("VectorRagSearcher успешно инициализирован")
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        score_threshold: float = 0.0,
        filter_metadata: Optional[dict] = None,
    ) -> List[RagHit]:
        """
        Поиск релевантных документов.
        
        Args:
            query: Текст запроса
            top_k: Количество возвращаемых результатов
            score_threshold: Минимальный score (0.0 - 1.0)
            filter_metadata: Фильтр по метаданным (например, {"source": "https://guu.ru/..."})
        
        Returns:
            Список RagHit с результатами поиска
        """
        logger.debug(f"Векторный поиск: query='{query[:100]}', top_k={top_k}")
        
        try:
            # ШАГ 1: Векторизация запроса через локальную модель
            logger.debug("Векторизация запроса через локальную модель...")
            query_vectors = get_embeddings([query])
            if not query_vectors:
                logger.error("Не удалось получить вектор для запроса")
                return []
            query_vector = query_vectors[0]
            
            # ШАГ 2: Построение фильтра (если указан)
            query_filter = None
            if filter_metadata:
                conditions = []
                for key, value in filter_metadata.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value),
                        )
                    )
                if conditions:
                    query_filter = Filter(must=conditions)
            
            # ШАГ 3: Поиск в Qdrant
            logger.debug(f"Поиск в Qdrant (коллекция: {self.collection_name})...")
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=query_filter,
            )
            
            # ШАГ 4: Преобразование результатов
            hits: List[RagHit] = []
            for result in search_results:
                payload = result.payload
                # Используем chunk_id из payload (оригинальный строковый ID)
                chunk_id = payload.get("chunk_id", str(result.id))
                hits.append(
                    RagHit(
                        id=chunk_id,  # Оригинальный строковый ID из payload
                        title=payload.get("title", ""),
                        source=payload.get("source", ""),
                        content=payload.get("content", ""),
                        score=float(result.score),
                    )
                )
            
            if hits:
                logger.debug(f"Найдено {len(hits)} результатов, лучший score: {hits[0].score:.4f}")
            else:
                logger.warning("Поиск не вернул результатов")
            
            return hits
            
        except Exception as e:
            logger.error(f"Ошибка при векторном поиске: {e}", exc_info=True)
            return []
    
    @staticmethod
    def format_context(hits: List[RagHit]) -> List[str]:
        """
        Форматирует результаты поиска для промпта GigaChat.
        
        Args:
            hits: Список результатов поиска
        
        Returns:
            Список отформатированных строк для контекста
        """
        lines: List[str] = []
        for h in hits:
            # Ограничиваем длину цитаты
            quote_words = h.content.split()[:60]
            quote = " ".join(quote_words)
            lines.append(
                f"{h.id}|{h.title}|{h.source}|page:1|score:{h.score:.3f}|quote:\"{quote}\""
            )
        return lines
