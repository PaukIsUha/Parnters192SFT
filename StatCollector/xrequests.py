from baseclasses import *
from functools import wraps
from typing import Callable, TypeVar, Coroutine, Any, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker
)
from sqlalchemy import select
from datetime import datetime, timezone
import datetime as _dt
import zoneinfo
from sqlalchemy.orm import sessionmaker



F = TypeVar("F", bound=Callable[..., Coroutine[Any, Any, Any]])
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

PARIS = zoneinfo.ZoneInfo("Europe/Moscow")


def _yesterday() -> _dt.date:
    return _dt.datetime.now(PARIS).date() # - _dt.timedelta(days=1)


def get_yesterday_users_started() -> int:
    target_day = _yesterday()
    global SessionLocal
    with SessionLocal() as session:
        q = (
            select(func.count(TgUser.id))
            .where(func.date(TgUser.dtime) == target_day)
            .where(TgUser.is_no_prod.is_(False))          # ← нужный фильтр
        )
        return session.execute(q).scalar_one()


def get_yesterday_users_registered() -> int:
    target_day = _yesterday()
    global SessionLocal
    with SessionLocal() as session:
        q = (
            select(func.count(UserHub.id))
            .select_from(UserHub)
            .join(TgUser, UserHub.tg_id == TgUser.id)      # JOIN к tg_users
            .where(UserHub.registered.is_(True))
            .where(func.date(UserHub.dtime) == target_day)
            .where(TgUser.is_no_prod.is_(False))           # ← тот же фильтр
        )
        return session.execute(q).scalar_one()


def get_today_clicks_by_button() -> list[tuple[int, int]]:
    """
    Возвращает список пар (button_id, clicks_count) за текущий день
    для пользователей, у которых is_no_prod = FALSE.

    Пример результата:
        [(1, 27), (2, 13), (5, 42)]
    """
    today_date = _dt.datetime.now(PARIS).date()

    with SessionLocal() as session:
        stmt = (
            select(Click.button_id, func.count(Click.id))
            .select_from(Click)
            .join(TgUser, Click.tg_user_id == TgUser.id, isouter=True)   # LEFT JOIN
            .where(TgUser.is_no_prod.is_(False))                         # фильтр пользователей
            .where(func.date(Click.ts) == today_date)                    # клики за «сегодня»
            .group_by(Click.button_id)
            .order_by(Click.button_id)
        )
        return session.execute(stmt).all()   # [(button_id, count), ...]


