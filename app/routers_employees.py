from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from .database import get_db_dependency
from .schemas import EmployeeCreate, EmployeeInDB, EmployeeListItem


router = APIRouter(prefix="/employees", tags=["employees"])


@router.post(
    "",
    response_model=EmployeeInDB,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {
            "description": "Employee with same ID or email already exists"
        }
    },
)
async def create_employee(
    payload: EmployeeCreate, db: AsyncIOMotorDatabase = Depends(get_db_dependency)
) -> EmployeeInDB:
    existing = await db.employees.find_one(
        {
            "$or": [
                {"employee_id": payload.employee_id},
                {"email": payload.email},
            ]
        }
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee with this ID or email already exists",
        )

    doc = {
        "employee_id": payload.employee_id,
        "full_name": payload.full_name,
        "email": payload.email,
        "department": payload.department,
        "created_at": datetime.utcnow(),
    }
    result = await db.employees.insert_one(doc)
    created = await db.employees.find_one({"_id": result.inserted_id})
    if created is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load created employee",
        )
    created["id"] = str(created["_id"])
    return EmployeeInDB(**created)


@router.get("", response_model=list[EmployeeListItem])
async def list_employees(
    db: AsyncIOMotorDatabase = Depends(get_db_dependency),
) -> list[EmployeeListItem]:
    employees: list[EmployeeListItem] = []
    cursor = db.employees.find().sort("created_at", 1)
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        employees.append(EmployeeListItem(**doc))
    return employees


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Employee not found"}},
)
async def delete_employee(
    employee_id: str, db: AsyncIOMotorDatabase = Depends(get_db_dependency)
) -> None:
    result = await db.employees.delete_one({"employee_id": employee_id})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
        )

