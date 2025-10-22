#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой тест исправлений
"""

def simple_test():
    """Простой тест"""
    print("🔍 Тестирование исправлений...")
    
    try:
        from stats_predictor import get_predictor
        print("✅ Импорт stats_predictor успешен")
        
        predictor = get_predictor()
        print("✅ Предиктор создан")
        
        # Тестируем загрузку данных
        budget_data = predictor.get_stats_for_form("Очно-бюджетная")
        if budget_data is not None:
            print(f"✅ Бюджетные данные загружены: {len(budget_data)} направлений")
            
            # Проверяем, есть ли Прикладная информатика
            has_applied_info = False
            for _, row in budget_data.iterrows():
                direction = str(row.get('Направление', ''))
                if '09.03.03' in direction or 'Прикладная информатика' in direction:
                    has_applied_info = True
                    print(f"❌ Найдена Прикладная информатика в бюджетной форме: {direction}")
                    break
            
            if not has_applied_info:
                print("✅ Прикладная информатика НЕ найдена в бюджетной форме (правильно)")
        else:
            print("❌ Бюджетные данные не загружены")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_test()
