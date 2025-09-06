import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from bot.utils.consts import GOOD_NEWS, BAD_NEWS
from bot.keyboards.back_to_menu import get_back_to_menu_keyboard
from bot.handlers.states import submission_data

moderation_router = Router(name='moderation_router')

@moderation_router.callback_query(F.data.startswith("accept_"))
async def accept_submission(callback: CallbackQuery, bot: Bot):
    try:
        submission_id = callback.data.split('_')[1]
        data = submission_data.get(submission_id)

        if not data:
            await callback.answer("❌ Данные отправки не найдены!")
            return

        try:
            await bot.send_message(
                # Тут копайся с БД, я не шарю как это делается..(
                chat_id = data['user_id'],
                text = GOOD_NEWS,
                parse_mode = 'HTML',
                reply_markup = get_back_to_menu_keyboard()
            )
        except TelegramBadRequest:
            logging.warning(f"User {data['user_id']} blocked the bot")

        try:
            new_caption = (
                f"✅ <b>ПРИНЯТАЯ РАБОТА</b>\n\n"
                f"<b>От:</b> {data['first_name']} (@{data['username']})\n"
                f"<b>Предмет:</b> {data['subject']}\n"
                f"<b>Курс:</b> {data['course']}\n"
                f"<b>Работа:</b> {data['work_name']}\n\n"
                f"<i>Работа принята модератором @{callback.from_user.username}</i>"
            )

            await callback.message.edit_caption(
                caption=new_caption,
                parse_mode='HTML'
            )
        except TelegramBadRequest:
            new_text = (
                f"✅ <b>ПРИНЯТАЯ РАБОТА</b>\n\n"
                f"<b>От:</b> {data['first_name']} (@{data['username']})\n"
                f"<b>Предмет:</b> {data['subject']}\n"
                f"<b>Курс:</b> {data['course']}\n"
                f"<b>Работа:</b> {data['work_name']}\n\n"
                f"<i>Работа принята модератором @{callback.from_user.username}</i>"
            )

            await callback.message.edit_text(
                text=new_text,
                parse_mode='HTML'
            )

        await callback.message.edit_reply_markup(reply_markup = None)

        if submission_id in submission_data:
            del submission_data[submission_id]

        await callback.answer("✅ Работа принята в базу!")

    except Exception as e:
        logging.error(f"Error accepting submission: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при принятии работы")

@moderation_router.callback_query(F.data.startswith("reject_"))
async def reject_submission(callback: CallbackQuery, bot: Bot):
    try:
        submission_id = callback.data.split('_')[1]
        data = submission_data.get(submission_id)

        if not data:
            await callback.answer("❌ Данные отправки не найдены!")
            return

        try:
            await bot.send_message(
                chat_id=data['user_id'],
                text = BAD_NEWS,
                parse_mode='HTML',
                reply_markup= get_back_to_menu_keyboard()
            )
        except TelegramBadRequest:
            logging.warning(f"User {data['user_id']} blocked the bot")

        try:
            await callback.message.delete()
        except Exception as e:
            logging.error(f"Error deleting message: {e}")
            await callback.message.edit_reply_markup(reply_markup=None)

        if submission_id in submission_data:
            del submission_data[submission_id]

        await callback.answer("❌ Работа отклонена!")

    except Exception as e:
        logging.error(f"Error rejecting submission: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при отклонении работы")