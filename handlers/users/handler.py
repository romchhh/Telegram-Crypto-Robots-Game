import os
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, KeyboardButton, ContentTypes, ReplyKeyboardMarkup, \
    InputFile
    
import asyncio
import datetime
import time
import pytz


from aiogram.utils.markdown import hbold, hcode, hitalic
from bot import bot, dp, storage, scheduler, mdb
from data.functions.db import *
from data.functions.text import get_start_text, robot_chances_text
from data.functions.tournament import end_tour
from data.functions.squad import end_squad
from data.payments.cryptobot import create_cry_invoice
from data.payments.rocket import create_invoice
from data.functions.game import heal_user_robots, give_robot_to_user, check_game_valid
from filters import IsPrivate, IsSubscribed
from keyboards.users.keyboards import bet_key, deposit_key, back_key, withdraw_key, market_key, \
    my_robots_key, get_robot_keyboard, locations_key, bazar_key, nft_key, create_start_keyboard, withdraw_key_take
from states.users.states import DepositTon, WithdrawTon, DepositTake, DepositCry, WithdrawTake
from data.payments.tonscan_api import TonScan
from data.functions.db_squads import add_group_to_db, add_user_to_squad, get_squads_count, get_top_squads, get_top_payments

from data.payments.rocket import get_all_balance
from aiogram.dispatcher.filters import Command

from data.config import administrators, NFT_COLLECTIONS
from keyboards.admins.keyboards import cancel_adm_key, admin_key, admin_search_key, confirm_new_robot
from keyboards.users.keyboards import join_game_key, get_language_keyboard
from states.admins.states import SendAllPhoto, SendAllText, StartTour, EditUserBalance, SearchUser, NewRobot, \
    DeleteRobot
from data.functions.translate import translate_text

html = 'HTML'


async def scheduler_jobs():
    scheduler.add_job(end_tour, "interval", minutes=10)
    scheduler.add_job(end_squad, 'interval', minutes=60)
    scheduler.add_job(heal_user_robots, "interval", minutes=5)
    scheduler.add_job(check_game_valid, "interval", minutes=10)


async def antiflood(*args, **kwargs):
    m = args[0]
    await m.answer("Не спеши :)")


async def on_startup(dp):
    await scheduler_jobs()
    await bot.send_message(-1002069022449, "Бот запушен!")
    print(get_active_tour())


async def on_shutdown(dp):
    await storage.close()
    await bot.close()
    me = await bot.get_me()
    print(f'Bot: @{me.username}\nОстановлен!')


@dp.message_handler(commands=['getid'])
async def get_id(msg: types.Message):
    await msg.answer(f'<code>{msg.chat.id}</code>')



@dp.message_handler(content_types=types.ContentType.NEW_CHAT_MEMBERS)
async def on_bot_added(message: types.Message):
    for new_member in message.new_chat_members:
        if new_member.id == (await bot.me).id:

            group_name = message.chat.title
            
            print(group_name)

            link = f'https://t.me/TonTakeRoBot?start=joinsquad_{message.chat.id}'
            inline_btn = InlineKeyboardButton("Присоединиться к скваду", url=f'{link}')
            inline_kb = InlineKeyboardMarkup().add(inline_btn)

            welcome_text = (
                "Добро пожаловать в сквады TonTakeRobot! 🤖\n\n"
                f"Здесь ты мможешь вступить в {group_name} сквад и бороться с другими "
                "скавадами в еженедельном турнире. 🏆\n\n"
                "Каждую неделю сквад с наибольшим количеством побед заберет приз в "
                "размере 5% от каждого боя, проведенного в сквадах. 💰\n\n"
                "Нажми на кнопку ниже, чтобы присоединиться к скваду!"
            )

            await message.answer(welcome_text, reply_markup=inline_kb)

            leader_id = message.from_user.id
            add_group_to_db(message.chat.id, leader_id, group_name)  # Обновить вызов функции
            add_user_to_squad(message.chat.id, leader_id)


            
            
@dp.message_handler(IsPrivate(), commands=["start"])
@dp.throttled(antiflood, rate=1)
async def start(message: types.Message):
    user = message.from_user
    robots = mdb.get_user_robots(user.id)
    ref = 0

    if len(message.text) > 6:
        try:
            int(message.text.split()[1])
            ref = message.text.split()[1]
        except ValueError:
            pass

    if not check_user(user.id):
        # prompt user to select language
        language_keyboard = get_language_keyboard()
        await message.answer("Please select your language:", reply_markup=language_keyboard)
        add_user(user.id, ref)
        # if ref != 0:
        #     if ref:
        #         add_refferal_balance(ref)
        #         await bot.send_message(ref,
        #                                     f'👤 Вы пригласили <a href="tg://user?id={user.id}"><b>{user.first_name}</b></a> и получили <b>0.03</b> TAKE')
        #     else:
        #         print(f"Referral user with ID {ref} not found.")
    elif len(robots) == 0:
        await message.answer(translate_text(robot_chances_text(), user.id), reply_markup=get_robot_keyboard(user.id))

    elif 'joingame_' in message.text:
        game_id = message.text.split('_')[1]
        game = mdb.get_game(game_id)
        if game:
            player_id = game[3]
            if player_id != user.id:
                await join_game(user, game_id)
                return

    elif 'joinsquad_' in message.text:
        group_id = message.text.split('_')[1]
        user_id = message.from_user.id
        if add_user_to_squad(group_id, user_id):
            await message.answer(f"Вы успешно вступили в сквад {group_id}!")
        else:
            await message.answer("Вы уже состоите в скваде!")

    else:
        await message.answer(translate_text(get_start_text(), user.id), reply_markup=create_start_keyboard(user.id))




async def join_game(user, game_id):
    game = mdb.get_game(game_id)
    player_id = game[3]

    try:
        player = await bot.get_chat(player_id)
        player = player.first_name
        player = f'<a href="tg://user?id={player_id}">{player}</a>'
    except:
        player = f'<a href="tg://user?id={player_id}">Пользователь</a>'

    text = f'<b>#️⃣ Бой номер:</b> #{game[0]}\n' \
           f'<b>💎 Ставка:</b> {game[1]} TON\n' \
           f'📆 Дата создание: {game[6]}\n' \
           f'<b>👤 Создатель:</b> {player}\n\n' \
           f'<i>Уверены что хотите начать бой?</i>'

    keyboard = await join_game_key(game[0])

    await bot.send_message(
        user.id,
        text,
        reply_markup=keyboard,
        parse_mode='HTML'
    )


@dp.message_handler(lambda message: message.text in [translate_text("👝 Привязать кошелек", message.from_user.id), "👝 Link wallet"])
@dp.throttled(antiflood, rate=1)
async def process_wallet_request(message: types.Message):

    user_id = message.from_user.id
    wallet_address = 'EQCSvwpsHiBvdS2nxIJ77Z7D-8MNqe4vGy0ZBW50WM1WJtvO'
    comment = f'TonTakeRoBot{user_id}'

    bonus_info = (
        '🚀 После успешной привязки вашего кошелька с наличием НФТ ТонТейка вы получите бонус в виде ускорения'
        'восстановления робота и скидки на прокачку! Также ваш робот будет ремонтироваться автоматически!'
    )

    message_text = (
        'Пожалуйста переведите 0.01 TON с кошелька который хотите привязать на адрес '
        f'`{wallet_address}`\n\n'
        'С комментарием: `{}`\n\n'
        'Внимание! Нужно переводить ровно 0.01 TON!\n\n'
        'После нажмите на кнопку "Проверить платёж".\n\n'
        .format(comment)
    )

    message_text_with_bonus = f'{message_text}\n{bonus_info}'

    await message.answer(translate_text(message_text_with_bonus, user_id), reply_markup=nft_key(message.from_user.id), parse_mode='Markdown')


@dp.message_handler(lambda message: message.text in [translate_text("🖼 NFTs", message.from_user.id), "🖼 NFTs"])
@dp.throttled(antiflood, rate=1)
async def process_nft_request(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    wallet = get_user_wallet(chat_id)
    if not wallet:  # Check if wallet is None or empty
        await bot.send_message(chat_id, translate_text("Сначала привяжите свой кошелек к боту", user_id))
    else:
        check_nft = check_owner_nft(address=wallet)
        if check_nft:
            text = translate_text(f"🎉 Отлично! На вашем кошельке ({wallet}) есть НФТ из нашей коллекции!\n\n"
                                   f"🎁 Это дает вам следующие бонусы:\n"
                                   f"- 10% скидка на прокачку наших роботов\n"
                                   f"- Увеличение скорости восстановления вашего робота в 2 раза\n"
                                   f"- Бонус +1 к силе удара в битвах\n\n"
                                   f"Наслаждайтесь своими преимуществами и удачи в боях! 💪🎉", user_id)
            await bot.send_message(chat_id, text)
            current_nft_status = get_user_nft_status(chat_id)
            if current_nft_status != 1:
                set_user_nft_status(chat_id, 1)
        else:
            await bot.send_message(chat_id, translate_text(f"❌ На вашем кошельке ({wallet}) нет НФТ из нашей коллекции", user_id))
            
            set_user_nft_status(chat_id, 0)



     
def check_owner_nft(address):
    try:
        ton = TonScan()
        res = ton.unpack_address(address)
        print(res)
        if res['ok']:
            address = res['result']
            for collection in NFT_COLLECTIONS:
                collection = collection.replace('https://getgems.io/collection/', '')
                collection_items = ton.collection_items(collection)
                if address in str(collection_items):
                    return True
                    break
        return False
    except Exception as e:
        print('Err422: ', e)
        return False                        


@dp.message_handler(lambda message: message.text in [translate_text("📸 Сквады", message.from_user.id), "📸 Сквады"])
@dp.throttled(antiflood, rate=1)
async def team(message: types.Message):
    welcome_text = (
        "Добро пожаловать в сквады TonTakeRobot! 🤖\n\n"
        "Здесь ты сможешь создать свой собственный сквад и бороться с другими "
        "скавадами в еженедельном турнире. 🏆\n\n"
        "Каждую неделю сквад с наибольшим количеством побед заберет приз в "
        "размере 5% от каждого боя, проведенного в сквадах. 💰\n\n"
        "Чтобы участвовать в сквадах, просто добавьте бота в свой чат.\n\n"
    )

    top_squads = get_top_squads(10)
    
    async def get_user_name(user_id):
        user = await bot.get_chat(user_id)
        return user.first_name

    squads_info = ""
    if top_squads:
        squads_info += "<b>Топ сквадов:</b>\n\n"
        for i, (squad_id, group_name, leader_id, balance) in enumerate(top_squads, start=1):
            leader_name = await get_user_name(leader_id)
            squads_info += f"{i}. Сквад: {group_name}, Лидер: {leader_name}, Баланс: {balance} TON\n\n"
    else:
        squads_info = "Нет доступных сквадов."

    # Retrieve top 10 payment

    top_payments = get_top_payments(10)
    
    payments_info = ""
    if top_payments:
        payments_info += "<b>Топ выплат:</b>\n\n"
        for i, (group_id, leader_id, group_name, prize) in enumerate(top_payments, start=1):
            leader_name = await get_user_name(leader_id)
            payments_info += f"{i}. Сквад: {group_name}, Лидер: {leader_name}, Выплата: {prize} TON\n\n"
    else:
        payments_info = "Нет доступных выплат."

    combined_text = welcome_text + squads_info + payments_info
    await message.answer(combined_text, parse_mode='HTML')






@dp.message_handler(IsPrivate(), lambda message: message.text in [translate_text("Получить робота 🤖", message.from_user.id), "Get robot 🤖"])
async def get_robot_button_handler(message: types.Message):
    user = message.from_user
    ref = 0
    robots = mdb.get_user_robots(user.id)

    if len(robots) == 0:
        robot_name = give_robot_to_user(user.id)
        await message.answer(translate_text(f"🎁 Вы получили робота <b>{robot_name}</b> в подарок!", user.id))
        
    await message.answer(get_start_text(), reply_markup=create_start_keyboard(user.id))
        
@dp.message_handler(Text('🔙 Назад', ignore_case=True), state='*')
async def back(msg: types.Message, state: FSMContext):
    user = msg.from_user
    await state.finish()
    await msg.answer(translate_text('🔙 Возвращаю назад', user.id), reply_markup=create_start_keyboard(user.id))
    await msg.delete()

@dp.message_handler(Text('🔙Back', ignore_case=True), state='*')
async def back(msg: types.Message, state: FSMContext):
    user = msg.from_user
    await state.finish()
    await msg.answer(translate_text('🔙 Возвращаю назад', user.id), reply_markup=create_start_keyboard(user.id))
    await msg.delete()



@dp.message_handler(lambda message: message.text in [translate_text("👥 Реферальная система", message.from_user.id), "👥 Referral system"], IsSubscribed())
@dp.throttled(antiflood, rate=1)
async def refferal_system(msg: types.Message):
    user = msg.from_user
    username = await bot.get_me()
    refferals_count = get_refferals(msg.from_user.id)
    refferal_take_reward = refferals_count * 0.03

    text = (
        '🔥 За каждого человека приглашенного по вашей '
        'ссылке, вы получите <b>+0.03 TAKE</b> для прокачки робота!'
        'Для зачисления 0.03 TAKE он <b>должен привязать свой кошелек.</b>'
        '\n\n'
        '<i>🤝 Приглашено рефералов:</i> <b>{}</b>\n💰Получено TAKE: {:.3f}\n\n🔗 <i>Твоя реферальная ссылка:</i>'
        ' <code>t.me/{}?start={}</code>'.format(
            refferals_count,
            refferal_take_reward,
            username['username'],
            user.id)
    )

    translated_text = translate_text(text, user.id)

    await msg.answer(translated_text, parse_mode=html)

@dp.message_handler(lambda message: message.text in ["🔼 Апгрейд", "🔼 Upgrade"], IsSubscribed())
@dp.throttled(antiflood, rate=1)
async def upgrades(msg: types.Message):
    user = msg.from_user
    kb = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(text=translate_text("🔋 Улучшенный макс здоровье", user.id), callback_data="info-max_health"),
        InlineKeyboardButton(text=translate_text("⚔️ Плазменный меч", user.id), callback_data="info-damage"),
        InlineKeyboardButton(text=translate_text("⚙️ Улучшенный ремкомплект", user.id), callback_data="info-heal"),
        InlineKeyboardButton(text=translate_text("🛡 Титановая броня", user.id), callback_data="info-armor"),
    )

    robot = mdb.get_user_active_robot(user.id)
    robot_id = robot[1]
    robot_name = robot[2]
    robot_max_health = robot[8]
    robot_damage = robot[4]
    robot_heal = robot[5]
    robot_armor = robot[6]

    nft_status = check_owner_nft(user.id)
    discount_message = ""
    if nft_status:
        discount_message = "\n<i>🏷️ Вы имеете 10% скидку на все улучшения благодаря вашему НФТ!</i>"

    with open(f'data/photos/robot_{robot_id}.png', 'rb') as photo:
        await msg.answer_photo(
            photo,
            f"🤖 {translate_text('Робот', user.id)}: <b>{robot_name}</b>\n\n"
            f"<b>{translate_text('Выберите желаемое улучшение', user.id)}</b>\n\n"
            f"{translate_text('Ваша текущая статистика', user.id)}:\n"
            f"🔋 {translate_text('Макс здоровье', user.id)}: <b>{robot_max_health}</b>\n"
            f"⚔️ {translate_text('Урон', user.id)}: <b>{robot_damage}</b>\n"
            f"⚙️ {translate_text('Восстановление', user.id)}: <b>{robot_heal}</b>\n"
            f"🛡 {translate_text('Броня', user.id)}: <b>{robot_armor}</b>\n"
            f"{discount_message}",
            reply_markup=kb,
            parse_mode="HTML"
        )




@dp.message_handler(lambda message: message.text in [translate_text("🤖 Мои роботы", message.from_user.id), "🤖 My robots"], IsSubscribed())
@dp.throttled(antiflood, rate=1)
async def getrobot(msg: types.Message):
    user = msg.from_user
    robots = mdb.get_user_robots(user.id)

    if len(robots) == 0:
        await msg.answer(translate_text('🙁 У вас нет роботов, купите их в разделе <b>"🛒 Магазин"</b>', user.id))
        return

    robot = robots[0]
    robot_id = robot[1]
    robot_name = robot[2]
    robot_health = robot[3]
    robot_damage = robot[4]
    robot_heal = robot[5]
    robot_armor = robot[6]
    status = robot[7]
    robot_lvl = robot[9]
    robot_max_health = robot[8]

    with open(f'data/photos/robot_{robot_id}.png', 'rb') as photo:
        await msg.answer_photo(photo, f'''
🤖 {translate_text('Робот', user.id)}: <b>{robot_name}</b>
🆔 ID: <b>{robot_id}</b>

🔋 {translate_text('Макс здоровье', user.id)}: <b>{robot_max_health}</b>
⚡️ {translate_text('Здоровье', user.id)}: <b>{robot_health}</b>
⚔️ {translate_text('Урон', user.id)}: <b>{robot_damage}</b>
⚙️ {translate_text('Восстановление', user.id)}: <b>{robot_heal}</b>
🎚  {translate_text('Уровень робота', user.id)}: <b>{robot_lvl}</b> 
🛡 {translate_text('Броня', user.id)}: <b>{robot_armor}</b>''', reply_markup=await my_robots_key(0, robot_id, len(robots), status, user.id))

@dp.message_handler(lambda message: message.text in [translate_text("💎 Баланс", message.from_user.id), "💎 Balance"], IsSubscribed())
@dp.throttled(antiflood, rate=1)
async def getbalance(msg: types.Message, state: FSMContext):
    await state.finish()
    uid = msg.from_user.id
    user_balance = round(get_balance(uid), 5)
    take_balance = round(get_take_balance(uid), 5)

    await msg.answer(f'''🆔 {translate_text('Ваш ID', uid)}: <code>{uid}</code>

<b>💎 TON:</b> {user_balance}
<b>💰 TAKE</b> {take_balance}''', reply_markup=deposit_key, parse_mode=html)



@dp.message_handler(lambda message: message.text in [translate_text("🏆 Турнир", message.from_user.id), "🏆 Tournament"], IsSubscribed())
@dp.throttled(antiflood, rate=1)
async def tournament(msg: types.Message, state: FSMContext):
    await state.finish()
    uid = msg.from_user.id
    active_tour = get_active_tour()
    if active_tour is not None:
        active_tour = get_tour(active_tour[0])
        user_exist = get_tour_user_exist(uid, active_tour[0])
        if not user_exist:
            user_status = translate_text('🚫 Статуc: <b>Вы не участвуете</b>', user_id=uid)
            user_place = translate_text('нет места', user_id=uid)
        else:
            user_status = translate_text('✅ Статуc: <b>Вы участвуете</b>', user_id=uid)
            user_place = get_user_place(active_tour[0], uid)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text=translate_text('✅ Участвовать', user_id=uid), callback_data='tour-run_' + str(active_tour[0])))
        markup.add(InlineKeyboardButton(text=translate_text('📁 История турнира', user_id=uid), callback_data='tour_history'))

        top_users = get_tour_top_user(active_tour[0])
        count_users = get_count_tour_users(active_tour[0])
        if not count_users:
            top_users_text = translate_text('нет участников', user_id=uid)
        else:
            top_users_text = ''
            for i, user in enumerate(top_users, start=1):
                top_users_text += f'{i}. 👤 <a href="tg://user?id={user[0]}">{translate_text("Пользователь", user_id=uid)}</a> (<code>{user[0]}</code>): <b>{user[1]}</b> {translate_text("очков", user_id=uid)}\n'

        user_ball = get_user_tour_ball(active_tour[0], uid)
        await msg.answer(f'''<b>🏆 {translate_text("Турнир", user_id=uid)} <b>№{active_tour[0]}</b></b>

{user_status}
            
🕞 {translate_text("Дата начала турнира", user_id=uid)} - <b>{active_tour[2]}:00 по MSK</b>
🕔 {translate_text("Дата окончания турнира", user_id=uid)} - <b>{active_tour[3]}:00 по MSK</b>

⭐️ {translate_text("Всего участников", user_id=uid)}: <b>{count_users}</b>
🔝 {translate_text("Лидеры турнира", user_id=uid)}: ⤵️
{top_users_text}
💎 {translate_text("Цена вступления в турнир", user_id=uid)}: <b>0.1</b> TON
💵 {translate_text("Фонд турнира", user_id=uid)}: <b>{round(count_users * 0.09, 2)}</b> TON

🫵 {translate_text("Ваше место в турнире", user_id=uid)}: <b>{user_place}</b>
⚡️ {translate_text("У вас очков", user_id=uid)}: <b>{user_ball}</b>

🏆{translate_text("В турнире победит участник, у которого будут наибольшее количество победных боев в ", user_id=uid)}"👥 {translate_text("Многопользовательской игре", user_id=uid)}" <b>({translate_text("игры со ставкой 0 TON не считаются", user_id=uid)})</b>. 
⭐️{translate_text("Каждая победа вам приносит 1 очко.", user_id=uid)}''',
                         reply_markup=markup, parse_mode=html)
    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text=translate_text('📁 История турнира', user_id=uid), callback_data='tour_history'))
        await msg.answer(f'''<b>⭕️ {translate_text("Нет активных турниров, ожидайте новостей!", user_id=uid)}</b>''',
                         reply_markup=markup, parse_mode=html)


@dp.message_handler(lambda message: message.text in [translate_text("🛒 Магазин", message.from_user.id), "🛒 Shop"], IsSubscribed())
@dp.throttled(antiflood, rate=1)
async def market(message: types.Message):
    user = message.from_user
    robots = mdb.get_robots()
    count_robots = len(robots)
    if count_robots == 0:
        await message.answer(translate_text('Нет роботов на продаже!', message.from_user.id))
        return

    robot = robots[0]

    robot_id = robot[0]
    robot_name = robot[1]
    robot_health = robot[2]
    robot_damage = robot[3]
    robot_heal = robot[4]
    robot_armor = robot[5]
    robot_price = robot[6]

    with open(f'data/photos/robot_{robot_id}.png', 'rb') as photo:
        await message.answer_photo(photo, f'''
🤖 {translate_text('Робот', message.from_user.id)}: <b>{robot_name}</b>
🆔 'ID': <b>{robot_id}</b>

🔋 {translate_text('Макс здоровье', message.from_user.id)}: <b>{robot_health}</b>
⚔️ {translate_text('Урон', message.from_user.id)}: <b>{robot_damage}</b>
⚙️ {translate_text('Восстановление', message.from_user.id)}: <b>{robot_heal}</b>
🛡 {translate_text('Броня', message.from_user.id)}: <b>{robot_armor}</b>

💎 <b>{translate_text('Стоимость', message.from_user.id)} {robot_price} ТАКЕ</b>''', reply_markup=await market_key(robot_id,
                                                                                                                    robots.index(robot) + 1,
                                                                                                                    robots.index(robot) - 1,
                                                                                                                    count_robots,
                                                                                                                    robots.index(robot),
                                                                                                                    user.id
                                                                                                                    )
                                                                                                   )
                               


@dp.message_handler(lambda message: message.text in [translate_text("🔝 Топ игроков", message.from_user.id), "🔝 Top players"], IsSubscribed())
@dp.throttled(antiflood, rate=1)
async def get_top(msg: types.Message):
    top_lvl = new_top_lvl()
    top_bet = new_top_bet_games()
    top_refferals = get_top_refferals()  # Получение топ 10 рефералов

    text = '🏆 <b>Топ игроков:</b>\n\n'

    text += '<b>По уровню робота:</b>\n'
    for i, user in enumerate(top_lvl):
        user_id = user[0]
        user_lvl = user[9]  # Изменить индекс с 9 на 3
        user_robot = user[2]
        try:
            player_name = await bot.get_chat(user_id)
            player_name = player_name.first_name
            player_name = f'<a href="tg://user?id={user_id}">{player_name}</a>'
        except:
            player_name = f'<a href="tg://user?id={user_id}">Пользователь</a>'

        text += f'{hbold(i + 1)}. {player_name} - {user_lvl} - {user_robot}\n'

    text += '\n<b>По платным боям:</b>\n'
    for i, user in enumerate(top_bet):
        user_id = user[0]
        user_bet = round(user[1], 3)
        try:
            player_name = await bot.get_chat(user_id)
            player_name = player_name.first_name
            player_name = f'<a href="tg://user?id={user_id}">{player_name}</a>'
        except:
            player_name = f'<a href="tg://user?id={user_id}">Пользователь</a>'

        text += f'{hbold(i + 1)}. {player_name} - {user_bet:.2f}\n'

    text += '\n<b>По рефералам:</b>\n'
    for i, refferal in enumerate(top_refferals):
        refferal_id = refferal[0]
        refferal_count = refferal[1]
        try:
            refferal_name = await bot.get_chat(refferal_id)
            refferal_name = refferal_name.first_name
            refferal_name = f'<a href="tg://user?id={refferal_id}">{refferal_name}</a>'
        except:
            refferal_name = f'<a href="tg://user?id={refferal_id}">Пользователь</a>'

        text += f'{hbold(i + 1)}. {refferal_name} - {refferal_count}\n'

    # перевод текста
    user_lang = check_user_language(msg.from_user.id)
    if user_lang == 'en':
        text = text.replace('Топ игроков:', 'Top players:')
        text = text.replace('По уровню робота:', 'By robot level:')
        text = text.replace('По платным боям:', 'Paid battles:')
        text = text.replace('По рефералам:', 'Referrals:')
        text = text.replace('Пользователь', 'User')
    elif user_lang == 'ru':
        pass  # текст уже на русском языке
    else:
        # используем язык по умолчанию (русский)
        pass

    await msg.answer(text, parse_mode='HTML')



@dp.message_handler(lambda message: message.text in [translate_text("🎮 Играть", message.from_user.id), "🎮 Play"], IsSubscribed())
@dp.throttled(antiflood, rate=1)
async def game_match(message: types.Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(KeyboardButton(translate_text("⚔️ Создать бой", user_id)), KeyboardButton(translate_text("🤝 Присоединиться к бою", user_id)))
    keyboard.row(KeyboardButton(translate_text("🛡️ Мои активные бои", user_id)), KeyboardButton(translate_text("📜 История моих боев", user_id)))

    keyboard.row(KeyboardButton(translate_text("🔙 Назад", user_id)))
    await message.answer(translate_text('Чтобы начать играть, нажмите одну из кнопок', user_id),
                         reply_markup=keyboard,
                         )


@dp.message_handler(text='⚔️ Create a battle')
@dp.throttled(antiflood, rate=1)
async def create_game_0(message: types.Message):
    user_id = message.from_user.id
    await message.answer(translate_text('<b>💎 Выберите сумму ставки на бой:</b>', user_id), reply_markup=bet_key)


@dp.message_handler(text='🤝 Join the fight')
@dp.throttled(antiflood, rate=1)
async def join_to_game(message: types.Message):
    active_games = mdb.get_active_games()
    user_id = message.from_user.id
    if len(active_games) == 0:
        await message.answer(translate_text('''<b>❌ Нет активных боев!</b>

📌 Создайте сами в разделе "🔸 Создать бой" или ожидайте других игроков.'''), user_id)
        return

    markup = InlineKeyboardMarkup()
    for game in active_games:
        markup.add(InlineKeyboardButton(text=f'#{game[0]} | {game[1]} TON', callback_data=f'join_{game[0]}'))

    await message.answer(translate_text('<b>⚔️ Активные бои:</b>', user_id), reply_markup=markup)


@dp.message_handler(text='🛡️ My active battles')
@dp.throttled(antiflood, rate=1)
async def my_active_games(message: types.Message):
    user = message.from_user
    active_games = mdb.get_user_active_games(user.id)
    if len(active_games) == 0:
        await message.answer(translate_text('''<b>❌ Нет активных боев!</b>

📌 Можете создать разделе "🔸 Создать бой".'''), user.id)
        return

    markup = InlineKeyboardMarkup()
    for game in active_games:
        markup.add(InlineKeyboardButton(text=f'#{game[0]} | {game[1]} TON', callback_data=f'mygame_{game[0]}'))

    await message.answer(translate_text('<b>⚔️ Ваши активные бои:</b>', user.id), reply_markup=markup)


@dp.message_handler(text='📜 History of my fights')
@dp.throttled(antiflood, rate=1)
async def game_history(message: types.Message):
    user = message.from_user
    history = mdb.get_user_all_games(user.id)
    if len(history) == 0:
        await message.answer(translate_text('''<b>❌ Вы еще не участвовали в боях.</b>'''), user.id)
        return

    text = f'📁 History of battles of a player with ID {user.id}\n\n'
    for game in history:
        if game[5] == 0:
            winner = 'The battle has not yet started, is not finished, or has been deleted!'
        else:
            winner = game[5]

        if game[2] == 'finished':
            status = 'ENDED'
        elif game[2] == 'started':
            status = 'STARTED'
        elif game[2] == 'expectation':
            status = 'WAITING'
        else:
            status = 'DELETED'

        try:
            player1 = await bot.get_chat(game[3])
            player1 = player1.first_name

            player2 = await bot.get_chat(game[4])
            player2 = player2.first_name
        except:
            player1 = f'User'
            player2 = f'User'

        text += f'''⚔️ Бой номер #{game[0]}
👤 Player 1: {player1} ({game[3]})
👤 Player 2: {player2} ({game[4]})
📌 Status: {status}
💎 Bet: {game[1]} TON
📆 Date: {game[6]}
👑 Winner: {winner}
➖➖➖➖➖➖➖➖➖
'''

    with open(f'data/texts/{user.id}-history.txt', 'w', encoding='UTF-8') as file:
        file.write(text)

    input_file = InputFile(f'data/texts/{user.id}-history.txt', filename=f'{user.id}-history.txt')
    await message.answer_document(input_file, caption='Your battles history.')

    os.remove(f'data/texts/{user.id}-history.txt')


@dp.message_handler(text='⚔️ Создать бой')
@dp.throttled(antiflood, rate=1)
async def create_game_0(message: types.Message):
    await message.answer('<b>💎 Выберите сумму ставки на бой:</b>', reply_markup=bet_key)


@dp.message_handler(text='🤝 Присоединиться к бою')
@dp.throttled(antiflood, rate=1)
async def join_to_game(message: types.Message):
    active_games = mdb.get_active_games()
    if len(active_games) == 0:
        await message.answer('''<b>❌ Нет активных боев!</b>

📌 Создайте сами в разделе "🔸 Создать бой" или ожидайте других игроков.''')
        return

    markup = InlineKeyboardMarkup()
    for game in active_games:
        markup.add(InlineKeyboardButton(text=f'#{game[0]} | {game[1]} TON', callback_data=f'join_{game[0]}'))

    await message.answer('<b>⚔️ Активные бои:</b>', reply_markup=markup)


@dp.message_handler(text='🛡️ Мои активные бои')
@dp.throttled(antiflood, rate=1)
async def my_active_games(message: types.Message):
    user = message.from_user
    active_games = mdb.get_user_active_games(user.id)
    if len(active_games) == 0:
        await message.answer('''<b>❌ Нет активных боев!</b>

📌 Можете создать разделе "🔸 Создать бой".''')
        return

    markup = InlineKeyboardMarkup()
    for game in active_games:
        markup.add(InlineKeyboardButton(text=f'#{game[0]} | {game[1]} TON', callback_data=f'mygame_{game[0]}'))

    await message.answer('<b>⚔️ Ваши активные бои:</b>', reply_markup=markup)


@dp.message_handler(text='📜 История моих боев')
@dp.throttled(antiflood, rate=1)
async def game_history(message: types.Message):
    user = message.from_user
    history = mdb.get_user_all_games(user.id)
    if len(history) == 0:
        await message.answer('''<b>❌ Вы еще не участвовали в боях.</b>''')
        return

    text = f'📁 История боев игрока с ID {user.id}\n\n'
    for game in history:
        if game[5] == 0:
            winner = 'Бой еще не начат или не закончен или удален!'
        else:
            winner = game[5]

        if game[2] == 'finished':
            status = 'БОЙ ЗАКОНЧЕН'
        elif game[2] == 'started':
            status = 'БОЙ НАЧАТ'
        elif game[2] == 'expectation':
            status = 'В ОЖИДАНИИ'
        else:
            status = 'БОЙ УДАЛЕН'

        try:
            player1 = await bot.get_chat(game[3])
            player1 = player1.first_name

            player2 = await bot.get_chat(game[4])
            player2 = player2.first_name
        except:
            player1 = f'Пользователь'
            player2 = f'Пользователь'

        text += f'''⚔️ Бой номер #{game[0]}
👤 Игрок 1: {player1} ({game[3]})
👤 Игрок 2: {player2} ({game[4]})
📌 Статус: {status}
💎 Ставка: {game[1]} TON
📆 Дата игры: {game[6]}
👑 Победитель: {winner}
➖➖➖➖➖➖➖➖➖
'''

    with open(f'data/texts/{user.id}-history.txt', 'w', encoding='UTF-8') as file:
        file.write(text)

    input_file = InputFile(f'data/texts/{user.id}-history.txt', filename=f'{user.id}-history.txt')
    await message.answer_document(input_file, caption='История ваших боев.')

    os.remove(f'data/texts/{user.id}-history.txt')
    
@dp.message_handler(state=WithdrawTon.amount)
@dp.throttled(antiflood, rate=1)
async def process_sum(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    valid = False
    try:
        float(message.text)
        valid = True
    except ValueError:
        pass
    if valid and 0 < float(message.text) <= get_balance(user_id):
        amount = round(float(message.text), 6)
        if amount < 0.1:
            text = '🚫 Минимальная сумма вывода 0.1 TON!'
            await message.answer(translate_text(text, user_id))
            return
        text = f'<i>📤 Подтвердите вывод</i>\n\n💎 Сумма: <b>{amount}</b> TON'
        await message.answer(translate_text(text, user_id), reply_markup=await withdraw_key(amount))
        await state.finish()
    elif valid and float(message.text) > get_balance(user_id):
        text = "***Недостаточно средств...***"
        await message.answer(translate_text(text, user_id), parse_mode=ParseMode.MARKDOWN, reply_markup=create_start_keyboard(user_id))
        await state.finish()
    else:
        text = "***Некорректные данные.*** Попробуйте еще раз..."
        await message.answer(translate_text(text, user_id), parse_mode=ParseMode.MARKDOWN, reply_markup=create_start_keyboard(user_id))
        await state.finish()



@dp.message_handler(state=WithdrawTake.amount)
@dp.throttled(antiflood, rate=1)
async def process_sum_take(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    valid = False
    try:
        float(message.text)
        valid = True
    except ValueError:
        pass
    if valid and 0 < float(message.text) <= get_take_balance(user_id):
        amount = round(float(message.text), 6)
        if amount < 0.1:
            text = '🚫 Минимальная сумма вывода 0.1 TAKE!'
            await message.answer(translate_text(text, user_id))
            return
        text = f'📤 Подтвердите вывод\n\n💎 Сумма: <b>{amount}</b> TAKE'
        await message.answer(translate_text(text, user_id), reply_markup=await withdraw_key_take(amount))
        await state.finish()
    elif valid and float(message.text) > get_take_balance(user_id):
        text = "***Недостаточно средств...***"
        await message.answer(translate_text(text, user_id), parse_mode=ParseMode.MARKDOWN, reply_markup=create_start_keyboard(user_id))
        await state.finish()
    else:
        text = "***Некорректные данные.*** Попробуйте еще раз..."
        await message.answer(translate_text(text, user_id), parse_mode=ParseMode.MARKDOWN, reply_markup=create_start_keyboard(user_id))
        await state.finish()


@dp.message_handler(state=DepositTon.amount)
async def deposit_ton_2(message: types.Message, state: FSMContext):
    user = message.from_user
    user_id = message.from_user.id
    try:
        amount = float(message.text)
    except ValueError:
        text = '<b>Введите число!</b>'
        await message.answer(translate_text(text, user_id), reply_markup=back_key, parse_mode=html)
        return

    invoice_id, invoice_link = await create_invoice(amount, user.id, 'TONCOIN')

    if invoice_id is None:
        text = '<b>🚫 Ошибка при создание счета, сумма слишком маленькая, попробуйте еще раз!</b>'
        await message.answer(translate_text(text, user_id), parse_mode=html)
        await bot.send_message(1251379793, f'🚫 Ошибка при создание счета у юзера {user.id}\nТекст: {invoice_link}',
                               parse_mode=html)
        await state.finish()
        return

    await message.answer('Обработка...', reply_markup=create_start_keyboard(user.id))

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(text=translate_text('🔗 Оплатить', user_id), url=invoice_link))
    markup.add(InlineKeyboardButton(text=translate_text('✅ Я оплатил', user_id), callback_data='check-ton_' + str(invoice_id)))

    text = '''<b>💎 Пополнение с помощью TON:</b>

❗️ У вас есть 10 минут что бы совершить платеж ❗

👇 Нажмите на <b>"🔗 Оплатить"</b> что бы совершить платеж, после оплаты нажмите на <b>"✅ Я оплатил"</b>!'''
    await message.answer(translate_text(text, user_id), reply_markup=markup, parse_mode=html)
    await state.finish()



@dp.message_handler(state=DepositTake.amount)
async def deposit_take_2(message: types.Message, state: FSMContext):
    user = message.from_user
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer(translate_text('<b>Введите число!</b>', user.id), reply_markup=back_key, parse_mode=html)
        return

    invoice_id, invoice_link = await create_invoice(amount, user.id, 'TAKE')

    if invoice_id is None:
        await message.answer(translate_text('<b>🚫 Ошибка при создание счета, сумма слишком маленькая, попробуйте еще раз!</b>', user.id),
                             parse_mode=html)
        await bot.send_message(1251379793, f'🚫 Ошибка при создание счета у юзера {user.id}\nТекст: {invoice_link}',
                               parse_mode=html)
        await state.finish()
        return

    await message.answer(translate_text('Обработка...', user.id), reply_markup=create_start_keyboard(user.id))

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(text='🔗 Оплатить', url=invoice_link))
    markup.add(InlineKeyboardButton(text='✅ Я оплатил', callback_data='check-take_' + str(invoice_id)))
    await message.answer(f'''<b>💎 {translate_text('Пополнение с помощью TAKE:', user.id)}</b>

❗️ {translate_text('У вас есть 10 минут что бы совершить платеж', user.id)} ❗

👇 {translate_text('Нажмите на <b>"🔗 Оплатить"</b> что бы совершить платеж, после оплаты нажмите на <b>"✅ Я оплатил"</b>!', user.id)}''',
                         reply_markup=markup, parse_mode=html)
    await state.finish()

@dp.message_handler(state=DepositCry.amount)
async def receive_amount_in_ton(message: types.Message, state: FSMContext):
    user = message.from_user
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer(translate_text('<b>Введите число!</b>', user.id))
        return

    await message.answer(translate_text('Обработка...', user.id), reply_markup=create_start_keyboard(user.id))
    invoice_id, invoice_url = await create_cry_invoice(amount, 'TON', user.id)

    if invoice_id == 'small':
        await message.answer(translate_text('<b>🚫 Сумма слишком маленькая!</b>', user.id))
        return

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(text='🔗 Оплатить', url=invoice_url))
    markup.add(
        InlineKeyboardButton(text='✅ Я оплатил', callback_data='check-cry_' + str(invoice_id)))
    await message.answer(f'''<b>💎 {translate_text('Пополнение с помощью TON:', user.id)}</b>

❗️ {translate_text('У вас есть 10 минут что бы совершить платеж', user.id)} ❗

👇 {translate_text('Нажмите на <b>"🔗 Оплатить"</b> что бы совершить платеж, после оплаты нажмите на <b>"✅ Я оплатил"</b>!', user.id)}''',
                         reply_markup=markup)
    await state.finish()


@dp.message_handler(lambda message: message.text in [translate_text("🏪 Рынок", message.from_user.id), "🏪 Market"], IsSubscribed())
@dp.throttled(antiflood, rate=1)
async def bazar(message: types.Message):
    robots = mdb.get_bazar_robots()
    user_id = message.from_user.id
    count_robots = len(robots)
    if count_robots == 0:
        await message.answer(translate_text('Нет роботов на продаже!', message.from_user.id))
        return

    robot = robots[0]

    robot_seller = robot[0]
    robot_id = robot[2]
    robot_name = robot[3]
    robot_health = robot[4]
    robot_damage = robot[5]
    robot_heal = robot[6]
    robot_armor = robot[7]
    robot_price = robot[10]
    robot_lvl = robot[8]

    with open(f'data/photos/robot_{robot_id}.png', 'rb') as photo:
        await message.answer_photo(photo, f'''
🤖 {translate_text('Робот', message.from_user.id)}: <b>{robot_name}</b>
👤 {translate_text('Продавец', message.from_user.id)}: <b>{robot_seller}</b>
🆔 'ID': <b>{robot_id}</b>

🔋 {translate_text('Макс здоровье', message.from_user.id)}: <b>{robot_health}</b>
⚔️ {translate_text('Урон', message.from_user.id)}: <b>{robot_damage}</b>
⚙️ {translate_text('Восстановление', message.from_user.id)}: <b>{robot_heal}</b>
🎚  {translate_text('Уровень робота', message.from_user.id)}: <b>{robot_lvl}</b> 
🛡  {translate_text('Броня', message.from_user.id)}: <b>{robot_armor}</b>

💎 <b>{translate_text('Стоимость', message.from_user.id)} {robot_price} ТАКЕ</b>''', reply_markup=await bazar_key(robot_id,
                                                                                                                  robots.index(robot) + 1,
                                                                                                                  robots.index(robot) - 1,
                                                                                                                  count_robots,
                                                                                                                  robots.index(robot),
                                                                                                                  robot_seller,
                                                                                                                  user_id  
                                                                                                                  )
                                               )
                               




@dp.message_handler(lambda message: message.text in [translate_text("🏭 Локации", message.from_user.id), "🏭 Locations"], IsSubscribed())
@dp.throttled(antiflood, rate=1)
async def locations(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    keyboard = await locations_key(user_id)
    text = translate_text('Выберите локацию:', user_id)
    await message.answer(text, reply_markup=keyboard)

    
@dp.message_handler(lambda message: message.text in [translate_text("🕹 Игры ТАКЕ", message.from_user.id), "🕹 TAKE Games"])
@dp.throttled(antiflood, rate=1)
async def games_tontake(message: types.Message):
    user_id = message.from_user.id
    language = check_user_language(user_id)

    if language == 'ru':
        button1 = InlineKeyboardButton("Кликер зерносклад", url="https://zernosklad.com/")
        button2 = InlineKeyboardButton("Стратегия TONvsTAKE", url="https://tontake.com/")
        text = "Здесь вы также можете играть и зарабатывать таке монеты! Выберите игру:"
    elif language == 'en':
        button1 = InlineKeyboardButton("Grain storage clicker", url="https://zernosklad.com/")
        button2 = InlineKeyboardButton("TONvsTAKE strategy", url="https://tontake.com/")
        text = "Here you can also play and earn take coins! Choose a game:"

    markup = InlineKeyboardMarkup(row_width=1).add(button1, button2)

    await message.answer(text, reply_markup=markup)

    
    
    
    
    
    
    
    
@dp.message_handler(Command(['a', 'admin']))
async def admin(message: Message):
    if message.from_user.id in administrators:
        take_balance = await get_all_balance('TAKE')
        ton_balance = await get_all_balance()
        # cry_ton_balance = await get_cry_balance('ton')
        await message.answer(
            f'Админка:\n\nБаланс TAKE: <b>{take_balance}</b>\nБаланс TON: <b>{ton_balance}</b>',
            reply_markup=admin_key,
            parse_mode=html
        )
    else:
        await message.answer("You don't have permission to access the admin panel.")


# @dp.message_handler(IsAdmin(), Command(['restore_robot']))
# async def restore_robots(message: Message):
#     robots = get_all_user_robots()
#     counter = 0
#     for robot in robots:
#         counter += 1
#         user_id = robot[0]
#         health = robot[1]
#         damage = robot[2]
#         heal = robot[3]
#         armor = robot[4]
#         lvl = robot[5]
#         mdb.add_robot(user_id, 999, "Титан", health, damage, heal, armor, lvl)
#         mdb.update_robot_status(user_id, 999)
#
#     await message.answer(f'Процесс завершен, добавлено {counter} роботов.')


@dp.message_handler(state=SendAllText.text)
async def send_to_users(message: Message, state: FSMContext):
    user.id = message.from_user.id
    users = get_users()
    bad_result = 0
    good_result = 0
    async with state.proxy() as data:
        data["text"] = message.text

    async with state.proxy() as data:
        text = data["text"]
    start_time = time.time()
    await state.finish()
    await message.answer('Рассылка начата!')
    for user in users:
        for x in user:
            try:
                await bot.send_message(x, text, reply_markup=create_start_keyboard(user.id), parse_mode=html)
                await asyncio.sleep(0.05)
                good_result += 1
            except:
                bad_result += 1
    end_time = time.time()
    await message.answer(
        f"""<b>Рассылка завершена!</b>

Заняло время: <code>{round(end_time - start_time, 2)}</code> секунд
Успешно: <code>{good_result}</code>
Неуспешно: <code>{bad_result}</code>""",
        parse_mode=html
    )


# Рассылка c фото
@dp.message_handler(content_types="photo", state=SendAllPhoto.photo)
async def send_to_users_photo(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data["photo"] = message.photo[0].file_id
    await bot.send_message(
        message.from_user.id,
        "Напишите текст для рассылки:",
        reply_markup=cancel_adm_key,
    )
    await SendAllPhoto.next()


@dp.message_handler(state=SendAllPhoto.text)
async def send_to_users_text(message: Message, state: FSMContext):
    users = get_users()
    bad_result = 0
    good_result = 0
    async with state.proxy() as data:
        data["text"] = message.text

    async with state.proxy() as data:
        text = data["text"]
        photo_id = data["photo"]
    start_time = time.time()
    await state.finish()
    await message.answer('Рассылка начата!')
    for user in users:
        for x in user:
            try:
                await bot.send_photo(x, photo_id, text, reply_markup=create_start_keyboard(user.id), parse_mode=html)
                await asyncio.sleep(0.05)
                good_result += 1
            except:
                bad_result += 1

    end_time = time.time()
    await message.answer(
        f"""<b>Рассылка завершена!
Заняло время:{end_time - start_time}
Успешно: {good_result}
Неуспешно: {bad_result}</b>""",
        parse_mode=html
    )


@dp.message_handler(state=StartTour.date)
async def start_tour_2(message: Message, state: FSMContext):
    end_date = message.text
    if ':' in end_date:
        end_date = end_date.split(':')[0]
    print(end_date)
    utc_now = datetime.datetime.now(pytz.utc)
    moscow_tz = pytz.timezone('Europe/Moscow')
    moscow_time = utc_now.astimezone(moscow_tz)
    moscow_now = datetime.datetime.strftime(moscow_time, '%d.%m.%y %H')
    count_tour = get_count_exist_tour()
    add_tour(count_tour, moscow_now, end_date)

    await message.answer(f'✅ Успешно начать турнир под номером <b>№{count_tour}</b>', parse_mode=html)
    await state.finish()


@dp.message_handler(state=SearchUser.id)
async def user_search(message: Message, state: FSMContext):
    user_id = message.text

    if not check_user(user_id):
        await message.answer("❌ Пользовател не найден в боте!")
        return

    ref_count = get_refferals(user_id)
    ton_balance = round(get_balance(user_id), 4)
    take_balance = round(get_take_balance(user_id), 4)

    await message.answer(
        f"""
👤 Информация о <a href="tg://user?id={user_id}"><b>пользователе</b></a>

🆔 ID: <b>{user_id}</b>
➖➖➖➖➖➖➖➖➖
💰 Баланс TAKE: <b>{take_balance}</b>
➖➖➖➖➖➖➖➖➖
💎 Баланс TON: <b>{ton_balance}</b>
➖➖➖➖➖➖➖➖➖
👥 Количество рефералов: <b>{ref_count}</b>""",
        reply_markup=await admin_search_key(user_id),
        parse_mode=html
    )
    await state.finish()


@dp.message_handler(state=EditUserBalance.value)
async def edit_4(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    currency = data['currency']
    edit_type = data['edit_type']
    try:
        value = round(float(message.text), 4)
    except ValueError:
        await message.answer('Введите число!', reply_markup=cancel_adm_key)
        return
    if edit_type == 'give' and currency == 'balance':
        add_take_balance(user_id, value)
    elif edit_type == 'give' and currency == 'ton_balance':
        add_balance(user_id, value)
    elif edit_type == 'take' and currency == 'balance':
        decrease_take_balance(user_id, value)
    elif edit_type == 'take' and currency == 'ton_balance':
        decrease_balance(user_id, value)
    await message.answer(f'<b>Успешно</b>')
    await state.finish()


@dp.message_handler(state=NewRobot.name)
async def new_robot_1(message: Message, state: FSMContext):
    name = message.text
    async with state.proxy() as data:
        data['name'] = name

    await message.answer('✅ Принято!\n\n<b>Теперь введите здоровье для робота:</b>', reply_markup=cancel_adm_key)
    await NewRobot.health.set()


@dp.message_handler(state=NewRobot.health)
async def new_robot_2(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['health'] = message.text

    await message.answer('✅ Принято!\n\n<b>Теперь введите урон для робота:</b>', reply_markup=cancel_adm_key)
    await NewRobot.damage.set()


@dp.message_handler(state=NewRobot.damage)
async def new_robot_3(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['damage'] = message.text

    await message.answer('✅ Принято!\n\n<b>Теперь введите восстановление для робота:</b>', reply_markup=cancel_adm_key)
    await NewRobot.heal.set()


@dp.message_handler(state=NewRobot.heal)
async def new_robot_4(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['heal'] = message.text

    await message.answer('✅ Принято!\n\n<b>Теперь введите броню для робота:</b>', reply_markup=cancel_adm_key)
    await NewRobot.armor.set()


@dp.message_handler(state=NewRobot.armor)
async def new_robot_5(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['armor'] = message.text

    await message.answer('✅ Принято!\n\n<b>Теперь введите цену для робота в TAKE:</b>', reply_markup=cancel_adm_key)
    await NewRobot.price.set()


@dp.message_handler(state=NewRobot.price)
async def new_robot_6(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['price'] = message.text

    await message.answer('✅ Принято!\n\n<b>Теперь скинтье фото для робота:</b>', reply_markup=cancel_adm_key)
    await NewRobot.photo.set()


@dp.message_handler(state=NewRobot.photo, content_types=ContentTypes.PHOTO)
async def new_robot_7(message: Message, state: FSMContext):
    photo = message.photo[-1]

    photo_id = photo.file_id

    async with state.proxy() as data:
        data['photo'] = photo_id

    robot_data = await state.get_data()
    await message.answer_photo(photo_id, f'''
Название: <b>{robot_data['name']}</b>

Здоровье: <b>{robot_data['health']}</b>
Урон: <b>{robot_data['damage']}</b>
Восстановление: <b>{robot_data['heal']}</b>
Броня: <b>{robot_data['armor']}</b>

Стоимость <b>{robot_data['price']}</b> ТАКЕ

<b>👇 Потвердите данные создания робота:</b>
''', reply_markup=confirm_new_robot)
    await NewRobot.confirm.set()


@dp.message_handler(state=NewRobot.confirm)
async def new_robot_8(message: Message):
    await message.answer('<b>👆 Подтвердите создание нового робота или отмените 👇</b>', reply_markup=cancel_adm_key)


@dp.message_handler(state=DeleteRobot.robot_id)
async def del_robot_2(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer('ID робота должен быть в виде числа, попробуйте еще раз!', reply_markup=cancel_adm_key)
        return

    robot_id = message.text

    await state.update_data(robot_id=robot_id)

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('Удалить', callback_data='confirm-delete-robot'))
    markup.add(InlineKeyboardButton('Отменить', callback_data='cancel_admin'))

    await message.answer(f'❓ Вы точно хотите удалить робот с ID {robot_id}?', reply_markup=markup)

    await DeleteRobot.confirm.set()


@dp.message_handler(state=DeleteRobot.confirm)
async def delete_confirm(message: Message):
    await message.answer('<b>👆 Подтвердите удаления робота или отмените 👇</b>', reply_markup=cancel_adm_key)
    
    

from data.functions.db_squads import get_squads_count

@dp.message_handler(lambda message: message.text in [translate_text("⭐️ Статистика", message.from_user.id), "⭐️ Statistic"], IsSubscribed())
@dp.throttled(antiflood, rate=1)
async def super_statistic(message: types.Message):
    # Calculate the number of months and days since September 27, 2023
    start_date = datetime.datetime(2023, 9, 27)

    today = datetime.datetime.today()
    diff = today - start_date
    months = diff.days // 30
    days = diff.days % 30

    # Get the number of users, battles, robots, and squads from the database
    user_count = get_user_count()
    battle_count = get_battle_count()
    robots_count = get_robots_count()
    squads_count = get_squads_count()

    # Translate the text using the user's selected language
    text = (
        f"<b>🤖 Боту: {months} месяцев {days} дней! 📅</b>\n\n"
        f"<b>За это время:</b>\n"
        f"{hbold('👥 Нас уже')} {user_count} {hbold('человек!')}\n"
        f"{hbold('🤜 Мы провели')} {battle_count} {hbold('битв!')}\n"
        f"{hbold('🤖 В игре уже')} {robots_count} {hbold('роботов!')}\n"
        f"{hbold('🏆 В игре уже')} {squads_count} {hbold('скавадов!')}\n"
    )
    translated_text = translate_text(text, message.from_user.id)

    # Send the statistics as a message with smileys and HTML tags
    await message.answer(
        translated_text,
        parse_mode="HTML",
    )

async def on_shutdown(dp):
    await storage.close()
    await bot.close()
    me = await bot.get_me()
    print(f'Bot: @{me.username}\nОстановлен!')


@dp.message_handler(commands=['getid'])
async def get_id(msg: types.Message):
    await msg.answer(f'<code>{msg.chat.id}</code>')



@dp.message_handler(content_types=types.ContentType.NEW_CHAT_MEMBERS)
async def on_bot_added(message: types.Message):
    for new_member in message.new_chat_members:
        if new_member.id == (await bot.me).id:

            group_name = message.chat.title
            
            print(group_name)

            link = f'https://t.me/TonTakeRoBot?start=joinsquad_{message.chat.id}'
            inline_btn = InlineKeyboardButton("Присоединиться к скваду", url=f'{link}')
            inline_kb = InlineKeyboardMarkup().add(inline_btn)

            welcome_text = (
                "Добро пожаловать в сквады TonTakeRobot! 🤖\n\n"
                f"Здесь ты мможешь вступить в {group_name} сквад и бороться с другими "
                "скавадами в еженедельном турнире. 🏆\n\n"
                "Каждую неделю сквад с наибольшим количеством побед заберет приз в "
                "размере 5% от каждого боя, проведенного в сквадах. 💰\n\n"
                "Нажми на кнопку ниже, чтобы присоединиться к скваду!"
            )

            await message.answer(welcome_text, reply_markup=inline_kb)

            leader_id = message.from_user.id
            add_group_to_db(message.chat.id, leader_id, group_name)  # Обновить вызов функции
            add_user_to_squad(message.chat.id, leader_id)


            
            
@dp.message_handler(IsPrivate(), commands=["start"])
@dp.throttled(antiflood, rate=1)
async def start(message: types.Message):
    user = message.from_user
    robots = mdb.get_user_robots(user.id)
    ref = 0

    if len(message.text) > 6:
        try:
            int(message.text.split()[1])
            ref = message.text.split()[1]
        except ValueError:
            pass

    if not check_user(user.id):
        # prompt user to select language
        language_keyboard = get_language_keyboard()
        await message.answer("Please select your language:", reply_markup=language_keyboard)
        add_user(user.id, ref)
        # if ref != 0:
        #     if ref:
        #         add_refferal_balance(ref)
        #         await bot.send_message(ref,
        #                                     f'👤 Вы пригласили <a href="tg://user?id={user.id}"><b>{user.first_name}</b></a> и получили <b>0.03</b> TAKE')
        #     else:
        #         print(f"Referral user with ID {ref} not found.")
    elif len(robots) == 0:
        await message.answer(translate_text(robot_chances_text(), user.id), reply_markup=get_robot_keyboard(user.id))

    elif 'joingame_' in message.text:
        game_id = message.text.split('_')[1]
        game = mdb.get_game(game_id)
        if game:
            player_id = game[3]
            if player_id != user.id:
                await join_game(user, game_id)
                return

    elif 'joinsquad_' in message.text:
        group_id = message.text.split('_')[1]
        user_id = message.from_user.id
        if add_user_to_squad(group_id, user_id):
            await message.answer(f"Вы успешно вступили в сквад {group_id}!")
        else:
            await message.answer("Вы уже состоите в скваде!")

    else:
        await message.answer(translate_text(get_start_text(), user.id), reply_markup=create_start_keyboard(user.id))




async def join_game(user, game_id):
    game = mdb.get_game(game_id)
    player_id = game[3]

    try:
        player = await bot.get_chat(player_id)
        player = player.first_name
        player = f'<a href="tg://user?id={player_id}">{player}</a>'
    except:
        player = f'<a href="tg://user?id={player_id}">Пользователь</a>'

    text = f'<b>#️⃣ Бой номер:</b> #{game[0]}\n' \
           f'<b>💎 Ставка:</b> {game[1]} TON\n' \
           f'📆 Дата создание: {game[6]}\n' \
           f'<b>👤 Создатель:</b> {player}\n\n' \
           f'<i>Уверены что хотите начать бой?</i>'

    keyboard = await join_game_key(game[0])

    await bot.send_message(
        user.id,
        text,
        reply_markup=keyboard,
        parse_mode='HTML'
    )


@dp.message_handler(lambda message: message.text in [translate_text("👝 Привязать кошелек", message.from_user.id), "👝 Link wallet"])
@dp.throttled(antiflood, rate=1)
async def process_wallet_request(message: types.Message):

    user_id = message.from_user.id
    wallet_address = 'EQCSvwpsHiBvdS2nxIJ77Z7D-8MNqe4vGy0ZBW50WM1WJtvO'
    comment = f'TonTakeRoBot{user_id}'

    bonus_info = (
        '🚀 После успешной привязки вашего кошелька с наличием НФТ ТонТейка вы получите бонус в виде ускорения'
        'восстановления робота и скидки на прокачку! Также ваш робот будет ремонтироваться автоматически!'
    )

    message_text = (
        'Пожалуйста переведите 0.01 TON с кошелька который хотите привязать на адрес '
        f'`{wallet_address}`\n\n'
        'С комментарием: `{}`\n\n'
        'Внимание! Нужно переводить ровно 0.01 TON!\n\n'
        'После нажмите на кнопку "Проверить платёж".\n\n'
        .format(comment)
    )

    message_text_with_bonus = f'{message_text}\n{bonus_info}'

    await message.answer(translate_text(message_text_with_bonus, user_id), reply_markup=nft_key(message.from_user.id), parse_mode='Markdown')


@dp.message_handler(lambda message: message.text in [translate_text("🖼 NFTs", message.from_user.id), "🖼 NFTs"])
@dp.throttled(antiflood, rate=1)
async def process_nft_request(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    wallet = get_user_wallet(chat_id)
    if not wallet:  # Check if wallet is None or empty
        await bot.send_message(chat_id, translate_text("Сначала привяжите свой кошелек к боту", user_id))
    else:
        check_nft = check_owner_nft(address=wallet)
        if check_nft:
            text = translate_text(f"🎉 Отлично! На вашем кошельке ({wallet}) есть НФТ из нашей коллекции!\n\n"
                                   f"🎁 Это дает вам следующие бонусы:\n"
                                   f"- 10% скидка на прокачку наших роботов\n"
                                   f"- Увеличение скорости восстановления вашего робота в 2 раза\n"
                                   f"- Бонус +1 к силе удара в битвах\n\n"
                                   f"Наслаждайтесь своими преимуществами и удачи в боях! 💪🎉", user_id)
            await bot.send_message(chat_id, text)
            current_nft_status = get_user_nft_status(chat_id)
            if current_nft_status != 1:
                set_user_nft_status(chat_id, 1)
        else:
            await bot.send_message(chat_id, translate_text(f"❌ На вашем кошельке ({wallet}) нет НФТ из нашей коллекции", user_id))
            
            set_user_nft_status(chat_id, 0)



     
def check_owner_nft(address):
    try:
        ton = TonScan()
        res = ton.unpack_address(address)
        print(res)
        if res['ok']:
            address = res['result']
            for collection in NFT_COLLECTIONS:
                collection = collection.replace('https://getgems.io/collection/', '')
                collection_items = ton.collection_items(collection)
                if address in str(collection_items):
                    return True
                    break
        return False
    except Exception as e:
        print('Err422: ', e)
        return False                        


@dp.message_handler(lambda message: message.text in [translate_text("📸 Сквады", message.from_user.id), "📸 Сквады"])
@dp.throttled(antiflood, rate=1)
async def team(message: types.Message):
    welcome_text = (
        "Добро пожаловать в сквады TonTakeRobot! 🤖\n\n"
        "Здесь ты сможешь создать свой собственный сквад и бороться с другими "
        "скавадами в еженедельном турнире. 🏆\n\n"
        "Каждую неделю сквад с наибольшим количеством побед заберет приз в "
        "размере 5% от каждого боя, проведенного в сквадах. 💰\n\n"
        "Чтобы участвовать в сквадах, просто добавьте бота в свой чат.\n\n"
    )

    top_squads = get_top_squads(10)
    
    async def get_user_name(user_id):
        user = await bot.get_chat(user_id)
        return user.first_name

    squads_info = ""

    if top_squads:
        squads_info += "<b>Топ сквадов:</b>\n\n"

        for i, (squad_id, group_name, leader_id, balance) in enumerate(top_squads, start=1):
            leader_name = await get_user_name(leader_id)
            squads_info += f"{i}. Сквад: {group_name}, Лидер: {leader_name}, Баланс: {balance} TON\n\n"
    else:
        squads_info = "Нет доступных сквадов."

    combined_text = welcome_text + squads_info
    await message.answer(combined_text, parse_mode='HTML')





@dp.message_handler(IsPrivate(), lambda message: message.text in [translate_text("Получить робота 🤖", message.from_user.id), "Get robot 🤖"])
async def get_robot_button_handler(message: types.Message):
    user = message.from_user
    ref = 0
    robots = mdb.get_user_robots(user.id)

    if len(robots) == 0:
        robot_name = give_robot_to_user(user.id)
        await message.answer(translate_text(f"🎁 Вы получили робота <b>{robot_name}</b> в подарок!", user.id))
        
    await message.answer(get_start_text(), reply_markup=create_start_keyboard(user.id))
        
@dp.message_handler(Text('🔙 Назад', ignore_case=True), state='*')
async def back(msg: types.Message, state: FSMContext):
    user = msg.from_user
    await state.finish()
    await msg.answer(translate_text('🔙 Возвращаю назад', user.id), reply_markup=create_start_keyboard(user.id))
    await msg.delete()

@dp.message_handler(Text('🔙Back', ignore_case=True), state='*')
async def back(msg: types.Message, state: FSMContext):
    user = msg.from_user
    await state.finish()
    await msg.answer(translate_text('🔙 Возвращаю назад', user.id), reply_markup=create_start_keyboard(user.id))
    await msg.delete()



@dp.message_handler(lambda message: message.text in [translate_text("👥 Реферальная система", message.from_user.id), "👥 Referral system"], IsSubscribed())
@dp.throttled(antiflood, rate=1)
async def refferal_system(msg: types.Message):
    user = msg.from_user
    username = await bot.get_me()
    refferals_count = get_refferals(msg.from_user.id)
    refferal_take_reward = refferals_count * 0.03

    text = (
        '🔥 За каждого человека приглашенного по вашей '
        'ссылке, вы получите <b>+0.03 TAKE</b> для прокачки робота!'
        'Для зачисления 0.03 TAKE он должен привязать свой кошелек.'
        '\n\n'
        '<i>🤝 Приглашено рефералов:</i> <b>{}</b>\n💰 TAKE: {:.3f}\n\n🔗 <i>Твоя реферальная ссылка:</i>'
        ' <code>t.me/{}?start={}</code>'.format(
            refferals_count,
            refferal_take_reward,
            username['username'],
            user.id)
    )

    translated_text = translate_text(text, user.id)

    await msg.answer(translated_text, parse_mode=html)

@dp.message_handler(lambda message: message.text in ["🔼 Улучшения", "🔼 Improvements"], IsSubscribed())
@dp.throttled(antiflood, rate=1)
async def upgrades(msg: types.Message):
    user = msg.from_user
    kb = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(text=translate_text("🔋 Улучшенный макс здоровье", user.id), callback_data="info-max_health"),
        InlineKeyboardButton(text=translate_text("⚔️ Плазменный меч", user.id), callback_data="info-damage"),
        InlineKeyboardButton(text=translate_text("⚙️ Улучшенный ремкомплект", user.id), callback_data="info-heal"),
        InlineKeyboardButton(text=translate_text("🛡 Титановая броня", user.id), callback_data="info-armor"),
    )

    robot = mdb.get_user_active_robot(user.id)
    robot_id = robot[1]
    robot_name = robot[2]
    robot_max_health = robot[8]
    robot_damage = robot[4]
    robot_heal = robot[5]
    robot_armor = robot[6]

    nft_status = check_owner_nft(user.id)
    discount_message = ""
    if nft_status:
        discount_message = "\n<i>🏷️ Вы имеете 10% скидку на все улучшения благодаря вашему НФТ!</i>"

    with open(f'data/photos/robot_{robot_id}.png', 'rb') as photo:
        await msg.answer_photo(
            photo,
            f"🤖 {translate_text('Робот', user.id)}: <b>{robot_name}</b>\n\n"
            f"<b>{translate_text('Выберите желаемое улучшение', user.id)}</b>\n\n"
            f"{translate_text('Ваша текущая статистика', user.id)}:\n"
            f"🔋 {translate_text('Макс здоровье', user.id)}: <b>{robot_max_health}</b>\n"
            f"⚔️ {translate_text('Урон', user.id)}: <b>{robot_damage}</b>\n"
            f"⚙️ {translate_text('Восстановление', user.id)}: <b>{robot_heal}</b>\n"
            f"🛡 {translate_text('Броня', user.id)}: <b>{robot_armor}</b>\n"
            f"{discount_message}",
            reply_markup=kb,
            parse_mode="HTML"
        )




@dp.message_handler(lambda message: message.text in [translate_text("🤖 Мои роботы", message.from_user.id), "🤖 My robots"], IsSubscribed())
@dp.throttled(antiflood, rate=1)
async def getrobot(msg: types.Message):
    user = msg.from_user
    robots = mdb.get_user_robots(user.id)

    if len(robots) == 0:
        await msg.answer(translate_text('🙁 У вас нет роботов, купите их в разделе <b>"🛒 Магазин"</b>', user.id))
        return

    robot = robots[0]
    robot_id = robot[1]
    robot_name = robot[2]
    robot_health = robot[3]
    robot_damage = robot[4]
    robot_heal = robot[5]
    robot_armor = robot[6]
    status = robot[7]
    robot_lvl = robot[9]
    robot_max_health = robot[8]

    with open(f'data/photos/robot_{robot_id}.png', 'rb') as photo:
        await msg.answer_photo(photo, f'''
🤖 {translate_text('Робот', user.id)}: <b>{robot_name}</b>
🆔 ID: <b>{robot_id}</b>

🔋 {translate_text('Макс здоровье', user.id)}: <b>{robot_max_health}</b>
⚡️ {translate_text('Здоровье', user.id)}: <b>{robot_health}</b>
⚔️ {translate_text('Урон', user.id)}: <b>{robot_damage}</b>
⚙️ {translate_text('Восстановление', user.id)}: <b>{robot_heal}</b>
🎚  {translate_text('Уровень робота', user.id)}: <b>{robot_lvl}</b> 
🛡 {translate_text('Броня', user.id)}: <b>{robot_armor}</b>''', reply_markup=await my_robots_key(0, robot_id, len(robots), status, user.id))

@dp.message_handler(lambda message: message.text in [translate_text("💎 Баланс", message.from_user.id), "💎 Balance"], IsSubscribed())
@dp.throttled(antiflood, rate=1)
async def getbalance(msg: types.Message, state: FSMContext):
    await state.finish()
    uid = msg.from_user.id
    user_balance = round(get_balance(uid), 5)
    take_balance = round(get_take_balance(uid), 5)

    await msg.answer(f'''🆔 {translate_text('Ваш ID', uid)}: <code>{uid}</code>

<b>💎 TON:</b> {user_balance}
<b>💰 TAKE</b> {take_balance}''', reply_markup=deposit_key, parse_mode=html)



@dp.message_handler(lambda message: message.text in [translate_text("🏆 Турнир", message.from_user.id), "🏆 Tournament"], IsSubscribed())
@dp.throttled(antiflood, rate=1)
async def tournament(msg: types.Message, state: FSMContext):
    await state.finish()
    uid = msg.from_user.id
    active_tour = get_active_tour()
    if active_tour is not None:
        active_tour = get_tour(active_tour[0])
        user_exist = get_tour_user_exist(uid, active_tour[0])
        if not user_exist:
            user_status = translate_text('🚫 Статуc: <b>Вы не участвуете</b>', user_id=uid)
            user_place = translate_text('нет места', user_id=uid)
        else:
            user_status = translate_text('✅ Статуc: <b>Вы участвуете</b>', user_id=uid)
            user_place = get_user_place(active_tour[0], uid)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text=translate_text('✅ Участвовать', user_id=uid), callback_data='tour-run_' + str(active_tour[0])))
        markup.add(InlineKeyboardButton(text=translate_text('📁 История турнира', user_id=uid), callback_data='tour_history'))

        top_users = get_tour_top_user(active_tour[0])
        count_users = get_count_tour_users(active_tour[0])
        if not count_users:
            top_users_text = translate_text('нет участников', user_id=uid)
        else:
            top_users_text = ''
            for i, user in enumerate(top_users, start=1):
                top_users_text += f'{i}. 👤 <a href="tg://user?id={user[0]}">{translate_text("Пользователь", user_id=uid)}</a> (<code>{user[0]}</code>): <b>{user[1]}</b> {translate_text("очков", user_id=uid)}\n'

        user_ball = get_user_tour_ball(active_tour[0], uid)
        await msg.answer(f'''<b>🏆 {translate_text("Турнир", user_id=uid)} <b>№{active_tour[0]}</b></b>

{user_status}
            
🕞 {translate_text("Дата начала турнира", user_id=uid)} - <b>{active_tour[2]}:00 по MSK</b>
🕔 {translate_text("Дата окончания турнира", user_id=uid)} - <b>{active_tour[3]}:00 по MSK</b>

⭐️ {translate_text("Всего участников", user_id=uid)}: <b>{count_users}</b>
🔝 {translate_text("Лидеры турнира", user_id=uid)}: ⤵️
{top_users_text}
💎 {translate_text("Цена вступления в турнир", user_id=uid)}: <b>0.1</b> TON
💵 {translate_text("Фонд турнира", user_id=uid)}: <b>{round(count_users * 0.09, 2)}</b> TON

🫵 {translate_text("Ваше место в турнире", user_id=uid)}: <b>{user_place}</b>
⚡️ {translate_text("У вас очков", user_id=uid)}: <b>{user_ball}</b>

🏆{translate_text("В турнире победит участник, у которого будут наибольшее количество победных боев в ", user_id=uid)}"👥 {translate_text("Многопользовательской игре", user_id=uid)}" <b>({translate_text("игры со ставкой 0 TON не считаются", user_id=uid)})</b>. 
⭐️{translate_text("Каждая победа вам приносит 1 очко.", user_id=uid)}''',
                         reply_markup=markup, parse_mode=html)
    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text=translate_text('📁 История турнира', user_id=uid), callback_data='tour_history'))
        await msg.answer(f'''<b>⭕️ {translate_text("Нет активных турниров, ожидайте новостей!", user_id=uid)}</b>''',
                         reply_markup=markup, parse_mode=html)


@dp.message_handler(lambda message: message.text in [translate_text("🛒 Магазин", message.from_user.id), "🛒 Shop"], IsSubscribed())
@dp.throttled(antiflood, rate=1)
async def market(message: types.Message):
    user = message.from_user
    robots = mdb.get_robots()
    count_robots = len(robots)
    if count_robots == 0:
        await message.answer(translate_text('Нет роботов на продаже!', message.from_user.id))
        return

    robot = robots[0]

    robot_id = robot[0]
    robot_name = robot[1]
    robot_health = robot[2]
    robot_damage = robot[3]
    robot_heal = robot[4]
    robot_armor = robot[5]
    robot_price = robot[6]

    with open(f'data/photos/robot_{robot_id}.png', 'rb') as photo:
        await message.answer_photo(photo, f'''
🤖 {translate_text('Робот', message.from_user.id)}: <b>{robot_name}</b>
🆔 'ID': <b>{robot_id}</b>

🔋 {translate_text('Макс здоровье', message.from_user.id)}: <b>{robot_health}</b>
⚔️ {translate_text('Урон', message.from_user.id)}: <b>{robot_damage}</b>
⚙️ {translate_text('Восстановление', message.from_user.id)}: <b>{robot_heal}</b>
🛡 {translate_text('Броня', message.from_user.id)}: <b>{robot_armor}</b>

💎 <b>{translate_text('Стоимость', message.from_user.id)} {robot_price} ТАКЕ</b>''', reply_markup=await market_key(robot_id,
                                                                                                                    robots.index(robot) + 1,
                                                                                                                    robots.index(robot) - 1,
                                                                                                                    count_robots,
                                                                                                                    robots.index(robot),
                                                                                                                    user.id
                                                                                                                    )
                                                                                                   )
                               


@dp.message_handler(lambda message: message.text in [translate_text("🔝 Топ игроков", message.from_user.id), "🔝 Top players"], IsSubscribed())
@dp.throttled(antiflood, rate=1)
async def get_top(msg: types.Message):
    top_lvl = new_top_lvl()
    top_bet = new_top_bet_games()
    top_refferals = get_top_refferals()  # Получение топ 10 рефералов

    text = '🏆 <b>Топ игроков:</b>\n\n'

    text += '<b>По уровню робота:</b>\n'
    for i, user in enumerate(top_lvl):
        user_id = user[0]
        user_lvl = user[9]  # Изменить индекс с 9 на 3
        user_robot = user[2]
        try:
            player_name = await bot.get_chat(user_id)
            player_name = player_name.first_name
            player_name = f'<a href="tg://user?id={user_id}">{player_name}</a>'
        except:
            player_name = f'<a href="tg://user?id={user_id}">Пользователь</a>'

        text += f'{hbold(i + 1)}. {player_name} - {user_lvl} - {user_robot}\n'

    text += '\n<b>По платным боям:</b>\n'
    for i, user in enumerate(top_bet):
        user_id = user[0]
        user_bet = round(user[1], 3)
        try:
            player_name = await bot.get_chat(user_id)
            player_name = player_name.first_name
            player_name = f'<a href="tg://user?id={user_id}">{player_name}</a>'
        except:
            player_name = f'<a href="tg://user?id={user_id}">Пользователь</a>'

        text += f'{hbold(i + 1)}. {player_name} - {user_bet:.2f}\n'

    text += '\n<b>По рефералам:</b>\n'
    for i, refferal in enumerate(top_refferals):
        refferal_id = refferal[0]
        refferal_count = refferal[1]
        try:
            refferal_name = await bot.get_chat(refferal_id)
            refferal_name = refferal_name.first_name
            refferal_name = f'<a href="tg://user?id={refferal_id}">{refferal_name}</a>'
        except:
            refferal_name = f'<a href="tg://user?id={refferal_id}">Пользователь</a>'

        text += f'{hbold(i + 1)}. {refferal_name} - {refferal_count}\n'

    # перевод текста
    user_lang = check_user_language(msg.from_user.id)
    if user_lang == 'en':
        text = text.replace('Топ игроков:', 'Top players:')
        text = text.replace('По уровню робота:', 'By robot level:')
        text = text.replace('По платным боям:', 'Paid battles:')
        text = text.replace('По рефералам:', 'Referrals:')
        text = text.replace('Пользователь', 'User')
    elif user_lang == 'ru':
        pass  # текст уже на русском языке
    else:
        # используем язык по умолчанию (русский)
        pass

    await msg.answer(text, parse_mode='HTML')



@dp.message_handler(lambda message: message.text in [translate_text("🎮 Играть", message.from_user.id), "🎮 Play"], IsSubscribed())
@dp.throttled(antiflood, rate=1)
async def game_match(message: types.Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(KeyboardButton(translate_text("⚔️ Создать бой", user_id)), KeyboardButton(translate_text("🤝 Присоединиться к бою", user_id)))
    keyboard.row(KeyboardButton(translate_text("🛡️ Мои активные бои", user_id)), KeyboardButton(translate_text("📜 История моих боев", user_id)))

    keyboard.row(KeyboardButton(translate_text("🔙 Назад", user_id)))
    await message.answer(translate_text('Чтобы начать играть, нажмите одну из кнопок', user_id),
                         reply_markup=keyboard,
                         )


@dp.message_handler(text='⚔️ Create a battle')
@dp.throttled(antiflood, rate=1)
async def create_game_0(message: types.Message):
    user_id = message.from_user.id
    await message.answer(translate_text('<b>💎 Выберите сумму ставки на бой:</b>', user_id), reply_markup=bet_key)


@dp.message_handler(text='🤝 Join the fight')
@dp.throttled(antiflood, rate=1)
async def join_to_game(message: types.Message):
    active_games = mdb.get_active_games()
    user_id = message.from_user.id
    if len(active_games) == 0:
        await message.answer(translate_text('''<b>❌ Нет активных боев!</b>

📌 Создайте сами в разделе "🔸 Создать бой" или ожидайте других игроков.'''), user_id)
        return

    markup = InlineKeyboardMarkup()
    for game in active_games:
        markup.add(InlineKeyboardButton(text=f'#{game[0]} | {game[1]} TON', callback_data=f'join_{game[0]}'))

    await message.answer(translate_text('<b>⚔️ Активные бои:</b>', user_id), reply_markup=markup)


@dp.message_handler(text='🛡️ My active battles')
@dp.throttled(antiflood, rate=1)
async def my_active_games(message: types.Message):
    user = message.from_user
    active_games = mdb.get_user_active_games(user.id)
    if len(active_games) == 0:
        await message.answer(translate_text('''<b>❌ Нет активных боев!</b>

📌 Можете создать разделе "🔸 Создать бой".'''), user.id)
        return

    markup = InlineKeyboardMarkup()
    for game in active_games:
        markup.add(InlineKeyboardButton(text=f'#{game[0]} | {game[1]} TON', callback_data=f'mygame_{game[0]}'))

    await message.answer(translate_text('<b>⚔️ Ваши активные бои:</b>', user.id), reply_markup=markup)


@dp.message_handler(text='📜 History of my fights')
@dp.throttled(antiflood, rate=1)
async def game_history(message: types.Message):
    user = message.from_user
    history = mdb.get_user_all_games(user.id)
    if len(history) == 0:
        await message.answer(translate_text('''<b>❌ Вы еще не участвовали в боях.</b>'''), user.id)
        return

    text = f'📁 History of battles of a player with ID {user.id}\n\n'
    for game in history:
        if game[5] == 0:
            winner = 'The battle has not yet started, is not finished, or has been deleted!'
        else:
            winner = game[5]

        if game[2] == 'finished':
            status = 'ENDED'
        elif game[2] == 'started':
            status = 'STARTED'
        elif game[2] == 'expectation':
            status = 'WAITING'
        else:
            status = 'DELETED'

        try:
            player1 = await bot.get_chat(game[3])
            player1 = player1.first_name

            player2 = await bot.get_chat(game[4])
            player2 = player2.first_name
        except:
            player1 = f'User'
            player2 = f'User'

        text += f'''⚔️ Бой номер #{game[0]}
👤 Player 1: {player1} ({game[3]})
👤 Player 2: {player2} ({game[4]})
📌 Status: {status}
💎 Bet: {game[1]} TON
📆 Date: {game[6]}
👑 Winner: {winner}
➖➖➖➖➖➖➖➖➖
'''

    with open(f'data/texts/{user.id}-history.txt', 'w', encoding='UTF-8') as file:
        file.write(text)

    input_file = InputFile(f'data/texts/{user.id}-history.txt', filename=f'{user.id}-history.txt')
    await message.answer_document(input_file, caption='Your battles history.')

    os.remove(f'data/texts/{user.id}-history.txt')


@dp.message_handler(text='⚔️ Создать бой')
@dp.throttled(antiflood, rate=1)
async def create_game_0(message: types.Message):
    await message.answer('<b>💎 Выберите сумму ставки на бой:</b>', reply_markup=bet_key)


@dp.message_handler(text='🤝 Присоединиться к бою')
@dp.throttled(antiflood, rate=1)
async def join_to_game(message: types.Message):
    active_games = mdb.get_active_games()
    if len(active_games) == 0:
        await message.answer('''<b>❌ Нет активных боев!</b>

📌 Создайте сами в разделе "🔸 Создать бой" или ожидайте других игроков.''')
        return

    markup = InlineKeyboardMarkup()
    for game in active_games:
        markup.add(InlineKeyboardButton(text=f'#{game[0]} | {game[1]} TON', callback_data=f'join_{game[0]}'))

    await message.answer('<b>⚔️ Активные бои:</b>', reply_markup=markup)


@dp.message_handler(text='🛡️ Мои активные бои')
@dp.throttled(antiflood, rate=1)
async def my_active_games(message: types.Message):
    user = message.from_user
    active_games = mdb.get_user_active_games(user.id)
    if len(active_games) == 0:
        await message.answer('''<b>❌ Нет активных боев!</b>

📌 Можете создать разделе "🔸 Создать бой".''')
        return

    markup = InlineKeyboardMarkup()
    for game in active_games:
        markup.add(InlineKeyboardButton(text=f'#{game[0]} | {game[1]} TON', callback_data=f'mygame_{game[0]}'))

    await message.answer('<b>⚔️ Ваши активные бои:</b>', reply_markup=markup)


@dp.message_handler(text='📜 История моих боев')
@dp.throttled(antiflood, rate=1)
async def game_history(message: types.Message):
    user = message.from_user
    history = mdb.get_user_all_games(user.id)
    if len(history) == 0:
        await message.answer('''<b>❌ Вы еще не участвовали в боях.</b>''')
        return

    text = f'📁 История боев игрока с ID {user.id}\n\n'
    for game in history:
        if game[5] == 0:
            winner = 'Бой еще не начат или не закончен или удален!'
        else:
            winner = game[5]

        if game[2] == 'finished':
            status = 'БОЙ ЗАКОНЧЕН'
        elif game[2] == 'started':
            status = 'БОЙ НАЧАТ'
        elif game[2] == 'expectation':
            status = 'В ОЖИДАНИИ'
        else:
            status = 'БОЙ УДАЛЕН'

        try:
            player1 = await bot.get_chat(game[3])
            player1 = player1.first_name

            player2 = await bot.get_chat(game[4])
            player2 = player2.first_name
        except:
            player1 = f'Пользователь'
            player2 = f'Пользователь'

        text += f'''⚔️ Бой номер #{game[0]}
👤 Игрок 1: {player1} ({game[3]})
👤 Игрок 2: {player2} ({game[4]})
📌 Статус: {status}
💎 Ставка: {game[1]} TON
📆 Дата игры: {game[6]}
👑 Победитель: {winner}
➖➖➖➖➖➖➖➖➖
'''

    with open(f'data/texts/{user.id}-history.txt', 'w', encoding='UTF-8') as file:
        file.write(text)

    input_file = InputFile(f'data/texts/{user.id}-history.txt', filename=f'{user.id}-history.txt')
    await message.answer_document(input_file, caption='История ваших боев.')

    os.remove(f'data/texts/{user.id}-history.txt')
    
@dp.message_handler(state=WithdrawTon.amount)
@dp.throttled(antiflood, rate=1)
async def process_sum(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    valid = False
    try:
        float(message.text)
        valid = True
    except ValueError:
        pass
    if valid and 0 < float(message.text) <= get_balance(user_id):
        amount = round(float(message.text), 6)
        if amount < 0.1:
            text = '🚫 Минимальная сумма вывода 0.1 TON!'
            await message.answer(translate_text(text, user_id))
            return
        text = f'<i>📤 Подтвердите вывод</i>\n\n💎 Сумма: <b>{amount}</b> TON'
        await message.answer(translate_text(text, user_id), reply_markup=await withdraw_key(amount))
        await state.finish()
    elif valid and float(message.text) > get_balance(user_id):
        text = "***Недостаточно средств...***"
        await message.answer(translate_text(text, user_id), parse_mode=ParseMode.MARKDOWN, reply_markup=create_start_keyboard(user_id))
        await state.finish()
    else:
        text = "***Некорректные данные.*** Попробуйте еще раз..."
        await message.answer(translate_text(text, user_id), parse_mode=ParseMode.MARKDOWN, reply_markup=create_start_keyboard(user_id))
        await state.finish()



@dp.message_handler(state=WithdrawTake.amount)
@dp.throttled(antiflood, rate=1)
async def process_sum_take(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    valid = False
    try:
        float(message.text)
        valid = True
    except ValueError:
        pass
    if valid and 0 < float(message.text) <= get_take_balance(user_id):
        amount = round(float(message.text), 6)
        if amount < 0.1:
            text = '🚫 Минимальная сумма вывода 0.1 TAKE!'
            await message.answer(translate_text(text, user_id))
            return
        text = f'📤 Подтвердите вывод\n\n💎 Сумма: <b>{amount}</b> TAKE'
        await message.answer(translate_text(text, user_id), reply_markup=await withdraw_key_take(amount))
        await state.finish()
    elif valid and float(message.text) > get_take_balance(user_id):
        text = "***Недостаточно средств...***"
        await message.answer(translate_text(text, user_id), parse_mode=ParseMode.MARKDOWN, reply_markup=create_start_keyboard(user_id))
        await state.finish()
    else:
        text = "***Некорректные данные.*** Попробуйте еще раз..."
        await message.answer(translate_text(text, user_id), parse_mode=ParseMode.MARKDOWN, reply_markup=create_start_keyboard(user_id))
        await state.finish()


@dp.message_handler(state=DepositTon.amount)
async def deposit_ton_2(message: types.Message, state: FSMContext):
    user = message.from_user
    user_id = message.from_user.id
    try:
        amount = float(message.text)
    except ValueError:
        text = '<b>Введите число!</b>'
        await message.answer(translate_text(text, user_id), reply_markup=back_key, parse_mode=html)
        return

    invoice_id, invoice_link = await create_invoice(amount, user.id, 'TONCOIN')

    if invoice_id is None:
        text = '<b>🚫 Ошибка при создание счета, сумма слишком маленькая, попробуйте еще раз!</b>'
        await message.answer(translate_text(text, user_id), parse_mode=html)
        await bot.send_message(1251379793, f'🚫 Ошибка при создание счета у юзера {user.id}\nТекст: {invoice_link}',
                               parse_mode=html)
        await state.finish()
        return

    await message.answer('Обработка...', reply_markup=create_start_keyboard(user.id))

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(text=translate_text('🔗 Оплатить', user_id), url=invoice_link))
    markup.add(InlineKeyboardButton(text=translate_text('✅ Я оплатил', user_id), callback_data='check-ton_' + str(invoice_id)))

    text = '''<b>💎 Пополнение с помощью TON:</b>

❗️ У вас есть 10 минут что бы совершить платеж ❗

👇 Нажмите на <b>"🔗 Оплатить"</b> что бы совершить платеж, после оплаты нажмите на <b>"✅ Я оплатил"</b>!'''
    await message.answer(translate_text(text, user_id), reply_markup=markup, parse_mode=html)
    await state.finish()



@dp.message_handler(state=DepositTake.amount)
async def deposit_take_2(message: types.Message, state: FSMContext):
    user = message.from_user
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer(translate_text('<b>Введите число!</b>', user.id), reply_markup=back_key, parse_mode=html)
        return

    invoice_id, invoice_link = await create_invoice(amount, user.id, 'TAKE')

    if invoice_id is None:
        await message.answer(translate_text('<b>🚫 Ошибка при создание счета, сумма слишком маленькая, попробуйте еще раз!</b>', user.id),
                             parse_mode=html)
        await bot.send_message(1251379793, f'🚫 Ошибка при создание счета у юзера {user.id}\nТекст: {invoice_link}',
                               parse_mode=html)
        await state.finish()
        return

    await message.answer(translate_text('Обработка...', user.id), reply_markup=create_start_keyboard(user.id))

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(text='🔗 Оплатить', url=invoice_link))
    markup.add(InlineKeyboardButton(text='✅ Я оплатил', callback_data='check-take_' + str(invoice_id)))
    await message.answer(f'''<b>💎 {translate_text('Пополнение с помощью TAKE:', user.id)}</b>

❗️ {translate_text('У вас есть 10 минут что бы совершить платеж', user.id)} ❗

👇 {translate_text('Нажмите на <b>"🔗 Оплатить"</b> что бы совершить платеж, после оплаты нажмите на <b>"✅ Я оплатил"</b>!', user.id)}''',
                         reply_markup=markup, parse_mode=html)
    await state.finish()

@dp.message_handler(state=DepositCry.amount)
async def receive_amount_in_ton(message: types.Message, state: FSMContext):
    user = message.from_user
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer(translate_text('<b>Введите число!</b>', user.id))
        return

    await message.answer(translate_text('Обработка...', user.id), reply_markup=create_start_keyboard(user.id))
    invoice_id, invoice_url = await create_cry_invoice(amount, 'TON', user.id)

    if invoice_id == 'small':
        await message.answer(translate_text('<b>🚫 Сумма слишком маленькая!</b>', user.id))
        return

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(text='🔗 Оплатить', url=invoice_url))
    markup.add(
        InlineKeyboardButton(text='✅ Я оплатил', callback_data='check-cry_' + str(invoice_id)))
    await message.answer(f'''<b>💎 {translate_text('Пополнение с помощью TON:', user.id)}</b>

❗️ {translate_text('У вас есть 10 минут что бы совершить платеж', user.id)} ❗

👇 {translate_text('Нажмите на <b>"🔗 Оплатить"</b> что бы совершить платеж, после оплаты нажмите на <b>"✅ Я оплатил"</b>!', user.id)}''',
                         reply_markup=markup)
    await state.finish()


@dp.message_handler(lambda message: message.text in [translate_text("🏪 Рынок", message.from_user.id), "🏪 Market"], IsSubscribed())
@dp.throttled(antiflood, rate=1)
async def bazar(message: types.Message):
    robots = mdb.get_bazar_robots()
    user_id = message.from_user.id
    count_robots = len(robots)
    if count_robots == 0:
        await message.answer(translate_text('Нет роботов на продаже!', message.from_user.id))
        return

    robot = robots[0]

    robot_seller = robot[0]
    robot_id = robot[2]
    robot_name = robot[3]
    robot_health = robot[4]
    robot_damage = robot[5]
    robot_heal = robot[6]
    robot_armor = robot[7]
    robot_price = robot[10]
    robot_lvl = robot[8]

    with open(f'data/photos/robot_{robot_id}.png', 'rb') as photo:
        await message.answer_photo(photo, f'''
🤖 {translate_text('Робот', message.from_user.id)}: <b>{robot_name}</b>
👤 {translate_text('Продавец', message.from_user.id)}: <b>{robot_seller}</b>
🆔 'ID': <b>{robot_id}</b>

🔋 {translate_text('Макс здоровье', message.from_user.id)}: <b>{robot_health}</b>
⚔️ {translate_text('Урон', message.from_user.id)}: <b>{robot_damage}</b>
⚙️ {translate_text('Восстановление', message.from_user.id)}: <b>{robot_heal}</b>
🎚  {translate_text('Уровень робота', message.from_user.id)}: <b>{robot_lvl}</b> 
🛡  {translate_text('Броня', message.from_user.id)}: <b>{robot_armor}</b>

💎 <b>{translate_text('Стоимость', message.from_user.id)} {robot_price} ТАКЕ</b>''', reply_markup=await bazar_key(robot_id,
                                                                                                                  robots.index(robot) + 1,
                                                                                                                  robots.index(robot) - 1,
                                                                                                                  count_robots,
                                                                                                                  robots.index(robot),
                                                                                                                  robot_seller,
                                                                                                                  user_id  
                                                                                                                  )
                                               )
                               




@dp.message_handler(lambda message: message.text in [translate_text("🏭 Локации", message.from_user.id), "🏭 Locations"], IsSubscribed())
@dp.throttled(antiflood, rate=1)
async def locations(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    keyboard = await locations_key(user_id)
    text = translate_text('Выберите локацию:', user_id)
    await message.answer(text, reply_markup=keyboard)

    
@dp.message_handler(lambda message: message.text in [translate_text("🕹 Игры ТАКЕ", message.from_user.id), "🕹 TAKE Games"])
@dp.throttled(antiflood, rate=1)
async def games_tontake(message: types.Message):
    user_id = message.from_user.id
    language = check_user_language(user_id)

    if language == 'ru':
        button1 = InlineKeyboardButton("Кликер зерносклад", url="https://zernosklad.com/")
        button2 = InlineKeyboardButton("Стратегия TONvsTAKE", url="https://tontake.com/")
        text = "Здесь вы также можете играть и зарабатывать таке монеты! Выберите игру:"
    elif language == 'en':
        button1 = InlineKeyboardButton("Grain storage clicker", url="https://zernosklad.com/")
        button2 = InlineKeyboardButton("TONvsTAKE strategy", url="https://tontake.com/")
        text = "Here you can also play and earn take coins! Choose a game:"

    markup = InlineKeyboardMarkup(row_width=1).add(button1, button2)

    await message.answer(text, reply_markup=markup)

    
    
    
    
    
    
    
    
@dp.message_handler(Command(['a', 'admin']))
async def admin(message: Message):
    if message.from_user.id in administrators:
        take_balance = await get_all_balance('TAKE')
        ton_balance = await get_all_balance()
        # cry_ton_balance = await get_cry_balance('ton')
        await message.answer(
            f'Админка:\n\nБаланс TAKE: <b>{take_balance}</b>\nБаланс TON: <b>{ton_balance}</b>',
            reply_markup=admin_key,
            parse_mode=html
        )
    else:
        await message.answer("You don't have permission to access the admin panel.")


# @dp.message_handler(IsAdmin(), Command(['restore_robot']))
# async def restore_robots(message: Message):
#     robots = get_all_user_robots()
#     counter = 0
#     for robot in robots:
#         counter += 1
#         user_id = robot[0]
#         health = robot[1]
#         damage = robot[2]
#         heal = robot[3]
#         armor = robot[4]
#         lvl = robot[5]
#         mdb.add_robot(user_id, 999, "Титан", health, damage, heal, armor, lvl)
#         mdb.update_robot_status(user_id, 999)
#
#     await message.answer(f'Процесс завершен, добавлено {counter} роботов.')


@dp.message_handler(state=SendAllText.text)
async def send_to_users(message: Message, state: FSMContext):
    user.id = message.from_user.id
    users = get_users()
    bad_result = 0
    good_result = 0
    async with state.proxy() as data:
        data["text"] = message.text

    async with state.proxy() as data:
        text = data["text"]
    start_time = time.time()
    await state.finish()
    await message.answer('Рассылка начата!')
    for user in users:
        for x in user:
            try:
                await bot.send_message(x, text, reply_markup=create_start_keyboard(user.id), parse_mode=html)
                await asyncio.sleep(0.05)
                good_result += 1
            except:
                bad_result += 1
    end_time = time.time()
    await message.answer(
        f"""<b>Рассылка завершена!</b>

Заняло время: <code>{round(end_time - start_time, 2)}</code> секунд
Успешно: <code>{good_result}</code>
Неуспешно: <code>{bad_result}</code>""",
        parse_mode=html
    )


# Рассылка c фото
@dp.message_handler(content_types="photo", state=SendAllPhoto.photo)
async def send_to_users_photo(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data["photo"] = message.photo[0].file_id
    await bot.send_message(
        message.from_user.id,
        "Напишите текст для рассылки:",
        reply_markup=cancel_adm_key,
    )
    await SendAllPhoto.next()


@dp.message_handler(state=SendAllPhoto.text)
async def send_to_users_text(message: Message, state: FSMContext):
    users = get_users()
    bad_result = 0
    good_result = 0
    async with state.proxy() as data:
        data["text"] = message.text

    async with state.proxy() as data:
        text = data["text"]
        photo_id = data["photo"]
    start_time = time.time()
    await state.finish()
    await message.answer('Рассылка начата!')
    for user in users:
        for x in user:
            try:
                await bot.send_photo(x, photo_id, text, reply_markup=create_start_keyboard(user.id), parse_mode=html)
                await asyncio.sleep(0.05)
                good_result += 1
            except:
                bad_result += 1

    end_time = time.time()
    await message.answer(
        f"""<b>Рассылка завершена!
Заняло время:{end_time - start_time}
Успешно: {good_result}
Неуспешно: {bad_result}</b>""",
        parse_mode=html
    )


@dp.message_handler(state=StartTour.date)
async def start_tour_2(message: Message, state: FSMContext):
    end_date = message.text
    if ':' in end_date:
        end_date = end_date.split(':')[0]
    print(end_date)
    utc_now = datetime.datetime.now(pytz.utc)
    moscow_tz = pytz.timezone('Europe/Moscow')
    moscow_time = utc_now.astimezone(moscow_tz)
    moscow_now = datetime.datetime.strftime(moscow_time, '%d.%m.%y %H')
    count_tour = get_count_exist_tour()
    add_tour(count_tour, moscow_now, end_date)

    await message.answer(f'✅ Успешно начать турнир под номером <b>№{count_tour}</b>', parse_mode=html)
    await state.finish()


@dp.message_handler(state=SearchUser.id)
async def user_search(message: Message, state: FSMContext):
    user_id = message.text

    if not check_user(user_id):
        await message.answer("❌ Пользовател не найден в боте!")
        return

    ref_count = get_refferals(user_id)
    ton_balance = round(get_balance(user_id), 4)
    take_balance = round(get_take_balance(user_id), 4)

    await message.answer(
        f"""
👤 Информация о <a href="tg://user?id={user_id}"><b>пользователе</b></a>

🆔 ID: <b>{user_id}</b>
➖➖➖➖➖➖➖➖➖
💰 Баланс TAKE: <b>{take_balance}</b>
➖➖➖➖➖➖➖➖➖
💎 Баланс TON: <b>{ton_balance}</b>
➖➖➖➖➖➖➖➖➖
👥 Количество рефералов: <b>{ref_count}</b>""",
        reply_markup=await admin_search_key(user_id),
        parse_mode=html
    )
    await state.finish()


@dp.message_handler(state=EditUserBalance.value)
async def edit_4(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    currency = data['currency']
    edit_type = data['edit_type']
    try:
        value = round(float(message.text), 4)
    except ValueError:
        await message.answer('Введите число!', reply_markup=cancel_adm_key)
        return
    if edit_type == 'give' and currency == 'balance':
        add_take_balance(user_id, value)
    elif edit_type == 'give' and currency == 'ton_balance':
        add_balance(user_id, value)
    elif edit_type == 'take' and currency == 'balance':
        decrease_take_balance(user_id, value)
    elif edit_type == 'take' and currency == 'ton_balance':
        decrease_balance(user_id, value)
    await message.answer(f'<b>Успешно</b>')
    await state.finish()


@dp.message_handler(state=NewRobot.name)
async def new_robot_1(message: Message, state: FSMContext):
    name = message.text
    async with state.proxy() as data:
        data['name'] = name

    await message.answer('✅ Принято!\n\n<b>Теперь введите здоровье для робота:</b>', reply_markup=cancel_adm_key)
    await NewRobot.health.set()


@dp.message_handler(state=NewRobot.health)
async def new_robot_2(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['health'] = message.text

    await message.answer('✅ Принято!\n\n<b>Теперь введите урон для робота:</b>', reply_markup=cancel_adm_key)
    await NewRobot.damage.set()


@dp.message_handler(state=NewRobot.damage)
async def new_robot_3(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['damage'] = message.text

    await message.answer('✅ Принято!\n\n<b>Теперь введите восстановление для робота:</b>', reply_markup=cancel_adm_key)
    await NewRobot.heal.set()


@dp.message_handler(state=NewRobot.heal)
async def new_robot_4(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['heal'] = message.text

    await message.answer('✅ Принято!\n\n<b>Теперь введите броню для робота:</b>', reply_markup=cancel_adm_key)
    await NewRobot.armor.set()


@dp.message_handler(state=NewRobot.armor)
async def new_robot_5(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['armor'] = message.text

    await message.answer('✅ Принято!\n\n<b>Теперь введите цену для робота в TAKE:</b>', reply_markup=cancel_adm_key)
    await NewRobot.price.set()


@dp.message_handler(state=NewRobot.price)
async def new_robot_6(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['price'] = message.text

    await message.answer('✅ Принято!\n\n<b>Теперь скинтье фото для робота:</b>', reply_markup=cancel_adm_key)
    await NewRobot.photo.set()


@dp.message_handler(state=NewRobot.photo, content_types=ContentTypes.PHOTO)
async def new_robot_7(message: Message, state: FSMContext):
    photo = message.photo[-1]

    photo_id = photo.file_id

    async with state.proxy() as data:
        data['photo'] = photo_id

    robot_data = await state.get_data()
    await message.answer_photo(photo_id, f'''
Название: <b>{robot_data['name']}</b>

Здоровье: <b>{robot_data['health']}</b>
Урон: <b>{robot_data['damage']}</b>
Восстановление: <b>{robot_data['heal']}</b>
Броня: <b>{robot_data['armor']}</b>

Стоимость <b>{robot_data['price']}</b> ТАКЕ

<b>👇 Потвердите данные создания робота:</b>
''', reply_markup=confirm_new_robot)
    await NewRobot.confirm.set()


@dp.message_handler(state=NewRobot.confirm)
async def new_robot_8(message: Message):
    await message.answer('<b>👆 Подтвердите создание нового робота или отмените 👇</b>', reply_markup=cancel_adm_key)


@dp.message_handler(state=DeleteRobot.robot_id)
async def del_robot_2(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer('ID робота должен быть в виде числа, попробуйте еще раз!', reply_markup=cancel_adm_key)
        return

    robot_id = message.text

    await state.update_data(robot_id=robot_id)

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('Удалить', callback_data='confirm-delete-robot'))
    markup.add(InlineKeyboardButton('Отменить', callback_data='cancel_admin'))

    await message.answer(f'❓ Вы точно хотите удалить робот с ID {robot_id}?', reply_markup=markup)

    await DeleteRobot.confirm.set()


@dp.message_handler(state=DeleteRobot.confirm)
async def delete_confirm(message: Message):
    await message.answer('<b>👆 Подтвердите удаления робота или отмените 👇</b>', reply_markup=cancel_adm_key)
    
    

from data.functions.db_squads import get_squads_count

@dp.message_handler(lambda message: message.text in [translate_text("⭐️ Статистика", message.from_user.id), "⭐️ Statistic"], IsSubscribed())
@dp.throttled(antiflood, rate=1)
async def super_statistic(message: types.Message):
    # Calculate the number of months and days since September 27, 2023
    start_date = datetime.datetime(2023, 9, 27)

    today = datetime.datetime.today()
    diff = today - start_date
    months = diff.days // 30
    days = diff.days % 30

    # Get the number of users, battles, robots, and squads from the database
    user_count = get_user_count()
    battle_count = get_battle_count()
    robots_count = get_robots_count()
    squads_count = get_squads_count()

    # Translate the text using the user's selected language
    text = (
        f"<b>🤖 Боту: {months} месяцев {days} дней! 📅</b>\n\n"
        f"<b>За это время:</b>\n"
        f"{hbold('👥 Нас уже')} {user_count} {hbold('человек!')}\n"
        f"{hbold('🤜 Мы провели')} {battle_count} {hbold('битв!')}\n"
        f"{hbold('🤖 В игре уже')} {robots_count} {hbold('роботов!')}\n"
        f"{hbold('🏆 В игре уже')} {squads_count} {hbold('скавадов!')}\n"
    )
    translated_text = translate_text(text, message.from_user.id)

    # Send the statistics as a message with smileys and HTML tags
    await message.answer(
        translated_text,
        parse_mode="HTML",
    )

