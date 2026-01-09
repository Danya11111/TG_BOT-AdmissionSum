"""
Локальный модуль для векторизации текстов с использованием Sentence Transformers.
Альтернатива GigaChat Embeddings API.
"""

import logging
from typing import List

logger = logging.getLogger(__name__)

# Глобальная переменная для модели (загружается один раз)
_model = None


def get_model():
    """Загружает модель Sentence Transformers (ленивая загрузка)."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Загрузка модели Sentence Transformers...")
            # Используем мультиязычную модель (поддерживает русский)
            # Альтернативы: 'intfloat/multilingual-e5-base', 'ai-forever/sbert_large_nlu_ru'
            _model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            logger.info("Модель загружена успешно")
        except ImportError:
            logger.error("sentence-transformers не установлен. Установите: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Ошибка загрузки модели: {e}")
            raise
    return _model


def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Получает векторные представления текстов через локальную модель.
    
    Args:
        texts: Список текстов для векторизации
    
    Returns:
        Список векторов (каждый вектор - список из 768 float)
    """
    model = get_model()
    logger.debug(f"Векторизация {len(texts)} текстов через локальную модель...")
    
    try:
        # Векторизация
        embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        
        # Преобразование numpy array в список списков float
        result = [embedding.tolist() for embedding in embeddings]
        
        logger.debug(f"Векторизация завершена, размерность: {len(result[0])}")
        return result
    except Exception as e:
        logger.error(f"Ошибка при векторизации: {e}")
        raise


def get_vector_size() -> int:
    """Возвращает размерность векторов (384 для multilingual-MiniLM-L12-v2)."""
    return 384
