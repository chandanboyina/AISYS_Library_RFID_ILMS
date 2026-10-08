from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class RFIDEvent:
    tag_id: str
    device_id: str
    event_type: str

class RFIDReaderAdapter(ABC):
    @abstractmethod
    def read(self, tag_id: str, device_id: str = "mock-reader") -> RFIDEvent: ...

class GateAdapter(ABC):
    @abstractmethod
    def emit(self, tag_id: str, security_bit: bool = True) -> dict: ...

class CredentialAdapter(ABC):
    @abstractmethod
    def authenticate(self, card_id: str, username: str) -> bool: ...

class NotificationAdapter(ABC):
    @abstractmethod
    def send(self, recipient: str, message: str) -> str: ...

class ILMSAdapter(ABC):
    @abstractmethod
    def checkout(self, accession_no: str, member_no: str) -> dict: ...
    @abstractmethod
    def checkin(self, accession_no: str) -> dict: ...
    @abstractmethod
    def renew(self, accession_no: str, member_no: str) -> dict: ...
