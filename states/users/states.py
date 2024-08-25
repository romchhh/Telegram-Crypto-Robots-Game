from aiogram.dispatcher.filters.state import StatesGroup, State


class Form(StatesGroup):
    battlestate = State()
    freebattle = State()
    invite = State()


class DepositTon(StatesGroup):
    amount = State()


class DepositTake(StatesGroup):
    amount = State()


class WithdrawTon(StatesGroup):
    currency = State()
    amount = State()


class WithdrawTake(StatesGroup):
    currency = State()
    amount = State()

class DepositCry(StatesGroup):
    amount = State()