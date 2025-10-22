#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Улучшенный скрипт аудита всех комбинаций предметов и форм обучения
Генерирует графики для каждого направления и создает полный отчет
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Tuple
import re
from stats_predictor import get_predictor

# Настройка matplotlib для русского языка
plt.rcParams['font.family'] = ['DejaVu Sans', 'Liberation Sans', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

def generate_direction_graph(direction_code: str, direction_name: str, form: str, 
                           historical_scores: List[int], predicted_2025: int, 
                           user_score: int = None) -> str:
    """Генерирует график для направления"""
    
    # Создаем директорию для графиков если её нет
    graphs_dir = "reports/graphs"
    os.makedirs(graphs_dir, exist_ok=True)
    
    # Годы для исторических данных
    years = list(range(2019, 2025))
    
    # Фильтруем только существующие данные
    valid_data = [(year, score) for year, score in zip(years, historical_scores) if score > 0]
    
    if not valid_data:
        return ""
    
    years_data, scores_data = zip(*valid_data)
    
    # Создаем график
    plt.figure(figsize=(12, 8))
    
    # Основная линия исторических данных
    plt.plot(years_data, scores_data, 'o-', linewidth=2, markersize=8, 
             color='#2E86AB', label='Исторические данные', alpha=0.8)
    
    # Прогноз на 2025
    if predicted_2025 > 0:
        plt.plot(2025, predicted_2025, 's', markersize=10, 
                color='#F24236', label=f'Прогноз 2025: {predicted_2025}', alpha=0.9)
        
        # Линия тренда к прогнозу
        if len(scores_data) > 1:
            last_year = max(years_data)
            last_score = scores_data[-1]
            plt.plot([last_year, 2025], [last_score, predicted_2025], 
                    '--', color='#F24236', alpha=0.6, linewidth=1)
    
    # Пользовательский балл если указан
    if user_score and user_score > 0:
        plt.axhline(y=user_score, color='#F77F00', linestyle=':', linewidth=2, 
                   label=f'Ваш балл: {user_score}', alpha=0.8)
    
    # Настройка графика
    plt.title(f'{direction_name}\n({direction_code}) - {form}', fontsize=14, fontweight='bold', pad=20)
    plt.xlabel('Год', fontsize=12)
    plt.ylabel('Проходной балл', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=10)
    
    # Настройка осей
    plt.xlim(min(years_data) - 0.5, 2025.5)
    if scores_data:
        min_score = min(scores_data)
        max_score = max(scores_data)
        if predicted_2025 > 0:
            min_score = min(min_score, predicted_2025)
            max_score = max(max_score, predicted_2025)
        if user_score and user_score > 0:
            min_score = min(min_score, user_score)
            max_score = max(max_score, user_score)
        
        plt.ylim(min_score - 10, max_score + 10)
    
    # Добавляем аннотации для ключевых точек
    for year, score in valid_data:
        plt.annotate(f'{score}', (year, score), textcoords="offset points", 
                    xytext=(0,10), ha='center', fontsize=9, alpha=0.7)
    
    if predicted_2025 > 0:
        plt.annotate(f'{predicted_2025}', (2025, predicted_2025), 
                    textcoords="offset points", xytext=(0,10), ha='center', 
                    fontsize=9, alpha=0.7, color='#F24236')
    
    # Сохраняем график
    safe_name = re.sub(r'[^\w\s-]', '', direction_name).strip()
    safe_name = re.sub(r'[-\s]+', '-', safe_name)
    filename = f"{direction_code}_{safe_name}_{form.replace(' ', '_')}.png"
    filepath = os.path.join(graphs_dir, filename)
    
    plt.tight_layout()
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    return filepath

def run_enhanced_audit():
    """Запускает улучшенный аудит с генерацией графиков"""
    
    print("🔍 Запуск улучшенного аудита всех комбинаций...")
    
    # Получаем предиктор
    predictor = get_predictor()
    
    # Формы обучения
    forms = ["Очно-бюджетная", "Очно-платная", "Заочно-бюджетная", "Заочно-платная"]
    
    # Предметы для тестирования
    subjects_list = [
        ["Математика", "Информатика"],
        ["Математика", "Обществознание"],
        ["Математика", "История"],
        ["Математика", "Биология"],
        ["Математика", "Химия"],
        ["Математика", "Физика"],
        ["Математика", "География"],
        ["Математика", "Английский язык"],
        ["Информатика", "Обществознание"],
        ["Информатика", "История"],
        ["Информатика", "Биология"],
        ["Информатика", "Химия"],
        ["Информатика", "Физика"],
        ["Информатика", "География"],
        ["Информатика", "Английский язык"],
        ["Обществознание", "История"],
        ["Обществознание", "Биология"],
        ["Обществознание", "Химия"],
        ["Обществознание", "Физика"],
        ["Обществознание", "География"],
        ["Обществознание", "Английский язык"],
        ["История", "Биология"],
        ["История", "Химия"],
        ["История", "Физика"],
        ["История", "География"],
        ["История", "Английский язык"],
        ["Биология", "Химия"],
        ["Биология", "Физика"],
        ["Биология", "География"],
        ["Биология", "Английский язык"],
        ["Химия", "Физика"],
        ["Химия", "География"],
        ["Химия", "Английский язык"],
        ["Физика", "География"],
        ["Физика", "Английский язык"],
        ["География", "Английский язык"]
    ]
    
    # Результаты аудита
    audit_results = []
    total_combinations = len(forms) * len(subjects_list)
    processed = 0
    
    print(f"📊 Всего комбинаций для проверки: {total_combinations}")
    
    for form in forms:
        print(f"\n📋 Проверка формы: {form}")
        
        for subjects in subjects_list:
            processed += 1
            print(f"  [{processed}/{total_combinations}] Предметы: {', '.join(subjects)}")
            
            # Ищем направления
            directions = predictor.find_directions_by_subjects(subjects, form)
            
            if not directions:
                # Записываем отсутствие направлений
                audit_results.append({
                    'form': form,
                    'subjects': ', '.join(subjects),
                    'code': '',
                    'name': 'НАПРАВЛЕНИЯ НЕ НАЙДЕНЫ',
                    'predicted_2025': '',
                    'trend': '',
                    'budget_places': '',
                    'chance_text': '',
                    'chance_prob': '',
                    'graph_path': '',
                    'historical_scores': '',
                    'user_score': '',
                    'analysis': ''
                })
            else:
                # Обрабатываем найденные направления
                for direction in directions:
                    code = direction.get('code', '')
                    name = direction.get('name', '')
                    
                    # Получаем детали направления
                    details = predictor.get_direction_details(code, form)
                    
                    if details:
                        historical_scores = details.get('historical_scores', [])
                        predicted_2025 = details.get('predicted_2025', 0)
                        trend = details.get('trend', '')
                        budget_places = details.get('budget_places', 0)
                        
                        # Генерируем график
                        graph_path = generate_direction_graph(
                            code, name, form, historical_scores, predicted_2025
                        )
                        
                        # Определяем шансы
                        chance_prob = 0.5
                        chance_text = "🟡 Средние"
                        
                        if predicted_2025 > 0:
                            if predicted_2025 <= 200:
                                chance_prob = 0.85
                                chance_text = "🟢 Высокие"
                            elif predicted_2025 <= 250:
                                chance_prob = 0.65
                                chance_text = "🟡 Средние"
                            else:
                                chance_prob = 0.15
                                chance_text = "🔴 Очень низкие"
                        
                        # Записываем результат
                        audit_results.append({
                            'form': form,
                            'subjects': ', '.join(subjects),
                            'code': code,
                            'name': name,
                            'predicted_2025': predicted_2025,
                            'trend': trend,
                            'budget_places': budget_places,
                            'chance_text': chance_text,
                            'chance_prob': chance_prob,
                            'graph_path': graph_path,
                            'historical_scores': ', '.join(map(str, historical_scores)),
                            'user_score': '',
                            'analysis': f"Прогноз: {predicted_2025}, Тренд: {trend}, Места: {budget_places}"
                        })
    
    # Сохраняем результаты
    os.makedirs("reports", exist_ok=True)
    
    df_results = pd.DataFrame(audit_results)
    df_results.to_csv("reports/enhanced_audit_directions.csv", index=False, encoding='utf-8')
    
    # Создаем сводную статистику
    summary_stats = []
    
    for form in forms:
        form_data = df_results[df_results['form'] == form]
        total_combinations_form = len(subjects_list)
        found_directions = len(form_data[form_data['code'] != ''])
        not_found = total_combinations_form - found_directions
        
        summary_stats.append({
            'form': form,
            'total_combinations': total_combinations_form,
            'directions_found': found_directions,
            'directions_not_found': not_found,
            'success_rate': f"{(found_directions/total_combinations_form)*100:.1f}%",
            'avg_predicted_score': form_data[form_data['predicted_2025'] != '']['predicted_2025'].mean() if found_directions > 0 else 0,
            'total_budget_places': form_data[form_data['budget_places'] != '']['budget_places'].sum() if found_directions > 0 else 0
        })
    
    df_summary = pd.DataFrame(summary_stats)
    df_summary.to_csv("reports/audit_summary.csv", index=False, encoding='utf-8')
    
    # Выводим результаты
    print(f"\n✅ Аудит завершен!")
    print(f"📊 Всего комбинаций проверено: {total_combinations}")
    print(f"📈 Направлений найдено: {len(df_results[df_results['code'] != ''])}")
    print(f"📉 Комбинаций без направлений: {len(df_results[df_results['code'] == ''])}")
    print(f"📁 Отчеты сохранены:")
    print(f"   - reports/enhanced_audit_directions.csv")
    print(f"   - reports/audit_summary.csv")
    print(f"   - reports/graphs/ (графики)")
    
    # Показываем сводку по формам
    print(f"\n📋 Сводка по формам обучения:")
    for _, row in df_summary.iterrows():
        print(f"   {row['form']}: {row['directions_found']}/{row['total_combinations']} "
              f"({row['success_rate']}) - средний балл: {row['avg_predicted_score']:.0f}")
    
    return df_results, df_summary

if __name__ == "__main__":
    try:
        results, summary = run_enhanced_audit()
        print(f"\n🎉 Улучшенный аудит успешно завершен!")
    except Exception as e:
        print(f"❌ Ошибка при выполнении аудита: {e}")
        import traceback
        traceback.print_exc()
