from enum import StrEnum
from html import escape
from bot.utils.states import submission_data

WELCOME_TEXT = (
    '<b>Приветствую, боец!</b>\n'
    'Ты в тылу врага (сессии), но я - твой бот-подкрепление!\n\n'
    '<b>Выбирай стратегию:</b>\n'
    '💥 Прорыв обороны - заказать работу\n'
    '🛡 Готовые укрепления - собранная база решений\n'
    '☮️ Усилить армию - отправить свою работу\n'
    '⚡️ Блиц-помощь - связь с поддержкой\n'
    '📋 Архив миссий - посмотреть свои заказы\n\n'
    'Навигация по боту происходит путём нажатия кнопок, не запутайся!'
    )

DESIGN_EXAMPLE = (
    '☮️ <b>Готов принять твой вклад в общее дело!</b>\n\n'
    'Сначала пришли описание работы в формате:\n\n'
    '<code>Предмет\n'
    'Уровень высшего образования, где( Бакалавриат -- 1, Специалитет -- 2, Магистратура -- 3, СПО -- 4)\n'
    'Курс\n'
    'Название работы + Вариант + Преподователь</code>\n\n'
    'Пример:\n'
    '<code>Высшая математика\n'
    '1(Обязательно просто цифра!)\n'
    '2(Обязательно просто цифра!)\n' 
    'Иванов Иван Иваныч, Ряды 2 вариант</code>\n\n'
    'После описания сможешь прикрепить файлы работы.'
    ) 

TEXT_ANALYSIS_ERROR = (
    '❌ Боец! Я такого не понимаю, отправь текстом по примеру выше!'
    )

INCORRECT_TEXT_FORMAT = (
    '❌ <b>Мало информации!</b>\n\n'
    'Пришли описание в <b>4 строки</b>:\n'
    '• <code>Предмет</code>\n'
    '• <code>Уровень образования</code>\n' 
    '• <code>Курс</code>\n' 
    '• <code>Название работы и преподователь</code>\n'
    )

EMPTY_FIELDS = (
    '❌ <b>Важные поля пустые,боец!</b>\n'
    'Предмет, уровень образования, курс и название работы должны быть заполнены.'
    )

ERROR_TRY_AGAIN = (
    '❌ <b>Что-то пошло не так!</b>\n'
    'Начни заново /start'
)

MAXIMUM_FILES = (
    '⚠️ <b>Максимум 10 файлов на работу</b>\n'
    'Нажми "✅Готово" чтобы продолжить'
)

ADD_FILES = (
    '📎 <b>Присылай дополнительные файлы</b>\n\n'
    'Можно присылать документы и изображения.\n'
    'Когда закончишь, нажми кнопку "✅Готово"'
)

CANCELING_A_SHIPMENT = (
    '❌ <b>Отправка работы отменена</b>\n\n'
    'Если передумаешь - всегда можно отправить работу снова, боец!'
)

SUBMITTED_TO_MODERATION = (
    '✅ <b>Работа отправлена на модерацию!</b>\n\n'
    'Обычно проверка занимает до 24 часов.\n'
    'Как только твоя работа пополнит наши запасы и сможет помочь другим -- мы сразу сообщим!'
)

GOOD_NEWS = (
    '🎉 <b>Отличные новости, боец!</b>\n\n'
    'Твоя работа из предложки принята и добавлена в нашу базу решений!\n'
    'Теперь она поможет другим студентам в борьбе с сессией.\n\n'
    'Спасибо за вклад в общее дело! 💪'
)

BAD_NEWS = (
    '❌ <b>Работа из предложки отклонена</b>\n\n'
    'К сожалению, твоя работа не прошла проверку модераторами.\n'
    'Возможные причины:\n'
    '• Неправильный формат\n'
    '• Низкое качество\n'
    '• Уже есть в базе\n'
    '• Нарушение правил\n\n'
    'Попробуй отправить другую работу или свяжись с поддержкой для уточнения причин.'
)

SUPPORT_CENTER = (
    '🆘 <b>Центр поддержки</b>\n\n'
    'Здесь ты можешь:\n'
    '• 📩 Написать вопрос в поддержку\n'
    '• 🤝 Предложить улучшения для бота\n' 
    '• 🐛 Сообщить об ошибке\n\n'
    'Просто напиши свой вопрос ниже, и мы обязательно ответим!'
)

WRITE_QUESTION = (
    '✍️ <b>Напиши свой вопрос</b>\n\n'
    'Опиши подробно свою проблему или вопрос, и мы обязательно поможем!'
)

EXPECT_RESPONSE = (
    '✅ <b>Сообщение отправлено в поддержку!</b>\n'
    'Ожидай ответа ⏳'
)

START_ORDER = (
    '<b> Присылай описание работы, боец!</b>\n'
    'Оно может быть любым, но если ты оформишь в таком виде:\n\n'
    '<code>Предмет: Высшая математика\n'
    'Тип работы: Курсовая\n'
    'Тема: Теория вероятности\n'
    'Объём: 25-30 страниц\n'
    'Дедлайн(срок сдачи): 25.12.2024\n'
    'Бюджет: 5000  руб.\n' 
    'Описание: Мне нужно побольше про Энштейна и меньше другого всего</code>\n\n'
    'То твой исполнитель будет вне себя от радости!)' 
)

def get_suggestion_preview_text(subject: str, lvl_education: int, course: int, work_name: str):
    preview_text = (
        '✅ <b>Принял!</b> Проверь информацию:\n\n'
        f"<b>Предмет:</b> <code>{escape(subject)}</code>\n"
        f"<b>Уровень образования:</b> <code>{escape(lvl_education)}</code>\n"
        f"<b>Курс:</b> <code>{escape(course)}</code>\n"
        f"<b>Работа:</b> <code>{escape(work_name)}</code>\n\n"
        '📎 <b>Теперь прикрепи дополнительные файлы к работе</b>\n'
        '• Документы, фото, архивы\n'
        '• Можно несколько файлов(Но максимум -- 10)\n'
        '• Когда всё отправишь — нажми "✅Готово"'
    )
    return preview_text

def get_suggestion_edit_text(old_text : str):
    edit_text = ( '✏️ <b>Редактирование описания</b>\n\n'
    f"Текущий текст:\n<code>{escape(old_text)}</code>\n\n"
    'Пришли новый текст в том же формате:'
    )
    return edit_text
    
def get_text_done(file_name: str, order: int, total_count: int):
    if total_count % 10 == 1 and total_count % 100 != 11:
        file_word = 'файл'
    elif total_count % 10 in [2, 3, 4] and total_count % 100 not in [12, 13, 14]:
        file_word = 'файла'
    else:
        file_word = 'файлов'
    
    text_done = (
        '✅ <b>Добавлено!</b>\n'
        f"📦 <b>Файл {order}:</b> <code>{escape(file_name)}</code>\n"
        f"📊 <b>Всего:</b> {total_count} {file_word}\n\n"
        'Можно отправить ещё или нажать <b>"✅Готово"</b>' 
    )
    return text_done
    
def  get_response_text(title : str, subject : str, lvl_education : int, course : int, work_name : str):
    response_text = ( 
        f"{title}\n\n"
        f"<b>Предмет:</b> <code>{subject}</code>\n"
        f"<b>Уровень образования:</b> <code>{escape(lvl_education)}</code>\n"
        f"<b>Курс:</b> <code>{course}</code>\n"
        f"<b>Работа:</b> <code>{work_name}</code>\n\n"
        )
    return response_text

def get_executor_text(order_info):
    executor_text = (
        f"🛒 <b>НОВЫЙ ЗАКАЗ</b>\n\n"
        f"<b>От:</b> {order_info['first_name']} (@{order_info['username']})\n"
        f"<b>ID:</b> {order_info['user_id']}\n\n"
        f"<b>Описание заказа:</b>\n{order_info['text']}\n\n"
        )
    return executor_text

def get_edit_order_text(old_text : str):
    edit_text = (
        '✏️ <b>Редактирование описания</b>\n\n'
        f"екущий текст:\n<code>{escape(old_text)}</code>\n\n"
        'Пришли новый текст:'
        )
    return edit_text
    
SUBMITTED_TO_EXECUTOR = (
    '✅ <b>Заказ отправлен!</b>\n\n'
    'Обычно проверка и принятие заказа занимает до 24 часов.\n'
    'Как только твой заказ примут - он появится в списке заказов и ты сможешь написать исполнителю'
)

def get_accept_work(data, callback):
    accept_work = (
        '✅ <b>ПРИНЯТАЯ РАБОТА</b>\n\n'
        f"<b>От:</b> {data['first_name']} (@{data['username']})\n"
        f"<b>Предмет:</b> {data['subject']}\n"
        f"<b>Уровень образования:</b> {data['lvl_education']}\n"
        f"<b>Курс:</b> {data['course']}\n"
        f"<b>Работа:</b> {data['work_name']}\n\n"
        f"<i>Работа принята модератором @{callback.from_user.username}</i>"
    )
    return accept_work

def get_new_suggeston_text(submission_info):
    text = (
        '☮ <b>НОВАЯ РАБОТА В ПРЕДЛОЖКУ</b>\n\n'
        f"<b>От:</b> {submission_info['first_name']} (@{submission_info['username']})\n"
        f"<b>ID:</b> {submission_info['user_id']}\n\n"
        f"<b>Предмет:</b> {submission_info['subject']}\n"
        f"<b>Уровень образования:</b> {submission_info['lvl_education']}\n"
        f"<b>Курс:</b> {submission_info['course']}\n"
        f"<b>Работа:</b> {submission_info['work_name']}\n\n"
        'Проверь и прими решение:'
    )
    return text

def get_preview_text(message):
    text = ( 
        '✅<b>Описание принято!</b>\n'
        'Проверяй своё описание!\n'
        f"{escape(message.text)}\n\n"
        '📎 <b>Теперь прикрепи дополнительыне файлы, для большей точности!</b>\n'
        '• Документы, фото, архивы\n'
        '• Можно несколько файлов(Но максимум -- 10)\n'
        '• Когда всё отправишь — нажми "✅Готово"'
    )
    return text

ORDER_ACCEPTED = '✅ Ваш заказ был принят исполнителем!'

ORDER_REJECTED = '❌ К сожалению, ваш заказ был отклонен исполнителем.'

def get_accept_order(order_info, callback):
    accept_work = (
        '✅ <b>ПРИНЯТЫЙ ЗАКАЗ</b>\n\n'
        f"<b>От:</b> {order_info['first_name']} (@{order_info['username']})\n"
        f"<b>ID:</b> {order_info['user_id']}\n\n"
        f"<b>Описание заказа:</b>\n{order_info['text']}\n\n"
        f"<i>Работа принята исполнителем @{callback.from_user.username}</i>"
    )
    return accept_work

ORDER_COMPLETED = (
        '✅ <b>Ваш заказ завершен!</b>\n'
        'Спасибо за использование нашего сервиса! Исполнитель завершил работу над вашим заказом.\n'
        'Если у вас есть вопросы или нужна дополнительная помощь, не стесняйтесь обращаться!\n' 
        '⬇️ Вы можете оставить отзы в нашем тгк:\n'
        'https://t.me/KapitalLaba_TGK'
    )

class BotMenu(StrEnum):
    START = "start"
    
class AuthActionText(StrEnum):
    NOT_AUTH = "Вы не авторизованы. Напиши /start"