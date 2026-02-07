from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.errors import FeatureNotImplementedError

app = FastAPI(title="Store Scheduler API", version="0.1.0")
app.include_router(api_router)


@app.get("/healthz", tags=["system"])
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(FeatureNotImplementedError)
async def feature_not_implemented_handler(
    _request,
    exc: FeatureNotImplementedError,
) -> JSONResponse:
    return JSONResponse(
        status_code=501,
        content={"code": "not_implemented", "message": str(exc)},
    )

