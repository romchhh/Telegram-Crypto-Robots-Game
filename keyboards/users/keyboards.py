from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


from data.functions.translate import translate_text

def start_keyboard(user_id):
    start_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    start_keyboard.row(
        KeyboardButton(translate_text("🎮 Играть", user_id)),
        KeyboardButton(translate_text("🤖 Мои роботы", user_id))
    )

    start_keyboard.row(
        KeyboardButton(translate_text("💎 Баланс", user_id)),
        KeyboardButton(translate_text('🔼 Апгрейд', user_id)),
        KeyboardButton(translate_text("👥 Реферальная система", user_id)),
        KeyboardButton(translate_text("👝 Привязать кошелек", user_id))
    )

    start_keyboard.row(
        KeyboardButton(translate_text("🔝 Топ игроков", user_id)),
        KeyboardButton(translate_text("🏆 Турнир", user_id)),
        KeyboardButton(translate_text("🛒 Магазин", user_id)),
        KeyboardButton(translate_text("🖼 NFTs", user_id))
    )

    start_keyboard.row(
        KeyboardButton(translate_text("🏪 Рынок", user_id)),
        KeyboardButton(translate_text("⭐️", user_id)),
        KeyboardButton(translate_text("🏭 Локации", user_id)),
        KeyboardButton(translate_text("🕹 Игры ТАКЕ", user_id))
    )

    # start_keyboard.row(
    #         KeyboardButton(translate_text("👝 Привязать кошелек", user_id)),
    #         KeyboardButton(translate_text("🖼 Мои НФТ", user_id)),
    #         KeyboardButton(translate_text("🕹 Игры ТАКЕ", user_id))
    # )

    return start_keyboard


def get_robot_keyboard(user_id):
    get_robots_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    get_robots_keyboard.row(
        KeyboardButton(translate_text("Получить робота 🤖", user_id))
    )
    return get_robots_keyboard


def create_start_keyboard(user_id):
    start_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    start_keyboard.row(
        KeyboardButton(translate_text("🎮 Играть", user_id)),
        KeyboardButton(translate_text("🤖 Мои роботы", user_id)),
        KeyboardButton(translate_text("🏭 Локации", user_id))
    )

    start_keyboard.row(
        KeyboardButton(translate_text("💎 Баланс", user_id)),
        KeyboardButton(translate_text('🔼 Апгрейд', user_id)),
        KeyboardButton(translate_text("👥 Реферальная система", user_id)),
        KeyboardButton(translate_text("👝 Привязать кошелек", user_id))
    )

    start_keyboard.row(
        KeyboardButton(translate_text("🔝 Топ игроков", user_id)),
        KeyboardButton(translate_text("🏆 Турнир", user_id)),
        KeyboardButton(translate_text("🛒 Магазин", user_id)),
        KeyboardButton("🖼 NFTs")
    )

    start_keyboard.row(
        KeyboardButton(translate_text("🏪 Рынок", user_id)),
        KeyboardButton(translate_text("⭐️ Статистика", user_id)),
        KeyboardButton("📸 Сквады"),
        KeyboardButton(translate_text("🕹 Игры ТАКЕ", user_id))
    )

    # start_keyboard.row(
    #         KeyboardButton(translate_text("👝 Привязать кошелек", user_id)),
    #         KeyboardButton(translate_text("🖼 Мои НФТ", user_id)),
    #         KeyboardButton(translate_text("🕹 Игры ТАКЕ", user_id))
    # )

    return start_keyboard

def get_sand_keyboard(user_id):
    sand = InlineKeyboardMarkup(row_width=1)
    sand.row(InlineKeyboardButton(text=translate_text("🔼 Вперёд", user_id), callback_data="hod"))
    sand.row(InlineKeyboardButton(text=translate_text("◀️ Налево", user_id), callback_data="hod"),
             InlineKeyboardButton(text=translate_text("Направо ▶️", user_id), callback_data="hod"))
    sand.row(InlineKeyboardButton(text=translate_text("🔽 Назад", user_id), callback_data="hod"))
    sand.row(InlineKeyboardButton(text=translate_text("🛸 На базу", user_id), callback_data="to_base"))
    return sand


def get_sand_zero_keyboard(user_id):
    sand = InlineKeyboardMarkup(row_width=1)
    sand.row(InlineKeyboardButton(text=translate_text("🏭 Завод", user_id), callback_data="factory")),
    sand.row(InlineKeyboardButton(text=translate_text('⚡️ Восстановить', user_id), callback_data='heal_location')),
    sand.row(InlineKeyboardButton(text=translate_text("🛸 На базу", user_id), callback_data="to_base"))
    return sand

def get_factory_keyboard(user_id):
    factory = InlineKeyboardMarkup(row_width=1)
    factory.row(InlineKeyboardButton(text=translate_text("🔼 Вперёд", user_id), callback_data="fhod"))
    factory.row(InlineKeyboardButton(text=translate_text("◀️ Налево", user_id), callback_data="fhod"),
             InlineKeyboardButton(text=translate_text("Направо ▶️", user_id), callback_data="fhod"))
    factory.row(InlineKeyboardButton(text=translate_text("🔽 Назад", user_id), callback_data="fhod"))
    factory.row(InlineKeyboardButton(text=translate_text("🛸 На базу", user_id), callback_data="to_base"))
    return factory


def get_island_keyboard(user_id):
    island = InlineKeyboardMarkup(row_width=1)
    island.row(InlineKeyboardButton(text=translate_text("🔼 Вперёд", user_id), callback_data="ihod"))
    island.row(InlineKeyboardButton(text=translate_text("◀️ Налево", user_id), callback_data="ihod"),
             InlineKeyboardButton(text=translate_text("Направо ▶️", user_id), callback_data="ihod"))
    island.row(InlineKeyboardButton(text=translate_text("🔽 Назад", user_id), callback_data="ihod"))
    island.row(InlineKeyboardButton(text=translate_text("🛸 На базу", user_id), callback_data="to_base"))
    return island


def get_atlantida_keyboard(user_id):
    atlantida = InlineKeyboardMarkup(row_width=1)
    atlantida.row(InlineKeyboardButton(text=translate_text("🔼 Вперёд", user_id), callback_data="ahod"))
    atlantida.row(InlineKeyboardButton(text=translate_text("◀️ Налево", user_id), callback_data="ahod"),
             InlineKeyboardButton(text=translate_text("Направо ▶️", user_id), callback_data="ahod"))
    atlantida.row(InlineKeyboardButton(text=translate_text("🔽 Назад", user_id), callback_data="ahod"))
    atlantida.row(InlineKeyboardButton(text=translate_text("🛸 На базу", user_id), callback_data="to_base"))
    return atlantida



atlantida = InlineKeyboardMarkup(row_width=1)  
atlantida.row(InlineKeyboardButton(text="🔼 Вперёд", callback_data="ahod")) 
atlantida.row(InlineKeyboardButton(text="◀️ Налево", callback_data="ahod"),
         InlineKeyboardButton(text="Направо ▶️", callback_data="ahod"))
atlantida.row(InlineKeyboardButton(text="🔽 Назад", callback_data="ahod")) 
atlantida.row(InlineKeyboardButton(text="🛸 На базу", callback_data="to_base"))

battle = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton(text="⚔️ Атака", callback_data="mhit"),
    InlineKeyboardButton(text="🛡 Защита", callback_data="mnohit"),
)
bet_key = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton(text="0 TON", callback_data="bet_0"),
    InlineKeyboardButton(text="0.05 TON", callback_data="bet_0.05"),
    InlineKeyboardButton(text="0.1 TON", callback_data="bet_0.1"),
    InlineKeyboardButton(text="0.5 TON", callback_data="bet_0.5"),
    InlineKeyboardButton(text="1 TON", callback_data="bet_1"),
    InlineKeyboardButton(text="5 TON", callback_data="bet_5"),
)
battle_k = InlineKeyboardMarkup(resize_keyboard=True)
battle_k.row(InlineKeyboardButton(text="⚔️ Атака", callback_data="hitmp"), InlineKeyboardButton(text="🛡 Защита",
                                                                                                callback_data="healmp"))
btl = ReplyKeyboardMarkup(resize_keyboard=True)
btl.row(KeyboardButton("Противник не отвечает"))
btl.row(KeyboardButton("Сбежать"))


deposit_key = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='📥 Пополнить', callback_data='deposit'),
            InlineKeyboardButton(text='📤 Вывести', callback_data='withdraw')
        ]
    ]
)

currency_key = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='TON', callback_data='dep_ton'),
            InlineKeyboardButton(text='TAKE', callback_data='dep_take')
        ]
    ]
)

dep_ton_key = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='🚀 xRocket', callback_data='dep_ton_rocket')
        ]
    ]
)

back_key = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='🔙 Назад')
        ]
    ],
    resize_keyboard=True
)

heal_key = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton('⚡️ Восстановить', callback_data='heal')
        ]
    ]
)

confirm_heal_key = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton('✅ Потвердить', callback_data='confirm-heal')
        ]
    ]
)


async def withdraw_key(amount):
    key = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='✅ Подтвердить', callback_data='accept-withdraw_' + str(amount))
            ]
        ]
    )

    return key

async def withdraw_key_take(amount):
    key = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='✅ Подтвердить', callback_data='accept-takewithdraw_' + str(amount))
            ]
        ]
    )

    return key

async def admin_withdraw_key(user_id, amount):
    key = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='✅ Подтвердить', callback_data=f'admin-withdraw_{user_id}_{amount}')
            ]
        ]
    )

    return key

async def admin_withdraw_take_key(user_id, amount):
    key = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='✅ Подтвердить', callback_data=f'admin-takewithdraw{user_id}_{amount}')
            ]
        ]
    )

    return key

async def market_key(robot_id, next_id, back_id, length, robot_index, user_id):
    text_buy_robot = translate_text('🤖 Купить робота', user_id)
    text_back = translate_text('⬅️', user_id)
    text_index = translate_text(f'{robot_index + 1}/{length}', user_id)
    text_forward = translate_text('➡️', user_id)

    key = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=text_buy_robot, callback_data=f'buy_{robot_id}')
            ],
            [
                InlineKeyboardButton(text=text_back, callback_data=f'next_{back_id}'),
                InlineKeyboardButton(text=text_index, callback_data='None'),
                InlineKeyboardButton(text=text_forward, callback_data=f'next_{next_id}')
            ]
        ]

    )

    return key


async def my_robots_key(robot_index, robot_id, length, status, user_id):
    if status == 'unselected':
        text_select_robot = translate_text('🤖 Выбрать робота', user_id)
        text_back = translate_text('⬅️', user_id)
        text_index = translate_text(f'{robot_index + 1}/{length}', user_id)
        text_forward = translate_text('➡️', user_id)

        key = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text=text_select_robot, callback_data=f'select_{robot_id}')
                ],
                [
                    InlineKeyboardButton(text=text_back, callback_data=f'myrobot_{robot_index - 1}'),
                    InlineKeyboardButton(text=text_index, callback_data='None'),
                    InlineKeyboardButton(text=text_forward, callback_data=f'myrobot_{robot_index + 1}')
                ]
            ]

        )
    else:
        text_selected = translate_text('✅ Выбран', user_id)
        text_back = translate_text('⬅️', user_id)
        text_index = translate_text(f'{robot_index + 1}/{length}', user_id)
        text_forward = translate_text('➡️', user_id)

        key = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text=text_selected, callback_data=f'None')
                ],
                [
                    InlineKeyboardButton(text=text_back, callback_data=f'myrobot_{robot_index - 1}'),
                    InlineKeyboardButton(text=text_index, callback_data='None'),
                    InlineKeyboardButton(text=text_forward, callback_data=f'myrobot_{robot_index + 1}')
                ]
            ]

        )

    return key



async def bet_confirm_key(bet):
    key = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='✅ Создать', callback_data=f'create_{bet}')
            ]
        ]
    )

    return key

async def bet_confirm_zero_key(bet):
    key = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='✅ Все равно создать', callback_data=f'create_{bet}')
                
            ],
            [
                InlineKeyboardButton(text='⚔️ Присоединится', callback_data=f'zerogame')
                
            ],
            [
                InlineKeyboardButton(text='❌ Отменить', callback_data=f'back_to_battle_')
            ]
        ]
    )

    return key


async def join_game_key(game_id):
    key = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='⚔️ Начать', callback_data=f'start_{game_id}')
            ],
            [
                InlineKeyboardButton(text='🤖 Робот противника', callback_data=f'robotopponent_{game_id}')
            ]
        ]
    )

    return key








async def send_challenge(game_id, user_id):
    key = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='⚔️ Начать бой', callback_data=f'accept_{game_id}_{user_id}')
            ]
        ]
    )

    return key


async def attack_key(game_id, user_id):
    key = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton('⚔️ Атака', callback_data=f'attack_{game_id}_{user_id}'),
            ],
            [
                InlineKeyboardButton('🗽 Сбежать', callback_data=f'escape_{game_id}_{user_id}')
            ]
        ]
    )

    return key


async def only_attack_key(game_id, user_id):
    key = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton('⚔️ Атака', callback_data=f'attack_{game_id}_{user_id}')
            ]
        ]
    )

    return key


async def double_strike_key(game_id, user_id):
    key = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton('🗡️ Двойной удар', callback_data=f'doublestrike_{game_id}_{user_id}'),
            ],
            [
                InlineKeyboardButton('🗽 Сбежать', callback_data=f'escape_{game_id}_{user_id}')
            ]
        ]
    )

    return key


async def not_respond_key(game_id, user_id):
    key = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton('Противник не отвечает', callback_data=f'not-respond_{game_id}')
            ],
            [
                InlineKeyboardButton('🗽 Сбежать', callback_data=f'escape_{game_id}_{user_id}')
            ]
        ]
    )

    return key


async def locations_key(user_id):
    key = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=translate_text("Остров 🏝", user_id), callback_data="island")
            ],
            [
                InlineKeyboardButton(text=translate_text("Пустыня 🏜", user_id), callback_data="sand")
            ],
            [
                InlineKeyboardButton(text=translate_text("Завод 🏭", user_id), callback_data="factory")
            ],
            [
                InlineKeyboardButton(text=translate_text("Атлантида 🐬", user_id), callback_data="atlantida")
            ]
        ]
    )

    return key



pay_locations_key = InlineKeyboardMarkup(row_width=1)  
pay_locations_key.row(InlineKeyboardButton(text="Оплатить вход 💸", callback_data="pay_island_")) 
pay_locations_key.row(InlineKeyboardButton(text="Назад 🔙", callback_data="to_base"))


pay_island_key = InlineKeyboardMarkup(row_width=1)  
pay_island_key.row(InlineKeyboardButton(text="Оплатить вход 💸", callback_data="pay_take_island_")) 


def get_pay_atlantida_keyboard(user_id):
    pay_atlantida_key = InlineKeyboardMarkup(row_width=1)
    pay_button_text = translate_text("Оплатить вход 💸", user_id)
    back_button_text = translate_text("Назад 🔙", user_id)
    pay_atlantida_key.row(InlineKeyboardButton(text=pay_button_text, callback_data="pay_atlantida_"))
    pay_atlantida_key.row(InlineKeyboardButton(text=back_button_text, callback_data="to_base"))
    return pay_atlantida_key


def get_pay_atlantida_keyboard_confirm(user_id):
    pay_atlantida = InlineKeyboardMarkup(row_width=1)
    pay_button_text = translate_text("Оплатить вход 💸", user_id)
    pay_atlantida.row(InlineKeyboardButton(text=pay_button_text, callback_data="pay_take_atlantida_"))
    return pay_atlantida

async def bazar_key(robot_id, next_id, back_id, length, robot_index, robot_seller, user_id):
    key = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=translate_text('⬅️', user_id), callback_data=f'bazarnext_{back_id}'),
                InlineKeyboardButton(text=f'{robot_index + 1}/{length}', callback_data='None'),
                InlineKeyboardButton(text=translate_text('➡️', user_id), callback_data=f'bazarnext_{next_id}')
            ],
            [
                InlineKeyboardButton(text=translate_text('🤖 Купить робота', user_id), callback_data=f'bazarbuy_{robot_id}_{robot_seller}')
            ],
            [
                InlineKeyboardButton(text=translate_text('🛍 Продать робота', user_id), callback_data=f'bazarsell')
            ],
            [
                InlineKeyboardButton(text=translate_text('👨🏼‍💻 Мои продажи', user_id), callback_data='mybazaritems_')
            ]
        ]

    )

    return key



async def sell_my_robots_key(robot_index, robot_id, length):
    key = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='⬅️', callback_data=f'mybazarrobot_{robot_index - 1}'),
                    InlineKeyboardButton(text=f'{robot_index + 1}/{length}', callback_data='None'),
                    InlineKeyboardButton(text='➡️', callback_data=f'mybazarrobot_{robot_index + 1}')
                ],
                [
                    InlineKeyboardButton(text='🤖 Продать робота', callback_data=f'sellrobot_{robot_id}')
                ]
            ]

        )


    return key

def nft_key(chat_id, bot_name='TonTakeRoBot'):
    key = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text=translate_text('Проверить платёж', chat_id), callback_data='checkLinkWallet')
                ],
                [
                    InlineKeyboardButton(text=translate_text('💸 Отправить через TonKeeper', chat_id),
                                      url=f"https://app.tonkeeper.com/transfer/EQCSvwpsHiBvdS2nxIJ77Z7D-8MNqe4vGy0ZBW50WM1WJtvO?text={bot_name}{chat_id}")
                ]
            ]

        )

    return key






def confirmation_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="✅", callback_data="confirm_surrender"),
                 InlineKeyboardButton(text="❌", callback_data="cancel_surrender"))
    return keyboard


def get_language_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    btn_ru = InlineKeyboardButton("Русский", callback_data="ru")
    btn_en = InlineKeyboardButton("English", callback_data="en")
    markup.add(btn_ru, btn_en)
    return markup
