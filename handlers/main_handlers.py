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

# ========== МЕНЮ ==========
def main_menu():
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

# ========== СТАРТ ==========
@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=message.from_user.id).first()
    
    if user:
        await message.answer(
            f"👋 С возвращением, {user.play_nick}!",
            reply_markup=main_menu()
        )
    else:
        await message.answer("👋 Введите ваш ник в Telegram (без @):")
        await state.set_state(RegisterState.wait_tg_nick)
    
    session.close()

# ========== РЕГИСТРАЦИЯ ==========
@router.message(RegisterState.wait_tg_nick)
async def reg_tg(message: Message, state: FSMContext):
    if message.text.startswith('@'):
        message.text = message.text[1:]
    await state.update_data(tg_nick=message.text)
    await message.answer("✅ Теперь введите ваш ник в TSUM:")
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
        f"✅ Регистрация завершена!",
        reply_markup=main_menu()
    )
    await state.clear()

# ========== ЗАГЛУШКИ ДЛЯ КНОПОК ==========
@router.callback_query(F.data == "my_stats")
async def my_stats_callback(callback: CallbackQuery):
    await callback.message.answer("📊 Статистика появится после сделок!")
    await callback.answer()

@router.callback_query(F.data == "my_profile")
async def my_profile_callback(callback: CallbackQuery):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    session.close()
    
    if user:
        await callback.message.answer(f"👤 Твой профиль:\n🎮 TSUM: {user.play_nick}\n📱 TG: @{user.tg_username}\n⭐ Рейтинг: {user.rating}")
    else:
        await callback.message.answer("❌ Ты не зарегистрирован!")
    await callback.answer()

@router.callback_query(F.data == "create_lot")
async def create_lot_callback(callback: CallbackQuery):
    await callback.message.answer("➕ Создание лота: скоро будет!")
    await callback.answer()

@router.callback_query(F.data == "active_lots")
async def active_lots_callback(callback: CallbackQuery):
    await callback.message.answer("📋 Активных аукционов пока нет.")
    await callback.answer()

@router.callback_query(F.data == "my_lots")
async def my_lots_callback(callback: CallbackQuery):
    await callback.message.answer("📈 У вас пока нет лотов.")
    await callback.answer()

@router.callback_query(F.data == "achievements")
async def achievements_callback(callback: CallbackQuery):
    await callback.message.answer("🏆 Список достижений скоро появится!")
    await callback.answer()

@router.callback_query(F.data == "favorites")
async def favorites_callback(callback: CallbackQuery):
    await callback.message.answer("⭐ У вас пока нет избранных лотов.")
    await callback.answer()

@router.callback_query(F.data == "random_lot")
async def random_lot_callback(callback: CallbackQuery):
    await callback.message.answer("🎲 Активных лотов пока нет.")
    await callback.answer()

@router.callback_query(F.data == "search_lots")
async def search_lots_callback(callback: CallbackQuery):
    await callback.message.answer("🔍 Введите название для поиска:")
    await callback.answer()

@router.callback_query(F.data == "instructions")
async def instructions_callback(callback: CallbackQuery):
    text = "📖 TSUM AUCTION:\n1. /start — главное меню\n2. Регистрация\n3. Создавай лоты и торгуй!"
    await callback.message.answer(text)
    await callback.answer()

@router.callback_query(F.data == "top_users")
async def top_users_callback(callback: CallbackQuery):
    await callback.message.answer("🏆 Топ пользователей появится после сделок!")
    await callback.answer()
