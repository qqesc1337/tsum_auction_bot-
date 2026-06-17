from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import SessionLocal, User, Report

router = Router()

async def admin_panel(message: Message):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=message.from_user.id).first()
    session.close()
    
    if not user or not (user.is_admin or user.is_owner):
        await message.answer("⛔ У вас нет прав администратора!")
        return
    
    await message.answer(
        f"⚡ <b>Админ-панель</b>\n\n"
        f"👤 Вы: {user.play_nick}\n"
        f"🔑 Статус: {'Владелец' if user.is_owner else 'Администратор'}\n\n"
        f"Доступные команды:\n"
        f"/ban [ID] — забанить пользователя\n"
        f"/unban [ID] — разбанить\n"
        f"/scam [ID] — метка СКАМ\n"
        f"/unscam [ID] — снять метку\n"
        f"/stats — статистика бота"
    )

async def admin_manage(message: Message):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=message.from_user.id).first()
    session.close()
    
    if not user or not user.is_owner:
        await message.answer("⛔ Только владелец бота может управлять администраторами!")
        return
    
    await message.answer(
        "👑 <b>Управление администраторами</b>\n\n"
        "Чтобы добавить админа:\n"
        "1. Попроси пользователя написать /id\n"
        "2. Введи /add_admin [ID]\n\n"
        "Чтобы удалить админа:\n"
        "/remove_admin [ID]"
    )
