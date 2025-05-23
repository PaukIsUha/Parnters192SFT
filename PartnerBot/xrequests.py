from baseclasses import *
from functools import wraps
from typing import Callable, TypeVar, Coroutine, Any, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker
)
from sqlalchemy import select
from datetime import datetime, timezone

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    class_=AsyncSession,
)

F = TypeVar("F", bound=Callable[..., Coroutine[Any, Any, Any]])


def _wrap_async(
        iso: str,
        commit: bool,
) -> Callable[[F], F]:
    """Внутренняя обёртка с выбором isolation level + (no)commit."""

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):  # type: ignore[override]
            async with AsyncSessionLocal() as session:
                # isolation per-transaction
                await session.connection(
                    execution_options={"isolation_level": iso}
                )
                try:
                    result = await func(*args, session=session, **kwargs)
                    if commit:
                        await session.commit()
                    return result
                except Exception:
                    await session.rollback()
                    raise

        return wrapper  # type: ignore[return-value]

    return decorator


adb_request = _wrap_async("READ COMMITTED", commit=False)  # read-only
adb_update = _wrap_async("SERIALIZABLE", commit=True)  # write + commit


@adb_update
async def ensure_tg_user(tg_id: int, handle: Optional[str], *, session, ) -> TgUser:
    """
    Создаёт запись в tg_users, если нет. Если сменился @handle, обновляет.
    Работает в транзакции SERIALIZABLE с авто-commit.
    """
    tg_user = await session.get(TgUser, tg_id)
    if tg_user is None:
        tg_user = TgUser(
            id=tg_id,
            handle=handle or f"user_{tg_id}",
        )
        session.add(tg_user)
    elif handle and tg_user.handle != handle:
        tg_user.handle = handle
    return tg_user


@adb_update
async def create_userhub_if_absent(tg_id: int, *, session) -> UserHub:
    """
    Гарантирует запись в userhub, связанную с tg_id.
    Поля phone / name / field_info остаются NULL,
    registered и dtime берут значения по умолчанию.
    """
    stmt = select(UserHub).where(UserHub.tg_id == tg_id)
    entry = await session.scalar(stmt)
    if entry is None:
        entry = UserHub(tg_id=tg_id)  # остальные колонки по умолчанию
        session.add(entry)
    return entry


@adb_update
async def update_userhub_data(
        tg_id: int,
        *,
        phone: str | None,
        name: str | None,
        email: str | None,
        field_info: str,
        registered: bool,
        referrer_id: int | None = None,  # ← НОВЫЙ параметр
        session,
) -> UserHub:
    hub: UserHub | None = await session.scalar(
        select(UserHub).where(UserHub.tg_id == tg_id)
    )
    if hub is None:
        raise RuntimeError(f"userhub row for tg_id={tg_id} not found")

    # базовые поля
    hub.phone = phone
    hub.name = name
    hub.email = email
    hub.field_info = field_info
    hub.registered = registered
    hub.dtime = datetime.now(timezone.utc)

    if (
            referrer_id
            and referrer_id != hub.id  # не сами себе
            and hub.referrer_id is None  # ещё не установлен
    ):
        # проверяем, существует ли такой партнёр
        exists = await session.scalar(
            select(UserHub.id).where(UserHub.id == referrer_id)
        )
        if exists:
            hub.referrer_id = referrer_id
    # -----------------------------------------------------------------------------

    return hub


@adb_request
async def get_hub_by_tg(tg_id: int, *, session) -> UserHub | None:
    """Вернуть запись userhub по Telegram-ID (или None, если её ещё нет)."""
    return await session.scalar(select(UserHub).where(UserHub.tg_id == tg_id))


@adb_update
async def update_progress(tg_id: int, new_progress: int, *, session):
    hub: UserHub | None = await session.scalar(
        select(UserHub).where(UserHub.tg_id == tg_id)
    )
    if hub is None:
        # raise RuntimeError(f"userhub row for tg_id={tg_id} not found")
        print(f"userhub row for tg_id={tg_id} not found")
        return

    hub.lessons_progress = new_progress

    return hub


@adb_update
async def spylog_click(
    tg_id: int,
    button_id: int,
    *,                       # session будет передан декоратором как kw-arg
    session
) -> Click:
    """
    Сохраняет клик в БД и возвращает созданный объект.
    Работает в отдельной транзакции с уровнем изоляции SERIALIZABLE,
    commit выполняет сам декоратор ``adb_update``.

    Parameters
    ----------
    tg_id : int
        Идентификатор пользователя из tg_users.id
    button_id : int
        Идентификатор кнопки
    session : AsyncSession
        Автоматически передаётся декоратором, указывать при вызове не нужно.

    Returns
    -------
    Click
        Созданный объект Click c заполненными id и ts.
    """
    # (необязательно) убеждаемся, что пользователь существует —
    # так ловим ошибку заранее, а не на ограничении FK
    if not await session.scalar(select(TgUser).filter_by(id=tg_id)):
        raise ValueError(f"TgUser {tg_id} not found")

    click = Click(tg_user_id=tg_id, button_id=button_id)
    session.add(click)

    await session.flush()        # click.id и click.ts уже доступны

    return click
