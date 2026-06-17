from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime
from database import SessionLocal, User, Lot, Favorite, BlackList, Achievement
import random

router = Router()

class SearchState(StatesGroup):
    query = State()

# ========== ИЗБРАННОЕ ==========
@router.callback_query(F.data == "favorites")
async def favorites_callback(callback: CallbackQuery):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    
    if not user:
        await callback.message.answer("❌ Сначала зарегистрируйтесь /start")
        await callback.answer()
        return
    
    favorites = session.query(Favorite).filter_by(user_id=user.tg_id).all()
    
    if not favorites:
        await callback.message.answer("⭐ У вас нет избранных лотов.")
        session.close()
        await callback.answer()
        return
    
    text = "⭐ <b>Ваши избранные лоты:</b>\n\n"
    for fav in favorites[:10]:
        lot = session.query(Lot).filter_by(id=fav.lot_id).first()
        if lot and lot.is_active:
            time_left = lot.end_time - datetime.utcnow()
            minutes = int(time_left.total_seconds() / 60)
            text += f"• {lot.title} — {lot.current_price:,.0f}$ (⏳ {minutes} мин.)\n"
    
    await callback.message.answer(text)
    session.close()
    await callback.answer()

# ========== СЛУЧАЙНЫЙ ЛОТ ==========
@router.callback_query(F.data == "random_lot")
async def random_lot_callback(callback: CallbackQuery):
    session = SessionLocal()
    lots = session.query(Lot).filter_by(is_active=True).all()
    session.close()
    
    if not lots:
        await callback.message.answer("📭 Активных лотов нет.")
        await callback.answer()
        return
    
    lot = random.choice(lots)
    await callback.message.answer(
        f"🎲 <b>Случайный лот!</b>\n\n"
        f"📌 {lot.title}\n"
        f"💰 Текущая цена: {lot.current_price:,.0f}$\n"
        f"⏰ Завершится: {lot.end_time.strftime('%d.%m.%Y %H:%M')}"
    )
    await callback.answer()

# ========== ПОИСК ==========
@router.callback_query(F.data == "search_lots")
async def search_start_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🔍 Введите название лота для поиска:")
    await state.set_state(SearchState.query)
    await callback.answer()

@router.message(SearchState.query)
async def search_process(message: Message, state: FSMContext):
    query = message.text.lower()
    session = SessionLocal()
    
    lots = session.query(Lot).filter(
        Lot.is_active == True,
        Lot.title.ilike(f"%{query}%")
    ).limit(10).all()
    
    session.close()
    
    if not lots:
        await message.answer(f"🔍 По запросу «{query}» ничего не найдено.")
        await state.clear()
        return
    
    text = f"🔍 Результаты по запросу «{query}»:\n\n"
    for lot in lots[:10]:
        time_left = lot.end_time - datetime.utcnow()
        minutes = int(time_left.total_seconds() / 60)
        text += f"• {lot.title} — {lot.current_price:,.0f}$ (⏳ {minutes} мин.)\n"
    
    await message.answer(text)
    await state.clear()

# ========== ИНСТРУКЦИЯ ==========
@router.callback_query(F.data == "instructions")
async def instructions_callback(callback: CallbackQuery):
    text = """
📖 <b>ИНСТРУКЦИЯ ПО TSUM AUCTION</b>

<b>1️⃣ Регистрация</b>
• Напиши /start
• Введи свой ник в Telegram и ник в TSUM

<b>2️⃣ Создание лота</b>
• Нажми "➕ Создать лот"
• Заполни: название, описание, фото, цену, время

<b>3️⃣ Участие в аукционе</b>
• Найди лот в "📋 Активные аукционы"
• Нажми "💰 Сделать ставку"
• Выбери сумму или введи свою

<b>4️⃣ Профиль</b>
• "👤 Мой профиль" — вся информация о тебе
• "📊 Моя статистика" — детальная аналитика

<b>5️⃣ Достижения</b>
• Получай за количество сделок
• От новичка до абсолютного чемпиона!

<b>6️⃣ Избранное</b>
• Добавляй понравившиеся лоты в ⭐

<b>7️⃣ Отзывы</b>
• Оценивай продавцов после сделок

<b>8️⃣ Сделки</b>
• После завершения аукциона бот присылает ник продавца/покупателя
• Свяжитесь в игре TSUM или Telegram

<i>Удачных торгов в TSUM! 🍀</i>
    """
    await callback.message.answer(text)
    await callback.answer()

# ========== ТОП ПОЛЬЗОВАТЕЛЕЙ ==========
@router.callback_query(F.data == "top_users")
async def top_users_callback(callback: CallbackQuery):
    session = SessionLocal()
    users = session.query(User).order_by(User.deals_count.desc()).limit(10).all()
    session.close()
    
    if not users:
        await callback.message.answer("📭 Нет пользователей.")
        await callback.answer()
        return
    
    text = "🏆 <b>Топ пользователей по сделкам</b>\n\n"
    medals = ["🥇", "🥈", "🥉"]
    
    for i, user in enumerate(users):
        medal = medals[i] if i < 3 else f"{i+1}."
        scam = " 🚫" if user.is_scammer else ""
        text += f"{medal} <b>{user.play_nick}</b> — {user.deals_count} сделок (⭐{user.rating:.1f}){scam}\n"
    
    await callback.message.answer(text)
    await callback.answer()

# ========== ДОСТИЖЕНИЯ ==========
@router.callback_query(F.data == "achievements")
async def achievements_callback(callback: CallbackQuery):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    achievements = session.query(Achievement).order_by(Achievement.min_deals).all()
    session.close()
    
    text = "🏆 <b>Система достижений</b>\n\n"
    for ach in achievements:
        if user and user.deals_count >= ach.min_deals:
            status = "✅"
        else:
            status = "🔒"
        text += f"{status} {ach.icon} <b>{ach.name}</b>\n"
        text += f"   {ach.description}\n"
        if ach.min_deals == 0:
            text += f"   (доступно сразу)\n"
        else:
            text += f"   (нужно {ach.min_deals} сделок)\n"
        text += "\n"
    
    await callback.message.answer(text)
    await callback.answer()

# ========== АКТИВНЫЕ АУКЦИОНЫ (заглушка, основная логика в auction.py) ==========
@router.callback_query(F.data == "active_lots")
async def active_lots_callback(callback: CallbackQuery):
    from handlers.auction import active_auctions
    await active_auctions(callback.message)
    await callback.answer()

# ========== МОИ ЛОТЫ (заглушка) ==========
@router.callback_query(F.data == "my_lots")
async def my_lots_callback(callback: CallbackQuery):
    from handlers.auction import my_lots
    await my_lots(callback.message)
    await callback.answer()
