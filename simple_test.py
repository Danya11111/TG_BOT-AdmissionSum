#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой тест для проверки работы системы
"""

def simple_test():
    """Простой тест"""
    print("🔍 Простой тест системы...")
    
    try:
        from utils import find_directions_by_subjects
        print("✅ Импорт utils успешен")
        
        # Тестируем функцию
        directions = find_directions_by_subjects(["Математика", "Информатика"], "Очно-бюджетная")
        print(f"✅ Функция работает: найдено {len(directions)} направлений")
        
        if directions:
            print("📝 Первые 3 направления:")
            for i, direction in enumerate(directions[:3]):
                print(f"   {i+1}. {direction.get('code', '')} - {direction.get('direction_name', '')}")
        else:
            print("❌ Направления не найдены!")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_test()
