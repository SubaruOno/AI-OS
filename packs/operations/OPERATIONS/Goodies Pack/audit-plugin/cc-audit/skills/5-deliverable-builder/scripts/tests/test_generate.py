#!/usr/bin/env python3
"""
Tests for generate.py — verifies HTML output structure and data binding.
Run: python3 test_generate.py
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from generate import (
    generate_process_map,
    generate_audit_report,
    generate_client_website,
    fmt_aud,
)


def make_audit_data(**overrides) -> dict:
    ssad = {
        "client_slug": "test-co",
        "company_name": "Test Co Pty Ltd",
        "industry_tag": "home-services",
        "audit_status": "session-2",
        "sessions_completed": 2,
        "contact": {"name": "Jane Smith", "role": "Owner", "company_size": "12", "revenue_range": "$2M"},
        "blended_hourly_rate_aud": 45.0,
        "blended_rate_confidence": "HIGH",
        "blended_rate_source": "Owner stated",
        "processes": [
            {
                "stage": "acquisition",
                "steps": [
                    {"step_id": "S1", "description": "Receive lead via Google form",
                     "owner": "Admin", "type": "step", "confidence": "HIGH",
                     "source_quote": "All leads come through the Google form", "source_session": 1,
                     "source_speaker": "Jane"},
                    {"step_id": "S2", "description": "If job value > $5k, escalate to owner",
                     "owner": "Admin", "type": "decision", "confidence": "HIGH",
                     "source_quote": "Big jobs go to me directly", "source_session": 1,
                     "source_speaker": "Jane"},
                ]
            }
        ],
        "waste_items": [
            {"activity": "Manual quote entry", "hours_per_week": 5, "headcount_affected": 2,
             "annual_waste_aud": 23400, "monthly_waste_aud": 1950,
             "waste_type": "manual_data_entry", "quote": "Takes us 5 hours a week",
             "confidence": "HIGH", "source_session": 1},
            {"activity": "Phone tag for scheduling", "hours_per_week": 3, "headcount_affected": 1,
             "annual_waste_aud": 7020, "monthly_waste_aud": 585,
             "waste_type": "communication_gap", "quote": "Always playing phone tag",
             "confidence": "MEDIUM", "source_session": 1},
        ],
        "roi_items": [
            {"activity": "Automated quote generation", "annual_saving_aud": 23400,
             "monthly_saving_aud": 1950, "suggested_tier": "standard",
             "build_cost_aud": 3800, "payback_months": 1.95, "payback_tag": "QUICK_WIN",
             "quote": "Takes us 5 hours a week", "confidence": "HIGH"},
        ],
        "pain_points": [
            {"description": "Manual quoting takes too long", "stage": "quoting",
             "quote": "It takes forever to do quotes manually", "speaker": "Jane",
             "source_session": 1, "confidence": "HIGH"},
        ],
        "decision_nodes": [],
        "contradictions": [],
        "completeness_checklist": {
            "acquisition": {"covered": True, "confidence": "HIGH", "items_confirmed": [], "items_missing": []},
            "quoting": {"covered": True, "confidence": "MEDIUM", "items_confirmed": [], "items_missing": []},
            "onboarding": {"covered": False, "confidence": "LOW", "items_confirmed": [], "items_missing": []},
            "fulfilment": {"covered": False, "confidence": "LOW", "items_confirmed": [], "items_missing": []},
            "retention": {"covered": False, "confidence": "LOW", "items_confirmed": [], "items_missing": []},
        },
        "follow_up_questions": [],
        "sessions": [
            {"session_number": 1, "date": "2026-03-01", "transcript_file": "s1.txt",
             "participants": ["Adam", "Jane"], "stages_covered": ["acquisition", "quoting"],
             "key_findings": ["Manual quoting"], "analyzed": True},
        ],
        "tools": [], "quick_wins": [], "gemini_screenshots": [],
        "objections": [], "positive_signals": [], "data_gaps": [],
    }
    ssad.update(overrides)
    return ssad


class TestFmtAud(unittest.TestCase):
    def test_formats_integer(self):
        self.assertEqual(fmt_aud(23400), "$23,400")

    def test_formats_float(self):
        # Python :.0f uses banker's rounding (round half to even)
        self.assertEqual(fmt_aud(1950.5), "$1,950")
        self.assertEqual(fmt_aud(1951.5), "$1,952")

    def test_none_returns_na(self):
        self.assertEqual(fmt_aud(None), "N/A")

    def test_zero(self):
        self.assertEqual(fmt_aud(0), "$0")


class TestProcessMapGenerator(unittest.TestCase):
    def setUp(self):
        self.ssad = make_audit_data()
        self.html = generate_process_map(self.ssad)

    def test_returns_html_string(self):
        self.assertIsInstance(self.html, str)
        self.assertIn("<!DOCTYPE html>", self.html)

    def test_contains_company_name(self):
        self.assertIn("Test Co Pty Ltd", self.html)

    def test_contains_stage_labels(self):
        self.assertIn("Acquisition", self.html)
        self.assertIn("Quoting", self.html)

    def test_contains_step_descriptions(self):
        self.assertIn("Receive lead via Google form", self.html)

    def test_pending_zone_for_empty_stage(self):
        self.assertIn("Data collection in progress", self.html)

    def test_decision_step_renders(self):
        self.assertIn("If job value &gt; $5k, escalate to owner", self.html)

    def test_heatmap_toggle_present(self):
        self.assertIn("heatmapToggle", self.html)

    def test_source_quote_in_data_attribute(self):
        self.assertIn("All leads come through", self.html)


class TestAuditReportGenerator(unittest.TestCase):
    def setUp(self):
        self.ssad = make_audit_data()
        self.html = generate_audit_report(self.ssad)

    def test_returns_html_string(self):
        self.assertIn("<!DOCTYPE html>", self.html)

    def test_company_name_present(self):
        self.assertIn("Test Co Pty Ltd", self.html)

    def test_total_waste_calculated(self):
        # $23,400 + $7,020 = $30,420
        self.assertIn("30,420", self.html)

    def test_quick_win_section_present(self):
        self.assertIn("Quick Wins", self.html)
        self.assertIn("Automated quote generation", self.html)

    def test_pain_points_table_present(self):
        self.assertIn("Manual quoting takes too long", self.html)

    def test_verbatim_quotes_included(self):
        self.assertIn("Takes us 5 hours a week", self.html)

    def test_unresolved_contradiction_warning(self):
        ssad = make_audit_data()
        ssad["contradictions"] = [{
            "contradiction_id": "C1",
            "topic": "CRM vs spreadsheet",
            "statement_a": {"session": 1, "speaker": "Jane", "quote": "We use CRM", "timestamp": ""},
            "statement_b": {"session": 2, "speaker": "Mark", "quote": "We use spreadsheets", "timestamp": ""},
            "resolution": "", "status": "unresolved"
        }]
        html = generate_audit_report(ssad)
        self.assertIn("unresolved contradiction", html)
        self.assertIn("CRM vs spreadsheet", html)


class TestClientWebsiteGenerator(unittest.TestCase):
    def setUp(self):
        self.ssad = make_audit_data()
        self.html = generate_client_website(self.ssad)

    def test_returns_html_string(self):
        self.assertIn("<!DOCTYPE html>", self.html)

    def test_company_name_in_hero(self):
        self.assertIn("Test Co Pty Ltd", self.html)

    def test_five_stages_shown(self):
        for stage in ["Acquisition", "Quoting", "Onboarding", "Fulfilment", "Retention"]:
            self.assertIn(stage, self.html)

    def test_guarantee_section_present(self):
        self.assertIn("APG Guarantee", self.html)
        self.assertIn("$5,000", self.html)

    def test_s1_findings_unlocked_when_sessions_gte_1(self):
        # sessions_completed = 2, so S1 should be unlocked
        self.assertIn("Manual quoting takes too long", self.html)

    def test_quick_wins_locked_when_sessions_lt_3(self):
        # sessions_completed = 2, quick wins need 3
        self.assertIn("Unlocked after Session 3", self.html)

    def test_quick_wins_unlocked_when_sessions_gte_3(self):
        ssad = make_audit_data(sessions_completed=3, audit_status="session-3")
        html = generate_client_website(ssad)
        self.assertIn("Automated quote generation", html)
        self.assertNotIn("Unlocked after Session 3", html)

    def test_discovery_status_locks_s1(self):
        ssad = make_audit_data(sessions_completed=0, audit_status="discovery")
        html = generate_client_website(ssad)
        self.assertIn("Unlocked after Session 1", html)

    def test_self_contained_no_cdn(self):
        # No external resource references
        self.assertNotIn("cdn.jsdelivr.net", self.html)
        self.assertNotIn("googleapis.com/css", self.html)
        self.assertNotIn('<script src="http', self.html)


if __name__ == "__main__":
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
