from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from bot.utils.consts import ( DESIGN_EXAMPLE, TEXT_ANALYSIS_ERROR, INCORRECT_TEXT_FORMAT, 
                              EMPTY_FIELDS, ERROR_TRY_AGAIN, MAXIMUM_FILES, ADD_FILES, CANCELING_A_SHIPMENT, 
                              SUBMITTED_TO_MODERATION )
from bot.keyboards.back_to_menu import get_back_to_menu_keyboard
from bot.handlers.states import SubmissionStates
import uuid
from html import escape
from bot.keyboards.add_file import get_files_keyboard
from bot.keyboards.submission_preview import get_submission_preview_keyboard
from bot.keyboards.repeal import get_cancel_keyboard

suggestion_user_router = Router(name='suggestion_user_router')

# Словарь для отправки
submission_data = {}
    
@suggestion_user_router.callback_query(F.data == 'suggestion')
async def read_submission_text(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(SubmissionStates.waiting_text)
    
    await callback.message.edit_text(        
        text = DESIGN_EXAMPLE,       
        parse_mode = 'HTML',        
        reply_markup = get_back_to_menu_keyboard()
    )
    
@suggestion_user_router.message(SubmissionStates.waiting_text)
async def text_message_analysis(message: Message, state: FSMContext):
    
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
    
    return
    subject, course, teacher, work_name = lines[0], lines[1], lines[2], lines[3]
    
    if not all([subject, course, work_name]):
        await message.answer(
            text = EMPTY_FIELDS,
            parse_mode = 'HTML'
        )
        return
    
    submission_id = str(uuid.uuid4())
    user = message.from_user
    
    submission_data[submission_id] = {
        'text': message.text,
        'files': [],
        'user_id': user.id,
        'username': user.username or f'id{user.id}',
        'first_name': user.first_name or 'Аноним',
        'subject': subject,
        'course': course,
        'teacher': teacher, 
        'work_name': work_name,
    }
    
    await state.update_data({
        'submission_id' : submission_id,
        'current_submission_lines': lines
    })
    
    # Из-за того, что тут курсы и т.д. -- его как отдельны текст и константу решил не делать
    preview_text = (
        '✅ <b>Принял!</b> Проверь информацию:\n\n'
        f'<b>Предмет:</b> <code>{escape(subject)}</code>\n'
        f'<b>Курс:</b> <code>{escape(course)}</code>\n'
        f'<b>Преподаватель:</b> <code>{escape(teacher)}</code>\n' 
        f'<b>Работа:</b> <code>{escape(work_name)}</code>\n\n'
        '📎 <b>Теперь прикрепи файлы работы</b>\n'
        '• Документы, фото, архивы\n'
        '• Можно несколько файлов(Но максимум -- 10)\n'
        '• Когда всё отправишь — нажми "✅Готово"'
    )
    
    await message.answer(
        text = preview_text,
        parse_mode='HTML',
        reply_markup = get_files_keyboard(submission_id)
    )
    
    await state.set_state(SubmissionStates.waiting_files)

# Тута кнопки(отмена, редактирвоание и т.д.), после кнопок пойдёт как раз обработка файлов и т.д.
@suggestion_user_router.callback_query(F.data == "confirm_submission")
async def confirm_submission_handler(callback: CallbackQuery, state: FSMContext):
    """Отправка работы на модерацию"""
    data = await state.get_data()
    submission_id = data.get('submission_id')
    
    if not submission_id or submission_id not in submission_data:
        await callback.answer("❌ Ошибка: работа не найдена")
        return

    submission = submission_data[submission_id]
    
    # Здесь будет логика отправки модераторам
    # await send_to_moderation(submission) !!! 
    
    del submission_data[submission_id]
    await state.clear()
    
    await callback.message.edit_text(
        text = SUBMITTED_TO_MODERATION,
        parse_mode='HTML',
        reply_markup=get_back_to_menu_keyboard()
    )
    await callback.answer()

@suggestion_user_router.callback_query(F.data == "edit_description")
async def edit_submission_text_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    old_text = data.get('temp_text_input', '')
    
    # Мб надоел, но не константа снова из-за того, что тут подставляется много чего
    await callback.message.answer(
        "✏️ <b>Редактирование описания</b>\n\n"
        f"Текущий текст:\n<code>{escape(old_text)}</code>\n\n"
        "Пришли новый текст в том же формате:",
        parse_mode='HTML',
        reply_markup=get_cancel_keyboard()
    )
    
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
    await callback.message.answer(
        text = ADD_FILES,
        parse_mode='HTML',
        reply_markup=get_files_keyboard()  
    )
    await state.set_state(SubmissionStates.waiting_files)
    await callback.answer()

@suggestion_user_router.callback_query(F.data == "cancel_submission")
async def cancel_submission(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    submission_id = data.get('submission_id')
    
    if submission_id and submission_id in submission_data:
        del submission_data[submission_id]
    
    await state.clear()
    await callback.message.edit_text(
        text = CANCELING_A_SHIPMENT,
        parse_mode='HTML',
        reply_markup=get_back_to_menu_keyboard() 
    )
    await callback.answer()

@suggestion_user_router.callback_query(F.data == "cancel_current_action")
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

@suggestion_user_router.message(SubmissionStates.waiting_files, F.document | F.photo)  
async def process_submission_files(message: Message, state: FSMContext):
    data = await state.get_data()
    submission_id = data.get('submission_id')
    
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

    submission_data[submission_id]['files'] = files

    file_count = len(files)
    file_word = 'файлов' if file_count % 10 not in [2, 3, 4] or file_count % 100 in [12, 13, 14] else 'файла'  
    
    # Тут тема такая же, тут много штук, которые есть в этом файле, так что, не константы
    text_done = (
        f'✅ <b>Добавлено!</b>\n'
        f'📦 <b>Файл:</b> <code>{escape(file_name)}</code>\n'
        f'📊 <b>Всего:</b> {file_count} {file_word}\n\n'
        f'Можно отправить ещё или нажать <b>Готово</b>' )
    
    await message.answer(
        text = text_done,
        parse_mode = 'HTML'
    )
    
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
        submission_data[submission_id]['no_files'] = True
        await callback.answer('✅ Принято: работа без файлов')
    else:
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
    title: str = '📝 <b>Текущая работа:</b>'
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
    course = escape(submission_info.get('course', 'Не указано'))
    teacher = escape(submission_info.get('teacher', 'Не указано'))
    work_name = escape(submission_info.get('work_name', 'Не указано'))

    response_text = (
        f'{title}\n\n'
        f'<b>Предмет:</b> <code>{subject}</code>\n'
        f'<b>Курс:</b> <code>{course}</code>\n'
        f'<b>Преподаватель:</b> <code>{teacher}</code>\n'
        f'<b>Работа:</b> <code>{work_name}</code>\n\n'
    )

    files = submission_info.get('files', [])
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

    response_text += '\n<b>Всё верно? Отправляем на проверку?</b>'

    await message.answer(
        response_text,
        parse_mode='HTML',
        reply_markup=get_submission_preview_keyboard()
    )