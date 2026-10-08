import json
from sqlalchemy.orm import Session
from app.models.models import AuditLog

def audit(db: Session, actor: str, action: str, entity: str = "", entity_id: str = "", outcome: str = "SUCCESS", details: dict | None = None):
    db.add(AuditLog(actor=actor, action=action, entity=entity, entity_id=entity_id, outcome=outcome, details=json.dumps(details or {}, default=str)))
