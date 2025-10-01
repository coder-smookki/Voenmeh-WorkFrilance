from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from bot.keyboards.go_to_menu import get_back_to_menu_keyboard, get_cancel_submission_keyboard
from bot.utils.states import OrderStates
from bot.settings import get_settings
from bot.utils.consts import (
    NO_ORDERS,
    MAX_FILE_SIZE,
    MESSAGE_FROM_EXECUTOR,
    get_order_text,
    get_attachment_text
)
from bot.keyboards.order_list import get_view_order_keyboard, get_order_details_keyboard, get_order_list_keyboard
settings = get_settings()
ORDER_CHAT_ID = settings.bot_settings.order_chat_id

order_list_router = Router(name='order_list_router')

@order_list_router.callback_query(F.data == 'order_list')
async def show_order_list(callback: CallbackQuery, repo):
    """Показывает список заказов пользователя."""
    user_id = callback.from_user.id
    user = await repo.users.get_by_user_id(user_id)
    
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return

    orders = await repo.orders.get_user_orders(user.id)
    
    if not orders:
        await callback.message.edit_text(
            text=NO_ORDERS,
            parse_mode='HTML',
            reply_markup=get_back_to_menu_keyboard()
        )
        return

    text = f"📋 <b>Ваши заказы</b> ({len(orders)})\n\n"
    for order in orders[:10]:
        short_id = order.id[:8]
        text += f"📦 Заказ #{short_id}\n"

    await callback.message.edit_text(
        text=text,
        parse_mode='HTML',
        reply_markup=get_order_list_keyboard(orders)
    )

@order_list_router.callback_query(F.data.startswith("view_order:"))
async def view_order_details(callback: CallbackQuery, repo):
    """Показывает детали конкретного заказа."""
    order_id = callback.data.split(":")[1]
    
    order = await repo.orders.get_order_by_id(order_id)
    if not order:
        await callback.answer("❌ Заказ не найден")
        return

    text = get_order_text(order)

    keyboard_buttons = get_order_details_keyboard

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(
        text=text,
        parse_mode='HTML',
        reply_markup=keyboard
    )


@order_list_router.callback_query(F.data.startswith("message_executor:"))
async def start_message_to_executor(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс отправки сообщения исполнителю."""
    order_id = callback.data.split(":")[1]
    
    await state.update_data(order_id=order_id)
    await state.set_state(OrderStates.waiting_message_to_executor)
    
    await callback.message.edit_text(
        text=MESSAGE_FROM_EXECUTOR,
        parse_mode='HTML',
        reply_markup=get_view_order_keyboard(order_id)
    )


@order_list_router.message(OrderStates.waiting_message_to_executor)
async def send_message_to_executor(message: Message, state: FSMContext, bot, repo):
    """Отправляет сообщение пользователя в тему заказа."""
    data = await state.get_data()
    order_id = data.get('order_id')
    
    if not order_id:
        await message.answer("❌ Ошибка: заказ не найден")
        await state.clear()
        return

    order = await repo.orders.get_order_by_id(order_id)
    if not order or not order.thread_id:
        await message.answer("❌ Заказ или тема не найдены")
        await state.clear()
        return

    # Проверка и сбор вложений
    attachments = []
    if message.document:
        if message.document.file_size > MAX_FILE_SIZE:
            await message.answer("❌ Размер файла превышает лимит в 30 МБ")
            return
        attachments.append(('document', message.document.file_id))
    elif message.photo:
        attachments.append(('photo', message.photo[-1].file_id))
    elif message.video:
        if message.video.file_size > MAX_FILE_SIZE * 2:
            await message.answer("❌ Размер видео превышает лимит в 60 МБ")
            return
        attachments.append(('video', message.video.file_id))

    # Отправка текстового сообщения
    message_text = get_attachment_text(message)
    
    await bot.send_message(
        chat_id=ORDER_CHAT_ID,
        message_thread_id=order.thread_id,
        text=message_text,
        parse_mode='HTML'
    )

    # Отправка вложений
    for attach_type, file_id in attachments:
        if attach_type == 'document':
            await bot.send_document(
                chat_id=ORDER_CHAT_ID,
                message_thread_id=order.thread_id,
                document=file_id
            )
        elif attach_type == 'photo':
            await bot.send_photo(
                chat_id=ORDER_CHAT_ID,
                message_thread_id=order.thread_id,
                photo=file_id
            )
        elif attach_type == 'video':
            await bot.send_video(
                chat_id=ORDER_CHAT_ID,
                message_thread_id=order.thread_id,
                video=file_id
            )
    
    await message.answer(
        text="✅ Сообщение отправлено исполнителю",
        reply_markup=get_back_to_menu_keyboard()
    )
    
    await state.clear()


@order_list_router.callback_query(F.data.startswith("reply_executor:"))
async def handle_reply_to_executor(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает кнопку 'Ответить исполнителю' из пересланного сообщения."""
    order_id = callback.data.split(":")[1]
    
    await state.update_data(
        order_id=order_id,
        reply_message_id=callback.message.message_id
    )
    await state.set_state(OrderStates.waiting_message_to_executor)
    
    cancel_keyboard = get_cancel_submission_keyboard()
    
    # Редактирование сообщения в зависимости от типа
    if callback.message.text:
        await callback.message.edit_text(
            text=MESSAGE_FROM_EXECUTOR,
            parse_mode='HTML',
            reply_markup=cancel_keyboard
        )
    elif callback.message.caption or any([
        callback.message.photo, 
        callback.message.video, 
        callback.message.document
    ]):
        await callback.message.edit_caption(
            caption=MESSAGE_FROM_EXECUTOR,
            parse_mode='HTML',
            reply_markup=cancel_keyboard
        )