"""Configuración de la base de datos SQLite y de la sesión de SQLAlchemy."""
from collections.abc import Iterator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./smartticket.db"


class Base(DeclarativeBase):
    """Clase base declarativa de todas las entidades."""


def habilitar_foreign_keys(engine: Engine) -> None:
    """SQLite no valida claves foráneas salvo que se active el PRAGMA por conexión."""

    @event.listens_for(engine, "connect")
    def _activar_pragma(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
habilitar_foreign_keys(engine)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """Provee una sesión por request y garantiza su cierre."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

