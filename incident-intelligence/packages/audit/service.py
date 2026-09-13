from sqlalchemy.orm import Session

from packages.domain_models.models import AuditEvent, Customer, DataSource, DiagnosticEngagement, Incident, Site


def audit(session: Session, *, actor: str, action: str, entity_type: str, entity_id: str | None, details: dict | None = None, customer_id: str | None = None) -> None:
    if not customer_id and entity_id:
        if entity_type == "customer": customer_id = entity_id
        elif entity_type == "site" and (entity := session.get(Site, entity_id)): customer_id = entity.customer_id
        elif entity_type in {"diagnostic_engagement", "engagement"} and (entity := session.get(DiagnosticEngagement, entity_id)): customer_id = entity.customer_id
        elif entity_type == "data_source" and (source := session.get(DataSource, entity_id)):
            engagement = session.get(DiagnosticEngagement, source.engagement_id); customer_id = engagement.customer_id if engagement else None
        elif entity_type == "incident" and (incident := session.get(Incident, entity_id)):
            engagement = session.get(DiagnosticEngagement, incident.diagnostic_engagement_id); customer_id = engagement.customer_id if engagement else None
    session.add(AuditEvent(actor=actor, action=action, entity_type=entity_type, entity_id=entity_id, details=details or {}, customer_id=customer_id))
