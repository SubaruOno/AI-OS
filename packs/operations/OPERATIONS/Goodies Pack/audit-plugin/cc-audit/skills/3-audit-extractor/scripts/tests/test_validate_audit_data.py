#!/usr/bin/env python3
"""
Tests for validate_audit_data.py validation logic.
Run: python3 -m pytest test_validate_audit_data.py -v
or:  python3 test_validate_audit_data.py
"""

import json
import sys
import unittest
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from validate_audit_data import validate


def make_valid_audit_data(**overrides) -> dict:
    """Return a minimal valid audit data file that passes all critical/high checks."""
    ssad = {
        "client_slug": "test-client",
        "company_name": "Test Co",
        "industry_tag": "home-services",
        "audit_status": "session-1",
        "sessions_completed": 1,
        "contact": {
            "name": "Jane Smith",
            "role": "Owner",
            "company_size": "10",
            "revenue_range": "$1M-$2M"
        },
        "blended_hourly_rate_aud": 45.0,
        "blended_rate_confidence": "HIGH",
        "blended_rate_source": "Owner stated team is on $45/hr",
        "processes": [
            {
                "stage": "acquisition",
                "steps": [
                    {
                        "step_id": "S001",
                        "description": "Receive lead via Google form",
                        "owner": "Admin",
                        "type": "step",
                        "confidence": "HIGH",
                        "source_quote": "All our leads come through the Google form on the website"
                    }
                ]
            }
        ],
        "waste_items": [
            {
                "activity": "Manual quote data entry",
                "hours_per_week": 5,
                "headcount_affected": 2,
                "annual_waste_aud": 23400,
                "monthly_waste_aud": 1950,
                "waste_type": "manual_data_entry",
                "quote": "It takes us about 5 hours a week just doing quotes manually",
                "confidence": "HIGH"
            }
        ],
        "decision_nodes": [],
        "contradictions": [],
        "completeness_checklist": {
            "acquisition": {"covered": True, "confidence": "HIGH", "items_confirmed": [], "items_missing": []},
            "quoting": {"covered": False, "confidence": "LOW", "items_confirmed": [], "items_missing": []},
            "onboarding": {"covered": False, "confidence": "LOW", "items_confirmed": [], "items_missing": []},
            "fulfilment": {"covered": False, "confidence": "LOW", "items_confirmed": [], "items_missing": []},
            "retention": {"covered": False, "confidence": "LOW", "items_confirmed": [], "items_missing": []}
        },
        "follow_up_questions": [],
        "sessions": [
            {
                "session_number": 1,
                "date": "2026-03-15",
                "transcript_file": "session-1.txt",
                "participants": ["Adam", "Jane"],
                "stages_covered": ["acquisition"],
                "key_findings": ["Manual quote process"],
                "analyzed": True
            }
        ],
        "tools": [],
        "pain_points": [],
        "roi_items": [],
        "quick_wins": [],
        "gemini_screenshots": [],
        "objections": [],
        "positive_signals": [],
        "data_gaps": []
    }
    ssad.update(overrides)
    return ssad


make_valid_ssad = make_valid_audit_data


class TestRequiredFields(unittest.TestCase):

    def test_missing_client_slug_is_critical(self):
        ssad = make_valid_ssad()
        del ssad["client_slug"]
        findings = validate(ssad)
        critical = [f for f in findings if f["severity"] == "critical"]
        self.assertTrue(any("client_slug" in f["field"] for f in critical))

    def test_missing_processes_is_critical(self):
        ssad = make_valid_ssad()
        del ssad["processes"]
        findings = validate(ssad)
        critical = [f for f in findings if f["severity"] == "critical"]
        self.assertTrue(any("processes" in f["field"] for f in critical))

    def test_valid_ssad_has_no_critical_or_high(self):
        ssad = make_valid_ssad()
        findings = validate(ssad)
        blocking = [f for f in findings if f["severity"] in ("critical", "high")]
        self.assertEqual(blocking, [], f"Unexpected critical/high findings: {blocking}")


class TestContactValidation(unittest.TestCase):

    def test_empty_contact_name_is_high(self):
        ssad = make_valid_ssad()
        ssad["contact"]["name"] = ""
        findings = validate(ssad)
        high = [f for f in findings if f["severity"] == "high"]
        self.assertTrue(any("contact.name" in f["field"] for f in high))

    def test_empty_contact_role_is_medium(self):
        ssad = make_valid_ssad()
        ssad["contact"]["role"] = ""
        findings = validate(ssad)
        medium = [f for f in findings if f["severity"] == "medium"]
        self.assertTrue(any("contact.role" in f["field"] for f in medium))


class TestBlendedRateValidation(unittest.TestCase):

    def test_null_rate_is_high(self):
        ssad = make_valid_ssad(blended_hourly_rate_aud=None)
        findings = validate(ssad)
        high = [f for f in findings if f["severity"] == "high"]
        self.assertTrue(any("blended_hourly_rate_aud" in f["field"] for f in high))

    def test_negative_rate_is_high(self):
        ssad = make_valid_ssad(blended_hourly_rate_aud=-10)
        findings = validate(ssad)
        high = [f for f in findings if f["severity"] == "high"]
        self.assertTrue(any("blended_hourly_rate_aud" in f["field"] for f in high))

    def test_confidence_field_is_not_validated(self):
        # blended_rate_confidence is no longer required or validated.
        # The blended rate is fixed at $50/hr by convention.
        ssad = make_valid_ssad(blended_rate_confidence="UNKNOWN")
        findings = validate(ssad)
        conf_issues = [f for f in findings if "blended_rate_confidence" in f["field"]]
        self.assertEqual(conf_issues, [])

    def test_valid_rate_passes(self):
        ssad = make_valid_ssad(blended_hourly_rate_aud=50.0, blended_rate_confidence="LOW")
        findings = validate(ssad)
        rate_issues = [f for f in findings if "blended" in f["field"] and f["severity"] in ("critical", "high")]
        self.assertEqual(rate_issues, [])


class TestProcessValidation(unittest.TestCase):

    def test_step_missing_description_is_high(self):
        ssad = make_valid_ssad()
        ssad["processes"][0]["steps"][0]["description"] = ""
        findings = validate(ssad)
        high = [f for f in findings if f["severity"] == "high"]
        self.assertTrue(any("description" in f["field"] for f in high))

    def test_invalid_step_type_is_medium(self):
        ssad = make_valid_ssad()
        ssad["processes"][0]["steps"][0]["type"] = "unknown_type"
        findings = validate(ssad)
        medium = [f for f in findings if f["severity"] == "medium"]
        self.assertTrue(any("type" in f["field"] for f in medium))

    def test_step_missing_quote_is_medium(self):
        ssad = make_valid_ssad()
        ssad["processes"][0]["steps"][0]["source_quote"] = ""
        findings = validate(ssad)
        medium = [f for f in findings if f["severity"] == "medium"]
        self.assertTrue(any("source_quote" in f["field"] for f in medium))


class TestWasteItemValidation(unittest.TestCase):

    def test_high_confidence_without_annual_waste_is_high(self):
        ssad = make_valid_ssad()
        ssad["waste_items"][0]["annual_waste_aud"] = None
        findings = validate(ssad)
        high = [f for f in findings if f["severity"] == "high"]
        self.assertTrue(any("annual_waste_aud" in f["field"] for f in high))

    def test_low_confidence_without_annual_waste_is_ok(self):
        ssad = make_valid_ssad()
        ssad["waste_items"][0]["confidence"] = "LOW"
        ssad["waste_items"][0]["annual_waste_aud"] = None
        findings = validate(ssad)
        # LOW confidence items don't need annual_waste_aud — but they do need a HIGH item elsewhere
        # Our valid ssad no longer has a HIGH waste item, so that check fires instead
        # This test just verifies the specific annual_waste_aud check doesn't fire for LOW
        annual_waste_findings = [f for f in findings if "annual_waste_aud" in f["field"]]
        self.assertEqual(annual_waste_findings, [])

    def test_waste_item_missing_quote_is_medium(self):
        ssad = make_valid_ssad()
        ssad["waste_items"][0]["quote"] = ""
        findings = validate(ssad)
        medium = [f for f in findings if f["severity"] == "medium"]
        self.assertTrue(any("quote" in f["field"] for f in medium))

    def test_no_high_confidence_items_after_session_1_is_high(self):
        ssad = make_valid_ssad(audit_status="session-2")
        ssad["waste_items"][0]["confidence"] = "LOW"
        findings = validate(ssad)
        high = [f for f in findings if f["severity"] == "high"]
        self.assertTrue(any("waste_items" in f["field"] for f in high))

    def test_discovery_status_does_not_require_high_waste(self):
        ssad = make_valid_ssad(audit_status="discovery")
        ssad["waste_items"][0]["confidence"] = "LOW"
        ssad["waste_items"][0]["annual_waste_aud"] = None
        findings = validate(ssad)
        high_waste = [f for f in findings if f["field"] == "waste_items" and f["severity"] == "high"]
        self.assertEqual(high_waste, [])


class TestContradictionsAndFollowUps(unittest.TestCase):

    def test_unresolved_contradiction_is_medium(self):
        ssad = make_valid_ssad()
        ssad["contradictions"] = [
            {
                "contradiction_id": "C001",
                "topic": "Follow-up process",
                "statement_a": {"session": 1, "speaker": "Jane", "quote": "We use CRM", "timestamp": ""},
                "statement_b": {"session": 2, "speaker": "Mark", "quote": "We use spreadsheets", "timestamp": ""},
                "resolution": "",
                "status": "unresolved"
            }
        ]
        findings = validate(ssad)
        medium = [f for f in findings if f["severity"] == "medium"]
        self.assertTrue(any("contradictions" in f["field"] for f in medium))

    def test_pending_high_followup_is_medium(self):
        ssad = make_valid_ssad()
        ssad["follow_up_questions"] = [
            {"question": "How long does quoting take?", "stage": "quoting",
             "priority": "HIGH", "reason": "No time data", "status": "pending"}
        ]
        findings = validate(ssad)
        medium = [f for f in findings if f["severity"] == "medium"]
        self.assertTrue(any("follow_up_questions" in f["field"] for f in medium))


if __name__ == "__main__":
    # Run tests and report results
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"\n{'='*50}")
    print(f"Results: {passed}/{result.testsRun} passed")
    if result.failures or result.errors:
        sys.exit(1)
    else:
        print("All tests passed.")
        sys.exit(0)
