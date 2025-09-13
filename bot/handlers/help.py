import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.utils.consts import SUPPORT_CENTER, WRITE_QUESTION, EXPECT_RESPONSE
from bot.settings import get_settings
from bot.keyboards.go_to_menu import get_back_to_menu_keyboard
from bot.keyboards.support import get_support_keyboard

settings = get_settings()
SUPPORT_CHAT_ID = settings.bot_settings.support_chat_id

message_mapping = {}

class SupportState(StatesGroup):
    waiting_for_support_message = State()

help_router = Router(name='help_router')

@help_router.message(Command('help'))
@help_router.callback_query(F.data == 'support')
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

@help_router.callback_query(F.data == 'write_to_support')
async def write_to_support(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SupportState.waiting_for_support_message)
    
    await callback.message.edit_text(
        text=WRITE_QUESTION,
        parse_mode='HTML',
        reply_markup=get_back_to_menu_keyboard()
    )
    await callback.answer()

@help_router.message(StateFilter(SupportState.waiting_for_support_message), F.chat.type == 'private')
@help_router.message(StateFilter(SupportState.waiting_for_support_message), F.chat.type == 'private')
async def forward_to_support(message: Message, state: FSMContext):
    try:
        await state.clear()
        
        user_info = (
            f'👤 <b>Сообщение от пользователя:</b>\n'
            f'🆔 ID: <code>{message.from_user.id}</code>\n'
            f'👤 Username: @{message.from_user.username or "N/A"}\n'
        )
        
        if message.content_type == 'text':
            full_text = (user_info + f'💬 Сообщение:\n{message.text}\n\n' + 
                         f'📝 Ответьте на это сообщение, чтобы отправить ответ пользователю')
            await message.bot.send_message(
                chat_id=SUPPORT_CHAT_ID,
                text=full_text,
                parse_mode='HTML'
            )
        else:
            caption = user_info
            if message.caption:
                caption += f'💬 Подпись:\n{message.caption}\n\n'
            caption += f'📝 Ответьте на это сообщение, чтобы отправить ответ пользователю'
            
            if message.content_type == 'photo':
                await message.bot.send_photo(
                    chat_id=SUPPORT_CHAT_ID,
                    photo=message.photo[-1].file_id,
                    caption=caption,
                    parse_mode='HTML'
                )
            elif message.content_type == 'document':
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
        logging.error(f'Error in forward_to_support: {e}')
        await message.answer(
            '❌ Ошибка при отправке сообщения.',
            reply_markup=get_back_to_menu_keyboard()
        )
        
@help_router.message(F.reply_to_message)
async def admin_reply(message: Message):
    try:
        if str(message.chat.id) != str(SUPPORT_CHAT_ID):
            return
        
        user_status = await message.bot.get_chat_member(SUPPORT_CHAT_ID, message.from_user.id)
        if user_status.status not in ['administrator', 'creator']:
            return
        
        replied_message = message.reply_to_message
        
        if not replied_message.from_user.is_bot:
            return
        
        import re
        user_id_match = re.search(r'🆔.*?(\d+)', replied_message.text or '')
        
        if not user_id_match:
            await message.reply('❌ Не удалось найти ID пользователя в сообщении.', parse_mode='HTML')
            return
        
        chat_id = int(user_id_match.group(1))
        answer_text = message.text

        await message.bot.send_message(
            chat_id=chat_id,
            text=f'💬 <b>Ответ от поддержки:</b>\n\n{answer_text}',
            parse_mode='HTML'
        )
        
        await message.reply('✅ Ответ отправлен!')
        
    except Exception as e:
        logging.error(f'Error in admin_reply: {e}')
        await message.reply('❌ Ошибка при отправке ответа.')