"""Regression tests for catalog exactness, audit tampering and API access."""
import math
import pytest
from pydantic import ValidationError

from hla_matcher import lookup, process_csv
from agents.base import AuditTrail, SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from agents.api import require_api_token
from fastapi import HTTPException


@pytest.mark.parametrize("query, expected", [
    ("A*02:01", "A*02:01"),
    ("a02", "A*02:01"),  # compatibility with legacy demonstration shorthand
    ("DRB115", "DRB1*15:01"),
    ("B*07:02", "B*07:02"),
])
def test_catalog_lookup(query, expected):
    assert lookup(query)["top_hit"] == expected


@pytest.mark.parametrize("query", ["A*02:011", "prefix A*02:01 suffix", "zzA02zz", "", None])
def test_lookup_does_not_accept_partial_or_absent_matches(query):
    result = lookup(query)
    assert result["top_hit"] == "no match"
    assert result["score"] == 0
    assert result["all"] == []


def test_existing_lookup_result_csv_columns(tmp_path):
    source = tmp_path / "source.csv"
    source.write_text("hla,top_hit,lookup_score\nA*02:01,old,-1\n", encoding="utf-8")
    destination = tmp_path / "out.csv"
    results = process_csv(source, destination)
    assert results[0]["top_hit"] == "A*02:01"
    assert destination.read_text().splitlines()[0] == "hla,top_hit,lookup_score"


def test_audit_detects_changed_entry_and_copy_isolation():
    ledger = AuditTrail(secret_key="test-secret")
    ledger.log("operator", "supervisor", "test", {"task": "dummy"})
    assert ledger.verify_integrity()
    exported = ledger.get_trail()
    exported[0]["actor"] = "modified"
    assert ledger.verify_integrity()  # A returned trail must not allow mutation
    ledger.logs[0]["actor"] = "modified"
    assert not ledger.verify_integrity()


def test_audit_detects_replaced_signature():
    ledger = AuditTrail(secret_key="test-secret")
    ledger.log("operator", "supervisor", "test", {"task": "dummy"})
    ledger.logs[0]["current_hash"] = "0" * 64
    assert not ledger.verify_integrity()


def test_phi_guard_checks_nested_payload_attributes():
    payload = SystemTaskPayload(
        task_id="demo", target_identifier="case",
        primary_metric=1.0, attributes={"nested": {"note": "MRN-123456"}}
    )
    with pytest.raises(SecurityException):
        SystemSupervisor().process_task(payload)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_non_finite_metrics_rejected(value):
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="demo", target_identifier="case", primary_metric=value)


def test_api_requires_bearer_token(monkeypatch):
    monkeypatch.delenv("API_ACCESS_TOKEN", raising=False)
    with pytest.raises(HTTPException) as missing:
        require_api_token(None)
    assert missing.value.status_code == 503
    monkeypatch.setenv("API_ACCESS_TOKEN", "repro-test-token")
    with pytest.raises(HTTPException) as bad:
        require_api_token("Bearer wrong")
    assert bad.value.status_code == 401
    assert require_api_token("Bearer repro-test-token") is None


def test_csv_export_escapes_spreadsheet_formulas(tmp_path):
    import csv
    from hla_matcher import safe_csv_row
    assert safe_csv_row({"query": " =1+1"})["query"] == "' =1+1"
    assert safe_csv_row({"query": "A*02:01"})["query"] == "A*02:01"
    source = tmp_path / "source.csv"
    source.write_text("hla,note\nA*02:01,=1+1\n", encoding="utf-8")
    destination = tmp_path / "out.csv"
    process_csv(source, destination)
    with destination.open(newline="", encoding="utf-8") as stream:
        row = next(csv.DictReader(stream))
    assert row["note"] == "'=1+1"
