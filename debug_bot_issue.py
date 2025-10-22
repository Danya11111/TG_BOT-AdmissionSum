#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Отладка проблемы с ботом
"""

import logging
from utils import find_directions_by_subjects

# Настройка логирования
logging.basicConfig(level=logging.INFO)

def debug_bot_issue():
    """Отладка проблемы с ботом"""
    
    print("🔍 Отладка проблемы с ботом...")
    
    # Тестируем точно те же параметры, что использует бот
    test_cases = [
        (["Математика", "Информатика"], "Очно-бюджетная"),
        (["Обществознание", "История"], "Очно-бюджетная"),
    ]
    
    for subjects, form in test_cases:
        print(f"\n📋 Тест: {subjects} ({form})")
        
        try:
            # Вызываем функцию точно так же, как в боте
            similar_directions = find_directions_by_subjects(subjects, form)
            print(f"   📊 similar_directions: {len(similar_directions)}")
            
            # Конвертируем в старый формат для совместимости (как в боте)
            directions = []
            for analysis in similar_directions[:10]:  # Ограничиваем до 10 направлений
                direction = {
                    'code': analysis['code'],
                    'name': analysis['direction_name'],
                    'subjects': analysis.get('subjects') or '',
                    'passing_score_2022': 0,
                    'passing_score_2023': 0,
                    'passing_score_2024': 0,
                    'predicted_score_2025': (analysis.get('predicted_2025') or 0),
                    'budget_places': (analysis.get('budget_places') or 0),
                    'target_quota': (analysis.get('quotas', {}).get('target') or 0),
                    'special_quota': (analysis.get('quotas', {}).get('special') or 0),
                    'separate_quota': (analysis.get('quotas', {}).get('separate') or 0),
                    'trend': analysis['trend']
                }
                directions.append(direction)
            
            print(f"   🎯 directions: {len(directions)}")
            
            if directions:
                print(f"   ✅ Направления найдены!")
                for i, direction in enumerate(directions[:3]):
                    print(f"      {i+1}. {direction['code']} - {direction['name']}")
            else:
                print(f"   ❌ Направления не найдены!")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_bot_issue()
