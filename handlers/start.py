from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database import SessionLocal, User
from config import OWNER_ID, ADMIN_IDS

router = Router()

class RegisterState(StatesGroup):
    wait_tg_nick = State()
    wait_play_nick = State()

# ========== INLINE МЕНЮ ==========
def main_menu_inline(is_admin=False, is_owner=False):
    keyboard = [
        [InlineKeyboardButton(text="📊 Моя статистика", callback_data="my_stats"),
         InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile")],
        [InlineKeyboardButton(text="➕ Создать лот", callback_data="create_lot"),
         InlineKeyboardButton(text="📋 Активные аукционы", callback_data="active_lots")],
        [InlineKeyboardButton(text="📈 Мои лоты", callback_data="my_lots"),
         InlineKeyboardButton(text="🏆 Достижения", callback_data="achievements")],
        [InlineKeyboardButton(text="⭐ Избранное", callback_data="favorites"),
         InlineKeyboardButton(text="🎲 Случайный лот", callback_data="random_lot")],
        [InlineKeyboardButton(text="🔍 Поиск", callback_data="search_lots"),
         InlineKeyboardButton(text="📖 Инструкция", callback_data="instructions")],
        [InlineKeyboardButton(text="🏆 Топ пользователей", callback_data="top_users")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    if is_admin or is_owner:
        keyboard.append([InlineKeyboardButton(text="🛠 Админ-панель", callback_data="admin_panel")])
    
    if is_owner:
        keyboard.append([InlineKeyboardButton(text="👑 Управление админами", callback_data="admin_manage")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

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
            reply_markup=main_menu_inline(is_admin, is_owner)
        )
    else:
        await message.answer(
            "👋 Добро пожаловать в TSUM Auction!\n\n"
            "📌 Введите ваш ник в Telegram (без @):"
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
        session.close()
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
        f"📱 Твой TG: @{data['tg_nick']}",
        reply_markup=main_menu_inline()
    )
    await state.clear()

# ========== ОБРАБОТЧИКИ ОСТАЛЬНЫХ КНОПОК ==========
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
    from handlers.extra_features import show_achievements
    await show_achievements(callback.message)
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

@router.callback_query(F.data == "instructions")
async def instructions_callback(callback: CallbackQuery):
    from handlers.extra_features import show_instructions
    await show_instructions(callback.message)
    await callback.answer()

@router.callback_query(F.data == "top_users")
async def top_users_callback(callback: CallbackQuery):
    from handlers.extra_features import top_users
    await top_users(callback.message)
    await callback.answer()

@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery):
    from handlers.admin import admin_panel
    await admin_panel(callback.message)
    await callback.answer()

@router.callback_query(F.data == "admin_manage")
async def admin_manage_callback(callback: CallbackQuery):
    from handlers.admin import admin_manage
    await admin_manage(callback.message)
    await callback.answer()
# ========== ОСТАЛЬНЫЕ ОБРАБОТЧИКИ ==========
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
    from handlers.extra_features import show_achievements
    await show_achievements(callback.message)
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

@router.callback_query(F.data == "instructions")
async def instructions_callback(callback: CallbackQuery):
    from handlers.extra_features import show_instructions
    await show_instructions(callback.message)
    await callback.answer()

@router.callback_query(F.data == "top_users")
async def top_users_callback(callback: CallbackQuery):
    from handlers.extra_features import top_users
    await top_users(callback.message)
    await callback.answer()
