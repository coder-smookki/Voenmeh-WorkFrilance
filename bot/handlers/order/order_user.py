from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from bot.utils.consts import (START_ORDER, TEXT_ANALYSIS_ERROR, ERROR_TRY_AGAIN, 
                              MAXIMUM_FILES, ADD_FILES, CANCELING_A_SHIPMENT,
                              SUBMITTED_TO_MODERATION)
from bot.keyboards.back_to_menu import get_back_to_menu_keyboard
from bot.handlers.states import OrderStates, order_data
import uuid
from html import escape
from bot.keyboards.add_file import get_order_files_keyboard, get_order_done_keyboard
from bot.keyboards.order_preview import get_order_preview_keyboard
from bot.keyboards.repeal import get_cancel_keyboard
from bot.settings import ORDER_CHAT_ID
import logging

order_user_router = Router(name='order_user_router')

@order_user_router.callback_query(F.data == 'create_order')
async def read_order_text(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data({'old_files': []})
    await state.set_state(OrderStates.waiting_text)
    
    await callback.message.edit_text(        
        text = START_ORDER,       
        parse_mode = 'HTML',        
        reply_markup = get_back_to_menu_keyboard()
    ) 
    
@order_user_router.message(OrderStates.waiting_text) 
async def text_message_analysis_order(message: Message, state: FSMContext):
    data = await state.get_data()
    old_files = data.get('old_files', [])  
    order_id = data.get('order_id')
    await state.update_data({'temp_text_input': message.text})
    
    if not message.text:
        await message.answer(
            text=TEXT_ANALYSIS_ERROR,
            parse_mode='HTML'
        )
        return
    
    if not order_id:
        order_id = str(uuid.uuid4())
        
    user = message.from_user
    
    order_data[order_id] = {
        'text': message.text, 
        'files': old_files,
        'user_id': user.id,
        'username': user.username or f'id{user.id}',
        'first_name': user.first_name or 'Аноним',
    }
    
    await state.update_data({
        'order_id': order_id
    })
    
    preview_text = ( 
        '✅<b>Описание принято!</b>\n'
        'Проверяй своё описание!\n'
        f'{escape(message.text)}\n\n'
        '📎 <b>Теперь прикрепи дополнительыне файлы, для большей точности!</b>\n'
        '• Документы, фото, архивы\n'
        '• Можно несколько файлов(Но максимум -- 10)\n'
        '• Когда всё отправишь — нажми "✅Готово"'
    )
    
    await message.answer(
        text=preview_text,
        parse_mode='HTML',
        reply_markup=get_order_files_keyboard(order_id)
    )
    
    await state.set_state(OrderStates.waiting_files)

# Добавляем обработчик подтверждения заказа для отправки модератору
@order_user_router.callback_query(OrderStates.waiting_confirmation, F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext, bot: Bot):
    try:
        data = await state.get_data()
        order_id = data['order_id']
        order_info = order_data.get(order_id)

        if not order_info:
            await callback.answer("Данные заказа не найдены!")
            return

        moderator_text = (
            f"🛒 <b>НОВЫЙ ЗАКАЗ</b>\n\n"
            f"<b>От:</b> {order_info['first_name']} (@{order_info['username']})\n"
            f"<b>ID:</b> {order_info['user_id']}\n\n"
            f"<b>Описание заказа:</b>\n{order_info['text']}\n\n"
            f"Проверь и прими решение:"
        )

        moderator_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принять заказ", callback_data=f"accept_order_{order_id}")],
            [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_order_{order_id}")]
        ])

        files = order_info.get('files', [])

        if files:
            first_file = files[0]
            first_file_type = first_file['type']
            first_file_id = first_file['id']

            if first_file_type == 'document':
                message = await bot.send_document(
                    chat_id=ORDER_CHAT_ID,
                    document=first_file_id,
                    caption=moderator_text,
                    parse_mode='HTML',
                    reply_markup=moderator_keyboard
                )
            else:
                message = await bot.send_photo(
                    chat_id=ORDER_CHAT_ID,
                    photo=first_file_id,
                    caption=moderator_text,
                    parse_mode='HTML',
                    reply_markup=moderator_keyboard
                )

            for i, file_info in enumerate(files[1:], 2):
                file_type = file_info['type']
                file_id = file_info['id']
                try:
                    if file_type == 'document':
                        await bot.send_document(
                            chat_id=ORDER_CHAT_ID,
                            document=file_id,
                            caption=f"📄 Файл {i} к заказу",
                            reply_to_message_id=message.message_id
                        )
                    else:
                        await bot.send_photo(
                            chat_id=ORDER_CHAT_ID,
                            photo=file_id,
                            caption=f"🖼️ Изображение {i} к заказу",
                            reply_to_message_id=message.message_id
                        )
                except Exception as e:
                    logging.error(f"Error sending additional file: {e}")

        else:
            message = await bot.send_message(
                chat_id=ORDER_CHAT_ID,
                text=moderator_text,
                parse_mode='HTML',
                reply_markup=moderator_keyboard 
            )

        await callback.message.edit_text(
            text=SUBMITTED_TO_MODERATION,
            parse_mode='HTML',
            reply_markup=get_back_to_menu_keyboard()
        )

    except Exception as e:
        logging.error(f"Error confirming order: {e}")

        await callback.message.edit_text(
            text=ERROR_TRY_AGAIN,
            parse_mode='HTML',
            reply_markup=get_back_to_menu_keyboard()
        )

@order_user_router.callback_query(F.data == "edit_order_description")
async def edit_order_text_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data.get('order_id') 
    old_text = data.get('temp_text_input', '')
    
    old_files = []
    if order_id and order_id in order_data:
        old_files = order_data[order_id].get('files', [])
    
    await callback.message.answer(
        "✏️ <b>Редактирование описания</b>\n\n"
        f"Текущий текст:\n<code>{escape(old_text)}</code>\n\n"
        "Пришли новый текст:",
        parse_mode='HTML',
        reply_markup=get_cancel_keyboard()
    )
    
    await state.update_data({'old_files': old_files})
    await state.set_state(OrderStates.waiting_text)
    await callback.answer()

@order_user_router.callback_query(F.data == "more_files_done")
async def more_files_done_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data.get('order_id')
    
    await show_order_preview(
        callback.message,
        order_id,
        state,
        "📝 <b>Заказ обновлен:</b>"
    )
    await state.set_state(OrderStates.waiting_confirmation)
    await callback.answer("✅ Дополнительные файлы добавлены!")

@order_user_router.callback_query(F.data == "cancel_more_files")
async def cancel_more_files_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data.get('order_id')
    
    await show_order_preview(
        callback.message,
        order_id,
        state,
        "📝 <b>Возврат к редактированию:</b>"
    )
    await state.set_state(OrderStates.waiting_confirmation)
    await callback.answer("❌ Добавление файлов отменено")

@order_user_router.callback_query(OrderStates.waiting_confirmation, F.data == "add_more_files")
async def add_more_order_files(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data.get('order_id')
    await callback.message.answer(
        text = ADD_FILES,
        parse_mode='HTML',
        reply_markup=get_order_files_keyboard(order_id)
    )
    await state.set_state(OrderStates.waiting_files)
    await callback.answer()

@order_user_router.callback_query(F.data == "cancel_order")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data.get('order_id')
    
    if order_id and order_id in order_data:
        del order_data[order_id]
    
    await state.clear()
    await callback.message.edit_text(
        text = CANCELING_A_SHIPMENT,
        parse_mode='HTML',
        reply_markup=get_back_to_menu_keyboard() 
    )
    await callback.answer()

@order_user_router.callback_query(F.data == "cancel_current_action")
async def cancel_current_action_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data.get('order_id')
    
    await show_order_preview(
        callback.message,
        order_id,
        state,
        "📝 <b>Редактирование отменено:</b>"
    )
    await state.set_state(OrderStates.waiting_confirmation)
    await callback.answer("✏️ Редактирование отменено")

@order_user_router.callback_query(F.data == "go_to_menu")
async def go_to_menu_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data.get('order_id')
    
    if order_id and order_id in order_data:
        del order_data[order_id]
    
    await state.clear()
    await callback.message.edit_text(
        "❌ <b>Отправка отменена</b>\n\nВозврат в главное меню...",
        parse_mode='HTML',
        reply_markup=get_back_to_menu_keyboard()
    )
    await callback.answer()

@order_user_router.message(OrderStates.waiting_files, F.document | F.photo)  
async def process_order_files(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get('order_id')
    
    if not order_id or order_id not in order_data:
        await message.answer(
            text = ERROR_TRY_AGAIN,
            parse_mode = 'HTML'
        )
        await state.clear()
        return

    files = order_data[order_id].get('files', [])
    if len(files) >= 10:
        await message.answer(
            text = MAXIMUM_FILES,
            parse_mode='HTML')
        return

    file_type = None
    file_id = None

    if message.document:
        file_type = 'document'
        file_id = message.document.file_id
        file_name = message.document.file_name or 'Без названия'
    elif message.photo:
        file_type = 'photo' 
        file_id = message.photo[-1].file_id 
        file_name = 'Изображение'
        
    files.append({
        'type': file_type,
        'id': file_id,
        'name': file_name,
    })

    order_data[order_id]['files'] = files

    file_count = len(files)
    file_word = 'файлов' if file_count % 10 not in [2, 3, 4] or file_count % 100 in [12, 13, 14] else 'файла'  
    
    text_done = (
        f'✅ <b>Добавлено!</b>\n'
        f'📦 <b>Файл:</b> <code>{escape(file_name)}</code>\n'
        f'📊 <b>Всего:</b> {file_count} {file_word}\n\n'
        f'Можно отправить ещё или нажать <b>"✅Готово "</b>' )
    
    await message.answer(
        text = text_done,
        parse_mode = 'HTML',
        reply_markup = get_order_done_keyboard(order_id)
    )
    
@order_user_router.callback_query(F.data.startswith('order_done:'))  # Для кнопки 'Готово'
@order_user_router.callback_query(F.data.startswith('order_nofiles:'))  # Для кнопки 'Без файлов'
async def handle_order_finalize(callback: CallbackQuery, state: FSMContext):
    try:
        order_id = callback.data.split(':')[1]  
    except IndexError:
        await callback.answer('❌ Ошибка: неверный формат данных')
        return

    if order_id not in order_data:
        await callback.answer(
            text = ERROR_TRY_AGAIN,
            parse_mode = 'HTML'
        )
        await state.clear()
        return

    if callback.data.startswith('order_nofiles:'):
        order_data[order_id]['no_files'] = True
        await callback.answer('✅ Принято: заказ без файлов')
    else:
        await callback.answer('✅ Файлы добавлены!')

    await show_order_preview(
        callback.message, 
        order_id, 
        state, 
        '📝 <b>Проверь заказ:</b>'
    )
    await state.set_state(OrderStates.waiting_confirmation)
    
async def show_order_preview(
    message: Message, 
    order_id: str, 
    state: FSMContext,
    title: str = '📝 <b>Текущий заказ:</b>'
):
    if order_id not in order_data:
        await message.answer(
            text=ERROR_TRY_AGAIN,
            parse_mode='HTML'
        )
        await state.clear()
        return

    order_info = order_data[order_id]
    order_text = escape(order_info.get('text', 'Текст отсутствует'))
    
    response_text = (
        f'{title}\n\n'
        f'{order_text}\n\n'
    )

    files = order_info.get('files', [])
    if files:
        file_count = len(files)
        doc_count = sum(1 for f in files if f.get('type') == 'document')
        photo_count = sum(1 for f in files if f.get('type') == 'photo')
        
        response_text += f'📎 <b>Прикреплено файлов:</b> {file_count}\n'
        if doc_count > 0:
            response_text += f'   • Документов: {doc_count}\n'
        if photo_count > 0:
            response_text += f'   • Изображений: {photo_count}\n'
    else:
        response_text += '📎 <b>Файлы:</b> не прикреплены\n'

    response_text += '\n<b>Всё верно? Отправляем заказ?</b>'

    await message.answer(
        response_text,
        parse_mode='HTML',
        reply_markup=get_order_preview_keyboard()
    )