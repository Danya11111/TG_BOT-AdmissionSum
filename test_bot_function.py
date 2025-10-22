#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Быстрый тест функции find_directions_by_subjects
"""

from utils import find_directions_by_subjects

def test_bot_function():
    """Тестирует функцию, которую использует бот"""
    
    print("🔍 Тестирование функции find_directions_by_subjects...")
    
    # Тестовые случаи из скриншота
    test_cases = [
        (["Математика", "Информатика"], "Очно-бюджетная"),
        (["Математика", "Информатика"], "Очно-платная"),
        (["Обществознание", "История"], "Очно-бюджетная"),
        (["Обществознание", "Биология"], "Очно-бюджетная"),
    ]
    
    for subjects, form in test_cases:
        print(f"\n📋 Тест: {', '.join(subjects)} ({form})")
        
        try:
            directions = find_directions_by_subjects(subjects, form)
            print(f"   🎯 Найдено направлений: {len(directions)}")
            
            if directions:
                print(f"   📝 Направления:")
                for i, direction in enumerate(directions[:5]):  # Показываем первые 5
                    code = direction.get('code', '')
                    name = direction.get('direction_name', '')
                    print(f"      {i+1}. {code} - {name}")
            else:
                print(f"   ❌ Направления не найдены!")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_bot_function()
