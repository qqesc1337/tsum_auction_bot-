from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database import SessionLocal, User
from config import OWNER_ID

router = Router()

class AddAdminState(StatesGroup):
    user_id = State()

@router.callback_query(F.data == "admin_manage")
async def manage_admins(callback: CallbackQuery):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    session.close()
    
    if not user or not user.is_owner:
        await callback.answer("⛔ Только владелец бота может управлять администраторами!", show_alert=True)
        return
    
    session = SessionLocal()
    admins = session.query(User).filter_by(is_admin=True).all()
    session.close()
    
    text = "👑 <b>Управление администраторами</b>\n\n"
    
    if admins:
        text += "📋 Текущие администраторы:\n"
        for admin in admins:
            owner_tag = " 👑 ВЛАДЕЛЕЦ" if admin.is_owner else ""
            text += (
                f"• <b>{admin.play_nick}</b>\n"
                f"  🎮 TSUM | 📱 @{admin.tg_username}\n"
                f"  🆔 {admin.tg_id}{owner_tag}\n\n"
            )
    else:
        text += "📭 Администраторов нет\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить админа", callback_data="add_admin")],
        [InlineKeyboardButton(text="➖ Удалить админа", callback_data="remove_admin")],
        [InlineKeyboardButton(text="📋 Список всех пользователей", callback_data="list_users")],
        [InlineKeyboardButton(text="↩️ Назад в админ-панель", callback_data="back_to_admin")]
    ])
    
    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "add_admin")
async def add_admin_start(callback: CallbackQuery, state: FSMContext):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    session.close()
    
    if not user or not user.is_owner:
        await callback.answer("⛔ Только владелец может добавлять админов!", show_alert=True)
        return
    
    await callback.message.answer(
        "✏️ Введите Telegram ID пользователя, которого хотите сделать администратором:\n\n"
        "📌 Как узнать ID:\n"
        "1. Попросите пользователя написать /id в боте\n"
        "2. Или найдите его в списке /list_users"
    )
    await state.set_state(AddAdminState.user_id)
    await callback.answer()

@router.message(AddAdminState.user_id)
async def add_admin_process(message: Message, state: FSMContext):
    session = SessionLocal()
    owner = session.query(User).filter_by(tg_id=message.from_user.id).first()
    
    if not owner or not owner.is_owner:
        await message.answer("⛔ Доступ запрещен!")
        session.close()
        await state.clear()
        return
    
    try:
        user_id = int(message.text.strip())
        user = session.query(User).filter_by(tg_id=user_id).first()
        
        if not user:
            await message.answer(
                f"❌ Пользователь с ID {user_id} не найден.\n"
                f"Убедитесь, что он зарегистрирован в боте (/start)"
            )
            session.close()
            await state.clear()
            return
        
        if user.is_admin:
            await message.answer(f"❌ {user.play_nick} уже администратор!")
            session.close()
            await state.clear()
            return
        
        if user.is_owner:
            await message.answer(f"❌ {user.play_nick} является владельцем!")
            session.close()
            await state.clear()
            return
        
        user.is_admin = True
        session.commit()
        
        await message.answer(
            f"✅ {user.play_nick} (@{user.tg_username}) назначен администратором!"
        )
        
        try:
            await message.bot.send_message(
                user.tg_id,
                "🎉 Вы назначены администратором TSUM Auction!\n"
                "Теперь вам доступна админ-панель."
            )
        except:
            pass
        
    except ValueError:
        await message.answer("❌ Введите корректный числовой ID!")
    
    session.close()
    await state.clear()

@router.callback_query(F.data == "remove_admin")
async def remove_admin_start(callback: CallbackQuery):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    session.close()
    
    if not user or not user.is_owner:
        await callback.answer("⛔ Только владелец может удалять админов!", show_alert=True)
        return
    
    session = SessionLocal()
    admins = session.query(User).filter_by(is_admin=True).all()
    session.close()
    
    if not admins:
        await callback.message.answer("📭 Нет администраторов для удаления.")
        await callback.answer()
        return
    
    keyboard_buttons = []
    for admin in admins:
        if admin.is_owner:
            continue
        keyboard_buttons.append([InlineKeyboardButton(
            text=f"❌ {admin.play_nick} (@{admin.tg_username})",
            callback_data=f"remove_admin_confirm_{admin.tg_id}"
        )])
    
    keyboard_buttons.append([InlineKeyboardButton(text="↩️ Назад", callback_data="admin_manage")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.answer(
        "👆 Выберите администратора для удаления:",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data.startswith("remove_admin_confirm_"))
async def remove_admin_confirm(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[3])
    
    session = SessionLocal()
    owner = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    
    if not owner or not owner.is_owner:
        await callback.answer("⛔ Доступ запрещен!", show_alert=True)
        session.close()
        return
    
    user = session.query(User).filter_by(tg_id=user_id).first()
    
    if not user:
        await callback.answer("❌ Пользователь не найден")
        session.close()
        return
    
    if user.is_owner:
        await callback.answer("❌ Нельзя удалить владельца!", show_alert=True)
        session.close()
        return
    
    user.is_admin = False
    session.commit()
    session.close()
    
    await callback.message.answer(
        f"✅ {user.play_nick} лишен прав администратора!"
    )
    
    try:
        await callback.bot.send_message(
            user.tg_id,
            "⛔ Вы лишены прав администратора TSUM Auction."
        )
    except:
        pass
    
    await callback.answer()

@router.callback_query(F.data == "list_users")
async def list_users(callback: CallbackQuery):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    
    if not user or not user.is_owner:
        await callback.answer("⛔ Доступ запрещен!", show_alert=True)
        session.close()
        return
    
    users = session.query(User).order_by(User.registration_date.desc()).limit(20).all()
    session.close()
    
    if not users:
        await callback.message.answer("📭 Нет пользователей.")
        await callback.answer()
        return
    
    text = "📋 <b>Последние 20 пользователей:</b>\n\n"
    for i, u in enumerate(users, 1):
        status = "👑" if u.is_owner else "🔑" if u.is_admin else "👤"
        scam = "🚫" if u.is_scammer else ""
        ban = "⛔" if u.is_banned else ""
        text += f"{i}. {status} {u.play_nick} (@{u.tg_username}) [ID: {u.tg_id}] {scam}{ban}\n"
    
    await callback.message.answer(text)
    await callback.answer()

@router.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery):
    from handlers.admin import admin_panel_message
    await admin_panel_message(callback.message)
    await callback.answer()

@router.message(F.text == "/id")
async def show_user_id(message: Message):
    await message.answer(
        f"🆔 Ваш Telegram ID: <code>{message.from_user.id}</code>\n\n"
        f"📌 Скопируйте этот ID для передачи владельцу бота."
    )

@router.message(F.text == "/admins")
async def list_admins_command(message: Message):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=message.from_user.id).first()
    
    if not user or not user.is_owner:
        await message.answer("⛔ Только владелец может смотреть список админов!")
        session.close()
        return
    
    admins = session.query(User).filter_by(is_admin=True).all()
    session.close()
    
    if not admins:
        await message.answer("📭 Администраторов нет.")
        return
    
    text = "👑 Список администраторов:\n\n"
    for admin in admins:
        owner_tag = " (ВЛАДЕЛЕЦ)" if admin.is_owner else ""
        text += f"• {admin.play_nick} (@{admin.tg_username}) [ID: {admin.tg_id}]{owner_tag}\n"
    
    await message.answer(text)
