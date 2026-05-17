# scripts/seed.py

import sys
import os

# Add the project root to Python's path so we can import from app/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta
from app.database import SessionLocal, engine, Base
from app import models

# Create all tables if they don't exist yet
Base.metadata.create_all(bind=engine)


def clear_data(db):
    # Delete in reverse dependency order to respect foreign keys
    db.query(models.Loan).delete()
    db.query(models.Book).delete()

    # Clear the M:N join table via the association table directly
    from app.database import Base
    models.book_authors.delete(bind=engine)

    db.query(models.Author).delete()
    db.query(models.Category).delete()
    db.query(models.Member).delete()
    db.commit()


def seed():
    db = SessionLocal()

    try:
        # ── Clear existing data ──
        db.query(models.Loan).delete()

        # Clear book_authors join table
        db.execute(models.book_authors.delete())

        db.query(models.Book).delete()
        db.query(models.Author).delete()
        db.query(models.Category).delete()
        db.query(models.Member).delete()
        db.commit()

        # ─────────────────────────────────────────────
        # CATEGORIES
        # ─────────────────────────────────────────────
        fiction = models.Category(name="Fiction")
        science = models.Category(name="Science")
        history = models.Category(name="History")
        technology = models.Category(name="Technology")
        philosophy = models.Category(name="Philosophy")

        db.add_all([fiction, science, history, technology, philosophy])
        db.commit()

        # ─────────────────────────────────────────────
        # AUTHORS
        # ─────────────────────────────────────────────
        orwell = models.Author(full_name="George Orwell", country="United Kingdom")
        huxley = models.Author(full_name="Aldous Huxley", country="United Kingdom")
        tolkien = models.Author(full_name="J.R.R. Tolkien", country="United Kingdom")
        hawking = models.Author(full_name="Stephen Hawking", country="United Kingdom")
        mlodinow = models.Author(full_name="Leonard Mlodinow", country="United States")
        harari = models.Author(full_name="Yuval Noah Harari", country="Israel")
        knuth = models.Author(full_name="Donald Knuth", country="United States")
        martin = models.Author(full_name="Robert C. Martin", country="United States")
        nietzsche = models.Author(full_name="Friedrich Nietzsche", country="Germany")
        plato = models.Author(full_name="Plato", country="Greece")

        db.add_all([
            orwell, huxley, tolkien, hawking,
            mlodinow, harari, knuth, martin, nietzsche, plato
        ])
        db.commit()

        # ─────────────────────────────────────────────
        # BOOKS
        # ─────────────────────────────────────────────
        # Format: models.Book(fields...) then assign .authors list for M:N

        b1 = models.Book(
            title="1984",
            isbn="978-0451524935",
            category_id=fiction.id,
            total_copies=3,
            published_year=1949
        )
        b1.authors = [orwell]

        b2 = models.Book(
            title="Animal Farm",
            isbn="978-0451526342",
            category_id=fiction.id,
            total_copies=2,
            published_year=1945
        )
        b2.authors = [orwell]

        b3 = models.Book(
            title="Brave New World",
            isbn="978-0060850524",
            category_id=fiction.id,
            total_copies=2,
            published_year=1932
        )
        b3.authors = [huxley]

        b4 = models.Book(
            title="The Lord of the Rings",
            isbn="978-0618640157",
            category_id=fiction.id,
            total_copies=3,
            published_year=1954
        )
        b4.authors = [tolkien]

        b5 = models.Book(
            title="The Hobbit",
            isbn="978-0547928227",
            category_id=fiction.id,
            total_copies=2,
            published_year=1937
        )
        b5.authors = [tolkien]

        b6 = models.Book(
            title="A Brief History of Time",
            isbn="978-0553380163",
            category_id=science.id,
            total_copies=2,
            published_year=1988
        )
        b6.authors = [hawking]

        b7 = models.Book(
            title="The Grand Design",
            isbn="978-0553840926",
            category_id=science.id,
            total_copies=2,
            published_year=2010
        )
        # Multiple authors — satisfies the "3 books with more than one author" requirement
        b7.authors = [hawking, mlodinow]

        b8 = models.Book(
            title="Sapiens: A Brief History of Humankind",
            isbn="978-0062316097",
            category_id=history.id,
            total_copies=3,
            published_year=2011
        )
        b8.authors = [harari]

        b9 = models.Book(
            title="Homo Deus",
            isbn="978-0062464316",
            category_id=history.id,
            total_copies=2,
            published_year=2015
        )
        b9.authors = [harari]

        b10 = models.Book(
            title="21 Lessons for the 21st Century",
            isbn="978-0525512172",
            category_id=history.id,
            total_copies=2,
            published_year=2018
        )
        b10.authors = [harari]

        b11 = models.Book(
            title="The Art of Computer Programming",
            isbn="978-0201896831",
            category_id=technology.id,
            total_copies=2,
            published_year=1968
        )
        b11.authors = [knuth]

        b12 = models.Book(
            title="Clean Code",
            isbn="978-0132350884",
            category_id=technology.id,
            total_copies=3,
            published_year=2008
        )
        b12.authors = [martin]

        b13 = models.Book(
            title="The Clean Coder",
            isbn="978-0137081073",
            category_id=technology.id,
            total_copies=2,
            published_year=2011
        )
        b13.authors = [martin]

        b14 = models.Book(
            title="Clean Architecture",
            isbn="978-0134494166",
            category_id=technology.id,
            total_copies=2,
            published_year=2017
        )
        b14.authors = [martin]

        b15 = models.Book(
            title="Beyond Good and Evil",
            isbn="978-0679724650",
            category_id=philosophy.id,
            total_copies=2,
            published_year=1886
        )
        b15.authors = [nietzsche]

        b16 = models.Book(
            title="Thus Spoke Zarathustra",
            isbn="978-0140441185",
            category_id=philosophy.id,
            total_copies=2,
            published_year=1883
        )
        b16.authors = [nietzsche]

        b17 = models.Book(
            title="The Republic",
            isbn="978-0140455113",
            category_id=philosophy.id,
            total_copies=2,
            published_year=-380
        )
        b17.authors = [plato]

        b18 = models.Book(
            title="Doors of Perception",
            isbn="978-0060900518",
            category_id=philosophy.id,
            total_copies=1,
            published_year=1954
        )
        b18.authors = [huxley]

        b19 = models.Book(
            title="The Grand Inquisitor",
            isbn="978-0872202522",
            category_id=philosophy.id,
            total_copies=1,
            published_year=1880
        )
        b19.authors = [nietzsche, plato]

        b20 = models.Book(
            title="The Briefest History of Time",
            isbn="978-1250301697",
            category_id=science.id,
            total_copies=2,
            published_year=2020
        )
        # Another multi-author book
        b20.authors = [hawking, mlodinow]

        all_books = [
            b1, b2, b3, b4, b5, b6, b7, b8, b9, b10,
            b11, b12, b13, b14, b15, b16, b17, b18, b19, b20
        ]
        db.add_all(all_books)
        db.commit()

        # ─────────────────────────────────────────────
        # MEMBERS
        # ─────────────────────────────────────────────
        members = [
            models.Member(
                full_name="Alice Johnson",
                email="alice@example.com",
                join_date=date(2024, 1, 10),
                is_active=True
            ),
            models.Member(
                full_name="Bob Smith",
                email="bob@example.com",
                join_date=date(2024, 2, 5),
                is_active=True
            ),
            models.Member(
                full_name="Carol White",
                email="carol@example.com",
                join_date=date(2024, 3, 15),
                is_active=True
            ),
            models.Member(
                full_name="David Brown",
                email="david@example.com",
                join_date=date(2024, 4, 20),
                is_active=True
            ),
            models.Member(
                full_name="Eva Martinez",
                email="eva@example.com",
                join_date=date(2024, 5, 1),
                is_active=True
            ),
            models.Member(
                full_name="Frank Lee",
                email="frank@example.com",
                join_date=date(2024, 6, 12),
                is_active=True
            ),
            models.Member(
                full_name="Grace Kim",
                email="grace@example.com",
                join_date=date(2024, 7, 8),
                is_active=True
            ),
            models.Member(
                full_name="Henry Davis",
                email="henry@example.com",
                join_date=date(2024, 8, 22),
                is_active=True
            ),
            models.Member(
                full_name="Iris Wilson",
                email="iris@example.com",
                join_date=date(2024, 9, 30),
                is_active=True
            ),
            models.Member(
                full_name="Jack Taylor",
                email="jack@example.com",
                join_date=date(2024, 10, 5),
                is_active=False  # Inactive member — useful for testing 400 on borrow
            ),
        ]

        db.add_all(members)
        db.commit()

        # Shorthand references for loan creation below
        alice, bob, carol, david, eva, frank, grace, henry, iris, jack = members

        # ─────────────────────────────────────────────
        # LOANS
        # Mix of: returned, active, overdue
        # ─────────────────────────────────────────────
        today = date.today()

        loans = [
            # ── Returned loans (return_date is set) ──
            models.Loan(
                member_id=alice.id, book_id=b1.id,
                loan_date=date(2026, 1, 5),
                due_date=date(2026, 1, 25),
                return_date=date(2026, 1, 20)
            ),
            models.Loan(
                member_id=alice.id, book_id=b2.id,
                loan_date=date(2026, 1, 25),
                due_date=date(2026, 2, 14),
                return_date=date(2026, 2, 10)
            ),
            models.Loan(
                member_id=alice.id, book_id=b8.id,
                loan_date=date(2026, 2, 15),
                due_date=date(2026, 3, 7),
                return_date=date(2026, 3, 1)
            ),
            models.Loan(
                member_id=bob.id, book_id=b3.id,
                loan_date=date(2026, 1, 10),
                due_date=date(2026, 1, 30),
                return_date=date(2026, 1, 28)
            ),
            models.Loan(
                member_id=bob.id, book_id=b6.id,
                loan_date=date(2026, 2, 1),
                due_date=date(2026, 2, 21),
                return_date=date(2026, 2, 18)
            ),
            models.Loan(
                member_id=bob.id, book_id=b12.id,
                loan_date=date(2026, 2, 22),
                due_date=date(2026, 3, 14),
                return_date=date(2026, 3, 10)
            ),
            models.Loan(
                member_id=carol.id, book_id=b4.id,
                loan_date=date(2026, 1, 15),
                due_date=date(2026, 2, 4),
                return_date=date(2026, 2, 1)
            ),
            models.Loan(
                member_id=carol.id, book_id=b9.id,
                loan_date=date(2026, 2, 10),
                due_date=date(2026, 3, 2),
                return_date=date(2026, 2, 27)
            ),
            models.Loan(
                member_id=david.id, book_id=b5.id,
                loan_date=date(2026, 1, 20),
                due_date=date(2026, 2, 9),
                return_date=date(2026, 2, 5)
            ),
            models.Loan(
                member_id=david.id, book_id=b11.id,
                loan_date=date(2026, 2, 12),
                due_date=date(2026, 3, 4),
                return_date=date(2026, 3, 1)
            ),
            models.Loan(
                member_id=eva.id, book_id=b7.id,
                loan_date=date(2026, 1, 8),
                due_date=date(2026, 1, 28),
                return_date=date(2026, 1, 25)
            ),
            models.Loan(
                member_id=eva.id, book_id=b13.id,
                loan_date=date(2026, 2, 5),
                due_date=date(2026, 2, 25),
                return_date=date(2026, 2, 22)
            ),
            models.Loan(
                member_id=frank.id, book_id=b15.id,
                loan_date=date(2026, 1, 12),
                due_date=date(2026, 2, 1),
                return_date=date(2026, 1, 30)
            ),
            models.Loan(
                member_id=grace.id, book_id=b17.id,
                loan_date=date(2026, 1, 18),
                due_date=date(2026, 2, 7),
                return_date=date(2026, 2, 4)
            ),
            models.Loan(
                member_id=henry.id, book_id=b20.id,
                loan_date=date(2026, 2, 3),
                due_date=date(2026, 2, 23),
                return_date=date(2026, 2, 20)
            ),

            # ── Active loans (return_date is None = still borrowed) ──
            models.Loan(
                member_id=alice.id, book_id=b12.id,
                loan_date=today - timedelta(days=5),
                due_date=today + timedelta(days=14),
                return_date=None
            ),
            models.Loan(
                member_id=bob.id, book_id=b1.id,
                loan_date=today - timedelta(days=3),
                due_date=today + timedelta(days=18),
                return_date=None
            ),
            models.Loan(
                member_id=carol.id, book_id=b8.id,
                loan_date=today - timedelta(days=7),
                due_date=today + timedelta(days=10),
                return_date=None
            ),
            models.Loan(
                member_id=david.id, book_id=b14.id,
                loan_date=today - timedelta(days=2),
                due_date=today + timedelta(days=20),
                return_date=None
            ),
            models.Loan(
                member_id=eva.id, book_id=b16.id,
                loan_date=today - timedelta(days=6),
                due_date=today + timedelta(days=12),
                return_date=None
            ),
            models.Loan(
                member_id=frank.id, book_id=b4.id,
                loan_date=today - timedelta(days=4),
                due_date=today + timedelta(days=15),
                return_date=None
            ),
            models.Loan(
                member_id=grace.id, book_id=b6.id,
                loan_date=today - timedelta(days=1),
                due_date=today + timedelta(days=21),
                return_date=None
            ),

            # ── Overdue loans (due_date in past, return_date is None) ──
            models.Loan(
                member_id=alice.id, book_id=b3.id,
                loan_date=today - timedelta(days=45),
                due_date=today - timedelta(days=15),
                return_date=None
            ),
            models.Loan(
                member_id=bob.id, book_id=b9.id,
                loan_date=today - timedelta(days=50),
                due_date=today - timedelta(days=20),
                return_date=None
            ),
            models.Loan(
                member_id=carol.id, book_id=b11.id,
                loan_date=today - timedelta(days=40),
                due_date=today - timedelta(days=10),
                return_date=None
            ),
            models.Loan(
                member_id=david.id, book_id=b2.id,
                loan_date=today - timedelta(days=35),
                due_date=today - timedelta(days=5),
                return_date=None
            ),
            models.Loan(
                member_id=henry.id, book_id=b5.id,
                loan_date=today - timedelta(days=60),
                due_date=today - timedelta(days=30),
                return_date=None
            ),
            models.Loan(
                member_id=iris.id, book_id=b18.id,
                loan_date=today - timedelta(days=55),
                due_date=today - timedelta(days=25),
                return_date=None
            ),
            models.Loan(
                member_id=frank.id, book_id=b19.id,
                loan_date=today - timedelta(days=38),
                due_date=today - timedelta(days=8),
                return_date=None
            ),
            models.Loan(
                member_id=grace.id, book_id=b10.id,
                loan_date=today - timedelta(days=42),
                due_date=today - timedelta(days=12),
                return_date=None
            ),
            models.Loan(
                member_id=henry.id, book_id=b15.id,
                loan_date=today - timedelta(days=33),
                due_date=today - timedelta(days=3),
                return_date=None
            ),
            models.Loan(
                member_id=iris.id, book_id=b7.id,
                loan_date=today - timedelta(days=48),
                due_date=today - timedelta(days=18),
                return_date=None
            ),
            models.Loan(
                member_id=bob.id, book_id=b17.id,
                loan_date=today - timedelta(days=52),
                due_date=today - timedelta(days=22),
                return_date=None
            ),
            models.Loan(
                member_id=carol.id, book_id=b20.id,
                loan_date=today - timedelta(days=36),
                due_date=today - timedelta(days=6),
                return_date=None
            ),
            models.Loan(
                member_id=eva.id, book_id=b13.id,
                loan_date=today - timedelta(days=44),
                due_date=today - timedelta(days=14),
                return_date=None
            ),
            models.Loan(
                member_id=david.id, book_id=b16.id,
                loan_date=today - timedelta(days=30),
                due_date=today - timedelta(days=2),
                return_date=None
            ),
        ]

        db.add_all(loans)
        db.commit()

        print("Seed complete.")
        print(f"  Categories : 5")
        print(f"  Authors    : 10")
        print(f"  Books      : 20")
        print(f"  Members    : 10")
        print(f"  Loans      : {len(loans)}")
        print(f"    Returned : 15")
        print(f"    Active   : 7")
        print(f"    Overdue  : 13")

    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()