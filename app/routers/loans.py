from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import Optional
from datetime import date

from app.database import get_db
from app import models, schemas
from app.auth import verify_api_key

router = APIRouter(
    prefix="/api/v1/loans",
    tags=["Loans"]
)


# ─────────────────────────────────────────────
# GET /api/v1/loans — List loans with filters
# ─────────────────────────────────────────────
@router.get("/", response_model=schemas.PaginatedResponse)
def list_loans(
    # Optional filters — all have defaults so they're not required
    member_id: Optional[int] = Query(None, description="Filter by member ID"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),

    # status filter: "active", "returned", or "overdue"
    # None means no filter — return all
    loan_status: Optional[str] = Query(
        None,
        alias="status",           
        description="Filter by status: active, returned, overdue"
    ),

    # Pagination parameters
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),

    db: Session = Depends(get_db)
):
    # Start building the query 
    query = db.query(models.Loan).options(
        joinedload(models.Loan.member),
        joinedload(models.Loan.book)
    )

    # Apply member_id filter if provided
    if member_id is not None:
        query = query.filter(models.Loan.member_id == member_id)

    # Apply book_id filter if provided
    if book_id is not None:
        query = query.filter(models.Loan.book_id == book_id)

    # Apply status filter if provided
    if loan_status is not None:
        if loan_status == "active":
            # Active = not yet returned (return_date is NULL)
            query = query.filter(models.Loan.return_date == None)

        elif loan_status == "returned":
            # Returned = has a return_date (not NULL)
            query = query.filter(models.Loan.return_date != None)

        elif loan_status == "overdue":
            # Overdue = not returned AND past the due date
            query = query.filter(
                and_(
                    models.Loan.return_date == None,        # Still out
                    models.Loan.due_date < date.today()     # Past due
                )
            )
        else:
            # If an invalid status is provided, tell the client
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="status must be one of: active, returned, overdue"
            )

    # Count total matching records BEFORE applying pagination
    total = query.count()

    # Calculate how many records to skip
    # Page 1 → skip 0, Page 2 → skip 20, Page 3 → skip 40, etc.
    skip = (page - 1) * page_size

    # Apply pagination and get results
    loans = query.offset(skip).limit(page_size).all()

    # Calculate total pages — math.ceil equivalent
    # e.g. 45 items / 20 per page = 2.25 → 3 pages
    import math
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    # Return in the PaginatedResponse shape the assignment requires
    return {
        "items": loans,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages
    }


# ─────────────────────────────────────────────
# POST /api/v1/loans — Borrow a book
# ─────────────────────────────────────────────
@router.post(
    "/",
    response_model=schemas.LoanResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_api_key)]
)
def borrow_book(
    loan_in: schemas.LoanCreate,
    db: Session = Depends(get_db)
):
    # ── Step 1: Check the member exists ──
    member = db.query(models.Member).filter(
        models.Member.id == loan_in.member_id
    ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member with id {loan_in.member_id} not found"
        )

    # ── Step 2: Check the member is active ─
    if not member.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Member {loan_in.member_id} is not active and cannot borrow books"
        )

    # ── Step 3: Check the book exists ──
    book = db.query(models.Book).filter(
        models.Book.id == loan_in.book_id
    ).first()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {loan_in.book_id} not found"
        )

    # ── Step 4: Check available copies ──
    # Count how many copies of this book are currently out (not returned)
    active_loans_count = db.query(models.Loan).filter(
        models.Loan.book_id == loan_in.book_id,
        models.Loan.return_date == None     # NULL = still borrowed
    ).count()

    # available = total copies - currently borrowed copies
    available_copies = book.total_copies - active_loans_count

   
    if available_copies <= 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No copies of book {loan_in.book_id} are currently available"
        )

    # ── Step 5: Create the loan ──
    new_loan = models.Loan(
        member_id=loan_in.member_id,
        book_id=loan_in.book_id,
        due_date=loan_in.due_date,
        loan_date=date.today(),     # Always set to today 
        return_date=None            # NULL = book is still out (active loan)
    )

    db.add(new_loan)
    db.commit()
    db.refresh(new_loan)

    # Re-fetch with member and book loaded so the response includes them
    return db.query(models.Loan).options(
        joinedload(models.Loan.member),
        joinedload(models.Loan.book)
    ).filter(models.Loan.id == new_loan.id).first()


# ─────────────────────────────────────────────
# POST /api/v1/loans/{id}/return — Return a book
# ─────────────────────────────────────────────
@router.post(
    "/{loan_id}/return",
    response_model=schemas.LoanResponse,
    dependencies=[Depends(verify_api_key)]
)
def return_book(
    loan_id: int,
    db: Session = Depends(get_db)
):
    # ── Step 1: Find the loan ──
    loan = db.query(models.Loan).options(
        joinedload(models.Loan.member),
        joinedload(models.Loan.book)
    ).filter(models.Loan.id == loan_id).first()

    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan with id {loan_id} not found"
        )

    # ── Step 2: Check if already returned ──
    if loan.return_date is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Loan {loan_id} has already been returned on {loan.return_date}"
        )

    # ── Step 3: Mark as returned ──
    loan.return_date = date.today()

    db.commit()
    db.refresh(loan)
    return loan