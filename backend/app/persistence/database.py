import os
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

DEFAULT_DATABASE_URL = (
    "sqlite:///./aeroreplan.db"
)

class Base(DeclarativeBase):
    pass


def create_database_engine(
        database_url: str | None = None
) -> Engine:
    resolved_url = (
        database_url
        or os.getenv("AEROREPLAN_DATABASE_URL",
                     DEFAULT_DATABASE_URL
                     )
    )

    connect_args = {}

    if resolved_url.startswith(
        "sqlite"
    ):
        connect_args = {"check_same_thread": False}

    return create_engine(resolved_url, connect_args=connect_args)


engine = create_database_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)

def init_database(
        target_engine: Engine | None = None
) -> None:
    from backend.app.persistence import models # noqa F401

    Base.metadata.create_all(bind=target_engine or engine)

def get_database_session():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


def create_session_factory(
        target_engine: Engine
) -> sessionmaker[Session]:
    return sessionmaker(
        bind=target_engine,
        autoflush=False,
        expire_on_commit=False,
    )

