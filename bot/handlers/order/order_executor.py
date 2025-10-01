from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InputMediaPhoto, InputMediaVideo
from aiogram.exceptions import TelegramBadRequest
import logging
import re
from typing import Dict, Any

from bot.utils.consts import (ORDER_ACCEPTED, ORDER_REJECTED, ORDER_COMPLETED, 
                              get_accept_order, get_update_order_message, get_accepted_order_text)
from bot.keyboards.go_to_menu import get_back_to_menu_keyboard
from bot.utils.states import order_data
from bot.settings import get_settings
from bot.keyboards.order_preview import get_complete_order_keyboard
from database.repo.user import UserRepo
from bot.services.order_topic_service import OrderTopicService
from database.repo.user import OrderRepo

logger = logging.getLogger(__name__)

settings = get_settings()
ORDER_CHAT_ID = settings.bot_settings.order_chat_id

order_executor_router = Router(name='order_executor_router')


def add_order_to_list(current_list: str | None, order_id: str) -> str:
    """Добавляет order_id в строку списка заказов."""
    if current_list is None or current_list == "":
        return order_id
    else:
        return f"{current_list},{order_id}"


def remove_order_from_list(current_list: str | None, order_id: str) -> str:
    """Удаляет order_id из строки списка заказов."""
    if current_list is None:
        return ""
    
    orders = current_list.split(',')
    filtered_orders = [o for o in orders if o != order_id]
    return ','.join(filtered_orders)


class OrderMessageService:
    """Сервис для обработки сообщений между исполнителем и пользователем"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
    
    async def process_executor_message(self, message: Message, topic_name: str) -> bool:
        """Обрабатывает сообщение от исполнителя и пересылает пользователю"""
        try:
            if message.text and message.text.startswith('/'):
                return False
            
            order_id = self._extract_order_id(topic_name)
            if not order_id:
                return False
            
            full_order_id = self._find_full_order_id(order_id)
            if not full_order_id:
                return False
            
            data = order_data.get(full_order_id)
            if not data:
                logger.warning(f"Данные заказа {full_order_id} не найдены")
                return False
            
            await self._check_user_blocked(data['user_id'], message)
            await self._send_message_to_user(message, data, full_order_id)
            
            return True
                
        except Exception as e:
            logger.error(f"Ошибка в process_executor_message: {e}", exc_info=True)
            return False
    
    def _extract_order_id(self, topic_name: str) -> str | None:
        """Извлекает order_id из названия темы"""
        patterns = [
            r"✅ #(\w+)",
            r"#(\w+)",
            r"Заказ #(\w+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, topic_name)
            if match:
                return match.group(1)
        
        hashtags = re.findall(r'#(\w+)', topic_name)
        return hashtags[0] if hashtags else None
    
    def _find_full_order_id(self, short_order_id: str) -> str | None:
        """Ищет полный order_id в order_data"""
        for stored_order_id in order_data.keys():
            if stored_order_id.startswith(short_order_id):
                return stored_order_id
        
        logger.warning(f"Не найден полный order_id для '{short_order_id}'")
        return None
    
    async def _check_user_blocked(self, user_id: int, message: Message):
        """Проверяет, не заблокирован ли пользователь"""
        try:
            await self.bot.send_chat_action(chat_id=user_id, action='typing')
        except TelegramBadRequest as e:
            if "bot was blocked" in str(e).lower():
                logger.warning(f"Пользователь {user_id} заблокировал бота")
                await message.reply("Не удалось отправить сообщение. Пользователь заблокировал бота.")
                raise
            else:
                raise
    
    async def _send_message_to_user(self, message: Message, data: Dict, full_order_id: str):
        """Отправляет сообщение пользователю"""
        message_text = f"Сообщение от исполнителя по заказу #{full_order_id[:8]}:\n\n{message.text or 'Вложение'}"
        
        try:
            if message.photo:
                await self.bot.send_photo(
                    chat_id=data['user_id'],
                    photo=message.photo[-1].file_id,
                    caption=message_text
                )
            elif message.video:
                await self.bot.send_video(
                    chat_id=data['user_id'],
                    video=message.video.file_id,
                    caption=message_text
                )
            elif message.document:
                await self.bot.send_document(
                    chat_id=data['user_id'],
                    document=message.document.file_id,
                    caption=message_text
                )
            elif message.audio:
                await self.bot.send_audio(
                    chat_id=data['user_id'],
                    audio=message.audio.file_id,
                    caption=message_text
                )
            else:
                await self.bot.send_message(
                    chat_id=data['user_id'],
                    text=message_text
                )
        
        except TelegramBadRequest as e:
            if "bot was blocked" in str(e).lower():
                logger.warning(f"Пользователь {data['user_id']} заблокировал бота")
                await message.reply("Не удалось отправить сообщение. Пользователь заблокировал бота.")
                raise
            else:
                raise

async def _update_user_order_list(user_repo: UserRepo, user_id: int, order_id: str, operation: str):
    """Обновляет список заказов пользователя"""
    try:
        user = await user_repo.get_by_user_id(user_id)
        if not user:
            return

        current_list = user.list_order or ""
        
        if operation == "add":
            new_list_order = add_order_to_list(current_list, order_id)
        elif operation == "remove":
            new_list_order = remove_order_from_list(current_list, order_id)
        else:
            return

        user.count_works_ordered = len(new_list_order.split(',')) if new_list_order else 0
        user.list_order = new_list_order
        
        await user_repo.session.commit()
        
    except Exception as e:
        logger.error(f"Ошибка обновления списка заказов пользователя: {e}")


async def _update_order_message(callback: CallbackQuery, data: Dict, order_id: str, status: str):
    """Обновляет сообщение с заказом"""
    try:
        order_description = data.get('text', 'Описание заказа')
        user_info = f"Заказчик: @{data.get('username', 'Unknown')} (ID: {data['user_id']})"
        
        status_texts = {
            'accepted': f"ЗАКАЗ ПРИНЯТ\nИсполнитель: @{callback.from_user.username}",
            'rejected': f"ОТКЛОНЕННЫЙ ЗАКАЗ\nИсполнитель: @{callback.from_user.username}",
            'completed': f"ЗАКАЗ ВЫПОЛНЕН\nИсполнитель: @{callback.from_user.username}"
        }
        
        status_text = status_texts.get(status, "ЗАКАЗ")
        
        updated_text = get_update_order_message(status_text, order_description, user_info, order_id)
        
        if callback.message.text:
            await callback.message.edit_text(text=updated_text, parse_mode='HTML')
        elif callback.message.caption:
            await callback.message.edit_caption(caption=updated_text, parse_mode='HTML')
            
    except Exception as e:
        logger.error(f"Ошибка обновления сообщения: {e}")


@order_executor_router.callback_query(F.data.startswith("acceptor_"))
async def accept_order(callback: CallbackQuery, bot: Bot, order_repo: OrderRepo, user_repo: UserRepo):
    try:
        order_id = callback.data.split('_')[1]
        data = order_data.get(order_id)

        if not data:
            await callback.answer("Данные заказа не найдены!")
            return

        # Проверяем, существует ли уже заказ
        existing_order = await order_repo.get_order_by_id(order_id)
        if existing_order:
            await callback.answer("Заказ уже был принят!")
            return

        telegram_user_id = data['user_id']
        user = await user_repo.get_by_user_id(telegram_user_id)
        
        if not user:
            user = await user_repo.create_user(
                user_id=telegram_user_id,
                chat_id=telegram_user_id,
                username=data.get('username'),
                first_name=data.get('first_name')
            )

        # 2. СОЗДАЕМ ЗАКАЗ В БД ТОЛЬКО ПРИ ПОДТВЕРЖДЕНИИ
        await order_repo.create_order(
            order_id=order_id,
            user_id=user.id,  # ID из таблицы users
            description=data['text'],
            user_message_id=callback.message.message_id
        )

        # 3. СОЗДАЕМ ТЕМУ ТОЛЬКО ПРИ ПОДТВЕРЖДЕНИИ ИСПОЛНИТЕЛЕМ
        order_topic_service = OrderTopicService(bot)
        thread_id = await order_topic_service.create_order_topic(
            order_id=order_id,
            order_description=data['text'],
            user_message_id=callback.message.message_id
        )

        # 4. СОХРАНЯЕМ thread_id В БАЗУ
        if thread_id:
            try:
                await order_repo.update_order_thread(  # Используем order_repo
                    order_id=order_id,
                    thread_id=thread_id,
                    user_message_id=callback.message.message_id
                )
                logger.info(f"✅ Тема создана и сохранена для заказа {order_id}")
            except Exception as e:
                logger.error(f"❌ Ошибка сохранения темы: {e}")

        # 5. ОБНОВЛЯЕМ ДАННЫЕ ПОЛЬЗОВАТЕЛЯ (активные заказы)
        try:
            current_list = user.list_order or ""
            new_list_order = add_order_to_list(current_list, order_id)
            
            user.count_works_ordered = len(new_list_order.split(',')) if new_list_order else 0
            user.list_order = new_list_order
            
            # Сохраняем изменения пользователя
            await user_repo.session.commit()
            logger.info(f"✅ Заказ {order_id} добавлен пользователю {user.user_id}. Активных заказов: {user.count_works_ordered}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка обновления данных пользователя: {e}")

        try:
            if thread_id:
                executor_text = get_accept_order(data, callback)
                
                description_message = await bot.send_message(
                    chat_id=ORDER_CHAT_ID,
                    message_thread_id=thread_id,
                    text=executor_text,
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
                            message_thread_id=thread_id,
                            media=media_group,
                            reply_to_message_id=message_to_reply_to
                        )
                    except Exception as e:
                        logger.error(f"Error sending media group: {e}")
                        for i, file_info in enumerate(media_group_files, 1):
                            try:
                                if file_info['type'] == 'photo':
                                    await bot.send_photo(
                                        chat_id=ORDER_CHAT_ID,
                                        message_thread_id=thread_id,
                                        photo=file_info['id'],
                                        caption=f"🖼️ Изображение {i} к принятой работе",
                                        reply_to_message_id=message_to_reply_to
                                    )
                                elif file_info['type'] == 'video':
                                    await bot.send_video(
                                        chat_id=ORDER_CHAT_ID,
                                        message_thread_id=thread_id,
                                        video=file_info['id'],
                                        caption=f"🎥 Видео {i} к принятой работе",
                                        reply_to_message_id=message_to_reply_to
                                    )
                            except Exception as e:
                                logger.error(f"Error sending media file: {e}")

                for i, file_info in enumerate(single_files, 1):
                    try:
                        if file_info['type'] == 'document':
                            await bot.send_document(
                                chat_id=ORDER_CHAT_ID,
                                message_thread_id=thread_id,
                                document=file_info['id'],
                                caption=f"📄 Документ {i} к принятой работе",
                                reply_to_message_id=message_to_reply_to
                            )
                        elif file_info['type'] == 'audio':
                            await bot.send_audio(
                                chat_id=ORDER_CHAT_ID,
                                message_thread_id=thread_id,
                                audio=file_info['id'],
                                caption=f"🎵 Аудио {i} к принятой работе",
                                reply_to_message_id=message_to_reply_to
                            )
                    except Exception as e:
                        logger.error(f"Error sending single file: {e}")

                    await bot.pin_forum_topic_message(
                        chat_id=ORDER_CHAT_ID,
                        message_thread_id=thread_id,
                        message_id=description_message.message_id
                    )
                
                await description_message.edit_reply_markup(
                    reply_markup=get_complete_order_keyboard(order_id)
                )
                
        except Exception as e:
            logger.error(f"Error sending files to topic: {e}")

        try:
            await bot.send_message(
                chat_id=data['user_id'],  
                text=ORDER_ACCEPTED,
                parse_mode='HTML',
                reply_markup=get_back_to_menu_keyboard()
            )
        except TelegramBadRequest:
            logger.warning(f"User {data['user_id']} blocked the bot")
            
        try:
            order_description = data.get('text', 'Описание заказа')
            user_info = f"Заказчик: @{data.get('username', 'Unknown')} (ID: {data['user_id']})"
            
            accepted_text = get_accepted_order_text(callback, order_description, user_info, order_id)
            
            if callback.message.text:
                await callback.message.edit_text(
                    text=accepted_text,
                    parse_mode='HTML'
                )
            elif callback.message.caption:
                await callback.message.edit_caption(
                    caption=accepted_text,
                    parse_mode='HTML'
                )
        except Exception as e:
            logger.error(f"Error updating message: {e}")
            
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
            logger.info("Клавиатура уже была убрана")

        await callback.answer("✅ Заказ принят!")

    except Exception as e:
        logger.error(f"Error accepting order: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при принятии заказа")


@order_executor_router.callback_query(F.data.startswith("rejector_"))
async def reject_order(callback: CallbackQuery, bot: Bot, user_repo: UserRepo, order_repo: OrderRepo):
    try:
        order_id = callback.data.split('_')[1]
        data = order_data.get(order_id)

        if not data:
            await callback.answer("Данные заказа не найдены!")
            return

        order = await order_repo.get_order_by_id(order_id)
        was_accepted = order and order.thread_id is not None

        if was_accepted:
            try:
                await bot.close_forum_topic(
                    chat_id=ORDER_CHAT_ID,
                    message_thread_id=order.thread_id
                )
                await bot.edit_forum_topic(
                    chat_id=ORDER_CHAT_ID,
                    message_thread_id=order.thread_id,
                    name=f"Заказ #{order_id[:8]} (отменён)"
                )
            except Exception as e:
                logger.error(f"Ошибка закрытия/переименования темы: {e}")

        await _update_user_order_list(user_repo, data['user_id'], order_id, "remove")

        try:
            await order_repo.update_order_status(order_id, "rejected")
        except Exception as e:
            logger.error(f"Ошибка обновления статуса заказа: {e}")

        try:
            await bot.send_message(
                chat_id=data['user_id'],
                text=ORDER_REJECTED,
                parse_mode='HTML',
                reply_markup=get_back_to_menu_keyboard()
            )
        except TelegramBadRequest as e:
            if "bot was blocked" in str(e).lower():
                logger.warning(f"Пользователь {data['user_id']} заблокировал бота")
            else:
                raise

        await _update_order_message(callback, data, order_id, 'rejected')

        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise

        if not was_accepted and order and order.thread_id:
            try:
                await bot.delete_forum_topic(
                    chat_id=ORDER_CHAT_ID,
                    message_thread_id=order.thread_id
                )
            except Exception as e:
                logger.error(f"Ошибка удаления темы: {e}")

        try:
            await order_repo.delete_order(order_id)
        except Exception as e:
            logger.error(f"Ошибка удаления заказа {order_id}: {e}")

        if order_id in order_data:
            del order_data[order_id]

        await callback.answer("Заказ отклонен!")

    except Exception as e:
        logger.error(f"Ошибка при отклонении заказа: {e}", exc_info=True)
        await callback.answer("Ошибка при отклонении заказа")


@order_executor_router.callback_query(F.data.startswith("complete_"))
async def complete_order(callback: CallbackQuery, bot: Bot, user_repo: UserRepo, order_repo: OrderRepo):
    try:
        order_id = callback.data.split('_')[1]
        data = order_data.get(order_id)

        if not data:
            await callback.answer("Данные заказа не найдены!")
            return

        await _update_user_order_list(user_repo, data['user_id'], order_id, "remove")

        try:
            await bot.send_message(
                chat_id=data['user_id'],
                text=ORDER_COMPLETED,
                parse_mode='HTML',
                reply_markup=get_back_to_menu_keyboard()
            )
        except TelegramBadRequest:
            logger.warning(f"Пользователь {data['user_id']} заблокировал бота")

        try:
            if callback.message.message_thread_id:
                await bot.close_forum_topic(
                    chat_id=ORDER_CHAT_ID,
                    message_thread_id=callback.message.message_thread_id
                )
                await bot.edit_forum_topic(
                    chat_id=ORDER_CHAT_ID,
                    message_thread_id=callback.message.message_thread_id,
                    name=f"Заказ #{order_id[:8]} (завершён)"
                )
        except Exception as e:
            logger.error(f"Ошибка закрытия/переименования темы: {e}")

        await _update_order_message(callback, data, order_id, 'completed')

        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass

        try:
            await order_repo.delete_order(order_id)
        except Exception as e:
            logger.error(f"Ошибка удаления заказа {order_id}: {e}")

        if order_id in order_data:
            del order_data[order_id]

        await callback.answer("Заказ завершен!")

    except Exception as e:
        logger.error(f"Ошибка при завершении заказа: {e}", exc_info=True)
        await callback.answer("Ошибка при завершении заказа")