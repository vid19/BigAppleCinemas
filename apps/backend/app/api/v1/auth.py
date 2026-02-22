from fastapi import APIRouter

router = APIRouter()


@router.post("/register")
async def register() -> dict[str, str]:
    return {"message": "register endpoint scaffold"}


@router.post("/login")
async def login() -> dict[str, str]:
    return {"message": "login endpoint scaffold"}
