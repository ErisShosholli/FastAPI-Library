from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas
from app.auth import verify_api_key

router = APIRouter(
    prefix="/api/v1/members",
    tags=["Members"]
)


@router.get("/", response_model=List[schemas.MemberResponse])
def list_members(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    members = db.query(models.Member).offset(skip).limit(limit).all()
    return members


@router.get("/{member_id}", response_model=schemas.MemberResponse)
def get_member(member_id: int, db: Session = Depends(get_db)):
    member = db.query(models.Member).filter(
        models.Member.id == member_id
    ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member with id {member_id} not found"
        )
    return member


@router.post(
    "/",
    response_model=schemas.MemberResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_api_key)]
)
def create_member(
    member_in: schemas.MemberCreate,
    db: Session = Depends(get_db)
):
    # Check email uniqueness before inserting
    existing = db.query(models.Member).filter(
        models.Member.email == member_in.email
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{member_in.email}' is already registered"
        )

    # model_dump() converts Pydantic schema to a plain dict
    member_data = member_in.model_dump()

    # If join_date not provided, set it to today
    if member_data.get("join_date") is None:
        from datetime import date
        member_data["join_date"] = date.today()

    new_member = models.Member(**member_data)
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member


@router.patch(
    "/{member_id}",
    response_model=schemas.MemberResponse,
    dependencies=[Depends(verify_api_key)]
)
def update_member(
    member_id: int,
    member_in: schemas.MemberUpdate,
    db: Session = Depends(get_db)
):
    member = db.query(models.Member).filter(
        models.Member.id == member_id
    ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member with id {member_id} not found"
        )

    # If client is updating email, check it's not taken by another member
    update_data = member_in.model_dump(exclude_unset=True)

    if "email" in update_data:
        existing = db.query(models.Member).filter(
            models.Member.email == update_data["email"],
            models.Member.id != member_id   # Exclude the current member
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{update_data['email']}' is already in use"
            )

    for field, value in update_data.items():
        setattr(member, field, value)

    db.commit()
    db.refresh(member)
    return member


@router.delete(
    "/{member_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_api_key)]
)
def delete_member(
    member_id: int,
    db: Session = Depends(get_db)
):
    member = db.query(models.Member).filter(
        models.Member.id == member_id
    ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member with id {member_id} not found"
        )

    # Check for active loans — return_date IS NULL means still borrowed
    active_loans = db.query(models.Loan).filter(
        models.Loan.member_id == member_id,
        models.Loan.return_date == None     # NULL = active loan
    ).count()


    if active_loans > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete member {member_id}: they have {active_loans} active loan(s)"
        )

    db.delete(member)
    db.commit()
    return {"detail": f"Member {member_id} deleted successfully"}