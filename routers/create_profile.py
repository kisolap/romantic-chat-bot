import asyncio
import os

from main import my_bot

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram import Router, F
from aiogram.filters import Command, Filter
from aiogram.types import (Message, ReplyKeyboardRemove, PhotoSize)

from states import ChangeProfile
from answer_functions.create_keyboard import create_row_kb, create_menu_keyboard
from answer_functions.show_profile import show_profile

from db_directory.crud import user_exists, create_user, add_photo

# Папка для сохранения фото
PHOTO_DIR = "/Users/mikhailtyo/Desktop/chatbot"
os.makedirs(PHOTO_DIR, exist_ok=True)

router = Router()

class isDigitFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        if message.text:
            return message.text.isdigit() and int(message.text) in range(18, 100)
        else:
            return False

class CreateProfile(StatesGroup):
    waiting_start = State()
    setting_age = State()
    setting_faculty = State()
    setting_goals = State()
    setting_gender = State()
    setting_preference = State()
    setting_name = State()
    setting_description = State()
    setting_photo = State()

# Приветственное сообщение
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.update_data(telegram_username=message.from_user.username)

    telegram_id = message.from_user.id

    if await user_exists(telegram_id):
        await message.answer(
            text="Ты уже зарегистрирован! Вот твоя анкета:",
            reply_markup=ReplyKeyboardRemove()
        )
        await show_profile(message=message)
        await create_menu_keyboard(message=message)
        await state.set_state(ChangeProfile.selects_menu)
    else:
        await message.answer(
            text="Привет! Если ты здесь, значит, ты открыт к новым знакомствам.\n\n"
                 "Добро пожаловать!\n\n"
                 "Мы посчитали, что в нашем институте недостаточно коммуникации между разными факультетами, "
                 "а время на живое общение найти не всегда удаётся. "
                 "Надеемся, новый формат поможет решить эту проблему 🤍\n\n"
                 "В нашем боте можно найти себе половинку, друга или единомышленника.\n\n"
                 "Ну что, начнём?\n\n"
                 "--------------------------\n"
                 "автор бота: @creator_kitt",
            reply_markup=create_row_kb(["Давай начнем!"])
        )
        await state.set_state(CreateProfile.waiting_start)

# Подтверждение старта, переход к возрасту
@router.message(CreateProfile.waiting_start, F.text.lower() == "давай начнем!")
async def chosen_start(message: Message, state: FSMContext):
    await message.answer(
        text="Сколько тебе лет?",
        reply_markup=ReplyKeyboardRemove()
    )

    await state.set_state(CreateProfile.setting_age)

# Обработка некорректного подтверждения старта
@router.message(CreateProfile.waiting_start)
async def chosen_start_incorrectly(message: Message):
    await message.answer(
        text="Нажми на кнопку, чтобы продолжить регистрацию:",
        reply_markup=create_row_kb(["Давай начнем!"])
    )

# Обработка подтверждения возраста, переход к faculty
@router.message(CreateProfile.setting_age, isDigitFilter())
async def chosen_age(message: Message, state: FSMContext):
    await state.update_data(age=int(message.text))

    await message.answer(
        text="Откуда ты? С какого факультета, кто мастер (если есть)?",
        reply_markup=ReplyKeyboardRemove()
    )

    await state.set_state(CreateProfile.setting_faculty)

# Обработка некорректного ответа на возраст
@router.message(CreateProfile.setting_age)
async def chosen_age_incorrectly(message: Message):
    await message.answer(
        text="Укажи правильный возраст, используй только цифры!"
    )

# Обработка подтверждения факультета, переход к целям
@router.message(CreateProfile.setting_faculty, F.text)
async def chosen_faculty(message: Message, state: FSMContext):
    await state.update_data(faculty=message.text)

    await message.answer(
        text="Кого ты ищешь?",
        reply_markup=create_row_kb(["Любовь", "Друзей", "Единомышленников", "Всех!"])
    )

    await state.set_state(CreateProfile.setting_goals)

# Обработка некорректного ответа на факультет
@router.message(CreateProfile.setting_faculty)
async def chosen_faculty_incorrectly(message: Message):
    await message.answer(
        text="Это не похоже на название факультета, напиши текстом"
    )

# Обработка целей, переход к имени
@router.message(CreateProfile.setting_goals, F.text.lower().in_({"любовь", "друзей", "единомышленников", "всех!"}))
async def chosen_gender(message: Message, state: FSMContext):

    if message.text.lower() == "любовь":
        await state.update_data(sex="love")
    elif message.text.lower() == "друзей":
        await state.update_data(sex="friend")
    elif message.text.lower() == "единомышленников":
        await state.update_data(sex="supporter")
    elif message.text.lower() == "всех!":
        await state.update_data(sex="all")

    await message.answer(
        text="Как тебя зовут?",
        reply_markup=ReplyKeyboardRemove()
    )

    await state.set_state(CreateProfile.setting_name)

# Некорректная обработка целей
@router.message(CreateProfile.setting_goals)
async def chosen_gender_incorrectly(message: Message):
    await message.answer(
        text="Выбери кого ты ищешь:",
        reply_markup=create_row_kb(["Любовь", "Друзей", "Единомышленников", "Всех!"])
    )

# Обработка имени, переход к описанию
@router.message(CreateProfile.setting_name, F.text)
async def chosen_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)

    await message.answer(
        text=f"Приятно познакомиться, {message.text}!\n\n "
             f"Расскажи о себе...\n\n"
             f"(Примеры того, что можно написать, если нет идей:\n"
             f"1. Что ты ел на обед?\n"
             f"2. Почему решил поступать в РГИСИ?\n"
             f"3. Если бы ты был рыбой, то какой?\n"
             f"4. Твой любимый район Санкт-Петербурга)\n\n"
             f"...и подробнее о том, кого хочешь найти\n\n"
             f"❤️‍🩹 Если ищешь любовь, то опиши свою идеальную вторую половинку.\n"
             f"💜 Если ищешь друзей, то напиши, что для тебя дружба.\n"
             f"🩵 Если ищешь единомышленника, то расскажи о своей идее и кто тебе нужен",
        reply_markup=create_row_kb(["Пропустить"])
    )

    await state.set_state(CreateProfile.setting_description)

# Некорректная обработка имени
@router.message(CreateProfile.setting_name)
async def chosen_name_incorrectly(message: Message):
    await message.answer(
        text=f"Напиши свое имя текстом."
    )

# Отказ от описания, переход к главному фото
@router.message(CreateProfile.setting_description, F.text.lower() == "пропустить")
async def chosen_cancel_description(message: Message, state: FSMContext):
    await state.update_data(bio=None)
    await message.answer(
        text="А теперь пришли одну свою самую клёвую фотографию!",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.update_data(photos=[])
    await state.set_state(CreateProfile.setting_photo)

# Обработка описания, переход к главному фото
@router.message(CreateProfile.setting_description, F.text)
async def chosen_description(message: Message, state: FSMContext):

    await state.update_data(bio=message.text)

    await message.answer(
        text="А теперь пришли одну свою самую клёвую фотографию!",
        reply_markup=ReplyKeyboardRemove()
    )

    await state.update_data(photos=[])

    await state.set_state(CreateProfile.setting_photo)

# Обработка некорректного описания, предложение пропустить
@router.message(CreateProfile.setting_description)
async def chosen_description_incorrectly(message: Message):
    await message.answer(
        text=f"Напиши немного о себе или нажми \"Пропустить\".",
        reply_markup=create_row_kb(["Пропустить"])
    )

# Обработка фото, переход в "меню"
@router.message(CreateProfile.setting_photo, F.photo[-1].as_('largest_photo'))
async def chosen_main_photo(message: Message, state: FSMContext, largest_photo: PhotoSize):
    data = await state.get_data()
    data["telegram_id"] = message.from_user.id
    cur_photos = data.get('photos', [])

    file = await my_bot.get_file(largest_photo.file_id)
    file_path = os.path.join(PHOTO_DIR, f"{file.file_id}.jpg")
    await my_bot.download(file, destination=file_path)
    cur_photos.append(file_path)

    await state.update_data(photos=cur_photos)

    if len(cur_photos) < 3:
        await message.answer(
            text=f"Добавлено {len(cur_photos)} из 3. Добавим ещё?",
            reply_markup=create_row_kb(["Нет, хватит"])
        )
    else:
        user_data = await state.get_data()
        new_user = await create_user(
            message.from_user.id,
            user_data.get('telegram_username'),
            user_data.get('name'),
            user_data.get('age'),
            user_data.get('sex'),
            "both",
            user_data.get('bio'),
            user_data.get('faculty')
        )

        for photo_path in user_data.get('photos', []):
            await add_photo(new_user.telegram_id, photo_path)

        await message.answer("Так выглядит твоя анкета:", reply_markup=ReplyKeyboardRemove())
        await show_profile(message=message)
        await create_menu_keyboard(message=message)
        await state.set_state(ChangeProfile.selects_menu)

# Обработка отказа от дополнительных фото, переход к просмотру своей анкеты
@router.message(CreateProfile.setting_photo,
                F.text.lower() == "нет, хватит")
async def chosen_one_main_photo_(message: Message, state: FSMContext):

    user_data = await state.get_data()
    user_data['telegram_id'] = message.from_user.id

    new_user = await create_user(
        message.from_user.id,
        user_data.get('telegram_username'),
        user_data.get('name'),
        user_data.get('age'),
        user_data.get('sex'),
        "both",
        user_data.get('bio'),
        user_data.get('faculty')
    )

    for photo_path in user_data.get('photos', []):
        await add_photo(new_user.telegram_id, photo_path)

    await message.answer(
        text="Так выглядит твоя анкета:",
        reply_markup=ReplyKeyboardRemove()
    )

    await asyncio.sleep(1)

    await show_profile(message=message)
    await create_menu_keyboard(message=message)

    await state.set_state(ChangeProfile.selects_menu)

# Обработка некорректного фото
@router.message(CreateProfile.setting_photo)
async def chosen_main_photo_incorrect(message: Message):
    await message.answer(
        text="Это не фотография. Добавим ещё одну фотографию?",
        reply_markup=create_row_kb(["Нет, хватит"])
    )

