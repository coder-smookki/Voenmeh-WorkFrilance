from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InputMediaPhoto, InputMediaVideo
from bot.utils.consts import ( DESIGN_EXAMPLE, TEXT_ANALYSIS_ERROR, INCORRECT_TEXT_FORMAT, 
                              EMPTY_FIELDS, ERROR_TRY_AGAIN, MAXIMUM_FILES, ADD_FILES, CANCELING_A_SHIPMENT, 
                              SUBMITTED_TO_MODERATION, get_suggestion_preview_text, get_suggestion_edit_text, get_text_done,
                              get_response_text, get_new_suggeston_text)
from bot.keyboards.go_to_menu import get_back_to_menu_keyboard
from bot.utils.states import SubmissionStates, submission_data, RobustUploadManager
import uuid
from bot.keyboards.add_file import get_suggestion_files_keyboard, get_suggestion_done_keyboard
from bot.keyboards.submission_preview import get_submission_preview_keyboard, get_moderator_keyboard, get_cancel_current_action
from bot.settings import get_settings
import logging
from html import escape
import asyncio

settings = get_settings()
MODERATOR_CHAT_ID = settings.bot_settings.moder_chat_id

upload_manager = RobustUploadManager()

suggestion_user_router = Router(name='suggestion_user_router')
    
@suggestion_user_router.callback_query(F.data == 'suggestion')
async def read_submission_text(callback: CallbackQuery, state: FSMContext):
    
    await callback.answer()

    async with upload_manager.lock:
        upload_manager.pending_uploads.clear()
        upload_manager.next_expected = 1
    
    await state.update_data({
        'old_files' : [],
        'file_counter' : 0,
        'processed_files' : []})
    await state.set_state(SubmissionStates.waiting_text)
    
    await callback.message.edit_text(        
        text = DESIGN_EXAMPLE,       
        parse_mode = 'HTML',         
        reply_markup = get_back_to_menu_keyboard()
    )
    
@suggestion_user_router.message(SubmissionStates.waiting_text)
async def text_message_analysis_suggestion(message: Message, state: FSMContext):
    
    data = await state.get_data()
    old_files = data.get('old_files', [])  
    submission_id = data.get('submission_id')
    await state.update_data({'temp_text_input': message.text})
    
    if not message.text:
        await message.answer(
            text = TEXT_ANALYSIS_ERROR,
            parse_mode = 'HTML'
        )
        return
    
    lines = [line.strip() for line in message.text.split('\n') if line.strip()]
    
    if len(lines) < 4:
        await message.answer(
            text = INCORRECT_TEXT_FORMAT,
            parse_mode = 'HTML'
        )
        return
    subject, lvl_education, course, work_name  = lines[0], lines[1], lines[2], lines[3]
    
    if not all([subject, lvl_education, course, work_name]):
        await message.answer(
            text = EMPTY_FIELDS,
            parse_mode = 'HTML'
        )
        return
    
    if not submission_id:
        submission_id = str(uuid.uuid4())
        
    user = message.from_user
    
    submission_data[submission_id] = {
        'text': message.text,
        'files': old_files,
        'user_id': user.id,
        'username': user.username or f'id{user.id}',
        'first_name': user.first_name or 'Аноним',
        'subject': subject,
        'lvl_education': lvl_education, 
        'course': course,
        'work_name': work_name,
    }
    
    await state.update_data({
        'submission_id' : submission_id,
        'current_submission_lines': lines
    })
    
    await message.answer(
        text = get_suggestion_preview_text(subject, lvl_education, course, work_name),
        parse_mode='HTML',
        reply_markup = get_suggestion_files_keyboard(submission_id)
    )
    
    await state.set_state(SubmissionStates.waiting_files)

# Тута кнопки(отмена, редактирвоание и т.д.), после кнопок пойдёт как раз обработка файлов и т.д.
@suggestion_user_router.callback_query(SubmissionStates.waiting_confirmation, F.data == "confirm_submission")
async def confirm_submission(callback: CallbackQuery, state: FSMContext, bot: Bot):
    try:
        data = await state.get_data()
        submission_id = data['submission_id']
        file_counter = data.get('file_counter', 0)
        submission_info = submission_data.get(submission_id)

        if not submission_info:
            await callback.answer("Данные отправки не найдены!")
            return

        success = await upload_manager.wait_for_order(file_counter + 1, timeout=5.0)
        
        if not success:
            logging.warning(f"Timeout waiting for file processing for submission {submission_id}")

        async with upload_manager.lock:
            upload_manager.pending_uploads.clear()
            upload_manager.next_expected = 1
            remaining_files = await upload_manager._check_sequential_uploads()
            for msg_data in remaining_files:
                await callback.message.answer(
                    text=msg_data['text'],
                    parse_mode='HTML'
                )
            await asyncio.sleep(0.1)  

        moderator_text = get_new_suggeston_text(submission_info)
        files = submission_info.get('files', [])
        sorted_files = sorted(files, key=lambda x: x.get('order', 0))

        description_message = await bot.send_message(
            chat_id=MODERATOR_CHAT_ID,
            text=moderator_text,
            parse_mode='HTML',
            reply_markup=get_moderator_keyboard(submission_id)
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
                            caption=f"🖼️ Изображение {i}"
                        ))
                    elif file_info['type'] == 'video':
                        media_group.append(InputMediaVideo(
                            media=file_info['id'],
                            caption=f"🎥 Видео {i}"
                        ))
                
                await bot.send_media_group(
                    chat_id=MODERATOR_CHAT_ID,
                    media=media_group,
                    reply_to_message_id=message_to_reply_to
                )
            except Exception as e:
                logging.error(f"Error sending media group: {e}")
                for i, file_info in enumerate(media_group_files, 1):
                    try:
                        if file_info['type'] == 'photo':
                            await bot.send_photo(
                                chat_id=MODERATOR_CHAT_ID,
                                photo=file_info['id'],
                                caption=f"🖼️ Изображение {i} к работе",
                                reply_to_message_id=message_to_reply_to
                            )
                        elif file_info['type'] == 'video':
                            await bot.send_video(
                                chat_id=MODERATOR_CHAT_ID,
                                video=file_info['id'],
                                caption=f"🎥 Видео {i} к работе",
                                reply_to_message_id=message_to_reply_to
                            )
                    except Exception as e:
                        logging.error(f"Error sending media file: {e}")

        for i, file_info in enumerate(single_files, 1):
            try:
                if file_info['type'] == 'document':
                    await bot.send_document(
                        chat_id=MODERATOR_CHAT_ID,
                        document=file_info['id'],
                        caption=f"📄 Документ {i} к работе",
                        reply_to_message_id=message_to_reply_to
                    )
                elif file_info['type'] == 'audio':
                    await bot.send_audio(
                        chat_id=MODERATOR_CHAT_ID,
                        audio=file_info['id'],
                        caption=f"🎵 Аудио {i} к работе",
                        reply_to_message_id=message_to_reply_to
                    )
            except Exception as e:
                logging.error(f"Error sending single file: {e}")

        await callback.message.edit_text(
            text=SUBMITTED_TO_MODERATION,
            parse_mode='HTML',
            reply_markup=get_back_to_menu_keyboard()
        )

    except Exception as e:
        logging.error(f"Error confirming submission: {e}")

        await callback.message.edit_text(
            text=ERROR_TRY_AGAIN,
            parse_mode='HTML',
            reply_markup=get_back_to_menu_keyboard()
        )

@suggestion_user_router.callback_query(F.data == "edit_sub_description")
async def edit_submission_text_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    submission_id = data.get('submission_id') 
    old_text = data.get('temp_text_input', '')
    
    old_files = []
    if submission_id and submission_id in submission_data:
        old_files = submission_data[submission_id].get('files', [])
    
    await callback.message.answer(
        text = get_suggestion_edit_text(old_text),
        parse_mode = 'HTML',
        reply_markup= get_cancel_current_action()
    )
    
    await state.update_data({'old_files': old_files})
    await state.set_state(SubmissionStates.waiting_text)
    await callback.answer()

@suggestion_user_router.callback_query(F.data == "more_files_done")
async def more_files_done_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    submission_id = data.get('submission_id')
    
    await show_submission_preview(
        callback.message,
        submission_id,
        state,
        "📝 <b>Работа обновлена:</b>"
    )
    await state.set_state(SubmissionStates.waiting_confirmation)
    await callback.answer("✅ Дополнительные файлы добавлены!")

@suggestion_user_router.callback_query(F.data == "cancel_more_files")
async def cancel_more_files_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    submission_id = data.get('submission_id')
    
    await show_submission_preview(
        callback.message,
        submission_id,
        state,
        "📝 <b>Возврат к редактированию:</b>"
    )
    await state.set_state(SubmissionStates.waiting_confirmation)
    await callback.answer("❌ Добавление файлов отменено")

@suggestion_user_router.callback_query(SubmissionStates.waiting_confirmation, F.data == "add_more_files")
async def add_more_submission_files(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    submission_id = data.get('submission_id')
    await callback.message.answer(
        text = ADD_FILES,
        parse_mode='HTML',
        reply_markup=get_suggestion_files_keyboard(submission_id)
    )
    await state.set_state(SubmissionStates.waiting_files)
    await callback.answer()

@suggestion_user_router.callback_query(F.data == "cancel_submission")
async def cancel_submission(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    submission_id = data.get('submission_id')
    
    if submission_id and submission_id in submission_data:
        del submission_data[submission_id]
    
    async with upload_manager.lock:
        upload_manager.pending_uploads.clear()
        upload_manager.next_expected = 1
    
    await state.clear()
    await callback.message.edit_text(
        text = CANCELING_A_SHIPMENT,
        parse_mode='HTML',
        reply_markup=get_back_to_menu_keyboard()
    )
    await callback.answer()

@suggestion_user_router.callback_query(F.data == "cancel_editing")
async def cancel_current_action_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    submission_id = data.get('submission_id')
    
    await show_submission_preview(
        callback.message,
        submission_id,
        state,
        "📝 <b>Редактирование отменено:</b>"
    )
    await state.set_state(SubmissionStates.waiting_confirmation)
    await callback.answer("✏️ Редактирование отменено")
 
@suggestion_user_router.message(SubmissionStates.waiting_files, F.document | F.photo | F.audio | F.video)  
async def process_submission_files(message: Message, state: FSMContext):
    data = await state.get_data()
    submission_id = data.get('submission_id')
    user_id = message.from_user.id
    
    if not submission_id or submission_id not in submission_data:
        await message.answer(
            text = ERROR_TRY_AGAIN,
            parse_mode = 'HTML'
        )
        await state.clear()
        return

    files = submission_data[submission_id].get('files', [])
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
    submission_data[submission_id]['files'] = files

    expected_order = current_counter
    timeout = 10.0
    start_time = asyncio.get_event_loop().time()
    
    while asyncio.get_event_loop().time() - start_time < timeout:
        async with upload_manager.lock:
            if upload_manager.next_expected >= expected_order:
                break
        await asyncio.sleep(0.1)
    
    await message.answer(
        text=get_text_done(file_name, current_counter, len(files)),
        parse_mode='HTML',
        reply_markup=get_suggestion_done_keyboard(submission_id)
    )
    
    message_data = {
        'chat_id': message.chat.id,
        'text': get_text_done(file_name, current_counter, len(files)),
        'order': current_counter
    }
    
    await upload_manager.add_upload(current_counter, message_data)

@suggestion_user_router.callback_query(F.data.startswith('sub_done:'))  # Для кнопки 'Готово'
@suggestion_user_router.callback_query(F.data.startswith('sub_nofiles:'))  # Для кнопки 'Без файлов'
async def handle_submission_finalize(callback: CallbackQuery, state: FSMContext):
    try:
        submission_id = callback.data.split(':')[1]  
    except IndexError:
        await callback.answer('❌ Ошибка: неверный формат данных')
        return

    if submission_id not in submission_data:
        await callback.answer(
            text = ERROR_TRY_AGAIN,
            parse_mode = 'HTML'
        )
        await state.clear()
        return

    if callback.data.startswith('sub_nofiles:'):
        submission_data[submission_id]['files'] = []
        submission_data[submission_id]['no_files'] = True
        await state.update_data({'file_counter': 0})
        await callback.answer('✅ Принято: работа без файлов')
    else:
        submission_data[submission_id]['no_files'] = False
        await callback.answer('✅ Файлы добавлены!')

    await show_submission_preview(
        callback.message, 
        submission_id, 
        state, 
        '📝 <b>Проверь работу:</b>'
    )
    await state.set_state(SubmissionStates.waiting_confirmation)

async def show_submission_preview(
    message: Message, 
    submission_id: str, 
    state: FSMContext,
    title: str = '📝 <b>Проверь работу:</b>'
):
    if submission_id not in submission_data:
        await message.answer(
            text = ERROR_TRY_AGAIN,
            parse_mode = 'HTML'
        )
        await state.clear()
        return

    submission_info = submission_data[submission_id]
    
    subject = escape(submission_info.get('subject', 'Не указано'))
    lvl_education = escape(submission_info.get('lvl_education', 'Не указано'))
    course = escape(submission_info.get('course', 'Не указано'))
    work_name = escape(submission_info.get('work_name', 'Не указано'))
    
    response_text = get_response_text(title, subject, lvl_education, course, work_name)

    no_files = submission_info.get('no_files', False)
    files = submission_info.get('files', [])

    sorted_files = sorted(files, key=lambda x: x.get('order', 0))
    
    if no_files:
        response_text += '📎 <b>Файлы:</b> работа отправлена без файлов\n'
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

    response_text += '\n<b>Всё верно? Отправляем на проверку?</b>'

    await message.answer(
        response_text,
        parse_mode ='HTML',
        reply_markup = get_submission_preview_keyboard()
    )
    
def get_order_number():
    return int(uuid.uuid4().int % 1000000)

async def wait_for_uploads_completion(expected_count: int, timeout: float = 5.0):
    start_time = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start_time < timeout:
        async with upload_manager.lock:
            if upload_manager.next_expected > expected_count:
                return True
        await asyncio.sleep(0.1)
    return False
