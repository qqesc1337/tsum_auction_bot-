from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database import SessionLocal, User
from keyboards.inline import main_menu_keyboard
from config import OWNER_ID, ADMIN_IDS

router = Router()

class RegisterState(StatesGroup):
    wait_tg_nick = State()
    wait_play_nick = State()

@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=message.from_user.id).first()
    
    if user:
        is_admin = user.is_admin or user.is_owner
        is_owner = user.is_owner
        
        welcome_text = f"👋 С возвращением, {user.play_nick}!\n"
        welcome_text += f"⭐ Рейтинг: {user.rating:.1f}\n"
        welcome_text += f"📦 Сделок: {user.deals_count}\n"
        
        if user.is_owner:
            welcome_text += "\n👑 Вы — ВЛАДЕЛЕЦ бота!"
        elif user.is_admin:
            welcome_text += "\n🔑 Вы — АДМИНИСТРАТОР!"
        
        await message.answer(
            welcome_text,
            reply_markup=main_menu_keyboard(is_admin, is_owner)
        )
    else:
        await message.answer(
            "👋 Добро пожаловать в TSUM Auction!\n\n"
            "📌 Для регистрации введите ваш ник в Telegram (без @):"
        )
        await state.set_state(RegisterState.wait_tg_nick)
    
    session.close()

@router.message(RegisterState.wait_tg_nick)
async def reg_tg(message: Message, state: FSMContext):
    if message.text.startswith('@'):
        message.text = message.text[1:]
    await state.update_data(tg_nick=message.text)
    await message.answer("✅ Отлично! Теперь введите ваш ник в TSUM:")
    await state.set_state(RegisterState.wait_play_nick)

@router.message(RegisterState.wait_play_nick)
async def reg_play(message: Message, state: FSMContext):
    data = await state.get_data()
    
    session = SessionLocal()
    
    existing = session.query(User).filter_by(play_nick=message.text).first()
    if existing:
        await message.answer("❌ Этот ник уже занят! Введите другой:")
        return
    
    new_user = User(
        tg_id=message.from_user.id,
        tg_username=data['tg_nick'],
        play_nick=message.text
    )
    
    if message.from_user.id == OWNER_ID:
        new_user.is_owner = True
        new_user.is_admin = True
        await message.answer("👑 Вы зарегистрированы как ВЛАДЕЛЕЦ бота!")
    elif message.from_user.id in ADMIN_IDS:
        new_user.is_admin = True
        await message.answer("🔑 Вы зарегистрированы как АДМИНИСТРАТОР!")
    
    session.add(new_user)
    session.commit()
    session.close()
    
    await message.answer(
        f"✅ Регистрация завершена!\n"
        f"🎮 Твой ник в TSUM: <b>{message.text}</b>\n"
        f"📱 Твой TG: @{data['tg_nick']}\n\n"
        f"Теперь ты можешь создавать лоты и участвовать в аукционах!",
        reply_markup=main_menu_keyboard()
    )
    await state.clear()

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    session.close()
    
    if user:
        is_admin = user.is_admin or user.is_owner
        is_owner = user.is_owner
        await callback.message.edit_text(
            f"👋 Главное меню, {user.play_nick}",
            reply_markup=main_menu_keyboard(is_admin, is_owner)
        )
    await callback.answer()

@router.callback_query(F.data == "my_profile")
async def my_profile_callback(callback: CallbackQuery):
    from handlers.profile import show_my_profile
    await show_my_profile(callback.message)
    await callback.answer()

@router.callback_query(F.data == "create_lot")
async def create_lot_callback(callback: CallbackQuery, state: FSMContext):
    from handlers.auction import create_lot_start
    await create_lot_start(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "active_lots")
async def active_lots_callback(callback: CallbackQuery):
    from handlers.auction import active_auctions
    await active_auctions(callback.message)
    await callback.answer()

@router.callback_query(F.data == "my_lots")
async def my_lots_callback(callback: CallbackQuery):
    from handlers.auction import my_lots
    await my_lots(callback.message)
    await callback.answer()

@router.callback_query(F.data == "achievements")
async def achievements_callback(callback: CallbackQuery):
    from handlers.profile import show_achievements
    await show_achievements(callback.message)
    await callback.answer()

@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery):
    from handlers.admin import admin_panel_message
    await admin_panel_message(callback.message)
    await callback.answer()

@router.callback_query(F.data == "admin_manage")
async def admin_manage_callback(callback: CallbackQuery):
    from handlers.admin_manage import manage_admins
    await manage_admins(callback.message)
    await callback.answer()

@router.callback_query(F.data == "favorites")
async def favorites_callback(callback: CallbackQuery):
    from handlers.extra_features import show_favorites
    await show_favorites(callback.message)
    await callback.answer()

@router.callback_query(F.data == "random_lot")
async def random_lot_callback(callback: CallbackQuery):
    from handlers.extra_features import random_lot
    await random_lot(callback.message)
    await callback.answer()

@router.callback_query(F.data == "search_lots")
async def search_lots_callback(callback: CallbackQuery, state: FSMContext):
    from handlers.extra_features import search_start
    await search_start(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "top_users")
async def top_users_callback(callback: CallbackQuery):
    from handlers.admin import top_users
    await top_users(callback.message)
    await callback.answer()

@router.callback_query(F.data == "instructions")
async def instructions_callback(callback: CallbackQuery):
    from handlers.extra_features import show_instructions
    await show_instructions(callback.message)
    await callback.answer()

@router.callback_query(F.data == "my_stats")
async def my_stats_callback(callback: CallbackQuery):
    from handlers.extra_features import my_stats
    await my_stats(callback.message)
    await callback.answer()
