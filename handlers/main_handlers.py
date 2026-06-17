from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database import SessionLocal, User, Review, Achievement, Lot, Favorite
from config import OWNER_ID, ADMIN_IDS
from datetime import datetime
import random

router = Router()

class RegisterState(StatesGroup):
    wait_tg_nick = State()
    wait_play_nick = State()

class CreateLotState(StatesGroup):
    title = State()
    description = State()
    photo = State()
    start_price = State()
    duration = State()

class SearchState(StatesGroup):
    query = State()

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

# ========== ПРОФИЛЬ ==========
@router.callback_query(F.data == "my_profile")
async def my_profile_callback(callback: CallbackQuery):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    
    if not user:
        await callback.message.edit_text("❌ Сначала зарегистрируйтесь /start")
        await callback.answer()
        session.close()
        return
    
    achievement = session.query(Achievement).filter(
        Achievement.min_deals <= user.deals_count
    ).order_by(Achievement.min_deals.desc()).first()
    
    reviews = session.query(Review).filter_by(target_id=user.tg_id).all()
    avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 5.0
    user.rating = avg_rating
    session.commit()
    
    scam_label = "🚫 СКАМЕР" if user.is_scammer else "✅ Проверен"
    ban_label = "⛔ ЗАБАНЕН" if user.is_banned else "🟢 Активен"
    
    text = f"👤 <b>Твой профиль</b>\n\n"
    text += f"🎮 TSUM: <b>{user.play_nick}</b>\n"
    text += f"📱 TG: @{user.tg_username}\n"
    text += f"⭐ Рейтинг: {user.rating:.1f} (отзывов: {len(reviews)})\n"
    text += f"📦 Сделок: {user.deals_count}\n"
    text += f"🏆 Достижение: {achievement.icon} {achievement.name if achievement else 'Нет'}\n"
    text += f"📊 Статус: {ban_label}\n"
    text += f"🔰 {scam_label}"
    
    await callback.message.edit_text(text, reply_markup=main_menu())
    session.close()
    await callback.answer()

# ========== СТАТИСТИКА ==========
@router.callback_query(F.data == "my_stats")
async def my_stats_callback(callback: CallbackQuery):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    
    if not user:
        await callback.message.edit_text("❌ Сначала зарегистрируйтесь /start")
        await callback.answer()
        session.close()
        return
    
    active_lots = session.query(Lot).filter_by(seller_id=user.tg_id, is_active=True).count()
    sold_lots = session.query(Lot).filter_by(seller_id=user.tg_id, is_sold=True).count()
    bought = session.query(Lot).filter_by(buyer_id=user.tg_id, is_sold=True).count()
    
    text = f"📊 <b>Статистика {user.play_nick}</b>\n\n"
    text += f"⭐ Рейтинг: {user.rating:.1f}\n"
    text += f"📦 Сделок: <b>{user.deals_count}</b>\n"
    text += f"📤 Активных лотов: {active_lots}\n"
    text += f"✅ Продано: {sold_lots}\n"
    text += f"🛒 Куплено: {bought}\n"
    
    achievement = session.query(Achievement).filter(
        Achievement.min_deals <= user.deals_count
    ).order_by(Achievement.min_deals.desc()).first()
    
    if achievement:
        text += f"\n🏅 Текущее достижение: {achievement.icon} {achievement.name}"
    
    await callback.message.edit_text(text, reply_markup=main_menu())
    session.close()
    await callback.answer()

# ========== СОЗДАНИЕ ЛОТА ==========
@router.callback_query(F.data == "create_lot")
async def create_lot_callback(callback: CallbackQuery, state: FSMContext):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    session.close()
    
    if not user:
        await callback.message.edit_text("❌ Сначала зарегистрируйтесь /start")
        await callback.answer()
        return
    
    if user.is_banned:
        await callback.message.edit_text("⛔ Вы забанены!")
        await callback.answer()
        return
    
    if user.is_scammer:
        await callback.message.edit_text("⛔ Вы помечены как скамер!")
        await callback.answer()
        return
    
    await callback.message.edit_text("📝 Введите название предмета:")
    await state.set_state(CreateLotState.title)
    await callback.answer()

@router.message(CreateLotState.title)
async def lot_title(message: Message, state: FSMContext):
    if len(message.text) > 100:
        await message.answer("❌ Название слишком длинное (макс 100 символов)")
        return
    await state.update_data(title=message.text)
    await message.answer("📄 Теперь описание (отправьте '-' чтобы пропустить):")
    await state.set_state(CreateLotState.description)

@router.message(CreateLotState.description)
async def lot_desc(message: Message, state: FSMContext):
    desc = message.text if message.text != "-" else "Без описания"
    await state.update_data(description=desc)
    await message.answer("📸 Загрузите фото предмета:")
    await state.set_state(CreateLotState.photo)

@router.message(CreateLotState.photo, F.photo)
async def lot_photo(message: Message, state: FSMContext):
    await state.update_data(photo_id=message.photo[-1].file_id)
    await message.answer("💰 Введите стартовую цену (число):")
    await state.set_state(CreateLotState.start_price)

@router.message(CreateLotState.start_price)
async def lot_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.replace(',', '.'))
        if price <= 0:
            await message.answer("❌ Цена должна быть больше 0!")
            return
        await state.update_data(start_price=price)
        await message.answer("⏰ Введите длительность в МИНУТАХ (например: 60):")
        await state.set_state(CreateLotState.duration)
    except ValueError:
        await message.answer("❌ Введите число!")

@router.message(CreateLotState.duration)
async def lot_duration(message: Message, state: FSMContext):
    try:
        minutes = int(message.text)
        if minutes < 5:
            await message.answer("❌ Минимум 5 минут!")
            return
        if minutes > 1440:
            await message.answer("❌ Максимум 1440 минут (24 часа)!")
            return
        
        data = await state.get_data()
        
        session = SessionLocal()
        new_lot = Lot(
            seller_id=message.from_user.id,
            title=data['title'],
            description=data['description'],
            photo_id=data['photo_id'],
            start_price=data['start_price'],
            current_price=data['start_price'],
            min_bet=data['start_price'] * 1.05,
            end_time=datetime.utcnow() + timedelta(minutes=minutes)
        )
        session.add(new_lot)
        session.commit()
        session.close()
        
        await message.answer(
            f"✅ <b>Лот создан!</b>\n\n"
            f"📌 {data['title']}\n"
            f"💰 Старт: {data['start_price']:,.0f}$\n"
            f"⏰ Завершится через {minutes} мин.",
            reply_markup=main_menu()
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите число минут!")

# ========== АКТИВНЫЕ АУКЦИОНЫ ==========
@router.callback_query(F.data == "active_lots")
async def active_lots_callback(callback: CallbackQuery):
    session = SessionLocal()
    lots = session.query(Lot).filter_by(is_active=True).all()
    session.close()
    
    if not lots:
        await callback.message.edit_text("📭 Активных аукционов нет.", reply_markup=main_menu())
        await callback.answer()
        return
    
    text = "📋 <b>Активные аукционы:</b>\n\n"
    for i, lot in enumerate(lots[:10], 1):
        time_left = lot.end_time - datetime.utcnow()
        minutes = int(time_left.total_seconds() / 60)
        text += f"{i}. {lot.title} — {lot.current_price:,.0f}$ (⏳ {minutes} мин.)\n"
    
    if len(lots) > 10:
        text += f"\n... и еще {len(lots) - 10} лотов"
    
    await callback.message.edit_text(text, reply_markup=main_menu())
    await callback.answer()

# ========== МОИ ЛОТЫ ==========
@router.callback_query(F.data == "my_lots")
async def my_lots_callback(callback: CallbackQuery):
    session = SessionLocal()
    lots = session.query(Lot).filter_by(seller_id=callback.from_user.id).all()
    session.close()
    
    if not lots:
        await callback.message.edit_text("📭 У вас нет созданных лотов.", reply_markup=main_menu())
        await callback.answer()
        return
    
    text = "📈 <b>Ваши лоты:</b>\n\n"
    for lot in lots:
        status = "🟢 Активен" if lot.is_active else "🔴 Завершен"
        sold = "✅ Продан" if lot.is_sold else "❌ Не продан"
        text += f"• {lot.title} — {lot.current_price:,.0f}$ | {status} | {sold}\n"
    
    await callback.message.edit_text(text, reply_markup=main_menu())
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
    
    await callback.message.edit_text(text, reply_markup=main_menu())
    await callback.answer()

# ========== ИЗБРАННОЕ ==========
@router.callback_query(F.data == "favorites")
async def favorites_callback(callback: CallbackQuery):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    
    if not user:
        await callback.message.edit_text("❌ Сначала зарегистрируйтесь /start")
        await callback.answer()
        session.close()
        return
    
    favorites = session.query(Favorite).filter_by(user_id=user.tg_id).all()
    
    if not favorites:
        await callback.message.edit_text("⭐ У вас нет избранных лотов.", reply_markup=main_menu())
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
    
    await callback.message.edit_text(text, reply_markup=main_menu())
    session.close()
    await callback.answer()

# ========== СЛУЧАЙНЫЙ ЛОТ ==========
@router.callback_query(F.data == "random_lot")
async def random_lot_callback(callback: CallbackQuery):
    session = SessionLocal()
    lots = session.query(Lot).filter_by(is_active=True).all()
    session.close()
    
    if not lots:
        await callback.message.edit_text("📭 Активных лотов нет.", reply_markup=main_menu())
        await callback.answer()
        return
    
    lot = random.choice(lots)
    text = f"🎲 <b>Случайный лот!</b>\n\n"
    text += f"📌 {lot.title}\n"
    text += f"💰 Текущая цена: {lot.current_price:,.0f}$\n"
    text += f"⏰ Завершится: {lot.end_time.strftime('%d.%m.%Y %H:%M')}"
    
    await callback.message.edit_text(text, reply_markup=main_menu())
    await callback.answer()

# ========== ПОИСК ==========
@router.callback_query(F.data == "search_lots")
async def search_lots_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🔍 Введите название лота для поиска:")
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
    
    await message.answer(text, reply_markup=main_menu())
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
    await callback.message.edit_text(text, reply_markup=main_menu())
    await callback.answer()

# ========== ТОП ПОЛЬЗОВАТЕЛЕЙ ==========
@router.callback_query(F.data == "top_users")
async def top_users_callback(callback: CallbackQuery):
    session = SessionLocal()
    users = session.query(User).order_by(User.deals_count.desc()).limit(10).all()
    session.close()
    
    if not users:
        await callback.message.edit_text("📭 Нет пользователей.", reply_markup=main_menu())
        await callback.answer()
        return
    
    text = "🏆 <b>Топ пользователей по сделкам</b>\n\n"
    medals = ["🥇", "🥈", "🥉"]
    
    for i, user in enumerate(users):
        medal = medals[i] if i < 3 else f"{i+1}."
        scam = " 🚫" if user.is_scammer else ""
        text += f"{medal} <b>{user.play_nick}</b> — {user.deals_count} сделок (⭐{user.rating:.1f}){scam}\n"
    
    await callback.message.edit_text(text, reply_markup=main_menu())
    await callback.answer()
