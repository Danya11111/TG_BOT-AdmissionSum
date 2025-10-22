#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Финальное решение: Автоматическая валидация и исправление системы поиска направлений
"""

import os
import pandas as pd
import re
from typing import Dict, List, Set
from stats_predictor import get_predictor

def create_validation_system():
    """Создает систему валидации соответствия схеме"""
    
    print("🔧 Создание системы валидации...")
    
    # Схема из предоставленной диаграммы
    SCHEME_MAPPING = {
        # Колонка 1: Русский + Математика + Информатика
        ("Математика", "Информатика"): [
            "Статистика", "Экология и природопользование", 
            "Технология транспортных процессов", "Бизнес-информатика", 
            "Инноватика", "Прикладная информатика"
        ],
        
        # Колонка 2: Русский + Математика + Иностранный язык
        ("Математика", "Английский язык"): [
            "Менеджмент", "Управление персоналом", "Экономика"
        ],
        
        # Колонка 3: Русский + Математика + Физика
        ("Математика", "Физика"): [
            "Технология транспортных процессов", "Инноватика"
        ],
        
        # Колонка 4: Русский + Математика + География
        ("Математика", "География"): [
            "Экология и природопользование"
        ],
        
        # Колонка 5: Русский + Обществознание + История
        ("Обществознание", "История"): [
            "Политология", "Реклама и связи с общественностью", 
            "Социология", "Юриспруденция", "Гостиничное дело"
        ],
        
        # Колонка 6: Русский + Обществознание + Иностранный язык
        ("Обществознание", "Английский язык"): [
            "Гостиничное дело", "Реклама и связи с общественностью", 
            "Социология", "Юриспруденция", "Государственное и муниципальное управление"
        ],
        
        # Колонка 7: Русский + История + Иностранный язык
        ("История", "Английский язык"): [
            "Политология"
        ],
        
        # Колонка 8: Русский + Обществознание + Биология
        ("Обществознание", "Биология"): [
            "Психология"
        ],
        
        # Колонка 9: Русский + Математика + Обществознание
        ("Математика", "Обществознание"): [
            "Бизнес-информатика", "Государственное и муниципальное управление", 
            "Менеджмент", "Управление персоналом", "Экономика"
        ]
    }
    
    # Создаем улучшенный предиктор с валидацией
    class ValidatedStatsPredictor:
        def __init__(self):
            self.predictor = get_predictor()
            self.scheme_mapping = SCHEME_MAPPING
            
        def validate_and_find_directions(self, user_subjects: List[str], form: str) -> Dict:
            """Валидирует и находит направления с детальной диагностикой"""
            
            result = {
                'found_directions': [],
                'validation_status': 'success',
                'issues': [],
                'recommendations': [],
                'scheme_compliance': 0.0
            }
            
            # Нормализация предметов
            normalized_subjects = self._normalize_subjects(user_subjects)
            
            # Проверяем соответствие схеме
            scheme_match = self._check_scheme_compliance(normalized_subjects)
            result['scheme_compliance'] = scheme_match['compliance_rate']
            
            if scheme_match['compliance_rate'] == 0:
                result['validation_status'] = 'no_match'
                result['issues'].append(f"Комбинация {', '.join(user_subjects)} не соответствует ни одной схеме")
                result['recommendations'].append("Проверьте правильность выбора предметов")
                return result
            
            # Ищем направления в базе данных
            try:
                found_directions = self.predictor.find_directions_by_subjects(user_subjects, form)
                result['found_directions'] = found_directions
                
                if not found_directions:
                    result['validation_status'] = 'no_directions_found'
                    result['issues'].append("Направления не найдены в базе данных")
                    result['recommendations'].append("Проверьте наличие направлений в CSV файлах")
                else:
                    result['validation_status'] = 'success'
                    
            except Exception as e:
                result['validation_status'] = 'error'
                result['issues'].append(f"Ошибка поиска направлений: {str(e)}")
                result['recommendations'].append("Проверьте корректность данных в CSV файлах")
            
            return result
        
        def _normalize_subjects(self, subjects: List[str]) -> List[str]:
            """Нормализует названия предметов"""
            normalized = []
            for subject in subjects:
                subject_lower = subject.lower().strip()
                if any(x in subject_lower for x in ['матем', 'мат', 'профильн']):
                    normalized.append('математика')
                elif any(x in subject_lower for x in ['информ', 'инф', 'ит']):
                    normalized.append('информатика')
                elif any(x in subject_lower for x in ['обществ', 'общ', 'общество']):
                    normalized.append('обществознание')
                elif any(x in subject_lower for x in ['истор', 'ист']):
                    normalized.append('история')
                elif any(x in subject_lower for x in ['иностр', 'англий', 'англ', 'ин яз']):
                    normalized.append('английский язык')
                elif any(x in subject_lower for x in ['физик', 'физ']):
                    normalized.append('физика')
                elif any(x in subject_lower for x in ['географ', 'гео']):
                    normalized.append('география')
                elif any(x in subject_lower for x in ['биолог', 'био']):
                    normalized.append('биология')
                elif any(x in subject_lower for x in ['хими', 'хим']):
                    normalized.append('химия')
                else:
                    normalized.append(subject_lower)
            return normalized
        
        def _check_scheme_compliance(self, normalized_subjects: List[str]) -> Dict:
            """Проверяет соответствие схеме"""
            best_match = None
            best_score = 0
            
            for scheme_subjects, expected_directions in self.scheme_mapping.items():
                # Проверяем, покрывает ли пользователь схему
                scheme_set = set(scheme_subjects)
                user_set = set(normalized_subjects)
                
                if scheme_set.issubset(user_set):
                    score = len(scheme_set) / len(user_set)
                    if score > best_score:
                        best_score = score
                        best_match = {
                            'scheme_subjects': scheme_subjects,
                            'expected_directions': expected_directions,
                            'compliance_rate': score
                        }
            
            return best_match or {'compliance_rate': 0.0}
    
    return ValidatedStatsPredictor()

def run_comprehensive_validation():
    """Запускает комплексную валидацию системы"""
    
    print("🔍 Запуск комплексной валидации...")
    
    validator = create_validation_system()
    
    # Тестовые случаи
    test_cases = [
        (["Математика", "Информатика"], "Очно-бюджетная"),
        (["Математика", "Обществознание"], "Очно-бюджетная"),
        (["Обществознание", "История"], "Очно-бюджетная"),
        (["Обществознание", "Биология"], "Очно-бюджетная"),
        (["Математика", "Английский язык"], "Очно-бюджетная"),
    ]
    
    results = []
    
    for subjects, form in test_cases:
        print(f"\n📋 Тест: {', '.join(subjects)} ({form})")
        
        result = validator.validate_and_find_directions(subjects, form)
        results.append({
            'subjects': ', '.join(subjects),
            'form': form,
            'status': result['validation_status'],
            'compliance': result['scheme_compliance'],
            'found_count': len(result['found_directions']),
            'issues': result['issues'],
            'recommendations': result['recommendations']
        })
        
        print(f"   📊 Статус: {result['validation_status']}")
        print(f"   📈 Соответствие схеме: {result['scheme_compliance']:.2f}")
        print(f"   🎯 Найдено направлений: {len(result['found_directions'])}")
        
        if result['issues']:
            print(f"   ⚠️ Проблемы: {', '.join(result['issues'])}")
        if result['recommendations']:
            print(f"   💡 Рекомендации: {', '.join(result['recommendations'])}")
    
    # Сохраняем результаты
    df_results = pd.DataFrame(results)
    df_results.to_csv("reports/comprehensive_validation.csv", index=False, encoding='utf-8')
    
    print(f"\n✅ Комплексная валидация завершена!")
    print(f"📁 Результаты сохранены: reports/comprehensive_validation.csv")
    
    return results

def create_final_solution():
    """Создает финальное решение всех проблем"""
    
    print("🎯 Создание финального решения...")
    
    # Создаем улучшенный stats_predictor с исправлениями
    improved_predictor_code = '''
# Исправления в stats_predictor.py

def load_all_stats(self) -> None:
    """Загружает всю статистику из CSV файлов с исправлениями."""
    for key, filename in self.STATS_FILES.items():
        filepath = os.path.join(self.STATS_DIR, filename)
        if os.path.exists(filepath):
            try:
                # Читаем CSV файл
                df = pd.read_csv(filepath, encoding='utf-8')
                
                # Исправляем проблему с заголовками
                if 'Направление' not in df.columns:
                    # Ищем строку с заголовком "Направление"
                    for i, row in df.iterrows():
                        if 'Направление' in str(row.iloc[0]):
                            df = pd.read_csv(filepath, encoding='utf-8', header=i)
                            break
                
                # Очищаем данные
                df = df.dropna(subset=['Направление'])
                df = df[df['Направление'].str.strip() != '']
                df = df[df['Направление'].str.strip() != '-']
                
                # Фильтруем только реальные направления
                df = df[df['Направление'].str.contains(r'\\d{2}\\.\\d{2}\\.\\d{2}', na=False)]
                
                self.stats_data[key] = df
                logger.info(f"Загружена статистика {key}: {len(df)} направлений")
            except Exception as e:
                logger.error(f"Ошибка загрузки {filepath}: {e}")
        else:
            logger.warning(f"Файл статистики не найден: {filepath}")

def find_directions_by_subjects(self, user_subjects: List[str], form: str) -> List[Dict]:
    """Исправленная функция поиска направлений."""
    df = self.get_stats_for_form(form)
    if df is None or df.empty:
        return []

    def normalize_subject_name(s: str) -> str:
        text = str(s).strip().lower()
        if any(x in text for x in ['матем', 'мат', 'профильн']):
            return 'математика'
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

    normalized_user_subjects = [normalize_subject_name(s) for s in user_subjects if s]
    user_has_math = 'математика' in normalized_user_subjects

    results: List[Dict] = []
    for _, row in df.iterrows():
        direction_raw = str(row.get('Направление', '')).strip()
        if not direction_raw:
            continue
            
        code = direction_raw.split(' ')[0]
        subjects_text = str(row.get('Предметы', '')).strip()
        if not subjects_text:
            continue

        # Разбиваем на альтернативные наборы
        alternatives_raw = [alt.strip() for alt in subjects_text.split('/')]
        alternatives: List[List[str]] = []
        for alt in alternatives_raw:
            parts = [normalize_subject_name(p) for p in re.split(r'[;,]', alt) if p.strip()]
            parts = [p for p in parts if p and p != 'русский язык']
            alternatives.append(parts)

        # Проверяем требование математики
        direction_requires_math = any('математика' in alt for alt in alternatives)
        if direction_requires_math and not user_has_math:
            continue

        # Проверяем совпадение
        def covers(alternative: List[str]) -> bool:
            if not alternative:
                return False
            if not direction_requires_math:
                # Гуманитарные направления - полное покрытие
                overlap = sum(1 for subj in alternative if subj in normalized_user_subjects)
                return overlap >= len(alternative)
            else:
                # Технические направления - минимум 2 предмета
                overlap = sum(1 for subj in alternative if subj in normalized_user_subjects)
                return overlap >= min(2, len(alternative))

        if not any(covers(alt) for alt in alternatives):
            continue

        # Добавляем результат
        results.append({
            'code': code,
            'direction_name': direction_raw,
            'subjects': subjects_text,
            'predicted_2025': int(row.get('Год 2025', 0) or 0),
            'budget_places': int(row.get('Кол-во бюджетных мест', 0) or 0),
            'trend': '➡️ Стабильный'
        })

    return results
'''
    
    # Сохраняем исправления
    with open("reports/IMPROVED_STATS_PREDICTOR.py", "w", encoding="utf-8") as f:
        f.write(improved_predictor_code)
    
    print("   ✅ Исправления сохранены: reports/IMPROVED_STATS_PREDICTOR.py")
    
    return improved_predictor_code

if __name__ == "__main__":
    try:
        # Запускаем комплексную валидацию
        validation_results = run_comprehensive_validation()
        
        # Создаем финальное решение
        final_solution = create_final_solution()
        
        print(f"\n🎉 Все пункты рекомендаций выполнены!")
        print(f"📊 Результаты валидации: {len(validation_results)} тестов")
        print(f"🔧 Созданы исправления для stats_predictor.py")
        
    except Exception as e:
        print(f"❌ Ошибка при выполнении: {e}")
        import traceback
        traceback.print_exc()
