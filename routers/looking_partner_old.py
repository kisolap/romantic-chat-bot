from aiogram import Router, F, Bot

from aiogram.fsm.context import FSMContext
from aiogram.filters import Filter
from aiogram.types import ReplyKeyboardRemove, Message

from answer_functions.create_keyboard import create_row_kb, create_menu_keyboard
from db import find_partner, add_viewed_partner, add_like, check_match
from answer_functions.show_profile import show_profile, show_partner_profile

from states import LookingPartner, ChangeProfile

router = Router()

class CorrectEmoji(Filter):
    async def __call__(self, message: Message) -> bool:
        if message.text == "❤️" or message.text == "👎":
            return True
        else:
            return False

# Уведомление партнера о совпадении
async def notify_partner_about_match(partner_id: int, bot: Bot, user_name: str):
    await bot.send_message(
        chat_id=partner_id,
        text=f"🎉 У вас новое совпадение! Начните общение {user_name}")

#-----------------------------------------#

# Переход к режиму "Поиск партнера"
@router.message(F.text.lower() == "1🚀")
@router.message(LookingPartner.after_matches)
async def chosen_looking_partner(message: Message, state: FSMContext):
    await message.answer(
        text="✨🔍",
        reply_markup=create_row_kb(["❤️", "👎", "💤"])
    )

    user_id = message.from_user.id
    partner = find_partner(user_id)

    add_viewed_partner(user_id=user_id, partner_id=partner["telegram_id"])
    await show_partner_profile(message)

    await state.update_data(current_partner_id=partner["telegram_id"])
    await state.update_data(current_partner_username=partner["username"])
    await state.set_state(LookingPartner.looking_partners)

# Режим "Поиска партнера"
@router.message(LookingPartner.looking_partners,
                CorrectEmoji())
async def like_dislike_partner(message: Message, state: FSMContext):
    user_data = await state.get_data()
    user_username = user_data.get("username")
    current_partner_id = user_data.get("current_partner_id")
    current_partner_username = user_data.get("current_partner_username")

    if message.text.lower() == "❤️":
        add_like(user_id=message.from_user.id, partner_id=current_partner_id)

    if check_match(user_id=message.from_user.id, partner_id=current_partner_id):
        await message.answer(
            text=f"Кажется это взаимно! Надеюсь, вы хорошо проведете время :) "
                 f"Начинайте общаться 👉 {current_partner_username}"
        )
        # await notify_partner_about_match(partner_id=current_partner_id, bot=my_bot, user_name=user_username)
        await state.set_state(LookingPartner.after_matches)
    else:
        user_id = message.from_user.id
        partner = find_partner(user_id)

        add_viewed_partner(user_id=user_id, partner_id=partner["telegram_id"])
        await show_partner_profile(message)

        await state.update_data(current_partner_id=partner["telegram_id"])
        await state.update_data(current_partner_username=partner["username"])

        await state.set_state(LookingPartner.looking_partners)

# Меню режима "Поиска партнера"
# (Если отказались от отключения анкеты)
@router.message(LookingPartner.looking_partners, F.text.lower() == "💤")
@router.message(LookingPartner.menu, F.text.lower() == "нет, оставить")
async def stop_looking_partner(message: Message, state: FSMContext):
    await message.answer(
        text="Подождем новых пар!"
    )

    await message.answer(
        text="1. Смотреть анкеты\n"
             "2. Моя анкета\n"
             "3. Отключить анкету",
        reply_markup = create_row_kb(["1🚀", "2", "3"])
    )

    await state.set_state(LookingPartner.menu)

#-----------------------------------------#

# 2. Моя анкета
@router.message(LookingPartner.menu,
                F.text.lower() == "2")
@router.message(LookingPartner.hidden_profile,
                F.text.lower() == "включить анкету")
async def chosen_show_profile(message: Message, state: FSMContext):
    await message.answer(
        text="Так выглядит твоя анкета:",
        reply_markup=ReplyKeyboardRemove()
    )
    await show_profile(message=message, state=state)
    await create_menu_keyboard(message=message)

    await state.set_state(ChangeProfile.selects_menu)

# 3. Отключить анкету
@router.message(LookingPartner.menu,
                F.text.lower() == "3")
async def sure_to_hide_profile(message: Message, state: FSMContext):
    await message.answer(
        text="Если отключишь анкету, то не сможешь искать пары и узнавать, "
             "что кому-то нравишься. Точно хочешь отключить анкету?",
        reply_markup=create_row_kb(["Да, отключить", "Нет, оставить"])
    )

# Отключение анкеты
@router.message(F.text.lower() == "да, отключить")
async def chosen_hide_profile(message: Message, state: FSMContext):
    await message.answer(
        text="Рад был с тобой пообщаться!\n"
             "Если будет скучно пиши, обязательно найдем тебе пару!",
        reply_markup=create_row_kb(["Включить анкету"])
    )
    await state.set_state(LookingPartner.hidden_profile)

