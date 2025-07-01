# Skyfort Partner Telegram Bot
# -*- coding: utf-8 -*-

import logging
import re
import xrequests as reqs
from configs import BOT_CONFIGS, LESSONS, SpyLogButton
import notifier as notr

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram.ext import Application, PicklePersistence

from telegram.error import BadRequest


async def clear_kbd(query):
    """Убирает inline-клавиатуру у сообщения, по которому был callback."""
    try:
        await query.message.edit_reply_markup(reply_markup=None)
    except BadRequest:
        pass

JOB_NAME_TPL = "unlock_%s_lesson%d"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ------------- Conversation states -------------
REG_CONTACT, REG_NAME, REG_EMAIL, REG_FIELD = range(4)


# ------------- Helpers -------------


def menu_text() -> str:
    """Common descriptive block shown on every menu screen."""
    return (
        "Добро пожаловать!\r\nЗдесь вы найдете:\r\n"
        "• Посмотри приветственное видео для партнеров от создателя компании Ильи Опренко - https://drive.google.com/drive/u/1/folders/1rVTYA9Y5omGhL9HgQGFyAC4P4vhAxs38\r\n"
        "• Договоритесь о встрече с личным куратором и начнете эффективное обучение, после которого поймете всю широту возможностей в работе со Skyfort, для этого необходимо пройти регистрацию нажав соответствующую кнопку в меню.\r\n"
        "• После регистрации вы сможете изучить актуальные предложения и продукты, которыми мы даем возможность пользоваться на нашей платформе.\r\n"
        "\r\n"
        "Выберите нужный раздел ниже 👇"
    )


def build_main_menu(registered: bool) -> InlineKeyboardMarkup:
    """Return the main menu keyboard, locking options until `registered` is True."""
    if registered:
        keyboard = [
            [InlineKeyboardButton("Реферальная ссылка", callback_data="referral")],
            [InlineKeyboardButton("Актуальные предложения", callback_data="offers")],
            [InlineKeyboardButton("Обучение", callback_data="get_education")],
            [InlineKeyboardButton("Связаться", callback_data="contact")],
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("Регистрация", callback_data="register")],
            [InlineKeyboardButton("Связаться", callback_data="contact")],
            [InlineKeyboardButton("Реферальная ссылка 🔒", callback_data="locked")],
            [InlineKeyboardButton("Актуальные предложения 🔒", callback_data="locked")],
            # [InlineKeyboardButton("Обучение 🔒", callback_data="locked")],
        ]
    return InlineKeyboardMarkup(keyboard)


def build_lessons(progress: int):
    if progress == 0:
        keyboard = [
            [InlineKeyboardButton("1", callback_data="lesson1")],
            [InlineKeyboardButton("2 🔒", callback_data="locked")],
            [InlineKeyboardButton("3 🔒", callback_data="locked")],
            [InlineKeyboardButton("Меню", callback_data="menu")],
        ]
    elif progress == 1:
        keyboard = [
            [InlineKeyboardButton("1 ✅", callback_data="locked")],
            [InlineKeyboardButton("2", callback_data="lesson2")],
            [InlineKeyboardButton("3 🔒", callback_data="locked")],
            [InlineKeyboardButton("Меню", callback_data="menu")],
        ]
    elif progress == 2:
        keyboard = [
            [InlineKeyboardButton("1 ✅", callback_data="locked")],
            [InlineKeyboardButton("2 ✅", callback_data="locked")],
            [InlineKeyboardButton("3", callback_data="lesson3")],
            [InlineKeyboardButton("Меню", callback_data="menu")],
        ]
    return InlineKeyboardMarkup(keyboard)


def validate_email(email: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email))

video_ids = {}


async def send_video(update: Update, ctx: ContextTypes.DEFAULT_TYPE, video_path):
    chat_id = update.effective_chat.id

    video_id = video_ids.get(video_path)
    if video_id:
        await ctx.application.create_task(
            ctx.bot.send_video(chat_id, video=video_id)
        )
    else:
        msg = await ctx.bot.send_video(
            chat_id,
            video=open(video_path, "rb"),
            # caption="First upload; will be cached",
        )
        video_ids[video_path] = msg.video.file_id


# ------------- Core commands -------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get("started"):
        registered = context.user_data.get("registered", False)
        await update.message.reply_text(
            menu_text(),
            reply_markup=build_main_menu(registered),
        )
        return

    payload = context.args[0] if context.args else None
    referrer_id = int(payload) if payload and payload.isdigit() else None
    context.user_data["referrer_id"] = referrer_id

    # ---------- первый запуск ----------
    context.user_data["started"] = True  # помним, что стартовали

    """Entry command: always resets to consent screen."""
    # Cancel any running conversation for this user/chat
    if user_conv := context.user_data.get("_conversation"):  # noqa: E501 — helper key populated in conv handler
        user_conv[0].end(user_conv[1])  # (handler, key)
        context.user_data.pop("_conversation", None)

    user = update.effective_user  # telegram.User
    await reqs.ensure_tg_user(user.id, user.username)

    # consent_kb = InlineKeyboardMarkup(
    #     [[InlineKeyboardButton("Согласен на обработку персональных данных", callback_data="agree")]]
    # )
#     await update.message.reply_text(
#         "Добро пожаловать в бота для партнеров компании Skyfort!!! "
#         "Нажимайте кнопку согласен с обработкой данных и рассылками.",
# #        reply_markup=consent_kb,
#     )

    await send_video(update, context, "source4/intro.mp4")
    context.user_data.setdefault("registered", False)
    await update.message.reply_text(menu_text(), reply_markup=build_main_menu(context.user_data["registered"]))



# ------------- CallbackQuery handlers -------------
async def agree_pressed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await clear_kbd(query)
    context.user_data.setdefault("registered", False)
    await query.message.reply_text(menu_text(), reply_markup=build_main_menu(context.user_data["registered"]))


async def locked_pressed(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer("Доступк к этому разделу пока закрыт", show_alert=True)


async def contact_pressed(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await clear_kbd(query)

    await reqs.spylog_click(tg_id=update.effective_user.id, button_id=SpyLogButton["connect_start"])

    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        """📞 Нужна помощь? Напишите нам!
Мы всегда рады ответить на ваши вопросы и помочь с любыми сложностями.
📌 Контакты:
📧 Электронная почта: support@skyfort.capital
📱 Telegram: https://t.me/skyfort_support
📞 Телефон: +7 (903) 100-54-81
🌐 Сайт: [https://skyfort.capital/investors]
📱Контакты кураторов по работе с партнерами:
@tatiana_proinvest, @a_tynkov , @veronikaPal, @Valerii_Invest""",
    reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Запросить звонок", callback_data="contact_request")],
                [InlineKeyboardButton("Меню", callback_data="menu_f_contact")],
            ]
        )
    )


async def contact_request_pressed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await clear_kbd(query)

    await notr.contact_send(
        username=update.effective_user.username,
        name=context.user_data.get("phone", ""),
        phone=context.user_data.get("name", ""),
        email=context.user_data.get("email", ""),
        field_info=context.user_data.get("field", ""),
    )

    await reqs.spylog_click(tg_id=update.effective_user.id, button_id=SpyLogButton["connect_finish"])
    await reqs.spylog_click(tg_id=update.effective_user.id, button_id=SpyLogButton["connect_conv"])

    await query.message.reply_text("Спасибо за заявку!\r\nМы скоро свяжемся с Вами!\r\nТак же вы можете написать любому из нас самостоятельно в Telegram:\r\n@a_tynkov\r\n@tatiana_proinvest\r\n@veronikaPal\r\n@Valerii_Invest")
    await query.message.reply_text(menu_text(), reply_markup=build_main_menu(context.user_data["registered"]))


# ------------- Registration conversation -------------
async def register_pressed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data["registered"]:
        return

    query = update.callback_query
    await query.answer()
    await clear_kbd(query)

    tg_user = update.effective_user
    await reqs.ensure_tg_user(tg_user.id, tg_user.username)

    await reqs.spylog_click(tg_id=tg_user.id, button_id=SpyLogButton["register_start"])

    await notr.reg_send(
        username=tg_user.username
    )

    await reqs.create_userhub_if_absent(tg_user.id)

    contact_kb = ReplyKeyboardMarkup(
        [[KeyboardButton("Поделиться контактом", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await query.message.reply_text(
        "Шаг 1 из 4\n📱 Пожалуйста, предоставьте доступ к своему номеру телефона в Telegram.\n"
        "Это нужно для быстрой регистрации 👇",
        reply_markup=contact_kb,
    )
    return REG_CONTACT


async def reg_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.contact is None:
        await update.message.reply_text("Пожалуйста, используйте кнопку, чтобы отправить контакт.")
        return REG_CONTACT

    context.user_data["phone"] = update.message.contact.phone_number
    await update.message.reply_text(
        "Шаг 2 из 4\n🧾 Укажите ваше полное имя (ФИО).\nЭто поможет нам обращаться к вам корректно 👇",
        reply_markup=ReplyKeyboardRemove(),
    )
    return REG_NAME


async def reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text(
        "Шаг 3 из 4:\nВведите ваш email, чтобы:\n"
        "📢 Быть в курсе эксклюзивных акций\n📚 Получать полезные материалы для обучения\n🚀 Не упустить возможности для роста\n\nНапишите ваш email ниже 👇"
    )
    return REG_EMAIL


async def reg_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text.strip()
    if not validate_email(email):
        await update.message.reply_text("Кажется, это не похоже на email. Попробуйте ещё раз ⤵️")
        return REG_EMAIL  # остаёмся в том же состоянии

    context.user_data["email"] = email
    await update.message.reply_text(
        "Шаг 4 из 4:\n💼 Расскажите, в какой сфере вы работаете.\nЭто поможет нам подобрать самые актуальные предложения именно для вас 👇"
    )
    return REG_FIELD


async def reg_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tg_user_id = update.effective_user.id

    context.user_data["field"] = update.message.text.strip()
    context.user_data["registered"] = True

    await reqs.update_userhub_data(
        tg_id=update.effective_user.id,
        phone=context.user_data.get("phone"),
        name=context.user_data.get("name"),
        email=context.user_data.get("email"),
        field_info=context.user_data["field"],
        registered=True,
        referrer_id=context.user_data.get("referrer_id"),
    )

    await notr.register_send(
        name=context.user_data.get("phone"),
        phone=context.user_data.get("name"),
        email=context.user_data.get("email"),
        field_info=context.user_data["field"],
    )

    await reqs.spylog_click(tg_id=tg_user_id, button_id=SpyLogButton["register_finish"])

    logger.info(
        "REGISTERED REQUEST: phone=%s name=%s email=%s field=%s, refferer=%s",
        context.user_data.get("phone"),
        context.user_data.get("name"),
        context.user_data.get("email"),
        context.user_data["field"],
        context.user_data.get("referrer_id"),
    )

    await update.message.reply_text(
        "🎉 Регистрация завершена! 🎉\r\n"
        "Мы скоро свяжемся с вами! Чтобы получить больше полезной информации и начните развиваться в финансовом мире:\r\n"
        "• Присоединяйтесь к нашему закрытому каналу https://web.telegram.org/a/#-1001978569036— здесь даем эксклюзивные материалы и больше информации о том как с нами взаимодействовать и какую ценность мы даем нашим партнерам.\r\n"
        "• Рассказываем про продукты и возможности в индустрии инвестиций.\r\n"
        "Хотите начать обучение прямо сейчас? 👇",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Пройти обучение", callback_data="education")],
                [InlineKeyboardButton("Меню", callback_data="menu")],
            ]
        ),
    )
    logger.info("Registered user %s", update.effective_user.id)
    return ConversationHandler.END


async def registration_cancel(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Регистрация прервана.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# ------------- Post‑registration callbacks -------------
async def referral_pressed(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await clear_kbd(query)

    hub = await reqs.get_hub_by_tg(query.from_user.id)

    if not hub or not hub.registered:
        await query.message.reply_text(
            "Сначала завершите регистрацию, чтобы получить реферальную ссылку."
        )
        return

    deep_link = f"https://t.me/{BOT_CONFIGS.bot_name}?start={hub.id}"
    await query.message.reply_text(f"""🤝 Делитесь возможностями и зарабатывайте больше!
Это ваша персональная реферальная ссылка:
{deep_link}

Как это работает?
Все подробности вы можете узнать у куратора.""",
    reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Меню", callback_data="menu")],
            ]
        ))


async def offers_pressed(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await send_video(update, ctx, "source4/actual_products.mp4")

    await reqs.spylog_click(tg_id=update.effective_user.id, button_id=SpyLogButton["act_prod_start"])

    query = update.callback_query
    await query.answer()
    await clear_kbd(query)

    await query.message.reply_text("""Актуальные продукты:
- ссылка на сайт для партнеров Skyfort - https://skyfort.capital/partners
- ссылки на официальные каналы в telegram: 
Общий канал для партнеров https://web.telegram.org/a/#-1001978569036,
Закрытый канал для партнеров - https://web.telegram.org/a/#-1002357634416
- Презентация “актуальные продукты и сервисы” (с комиссиями для партнеров): https://drive.google.com/drive/u/1/folders/13UZUsbkYLRq4erRY4nEch2dX_96px9l1
“База знаний” для партнеров Skyfort: https://drive.google.com/drive/u/0/folders/1hxRZ2XIpdRd2paJk1Pdp8qi0Z9Kr-Gb6 
""",
    reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Запросить звонок", callback_data="products_request")],
                [InlineKeyboardButton("Меню", callback_data="menu_f_offers")],
            ]
        )
    )


async def products_request_pressed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await clear_kbd(query)

    await notr.products_send(
        name=context.user_data.get("phone"),
        phone=context.user_data.get("name"),
        email=context.user_data.get("email"),
        field_info=context.user_data["field"],
    )

    await reqs.spylog_click(tg_id=update.effective_user.id, button_id=SpyLogButton["act_prod_finish"])
    await reqs.spylog_click(tg_id=update.effective_user.id, button_id=SpyLogButton["act_prod_conv"])

    await query.message.reply_text("Спасибо за заявку!\r\nМы скоро свяжемся с Вами!\r\nТак же вы можете написать любому из нас самостоятельно в Telegram:\r\n@a_tynkov\r\n@tatiana_proinvest\r\n@veronikaPal\r\n@Valerii_Invest")
    await query.message.reply_text(menu_text(), reply_markup=build_main_menu(context.user_data["registered"]))


async def education_pressed(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await clear_kbd(query)

    await notr.start_edu_send(
        username=update.effective_user.username,
        name=ctx.user_data.get("phone"),
        phone=ctx.user_data.get("name"),
        email=ctx.user_data.get("email"),
        field_info=ctx.user_data.get("field"),
    )

    await reqs.spylog_click(tg_id=update.effective_user.id, button_id=SpyLogButton["edu_start"])

    hub = await reqs.get_hub_by_tg(tg_id=update.effective_user.id)

    if hub.lessons_progress and hub.lessons_progress >= 3:
        return

    query = update.callback_query
    await query.answer()

    await send_education(update.effective_chat.id, ctx)


async def send_education(chat_id: int, ctx: ContextTypes.DEFAULT_TYPE) -> None:

    hub = await reqs.get_hub_by_tg(chat_id)
    lesson_prog = hub.lessons_progress
    lesson_prog = 0 if lesson_prog is None else lesson_prog
    await ctx.bot.send_message(
        chat_id,
        """🔥 Готовы открыть для себя новые возможности? 🔥
После успешного завершения вводного обучения вы получите доступ к нашему закрытому каналу, где вас ждут:
💎 Эксклюзивные предложения, которые вы больше нигде не найдете!
🤝 Поддержка и общение с опытными партнерами, готовыми поделиться секретами успеха!
🚀 Возможности для развития и роста вашего дохода!
Завершите обучение, чтобы присоединиться к нам! 👇""",
        reply_markup=build_lessons(lesson_prog),
    )


async def send_finish_education(chat_id: int, ctx: ContextTypes.DEFAULT_TYPE):
    await ctx.bot.send_message(
        chat_id,
        """🎉 Поздравляем! 🎉
Вы успешно завершили вводное обучение!
🚀 Теперь доступен закрытый партнерский канал!
Внутри вас ждут:
✅ Эксклюзивные предложения и обновления
✅ Общение с успешными партнерами
✅ Инструменты для роста вашего бизнеса
Присоединяйтесь к закрытому каналу
📢 Скоро стартует расширенное обучение по управлению благосостоянием!
Оставьте обратную связь, чтобы мы могли стать лучше! 👇""",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Запишите меня на обучения", callback_data="get_education")],
            ]
        ),
    )


async def lesson1_pressed(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    tg_id = update.effective_user.id

    await query.answer()
    await reqs.update_progress(tg_id, 1)

    await send_video(update, ctx, LESSONS[0][0])

    job_name = JOB_NAME_TPL % (tg_id, 1)
    for job in ctx.job_queue.get_jobs_by_name(job_name):
        job.schedule_removal()

    ctx.job_queue.run_once(
        lambda c: send_education(update.effective_chat.id, c),
        when=LESSONS[0][1],
    )


async def lesson2_pressed(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    tg_id = update.effective_user.id

    await query.answer()
    await reqs.update_progress(tg_id, 2)

    await send_video(update, ctx, LESSONS[1][0])

    job_name = JOB_NAME_TPL % (tg_id, 2)
    for job in ctx.job_queue.get_jobs_by_name(job_name):
        job.schedule_removal()

    ctx.job_queue.run_once(
        lambda c: send_education(update.effective_chat.id, c),
        when=LESSONS[1][1],
    )


async def lesson3_pressed(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    tg_id = update.effective_user.id

    await query.answer()
    await clear_kbd(query)
    await reqs.update_progress(tg_id, 3)

    await send_video(update, ctx, LESSONS[2][0])

    job_name = JOB_NAME_TPL % (tg_id, 3)
    for job in ctx.job_queue.get_jobs_by_name(job_name):
        job.schedule_removal()

    await notr.finish_edu_send(
        username=update.effective_user.username,
        name=ctx.user_data.get("phone"),
        phone=ctx.user_data.get("name"),
        email=ctx.user_data.get("email"),
        field_info=ctx.user_data.get("field"),
    )

    await reqs.spylog_click(tg_id=update.effective_user.id, button_id=SpyLogButton["edu_finish"])

    ctx.job_queue.run_once(
        lambda c: send_finish_education(update.effective_chat.id, c),
        when=LESSONS[2][1],
    )


async def get_education_pressed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await clear_kbd(query)

    await notr.get_indiv_send(
        username=update.effective_user.username,
        name=context.user_data.get("phone"),
        phone=context.user_data.get("name"),
        email=context.user_data.get("email"),
        field_info=context.user_data.get("field"),
    )

    await reqs.spylog_click(tg_id=update.effective_user.id, button_id=SpyLogButton["edu_conv"])

    await query.message.reply_text("""📋 Вы записаны в лист ожидания!
Спасибо за интерес к расширенному обучению по управлению благосостоянием! Мы скоро свяжемся с Вами!
Так же вы можете написать любому из нас самостоятельно в Telegram: 
@a_tynkov
@tatiana_proinvest 
@veronikaPal
@Valerii_Invest""",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Посмотреть список актуальный продуктов", callback_data="offers")],
                [InlineKeyboardButton("Меню", callback_data="menu")],
            ]
        )
    )


async def menu_pressed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await clear_kbd(query)
    registered = context.user_data.get("registered", False)
    await query.message.reply_text(menu_text(), reply_markup=build_main_menu(registered))


async def menu_f_contact_pressed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reqs.spylog_click(tg_id=update.effective_user.id, button_id=SpyLogButton["connect_finish"])

    return await menu_pressed(update, context)


async def menu_f_offers_pressed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reqs.spylog_click(tg_id=update.effective_user.id, button_id=SpyLogButton["act_prod_finish"])

    return await menu_pressed(update, context)


# ------------- Main -------------

def main() -> None:
    token = BOT_CONFIGS.token
    if not token:
        raise RuntimeError("Set BOT_TOKEN environment variable")

    persistence = PicklePersistence(filepath="skyfort_bot_state.pkl")

    application = (
        Application.builder()
        .token(token)
        .persistence(persistence)
        .read_timeout(120)
        .write_timeout(120)
        .build()
    )

    # /start — always available
    application.add_handler(CommandHandler("start", start))

    # Basic callback handlers
    application.add_handler(CallbackQueryHandler(agree_pressed, pattern="^agree$"))
    application.add_handler(CallbackQueryHandler(locked_pressed, pattern="^locked$"))
    application.add_handler(CallbackQueryHandler(contact_pressed, pattern="^contact$"))
    application.add_handler(CallbackQueryHandler(referral_pressed, pattern="^referral$"))
    application.add_handler(CallbackQueryHandler(offers_pressed, pattern="^offers$"))
    application.add_handler(CallbackQueryHandler(education_pressed, pattern="^education$"))
    application.add_handler(CallbackQueryHandler(contact_request_pressed, pattern="^contact_request$"))
    application.add_handler(CallbackQueryHandler(products_request_pressed, pattern="^products_request$"))
    application.add_handler(CallbackQueryHandler(lesson1_pressed, pattern="^lesson1$"))
    application.add_handler(CallbackQueryHandler(lesson2_pressed, pattern="^lesson2$"))
    application.add_handler(CallbackQueryHandler(lesson3_pressed, pattern="^lesson3$"))
    application.add_handler(CallbackQueryHandler(get_education_pressed, pattern="^get_education$"))
    application.add_handler(CallbackQueryHandler(menu_pressed, pattern="^menu$"))
    application.add_handler(CallbackQueryHandler(menu_f_contact_pressed, pattern="^menu_f_contact$"))
    application.add_handler(CallbackQueryHandler(menu_f_offers_pressed, pattern="^menu_f_offers$"))

    # Registration conversation (added after generic handlers so that `register` is caught)
    registration_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(register_pressed, pattern="^register$")],
        states={
            REG_CONTACT: [MessageHandler(filters.CONTACT, reg_contact)],
            REG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_name)],
            REG_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_email)],
            REG_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_field)],
        },
        fallbacks=[
            CommandHandler("cancel", registration_cancel),
            CommandHandler("start", registration_cancel),  # restart resets convo
        ],
        per_user=True,
    )
    application.add_handler(registration_conv)

    # Store handler reference in user_data on conversation start so /start can cancel
    # (hook into ConversationHandler lifecycle)
    def store_conv(handler, key):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            context.user_data["_conversation"] = (handler, key)
            return await handler.callback(update, context)

        return wrapper

    registration_conv.callback = store_conv(registration_conv, registration_conv._conversations)  # type: ignore

    application.run_polling()


if __name__ == "__main__":
    main()
