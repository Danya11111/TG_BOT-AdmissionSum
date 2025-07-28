import telebot
from telebot import types

# Заменить "YOUR_BOT_TOKEN" на токен вашего бота
BOT_TOKEN = "7832512282:AAE8lq4ZPpoJBwdUEtEVDA0Jh7_QoZr_DDc"

bot = telebot.TeleBot(BOT_TOKEN)

# Информация о факультетах ГУУ
GUU_FACULTIES = {
    "Институт управления персоналом, организационной и кадровой работы": "Информация о факультете ...",
    "Институт отраслевого менеджмента": "Информация о факультете ...",
    "Институт государственного управления и права": "Информация о факультете ...",
    "Институт информационных систем": "Информация о факультете ...",
    "Институт экономики и финансов": "Информация о факультете ..."
}

# Контакты ГУУ
GUU_CONTACTS = {
    "Приемная комиссия": "Телефон: +7 (495) 371-70-52, email: priem@guu.ru",
    "Сайт": "https://guu.ru/"
}

# Функция для создания клавиатуры
def create_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    button1 = types.KeyboardButton("Факультеты ГУУ")
    button2 = types.KeyboardButton("Контакты ГУУ")
    button3 = types.KeyboardButton("Сайт ГУУ")
    button4 = types.KeyboardButton("Помощь")
    keyboard.add(button1, button2, button3, button4)
    return keyboard

# Обработка команды /start
@bot.message_handler(commands=['start'])
def start_message(message):
    keyboard = create_keyboard()
    bot.send_message(message.chat.id, "Привет! Я бот-помощник для абитуриентов ГУУ. Чем я могу тебе помочь?", reply_markup=keyboard)

# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "Факультеты ГУУ":
        faculty_list = "\n".join([f"- {faculty}" for faculty in GUU_FACULTIES.keys()])
        bot.send_message(message.chat.id, f"Список факультетов ГУУ:\n{faculty_list}\n\nЧтобы узнать подробнее, введите название факультета.")
    elif message.text in GUU_FACULTIES:
          bot.send_message(message.chat.id, GUU_FACULTIES[message.text])
    elif message.text == "Контакты ГУУ":
        contact_info = "\n".join([f"{key}: {value}" for key, value in GUU_CONTACTS.items()])
        bot.send_message(message.chat.id, f"Контактная информация ГУУ:\n{contact_info}")
    elif message.text == "Сайт ГУУ":
        bot.send_message(message.chat.id, GUU_CONTACTS["Сайт"])
    elif message.text == "Помощь":
        bot.send_message(message.chat.id, "Я помогу вам узнать о факультетах, контактах и сайте ГУУ. Используйте кнопки на клавиатуре.")
    else:
        bot.send_message(message.chat.id, "Извини, я не понимаю эту команду. Используй кнопки или введи название факультета.")


# Запуск бота
if __name__ == '__main__':
    bot.infinity_polling()

