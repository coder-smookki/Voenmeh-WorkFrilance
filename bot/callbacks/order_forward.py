from aiogram.types import CallbackQuery

def message_been_send(callback: CallbackQuery):
    return callback.answer("Сообщение отправлено!")
