import json
import threading
from typing import Dict, Any

from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from configs import BOT_CONFIGS
import asyncio
from contextlib import asynccontextmanager

if not BOT_CONFIGS.token:
    raise RuntimeError("Environment variable TELEGRAM_BOT_TOKEN is required")

bot = Bot(token=BOT_CONFIGS.token)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text=f"Ошибка доступа\n\nКод {chat_id}")


BOT_LOOP: asyncio.AbstractEventLoop | None = None   # <–– глобальный loop


def run_bot() -> None:
    """Запуск Telegram-бота в отдельном потоке с собственным event-loop."""
    global BOT_LOOP
    loop = asyncio.new_event_loop()
    BOT_LOOP = loop                   # <–– сохраняем
    asyncio.set_event_loop(loop)

    application = ApplicationBuilder().token(BOT_CONFIGS.token).build()
    application.add_handler(CommandHandler("start", start_handler))

    application.run_polling(
        close_loop=False,
        stop_signals=(),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    bot_thread = threading.Thread(target=run_bot, name="telegram-bot", daemon=True)
    bot_thread.start()
    yield


app = FastAPI(title="Telegram Notifier Service", lifespan=lifespan)


class Payload(BaseModel):
    data: Dict[str, Any]


def _send(text):

    if BOT_LOOP is None:
        print("[ERR] bot loop not ready – message not sent")
        return

    for cid in BOT_CONFIGS.recipients_ids:
        try:
            fut = asyncio.run_coroutine_threadsafe(
                bot.send_message(chat_id=cid, text=text),
                BOT_LOOP,
            )
            fut.result()
        except Exception as e:
            print(f"[WARN] failed to send to {cid}: {e}")


@app.post("/notify", status_code=202)
async def notify(payload: Payload, bg: BackgroundTasks):
    if not BOT_CONFIGS.recipients_ids:
        raise HTTPException(status_code=503, detail="No recipients configured")

    text = f"""Пользователь:
{payload.data.get("name")}
{payload.data.get("phone")}
{payload.data.get("email")}
{payload.data.get("field_info")}
Завершил регистрацию => свяжитесь 📞"""
    bg.add_task(_send, text)
    return {"status": "queued", "recipients": BOT_CONFIGS.recipients_ids}


@app.post("/notif", status_code=202)
async def notif(payload: Payload, bg: BackgroundTasks):
    if not BOT_CONFIGS.recipients_ids:
        raise HTTPException(status_code=503, detail="No recipients configured")
    text = f"""Пользователь:
@{payload.data.get("username")}
Начал регистрацию!!!"""
    bg.add_task(_send, text)
    return {"status": "queued", "recipients": BOT_CONFIGS.recipients_ids}


@app.post("/contact", status_code=202)
async def contact(payload: Payload, bg: BackgroundTasks):
    if not BOT_CONFIGS.recipients_ids:
        raise HTTPException(status_code=503, detail="No recipients configured")

    text = f"""Пользователь:
@{payload.data.get("username")}
{payload.data.get("name")}
{payload.data.get("phone")}
{payload.data.get("email")}
{payload.data.get("field_info")}
Запросил звонок в разделе <Связаться> => свяжитесь 📞"""
    bg.add_task(_send, text)
    return {"status": "queued", "recipients": BOT_CONFIGS.recipients_ids}


@app.post("/products", status_code=202)
async def products(payload: Payload, bg: BackgroundTasks):
    if not BOT_CONFIGS.recipients_ids:
        raise HTTPException(status_code=503, detail="No recipients configured")

    text = f"""Пользователь:
{payload.data.get("name")}
{payload.data.get("phone")}
{payload.data.get("email")}
{payload.data.get("field_info")}
Запросил звонок в разделе <Актуальные продукты> => свяжитесь 📞"""
    bg.add_task(_send, text)
    return {"status": "queued", "recipients": BOT_CONFIGS.recipients_ids}


@app.post("/start_edu", status_code=202)
async def contact(payload: Payload, bg: BackgroundTasks):
    if not BOT_CONFIGS.recipients_ids:
        raise HTTPException(status_code=503, detail="No recipients configured")

    text = f"""Пользователь:
@{payload.data.get("username")}
{payload.data.get("name")}
{payload.data.get("phone")}
{payload.data.get("email")}
{payload.data.get("field_info")}
Начал обучение!!!"""
    bg.add_task(_send, text)
    return {"status": "queued", "recipients": BOT_CONFIGS.recipients_ids}


@app.post("/finish_edu", status_code=202)
async def contact(payload: Payload, bg: BackgroundTasks):
    if not BOT_CONFIGS.recipients_ids:
        raise HTTPException(status_code=503, detail="No recipients configured")

    text = f"""Пользователь:
@{payload.data.get("username")}
{payload.data.get("name")}
{payload.data.get("phone")}
{payload.data.get("email")}
{payload.data.get("field_info")}
Закончил обучение!!!"""
    bg.add_task(_send, text)
    return {"status": "queued", "recipients": BOT_CONFIGS.recipients_ids}


@app.post("/get_indiv", status_code=202)
async def contact(payload: Payload, bg: BackgroundTasks):
    if not BOT_CONFIGS.recipients_ids:
        raise HTTPException(status_code=503, detail="No recipients configured")

    text = f"""Пользователь:
@{payload.data.get("username")}
{payload.data.get("name")}
{payload.data.get("phone")}
{payload.data.get("email")}
{payload.data.get("field_info")}
Записался на обучение => свяжитесь 📞"""
    bg.add_task(_send, text)
    return {"status": "queued", "recipients": BOT_CONFIGS.recipients_ids}


if __name__ == "__main__":
    import uvicorn

    host = "0.0.0.0"
    port = 2948
    reload = 0

    print(f"Starting server at http://{host}:{port} (reload={reload})…")
    uvicorn.run("main:app", host=host, port=port, reload=reload)
