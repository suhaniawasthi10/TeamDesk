from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class EmployeeWrite(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: Annotated[str, Field(min_length=1, max_length=120)]
    email: Annotated[EmailStr, Field(max_length=254)]
    department: Annotated[str, Field(min_length=1, max_length=80)]
    job_title: Annotated[str, Field(min_length=1, max_length=120)]
    joining_date: date

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()


class EmployeeRead(EmployeeWrite):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
