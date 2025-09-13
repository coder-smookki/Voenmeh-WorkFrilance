from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InputMediaVideo, InputMediaPhoto
from bot.utils.consts import (START_ORDER, TEXT_ANALYSIS_ERROR, ERROR_TRY_AGAIN, 
                              MAXIMUM_FILES, ADD_FILES, CANCELING_A_SHIPMENT,
                              SUBMITTED_TO_MODERATION, SUBMITTED_TO_EXECUTOR, 
                              get_executor_text, get_text_done, get_edit_order_text, get_preview_text)
from bot.keyboards.go_to_menu import get_back_to_menu_keyboard
from bot.utils.states import OrderStates, order_data, order_upload_manager
import uuid
from html import escape
from bot.keyboards.add_file import get_order_files_keyboard, get_order_done_keyboard
from bot.keyboards.order_preview import get_order_preview_keyboard, get_cancel_current_action, get_executor_keyboard
from bot.settings import get_settings
import logging
import asyncio

settings = get_settings()
ORDER_CHAT_ID = settings.bot_settings.order_chat_id

order_user_router = Router(name = 'order_user_router')

@order_user_router.callback_query(F.data == 'create_order')
async def read_order_text(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    async with order_upload_manager.lock:
        order_upload_manager.pending_uploads.clear()
        order_upload_manager.next_expected = 1
    
    await state.update_data({
        'old_files': [],
        'file_counter': 0
    })
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
    
    preview_text = get_preview_text(message)
    
    await message.answer(
        text = preview_text,
        parse_mode = 'HTML',
        reply_markup = get_order_files_keyboard(order_id)
    )
    
    await state.set_state(OrderStates.waiting_files)

@order_user_router.callback_query(OrderStates.waiting_confirmation, F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext, bot: Bot):
    try:
        data = await state.get_data()
        order_id = data['order_id']
        file_counter = data.get('file_counter', 0)
        order_info = order_data.get(order_id)

        if not order_info:
            await callback.answer("Данные отправки не найдены!")
            return

        success = await order_upload_manager.wait_for_order(file_counter + 1, timeout=5.0)
        
        if not success:
            logging.warning(f"Timeout waiting for file processing for order {order_id}")

        async with order_upload_manager.lock:
            order_upload_manager.pending_uploads.clear()
            order_upload_manager.next_expected = 1
            remaining_files = await order_upload_manager._check_sequential_uploads()
            for msg_data in remaining_files:
                await callback.message.answer(
                    text=msg_data['text'],
                    parse_mode='HTML'
                )
            await asyncio.sleep(0.1)  

        moderator_text = get_executor_text(order_info)
        files = order_info.get('files', [])
        sorted_files = sorted(files, key=lambda x: x.get('order', 0))

        description_message = await bot.send_message(
            chat_id=ORDER_CHAT_ID,
            text=moderator_text,
            parse_mode='HTML',
            reply_markup=get_executor_keyboard(order_id)
        )
        message_to_reply_to = description_message.message_id

        media_group_files = []
        single_files = []

        for file_info in sorted_files:
            if file_info['type'] in ['photo', 'video']:
                media_group_files.append(file_info)
            else:
                single_files.append(file_info)

        if media_group_files:
            try:
                media_group = []
                for i, file_info in enumerate(media_group_files, 1):
                    if file_info['type'] == 'photo':
                        media_group.append(InputMediaPhoto(
                            media=file_info['id'],
                            caption=f"🖼️ Изображение {i} к заказу"
                        ))
                    elif file_info['type'] == 'video':
                        media_group.append(InputMediaVideo(
                            media=file_info['id'],
                            caption=f"🎥 Видео {i} к заказу"
                        ))
                
                await bot.send_media_group(
                    chat_id=ORDER_CHAT_ID,
                    media=media_group,
                    reply_to_message_id=message_to_reply_to
                )
            except Exception as e:
                logging.error(f"Error sending media group: {e}")
                for i, file_info in enumerate(media_group_files, 1):
                    try:
                        if file_info['type'] == 'photo':
                            await bot.send_photo(
                                chat_id=ORDER_CHAT_ID,
                                photo=file_info['id'],
                                caption=f"🖼️ Изображение {i} к заказу",
                                reply_to_message_id=message_to_reply_to
                            )
                        elif file_info['type'] == 'video':
                            await bot.send_video(
                                chat_id=ORDER_CHAT_ID,
                                video=file_info['id'],
                                caption=f"🎥 Видео {i} к заказу",
                                reply_to_message_id=message_to_reply_to
                            )
                    except Exception as e:
                        logging.error(f"Error sending media file: {e}")

        for i, file_info in enumerate(single_files, 1):
            try:
                if file_info['type'] == 'document':
                    await bot.send_document(
                        chat_id=ORDER_CHAT_ID,
                        document=file_info['id'],
                        caption=f"📄 Документ {i} к заказу",
                        reply_to_message_id=message_to_reply_to
                    )
                elif file_info['type'] == 'audio':
                    await bot.send_audio(
                        chat_id=ORDER_CHAT_ID,
                        audio=file_info['id'],
                        caption=f"🎵 Аудио {i} к заказу",
                        reply_to_message_id=message_to_reply_to
                    )
            except Exception as e:
                logging.error(f"Error sending single file: {e}")

        await callback.message.edit_text(
            text=SUBMITTED_TO_EXECUTOR,
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
        text = get_edit_order_text(old_text),
        parse_mode = 'HTML',
        reply_markup = get_cancel_current_action()
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
        '📝 <b>Заказ обновлен:</b>'
    )
    await state.set_state(OrderStates.waiting_confirmation)
    await callback.answer('✅ Дополнительные файлы добавлены!')

@order_user_router.callback_query(F.data == "cancel_more_files")
async def cancel_more_files_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data.get('order_id')
    
    await show_order_preview(
        callback.message,
        order_id,
        state,
        '📝 <b>Возврат к редактированию:</b>'
    )
    await state.set_state(OrderStates.waiting_confirmation)
    await callback.answer('❌ Добавление файлов отменено')

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
    
    async with order_upload_manager.lock:
        order_upload_manager.pending_uploads.clear()
        order_upload_manager.next_expected = 1
    
    await state.clear()
    await callback.message.edit_text(
        text = CANCELING_A_SHIPMENT,
        parse_mode='HTML',
        reply_markup=get_back_to_menu_keyboard() 
    )
    await callback.answer()

@order_user_router.callback_query(F.data == 'cancel_order_editing')
async def cancel_current_action_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data.get('order_id')
    
    await show_order_preview(
        callback.message,
        order_id,
        state,
        '📝 <b>Редактирование отменено:</b>'
    )
    await state.set_state(OrderStates.waiting_confirmation)
    await callback.answer('✏️ Редактирование отменено')

@order_user_router.message(OrderStates.waiting_files, F.document | F.photo | F.audio | F.video)  
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
    file_name = 'Файл'

    if message.document:
        file_type = 'document'
        file_id = message.document.file_id
        file_name = message.document.file_name or 'Документ'
    elif message.photo:
        file_type = 'photo' 
        file_id = message.photo[-1].file_id 
        file_name = 'Изображение'
    elif message.audio:
        file_type = 'audio'
        file_id = message.audio.file_id
        file_name = message.audio.file_name or 'Аудио'
    elif message.video:
        file_type = 'video'
        file_id = message.video.file_id
        file_name = message.video.file_name or 'Видео'
    
    current_counter = data.get('file_counter', 0) + 1
    await state.update_data({'file_counter': current_counter})

    new_file = {
        'type': file_type,
        'id': file_id,
        'name': file_name,
        'order': current_counter
    }
    files.append(new_file)
    order_data[order_id]['files'] = files
    expected_order = current_counter
    
    timeout = 10.0  
    start_time = asyncio.get_event_loop().time()
    
    while asyncio.get_event_loop().time() - start_time < timeout:
        async with order_upload_manager.lock:
            if order_upload_manager.next_expected >= expected_order:
                break
        await asyncio.sleep(0.1)
    
    await message.answer(
        text=get_text_done(file_name, current_counter, len(files)),
        parse_mode='HTML',
        reply_markup=get_order_done_keyboard(order_id)
    )
    
    message_data = {
        'chat_id': message.chat.id,
        'text': get_text_done(file_name, current_counter, len(files)),
        'order': current_counter
    }
    
    await order_upload_manager.add_upload(current_counter, message_data)
    
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
        order_data[order_id]['files'] = []
        order_data[order_id]['no_files'] = True
        await state.update_data({'file_counter': 0})
        await callback.answer('✅ Принято: заказ без файлов')
    else:
        order_data[order_id]['no_files'] = False
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

    no_files = order_info.get('no_files', False)
    files = order_info.get('files', [])
    
    sorted_files = sorted(files, key=lambda x: x.get('order', 0))
    
    if no_files:
        response_text += '📎 <b>Файлы:</b> заказ отправлен без файлов\n'
    elif sorted_files:
        file_count = len(sorted_files)
        doc_count = sum(1 for f in sorted_files if f.get('type') == 'document')
        photo_count = sum(1 for f in sorted_files if f.get('type') == 'photo')
        audio_count = sum(1 for f in sorted_files if f.get('type') == 'audio')
        video_count = sum(1 for f in sorted_files if f.get('type') == 'video')
        
        response_text += f'📎 <b>Прикреплено файлов:</b> {file_count}\n'
        if doc_count > 0:
            response_text += f'   • Документов: {doc_count}\n'
        if photo_count > 0:
            response_text += f'   • Изображений: {photo_count}\n'
        if audio_count > 0:
            response_text += f'   • Аудиофайлов: {audio_count}\n'
        if video_count > 0:
            response_text += f'   • Видеофайлов: {video_count}\n'
        
        response_text += '\n<b>Порядок файлов:</b>\n'
        for i, file_info in enumerate(sorted_files, 1):
            file_type_emoji = {
                'document': '📄',
                'photo': '🖼️',
                'audio': '🎵',
                'video': '🎥'
            }.get(file_info['type'], '📎')
            
            response_text += f'   {i}. {file_type_emoji} {file_info["name"]}\n'
    else:
        response_text += '📎 <b>Файлы:</b> не прикреплены\n'

    response_text += '\n<b>Всё верно? Отправляем заказ?</b>'

    await message.answer(
        response_text,
        parse_mode='HTML',
        reply_markup=get_order_preview_keyboard()
    )