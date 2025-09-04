from aiogram.fsm.state import State, StatesGroup

# План чтения работы(Текст -> Файл -> Подтверждение)
class SubmissionStates(StatesGroup):
    waiting_text = State()
    waiting_files = State()
    waiting_confirmation = State()