from datetime import datetime, timedelta, timezone
from sqlalchemy import or_, func
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.models import Book, Member, Circulation, RFIDTag, InventoryEvent, GateEvent, Notification, SystemConfig
from app.services.audit import audit
from app.adapters.mocks import MockNCIPAdapter, MockSIP2Adapter, MockCamera, MockGate, MockNotification

def get_book(db, accession): return db.query(Book).filter(Book.accession_no==accession).first()
def get_member(db, member_no): return db.query(Member).filter(Member.member_no==member_no).first()

def checkout(db: Session, accession_no, member_no, protocol, days, actor):
    book=get_book(db,accession_no); member=get_member(db,member_no)
    if not book or not member: raise HTTPException(404,"Book or member not found")
    if not book.available: raise HTTPException(409,"Book is already checked out")
    if book.reference_only: raise HTTPException(409,"Reference-only item cannot circulate")
    if member.blocked: raise HTTPException(409,"Member is blocked")
    configured = db.query(SystemConfig).filter(SystemConfig.key == "fine_limit").first()
    try: fine_limit = float(configured.value) if configured else 100.0
    except (TypeError, ValueError): fine_limit = 100.0
    if member.fine_amount > fine_limit: raise HTTPException(409, f"Member exceeds configurable fine limit of {fine_limit:.2f}")
    due=datetime.now(timezone.utc)+timedelta(days=days)
    adapter=MockNCIPAdapter() if protocol.upper()=="NCIP2" else MockSIP2Adapter() if protocol.upper()=="SIP2" else None
    if adapter: adapter.checkout(accession_no,member_no)
    c=Circulation(book_id=book.id,member_id=member.id,due_at=due,source_protocol=protocol.upper())
    book.available=False; db.add(c); audit(db,actor,"CHECKOUT","Book",str(book.id),details={"member":member_no,"protocol":protocol})
    db.commit(); db.refresh(c); return c

def checkin(db: Session, accession_no, protocol, actor):
    book=get_book(db,accession_no)
    if not book: raise HTTPException(404,"Book not found")
    c=db.query(Circulation).filter(Circulation.book_id==book.id,Circulation.status=="CHECKED_OUT").order_by(Circulation.id.desc()).first()
    if not c: raise HTTPException(409,"No active circulation")
    adapter=MockNCIPAdapter() if protocol.upper()=="NCIP2" else MockSIP2Adapter() if protocol.upper()=="SIP2" else None
    if adapter: adapter.checkin(accession_no)
    c.status="RETURNED"; c.returned_at=datetime.now(timezone.utc); book.available=True
    audit(db,actor,"CHECKIN","Book",str(book.id),details={"protocol":protocol}); db.commit(); return c

def renew(db: Session, accession_no, protocol, days, actor):
    book=get_book(db,accession_no)
    if not book: raise HTTPException(404,"Book not found")
    c=db.query(Circulation).filter(Circulation.book_id==book.id,Circulation.status=="CHECKED_OUT").order_by(Circulation.id.desc()).first()
    if not c: raise HTTPException(409,"No active circulation")
    member=db.query(Member).filter(Member.id==c.member_id).first()
    if member.blocked: raise HTTPException(409,"Member is blocked")
    adapter=MockNCIPAdapter() if protocol.upper()=="NCIP2" else MockSIP2Adapter() if protocol.upper()=="SIP2" else None
    if adapter: adapter.renew(accession_no,member.member_no)
    c.due_at += timedelta(days=days); audit(db,actor,"RENEW","Book",str(book.id),details={"protocol":protocol}); db.commit(); return c

def gate_event(db, tag_id, security_bit, cctv_ref, actor, lms_online=True, footfall_count=1):
    tag=db.query(RFIDTag).filter(RFIDTag.tag_id==tag_id,RFIDTag.active==True).first()
    book=db.query(Book).filter(Book.id==tag.book_id).first() if tag and tag.book_id else None
    # Online: use the live circulation state. Offline: use the RFID security bit as the local decision source.
    authorized = bool(book and not book.available) if lms_online else bool(book and not security_bit)
    event=GateEvent(tag_id=tag_id,accession_no=book.accession_no if book else "UNKNOWN",authorized=authorized,security_bit=security_bit,cctv_image_ref=cctv_ref,notification_status="QUEUED")
    db.add(event); db.flush()
    if not authorized:
        n=Notification(channel="EMAIL",recipient="library-security@example.local",message=f"Unauthorized RFID removal: {event.accession_no} (footfall={footfall_count})",status="QUEUED")
        db.add(n); MockNotification("email").send(n.recipient,n.message); event.notification_status="QUEUED"
    audit(db,actor,"GATE_EVENT","GateEvent",str(event.id),details={"authorized":authorized,"tag":tag_id,"decision_basis":"CIRCULATION" if lms_online else "SECURITY_BIT","lms_online":lms_online,"footfall_count":footfall_count}); db.commit(); return event
