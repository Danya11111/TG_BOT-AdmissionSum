import os
import logging
import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException
from telebot.handler_backends import BaseMiddleware
from dotenv import load_dotenv
import requests

from gigachat_client import GigaChatClient
from prompts import build_system_prompt, build_short_prompt
from rag_search import RagSearcher
from utils import calculate_total_score, get_directions_data, calculate_chance, get_improved_prediction, get_direction_chart, get_full_direction_stats, find_directions_by_subjects
from prompts import build_admission_chance_prompt
from keyboards import (
    get_form_keyboard, get_subjects_keyboard, get_achievements_keyboard,
    get_directions_keyboard, get_direction_details_keyboard, get_main_menu_keyboard,
    get_main_reply_keyboard, get_ege_score_keyboard, get_question_keyboard, get_info_keyboard
)
from stats_analyzer import stats_analyzer

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set. Add it to .env")

logger.info("Инициализация Telegram бота...")
bot = telebot.TeleBot(BOT_TOKEN)


def safe_edit_reply_markup(chat_id: int, message_id: int, reply_markup: types.InlineKeyboardMarkup) -> None:
    """Edit reply markup and silently ignore 'message is not modified' errors from Telegram API."""
    try:
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=reply_markup)
    except ApiTelegramException as e:
        # Ignore harmless 400 error when markup didn't change
        if 'message is not modified' in str(e).lower():
            logger.debug("Ignored 'message is not modified' for edit_message_reply_markup")
            return
        raise

# GigaChat (опционально)
GIGACHAT_AUTH_BASIC = os.getenv("GIGACHAT_AUTH_BASIC", "").strip()
GIGACHAT_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS").strip()
GIGACHAT_VERIFY_TLS = os.getenv("GIGACHAT_VERIFY_TLS", "true").strip().lower() in ("1", "true", "yes")

gc_client = None
if GIGACHAT_AUTH_BASIC:
    try:
        logger.info("Инициализация GigaChat клиента...")
        gc_client = GigaChatClient(
            auth_basic_base64=GIGACHAT_AUTH_BASIC,
            scope=GIGACHAT_SCOPE,
            verify_tls=GIGACHAT_VERIFY_TLS,
            max_retries=3,
            retry_delay_sec=1.0,
        )
        logger.info("GigaChat клиент успешно инициализирован")
    except Exception as e:
        logger.error(f"Ошибка инициализации GigaChat клиента: {e}")
        gc_client = None

# Инициализация RAG-поиска
RAG_SEARCHER = None
try:
    logger.info("Инициализация RAG-поиска...")
    RAG_SEARCHER = RagSearcher()
    logger.info("RAG-поиск успешно инициализирован")
except Exception as e:
    logger.error(f"Ошибка инициализации RAG-поиска: {e}")
    RAG_SEARCHER = None

# Хранение данных пользователей
user_data = {}

# Информация о факультетах ГУУ
GUU_FACULTIES = {
    "Институт управления персоналом, организационной и кадровой работы": "Информация о факультете управления персоналом...",
    "Институт отраслевого менеджмента": "Информация о факультете отраслевого менеджмента...",
    "Институт государственного управления и права": "Информация о факультете государственного управления...",
    "Институт информационных систем": "Информация о факультете информационных систем...",
    "Институт экономики и финансов": "Информация о факультете экономики и финансов..."
}

# Контакты ГУУ
GUU_CONTACTS = {
    "Приемная комиссия": "Телефон: +7 (495) 371-70-52, email: priem@guu.ru",
    "Сайт": "https://guu.ru/"
}


def ask_gigachat(user_text: str) -> str:
    """RAG-поиск и генерация ответа через GigaChat с fallback-механизмом"""
    logger.info(f"Обработка вопроса пользователя: {user_text[:100]}")
    
    # Этап 1: RAG-поиск
    rag_context_lines = None
    sources_suffix = ""
    hits = []
    
    if RAG_SEARCHER is not None:
        try:
            logger.info("Выполняется RAG-поиск...")
            hits = RAG_SEARCHER.search(user_text, top_k=3)
            rag_context_lines = RagSearcher.format_context(hits)
            
            if hits:
                logger.info(f"Найдено {len(hits)} релевантных фрагментов, лучший score: {hits[0].score:.3f}")
                # Дедупликация источников при одинаковых ссылках/заголовках с сохранением порядка
                seen_sources = set()
                unique_sources = []
                for h in hits:
                    title = h.title or 'Источник'
                    key = (title.strip(), (h.source or '').strip())
                    if key in seen_sources:
                        continue
                    seen_sources.add(key)
                    unique_sources.append(f"- {title} — {h.source}")
                if unique_sources:
                    sources_suffix = "\n\n📚 <b>Источники:</b>\n" + "\n".join(unique_sources)
            else:
                logger.warning("RAG-поиск не вернул результатов")
        except Exception as e:
            logger.error(f"Ошибка при RAG-поиске: {e}", exc_info=True)
    else:
        logger.warning("RAG_SEARCHER не инициализирован")
    
    # Если нет контекста — возвращаем стандартный ответ
    if not rag_context_lines or not hits:
        logger.info("Контекст не найден, возвращаем стандартный ответ")
        return (
            "❌ Не найдено подтверждённых данных в официальных источниках ГУУ.\n\n"
            "💡 <b>Рекомендации:</b>\n"
            "• Уточните вопрос\n"
            "• Обратитесь в приёмную комиссию: +7 (495) 371-70-52\n"
            "• Email: priem@guu.ru\n"
            "• Сайт: https://priem.guu.ru/\n\n"
            "RAG_CONFIDENCE: none"
        )
    
    # Этап 2: Fallback - возвращаем RAG-фрагменты без GigaChat
    def create_fallback_response(confidence: str = "medium") -> str:
        """Создание fallback-ответа на основе RAG-фрагментов"""
        try:
            quote_text = rag_context_lines[0].split('|quote:')[1].strip('"')
            # Ограничиваем длину цитаты
            if len(quote_text) > 300:
                quote_text = quote_text[:300] + "..."
            
            return (
                f"📋 <b>Найдена информация в базе ГУУ:</b>\n\n"
                f"{quote_text}\n"
                f"{sources_suffix}\n\n"
                f"💡 <i>Для получения более полной информации обратитесь в приёмную комиссию.</i>\n\n"
                f"RAG_CONFIDENCE: {confidence}"
            )
        except Exception as e:
            logger.error(f"Ошибка создания fallback-ответа: {e}")
            return (
                "📋 Найдена релевантная информация, но не удалось её отобразить.\n"
                f"{sources_suffix}\n\n"
                "Обратитесь в приёмную комиссию: +7 (495) 371-70-52\n\n"
                f"RAG_CONFIDENCE: {confidence}"
            )
    
    # Если нет GigaChat — используем fallback
    if not gc_client:
        logger.info("GigaChat не доступен, используется fallback-режим")
        return create_fallback_response("medium")
    
    # Этап 3: Генерация ответа через GigaChat
    format_json = "format=json" in user_text.lower()
    short_ctx = build_short_prompt(rag_context_lines)
    messages = [
        {"role": "system", "content": short_ctx},
        {"role": "user", "content": user_text},
    ]
    
    try:
        logger.info("Отправка запроса в GigaChat...")
        answer = gc_client.chat_text(messages=messages, temperature=0.1)
        logger.info("Ответ от GigaChat успешно получен")
        
        # Добавляем источники, если их ещё нет
        if sources_suffix and "Источники:" not in answer and "источник" not in answer.lower():
            answer = f"{answer}{sources_suffix}"
        
        # Добавляем RAG_CONFIDENCE если его нет
        if "RAG_CONFIDENCE:" not in answer:
            answer += "\n\nRAG_CONFIDENCE: high"
        
        return answer
        
    except requests.exceptions.Timeout as e:
        logger.error(f"GigaChat timeout: {e}")
        return (
            "⏱️ <b>Превышено время ожидания ответа от сервиса.</b>\n\n"
            "Попробуйте позже или используйте альтернативные каналы связи:\n\n"
            f"{create_fallback_response('low')}\n\n"
            "📞 Контакты приёмной комиссии:\n"
            "• Телефон: +7 (495) 371-70-52\n"
            "• Email: priem@guu.ru"
        )
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"GigaChat connection error: {e}")
        return (
            "🔌 <b>Ошибка подключения к сервису ответов.</b>\n\n"
            "Проверьте подключение к интернету или попробуйте позже.\n\n"
            f"{create_fallback_response('low')}\n\n"
            "📞 Контакты приёмной комиссии:\n"
            "• Телефон: +7 (495) 371-70-52\n"
            "• Email: priem@guu.ru"
        )
        
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, 'response') else 'unknown'
        logger.error(f"GigaChat HTTP error {status_code}: {e}")
        
        if status_code == 401:
            error_msg = "🔐 <b>Ошибка авторизации сервиса.</b>"
        elif status_code == 429:
            error_msg = "⏳ <b>Превышен лимит запросов.</b> Попробуйте через несколько минут."
        elif status_code >= 500:
            error_msg = "🛠️ <b>Сервис временно недоступен (ошибка сервера).</b>"
        else:
            error_msg = f"⚠️ <b>Ошибка сервиса (код {status_code}).</b>"
        
        return (
            f"{error_msg}\n\n"
            f"{create_fallback_response('low')}\n\n"
            "📞 Контакты приёмной комиссии:\n"
            "• Телефон: +7 (495) 371-70-52\n"
            "• Email: priem@guu.ru"
        )
        
    except RuntimeError as e:
        logger.error(f"GigaChat runtime error: {e}")
        if "failed after" in str(e):
            return (
                "🔄 <b>Сервис ответов недоступен после нескольких попыток.</b>\n\n"
                f"{create_fallback_response('low')}\n\n"
                "📞 Контакты приёмной комиссии:\n"
                "• Телефон: +7 (495) 371-70-52\n"
                "• Email: priem@guu.ru"
            )
        raise
        
    except Exception as e:
        logger.error(f"Неожиданная ошибка при работе с GigaChat: {e}", exc_info=True)
        return (
            "❌ <b>Произошла непредвиденная ошибка.</b>\n\n"
            f"{create_fallback_response('low')}\n\n"
            "📞 Контакты приёмной комиссии:\n"
            "• Телефон: +7 (495) 371-70-52\n"
            "• Email: priem@guu.ru\n\n"
            f"<i>Код ошибки для техподдержки: {type(e).__name__}</i>"
        )


@bot.message_handler(commands=['start'])
def start_message(message):
    """Обработка команды /start"""
    user_id = message.chat.id
    logger.info(f"Пользователь {user_id} запустил бота командой /start")
    
    user_data[user_id] = {
        'state': 'main_menu',
        'form': None,
        'subjects': [],
        'ege_score': None,
        'achievements': [],
        'directions': []
    }
    
    # Постоянное меню с главными кнопками
    reply_keyboard = get_main_reply_keyboard()
    
    welcome_text = """
🎓 <b>Добро пожаловать в Ассистент ГУУ!</b>

Я — ваш персональный помощник для поступления в Государственный университет управления.

<b>🚀 Мои возможности:</b>

<b>🎯 Прогнозирование поступления:</b>
• Анализ проходных баллов 2019-2025
• Расчёт конкурсного балла с учётом достижений
• Оценка шансов поступления по направлениям
• Статистика по квотам и бюджетным местам

<b>❓ Интеллектуальные ответы:</b>
• Поиск по базе знаний ГУУ (RAG-технология)
• Ответы на вопросы о поступлении
• Информация об общежитии и расписании
• Контакты и справочная информация

<b>📊 Аналитика и статистика:</b>
• Тренды изменения проходных баллов
• Конкурентный анализ направлений
• Рекомендации по выбору специальности

<b>💬 Удобный интерфейс:</b>
• Пошаговый ввод данных
• Интерактивные кнопки в сообщениях
• Постоянное меню для быстрой навигации
• Подробная аналитика по каждому направлению

<b>Используйте кнопки меню ниже ⬇️</b>
    """
    
    bot.send_message(
        user_id, 
        welcome_text,
        reply_markup=reply_keyboard,
        parse_mode='HTML'
    )


@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    """Обработка всех callback запросов"""
    user_id = call.message.chat.id
    data = call.data
    logger.info(f"Пользователь {user_id} нажал кнопку: {data}")
    
    if user_id not in user_data:
        user_data[user_id] = {
            'state': 'main_menu',
            'form': None,
            'subjects': [],
            'ege_score': None,
            'achievements': [],
            'directions': []
        }
    
    # Главное меню
    if data == "start_admission":
        user_data[user_id]['state'] = 'select_form'
        # Сбрасываем предыдущие данные
        user_data[user_id]['form'] = None
        user_data[user_id]['subjects'] = []
        user_data[user_id]['ege_score'] = None
        user_data[user_id]['achievements'] = []
        user_data[user_id]['directions'] = []
        
        keyboard = get_form_keyboard()
        bot.edit_message_text(
            "📝 <b>Шаг 1/4: Форма обучения</b>\n\n"
            "Выберите форму обучения:",
            user_id, call.message.message_id,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    elif data == "ask_question":
        user_data[user_id]['state'] = 'ask_question'
        keyboard = get_question_keyboard()
        bot.edit_message_text(
            "❓ <b>Режим вопросов</b>\n\n"
            "Задайте ваш вопрос о ГУУ:\n\n"
            "<i>Например:</i>\n"
            "• Какие документы нужны для поступления?\n"
            "• Как подать документы в общежитие?\n"
            "• Расписание работы приёмной комиссии\n"
            "• Информация о стипендиях",
            user_id, call.message.message_id,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    elif data == "faculties":
        faculty_list = "\n".join([f"• {faculty}" for faculty in GUU_FACULTIES.keys()])
        keyboard = get_info_keyboard()
        bot.edit_message_text(
            f"📋 <b>Факультеты ГУУ:</b>\n\n{faculty_list}\n\n"
            "Для получения подробной информации задайте вопрос в разделе '❓ Задать вопрос'",
            user_id, call.message.message_id,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    elif data == "contacts":
        contact_info = "\n".join([f"• {key}: {value}" for key, value in GUU_CONTACTS.items()])
        keyboard = get_info_keyboard()
        bot.edit_message_text(
            f"📞 <b>Контакты ГУУ:</b>\n\n{contact_info}",
            user_id, call.message.message_id,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    elif data == "back_to_menu":
        user_data[user_id]['state'] = 'main_menu'
        reply_keyboard = get_main_reply_keyboard()
        bot.edit_message_text(
            "🏠 <b>Главное меню</b>\n\n"
            "Используйте кнопки меню ниже для навигации ⬇️",
            user_id, call.message.message_id,
            parse_mode='HTML'
        )
    
    # Прогноз поступления - выбор формы
    elif data.startswith("form_"):
        form_key = data.replace("form_", "")
        # Преобразуем ключ формы в полное название
        form_mapping = {
            "budget": "Очно-бюджетная",
            "contract": "Очно-платная", 
            "oz_budget": "ОЗО-бюджетная",
            "oz_contract": "ОЗО-платная"
        }
        user_data[user_id]['form'] = form_mapping.get(form_key, form_key)
        user_data[user_id]['state'] = 'select_subjects'
        user_data[user_id]['subjects'] = []  # Сбрасываем предметы
        keyboard = get_subjects_keyboard()
        bot.edit_message_text(
            "📚 <b>Шаг 2/4: Предметы ЕГЭ</b>\n\n"
            "Выберите предметы ЕГЭ (минимум 2):",
            user_id, call.message.message_id,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    elif data == "back_to_form":
        user_data[user_id]['state'] = 'select_form'
        keyboard = get_form_keyboard()
        bot.edit_message_text(
            "📝 <b>Шаг 1/4: Форма обучения</b>\n\n"
            "Выберите форму обучения:",
            user_id, call.message.message_id,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    # Выбор предметов
    elif data.startswith("subject_"):
        subject = data.replace("subject_", "").replace("_", " ").title()
        if subject not in user_data[user_id]['subjects']:
            user_data[user_id]['subjects'].append(subject)
        else:
            user_data[user_id]['subjects'].remove(subject)
        
        keyboard = get_subjects_keyboard(user_data[user_id]['subjects'])
        safe_edit_reply_markup(user_id, call.message.message_id, reply_markup=keyboard)
    
    elif data == "subjects_done":
        if len(user_data[user_id]['subjects']) >= 2:
            user_data[user_id]['state'] = 'enter_ege_score'
            keyboard = get_ege_score_keyboard()
            subjects_text = ", ".join(user_data[user_id]['subjects'])
            bot.edit_message_text(
                f"📊 <b>Шаг 3/4: Балл ЕГЭ</b>\n\n"
                f"Выбранные предметы: {subjects_text}\n\n"
                f"Введите суммарный балл ЕГЭ (120-310):",
                user_id, call.message.message_id,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
    
    elif data == "back_to_subjects":
        user_data[user_id]['state'] = 'select_subjects'
        keyboard = get_subjects_keyboard(user_data[user_id]['subjects'])
        bot.edit_message_text(
            "📚 <b>Шаг 2/4: Предметы ЕГЭ</b>\n\n"
            "Выберите предметы ЕГЭ (минимум 2):",
            user_id, call.message.message_id,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    elif data == "back_to_ege_score":
        user_data[user_id]['state'] = 'enter_ege_score'
        keyboard = get_ege_score_keyboard()
        subjects_text = ", ".join(user_data[user_id]['subjects'])
        bot.edit_message_text(
            f"📊 <b>Шаг 3/4: Балл ЕГЭ</b>\n\n"
            f"Выбранные предметы: {subjects_text}\n\n"
            f"Введите суммарный балл ЕГЭ (120-310):",
            user_id, call.message.message_id,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    # Выбор достижений
    elif data.startswith("achievement_"):
        # Преобразуем slug из callback_data обратно в каноническое имя достижения
        slug_text = data.replace("achievement_", "")
        candidate = slug_text.replace("_", " ").lower()
        # Доступные достижения (канонические названия используются в клавиатуре и расчётах)
        available_achievements = [
            "Диплом с отличием",
            "Золотой ГТО",
        ]
        # Подбираем точное имя без искажения регистра (title() ломал аббревиатуры вроде ГТО)
        achievement = next((a for a in available_achievements if a.lower() == candidate), candidate)
        
        if achievement not in user_data[user_id]['achievements']:
            user_data[user_id]['achievements'].append(achievement)
        else:
            user_data[user_id]['achievements'].remove(achievement)
        
        keyboard = get_achievements_keyboard(user_data[user_id]['achievements'])
        safe_edit_reply_markup(user_id, call.message.message_id, reply_markup=keyboard)
    
    elif data in ["achievements_done", "achievements_skip"]:
        user_data[user_id]['state'] = 'show_directions'
        
        logger.info(f"Поиск направлений для пользователя {user_id}: предметы={user_data[user_id]['subjects']}, форма={user_data[user_id]['form']}")
        
        # Показываем сообщение о загрузке
        loading_msg = bot.edit_message_text(
            "🔍 <b>Ищу подходящие направления...</b>\n\n"
            "Анализирую базу данных ГУУ...",
            user_id, call.message.message_id,
            parse_mode='HTML'
        )
        
        # Используем CSV-статистику для подбора направлений по предметам
        try:
            similar_directions = find_directions_by_subjects(
                user_data[user_id]['subjects'],
                user_data[user_id]['form']
            )
            logger.info(f"Найдено {len(similar_directions)} направлений по CSV для пользователя {user_id}")
        except Exception as e:
            logger.error(f"Ошибка при поиске направлений (CSV) для пользователя {user_id}: {e}", exc_info=True)
            similar_directions = []
        
        # Конвертируем в старый формат для совместимости
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
        
        user_data[user_id]['directions'] = directions
        
        if directions:
            keyboard = get_directions_keyboard(directions)
            total_score = calculate_total_score(
                user_data[user_id]['ege_score'], 
                user_data[user_id]['achievements']
            )
            bot.edit_message_text(
                f"🎯 <b>Результаты анализа</b>\n\n"
                f"Ваш балл: {total_score}\n"
                f"Найдено направлений: {len(directions)}\n\n"
                f"Выберите направление для детальной информации:",
                user_id, call.message.message_id,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        else:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton("🔄 Начать заново", callback_data="start_admission"),
                types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")
            )
            bot.edit_message_text(
                "❌ <b>Направления не найдены</b>\n\n"
                "К сожалению, не найдено подходящих направлений.\n"
                "Попробуйте изменить предметы ЕГЭ.",
                user_id, call.message.message_id,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
    
    elif data == "back_to_achievements":
        user_data[user_id]['state'] = 'select_achievements'
        keyboard = get_achievements_keyboard(user_data[user_id]['achievements'])
        bot.edit_message_text(
            f"🏆 <b>Шаг 4/4: Достижения</b>\n\n"
            f"Выберите ваши достижения (необязательно):",
            user_id, call.message.message_id,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    # Детальная информация о направлении
    elif data.startswith("direction_"):
        direction_code = data.replace("direction_", "")
        logger.info(f"Пользователь {user_id} запросил детали направления: {direction_code}")
        direction = next((d for d in user_data[user_id]['directions'] if d['code'] == direction_code), None)
        
        if direction:
            total_score = calculate_total_score(
                user_data[user_id]['ege_score'], 
                user_data[user_id]['achievements']
            )
            
            logger.info(f"Рассчитываем шансы поступления для пользователя {user_id}: направление={direction_code}, балл={total_score}")
            
            # Получаем улучшенный прогноз из CSV данных
            form = user_data[user_id]['form']
            prediction_data = get_improved_prediction(direction_code, form)
            full_stats = get_full_direction_stats(direction_code, form)
            
            # ИСПРАВЛЕНИЕ: Рассчитываем шансы поступления на основе прогноза из CSV
            predicted_2025 = prediction_data.get('predicted_score') or direction.get('predicted_score_2025', 0)
            if predicted_2025 and predicted_2025 > 0:
                score_diff = total_score - predicted_2025
                if score_diff >= 15:
                    chance_text = "🟢 Очень высокие"
                    probability = 0.95
                elif score_diff >= 10:
                    chance_text = "🟢 Высокие"
                    probability = 0.85
                elif score_diff >= 5:
                    chance_text = "🟡 Средние"
                    probability = 0.65
                elif score_diff >= 0:
                    chance_text = "🟡 Низкие"
                    probability = 0.35
                elif score_diff >= -5:
                    chance_text = "🔴 Очень низкие"
                    probability = 0.15
                else:
                    chance_text = "🔴 Практически нет"
                    probability = 0.05
                logger.info(f"Шанс поступления для {user_id}: {probability:.1%} (балл: {total_score}, прогноз: {predicted_2025})")
            else:
                chance_text = "Неизвестно"
                probability = 0.0
                logger.warning(f"Не удалось рассчитать шансы для {direction_code}")
            
            # Получаем дополнительную статистику
            stats = stats_analyzer.get_direction_stats(direction_code)
            years_data = stats['years_data'] if stats else {}
            
            text = f"""
🎯 <b>{direction['name']}</b>
📋 Код: {direction['code']}

📊 <b>Проходные баллы по годам:</b>"""
            
            # Добавляем данные по годам
            historical_scores = prediction_data.get('historical_scores', [])
            if historical_scores:
                for year, score in historical_scores:
                    text += f"\n• {year}: {int(score)}"
            else:
                for year_col in ['Год 2019', 'Год 2020', 'Год 2021', 'Год 2022', 'Год 2023', 'Год 2024']:
                    if year_col in years_data:
                        year_num = year_col.split()[1]
                        text += f"\n• {year_num}: {years_data[year_col]}"
            
            # Прогноз на 2025
            predicted_2025 = prediction_data.get('predicted_score') or direction['predicted_score_2025']
            text += f"\n• Прогноз 2025: {predicted_2025}"
            
            # Тренд
            trend_value = prediction_data.get('trend', 0)
            if trend_value > 0:
                trend_text = f"📈 Растущий (+{abs(round(trend_value, 1))} балл/год)"
            elif trend_value < 0:
                trend_text = f"📉 Снижающийся ({round(trend_value, 1)} балл/год)"
            else:
                trend_text = "➡️ Стабильный"
            
            # ИСПРАВЛЕНИЕ: Показываем правильный тип мест в зависимости от формы обучения
            places_count = full_stats.get('budget_places', 0) if 'бюджет' in form.lower() else full_stats.get('contract_places', 0)
            places_label = "Бюджетные места" if 'бюджет' in form.lower() else "Договорные места"
            
            text += f"""

📈 <b>Тренд:</b> {trend_text}

🎓 <b>Ваш балл:</b> {total_score}
🎯 <b>Шансы поступления:</b> {chance_text} ({probability:.0%})

📚 <b>Предметы:</b> {direction['subjects']}
🏛️ <b>{places_label}:</b> {places_count}

📋 <b>Квоты:</b>
• Целевая: {direction['target_quota']}
• Особая: {direction['special_quota']}
• Отдельная: {direction['separate_quota']}"""
            
            # Получаем краткую оценку от GigaChat (если доступен)
            gigachat_analysis = ""
            if gc_client:
                try:
                    logger.info(f"Запрос оценки шансов от GigaChat для {direction_code}")
                    # Подготавливаем данные для GigaChat
                    analysis_data = {
                        'name': direction['name'],
                        'historical_scores': historical_scores,
                        'predicted_score': predicted_2025,
                        'trend': trend_value,
                        'budget_places': places_count  # ИСПРАВЛЕНИЕ: используем правильное количество мест
                    }
                    
                    # Создаем промпт
                    prompt = build_admission_chance_prompt(total_score, analysis_data)
                    messages = [
                        {"role": "user", "content": prompt}
                    ]
                    
                    # Вызов GigaChat с ограничением токенов
                    gigachat_response = gc_client.chat_text(
                        messages=messages, 
                        temperature=0.1,
                        max_tokens=200  # Ограничение в 200 токенов
                    )
                    
                    gigachat_analysis = f"\n\n🤖 <b>Анализ GigaChat:</b>\n{gigachat_response}"
                    logger.info(f"GigaChat анализ получен для {direction_code}")
                except Exception as e:
                    logger.error(f"Ошибка при получении анализа GigaChat: {e}", exc_info=True)
            
            text += gigachat_analysis
            
            keyboard = get_direction_details_keyboard()
            
            # Отправляем текстовое сообщение
            bot.edit_message_text(
                text, user_id, call.message.message_id,
                reply_markup=keyboard, parse_mode='HTML'
            )
            
            # Генерируем и отправляем график
            try:
                logger.info(f"Генерация графика для {direction_code}")
                chart_buffer = get_direction_chart(direction_code, direction['name'], form, total_score)
                
                if chart_buffer:
                    bot.send_photo(
                        user_id,
                        chart_buffer,
                        caption=f"📊 График проходных баллов: {direction['code']} — {direction['name']}"
                    )
                    logger.info(f"График отправлен пользователю {user_id}")
                else:
                    logger.warning(f"График не сгенерирован для {direction_code}")
            except Exception as e:
                logger.error(f"Ошибка при генерации/отправке графика: {e}", exc_info=True)
    
    elif data == "back_to_directions":
        keyboard = get_directions_keyboard(user_data[user_id]['directions'])
        total_score = calculate_total_score(
            user_data[user_id]['ege_score'], 
            user_data[user_id]['achievements']
        )
        bot.edit_message_text(
            f"🎯 <b>Результаты анализа</b>\n\n"
            f"Ваш балл: {total_score}\n"
            f"Найдено направлений: {len(user_data[user_id]['directions'])}\n\n"
            f"Выберите направление для детальной информации:",
            user_id, call.message.message_id,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Обработка текстовых сообщений"""
    user_id = message.chat.id
    text = (message.text or "").strip()
    logger.info(f"Получено сообщение от пользователя {user_id}: {text[:100]}")
    
    if user_id not in user_data:
        user_data[user_id] = {
            'state': 'main_menu',
            'form': None,
            'subjects': [],
            'ege_score': None,
            'achievements': [],
            'directions': []
        }
    
    state = user_data[user_id].get('state', 'main_menu')
    
    # Обработка команд из постоянного меню
    if text == "🎯 Прогноз поступления":
        user_data[user_id]['state'] = 'select_form'
        # Сбрасываем предыдущие данные
        user_data[user_id]['form'] = None
        user_data[user_id]['subjects'] = []
        user_data[user_id]['ege_score'] = None
        user_data[user_id]['achievements'] = []
        user_data[user_id]['directions'] = []
        
        keyboard = get_form_keyboard()
        bot.send_message(
            user_id,
            "📝 <b>Шаг 1/4: Форма обучения</b>\n\n"
            "Выберите форму обучения:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return
    
    elif text == "❓ Задать вопрос":
        user_data[user_id]['state'] = 'ask_question'
        keyboard = get_question_keyboard()
        bot.send_message(
            user_id,
            "❓ <b>Режим вопросов</b>\n\n"
            "Задайте ваш вопрос о ГУУ:\n\n"
            "<i>Например:</i>\n"
            "• Какие документы нужны для поступления?\n"
            "• Как подать документы в общежитие?\n"
            "• Расписание работы приёмной комиссии\n"
            "• Информация о стипендиях",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return
    
    elif text == "📋 Факультеты ГУУ":
        faculty_list = "\n".join([f"• {faculty}" for faculty in GUU_FACULTIES.keys()])
        keyboard = get_info_keyboard()
        bot.send_message(
            user_id,
            f"📋 <b>Факультеты ГУУ:</b>\n\n{faculty_list}\n\n"
            "Для получения подробной информации задайте вопрос в разделе '❓ Задать вопрос'",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return
    
    elif text == "📞 Контакты":
        contact_info = "\n".join([f"• {key}: {value}" for key, value in GUU_CONTACTS.items()])
        keyboard = get_info_keyboard()
        bot.send_message(
            user_id,
            f"📞 <b>Контакты ГУУ:</b>\n\n{contact_info}",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return
    
    # Ввод балла ЕГЭ
    if state == 'enter_ege_score':
        try:
            score = int(text)
            if 120 <= score <= 310:
                user_data[user_id]['ege_score'] = score
                user_data[user_id]['state'] = 'select_achievements'
                logger.info(f"Пользователь {user_id} ввёл балл ЕГЭ: {score}")
                keyboard = get_achievements_keyboard()
                bot.send_message(
                    user_id,
                    f"🏆 <b>Шаг 4/4: Достижения</b>\n\n"
                    f"Отлично! Ваш балл ЕГЭ: {score}\n\n"
                    "Выберите ваши достижения (необязательно):",
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            else:
                logger.warning(f"Пользователь {user_id} ввёл некорректный балл: {score}")
                keyboard = get_ege_score_keyboard()
                bot.send_message(
                    user_id,
                    "❌ Балл должен быть от 120 до 310. Попробуйте еще раз:",
                    reply_markup=keyboard
                )
        except ValueError:
            logger.warning(f"Пользователь {user_id} ввёл некорректное значение: {text}")
            keyboard = get_ege_score_keyboard()
            bot.send_message(
                user_id,
                "❌ Введите корректное число от 120 до 310:",
                reply_markup=keyboard
            )
    
    # Задавание вопросов
    elif state == 'ask_question':
        # Фильтр релевантности к ГУУ
        keywords = [
            "гуу", "университет управления", "прием", "поступление", "правила приема",
            "факультет", "направление", "кафедра", "общежит", "расписание", "стипенд", "перевод",
            "зачислен", "абитуриент", "студент", "приемная комиссия", "документы", "баллы",
            "егэ", "экзамен", "конкурс", "квота", "бюджет", "договор"
        ]
        is_relevant = any(k in text.lower() for k in keywords)
        wants_json = "format=json" in text.lower()
        
        if not is_relevant and len(text) > 10:
            logger.warning(f"Пользователь {user_id} задал нерелевантный вопрос: {text[:100]}")
            block_text = (
                "❓ Я отвечаю только на вопросы, связанные с Государственным университетом управления. "
                "Попробуйте уточнить вопрос."
            )
            if wants_json:
                reply = (
                    '{"answer_short":"' + block_text + '","answer_full":"","sources":[],"rag_confidence":"low","followup":""}'
                )
            else:
                reply = block_text
        else:
            # Передаём свободную формулировку в RAG-поиск
            logger.info(f"Обработка релевантного вопроса от пользователя {user_id}")
            reply = ask_gigachat(text)
        
        keyboard = get_question_keyboard()
        bot.send_message(user_id, reply, parse_mode='HTML', reply_markup=keyboard, disable_web_page_preview=True)
    
    else:
        # Если пользователь не в режиме вопросов, проверяем на вопросы о ГУУ
        # Проверяем, является ли сообщение вопросом о ГУУ
        keywords = [
            "гуу", "университет управления", "прием", "поступление", "правила приема",
            "факультет", "направление", "кафедра", "общежит", "расписание", "стипенд", "перевод",
            "зачислен", "абитуриент", "студент", "приемная комиссия", "документы", "баллы",
            "егэ", "экзамен", "конкурс", "квота", "бюджет", "договор"
        ]
        is_guu_question = any(k in text.lower() for k in keywords)
        
        if is_guu_question and len(text) > 10:
            # Автоматически переключаемся в режим вопросов
            logger.info(f"Автоматическое переключение в режим вопросов для пользователя {user_id}")
            user_data[user_id]['state'] = 'ask_question'
            reply = ask_gigachat(text)
            keyboard = get_question_keyboard()
            bot.send_message(user_id, reply, parse_mode='HTML', reply_markup=keyboard, disable_web_page_preview=True)
        else:
            reply_keyboard = get_main_reply_keyboard()
            bot.send_message(
                user_id,
                "🏠 <b>Главное меню</b>\n\n"
                "Используйте кнопки меню ниже для навигации ⬇️",
                reply_markup=reply_keyboard,
                parse_mode='HTML'
            )


# Запуск бота
if __name__ == '__main__':
    try:
        logger.info("Удаление вебхука...")
        bot.remove_webhook()
    except Exception as e:
        logger.warning(f"Не удалось удалить вебхук: {e}")
    
    logger.info("="*50)
    logger.info("Бот запущен и готов к работе!")
    logger.info("="*50)
    
    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка при работе бота: {e}", exc_info=True)
        raise
