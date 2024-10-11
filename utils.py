from aiogram.fsm.state import StatesGroup, State


class TaskForm(StatesGroup):
    task_name = State()