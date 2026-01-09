"""
Скрипт для обработки всех документов из папки GUU_docs и добавления их в векторную БД Qdrant.
"""

import argparse
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document
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

GUU_DOCS_DIR = "GUU_docs"
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "guu_documents")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
VECTOR_SIZE = get_vector_size()
BATCH_SIZE = 20
CHUNK_SIZE = 500  # Примерно 500 слов на чанк


def extract_text_from_pdf(file_path: str) -> str:
    """Извлекает текст из PDF файла."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Ошибка при чтении PDF {file_path}: {e}")
        return ""


def extract_text_from_docx(file_path: str) -> str:
    """Извлекает текст из DOCX файла."""
    try:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Ошибка при чтении DOCX {file_path}: {e}")
        return ""


def extract_text_from_xlsx(file_path: str) -> str:
    """Извлекает текст из XLSX файла (базовая версия - только названия листов и ячеек)."""
    try:
        import pandas as pd
        # Читаем все листы
        excel_file = pd.ExcelFile(file_path, engine='openpyxl')
        text = ""
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name, engine='openpyxl')
            # Преобразуем DataFrame в текст
            text += f"Лист: {sheet_name}\n"
            text += df.to_string(index=False) + "\n\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Ошибка при чтении XLSX {file_path}: {e}")
        return ""


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
    """Разбивает текст на чанки по словам."""
    if not text:
        return []
    
    words = text.split()
    chunks = []
    current_chunk = []
    current_size = 0
    
    for word in words:
        current_chunk.append(word)
        current_size += 1
        
        if current_size >= chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_size = 0
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks


def process_documents(docs_dir: str) -> List[Dict]:
    """Обрабатывает все документы из папки GUU_docs."""
    docs_dir_path = Path(docs_dir)
    if not docs_dir_path.exists():
        logger.error(f"Папка {docs_dir} не найдена")
        return []
    
    documents = []
    counter = 1
    
    # Обрабатываем все файлы
    for file_path in docs_dir_path.iterdir():
        if file_path.is_file():
            file_name = file_path.name
            file_ext = file_path.suffix.lower()
            
            logger.info(f"Обработка файла: {file_name}")
            
            text = ""
            if file_ext == ".pdf":
                text = extract_text_from_pdf(str(file_path))
            elif file_ext == ".docx":
                text = extract_text_from_docx(str(file_path))
            elif file_ext in [".xlsx", ".xls"]:
                text = extract_text_from_xlsx(str(file_path))
            else:
                logger.warning(f"Неподдерживаемый формат файла: {file_ext}")
                continue
            
            if not text:
                logger.warning(f"Не удалось извлечь текст из {file_name}")
                continue
            
            # Разбиваем на чанки
            chunks = chunk_text(text)
            
            for i, chunk_text_content in enumerate(chunks):
                chunk_id = f"doc_{counter:06d}_{i}"
                documents.append({
                    "id": chunk_id,
                    "source": f"GUU_docs/{file_name}",
                    "title": file_name.replace("_", " ").replace("-", " "),
                    "content": chunk_text_content,
                    "file_type": file_ext[1:],  # Без точки
                })
            
            counter += 1
            logger.info(f"Обработано {len(chunks)} чанков из {file_name}")
    
    logger.info(f"Всего обработано {len(documents)} чанков из {counter - 1} файлов")
    return documents


def upload_to_qdrant(
    client: QdrantClient,
    documents: List[Dict],
    collection_name: str,
    batch_size: int,
) -> None:
    """Векторизует и загружает документы в Qdrant."""
    logger.info(f"Начало векторизации и загрузки {len(documents)} чанков в коллекцию {collection_name}")
    
    total_batches = (len(documents) + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(documents))
        batch = documents[start_idx:end_idx]
        
        logger.info(f"Обработка батча {batch_num + 1}/{total_batches} ({len(batch)} чанков)...")
        
        try:
            texts = [item["content"] for item in batch]
            # Получаем embeddings
            embeddings = get_embeddings(texts)
            
            if not embeddings or len(embeddings) != len(batch):
                logger.error(f"Ошибка: получено {len(embeddings) if embeddings else 0} embeddings для {len(batch)} текстов")
                continue
            
            points = []
            for i, item in enumerate(batch):
                # Преобразуем строковый ID в числовой
                chunk_id_str = item["id"]
                # Извлекаем число из ID (doc_000001_0 -> 1000001)
                match = re.search(r'(\d+)', chunk_id_str)
                if match:
                    point_id = int(match.group(1)) * 1000 + i  # Умножаем на 1000 для уникальности
                else:
                    point_id = hash(chunk_id_str) % (10 ** 9)  # Fallback на хеш
                
                points.append(
                    PointStruct(
                        id=point_id,
                        vector=embeddings[i],
                        payload={
                            "chunk_id": chunk_id_str,
                            "title": item["title"],
                            "source": item["source"],
                            "content": item["content"],
                            "file_type": item.get("file_type", ""),
                        },
                    )
                )
            
            # Загружаем в Qdrant
            client.upsert(
                collection_name=collection_name,
                points=points,
            )
            
            logger.info(f"Загружено {len(batch)}/{len(documents)} чанков ({end_idx * 100 // len(documents)}%)")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке батча {batch_num + 1}: {e}", exc_info=True)
            continue
    
    logger.info(f"Загрузка завершена. Всего загружено {len(documents)} чанков в Qdrant")


def main() -> None:
    parser = argparse.ArgumentParser(description="Обработка документов из GUU_docs и загрузка в Qdrant")
    parser.add_argument("--docs-dir", type=str, default=GUU_DOCS_DIR, help="Путь к папке с документами")
    parser.add_argument("--collection", type=str, default=COLLECTION_NAME, help="Название коллекции в Qdrant")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help="Размер батча для векторизации")
    args = parser.parse_args()
    
    # Подключение к Qdrant
    logger.info(f"Подключение к Qdrant {QDRANT_HOST}:{QDRANT_PORT}...")
    try:
        qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        # Проверка подключения
        qdrant_client.get_collections()
        logger.info("Подключение к Qdrant успешно")
    except Exception as e:
        logger.error(f"Ошибка подключения к Qdrant: {e}")
        logger.error("Убедитесь, что Qdrant запущен (docker-compose up)")
        return
    
    # Проверка существования коллекции
    try:
        collections = qdrant_client.get_collections()
        collection_names = [c.name for c in collections.collections]
        if args.collection not in collection_names:
            logger.error(f"Коллекция {args.collection} не найдена")
            logger.error("Сначала запустите: python rag_build_vector.py")
            return
        logger.info(f"Коллекция {args.collection} найдена")
    except Exception as e:
        logger.error(f"Ошибка при проверке коллекции: {e}")
        return
    
    # Обработка документов
    logger.info(f"Начало обработки документов из {args.docs_dir}...")
    documents = process_documents(args.docs_dir)
    
    if not documents:
        logger.warning("Не найдено документов для обработки")
        return
    
    # Загрузка в Qdrant
    upload_to_qdrant(
        qdrant_client,
        documents,
        args.collection,
        args.batch_size,
    )
    
    logger.info("✅ Обработка документов завершена!")
    logger.info(f"   Коллекция: {args.collection}")
    logger.info(f"   Загружено чанков: {len(documents)}")
    logger.info(f"   Размерность векторов: {VECTOR_SIZE}")


if __name__ == "__main__":
    main()
