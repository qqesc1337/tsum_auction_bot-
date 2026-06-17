from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database import SessionLocal, User
from config import OWNER_ID, ADMIN_IDS

router = Router()

class RegisterState(StatesGroup):
    wait_tg_nick = State()
    wait_play_nick = State()

# ========== ГЛАВНОЕ МЕНЮ (Reply кнопки) ==========
def get_main_keyboard(is_admin=False, is_owner=False):
    """Обычные Reply кнопки (видны в поле ввода)"""
    keyboard = [
        [KeyboardButton(text="📊 Моя статистика"), KeyboardButton(text="👤 Мой профиль")],
        [KeyboardButton(text="➕ Создать лот"), KeyboardButton(text="📋 Активные аукционы")],
        [KeyboardButton(text="📈 Мои лоты"), KeyboardButton(text="🏆 Достижения")],
        [KeyboardButton(text="⭐ Избранное"), KeyboardButton(text="🎲 Случайный лот")],
        [KeyboardButton(text="🔍 Поиск"), KeyboardButton(text="📖 Инструкция")],
        [KeyboardButton(text="🏆 Топ пользователей")]
    ]
    
    if is_admin or is_owner:
        keyboard.append([KeyboardButton(text="🛠 Админ-панель")])
    
    if is_owner:
        keyboard.append([KeyboardButton(text="👑 Управление админами")])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

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
            reply_markup=get_main_keyboard(is_admin, is_owner)
        )
    else:
        await message.answer(
            "👋 Добро пожаловать в TSUM Auction!\n\n"
            "📌 Для регистрации введите ваш ник в Telegram (без @):"
        )
        await state.set_state(RegisterState.wait_tg_nick)
    
    session.close()

# ========== РЕГИСТРАЦИЯ ==========
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
        reply_markup=get_main_keyboard()
    )
    await state.clear()
