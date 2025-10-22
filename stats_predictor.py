"""
Модуль для прогнозирования проходных баллов и визуализации статистики.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple
import re
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Для работы без GUI
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

logger = logging.getLogger(__name__)

# Настройка стиля графиков
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.unicode_minus'] = False


class StatsPredictor:
    """Класс для работы со статистикой и прогнозирования."""
    
    STATS_DIR = os.path.join("data", "guu", "stats")
    
    # Мапинг файлов статистики
    STATS_FILES = {
        "очная_бюджет": "Статистика баллов - очная бюджет.csv",
        "очная_договор": "Статистика баллов - Договор ОЧ.csv",
        "озо_бюджет": "Статистика баллов - Бюджет ОЗ.csv",
        "озо_договор": "Статистика баллов - Договор ОЗ.csv",
    }
    
    def __init__(self):
        """Инициализация и загрузка данных."""
        self.stats_data = {}
        self.load_all_stats()
    
    def load_all_stats(self) -> None:
        """Загружает всю статистику из CSV файлов с исправлениями."""
        for key, filename in self.STATS_FILES.items():
            filepath = os.path.join(self.STATS_DIR, filename)
            if os.path.exists(filepath):
                try:
                    # Читаем CSV файл
                    df = pd.read_csv(filepath, encoding='utf-8')
                    
                    # Очищаем данные более аккуратно
                    df = df.dropna(subset=['Направление'])
                    df = df[df['Направление'].str.strip() != '']
                    df = df[df['Направление'].str.strip() != '-']
                    
                    # ИСПРАВЛЕНИЕ: для файла "Статистика баллов - очная бюджет.csv" используем правильную загрузку
                    if filename == "Статистика баллов - очная бюджет.csv":
                        # Читаем с правильным заголовком (строка 3)
                        df = pd.read_csv(filepath, encoding='utf-8', header=2)
                        
                        # Создаем маппинг для переименования колонок по индексу
                        # Структура: 0=Направление, 1-6=Годы 2019-2024, 7=Год 2025, 8=места, 17=предметы
                        column_rename = {}
                        if len(df.columns) > 0:
                            column_rename[df.columns[0]] = 'Направление'
                        if len(df.columns) > 1:
                            column_rename[df.columns[1]] = 'Год 2019'
                        if len(df.columns) > 2:
                            column_rename[df.columns[2]] = 'Год 2020'
                        if len(df.columns) > 3:
                            column_rename[df.columns[3]] = 'Год 2021'
                        if len(df.columns) > 4:
                            column_rename[df.columns[4]] = 'Год 2022'
                        if len(df.columns) > 5:
                            column_rename[df.columns[5]] = 'Год 2023'
                        if len(df.columns) > 6:
                            column_rename[df.columns[6]] = 'Год 2024'
                        if len(df.columns) > 7:
                            column_rename[df.columns[7]] = 'Год 2025'
                        if len(df.columns) > 8:
                            column_rename[df.columns[8]] = 'Кол-во бюджетных мест'
                        if len(df.columns) > 17:
                            column_rename[df.columns[17]] = 'Предметы'
                        
                        df = df.rename(columns=column_rename)
                        
                        # Очищаем данные
                        if 'Направление' in df.columns:
                            df = df.dropna(subset=['Направление'])
                            df = df[df['Направление'].astype(str).str.strip() != '']
                            df = df[df['Направление'].astype(str).str.strip() != '-']
                            
                            # Фильтруем только реальные направления
                            df = df[df['Направление'].astype(str).str.contains(r'\d{2}\.\d{2}\.\d{2}', na=False, regex=True)]
                        
                        self.stats_data[key] = df
                        logger.info(f"Загружена статистика {key}: {len(df)} направлений")
                        continue
                    
                    # Более мягкий фильтр для направлений
                    df = df[df['Направление'].str.contains(r'\d{2}\.\d{2}\.\d{2}', na=False, regex=True)]
                    
                    # Дополнительная очистка от строк с числами вместо названий
                    df = df[~df['Направление'].str.match(r'^\d+$', na=False)]
                    
                    self.stats_data[key] = df
                    logger.info(f"Загружена статистика {key}: {len(df)} направлений")
                except Exception as e:
                    logger.error(f"Ошибка загрузки {filepath}: {e}")
            else:
                logger.warning(f"Файл статистики не найден: {filepath}")
    
    def get_stats_for_form(self, form: str) -> Optional[pd.DataFrame]:
        """Возвращает статистику для указанной формы обучения."""
        form_lower = form.lower().strip()

        # Поддержка внутренних ключей из бота:
        # 'budget' (очно-бюджетная), 'contract' (очно-договорная),
        # 'part_budget' (очно-заочная бюджет), 'part_contract' (очно-заочная договор)
        if form_lower in ("budget", "contract", "part_budget", "part_contract"):
            mapping = {
                "budget": "очная_бюджет",
                "contract": "очная_договор",
                "part_budget": "озо_бюджет",
                "part_contract": "озо_договор",
            }
            key = mapping.get(form_lower)
            return self.stats_data.get(key)
        
        if "очно-бюджет" in form_lower or ("очн" in form_lower and "бюджет" in form_lower):
            # Используем данные из бюджетного файла
            return self.stats_data.get("очная_бюджет")
        elif "очно-договор" in form_lower or ("очн" in form_lower and "договор" in form_lower):
            return self.stats_data.get("очная_договор")
        elif "озо" in form_lower and "бюджет" in form_lower:
            return self.stats_data.get("озо_бюджет")
        elif "озо" in form_lower and "договор" in form_lower:
            return self.stats_data.get("озо_договор")
        
        # По умолчанию очная бюджет
        return self.stats_data.get("очная_бюджет")
    
    def find_direction_stats(self, direction_code: str, form: str) -> Optional[pd.Series]:
        """Ищет статистику для конкретного направления."""
        df = self.get_stats_for_form(form)
        if df is None:
            return None
        
        # Ищем по коду направления
        for idx, row in df.iterrows():
            direction_str = str(row.get('Направление', ''))
            if direction_code in direction_str:
                return row
        
        return None
    
    def calculate_prediction(self, direction_code: str, form: str) -> Dict:
        """
        Вычисляет улучшенный прогноз проходного балла.
        Использует взвешенное среднее с учетом трендов.
        """
        row = self.find_direction_stats(direction_code, form)
        if row is None:
            return {
                'predicted_score': None,
                'method': 'no_data',
                'confidence': 'low',
                'historical_scores': []
            }
        
        # Извлекаем баллы по годам
        years = ['Год 2019', 'Год 2020', 'Год 2021', 'Год 2022', 'Год 2023', 'Год 2024']
        scores = []
        valid_years = []
        
        for year in years:
            score = row.get(year)
            if pd.notna(score) and score != '-' and score != 0:
                try:
                    scores.append(float(score))
                    valid_years.append(int(year.split()[-1]))
                except (ValueError, TypeError):
                    pass
        
        if len(scores) == 0:
            return {
                'predicted_score': None,
                'method': 'no_valid_data',
                'confidence': 'low',
                'historical_scores': []
            }
        
        # Если есть готовый прогноз в данных
        predicted_2025 = row.get('Год 2025')
        if pd.notna(predicted_2025) and predicted_2025 != '-' and predicted_2025 != 0:
            try:
                return {
                    'predicted_score': int(float(predicted_2025)),
                    'method': 'official_prediction',
                    'confidence': 'high',
                    'historical_scores': list(zip(valid_years, scores))
                }
            except (ValueError, TypeError):
                pass
        
        # Метод 1: Взвешенное среднее (больший вес последним годам)
        weights = np.arange(1, len(scores) + 1)
        weighted_avg = np.average(scores, weights=weights)
        
        # Метод 2: Линейная регрессия (тренд)
        if len(scores) >= 3:
            coeffs = np.polyfit(range(len(scores)), scores, 1)
            trend = coeffs[0]  # Наклон
            trend_prediction = scores[-1] + trend
            
            # Комбинированный прогноз (70% взвешенное среднее + 30% тренд)
            combined = weighted_avg * 0.7 + trend_prediction * 0.3
            
            confidence = 'high' if len(scores) >= 4 else 'medium'
        else:
            # Мало данных - используем только взвешенное среднее
            combined = weighted_avg
            confidence = 'medium' if len(scores) >= 2 else 'low'
        
        return {
            'predicted_score': int(round(combined)),
            'method': 'weighted_avg_with_trend',
            'confidence': confidence,
            'historical_scores': list(zip(valid_years, scores)),
            'trend': coeffs[0] if len(scores) >= 3 else 0
        }
    
    def generate_plot(self, direction_code: str, direction_name: str, form: str, 
                     user_score: int) -> Optional[BytesIO]:
        """
        Генерирует график проходных баллов для направления.
        Возвращает BytesIO объект с PNG изображением.
        """
        row = self.find_direction_stats(direction_code, form)
        if row is None:
            logger.warning(f"Статистика не найдена для {direction_code}")
            return None
        
        # Извлекаем данные
        years = ['Год 2019', 'Год 2020', 'Год 2021', 'Год 2022', 'Год 2023', 'Год 2024']
        scores = []
        valid_years = []
        
        for year in years:
            score = row.get(year)
            if pd.notna(score) and score != '-' and score != 0:
                try:
                    scores.append(float(score))
                    valid_years.append(int(year.split()[-1]))
                except (ValueError, TypeError):
                    pass
        
        if len(scores) == 0:
            logger.warning(f"Нет валидных данных для графика {direction_code}")
            return None
        
        # Прогноз на 2025
        prediction = self.calculate_prediction(direction_code, form)
        if prediction['predicted_score']:
            valid_years.append(2025)
            scores.append(prediction['predicted_score'])
        
        # Создание графика
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Линия проходных баллов
        ax.plot(valid_years[:-1] if len(valid_years) > len(scores) - 1 else valid_years, 
                scores[:-1] if prediction['predicted_score'] else scores, 
                marker='o', linewidth=2, markersize=8, label='Проходной балл', color='#2E86AB')
        
        # Прогноз на 2025 (другим цветом)
        if prediction['predicted_score']:
            ax.plot([valid_years[-2], valid_years[-1]], [scores[-2], scores[-1]], 
                   marker='o', linewidth=2, markersize=8, label='Прогноз 2025', 
                   color='#A23B72', linestyle='--')
        
        # Линия балла пользователя
        ax.axhline(y=user_score, color='#F18F01', linestyle='--', linewidth=2, 
                  label=f'Ваш балл: {user_score}')
        
        # Заливка области между проходным баллом и баллом пользователя
        if user_score >= min(scores):
            ax.fill_between(valid_years, user_score, min(scores) - 10, 
                           alpha=0.2, color='green', label='Зона поступления')
        
        # Настройка графика
        ax.set_xlabel('Год', fontsize=12, fontweight='bold')
        ax.set_ylabel('Проходной балл', fontsize=12, fontweight='bold')
        ax.set_title(f'{direction_code} — {direction_name}\nДинамика проходных баллов', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Установка целочисленных меток по оси X
        ax.set_xticks(valid_years)
        ax.set_xticklabels(valid_years, rotation=0)
        
        # Диапазон по Y с запасом
        y_min = min(min(scores), user_score) - 20
        y_max = max(max(scores), user_score) + 20
        ax.set_ylim(y_min, y_max)
        
        # Добавление значений на точки
        for i, (year, score) in enumerate(zip(valid_years, scores)):
            ax.annotate(f'{int(score)}', 
                       xy=(year, score), 
                       xytext=(0, 10), 
                       textcoords='offset points',
                       ha='center', 
                       fontsize=9,
                       fontweight='bold')
        
        plt.tight_layout()
        
        # Сохранение в BytesIO
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        return buf
    
    def get_direction_details(self, direction_code: str, form: str) -> Dict:
        """Возвращает детальную информацию о направлении."""
        row = self.find_direction_stats(direction_code, form)
        if row is None:
            return {}
        
        details = {
            'code': direction_code,
            'name': str(row.get('Направление', '')).split('—')[1].strip() if '—' in str(row.get('Направление', '')) else '',
            'subjects': str(row.get('Предметы', '')),
        }
        
        # Извлекаем проходные баллы
        years = ['Год 2019', 'Год 2020', 'Год 2021', 'Год 2022', 'Год 2023', 'Год 2024']
        for year in years:
            year_key = year.replace('Год ', '').strip()
            score = row.get(year)
            if pd.notna(score) and score != '-':
                try:
                    details[f'score_{year_key}'] = int(float(score))
                except (ValueError, TypeError):
                    details[f'score_{year_key}'] = None
            else:
                details[f'score_{year_key}'] = None
        
        # Прогноз
        prediction = self.calculate_prediction(direction_code, form)
        details['predicted_2025'] = prediction['predicted_score']
        details['prediction_confidence'] = prediction['confidence']
        
        # Места и квоты - ищем правильные колонки
        budget_places = None
        contract_places = None
        
        # Ищем колонки с местами по названию
        for col in row.index:
            if 'бюджетных мест' in str(col).lower():
                budget_places = row.get(col)
            elif 'договорных мест' in str(col).lower():
                contract_places = row.get(col)
        
        # ИСПРАВЛЕНИЕ: Если не нашли по названию, ищем по позиции (для Unnamed колонок)
        # В CSV файлах колонка 8 (Unnamed: 8) обычно содержит количество мест
        if budget_places is None and contract_places is None:
            # Ищем колонку "Unnamed: 8" или по индексу
            if 'Unnamed: 8' in row.index:
                places_value = row.get('Unnamed: 8')
                if pd.notna(places_value) and places_value != '-':
                    # Определяем тип мест по форме обучения
                    if 'бюджет' in form.lower():
                        budget_places = places_value
                    else:
                        contract_places = places_value
            # Или ищем по индексу напрямую
            elif len(row.index) > 8:
                # Колонка с индексом 8 (9-я по счету)
                col_at_8 = row.index[8] if len(row.index) > 8 else None
                if col_at_8 and 'Unnamed' in str(col_at_8):
                    places_value = row.get(col_at_8)
                    if pd.notna(places_value) and places_value != '-':
                        if 'бюджет' in form.lower():
                            budget_places = places_value
                        else:
                            contract_places = places_value
        
        if pd.notna(budget_places):
            try:
                details['budget_places'] = int(float(budget_places))
            except (ValueError, TypeError):
                details['budget_places'] = 0
        else:
            details['budget_places'] = 0
        
        if pd.notna(contract_places):
            try:
                details['contract_places'] = int(float(contract_places))
            except (ValueError, TypeError):
                details['contract_places'] = 0
        else:
            details['contract_places'] = 0
        
        # Квоты (если есть)
        for quota_type in ['общие места', 'квота приема на целевое обучение', 
                          'особая квота', 'отдельная квота']:
            quota_value = row.get(quota_type)
            if pd.notna(quota_value):
                try:
                    details[quota_type.replace(' ', '_')] = int(float(quota_value))
                except (ValueError, TypeError):
                    pass
        
        return details

    # --- Новый метод: подбор направлений по предметам из CSV ---
    def find_directions_by_subjects(self, user_subjects: List[str], form: str) -> List[Dict]:
        """
        Ищет направления по таблицам статистики (CSV) на основе выбранных предметов.
        Логика совпадений:
        - нормализованные строки, разделители: запятая, точка с запятой, слеш, пробелы
        - подсчёт совпадений по подстроке в обе стороны
        - минимум 2 совпадения
        Возвращает список словарей с ключами:
        code, direction_name, subjects, trend, predicted_2025, budget_places, quotas
        """
        df = self.get_stats_for_form(form)
        if df is None or df.empty:
            return []

        def norm(s: str) -> str:
            return str(s).strip().lower()

        def normalize_subject_name(s: str) -> str:
            text = norm(s)
            # Приводим варианты к базовым формам с расширенными синонимами
            # ВАЖНО: "Профильная математика" = "Математика"
            if any(x in text for x in ['матем', 'мат', 'профильн', 'профильная математика']):
                return 'математика'
            if any(x in text for x in ['русск', 'рус яз', 'рус']):
                return 'русский язык'
            if any(x in text for x in ['информ', 'инф', 'ит']):
                return 'информатика'
            if any(x in text for x in ['обществ', 'общ', 'общество']):
                return 'обществознание'
            if any(x in text for x in ['истор', 'ист']):
                return 'история'
            if any(x in text for x in ['иностр', 'англий', 'англ', 'ин яз']):
                return 'иностранный язык'
            if any(x in text for x in ['физик', 'физ']):
                return 'физика'
            if any(x in text for x in ['географ', 'гео']):
                return 'география'
            if any(x in text for x in ['биолог', 'био']):
                return 'биология'
            if any(x in text for x in ['хими', 'хим']):
                return 'химия'
            return text

        # ИСПРАВЛЕНИЕ: нормализуем каждый предмет отдельно
        normalized_user_subjects = []
        for s in user_subjects:
            if s:  # Проверяем, что предмет не пустой
                normalized_user_subjects.append(normalize_subject_name(s))

        # Определяем, есть ли у пользователя математика
        user_has_math = 'математика' in normalized_user_subjects

        results: List[Dict] = []
        for _, row in df.iterrows():
            direction_raw = str(row.get('Направление', '')).strip()
            if not direction_raw:
                continue
            code = direction_raw.split(' ')[0]
            # Колонка 18: строка вида
            # "Предмет1, Предмет2 / Предмет2, Предмет3" (варианты через '/').
            # Игнорируем "Русский язык" как всегда присутствующий.
            subjects_text = str(row.get('Предметы', '')).strip()
            if not subjects_text:
                continue

            # Разбиваем на альтернативные наборы
            alternatives_raw = [alt.strip() for alt in subjects_text.split('/')]
            alternatives: List[List[str]] = []
            for alt in alternatives_raw:
                parts = [normalize_subject_name(p) for p in re.split(r'[;,]', alt) if p.strip()]
                parts = [p for p in parts if p and p != 'русский язык']  # Русский не учитываем в совпадениях
                alternatives.append(parts)

            # Проверяем, требует ли направление математику
            direction_requires_math = any('математика' in alt for alt in alternatives)
            
            # Если направление требует математику, а у пользователя её нет - пропускаем
            if direction_requires_math and not user_has_math:
                continue

            # Совпадение: пользователь должен покрыть любой из альтернативных наборов
            def covers(alternative: List[str]) -> bool:
                if not alternative:
                    return False
                
                # Для гуманитарных направлений (без математики) требуем полное покрытие
                if not direction_requires_math:
                    overlap = sum(1 for subj in alternative if subj in normalized_user_subjects)
                    return overlap >= len(alternative)  # Все предметы должны совпадать
                
                # Для технических направлений (с математикой) требуем минимум 2 предмета
                overlap = sum(1 for subj in alternative if subj in normalized_user_subjects)
                return overlap >= min(2, len(alternative))

            if not any(covers(alt) for alt in alternatives):
                continue

            # Аналитика и прогноз
            analysis = self.get_competitive_analysis_from_row(code, row)
            if not analysis:
                # Базовый минимум, если вдруг не удалось собрать аналитику
                analysis = {
                    'direction_name': direction_raw,
                    'code': code,
                    'budget_places': int(row.get('Кол-во бюджетных мест', 0)) if 'Кол-во бюджетных мест' in row else int(row.get('Кол-во договорных мест', 0) or 0),
                    'quotas': {'target': None, 'special': None, 'separate': None},
                    'trend': '➡️ Стабильный',
                    'predicted_2025': int(row.get('Год 2025', 0) or 0),
                    'subjects': str(row.get('Предметы', '')),
                }

            results.append(analysis)

        # Сортируем по наличию математики и количеству совпадений
        def sort_key(item: Dict) -> tuple:
            subj_text = norm(item.get('subjects', ''))
            matches_cnt = sum(1 for s in normalized_user_subjects if s in subj_text)
            return (matches_cnt, item.get('predicted_2025') or 0)

        results.sort(key=sort_key, reverse=True)
        return results

    def get_competitive_analysis_from_row(self, direction_code: str, row: pd.Series) -> Dict:
        """Формирует competitive analysis по строке CSV без доступа к Excel."""
        direction_name = str(row.get('Направление', '')).strip()
        # Годы
        years_cols = ['Год 2019', 'Год 2020', 'Год 2021', 'Год 2022', 'Год 2023', 'Год 2024']
        years_data: Dict[str, int] = {}
        scores: List[int] = []
        for col in years_cols:
            if col in row and pd.notna(row[col]) and str(row[col]) not in ('-', '0'):
                try:
                    val = int(float(row[col]))
                    years_data[col] = val
                    scores.append(val)
                except Exception:
                    pass
        # Тренд
        trend_label = '➡️ Стабильный'
        if len(scores) >= 3:
            recent = np.mean(np.diff(scores[-3:]))
            if recent > 2:
                trend_label = '📈 Растущий'
            elif recent < -2:
                trend_label = '📉 Снижающийся'

        # Прогноз
        predicted = None
        if 'Год 2025' in row and pd.notna(row['Год 2025']) and str(row['Год 2025']) not in ('-', '0'):
            try:
                predicted = int(float(row['Год 2025']))
            except Exception:
                predicted = None

        # ИСПРАВЛЕНИЕ: Ищем количество мест - сначала по названию, потом по индексу
        places_count = 0
        if 'Кол-во бюджетных мест' in row:
            places_count = int(float(row.get('Кол-во бюджетных мест', 0)))
        elif 'Кол-во договорных мест' in row:
            places_count = int(float(row.get('Кол-во договорных мест', 0) or 0))
        elif 'Unnamed: 8' in row.index and pd.notna(row.get('Unnamed: 8')):
            # Fallback на колонку Unnamed: 8
            try:
                places_count = int(float(row.get('Unnamed: 8', 0)))
            except (ValueError, TypeError):
                places_count = 0
        elif len(row.index) > 8:
            # Fallback на 8-ю колонку по индексу
            col_at_8 = row.index[8]
            if 'Unnamed' in str(col_at_8) and pd.notna(row.get(col_at_8)):
                try:
                    places_count = int(float(row.get(col_at_8, 0)))
                except (ValueError, TypeError):
                    places_count = 0

        return {
            'direction_name': direction_name,
            'code': direction_code,
            'budget_places': places_count,
            'quotas': {
                'target': None,
                'special': None,
                'separate': None,
            },
            'trend': trend_label,
            'predicted_2025': predicted,
            'subjects': str(row.get('Предметы', '')),
        }


# Глобальный экземпляр предиктора
_predictor_instance = None

def get_predictor() -> StatsPredictor:
    """Возвращает глобальный экземпляр предиктора."""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = StatsPredictor()
    return _predictor_instance

