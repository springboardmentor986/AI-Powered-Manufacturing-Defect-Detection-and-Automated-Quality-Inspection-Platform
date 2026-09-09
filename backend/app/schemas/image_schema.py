from typing import Literal

from pydantic import BaseModel


class ImageReviewRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    notes: str | None = None
