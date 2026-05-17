from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.database import get_db
from app import models, schemas
from app.auth import verify_api_key

router = APIRouter(
    prefix="/api/v1/books",
    tags=["Books"]
)


@router.get("/", response_model=List[schemas.BookResponse])
def list_books(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    # joinedload tells SQLAlchemy to load authors and category
    books = db.query(models.Book).options(
        joinedload(models.Book.authors),
        joinedload(models.Book.category)
    ).offset(skip).limit(limit).all()
    return books


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
    # Check ISBN uniqueness
    existing = db.query(models.Book).filter(
        models.Book.isbn == book_in.isbn
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Book with ISBN '{book_in.isbn}' already exists"
        )

    # Check that the category exists
    category = db.query(models.Category).filter(
        models.Category.id == book_in.category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {book_in.category_id} not found"
        )

    # Separate author_ids from the rest of the book data
    book_data = book_in.model_dump(exclude={"author_ids"})
    new_book = models.Book(**book_data)

    # Handle the M:N relationship with authors
    if book_in.author_ids:
        # Fetch all authors whose IDs are in the list
        authors = db.query(models.Author).filter(
            models.Author.id.in_(book_in.author_ids)
        ).all()

        # Check all requested author IDs actually exist
        if len(authors) != len(book_in.author_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more author IDs not found"
            )

        new_book.authors = authors

    db.add(new_book)
    db.commit()
    db.refresh(new_book)

    # Re-fetch with joinedload so the response includes authors and category
    return db.query(models.Book).options(
        joinedload(models.Book.authors),
        joinedload(models.Book.category)
    ).filter(models.Book.id == new_book.id).first()


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

    # Handle author update separately (M:N relationship)
    if "author_ids" in update_data:
        author_ids = update_data.pop("author_ids")  # Remove from dict
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

    # Check ISBN uniqueness if it's being updated
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

    # Update all other scalar fields
    for field, value in update_data.items():
        setattr(book, field, value)

    db.commit()
    db.refresh(book)

    return db.query(models.Book).options(
        joinedload(models.Book.authors),
        joinedload(models.Book.category)
    ).filter(models.Book.id == book_id).first()


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

    # Cannot delete a book that has active loans
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