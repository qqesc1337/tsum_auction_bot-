from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database import SessionLocal, User, Review, Achievement, Report
from keyboards.inline import seller_profile_buttons
from config import ADMIN_IDS, OWNER_ID

router = Router()

class ReviewState(StatesGroup):
    rating = State()
    text = State()

class ReportState(StatesGroup):
    reason = State()

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
    
    scam_label = "🚫 Метка: СКАМЕР" if user.is_scammer else "✅ Репутация: чистая"
    ban_label = "⛔ ЗАБАНЕН" if user.is_banned else "🟢 Активен"
    
    text = (
        f"👤 <b>Мой профиль</b>\n\n"
        f"🎮 Ник в TSUM: <b>{user.play_nick}</b>\n"
        f"📱 TG: @{user.tg_username}\n"
        f"🆔 ID: <code>{user.tg_id}</code>\n\n"
        f"⭐ Рейтинг: {user.rating:.1f} (отзывов: {len(reviews)})\n"
        f"📦 Сделок: {user.deals_count}\n"
        f"🏆 Достижение: {achievement.icon} {achievement.name if achievement else 'Нет'}\n"
        f"📊 Статус: {ban_label}\n"
        f"🔰 {scam_label}\n"
        f"📅 В системе с: {user.registration_date.strftime('%d.%m.%Y')}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Мои отзывы", callback_data="my_reviews")],
        [InlineKeyboardButton(text="📱 Мой Telegram", url=f"https://t.me/{user.tg_username}")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")]
    ])
    
    if message.from_user.id in ADMIN_IDS or message.from_user.id == OWNER_ID:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="🛠 Админ-панель", callback_data="admin_panel")
        ])
    
    await message.answer(text, reply_markup=keyboard)
    session.close()

@router.callback_query(F.data.startswith("seller_profile_"))
async def show_seller_profile(callback: CallbackQuery):
    seller_id = int(callback.data.split("_")[2])
    session = SessionLocal()
    seller = session.query(User).filter_by(tg_id=seller_id).first()
    
    if not seller:
        await callback.answer("❌ Пользователь не найден")
        session.close()
        return
    
    achievement = session.query(Achievement).filter(
        Achievement.min_deals <= seller.deals_count
    ).order_by(Achievement.min_deals.desc()).first()
    
    reviews = session.query(Review).filter_by(target_id=seller_id).all()
    avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 5.0
    
    scam_label = "🚫 [СКАМЕР]" if seller.is_scammer else "✅ Проверен"
    ban_label = "⛔ ЗАБАНЕН" if seller.is_banned else "🟢 Активен"
    
    text = (
        f"👤 <b>Профиль продавца</b>\n\n"
        f"🎮 Ник в TSUM: <b>{seller.play_nick}</b>\n"
        f"📱 TG: @{seller.tg_username}\n"
        f"🆔 ID: <code>{seller.tg_id}</code>\n\n"
        f"⭐ Рейтинг: {avg_rating:.1f} (отзывов: {len(reviews)})\n"
        f"📦 Сделок: {seller.deals_count}\n"
        f"🏆 Достижение: {achievement.icon} {achievement.name if achievement else 'Нет'}\n"
        f"📊 Статус: {ban_label}\n"
        f"🔰 {scam_label}\n"
        f"📅 В системе с: {seller.registration_date.strftime('%d.%m.%Y')}"
    )
    
    keyboard = seller_profile_buttons(seller_id)
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(
            text="📱 Написать в Telegram",
            url=f"https://t.me/{seller.tg_username}"
        )
    ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(
            text="⚠️ Пожаловаться на пользователя",
            callback_data=f"report_user_{seller_id}"
        )
    ])
    
    await callback.message.answer(text, reply_markup=keyboard)
    session.close()
    await callback.answer()

@router.callback_query(F.data.startswith("report_user_"))
async def report_user_start(callback: CallbackQuery, state: FSMContext):
    reported_id = int(callback.data.split("_")[2])
    
    if callback.from_user.id == reported_id:
        await callback.answer("❌ Нельзя пожаловаться на самого себя!", show_alert=True)
        return
    
    session = SessionLocal()
    reported_user = session.query(User).filter_by(tg_id=reported_id).first()
    
    if not reported_user:
        await callback.answer("❌ Пользователь не найден")
        session.close()
        return
    
    existing_report = session.query(Report).filter_by(
        reporter_id=callback.from_user.id,
        reported_id=reported_id,
        status="pending"
    ).first()
    
    if existing_report:
        await callback.answer(
            "⏳ Вы уже отправили жалобу на этого пользователя!",
            show_alert=True
        )
        session.close()
        return
    
    session.close()
    
    await state.update_data(reported_id=reported_id)
    
    await callback.message.answer(
        f"⚠️ <b>Жалоба на пользователя {reported_user.play_nick}</b>\n\n"
        f"Опишите причину жалобы:\n"
        f"• Мошенничество\n"
        f"• Оскорбления\n"
        f"• Нарушение правил\n"
        f"• Другое\n\n"
        f"Напишите подробности в следующем сообщении:"
    )
    await state.set_state(ReportState.reason)
    await callback.answer()

@router.message(ReportState.reason)
async def report_reason(message: Message, state: FSMContext):
    data = await state.get_data()
    reported_id = data.get('reported_id')
    reason = message.text
    
    if len(reason) < 10:
        await message.answer("❌ Пожалуйста, опишите причину подробнее (минимум 10 символов):")
        return
    
    session = SessionLocal()
    
    new_report = Report(
        reporter_id=message.from_user.id,
        reported_id=reported_id,
        reason=reason
    )
    session.add(new_report)
    session.commit()
    report_id = new_report.id
    session.close()
    
    await message.answer(
        f"✅ Ваша жалоба отправлена!\n\n"
        f"Номер жалобы: #{report_id}\n"
        f"Статус: ожидает рассмотрения\n\n"
        f"Администрация рассмотрит вашу жалобу в ближайшее время."
    )
    
    session = SessionLocal()
    reporter = session.query(User).filter_by(tg_id=message.from_user.id).first()
    reported = session.query(User).filter_by(tg_id=reported_id).first()
    admins = session.query(User).filter(
        (User.is_admin == True) | (User.is_owner == True)
    ).all()
    session.close()
    
    report_text = (
        f"🚨 <b>НОВАЯ ЖАЛОБА #{report_id}</b>\n\n"
        f"👤 От: {reporter.play_nick} (@{reporter.tg_username})\n"
        f"👤 На: {reported.play_nick} (@{reported.tg_username})\n"
        f"🆔 ID нарушителя: <code>{reported_id}</code>\n"
        f"📝 Причина: {reason}\n\n"
        f"📌 Действия:\n"
        f"/ban {reported_id} — забанить пользователя\n"
        f"/scam {reported_id} — выдать метку СКАМ\n"
        f"/unban {reported_id} — разбанить\n"
        f"/unscam {reported_id} — снять метку"
    )
    
    for admin in admins:
        try:
            await message.bot.send_message(
                admin.tg_id,
                report_text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔨 Забанить",
                            callback_data=f"admin_quick_ban_{reported_id}"
                        ),
                        InlineKeyboardButton(
                            text="🚫 Метка СКАМ",
                            callback_data=f"admin_quick_scam_{reported_id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="👤 Профиль нарушителя",
                            callback_data=f"seller_profile_{reported_id}"
                        )
                    ]
                ])
            )
        except Exception as e:
            print(f"Не удалось отправить уведомление админу {admin.tg_id}: {e}")
    
    await state.clear()

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

@router.callback_query(F.data.startswith("all_reviews_"))
async def all_reviews(callback: CallbackQuery):
    target_id = int(callback.data.split("_")[2])
    session = SessionLocal()
    reviews = session.query(Review).filter_by(target_id=target_id).order_by(
        Review.date.desc()
    ).limit(20).all()
    session.close()
    
    if not reviews:
        await callback.message.answer("📭 Отзывов пока нет.")
        await callback.answer()
        return
    
    text = "📋 <b>Все отзывы:</b>\n\n"
    for review in reviews:
        stars = "⭐" * review.rating
        text += f"{stars} {review.text[:100]}\n"
        text += f"   — от {review.date.strftime('%d.%m.%Y')}\n\n"
    
    await callback.message.answer(text)
    await callback.answer()

@router.callback_query(F.data == "my_reviews")
async def my_reviews(callback: CallbackQuery):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    
    if not user:
        await callback.answer("❌ Сначала зарегистрируйтесь!")
        session.close()
        return
    
    reviews = session.query(Review).filter_by(target_id=user.tg_id).order_by(
        Review.date.desc()
    ).limit(10).all()
    session.close()
    
    if not reviews:
        await callback.message.answer("📭 Отзывов о вас пока нет.")
        await callback.answer()
        return
    
    text = "📋 <b>Отзывы о вас:</b>\n\n"
    for review in reviews:
        stars = "⭐" * review.rating
        text += f"{stars} {review.text[:100]}\n"
        text += f"   — от пользователя (ID: {review.author_id})\n\n"
    
    await callback.message.answer(text)
    await callback.answer()

@router.callback_query(F.data == "achievements")
async def show_achievements(callback: CallbackQuery):
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
