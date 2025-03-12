import os

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, PhotoSize
from aiogram.filters import Command

from answer_functions.create_keyboard import create_row_kb, create_menu_keyboard
from db_directory.crud import get_user, add_photo, update_user_info, update_user_photos, delete_photo, get_user_photos
from answer_functions.show_profile import show_profile
from main import my_bot

from states import ChangeProfile

PHOTO_DIR = "/Users/mikhailtyo/Desktop/chatbot/"

router = Router()

# Отменили выбор нового описания, имени
@router.message(F.text.lower() == "отменить")
@router.message(Command("profile"))
async def cancel_any_action(message: Message, state: FSMContext):
    await message.answer(
        text="Так выглядит твоя анкета:",
        reply_markup=ReplyKeyboardRemove()
    )

    await show_profile(message=message)
    await create_menu_keyboard(message=message)

    await state.set_state(ChangeProfile.selects_menu)

#-----------------------------------------#

# Смена фотографий
@router.message(ChangeProfile.selects_menu, F.text.lower() == "2")
async def chosen_changing_photo(message: Message, state: FSMContext):
    await message.answer(
        text="Теперь пришли одно новое фото, которое будут видеть другие пользователи.",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.update_data(photos=[])
    photos = await get_user_photos(message.from_user.id)
    for photo in photos:
        await delete_photo(photo.id)
    await state.set_state(ChangeProfile.setting_new_photos)

# Установка новых фотографий (до 3х шт.)
@router.message(ChangeProfile.setting_new_photos, F.photo[-1].as_('largest_photo'))
async def chosen_new_photo(message: Message, state: FSMContext, largest_photo: PhotoSize):
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

        for photo_path in user_data.get('photos', []):
            await add_photo(message.from_user.id, photo_path)

        await message.answer("Так выглядит твоя анкета:", reply_markup=ReplyKeyboardRemove())
        await show_profile(message=message)
        await create_menu_keyboard(message=message)
        await state.set_state(ChangeProfile.selects_menu)

# Отказ от установки дополнительных фотографий
@router.message(ChangeProfile.setting_new_photos,
                F.text.lower() == "нет, хватит")
async def chosen_cancel_new_photo(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    data = await state.get_data()

    if user:
        for photo_path in data.get("photos", []):
            await add_photo(user.telegram_id, photo_path)

    await update_user_photos(telegram_id=message.from_user.id, photo_paths=data.get("photos"))

    await message.answer("Так выглядит твоя анкета:", reply_markup=ReplyKeyboardRemove())
    await show_profile(message=message)
    await create_menu_keyboard(message=message)
    await state.set_state(ChangeProfile.selects_menu)

# Для фото использовался не формат фото
@router.message(ChangeProfile.setting_new_photos)
async def chosen_new_photo_incorrect(message: Message):
    await message.answer(
        text="Это не фотография. "
             "Пришли фотографию, которую будут видеть другие пользователи",
    )

#-----------------------------------------#

# Смена описания
@router.message(ChangeProfile.selects_menu, F.text.lower() == "3")
async def chosen_changing_description(message: Message, state: FSMContext):
    await message.answer(
        text=f"Расскажи о себе и кого ты хочешь найти.",
        reply_markup=create_row_kb(["Отменить"])
    )

    await state.set_state(ChangeProfile.setting_new_description)

# Установили новое описание
@router.message(ChangeProfile.setting_new_description, F.text)
async def chosen_new_description(message: Message, state: FSMContext):
    await update_user_info(telegram_id=message.from_user.id, bio=message.text)
    await state.update_data(bio=message.text)

    await message.answer("Так выглядит твоя анкета:", reply_markup=ReplyKeyboardRemove())
    await show_profile(message=message)

    await create_menu_keyboard(message=message)

    await state.set_state(ChangeProfile.selects_menu)


# Для описания использовался не текст
@router.message(ChangeProfile.setting_new_description)
async def chosen_new_description_incorrect(message: Message):
    await message.answer(
        text="В описании можно оставить только текст.\n\n"
             "Расскажи о себе и кого ты хочешь найти.",
        reply_markup=create_row_kb(["Отменить"])
    )

#-----------------------------------------#

# Смена имени
@router.message(ChangeProfile.selects_menu, F.text.lower() == "4")
async def chosen_changing_name(message: Message, state: FSMContext):
    await message.answer(
        text="Как тебя зовут?",
        reply_markup=ReplyKeyboardRemove()
    )

    await state.set_state(ChangeProfile.changing_name)

# Установили новое имя
@router.message(ChangeProfile.changing_name, F.text)
async def chosen_new_name(message: Message, state: FSMContext):
    await update_user_info(telegram_id=message.from_user.id, name=message.text)
    await state.update_data(name=message.text)

    await message.answer("Так выглядит твоя анкета:", reply_markup=ReplyKeyboardRemove())
    await show_profile(message=message)
    await create_menu_keyboard(message=message)

    await state.set_state(ChangeProfile.selects_menu)

# Для имени использовался не текст
@router.message(ChangeProfile.changing_name)
async def chosen_new_name_incorrectly(message: Message):
    await message.answer(
        text=f"Напиши свое имя текстом."
    )

#-----------------------------------------#

# Смена целей
@router.message(ChangeProfile.selects_menu, F.text.lower() == "5")
async def chosen_changing_name(message: Message, state: FSMContext):
    await message.answer(
        text="Кого ты ищешь?",
        reply_markup=create_row_kb(["Любовь", "Друзей", "Единомышленников", "Всех!"])
    )

    await state.set_state(ChangeProfile.changing_goals)

# Установили новое имя
@router.message(ChangeProfile.changing_goals, F.text.lower().in_({"любовь", "друзей", "единомышленников", "всех!"}))
async def chosen_new_name(message: Message, state: FSMContext):
    if message.text.lower() == "любовь":
        await state.update_data(sex="love")
        await update_user_info(telegram_id=message.from_user.id, sex="love")
    elif message.text.lower() == "друзей":
        await state.update_data(sex="friend")
        await update_user_info(telegram_id=message.from_user.id, sex="friend")
    elif message.text.lower() == "единомышленников":
        await state.update_data(sex="supporter")
        await update_user_info(telegram_id=message.from_user.id, sex="supporter")
    elif message.text.lower() == "всех!":
        await state.update_data(sex="all")
        await update_user_info(telegram_id=message.from_user.id, sex="all")

    await message.answer("Так выглядит твоя анкета:", reply_markup=ReplyKeyboardRemove())
    await show_profile(message=message)
    await create_menu_keyboard(message=message)

    await state.set_state(ChangeProfile.selects_menu)

# Для имени использовался не текст
@router.message(ChangeProfile.changing_goals)
async def chosen_new_name_incorrectly(message: Message):
    await message.answer(
        text="Выбери кого ты ищешь:",
        reply_markup=create_row_kb(["Любовь", "Друзей", "Единомышленников", "Всех!"])
    )