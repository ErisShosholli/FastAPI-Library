from datetime import datetime, date


from sqlalchemy import (
    Column, Integer, String, Boolean,
    Date, DateTime, ForeignKey, Table, CheckConstraint
)

# relationship = defines how models connect to each other in Python

from sqlalchemy.orm import relationship

# Import Base from our database.py
from app.database import Base


# ─────────────────────────────────────────────
# ASSOCIATION TABLE (Many-to-Many: books ↔ authors)
# ─────────────────────────────────────────────

book_authors = Table(
    "book_authors",         
    Base.metadata,          
    Column("book_id", Integer, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
    Column("author_id", Integer, ForeignKey("authors.id", ondelete="CASCADE"), primary_key=True)

)


# ─────────────────────────────────────────────
# MEMBERS TABLE
# ─────────────────────────────────────────────
class Member(Base):
    # __tablename__ tells SQLAlchemy what to name this table in the database
    __tablename__ = "members"

    # Primary key — auto-increments (1, 2, 3, ...)
    id = Column(Integer, primary_key=True, index=True)

    # The member's full name — cannot be empty (nullable=False)
    full_name = Column(String(255), nullable=False)

    # Email must be unique — no two members share an email
    # index=True creates a database index for faster lookups
    email = Column(String(255), unique=True, nullable=False, index=True)

    # The date the member joined the library
    # default=date.today means: if not provided, use today's date
    join_date = Column(Date, default=date.today, nullable=False)

    # Whether the member can borrow books
    # default=True means new members are active by default
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationship: one member → many loans
    loans = relationship("Loan", back_populates="member", cascade="all, delete-orphan")


# ─────────────────────────────────────────────
# CATEGORIES TABLE
# ─────────────────────────────────────────────
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)

    # Category name must be unique — no duplicate categories
    name = Column(String(100), unique=True, nullable=False, index=True)

    # Relationship: one category → many books
    books = relationship("Book", back_populates="category")


# ─────────────────────────────────────────────
# AUTHORS TABLE
# ─────────────────────────────────────────────
class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String(255), nullable=False)

    # Country is optional — some authors may be unknown
    country = Column(String(100), nullable=True)

    # Relationship: many authors ↔ many books
    # secondary=book_authors tells SQLAlchemy to use the join table
    books = relationship("Book", secondary=book_authors, back_populates="authors")


# ─────────────────────────────────────────────
# BOOKS TABLE
# ─────────────────────────────────────────────
class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(500), nullable=False, index=True)

    # ISBN must be unique — every book edition has a unique ISBN
    isbn = Column(String(20), unique=True, nullable=False)

    # Foreign key: links to the categories table
    # This is the "many" side: many books → one category
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    # How many physical copies the library owns
    # CheckConstraint ensures this never goes below 0
    total_copies = Column(Integer, nullable=False, default=1)

    published_year = Column(Integer, nullable=True)

    # Database-level constraint: total_copies must be ≥ 0
    # This is enforced by the database itself, not just our Python code
    __table_args__ = (
        CheckConstraint("total_copies >= 0", name="check_total_copies_positive"),
    )

    # Relationship: many books → one category
    category = relationship("Category", back_populates="books")

    # Relationship: many books ↔ many authors (using the join table)
    authors = relationship("Author", secondary=book_authors, back_populates="books")

    # Relationship: one book → many loans
    loans = relationship("Loan", back_populates="book", cascade="all, delete-orphan")


# ─────────────────────────────────────────────
# LOANS TABLE
# ─────────────────────────────────────────────
class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign key: which member borrowed the book
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)

    # Foreign key: which book was borrowed
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)

    # The date the book was borrowed
    # default=date.today: automatically set to today when created
    loan_date = Column(Date, default=date.today, nullable=False)

    # The date the book must be returned by
    due_date = Column(Date, nullable=False)

    # The date the book was actually returned
    # nullable=True means it CAN be NULL — NULL = book is still out (active loan)
    # This is the key field: NULL = active loan, a date = returned loan
    return_date = Column(Date, nullable=True)

    # Relationships — let us do: loan.member and loan.book in Python
    member = relationship("Member", back_populates="loans")
    book = relationship("Book", back_populates="loans")