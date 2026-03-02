from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import get_db
from .routers_attendance import router as attendance_router
from .routers_employees import router as employees_router


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    # Ensure we can connect to the database on startup.
    db = get_db()
    await db.command("ping")

    # Create indexes for uniqueness and performance.
    await db.employees.create_index("employee_id", unique=True)
    await db.employees.create_index("email", unique=True)
    await db.attendance.create_index(
        [("employee_id", 1), ("date", 1)], unique=True
    )

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend domain.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    employees_router,
    prefix=f"{settings.API_V1_PREFIX}",
)
app.include_router(
    attendance_router,
    prefix=f"{settings.API_V1_PREFIX}",
)


@app.get("/")
async def root():
    return {"message": "HRMS Lite API is running"}

