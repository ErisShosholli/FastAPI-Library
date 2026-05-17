# app/routers/books.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from typing import Optional, List
import math

from app.database import get_db
from app import models, schemas
from app.auth import verify_api_key

router = APIRouter(
    prefix="/api/v1/books",
    tags=["Books"]
)


# ─────────────────────────────────────────────
# GET /api/v1/books/search
# ─────────────────────────────────────────────
@router.get("/search", response_model=schemas.PaginatedResponse)
def search_books(
    # Free-text search on title (case-insensitive partial match)
    q: Optional[str] = Query(None, description="Partial title search"),

    # Filter by category ID
    category_id: Optional[int] = Query(None, description="Filter by category"),

    # Filter by author ID (uses the M:N relationship)
    author_id: Optional[int] = Query(None, description="Filter by author"),

    # Only show books with at least one copy available
    available_only: Optional[bool] = Query(None, description="Only available books"),

    # Year range filters
    published_after: Optional[int] = Query(None, description="Published after year"),
    published_before: Optional[int] = Query(None, description="Published before year"),

    # Sorting
    sort_by: Optional[str] = Query(
        "title",
        description="Sort by: title, published_year, popularity"
    ),
    sort_order: Optional[str] = Query(
        "asc",
        description="Sort order: asc or desc"
    ),

    # Pagination
    page: int = Query(1, ge=1, description="Page number, starts at 1"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page, max 100"),

    db: Session = Depends(get_db)
):
    # ── Validate sort parameters early ──
    # Fail fast with a clear error rather than a cryptic database error
    valid_sort_fields = ["title", "published_year", "popularity"]
    if sort_by not in valid_sort_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"sort_by must be one of: {', '.join(valid_sort_fields)}"
        )

    valid_sort_orders = ["asc", "desc"]
    if sort_order not in valid_sort_orders:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sort_order must be 'asc' or 'desc'"
        )

    # ── Build the popularity subquery ──
    loan_count_subquery = (
        db.query(func.count(models.Loan.id))
        .filter(models.Loan.book_id == models.Book.id)
        .correlate(models.Book)
        .scalar_subquery()
        .label("loan_count")
    )

    # ── Build the active loans subquery (for availability filter) ──
    active_loans_subquery = (
        db.query(func.count(models.Loan.id))
        .filter(
            models.Loan.book_id == models.Book.id,
            models.Loan.return_date == None   # NULL = active
        )
        .correlate(models.Book)
        .scalar_subquery()
    )

    # ── Start building the main query ──
    query = db.query(models.Book).options(
        joinedload(models.Book.authors),
        joinedload(models.Book.category)
    )

    # ── Apply filters one by one ──
    # Each filter is independent and adds a WHERE condition
    # All conditions are combined with AND automatically

    # 1. Free-text title search — case-insensitive partial match
    if q is not None and q.strip() != "":
        query = query.filter(models.Book.title.ilike(f"%{q}%"))

    # 2. Category filter
    if category_id is not None:
        query = query.filter(models.Book.category_id == category_id)

    # 3. Author filter — uses the M:N relationship

    if author_id is not None:
        query = query.filter(
            models.Book.authors.any(models.Author.id == author_id)
        )

    # 4. Availability filter
    # Only include books where total_copies > count of active loans
    if available_only:
        query = query.filter(
            models.Book.total_copies > active_loans_subquery
        )

    # 5. Year range filters
    if published_after is not None:
        query = query.filter(models.Book.published_year >= published_after)

    if published_before is not None:
        query = query.filter(models.Book.published_year <= published_before)

    # ── Count total BEFORE pagination ──
    count_query = db.query(func.count(models.Book.id)).filter(
        *[
        ]
    )

    count_base = db.query(func.count(models.Book.id.distinct()))

    # Re-apply all the same filters to the count query
    if q is not None and q.strip() != "":
        count_base = count_base.filter(models.Book.title.ilike(f"%{q}%"))

    if category_id is not None:
        count_base = count_base.filter(models.Book.category_id == category_id)

    if author_id is not None:
        count_base = count_base.filter(
            models.Book.authors.any(models.Author.id == author_id)
        )

    if available_only:
        count_base = count_base.filter(
            models.Book.total_copies > active_loans_subquery
        )

    if published_after is not None:
        count_base = count_base.filter(models.Book.published_year >= published_after)

    if published_before is not None:
        count_base = count_base.filter(models.Book.published_year <= published_before)

    # Execute the count query — returns a single integer
    total = count_base.scalar()

    # ── Apply sorting ──
    if sort_by == "title":
        if sort_order == "asc":
            query = query.order_by(models.Book.title.asc())
        else:
            query = query.order_by(models.Book.title.desc())

    elif sort_by == "published_year":
        if sort_order == "asc":
            query = query.order_by(models.Book.published_year.asc())
        else:
            query = query.order_by(models.Book.published_year.desc())

    elif sort_by == "popularity":
        # Sort by the loan_count subquery
        if sort_order == "asc":
            query = query.order_by(loan_count_subquery.asc())
        else:
            query = query.order_by(loan_count_subquery.desc())

    # ── Apply pagination ──
    skip = (page - 1) * page_size
    books = query.offset(skip).limit(page_size).all()

    # ── Calculate total_pages ──
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    # ── Return paginated response ──
    return {
        "items": books,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages
    }


# ─────────────────────────────────────────────
# GET /api/v1/books — List all books (paginated)
# ─────────────────────────────────────────────
@router.get("/", response_model=List[schemas.BookResponse])
def list_books(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    books = db.query(models.Book).options(
        joinedload(models.Book.authors),
        joinedload(models.Book.category)
    ).offset(skip).limit(limit).all()
    return books


# ─────────────────────────────────────────────
# GET /api/v1/books/{book_id} — Get one book
# ─────────────────────────────────────────────
@router.get("/{book_id}", response_model=schemas.BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(models.Book).options(
        joinedload(models.Book.authors),
        joinedload(models.Book.category)
    ).filter(models.Book.id == book_id).first()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found"
        )
    return book


# ─────────────────────────────────────────────
# POST /api/v1/books — Create a book
# ─────────────────────────────────────────────
@router.post(
    "/",
    response_model=schemas.BookResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_api_key)]
)
def create_book(
    book_in: schemas.BookCreate,
    db: Session = Depends(get_db)
):
    existing = db.query(models.Book).filter(
        models.Book.isbn == book_in.isbn
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Book with ISBN '{book_in.isbn}' already exists"
        )

    category = db.query(models.Category).filter(
        models.Category.id == book_in.category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {book_in.category_id} not found"
        )

    book_data = book_in.model_dump(exclude={"author_ids"})
    new_book = models.Book(**book_data)

    if book_in.author_ids:
        authors = db.query(models.Author).filter(
            models.Author.id.in_(book_in.author_ids)
        ).all()

        if len(authors) != len(book_in.author_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more author IDs not found"
            )
        new_book.authors = authors

    db.add(new_book)
    db.commit()
    db.refresh(new_book)

    return db.query(models.Book).options(
        joinedload(models.Book.authors),
        joinedload(models.Book.category)
    ).filter(models.Book.id == new_book.id).first()


# ─────────────────────────────────────────────
# PATCH /api/v1/books/{book_id} — Update a book
# ─────────────────────────────────────────────
@router.patch(
    "/{book_id}",
    response_model=schemas.BookResponse,
    dependencies=[Depends(verify_api_key)]
)
def update_book(
    book_id: int,
    book_in: schemas.BookUpdate,
    db: Session = Depends(get_db)
):
    book = db.query(models.Book).options(
        joinedload(models.Book.authors),
        joinedload(models.Book.category)
    ).filter(models.Book.id == book_id).first()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found"
        )

    update_data = book_in.model_dump(exclude_unset=True)

    if "author_ids" in update_data:
        author_ids = update_data.pop("author_ids")
        if author_ids is not None:
            authors = db.query(models.Author).filter(
                models.Author.id.in_(author_ids)
            ).all()
            if len(authors) != len(author_ids):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="One or more author IDs not found"
                )
            book.authors = authors

    if "isbn" in update_data:
        existing = db.query(models.Book).filter(
            models.Book.isbn == update_data["isbn"],
            models.Book.id != book_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"ISBN '{update_data['isbn']}' is already in use"
            )

    for field, value in update_data.items():
        setattr(book, field, value)

    db.commit()
    db.refresh(book)

    return db.query(models.Book).options(
        joinedload(models.Book.authors),
        joinedload(models.Book.category)
    ).filter(models.Book.id == book_id).first()


# ─────────────────────────────────────────────
# DELETE /api/v1/books/{book_id} — Delete a book
# ─────────────────────────────────────────────
@router.delete(
    "/{book_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_api_key)]
)
def delete_book(
    book_id: int,
    db: Session = Depends(get_db)
):
    book = db.query(models.Book).filter(
        models.Book.id == book_id
    ).first()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found"
        )

    active_loans = db.query(models.Loan).filter(
        models.Loan.book_id == book_id,
        models.Loan.return_date == None
    ).count()

    if active_loans > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete book {book_id}: it has {active_loans} active loan(s)"
        )

    db.delete(book)
    db.commit()
    return {"detail": f"Book {book_id} deleted successfully"}