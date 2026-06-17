from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def lot_buttons(lot_id, user_id, seller_id):
    keyboard = [
        [InlineKeyboardButton(text="💰 Сделать ставку", callback_data=f"bet_{lot_id}")],
        [InlineKeyboardButton(text="👤 Профиль продавца", callback_data=f"seller_profile_{seller_id}")],
        [InlineKeyboardButton(text="⭐ В избранное", callback_data=f"favorite_{lot_id}")]
    ]
    
    if user_id != seller_id:
        keyboard.append([InlineKeyboardButton(text="⚠️ Пожаловаться", callback_data=f"report_user_{seller_id}")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def seller_profile_buttons(seller_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Оставить отзыв", callback_data=f"leave_review_{seller_id}")],
        [InlineKeyboardButton(text="📋 Все отзывы", callback_data=f"all_reviews_{seller_id}")],
        [InlineKeyboardButton(text="🚫 В черный список", callback_data=f"blacklist_{seller_id}")]
    ])

def admin_user_buttons(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔨 Забанить", callback_data=f"admin_ban_{user_id}")],
        [InlineKeyboardButton(text="🚫 Метка СКАМ", callback_data=f"admin_scam_{user_id}")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data=f"admin_stats_user_{user_id}")],
        [InlineKeyboardButton(text="📝 Отзывы", callback_data=f"admin_reviews_{user_id}")]
    ])

def bet_keyboard(lot_id, current_price):
    min_bet = current_price * 1.05
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💵 {int(min_bet):,}", callback_data=f"bet_quick_{lot_id}_{int(min_bet)}"),
         InlineKeyboardButton(text=f"💵 {int(min_bet*1.1):,}", callback_data=f"bet_quick_{lot_id}_{int(min_bet*1.1)}")],
        [InlineKeyboardButton(text=f"💵 {int(min_bet*1.2):,}", callback_data=f"bet_quick_{lot_id}_{int(min_bet*1.2)}")],
        [InlineKeyboardButton(text="✏️ Своя сумма", callback_data=f"bet_custom_{lot_id}")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data=f"back_to_lot_{lot_id}")]
    ])
