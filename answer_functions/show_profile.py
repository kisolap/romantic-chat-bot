from aiogram.types import Message
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.types import FSInputFile

from db_directory.crud import get_user_photos, get_user

# -- Показать профиль --
async def show_profile(message: Message):
    user = await get_user(message.from_user.id)

    text = "Отношения, дружба, совместное творчество"

    if user.sex == "love":
        text = "Отношения"
    elif user.sex == "friend":
        text = "Дружба"
    elif user.sex == "supporter":
        text = "Совместное творчество"

    profile_text = (
        f"{user.name}, {user.age}\n\n"
        f"🎯: {text}\n\n"
        f"🎭: {user.faculty}\n\n"
    )

    # Если нет био и фоток
    if (not user.photos or len(user.photos) == 0) and not user.bio:
        await message.answer(text=profile_text)

    # Если есть только био (нет фото)
    elif not user.photos or len(user.photos) == 0:
        await message.answer(text=f"{profile_text}{user.bio}")

    # Если есть только фото (нет био)
    elif not user.bio:
        profile_builder = MediaGroupBuilder(caption=profile_text)
        for photo in user.photos:
            photo_path = photo.path
            profile_builder.add_photo(FSInputFile(photo_path))
        await message.answer_media_group(media=profile_builder.build())

    # Если есть и фото, и био
    else:
        profile_builder = MediaGroupBuilder(caption=f"{profile_text}{user.bio}")
        for photo in user.photos:
            photo_path = photo.path
            profile_builder.add_photo(FSInputFile(photo_path))
        await message.answer_media_group(media=profile_builder.build())

    # if (user.photos is None or len(user.photos) == 0) and user.bio is None:
    #     await message.answer(
    #         text=f"{user.name}, {user.age}\n\n"
    #              f"🎯: {text}\n\n"
    #              f"🎭: {user.faculty}\n\n"
    #     )
    # else:
    #     profile_builder = MediaGroupBuilder(
    #         caption=f"{user.name}, {user.age}\n\n"
    #                 f"🎯: {text}\n\n"
    #                 f"🎭: {user.faculty}\n\n"
    #                 f"{user.bio}"
    #     )
    #
    #     for photo in user.photos:
    #         photo_path = photo.path
    #         profile_builder.add_photo(FSInputFile(photo_path))
    #
    #     await message.answer_media_group(media=profile_builder.build())

# -- Показать профиль партнера --
async def show_partner_profile(message: Message, partner):
    photos = await get_user_photos(partner.telegram_id)

    text = "Отношения, дружба, совместное творчество"

    if partner.sex == "love":
        text = "Отношения"
    elif partner.sex == "friend":
        text = "Дружба"
    elif partner.sex == "supporter":
        text = "Совместное творчество"

    profile_text = (
        f"{partner.name}, {partner.age}\n"
        f"🎯: {text}\n\n"
        f"🎭: {partner.faculty}\n\n"
    )

    # Если нет фото
    if not photos or len(photos) == 0:
        bio_text = partner.bio if partner.bio else ""
        await message.answer(text=f"{profile_text}{bio_text}")
    # Если есть фото
    else:
        caption = profile_text + (partner.bio if partner.bio else "")

        partner_profile_builder = MediaGroupBuilder(caption=caption)
        for photo in photos:
                partner_profile_builder.add_photo(FSInputFile(photo.path))

        await message.answer_media_group(media=partner_profile_builder.build())

    # if photos is None or len(photos) == 0:
    #     await message.answer(
    #         text=f"{partner.name}, {partner.age}\n"
    #              f"🎯: {text}\n\n"
    #              f"🎭: {partner.faculty}\n\n"
    #              f"{partner.bio}\n"
    #     )
    # else:
    #     partner_profile_builder = MediaGroupBuilder(
    #         caption=f"{partner.name}, {partner.age}\n"
    #                 f"🎯: {text}\n\n"
    #                 f"🎭: {partner.faculty}\n\n"
    #                 f"{partner.bio}\n"
    #     )
    #
    #     for photo in photos:
    #         partner_profile_builder.add_photo(FSInputFile(photo.path))
    #
    #     await message.answer_media_group(media=partner_profile_builder.build())
