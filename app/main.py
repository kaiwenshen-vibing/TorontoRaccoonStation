from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import redis.asyncio as redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import FeatureNotImplementedError, ServiceError

app = FastAPI(title="Store Scheduler API", version="0.1.0")
app.include_router(api_router)


@app.get("/healthz", tags=["system"])
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["system"])
async def ready() -> JSONResponse:
    db_status = "ok"
    redis_status = "ok"
    try:
        settings = get_settings()
    except ValidationError:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "db": "missing", "redis": "missing"},
        )

    if not settings.redis_url:
        redis_status = "missing"
    else:
        redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        try:
            await redis_client.ping()
        except Exception:
            redis_status = "down"
        finally:
            await redis_client.aclose()

    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("select 1"))
    except Exception:
        db_status = "down"
    finally:
        await engine.dispose()

    status_code = 200 if db_status == "ok" and redis_status == "ok" else 503
    status_text = "ok" if status_code == 200 else "error"
    return JSONResponse(
        status_code=status_code,
        content={"status": status_text, "db": db_status, "redis": redis_status},
    )


@app.exception_handler(FeatureNotImplementedError)
async def feature_not_implemented_handler(
    _request,
    exc: FeatureNotImplementedError,
) -> JSONResponse:
    return JSONResponse(
        status_code=501,
        content={"code": "not_implemented", "message": str(exc)},
    )


@app.exception_handler(ServiceError)
async def service_error_handler(
    _request,
    exc: ServiceError,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": str(exc)},
    )

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8080)
