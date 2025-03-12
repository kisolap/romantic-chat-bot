from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message

def create_row_kb(items: list[str]) -> ReplyKeyboardMarkup:
    row = [KeyboardButton(text=item) for item in items]
    return ReplyKeyboardMarkup(keyboard = [row], resize_keyboard=True)

async def create_menu_keyboard(message: Message):
    await message.answer(
        text="1. Смотреть анкеты.\n"
             "2. Изменить фотографии.\n"
             "3. Изменить описание.\n"
             "4. Изменить имя.\n"
             "5. Изменить цели.",
        reply_markup=create_row_kb(["1🚀", "2", "3", "4", "5"]))