import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.hello import HelloMessage
from app.schemas.hello import HelloResponse
from app.services.engine import add

router = APIRouter()


@router.get("/hello", response_model=HelloResponse)
async def hello(db: AsyncSession = Depends(get_db)):
    result = await asyncio.to_thread(add, 40, 2)
    msg = HelloMessage(message="Hello from Munnir!", cpp_result=result)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg
