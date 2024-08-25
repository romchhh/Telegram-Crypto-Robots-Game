import asyncio
import datetime
import time

import pytz
from aiogram.dispatcher import FSMContext

from bot import bot, dp, mdb
from data.functions.db import get_users, get_count_exist_tour, add_tour, get_balance as get_user_balance, \
    get_take_balance, get_refferals, check_user, add_balance, decrease_balance, add_take_balance, decrease_take_balance
from data.payments.cryptobot import get_cry_balance
from filters import IsAdmin
from data.payments.rocket import get_all_balance

from aiogram.types import Message, ContentTypes, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import Command

from data.config import administrators
from keyboards.admins.keyboards import cancel_adm_key, admin_key, admin_search_key, confirm_new_robot
from keyboards.users.keyboards import start_keyboard
from states.admins.states import SendAllPhoto, SendAllText, StartTour, EditUserBalance, SearchUser, NewRobot, \
    DeleteRobot

html = 'HTML'


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
    user_id = message.from_user.id
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
                await bot.send_message(x, text, reply_markup=start_keyboard(user_id), parse_mode=html)
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
                await bot.send_photo(x, photo_id, text, reply_markup=start_keyboard, parse_mode=html)
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
    ton_balance = round(get_user_balance(user_id), 4)
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