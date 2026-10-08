from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.models import Book, Member, RFIDTag


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        book = db.query(Book).filter(Book.accession_no == "DEMO-0001").first()
        if not book:
            book = Book(accession_no="DEMO-0001", isbn="9780000000001", title="RFID Systems Engineering", author="AISYS Demo", category="Technology")
            db.add(book)
            db.flush()
        if not db.query(RFIDTag).filter(RFIDTag.tag_id == "RFID-DEMO-0001").first():
            db.add(RFIDTag(tag_id="RFID-DEMO-0001", book_id=book.id))
        if not db.query(Member).filter(Member.member_no == "M-DEMO-01").first():
            db.add(Member(member_no="M-DEMO-01", name="Demo Member", email="demo@example.local"))
        db.commit()
        print("Demo records ready: DEMO-0001, M-DEMO-01, RFID-DEMO-0001")
    finally:
        db.close()


if __name__ == "__main__":
    main()
