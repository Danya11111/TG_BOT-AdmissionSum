#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой тест для отладки загрузки CSV
"""

import pandas as pd
import os

def debug_csv_loading():
    """Отладка загрузки CSV файла"""
    
    filepath = "data/guu/stats/Статистика баллов - очная бюджет.csv"
    
    print(f"🔍 Отладка файла: {filepath}")
    
    if not os.path.exists(filepath):
        print("❌ Файл не найден!")
        return
    
    # Читаем CSV
    df = pd.read_csv(filepath, encoding='utf-8')
    print(f"📊 Исходный размер: {len(df)} строк")
    print(f"📋 Колонки: {list(df.columns)}")
    
    # Показываем первые строки
    print(f"\n📝 Первые 5 строк:")
    for i, row in df.head().iterrows():
        print(f"   Строка {i}: {row['Направление']}")
    
    # Очищаем данные
    df_clean = df.dropna(subset=['Направление'])
    print(f"\n🧹 После dropna: {len(df_clean)} строк")
    
    df_clean = df_clean[df_clean['Направление'].str.strip() != '']
    print(f"🧹 После удаления пустых: {len(df_clean)} строк")
    
    df_clean = df_clean[df_clean['Направление'].str.strip() != '-']
    print(f"🧹 После удаления '-': {len(df_clean)} строк")
    
    # Тестируем фильтр
    print(f"\n🔍 Тестируем фильтр направлений:")
    for i, row in df_clean.iterrows():
        direction = str(row['Направление'])
        has_code = bool(pd.Series([direction]).str.contains(r'\d{2}\.\d{2}\.\d{2}', na=False, regex=True).iloc[0])
        print(f"   {direction}: {has_code}")
    
    # Применяем фильтр
    df_filtered = df_clean[df_clean['Направление'].str.contains(r'\d{2}\.\d{2}\.\d{2}', na=False, regex=True)]
    print(f"\n✅ После фильтрации: {len(df_filtered)} строк")
    
    # Показываем результат
    if len(df_filtered) > 0:
        print(f"\n📋 Найденные направления:")
        for i, row in df_filtered.iterrows():
            direction = row['Направление']
            subjects = row.get('Предметы', 'Нет данных')
            print(f"   {direction}: {subjects}")
    else:
        print(f"\n❌ Направления не найдены!")

if __name__ == "__main__":
    debug_csv_loading()
