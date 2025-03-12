from typing import List
from sqlalchemy import String, Boolean, ForeignKey, BigInteger, Integer
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship
)

class Base(DeclarativeBase):
    pass

# Модель пользователя
class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, unique=True, index=True)
    telegram_username: Mapped[str] = mapped_column(String(256), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    sex: Mapped[str] = mapped_column(nullable=False)
    preference: Mapped[str] = mapped_column(nullable=False)
    faculty: Mapped[str] = mapped_column(String(256))
    bio: Mapped[str] = mapped_column(String(1000), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Связь с фото (один ко многим)
    photos: Mapped[List["Photo"]] = relationship("Photo", back_populates="user", cascade="all, delete-orphan")

    likes: Mapped[List["Like"]] = relationship("Like", back_populates="user", foreign_keys="[Like.user_id]")
    received_likes: Mapped[List["Like"]] = relationship("Like", back_populates="liked_user", foreign_keys="[Like.liked_user_id]")

    viewed_partners: Mapped[List["ViewedPartner"]] = relationship("ViewedPartner", back_populates="user", foreign_keys="[ViewedPartner.user_id]")
    viewed_by: Mapped[List["ViewedPartner"]] = relationship("ViewedPartner", back_populates="partner", foreign_keys="[ViewedPartner.partner_id]")

# Модель фото
class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    path: Mapped[str] = mapped_column(String(512), nullable=False)  # Увеличенный размер пути

    user: Mapped["User"] = relationship("User", back_populates="photos")

# Модель лайков
class Like(Base):
    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    liked_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="likes", foreign_keys=[user_id])
    liked_user: Mapped["User"] = relationship("User", back_populates="received_likes", foreign_keys=[liked_user_id])

# Модель просмотренных партнеров
class ViewedPartner(Base):
    __tablename__ = "viewed_partners"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    partner_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="viewed_partners", foreign_keys=[user_id])
    partner: Mapped["User"] = relationship("User", back_populates="viewed_by", foreign_keys=[partner_id])
