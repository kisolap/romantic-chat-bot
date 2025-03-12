import logging
import os

from db_directory.models import User, Like, ViewedPartner, Photo
from db_directory.database import get_db
from sqlalchemy.future import select
from sqlalchemy import delete
from sqlalchemy.orm import joinedload
from aiogram import Bot

# Получаем всех пользователей из базы данных
async def broadcast_message(bot: Bot, text: str):
    async for session in get_db():
        query = select(User.telegram_id)
        result = await session.execute(query)
        chat_ids = [row[0] for row in result.fetchall()]

        for chat_id in chat_ids:
            try:
                await bot.send_message(chat_id=chat_id, text=text)
            except Exception as e:
                # (например, если пользователь заблокировал бота)
                logging.error(f"Failed to send message to chat_id {chat_id}: {e}")

# Проверка существования пользователя
async def user_exists(telegram_id: int) -> bool:
    async for session in get_db():
        result = await session.execute(select(User).filter(User.telegram_id == telegram_id))
        return result.scalar_one_or_none() is not None

# 🔹 Получение пользователя по Telegram ID (с загрузкой фото)
async def get_user(telegram_id: int) -> User:
    async for session in get_db():
        result = await session.execute(
            select(User)
            .options(joinedload(User.photos))
            .filter(User.telegram_id == telegram_id)
        )
        return result.unique().scalar_one_or_none()

# 🔹 Создание пользователя (без фото)
async def create_user(
    telegram_id: int, telegram_username: str, name: str, age: int, sex: str, preference: str, bio: str, faculty: str
) -> User:
    async for session in get_db():
        new_user = User(
            telegram_id=telegram_id,
            telegram_username=telegram_username,
            name=name,
            age=age,
            sex=sex,
            preference=preference,
            bio=bio,
            faculty=faculty,
            is_active=True
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user


# 🔹 Добавление фото пользователю
async def add_photo(user_id: int, photo_path: str) -> Photo:
    async for session in get_db():
        new_photo = Photo(user_id=user_id, path=photo_path)
        session.add(new_photo)
        await session.commit()
        await session.refresh(new_photo)
        return new_photo

# 🔹 Удаление фото пользователя
async def delete_photo(photo_id: int) -> bool:
    async for session in get_db():
        result = await session.execute(select(Photo).filter(Photo.id == photo_id))
        photo = result.scalar_one_or_none()
        if photo:
            if os.path.exists(photo.path):
                os.remove(photo.path)
            await session.delete(photo)
            await session.commit()
            return True
        return False

async def get_user_photos(user_id: int) -> list[Photo]:
    async for session in get_db():
        result = await session.execute(select(Photo).filter(Photo.user_id == user_id))
        return result.scalars().all()

async def update_user_info(telegram_id: int, name: str = None, bio: str = None, sex: str = None):
    """Обновляет имя и описание пользователя."""
    async for session in get_db():
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalars().first()

        if user:
            if name:
                user.name = name
            if bio:
                user.bio = bio
            if sex:
                user.sex = sex

            await session.commit()
            return user
        return None

async def update_user_photos(telegram_id: int, photo_paths: list[str]):
    """Обновляет фотографии пользователя (заменяет старые)."""
    async for session in get_db():
        result = await session.execute(
            select(User).options(joinedload(User.photos)).where(User.telegram_id == telegram_id))
        user = result.scalars().first()

        if user:
            # Удаляем старые фото
            await session.execute(delete(Photo).where(Photo.user_id == telegram_id))

            # Добавляем новые
            new_photos = [Photo(user_id=telegram_id, path=path) for path in photo_paths]
            session.add_all(new_photos)

            await session.commit()
            return user
        return None


# 🔹 Удаление пользователя (и его фото)
async def delete_user(telegram_id: int) -> bool:
    async for session in get_db():
        result = await session.execute(select(User).filter(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            # Удаляем все фото пользователя
            photos = await session.execute(select(Photo).filter(Photo.user_id == user.id))
            for photo in photos.scalars().all():
                if os.path.exists(photo.path):
                    os.remove(photo.path)
                await session.delete(photo)
            await session.delete(user)
            await session.commit()
            return True
        return False

async def deactivate_user(user_id: int):
    async for session in get_db():
        stmt = select(User).where(User.telegram_id == user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()  # Получаем объект User

        if user:
            user.is_active = False
            await session.commit()

async def activate_user(user_id: int):
    async for session in get_db():
        stmt = select(User).where(User.telegram_id == user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()  # Получаем объект User

        if user:
            user.is_active = True
            await session.commit()
            await session.refresh(user)  # Обновляем объект в сессии
            return user
        return None

# 🔹 Добавление лайка
async def add_like(user_id: int, liked_user_id: int) -> Like:
    async for session in get_db():
        new_like = Like(user_id=user_id, liked_user_id=liked_user_id)
        session.add(new_like)
        await session.commit()
        await session.refresh(new_like)
        return new_like

# 🔹 Получение всех партнеров, лайкнувших пользователя
async def get_likers(user_id: int) -> list[Like] | None:
    """
    Получает список объектов Like, где user_id является получателем лайка.

    :param user_id: ID пользователя, чьи лайкеры нужны
    :param session: Асинхронная сессия БД
    :return: Список объектов Like (те, кто лайкнули user_id)
    """
    async for session in get_db():
        stmt = select(Like).where(Like.liked_user_id == user_id)
        result = await session.execute(stmt)
        likers = result.scalars().all()
        if likers:
            return likers
        if not likers:
            return None

async def delete_like(user_id: int, liked_user_id: int) -> Like:
    """
    Удаляет все лайки, которые user_id поставил liked_user_id.

    :param user_id: ID пользователя, который поставил лайк
    :param liked_user_id: ID пользователя, которому был поставлен лайк
    :return: True, если хотя бы один лайк был удалён, False, если лайков не было
    """
    async for session in get_db():
        stmt = select(Like).where(Like.user_id == user_id, Like.liked_user_id == liked_user_id)
        result = await session.execute(stmt)
        likes = result.scalars().all()  # Получаем все найденные лайки

        if likes:
            for like in likes:
                await session.delete(like)  # Удаляем каждый найденный лайк
            await session.commit()
            return likes[0]


# 🔹 Проверка, лайкал ли пользователь другого
async def is_user_liked(user_id: int, liked_user_id: int) -> bool:
    async for session in get_db():
        result = await session.execute(
            select(Like).filter(Like.user_id == user_id, Like.liked_user_id == liked_user_id)
        )
        return result.scalar_one_or_none() is not None

# 🔹 Добавление просмотренного партнёра
async def add_viewed_partner(user_id: int, partner_id: int) -> ViewedPartner:
    async for session in get_db():
        new_viewed = ViewedPartner(user_id=user_id, partner_id=partner_id)
        session.add(new_viewed)
        await session.commit()
        await session.refresh(new_viewed)
        return new_viewed

# 🔹 Удаление просмотренного партнёра
async def remove_viewed_partner(user_id: int, partner_id: int) -> ViewedPartner | None:
    async for session in get_db():
        stmt = (select(ViewedPartner)
        .where(ViewedPartner.user_id == user_id, ViewedPartner.partner_id == partner_id))
        result = await session.execute(stmt)

        viewed = result.scalars().first()
        # viewed = result.scalar_one_or_none()

        if viewed:
            await session.delete(viewed)
            await session.commit()
            return viewed

# 🔹 Проверка, просматривал ли пользователь другого
async def is_partner_viewed(user_id: int, partner_id: int) -> bool:
    async for session in get_db():
        result = await session.execute(
            select(ViewedPartner).filter(ViewedPartner.user_id == user_id, ViewedPartner.partner_id == partner_id)
        )
        return result.scalar_one_or_none() is not None

# 🔹 Поиск непросмотренного партнера
async def find_unviewed_partner(user_id: int, preference: str) -> User:
    async for session in get_db():
        # Получаем текущего пользователя и его предпочтения
        user = await session.get(User, user_id)

        if user.preference == "both":
            result = await session.execute(
                select(User)
                .filter(
                    User.is_active == True,
                    User.telegram_id != user_id,
                    User.telegram_id.notin_(
                        select(ViewedPartner.partner_id).filter(ViewedPartner.user_id == user_id)
                    ),
                )
                .limit(1)
            )
        else:
            result = await session.execute(
                select(User)
                .filter(
                    User.is_active == True,
                    User.sex == user.preference,
                    User.telegram_id != user_id,
                    User.telegram_id.notin_(
                        select(ViewedPartner.partner_id).filter(ViewedPartner.user_id == user_id)
                    ),
                )
                .limit(1)
            )


        return result.unique().scalar_one_or_none()  # Убираем дубликаты


# 🔹 Проверка, ставил ли партнер лайк пользователю
async def has_partner_liked_back(user_id: int, partner_id: int) -> bool:
    async for session in get_db():
        result = await session.execute(
            select(Like).filter(Like.user_id == partner_id, Like.liked_user_id == user_id)
        )
        return result.scalar_one_or_none() is not None
