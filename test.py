class AdminAtlantidaStates(StatesGroup):
    value = State()
    prize = State()
    power = State()

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
    )

    confirm_keyboard = types.InlineKeyboardMarkup(row_width=2)
    confirm_button = types.InlineKeyboardButton("Да", callback_data="confirm_atlantida")
    cancel_button = types.InlineKeyboardButton("Нет", callback_data="cancel_atlantida")
    confirm_keyboard.add(confirm_button, cancel_button)

    # Сохраняем данные в словарь Python
    atlantida_data = {
        "value": data["value"],
        "prize": data["prize"],
        "power": data["power"]
    }

    print("1")
    print(atlantida_data)

    await bot.send_message(
        message.from_user.id,
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
        
        print("2")
        print(atlantida_data)

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