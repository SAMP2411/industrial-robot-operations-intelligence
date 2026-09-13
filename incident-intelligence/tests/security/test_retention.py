from datetime import datetime, timedelta, timezone

from packages.domain_models.models import Customer, DiagnosticEngagement, Site
from packages.retention import approve_deletion, execute_deletion, preview_deletion


def test_retention_requires_expiry_no_hold_and_independent_approval(db_session, tmp_path):
    customer = Customer(name="Synthetic"); db_session.add(customer); db_session.flush()
    site = Site(customer_id=customer.id, name="Lab", timezone="UTC"); db_session.add(site); db_session.flush()
    engagement = DiagnosticEngagement(customer_id=customer.id, site_id=site.id, title="Expired", retention_until=datetime.now(timezone.utc) - timedelta(days=1), legal_hold=False)
    db_session.add(engagement); db_session.commit()
    request = preview_deletion(db_session, engagement, actor="requester", reason="Retention expired")
    try:
        approve_deletion(db_session, request, actor="requester")
        assert False, "self-approval must fail"
    except ValueError: pass
    approve_deletion(db_session, request, actor="reviewer")
    receipt = execute_deletion(db_session, request, tmp_path, actor="admin")
    assert receipt.deletion_request_id == request.id
    assert engagement.status == "deleted"
