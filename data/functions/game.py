from time import time

from bot import mdb, bot
from datetime import datetime, timedelta
import pytz
import random
from data.config import LOGS, TAKE_CHAT
from data.functions.db import add_balance, get_active_tour, add_ball_to_tour_user, get_tour_user_exist
from data.functions.translate import translate_text
from data.functions.db_squads import get_squad_id_by_user_id, add_squad_balance


def get_current_time():
    tz_moscow = pytz.timezone('Europe/Moscow')
    current_time = datetime.now(tz_moscow)
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time


async def create_game(bet, player_id):
    game_id = mdb.get_game_count()
    date = get_current_time()
    mdb.add_game(game_id, bet, player_id, date)

    return game_id


async def start_game(game_id, player2_id):
    mdb.start_game(game_id, player2_id)


async def finish_game(game_id, winner, loser, user_message_ids):
    game = mdb.get_game(game_id)
    bet = game[1]
    mdb.finish_game(game_id, winner)
    prize = round(bet * 2 * 0.90, 4)
    add_balance(winner, prize)

    try:
        photo = 'https://telegra.ph/file/3d20a37c33b5857b0eab6.jpg'
        translated_text = translate_text(f'<b>⚔️ Бой номер #{game_id}</b>\n\n'
                                           f'Ваша атака оказался решающим для робота противника и вы выиграли бой и получили 90% от ставок в размере {prize} TON!', winner)
        await bot.send_photo(
            winner,
            photo,
            translated_text,
            parse_mode='HTML'
        )

        defeat_photo = 'https://telegra.ph/file/f79735301f803d63995e4.jpg'
        translated_text = translate_text(f'<b>⚔️ Бой номер #{game_id}</b>\n\n'
                                           f'Последний удар противника оказался решающим для вашего робота.\n'
                                           f'У вас закончилось здоровье и вы проиграли.', loser)
        await bot.send_photo(
            loser,
            defeat_photo,
            translated_text,
            parse_mode='HTML'
        )

        try:
            player_1_name = await bot.get_chat(winner)
            player_1_name = player_1_name.first_name
            player_1_name = f'<a href="tg://user?id={winner}">{player_1_name}</a>'

            player_2_name = await bot.get_chat(loser)
            player_2_name = player_2_name.first_name
            player_2_name = f'<a href="tg://user?id={loser}">{player_2_name}</a>'
        except:
            player_1_name = f'<a href="tg://user?id={winner}">Пользователь</a>'
            player_2_name = f'<a href="tg://user?id={loser}">пользователя</a>'

        if get_active_tour() and prize not in [0, 0.0]:
            if get_tour_user_exist(winner, get_active_tour()[0]):
                add_ball_to_tour_user(get_active_tour()[0], winner)
                translated_text = translate_text(f'⚡️ Вы так же получили <b>1 очков</b> турнира за победу в бою!', winner)
                await bot.send_message(
                    winner,
                    translated_text,
                    parse_mode='HTML'
                )
    
        take2_text = f'<a href="https://t.me/TonTakeRoBot">TonTakeRoBot</a>\n' \
                            f'<b>⚔️ Бой номер #{game_id}</b> завершен!\n\n' \
                            f'{player_1_name} против {player_2_name}\n\n' \
                            f'<b>👑 Победитель</b> {player_1_name}\n' \
                            f'🎁 Получено <b>{prize}</b> TON'
            
        await bot.send_message(
                    LOGS,
                    take2_text
                )
                
        squad_id = get_squad_id_by_user_id(winner)
        if squad_id:
            squad_prize = round(prize * 0.05, 4)
            add_squad_balance(squad_id, squad_prize)

        if prize not in [0, 0.0]:
            translated_text = (f'<a href="https://t.me/TonTakeRoBot">TonTakeRoBot</a>\n'
                                               f'<b>⚔️ Бой номер #{game_id}</b> завершен!\n\n'
                                               f'{player_1_name} против {player_2_name}\n\n'
                                               f'<b>👑 Победитель</b> {player_1_name}\n'
                                               f'🎁 Получено <b>{prize}</b> TON')
            await bot.send_message(
                TAKE_CHAT,
                translated_text,
                parse_mode='HTML'
            )
            

    except Exception as e:
        print(e)

    def delete_user_message_ids(user_id, user2_id, user_message_ids):
        user_id_str = str(user_id)
        user2_id_str = str(user2_id)

        if user_id in user_message_ids:
            del user_message_ids[user_id]
        if user_id_str in user_message_ids:
            del user_message_ids[user_id_str]
        if user2_id in user_message_ids:
            del user_message_ids[user2_id]
        if user2_id_str in user_message_ids:
            del user_message_ids[user2_id_str]

    # Delete user message IDs
    delete_user_message_ids(winner, loser, user_message_ids)

    




async def attack_game(attacker_id, defender_id, game_id):
    attacker_robot = mdb.get_user_active_robot(attacker_id)
    defender_robot = mdb.get_user_active_robot(defender_id)
    attacker_damage = attacker_robot[4]
    defender_health = defender_robot[3]
    defender_armor = defender_robot[6]
    defender_robot_id = defender_robot[1]
    damage = random.randint(2, attacker_damage)
    if damage < defender_armor:
        damage = 1
    time_now = time()

    mdb.update_robot(defender_id, defender_robot_id, 'health', damage, False)
    mdb.update_last_attack(time_now, game_id)
    mdb.update_turn(defender_id, game_id)

    return defender_health, damage, defender_armor


async def defense_game(defender_id, attacker_id, game_id):
    defender_robot = mdb.get_user_active_robot(defender_id)
    health = defender_robot[3]
    max_health = defender_robot[8]
    armor = random.randint(1, defender_robot[6])
    time_now = time()

    if health + armor > max_health:
        armor = max_health - health

    mdb.update_turn(attacker_id, game_id)
    mdb.update_last_attack(time_now, game_id)
    mdb.update_robot(defender_id, defender_robot[1], 'health', armor)

    return armor, health


async def heal_user_robots():
    robots = mdb.get_unhealthy_robots()

    for robot in robots:
        if not mdb.check_user_playable(robot[0]):
            heal = robot[5]
            health = robot[3]
            max_health = robot[8]

            if heal + health < max_health:
                mdb.update_robot(robot[0], robot[1], 'health', heal)
            else:
                heal = max_health - health
                mdb.update_robot(robot[0], robot[1], 'health', heal)
                try:
                    await bot.send_message(
                        robot[0],
                        f'<i>🚀  Ваш робот полностью восстановлен, можете вступить в бой!</i>'
                    )
                except Exception as e:
                    print(e)


def give_robot_to_user(user_id):
    rand_number = random.randint(1, 100)

    if rand_number <= 35:
        rand_damage = random.randint(6, 12)
        mdb.add_robot(
            user_id=user_id,
            robot_id=1000,
            name="Исследователь",
            health=110,
            damage=rand_damage,
            heal=15,
            armor=1
        )
        mdb.update_robot_status(user_id=user_id, robot_id=1000)

        return "Исследователь"

    elif 36 <= rand_number <= 65:
        rand_damage = random.randint(7, 13)
        mdb.add_robot(
            user_id=user_id,
            robot_id=1001,
            name="Силач",
            health=100,
            damage=rand_damage,
            heal=12,
            armor=2
        )
        mdb.update_robot_status(user_id=user_id, robot_id=1001)

        return "Силач"

    elif 66 <= rand_number <= 85:
        rand_damage = random.randint(7, 12)
        mdb.add_robot(
            user_id=user_id,
            robot_id=1002,
            name="Броневик",
            health=100,
            damage=rand_damage,
            heal=13,
            armor=3
        )
        mdb.update_robot_status(user_id=user_id, robot_id=1002)

        return "Броневик"

    elif 86 <= rand_number <= 95:
        rand_damage = random.randint(6, 13)
        mdb.add_robot(
            user_id=user_id,
            robot_id=1003,
            name="Защитник",
            health=110,
            damage=rand_damage,
            heal=13,
            armor=4
        )
        mdb.update_robot_status(user_id=user_id, robot_id=1003)

        return "Защитник"

    else:
        rand_damage = random.randint(6, 14)
        mdb.add_robot(
            user_id=user_id,
            robot_id=1004,
            name="Терминатор",
            health=105,
            damage=rand_damage,
            heal=14,
            armor=5
        )
        mdb.update_robot_status(user_id=user_id, robot_id=1004)

        return "Терминатор"


def has_one_hour_passed(original_date_str):
    original_date = datetime.strptime(original_date_str, "%Y-%m-%d %H:%M:%S")
    original_date = pytz.timezone('Europe/Moscow').localize(original_date)

    tz_moscow = pytz.timezone('Europe/Moscow')
    current_date = datetime.now(tz_moscow)

    time_difference = current_date - original_date

    if time_difference >= timedelta(hours=1):
        return True
    else:
        return False


async def check_game_valid():
    active_games = mdb.get_active_games()
    for game in active_games:
        if game[2] == "expectation" and has_one_hour_passed(game[6]):
            mdb.delete_game(game[0])
            add_balance(game[3], game[1])
            try:
                await bot.send_message(
                    game[3],
                    f"⭕️ Ваша игра с номером #{game[0]} была неактивна в течение 1 часа и была удалена!\n"
                    f"💎 На ваш баланс была возвращена сумма ставки в размере {game[1]} TON."
                )
            except Exception as e:
                print(e)