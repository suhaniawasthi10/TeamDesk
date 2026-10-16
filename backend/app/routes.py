from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Employee
from app.schemas import EmployeeRead, EmployeeWrite

router = APIRouter(prefix="/api/employees", tags=["Employees"])
Database = Annotated[Session, Depends(get_db)]


def find_employee(employee_id: int, db: Session) -> Employee:
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


def save_employee(employee: Employee, db: Session) -> Employee:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if getattr(exc.orig, "sqlstate", None) == "23505":
            raise HTTPException(
                status_code=409, detail="An employee with this email already exists"
            ) from exc
        raise
    db.refresh(employee)
    return employee


@router.get("", response_model=list[EmployeeRead])
def list_employees(db: Database):
    return db.scalars(select(Employee).order_by(Employee.id.desc())).all()


@router.get("/{employee_id}", response_model=EmployeeRead)
def get_employee(employee_id: int, db: Database):
    return find_employee(employee_id, db)


@router.post("", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeWrite, db: Database):
    employee = Employee(**payload.model_dump())
    db.add(employee)
    return save_employee(employee, db)


@router.put("/{employee_id}", response_model=EmployeeRead)
def update_employee(employee_id: int, payload: EmployeeWrite, db: Database):
    employee = find_employee(employee_id, db)
    for field, value in payload.model_dump().items():
        setattr(employee, field, value)
    return save_employee(employee, db)


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(employee_id: int, db: Database):
    db.delete(find_employee(employee_id, db))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
