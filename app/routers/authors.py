# app/routers/authors.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas
from app.auth import verify_api_key

router = APIRouter(
    prefix="/api/v1/authors",
    tags=["Authors"]
)


@router.get("/", response_model=List[schemas.AuthorResponse])
def list_authors(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    authors = db.query(models.Author).offset(skip).limit(limit).all()
    return authors


@router.get("/{author_id}", response_model=schemas.AuthorResponse)
def get_author(author_id: int, db: Session = Depends(get_db)):
    author = db.query(models.Author).filter(
        models.Author.id == author_id
    ).first()

    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Author with id {author_id} not found"
        )
    return author


@router.post(
    "/",
    response_model=schemas.AuthorResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_api_key)]
)
def create_author(
    author_in: schemas.AuthorCreate,
    db: Session = Depends(get_db)
):
    new_author = models.Author(**author_in.model_dump())
    db.add(new_author)
    db.commit()
    db.refresh(new_author)
    return new_author


@router.patch(
    "/{author_id}",
    response_model=schemas.AuthorResponse,
    dependencies=[Depends(verify_api_key)]
)
def update_author(
    author_id: int,
    author_in: schemas.AuthorUpdate,
    db: Session = Depends(get_db)
):
    author = db.query(models.Author).filter(
        models.Author.id == author_id
    ).first()

    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Author with id {author_id} not found"
        )

    update_data = author_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(author, field, value)

    db.commit()
    db.refresh(author)
    return author


@router.delete(
    "/{author_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_api_key)]
)
def delete_author(
    author_id: int,
    db: Session = Depends(get_db)
):
    author = db.query(models.Author).filter(
        models.Author.id == author_id
    ).first()

    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Author with id {author_id} not found"
        )

    db.delete(author)
    db.commit()
    return {"detail": f"Author {author_id} deleted successfully"}