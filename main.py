import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from config import BOT_TOKEN, OWNER_ID, ADMIN_IDS
from database import SessionLocal, User
from scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ========== РЕГИСТРАЦИЯ ==========
class RegisterState(StatesGroup):
    wait_tg_nick = State()
    wait_play_nick = State()

def main_menu(is_admin=False, is_owner=False):
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

@dp.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=message.from_user.id).first()
    session.close()
    
    if user:
        await message.answer(
            f"👋 С возвращением, {user.play_nick}!",
            reply_markup=main_menu(user.is_admin or user.is_owner, user.is_owner)
        )
    else:
        await message.answer("👋 Введите ваш ник в Telegram (без @):")
        await state.set_state(RegisterState.wait_tg_nick)

@dp.message(RegisterState.wait_tg_nick)
async def reg_tg(message: Message, state: FSMContext):
    if message.text.startswith('@'):
        message.text = message.text[1:]
    await state.update_data(tg_nick=message.text)
    await message.answer("✅ Отлично! Теперь введите ваш ник в TSUM:")
    await state.set_state(RegisterState.wait_play_nick)

@dp.message(RegisterState.wait_play_nick)
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
@dp.message(F.text == "👤 Мой профиль")
async def my_profile(message: Message):
    await message.answer("📝 Твой профиль: скоро тут будет информация!")

@dp.message(F.text == "📊 Моя статистика")
async def my_stats(message: Message):
    await message.answer("📊 Твоя статистика: скоро появится!")

@dp.message(F.text == "➕ Создать лот")
async def create_lot(message: Message):
    await message.answer("➕ Создание лота: пока в разработке!")

@dp.message(F.text == "📋 Активные аукционы")
async def active_lots(message: Message):
    await message.answer("📋 Активных аукционов пока нет.")

@dp.message(F.text == "📈 Мои лоты")
async def my_lots(message: Message):
    await message.answer("📈 У вас пока нет лотов.")

@dp.message(F.text == "🏆 Достижения")
async def achievements(message: Message):
    await message.answer("🏆 Список достижений скоро появится!")

@dp.message(F.text == "⭐ Избранное")
async def favorites(message: Message):
    await message.answer("⭐ У вас пока нет избранных лотов.")

@dp.message(F.text == "🎲 Случайный лот")
async def random_lot(message: Message):
    await message.answer("🎲 Активных лотов пока нет.")

@dp.message(F.text == "🔍 Поиск")
async def search(message: Message):
    await message.answer("🔍 Введите название для поиска:")

@dp.message(F.text == "📖 Инструкция")
async def instructions(message: Message):
    await message.answer("📖 Инструкция по использованию бота:\n1. /start — главное меню\n2. Регистрация\n3. Создавай лоты и участвуй в аукционах!")

@dp.message(F.text == "🏆 Топ пользователей")
async def top_users(message: Message):
    await message.answer("🏆 Топ пользователей появится после первых сделок!")

@dp.message(F.text == "🛠 Админ-панель")
async def admin_panel(message: Message):
    await message.answer("🛠 Админ-панель: только для админов!")

@dp.message(F.text == "👑 Управление админами")
async def admin_manage(message: Message):
    await message.answer("👑 Управление админами: только для владельца!")

# ========== ЗАПУСК ==========
async def main():
    start_scheduler()
    logger.info("🚀 Бот TSUM Auction запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
