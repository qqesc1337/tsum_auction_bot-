from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database import SessionLocal, User, Review, Achievement, Lot

router = Router()

class ReviewState(StatesGroup):
    rating = State()
    text = State()

# ========== ПРОФИЛЬ ==========
async def show_my_profile(message: Message):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=message.from_user.id).first()
    
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь /start")
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
    
    await message.answer(text)
    session.close()

# ========== СТАТИСТИКА ==========
async def my_stats(message: Message):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=message.from_user.id).first()
    
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь!")
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
    
    await message.answer(text)
    session.close()

# ========== ОТЗЫВЫ ==========
@router.callback_query(F.data.startswith("leave_review_"))
async def leave_review_start(callback: CallbackQuery, state: FSMContext):
    target_id = int(callback.data.split("_")[2])
    await state.update_data(target_id=target_id)
    
    await callback.message.answer(
        "⭐ Оцените пользователя (1-5):\n"
        "1 — ужасно\n"
        "2 — плохо\n"
        "3 — нормально\n"
        "4 — хорошо\n"
        "5 — отлично"
    )
    await state.set_state(ReviewState.rating)
    await callback.answer()

@router.message(ReviewState.rating)
async def review_rating(message: Message, state: FSMContext):
    try:
        rating = int(message.text)
        if rating < 1 or rating > 5:
            await message.answer("❌ Оценка должна быть от 1 до 5!")
            return
        
        await state.update_data(rating=rating)
        await message.answer("✍️ Напишите текст отзыва:")
        await state.set_state(ReviewState.text)
    except ValueError:
        await message.answer("❌ Введите число от 1 до 5!")

@router.message(ReviewState.text)
async def review_text(message: Message, state: FSMContext):
    data = await state.get_data()
    
    session = SessionLocal()
    new_review = Review(
        target_id=data['target_id'],
        author_id=message.from_user.id,
        text=message.text,
        rating=data['rating']
    )
    session.add(new_review)
    session.commit()
    session.close()
    
    await message.answer("✅ Отзыв сохранен! Спасибо за ваш отзыв.")
    await state.clear()
