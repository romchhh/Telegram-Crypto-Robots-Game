import os

from bot import dp, bot, mdb

from aiogram.types import CallbackQuery

from data.config import LOGS

from data.payments.rocket import transfer
from keyboards.admins.keyboards import *

from aiogram.dispatcher import FSMContext

from states.admins.states import *

from data.functions.db import get_active_tour, decrease_balance, decrease_take_balance

html = 'HTML'


@dp.callback_query_handler(text='cancel_admin', state='*')
async def cancellation_state_admin(call: CallbackQuery, state: FSMContext):
    await state.finish()
    await call.answer('❌ Отменено')
    await call.message.delete()


# РАССЫЛКА
@dp.callback_query_handler(text='send_all')
async def send_all(call: CallbackQuery):
    await call.message.edit_text('Выберите:', reply_markup=send_all_key)


@dp.callback_query_handler(text='send_all_text', state=None)
async def send_all_text(call: CallbackQuery):
    await call.message.edit_text('Введите текст рассылки:', reply_markup=cancel_adm_key)

    await SendAllText.text.set()


@dp.callback_query_handler(text='send_all_photo', state=None)
async def send_all_photo(call: CallbackQuery):
    await call.message.edit_text('Введите фото для рассылки:', reply_markup=cancel_adm_key)

    await SendAllPhoto.photo.set()


@dp.callback_query_handler(text='start-tour')
async def start_tour(call: CallbackQuery):
    active_tour = get_active_tour()
    if active_tour is not None:
        await call.answer(
            '🚫 Уже есть активный турнир, вы не можете начать еще один турнир пока активный не закончится!',
            True
        )
        return
    await call.message.edit_text('''🕐 Введите дату окончание турнира в формате: день.месяц.год час(в 24х часовом формате) минут указать не надо!
Пример: 08.09.23 18
ℹ️ Это означает что турнир окончиться 8-сентября 23-года в 18:00, внимательно укажите дату окончания как в примере:''',
                                 reply_markup=cancel_adm_key,
                                 parse_mode=html)
    await StartTour.date.set()


@dp.callback_query_handler(text='search', state=None)
async def search_user(call: CallbackQuery):
    await call.message.edit_text('✍️ Напишите id юзера:', reply_markup=cancel_adm_key)
    await SearchUser.id.set()


@dp.callback_query_handler(text_startswith='user-give')
async def edit(call: CallbackQuery):
    user_id = call.data.split('_')[1]
    await call.message.edit_text('<b>Что будем изменять?</b>', reply_markup=await admin_user_edit_key(user_id))


@dp.callback_query_handler(text_startswith='user-currency')
async def edit_2(call: CallbackQuery):
    currency = call.data.split(':')[1]
    user_id = call.data.split(':')[2]
    await call.message.edit_text('<b>Дать или отрбрать?</b>', reply_markup=await admin_user_edit_key_2(user_id, currency))


@dp.callback_query_handler(text_startswith='user-edit')
async def edit_3(call: CallbackQuery, state: FSMContext):
    user_id = call.data.split(':')[1]
    currency = call.data.split(':')[2]
    edit_type = call.data.split(':')[3]
    async with state.proxy() as data:
        data['user_id'] = user_id
        data['currency'] = currency
        data['edit_type'] = edit_type
    await call.message.edit_text('<b>Введите сумму:</b>', reply_markup=cancel_adm_key)
    await EditUserBalance.value.set()


@dp.callback_query_handler(text_startswith='admin-withdraw')
async def withdraw(call: CallbackQuery):
    user = call.data.split('_')[1]
    amount = call.data.split('_')[2]
    
    user_id = int(user) 
    user_obj = await bot.get_chat(user_id)

    success = await transfer(user, amount, 'TONCOIN')
    if success:
        decrease_balance(call.from_user.id, amount)
        
        await bot.send_message(LOGS, f'<b>📥 Новый вывод TОN!\n\n'
                                 f'👤Юзернейм: @{user_obj.username}\n'
                                 f'🆔Айди: <code>{user_obj.id}</code>\n'
                                 f'💳Сумма: {amount} TON</b>')
        await bot.send_message(user, f'✅ Вам выплачено <b>{amount}</b> TON.')
    else:
        await call.message.answer('🚫 Ошибка при выводе, проверьте баланс api!')


@dp.callback_query_handler(text_startswith='admin-takewithdraw')
async def withdraw_take(call: CallbackQuery):
    user = call.data.split('_')[1]
    user_id = int(user)  # assuming user is the string representation of the user id
    amount = call.data.split('_')[2]

    # Get the user object
    user_obj = await bot.get_chat(user_id)

    success = await transfer(user, amount, 'TAKE')
    if success:
        decrease_take_balance(user_id, amount)
        await bot.send_message(LOGS, f'<b>📥 Новый вывод TAKE!\n\n'
                                 f'👤Юзернейм: @{user_obj.username}\n'
                                 f'🆔Айди: <code>{user_obj.id}</code>\n'
                                 f'💳Сумма: {amount} TAKE</b>')
        await bot.send_message(user_id, f'✅ Вам выплачено <b>{amount}</b> TAKE.')
    else:
        await call.message.answer('🚫 Ошибка при выводе, проверьте баланс api!')


@dp.callback_query_handler(text='add-robot')
async def add_new_robot(call: CallbackQuery):
    await call.message.edit_text('Введете название нового робота:', reply_markup=cancel_adm_key)
    await NewRobot.name.set()


@dp.callback_query_handler(text='del-robot')
async def del_robot_1(call: CallbackQuery):
    await call.message.edit_text('Введете название id робота которого нужно удалить:', reply_markup=cancel_adm_key)
    await DeleteRobot.robot_id.set()


@dp.callback_query_handler(text='confirm-delete-robot', state=DeleteRobot.confirm)
async def del_robot_3(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    robot_id = data['robot_id']
    mdb.delete_robot(robot_id)

    await call.message.edit_text(f'Робот с ID <b>{robot_id}</b> удален успешно!')
    await state.finish()


@dp.callback_query_handler(text='confirm-new-robot', state=NewRobot.confirm)
async def confirm_new_robot(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    name = data['name']
    health = data['health']
    damage = data['damage']
    heal = data['heal']
    armor = data['armor']
    price = data['price']
    photo_id = data['photo']

    robot_id = mdb.create_robot(
        name,
        health,
        damage,
        heal,
        armor,
        price
    )

    photo_info = await bot.get_file(photo_id)

    file_path = photo_info.file_path

    file = await bot.download_file(file_path)

    os.makedirs("data/photos/", exist_ok=True)

    save_path = f"data/photos/robot_{robot_id}.png"

    with open(save_path, 'wb') as new_file:
        new_file.write(file.read())

    await call.message.edit_caption(f'🤖 Робот <b>{name}</b> создан, ID робота: <b>{robot_id}</b>')

    await state.finish()