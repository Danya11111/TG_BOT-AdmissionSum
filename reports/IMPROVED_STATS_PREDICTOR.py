
# Исправления в stats_predictor.py

def load_all_stats(self) -> None:
    """Загружает всю статистику из CSV файлов с исправлениями."""
    for key, filename in self.STATS_FILES.items():
        filepath = os.path.join(self.STATS_DIR, filename)
        if os.path.exists(filepath):
            try:
                # Читаем CSV файл
                df = pd.read_csv(filepath, encoding='utf-8')
                
                # Исправляем проблему с заголовками
                if 'Направление' not in df.columns:
                    # Ищем строку с заголовком "Направление"
                    for i, row in df.iterrows():
                        if 'Направление' in str(row.iloc[0]):
                            df = pd.read_csv(filepath, encoding='utf-8', header=i)
                            break
                
                # Очищаем данные
                df = df.dropna(subset=['Направление'])
                df = df[df['Направление'].str.strip() != '']
                df = df[df['Направление'].str.strip() != '-']
                
                # Фильтруем только реальные направления
                df = df[df['Направление'].str.contains(r'\d{2}\.\d{2}\.\d{2}', na=False)]
                
                self.stats_data[key] = df
                logger.info(f"Загружена статистика {key}: {len(df)} направлений")
            except Exception as e:
                logger.error(f"Ошибка загрузки {filepath}: {e}")
        else:
            logger.warning(f"Файл статистики не найден: {filepath}")

def find_directions_by_subjects(self, user_subjects: List[str], form: str) -> List[Dict]:
    """Исправленная функция поиска направлений."""
    df = self.get_stats_for_form(form)
    if df is None or df.empty:
        return []

    def normalize_subject_name(s: str) -> str:
        text = str(s).strip().lower()
        if any(x in text for x in ['матем', 'мат', 'профильн']):
            return 'математика'
        if any(x in text for x in ['информ', 'инф', 'ит']):
            return 'информатика'
        if any(x in text for x in ['обществ', 'общ', 'общество']):
            return 'обществознание'
        if any(x in text for x in ['истор', 'ист']):
            return 'история'
        if any(x in text for x in ['иностр', 'англий', 'англ', 'ин яз']):
            return 'иностранный язык'
        if any(x in text for x in ['физик', 'физ']):
            return 'физика'
        if any(x in text for x in ['географ', 'гео']):
            return 'география'
        if any(x in text for x in ['биолог', 'био']):
            return 'биология'
        if any(x in text for x in ['хими', 'хим']):
            return 'химия'
        return text

    normalized_user_subjects = [normalize_subject_name(s) for s in user_subjects if s]
    user_has_math = 'математика' in normalized_user_subjects

    results: List[Dict] = []
    for _, row in df.iterrows():
        direction_raw = str(row.get('Направление', '')).strip()
        if not direction_raw:
            continue
            
        code = direction_raw.split(' ')[0]
        subjects_text = str(row.get('Предметы', '')).strip()
        if not subjects_text:
            continue

        # Разбиваем на альтернативные наборы
        alternatives_raw = [alt.strip() for alt in subjects_text.split('/')]
        alternatives: List[List[str]] = []
        for alt in alternatives_raw:
            parts = [normalize_subject_name(p) for p in re.split(r'[;,]', alt) if p.strip()]
            parts = [p for p in parts if p and p != 'русский язык']
            alternatives.append(parts)

        # Проверяем требование математики
        direction_requires_math = any('математика' in alt for alt in alternatives)
        if direction_requires_math and not user_has_math:
            continue

        # Проверяем совпадение
        def covers(alternative: List[str]) -> bool:
            if not alternative:
                return False
            if not direction_requires_math:
                # Гуманитарные направления - полное покрытие
                overlap = sum(1 for subj in alternative if subj in normalized_user_subjects)
                return overlap >= len(alternative)
            else:
                # Технические направления - минимум 2 предмета
                overlap = sum(1 for subj in alternative if subj in normalized_user_subjects)
                return overlap >= min(2, len(alternative))

        if not any(covers(alt) for alt in alternatives):
            continue

        # Добавляем результат
        results.append({
            'code': code,
            'direction_name': direction_raw,
            'subjects': subjects_text,
            'predicted_2025': int(row.get('Год 2025', 0) or 0),
            'budget_places': int(row.get('Кол-во бюджетных мест', 0) or 0),
            'trend': '➡️ Стабильный'
        })

    return results
