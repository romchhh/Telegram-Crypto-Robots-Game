from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

admin_key = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='✉️ Рассылка', callback_data='send_all')
        ],
        [
            InlineKeyboardButton(text='🏆 Начать турнир', callback_data='start-tour')
        ],
        [
            InlineKeyboardButton(text='🔎 Искать юзера', callback_data='search')
        ],
        [
            InlineKeyboardButton(text='🤖 Роботы', callback_data='admin-robots')
        ],
        [
            InlineKeyboardButton(text='🐬 Запустить атлантиду', callback_data='admin_start_atlantida')
        ],
        [
            InlineKeyboardButton(text='📸 Сквады', callback_data='admin_squads')
        ],
        [
            InlineKeyboardButton(text='0️⃣ Обнулить уровни игроков', callback_data='zerofacaze')
        ],
        [
            InlineKeyboardButton(text='💸 Автовывод', callback_data='autowithdraw')
        ]
    ]
    
    )
    


cancel_adm_key = InlineKeyboardMarkup(
    inline_keyboard=[

        [
            InlineKeyboardButton(text='❌ Отменить', callback_data='cancel_admin')
        ],

    ]
)


confirm_new_robot = InlineKeyboardMarkup(
    inline_keyboard=[

        [
            InlineKeyboardButton(text='✅ Подтвердить', callback_data='confirm-new-robot')
        ],
        [
            InlineKeyboardButton(text='❌ Отменить', callback_data='cancel_admin')
        ]

    ]
)

send_all_key = InlineKeyboardMarkup(
    inline_keyboard=[

        [
            InlineKeyboardButton(text='➕ С фоткой', callback_data='send_all_photo'),
            InlineKeyboardButton(text='➖ Без фотки', callback_data='send_all_text')
        ],

        [
            InlineKeyboardButton(text='❌ Отменить', callback_data='cancel_admin')
        ],

    ]
)

robots_key = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton('➕ Добавить робота', callback_data='add-robot')
        ],
        [
            InlineKeyboardButton('➖ Удалить робота', callback_data='del-robot')
        ]
    ]
)


async def admin_search_key(user_id):
    key = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='✏️ Изменить', callback_data='user-give_' + str(user_id))
            ]
        ]
    )
    return key


async def admin_user_edit_key(user_id):
    key = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(text='Баланс TON', callback_data='user-currency:ton_balance:' + str(user_id)),
                InlineKeyboardButton(text='Баланс TAKE', callback_data='user-currency:balance:' + str(user_id))
            ],
        ]
    )
    return key


async def admin_user_edit_key_2(user_id, currency):
    key = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(text='Дать', callback_data=f'user-edit:{user_id}:{currency}:give'),
                InlineKeyboardButton(text='Отобрать', callback_data=f'user-edit:{user_id}:{currency}:take')
            ],
            [
                InlineKeyboardButton(text='❌ Отменить', callback_data='cancel_admin')
            ],
        ]
    )
    return key