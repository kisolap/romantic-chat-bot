from aiogram import Router
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command

from answer_functions.create_keyboard import create_row_kb, create_menu_keyboard
from db_directory.crud import broadcast_message
from states import ChangeProfile, LookingPartner
from main import my_bot

router = Router()

ADMIN_ID = 1

@router.message(Command("broadcast"))
async def broadcast_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("У вас нет прав для выполнения этой команды.")

    # Получаем текст для рассылки
    text = ("Друзья, боту нужно немного отдохнуть!\n\n"
            "Работа бота будет восстановлена сегодня не позднее 21:00. "
            "До этого времени бот не будет реагировать на ваши действия.\n\n"
            "Спасибо за понимание!\n"
            "С уважением,\n"
            "ваш @creator_kitt")

    await broadcast_message(my_bot, text)
    await message.answer("Рассылка завершена!")

@router.message(Command("finbroadcast"))
async def broadcast_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("У вас нет прав для выполнения этой команды.")

    # Получаем текст для рассылки
    text = ("Бот снова работает, можешь продолжать искать новые пары, спасибо за ожидание!\n\n"
            "С уважением,\n"
            "ваш @creator_kitt")

    await broadcast_message(my_bot, text)
    await message.answer("Рассылка завершена!")

@router.message(Command("end"))
async def broadcast_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("У вас нет прав для выполнения этой команды.")

    # Получаем текст для рассылки
    text = ("Друзья, спасибо вам всем, что решили воспользоваться этим ботом. Я и Алиса рады, что он оказался полезен"
            " такому количеству людей. Было приятно увидеть и знакомые лица, и новых студентов, и соседей из других вузов. "
            "На этом работа бота подходит к концу, надеюсь за эти 3 дня вы успели найти своего человека :)\n\n"
            "Возможно, мы вернемся и добавим много новых интересных функций, чтобы вы смогли найти еще больше"
            " людей, близких вам по духу, но это будет чуть-чуть попозже.\n\n"
            "Будем рады прочитать ваши отзывы у себя в личке,\n"
            "ваш @creator_kitt ❤️")

    await broadcast_message(my_bot, text)
    await message.answer("Рассылка завершена!")

# В меню выбрали несуществующий вариант
@router.message(ChangeProfile.selects_menu)
async def unknown_option(message: Message):
    await message.answer(
        text="Нет такого варианта, выбери из этих:",
        reply_markup=ReplyKeyboardRemove()
    )

    await create_menu_keyboard(message=message)

# В поиске пар выбрали несуществующий вариант
@router.message(LookingPartner.looking_partners)
async def unknown_option(message: Message):
    await message.answer(
        text="Нет такого варианта, выбери из этих:",
        reply_markup=create_row_kb(["❤️", "👎", "💤"])
    )

# В меню выбрали несуществующий вариант
@router.message(LookingPartner.menu)
async def unknown_option(message: Message):
    await message.answer(
        text="Нет такого варианта, выбери из этих:"
    )

    await message.answer(
        text="1. Смотреть анкеты\n"
             "2. Моя анкета\n"
             "3. Отключить анкету",
        reply_markup=create_row_kb(["1🚀", "2", "3"])
    )

#-----------------------------------------#

@router.message()
async def unforeseen_message(message: Message):
    await message.answer(
        text="Хм, я не знаю, что ответить на это сообщение.\nПопробуй нажать команду /start",
        reply_markup=ReplyKeyboardRemove()
    )