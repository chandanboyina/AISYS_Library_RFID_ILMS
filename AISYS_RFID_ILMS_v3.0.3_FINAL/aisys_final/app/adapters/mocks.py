from datetime import datetime, timezone
from app.adapters.contracts import RFIDEvent, RFIDReaderAdapter, GateAdapter, CredentialAdapter, NotificationAdapter, ILMSAdapter

class MockRFIDReader(RFIDReaderAdapter):
    def read(self, tag_id: str, device_id: str = "mock-reader"):
        return RFIDEvent(tag_id=tag_id, device_id=device_id, event_type="TAG_READ")

class MockHandheldReader(MockRFIDReader):
    pass

class MockGate(GateAdapter):
    def emit(self, tag_id: str, security_bit: bool = True):
        return {"tag_id": tag_id, "security_bit": security_bit, "event_time": datetime.now(timezone.utc).isoformat(), "device": "MOCK-GATE-01"}

class MockSmartCard(CredentialAdapter):
    CARD_MAP = {
        "CARD-ADMIN-01": "admin",
        "CARD-LIB-01": "librarian",
        "CARD-OP-01": "operator",
    }
    def authenticate(self, card_id: str, username: str):
        return self.CARD_MAP.get(card_id) == username

class MockNotification(NotificationAdapter):
    def __init__(self, channel: str): self.channel = channel
    def send(self, recipient: str, message: str):
        return f"mock://{self.channel}/{recipient}"

class MockCamera:
    def capture(self, gate_event_id: int | None = None):
        return f"mock://cctv/capture/{gate_event_id or 'pending'}"

class MockPrinter:
    def print_document(self, document: str):
        return f"mock://print/job/{abs(hash(document))}"

class MockNCIPAdapter(ILMSAdapter):
    def checkout(self, accession_no, member_no): return {"protocol":"NCIP2","operation":"CHECKOUT","accession_no":accession_no,"member_no":member_no,"status":"OK"}
    def checkin(self, accession_no): return {"protocol":"NCIP2","operation":"CHECKIN","accession_no":accession_no,"status":"OK"}
    def renew(self, accession_no, member_no): return {"protocol":"NCIP2","operation":"RENEW","accession_no":accession_no,"member_no":member_no,"status":"OK"}

class MockSIP2Adapter(MockNCIPAdapter):
    def checkout(self, accession_no, member_no): return {**super().checkout(accession_no,member_no), "protocol":"SIP2"}
    def checkin(self, accession_no): return {**super().checkin(accession_no), "protocol":"SIP2"}
    def renew(self, accession_no, member_no): return {**super().renew(accession_no,member_no), "protocol":"SIP2"}
