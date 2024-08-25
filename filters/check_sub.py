from aiogram.dispatcher.filters import BoundFilter

from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.utils.exceptions import ChatNotFound

from bot import bot
from data.config import chat_id, administrators


class IsSubscribed(BoundFilter):
    async def check(self, message: Message):
        markup = InlineKeyboardMarkup(row_width=1)
        try:
            ch_name = await bot.get_chat(chat_id)
            ch_link = ch_name.invite_link
            ch_name = ch_name.title
            button = InlineKeyboardButton(text=f'{ch_name.title()}', url=ch_link)
            markup.add(button)
            user_status = await bot.get_chat_member(chat_id=chat_id, user_id=message.from_user.id)
        except ChatNotFound:
            for x in administrators:
                await bot.send_message(x, f'Бот удален с канала ТонТейк!')
            return

        markup.add(InlineKeyboardButton(text='Подписался', callback_data='check'))
        text = f"Чтобы получить доступ к функциям бота, <b>нужно подписаться на канал:</b>"

        if user_status.status == 'left':
            await bot.send_message(message.from_user.id, text, reply_markup=markup, disable_web_page_preview=True)
            return False
        else:
            return True