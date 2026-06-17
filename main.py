import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import BOT_TOKEN
from handlers import start, auction, profile, admin, bets, admin_manage, extra_features, deal_confirm
from scheduler import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Подключаем все роутеры
    dp.include_router(start.router)
    dp.include_router(auction.router)
    dp.include_router(profile.router)
    dp.include_router(admin.router)
    dp.include_router(bets.router)
    dp.include_router(admin_manage.router)
    dp.include_router(extra_features.router)
    dp.include_router(deal_confirm.router)
    
    start_scheduler()
    
    logger.info("🚀 Бот TSUM Auction запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
