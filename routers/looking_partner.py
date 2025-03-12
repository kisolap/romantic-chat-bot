from aiogram import Router, F, Bot

from aiogram.fsm.context import FSMContext
from aiogram.filters import Filter
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import ReplyKeyboardRemove, Message

from answer_functions.create_keyboard import create_row_kb, create_menu_keyboard
from answer_functions.show_profile import show_profile, show_partner_profile
from db_directory.crud import find_unviewed_partner, add_viewed_partner, add_like, has_partner_liked_back, get_likers, \
    get_user, delete_like, deactivate_user, activate_user, remove_viewed_partner

from main import my_bot
from redis_storage import storage

from states import LookingPartner, ChangeProfile

router = Router()

class CorrectEmoji(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.text in {"❤️", "👎"}

# Уведомление партнера о совпадении
async def notify_partner_about_match(partner_id: int, user_name: str, bot: Bot):
    if user_name is None:
        await bot.send_message(
            chat_id=partner_id,
            text=f"💘 У вас новое совпадение! Ваш мэтч захотел остаться анонимным, он сам вам напишет ;)"
        )
    else:
        await bot.send_message(
            chat_id=partner_id,
            text=f"💘 У вас новое совпадение! Начните общение c @{user_name}"
        )

# Уведомление партнера о лайке
async def notify_partner_about_like(partner_id: int, bot: Bot, message: Message):
    liked_user_state = FSMContext(storage=storage,
                                  key=StorageKey(bot_id=bot.id,
                                                 chat_id=partner_id,
                                                 user_id=partner_id
                                                 )
                                  )
    liked_user = await liked_user_state.get_data()
    cur_liked_user_state = await liked_user_state.get_state()

    # Обработка случая, когда пользователь уже и так смотрел лайки и пришел еще один
    if cur_liked_user_state == LookingPartner.choosing_show_likes or cur_liked_user_state == LookingPartner.show_likes:
        await add_like(user_id=liked_user.get("current_partner_id"), liked_user_id=partner_id)

    await bot.send_message(
        chat_id=partner_id,
        text=f"💘 Ты кому-то понравился, показать поклонника?\n\n"
             f"(А к анкете выше мы вернемся позже)",
        reply_markup=create_row_kb(["1👍", "2💤"])
    )

    # Удаление из просмотренных анкеты, которую не успели лайкнуть
    await remove_viewed_partner(user_id=partner_id, partner_id=liked_user.get("current_partner_id"))

    await liked_user_state.set_state(LookingPartner.choosing_show_likes)
    await liked_user_state.update_data(current_partner_id=message.from_user.id, current_partner_username=message.from_user.username)

# Переход к просмотру лайкнувшних партнеров
@router.message(LookingPartner.choosing_show_likes, F.text == "1👍")
@router.message(LookingPartner.show_likes, CorrectEmoji())
async def chosen_show_like(message: Message, state: FSMContext):
    if LookingPartner.choosing_show_likes:
        await message.answer(
            text="✨🔍",
            reply_markup=create_row_kb(["❤️", "👎", "💤"])
        )

    user_data = await state.get_data()
    current_partner_id = user_data.get("current_partner_id")
    current_partner_username = user_data.get("current_partner_username")

    if message.text == "❤️":
        await message.answer(
            text=f"💘 Кажется, это взаимно! Надеюсь, вы хорошо проведете время\n"
                 f"Начинайте общаться 👉 @{current_partner_username}"
        )
        await notify_partner_about_match(
            partner_id=current_partner_id,
            user_name=message.from_user.username,
            bot=my_bot
        )

    likers = await get_likers(message.from_user.id)

    if likers is None:
        await message.answer(
            text="Новых лайков пока нет, продолжим?",
            reply_markup=create_row_kb(["🚀Продолжить", "Меню"])
        )
        await state.set_state(LookingPartner.choosing_after_show_likes)
    elif likers:

        like = await delete_like(user_id=likers[0].user_id, liked_user_id=likers[0].liked_user_id)
        partner = await get_user(like.user_id)
        await state.update_data(current_partner_id=partner.telegram_id,
                                current_partner_username=partner.telegram_username)

        if len(likers) == 1:
            await message.answer(
                text=f"💘 Вот новый поклонник:"
            )
        else:
            await message.answer(
                text=f"💘 Вот новый поклонник (и еще {len(likers) - 1}):"
            )

        await show_partner_profile(message=message, partner=partner)
        await add_viewed_partner(user_id=message.from_user.id, partner_id=current_partner_id)

        await state.set_state(LookingPartner.show_likes)


# Переход к режиму "Поиск партнера"
@router.message(F.text.lower() == "1🚀")
@router.message(LookingPartner.after_matches)
@router.message(LookingPartner.choosing_after_show_likes, F.text.lower() == "🚀продолжить")
@router.message(LookingPartner.choosing_show_likes, F.text == "2💤")
async def chosen_looking_partner(message: Message, state: FSMContext):
    await message.answer(
        text="✨🔍",
        reply_markup=create_row_kb(["❤️", "👎", "💤"])
    )

    user = await get_user(message.from_user.id)
    partner = await find_unviewed_partner(user_id=user.telegram_id, preference=user.preference)

    if not partner:
        await message.answer(
            text="Пока нет доступных анкет. Попробуй позже!",
            reply_markup=create_row_kb(["Меню"])
        )
        await state.set_state(LookingPartner.menu)
    elif partner:
        await add_viewed_partner(user_id=user.telegram_id, partner_id=partner.telegram_id)

        await show_partner_profile(message, partner)
        await state.update_data(current_partner_id=partner.telegram_id,
                                current_partner_username=partner.telegram_username)

        await state.set_state(LookingPartner.looking_partners)

# Режим "Поиска партнера"
@router.message(LookingPartner.looking_partners, CorrectEmoji())
async def like_dislike_partner(message: Message, state: FSMContext):
    user_data = await state.get_data()
    current_partner_id = user_data.get("current_partner_id")
    current_partner_username = user_data.get("current_partner_username")

    if message.text == "❤️":
        if await has_partner_liked_back(user_id=message.from_user.id, partner_id=current_partner_id):
            await message.answer(
                text=f"💘 Кажется, это взаимно! Надеюсь, вы хорошо проведете время\n"
                     f"Начинайте общаться 👉 @{current_partner_username}"
            )
            await notify_partner_about_match(
                partner_id=current_partner_id,
                user_name=message.from_user.username,
                bot=my_bot
            )
            await state.set_state(LookingPartner.after_matches)
            await state.update_data(current_partner_id=None, current_partner_username=None)
        else:
            await add_like(user_id=message.from_user.id, liked_user_id=current_partner_id)
            await notify_partner_about_like(partner_id=current_partner_id, bot=my_bot, message=message)
            await state.update_data(current_partner_id=None, current_partner_username=None)

    user = await get_user(message.from_user.id)
    partner = await find_unviewed_partner(user_id=user.telegram_id, preference=user.preference)

    if not partner:
        await message.answer(
            text="Пока нет доступных анкет. Попробуй позже!",
            reply_markup=create_row_kb(["Меню"])
        )
        await state.set_state(LookingPartner.menu)
    elif partner:
        await add_viewed_partner(user_id=user.telegram_id, partner_id=partner.telegram_id)
        await show_partner_profile(message, partner)

        await state.update_data(current_partner_id=partner.telegram_id,
                                current_partner_username=partner.telegram_username)

# Меню режима "Поиска партнера"
@router.message(LookingPartner.looking_partners, F.text.lower() == "💤")
@router.message(LookingPartner.menu, F.text.lower() == "нет, оставить")
@router.message(F.text.lower() == "меню")
async def stop_looking_partner(message: Message, state: FSMContext):
    # Ушли в сонный режим, возврат последней просмотренней анкеты
    if (message.text == "💤"):
        user = await state.get_data()
        await remove_viewed_partner(user_id=message.from_user.id, partner_id=user.get("current_partner_id"))

    await message.answer("Подождем новых пар!")
    await message.answer(
        text="1. Смотреть анкеты\n"
             "2. Моя анкета\n"
             "3. Отключить анкету",
        reply_markup=create_row_kb(["1🚀", "2", "3"])
    )
    await state.set_state(LookingPartner.menu)

# 2. Моя анкета
@router.message(LookingPartner.menu, F.text.lower() == "2")
@router.message(LookingPartner.hidden_profile, F.text.lower() == "включить анкету")
async def chosen_show_profile(message: Message, state: FSMContext):
    await activate_user(user_id=message.from_user.id)
    await message.answer("Так выглядит твоя анкета:", reply_markup=ReplyKeyboardRemove())
    await show_profile(message=message)
    await create_menu_keyboard(message=message)
    await state.set_state(ChangeProfile.selects_menu)

# 3. Отключить анкету
@router.message(LookingPartner.menu, F.text.lower() == "3")
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
             "Если будет скучно, пиши, обязательно найдем тебе пару!",
        reply_markup=create_row_kb(["Включить анкету"])
    )
    await deactivate_user(user_id=message.from_user.id)
    await state.set_state(LookingPartner.hidden_profile)
