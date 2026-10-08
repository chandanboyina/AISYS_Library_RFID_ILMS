from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class BookCreate(BaseModel):
    accession_no: str = Field(min_length=1, max_length=80)
    isbn: str = ""
    title: str = Field(min_length=1, max_length=300)
    author: str = ""
    category: str = "General"
    reference_only: bool = False

class BookOut(BookCreate):
    id: int
    available: bool
    model_config = ConfigDict(from_attributes=True)

class MemberCreate(BaseModel):
    member_no: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=160)
    email: str = ""

class MemberOut(MemberCreate):
    id: int
    blocked: bool
    fine_amount: float
    model_config = ConfigDict(from_attributes=True)

class CheckoutRequest(BaseModel):
    member_no: str
    accession_no: str
    protocol: str = "LOCAL"
    days: int = Field(default=14, ge=1, le=90)

class RenewRequest(BaseModel):
    accession_no: str
    protocol: str = "LOCAL"
    days: int = Field(default=14, ge=1, le=90)

class RFIDAssociateRequest(BaseModel):
    accession_no: str
    tag_id: str = Field(min_length=1, max_length=120)

class RFIDReadRequest(BaseModel):
    tag_id: str
    shelf: str = "UNKNOWN"
    expected_shelf: str = ""

class GateRequest(BaseModel):
    tag_id: str
    security_bit: bool = True
    cctv_ref: str = "mock://cctv/event"
    lms_online: bool = True
    footfall_count: int = Field(default=1, ge=0, le=999)

class SmartCardRequest(BaseModel):
    card_id: str
    username: str

class NotificationRequest(BaseModel):
    channel: str
    recipient: str
    message: str

class ConfigRequest(BaseModel):
    key: str
    value: str


class InventorySessionRequest(BaseModel):
    shelf: str = Field(min_length=1, max_length=80)
    expected_tag_ids: list[str] = []
    observed_tag_ids: list[str] = []

class AdminUserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=8, max_length=120)
    role: str = Field(default="operator", pattern="^(admin|librarian|operator)$")
