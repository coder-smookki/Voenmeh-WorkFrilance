from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from bot.keyboards.start_keyboard import get_start_keyboard
from bot.utils.consts import WELCOME_TEXT
import logging

go_to_menu_router = Router(name='go_to_menu_router')

@go_to_menu_router.callback_query(F.data == "go_to_menu")
async def universal_go_to_menu_handler(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        submission_id = data.get('submission_id')

        await state.clear()

        from bot.utils.states import submission_data
        if submission_id and submission_id in submission_data:
            del submission_data[submission_id]
        
        await callback.message.edit_text(
            text=WELCOME_TEXT,
            parse_mode='HTML',
            reply_markup=get_start_keyboard()
        )
        
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback.answer()
            return
        else:
            await callback.message.answer(
                text=WELCOME_TEXT,
                parse_mode='HTML',
                reply_markup=get_start_keyboard()
            )
            
    except Exception as e:
        logging.error(f"Error in universal_go_to_menu_handler: {e}")
        await callback.message.answer(
            text=WELCOME_TEXT,
            parse_mode='HTML',
            reply_markup=get_start_keyboard()
        )
        
    finally:
        await callback.answer()