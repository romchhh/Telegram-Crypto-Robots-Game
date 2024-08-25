import sqlite3
import datetime
import pytz
import asyncio

from bot import bot
from data.functions.db_squads import get_squad_with_highest_balance, get_squad_leader, get_squads_balance_sum, get_all_squads, set_squad_balance, get_squad_admin_time, log_squad_payment
from data.functions.db import add_balance_leader
from ..config import TAKE_CHAT, LOGS


async def reset_squads_balance():
    squads = get_all_squads()
    for squad in squads:
        squad_id = squad[0]
        set_squad_balance(squad_id, 0)
        
        
async def end_squad():
    # Получаем время из таблицы squads_admin
    day, hour, minute = get_squad_admin_time()
    
    print(day, hour, minute)

    now = datetime.datetime.now(pytz.timezone('Europe/Moscow'))
    if now.weekday() == day and now.hour == hour and now.minute >= minute and now.second >= 0:
        try:
            squad_id = get_squad_with_highest_balance()

            if squad_id is not None:
                leader_id = get_squad_leader(squad_id)

                if leader_id is not None:
                    prize_fund = await get_squads_balance_sum()
                    add_balance_leader(leader_id, prize_fund)

                    await bot.send_message(
                        leader_id,
                        f'🏆 Ваш сквад выиграл еженедельный турнир сквадов! И вы как лидер получили баланс всех сквадов в размере {prize_fund} TON!',
                        parse_mode='HTML'
                    )

                    await bot.send_message(
                        squad_id,  # negative squad_id is used to represent a group chat
                        f'🏆 Поздравляем! Ваш сквад выиграл еженедельный турнир сквадов! Ваш <a href="tg://user?id={leader_id}">лидер</a> получил баланс всех сквадов в размере {prize_fund} TON!',
                        parse_mode='HTML'
                    )

                    # Отправляем сообщение в чат TAKE
                    await bot.send_message(
                        TAKE_CHAT,
                        f'🏆 Еженедельный турнир сквадов закончен! Сквад под руководством <a href="tg://user?id={leader_id}">лидера</a> выиграл баланс всех сквадов в размере  {prize_fund} TON!',
                        parse_mode='HTML'
                    )

                    # Log the payment with group name
                    log_squad_payment(squad_id, leader_id, prize_fund)

            await reset_squads_balance()

        except Exception as e:
            await bot.send_message(LOGS, f'Ошибка в турнире: {e}')
