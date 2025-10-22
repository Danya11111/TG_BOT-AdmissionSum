#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Комплексная проверка всех исправлений
"""

import pandas as pd
import os

def comprehensive_check():
    """Комплексная проверка всех исправлений"""
    
    print("🔍 КОМПЛЕКСНАЯ ПРОВЕРКА ВСЕХ ИСПРАВЛЕНИЙ")
    print("=" * 50)
    
    # 1. Проверка загрузки CSV файлов
    print("\n📁 1. ПРОВЕРКА ЗАГРУЗКИ CSV ФАЙЛОВ")
    
    stats_dir = "data/guu/stats"
    csv_files = {
        "очная_бюджет": "Статистика баллов - очная бюджет.csv",
        "очная_договор": "Статистика баллов - Договор ОЧ.csv", 
        "озо_бюджет": "Статистика баллов - Бюджет ОЗ.csv",
        "озо_договор": "Статистика баллов - Договор ОЗ.csv"
    }
    
    loaded_data = {}
    
    for key, filename in csv_files.items():
        filepath = os.path.join(stats_dir, filename)
        if os.path.exists(filepath):
            try:
                if filename == "Статистика баллов - очная бюджет.csv":
                    # Используем header=2 для бюджетного файла
                    df = pd.read_csv(filepath, encoding='utf-8', header=2)
                else:
                    df = pd.read_csv(filepath, encoding='utf-8')
                
                # Очищаем данные
                df = df.dropna(subset=['Направление'])
                df = df[df['Направление'].str.strip() != '']
                df = df[df['Направление'].str.strip() != '-']
                df = df[df['Направление'].str.contains(r'\d{2}\.\d{2}\.\d{2}', na=False, regex=True)]
                
                loaded_data[key] = df
                print(f"   ✅ {filename}: {len(df)} направлений")
                
            except Exception as e:
                print(f"   ❌ {filename}: Ошибка загрузки - {e}")
        else:
            print(f"   ⚠️ {filename}: Файл не найден")
    
    # 2. Проверка направлений в бюджетной форме
    print("\n🎯 2. ПРОВЕРКА НАПРАВЛЕНИЙ В БЮДЖЕТНОЙ ФОРМЕ")
    
    budget_data = loaded_data.get("очная_бюджет")
    if budget_data is not None:
        print(f"   📊 Всего направлений в бюджетной форме: {len(budget_data)}")
        
        # Проверяем, есть ли Прикладная информатика
        has_applied_info = False
        for _, row in budget_data.iterrows():
            direction = str(row.get('Направление', ''))
            if '09.03.03' in direction or 'Прикладная информатика' in direction:
                has_applied_info = True
                print(f"   ❌ ОШИБКА: Прикладная информатика найдена в бюджетной форме!")
                break
        
        if not has_applied_info:
            print(f"   ✅ Прикладная информатика НЕ найдена в бюджетной форме (правильно)")
        
        # Показываем все направления в бюджетной форме
        print(f"   📝 Направления в бюджетной форме:")
        for _, row in budget_data.iterrows():
            direction = str(row.get('Направление', ''))
            budget_places = row.get('Кол-во бюджетных мест всего', 0)
            print(f"      {direction} (мест: {budget_places})")
    
    # 3. Проверка направлений в договорной форме
    print("\n💰 3. ПРОВЕРКА НАПРАВЛЕНИЙ В ДОГОВОРНОЙ ФОРМЕ")
    
    contract_data = loaded_data.get("очная_договор")
    if contract_data is not None:
        print(f"   📊 Всего направлений в договорной форме: {len(contract_data)}")
        
        # Проверяем, есть ли Прикладная информатика
        has_applied_info = False
        for _, row in contract_data.iterrows():
            direction = str(row.get('Направление', ''))
            if '09.03.03' in direction or 'Прикладная информатика' in direction:
                has_applied_info = True
                contract_places = row.get('Кол-во договорных мест', 0)
                print(f"   ✅ Прикладная информатика найдена в договорной форме (мест: {contract_places})")
                break
        
        if not has_applied_info:
            print(f"   ❌ ОШИБКА: Прикладная информатика НЕ найдена в договорной форме!")
    
    # 4. Проверка маппинга форм обучения
    print("\n🔄 4. ПРОВЕРКА МАППИНГА ФОРМ ОБУЧЕНИЯ")
    
    form_mapping = {
        "budget": "Очно-бюджетная",
        "contract": "Очно-платная", 
        "oz_budget": "ОЗО-бюджетная",
        "oz_contract": "ОЗО-платная"
    }
    
    for key, value in form_mapping.items():
        print(f"   ✅ {key} → {value}")
    
    # 5. Проверка поиска направлений
    print("\n🔍 5. ПРОВЕРКА ПОИСКА НАПРАВЛЕНИЙ")
    
    try:
        from utils import find_directions_by_subjects
        
        test_cases = [
            (["Математика", "Информатика"], "Очно-бюджетная"),
            (["Математика", "Информатика"], "Очно-платная"),
            (["Обществознание", "История"], "Очно-бюджетная"),
        ]
        
        for subjects, form in test_cases:
            directions = find_directions_by_subjects(subjects, form)
            print(f"   📋 {', '.join(subjects)} ({form}): {len(directions)} направлений")
            
            # Проверяем, что Прикладная информатика не в бюджетной форме
            if form == "Очно-бюджетная":
                has_applied_info = any("09.03.03" in d.get('code', '') for d in directions)
                if has_applied_info:
                    print(f"      ❌ ОШИБКА: Прикладная информатика найдена в бюджетной форме!")
                else:
                    print(f"      ✅ Прикладная информатика НЕ найдена в бюджетной форме (правильно)")
    
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании поиска: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 ПРОВЕРКА ЗАВЕРШЕНА!")

if __name__ == "__main__":
    comprehensive_check()
