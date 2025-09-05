import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.utils.consts import SUPPORT_CENTER, WRITE_QUESTION, EXPECT_RESPONSE
from bot.settings import SUPPORT_CHAT_ID
from bot.keyboards.back_to_menu import get_back_to_menu_keyboard
from bot.keyboards.support import get_support_keyboard
from bot.keyboards.repeal import get_cancel_keyboard

message_mapping = {}

class SupportState(StatesGroup):
    waiting_for_support_message = State()

help_router = Router(name='help_router')

@help_router.message(Command("help"))
@help_router.callback_query(F.data == "support")
async def help_command(message: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    
    if isinstance(message, CallbackQuery):
        callback = message
        message_obj = callback.message
        await callback.answer()
    else:
        message_obj = message
    
    await message_obj.answer(
        text=SUPPORT_CENTER,
        parse_mode='HTML',
        reply_markup=get_support_keyboard()
    )

@help_router.callback_query(F.data == "write_to_support")
async def write_to_support(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SupportState.waiting_for_support_message)
    
    await callback.message.edit_text(
        text=WRITE_QUESTION,
        parse_mode='HTML',
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@help_router.message(StateFilter(SupportState.waiting_for_support_message), F.chat.type == "private")
async def forward_to_support(message: Message, state: FSMContext):
    try:
        await state.clear()
        
        user_info = (
            f"👤 <b>Сообщение от пользователя:</b>\n"
            f"ID: <code>{message.from_user.id}</code>\n"
            f"Username: @{message.from_user.username or 'N/A'}\n"
        )
        
        if message.content_type == "text":
            full_text = (user_info + f"💬 Сообщение:\n{message.text}\n\n" + 
                         f"📝 Чтобы ответить на вопрос введите <code>/ответ {message.chat.id} Ваш ответ</code>")
            await message.bot.send_message(
                chat_id=SUPPORT_CHAT_ID,
                text=full_text,
                parse_mode='HTML'
            )
        else:
            caption = user_info
            if message.caption:
                caption += f"💬 Подпись:\n{message.caption}\n\n"
            caption += f"<code>/ответ {message.from_user.id} </code>"
            
            if message.content_type == "photo":
                await message.bot.send_photo(
                    chat_id=SUPPORT_CHAT_ID,
                    photo=message.photo[-1].file_id,
                    caption=caption,
                    parse_mode='HTML'
                )
            elif message.content_type == "document":
                await message.bot.send_document(
                    chat_id=SUPPORT_CHAT_ID,
                    document=message.document.file_id,
                    caption=caption,
                    parse_mode='HTML'
                )
            else:
                await message.copy_to(chat_id=SUPPORT_CHAT_ID, caption=caption, parse_mode='HTML')
        
        await message.answer(
            text=EXPECT_RESPONSE,
            parse_mode='HTML',
            reply_markup=get_back_to_menu_keyboard()
        )
        
    except Exception as e:
        logging.error(f"Error in forward_to_support: {e}")
        await message.answer(
            "❌ Ошибка при отправке сообщения.",
            reply_markup=get_back_to_menu_keyboard()
        )

@help_router.message(Command("ответ", "otvet", "reply"))
async def admin_reply(message: Message):
    try:
        args = message.text.split()[1:]
        
        if len(args) < 2:
            await message.reply(
                '⚠ <b>Использование:</b>\n<code>/ответ ID_пользователя Ваш ответ</code>',
                parse_mode='HTML'
            )
            return

        chat_id_str = args[0]
        answer_text = " ".join(args[1:])
        
        try:
            chat_id = int(chat_id_str)
        except ValueError:
            await message.reply('❌ Неверный ID пользователя.', parse_mode='HTML')
            return

        await message.bot.send_message(
            chat_id=chat_id,
            text=f"💬 <b>Ответ от поддержки:</b>\n\n{answer_text}",
            parse_mode='HTML'
        )
        
        await message.reply('✅ Ответ отправлен!')
        
    except Exception as e:
        logging.error(f"Error in admin_reply: {e}")
        await message.reply('❌ Ошибка при отправке ответа.')

@help_router.callback_query(F.data == "cancel_support")
async def cancel_support(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ <b>Обращение отменено</b>",
        parse_mode='HTML',
        reply_markup=get_back_to_menu_keyboard()
    )
    await callback.answer()