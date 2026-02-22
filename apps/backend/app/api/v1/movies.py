from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_movies() -> dict[str, list[dict[str, str]]]:
    return {"items": []}
