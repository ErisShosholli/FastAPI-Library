from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas
from app.auth import verify_api_key

router = APIRouter(
    prefix="/api/v1/categories",
    tags=["Categories"]
)


# ─────────────────────────────────────────────
# GET /api/v1/categories — List all categories
# ─────────────────────────────────────────────
@router.get("/", response_model=List[schemas.CategoryResponse])
def list_categories(
    skip: int = 0,          # How many records to skip (for pagination)
    limit: int = 100,       # How many records to return
    db: Session = Depends(get_db)   # FastAPI injects the DB session
):
    categories = db.query(models.Category).offset(skip).limit(limit).all()
    return categories


# ─────────────────────────────────────────────
# GET /api/v1/categories/{id} — Get one category
# ─────────────────────────────────────────────
@router.get("/{category_id}", response_model=schemas.CategoryResponse)
def get_category(
    category_id: int,       #reads this from the URL path
    db: Session = Depends(get_db)
):

    category = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()

    # If no category found with that ID, return 404
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )
    return category


# ─────────────────────────────────────────────
# POST /api/v1/categories — Create a category
# ─────────────────────────────────────────────

@router.post(
    "/",
    response_model=schemas.CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_api_key)]
)
def create_category(
    category_in: schemas.CategoryCreate,   # Request body — validated by Pydantic
    db: Session = Depends(get_db)
):
    # Check if a category with this name already exists
    existing = db.query(models.Category).filter(
        models.Category.name == category_in.name
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category '{category_in.name}' already exists"
        )

    # Create a new SQLAlchemy model instance 
    new_category = models.Category(**category_in.model_dump())

    db.add(new_category)        # Stage the new record 
    db.commit()                 # Save to database 
    db.refresh(new_category)    # Reload from DB to get generated id

    return new_category


# ─────────────────────────────────────────────
# PATCH /api/v1/categories/{id} — Update a category
# ─────────────────────────────────────────────
@router.patch(
    "/{category_id}",
    response_model=schemas.CategoryResponse,
    dependencies=[Depends(verify_api_key)]
)
def update_category(
    category_id: int,
    category_in: schemas.CategoryUpdate,
    db: Session = Depends(get_db)
):
    category = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )

    update_data = category_in.model_dump(exclude_unset=True)

    # Loop through each field and update the SQLAlchemy object
    for field, value in update_data.items():
        setattr(category, field, value)  # like: category.name = "Science"

    db.commit()
    db.refresh(category)
    return category


# ─────────────────────────────────────────────
# DELETE /api/v1/categories/{id} — Delete a category
# ─────────────────────────────────────────────
@router.delete(
    "/{category_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_api_key)]
)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    category = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )

    db.delete(category)
    db.commit()

    return {"detail": f"Category {category_id} deleted successfully"}