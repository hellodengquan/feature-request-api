from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.auth import UserIdentity, require_user, require_write_user, require_delete_user
from app.database import get_db
from app.i18n import t
from app.models import Customer
from app.schemas import CustomerCreate, CustomerUpdate, CustomerOut

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("/", response_model=CustomerOut, status_code=201)
def create_customer(
    data: CustomerCreate,
    request: Request,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_write_user),
):
    customer = Customer(**data.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/", response_model=List[CustomerOut])
def list_customers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_user),
):
    return db.query(Customer).offset(skip).limit(limit).all()


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_user),
):
    accept_lang = request.headers.get("accept-language")
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=t("customer_not_found_single", accept_lang))
    return customer


@router.put("/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    request: Request,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_write_user),
):
    accept_lang = request.headers.get("accept-language")
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=t("customer_not_found_single", accept_lang))
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(customer, key, value)
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}", status_code=204)
def delete_customer(
    customer_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_delete_user),
):
    accept_lang = request.headers.get("accept-language")
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=t("customer_not_found_single", accept_lang))
    db.delete(customer)
    db.commit()
