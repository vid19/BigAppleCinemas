from fastapi import APIRouter

router = APIRouter()


@router.post("/scan")
async def scan_ticket() -> dict[str, str]:
    return {"message": "ticket scan endpoint scaffold"}
