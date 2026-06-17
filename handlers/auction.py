from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime, timedelta
from database import SessionLocal, Lot, User, BlackList
from keyboards.inline import lot_buttons
from config import DEFAULT_AUCTION_DURATION
import math

router = Router()

class CreateLotState(StatesGroup):
    title = State()
    description = State()
    photo = State()
    start_price = State()
    duration = State()

@router.message(F.text == "➕ Создать лот")
async def create_lot_start(message: Message, state: FSMContext):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=message.from_user.id).first()
    session.close()
    
    if user.is_banned:
        await message.answer("⛔ Вы забанены и не можете создавать лоты!")
        return
    
    if user.is_scammer:
        await message.answer("⛔ Вы помечены как скамер! Создание лотов запрещено!")
        return
    
    await message.answer("📝 Введите название предмета:")
    await state.set_state(CreateLotState.title)

@router.message(CreateLotState.title)
async def lot_title(message: Message, state: FSMContext):
    if len(message.text) > 100:
        await message.answer("❌ Название слишком длинное (макс 100 символов)")
        return
    await state.update_data(title=message.text)
    await message.answer("📄 Теперь описание (можете пропустить, отправьте '-'):")
    await state.set_state(CreateLotState.description)

@router.message(CreateLotState.description)
async def lot_desc(message: Message, state: FSMContext):
    desc = message.text if message.text != "-" else "Без описания"
    if len(desc) > 1000:
        await message.answer("❌ Описание слишком длинное (макс 1000 символов)")
        return
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
        await message.answer(f"⏰ Введите длительность аукциона в МИНУТАХ\n(по умолчанию {DEFAULT_AUCTION_DURATION} мин, отправьте '-'):")
        await state.set_state(CreateLotState.duration)
    except ValueError:
        await message.answer("❌ Введите число!")

@router.message(CreateLotState.duration)
async def lot_duration(message: Message, state: FSMContext):
    try:
        if message.text == "-":
            minutes = DEFAULT_AUCTION_DURATION
        else:
            minutes = int(message.text)
            if minutes < 5:
                await message.answer("❌ Минимальная длительность — 5 минут!")
                return
            if minutes > 1440:
                await message.answer("❌ Максимальная длительность — 1440 минут (24 часа)!")
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
        lot_id = new_lot.id
        session.close()
        
        end_time_str = (datetime.utcnow() + timedelta(minutes=minutes)).strftime("%d.%m.%Y %H:%M")
        
        await message.answer_photo(
            photo=data['photo_id'],
            caption=f"✅ <b>Лот создан!</b>\n\n"
                    f"📌 {data['title']}\n"
                    f"📄 {data['description']}\n"
                    f"💰 Старт: {data['start_price']:,.0f}$\n"
                    f"⏰ Завершится: {end_time_str} (через {minutes} мин.)\n"
                    f"📊 Ставок: 0",
            reply_markup=lot_buttons(lot_id, message.from_user.id, message.from_user.id)
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите число минут!")

@router.message(F.text == "📋 Активные аукционы")
async def active_auctions(message: Message):
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=message.from_user.id).first()
    
    blacklist = session.query(BlackList).filter_by(user_id=message.from_user.id).all()
    blocked_ids = [b.blocked_user_id for b in blacklist]
    
    lots = session.query(Lot).filter(
        Lot.is_active == True,
        Lot.seller_id.notin_(blocked_ids)
    ).order_by(Lot.end_time.asc()).all()
    
    session.close()
    
    if not lots:
        await message.answer("📭 Активных аукционов нет.")
        return
    
    lot_ids = [lot.id for lot in lots]
    total_pages = math.ceil(len(lot_ids) / 5)
    
    await show_lots_page(message, lot_ids, 1, total_pages)

@router.callback_query(F.data.startswith("lots_page_"))
async def lots_page_callback(callback: CallbackQuery):
    data_parts = callback.data.split("_")
    page = int(data_parts[2])
    total_pages = int(data_parts[3])
    
    session = SessionLocal()
    user = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    
    blacklist = session.query(BlackList).filter_by(user_id=callback.from_user.id).all()
    blocked_ids = [b.blocked_user_id for b in blacklist]
    
    lots = session.query(Lot).filter(
        Lot.is_active == True,
        Lot.seller_id.notin_(blocked_ids)
    ).order_by(Lot.end_time.asc()).all()
    
    session.close()
    
    if not lots:
        await callback.message.edit_text("📭 Активных аукционов нет.")
        await callback.answer()
        return
    
    lot_ids = [lot.id for lot in lots]
    await show_lots_page(callback.message, lot_ids, page, total_pages, edit=True)
    await callback.answer()

async def show_lots_page(message, lot_ids, page, total_pages, edit=False):
    start_idx = (page - 1) * 5
    end_idx = min(start_idx + 5, len(lot_ids))
    page_lots = lot_ids[start_idx:end_idx]
    
    session = SessionLocal()
    
    text = f"📋 <b>Активные аукционы</b> (стр. {page}/{total_pages})\n\n"
    
    for idx, lot_id in enumerate(page_lots, start=start_idx + 1):
        lot = session.query(Lot).filter_by(id=lot_id).first()
        if lot:
            time_left = lot.end_time - datetime.utcnow()
            minutes = int(time_left.total_seconds() / 60)
            hours = int(minutes / 60)
            if hours > 0:
                time_str = f"{hours}ч {minutes % 60}мин"
            else:
                time_str = f"{minutes}мин"
            
            text += f"{idx}. <b>{lot.title}</b>\n"
            text += f"   💰 {lot.current_price:,.0f}$ | ⏳ {time_str}\n"
            text += f"   📊 {lot.bid_count} ставок\n\n"
    
    session.close()
    
    keyboard_buttons = []
    
    for lot_id in page_lots:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text="👁️ Просмотр",
                callback_data=f"view_lot_{lot_id}"
            )
        ])
    
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=f"lots_page_{page-1}_{total_pages}"
        ))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(
            text="Вперед ▶️",
            callback_data=f"lots_page_{page+1}_{total_pages}"
        ))
    
    if nav_buttons:
        keyboard_buttons.append(nav_buttons)
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    if edit:
        await message.edit_text(text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)

@router.message(F.text == "📈 Мои лоты")
async def my_lots(message: Message):
    session = SessionLocal()
    lots = session.query(Lot).filter_by(seller_id=message.from_user.id).order_by(
        Lot.created_at.desc()
    ).all()
    session.close()
    
    if not lots:
        await message.answer("📭 У вас нет созданных лотов.")
        return
    
    lot_ids = [lot.id for lot in lots]
    total_pages = math.ceil(len(lot_ids) / 5)
    
    await show_my_lots_page(message, lot_ids, 1, total_pages)

@router.callback_query(F.data.startswith("mylots_page_"))
async def my_lots_page_callback(callback: CallbackQuery):
    data_parts = callback.data.split("_")
    page = int(data_parts[2])
    total_pages = int(data_parts[3])
    
    session = SessionLocal()
    lots = session.query(Lot).filter_by(seller_id=callback.from_user.id).order_by(
        Lot.created_at.desc()
    ).all()
    session.close()
    
    if not lots:
        await callback.message.edit_text("📭 У вас нет созданных лотов.")
        await callback.answer()
        return
    
    lot_ids = [lot.id for lot in lots]
    await show_my_lots_page(callback.message, lot_ids, page, total_pages, edit=True)
    await callback.answer()

async def show_my_lots_page(message, lot_ids, page, total_pages, edit=False):
    start_idx = (page - 1) * 5
    end_idx = min(start_idx + 5, len(lot_ids))
    page_lots = lot_ids[start_idx:end_idx]
    
    session = SessionLocal()
    
    text = f"📈 <b>Ваши лоты</b> (стр. {page}/{total_pages})\n\n"
    
    for lot_id in page_lots:
        lot = session.query(Lot).filter_by(id=lot_id).first()
        if lot:
            status = "🟢 Активен" if lot.is_active else "🔴 Завершен"
            sold = "✅ Продан" if lot.is_sold else "❌ Не продан"
            text += f"• <b>{lot.title}</b>\n"
            text += f"  💰 {lot.current_price:,.0f}$ | {status} | {sold}\n"
            text += f"  📊 {lot.bid_count} ставок\n\n"
    
    session.close()
    
    keyboard_buttons = []
    
    for lot_id in page_lots:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text="👁️ Просмотр",
                callback_data=f"view_lot_{lot_id}"
            )
        ])
    
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=f"mylots_page_{page-1}_{total_pages}"
        ))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(
            text="Вперед ▶️",
            callback_data=f"mylots_page_{page+1}_{total_pages}"
        ))
    
    if nav_buttons:
        keyboard_buttons.append(nav_buttons)
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    if edit:
        await message.edit_text(text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("view_lot_"))
async def view_lot(callback: CallbackQuery):
    lot_id = int(callback.data.split("_")[2])
    session = SessionLocal()
    lot = session.query(Lot).filter_by(id=lot_id).first()
    
    if not lot:
        await callback.answer("❌ Лот не найден")
        session.close()
        return
    
    seller = session.query(User).filter_by(tg_id=lot.seller_id).first()
    time_left = lot.end_time - datetime.utcnow()
    minutes = int(time_left.total_seconds() / 60)
    
    if minutes < 0:
        minutes = 0
    
    text = (
        f"📌 <b>{lot.title}</b>\n\n"
        f"📄 {lot.description}\n"
        f"💰 Текущая цена: <b>{lot.current_price:,.0f}$</b>\n"
        f"📈 Ставок: {lot.bid_count}\n"
        f"⏰ Осталось: {minutes} мин.\n\n"
        f"👤 <b>Продавец:</b>\n"
        f"   🎮 TSUM: <b>{seller.play_nick}</b>\n"
        f"   📱 TG: @{seller.tg_username}\n"
        f"⭐ Рейтинг: {seller.rating:.1f}"
    )
    
    back_button = InlineKeyboardButton(
        text="↩️ Назад к списку",
        callback_data="back_to_lots"
    )
    
    keyboard = lot_buttons(lot_id, callback.from_user.id, lot.seller_id)
    keyboard.inline_keyboard.append([back_button])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(
            text="📱 Написать продавцу в TG",
            url=f"https://t.me/{seller.tg_username}"
        )
    ])
    
    await callback.message.answer_photo(
        photo=lot.photo_id,
        caption=text,
        reply_markup=keyboard
    )
    session.close()
    await callback.answer()

@router.callback_query(F.data == "back_to_lots")
async def back_to_lots(callback: CallbackQuery):
    await active_auctions(callback.message)
    await callback.answer()
