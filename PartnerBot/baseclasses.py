from sqlalchemy import (
    create_engine, Column, Integer, Text,
    Boolean, TIMESTAMP, func, ForeignKey
)
from configs import DATABASE_CONFIGS
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = (
    DATABASE_CONFIGS()
)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)
Base = declarative_base()


class TgUser(Base):
    __tablename__ = "tg_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    handle = Column(Text, nullable=False)
    is_no_prod = Column(Boolean, server_default="false")
    dtime = Column(TIMESTAMP(timezone=True),
                   server_default=func.now())

    userhub_entries = relationship(
        "UserHub",
        back_populates="tg_user",
        lazy="dynamic"
    )
    clicks = relationship(
        "Click",
        back_populates="tg_user",
        lazy="dynamic"
    )


class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_user_id = Column(Integer, ForeignKey("tg_users.id"), nullable=False)
    button_id = Column(Integer, nullable=False)
    ts = Column(TIMESTAMP(timezone=True), server_default=func.now())

    tg_user = relationship("TgUser", back_populates="clicks")


class UserHub(Base):
    __tablename__ = "userhub"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(Text)
    name = Column(Text)
    email = Column(Text)
    field_info = Column(Text)
    registered = Column(Boolean, server_default="false")
    dtime = Column(TIMESTAMP(timezone=True),
                   server_default=func.now())
    tg_id = Column(Integer, ForeignKey("tg_users.id"))
    referrer_id = Column(Integer, ForeignKey("userhub.id"))
    lessons_progress = Column(Integer)

    tg_user = relationship("TgUser", back_populates="userhub_entries")
    referrer = relationship("UserHub", remote_side=[id])
