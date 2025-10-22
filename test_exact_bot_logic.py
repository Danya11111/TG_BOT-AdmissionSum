#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Точный тест логики бота
"""

import logging
from utils import find_directions_by_subjects

# Настройка логирования как в боте
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_exact_bot_logic():
    """Точный тест логики бота"""
    
    print("🔍 Точный тест логики бота...")
    
    # Симулируем данные пользователя как в боте
    user_data = {
        'subjects': ["Математика", "Информатика"],
        'form': "Очно-бюджетная"
    }
    
    print(f"📋 Данные пользователя: {user_data}")
    
    # Используем CSV-статистику для подбора направлений по предметам (точно как в боте)
    try:
        similar_directions = find_directions_by_subjects(
            user_data['subjects'],
            user_data['form']
        )
        logger.info(f"Найдено {len(similar_directions)} направлений по CSV")
        print(f"📊 similar_directions: {len(similar_directions)}")
    except Exception as e:
        logger.error(f"Ошибка при поиске направлений (CSV): {e}", exc_info=True)
        similar_directions = []
        print(f"❌ Ошибка: {e}")
    
    # Конвертируем в старый формат для совместимости (точно как в боте)
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
    
    print(f"🎯 directions: {len(directions)}")
    
    # Логика бота
    if directions:
        print(f"✅ Направления найдены! Показываем пользователю:")
        for i, direction in enumerate(directions):
            print(f"   {i+1}. {direction['code']} - {direction['name']}")
    else:
        print(f"❌ Направления не найдены! Показываем ошибку пользователю")

if __name__ == "__main__":
    test_exact_bot_logic()
