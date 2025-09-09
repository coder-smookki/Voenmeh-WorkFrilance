from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InputMediaPhoto, InputMediaVideo
from aiogram.exceptions import TelegramBadRequest
import logging
from typing import Dict, Any
from bot.utils.consts import get_executor_text, ORDER_ACCEPTED, ORDER_REJECTED, ORDER_COMPLETED
from bot.keyboards.go_to_menu import get_back_to_menu_keyboard
from bot.utils.states import order_data
from bot.settings import ORDER_CHAT_ID
from bot.keyboards.order_preview import get_executor_keyboard, get_complete_order_keyboard

order_executor_router = Router(name='order_executor_router')

async def create_order_thread_and_send_message(
    bot: Bot,
    order_chat_id: int,
    order_info: Dict[str, Any],
    order_id: str
) -> int:
    try:
        topic_name = f"Заказ #{order_id[:8]}"
        topic_result = await bot.create_forum_topic(
            chat_id=order_chat_id,
            name=topic_name
        )
        
        topic_id = topic_result.message_thread_id
        
        executor_text = get_executor_text(order_info)
        
        files = order_info.get('files', [])
        sorted_files = sorted(files, key=lambda x: x.get('order', 0))
        
        description_message = await bot.send_message(
            chat_id=order_chat_id,
            message_thread_id=topic_id,
            text=executor_text,
            parse_mode='HTML'
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
                            caption=f"🖼️ Изображение {i} к работе"
                        ))
                    elif file_info['type'] == 'video':
                        media_group.append(InputMediaVideo(
                            media=file_info['id'],
                            caption=f"🎥 Видео {i} к работе"
                        ))
                
                await bot.send_media_group(
                    chat_id=order_chat_id,
                    message_thread_id=topic_id,
                    media=media_group,
                    reply_to_message_id=message_to_reply_to
                )
            except Exception as e:
                logging.error(f"Error sending media group: {e}")
                for i, file_info in enumerate(media_group_files, 1):
                    try:
                        if file_info['type'] == 'photo':
                            await bot.send_photo(
                                chat_id=order_chat_id,
                                message_thread_id=topic_id,
                                photo=file_info['id'],
                                caption=f"🖼️ Изображение {i} к работе",
                                reply_to_message_id=message_to_reply_to
                            )
                        elif file_info['type'] == 'video':
                            await bot.send_video(
                                chat_id=order_chat_id,
                                message_thread_id=topic_id,
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
                        chat_id=order_chat_id,
                        message_thread_id=topic_id,
                        document=file_info['id'],
                        caption=f"📄 Документ {i} к работе",
                        reply_to_message_id=message_to_reply_to
                    )
                elif file_info['type'] == 'audio':
                    await bot.send_audio(
                        chat_id=order_chat_id,
                        message_thread_id=topic_id,
                        audio=file_info['id'],
                        caption=f"🎵 Аудио {i} к работе",
                        reply_to_message_id=message_to_reply_to
                    )
            except Exception as e:
                logging.error(f"Error sending single file: {e}")

        await bot.pin_chat_message(
            chat_id=order_chat_id,
            message_id=description_message.message_id
        )
        
        await description_message.edit_reply_markup(
            reply_markup=get_executor_keyboard(order_id)
        )
        
        return topic_id
        
    except Exception as e:
        logging.error(f'Error creating order thread: {e}')
        raise

@order_executor_router.callback_query(F.data.startswith("acceptor_"))
async def accept_order(callback: CallbackQuery, bot: Bot):
    # Добавление пользотваелю 1 заказа и его номера
    try:
        parts = callback.data.split('_')
        if len(parts) < 2:
            await callback.answer("❌ Неверный формат callback data!")
            return
            
        order_id = parts[1]
        data = order_data.get(order_id)

        if not data:
            await callback.answer("❌ Данные заказа не найдены!")
            return

        try:
            topic_name = f"✅ #{order_id[:8]} (@{callback.from_user.username})"
            
            topic_result = await bot.create_forum_topic(
                chat_id=ORDER_CHAT_ID,
                name=topic_name
            )
            topic_id = topic_result.message_thread_id
            
            accepted_text = (
                f"✅ <b>ПРИНЯТЫЙ ЗАКАЗ</b>\n\n"
                f"<b>От:</b> {data['first_name']} (@{data['username']})\n"
                f"<b>ID:</b> {data['user_id']}\n\n"
                f"<b>Описание заказа:</b>\n{data['text']}\n\n"
                f"<i>Работа принята исполнителем @{callback.from_user.username}</i>"
            )
            
            description_message = await bot.send_message(
                chat_id=ORDER_CHAT_ID,
                message_thread_id=topic_id,
                text=accepted_text,
                parse_mode='HTML'
            )
            message_to_reply_to = description_message.message_id

            files = data.get('files', [])
            sorted_files = sorted(files, key=lambda x: x.get('order', 0))
            
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
                                caption=f"🖼️ Изображение {i} к принятой работе"
                            ))
                        elif file_info['type'] == 'video':
                            media_group.append(InputMediaVideo(
                                media=file_info['id'],
                                caption=f"🎥 Видео {i} к принятой работе"
                            ))
                    
                    await bot.send_media_group(
                        chat_id=ORDER_CHAT_ID,
                        message_thread_id=topic_id,
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
                                    message_thread_id=topic_id,
                                    photo=file_info['id'],
                                    caption=f"🖼️ Изображение {i} к принятой работе",
                                    reply_to_message_id=message_to_reply_to
                                )
                            elif file_info['type'] == 'video':
                                await bot.send_video(
                                    chat_id=ORDER_CHAT_ID,
                                    message_thread_id=topic_id,
                                    video=file_info['id'],
                                    caption=f"🎥 Видео {i} к принятой работе",
                                    reply_to_message_id=message_to_reply_to
                                )
                        except Exception as e:
                            logging.error(f"Error sending media file: {e}")

            for i, file_info in enumerate(single_files, 1):
                try:
                    if file_info['type'] == 'document':
                        await bot.send_document(
                            chat_id=ORDER_CHAT_ID,
                            message_thread_id=topic_id,
                            document=file_info['id'],
                            caption=f"📄 Документ {i} к принятой работе",
                            reply_to_message_id=message_to_reply_to
                        )
                    elif file_info['type'] == 'audio':
                        await bot.send_audio(
                            chat_id=ORDER_CHAT_ID,
                            message_thread_id=topic_id,
                            audio=file_info['id'],
                            caption=f"🎵 Аудио {i} к принятой работе",
                            reply_to_message_id=message_to_reply_to
                        )
                except Exception as e:
                    logging.error(f"Error sending single file: {e}")

            await bot.pin_chat_message(
                chat_id=ORDER_CHAT_ID,
                message_id=description_message.message_id
            )
            
            await description_message.edit_reply_markup(
                reply_markup=get_complete_order_keyboard(order_id)
            )
            
        except Exception as e:
            logging.error(f"Error creating accepted order topic: {e}")

        try:
            await bot.send_message(
                chat_id=data['user_id'],
                text=ORDER_ACCEPTED,
                parse_mode='HTML',
                reply_markup=get_back_to_menu_keyboard()
            )
        except TelegramBadRequest:
            logging.warning(f"User {data['user_id']} blocked the bot")
            
        try:
            if callback.message.text:
                new_text = f"✅ ЗАКАЗ ПРИНЯТ\nисполнитель @{callback.from_user.username}\n\n{callback.message.text}"
                await callback.message.edit_text(
                    text=new_text,
                    parse_mode='HTML'
                )
            elif callback.message.caption:
                new_caption = f"✅ ЗАКАЗ ПРИНЯТ\nисполнитель @{callback.from_user.username}\n\n{callback.message.caption}"
                await callback.message.edit_caption(
                    caption=new_caption,
                    parse_mode='HTML'
                )
        except Exception as e:
            logging.error(f"Error updating message: {e}")

        await callback.message.edit_reply_markup(reply_markup=None)

        if order_id in order_data:
            del order_data[order_id]

        await callback.answer("✅ Заказ принят!")

    except Exception as e:
        logging.error(f"Error accepting order: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при принятии заказа")

@order_executor_router.callback_query(F.data.startswith("complete_"))
async def complete_order(callback: CallbackQuery, bot: Bot):
    """Обработчик завершения заказа"""
    try:
        parts = callback.data.split('_')
        if len(parts) < 2:
            await callback.answer("❌ Неверный формат callback data!")
            return
            
        order_id = parts[1] 
        data = order_data.get(order_id)

        if not data:
            await callback.answer("❌ Данные заказа не найдены!")
            return

        try:
            await bot.send_message(
                chat_id=data['user_id'],
                text=ORDER_COMPLETED,
                parse_mode='HTML',
                reply_markup=get_back_to_menu_keyboard()
            )
        except TelegramBadRequest:
            logging.warning(f"User {data['user_id']} blocked the bot")

        try:
            topic_id = callback.message.message_thread_id
            
            await bot.close_forum_topic(
                chat_id=ORDER_CHAT_ID,
                message_thread_id=topic_id
            )
            
            if callback.message.text:
                new_text = f"✅ ЗАКАЗ ЗАВЕРШЕН\nисполнитель @{callback.from_user.username}\n\n{callback.message.text}"
                await callback.message.edit_text(
                    text=new_text,
                    parse_mode='HTML'
                )
            elif callback.message.caption:
                new_caption = f"✅ ЗАКАЗ ЗАВЕРШЕН\nисполнитель @{callback.from_user.username}\n\n{callback.message.caption}"
                await callback.message.edit_caption(
                    caption=new_caption,
                    parse_mode='HTML'
                )
                
        except Exception as e:
            logging.error(f"Error closing forum topic: {e}")
            if callback.message.text:
                new_text = f"✅ ЗАКАЗ ЗАВЕРШЕН (тема не закрыта)\nисполнитель @{callback.from_user.username}\n\n{callback.message.text}"
                await callback.message.edit_text(
                    text=new_text,
                    parse_mode='HTML'
                )
            elif callback.message.caption:
                new_caption = f"✅ ЗАКАЗ ЗАВЕРШЕН (тема не закрыта)\nисполнитель @{callback.from_user.username}\n\n{callback.message.caption}"
                await callback.message.edit_caption(
                    caption=new_caption,
                    parse_mode='HTML'
                )

        await callback.message.edit_reply_markup(reply_markup=None)

        await callback.answer("✅ Заказ завершен!")

    except Exception as e:
        logging.error(f"Error completing order: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при завершении заказа")

@order_executor_router.callback_query(F.data.startswith("rejector_"))
async def reject_order(callback: CallbackQuery, bot: Bot):
    try:
        parts = callback.data.split('_')
        if len(parts) < 2:
            await callback.answer("❌ Неверный формат callback data!")
            return
            
        order_id = parts[1]
        data = order_data.get(order_id)

        if not data:
            await callback.answer("❌ Данные заказа не найдены!")
            return

        try:
            await bot.send_message(
                chat_id=data['user_id'],
                text=ORDER_REJECTED,
                parse_mode='HTML',
                reply_markup=get_back_to_menu_keyboard()
            )
        except TelegramBadRequest:
            logging.warning(f"User {data['user_id']} blocked the bot")

        try:
            topic_id = data.get('topic_id')
            if topic_id:
                await bot.delete_forum_topic(
                    chat_id=ORDER_CHAT_ID,
                    message_thread_id=topic_id
                )
        except Exception as e:
            logging.error(f"Error deleting forum topic: {e}")
            try:
                await callback.message.delete()
            except:
                try:
                    await callback.message.edit_reply_markup(reply_markup=None)
                except:
                    pass

        if order_id in order_data:
            del order_data[order_id]

        await callback.answer("❌ Заказ отклонен!")

    except Exception as e:
        logging.error(f"Error rejecting order: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при отклонении заказа")