from app.core.errors import FeatureNotImplementedError
from app.schemas.script import ScriptListResponse
from app.services.base import BaseService


class ScriptService(BaseService):
    async def list_store_scripts(self, store_id: int, limit: int, offset: int) -> ScriptListResponse:
        raise FeatureNotImplementedError("list_store_scripts is not implemented yet.")

