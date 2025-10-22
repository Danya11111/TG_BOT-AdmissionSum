#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для анализа структуры CSV файлов
"""

import pandas as pd
import os

def analyze_csv_structure():
    """Анализирует структуру CSV файлов"""
    
    csv_files = [
        "data/guu/stats/Статистика баллов - очная бюджет.csv",
        "data/guu/stats/Статистика баллов - Договор ОЧ.csv",
        "data/guu/stats/Статистика баллов - Бюджет ОЗ.csv",
        "data/guu/stats/Статистика баллов - Договор ОЗ.csv"
    ]
    
    for filepath in csv_files:
        if os.path.exists(filepath):
            print(f"\n📁 Анализ файла: {filepath}")
            
            # Читаем первые 10 строк
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:10]
                for i, line in enumerate(lines):
                    print(f"   Строка {i}: {line.strip()}")
            
            # Пробуем разные варианты чтения
            print(f"\n   🔍 Тестирование чтения:")
            
            # Вариант 1: без skiprows
            try:
                df1 = pd.read_csv(filepath, encoding='utf-8')
                print(f"      Без skiprows: {len(df1)} строк, колонки: {list(df1.columns)[:5]}...")
            except Exception as e:
                print(f"      Без skiprows: ОШИБКА - {e}")
            
            # Вариант 2: skiprows=1
            try:
                df2 = pd.read_csv(filepath, encoding='utf-8', skiprows=1)
                print(f"      skiprows=1: {len(df2)} строк, колонки: {list(df2.columns)[:5]}...")
            except Exception as e:
                print(f"      skiprows=1: ОШИБКА - {e}")
            
            # Вариант 3: skiprows=2
            try:
                df3 = pd.read_csv(filepath, encoding='utf-8', skiprows=2)
                print(f"      skiprows=2: {len(df3)} строк, колонки: {list(df3.columns)[:5]}...")
            except Exception as e:
                print(f"      skiprows=2: ОШИБКА - {e}")
            
            # Вариант 4: skiprows=3
            try:
                df4 = pd.read_csv(filepath, encoding='utf-8', skiprows=3)
                print(f"      skiprows=3: {len(df4)} строк, колонки: {list(df4.columns)[:5]}...")
            except Exception as e:
                print(f"      skiprows=3: ОШИБКА - {e}")

if __name__ == "__main__":
    analyze_csv_structure()
