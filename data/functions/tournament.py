import datetime

import pytz

from bot import bot
from .db import get_active_tour, get_tour, update_tour_status, get_tour_top_user, get_count_tour_users, add_balance
from ..config import TAKE_CHAT


async def end_tour():
    active_tour = get_active_tour()
    if active_tour is not None:
        active_tour = get_tour(active_tour[0])
        end_date = active_tour[3]
        utc_now = datetime.datetime.now(pytz.utc)
        moscow_tz = pytz.timezone('Europe/Moscow')
        moscow_time = utc_now.astimezone(moscow_tz)
        moscow_now = datetime.datetime.strftime(moscow_time, '%d.%m.%y %H')
        # await bot.send_message(1251379793, f'{end_date}\n\n{moscow_now}')
        end_date = datetime.datetime.strptime(end_date, '%d.%m.%y %H')
        moscow_now = datetime.datetime.strptime(moscow_now, '%d.%m.%y %H')

        if end_date <= moscow_now:
            try:
                winners = get_tour_top_user(active_tour[0])
                tour_users_count = get_count_tour_users(active_tour[0])
                prize_fund = tour_users_count * 0.09

                num_winners = len(winners)

                if num_winners == 1:
                    first_prize = prize_fund * 0.6
                elif num_winners == 2:
                    first_prize = prize_fund * 0.6
                    second_prize = prize_fund * 0.25
                else:
                    first_prize = prize_fund * 0.6
                    second_prize = prize_fund * 0.25
                    third_prize = prize_fund * 0.15

                for i, winner in enumerate(winners, start=1):
                    winner_id, winner_ball = winner[0], winner[1]

                    # Determine the prize based on the position
                    if i == 1:
                        prize = first_prize
                    elif i == 2:
                        prize = second_prize
                    else:
                        prize = third_prize

                    update_tour_status(active_tour[0])
                    add_balance(winner_id, prize)

                    await bot.send_message(
                        winner_id,
                        f'🎉 Вы заняли <b>{i}-е место</b> и выиграли <b>{prize} TON</b> в турнире набрав <b>{winner_ball}</b> очков!',
                        parse_mode='HTML'
                    )

                await bot.send_message(
                    -1002069022449,
                    f'''<b>🏆 Турнир успешно закончен!</b>

👥 Всего участников:  <b>{tour_users_count}</b>
💰 Фонд турнира: <b>{prize_fund}</b> TON\n''',
                    parse_mode='HTML'
                )
            except Exception as e:
                await bot.send_message(-1002069022449, f'Ошибка в турнире: {e}')




