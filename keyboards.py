from telebot import types
from typing import List


def get_main_reply_keyboard() -> types.ReplyKeyboardMarkup:
    """Постоянное меню бота с главными кнопками"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        types.KeyboardButton("🎯 Прогноз поступления"),
        types.KeyboardButton("❓ Задать вопрос")
    )
    keyboard.add(
        types.KeyboardButton("📋 Факультеты ГУУ"),
        types.KeyboardButton("📞 Контакты")
    )
    return keyboard


def get_form_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура формы обучения"""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("Очно-бюджетная", callback_data="form_budget"),
        types.InlineKeyboardButton("Очно-договорная", callback_data="form_contract")
    )
    keyboard.add(
        types.InlineKeyboardButton("Очно-заочная бюджет", callback_data="form_part_budget"),
        types.InlineKeyboardButton("Очно-заочная договор", callback_data="form_part_contract")
    )
    keyboard.add(
        types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")
    )
    return keyboard


def get_subjects_keyboard(selected_subjects: List[str] = None) -> types.InlineKeyboardMarkup:
    """Клавиатура предметов ЕГЭ"""
    if selected_subjects is None:
        selected_subjects = []
    
    subjects = [
        "Математика", "Русский язык", "Информатика", "Обществознание",
        "История", "Биология", "Химия", "Физика", "География",
        "Литература", "Английский язык"
    ]
    
    keyboard = types.InlineKeyboardMarkup()
    
    # Добавляем предметы по 2 в ряд
    for i in range(0, len(subjects), 2):
        row = []
        for j in range(2):
            if i + j < len(subjects):
                subject = subjects[i + j]
                prefix = "✅ " if subject in selected_subjects else ""
                callback_data = f"subject_{subject.lower().replace(' ', '_')}"
                row.append(types.InlineKeyboardButton(
                    f"{prefix}{subject}", 
                    callback_data=callback_data
                ))
        keyboard.add(*row)
    
    # Кнопка "Продолжить" (активна только если выбрано минимум 2 предмета)
    if len(selected_subjects) >= 2:
        keyboard.add(types.InlineKeyboardButton("✅ Продолжить", callback_data="subjects_done"))
    
    keyboard.add(
        types.InlineKeyboardButton("◀️ Назад", callback_data="back_to_form"),
        types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")
    )
    
    return keyboard


def get_achievements_keyboard(selected_achievements: List[str] = None) -> types.InlineKeyboardMarkup:
    """Клавиатура достижений"""
    if selected_achievements is None:
        selected_achievements = []
    
    achievements = [
        "Диплом с отличием",
        "Золотой ГТО"
    ]
    
    keyboard = types.InlineKeyboardMarkup()
    
    for achievement in achievements:
        prefix = "✅ " if achievement in selected_achievements else ""
        callback_data = f"achievement_{achievement.lower().replace(' ', '_')}"
        keyboard.add(types.InlineKeyboardButton(
            f"{prefix}{achievement}", 
            callback_data=callback_data
        ))
    
    keyboard.add(
        types.InlineKeyboardButton("⏭️ Пропустить", callback_data="achievements_skip"),
        types.InlineKeyboardButton("✅ Продолжить", callback_data="achievements_done")
    )
    keyboard.add(
        types.InlineKeyboardButton("◀️ Назад", callback_data="back_to_ege_score"),
        types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")
    )
    
    return keyboard


def get_directions_keyboard(directions: List[dict]) -> types.InlineKeyboardMarkup:
    """Клавиатура направлений"""
    keyboard = types.InlineKeyboardMarkup()
    
    for direction in directions:
        button_text = f"{direction['code']} {direction['name'][:30]}..."
        callback_data = f"direction_{direction['code']}"
        keyboard.add(types.InlineKeyboardButton(button_text, callback_data=callback_data))
    
    keyboard.add(
        types.InlineKeyboardButton("◀️ Назад к достижениям", callback_data="back_to_achievements"),
        types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")
    )
    
    return keyboard


def get_direction_details_keyboard() -> types.InlineKeyboardMarkup:
    """Кнопки управления для детальной информации"""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("◀️ Назад к направлениям", callback_data="back_to_directions"),
        types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")
    )
    return keyboard


def get_main_menu_keyboard() -> types.InlineKeyboardMarkup:
    """Инлайн-клавиатура главного меню (для совместимости)"""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("🎯 Прогноз поступления", callback_data="start_admission"),
        types.InlineKeyboardButton("❓ Задать вопрос", callback_data="ask_question")
    )
    keyboard.add(
        types.InlineKeyboardButton("📋 Факультеты ГУУ", callback_data="faculties"),
        types.InlineKeyboardButton("📞 Контакты", callback_data="contacts")
    )
    return keyboard


def get_ege_score_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура для ввода балла ЕГЭ"""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("◀️ Назад", callback_data="back_to_subjects"),
        types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")
    )
    return keyboard


def get_question_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура для режима вопросов"""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")
    )
    return keyboard


def get_info_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура для информационных страниц (факультеты, контакты)"""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")
    )
    return keyboard
