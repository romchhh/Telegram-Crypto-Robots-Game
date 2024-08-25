from aiogram.dispatcher.filters.state import StatesGroup, State


class SendAllText(StatesGroup):
    text = State()


class SendAllPhoto(StatesGroup):
    photo = State()
    text = State()


class StartTour(StatesGroup):
    date = State()


class EditUserBalance(StatesGroup):
    user_id = State()
    currency = State()
    edit_type = State()
    value = State()


class SearchUser(StatesGroup):
    id = State()


class NewRobot(StatesGroup):
    name = State()
    health = State()
    damage = State()
    heal = State()
    armor = State()
    price = State()
    photo = State()
    confirm = State()


class DeleteRobot(StatesGroup):
    robot_id = State()
    confirm = State()