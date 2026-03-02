from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from .database import get_db_dependency
from .schemas import (
    AttendanceCreate,
    AttendanceInDB,
    AttendanceListItem,
    AttendanceSummary,
)


router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post(
    "",
    response_model=AttendanceInDB,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Employee not found"},
        status.HTTP_409_CONFLICT: {
            "description": "Attendance already marked for this employee on this date"
        },
    },
)
async def mark_attendance(
    payload: AttendanceCreate, db: AsyncIOMotorDatabase = Depends(get_db_dependency)
) -> AttendanceInDB:
    employee = await db.employees.find_one({"employee_id": payload.employee_id})
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
        )

    existing = await db.attendance.find_one(
        {"employee_id": payload.employee_id, "date": payload.date.isoformat()}
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance already marked for this employee on this date",
        )

    doc = {
        "employee_id": payload.employee_id,
        "date": payload.date.isoformat(),
        "status": payload.status,
        "created_at": datetime.utcnow(),
    }
    result = await db.attendance.insert_one(doc)
    created = await db.attendance.find_one({"_id": result.inserted_id})
    if created is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load created attendance record",
        )
    created["id"] = str(created["_id"])
    return AttendanceInDB(**created)


@router.get("", response_model=list[AttendanceListItem])
async def list_attendance(
    employee_id: Optional[str] = Query(
        default=None, description="Filter by employee ID"
    ),
    date: Optional[str] = Query(
        default=None, description="Filter by ISO date (YYYY-MM-DD)"
    ),
    db: AsyncIOMotorDatabase = Depends(get_db_dependency),
) -> list[AttendanceListItem]:
    query: dict = {}
    if employee_id:
        query["employee_id"] = employee_id
    if date:
        query["date"] = date

    records: list[AttendanceListItem] = []
    cursor = db.attendance.find(query).sort("date", -1)
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        records.append(AttendanceListItem(**doc))
    return records


@router.get("/employee/{employee_id}", response_model=list[AttendanceListItem])
async def attendance_for_employee(
    employee_id: str, db: AsyncIOMotorDatabase = Depends(get_db_dependency)
) -> list[AttendanceListItem]:
    records: list[AttendanceListItem] = []
    cursor = db.attendance.find({"employee_id": employee_id}).sort("date", -1)
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        records.append(AttendanceListItem(**doc))
    return records


@router.get("/summary", response_model=list[AttendanceSummary])
async def attendance_summary(
    db: AsyncIOMotorDatabase = Depends(get_db_dependency),
) -> list[AttendanceSummary]:
    pipeline = [
        {
            "$group": {
                "_id": {"employee_id": "$employee_id", "status": "$status"},
                "count": {"$sum": 1},
            }
        }
    ]
    aggregate_cursor = db.attendance.aggregate(pipeline)

    summary_map: dict[str, dict[str, int]] = {}
    async for row in aggregate_cursor:
        emp_id = row["_id"]["employee_id"]
        status_value = row["_id"]["status"]
        count = row["count"]
        if emp_id not in summary_map:
            summary_map[emp_id] = {"Present": 0, "Absent": 0}
        summary_map[emp_id][status_value] = count

    summaries: list[AttendanceSummary] = []
    for emp_id, counts in summary_map.items():
        employee = await db.employees.find_one({"employee_id": emp_id})
        if not employee:
            # Skip orphaned records if any.
            continue
        summaries.append(
            AttendanceSummary(
                employee_id=emp_id,
                full_name=employee["full_name"],
                total_present=counts.get("Present", 0),
                total_absent=counts.get("Absent", 0),
            )
        )

    return summaries

