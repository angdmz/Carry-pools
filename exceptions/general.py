from fastapi.responses import JSONResponse
from fastapi import status

class ResourceNotFound(Exception):
    pass


class UnprocessableEntity(Exception):
    pass


async def resource_not_found_handler(_, exc: ResourceNotFound):
    return JSONResponse({"detail": str(exc)}, status_code=status.HTTP_404_NOT_FOUND)


async def generic_unprocessable_entity_handler(_, exc: UnprocessableEntity):
    return JSONResponse({"detail": str(exc)}, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)