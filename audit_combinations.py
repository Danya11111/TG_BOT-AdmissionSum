import os
import itertools
import pandas as pd
from typing import List, Dict
from stats_predictor import get_predictor
from utils import calculate_total_score

REPORTS_DIR = os.path.join('reports')
GRAPHS_DIR = os.path.join(REPORTS_DIR, 'graphs')

SUBJECT_POOL = [
    'Математика', 'Информатика', 'Обществознание', 'История',
    'Биология', 'Химия', 'Физика', 'География', 'Английский язык'
]

FORMS = [
    ('budget', 'Очно-бюджетная'),
    ('contract', 'Очно-договорная'),
    ('part_budget', 'Очно-заочная бюджет'),
    ('part_contract', 'Очно-заочная договор'),
]

DEFAULT_EGE_SCORE = 250


def ensure_dirs():
    os.makedirs(GRAPHS_DIR, exist_ok=True)


def normalize_subjects(subjects: List[str]) -> List[str]:
    # Русский язык везде присутствует, добавим автоматически
    base = list(subjects)
    if 'Русский язык' not in base:
        base.append('Русский язык')
    # Математика обязательна по требованию логики подбора
    if 'Математика' not in base:
        base.append('Математика')
    return base


def run_audit() -> pd.DataFrame:
    ensure_dirs()
    predictor = get_predictor()

    rows: List[Dict] = []

    # Комбинации: берём пары и тройки из пула предметов (математика добавится автоматически)
    all_subject_sets: List[List[str]] = []
    for r in (2, 3):
        for combo in itertools.combinations(SUBJECT_POOL, r):
            all_subject_sets.append(list(combo))

    for form_key, form_name in FORMS:
        df = predictor.get_stats_for_form(form_key)
        if df is None or df.empty:
            continue

        for subjects in all_subject_sets:
            subjects_full = normalize_subjects(subjects)
            matches = predictor.find_directions_by_subjects(subjects_full, form_key)

            if not matches:
                rows.append({
                    'form': form_name,
                    'subjects': ', '.join(subjects_full),
                    'code': '',
                    'name': 'НАПРАВЛЕНИЯ НЕ НАЙДЕНЫ',
                    'predicted_2025': '',
                    'trend': '',
                    'budget_places': '',
                    'chance_text': '—',
                    'chance_prob': '',
                    'graph_path': ''
                })
                continue

            # Ограничим до 5 направлений на комбинацию для читаемости
            for item in matches[:5]:
                # Простейшая оценка шансов: сравним DEFAULT_EGE_SCORE с прогнозом
                predicted = item.get('predicted_2025') or 0
                score = DEFAULT_EGE_SCORE
                diff = score - (predicted or score)
                if diff >= 10:
                    chance_text, chance_prob = '🟢 Высокие', 0.85
                elif diff >= 5:
                    chance_text, chance_prob = '🟡 Средние', 0.65
                elif diff >= 0:
                    chance_text, chance_prob = '🟡 Низкие', 0.35
                else:
                    chance_text, chance_prob = '🔴 Очень низкие', 0.15

                rows.append({
                    'form': form_name,
                    'subjects': ', '.join(subjects_full),
                    'code': item['code'],
                    'name': item['direction_name'],
                    'predicted_2025': predicted,
                    'trend': item.get('trend'),
                    'budget_places': item.get('budget_places'),
                    'chance_text': chance_text,
                    'chance_prob': chance_prob,
                    'graph_path': ''  # опционально можно добавить генерацию графиков
                })

    report_df = pd.DataFrame(rows)
    report_path = os.path.join(REPORTS_DIR, 'audit_directions.csv')
    report_df.to_csv(report_path, index=False, encoding='utf-8-sig')
    return report_df


if __name__ == '__main__':
    df = run_audit()
    print(f'Отчёт сохранён: {os.path.join(REPORTS_DIR, "audit_directions.csv")}')
    print(f'Всего строк: {len(df)}')
