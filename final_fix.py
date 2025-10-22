#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ОКОНЧАТЕЛЬНОЕ ИСПРАВЛЕНИЕ: Исправляем все проблемы с поиском направлений
"""

import pandas as pd
import os
import re
from typing import List, Dict

def fix_all_issues():
    """Исправляет все проблемы с поиском направлений"""
    
    print("🔧 ОКОНЧАТЕЛЬНОЕ ИСПРАВЛЕНИЕ всех проблем...")
    
    # Путь к файлам
    stats_dir = "data/guu/stats"
    csv_files = {
        "очная_бюджет": "Статистика баллов - очная бюджет.csv",
        "очная_договор": "Статистика баллов - Договор ОЧ.csv", 
        "озо_бюджет": "Статистика баллов - Бюджет ОЗ.csv",
        "озо_договор": "Статистика баллов - Договор ОЗ.csv"
    }
    
    fixed_data = {}
    
    for key, filename in csv_files.items():
        filepath = os.path.join(stats_dir, filename)
        if os.path.exists(filepath):
            print(f"\n📁 Исправляем: {filename}")
            
            try:
                # Читаем CSV файл
                df = pd.read_csv(filepath, encoding='utf-8')
                
                # Очищаем данные более аккуратно
                df = df.dropna(subset=['Направление'])
                df = df[df['Направление'].str.strip() != '']
                df = df[df['Направление'].str.strip() != '-']
                
                # Более мягкий фильтр для направлений
                df = df[df['Направление'].str.contains(r'\d{2}\.\d{2}\.\d{2}', na=False, regex=True)]
                
                # Дополнительная очистка от строк с числами вместо названий
                df = df[~df['Направление'].str.match(r'^\d+$', na=False)]
                
                fixed_data[key] = df
                print(f"   ✅ Загружено направлений: {len(df)}")
                
                # Показываем все направления
                if len(df) > 0:
                    print(f"   📝 Все направления:")
                    for i, row in df.iterrows():
                        direction = row['Направление']
                        subjects = row.get('Предметы', 'Нет данных')
                        print(f"      {direction}: {subjects}")
                
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
        else:
            print(f"   ⚠️ Файл не найден: {filepath}")
    
    return fixed_data

def test_fixed_search():
    """Тестирует исправленный поиск"""
    
    print("\n🔍 ТЕСТИРОВАНИЕ исправленного поиска...")
    
    # Получаем исправленные данные
    fixed_data = fix_all_issues()
    
    if not fixed_data:
        print("❌ Не удалось загрузить данные!")
        return
    
    # Тестируем с файлом, где есть данные
    test_cases = [
        (["Математика", "Информатика"], "очная_договор"),  # Используем файл с данными
        (["Обществознание", "История"], "очная_договор"),
        (["Обществознание", "Биология"], "очная_договор"),
        (["Математика", "Обществознание"], "очная_договор"),
    ]
    
    for subjects, form_key in test_cases:
        print(f"\n📋 Тест: {', '.join(subjects)} ({form_key})")
        
        df = fixed_data.get(form_key)
        if df is None:
            print("   ❌ Данные не найдены")
            continue
        
        print(f"   📊 Всего направлений в таблице: {len(df)}")
        
        # ИСПРАВЛЕННАЯ нормализация предметов
        def normalize_subject(s: str) -> str:
            s_lower = s.lower().strip()
            if any(x in s_lower for x in ['матем', 'мат', 'профильн']):
                return 'математика'
            elif any(x in s_lower for x in ['информ', 'инф', 'ит']):
                return 'информатика'
            elif any(x in s_lower for x in ['обществ', 'общ', 'общество']):
                return 'обществознание'
            elif any(x in s_lower for x in ['истор', 'ист']):
                return 'история'
            elif any(x in s_lower for x in ['иностр', 'англий', 'англ', 'ин яз']):
                return 'иностранный язык'
            elif any(x in s_lower for x in ['физик', 'физ']):
                return 'физика'
            elif any(x in s_lower for x in ['географ', 'гео']):
                return 'география'
            elif any(x in s_lower for x in ['биолог', 'био']):
                return 'биология'
            elif any(x in s_lower for x in ['хими', 'хим']):
                return 'химия'
            return s_lower
        
        # ИСПРАВЛЕНИЕ: нормализуем каждый предмет отдельно
        normalized_user_subjects = []
        for s in subjects:
            normalized_user_subjects.append(normalize_subject(s))
        
        user_has_math = 'математика' in normalized_user_subjects
        
        print(f"   🔍 Нормализованные предметы: {normalized_user_subjects}")
        print(f"   📐 Есть математика: {user_has_math}")
        
        # Поиск направлений
        found_directions = []
        
        for _, row in df.iterrows():
            direction_raw = str(row.get('Направление', '')).strip()
            if not direction_raw:
                continue
                
            code = direction_raw.split(' ')[0]
            subjects_text = str(row.get('Предметы', '')).strip()
            if not subjects_text or subjects_text == 'nan':
                continue
            
            # Разбиваем на альтернативные наборы
            alternatives_raw = [alt.strip() for alt in subjects_text.split('/')]
            alternatives = []
            for alt in alternatives_raw:
                parts = [normalize_subject(p) for p in re.split(r'[;,]', alt) if p.strip()]
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
            
            if any(covers(alt) for alt in alternatives):
                found_directions.append({
                    'code': code,
                    'name': direction_raw,
                    'subjects': subjects_text
                })
        
        print(f"   🎯 ИТОГО найдено направлений: {len(found_directions)}")
        for direction in found_directions:
            print(f"      ✅ {direction['code']} - {direction['name']}")

if __name__ == "__main__":
    test_fixed_search()
