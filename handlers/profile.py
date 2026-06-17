from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database import SessionLocal, User, Review, Achievement, Lot

router = Router()

@router.message(F.text == "👤 Мой профиль")
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
    
    text = f"👤 <b>Твой профиль</b>\n\n"
    text += f"🎮 TSUM: <b>{user.play_nick}</b>\n"
    text += f"📱 TG: @{user.tg_username}\n"
    text += f"⭐ Рейтинг: {user.rating:.1f} (отзывов: {len(reviews)})\n"
    text += f"📦 Сделок: {user.deals_count}\n"
    text += f"🏆 Достижение: {achievement.icon} {achievement.name if achievement else 'Нет'}\n"
    
    await message.answer(text)
    session.close()

@router.message(F.text == "📊 Моя статистика")
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
