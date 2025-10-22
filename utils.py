import re
from typing import List, Dict, Any, Optional
import pandas as pd
from stats_predictor import get_predictor


def calculate_total_score(ege_score: int, achievements: List[str]) -> int:
    """Суммирует баллы ЕГЭ и достижения"""
    total = ege_score
    achievement_points = 0
    
    for achievement in achievements:
        if achievement in ["Диплом с отличием", "Золотой ГТО"]:
            achievement_points += 5
    
    total += min(achievement_points, 10)  # Максимум 10 баллов за достижения
    return total


def normalize_form(form: str) -> str:
    """Стандартизирует форму обучения"""
    form_lower = form.lower()
    if "бюджет" in form_lower:
        return "бюджет"
    elif "договор" in form_lower or "платн" in form_lower:
        return "договор"
    return form


def normalize_subject_name(subject: str) -> str:
    """Нормализует названия предметов"""
    subject_lower = subject.lower()
    if "матем" in subject_lower:
        return "математика"
    elif "русск" in subject_lower:
        return "русский язык"
    elif "информ" in subject_lower:
        return "информатика"
    elif "обществ" in subject_lower:
        return "обществознание"
    elif "истор" in subject_lower:
        return "история"
    elif "биолог" in subject_lower:
        return "биология"
    elif "хими" in subject_lower:
        return "химия"
    elif "физик" in subject_lower:
        return "физика"
    elif "географ" in subject_lower:
        return "география"
    elif "литератур" in subject_lower:
        return "литература"
    elif "английск" in subject_lower:
        return "английский язык"
    return subject


def safe_callback_data(data: str) -> str:
    """Ограничивает длину и безопасность callback_data"""
    # Убираем недопустимые символы
    safe_data = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', data)
    # Ограничиваем длину (Telegram limit ~64 bytes)
    if len(safe_data) > 60:
        safe_data = safe_data[:60]
    return safe_data


def get_directions_data(subjects: List[str], form: str, excel_path: str = "directions.xlsx") -> List[Dict[str, Any]]:
    """Находит направления по предметам и форме обучения"""
    try:
        df = pd.read_excel(excel_path, engine='openpyxl')
    except FileNotFoundError:
        # Возвращаем тестовые данные если файл не найден
        return get_test_directions_data(subjects, form)
    
    normalized_form = normalize_form(form)
    normalized_subjects = [normalize_subject_name(s) for s in subjects]
    
    # Фильтруем по форме обучения
    if normalized_form == "бюджет":
        df_filtered = df[df['Форма обучения'].str.contains('бюджет', case=False, na=False)]
    elif normalized_form == "договор":
        df_filtered = df[df['Форма обучения'].str.contains('договор|платн', case=False, na=False)]
    else:
        df_filtered = df
    
    matching_directions = []
    
    for _, row in df_filtered.iterrows():
        required_subjects_str = str(row.get('Предметы', ''))
        required_subjects = re.findall(r'\b\w+\b', required_subjects_str.lower())
        
        # Проверяем наличие математики (обязательно)
        if 'математика' not in normalized_subjects:
            continue
            
        # Проверяем совпадение предметов (минимум 2)
        matches = sum(1 for req_subj in required_subjects 
                     if any(norm_subj in req_subj or req_subj in norm_subj 
                           for norm_subj in normalized_subjects))
        
        if matches >= 2:
            direction = {
                'code': str(row.get('Код', '')),
                'name': str(row.get('Название', '')),
                'subjects': required_subjects_str,
                'passing_score_2022': row.get('Год 2022', 0),
                'passing_score_2023': row.get('Год 2023', 0),
                'passing_score_2024': row.get('Год 2024', 0),
                'predicted_score_2025': row.get('Год 2025', 0),
                'budget_places': row.get('Кол-во бюджетных мест всего', 0),
                'target_quota': row.get('квота приема на целевое обучение', 0),
                'special_quota': row.get('особая квота', 0),
                'separate_quota': row.get('отдельная квота', 0),
            }
            matching_directions.append(direction)
    
    return matching_directions


def get_test_directions_data(subjects: List[str], form: str) -> List[Dict[str, Any]]:
    """Тестовые данные направлений для демонстрации"""
    test_directions = [
        {
            'code': '38.03.01',
            'name': 'Экономика',
            'subjects': 'математика, русский язык, обществознание',
            'passing_score_2022': 245,
            'passing_score_2023': 248,
            'passing_score_2024': 252,
            'predicted_score_2025': 255,
            'budget_places': 50,
            'target_quota': 5,
            'special_quota': 3,
            'separate_quota': 2,
        },
        {
            'code': '38.03.02',
            'name': 'Менеджмент',
            'subjects': 'математика, русский язык, обществознание',
            'passing_score_2022': 240,
            'passing_score_2023': 243,
            'passing_score_2024': 247,
            'predicted_score_2025': 250,
            'budget_places': 45,
            'target_quota': 4,
            'special_quota': 2,
            'separate_quota': 1,
        },
        {
            'code': '09.03.01',
            'name': 'Информатика и вычислительная техника',
            'subjects': 'математика, русский язык, информатика',
            'passing_score_2022': 250,
            'passing_score_2023': 253,
            'passing_score_2024': 257,
            'predicted_score_2025': 260,
            'budget_places': 30,
            'target_quota': 3,
            'special_quota': 2,
            'separate_quota': 1,
        }
    ]
    
    # Фильтруем по предметам
    normalized_subjects = [normalize_subject_name(s) for s in subjects]
    matching = []
    
    for direction in test_directions:
        required_subjects = direction['subjects'].split(', ')
        matches = sum(1 for req_subj in required_subjects 
                     if any(norm_subj in req_subj.lower() or req_subj.lower() in norm_subj 
                           for norm_subj in normalized_subjects))
        
        if 'математика' in normalized_subjects and matches >= 2:
            matching.append(direction)
    
    return matching


def calculate_chance(total_score: int, predicted_score: int) -> str:
    """Оценивает шансы поступления"""
    if total_score >= predicted_score + 10:
        return "🟢 Высокие"
    elif total_score >= predicted_score - 5:
        return "🟡 Средние"
    else:
        return "🔴 Низкие"


def get_improved_prediction(direction_code: str, form: str) -> Dict:
    """
    Получает улучшенный прогноз для направления.
    Использует StatsPredictor с данными из CSV файлов.
    """
    predictor = get_predictor()
    return predictor.calculate_prediction(direction_code, form)


def get_direction_chart(direction_code: str, direction_name: str, form: str, user_score: int):
    """
    Генерирует график проходных баллов для направления.
    Возвращает BytesIO объект с изображением или None.
    """
    predictor = get_predictor()
    return predictor.generate_plot(direction_code, direction_name, form, user_score)


def get_full_direction_stats(direction_code: str, form: str) -> Dict:
    """
    Получает полную статистику по направлению из CSV файлов.
    """
    predictor = get_predictor()
    return predictor.get_direction_details(direction_code, form)


def find_directions_by_subjects(subjects: List[str], form: str) -> List[Dict[str, Any]]:
    """
    Подбор направлений по выбранным предметам на основе CSV статистики.
    Возвращает список аналитики направлений в едином формате.
    """
    predictor = get_predictor()
    return predictor.find_directions_by_subjects(subjects, form)
