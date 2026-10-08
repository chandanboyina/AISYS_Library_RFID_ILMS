from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

def now(): return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="operator")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Member(Base):
    __tablename__ = "members"
    id: Mapped[int] = mapped_column(primary_key=True)
    member_no: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(160), default="")
    blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    fine_amount: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Book(Base):
    __tablename__ = "books"
    id: Mapped[int] = mapped_column(primary_key=True)
    accession_no: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    isbn: Mapped[str] = mapped_column(String(30), default="")
    title: Mapped[str] = mapped_column(String(300), index=True)
    author: Mapped[str] = mapped_column(String(200), default="")
    category: Mapped[str] = mapped_column(String(120), default="General")
    reference_only: Mapped[bool] = mapped_column(Boolean, default=False)
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class RFIDTag(Base):
    __tablename__ = "rfid_tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    tag_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    book_id: Mapped[int | None] = mapped_column(ForeignKey("books.id"), nullable=True)
    member_id: Mapped[int | None] = mapped_column(ForeignKey("members.id"), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class Circulation(Base):
    __tablename__ = "circulation"
    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    status: Mapped[str] = mapped_column(String(20), default="CHECKED_OUT")
    checkout_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_protocol: Mapped[str] = mapped_column(String(20), default="LOCAL")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String(80))
    action: Mapped[str] = mapped_column(String(100), index=True)
    entity: Mapped[str] = mapped_column(String(80), default="")
    entity_id: Mapped[str] = mapped_column(String(80), default="")
    outcome: Mapped[str] = mapped_column(String(20), default="SUCCESS")
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class InventoryEvent(Base):
    __tablename__ = "inventory_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    tag_id: Mapped[str] = mapped_column(String(120), index=True)
    accession_no: Mapped[str] = mapped_column(String(80), default="")
    shelf: Mapped[str] = mapped_column(String(80), default="")
    event_type: Mapped[str] = mapped_column(String(30), default="SEEN")
    confirmation: Mapped[str] = mapped_column(String(30), default="VISIBLE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class GateEvent(Base):
    __tablename__ = "gate_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    tag_id: Mapped[str] = mapped_column(String(120), index=True)
    accession_no: Mapped[str] = mapped_column(String(80), default="")
    authorized: Mapped[bool] = mapped_column(Boolean, default=False)
    security_bit: Mapped[bool] = mapped_column(Boolean, default=True)
    cctv_image_ref: Mapped[str] = mapped_column(String(255), default="mock://cctv/no-image")
    notification_status: Mapped[str] = mapped_column(String(30), default="QUEUED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    channel: Mapped[str] = mapped_column(String(20))
    recipient: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="QUEUED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class MigrationRun(Base):
    __tablename__ = "migration_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_name: Mapped[str] = mapped_column(String(255))
    source_rows: Mapped[int] = mapped_column(Integer, default=0)
    valid_rows: Mapped[int] = mapped_column(Integer, default=0)
    invalid_rows: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_rows: Mapped[int] = mapped_column(Integer, default=0)
    migrated_rows: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default="DRY_RUN")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class MigrationRow(Base):
    __tablename__ = "migration_rows"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("migration_runs.id"))
    row_number: Mapped[int] = mapped_column(Integer)
    accession_no: Mapped[str] = mapped_column(String(80), default="")
    status: Mapped[str] = mapped_column(String(30))
    error: Mapped[str] = mapped_column(Text, default="")


class SearchDocument(Base):
    __tablename__ = "search_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), unique=True)
    search_text: Mapped[str] = mapped_column(Text, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Acquisition(Base):
    __tablename__ = "acquisitions"
    id: Mapped[int] = mapped_column(primary_key=True)
    accession_no: Mapped[str] = mapped_column(String(80), default="")
    vendor: Mapped[str] = mapped_column(String(160), default="")
    status: Mapped[str] = mapped_column(String(30), default="ORDERED")
    ordered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class SerialIssue(Base):
    __tablename__ = "serial_issues"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    volume: Mapped[str] = mapped_column(String(50), default="")
    issue_no: Mapped[str] = mapped_column(String(50), default="")
    issue_date: Mapped[str] = mapped_column(String(30), default="")

class SystemConfig(Base):
    __tablename__ = "system_config"
    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True)
    value: Mapped[str] = mapped_column(Text)
