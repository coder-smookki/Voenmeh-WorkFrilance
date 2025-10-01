import logging
import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.utils.consts import (
    SUPPORT_CENTER,
    WRITE_QUESTION,
    EXPECT_RESPONSE,
    get_support_message_text,
    SUPPORT_ANSWER_PROMPT,
    MESSAGE_SENT_ERROR,
    USER_ID_NOT_FOUND,
    ANSWER_SENT_SUCCESS,
    ANSWER_SENT_ERROR
)
from bot.settings import get_settings
from bot.keyboards.go_to_menu import get_back_to_menu_keyboard, get_cancel_submission_keyboard
from bot.keyboards.support import get_support_keyboard

settings = get_settings()
SUPPORT_CHAT_ID = settings.bot_settings.support_chat_id
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MB
MAX_VIDEO_SIZE = 400 * 1024 * 1024  # 400 MB

class SupportState(StatesGroup):
    waiting_for_support_message = State()

help_router = Router(name='help_router')


@help_router.message(Command('help'))
@help_router.callback_query(F.data == 'support')
async def help_command(message: Message | CallbackQuery, state: FSMContext):
    """Показывает главное меню поддержки."""
    await state.clear()
    
    if isinstance(message, CallbackQuery):
        await message.answer()
        message_obj = message.message
        await message_obj.edit_text(
            text=SUPPORT_CENTER,
            parse_mode='HTML',
            reply_markup=get_support_keyboard()
        )
    else:
        await message.answer(
            text=SUPPORT_CENTER,
            parse_mode='HTML',
            reply_markup=get_support_keyboard()
        )


@help_router.callback_query(F.data == 'write_to_support')
async def write_to_support(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс отправки сообщения в поддержку."""
    await state.set_state(SupportState.waiting_for_support_message)
    
    await callback.message.edit_text(
        text=WRITE_QUESTION,
        parse_mode='HTML',
        reply_markup=get_cancel_submission_keyboard()
    )
    await callback.answer()


@help_router.message(StateFilter(SupportState.waiting_for_support_message), F.chat.type == 'private')
async def forward_to_support(message: Message, state: FSMContext):
    """Пересылает сообщение пользователя в чат поддержки."""
    try:
        await state.clear()
        
        user_info_text = get_support_message_text(message.from_user)
        
        # Проверка размера файлов
        if message.document and message.document.file_size > MAX_FILE_SIZE:
            await message.answer("❌ Размер файла превышает лимит 30 МБ")
            return
        
        if message.video and message.video.file_size > MAX_VIDEO_SIZE:
            await message.answer("❌ Размер видео превышает лимит в 60 МБ")
            return
        
        # Формирование полного текста/подписи
        caption = user_info_text
        if message.caption:
            caption += f'\n💬 Подпись:\n{message.caption}\n'
        caption += f'\n{SUPPORT_ANSWER_PROMPT}'
        
        # Отправка сообщения в зависимости от типа контента
        if message.photo:
            await message.bot.send_photo(
                chat_id=SUPPORT_CHAT_ID,
                photo=message.photo[-1].file_id,
                caption=caption,
                parse_mode='HTML'
            )
        elif message.document:
            await message.bot.send_document(
                chat_id=SUPPORT_CHAT_ID,
                document=message.document.file_id,
                caption=caption,
                parse_mode='HTML'
            )
        elif message.video:
            await message.bot.send_video(
                chat_id=SUPPORT_CHAT_ID,
                video=message.video.file_id,
                caption=caption,
                parse_mode='HTML'
            )
        elif message.text:
            full_text = user_info_text + f'\n💬 Сообщение:\n{message.text}\n\n{SUPPORT_ANSWER_PROMPT}'
            await message.bot.send_message(
                chat_id=SUPPORT_CHAT_ID,
                text=full_text,
                parse_mode='HTML'
            )
        else:
            # Для других типов контента (аудио, голосовые, стикеры и т.д.)
            await message.copy_to(
                chat_id=SUPPORT_CHAT_ID,
                caption=caption,
                parse_mode='HTML'
            )
        
        await message.answer(
            text=EXPECT_RESPONSE,
            parse_mode='HTML',
            reply_markup=get_back_to_menu_keyboard()
        )
        
    except Exception as e:
        logging.error(f'Error in forward_to_support: {e}', exc_info=True)
        await message.answer(
            text=MESSAGE_SENT_ERROR,
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
        
        # Ищем ID в тексте или подписи (для медиафайлов)
        message_content = replied_message.text or replied_message.caption or ''
        user_id_match = re.search(r'🆔.*?(\d+)', message_content)
        
        if not user_id_match:
            await message.reply('❌ Не удалось найти ID пользователя в сообщении.', parse_mode='HTML')
            return
        
        target_user_id = int(user_id_match.group(1))
        
        # Проверка размера файлов
        if message.document and message.document.file_size > MAX_FILE_SIZE:
            await message.reply("❌ Размер файла превышает лимит в 200 МБ")
            return
        
        if message.video and message.video.file_size > MAX_VIDEO_SIZE:
            await message.reply("❌ Размер видео превышает лимит в 400 МБ")
            return
        
        # Формирование ответа
        answer_prefix = '💬 <b>Ответ от поддержки:</b>\n\n'
        
        # Отправка ответа пользователю в зависимости от типа контента
        if message.photo:
            caption = answer_prefix
            if message.caption:
                caption += message.caption
            await message.bot.send_photo(
                chat_id=target_user_id,
                photo=message.photo[-1].file_id,
                caption=caption,
                parse_mode='HTML',
                reply_markup=get_back_to_menu_keyboard()
            )
        elif message.document:
            caption = answer_prefix
            if message.caption:
                caption += message.caption
            await message.bot.send_document(
                chat_id=target_user_id,
                document=message.document.file_id,
                caption=caption,
                parse_mode='HTML',
                reply_markup=get_back_to_menu_keyboard()
            )
        elif message.video:
            caption = answer_prefix
            if message.caption:
                caption += message.caption
            await message.bot.send_video(
                chat_id=target_user_id,
                video=message.video.file_id,
                caption=caption,
                parse_mode='HTML',
                reply_markup=get_back_to_menu_keyboard()
            )
        elif message.text:
            await message.bot.send_message(
                chat_id=target_user_id,
                text=f'{answer_prefix}{message.text}',
                parse_mode='HTML',
                reply_markup=get_back_to_menu_keyboard()
            )
        else:
            # Для других типов контента
            await message.copy_to(
                chat_id=target_user_id,
                caption=answer_prefix + (message.caption or ''),
                parse_mode='HTML',
                reply_markup=get_back_to_menu_keyboard()
            )
        
        await message.reply(ANSWER_SENT_SUCCESS)
        
    except Exception as e:
        logging.error(f'Error in admin_reply: {e}', exc_info=True)
        await message.reply(ANSWER_SENT_ERROR)