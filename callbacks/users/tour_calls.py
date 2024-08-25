from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot import dp, bot
from data.config import TAKE_CHAT
from data.functions.db import get_balance, get_tour, add_to_tour, get_tour_user_exist, decrease_balance, get_count_tour_users


@dp.callback_query_handler(text_startswith='tour-run_')
async def add_user_to_tour(call: CallbackQuery):
    user = call.from_user
    tour_id = call.data.split('_')[1]
    tour = get_tour(tour_id)
    user_status = get_tour_user_exist(user.id, tour_id)
    user_ton_balance = get_balance(user.id)
    if not tour[1]:
        await call.answer(f'🚫 Турнир №{tour[0]} уже завершен, вы не можете участвовать в нем!')
        return

    if user_status:
        await call.answer(f'🚫 Вы уже зарегистрированы на этот турнир, вы не можете зарегистрироваться снова!', True)
        return

    if user_ton_balance < 0.1:
        await call.answer(f'🚫 Недостаточно средств на балансе, цена участия 0.1 TON!', True)
        return

    add_to_tour(tour[0], user.id)
    decrease_balance(user.id, 0.1)

    await call.message.answer('''<b>✅ Вы успешно зарегистрировались на турнир, с вашего баланса списано 0.1 TON!</b>
        
ℹ️ Теперь можешь сражаться в многопользовательском режиме за 1-е место в турнире!
💸 С каждой победой ты будешь все ближе к денежному призу!!!''', parse_mode='HTML')

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text='🚀 Присоединиться в турнир', url='https://t.me/TonTakeRoBot'))
    tour_users_count = get_count_tour_users(tour_id)
    await bot.send_message(TAKE_CHAT, f'''<b>🏆 Новый участник в турнире №{tour[0]} @TonTakeRoBot!</b>

👤 @{user.username}, <code>{user.id}

Приз в турнире {round(tour_users_count * 0.09, 2)} TON</code>''',
                           reply_markup=markup,
                           parse_mode='HTML')