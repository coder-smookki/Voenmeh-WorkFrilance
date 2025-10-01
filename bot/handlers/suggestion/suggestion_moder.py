import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from bot.utils.consts import GOOD_NEWS, BAD_NEWS, get_accept_work
from bot.keyboards.go_to_menu import get_back_to_menu_keyboard
from bot.utils.states import submission_data
from sqlalchemy.ext.asyncio import AsyncSession

from database.repo.student_work import StudentWorkRepo
from database.repo.work_file import WorkFileRepo
from bot.services.file_service import FileService
from database.repo.user import UserRepo

moderation_router = Router(name='moderation_router')

@moderation_router.callback_query(F.data.startswith("accept_"))
async def accept_submission(callback: CallbackQuery, bot: Bot, session: AsyncSession):
    try:
        submission_id = callback.data.split('_')[1]
        data = submission_data.get(submission_id)

        if not data:
            await callback.answer("❌ Данные отправки не найдены!")
            return

        try:
            # Создаем репозитории и сервисы
            file_service = FileService()
            student_work_repo = StudentWorkRepo(session)
            work_file_repo = WorkFileRepo(session)
            user_repo = UserRepo(session)

            # Создаем запись в student_works
            student_work = await student_work_repo.create_work(
                education_level=int(data['lvl_education']),
                course=int(data['course']),
                subject=data['subject'],
                work_name=data['work_name'],
                archive_path=""  # Временно пустой путь
            )

            # Обрабатываем файлы
            files = data.get('files', [])
            archive_path = await file_service.process_submission_files(
                bot=bot,
                files_data=files,
                user_id=data['user_id'],
                work_id=student_work.id
            )

            # Обновляем путь к архиву
            student_work.archive_path = archive_path
            
            # Создаем записи для каждого файла
            for file_info in files:
                # Получаем размер файла, если доступен
                file_size = file_info.get('size', 0)
                
                await work_file_repo.create_work_file(
                    student_work_id=student_work.id,
                    file_field=file_service._get_field_name_by_order(file_info.get('order', 1)),
                    original_filename=file_info['name'],
                    file_path=f"{student_work.id}/{file_info['name']}",
                    file_size=file_size
                )

            # Обновляем счетчик работ пользователя
            await user_repo.increment_works_count(data['user_id'])
            
            await session.commit()
            
            # Уведомляем пользователя
            await bot.send_message(
                chat_id=data['user_id'],
                text=GOOD_NEWS,
                parse_mode='HTML',
                reply_markup=get_back_to_menu_keyboard()
            )
            
            # Обновляем сообщение модератора
            try:
                new_caption = get_accept_work(data, callback)
                await callback.message.edit_caption(
                    caption=new_caption,
                    parse_mode='HTML',
                    reply_markup=None
                )
            except TelegramBadRequest as e:
                if "message is not modified" not in str(e):
                    try:
                        new_text = get_accept_work(data, callback)
                        await callback.message.edit_text(
                            text=new_text,
                            parse_mode='HTML',
                            reply_markup=None
                        )
                    except TelegramBadRequest:
                        pass  # Игнорируем, если сообщение уже обновлено

            # Удаляем из временного хранилища
            if submission_id in submission_data:
                del submission_data[submission_id]

            await callback.answer("✅ Работа принята в базу!")

        except Exception as db_error:
            await session.rollback()
            logging.error(f"Database error: {db_error}", exc_info=True)
            await callback.answer("❌ Ошибка сохранения в БД")
            
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
                text=BAD_NEWS,
                parse_mode='HTML',
                reply_markup=get_back_to_menu_keyboard()
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