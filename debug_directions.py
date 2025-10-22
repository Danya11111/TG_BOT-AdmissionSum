#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для отладки поиска направлений
"""

from stats_predictor import get_predictor

def test_direction_search():
    """Тестирует поиск направлений с разными комбинациями предметов"""
    
    predictor = get_predictor()
    
    # Тестовые комбинации
    test_cases = [
        (["Математика", "Информатика"], "Очно-бюджетная"),
        (["Обществознание", "История"], "Очно-бюджетная"),
        (["Обществознание", "Биология"], "Очно-бюджетная"),
        (["Математика", "Обществознание"], "Очно-бюджетная"),
    ]
    
    print("🔍 Тестирование поиска направлений...")
    
    for subjects, form in test_cases:
        print(f"\n📋 Тест: {', '.join(subjects)} ({form})")
        
        # Получаем данные для формы
        df = predictor.get_stats_for_form(form)
        if df is None:
            print("   ❌ Данные не найдены")
            continue
            
        print(f"   📊 Всего направлений в таблице: {len(df)}")
        
        # Показываем все направления с их предметами
        print("   📝 Направления в таблице:")
        for idx, row in df.iterrows():
            direction = str(row.get('Направление', '')).strip()
            subjects_text = str(row.get('Предметы', '')).strip()
            if direction and subjects_text:
                print(f"      {direction}: {subjects_text}")
        
        # Тестируем поиск
        results = predictor.find_directions_by_subjects(subjects, form)
        print(f"   🎯 Найдено направлений: {len(results)}")
        
        for result in results:
            print(f"      ✅ {result.get('code', '')} - {result.get('direction_name', '')}")

if __name__ == "__main__":
    test_direction_search()
