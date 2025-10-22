"""
Скрипт для обработки PDF и DOCX документов и добавления их в RAG индекс.
"""

import datetime as dt
import json
import os
import re
from typing import List, Dict, Tuple

try:
    from PyPDF2 import PdfReader
except ImportError:
    print("ОШИБКА: Установите PyPDF2: pip install PyPDF2")
    exit(1)

try:
    from docx import Document
except ImportError:
    print("ОШИБКА: Установите python-docx: pip install python-docx")
    exit(1)


DOCS_DIR = "GUU_docs"
RAW_DIR = os.path.join("data", "guu", "raw")
CHUNKS_DIR = os.path.join("data", "guu", "chunks")
INDEX_PATH = os.path.join("data", "guu", "index.json")


def ensure_dirs() -> None:
    """Создает необходимые директории, если их нет."""
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(CHUNKS_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)


def extract_text_from_pdf(pdf_path: str) -> str:
    """Извлекает текст из PDF файла."""
    try:
        reader = PdfReader(pdf_path)
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n".join(text_parts)
    except Exception as e:
        print(f"Ошибка при чтении PDF {pdf_path}: {e}")
        return ""


def extract_text_from_docx(docx_path: str) -> str:
    """Извлекает текст из DOCX файла."""
    try:
        doc = Document(docx_path)
        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)
        return "\n".join(text_parts)
    except Exception as e:
        print(f"Ошибка при чтении DOCX {docx_path}: {e}")
        return ""


def clean_text(text: str) -> str:
    """Очищает и нормализует текст."""
    # Удаляем лишние пробелы и переносы
    text = re.sub(r'\s+', ' ', text)
    # Удаляем служебные символы
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', text)
    return text.strip()


def chunk_words(words: List[str], target: int = 700, min_size: int = 500, overlap: int = 60) -> List[List[str]]:
    """
    Разбивает слова на чанки с перекрытием.
    """
    chunks: List[List[str]] = []
    i = 0
    n = len(words)
    while i < n:
        j = min(i + target, n)
        # Ensure minimum size unless at end
        if j - i < min_size and j < n:
            j = min(i + min_size, n)
        chunk = words[i:j]
        chunks.append(chunk)
        if j >= n:
            break
        i = max(j - overlap, i + 1)
    return chunks


def save_raw(filename: str, title: str, text: str, source_path: str) -> str:
    """Сохраняет сырой текст документа."""
    # Создаем безопасное имя файла
    safe_filename = re.sub(r'[^\w\-\.]', '_', filename, flags=re.UNICODE)
    filepath = os.path.join(RAW_DIR, f"{safe_filename}.txt")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Source: {source_path}\n")
        if title:
            f.write(f"# Title: {title}\n")
        f.write("\n")
        f.write(text)
    
    return filepath


def write_chunk(chunk_id: str, source: str, title: str, content: str) -> str:
    """Записывает чанк в файл."""
    filename = f"{chunk_id}.txt"
    path = os.path.join(CHUNKS_DIR, filename)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Source: {source}\n")
        if title:
            f.write(f"# Title: {title}\n")
        f.write("\n")
        f.write(content)
    
    return path


def process_documents() -> List[Dict[str, str]]:
    """
    Обрабатывает все PDF и DOCX файлы из папки GUU_docs.
    Возвращает список документов для добавления в индекс.
    """
    documents = []
    
    if not os.path.exists(DOCS_DIR):
        print(f"ОШИБКА: Папка {DOCS_DIR} не найдена!")
        return documents
    
    # Ищем все PDF и DOCX файлы
    all_files = []
    for root, dirs, files in os.walk(DOCS_DIR):
        for file in files:
            if file.lower().endswith(('.pdf', '.docx')):
                all_files.append(os.path.join(root, file))
    
    print(f"Найдено {len(all_files)} документов для обработки")
    
    for idx, file_path in enumerate(all_files, 1):
        filename = os.path.basename(file_path)
        print(f"\n[{idx}/{len(all_files)}] Обработка: {filename}")
        
        # Извлекаем текст в зависимости от типа файла
        if file_path.lower().endswith('.pdf'):
            text = extract_text_from_pdf(file_path)
        elif file_path.lower().endswith('.docx'):
            text = extract_text_from_docx(file_path)
        else:
            continue
        
        if not text or len(text.strip()) < 100:
            print(f"  ⚠ Пропущен (слишком мало текста)")
            continue
        
        # Очищаем текст
        text = clean_text(text)
        
        # Используем имя файла как заголовок
        title = os.path.splitext(filename)[0]
        
        # Сохраняем сырой текст
        save_raw(filename, title, text, file_path)
        
        documents.append({
            "source": file_path,
            "title": title,
            "text": text
        })
        
        print(f"  ✓ Извлечено {len(text)} символов")
    
    return documents


def build_chunks_and_update_index(documents: List[Dict[str, str]]) -> None:
    """
    Разбивает документы на чанки и обновляет индекс.
    """
    # Загружаем существующий индекс
    existing_index = []
    if os.path.exists(INDEX_PATH):
        try:
            with open(INDEX_PATH, "r", encoding="utf-8") as f:
                existing_index = json.load(f)
            print(f"\nЗагружен существующий индекс: {len(existing_index)} записей")
        except Exception as e:
            print(f"ОШИБКА при загрузке существующего индекса: {e}")
            print("Будет создан новый индекс")
    
    # Находим максимальный номер чанка
    max_chunk_num = 0
    for item in existing_index:
        chunk_id = item.get("id", "")
        if chunk_id.startswith("chunk"):
            try:
                num = int(chunk_id.replace("chunk", ""))
                max_chunk_num = max(max_chunk_num, num)
            except:
                pass
    
    counter = max_chunk_num + 1
    date_str = dt.date.today().isoformat()
    new_chunks = []
    
    print(f"\nСоздание чанков (начиная с chunk{counter:06d})...")
    
    for doc in documents:
        words = doc["text"].split()
        parts = chunk_words(words)
        
        for part in parts:
            content = " ".join(part)
            chunk_id = f"chunk{counter:06d}"
            
            write_chunk(chunk_id, doc["source"], doc["title"], content)
            
            new_chunks.append({
                "id": chunk_id,
                "source": doc["source"],
                "title": doc["title"] or "",
                "content": content,
                "date": date_str,
            })
            
            counter += 1
    
    # Объединяем существующий индекс с новыми чанками
    updated_index = existing_index + new_chunks
    
    # Сохраняем обновленный индекс
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(updated_index, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Создано {len(new_chunks)} новых чанков")
    print(f"✓ Общее количество чанков в индексе: {len(updated_index)}")
    print(f"✓ Индекс сохранен: {INDEX_PATH}")


def main():
    """Основная функция."""
    print("=" * 70)
    print("Обработка документов ГУУ для RAG")
    print("=" * 70)
    
    ensure_dirs()
    
    # Обрабатываем документы
    documents = process_documents()
    
    if not documents:
        print("\n⚠ Документы не найдены или не обработаны")
        return
    
    print(f"\n✓ Успешно обработано документов: {len(documents)}")
    
    # Создаем чанки и обновляем индекс
    build_chunks_and_update_index(documents)
    
    print("\n" + "=" * 70)
    print("✓ ГОТОВО! Все документы добавлены в индекс RAG")
    print("=" * 70)
    print("\nТеперь GigaChat будет использовать эти данные для ответов!")
    print("\nДля применения изменений перезапустите бота:")
    print("  python main.py")


if __name__ == "__main__":
    main()

