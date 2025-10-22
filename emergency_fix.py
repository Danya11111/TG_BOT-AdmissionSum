#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ЭКСТРЕННОЕ ИСПРАВЛЕНИЕ: Исправляем загрузку CSV и поиск направлений
"""

import pandas as pd
import os
import re
from typing import List, Dict

def fix_csv_loading():
    """Исправляет загрузку CSV файлов"""
    
    print("🔧 ЭКСТРЕННОЕ ИСПРАВЛЕНИЕ загрузки CSV...")
    
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
                # Читаем файл построчно
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Находим строку с заголовком "Направление"
                header_line = 0
                for i, line in enumerate(lines):
                    if 'Направление' in line and 'Год 2019' in line:
                        header_line = i
                        break
                
                print(f"   📋 Заголовок найден в строке: {header_line}")
                
                # Читаем CSV с правильным заголовком
                df = pd.read_csv(filepath, encoding='utf-8', header=header_line)
                
                # Очищаем данные
                df = df.dropna(subset=['Направление'])
                df = df[df['Направление'].str.strip() != '']
                df = df[df['Направление'].str.strip() != '-']
                
                # Фильтруем только реальные направления (содержат код)
                df = df[df['Направление'].str.contains(r'\d{2}\.\d{2}\.\d{2}', na=False)]
                
                fixed_data[key] = df
                print(f"   ✅ Загружено направлений: {len(df)}")
                
                # Показываем первые несколько направлений
                if len(df) > 0:
                    print(f"   📝 Примеры направлений:")
                    for i, row in df.head(3).iterrows():
                        direction = row['Направление']
                        subjects = row.get('Предметы', 'Нет данных')
                        print(f"      {direction}: {subjects}")
                
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
        else:
            print(f"   ⚠️ Файл не найден: {filepath}")
    
    return fixed_data

def test_direction_search_fixed():
    """Тестирует поиск направлений с исправленными данными"""
    
    print("\n🔍 ТЕСТИРОВАНИЕ исправленного поиска...")
    
    # Получаем исправленные данные
    fixed_data = fix_csv_loading()
    
    if not fixed_data:
        print("❌ Не удалось загрузить данные!")
        return
    
    # Тестовые случаи
    test_cases = [
        (["Математика", "Информатика"], "очная_бюджет"),
        (["Обществознание", "История"], "очная_бюджет"),
        (["Обществознание", "Биология"], "очная_бюджет"),
        (["Математика", "Обществознание"], "очная_бюджет"),
    ]
    
    for subjects, form_key in test_cases:
        print(f"\n📋 Тест: {', '.join(subjects)} ({form_key})")
        
        df = fixed_data.get(form_key)
        if df is None:
            print("   ❌ Данные не найдены")
            continue
        
        print(f"   📊 Всего направлений в таблице: {len(df)}")
        
        # Нормализация предметов
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
        
        normalized_user_subjects = [normalize_subject(s) for s in subjects]
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
            if not subjects_text:
                continue
            
            print(f"   🔍 Проверяем: {direction_raw}")
            print(f"      Предметы: {subjects_text}")
            
            # Разбиваем на альтернативные наборы
            alternatives_raw = [alt.strip() for alt in subjects_text.split('/')]
            alternatives = []
            for alt in alternatives_raw:
                parts = [normalize_subject(p) for p in re.split(r'[;,]', alt) if p.strip()]
                parts = [p for p in parts if p and p != 'русский язык']
                alternatives.append(parts)
            
            print(f"      Альтернативы: {alternatives}")
            
            # Проверяем требование математики
            direction_requires_math = any('математика' in alt for alt in alternatives)
            print(f"      Требует математику: {direction_requires_math}")
            
            if direction_requires_math and not user_has_math:
                print(f"      ❌ Пропускаем - нет математики")
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
                print(f"      ✅ НАЙДЕНО!")
            else:
                print(f"      ❌ Не подходит")
        
        print(f"   🎯 ИТОГО найдено направлений: {len(found_directions)}")
        for direction in found_directions:
            print(f"      ✅ {direction['code']} - {direction['name']}")

if __name__ == "__main__":
    test_direction_search_fixed()
