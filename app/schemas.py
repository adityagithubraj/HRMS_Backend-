from datetime import date, datetime
from typing import Optional

from email_validator import validate_email, EmailNotValidError
from fastapi import HTTPException, status
from pydantic import BaseModel, Field, field_validator


class EmployeeBase(BaseModel):
    employee_id: str = Field(..., min_length=1, max_length=32)
    full_name: str = Field(..., min_length=1, max_length=128)
    email: str = Field(..., min_length=3, max_length=256)
    department: str = Field(..., min_length=1, max_length=64)

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value: str) -> str:
        try:
            result = validate_email(value, check_deliverability=False)
        except EmailNotValidError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid email address format",
            ) from exc
        return result.normalized


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeInDB(EmployeeBase):
    id: str
    created_at: datetime

    class Config:
        populate_by_name = True


class EmployeeListItem(EmployeeBase):
    id: str

    class Config:
        populate_by_name = True


class AttendanceStatus(str):
    PRESENT = "Present"
    ABSENT = "Absent"


class AttendanceBase(BaseModel):
    employee_id: str = Field(..., min_length=1, max_length=32)
    date: date
    status: str

    @field_validator("date")
    @classmethod
    def validate_date_not_future(cls, value: date) -> date:
        today = date.today()
        if value > today:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Attendance date cannot be in the future",
            )
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.capitalize()
        if normalized not in {AttendanceStatus.PRESENT, AttendanceStatus.ABSENT}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Status must be 'Present' or 'Absent'",
            )
        return normalized


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceInDB(AttendanceBase):
    id: str
    created_at: datetime

    class Config:
        populate_by_name = True


class AttendanceListItem(AttendanceBase):
    id: str

    class Config:
        populate_by_name = True


class AttendanceSummary(BaseModel):
    employee_id: str
    full_name: str
    total_present: int
    total_absent: int


class APIError(BaseModel):
    detail: str
    field: Optional[str] = None

