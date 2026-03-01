from datetime import datetime

from pydantic import BaseModel


class HelloResponse(BaseModel):
    message: str
    cpp_result: int
    created_at: datetime

    model_config = {"from_attributes": True}
