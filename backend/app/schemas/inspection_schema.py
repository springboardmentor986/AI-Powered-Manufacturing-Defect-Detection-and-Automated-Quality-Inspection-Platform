from typing import Optional
from pydantic import BaseModel


class InspectionRequest(BaseModel):
    category: Optional[str] = None
    defect_type: Optional[str] = None