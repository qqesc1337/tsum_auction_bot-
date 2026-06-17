from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime, timedelta
from database import SessionLocal, Lot, User

router = Router()

class CreateLotState(StatesGroup):
    title = State()
    description = State()
    photo = State()
    start_price = State()
    duration = State()

# ========== АКТИВНЫЕ АУКЦИОНЫ ==========
async def active_auctions(message: Message):
    session = SessionLocal()
    lots = session.query(Lot).filter_by(is_active=True).all()
    session.close()
    
    if not lots:
        await message.answer("📭 Активных аукционов нет.")
        return
    
    text = "📋 <b>Активные аукционы:</b>\n\n"
    for i, lot in enumerate(lots[:10], 1):
        time_left = lot.end_time - datetime.utcnow()
        minutes = int(time_left.total_seconds() / 60)
        text += f"{i}. {lot.title} — {lot.current_price:,.0f}$ (⏳ {minutes} мин.)\n"
    
    if len(lots) > 10:
        text += f"\n... и еще {len(lots) - 10} лотов"
    
    await message.answer(text)

# ========== МОИ ЛОТЫ ==========
async def my_lots(message: Message):
    session = SessionLocal()
    lots = session.query(Lot).filter_by(seller_id=message.from_user.id).all()
    session.close()
    
    if not lots:
        await message.answer("📭 У вас нет созданных лотов.")
        return
    
    text = "📈 <b>Ваши лоты:</b>\n\n"
    for lot in lots:
        status = "🟢 Активен" if lot.is_active else "🔴 Завершен"
        sold = "✅ Продан" if lot.is_sold else "❌ Не продан"
        text += f"• {lot.title} — {lot.current_price:,.0f}$ | {status} | {sold}\n"
    
    await message.answer(text)

# ========== СОЗДАНИЕ ЛОТА ==========
async def create_lot_start(message: Message, state: FSMContext):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=message.from_user.id).first()
    session.close()
    
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь /start")
        return
    
    if user.is_banned:
        await message.answer("⛔ Вы забанены!")
        return
    
    if user.is_scammer:
        await message.answer("⛔ Вы помечены как скамер!")
        return
    
    await message.answer("📝 Введите название предмета:")
    await state.set_state(CreateLotState.title)

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
            f"⏰ Завершится через {minutes} мин."
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите число минут!")
