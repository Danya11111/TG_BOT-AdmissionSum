import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import re
import os


class StatsAnalyzer:
    """Анализатор статистики проходных баллов ГУУ"""
    
    def __init__(self, stats_path: str = "data/guu/stats/Stats.xlsx"):
        self.stats_path = stats_path
        self.df = None
        self.directions_data = {}
        self.load_stats()
    
    def load_stats(self):
        """Загружает и обрабатывает статистику"""
        try:
            # Устанавливаем правильную кодировку для чтения Excel
            self.df = pd.read_excel(self.stats_path, engine='openpyxl')
            self._process_data()
        except Exception as e:
            print(f"Ошибка загрузки статистики: {e}")
            self.df = None
    
    def _process_data(self):
        """Обрабатывает загруженные данные"""
        if self.df is None:
            return
        
        # Нормализуем названия колонок для работы с кириллицей
        self._normalize_columns()
        
        # Находим строки с данными направлений (пропускаем заголовки)
        direction_rows = []
        code_pattern = re.compile(r'^\d{2}\.\d{2}\.\d{2}')
        for i, row in self.df.iterrows():
            if pd.notna(row.iloc[0]) and code_pattern.match(str(row.iloc[0])):
                direction_rows.append(i)
        
        # Обрабатываем каждое направление
        for row_idx in direction_rows:
            row = self.df.iloc[row_idx]
            direction_code = str(row.iloc[0]).split(' ')[0]  # Код направления
            
            # Извлекаем данные по годам
            years_data = {}
            year_cols = ['Год 2019', 'Год 2020', 'Год 2021', 'Год 2022', 'Год 2023', 'Год 2024', 'Год 2025']
            
            for year_col in year_cols:
                if year_col in self.df.columns:
                    value = row[year_col]
                    if pd.notna(value) and str(value) != '-' and str(value) != '0':
                        try:
                            years_data[year_col] = int(value)
                        except:
                            pass
            
            # Извлекаем дополнительные данные
            budget_places = None
            target_quota = None
            special_quota = None
            separate_quota = None
            
            if 'Количество бюджетных мест' in self.df.columns:
                budget_val = row['Количество бюджетных мест']
                if pd.notna(budget_val):
                    budget_places = int(budget_val)
            
            # Извлекаем квоты из соответствующих колонок
            quota_cols = ['Unnamed: 8', 'Unnamed: 9', 'Unnamed: 10', 'Unnamed: 11', 'Unnamed: 12', 'Unnamed: 13']
            quotas = []
            for col in quota_cols:
                if col in self.df.columns:
                    val = row[col]
                    if pd.notna(val) and str(val).isdigit():
                        quotas.append(int(val))
            
            if len(quotas) >= 3:
                target_quota, special_quota, separate_quota = quotas[0], quotas[1], quotas[2]
            
            # Определяем предметы: сначала берём из колонки 'Предметы', иначе — из последней ячейки строки
            subjects_value = None
            if 'Предметы' in self.df.columns:
                subjects_value = row.get('Предметы')
            if pd.isna(subjects_value) or subjects_value is None or str(subjects_value).strip() == '':
                subjects_value = row.iloc[-1]

            # Сохраняем данные направления
            self.directions_data[direction_code] = {
                'code': direction_code,
                'name': str(row.iloc[0]),
                'years_data': years_data,
                'budget_places': budget_places,
                'target_quota': target_quota,
                'special_quota': special_quota,
                'separate_quota': separate_quota,
                'subjects': str(subjects_value) if pd.notna(subjects_value) else ""
            }
    
    def get_direction_stats(self, direction_code: str) -> Optional[Dict]:
        """Получает статистику по конкретному направлению"""
        return self.directions_data.get(direction_code)
    
    def get_all_directions(self) -> List[Dict]:
        """Возвращает список всех направлений"""
        return list(self.directions_data.values())
    
    def predict_score_2025(self, direction_code: str) -> Optional[int]:
        """Прогнозирует проходной балл на 2025 год с улучшенным алгоритмом"""
        direction = self.get_direction_stats(direction_code)
        if not direction:
            return None
        
        years_data = direction['years_data']
        if not years_data:
            return None
        
        # Если есть прогноз на 2025, используем его
        if 'Год 2025' in years_data:
            return years_data['Год 2025']
        
        # Собираем баллы по годам
        scores = []
        years = []
        for year_col in ['Год 2019', 'Год 2020', 'Год 2021', 'Год 2022', 'Год 2023', 'Год 2024']:
            if year_col in years_data:
                scores.append(years_data[year_col])
                years.append(int(year_col.split()[1]))
        
        if len(scores) < 2:
            return None
        
        # Улучшенное прогнозирование с учетом нескольких факторов
        if len(scores) >= 4:
            # Используем взвешенное среднее тренда с большим весом для последних лет
            recent_3_trend = np.mean(np.diff(scores[-3:]))  # Тренд последних 3 лет
            overall_trend = np.mean(np.diff(scores))  # Общий тренд
            
            # Взвешенный тренд (70% последние годы, 30% общий)
            weighted_trend = 0.7 * recent_3_trend + 0.3 * overall_trend
            
            # Прогноз = последний балл + взвешенный тренд
            predicted = scores[-1] + weighted_trend
            
            # Проверяем на аномалии и корректируем
            mean_score = np.mean(scores)
            std_score = np.std(scores)
            
            # Если прогноз сильно отклоняется от среднего, корректируем
            if abs(predicted - mean_score) > 2 * std_score:
                # Используем комбинацию тренда и среднего
                predicted = 0.6 * predicted + 0.4 * mean_score
        
        elif len(scores) == 3:
            # Для 3 значений используем линейную регрессию
            recent_trend = np.mean(np.diff(scores))
            predicted = scores[-1] + recent_trend
        
        else:
            # Для 2 значений используем простой тренд
            trend = scores[1] - scores[0]
            predicted = scores[-1] + trend * 0.5  # Сглаживаем тренд
        
        # Ограничиваем прогноз разумными пределами (120-310)
        predicted = max(120, min(310, int(round(predicted))))
        
        return predicted
    
    def calculate_admission_probability(self, direction_code: str, user_score: int) -> Tuple[str, float]:
        """Рассчитывает вероятность поступления"""
        direction = self.get_direction_stats(direction_code)
        if not direction:
            return "Неизвестно", 0.0
        
        predicted_score = self.predict_score_2025(direction_code)
        if not predicted_score:
            return "Неизвестно", 0.0
        
        # Рассчитываем вероятность на основе разности баллов
        score_diff = user_score - predicted_score
        
        if score_diff >= 15:
            return "🟢 Очень высокие", 0.95
        elif score_diff >= 10:
            return "🟢 Высокие", 0.85
        elif score_diff >= 5:
            return "🟡 Средние", 0.65
        elif score_diff >= 0:
            return "🟡 Низкие", 0.35
        elif score_diff >= -5:
            return "🔴 Очень низкие", 0.15
        else:
            return "🔴 Практически нет", 0.05
    
    def get_competitive_analysis(self, direction_code: str) -> Dict:
        """Получает конкурентный анализ направления"""
        direction = self.get_direction_stats(direction_code)
        if not direction:
            return {}
        
        years_data = direction['years_data']
        analysis = {
            'direction_name': direction['name'],
            'code': direction_code,
            'budget_places': direction['budget_places'],
            'quotas': {
                'target': direction['target_quota'],
                'special': direction['special_quota'],
                'separate': direction['separate_quota']
            },
            'trend': self._analyze_trend(years_data),
            'predicted_2025': self.predict_score_2025(direction_code),
            'subjects': direction['subjects']
        }
        
        return analysis
    
    def _analyze_trend(self, years_data: Dict) -> str:
        """Анализирует тренд изменения проходных баллов"""
        if len(years_data) < 2:
            return "Недостаточно данных"
        
        scores = []
        for year_col in ['Год 2019', 'Год 2020', 'Год 2021', 'Год 2022', 'Год 2023', 'Год 2024']:
            if year_col in years_data:
                scores.append(years_data[year_col])
        
        if len(scores) < 2:
            return "Недостаточно данных"
        
        # Анализируем тренд
        if len(scores) >= 3:
            recent_trend = np.mean(np.diff(scores[-3:]))
            if recent_trend > 2:
                return "📈 Растущий"
            elif recent_trend < -2:
                return "📉 Снижающийся"
            else:
                return "➡️ Стабильный"
        else:
            return "➡️ Стабильный"
    
    def find_similar_directions(self, user_subjects: List[str], form: str = "бюджет") -> List[Dict]:
        """Находит похожие направления по предметам"""
        similar = []
        
        # Приводим пользовательские предметы к нормализованному виду
        def norm(s: str) -> str:
            return s.strip().lower()
        normalized_user_subjects = [norm(s) for s in user_subjects]

        for direction_code, direction_data in self.directions_data.items():
            subjects_text = (direction_data.get('subjects') or '').lower()
            # Разбиваем строку предметов на токены
            tokens = re.split(r'[;,\s/]+', subjects_text)
            tokens = [t for t in tokens if t]

            # Считаем совпадения по подстрокам в обе стороны
            def is_match(user_subj: str) -> bool:
                return any(user_subj in t or t in user_subj for t in tokens)

            matches = sum(1 for s in normalized_user_subjects if is_match(s))

            if matches >= 2:  # Минимум 2 совпадения
                analysis = self.get_competitive_analysis(direction_code)
                similar.append(analysis)
        
        # Сортируем по количеству совпадений
        similar.sort(key=lambda x: len([s for s in user_subjects if s.lower() in x['subjects'].lower()]), reverse=True)
        
        return similar
    
    def _normalize_columns(self):
        """Нормализует названия колонок для работы с кириллицей"""
        if self.df is None:
            return
        
        # Создаем маппинг для нормализации колонок
        column_mapping = {}
        for col in self.df.columns:
            col_str = str(col)
            # Ищем колонки с годами
            if '2019' in col_str:
                column_mapping[col] = 'Год 2019'
            elif '2020' in col_str:
                column_mapping[col] = 'Год 2020'
            elif '2021' in col_str:
                column_mapping[col] = 'Год 2021'
            elif '2022' in col_str:
                column_mapping[col] = 'Год 2022'
            elif '2023' in col_str:
                column_mapping[col] = 'Год 2023'
            elif '2024' in col_str:
                column_mapping[col] = 'Год 2024'
            elif '2025' in col_str:
                column_mapping[col] = 'Год 2025'
            elif 'бюджет' in col_str.lower() or 'место' in col_str.lower():
                column_mapping[col] = 'Количество бюджетных мест'
            elif 'предмет' in col_str.lower():
                column_mapping[col] = 'Предметы'
        
        # Переименовываем колонки
        self.df = self.df.rename(columns=column_mapping)


# Глобальный экземпляр анализатора
stats_analyzer = StatsAnalyzer()
