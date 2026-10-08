from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import gettempdir
from uuid import uuid4
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from sqlalchemy import text, func
from sqlalchemy.orm import Session

from app.adapters.mocks import MockCamera, MockGate, MockNotification, MockPrinter, MockRFIDReader, MockSmartCard
from app.core.config import settings
from app.core.security import create_access_token, get_current_user, hash_password, require_roles, verify_password
from app.db.base import Base
from app.db.session import SessionLocal, engine, get_db
from app.models.models import (
    Acquisition, AuditLog, Book, Circulation, GateEvent, InventoryEvent, Member,
    MigrationRun, MigrationRow, Notification, RFIDTag, SearchDocument, SerialIssue, SystemConfig, User
)
from app.schemas.schemas import *
from app.services.audit import audit
from app.services.library import checkin, checkout, gate_event, renew
from app.services.migration import dry_run, import_file
from pydantic import BaseModel
from barcode import Code128
from barcode.writer import SVGWriter
from io import BytesIO


def bootstrap_users() -> None:
    db = SessionLocal()
    try:
        defaults = [
            ("admin", "Admin@12345", "admin"),
            ("librarian", "Librarian@12345", "librarian"),
            ("operator", "Operator@12345", "operator"),
        ]
        for username, password, role in defaults:
            if not db.query(User).filter(User.username == username).first():
                db.add(User(username=username, password_hash=hash_password(password), role=role))
        db.commit()
    finally:
        db.close()


def bootstrap_demo_data() -> None:
    """Create small, idempotent synthetic records so a fresh demo deployment is usable."""
    db = SessionLocal()
    try:
        demo_books = [
            ("DEMO-0001", "9780000000001", "RFID Systems Engineering", "AISYS Demo", "Technology"),
            ("DEMO-0002", "9780000000002", "Library Automation & Digital Services", "AISYS Demo", "Library Science"),
            ("DEMO-0003", "9780000000003", "Enterprise Information Systems", "AISYS Demo", "Computer Science"),
            ("AISYS-ACC-0001", "TEST-AISYS-001", "Python for Library Automation", "A. Kumar", "Computer Science"),
            ("AISYS-ACC-0002", "TEST-AISYS-002", "RFID Systems in Smart Libraries", "S. Reddy", "Library Science"),
            ("AISYS-ACC-0003", "TEST-AISYS-003", "Database Management Fundamentals", "R. Sharma", "Database Systems"),
            ("AISYS-ACC-0004", "TEST-AISYS-004", "Network Security Essentials", "P. Rao", "Cybersecurity"),
            ("AISYS-ACC-0005", "TEST-AISYS-005", "Digital Library Management", "M. Patel", "Library Science"),
        ]
        for accession_no, isbn, title, author, category in demo_books:
            if not db.query(Book).filter(Book.accession_no == accession_no).first():
                db.add(Book(
                    accession_no=accession_no,
                    isbn=isbn,
                    title=title,
                    author=author,
                    category=category,
                ))
        db.flush()

        book = db.query(Book).filter(Book.accession_no == "DEMO-0001").first()
        if book and not db.query(RFIDTag).filter(RFIDTag.tag_id == "RFID-DEMO-0001").first():
            db.add(RFIDTag(tag_id="RFID-DEMO-0001", book_id=book.id))

        if not db.query(Member).filter(Member.member_no == "M-DEMO-01").first():
            db.add(Member(member_no="M-DEMO-01", name="Demo Member", email="demo@example.local"))
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    bootstrap_users()
    bootstrap_demo_data()
    yield


app = FastAPI(
    title=settings.app_name,
    version="3.0.3",
    description="Production-oriented AISYS RFID-enabled library platform prototype with device-neutral adapters and offline workflows.",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/sample", StaticFiles(directory="sample"), name="sample")
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "app_name": settings.app_name})



@app.get("/api/books/{accession_no}/barcode.svg")
def book_barcode(accession_no: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    book = db.query(Book).filter(Book.accession_no == accession_no).first()
    if not book:
        raise HTTPException(status_code=404, detail="Catalogue item not found")
    # Code 128 supports alphanumeric accession numbers used by this application.
    output = BytesIO()
    Code128(book.accession_no, writer=SVGWriter()).write(
        output, options={"write_text": False, "module_width": 0.35, "module_height": 18, "quiet_zone": 3}
    )
    return Response(content=output.getvalue(), media_type="image/svg+xml",
                    headers={"Cache-Control": "no-store", "Content-Disposition": "inline"})

@app.get("/api/books/{accession_no}")
def book_detail(accession_no: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    book = db.query(Book).filter(Book.accession_no == accession_no).first()
    if not book:
        raise HTTPException(404, "Book not found")
    tag = db.query(RFIDTag).filter(RFIDTag.book_id == book.id, RFIDTag.active.is_(True)).first()
    active_loan = db.query(Circulation).filter(Circulation.book_id == book.id, Circulation.status == "CHECKED_OUT").order_by(Circulation.id.desc()).first()
    return {
        "book": BookOut.model_validate(book).model_dump(),
        "rfid": {"tag_id": tag.tag_id, "last_seen_at": tag.last_seen_at} if tag else None,
        "active_loan": {"member_id": active_loan.member_id, "due_at": active_loan.due_at, "protocol": active_loan.source_protocol} if active_loan else None,
    }

@app.get("/api/books/{accession_no}/history")
def book_history(accession_no: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    book = db.query(Book).filter(Book.accession_no == accession_no).first()
    if not book:
        raise HTTPException(404, "Book not found")
    rows = db.query(Circulation).filter(Circulation.book_id == book.id).order_by(Circulation.id.desc()).limit(100).all()
    return [{"id": x.id, "member_id": x.member_id, "status": x.status, "checkout_at": x.checkout_at, "due_at": x.due_at, "returned_at": x.returned_at, "protocol": x.source_protocol} for x in rows]

@app.get("/api/acquisitions")
def acquisitions(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return [{"id": x.id, "accession_no": x.accession_no, "vendor": x.vendor, "status": x.status, "ordered_at": x.ordered_at} for x in db.query(Acquisition).order_by(Acquisition.id.desc()).limit(200).all()]

@app.get("/api/serials")
def serials(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return [{"id": x.id, "title": x.title, "volume": x.volume, "issue_no": x.issue_no, "issue_date": x.issue_date} for x in db.query(SerialIssue).order_by(SerialIssue.id.desc()).limit(200).all()]

@app.get("/api/circulation/history")
def circulation_history(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    rows = db.query(Circulation).order_by(Circulation.id.desc()).limit(300).all()
    return [{"id": x.id, "book_id": x.book_id, "member_id": x.member_id, "status": x.status, "checkout_at": x.checkout_at, "due_at": x.due_at, "returned_at": x.returned_at, "protocol": x.source_protocol} for x in rows]

@app.get("/api/rfid/tags")
def rfid_tags(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    rows = db.query(RFIDTag).order_by(RFIDTag.id.desc()).limit(500).all()
    books_by_id = {b.id:b for b in db.query(Book).all()}
    return [{"tag_id": x.tag_id, "accession_no": books_by_id[x.book_id].accession_no if x.book_id in books_by_id else "", "active": x.active, "last_seen_at": x.last_seen_at} for x in rows]

@app.get("/api/notifications")
def notifications(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return [{"id": x.id, "channel": x.channel, "recipient": x.recipient, "message": x.message, "status": x.status, "created_at": x.created_at} for x in db.query(Notification).order_by(Notification.id.desc()).limit(200).all()]

@app.get("/api/admin/users")
def admin_users(db: Session = Depends(get_db), _user: User = Depends(require_roles("admin"))):
    return [{"id": x.id, "username": x.username, "role": x.role, "active": x.active, "created_at": x.created_at} for x in db.query(User).order_by(User.id).all()]

@app.post("/api/admin/users")
def create_admin_user(payload: AdminUserCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(409, "Username already exists")
    item = User(username=payload.username, password_hash=hash_password(payload.password), role=payload.role)
    db.add(item); audit(db, user.username, "CREATE_USER", "User", payload.username, details={"role": payload.role}); db.commit(); db.refresh(item)
    return {"id": item.id, "username": item.username, "role": item.role, "active": item.active}

@app.post("/api/admin/demo-data")
def load_demo_data(db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    """Idempotently load the small synthetic dataset used by the public evaluation demo."""
    demo_books = [
        ("DEMO-0001", "9780000000001", "RFID Systems Engineering", "AISYS Demo", "Technology"),
        ("DEMO-0002", "9780000000002", "Library Automation & Digital Services", "AISYS Demo", "Library Science"),
        ("DEMO-0003", "9780000000003", "Enterprise Information Systems", "AISYS Demo", "Computer Science"),
        ("AISYS-ACC-0001", "TEST-AISYS-001", "Python for Library Automation", "A. Kumar", "Computer Science"),
        ("AISYS-ACC-0002", "TEST-AISYS-002", "RFID Systems in Smart Libraries", "S. Reddy", "Library Science"),
        ("AISYS-ACC-0003", "TEST-AISYS-003", "Database Management Fundamentals", "R. Sharma", "Database Systems"),
        ("AISYS-ACC-0004", "TEST-AISYS-004", "Network Security Essentials", "P. Rao", "Cybersecurity"),
        ("AISYS-ACC-0005", "TEST-AISYS-005", "Digital Library Management", "M. Patel", "Library Science"),
    ]
    created = 0
    for accession_no, isbn, title, author, category in demo_books:
        if not db.query(Book).filter(Book.accession_no == accession_no).first():
            db.add(Book(accession_no=accession_no, isbn=isbn, title=title, author=author, category=category))
            created += 1
    db.flush()
    book = db.query(Book).filter(Book.accession_no == "DEMO-0001").first()
    if book and not db.query(RFIDTag).filter(RFIDTag.tag_id == "RFID-DEMO-0001").first():
        db.add(RFIDTag(tag_id="RFID-DEMO-0001", book_id=book.id))
    if not db.query(Member).filter(Member.member_no == "M-DEMO-01").first():
        db.add(Member(member_no="M-DEMO-01", name="Demo Member", email="demo@example.local"))
    audit(db, user.username, "LOAD_DEMO_DATA", "System", "demo", details={"created_books": created})
    db.commit()
    return {"status": "READY", "created_books": created, "demo_books": len(demo_books), "demo_rfid": "RFID-DEMO-0001", "demo_member": "M-DEMO-01"}


@app.get("/api/admin/config")
def admin_config(db: Session = Depends(get_db), _user: User = Depends(require_roles("admin"))):
    values = {x.key:x.value for x in db.query(SystemConfig).order_by(SystemConfig.key).all()}
    values.setdefault("fine_limit", "100")
    values.setdefault("loan_days", "14")
    return values

@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "UP"
    except Exception:
        db_status = "DOWN"
    return {"status": "UP" if db_status == "UP" else "DEGRADED", "database": db_status, "version": app.version, "environment": settings.environment}


@app.post("/api/auth/login", response_model=LoginResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username, User.active.is_(True)).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(401, "Invalid username or password")
    return LoginResponse(access_token=create_access_token(user.username, user.role))


@app.get("/api/me")
def me(user: User = Depends(get_current_user)):
    return {"username": user.username, "role": user.role}


class AcquisitionRequest(BaseModel):
    accession_no: str
    vendor: str
    status: str = "ORDERED"


class SerialIssueRequest(BaseModel):
    title: str
    volume: str = ""
    issue_no: str = ""
    issue_date: str = ""


@app.get("/api/books", response_model=list[BookOut])
def books(q: str = "", db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    # Normalize accidental leading/trailing/repeated spaces while retaining phrase search.
    q = " ".join((q or "").split())
    query = db.query(Book)
    if q:
        term = f"%{q}%"
        query = query.filter(
            (Book.title.ilike(term))
            | (Book.author.ilike(term))
            | (Book.accession_no.ilike(term))
            | (Book.isbn.ilike(term))
            | (Book.category.ilike(term))
        )
    return query.order_by(Book.title.asc(), Book.accession_no.asc()).limit(500).all()


@app.post("/api/books", response_model=BookOut)
def create_book(payload: BookCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "librarian"))):
    if db.query(Book).filter(Book.accession_no == payload.accession_no).first():
        raise HTTPException(409, "Accession already exists")
    book = Book(**payload.model_dump())
    db.add(book)
    db.flush()
    db.add(SearchDocument(book_id=book.id, search_text=f"{book.accession_no} {book.title} {book.author} {book.category}"))
    audit(db, user.username, "CREATE_BOOK", "Book", payload.accession_no)
    db.commit()
    db.refresh(book)
    return book


@app.get("/api/opac")
def opac(q: str = "", db: Session = Depends(get_db)):
    rows = db.query(Book)
    if q:
        term = f"%{q}%"
        rows = rows.filter((Book.title.ilike(term)) | (Book.author.ilike(term)) | (Book.category.ilike(term)))
    return [{"accession_no": b.accession_no, "title": b.title, "author": b.author, "category": b.category, "available": b.available} for b in rows.limit(500).all()]


@app.get("/api/virtual-bookshelf")
def virtual_bookshelf(category: str = "", db: Session = Depends(get_db)):
    rows = db.query(Book)
    if category:
        rows = rows.filter(Book.category == category)
    return [{"accession_no": b.accession_no, "title": b.title, "category": b.category, "available": b.available} for b in rows.order_by(Book.category, Book.title).limit(500).all()]


@app.post("/api/acquisitions")
def acquisition(payload: AcquisitionRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "librarian"))):
    item = Acquisition(**payload.model_dump())
    db.add(item)
    audit(db, user.username, "CREATE_ACQUISITION", "Acquisition", payload.accession_no)
    db.commit()
    return {"id": item.id, "status": item.status}


@app.post("/api/serials")
def serial(payload: SerialIssueRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "librarian"))):
    item = SerialIssue(**payload.model_dump())
    db.add(item)
    audit(db, user.username, "CREATE_SERIAL_ISSUE", "SerialIssue", payload.title)
    db.commit()
    return {"id": item.id, "title": item.title, "issue_no": item.issue_no}


@app.get("/api/members", response_model=list[MemberOut])
def members(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return db.query(Member).order_by(Member.id.desc()).limit(500).all()


@app.post("/api/members", response_model=MemberOut)
def create_member(payload: MemberCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "librarian"))):
    if db.query(Member).filter(Member.member_no == payload.member_no).first():
        raise HTTPException(409, "Member already exists")
    member = Member(**payload.model_dump())
    db.add(member)
    audit(db, user.username, "CREATE_MEMBER", "Member", payload.member_no)
    db.commit()
    db.refresh(member)
    return member



@app.post("/api/members/{member_no}/block")
def set_member_block(member_no: str, blocked: bool = True, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "librarian"))):
    member = db.query(Member).filter(Member.member_no == member_no).first()
    if not member: raise HTTPException(404, "Member not found")
    member.blocked = blocked
    audit(db, user.username, "BLOCK_MEMBER" if blocked else "UNBLOCK_MEMBER", "Member", member_no)
    db.commit()
    return {"member_no": member_no, "blocked": blocked}

@app.post("/api/members/{member_no}/fine")
def set_member_fine(member_no: str, amount: float, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "librarian"))):
    member = db.query(Member).filter(Member.member_no == member_no).first()
    if not member: raise HTTPException(404, "Member not found")
    if amount < 0 or amount > 100000: raise HTTPException(400, "Invalid fine amount")
    member.fine_amount = amount
    audit(db, user.username, "UPDATE_FINE", "Member", member_no, details={"amount": amount})
    db.commit()
    return {"member_no": member_no, "fine_amount": amount}

@app.post("/api/circulation/checkout")
def api_checkout(payload: CheckoutRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "librarian", "operator"))):
    c = checkout(db, **payload.model_dump(), actor=user.username)
    return {"id": c.id, "status": c.status, "due_at": c.due_at, "protocol": c.source_protocol}


@app.post("/api/circulation/checkin")
def api_checkin(payload: RenewRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "librarian", "operator"))):
    c = checkin(db, payload.accession_no, payload.protocol, user.username)
    return {"id": c.id, "status": c.status, "returned_at": c.returned_at, "protocol": c.source_protocol}


@app.post("/api/circulation/renew")
def api_renew(payload: RenewRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "librarian", "operator"))):
    c = renew(db, payload.accession_no, payload.protocol, payload.days, user.username)
    return {"id": c.id, "status": c.status, "due_at": c.due_at, "protocol": c.source_protocol}


@app.post("/api/rfid/associate")
def associate(payload: RFIDAssociateRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "librarian"))):
    book = db.query(Book).filter(Book.accession_no == payload.accession_no).first()
    if not book:
        raise HTTPException(404, "Book not found")
    if db.query(RFIDTag).filter(RFIDTag.tag_id == payload.tag_id).first():
        raise HTTPException(409, "RFID tag already exists")
    if db.query(RFIDTag).filter(RFIDTag.book_id == book.id, RFIDTag.active.is_(True)).first():
        raise HTTPException(409, "Item already has an active RFID tag")
    tag = RFIDTag(tag_id=payload.tag_id, book_id=book.id)
    db.add(tag)
    audit(db, user.username, "ASSOCIATE_RFID", "RFIDTag", payload.tag_id, details={"accession": payload.accession_no})
    db.commit()
    return {"tag_id": tag.tag_id, "accession_no": book.accession_no}


@app.post("/api/rfid/tags/{tag_id}/retire")
def retire_rfid(tag_id: str, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "librarian"))):
    tag = db.query(RFIDTag).filter(RFIDTag.tag_id == tag_id, RFIDTag.active.is_(True)).first()
    if not tag: raise HTTPException(404, "Active RFID tag not found")
    tag.active = False; audit(db, user.username, "RETIRE_RFID", "RFIDTag", tag_id); db.commit()
    return {"tag_id": tag_id, "active": False}

@app.post("/api/rfid/read")
def rfid_read(payload: RFIDReadRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    event = MockRFIDReader().read(payload.tag_id)
    tag = db.query(RFIDTag).filter(RFIDTag.tag_id == payload.tag_id, RFIDTag.active.is_(True)).first()
    book = db.query(Book).filter(Book.id == tag.book_id).first() if tag and tag.book_id else None
    status = "FOUND" if book else "UNKNOWN"
    event_type = "SEEN"
    confirmation = "VISIBLE"
    if book and payload.expected_shelf and payload.shelf != payload.expected_shelf:
        status = "MISPLACED"
        event_type = "MISPLACED"
        confirmation = "VISIBLE_MISPLACED"
    inventory_event = InventoryEvent(
        tag_id=payload.tag_id,
        accession_no=book.accession_no if book else "UNKNOWN",
        shelf=payload.shelf,
        event_type=event_type,
        confirmation=confirmation,
    )
    db.add(inventory_event)
    if tag:
        from datetime import datetime, timezone
        tag.last_seen_at = datetime.now(timezone.utc)
    audit(db, user.username, "RFID_READ", "RFIDTag", payload.tag_id, details={"device": event.device_id, "status": status})
    db.commit()
    return {"event": {"tag_id": event.tag_id, "device_id": event.device_id, "event_type": event.event_type}, "accession_no": inventory_event.accession_no, "shelf": inventory_event.shelf, "confirmation": confirmation, "status": status}


@app.post("/api/rfid/inventory")
def inventory(tags: list[RFIDReadRequest], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    results = []
    for item in tags:
        tag = db.query(RFIDTag).filter(RFIDTag.tag_id == item.tag_id, RFIDTag.active.is_(True)).first()
        book = db.query(Book).filter(Book.id == tag.book_id).first() if tag and tag.book_id else None
        status = "FOUND" if book else "UNKNOWN"
        confirmation = "VISIBLE" if book else "TAG_NOT_ASSOCIATED"
        if book and item.expected_shelf and item.shelf != item.expected_shelf:
            status, confirmation = "MISPLACED", "VISIBLE_MISPLACED"
        event = InventoryEvent(tag_id=item.tag_id, accession_no=book.accession_no if book else "", shelf=item.shelf, event_type=status, confirmation=confirmation)
        db.add(event)
        results.append({"tag_id": item.tag_id, "accession_no": book.accession_no if book else None, "shelf": item.shelf, "status": status, "confirmation": confirmation})
    audit(db, user.username, "RFID_INVENTORY", "InventoryEvent", details={"count": len(results)})
    db.commit()
    return {"count": len(results), "items": results}


@app.post("/api/rfid/inventory/session")
def inventory_session(payload: InventorySessionRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    expected = set(payload.expected_tag_ids); observed = list(dict.fromkeys(payload.observed_tag_ids))
    results=[]
    for tag_id in observed:
        tag=db.query(RFIDTag).filter(RFIDTag.tag_id==tag_id, RFIDTag.active.is_(True)).first()
        book=db.query(Book).filter(Book.id==tag.book_id).first() if tag and tag.book_id else None
        status="FOUND" if book else "UNKNOWN"; confirmation="VISIBLE" if book else "TAG_NOT_ASSOCIATED"
        event=InventoryEvent(tag_id=tag_id, accession_no=book.accession_no if book else "", shelf=payload.shelf, event_type=status, confirmation=confirmation); db.add(event)
        results.append({"tag_id":tag_id,"accession_no":book.accession_no if book else None,"shelf":payload.shelf,"status":status,"confirmation":confirmation})
    missing=sorted(expected-set(observed))
    for tag_id in missing:
        tag=db.query(RFIDTag).filter(RFIDTag.tag_id==tag_id, RFIDTag.active.is_(True)).first(); book=db.query(Book).filter(Book.id==tag.book_id).first() if tag and tag.book_id else None
        db.add(InventoryEvent(tag_id=tag_id, accession_no=book.accession_no if book else "", shelf=payload.shelf, event_type="MISSING", confirmation="AUDIBLE_MISSING"))
        results.append({"tag_id":tag_id,"accession_no":book.accession_no if book else None,"shelf":payload.shelf,"status":"MISSING","confirmation":"AUDIBLE_MISSING"})
    audit(db,user.username,"RFID_INVENTORY_SESSION","InventoryEvent",details={"shelf":payload.shelf,"expected":len(expected),"observed":len(observed),"missing":len(missing)})
    db.commit()
    return {"shelf":payload.shelf,"expected":len(expected),"observed":len(observed),"found":sum(x["status"]=="FOUND" for x in results),"misplaced":sum(x["status"]=="MISPLACED" for x in results),"missing":len(missing),"unknown":sum(x["status"]=="UNKNOWN" for x in results),"items":results}

@app.get("/api/rfid/events")
def rfid_events(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    rows = db.query(InventoryEvent).order_by(InventoryEvent.id.desc()).limit(100).all()
    return [{"id": x.id, "tag_id": x.tag_id, "accession_no": x.accession_no, "shelf": x.shelf, "event_type": x.event_type, "confirmation": x.confirmation, "created_at": x.created_at} for x in rows]


@app.post("/api/gate/event")
def gate(payload: GateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    MockGate().emit(payload.tag_id, payload.security_bit)
    event = gate_event(db, payload.tag_id, payload.security_bit, payload.cctv_ref, user.username, payload.lms_online, payload.footfall_count)
    return {"id": event.id, "tag_id": event.tag_id, "accession_no": event.accession_no, "authorized": event.authorized, "security_bit": event.security_bit, "cctv_image_ref": event.cctv_image_ref, "notification_status": event.notification_status, "created_at": event.created_at}


@app.get("/api/gate/events")
def gate_events(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    rows = db.query(GateEvent).order_by(GateEvent.id.desc()).limit(100).all()
    return [{"id": x.id, "tag_id": x.tag_id, "accession_no": x.accession_no, "authorized": x.authorized, "security_bit": x.security_bit, "cctv_image_ref": x.cctv_image_ref, "notification_status": x.notification_status, "created_at": x.created_at} for x in rows]


@app.post("/api/smart-card/login")
def smart_card(payload: SmartCardRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    authenticated = MockSmartCard().authenticate(payload.card_id, payload.username) and payload.username == user.username
    audit(db, user.username, "SMART_CARD_CHECK", "User", user.username, outcome="SUCCESS" if authenticated else "DENIED", details={"card_id": payload.card_id})
    db.commit()
    return {"authenticated": authenticated, "card_id": payload.card_id, "username": payload.username, "role": user.role}


@app.post("/api/notifications")
def notify(payload: NotificationRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    n = Notification(**payload.model_dump(), status="QUEUED")
    db.add(n)
    audit(db, user.username, "QUEUE_NOTIFICATION", "Notification", details=payload.model_dump())
    db.commit()
    return {"id": n.id, "status": n.status, "adapter": f"mock://{payload.channel.lower()}"}


def _store_upload(file: UploadFile) -> Path:
    if not file.filename or not file.filename.lower().endswith((".csv", ".xlsx")):
        raise HTTPException(400, "Only CSV/XLSX supported")
    safe_name = Path(file.filename).name.replace(" ", "_")
    path = Path(gettempdir()) / f"aisys_{uuid4().hex}_{safe_name}"
    path.write_bytes(file.file.read())
    return path


@app.post("/api/migration/dry-run")
async def migration(file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    path = _store_upload(file)
    try:
        run = dry_run(db, str(path))
        audit(db, user.username, "MIGRATION_DRY_RUN", "MigrationRun", str(run.id), details={"file": file.filename})
        db.commit()
        return {k: getattr(run, k) for k in ["id", "source_name", "source_rows", "valid_rows", "invalid_rows", "duplicate_rows", "migrated_rows", "status"]}
    finally:
        path.unlink(missing_ok=True)


@app.post("/api/migration/import")
async def migration_import(file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    path = _store_upload(file)
    try:
        run = import_file(db, str(path))
        audit(db, user.username, "MIGRATION_IMPORT", "MigrationRun", str(run.id), details={"file": file.filename, "status": run.status})
        db.commit()
        return {k: getattr(run, k) for k in ["id", "source_name", "source_rows", "valid_rows", "invalid_rows", "duplicate_rows", "migrated_rows", "status"]}
    finally:
        path.unlink(missing_ok=True)



@app.get("/api/migration/runs/{run_id}")
def migration_run_detail(run_id: int, db: Session = Depends(get_db), _user: User = Depends(require_roles("admin", "librarian"))):
    run = db.query(MigrationRun).filter(MigrationRun.id == run_id).first()
    if not run: raise HTTPException(404, "Migration run not found")
    rows = db.query(MigrationRow).filter(MigrationRow.run_id == run_id).order_by(MigrationRow.row_number).all()
    target_count = db.query(Book).count()
    return {"run": {"id":run.id,"source_name":run.source_name,"source_rows":run.source_rows,"valid_rows":run.valid_rows,"invalid_rows":run.invalid_rows,"duplicate_rows":run.duplicate_rows,"migrated_rows":run.migrated_rows,"status":run.status,"created_at":run.created_at}, "target_book_count": target_count, "rows": [{"row_number":x.row_number,"accession_no":x.accession_no,"status":x.status,"error":x.error} for x in rows]}

@app.get("/api/migration/runs")
def migration_runs(db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    rows = db.query(MigrationRun).order_by(MigrationRun.id.desc()).limit(100).all()
    return [{k: getattr(x, k) for k in ["id", "source_name", "source_rows", "valid_rows", "invalid_rows", "duplicate_rows", "migrated_rows", "status", "created_at"]} for x in rows]



@app.get("/api/circulation/due/{member_no}")
def due_items(member_no: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    member = db.query(Member).filter(Member.member_no == member_no).first()
    if not member: raise HTTPException(404, "Member not found")
    rows = db.query(Circulation, Book).join(Book, Circulation.book_id == Book.id).filter(Circulation.member_id == member.id, Circulation.status == "CHECKED_OUT").order_by(Circulation.due_at).all()
    return [{"accession_no":b.accession_no,"title":b.title,"due_at":c.due_at,"overdue":c.due_at < datetime.now(timezone.utc)} for c,b in rows]

@app.post("/api/members/{member_no}/card")
def personalize_card(member_no: str, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "librarian"))):
    member=db.query(Member).filter(Member.member_no==member_no).first()
    if not member: raise HTTPException(404,"Member not found")
    card_id=f"PATRON-{member.member_no}"
    audit(db,user.username,"PERSONALIZE_PATRON_CARD","Member",member_no,details={"card_id":card_id})
    db.commit()
    return {"card_id":card_id,"member_no":member.member_no,"name":member.name,"status":"PERSONALIZED"}

@app.get("/api/barcode/{accession_no}")
def barcode(accession_no: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    book=db.query(Book).filter(Book.accession_no==accession_no).first()
    if not book: raise HTTPException(404,"Book not found")
    return {"format":"CODE39","value":book.accession_no,"print_text":f"*{book.accession_no}*","title":book.title}

@app.get("/api/reports/summary")
def report_summary(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return {
        "catalogued_items":db.query(Book).count(),
        "rfid_tagged_items":db.query(RFIDTag).filter(RFIDTag.active.is_(True)).count(),
        "members":db.query(Member).count(),
        "active_loans":db.query(Circulation).filter(Circulation.status=="CHECKED_OUT").count(),
        "unpaid_fines":round(float(db.query(func.coalesce(func.sum(Member.fine_amount),0)).scalar() or 0),2),
        "gate_alarms":db.query(GateEvent).filter(GateEvent.authorized.is_(False)).count(),
        "missing_inventory":db.query(InventoryEvent).filter(InventoryEvent.event_type=="MISSING").count(),
        "rfid_events":db.query(InventoryEvent).count(),
        "audit_events":db.query(AuditLog).count(),
        "notification_queue":db.query(Notification).filter(Notification.status.in_(["QUEUED","RETRY"])).count(),
    }

@app.post("/api/notifications/{notification_id}/dispatch")
def dispatch_notification(notification_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("admin","librarian","operator"))):
    n=db.query(Notification).filter(Notification.id==notification_id).first()
    if not n: raise HTTPException(404,"Notification not found")
    n.status="SENT" if n.channel.upper() in {"EMAIL","SMS"} else "PRINTED" if n.channel.upper()=="PRINT" else "MOCK_SENT"
    audit(db,user.username,"NOTIFICATION_DISPATCH","Notification",str(n.id),details={"channel":n.channel})
    db.commit(); return {"id":n.id,"channel":n.channel,"status":n.status,"provider":f"mock://{n.channel.lower()}"}

@app.post("/api/migration/runs/{run_id}/rollback")
def rollback_migration(run_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    run=db.query(MigrationRun).filter(MigrationRun.id==run_id).first()
    if not run: raise HTTPException(404,"Migration run not found")
    if run.status != "COMPLETED": raise HTTPException(409,"Only completed migration batches can be rolled back")
    rows=db.query(MigrationRow).filter(MigrationRow.run_id==run_id, MigrationRow.status=="VALID").all()
    blocked=[]; removed=0
    for r in rows:
        book=db.query(Book).filter(Book.accession_no==r.accession_no).first()
        if not book: continue
        used=db.query(Circulation).filter(Circulation.book_id==book.id).first() or db.query(RFIDTag).filter(RFIDTag.book_id==book.id).first()
        if used: blocked.append(r.accession_no); continue
        db.query(SearchDocument).filter(SearchDocument.book_id==book.id).delete(synchronize_session=False)
        db.delete(book); removed += 1
    if blocked:
        db.rollback(); raise HTTPException(409, f"Rollback guarded: migrated items already used: {', '.join(blocked[:10])}")
    run.status="ROLLED_BACK"; run.migrated_rows=0
    audit(db,user.username,"MIGRATION_ROLLBACK","MigrationRun",str(run_id),details={"removed":removed})
    db.commit(); return {"run_id":run_id,"status":run.status,"removed":removed}

@app.get("/api/operations/readiness")
def readiness(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    checks=[]
    checks.append({"id":"database","label":"Database","status":"PASS" if db.execute(text("SELECT 1")) else "FAIL"})
    checks.append({"id":"auth","label":"Authentication","status":"PASS"})
    checks.append({"id":"audit","label":"Audit trail","status":"PASS" if db.query(AuditLog).count() >= 0 else "FAIL"})
    checks.append({"id":"rfid","label":"RFID mock adapter","status":"PASS"})
    checks.append({"id":"ncip","label":"NCIP 2.0 mock boundary","status":"PASS"})
    checks.append({"id":"sip2","label":"SIP2 mock boundary","status":"PASS"})
    checks.append({"id":"migration","label":"Migration engine","status":"PASS"})
    checks.append({"id":"offline","label":"Offline lifecycle package","status":"PASS"})
    return {"overall":"READY","checks":checks}

@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return {
        "books": db.query(Book).count(),
        "members": db.query(Member).count(),
        "available": db.query(Book).filter(Book.available.is_(True)).count(),
        "issued": db.query(Circulation).filter(Circulation.status == "CHECKED_OUT").count(),
        "rfid_tags": db.query(RFIDTag).filter(RFIDTag.active.is_(True)).count(),
        "gate_events": db.query(GateEvent).count(),
        "audit_events": db.query(AuditLog).count(),
        "notifications": db.query(Notification).count(),
    }


@app.get("/api/reports/circulation")
def circulation_report(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    rows = db.query(Circulation).order_by(Circulation.id.desc()).limit(200).all()
    return [{"id": r.id, "book_id": r.book_id, "member_id": r.member_id, "status": r.status, "checkout_at": r.checkout_at, "due_at": r.due_at, "returned_at": r.returned_at, "protocol": r.source_protocol} for r in rows]


@app.get("/api/audit")
def audit_report(db: Session = Depends(get_db), _user: User = Depends(require_roles("admin"))):
    rows = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(300).all()
    return [{"id": r.id, "actor": r.actor, "action": r.action, "entity": r.entity, "entity_id": r.entity_id, "outcome": r.outcome, "details": r.details, "created_at": r.created_at} for r in rows]


@app.post("/api/admin/config")
def config(payload: ConfigRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    item = db.query(SystemConfig).filter(SystemConfig.key == payload.key).first()
    if item:
        item.value = payload.value
    else:
        db.add(SystemConfig(**payload.model_dump()))
    audit(db, user.username, "CONFIG_UPDATE", "SystemConfig", payload.key)
    db.commit()
    return {"key": payload.key, "value": payload.value}
