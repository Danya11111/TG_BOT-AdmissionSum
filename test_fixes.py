#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест исправлений
"""

from utils import find_directions_by_subjects

def test_fixes():
    """Тестирует исправления"""
    
    print("🔍 Тестирование исправлений...")
    
    # Тестируем очно-бюджетную форму
    directions = find_directions_by_subjects(["Математика", "Информатика"], "Очно-бюджетная")
    
    print(f"📊 Найдено направлений: {len(directions)}")
    
    for direction in directions:
        code = direction.get('code', '')
        name = direction.get('direction_name', '')
        budget_places = direction.get('budget_places', 0)
        print(f"   {code} - {name} (бюджетных мест: {budget_places})")
        
        # Проверяем, что Прикладная информатика не входит в бюджетную форму
        if "09.03.03" in code:
            print(f"   ❌ ОШИБКА: Прикладная информатика не должна быть в бюджетной форме!")

if __name__ == "__main__":
    test_fixes()
