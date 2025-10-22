import json
import logging
import os
from dataclasses import dataclass
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

INDEX_PATH = os.path.join("data", "guu", "index.json")


@dataclass
class RagHit:
    id: str
    title: str
    source: str
    content: str
    score: float


class RagSearcher:
    def __init__(self, index_path: str = INDEX_PATH) -> None:
        logger.info(f"Инициализация RAG-поиска из {index_path}")
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                self.index = json.load(f)
            logger.info(f"Загружено {len(self.index)} документов")
            
            self.docs = [item["content"] for item in self.index]
            self.vectorizer = TfidfVectorizer(max_features=50000, ngram_range=(1, 2))
            logger.info("Построение TF-IDF матрицы...")
            self.matrix = self.vectorizer.fit_transform(self.docs)
            logger.info(f"TF-IDF матрица построена, размер: {self.matrix.shape}")
        except Exception as e:
            logger.error(f"Ошибка при инициализации RAG-поиска: {e}", exc_info=True)
            raise

    def search(self, query: str, top_k: int = 5) -> List[RagHit]:
        logger.debug(f"RAG поиск: query='{query[:100]}', top_k={top_k}")
        try:
            qv = self.vectorizer.transform([query])
            sims = cosine_similarity(qv, self.matrix).ravel()
            order = sims.argsort()[::-1][:top_k]
            hits: List[RagHit] = []
            for idx in order:
                item = self.index[idx]
                score = float(sims[idx])
                hits.append(
                    RagHit(
                        id=item["id"],
                        title=item.get("title", ""),
                        source=item.get("source", ""),
                        content=item.get("content", ""),
                        score=score,
                    )
                )
            
            if hits:
                logger.debug(f"Найдено {len(hits)} результатов, лучший score: {hits[0].score:.4f}")
            else:
                logger.warning("RAG поиск не вернул результатов")
            
            return hits
        except Exception as e:
            logger.error(f"Ошибка при RAG-поиске: {e}", exc_info=True)
            return []

    @staticmethod
    def format_context(hits: List['RagHit']) -> List[str]:
        lines: List[str] = []
        for h in hits:
            quote_words = h.content.split()[:60]
            quote = " ".join(quote_words)
            lines.append(
                f"{h.id}|{h.title}|{h.source}|page:1|score:{h.score:.3f}|quote:\"{quote}\""
            )
        return lines


