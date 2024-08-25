import asyncio
import random
from time import time

from data.functions.text import get_start_text, robot_chances_text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.exceptions import ChatNotFound
from data.functions.game import finish_game
from bot import bot, dp, mdb
from data.config import LOGS, administrators, chat_id, address
from data.functions.db import *
from data.config import LOGS, TAKE_CHAT, administrators
from aiogram import types
from aiogram.utils.exceptions import MessageToEditNotFound
from filters import IsPrivate, IsSubscribed
from aiogram.types import InputMediaPhoto
import os
from collections import defaultdict
from typing import Union

from handlers.users.handler import check_owner_nft
from data.payments.rocket import transfer

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from data.functions.db_squads import add_user_to_squad, get_squad_id_by_user_id, add_squad_balance, get_all_squads, delete_squad_from_db, get_squad_admin_time, update_squad_admin_time
from data.payments.tonscan_api import TonScan
from data.functions.db import *
from data.functions.locations_db import *
from data.functions.game import create_game, start_game, attack_game
from data.functions.text import info_text
from keyboards.users.keyboards import get_sand_keyboard, get_island_keyboard, create_start_keyboard, get_atlantida_keyboard, admin_withdraw_key, market_key, \
    my_robots_key, bet_confirm_key, join_game_key, send_challenge, attack_key, only_attack_key, heal_key, \
    confirm_heal_key, not_respond_key, bet_confirm_zero_key, get_factory_keyboard, bazar_key, sell_my_robots_key, confirmation_keyboard, double_strike_key, \
        get_pay_atlantida_keyboard, get_pay_atlantida_keyboard_confirm, get_robot_keyboard, get_sand_zero_keyboard, admin_withdraw_take_key
from text import win_txt_pve

from data.functions.translate import translate_text

html = 'HTML'


async def callantiflood(*args, **kwargs):
    m = args[0]
    # await m.answer("Не спеши :)")


    
    
sand_distance_from_base = {}
factory_distance_from_base = {}
island_distance_from_base = {}
atlantida_distance_from_base = {}

@dp.callback_query_handler(text="sand")
@dp.throttled(callantiflood, rate=2)
async def sand_location(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    if user_id in factory_distance_from_base and factory_distance_from_base[user_id] > 0:
        text = translate_text("Вы не можете зайти в пустыню, пока вы находитесь на заводе.", user_id)
        await bot.answer_callback_query(
            callback_query_id=callback.id,
            text=text,
            show_alert=True
        )
        return

    if user_id in island_distance_from_base and island_distance_from_base[user_id] > 0:
        text = translate_text("Вы не можете зайти в пустыню, пока вы находитесь на острове.", user_id)
        await bot.answer_callback_query(
            callback_query_id=callback.id,
            text=text,
            show_alert=True
        )
        return

    if user_id in atlantida_distance_from_base and atlantida_distance_from_base[user_id] > 0:
        text = translate_text("Вы не можете зайти в пустыню, пока вы находитесь в Атлантиде.", user_id)
        await bot.answer_callback_query(
            callback_query_id=callback.id,
            text=text,
            show_alert=True
        )
        return

    photo_url = 'https://imageup.ru/img14/4446827/img_2202.jpeg'
    caption = translate_text("Локация: Пустыня", user_id)

    await bot.send_photo(
        callback.from_user.id,
        photo_url,
        caption=caption,
        reply_markup=get_sand_keyboard(user_id)
    )

        
@dp.callback_query_handler(text="hod")
@dp.throttled(callantiflood, rate=0.5)
async def hod(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    health = get_robot_health(callback.from_user.id)
    if health <= 5:
        new_photo = open('data/photos/sand.png', 'rb')
        new_caption = translate_text('Ваше здоровье слишком низкое, вам нужно восстановиться на заводе перед тем, как идти в бой.', user_id)
        await bot.edit_message_media(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            media=InputMediaPhoto(media=new_photo, caption=new_caption),
            reply_markup=get_sand_zero_keyboard(user_id)
        )
        return
    else:
        # Update the distance for the user
        if callback.from_user.id not in sand_distance_from_base:
            sand_distance_from_base[callback.from_user.id] = 0
        sand_distance_from_base[callback.from_user.id] += 5

        result = random.randint(1, 100)
        if result > 15:
            new_photo = open('data/photos/sand.png', 'rb')
            new_caption = translate_text(f'Локация: пустыня\nИдти дальше?\nЗдоровье: {get_robot_health(callback.from_user.id)}\nДистанция: {sand_distance_from_base[callback.from_user.id]} метров', user_id)
            await bot.edit_message_media(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                media=InputMediaPhoto(media=new_photo, caption=new_caption),
                reply_markup=get_sand_keyboard(user_id)
            )
        else:
            kb = InlineKeyboardMarkup(row_width=1).add(
                InlineKeyboardButton(text=translate_text("Вступить в бой", user_id), callback_data="gobattle"),
                InlineKeyboardButton(text=translate_text("Отступить на базу", user_id), callback_data="to_base")
            )
            new_photo = open('data/photos/sand.png', 'rb')
            new_caption = translate_text(f'Вы наткнулись на врага! Сражаться или отступить?\nДистанция: {sand_distance_from_base[callback.from_user.id]} метров', user_id)
            await bot.edit_message_media(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                media=InputMediaPhoto(media=new_photo, caption=new_caption),
                reply_markup=kb
            )




@dp.callback_query_handler(text="gobattle")
@dp.throttled(callantiflood, rate=2)
async def sandbattle(callback: types.CallbackQuery):

    uid = callback.from_user.id
    balance = get_game_take_balance(uid)
    if balance < 0.015:
        text = 'Ваш баланс слишком низок, вам нужно пополнить его хотябы на 0.015 ТАКЕ перед тем, как идти в бой.'
        translated_text = translate_text(text, uid)
        await bot.answer_callback_query(
            callback_query_id=callback.id,
            text=translated_text,
            show_alert=True
        )
        return

    if get_robot_health(uid) > 5:
        res = random.randint(1, 100)
        if res <= 45:
            new_photo = open('data/photos/sand_patrol.png', 'rb')
            text = 'Враг: патрульный. Веду сражение...'
            translated_text = translate_text(text, uid)
            new_caption = translated_text
            await bot.edit_message_media(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                media=InputMediaPhoto(media=new_photo, caption=new_caption)
            )
            await asyncio.sleep(5)
            rs = random.randint(1, 100)
            if rs <= 20:  # 50% chance to win
                dmg = random.randint(-15, -5)

                add_game_take_balance(uid, 0.003)

                add_health_to_robot(uid, dmg)
                new_photo = open('data/photos/sand.png', 'rb')
                text = win_txt_pve.format('патрульного', abs(dmg), get_robot_health(uid), 0.003)
                translated_text = translate_text(text, uid)
                new_caption = translated_text
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=new_caption),
                    reply_markup=get_sand_keyboard(uid)
                )
            elif rs <= 80:  # 30% chance to lose
                dmg = random.randint(-25, -15)
                add_health_to_robot(uid, dmg)
                
                kb = InlineKeyboardMarkup(row_width=1).add(
                    InlineKeyboardButton(text=translate_text("На базу", uid), callback_data="to_base"),

            )

                new_photo = open('data/photos/sand.png', 'rb')
                text = f'Поражение! Вы потеряли 0.006 ТАКЕ. Робот получил {abs(dmg)} урона. Текущее здоровье: {get_robot_health(uid)}. Эвакуироваться на базу?'
                translated_text = translate_text(text, uid)
                new_caption = translated_text
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=new_caption),
                    reply_markup=kb
                )
                await decrease_game_take_balance(uid, 0.006)
            else:  # 20% chance for enemy to escape
                dmg = random.randint(-9, -2)
                add_health_to_robot(uid, dmg)
                new_photo = open('data/photos/sand.png', 'rb')
                text = f'Противник убежал! Бой не был окончен. Робот получил {abs(dmg)} урона. Текущее здоровье: {get_robot_health(uid)}. Идти дальше?'
                translated_text = translate_text(text, uid)
                new_caption = translated_text
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=new_caption),
                    reply_markup=get_sand_keyboard(uid)
                )

        elif res <= 80:
            new_photo = open('data/photos/sand_stalker.png', 'rb')
            text = 'Враг: робот-сталкер. Веду сражение...'
            translated_text = translate_text(text, uid)
            new_caption = translated_text
            await bot.edit_message_media(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                media=InputMediaPhoto(media=new_photo, caption=new_caption)
            )
            await asyncio.sleep(5)
            rs = random.randint(1, 100)
            if rs <= 15:
                dmg = random.randint(-15, -5)

                add_game_take_balance(uid, 0.005)

                add_health_to_robot(uid, dmg)
                new_photo = open('data/photos/sand_stalker.png', 'rb')
                text = win_txt_pve.format('робота-сталкера', abs(dmg), get_robot_health(uid), 0.005)
                translated_text = translate_text(text, uid)
                new_caption = translated_text
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=new_caption),
                    reply_markup=get_sand_keyboard(uid)
                )
            elif rs <= 80:  # 30% chance to lose
                dmg = random.randint(-25, -15)
                add_health_to_robot(uid, dmg)
                kb = InlineKeyboardMarkup(row_width=1).add(
                    InlineKeyboardButton(text=translate_text("На базу", uid), callback_data="to_base"),

            )

                new_photo = open('data/photos/sand.png', 'rb')
                text =  f'Поражение! Вы потеряли 0.007 ТАКЕ. Робот получил {abs(dmg)} урона. Текущее здоровье: {get_robot_health(uid)}. Эвакуироваться на базу?'
                translated_text = translate_text(text, uid)
                new_caption = translated_text
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=new_caption),
                    reply_markup=kb
                )
                await decrease_game_take_balance(uid, 0.007)
            else:  # 20% chance for enemy to escape
                dmg = random.randint(-9, -2)
                add_health_to_robot(uid, dmg)
                new_photo = open('data/photos/sand.png', 'rb')
                text = f'Противник убежал! Бой не был окончен. Робот получил {abs(dmg)} урона. Текущее здоровье: {get_robot_health(uid)}. Идти дальше?'
                translated_text = translate_text(text, uid)
                new_caption = translated_text
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=new_caption),
                    reply_markup=get_sand_keyboard(uid)
                )

        else:
            new_photo = open('data/photos/sand_spider.png', 'rb')
            text = 'Враг: робо-паук. Веду сражение...'
            translated_text = translate_text(text, uid)
            new_caption = translated_text
            await bot.edit_message_media(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                media=InputMediaPhoto(media=new_photo, caption=new_caption)
            )
            await asyncio.sleep(5)
            rs = random.randint(1, 100)
            if rs <= 10:  # 50% chance to win
                dmg = random.randint(-15, -5)

                add_game_take_balance(uid, 0.01)
                add_health_to_robot(uid, dmg)
                new_photo = open('data/photos/sand_spider.png', 'rb')
                text = win_txt_pve.format('робота-паука', abs(dmg), get_robot_health(uid), 0.01)
                translated_text = translate_text(text, uid)
                new_caption = translated_text
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=new_caption),
                    reply_markup=get_sand_keyboard(uid)
                )
            elif rs <= 80:  # 30% chance to lose
                dmg = random.randint(-25, -15)
                add_health_to_robot(uid, dmg)
                kb = InlineKeyboardMarkup(row_width=1).add(
                    InlineKeyboardButton(text=translate_text("На базу", uid), callback_data="to_base"),

            )

                new_photo = open('data/photos/sand.png', 'rb')
                text =  f'Поражение! Вы потеряли 0.015 ТАКЕ. Робот получил {abs(dmg)} урона. Текущее здоровье: {get_robot_health(uid)}. Эвакуироваться на базу?'
                translated_text = translate_text(text, uid)
                new_caption = translated_text
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=new_caption),
                    reply_markup=kb
                )
                await decrease_game_take_balance(uid, 0.015)
            else:  # 20% chance for enemy to escape
                dmg = random.randint(-15, -8)
                add_health_to_robot(uid, dmg)
                new_photo = open('data/photos/sand.png', 'rb')
                text = f'Противник убежал! Бой не был окончен. Робот получил {abs(dmg)} урона. Текущее здоровье: {get_robot_health(uid)}. Идти дальше?'
                translated_text = translate_text(text, uid)
                new_caption = translated_text
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=new_caption),
                    reply_markup=get_sand_keyboard(uid)
                )

    else:
        kb = InlineKeyboardMarkup(row_width=1).add(
                InlineKeyboardButton(text=translate_text("На базу", uid), callback_data="to_base"),

            )
        text = 'Состояние робота критическое! Нужно срочно вернуться на базу'
        translated_text = translate_text(text, uid)
        await bot.edit_message_caption(
            uid,
            translated_text,
            reply_markup=kb
        )

user_data = {}

@dp.callback_query_handler(text="island")
@dp.throttled(callantiflood, rate=2)
async def island_location(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    pay_locations_key = InlineKeyboardMarkup(row_width=1)
    pay_locations_key.row(InlineKeyboardButton(text=translate_text("Оплатить вход 💸", user_id), callback_data="pay_island_"))
    pay_locations_key.row(InlineKeyboardButton(text=translate_text("Назад 🔙", user_id), callback_data="to_base"))


    if user_id in factory_distance_from_base and factory_distance_from_base[user_id] > 0:
        text = translate_text("Вы не можете зайти на остров, пока вы находитесь на фабрике.", user_id)
        await bot.answer_callback_query(
            callback_query_id=callback.id,
            text=text,
            show_alert=True
        )
        return

    if user_id in sand_distance_from_base and sand_distance_from_base[user_id] > 0:
        text = translate_text("Вы не можете зайти на остров, пока вы находитесь в пустыне.", user_id)
        await bot.answer_callback_query(
            callback_query_id=callback.id,
            text=text,
            show_alert=True
        )
        return

    if user_id in atlantida_distance_from_base and atlantida_distance_from_base[user_id] > 0:
        text = translate_text("Вы не можете зайти в пустыню, пока вы находитесь в Атлантиде.", user_id)
        await bot.answer_callback_query(
            callback_query_id=callback.id,
            text=text,
            show_alert=True
        )
        return

    photo_path = 'data/photos/island.png'

    remaining_time = check_user_in_island_location(user_id)

    if remaining_time:
        remaining_days = remaining_time.days
        remaining_hours, remaining_minutes = divmod(remaining_time.seconds, 3600)
        remaining_hours %= 24
        remaining_minutes //= 60

        message = await bot.send_photo(
            callback.from_user.id,
            photo=open(photo_path, 'rb'),
            caption=translate_text(f"<b>Локация: Остров</b>\nОсталось времени доступа к острову: {remaining_days} дней {remaining_hours} часов {remaining_minutes} минут. \nЗдоровье: {get_robot_health(callback.from_user.id)}", user_id),
            parse_mode="HTML",
            reply_markup=get_island_keyboard(user_id)
        )
    else:
        message = await bot.send_photo(
            callback.from_user.id,
            photo=open(photo_path, 'rb'),
            caption=translate_text("""<b>Локация: Остров</b>\n
    <i>Здесь можно найти самый драгоценный ресурс игры - Тейки.</i>
    Эти электронные деньги можно извлечь из модулей найденных роботов. Остров буквально переполнен старыми роботами, ваша задача найти их и извлечь эту валюту из них!
    Стоимость входа - <b>0.5 ТАКЕ</b> в сутки
    Удачи 🤩""", user_id),
            parse_mode="HTML",
            reply_markup=pay_locations_key
        )

    user_data[user_id] = {'message_id': message.message_id}

@dp.callback_query_handler(text="pay_island_")
@dp.throttled(callantiflood, rate=2)
async def island_location(callback: types.CallbackQuery):
    uid = callback.from_user.id
    user = callback.from_user
    user_take_balance = get_take_balance(user.id)

    if uid not in user_data:
        return

    message_id = user_data[uid]['message_id']
    await bot.edit_message_caption(
        chat_id=uid,
        message_id=message_id,
        caption=translate_text('На сколько дней желаете открыть доступ? (Введите число от 1 до 30)', user.id)
    )
    user_data[uid]['days'] = None

@dp.message_handler(lambda message: message.from_user.id in user_data and
                                    user_data[message.from_user.id]['days'] is None and
                                    message.text.isdigit() and
                                    1 <= int(message.text) <= 30)
async def process_island_access(message: types.Message):
    days = int(message.text)
    cost = days * 0.5  # Calculate the cost based on days

    user_id = message.from_user.id
    user_data[user_id]['days'] = days
    
    pay_island_key = InlineKeyboardMarkup(row_width=1)
    pay_island_key.row(InlineKeyboardButton(text=translate_text("Оплатить вход 💸", user_id), callback_data="pay_take_island_"))

    user_take_balance = get_take_balance(user_id)
    if user_take_balance < cost:  # Check if user has enough balance
        await message.answer(translate_text('<b>🚫 Недостаточно средств на балансе!</b>', user_id))
        return

    message_id = user_data[user_id]['message_id']
    await bot.edit_message_caption(
        chat_id=message.chat.id,
        message_id=message_id,
        caption=translate_text(f'Вы выбрали доступ на {days} дней за {cost} ТАКЕ. '
                                f'Пожалуйста, подтвердите оплату.', user_id),
        reply_markup=pay_island_key
    )

@dp.message_handler(lambda message: message.from_user.id in user_data and
                                    user_data[message.from_user.id]['days'] is None and
                                    (not message.text.isdigit() or
                                    int(message.text) < 1 or int(message.text) > 30))
async def invalid_input(message: types.Message):
    await message.reply(translate_text("Пожалуйста, введите число от 1 до 30.", message.from_user.id))

@dp.callback_query_handler(text="pay_take_island_")
async def pay_take_island(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    days = user_data[user_id]['days']
    cost = days * 0.5  # Calculate the cost based on days

    decrease_take_balance(user_id, cost)  # Decrease balance based on cost
    record_island_location(user_id, days)

    message_id = user_data[user_id]['message_id']
    await bot.edit_message_caption(
        chat_id=callback.message.chat.id,
        message_id=message_id,
        caption=translate_text(f'Оплата успешно проведена✅! Доступ к острову предоставлен на {days} дней.', user_id)
    )

    await asyncio.sleep(3)

    message_id = user_data[user_id]['message_id']
    await bot.edit_message_caption(
        chat_id=callback.message.chat.id,
        message_id=message_id,
        caption=translate_text('Локация: Остров', user_id),
        reply_markup=get_island_keyboard(user_id)
    )


@dp.callback_query_handler(text="factory")
@dp.throttled(callantiflood, rate=2)
async def factory_location(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    if user_id in sand_distance_from_base and sand_distance_from_base[user_id] > 0:
        text = translate_text("Вы не можете зайти на завод, пока вы находитесь в пустыне.", user_id)
        await bot.answer_callback_query(
            callback_query_id=callback.id,
            text=text,
            show_alert=True
        )
        return

    if user_id in island_distance_from_base and island_distance_from_base[user_id] > 0:
        text = translate_text("Вы не можете зайти на завод, пока вы находитесь на острове.", user_id)
        await bot.answer_callback_query(
            callback_query_id=callback.id,
            text=text,
            show_alert=True
        )
        return

    if user_id in atlantida_distance_from_base and atlantida_distance_from_base[user_id] > 0:
        text = translate_text("Вы не можете зайти в пустыню, пока вы находитесь в Атлантиде.", user_id)
        await bot.answer_callback_query(
            callback_query_id=callback.id,
            text=text,
            show_alert=True
        )
        return

    factory_distance_from_base[user_id] = 0

    photo_path = 'data/photos/factory.png'

    caption = translate_text(f'Локация: Завод\nЗдоровье: {get_robot_health(callback.from_user.id)}', user_id)
    await bot.send_photo(
        callback.from_user.id,
        photo=open(photo_path, 'rb'),
        caption=caption,
        reply_markup=get_factory_keyboard(user_id)
    )


@dp.callback_query_handler(text="fhod")
@dp.throttled(callantiflood, rate=0.5)
async def fhod(callback: types.CallbackQuery):
    uid = callback.from_user.id
    photo_path = 'data/photos/factory.png'
    result = random.randint(1, 100)
    health = get_robot_health(uid)
    max_health = get_robot_max_health(uid)

    if uid not in factory_distance_from_base:
        factory_distance_from_base[uid] = 0

    factory_distance_from_base[uid] += 5

    if health >= max_health:
        new_photo = open('data/photos/factory.png', 'rb')
        new_caption = translate_text(f"🔋 Здоровье вашего робота уже на максимуме. Вернутся на базу?\nРасстояние от базы: {factory_distance_from_base[uid]} м.", uid)
        await bot.edit_message_media(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            media=InputMediaPhoto(media=new_photo, caption=new_caption),
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(text=translate_text("Отступить на базу", uid), callback_data="to_base")
            )
        )
        return
    
        
    if result <= 13:
        add_health_to_robot(uid, 20)
        new_photo = open('data/photos/factory_loot_03.png', 'rb')
        new_caption = translate_text(f'🔋 Вы нашли первый набор, он добавил вашему роботу 4 единиц здоровья.\nЗдоровье: {get_robot_health(callback.from_user.id)}\nРасстояние от базы: {factory_distance_from_base[uid]} м.', uid)
        await bot.edit_message_media(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            media=InputMediaPhoto(media=new_photo, caption=new_caption),
            reply_markup=get_factory_keyboard(uid)
        )
    elif result <= 20:
        add_health_to_robot(uid, 20)
        new_photo = open('data/photos/factory_loot_02.png', 'rb')
        new_caption = translate_text(f'🔋 Вы нашли второй набор, он добавил вашему роботу 10 единиц здоровья.\nЗдоровье: {get_robot_health(callback.from_user.id)}\nРасстояние от базы: {factory_distance_from_base[uid]} м.', uid)
        await bot.edit_message_media(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            media=InputMediaPhoto(media=new_photo, caption=new_caption),
            reply_markup=get_factory_keyboard(uid)
        )
    elif result <= 25:
        add_health_to_robot(uid, 20)
        new_photo = open('data/photos/factory_loot_01.png', 'rb')
        new_caption = translate_text(f'🔋 Вы нашли третий набор, он добавил вашему роботу 20 единиц здоровья.\nЗдоровье: {get_robot_health(callback.from_user.id)}\nРасстояние от базы: {factory_distance_from_base[uid]} м.', uid)
        await bot.edit_message_media(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            media=InputMediaPhoto(media=new_photo, caption=new_caption),
            reply_markup=get_factory_keyboard(uid)
        )
    else:
        new_photo = open('data/photos/factory.png', 'rb')
        new_caption = translate_text(f'Тут ничего нет. Продолжить движение?\nЗдоровье: {get_robot_health(callback.from_user.id)}\nРасстояние от базы: {factory_distance_from_base[uid]} м.', uid)
        await bot.edit_message_media(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            media=InputMediaPhoto(media=new_photo, caption=new_caption),
            reply_markup=get_factory_keyboard(uid)
        )



@dp.callback_query_handler(text="ihod")
@dp.throttled(callantiflood, rate=0.5)
async def hod(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    remaining_time = check_user_in_island_location(user_id)

    if remaining_time:
        remaining_days = remaining_time.days
        remaining_hours, remaining_minutes = divmod(remaining_time.seconds, 3600)
        remaining_hours %= 24
        remaining_minutes //= 60

        if callback.from_user.id not in island_distance_from_base:
            island_distance_from_base[callback.from_user.id] = 0
        island_distance_from_base[callback.from_user.id] += 5

        result = random.randint(0, 100)
        photo_path = 'data/photos/island.png'
        if result <= 4:
            ikb = InlineKeyboardMarkup(row_width=1).add(
                InlineKeyboardButton(text=translate_text("Обыскать", user_id), callback_data="search_robot_island"),
                InlineKeyboardButton(text=translate_text("Отступить на базу", user_id), callback_data="to_base")
            )

            new_photo = open(photo_path, 'rb')
            new_caption = translate_text(f'Вы нашли старого робота, обыскать его?\nЗдоровье: {get_robot_health(callback.from_user.id)}\nДистанция: {island_distance_from_base[callback.from_user.id]} метров', user_id)
            await bot.edit_message_media(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                media=InputMediaPhoto(media=new_photo, caption=new_caption),
                reply_markup=ikb
            )

        elif result <= 19:
            ikb2 = InlineKeyboardMarkup(row_width=1).add(
                InlineKeyboardButton(text=translate_text("Вступить в бой", user_id), callback_data="gobattle_island"),
                InlineKeyboardButton(text=translate_text("Отступить на базу", user_id), callback_data="to_base")
            )
            new_photo = open(photo_path, 'rb')
            new_caption = translate_text(f'Вы наткнулись на врага! Сражаться или отступить?\nЗдоровье: {get_robot_health(callback.from_user.id)}\nДистанция: {island_distance_from_base[callback.from_user.id]} метров', user_id)
            await bot.edit_message_media(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                media=InputMediaPhoto(media=new_photo, caption=new_caption),
                reply_markup=ikb2
            )

        else:

            new_photo = open(photo_path, 'rb')
            new_caption = translate_text(f'Локация: Остров\nИдти дальше?\nЗдоровье: {get_robot_health(callback.from_user.id)}\nДистанция: {island_distance_from_base[callback.from_user.id]} метров', user_id)
            await bot.edit_message_media(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                media=InputMediaPhoto(media=new_photo, caption=new_caption),
                reply_markup=get_island_keyboard(user_id)
            )
    else:
        await bot.send_message(
            user_id,
            translate_text("Ваше время на острове истекло. Для доступа к острову вам необходимо приобрести новый пропуск.", user_id)
        )


@dp.callback_query_handler(text="search_robot_island")
async def search_robot_island(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    new_photo = open('data/photos/island.png', 'rb')
    new_caption = translate_text('Обыскиваем робота...', user_id)
    await bot.edit_message_media(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        media=InputMediaPhoto(media=new_photo, caption=new_caption)
    )

    await asyncio.sleep(5)

    result = random.uniform(0, 100)
    resources_found = 0

    if result <= 10:
        resources_found = random.uniform(0.01, 0.05)
        add_game_take_balance(user_id, resources_found)

        new_photo = open('data/photos/island_loot1.png', 'rb')
        new_caption = translate_text(f'Отлично! Вам очень повезло и вы нашли {resources_found:.2f} ТАКЕ в старом роботе, которые Вы можете потратить на прокачку вашего робота!\nЗдоровье: {get_robot_health(callback.from_user.id)}', user_id)
        await bot.edit_message_media(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            media=InputMediaPhoto(media=new_photo, caption=new_caption),
            reply_markup=get_island_keyboard(user_id)
        )

    elif result <= 13:
        resources_found = random.uniform(0.05, 0.1)
        add_game_take_balance(user_id, resources_found)

        new_photo = open('data/photos/island_loot2.png', 'rb')
        new_caption = translate_text(f'Хорошо! Вам повезло и вы нашли {resources_found:.2f} ТАКЕ в старом роботе, которые Вы можете потратить на прокачку вашего робота!\nЗдоровье: {get_robot_health(callback.from_user.id)}', user_id)
        await bot.edit_message_media(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            media=InputMediaPhoto(media=new_photo, caption=new_caption),
            reply_markup=get_island_keyboard(user_id)
        )
    elif result <=18:
        resources_found = random.uniform(0.1, 0.015)
        add_game_take_balance(user_id, resources_found)
        new_photo = open('data/photos/island_loot3.png', 'rb')
        new_caption = translate_text(f'Неплохо! Вам немного повезло и вы нашли {resources_found:.2f} ТАКЕ в старом роботе, которые Вы можете потратить на прокачку вашего робота!\nЗдоровье: {get_robot_health(callback.from_user.id)}', user_id)
        await bot.edit_message_media(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            media=InputMediaPhoto(media=new_photo, caption=new_caption),
            reply_markup=get_island_keyboard(user_id)
        )
    else:
        new_photo = open('data/photos/island.png', 'rb')
        new_caption = translate_text(f'К сожалению, на этот раз удача не на вашей стороне. Ничего не найдено.\nЗдоровье: {get_robot_health(callback.from_user.id)}', user_id)
        await bot.edit_message_media(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            media=InputMediaPhoto(media=new_photo, caption=new_caption),
            reply_markup=get_island_keyboard(user_id)
        )


@dp.callback_query_handler(text="gobattle_island")
@dp.throttled(callantiflood, rate=2)
async def sandbattle(callback: types.CallbackQuery):
    uid = callback.from_user.id
        
    health = get_robot_health(callback.from_user.id)
    if health <= 5:
        new_photo = open('data/photos/island.png', 'rb')
        island_distance_from_base.clear()
        new_caption = translate_text(f'Ваше здоровье слишком низкое, вам нужно восстановиться на заводе перед тем, как идти в бой.\nЗдоровье: {get_robot_health(callback.from_user.id)}', uid)
        await bot.edit_message_media(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            media=InputMediaPhoto(media=new_photo, caption=new_caption),
            reply_markup=get_sand_zero_keyboard(uid)
        )
        return
    
    else:
        res = random.randint(1, 100)

        if res <= 20:
            new_photo = open('data/photos/island_hardworker.png', 'rb')
            new_caption = 'Враг: Робот-трудяга. Веду сражение...'
            translated_caption = translate_text(new_caption, uid)
            await bot.edit_message_media(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                media=InputMediaPhoto(media=new_photo, caption=translated_caption)
            )
            await asyncio.sleep(5)
            rs = random.randint(1, 100)
            if rs <= 50:
                dmg = random.randint(-15, -5)
                add_game_take_balance(uid, 0.003)
                add_health_to_robot(uid, dmg)

                new_photo = open('data/photos/island.png', 'rb')
                new_caption = win_txt_pve.format('Робота-трудягу.', abs(dmg), get_robot_health(uid), 0.003)
                translated_caption = translate_text(new_caption, uid)
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=translated_caption),
                    reply_markup=get_island_keyboard(uid)
                )
            elif rs <= 80:
                dmg = random.randint(-25, -15)
                add_health_to_robot(uid, dmg)

                translated_text = translate_text('Поражение! Робот получил {} урона. Текущее здоровье: {}. Эвакуироваться на базу?'.format(abs(dmg), get_robot_health(uid)), uid)
                translated_button_text = translate_text("На базу", uid)

                kb2 = InlineKeyboardMarkup(row_width=1).add(
                    InlineKeyboardButton(text=translated_button_text, callback_data="to_base"),
                )
                new_photo = open('data/photos/island.png', 'rb')
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=translated_text),
                    reply_markup=kb2
                )
            else:
                dmg = random.randint(-9, -2)
                add_health_to_robot(uid, dmg)

                translated_text = translate_text('Противник убежал! Бой не был окончен. Робот получил {} урона. Текущее здоровье: {}. Идти дальше?'.format(abs(dmg), get_robot_health(uid)), uid)
                new_photo = open('data/photos/island.png', 'rb')
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=translated_text),
                    reply_markup=get_island_keyboard(uid)
                )
                           
        elif res <= 62:
            new_photo = open('data/photos/island_ninja.png', 'rb')
            new_caption = 'Враг: Робот-ниндзя. Веду сражение...'
            translated_caption = translate_text(new_caption, uid)
            await bot.edit_message_media(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                media=InputMediaPhoto(media=new_photo, caption=translated_caption)
            )
            await asyncio.sleep(5)
            rs = random.randint(1, 100)
            if rs <= 24:  # 40% chance to win
                dmg = random.randint(-19, -8)
                add_health_to_robot(uid, dmg)
                add_game_take_balance(uid, 0.005)
                new_photo = open('data/photos/island.png', 'rb')
                new_caption = win_txt_pve.format('Робота-ниндзя.', abs(dmg), get_robot_health(uid), 0.005)
                translated_caption = translate_text(new_caption, uid)
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=translated_caption),
                    reply_markup=get_island_keyboard(uid)
                )
            elif rs <= 80:  # 40% chance to lose
                dmg = random.randint(-25, -15)
                add_health_to_robot(uid, dmg)
                translated_text = translate_text('Поражение! Робот получил {} урона. Текущее здоровье: {}. Эвакуироваться на базу?'.format(abs(dmg), get_robot_health(uid)), uid)
                translated_button_text = translate_text("На базу", uid)

                kb2 = InlineKeyboardMarkup(row_width=1).add(
                    InlineKeyboardButton(text=translated_button_text, callback_data="to_base"),
                )
                new_photo = open('data/photos/island.png', 'rb')
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=translated_text),
                    reply_markup=kb2
                )
            else:  # 20% chance for enemy to escape
                dmg = random.randint(-15, -5)
                add_health_to_robot(uid, dmg)
                translated_text = translate_text('Противник убежал! Бой не был окончен. Робот получил {} урона. Текущее здоровье: {}. Идти дальше?'.format(abs(dmg), get_robot_health(uid)), uid)
                new_photo = open('data/photos/island.png', 'rb')
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=translated_text),
                    reply_markup=get_island_keyboard(uid)
                )                        
                
        elif res <= 79:
            new_photo = open('data/photos/island_parrot.png', 'rb')
            new_caption = 'Враг: Робот-попугай. Веду сражение...'
            translated_caption = translate_text(new_caption, uid)
            await bot.edit_message_media(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                media=InputMediaPhoto(media=new_photo, caption=translated_caption)
            )

            await asyncio.sleep(5)
            rs = random.randint(1, 100)
            if rs <= 20:
                dmg = random.randint(-19, -8)
                add_health_to_robot(uid, dmg)
                add_game_take_balance(uid, 0.007)
                new_photo = open('data/photos/island.png', 'rb')
                new_caption = win_txt_pve.format('Робота-попугая.', abs(dmg), get_robot_health(uid), 0.007)
                translated_caption = translate_text(new_caption, uid)
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=translated_caption),
                    reply_markup=get_island_keyboard(uid)
                )
            elif rs <= 80:  # 40% chance to lose
                dmg = random.randint(-25, -15)
                add_health_to_robot(uid, dmg)
                translated_text = translate_text('Поражение! Робот получил {} урона. Текущее здоровье: {}. Эвакуироваться на базу?'.format(abs(dmg), get_robot_health(uid)), uid)
                translated_button_text = translate_text("На базу", uid)

                kb2 = InlineKeyboardMarkup(row_width=1).add(
                    InlineKeyboardButton(text=translated_button_text, callback_data="to_base"),
                )
                new_photo = open('data/photos/island.png', 'rb')
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=translated_text),
                    reply_markup=kb2
                )
            else:  # 20% chance for enemy to escape
                dmg = random.randint(-15, -5)
                add_health_to_robot(uid, dmg)
                translated_text = translate_text('Противник убежал! Бой не был окончен. Робот получил {} урона. Текущее здоровье: {}. Идти дальше?'.format(abs(dmg), get_robot_health(uid)), uid)
                new_photo = open('data/photos/island.png', 'rb')
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=translated_text),
                    reply_markup=get_island_keyboard(uid)
                )
                
                
        elif res <= 93:
            new_photo = open('data/photos/island_jonny.png', 'rb')
            new_caption = 'Враг: Робот-Джонни. Веду сражение...'
            translated_caption = translate_text(new_caption, uid)
            await bot.edit_message_media(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                media=InputMediaPhoto(media=new_photo, caption=translated_caption)
            )

            await asyncio.sleep(5)
            rs = random.randint(1, 100)
            if rs <= 15:
                dmg = random.randint(-19, -8)
                add_health_to_robot(uid, dmg)
                add_game_take_balance(uid, 0.01)
                new_photo = open('data/photos/island.png', 'rb')
                new_caption = win_txt_pve.format('Робота-Джонни.', abs(dmg), get_robot_health(uid), 0.01)
                translated_caption = translate_text(new_caption, uid)
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=translated_caption),
                    reply_markup=get_island_keyboard(uid)
                )
            elif rs <= 80:  # 40% chance to lose
                dmg = random.randint(-25, -15)
                add_health_to_robot(uid, dmg)
                translated_text = translate_text('Поражение! Робот получил {} урона. Текущее здоровье: {}. Эвакуироваться на базу?'.format(abs(dmg), get_robot_health(uid)), uid)
                translated_button_text = translate_text("На базу", uid)

                kb2 = InlineKeyboardMarkup(row_width=1).add(
                    InlineKeyboardButton(text=translated_button_text, callback_data="to_base"),
                )
                new_photo = open('data/photos/island.png', 'rb')
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=translated_text),
                    reply_markup=kb2
                )
            else:
                dmg = random.randint(-15, -5)
                add_health_to_robot(uid, dmg)
                translated_text = translate_text('Противник убежал! Бой не был окончен. Робот получил {} урона. Текущее здоровье: {}. Идти дальше?'.format(abs(dmg), get_robot_health(uid)), uid)
                new_photo = open('data/photos/island.png', 'rb')
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=translated_text),
                    reply_markup=get_island_keyboard(uid)
                )
        else:
            new_photo = open('data/photos/island_shmel.png', 'rb')
            new_caption = 'Враг: Робот-Шмель. Веду сражение...'
            translated_caption = translate_text(new_caption, uid)
            await bot.edit_message_media(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                media=InputMediaPhoto(media=new_photo, caption=translated_caption)
            )

            await asyncio.sleep(5)
            rs = random.randint(1, 100)
            if rs <= 12:
                dmg = random.randint(-10, -5)

                add_game_take_balance(uid, 0.015)
                add_health_to_robot(uid, dmg)
                new_photo = open('data/photos/island.png', 'rb')
                new_caption = win_txt_pve.format('Робота-Шмеля.', abs(dmg), get_robot_health(uid), 0.015)
                translated_caption = translate_text(new_caption, uid)
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=translated_caption),
                    reply_markup=get_island_keyboard(uid)
                )
            elif rs <= 80:
                dmg = random.randint(-25, -15)
                add_health_to_robot(uid, dmg)
                translated_text = translate_text('Поражение! Робот получил {} урона. Текущее здоровье: {}. Эвакуироваться на базу?'.format(abs(dmg), get_robot_health(uid)), uid)
                translated_button_text = translate_text("На базу", uid)

                kb2 = InlineKeyboardMarkup(row_width=1).add(
                    InlineKeyboardButton(text=translated_button_text, callback_data="to_base"),
                )
                new_photo = open('data/photos/island.png', 'rb')
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=translated_text),
                    reply_markup=kb2
                )
            else:
                dmg = random.randint(-15, -8)
                add_health_to_robot(uid, dmg)
                translated_text = translate_text('Противник убежал! Бой не был окончен. Робот получил {} урона. Текущее здоровье: {}. Идти дальше?'.format(abs(dmg), get_robot_health(uid)), uid)
                new_photo = open('data/photos/island.png', 'rb')
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=translated_text),
                    reply_markup=get_island_keyboard(uid)
                )






@dp.callback_query_handler(text="atlantida")
@dp.throttled(callantiflood, rate=1)
async def atlantida_location(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    atlantida_started = check_atlantida_started()
    if not atlantida_started:
        translated_text = translate_text("Атлантида пока не запущена.", user_id)
        await bot.answer_callback_query(
            callback_query_id=callback.id,
            text=translated_text,
            show_alert=True
        )
        return

    if user_id in factory_distance_from_base and factory_distance_from_base[user_id] > 0:
        translated_text = translate_text("Вы не можете зайти в Атлантиду, пока вы находитесь на фабрике.", user_id)
        await bot.answer_callback_query(
            callback_query_id=callback.id,
            text=translated_text,
            show_alert=True
        )
        return

    if user_id in sand_distance_from_base and sand_distance_from_base[user_id] > 0:
        translated_text = translate_text("Вы не можете зайти в Атлантиду, пока вы находитесь в пустыне.", user_id)
        await bot.answer_callback_query(
            callback_query_id=callback.id,
            text=translated_text,
            show_alert=True
        )
        return

    if user_id in island_distance_from_base and island_distance_from_base[user_id] > 0:
        translated_text = translate_text("Вы не можете зайти в Атлантиду, пока вы находитесь на острове.", user_id)
        await bot.answer_callback_query(
            callback_query_id=callback.id,
            text=translated_text,
            show_alert=True
        )
        return

    photo_path = 'data/photos/atlantida.png'

    user_in_atlantida = check_user_in_atlantida_location(user_id)

    if user_in_atlantida:
        caption = f'<b>Локация: Атлантида</b>\n' \
                  f'Изучайте локацию в поисках таинственного босса Атлантиды.'
        translated_caption = translate_text(caption, user_id)
        message = await bot.send_photo(
            callback.from_user.id,
            photo=open(photo_path, 'rb'),
            caption=translated_caption,
            parse_mode="HTML",
            reply_markup=get_atlantida_keyboard(user_id)
        )
    else:
        caption = f'''<b>Локация: Атлантида</b>\n
    <i>Подключайтесь к массовой битве против огромного робота в новой локации "Атлантида".</i>
    
    Стоимость входа - <b>{get_atlantida_entrance_fee()} ТАКЕ</b>.
    Приз за боса - <b>{get_atlantida_prize()} ТАКЕ</b>.
    Удачи 🤩'''
        translated_caption = translate_text(caption, user_id)
        message = await bot.send_photo(
            callback.from_user.id,
            photo=open(photo_path, 'rb'),
            caption=translated_caption,
            parse_mode="HTML",
            reply_markup=get_pay_atlantida_keyboard(user_id)
        )

    user_data[user_id] = {'message_id': message.message_id}


@dp.callback_query_handler(text="pay_atlantida_")
@dp.throttled(callantiflood, rate=1)
async def atlantida_location(callback: types.CallbackQuery):
    uid = callback.from_user.id
    user = callback.from_user
    user_take_balance = get_take_balance(user.id)
    cost = get_atlantida_entrance_fee()

    user_take_balance = get_take_balance(uid)
    if user_take_balance < cost:  # Check if user has enough balance
        translated_text = translate_text('🚫 Недостаточно средств на балансе!', uid)
        await bot.answer_callback_query(
            callback_query_id=callback.id,
            text=translated_text,
            show_alert=True
        )
        return

    if uid not in user_data:
        return

    message_id = user_data[uid]['message_id']
    caption = f'Вы хотите оплатить доступ к Антлантиды для охоты на босса за {get_atlantida_entrance_fee()} ТАКЕ. ' \
              f'Пожалуйста, подтвердите оплату.'
    translated_caption = translate_text(caption, uid)
    await bot.edit_message_caption(
        chat_id=uid,
        message_id=message_id,
        caption=translated_caption,
        reply_markup=get_pay_atlantida_keyboard_confirm(uid)
    )
    user_data[uid]['days'] = None

@dp.callback_query_handler(text="pay_take_atlantida_")
async def pay_take_atlantida(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    cost = get_atlantida_entrance_fee()

    decrease_take_balance(user_id, cost)  # Decrease balance based on cost
    record_atlantida_location(user_id)

    message_id = user_data[user_id]['message_id']
    caption = 'Оплата успешно проведена✅! Доступ к Атлантиде предоставлен.'
    translated_caption = translate_text(caption, user_id)
    await bot.edit_message_caption(
        chat_id=callback.message.chat.id,
        message_id=message_id,
        caption=translated_caption
    )

    await asyncio.sleep(3)

    message_id = user_data[user_id]['message_id']
    caption = 'Локация: Атлантида'
    translated_caption = translate_text(caption, user_id)
    await bot.edit_message_caption(
        chat_id=callback.message.chat.id,
        message_id=message_id,
        caption=translated_caption,
        reply_markup=get_atlantida_keyboard(user_id)
    )


@dp.callback_query_handler(text="ahod")
@dp.throttled(callantiflood, rate=2)
async def hod(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    uid = callback.from_user.id
    current_power = get_boss_power()

    if not check_atlantida_started():
        translated_text = translate_text("Босс атлантиды был повержен и доступ к атлантиде закрылся.", user_id)
        await bot.answer_callback_query(
            callback_query_id=callback.id,
            text=translated_text,
            show_alert=True
        )
        return

    if user_id in atlantida_distance_from_base:
        atlantida_distance_from_base[user_id] += 5
    else:
        atlantida_distance_from_base[user_id] = 5

    user_in_atlantida = check_user_in_atlantida_location(user_id)

    if not user_in_atlantida:
        caption = f"Для доступа к Атлантиде необходимо приобрести пропуск.\n" \
                  f"Стоимость пропуска: {get_atlantida_entrance_fee()} ТАКЕ."
        translated_caption = translate_text(caption, user_id)
        await bot.send_message(
            user_id,
            translated_caption
        )
        return

    photo_path = 'data/photos/atlantida.png'
    photo_path2 = 'data/photos/atlantida_bos.png'
    result = random.randint(0, 100)

    if result <= 15:
        akb2 = InlineKeyboardMarkup(row_width=1).add(
            InlineKeyboardButton(text=translate_text("Вступить в бой", user_id), callback_data="gobattle_atlantida"),
            InlineKeyboardButton(text=translate_text("Отступить на базу", user_id), callback_data="to_base")
        )
        new_photo = open(photo_path2, 'rb')
       
        caption = f'Вы наткнулись на босса Атлантиды! Сражаться или отступить?\nЗдоровье: {get_robot_health(callback.from_user.id)}.\nЗдоровье босса: {current_power}.\nДистанция: {atlantida_distance_from_base[callback.from_user.id]} метров. '
        translated_caption = translate_text(caption, user_id)
        await bot.edit_message_media(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            media=InputMediaPhoto(media=new_photo, caption=translated_caption),
            reply_markup=akb2
        )
    else:
        new_photo = open(photo_path, 'rb')
        
        caption = f'Локация: Атлантида\nИдти дальше?\nЗдоровье: {get_robot_health(callback.from_user.id)}.\nЗдоровье босса: {current_power}.\nДистанция: {atlantida_distance_from_base[callback.from_user.id]} метров'
        translated_caption = translate_text(caption, user_id)
        await bot.edit_message_media(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            media=InputMediaPhoto(media=new_photo, caption=translated_caption),
            reply_markup=get_atlantida_keyboard(user_id)
        )



@dp.callback_query_handler(text="gobattle_atlantida")
@dp.throttled(callantiflood, rate=2)
async def atlantidabattle(callback: types.CallbackQuery):
    uid = callback.from_user.id
    current_power = get_boss_power()
    if get_robot_health(uid) > 10:
        res = random.randint(1, 100)

        if res <= 50:
            new_photo = open('data/photos/atlantida_bos.png', 'rb')
            new_caption = 'Враг: Робот-босс Атлантиды. Веду сражение...'
            translated_caption = translate_text(new_caption, uid)
            await bot.edit_message_media(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                media=InputMediaPhoto(media=new_photo, caption=translated_caption)
            )
            await asyncio.sleep(5)

            rs = random.randint(1, 100)

            if rs <= 70:
                dmg_to_boss = random.randint(1, 5)
                dmg_to_user = random.randint(5, 20)
                add_health_to_robot(uid, -dmg_to_user)
                
                # current_power = get_boss_power()
                new_power = current_power - dmg_to_boss
                update_boss_power(new_power)

                new_photo = open('data/photos/atlantida.png', 'rb')
                
                caption = f'Вы нанесли {abs(dmg_to_boss)} урона Роботу-боссу Атлантиды! \nНо босс Атлантиды также нанес {abs(dmg_to_user)} урона вам и убежал. \nТекущее здоровье: {get_robot_health(uid)}.\nЗдоровье босса: {new_power}. \nИдти дальше?'
                translated_caption = translate_text(caption, uid)
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=translated_caption),
                    reply_markup=get_atlantida_keyboard(uid)
                )
                

                akb2 = InlineKeyboardMarkup(row_width=1).add(
                    InlineKeyboardButton(text=translate_text("На базу", uid), callback_data="to_base"),
                )

                if new_power <= 0:
                    prize = get_atlantida_prize()
                    set_atlantida_started_to_zero()
                    fighter_ids = get_atlantida_fighters()
                    for fighter_id in fighter_ids:
                        if fighter_id != uid:
                            translated_text = translate_text(f"Игрок {callback.from_user.first_name} победил Робота-босса Атлантиды! Спасибо за участвие🤩", fighter_id)
                            await bot.send_message(
                                fighter_id,
                                translated_text
                            )
                    delete_all_atlantida_locations()
                    await asyncio.sleep(1)
                    new_photo = open('data/photos/atlantida_bos.png', 'rb')
                    caption = f'Вы нанесли решающий удар Роботу-боссу Атлантиды и победили его! Поздравляем, \nВам начислено {prize} TAKE за победу над боссом!'
                    translated_caption = translate_text(caption, uid)
                    await bot.edit_message_media(
                        chat_id=callback.message.chat.id,
                        message_id=callback.message.message_id,
                        media=InputMediaPhoto(media=new_photo, caption=translated_caption),
                        reply_markup=akb2
                    )
                    add_take_balance(uid, prize)
                    

            else:
                dmg = random.randint(-5, -1)
                add_health_to_robot(uid, dmg)
                new_photo = open('data/photos/atlantida.png', 'rb')
                caption = f'Робот-босс Атлантиды убежал! Ваш робот получил {abs(dmg)} урона. \nТекущее здоровье: {get_robot_health(uid)}.\nЗдоровье босса: {current_power}. \nИдти дальше?'
                translated_caption = translate_text(caption, uid)
                await bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=InputMediaPhoto(media=new_photo, caption=translated_caption),
                    reply_markup=get_atlantida_keyboard(uid)
                )
        else:
            await asyncio.sleep(2)
            new_photo = open('data/photos/atlantida.png', 'rb')
            caption = f'Робот-босс Атлантиды не вступил в бой с вами и убежал! \nТекущее здоровье: {get_robot_health(uid)}.\nЗдоровье босса: {current_power}.\nИдти дальше?'
            translated_caption = translate_text(caption, uid)
            await bot.edit_message_media(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                media=InputMediaPhoto(media=new_photo, caption=translated_caption),
                reply_markup=get_atlantida_keyboard(uid)
            )
    else:
        akb2 = InlineKeyboardMarkup(row_width=1).add(
               InlineKeyboardButton(text=translate_text("На базу", uid), callback_data="to_base"),
                )
        translated_text = translate_text("Состояние робота критическое! Нужно срочно вернуться на базу", uid)
        await bot.send_message(
            uid,
            translated_text,
            reply_markup=akb2
        )


@dp.callback_query_handler(text="to_base")
async def to_base(callback: types.CallbackQuery):
    await callback.message.delete()
    uid = callback.from_user.id
    island_distance_from_base.clear()
    factory_distance_from_base.clear()
    sand_distance_from_base.clear()  # очищаем словарь
    atlantida_distance_from_base.clear()





@dp.callback_query_handler(text_startswith='bet_')
@dp.throttled(callantiflood, rate=1)
async def create_game_1(call: types.CallbackQuery):
    user = call.from_user
    robots_count = len(mdb.get_user_robots(user.id))

    if not robots_count:
        message_text = '🚫 У вас нет роботов, купите их в разделе "🛒 Магазин".'
        translated_text = translate_text(message_text, user.id)
        await call.message.edit_text(translated_text)
        return

    bet_sum = call.data.split('_')[1]

    if zero_bet_game_exist() and bet_sum == '0':
        message_text = (
            f'🟢 Уже есть игра с такой ставкой <b>{bet_sum}</b> TON. '
            'Вы можете вернуться назад и присоединиться к этому бою или же создать свой.'
        )
        translated_text = translate_text(message_text, user.id)
        await call.message.edit_text(translated_text, reply_markup=await bet_confirm_zero_key(bet_sum))
    else:
        message_text = f'🟢 Создать бой со ставкой <b>{bet_sum}</b> TON?'
        translated_text = translate_text(message_text, user.id)
        await call.message.edit_text(translated_text, reply_markup=await bet_confirm_key(bet_sum))

@dp.callback_query_handler(text_startswith='create_')
@dp.throttled(callantiflood, rate=2)
async def create_game_2(call: types.CallbackQuery):
    bet_sum = call.data.split('_')[1]
    user = call.from_user
    user_balance = get_balance(user.id)
    user_game = mdb.check_user_game_create(user.id)
    user_playable = mdb.check_user_playable(user.id)
    user_health = mdb.check_robot_health(user.id)

    if not user_health:
        player1_robot = mdb.get_user_active_robot(user.id)
        message_text = (
            f'🚫 Нельзя начать бой! У вашего робота должно быть полное здоровье чтобы участвовать в бою!\n'
            f'✅До полного восстановления <code>30-45 минут</code>.\n'
            f'❤️Скорость восстановления {round(player1_robot[5] / 5)} единицы в минуту.\n\n'
            f'<b>👇 Вы можете восстановить здоровье моментально нажав на кнопку ниже.</b>'
        )
        translated_text = translate_text(message_text, user.id)
        await call.message.edit_text(translated_text, reply_markup=heal_key)
        return

    if user_game:
        message_text = '🚫 У вас уже есть активная созданная игра, вы не можете создать более 1 боев!'
        translated_text = translate_text(message_text, user.id)
        await call.answer(translated_text, True)
        return

    if user_playable:
        message_text = '🚫 Вы похоже уже участвуете в другом бою!'
        translated_text = translate_text(message_text, user.id)
        await call.answer(translated_text, True)
        return

    if user_balance < float(bet_sum):
        message_text = '<b>🚫 Недостаточно средств на балансе!</b>'
        translated_text = translate_text(message_text, user.id)
        await call.message.edit_text(translated_text)
        return

    decrease_balance(user.id, bet_sum)
    game_id = await create_game(bet_sum, user.id)

    message_text = f'⚔️ Бой успешно создан!\n\n#️⃣ Номер боя: #{game_id}'
    translated_text = translate_text(message_text, user.id)
    await call.message.edit_text(translated_text)

    await bot.send_message(LOGS,
                           f'<b>⚔️ Создан новый бой!</b>\n\n'
                           f'<b>#️⃣ Номер боя:</b> #{game_id}\n'
                           f'<b>💎 Ставка на бой:</b> {bet_sum} TON\n'
                           f'<b>👤 Создатель:</b> <a href="tg://user?id={user.id}">{user.first_name}</a>'
                           )

@dp.callback_query_handler(text_startswith='join_')
@dp.throttled(callantiflood, rate=2)
async def join(call: types.CallbackQuery):
    user = call.from_user
    game_id = call.data.split('_')[1]
    game = mdb.get_game(game_id)
    player_id = game[3]

    try:
        player = await bot.get_chat(player_id)
        player = player.first_name
        player = f'<a href="tg://user?id={player_id}">{player}</a>'
    except:
        player = f'<a href="tg://user?id={player_id}">Пользователь</a>'

    message_text = (
        f'<b>#️⃣ Бой номер:</b> #{game[0]}\n'
        f'<b>💎 Ставка:</b> {game[1]} TON\n'
        f'📆 Дата создание: {game[6]}\n'
        f'<b>👤 Создатель:</b> {player}\n\n'
        f'<i>Уверены что хотите начать бой?</i>'
    )
    translated_text = translate_text(message_text, user.id)
    await call.message.edit_text(translated_text, reply_markup=await join_game_key(game[0]))



@dp.callback_query_handler(text_startswith='start_')
@dp.throttled(callantiflood, rate=1)
async def send_challenge_to_user(call: types.CallbackQuery):
    game_id = call.data.split('_')[1]
    user = call.from_user
    user_balance = get_balance(user.id)
    user_health = mdb.check_robot_health(user.id)
    
    print(game_id)
    game = mdb.get_game(game_id)
    game_creator = game[3]

    if not user_health:
        player1_robot = mdb.get_user_active_robot(user.id)
        await call.message.edit_text(
            f'🚫 Нельзя начать бой! У вашего робота должно быть полное здоровье чтобы участвовать в бою!\n'
            f'✅До полного восстановления <code>30-45 минут</code>.\n'
            f'❤️Скорость восстановления {round(player1_robot[5] / 5)} единицы в минуту.\n\n'
            f'<b>👇 Вы можете восстановить здоровье моментально нажав на кнопку ниже.</b>',
            reply_markup=heal_key
        )
        return

    if user.id == game_creator:
        await call.message.edit_text(f'<b>🚫 Нельзя начать бой с самим собой!</b>')
        return

    if game[2] != 'expectation':
        await call.message.edit_text(f'<b>🚫 Бой с номером #{game[0]} уже начать или завершен!</b>')
        return

    user_playable = mdb.check_user_playable(user.id)

    if user_playable:
        await call.answer(
            '🚫 Вы похоже уже участвуете в другом бою или сами создали активный бой, проверьте в разделе "🟠 Мои активные бои"!',
            True
        )
        return

    if user_balance < game[1]:
        await call.message.edit_text('<b>🚫 Недостаточно средств на балансе для ставки!</b>')
        return

    await bot.send_message(game_creator,
                           f'<b>⚔️ Бой номер #{game[0]}</b>\n\n'
                           f'💎 Ставка: {game[1]} TON\n'
                           f'<a href="tg://user?id={user.id}">{user.first_name}</a> хочет вступить с вами бой.\n\n'
                           f'<i>Принят вызов?</i>',
                           reply_markup=await send_challenge(game[0], user.id)
                           )
    await call.message.edit_text(f'<b>⚔️ Бой номер #{game[0]}</b>\n\n'
                                 f'<i>✉️ Ваш вызов отправлен, бой начнется как только пользователь приметь вызов!</i>')


@dp.callback_query_handler(text_startswith='accept_')
@dp.throttled(callantiflood, rate=3)
async def accept_challenge(call: types.CallbackQuery):
    user_id = call.from_user.id
    game_id = call.data.split('_')[1]
    player_2_id = call.data.split('_')[2]
    player_2_balance = get_balance(player_2_id)
    player_2_status = mdb.check_user_playable(player_2_id)
    player_1_health = mdb.check_robot_health(call.from_user.id)
    player_2_health = mdb.check_robot_health(player_2_id)
    game = mdb.get_game(game_id)

    if not player_1_health:
        player1_robot = mdb.get_user_active_robot(call.from_user.id)
        await call.message.edit_text(
            f'🚫 Нельзя начать бой! У вашего робота должно быть полное здоровье чтобы участвовать в бою!\n'
            f'✅До полного восстановления <code>30-45 минут</code>.\n'
            f'❤️Скорость восстановления {round(player1_robot[5] / 5)} единицы в минуту.\n\n'
            f'<b>👇 Вы можете восстановить здоровье моментально нажав на кнопку ниже.</b>',
            reply_markup=heal_key
        )
        return

    if not player_2_health:
        await call.answer(
            '🚫 Нельзя начать бой, у роботв соперника должно быть полное здоровья что бы он смог участвовать в бою!')
        return

    if player_2_status:
        await call.answer('🚫 Соперник уже в другом бою или создал(а) собственный бой!')
        return

    if game[2] != 'expectation':
        await call.message.edit_text(f'<b>🚫 Бой 🚫номером #{game[0]} уже начат или завершен!</b>')
        return

    if player_2_balance < game[1]:
        await call.answer('🚫 Недостаточно средств на балансе для ставки у соперника!')
        return

    decrease_balance(player_2_id, game[1])
    await start_game(game_id, player_2_id)
    player_1_name = call.from_user.first_name
    player_1_name = f'<a href="tg://user?id={call.from_user.id}">{player_1_name}</a>'
    try:
        player_2_name = await bot.get_chat(player_2_id)
        player_2_name = player_2_name.first_name
        player_2_name = f'<a href="tg://user?id={player_2_id}">{player_2_name}</a>'
    except:
        player_2_name = f'<a href="tg://user?id={player_2_id}">Пользователь</a>'

    await asyncio.sleep(3)
    await call.message.answer(
        f'⚔️ Бой с номером <b>#{game[0]}</b> начат!\n\n'
        f'👤 Ваш соперник: {player_2_name}\n'
        f'💎 Ставка: <b>{game[1]} TON</b>\n\n'
        f'<i>👇 Вы атакуете первым у вас есть 5 секунд что бы действовать:</i>',
        reply_markup=await only_attack_key(game[0], player_2_id)
    )

    await bot.send_message(
        player_2_id,
        f'<b>⚔️ Бой номер #{game[0]}</b> начат!\n\n'
        f'👤 Ваш соперник: {player_1_name}\n'
        f'💎 Ставка: <b>{game[1]} TON</b>\n\n'
        f'ℹ️ С вашего баланса списано сумма ставки <b>{game[1]} TON</b>, соперник начинает бой первым!\n'
        f'<i>Если соперник бездействовал более 5 секунд нажмите на кнопку ниже 👇</i>',
        reply_markup=await not_respond_key(game_id, user_id)
    )

    await bot.send_message(
        LOGS,
        f'<b>⚔️ Бой номер #{game[0]}</b> начат!\n\n'
        f'👤 Игрок 1: {player_1_name}\n'
        f'👤 Игрок 2: {player_2_name}\n\n'
        f'<i>🤝 Удачи обоим игрокам!</i>'
    )



@dp.callback_query_handler(text_startswith='mygame_')
@dp.throttled(callantiflood, rate=1)
async def show_user_active_games(call: types.CallbackQuery):
    user_id = call.from_user.id
    game_id = call.data.split('_')[1]
    game = mdb.get_game(game_id)

    game_link = f'https://t.me/TonTakeRoBot?start=joingame_{game_id}'

    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton(translate_text('❌ Удалить бой', user_id), callback_data=f'delgame_{game[0]}'))
    markup.add(InlineKeyboardButton(translate_text('🔗 Поделиться боем', user_id), switch_inline_query=f'{game_link}'))

    text = f'<b>#️⃣ Бой номер:</b> #{game[0]}\n' \
            f'<b>💎 Ставка:</b> {game[1]} TON\n' \
            f'📆 Дата создание: {game[6]}\n\n' \
            f'<i>⏳ Ожидание второго игрока!</i>\n'
    translated_text = translate_text(text, user_id)

    await call.message.edit_text(translated_text,
                                 reply_markup=markup,
                                 parse_mode='HTML')




@dp.callback_query_handler(text_startswith='delgame_')
@dp.throttled(callantiflood, rate=3)
async def delete_game(call: types.CallbackQuery):
    game_id = call.data.split('_')[1]
    game = mdb.get_game(game_id)
    user = call.from_user

    if game[2] != 'expectation':
        text = '🚫 <b>Бой с номером #{game[0]} уже закончен или начат или уже удален!</b>'
        await call.message.edit_text(translate_text(text, user.id))
        return

    if user.id != game[3]:
        text = '🚫 Этот бой создали не вы!'
        await call.message.edit_text(translate_text(text, user.id))
        return

    mdb.delete_game(game[0])
    add_balance(user.id, game[1])

    text = f'✅ Бой номер <b>#{game[0]}</b> успешно удален, <b>{game[1]}</b> TON возвращены на ваш баланс!'
    await call.message.edit_text(translate_text(text, user.id))



user_message_ids = {}

@dp.callback_query_handler(text_startswith='attack_')
@dp.throttled(callantiflood, rate=3)
async def attack_in_game(call: types.CallbackQuery):
    user_id = call.from_user.id
    game_id = call.data.split('_')[1]
    user2_id = call.data.split('_')[2]
    game = mdb.get_game(game_id)

    print(user_message_ids)

    if game[2] != 'started':
        await call.message.edit_text(
            f'🚫 <b>Бой с номером #{game[0]} уже закончен!</b>'
        )
        return

    if game[8] != user_id:
        await call.answer('🚫 Сейчас очередь соперника!', True)
        return

    if random.randint(1, 3) == 1:
        double_strike_markup = await double_strike_key(game_id, user_id)
    else:
        double_strike_markup = None

    defender_health, damage, defender_armor = await attack_game(user_id, user2_id, game_id)

    # Save user's message ID
    user_message_id = call.message.message_id
    user_message_ids[user_id] = {'message_id': user_message_id, 'chat_id': call.message.chat.id}

    if damage > defender_health:
        await finish_game(game_id, user_id, user2_id, user_message_ids)
        return

    message_text = f'<b>⚔️ Бой номер #{game_id}</b>\n\n'
    message_text_opponent = f'<b>⚔️ Бой номер #{game_id}</b>\n\n'

    if damage == 1:
        message_text += (
            f'Вы атаковали соперника, и броня соперника полностью отразила вашу атаку.\n'
            f'Однако, вы все равно нанесли <b>{damage}</b> урона.\n'
            f'💚 Теперь у соперника <b>{defender_health - damage}</b> HP.\n\n'
            f'<i>Если соперник бездействовал более 5 секунд нажмите на кнопку ниже 👇</i>'
        )
        message_text_opponent += (
            f'Соперник атаковал вас, и ваша броня полностью отразила его атаку.\n'
            f'Однако, вы все равно получили <b>{damage}</b> урона.\n'
            f'♥️ Теперь у вас <b>{defender_health - damage}</b> HP.\n\n'
            f'<i>👇 Вы можете атаковать что бы нанести урон, у вас есть 5 секунд что бы действовать!</i>'
        )
    else:
        message_text += (
            f'Вы атаковали соперника, и броня соперника отразила {defender_armor} урона от вашей атаки.\n'
            f'Однако, вы все равно нанесли <b>{damage}</b> урона.\n'
            f'💚 Теперь у соперника <b>{defender_health - damage}</b> HP.\n\n'
            f'<i>Если соперник бездействовал более 5 секунд нажмите на кнопку ниже 👇</i>'
        )
        message_text_opponent += (
            f'Соперник атаковал вас, и ваша броня отразила {defender_armor} урона от его атаки.\n'
            f'Однако вы все равно получили <b>{damage}</b> урона.\n'
            f'♥️ Теперь у вас <b>{defender_health - damage}</b> HP.\n\n'
            f'<i>👇 Вы можете атаковать что бы нанести урон, у вас есть 5 секунд что бы действовати!</i>'
        )

    await bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=user_message_ids[user_id]['message_id'],
        text=message_text,
        reply_markup=await not_respond_key(game_id, user_id) 
    )

    # Update opponent's message ID
    if user2_id in user_message_ids:
        opponent_message_id = user_message_ids[user2_id]['message_id']
    else:
        # Send a new message to the opponent and save its ID
        opponent_message = await bot.send_message(user2_id, message_text_opponent)
        opponent_message_id = opponent_message.message_id
        user_message_ids[user2_id] = {'message_id': opponent_message_id, 'chat_id': opponent_message.chat.id}

    await bot.edit_message_text(
        chat_id=user2_id,
        message_id=opponent_message_id,
        text=message_text_opponent,
        reply_markup=await attack_key(game_id, user_id) if double_strike_markup is None else double_strike_markup
    )


    if random.randint(0, 10) == 10:
        user_robot = mdb.get_user_active_robot(user_id)
        health = user_robot[3]
        max_health = user_robot[8]
        heal = user_robot[5]

        if health + heal > max_health:
            heal = max_health - health

        mdb.update_robot(user_id, user_robot[1], 'health', heal)

        # Send the message as a pop-up alert
        await bot.answer_callback_query(
            callback_query_id=call.id,
            text=f'🔋 Вам повезло и вы восстановили {heal} здоровья во время атаки!',
            show_alert=True,
        )


@dp.callback_query_handler(text_startswith='doublestrike_')
@dp.throttled(callantiflood, rate=3)
async def double_strike_in_game(call: types.CallbackQuery):
    user_id = call.from_user.id
    game_id = call.data.split('_')[1]
    user2_id = call.data.split('_')[2]
    game = mdb.get_game(game_id)

    if game[2] != 'started':
        await call.message.edit_text(
            f'🚫 <b>Бой с номером #{game[0]} уже закончен!</b>'
        )
        return

    if game[8] != user_id:
        await call.answer('🚫 Сейчас очередь соперника!', True)
        return

    defender_health, damage, defender_armor = await attack_game(user_id, user2_id, game_id)

    # Double the damage for the "Double Strike!"
    damage *= 2

    # Save user's message ID
    user_message_id = call.message.message_id
    user_message_ids[user_id] = {'message_id': user_message_id, 'chat_id': call.message.chat.id}

    if damage > defender_health:
        await finish_game(game_id, user_id, user2_id, user_message_ids)
        return

    message_text = f'<b>⚔️ Бой номер #{game_id}</b>\n\n'
    message_text_opponent = f'<b>⚔️ Бой номер #{game_id}</b>\n\n'

    if damage == 1:
        message_text += (
            f'Вы атаковали соперника, и броня соперника полностью отразила вашу атаку.\n'
            f'Однако, вы все равно нанесли <b>{damage}</b> урона.\n'
            f'💚 Теперь у соперника <b>{defender_health - damage}</b> HP.\n\n'
            f'<i>Вы нанесли двойной удар!</i>\n\n'
            f'<i>Если соперник бездействовал более 5 секунд нажмите на кнопку ниже 👇</i>'
        )
        message_text_opponent += (
            f'Соперник атаковал вас, и ваша броня полностью отразила его атаку.\n'
            f'Однако, вы все равно получили <b>{damage}</b> урона.\n'
            f'♥️ Теперь у вас <b>{defender_health - damage}</b> HP.\n\n'
            f'<i>Соперник нанес двойной удар!</i>\n\n'
            f'<i>👇 Вы можете атаковать что бы нанести урон, у вас есть 5 секунд что бы действовать!</i>'
        )
    else:
        message_text += (
            f'Вы атаковали соперника, и броня соперника отразила {defender_armor} урона от вашей атаки.\n'
            f'Однако, вы все равно нанесли <b>{damage}</b> урона.\n'
            f'💚 Теперь у соперника <b>{defender_health - damage}</b> HP.\n\n'
            f'<i>Вы нанесли двойной удар!</i>\n\n'
            f'<i>Если соперник бездействовал более 5 секунд нажмите на кнопку ниже 👇</i>'
        )
        message_text_opponent += (
            f'Соперник атаковал вас, и ваша броня отразила {defender_armor} урона от его атаки.\n'
            f'Однако вы все равно получили <b>{damage}</b> урона.\n'
            f'♥️ Теперь у вас <b>{defender_health - damage}</b> HP.\n\n'
            f'<i>Соперник нанес двойной удар!</i>\n\n'
            f'<i>👇 Вы можете атаковать что бы нанести урон, у вас есть 5 секунд что бы действовати!</i>'
        )

    await bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=user_message_ids[user_id]['message_id'],
        text=message_text,
        reply_markup=await not_respond_key(game_id, user_id) 
    )

    # Update opponent's message ID
    if user2_id in user_message_ids:
        opponent_message_id = user_message_ids[user2_id]['message_id']
    else:
        # Send a new message to the opponent and save its ID
        opponent_message = await bot.send_message(user2_id, message_text_opponent)
        opponent_message_id = opponent_message.message_id
        user_message_ids[user2_id] = {'message_id': opponent_message_id, 'chat_id': opponent_message.chat.id}

    await bot.edit_message_text(
        chat_id=user2_id,
        message_id=opponent_message_id,
        text=message_text_opponent,
        reply_markup=await attack_key(game_id, user_id)
    )

    if random.randint(0, 10) == 10:
        user_robot = mdb.get_user_active_robot(user_id)
        health = user_robot[3]
        max_health = user_robot[8]
        heal = user_robot[5]

        if health + heal > max_health:
            heal = max_health - health

        mdb.update_robot(user_id, user_robot[1], 'health', heal)

        # Send the message as a pop-up alert
        await bot.answer_callback_query(
            callback_query_id=call.id,
            text=f'🔋 Вам повезло и вы восстановили {heal} здоровья во время атаки!',
            show_alert=True,
        )

    
@dp.callback_query_handler(text_startswith='not-respond')
@dp.throttled(callantiflood, rate=3)
async def user_not_response(call: types.CallbackQuery):
    game_id = call.data.split('_')[1]
    game = mdb.get_game(game_id)
    user = call.from_user
    user_id = user.id
    player1 = game[3]
    player2 = game[4]

    if game[2] != 'started':
        await call.message.edit_text(
            f'🚫 <b>Бой с номером #{game[0]} уже закончен!</b>'
        )
        return

    if game[8] == user.id:
        await call.answer('🚫 Сейчас ваша очередь атаковать!', True)
        return

    time_now = time()
    if time_now - game[7] < 5:
        await call.answer('🚫 Еще не прошло 5 секунд после вашей последней атаки!', True)
        return

    if player1 == user.id:
        mdb.update_turn(player1, game_id)
        message_text = (
            f'⚔️ Бой номер <b>#{game[0]}</b>!\n\n'
            f'Противник не ответил, вы можете атаковать!'
        )
        if user.id in user_message_ids:
            try:
                await bot.edit_message_text(
                    chat_id=user.id,
                    message_id=user_message_ids[user.id]['message_id'],
                    text=message_text,
                    reply_markup=await only_attack_key(game[0], player2)
                )
            except MessageToEditNotFound:
                await bot.send_message(
                    chat_id=user.id,
                    text=message_text,
                    reply_markup=await only_attack_key(game[0], player2)
                )
        else:
            await bot.send_message(
                chat_id=user.id,
                text=message_text,
                reply_markup=await only_attack_key(game[0], player2)
            )
        message_text_opponent = (
            f'⚔️ Бой номер <b>#{game[0]}</b>!\n\n'
            f'<i>Прошло более 5 секунд и соперник забрал шанс атаковать, у соперника так же есть 5 секунд что бы совершит атаку!</i>'
        )
        if player2 in user_message_ids:
            try:
                await bot.edit_message_text(
                    chat_id=player2,
                    message_id=user_message_ids[player2]['message_id'],
                    text=message_text_opponent,
                    reply_markup=await not_respond_key(game_id, user_id)
                )
            except MessageToEditNotFound:
                await bot.send_message(
                    chat_id=player2,
                    text=message_text_opponent,
                    reply_markup=await not_respond_key(game_id, user_id)
                )
        else:
            opponent_message = await bot.send_message(
                player2,
                message_text_opponent,
                reply_markup=await not_respond_key(game_id, user_id)
            )
            user_message_ids[player2] = {'message_id': opponent_message.message_id, 'chat_id': opponent_message.chat.id}
    else:
        mdb.update_turn(player2, game_id)
        message_text = (
            f'⚔️ Бой номер <b>#{game[0]}</b>!\n\n'
            f'<i>Противник не ответил, вы можете атаковать!</i>'
        )
        if user.id in user_message_ids:
            try:
                await bot.edit_message_text(
                    chat_id=user.id,
                    message_id=user_message_ids[user.id]['message_id'],
                    text=message_text,
                    reply_markup=await only_attack_key(game[0], player1)
                )
            except MessageToEditNotFound:
                await bot.send_message(
                    chat_id=user.id,
                    text=message_text,
                    reply_markup=await only_attack_key(game[0], player1)
                )
        else:
            await bot.send_message(
                chat_id=user.id,
                text=message_text,
                reply_markup=await only_attack_key(game[0], player1)
            )
        message_text_opponent = (
            f'⚔️ Бой номер <b>#{game[0]}</b>!\n\n'
            f'<i>Прошло более 5 секунд и соперник забрал шанс атаковать, у соперника так же есть 5 секунд что бы совершит атаку!</i>'
        )
        if player1 in user_message_ids:
            try:
                await bot.edit_message_text(
                    chat_id=player1,
                    message_id=user_message_ids[player1]['message_id'],
                    text=message_text_opponent,
                    reply_markup=await not_respond_key(game_id, user_id)
                )
            except MessageToEditNotFound:
                await bot.send_message(
                    chat_id=player1,
                    text=message_text_opponent,
                    reply_markup=await not_respond_key(game_id, user_id)
                )
        else:
            opponent_message = await bot.send_message(
                player1,
                message_text_opponent,
                reply_markup=await not_respond_key(game_id, user_id)
            )
            user_message_ids[player1] = {'message_id': opponent_message.message_id, 'chat_id': opponent_message.chat.id}

 
 

pending_surrenders = {}

@dp.callback_query_handler(text_startswith='escape_')
@dp.throttled(callantiflood, rate=3)
async def escape_from_game(call: types.CallbackQuery):
    game_id = call.data.split('_')[1]
    game = mdb.get_game(game_id)

    if game and game[2] == 'finished':
        text = "Невозможно сдаться в уже завершенной игре."
        translated_text = translate_text(text, call.from_user.id)
        await bot.answer_callback_query(
            callback_query_id=call.id,
            text=translated_text,
            show_alert=True
        )
        return

    user = call.from_user
    user_id = user.id

    player1 = game[3]
    player2 = game[4]

    if user_id == player1:
        user2_id = player2
    elif user_id == player2:
        user2_id = player1
    else:
        user2_id = None

    pending_surrenders[user_id] = game_id

    text = "Вы уверены, что хотите сдаться в этом бою? Это будет засчитано как поражение. " \
           "Нажмите кнопку ниже, чтобы подтвердить свое решение."
    translated_text = translate_text(text, call.from_user.id)
    await bot.send_message(
        user_id,
        translated_text,
        reply_markup=confirmation_keyboard()
    )

@dp.callback_query_handler(text="confirm_surrender")
async def confirm_surrender(call: types.CallbackQuery):
    await call.message.delete()
    user_id = call.from_user.id
    game_id = pending_surrenders.get(user_id)
    if game_id:
        game = mdb.get_game(game_id)
        user = call.from_user
        user_id = user.id

        player1 = game[3]
        player2 = game[4]

        if user_id == player1:
            user2_id = player2
        elif user_id == player2:
            user2_id = player1
        else:
            user2_id = None

        loser = user_id
        winner = user2_id
        game = mdb.get_game(game_id)
        bet = game[1]
        mdb.finish_game(game_id, winner)
        prize = round(bet * 2 * 0.90, 4)
        add_balance(winner, prize)

        try:
            photo = 'https://telegra.ph/file/3d20a37c33b5857b0eab6.jpg'
            winner_text = f'<b>⚔️ Бой номер #{game_id}</b>\n\n' \
                           f'Ваш соперник сдался и вы выиграли бой и получили 90% от ставок в размере {prize} TON!'
            translated_winner_text = translate_text(winner_text, winner)
            await bot.send_photo(
                winner,
                photo,
                translated_winner_text
            )

            defeat_photo = 'https://telegra.ph/file/f79735301f803d63995e4.jpg'
            loser_text = f'<b>⚔️ Бой номер #{game_id}</b>\n\n' \
                          f'Вы не выдержали натиска врага и решили сдаться.\n' \
                          f'Вам засчитали поражение.'
            translated_loser_text = translate_text(loser_text, loser)
            await bot.send_photo(
                loser,
                defeat_photo,
                translated_loser_text
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
                    tour_text = f'⚡️ Вы так же получили <b>1 очков</b> турнира за победу в бою!'
                    translated_tour_text = translate_text(tour_text, winner)
                    await bot.send_message(
                        winner,
                        translated_tour_text                    
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
                take_text = f'<a href="https://t.me/TonTakeRoBot">TonTakeRoBot</a>\n' \
                            f'<b>⚔️ Бой номер #{game_id}</b> завершен!\n\n' \
                            f'{player_1_name} против {player_2_name}\n\n' \
                            f'<b>👑 Победитель</b> {player_1_name}\n' \
                            f'🎁 Получено <b>{prize}</b> TON'
                await bot.send_message(
                    TAKE_CHAT,
                    take_text
                )
             
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

        except Exception as e:
            print(e)


      
@dp.callback_query_handler(text="cancel_surrender")
async def cancel_surrender(call: types.CallbackQuery):
    await call.message.delete()
    user_id = call.from_user.id
    if user_id in pending_surrenders:
        del pending_surrenders[user_id]
        await call.message.delete()
        


    
    
@dp.callback_query_handler(text='tour_history')
@dp.throttled(callantiflood, rate=2)
async def tour_history(call: types.CallbackQuery):
    history = get_all_tours()
    text = ''
    for x in history:
        if not x[1]:
            count_tour_users = get_count_tour_users(x[0])
            fund = round(count_tour_users * 0.09, 2)
            winner = get_tour_top_user(x[0])
            
            # Перевірте, чи не є winner пустим списком
            if winner and len(winner) > 0:
                winner_text = f'<a href="tg://user?id={winner[0]}">Пользователь</a> (<code>{winner[0]}</code>)'
            else:
                winner_text = 'Победитель'

            text += f'\n{x[0]} - {x[3]}:00 - {count_tour_users} - {fund} TON - {winner_text}'

    await call.message.edit_text(
        f'<b>📁 История турнира\n\n№ турнира - дата окончание - количество участников - фонд турнира - победитель</b>\n{text}'
    )


@dp.callback_query_handler(text_startswith='accept-withdraw')
@dp.throttled(callantiflood, rate=5)
async def withdraw(call: types.CallbackQuery):
    user = call.from_user
    amount = call.data.split('_')[1]
    
    if float(amount) > get_balance(call.from_user.id):
        message = "Недостаточно средств..."
        translated_message = translate_text(message, user.id)
        await call.answer(
            translated_message,
            True
        )
        return
    await call.message.delete()
    # Проверяем значение графы auto в таблице autowithdraw
    auto_withdraw = get_auto_withdraw()
    if auto_withdraw == 1:
        
        success = await transfer(user, amount, 'TONCOIN')
        if success:
            decrease_balance(call.from_user.id, amount)
            await bot.send_message(LOGS, f'<b>📥 Новый вывод TОN!\n\n'
                                 f'👤Юзернейм: @{user.username}\n'
                                 f'🆔Айди: <code>{user.id}</code>\n'
                                 f'💳Сумма: {amount} TON</b>')
            await bot.send_message(user, f'✅ Вам выплачено <b>{amount}</b> TON.')
        else:
            await call.message.answer('🚫 Ошибка при выводе, проверьте баланс api!')
    else:
        
        refs = get_refferals(call.from_user.id)
        await bot.send_message(LOGS,
                               f'''<b>📌 Новая заявка на вывод!</b>

От: @{user.username}, <code>{user.id}</code>

Сумма: {amount} TON
Количество рефов: {refs}''',
                               reply_markup=await admin_withdraw_key(user.id, amount))
        await call.message.answer(
            f"""Вы успешно создали запрос на вывод на сумму <b>{amount} TON</b>!""",
            reply_markup=create_start_keyboard(user.id)
        )

  ####      
@dp.callback_query_handler(text_startswith='accept-takewithdraw')
@dp.throttled(callantiflood, rate=5)
async def withdraw_take(call: types.CallbackQuery):
    user = call.from_user
    amount = call.data.split('_')[1]
    if float(amount) > get_take_balance(call.from_user.id):
        message = "Недостаточно средств..."
        translated_message = translate_text(message, user.id)
        await call.answer(
            translated_message,
            True
        )
        return
    await call.message.delete()
    # Проверяем значение графы auto в таблице autowithdraw
    auto_withdraw = get_auto_withdraw()
    if auto_withdraw == 1:
        success = await transfer(user, amount, 'TAKE')
        print("tried")
        if success:
            decrease_take_balance(user.id, amount)
            await bot.send_message(LOGS, f'<b>📥 Новый вывод TAKE!\n\n'
                                 f'👤Юзернейм: @{user.username}\n'
                                 f'🆔Айди: <code>{user.id}</code>\n'
                                 f'💳Сумма: {amount} TАКЕ</b>')
            await bot.send_message(user.id, f'✅ Вам выплачено <b>{amount}</b> TAKE.')
        else:
            await call.message.answer('🚫 Ошибка при выводе, проверьте баланс api!')
    else:
        
        refs = get_refferals(call.from_user.id)
        await bot.send_message(LOGS,
                               f'''<b>📌 Новая заявка на вывод!</b>

От: @{user.username}, <code>{user.id}</code>

Сумма: {amount} TAKE
Количество рефов: {refs}''',
                               reply_markup=await admin_withdraw_take_key(user.id, amount))
        await call.message.answer(
            f"""Вы успешно создали запрос на вывод на сумму <b>{amount} TAKE</b>!""",
            reply_markup=create_start_keyboard(user.id)
        )

        

        
        
        ####     
# @dp.callback_query_handler(text_startswith='accept-withdraw-take')
# @dp.throttled(callantiflood, rate=5)
# async def withdraw(call: types.CallbackQuery):
#     user = call.from_user
#     amount = call.data.split('_')[1]
#     if float(amount) > get_take_balance(call.from_user.id):
#         message = "Недостаточно средств..."
#         translated_message = translate_text(message, user.id)
#         await call.answer(
#             translated_message,
#             True
#         )
#         return
#     await call.message.delete()
#     decrease_take_balance(call.from_user.id, amount)
#     success = await transfer(user, amount, 'TAKECOIN')
#     if success:
#         await bot.send_message(LOGS, f'✅ <code>{user}</code> вывел <b>{amount}</b> TAKE!')
#         await bot.send_message(user, f'✅ Вам выплачено <b>{amount}</b> TAKE.')
#     else:
#         await call.message.answer('🚫 Ошибка при выводе, проверьте баланс api!')

@dp.callback_query_handler(text_startswith='next_')
@dp.throttled(callantiflood, rate=1)
async def next_robot(call: types.CallbackQuery):
    await call.message.delete()
    user = call.from_user
    robot_index = int(call.data.split('_')[1])
    robots = mdb.get_robots()
    count_robots = len(robots) - 1

    if robot_index > count_robots:
        robot = robots[0]
    elif robot_index < 0:
        robot = robots[count_robots]
    else:
        robot = robots[robot_index]

    robot_id = robot[0]
    robot_name = robot[1]
    robot_health = robot[2]
    robot_damage = robot[3]
    robot_heal = robot[4]
    robot_armor = robot[5]
    robot_price = robot[6]

    with open(f'data/photos/robot_{robot_id}.png', 'rb') as photo:
        translated_text = translate_text(f'''
🤖 Робот: <b>{robot_name}</b>
🆔 ID: <b>{robot_id}</b>

🔋 Здоровье: <b>{robot_health}</b>
⚔️ Урон: <b>{robot_damage}</b>
⚙️ Восстановление: <b>{robot_heal}</b>
🛡 Броня: <b>{robot_armor}</b>

💎 <b>Стоимость {robot_price} ТАКЕ</b>''', call.from_user.id)

        await call.message.answer_photo(photo, translated_text,
                                        reply_markup=await market_key(robot_id,
                                                                      robots.index(robot) + 1,
                                                                      robots.index(robot) - 1,
                                                                      count_robots + 1,
                                                                      robots.index(robot),
                                                                      user.id
                                                                      )
                                        )

@dp.callback_query_handler(text_startswith='buy_')
async def buy_robot(call: types.CallbackQuery):
    robot_id = int(call.data.split('_')[1])
    robot = mdb.get_one_robot(robot_id)
    robot_name = robot[1]
    robot_health = robot[2]
    robot_damage = robot[3]
    robot_heal = robot[4]
    robot_armor = robot[5]
    robot_price = robot[6]

    user = call.from_user
    user_balance = get_take_balance(user.id)

    if mdb.check_robot_exist(user.id, robot_id):
        translated_text = translate_text('🚫 У вас уже имеется этот робот!\n\nℹ️ Вы можете его выбрать во вкладке "🤖 Мои роботы"', user.id)
        await call.answer(translated_text, True)
        return

    if user_balance < robot_price:
        translated_text = translate_text('🚫 Недостаточно средств на вашем балансе!', user.id)
        await call.answer(translated_text, True)
        return

    decrease_take_balance(user.id, robot_price)
    mdb.add_robot(user.id, robot_id, robot_name, robot_health, robot_damage, robot_heal, robot_armor)
    mdb.update_robot_status(user.id, robot_id)
    translated_text = translate_text(f'✅ Робот <b>"{robot_name}"</b> успешно приобритен!', user.id)
    await call.message.edit_caption(translated_text)



@dp.callback_query_handler(text_startswith='bazarnext_')
@dp.throttled(callantiflood, rate=1)
async def next_bazar_robot(call: types.CallbackQuery):
    await call.message.delete()
    user_id = user = call.from_user.id
    robot_index = int(call.data.split('_')[1])
    robots = mdb.get_bazar_robots()
    count_robots = len(robots) - 1

    if robot_index > count_robots:
        robot = robots[0]
    elif robot_index < 0:
        robot = robots[count_robots]
    else:
        robot = robots[robot_index]

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
        translated_text = translate_text(f'''
🤖 Робот: <b>{robot_name}</b>
👤 Продавец: <b>{robot_seller}</b>
🆔 ID: <b>{robot_id}</b>

🔋 Макс здоровье: <b>{robot_health}</b>
⚔️ Урон: <b>{robot_damage}</b>
⚙️ Восстановление: <b>{robot_heal}</b>
🎚  Уровень робота: <b>{robot_lvl}</b> 
🛡 Броня: <b>{robot_armor}</b>

💎 <b>Стоимость {robot_price} ТАКЕ</b>''', user_id)

        await call.message.answer_photo(photo, translated_text,
                                        reply_markup=await bazar_key(robot_id,
                                                                      robots.index(robot) + 1,
                                                                      robots.index(robot) - 1,
                                                                      count_robots + 1,
                                                                      robots.index(robot),
                                                                      robot_seller,
                                                                      user_id
                                                                      )
                                        )

@dp.callback_query_handler(text_startswith='bazarbuy_')
async def buy_robot(call: types.CallbackQuery):
    robot_id = int(call.data.split('_')[1])
    robot_seller = int(call.data.split('_')[2])
    robot = mdb.get_bazar_robot(robot_id, robot_seller)
    robot_name = robot[3]
    robot_price = robot[10]

    user = call.from_user
    user_id = user.id
    user_balance = get_take_balance(user_id)

    if robot_seller == user_id:
        translated_text = translate_text('🚫 Вы не можете купить робота сам у себя', user_id)
        await call.answer(translated_text, True)
        return

    if mdb.check_robot_exist(user.id, robot_id):
        translated_text = translate_text('🚫 У вас уже имеется этот робот!\n\nℹ️ Вы можете его выбрать во вкладке "🤖 Мои роботы"', user_id)
        await call.answer(translated_text, True)
        return

    if user_balance < robot_price:
        translated_text = translate_text('🚫 Недостаточно средств на вашем балансе!', user_id)
        await call.answer(translated_text, True)
        return

    uid = robot_seller

    mdb.set_bought_status(user_id, robot_seller, robot_id)
    decrease_take_balance(user.id, robot_price)
    add_take_balance_bazar(uid, robot_price)

    mdb.transport_robot_from_seller_to_buyer(robot_seller, robot_id, user_id)
    translated_text = translate_text(f'✅ Робот <b>"{robot_name}"</b> успешно приобритен!', user_id)
    await call.message.edit_caption(translated_text)

    # Отправка сообщения пользователю с идентификатором uid
    translated_text = translate_text(f'✅ Робот <b>"{robot_name}"</b> успешно продан!\n\n'
                                       f'ℹ️ {robot_price} ТАКЕ были успешно перечислены на ваш баланс.', uid)
    await bot.send_message(
        uid,
        translated_text
    )

    
    
@dp.callback_query_handler(text_startswith='bazarsell')
async def bazar_robot(call: types.CallbackQuery):
    user = call.from_user
    robots = mdb.get_user_robots(user.id)

    if len(robots) == 0:
        translated_text = translate_text('🙁 У вас нет роботов, купите их в разделе <b>"🛒 Магазин"</b> или <b>"🏪 Рынок"</b>.', user.id)
        await call.message.answer(translated_text)
        return

    robot = robots[0]
    robot_id = robot[1]
    robot_name = robot[2]
    robot_health = robot[3]
    robot_damage = robot[4]
    robot_heal = robot[5]
    robot_armor = robot[6]
    robot_max_health = robot[8]
    robot_lvl = robot[9]

    with open(f'data/photos/robot_{robot_id}.png', 'rb') as photo:
        translated_text = translate_text(f'''
🤖 Робот: <b>{robot_name}</b>
🆔 ID: <b>{robot_id}</b>

🔋 Макс здоровье: <b>{robot_max_health}</b>
⚡️ Здоровье: <b>{robot_health}</b>
⚔️ Урон: <b>{robot_damage}</b>
⚙️ Восстановление: <b>{robot_heal}</b>
🎚  Уровень робота: <b>{robot_lvl}</b> 
🛡 Броня: <b>{robot_armor}</b>''', user.id)

        await call.message.answer_photo(photo, translated_text, reply_markup=await sell_my_robots_key(0, robot_id, len(robots)))

@dp.callback_query_handler(text_startswith='mybazarrobot_')
@dp.throttled(callantiflood, rate=1)
async def my_robot(call: types.CallbackQuery):
    await call.message.delete()
    user = call.from_user
    robot_index = int(call.data.split('_')[1])
    robots = mdb.get_user_robots(user.id)

    if robot_index > len(robots) - 1:
        robot = robots[0]
    elif robot_index < 0:
        robot = robots[len(robots) - 1]
    else:
        robot = robots[robot_index]
    robot_id = robot[1]
    robot_name = robot[2]
    robot_health = robot[3]
    robot_damage = robot[4]
    robot_heal = robot[5]
    robot_armor = robot[6]
    status = robot[7]
    robot_max_health = robot[8]
    robot_lvl = robot[9]

    for rb in robots:
        if rb[1] == robot_id:
            robot_index = robots.index(rb)

    with open(f'data/photos/robot_{robot_id}.png', 'rb') as photo:
        translated_text = translate_text(f'''
🤖 Робот: <b>{robot_name}</b>
🆔 ID: <b>{robot_id}</b>

🔋 Макс здоровье: <b>{robot_max_health}</b>
🔋 Здоровье: <b>{robot_health}</b>
⚔️ Урон: <b>{robot_damage}</b>
⚙️ Восстановление: <b>{robot_heal}</b>
🎚  Уровень робота: <b>{robot_lvl}</b> 
🛡 Броня: <b>{robot_armor}</b>''', user.id)

        await call.message.answer_photo(photo, translated_text, reply_markup=await sell_my_robots_key(robot_index, robot_id, len(robots)))

        

robot_prices = {}
waiting_for_price = {}

@dp.callback_query_handler(text_startswith='sellrobot_')
@dp.throttled(callantiflood, rate=1)
async def sell_robot(call: types.CallbackQuery):
    user = call.from_user
    robot_id = call.data.split('_')[1]
    player_status = mdb.check_user_playable(user.id)
    robots = mdb.get_user_robots(user.id)
    status = mdb.check_robot_status(robot_id, user.id)

    if mdb.check_bazar_robot_exist(robot_id, user.id):
        translated_text = translate_text('🚫 Нельзя продать одного и того же робота!', user.id)
        await call.answer(translated_text, True)
        return

    if status == 'selected':
        translated_text = translate_text('🚫 Нельзя продать активного робота. Выберите другого!', user.id)
        await call.answer(translated_text, True)
        return

    if len(robots) == 1:
        translated_text = translate_text('🙁 Вы не можете продать единственного робота.', user.id)
        await call.message.answer(translated_text)
        return

    if player_status:
        translated_text = translate_text('🚫 Нельзя продать робота во время боя!', user.id)
        await call.answer(translated_text, True)
        return

    waiting_for_price[user.id] = {'robot_id': robot_id, 'call': call}
    translated_text = translate_text(f'Введите цену робота с ID: <b>{robot_id}</b> в формате <code>x.xx</code> TAKE:', user.id)
    await call.message.answer(translated_text)



@dp.message_handler(IsSubscribed(), content_types=['text'])
@dp.throttled(callantiflood, rate=3)
async def enter_robot_price(message: types.Message):
    user_id = message.from_user.id

    if user_id in waiting_for_price:
        data = waiting_for_price[user_id]
        robot_id = data['robot_id']
        call = data['call']
        
        if mdb.check_bazar_robot_exist(robot_id, user_id):
            translated_text = translate_text('🚫 Этот робот уже был добавлен на базар!', user_id)
            await message.answer(translated_text)
            return

        if message.text.isdigit() or (message.text.replace('.', '', 1).isdigit() and message.text.count('.') == 1):
            price = float(message.text)
            if price > 0:
                robot_prices[user_id] = {'robot_id': robot_id, 'price': price}

                translated_text = translate_text(f'✅ Цена робота с ID: <b>{robot_id}</b> была установлена в размере <b>{price}</b> TAKE!', user_id)
                await message.answer(translated_text)
                mdb.sell_robot_bazar(user_id, robot_id, price)
                robots = mdb.get_user_robots(user_id)

                del robot_prices[user_id]
                del waiting_for_price[user_id]
            else:
                translated_text = translate_text('🚫 Введите положительное число!', user_id)
                await message.answer(translated_text)
        else:
            translated_text = translate_text('🚫 Введите допустимое значение цены!', user_id)
            await message.answer(translated_text)

@dp.callback_query_handler(text_startswith='mybazaritems_')
@dp.throttled(callantiflood, rate=1)
async def my_bazar_items(call: types.CallbackQuery):
    user = call.from_user
    user_id = user.id
    robots = mdb.get_user_bazar_robots(user_id)

    if not robots:
        translated_text = translate_text('🙁 У вас пока нет роботов на рынке.', user_id)
        await call.message.answer(translated_text)
        return

    for i, robot in enumerate(robots, start=1):
        robot_id, name, health, damage, heal, armor, price = robot
        text = f'{i}. {name} (ID: {robot_id}) - {price} TAKE\n'
        text += f'🔋 Здоровье: {health}\n'
        text += f'⚔️ Урон: {damage}\n'
        text += f'⚙️ Восстановление: {heal}\n'
        text += f'🛡 Броня: {armor}\n'

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton("🗑 Удалить с рынка", callback_data=f"deleterobotfrommarket_{robot_id}")
                ]
            ]
        )

        translated_text = translate_text(text, user_id)
        await call.message.answer(translated_text, reply_markup=keyboard)

@dp.callback_query_handler(text_startswith='deleterobotfrommarket_')
@dp.throttled(callantiflood, rate=1)
async def delete_robot_from_market(call: types.CallbackQuery):
    user = call.from_user
    user_id = user.id
    robot_id = int(call.data.split('_')[1])

    mdb.delete_robot_from_bazar(user_id, robot_id)

    await call.message.delete()
    translated_text = translate_text('Робот успешно удален с рынка!', user_id)
    await bot.send_message(user.id, translated_text)

    
@dp.callback_query_handler(text_startswith='myrobot_')
@dp.throttled(callantiflood, rate=1)
async def my_robot(call: types.CallbackQuery):
    await call.message.delete()
    user = call.from_user
    robot_index = int(call.data.split('_')[1])
    robots = mdb.get_user_robots(user.id)

    if robot_index > len(robots) - 1:
        robot = robots[0]
    elif robot_index < 0:
        robot = robots[len(robots) - 1]
    else:
        robot = robots[robot_index]
    robot_id = robot[1]
    robot_name = robot[2]
    robot_health = robot[3]
    robot_damage = robot[4]
    robot_heal = robot[5]
    robot_armor = robot[6]
    status = robot[7]
    robot_max_health = robot[8]
    robot_lvl = robot[9]

    for rb in robots:
        if rb[1] == robot_id:
            robot_index = robots.index(rb)

    with open(f'data/photos/robot_{robot_id}.png', 'rb') as photo:
        message_text = (
            f'🤖 Робот: <b>{robot_name}</b>\n'
            f'🆔 ID: <b>{robot_id}</b>\n\n'
            f'🔋 Макс здоровье: <b>{robot_max_health}</b>\n'
            f'🔋 Здоровье: <b>{robot_health}</b>\n'
            f'⚔️ Урон: <b>{robot_damage}</b>\n'
            f'⚙️ Восстановление: <b>{robot_heal}</b>\n'
            f'🎚  Уровень робота: <b>{robot_lvl}</b>  \n'
            f'🛡 Броня: <b>{robot_armor}</b>'
        )
        translated_text = translate_text(message_text, user.id)

        await call.message.answer_photo(
            photo,
            translated_text,
            reply_markup=await my_robots_key(robot_index, robot_id, len(robots), status, user.id)
        )



@dp.callback_query_handler(text_startswith='select_')
@dp.throttled(callantiflood, rate=1)
async def select_robot(call: types.CallbackQuery):
    user = call.from_user
    robot_id = call.data.split('_')[1]
    player_status = mdb.check_user_playable(user.id)

    if mdb.check_bazar_robot_exist(robot_id, user.id):
        message_text = '🚫 Нельзя выбрать робота который выставлен на рынку!'
        translated_text = translate_text(message_text, user.id)
        await call.answer(translated_text, True)
        return

    if player_status:
        message_text = '🚫 Нельзя изменить робота во время боя!'
        translated_text = translate_text(message_text, user.id)
        await call.answer(translated_text, True)
        return

    mdb.update_robot_status(user.id, robot_id)
    await call.message.delete()

    message_text = f'✅ Робот с ID: <b>{robot_id}</b> выбран как активный робот!'
    translated_text = translate_text(message_text, user.id)

    await call.message.answer(translated_text)

@dp.callback_query_handler(text='heal_location')
@dp.throttled(callantiflood, rate=1)
async def heal_robot(call: types.CallbackQuery):
    user = call.from_user
    await call.message.delete()
    robot = mdb.get_user_active_robot(user.id)
    robot_health = robot[3]
    robot_max_health = robot[8]
    player_status = mdb.check_user_playable(user.id)

    if player_status:
        message_text = '🚫 Нельзя восстановить робота во время боя!'
        translated_text = translate_text(message_text, user.id)
        await call.answer(translated_text, True)
        return

    if robot_health == robot_max_health:
        message_text = '🚫 У вашего робота полное здоровье!'
        translated_text = translate_text(message_text, user.id)
        await call.answer(translated_text)
        return

    message_text = (
        f'🤖 Робот: <b>{robot[2]}</b>\n\n'
        f'🟢 Максимальная здоровье: <b>{robot_max_health}</b>\n'
        f'🔴 Здоровье сейчас: <b>{robot_health}</b>\n'
        f'💰 Стоимость восстановления: <b>0.1 TAKE</b>\n\n'
        f'👇 После подтверждение действии вы получите <b>{robot_max_health - robot_health}</b> единиц здоровье восстановив полное здоровье робота!'
    )
    translated_text = translate_text(message_text, user.id)

    await call.message.answer(
        translated_text,
        reply_markup=confirm_heal_key
    )

@dp.callback_query_handler(text='heal')
@dp.throttled(callantiflood, rate=1)
async def heal_robot(call: types.CallbackQuery):
    user = call.from_user
    robot = mdb.get_user_active_robot(user.id)
    robot_health = robot[3]
    robot_max_health = robot[8]
    player_status = mdb.check_user_playable(user.id)

    if player_status:
        message_text = '🚫 Нельзя восстановить робота во время боя!'
        translated_text = translate_text(message_text, user.id)
        await call.answer(translated_text, True)
        return

    if robot_health == robot_max_health:
        message_text = '🚫 У вашего робота полное здоровье!'
        translated_text = translate_text(message_text, user.id)
        await call.answer(translated_text)
        return

    message_text = (
        f'🤖 Робот: <b>{robot[2]}</b>\n\n'
        f'🟢 Максимальная здоровье: <b>{robot_max_health}</b>\n'
        f'🔴 Здоровье сейчас: <b>{robot_health}</b>\n'
        f'💰 Стоимость восстановления: <b>0.1 TAKE</b>\n\n'
        f'👇 После подтверждение действии вы получите <b>{robot_max_health - robot_health}</b> единиц здоровье восстановив полное здоровье робота!'
    )
    translated_text = translate_text(message_text, user.id)

    await call.message.edit_text(
        translated_text,
        reply_markup=confirm_heal_key
    )

@dp.callback_query_handler(text='confirm-heal')
@dp.throttled(callantiflood, rate=3)
async def heal_robot_2(call: types.CallbackQuery):
    user = call.from_user
    user_take_balance = get_take_balance(user.id)
    robot = mdb.get_user_active_robot(user.id)
    robot_health = robot[3]
    robot_max_health = robot[8]
    price = 0.1
    player_status = mdb.check_user_playable(user.id)

    if player_status:
        message_text = '🚫 Нельзя восстановить робота во время боя!'
        translated_text = translate_text(message_text, user.id)
        await call.answer(translated_text, True)
        return

    if robot_health == robot_max_health:
        message_text = '🚫 У вашего робота полное здоровье!'
        translated_text = translate_text(message_text, user.id)
        await call.answer(translated_text, True)
        return

    if user_take_balance < price:
        message_text = '🚫 Недостаточно средств на балансе!'
        translated_text = translate_text(message_text, user.id)
        await call.answer(translated_text, True)
        return

    decrease_take_balance(user.id, price)
    mdb.heal_full_robot(user.id, robot[1])

    message_text = (
        f'<b>✅ Ваш робот полностью восстановлен!</b>\n\n'
        f'ℹ️ С вашего баланса списано {price} TAKE.'
    )
    translated_text = translate_text(message_text, user.id)

    await call.message.edit_text(
        translated_text
    )

upgrade_counts = {}

@dp.callback_query_handler(text_startswith='info-')
@dp.throttled(callantiflood, rate=1)
async def upgrade_info(call: types.CallbackQuery):
    info = call.data.split('-')[1]

    markup = InlineKeyboardMarkup()
    button_text = 'Оплатить ТАКЕ'
    translated_button_text = translate_text(button_text, call.from_user.id)
    markup.add(InlineKeyboardButton(text=translated_button_text, callback_data=f'improve-{info}'))

    message_text = info_text(info)
    translated_text = translate_text(message_text, call.from_user.id)

    await call.message.edit_caption(
        translated_text,
        reply_markup=markup
    )



upgrade_counts = defaultdict(lambda: defaultdict(int))

@dp.callback_query_handler(text_startswith='improve-')
@dp.throttled(callantiflood, rate=3)
async def improve_robot(call: types.CallbackQuery):
    user = call.from_user
    user_id = user.id
    user_balance = get_take_balance(user.id)
    robot = mdb.get_user_active_robot(user.id)
    improve_type = call.data.split('-')[1]

    robot_id = robot[1]

    data = {
        'max_health': {
            'name': 'Макс здоровье',
            'amount': 5,
            'base_price': 0.5
        },

        'damage': {
            'name': 'Урон',
            'amount': 2,
            'base_price': 0.2
        },

        'heal': {
            'name': 'Ремонт',
            'amount': 2,
            'base_price': 0.2
        },

        'armor': {
            'name': 'Броня',
            'amount': 1,
            'base_price': 0.3
        }
    }

    # Retrieve the number of upgrades for this type from the dictionary
    upgrade_count = upgrade_counts[user_id][improve_type]

    # Calculate the price considering the number of upgrades
    base_price = data[improve_type]['base_price']
    multiplier = 2 ** (upgrade_count // 5)  # Double the price after every 5 upgrades
    price = base_price * multiplier

    # Check NFT status and apply discount if needed
    nft_status = get_user_nft_status(user_id)
    if nft_status == 1:
        price *= 0.9  # Apply 10% discount
        discount_message = "\n<i>🏷️ Вы имеете 10% скидку на все улучшения благодаря вашему НФТ!</i>"
    else:
        discount_message = ""

    # Round the price to 3 decimal places
    price = round(price, 3)

    if user_balance < price:
        message_text = '🚫 Недостаточно средств на балансе!'
        translated_text = translate_text(message_text, user.id)
        await call.answer(translated_text, True)
        return

    # Deduct the balance and update the robot
    deduction_amount = round(price, 3)
    decrease_take_balance(user.id, deduction_amount)
    mdb.update_robot(user.id, robot[1], improve_type, data[improve_type]['amount'])
    
    # Increment the upgrade count in the dictionary
    upgrade_counts[user_id][improve_type] += 1

    message_text = f'🚀 {data[improve_type]["name"]} вашего робота <b>{robot[2]}</b> улучшен на <b>{data[improve_type]["amount"]}</b> единиц.\n\n'
    message_text += f'<i>💎 С вашего баланса списано <b>{deduction_amount}</b> TAKE</i>'
    message_text += discount_message
    translated_text = translate_text(message_text, user.id)

    # Create inline buttons
    keyboard = InlineKeyboardMarkup(row_width=1)
    upgrade_more_button = InlineKeyboardButton("Проапгрейдить еще", callback_data=f"upgrade")
    back_button = InlineKeyboardButton("Назад", callback_data="back")
    keyboard.add(upgrade_more_button, back_button)

    await call.message.edit_caption(translated_text, reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'back')
async def handle_back(call: types.CallbackQuery):
    await call.message.delete()

@dp.callback_query_handler(lambda c: c.data == 'upgrade')
async def upgrades(call: types.CallbackQuery):
    user = call.from_user
    kb = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(text=translate_text("🔋 Улучшенный макс здоровье", user.id), callback_data="info-max_health"),
        InlineKeyboardButton(text=translate_text("⚔️ Плазменный меч", user.id), callback_data="info-damage"),
        InlineKeyboardButton(text=translate_text("⚙️ Улучшенный ремкомплект", user.id), callback_data="info-heal"),
        InlineKeyboardButton(text=translate_text("🛡 Титановая броня", user.id), callback_data="info-armor"),
        InlineKeyboardButton(text=translate_text("Назад", user.id), callback_data="back")
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
        await bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=InputMediaPhoto(
                media=photo,
                caption=(
                    f"🤖 {translate_text('Робот', user.id)}: <b>{robot_name}</b>\n\n"
                    f"<b>{translate_text('Выберите желаемое улучшение', user.id)}</b>\n\n"
                    f"{translate_text('Ваша текущая статистика', user.id)}:\n"
                    f"🔋 {translate_text('Макс здоровье', user.id)}: <b>{robot_max_health}</b>\n"
                    f"⚔️ {translate_text('Урон', user.id)}: <b>{robot_damage}</b>\n"
                    f"⚙️ {translate_text('Восстановление', user.id)}: <b>{robot_heal}</b>\n"
                    f"🛡 {translate_text('Броня', user.id)}: <b>{robot_armor}</b>\n"
                    f"{discount_message}"
                ),
                parse_mode="HTML"
            ),
            reply_markup=kb
        )



@dp.callback_query_handler(text='check')
@dp.throttled(rate=1)
async def check(call: types.CallbackQuery):
    user = call.from_user
    refstatus = bool(get_user_ref_status(user.id))
    user_ref = get_user_ref(user.id)
    markup = InlineKeyboardMarkup(row_width=1)
    try:
        ch_name = await bot.get_chat(chat_id)
        ch_link = ch_name.invite_link
        ch_name = ch_name.title
        button = InlineKeyboardButton(text=f'{ch_name.title()}', url=ch_link)
        markup.add(button)
        user_status = await bot.get_chat_member(chat_id=chat_id, user_id=user.id)
    except ChatNotFound:
        for x in administrators:
            await bot.send_message(x, f'Бот удален с канала ТонТейк!')
        return

    markup.add(InlineKeyboardButton(text='Подписался', callback_data='check'))
    message_text = f"Чтобы получить доступ к функциям бота, <b>нужно подписаться на канал:</b>"
    translated_text = translate_text(message_text, user.id)

    if user_status.status == 'left':
        message_text = '❌ Вы не подписаны!'
        translated_text = translate_text(message_text, user.id)
        await call.answer(translated_text, True)
        await call.message.delete()
        await call.message.answer(translated_text, reply_markup=markup, disable_web_page_preview=True)
    else:
        message_text = '<b>✅ Успешно</b>'
        translated_text = translate_text(message_text, user.id)
        await call.message.delete()
        await call.message.answer(translated_text)

        
        
        
        
@dp.callback_query_handler(text_startswith='robotopponent_')
@dp.throttled(callantiflood, rate=3)
async def robot_opponent(call: types.CallbackQuery):
    game_id = call.data.split('_')[1]
    print(game_id)
    robots = mdb.get_opponents_robot(game_id)

    if robots is None:
        message_text = 'Игру не найдено'
        translated_text = translate_text(message_text, call.from_user.id)
        await call.answer(translated_text, show_alert=True)
        return

    robot = robots[0]
    robot_id = robot[1]
    robot_name = robot[2]
    robot_health = robot[3]
    robot_damage = robot[4]
    robot_heal = robot[5]
    robot_armor = robot[6]
    robot_max_health = robot[8]

    with open(f'data/photos/robot_{robot_id}.png', 'rb') as photo:
        message_text = f'''
🤖 Робот: <b>{robot_name}</b>
🆔 ID: <b>{robot_id}</b>

🔋 Макс здоровье: <b>{robot_max_health}</b>
⚡️ Здоровье: <b>{robot_health}</b>
⚔️ Урон: <b>{robot_damage}</b>
⚙️ Восстановление: <b>{robot_heal}</b>
🛡 Броня: <b>{robot_armor}</b>'''
        translated_text = translate_text(message_text, call.from_user.id)
        message = await bot.send_photo(
            chat_id=call.from_user.id,
            photo=photo,
            caption=translated_text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text='Назад к битве', callback_data=f'back_to_battle_{game_id}_{call.message.message_id}')
                    ]
                ]
            )
        )



@dp.callback_query_handler(text_startswith='back_to_battle_')
@dp.throttled(callantiflood, rate=3)
async def back_to_battle(call: types.CallbackQuery):
    game_id, message_id = call.data.split('_')[2:4]

    await bot.delete_message(chat_id=call.from_user.id, message_id=int(call.message.message_id))


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('join_zero_game'))
async def join_zero_game(callback_query: types.CallbackQuery):
    await join_to_zero_game(callback_query.message)

async def join_to_zero_game(call: types.CallbackQuery):
    active_games = mdb.get_active_games()
    if len(active_games) == 0:
        await call.message.answer('''<b>❌ Нет активных боев!</b>

📌 Создайте сами в разделе "⚔️ Создать бой" или ожидайте других игроков.''')
        return

    markup = InlineKeyboardMarkup()
    for game in active_games:
        markup.add(InlineKeyboardButton(text=f'#{game[0]} | {game[1]} TON', callback_data=f'join_{game[0]}'))

    await call.message.answer('<b>⚔️ Активные бои:</b>', reply_markup=markup)



@dp.callback_query_handler(text_startswith='zerogame')
async def join_to_game(callback_query: types.CallbackQuery):
    await callback_query.answer()

    active_games = mdb.get_active_games()
    if not active_games:
        await callback_query.message.answer('''<b>❌ Нет активных боев!</b>

📌 Создайте сами в разделе "🔸 Создать бой" или ожидайте других игроков.''')
        return

    markup = InlineKeyboardMarkup()
    for game in active_games:
        markup.add(InlineKeyboardButton(text=f'#{game[0]} | {game[1]} TON', callback_data=f'join_{game[0]}'))

    await callback_query.message.answer('<b>⚔️ Активные бои:</b>', reply_markup=markup)
    
    
    



    
    
@dp.callback_query_handler(text='checkLinkWallet')
@dp.throttled(rate=1)
async def check_wallet_request(call: types.CallbackQuery):
    user_id = call.from_user.id
    user = call.from_user
    chat_id = call.message.chat.id
    wallet = get_user_wallet(user_id)

    if wallet:
        translated_text = translate_text(f"К вашему акканту привязан кошелек: {wallet}", user_id)
        await bot.send_message(chat_id, translated_text)
    else:
        code = f"TonTakeRoBot{chat_id}"
        last_transactions = TonScan().get_transactions(address)
        check_bool = False
        print('last_transactions: ', last_transactions)
        if last_transactions['ok']:
            for item in last_transactions['result']:
                if item['in_msg']:
                    if str(item['in_msg']['message']).lower() == str(code).lower():
                        source = item['in_msg']['source']
                        update_user_wallet(chat_id, value=source)
                        check_bool = True
                        break
            if check_bool:
                translated_text = translate_text(f"Кошелек <code>{source}</code> успешно привязан", user_id)
                await bot.send_message(chat_id, translated_text, parse_mode='HTML')
                
                ref = get_user_ref(user_id)
                if ref != 0:
                    add_refferal_balance(ref)
                    await bot.send_message(ref,
                                                    f'👤 Вы пригласили <a href="tg://user?id={user.id}"><b>{user.first_name}</b></a> и получили <b>0.03</b> TAKE')
                else:
                    print(f"Referral user with ID {ref} not found.")
            else:
                translated_text = translate_text(f"Не найдено платежа с коментарием <code>{code}</code>", user_id)
                await bot.send_message(chat_id, translated_text, parse_mode='HTML')
        else:
            translated_text = translate_text("Упс..", user_id)
            await bot.answer_callback_query(call.id, translated_text)

    

class AdminAtlantidaStates(StatesGroup):
    value = State()
    prize = State()
    power = State()
    photo_confirmation = State()
    new_photo = State()

@dp.callback_query_handler(text='admin_start_atlantida', state=None)
@dp.throttled(callantiflood, rate=1)
async def admin_start_atlantida(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in administrators:  # Проверяем, является ли пользователь администратором
        await bot.answer_callback_query(
            callback_query_id=callback.id,
            text="У вас нет прав администратора для выполнения этого действия.",
            show_alert=True
        )
        return

    await AdminAtlantidaStates.value.set()
    await bot.send_message(
        callback.from_user.id,
        'Введите стоимость входа в Атлантиду:'
    )

@dp.message_handler(state=AdminAtlantidaStates.value)
async def admin_atlantida_value(message: types.Message, state: FSMContext):
    try:
        value = float(message.text)
    except ValueError:
        await bot.send_message(
            message.from_user.id,
            'Неверный формат. Пожалуйста, введите число.'
        )
        return

    async with state.proxy() as data:
        data['value'] = value

    await AdminAtlantidaStates.next()
    await bot.send_message(
        message.from_user.id,
        f'Стоимость входа: {value}\n'
        'Введите приз за босса:'
    )

@dp.message_handler(state=AdminAtlantidaStates.prize)
async def admin_atlantida_prize(message: types.Message, state: FSMContext):
    try:
        prize = float(message.text)
    except ValueError:
        await bot.send_message(
            message.from_user.id,
            'Неверный формат. Пожалуйста, введите число.'
        )
        return

    async with state.proxy() as data:
        data['prize'] = prize

    await AdminAtlantidaStates.next()
    await bot.send_message(
        message.from_user.id,
        f'Стоимость входа: {data["value"]}\n'
        f'Приз: {prize}\n'
        'Введите здоровье босса Атлантиды'
    )

@dp.message_handler(state=AdminAtlantidaStates.power)
async def admin_atlantida_power(message: types.Message, state: FSMContext):
    global atlantida_data
    try:
        power = int(message.text)
    except ValueError:
        await bot.send_message(
            message.from_user.id,
            'Неверный формат. Пожалуйста, введите целое число.'
        )
        return

    async with state.proxy() as data:
        data['power'] = power

    text = (
        f'Стоимость входа: {data["value"]}\n'
        f'Приз: {data["prize"]}\n'
        f'Здоровье робота: {data["power"]}\n'
        'Все верно?\n'
        'Добавить новое фото босса?'
    )

    photo_keyboard = types.InlineKeyboardMarkup(row_width=2)
    yes_button = types.InlineKeyboardButton("Да", callback_data="yes_photo")
    no_button = types.InlineKeyboardButton("Нет", callback_data="no_photo")
    photo_keyboard.add(yes_button, no_button)

    # Сохраняем данные в словарь Python
    atlantida_data = {
        "value": data["value"],
        "prize": data["prize"],
        "power": data["power"]
    }

    await bot.send_message(
        message.from_user.id,
        text,
        reply_markup=photo_keyboard
    )

    await AdminAtlantidaStates.photo_confirmation.set()

@dp.callback_query_handler(lambda callback: callback.data in ["yes_photo", "no_photo"], state=AdminAtlantidaStates.photo_confirmation)
async def admin_atlantida_photo_confirmation(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "yes_photo":
        await AdminAtlantidaStates.new_photo.set()
        await bot.send_message(
            callback.from_user.id,
            'Пожалуйста, отправьте новое фото босса.'
        )
    else:
        await proceed_to_confirmation(callback, state)

@dp.message_handler(content_types=types.ContentType.PHOTO, state=AdminAtlantidaStates.new_photo)
async def admin_atlantida_new_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    file_path = 'data/photos/atlantida_bos.png'
    
    # Удаляем старое фото и сохраняем новое
    os.remove(file_path)
    await photo.download(destination_file=file_path)

    await proceed_to_confirmation(message, state)

async def proceed_to_confirmation(message_or_callback: Union[types.Message, types.CallbackQuery], state: FSMContext):
    global atlantida_data

    text = (
        f'Стоимость входа: {atlantida_data["value"]}\n'
        f'Приз: {atlantida_data["prize"]}\n'
        f'Здоровье робота: {atlantida_data["power"]}\n'
        'Все верно?'
    )

    confirm_keyboard = types.InlineKeyboardMarkup(row_width=2)
    confirm_button = types.InlineKeyboardButton("Да", callback_data="confirm_atlantida")
    cancel_button = types.InlineKeyboardButton("Нет", callback_data="cancel_atlantida")
    confirm_keyboard.add(confirm_button, cancel_button)

    if isinstance(message_or_callback, types.Message):
        user_id = message_or_callback.from_user.id
    else:
        user_id = message_or_callback.from_user.id

    await bot.send_message(
        user_id,
        text,
        reply_markup=confirm_keyboard
    )

    await state.finish()

@dp.callback_query_handler(lambda callback: callback.data in ["confirm_atlantida", "cancel_atlantida"], state=None)
async def confirm_or_cancel_atlantida(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if user_id not in administrators:   # Проверяем, является ли пользователь администратором
        await bot.answer_callback_query(
            callback_query_id=callback.id,
            text="У вас нет прав администратора для выполнения этого действия.",
            show_alert=True
        )
        return

    if callback.data == "confirm_atlantida":
        # Извлекаем данные из словаря
        value = atlantida_data.get('value')
        prize = atlantida_data.get('prize')
        power = atlantida_data.get('power')

        # Записываем данные в базу данных
        set_atlantida_value(value)
        set_atlantida_prize(prize)
        set_boss_power(power)
        set_atlantida_started_to_one()

        # Очищаем словарь
        atlantida_data.clear()

        # Отправляем сообщение администратору о успешном запуске
        await bot.send_message(
            callback.from_user.id,
            'Атлантида успешно запущена!'
        )

        # Создаем inline-клавиатуру с кнопкой
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        button = types.InlineKeyboardButton(
            text="🔗 Играть",
            url="https://t.me/TonTakeRoBot"
        )
        keyboard.add(button)

        # Отправляем сообщение в TAKE_CHAT
        await bot.send_message(
            TAKE_CHAT,
            f'<b>Внимание!</b> В локации Атлантида замечен новый босс. Победитель получит <b>{prize} ТАКЕ</b>.',
            parse_mode='HTML',
            reply_markup=keyboard
        )
    elif callback.data == "cancel_atlantida":
        # Очищаем словарь
        atlantida_data.clear()

        await bot.send_message(
            callback.from_user.id,
            'Запуск Атлантиды отменен.'
        )

    await state.finish()

    
  

@dp.callback_query_handler(lambda c: c.data in ['ru', 'en'])
async def process_language_selection(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    language = callback_query.data  # 'ru' or 'en'
    store_user_language(user_id, language)

    if language == 'ru':
        await bot.answer_callback_query(callback_query.id, "Вы выбрали русский язык.")
    elif language == 'en':
        await bot.answer_callback_query(callback_query.id, "You selected English language.")
    robots = mdb.get_user_robots(user_id)
    if len(robots) == 0:
        await bot.send_message(user_id, robot_chances_text(), reply_markup=get_robot_keyboard)
    else:
        await bot.send_message(user_id, get_start_text(), reply_markup=create_start_keyboard(user_id))


@dp.callback_query_handler(lambda c: c.data == 'zerofacaze')
async def zero_facaze(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id

    # Спрашиваем у пользователя подтверждение обнуления уровней
    confirm_text = translate_text("Вы уверены, что хотите обнулить все уровни роботов? Это действие нельзя будет отменить.", user_id)
    confirmation_markup = InlineKeyboardMarkup(
        row_width=2,
        inline_keyboard=[
            [
                InlineKeyboardButton(text='✅ Да', callback_data='zero_facaze_confirm'),
                InlineKeyboardButton(text='❌ Нет', callback_data='zero_facaze_cancel')
            ]
        ]
    )
    await bot.edit_message_text(
        text=confirm_text,
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=confirmation_markup
    )

@dp.callback_query_handler(lambda c: c.data in ['zero_facaze_confirm', 'zero_facaze_cancel'])
async def zero_facaze_confirmation(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id

    if callback_query.data == 'zero_facaze_confirm':
        set_zero_levels()
        success_text = translate_text("Успешно! Все уровни роботов были обнулены.", user_id)
        await bot.edit_message_text(
            text=success_text,
            chat_id=chat_id,
            message_id=message_id
        )
    else:
        cancel_text = translate_text("Обнуление уровней отменено.", user_id)
        await bot.edit_message_text(
            text=cancel_text,
            chat_id=chat_id,
            message_id=message_id
        )



class AdminChangeTime(StatesGroup):
    waiting_for_day = State()
    waiting_for_time = State()

@dp.callback_query_handler(lambda c: c.data == 'admin_squads')
@dp.throttled(callantiflood, rate=1)
async def admin_squads(callback: types.CallbackQuery):
    squads = get_all_squads()  # Получение всех сквадов с информацией о пользователях

    current_time_info = get_squad_admin_time()
    current_time_text = f"Текущее время окончания сквадов: {current_time_info[0]} день, {current_time_info[1]:02d}:{current_time_info[2]:02d}"

    inline_btn_change_time = InlineKeyboardButton("Изменить время окончания сквадов", callback_data="admin_change_time")
    inline_2kb = InlineKeyboardMarkup().add(inline_btn_change_time)

    await bot.send_message(callback.from_user.id, "Сквады: \n" + current_time_text, parse_mode="HTML", reply_markup=inline_2kb)
    
    if not squads:
        await callback.answer("Нет сквадов для отображения.", show_alert=True)
    else:
        squad_info = ""
        for squad_data in squads:
            squad_id, leader_id, group_name, *_ = squad_data
            leader_name = (await bot.get_chat(leader_id)).first_name  # Получение имени лидера
            squad_info += f"ID сквада: {squad_id}\nНазвание: {group_name}\nЛидер: {leader_name} (<a href='tg://user?id={leader_id}'>{leader_id}</a>)\n\n"  # Ссылка на лидера

        inline_btn = InlineKeyboardButton(f"Заблокировать сквад {squad_id}", callback_data=f"admin_block_squad_{squad_id}")
        inline_kb = InlineKeyboardMarkup().add(inline_btn)

        await bot.send_message(callback.from_user.id, squad_info, parse_mode="HTML", reply_markup=inline_kb)  # Отправка информации о сквадах администратору

@dp.callback_query_handler(lambda c: c.data.startswith('admin_block_squad_'),)
@dp.throttled(callantiflood, rate=1)
async def admin_block_squad(callback: types.CallbackQuery):
    squad_id = int(callback.data.split('_')[-1])
    success = delete_squad_from_db(squad_id)

    if success:
        await callback.answer("Сквад успешно удален из базы данных.")
    else:
        await callback.answer("Ошибка при удалении сквада из базы данных. Возможно, сквад с таким ID не существует.")


@dp.callback_query_handler(lambda c: c.data == 'admin_change_time')
@dp.throttled(callantiflood, rate=1)
async def admin_change_time(callback: types.CallbackQuery):
    inline_kb = InlineKeyboardMarkup(row_width=3)
    days_of_week = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    for day in days_of_week:
        inline_kb.add(InlineKeyboardButton(day, callback_data=f"admin_change_day_{days_of_week.index(day)}"))

    await callback.message.answer("Выберите день недели:", reply_markup=inline_kb)
    await AdminChangeTime.waiting_for_day.set()


@dp.callback_query_handler(lambda c: c.data.startswith('admin_change_day_'), state=AdminChangeTime.waiting_for_day)
@dp.throttled(callantiflood, rate=1)
async def admin_change_day(callback: types.CallbackQuery, state: FSMContext):
    day = int(callback.data.split("_")[-1])
    async with state.proxy() as data:
        data['day'] = day
    await AdminChangeTime.waiting_for_time.set()
    await callback.message.answer("Пожалуйста, введите новое время окончания сквадов в формате ЧЧ:ММ.")


@dp.message_handler(state=AdminChangeTime.waiting_for_time)
@dp.throttled(callantiflood, rate=1)
async def process_time(message: types.Message, state: FSMContext):
    time_input = message.text.split(":")
    if len(time_input) != 2:
        await message.answer("Неверный формат времени. Пожалуйста, введите время в формате ЧЧ:ММ.")
        return

    hour = int(time_input[0])
    minute = int(time_input[1])

    if not (0 <= hour < 24) or not (0 <= minute < 60):
        await message.answer("Неверное время. Пожалуйста, введите время в диапазоне от 00:00 до 23:59.")
        return

    async with state.proxy() as data:
        day = data['day']
    
    success = update_squad_admin_time(day, hour, minute)

    if success:
        await message.answer("Время окончания сквадов успешно изменено.")
        await state.finish()
    else:
        await message.answer("Ошибка при обновлении времени окончания сквадов. Пожалуйста, попробуйте снова.")
        
        
@dp.callback_query_handler(text='autowithdraw')
async def autowithdraw(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    auto_withdraw = get_auto_withdraw()
    message = 'Автовывод включен' if auto_withdraw == 1 else 'Автовывод выключен'
    translated_message = translate_text(message, user_id)
    if auto_withdraw == 1:
        button_text = 'Выключить автовывод'
        new_auto_withdraw = 0
    else:
        button_text = 'Включить автовывод'
        new_auto_withdraw = 1
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(text=button_text, callback_data=f'setautowithdraw_{new_auto_withdraw}')
    )
    await callback_query.message.edit_text(translated_message, reply_markup=keyboard)

@dp.callback_query_handler(text_startswith='setautowithdraw_')
async def set_autowithdraw(callback_query: types.CallbackQuery):
    new_auto_withdraw = int(callback_query.data.split('_')[1])
    set_auto_withdraw(new_auto_withdraw)
    user_id = callback_query.from_user.id
    message = 'Автовывод включен' if new_auto_withdraw == 1 else 'Автовывод выключен'
    translated_message = translate_text(message, user_id)
    await callback_query.answer(translated_message, show_alert=True)


