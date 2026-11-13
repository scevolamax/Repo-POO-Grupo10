"""Punto de entrada de la API SmartTicket."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import models  # noqa: F401  (registra las entidades en Base.metadata)
from app.database import Base, engine
from app.exceptions import ConflictoError, DomainError, RecursoNoEncontradoError, ReglaNegocioError
from app.routers import TODOS_LOS_ROUTERS

# Traducción de familias de errores de dominio a HTTP (OCP: una nueva
# excepción hereda de una familia y no requiere tocar este mapa).
STATUS_POR_FAMILIA: dict[type[DomainError], int] = {
    RecursoNoEncontradoError: 404,
    ConflictoError: 409,
    ReglaNegocioError: 400,
}


def status_para(error: DomainError) -> int:
    for clase in type(error).__mro__:
        if clase in STATUS_POR_FAMILIA:
            return STATUS_POR_FAMILIA[clase]
    return 400


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="SmartTicket API",
    version="1.0.0",
    description="TP 9 - GRASP y SOLID aplicados: venta de entradas y control de acceso.",
    lifespan=lifespan,
)

for router in TODOS_LOS_ROUTERS:
    app.include_router(router)


@app.exception_handler(DomainError)
async def manejar_error_de_dominio(_request: Request, error: DomainError) -> JSONResponse:
    return JSONResponse(status_code=status_para(error), content={"detail": error.mensaje})

