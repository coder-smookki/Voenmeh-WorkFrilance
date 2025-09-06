from aiogram.fsm.state import State, StatesGroup

# План чтения работы для предложки(Текст -> Файл -> Подтверждение)
class SubmissionStates(StatesGroup):
    waiting_text = State()
    waiting_files = State()
    waiting_confirmation = State()
    
# Словарь для отправки в предложку
submission_data = {}

# Словарь для отправки заказа
order_data ={}

# План чтения работы для заказа(Текст -> Файл -> Подтверждение)
class OrderStates(StatesGroup):
    waiting_text = State()
    waiting_files = State()
    waiting_confirmation = State()