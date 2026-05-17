from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import date


from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/api/v1/reports",
    tags=["Reports"]
)


@router.get("/top-borrowers", response_model=List[schemas.TopBorrowerResponse])
def top_borrowers(
    limit: int = Query(5, ge=1, le=100),
    db: Session = Depends(get_db)
):
    # JOIN members with loans, group by member, count loans per member
    results = (
        db.query(
            models.Member.id,
            models.Member.full_name,
            models.Member.email,
            func.count(models.Loan.id).label("total_loans")
        )
        .join(models.Loan, models.Loan.member_id == models.Member.id)
        .group_by(models.Member.id)
        .order_by(func.count(models.Loan.id).desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": row.id,
            "full_name": row.full_name,
            "email": row.email,
            "total_loans": row.total_loans
        }
        for row in results
    ]


@router.get("/overdue-loans", response_model=List[schemas.OverdueLoanResponse])
def overdue_loans(db: Session = Depends(get_db)):
    # JOIN loans with members and books, filter for overdue active loans
    results = (
        db.query(
            models.Loan.id.label("loan_id"),
            models.Member.full_name.label("member_name"),
            models.Book.title.label("book_title"),
            models.Loan.due_date
        )
        .join(models.Member, models.Loan.member_id == models.Member.id)
        .join(models.Book, models.Loan.book_id == models.Book.id)
        .filter(
            models.Loan.return_date == None,
            models.Loan.due_date < date.today()
        )
        .order_by(models.Loan.due_date.asc())
        .all()
    )

    return [
        {
            "loan_id": row.loan_id,
            "member_name": row.member_name,
            "book_title": row.book_title,
            "due_date": row.due_date,
            "days_overdue": (date.today() - row.due_date).days
        }
        for row in results
    ]