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

def main_menu_keyboard(is_admin=False, is_owner=False):
    keyboard = [
        [InlineKeyboardButton(text="📊 Моя статистика", callback_data="my_stats"),
         InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile")],
        [InlineKeyboardButton(text="➕ Создать лот", callback_data="create_lot"),
         InlineKeyboardButton(text="📋 Активные аукционы", callback_data="active_lots")],
        [InlineKeyboardButton(text="📈 Мои лоты", callback_data="my_lots"),
         InlineKeyboardButton(text="🏆 Достижения", callback_data="achievements")],
        [InlineKeyboardButton(text="⭐ Избранное", callback_data="favorites"),
         InlineKeyboardButton(text="🎲 Случайный лот", callback_data="random_lot")],
        [InlineKeyboardButton(text="🔍 Поиск", callback_data="search_lots"),
         InlineKeyboardButton(text="📖 Инструкция", callback_data="instructions")],
        [InlineKeyboardButton(text="🏆 Топ пользователей", callback_data="top_users")]
    ]
    
    if is_admin or is_owner:
        keyboard.append([InlineKeyboardButton(text="🛠 Админ-панель", callback_data="admin_panel")])
    
    if is_owner:
        keyboard.append([InlineKeyboardButton(text="👑 Управление админами", callback_data="admin_manage")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
