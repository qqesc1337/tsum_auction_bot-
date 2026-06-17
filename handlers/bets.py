from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime
from database import SessionLocal, Lot, User
from keyboards.inline import bet_keyboard, lot_buttons

router = Router()

class BetState(StatesGroup):
    custom_bet = State()

@router.callback_query(F.data.startswith("bet_"))
async def start_bet(callback: CallbackQuery, state: FSMContext):
    lot_id = int(callback.data.split("_")[1])
    session = SessionLocal()
    lot = session.query(Lot).filter_by(id=lot_id).first()
    user = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    
    if not lot or not lot.is_active:
        await callback.answer("❌ Аукцион уже завершен!")
        session.close()
        return
    
    if user.is_banned:
        await callback.answer("⛔ Вы забанены!")
        session.close()
        return
    
    if lot.seller_id == callback.from_user.id:
        await callback.answer("❌ Вы не можете делать ставку на свой лот!")
        session.close()
        return
    
    await callback.message.edit_reply_markup(
        reply_markup=bet_keyboard(lot_id, lot.current_price)
    )
    session.close()
    await callback.answer()

@router.callback_query(F.data.startswith("bet_quick_"))
async def quick_bet(callback: CallbackQuery):
    _, _, lot_id, amount = callback.data.split("_")
    lot_id = int(lot_id)
    amount = float(amount)
    
    session = SessionLocal()
    lot = session.query(Lot).filter_by(id=lot_id).first()
    user = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    
    if amount < lot.min_bet:
        await callback.answer(f"❌ Минимальная ставка: {lot.min_bet:.2f}$")
        session.close()
        return
    
    lot.current_price = amount
    lot.min_bet = amount * 1.05
    lot.last_bidder_id = callback.from_user.id
    lot.bid_count += 1
    
    session.commit()
    session.close()
    
    await callback.message.edit_caption(
        caption=f"📌 {lot.title}\n"
                f"💰 Новая ставка: {amount:,.0f}$\n"
                f"👤 Последний: @{user.tg_username}",
        reply_markup=lot_buttons(lot_id, callback.from_user.id, lot.seller_id)
    )
    await callback.answer(f"✅ Ставка {amount:,.0f}$ принята!")

@router.callback_query(F.data.startswith("bet_custom_"))
async def custom_bet_start(callback: CallbackQuery, state: FSMContext):
    lot_id = int(callback.data.split("_")[2])
    await state.update_data(lot_id=lot_id)
    await callback.message.answer("✏️ Введите вашу сумму ставки:")
    await state.set_state(BetState.custom_bet)
    await callback.answer()

@router.message(BetState.custom_bet)
async def custom_bet_process(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        data = await state.get_data()
        lot_id = data['lot_id']
        
        session = SessionLocal()
        lot = session.query(Lot).filter_by(id=lot_id).first()
        user = session.query(User).filter_by(tg_id=message.from_user.id).first()
        
        if amount < lot.min_bet:
            await message.answer(f"❌ Минимальная ставка: {lot.min_bet:.2f}$")
            session.close()
            return
        
        lot.current_price = amount
        lot.min_bet = amount * 1.05
        lot.last_bidder_id = message.from_user.id
        lot.bid_count += 1
        session.commit()
        session.close()
        
        await message.answer(f"✅ Ставка {amount:,.0f}$ принята!")
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите число!")
