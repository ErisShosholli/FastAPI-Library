from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


# ══════════════════════════════════════════════
# CATEGORY SCHEMAS
# ══════════════════════════════════════════════

# Base: shared fields between create and response
class CategoryBase(BaseModel):
    name: str                         


# Create: what the client sends in the POST body
# 
class CategoryCreate(CategoryBase):
    pass                               


# Update: for PATCH — all fields optional
class CategoryUpdate(BaseModel):
    name: Optional[str] = None


# Response: what we send back to the client
class CategoryResponse(CategoryBase):
    id: int                            

    # read data from SQLAlchemy object attributes
    # Without this, CategoryResponse(category_object) would fail
    model_config = ConfigDict(from_attributes=True)


# ══════════════════════════════════════════════
# AUTHOR SCHEMAS
# ══════════════════════════════════════════════

class AuthorBase(BaseModel):
    full_name: str
    country: Optional[str] = None      # Country is optional


class AuthorCreate(AuthorBase):
    pass


class AuthorUpdate(BaseModel):
    full_name: Optional[str] = None
    country: Optional[str] = None


class AuthorResponse(AuthorBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ══════════════════════════════════════════════
# BOOK SCHEMAS
# ══════════════════════════════════════════════

# This is the minimal author info 
class AuthorSummary(BaseModel):
    id: int
    full_name: str
    model_config = ConfigDict(from_attributes=True)


# Minimal category info embedded inside book response
class CategorySummary(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class BookBase(BaseModel):
    title: str
    isbn: str
    category_id: int
    total_copies: int = 1              # Default to 1 copy if not specified
    published_year: Optional[int] = None

    # Validator: makes sure total_copies is never negative
    @field_validator("total_copies")
    @classmethod
    def total_copies_must_be_positive(cls, value):
        if value < 0:
            # Raising ValueError makes Pydantic return a 422 error automatically
            raise ValueError("total_copies must be 0 or greater")
        return value


class BookCreate(BookBase):
    # When creating a book, the client can optionally provide author IDs
    author_ids: List[int] = []         # Default: empty list (no authors yet)


class BookUpdate(BaseModel):
    # All fields optional for partial update (PATCH)
    title: Optional[str] = None
    isbn: Optional[str] = None
    category_id: Optional[int] = None
    total_copies: Optional[int] = None
    published_year: Optional[int] = None
    author_ids: Optional[List[int]] = None

    @field_validator("total_copies")
    @classmethod
    def total_copies_must_be_positive(cls, value):
        # value could be None (field not included in PATCH) — that's fine
        if value is not None and value < 0:
            raise ValueError("total_copies must be 0 or greater")
        return value


class BookResponse(BaseModel):
    id: int
    title: str
    isbn: str
    total_copies: int
    published_year: Optional[int]

    # Instead of returning just category_id (a number),
    # we embed the full category object so the client sees the name too
    category: CategorySummary

    # Instead of returning author_ids, we embed a list of author objects
    authors: List[AuthorSummary]

    model_config = ConfigDict(from_attributes=True)


# ══════════════════════════════════════════════
# MEMBER SCHEMAS
# ══════════════════════════════════════════════

class MemberBase(BaseModel):
    full_name: str
    email: EmailStr


class MemberCreate(MemberBase):
    # join_date defaults to today if not provided
    join_date: Optional[date] = None
    is_active: bool = True


class MemberUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class MemberResponse(MemberBase):
    id: int
    join_date: date
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


# ══════════════════════════════════════════════
# LOAN SCHEMAS
# ══════════════════════════════════════════════

# Minimal member info embedded in loan response
class MemberSummary(BaseModel):
    id: int
    full_name: str
    email: str
    model_config = ConfigDict(from_attributes=True)


# Minimal book info embedded in loan response
class BookSummary(BaseModel):
    id: int
    title: str
    isbn: str
    model_config = ConfigDict(from_attributes=True)


class LoanCreate(BaseModel):
    member_id: int
    book_id: int
    due_date: date                    

    # Validator
    @field_validator("due_date")
    @classmethod
    def due_date_must_be_future(cls, value):
        if value <= date.today():
            raise ValueError("due_date must be a future date")
        return value


class LoanResponse(BaseModel):
    id: int
    loan_date: date
    due_date: date
    return_date: Optional[date] = None

    # embed member and book info so the client doesn't need extra requests
    member: MemberSummary
    book: BookSummary

    model_config = ConfigDict(from_attributes=True)


# ══════════════════════════════════════════════
# PAGINATION SCHEMAS
# ══════════════════════════════════════════════
class PaginatedResponse(BaseModel):
    items: list                        # The actual data items for this page
    page: int                          # Current page number
    page_size: int                     # How many items per page
    total: int                         # Total matching items (before pagination)
    total_pages: int                   # How many pages exist in total


# ══════════════════════════════════════════════
# REPORT SCHEMAS
# ══════════════════════════════════════════════

# Response shape for the top-borrowers report
class TopBorrowerResponse(BaseModel):
    id: int
    full_name: str
    email: str
    total_loans: int                   # The count of all loans (active + returned)
    model_config = ConfigDict(from_attributes=True)


# Response shape for each item in the overdue-loans report
class OverdueLoanResponse(BaseModel):
    loan_id: int
    member_name: str
    book_title: str
    due_date: date
    days_overdue: int                  
    model_config = ConfigDict(from_attributes=True)


# ══════════════════════════════════════════════
# ERROR SCHEMA
# ══════════════════════════════════════════════

# Structured error response — used for 404, 409, 400, 401 errors

class ErrorResponse(BaseModel):
    detail: str                       