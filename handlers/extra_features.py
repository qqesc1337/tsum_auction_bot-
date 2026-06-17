from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime, timedelta
from database import SessionLocal, User, Lot, Favorite, BlackList, Transaction, Achievement
import random

router = Router()

class SearchState(StatesGroup):
    query = State()

@router.callback_query(F.data.startswith("favorite_"))
async def add_favorite(callback: CallbackQuery):
    lot_id = int(callback.data.split("_")[1])
    
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    lot = session.query(Lot).filter_by(id=lot_id).first()
    
    if not user or not lot:
        await callback.answer("❌ Ошибка!")
        session.close()
        return
    
    existing = session.query(Favorite).filter_by(
        user_id=user.tg_id,
        lot_id=lot_id
    ).first()
    
    if existing:
        session.delete(existing)
        session.commit()
        await callback.answer("⭐ Удалено из избранного!")
    else:
        fav = Favorite(user_id=user.tg_id, lot_id=lot_id)
        session.add(fav)
        session.commit()
        await callback.answer("⭐ Добавлено в избранное!")
    
    session.close()

@router.callback_query(F.data == "favorites")
async def show_favorites(callback: CallbackQuery):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    
    if not user:
        await callback.answer("❌ Сначала зарегистрируйтесь!")
        session.close()
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
    
    if len(favorites) > 10:
        text += f"\n... и еще {len(favorites) - 10} лотов"
    
    await callback.message.answer(text)
    session.close()
    await callback.answer()

@router.callback_query(F.data.startswith("blacklist_"))
async def add_blacklist(callback: CallbackQuery):
    target_id = int(callback.data.split("_")[1])
    
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    target = session.query(User).filter_by(tg_id=target_id).first()
    
    if not user or not target:
        await callback.answer("❌ Ошибка!")
        session.close()
        return
    
    existing = session.query(BlackList).filter_by(
        user_id=user.tg_id,
        blocked_user_id=target_id
    ).first()
    
    if existing:
        session.delete(existing)
        session.commit()
        await callback.answer(f"✅ {target.play_nick} удален из черного списка!")
    else:
        bl = BlackList(user_id=user.tg_id, blocked_user_id=target_id)
        session.add(bl)
        session.commit()
        await callback.answer(f"🚫 {target.play_nick} добавлен в черный список!")
    
    session.close()

@router.callback_query(F.data == "my_stats")
async def my_stats(callback: CallbackQuery):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    
    if not user:
        await callback.answer("❌ Сначала зарегистрируйтесь!")
        session.close()
        return
    
    active_lots = session.query(Lot).filter_by(seller_id=user.tg_id, is_active=True).count()
    sold_lots = session.query(Lot).filter_by(seller_id=user.tg_id, is_sold=True).count()
    bought = session.query(Lot).filter_by(buyer_id=user.tg_id, is_sold=True).count()
    
    top_lot = session.query(Lot).filter_by(
        seller_id=user.tg_id, is_sold=True
    ).order_by(Lot.current_price.desc()).first()
    
    from sqlalchemy import func
    avg_price = session.query(func.avg(Transaction.price)).filter_by(
        seller_id=user.tg_id
    ).scalar() or 0
    
    achievement = session.query(Achievement).filter(
        Achievement.min_deals <= user.deals_count
    ).order_by(Achievement.min_deals.desc()).first()
    
    text = f"📊 <b>Статистика {user.play_nick}</b>\n\n"
    text += f"⭐ Рейтинг: {user.rating:.1f}\n"
    text += f"📦 Сделок: <b>{user.deals_count}</b>\n"
    text += f"📤 Активных лотов: {active_lots}\n"
    text += f"✅ Продано: {sold_lots}\n"
    text += f"🛒 Куплено: {bought}\n"
    text += f"📈 Средняя цена: {avg_price:,.0f}$\n"
    
    if top_lot:
        text += f"\n🏆 Лучшая продажа:\n"
        text += f"   {top_lot.title} — {top_lot.current_price:,.0f}$"
    
    if achievement:
        text += f"\n\n🏅 Текущее достижение: {achievement.icon} {achievement.name}"
    
    await callback.message.answer(text)
    session.close()
    await callback.answer()

@router.callback_query(F.data == "instructions")
async def show_instructions(callback: CallbackQuery):
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
• Следи за ними в разделе "Избранное"

<b>7️⃣ Отзывы</b>
• Оценивай продавцов после сделок
• Рейтинг влияет на доверие

<b>8️⃣ Сделки</b>
• После завершения аукциона бот присылает ник продавца/покупателя
• Свяжитесь в игре TSUM или Telegram
• Проведите сделку и подтвердите её в боте

<b>9️⃣ Безопасность</b>
• Жалуйся на мошенников через "⚠️ Пожаловаться"
• Черный список — не видишь лоты от неугодных

<b>🔥 Дополнительные фишки:</b>
• Умные ставки с быстрыми суммами
• Автоматическое завершение аукционов
• Система рейтинга и достижений
• Топ пользователей

<i>Удачных торгов в TSUM! 🍀</i>
    """
    
    await callback.message.answer(text)
    await callback.answer()

@router.callback_query(F.data == "random_lot")
async def random_lot(callback: CallbackQuery):
    session = SessionLocal()
    lots = session.query(Lot).filter_by(is_active=True).all()
    
    if not lots:
        await callback.message.answer("📭 Активных лотов нет.")
        session.close()
        await callback.answer()
        return
    
    lot = random.choice(lots)
    session.close()
    
    await callback.message.answer(
        f"🎲 <b>Случайный лот!</b>\n\n"
        f"📌 {lot.title}\n"
        f"💰 Текущая цена: {lot.current_price:,.0f}$\n"
        f"⏰ Завершится: {lot.end_time.strftime('%d.%m.%Y %H:%M')}"
    )
    await callback.answer()

@router.callback_query(F.data == "search_lots")
async def search_start(callback: CallbackQuery, state: FSMContext):
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
