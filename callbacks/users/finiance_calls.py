from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot import dp, bot
from data.config import LOGS
from data.payments.cryptobot import check_cry_payment
from data.payments.rocket import check_payment
from keyboards.users.keyboards import back_key, currency_key, dep_ton_key
from states.users.states import DepositTon, DepositTake, WithdrawTon, DepositCry, WithdrawTake
from data.functions.db import add_balance, add_take_balance

html = 'HTML'


@dp.callback_query_handler(text='withdraw')
async def withdraw(call: CallbackQuery):
    markup = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("TON", callback_data="withdraw_ton"),
        InlineKeyboardButton("TAKE", callback_data="withdraw_take")
    )
    await call.message.answer('Выберите валюту для вывода:', reply_markup=markup)
    await call.message.delete()


@dp.callback_query_handler(text='withdraw_ton')
async def withdraw_ton(call: CallbackQuery):
    await call.message.answer('Введите сумму вывода в TON:', reply_markup=back_key)
    await WithdrawTon.amount.set()
    await call.message.delete()

@dp.callback_query_handler(text='withdraw_take')
async def withdraw_take(call: CallbackQuery):
    await call.message.answer('Введите сумму вывода в TAKE:', reply_markup=back_key)
    await WithdrawTake.amount.set()
    await call.message.delete()


@dp.callback_query_handler(text='deposit')
async def deposit(call: CallbackQuery):
    await call.message.edit_text('Выберите валюту пополнения:', reply_markup=currency_key)


@dp.callback_query_handler(text='dep_ton')
async def deposit_ton(call: CallbackQuery):
    await call.message.edit_text('🌐 Выберите способ оплаты:', reply_markup=dep_ton_key)


@dp.callback_query_handler(text='dep_ton_rocket')
async def deposit_ton_1(call: CallbackQuery):
    await call.message.answer(f'<b>Введите сумму которую хотите пополнить в TON:</b>',
                              reply_markup=back_key)
    await DepositTon.amount.set()
    await call.message.delete()


@dp.callback_query_handler(text_startswith='check-ton')
@dp.throttled(rate=1)
async def check_payment_ton(call: CallbackQuery):
    user = call.from_user
    invoice_id = call.data.split('_')[1]
    status, amount = await check_payment(invoice_id)
    if status is None:
        await call.message.answer('<b>❌ Ошибка при обработке, попробуйте еще раз!</b>')
        return
    elif status == 'active':
        await call.answer('❌ Платеж не найден!', True)
        return
    elif status == 'expired':
        await call.message.edit_text('❌ Время платежа вышло, ссылка больше не активен!\nСоздайте новый платеж!')
        return

    add_balance(user.id, amount)
    await call.message.edit_text(f'<b>✅ Оплата прошла успешно!\n\n📥 На ваш баланс зачислен {amount} TON!</b>',
                                 parse_mode=html)

    await bot.send_message(LOGS, f'<b>📥 Новое пополнения TON!\n\n'
                                 f'👤Юзернейм: @{user.username}\n'
                                 f'🆔Айди: <code>{user.id}</code>\n'
                                 f'💳Сумма: {amount} TON</b>')


@dp.callback_query_handler(text='dep_take')
async def deposit_take_1(call: CallbackQuery):
    await call.message.answer(f'<b>Введите сумму которую хотите пополнить в TAKE:</b>',
                              reply_markup=back_key)
    await DepositTake.amount.set()
    await call.message.delete()


@dp.callback_query_handler(text_startswith='check-take')
@dp.throttled(rate=1)
async def check_payment_take(call: CallbackQuery):
    user = call.from_user
    invoice_id = call.data.split('_')[1]
    status, amount = await check_payment(invoice_id)
    if status is None:
        await call.message.answer('<b>❌ Ошибка при обработке, попробуйте еще раз!</b>')
        return
    elif status == 'active':
        await call.answer('❌ Платеж не найден!', True)
        return
    elif status == 'expired':
        await call.message.edit_text('❌ Время платежа вышло, ссылка больше не активен!\nСоздайте новый платеж!')
        return

    add_take_balance(user.id, amount)
    await call.message.edit_text(f'<b>✅ Оплата прошла успешно!\n\n📥 На ваш баланс зачислен {amount} TAKE!</b>',
                                 parse_mode=html)

    await bot.send_message(LOGS, f'<b>📥 Новое пополнения TAKE!\n\n'
                                 f'👤Юзернейм: @{user.username}\n'
                                 f'🆔Айди: <code>{user.id}</code>\n'
                                 f'💳Сумма: {amount} TAKE</b>')


# DEPOSIT CRYPTO BOT
@dp.callback_query_handler(text='dep_crypto')
async def dep_crypto(call: CallbackQuery):
    await call.message.answer('<b>Введите сумму которую хотите пополнить в TON:</b>', reply_markup=back_key)
    await DepositCry.amount.set()
    await call.message.delete()


@dp.callback_query_handler(text_startswith='check-cry_')
@dp.throttled(rate=1)
async def check_payment_ton(call: CallbackQuery):
    user = call.from_user
    invoice_id = call.data.split('_')[1]
    invoice = await check_cry_payment(invoice_id)
    invoice = invoice[0]
    if invoice.status is None:
        await call.message.answer('<b>❌ Ошибка при обработке, попробуйте еще раз!</b>')
        return
    elif invoice.status == 'active':
        await call.answer('❌ Платеж не найден!', True)
        return
    elif invoice.status == 'expired':
        await call.message.edit_text('❌ Время платежа вышло, ссылка больше не активен!\nСоздайте новый платеж!')
        return
    amount = round(float(invoice.amount), 4)
    add_balance(user.id, amount)
    await call.message.edit_text(f'<b>✅ Оплата прошла успешно!\n\n📥 На ваш баланс зачислен {amount} TON!</b>')
    await bot.send_message(LOGS, f'<b>📥 Новое пополнения CryptoBot TON!\n\n'
                                 f'👤Юзернейм: @{user.username}\n'
                                 f'🆔Айди: <code>{user.id}</code>\n'
                                 f'💳Сумма: {amount} TON</b>')