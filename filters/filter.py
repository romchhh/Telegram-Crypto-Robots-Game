from aiogram import types
from aiogram.dispatcher.filters import BoundFilter

from data.config import administrators


class IsPrivate(BoundFilter):
    async def check(self, message: types.Message):
        return message.chat.type == types.ChatType.PRIVATE


class IsAdmin(BoundFilter):
    async def check(self, message: types.Message):
        return message.from_user.id in administrators
