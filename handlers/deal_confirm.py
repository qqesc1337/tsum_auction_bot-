from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import SessionLocal, Lot, User
from config import BOT_TOKEN
from aiogram import Bot

router = Router()

@router.callback_query(F.data.startswith("confirm_deal_"))
async def confirm_deal(callback: CallbackQuery):
    data_parts = callback.data.split("_")
    lot_id = int(data_parts[2])
    role = data_parts[3]
    
    session = SessionLocal()
    lot = session.query(Lot).filter_by(id=lot_id).first()
    
    if not lot or not lot.is_sold:
        await callback.answer("❌ Лот не найден или уже завершен!")
        session.close()
        return
    
    user = session.query(User).filter_by(tg_id=callback.from_user.id).first()
    
    if not user:
        await callback.answer("❌ Вы не зарегистрированы!")
        session.close()
        return
    
    if role == "seller" and lot.seller_id != callback.from_user.id:
        await callback.answer("❌ Вы не являетесь продавцом этого лота!")
        session.close()
        return
    
    if role == "buyer" and lot.buyer_id != callback.from_user.id:
        await callback.answer("❌ Вы не являетесь покупателем этого лота!")
        session.close()
        return
    
    if lot.confirmed_by_seller and lot.confirmed_by_buyer:
        await callback.answer("✅ Сделка уже подтверждена обеими сторонами!")
        session.close()
        return
    
    if role == "seller":
        lot.confirmed_by_seller = True
    else:
        lot.confirmed_by_buyer = True
    
    session.commit()
    
    seller = session.query(User).filter_by(tg_id=lot.seller_id).first()
    buyer = session.query(User).filter_by(tg_id=lot.buyer_id).first()
    
    if lot.confirmed_by_seller and lot.confirmed_by_buyer:
        seller.deals_count += 1
        buyer.deals_count += 1
        session.commit()
        
        await callback.message.answer(
            f"✅ <b>Сделка полностью завершена!</b>\n\n"
            f"📌 {lot.title}\n"
            f"💰 {lot.current_price:,.0f}$\n\n"
            f"👤 Продавец: <b>{seller.play_nick}</b> (@{seller.tg_username})\n"
            f"👤 Покупатель: <b>{buyer.play_nick}</b> (@{buyer.tg_username})\n\n"
            f"⭐ Рейтинг обновлен!\n"
            f"Не забудьте оставить отзыв!"
        )
        
        try:
            bot = Bot(token=BOT_TOKEN)
            
            await bot.send_message(
                seller.tg_id,
                f"✅ Сделка по лоту '{lot.title}' завершена!\n"
                f"Покупатель <b>{buyer.play_nick}</b> (@{buyer.tg_username}) подтвердил получение."
            )
            await bot.send_message(
                buyer.tg_id,
                f"✅ Сделка по лоту '{lot.title}' завершена!\n"
                f"Продавец <b>{seller.play_nick}</b> (@{seller.tg_username}) подтвердил оплату."
            )
        except Exception as e:
            print(f"Ошибка отправки уведомления: {e}")
        
    else:
        if role == "seller":
            await callback.message.answer(
                f"✅ Вы подтвердили сделку как <b>ПРОДАВЕЦ</b>!\n\n"
                f"👤 Покупатель: <b>{buyer.play_nick}</b> (@{buyer.tg_username})\n"
                f"Ожидайте подтверждения от покупателя.\n\n"
                f"📌 Свяжитесь в TSUM или Telegram: @{buyer.tg_username}"
            )
        else:
            await callback.message.answer(
                f"✅ Вы подтвердили сделку как <b>ПОКУПАТЕЛЬ</b>!\n\n"
                f"👤 Продавец: <b>{seller.play_nick}</b> (@{seller.tg_username})\n"
                f"Ожидайте подтверждения от продавца.\n\n"
                f"📌 Свяжитесь в TSUM или Telegram: @{seller.tg_username}"
            )
    
    session.close()
    await callback.answer()
