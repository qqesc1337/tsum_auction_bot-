from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import SessionLocal, User, Report

router = Router()

# ========== АДМИН-ПАНЕЛЬ (обработчик для кнопки) ==========
@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    session.close()
    
    if not user:
        await callback.message.answer("❌ Сначала зарегистрируйтесь /start")
        await callback.answer()
        return
    
    if not (user.is_admin or user.is_owner):
        await callback.message.answer("⛔ У вас нет прав администратора!")
        await callback.answer()
        return
    
    text = f"⚡ <b>Админ-панель</b>\n\n"
    text += f"👤 Вы: {user.play_nick}\n"
    text += f"🔑 Статус: {'Владелец' if user.is_owner else 'Администратор'}\n\n"
    text += f"📌 Доступные команды:\n"
    text += f"/ban [ID] — забанить пользователя\n"
    text += f"/unban [ID] — разбанить\n"
    text += f"/scam [ID] — метка СКАМ\n"
    text += f"/unscam [ID] — снять метку\n"
    text += f"/stats — статистика бота"
    
    await callback.message.answer(text)
    await callback.answer()

# ========== УПРАВЛЕНИЕ АДМИНАМИ ==========
@router.callback_query(F.data == "admin_manage")
async def admin_manage_callback(callback: CallbackQuery):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    session.close()
    
    if not user:
        await callback.message.answer("❌ Сначала зарегистрируйтесь /start")
        await callback.answer()
        return
    
    if not user.is_owner:
        await callback.message.answer("⛔ Только владелец бота может управлять администраторами!")
        await callback.answer()
        return
    
    text = f"👑 <b>Управление администраторами</b>\n\n"
    text += f"Чтобы добавить админа:\n"
    text += f"1. Попроси пользователя написать /id\n"
    text += f"2. Введи /add_admin [ID]\n\n"
    text += f"Чтобы удалить админа:\n"
    text += f"/remove_admin [ID]"
    
    await callback.message.answer(text)
    await callback.answer()
