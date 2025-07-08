import os
import json
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from telegram import BotCommand

# === ФАЙЛ ДЛЯ ХРАНЕНИЯ ДАННЫХ ===
DATA_FILE = "shopping_lists.json"

def load_shopping_lists():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_shopping_lists(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# === ОБЩИЙ СПИСОК ===
shopping_lists = load_shopping_lists()
current_items = {}

# === МЕНЮ ===

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("Изменить список")],
            [KeyboardButton("Показать кнопки товаров")],
            [KeyboardButton("Показать список")]
        ],
        resize_keyboard=True
    )

# === ОБРАБОТЧИКИ ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Это общий список покупок для всех пользователей.",
        reply_markup=get_main_menu()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "Показать список":
        if "global" in shopping_lists:
            await update.message.reply_text(shopping_lists["global"])
        else:
            await update.message.reply_text("Список пока не задан.")
    elif text == "Показать кнопки товаров":
        if "global" in shopping_lists:
            lines = shopping_lists["global"].splitlines()
            if not lines:
                await update.message.reply_text("Список пуст.")
                return
            current_items["global"] = lines[1:]  # исключаем дату
            await send_item_buttons(update, current_items["global"])
        else:
            await update.message.reply_text("Список пуст.")
    elif text == "Изменить список":
        await update.message.reply_text("Отправьте новый список (первая строка — дата, далее — товары).")
        context.user_data["awaiting_list"] = True
    elif context.user_data.get("awaiting_list"):
        shopping_lists["global"] = text
        save_shopping_lists(shopping_lists)
        await update.message.reply_text("Список обновлён!", reply_markup=get_main_menu())
        context.user_data["awaiting_list"] = False
    else:
        await update.message.reply_text("Неизвестная команда. Используйте меню.")

async def send_item_buttons(update: Update, items):
    if not items:
        await update.message.reply_text("Все товары куплены!")
        return

    keyboard = [[InlineKeyboardButton(text=item, callback_data=item)] for item in items]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите купленный товар:", reply_markup=reply_markup)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    item_clicked = query.data

    if "global" in current_items:
        current_items["global"] = [i for i in current_items["global"] if i != item_clicked]

        if current_items["global"]:
            keyboard = [[InlineKeyboardButton(text=item, callback_data=item)] for item in current_items["global"]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Выберите купленный товар:", reply_markup=reply_markup)
        else:
            await query.edit_message_text("Все товары куплены!")
            # Отправка эффекта 🎉
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="🎉"
            )
    else:
        await query.edit_message_text("Нет активного списка.")

# === ГЛАВНАЯ ФУНКЦИЯ ===

def main():
    TOKEN = os.getenv("BOT_TOKEN")  # Или вставить строкой

    app = ApplicationBuilder().token(TOKEN).build()

    # Команды для синего меню
    async def set_bot_commands(app):
        await app.bot.set_my_commands([
            BotCommand("start", "Запустить бота")
        ])

    app.post_init = set_bot_commands

    # Обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Бот запущен.")
    app.run_polling()


if __name__ == "__main__":
    main()
