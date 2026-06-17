from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from database import SessionLocal, Lot, Transaction, User
import logging

scheduler = AsyncIOScheduler()
logger = logging.getLogger(__name__)

async def check_auctions():
    session = SessionLocal()
    now = datetime.utcnow()
    
    expired_lots = session.query(Lot).filter(
        Lot.is_active == True,
        Lot.end_time <= now
    ).all()
    
    for lot in expired_lots:
        lot.is_active = False
        
        if lot.last_bidder_id:
            lot.is_sold = True
            lot.buyer_id = lot.last_bidder_id
            
            transaction = Transaction(
                lot_id=lot.id,
                seller_id=lot.seller_id,
                buyer_id=lot.last_bidder_id,
                price=lot.current_price
            )
            session.add(transaction)
            session.commit()
            
            seller = session.query(User).filter_by(tg_id=lot.seller_id).first()
            buyer = session.query(User).filter_by(tg_id=lot.last_bidder_id).first()
            
            logger.info(f"✅ Лот '{lot.title}' продан за {lot.current_price:,}$")
            
            try:
                from config import BOT_TOKEN
                from aiogram import Bot
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                bot = Bot(token=BOT_TOKEN)
                
                if seller:
                    seller_text = (
                        f"🎉 <b>Ваш лот продан!</b>\n\n"
                        f"📌 {lot.title}\n"
                        f"💰 Цена: {lot.current_price:,.0f}$\n\n"
                        f"👤 <b>Покупатель:</b>\n"
                        f"   🎮 TSUM: <b>{buyer.play_nick}</b>\n"
                        f"   📱 TG: @{buyer.tg_username}\n\n"
                        f"📌 <b>Как связаться:</b>\n"
                        f"1. В игре TSUM — найди <b>{buyer.play_nick}</b>\n"
                        f"2. В Telegram — напиши @{buyer.tg_username}\n\n"
                        f"⚠️ <i>После завершения сделки нажми кнопку ниже</i>"
                    )
                    
                    seller_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(
                            text="✅ Сделка завершена",
                            callback_data=f"confirm_deal_{lot.id}_seller"
                        )],
                        [InlineKeyboardButton(
                            text="❌ Пожаловаться на покупателя",
                            callback_data=f"report_user_{buyer.tg_id}"
                        )],
                        [InlineKeyboardButton(
                            text="📱 Написать в Telegram",
                            url=f"https://t.me/{buyer.tg_username}"
                        )]
                    ])
                    
                    await bot.send_message(
                        seller.tg_id,
                        seller_text,
                        reply_markup=seller_keyboard
                    )
                
                if buyer:
                    buyer_text = (
                        f"🎉 <b>Вы выиграли аукцион!</b>\n\n"
                        f"📌 {lot.title}\n"
                        f"💰 Ваша ставка: {lot.current_price:,.0f}$\n\n"
                        f"👤 <b>Продавец:</b>\n"
                        f"   🎮 TSUM: <b>{seller.play_nick}</b>\n"
                        f"   📱 TG: @{seller.tg_username}\n\n"
                        f"📌 <b>Как связаться:</b>\n"
                        f"1. В игре TSUM — найди <b>{seller.play_nick}</b>\n"
                        f"2. В Telegram — напиши @{seller.tg_username}\n\n"
                        f"⚠️ <i>После завершения сделки нажми кнопку ниже</i>"
                    )
                    
                    buyer_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(
                            text="✅ Сделка завершена",
                            callback_data=f"confirm_deal_{lot.id}_buyer"
                        )],
                        [InlineKeyboardButton(
                            text="❌ Пожаловаться на продавца",
                            callback_data=f"report_user_{seller.tg_id}"
                        )],
                        [InlineKeyboardButton(
                            text="📱 Написать в Telegram",
                            url=f"https://t.me/{seller.tg_username}"
                        )]
                    ])
                    
                    await bot.send_message(
                        buyer.tg_id,
                        buyer_text,
                        reply_markup=buyer_keyboard
                    )
                    
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления: {e}")
    
    session.commit()
    session.close()

def start_scheduler():
    scheduler.add_job(
        check_auctions,
        trigger=IntervalTrigger(minutes=1),
        id="check_auctions",
        next_run_time=datetime.utcnow()
    )
    scheduler.start()
    logger.info("🔄 Scheduler запущен, проверка каждую минуту")
