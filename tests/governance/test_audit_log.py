from creditscore.governance.audit_log import AuditLog


def test_audit_log_is_append_only_jsonl(tmp_path):
    log = AuditLog(tmp_path / "audit.jsonl")
    log.append("FIRST", {"value": 1})
    log.append("SECOND", {"value": 2})
    records = log.read_all()
    assert [item["event_type"] for item in records] == ["FIRST", "SECOND"]
    assert all("timestamp_utc" in item for item in records)
