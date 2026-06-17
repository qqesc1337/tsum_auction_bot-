from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from database import SessionLocal, User, Lot, Report, Transaction, Review
from config import ADMIN_IDS, OWNER_ID
from datetime import datetime

router = Router()

async def admin_panel_message(message: Message):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=message.from_user.id).first()
    session.close()
    
    if not user or not (user.is_admin or user.is_owner):
        await message.answer("⛔ У вас нет прав администратора!")
        return
    
    session = SessionLocal()
    pending_reports = session.query(Report).filter_by(status="pending").count()
    session.close()
    
    if user.is_owner:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👑 Управление админами", callback_data="admin_manage")],
            [InlineKeyboardButton(text=f"📊 Статистика бота", callback_data="admin_stats")],
            [InlineKeyboardButton(text=f"⚠️ Жалобы ({pending_reports})" if pending_reports else "⚠️ Жалоб нет", callback_data="admin_reports")],
            [InlineKeyboardButton(text="📋 Все пользователи", callback_data="admin_all_users")],
            [InlineKeyboardButton(text="🏆 Топ пользователей", callback_data="top_users")],
            [InlineKeyboardButton(text="📝 Логи аукционов", callback_data="admin_logs")],
            [InlineKeyboardButton(text="↩️ Главное меню", callback_data="back_to_main")]
        ])
        await message.answer(
            f"⚡ <b>Админ-панель (ВЛАДЕЛЕЦ)</b>\n\n"
            f"👤 Вы: {user.play_nick}",
            reply_markup=keyboard
        )
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика бота", callback_data="admin_stats")],
            [InlineKeyboardButton(text=f"⚠️ Жалобы ({pending_reports})" if pending_reports else "⚠️ Жалоб нет", callback_data="admin_reports")],
            [InlineKeyboardButton(text="↩️ Главное меню", callback_data="back_to_main")]
        ])
        await message.answer(
            f"⚡ <b>Админ-панель</b>\n\n"
            f"👤 Вы: {user.play_nick} (Администратор)",
            reply_markup=keyboard
        )

@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery):
    await admin_panel_message(callback.message)
    await callback.answer()

@router.callback_query(F.data.startswith("admin_quick_ban_"))
async def admin_quick_ban(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[3])
    
    session = SessionLocal()
    admin = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    
    if not admin or not (admin.is_admin or admin.is_owner):
        await callback.answer("⛔ У вас нет прав!", show_alert=True)
        session.close()
        return
    
    user = session.query(User).filter_by(tg_id=user_id).first()
    
    if not user:
        await callback.answer("❌ Пользователь не найден")
        session.close()
        return
    
    user.is_banned = True
    session.commit()
    session.close()
    
    await callback.message.answer(f"✅ Пользователь {user.play_nick} забанен!")
    await callback.answer()

@router.callback_query(F.data.startswith("admin_quick_scam_"))
async def admin_quick_scam(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[3])
    
    session = SessionLocal()
    admin = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    
    if not admin or not (admin.is_admin or admin.is_owner):
        await callback.answer("⛔ У вас нет прав!", show_alert=True)
        session.close()
        return
    
    user = session.query(User).filter_by(tg_id=user_id).first()
    
    if not user:
        await callback.answer("❌ Пользователь не найден")
        session.close()
        return
    
    user.is_scammer = True
    session.commit()
    session.close()
    
    await callback.message.answer(f"🚫 Пользователь {user.play_nick} помечен как СКАМЕР!")
    await callback.answer()

@router.callback_query(F.data == "admin_reports")
async def admin_reports(callback: CallbackQuery):
    session = SessionLocal()
    reports = session.query(Report).filter_by(status="pending").order_by(
        Report.date.desc()
    ).all()
    session.close()
    
    if not reports:
        await callback.message.answer("📭 Нет новых жалоб.")
        await callback.answer()
        return
    
    text = "⚠️ <b>Жалобы:</b>\n\n"
    for report in reports[:10]:
        text += f"📌 #{report.id}\n"
        text += f"От: {report.reporter_id}\n"
        text += f"На: {report.reported_id}\n"
        text += f"📝 {report.reason[:150]}\n"
        text += f"📅 {report.date.strftime('%d.%m.%Y %H:%M')}\n\n"
    
    if len(reports) > 10:
        text += f"\n... и еще {len(reports) - 10} жалоб"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Все жалобы", callback_data="admin_all_reports")]
    ])
    
    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "admin_all_reports")
async def admin_all_reports(callback: CallbackQuery):
    session = SessionLocal()
    reports = session.query(Report).order_by(Report.date.desc()).all()
    session.close()
    
    if not reports:
        await callback.message.answer("📭 Жалоб нет.")
        await callback.answer()
        return
    
    text = "📋 <b>Все жалобы:</b>\n\n"
    for report in reports[:10]:
        status_emoji = "🟡" if report.status == "pending" else "🟢" if report.status == "resolved" else "🔴"
        text += f"{status_emoji} #{report.id}\n"
        text += f"От: {report.reporter_id} → На: {report.reported_id}\n"
        text += f"📝 {report.reason[:100]}\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Назад", callback_data="admin_reports")]
    ])
    
    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    session = SessionLocal()
    total_users = session.query(User).count()
    banned = session.query(User).filter_by(is_banned=True).count()
    scammers = session.query(User).filter_by(is_scammer=True).count()
    active_lots = session.query(Lot).filter_by(is_active=True).count()
    sold_lots = session.query(Lot).filter_by(is_sold=True).count()
    pending_reports = session.query(Report).filter_by(status="pending").count()
    
    from sqlalchemy import func
    total_amount = session.query(func.sum(Transaction.price)).scalar() or 0
    total_deals = session.query(Transaction).count()
    
    session.close()
    
    await callback.message.answer(
        f"📊 <b>Статистика бота TSUM Auction</b>\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"⛔ Забанено: {banned}\n"
        f"🚫 Скамеров: {scammers}\n"
        f"⚠️ Жалоб: {pending_reports}\n"
        f"📋 Активных лотов: {active_lots}\n"
        f"✅ Продано лотов: {sold_lots}\n"
        f"📦 Всего сделок: {total_deals}\n"
        f"💰 Общая сумма сделок: {total_amount:,.0f}$"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_all_users")
async def admin_all_users(callback: CallbackQuery):
    session = SessionLocal()
    users = session.query(User).order_by(User.registration_date.desc()).limit(20).all()
    session.close()
    
    if not users:
        await callback.message.answer("📭 Нет пользователей.")
        await callback.answer()
        return
    
    text = "📋 <b>Последние пользователи:</b>\n\n"
    for i, user in enumerate(users, 1):
        status = "👑" if user.is_owner else "🔑" if user.is_admin else "👤"
        scam = "🚫" if user.is_scammer else ""
        ban = "⛔" if user.is_banned else ""
        text += (
            f"{i}. {status} <b>{user.play_nick}</b>\n"
            f"   🎮 TSUM | 📱 @{user.tg_username}\n"
            f"   🆔 {user.tg_id}\n"
            f"   📦 {user.deals_count} сделок, ⭐ {user.rating:.1f} {scam}{ban}\n\n"
        )
    
    await callback.message.answer(text)
    await callback.answer()

@router.callback_query(F.data == "admin_logs")
async def admin_logs(callback: CallbackQuery):
    session = SessionLocal()
    lots = session.query(Lot).filter_by(is_sold=True).order_by(Lot.end_time.desc()).limit(10).all()
    session.close()
    
    if not lots:
        await callback.message.answer("📭 Нет завершенных аукционов.")
        await callback.answer()
        return
    
    text = "📝 <b>Последние продажи:</b>\n\n"
    for lot in lots:
        text += f"• {lot.title} — {lot.current_price:,.0f}$\n"
        text += f"  Продавец: {lot.seller_id}, Покупатель: {lot.buyer_id}\n\n"
    
    await callback.message.answer(text)
    await callback.answer()

@router.callback_query(F.data == "top_users")
async def top_users(callback: CallbackQuery):
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
        text += (
            f"{medal} <b>{user.play_nick}</b>\n"
            f"   🎮 TSUM | 📱 @{user.tg_username}\n"
            f"   📦 {user.deals_count} сделок (⭐{user.rating:.1f}){scam}\n\n"
        )
    
    await callback.message.answer(text)
    await callback.answer()

@router.message(F.text.startswith("/ban "))
async def ban_user(message: Message):
    if message.from_user.id not in ADMIN_IDS and message.from_user.id != OWNER_ID:
        return
    
    try:
        user_id = int(message.text.split()[1])
        session = SessionLocal()
        user = session.query(User).filter_by(tg_id=user_id).first()
        if user:
            user.is_banned = True
            session.commit()
            await message.answer(f"✅ Пользователь {user.play_nick} забанен!")
            try:
                await message.bot.send_message(user_id, "⛔ Вы были забанены в TSUM Auction!")
            except:
                pass
        else:
            await message.answer("❌ Пользователь не найден")
        session.close()
    except:
        await message.answer("❌ Используйте: /ban [ID]")

@router.message(F.text.startswith("/unban "))
async def unban_user(message: Message):
    if message.from_user.id not in ADMIN_IDS and message.from_user.id != OWNER_ID:
        return
    
    try:
        user_id = int(message.text.split()[1])
        session = SessionLocal()
        user = session.query(User).filter_by(tg_id=user_id).first()
        if user:
            user.is_banned = False
            session.commit()
            await message.answer(f"✅ Пользователь {user.play_nick} разбанен!")
        else:
            await message.answer("❌ Пользователь не найден")
        session.close()
    except:
        await message.answer("❌ Используйте: /unban [ID]")

@router.message(F.text.startswith("/scam "))
async def scam_user(message: Message):
    if message.from_user.id not in ADMIN_IDS and message.from_user.id != OWNER_ID:
        return
    
    try:
        user_id = int(message.text.split()[1])
        session = SessionLocal()
        user = session.query(User).filter_by(tg_id=user_id).first()
        if user:
            user.is_scammer = True
            session.commit()
            await message.answer(f"🚫 Пользователь {user.play_nick} помечен как СКАМЕР!")
        else:
            await message.answer("❌ Пользователь не найден")
        session.close()
    except:
        await message.answer("❌ Используйте: /scam [ID]")

@router.message(F.text.startswith("/unscam "))
async def unscam_user(message: Message):
    if message.from_user.id not in ADMIN_IDS and message.from_user.id != OWNER_ID:
        return
    
    try:
        user_id = int(message.text.split()[1])
        session = SessionLocal()
        user = session.query(User).filter_by(tg_id=user_id).first()
        if user:
            user.is_scammer = False
            session.commit()
            await message.answer(f"✅ С пользователя {user.play_nick} снята метка СКАМ!")
        else:
            await message.answer("❌ Пользователь не найден")
        session.close()
    except:
        await message.answer("❌ Используйте: /unscam [ID]")

@router.message(F.text == "/stats")
async def full_stats(message: Message):
    if message.from_user.id not in ADMIN_IDS and message.from_user.id != OWNER_ID:
        return
    
    session = SessionLocal()
    total_users = session.query(User).count()
    banned = session.query(User).filter_by(is_banned=True).count()
    scammers = session.query(User).filter_by(is_scammer=True).count()
    active_lots = session.query(Lot).filter_by(is_active=True).count()
    sold_lots = session.query(Lot).filter_by(is_sold=True).count()
    pending_reports = session.query(Report).filter_by(status="pending").count()
    
    from sqlalchemy import func
    total_amount = session.query(func.sum(Transaction.price)).scalar() or 0
    
    session.close()
    
    await message.answer(
        f"📊 <b>Полная статистика бота:</b>\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"⛔ Забанено: {banned}\n"
        f"🚫 Скамеров: {scammers}\n"
        f"⚠️ Жалоб: {pending_reports}\n"
        f"📋 Активных лотов: {active_lots}\n"
        f"✅ Продано лотов: {sold_lots}\n"
        f"💰 Общая сумма сделок: {total_amount:,.0f}$"
    )

@router.callback_query(F.data.startswith("admin_stats_user_"))
async def admin_stats_user(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[3])
    
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=user_id).first()
    
    if not user:
        await callback.answer("❌ Пользователь не найден")
        session.close()
        return
    
    reviews = session.query(Review).filter_by(target_id=user_id).all()
    avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 5.0
    
    text = f"📊 <b>Статистика пользователя</b>\n\n"
    text += f"👤 Ник: {user.play_nick}\n"
    text += f"🆔 ID: {user.tg_id}\n"
    text += f"👤 TG: @{user.tg_username}\n"
    text += f"⭐ Рейтинг: {avg_rating:.1f} (отзывов: {len(reviews)})\n"
    text += f"📦 Сделок: {user.deals_count}\n"
    text += f"🚫 Бан: {'Да' if user.is_banned else 'Нет'}\n"
    text += f"⚠️ Скамер: {'Да' if user.is_scammer else 'Нет'}\n"
    text += f"🔑 Админ: {'Да' if user.is_admin else 'Нет'}\n"
    text += f"👑 Владелец: {'Да' if user.is_owner else 'Нет'}\n"
    text += f"📅 Зарегистрирован: {user.registration_date.strftime('%d.%m.%Y')}"
    
    await callback.message.answer(text)
    session.close()
    await callback.answer()

@router.callback_query(F.data.startswith("admin_reviews_"))
async def admin_reviews_user(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[2])
    
    session = SessionLocal()
    reviews = session.query(Review).filter_by(target_id=user_id).order_by(
        Review.date.desc()
    ).limit(10).all()
    session.close()
    
    if not reviews:
        await callback.message.answer("📭 Отзывов нет.")
        await callback.answer()
        return
    
    text = "📋 <b>Отзывы пользователя:</b>\n\n"
    for review in reviews:
        stars = "⭐" * review.rating
        text += f"{stars} {review.text[:100]}\n"
        text += f"   — от {review.date.strftime('%d.%m.%Y')}\n\n"
    
    await callback.message.answer(text)
    await callback.answer()
