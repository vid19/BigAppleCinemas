from fastapi import APIRouter

router = APIRouter()


@router.post("")
async def create_reservation() -> dict[str, str]:
    return {"message": "reservation endpoint scaffold"}
