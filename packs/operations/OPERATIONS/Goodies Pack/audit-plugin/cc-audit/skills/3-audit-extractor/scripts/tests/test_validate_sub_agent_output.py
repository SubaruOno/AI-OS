#!/usr/bin/env python3
"""Unit tests for validate_sub_agent_output.py (Source Attribution Gate)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from validate_sub_agent_output import validate


def _fathom_src(quote="a verbatim quote from the call", speaker="Adam",
                session_id=1, ts=1422, confidence="HIGH"):
    return {
        "kind": "fathom",
        "quote": quote,
        "speaker": speaker,
        "confidence": confidence,
        "session_id": session_id,
        "timestamp_seconds": ts,
    }


def _doc_src(quote="a verbatim line from the document", document_path="clients/x/y.md",
             speaker=None, confidence="MEDIUM"):
    return {
        "kind": "document",
        "quote": quote,
        "speaker": speaker,
        "confidence": confidence,
        "document_path": document_path,
    }


class GateTests(unittest.TestCase):

    def test_valid_fathom_pain_point_passes(self):
        payload = {"new_pain_points": [
            {"pain_point_id": "PP-001", "title": "x", "sources": [_fathom_src()]}
        ]}
        checked, failures = validate(payload, source_type="fathom_meeting")
        self.assertEqual(checked, 1)
        self.assertEqual(failures, [])

    def test_valid_document_waste_passes(self):
        payload = {"new_waste_items": [
            {"waste_id": "W-001", "activity": "x", "sources": [_doc_src()]}
        ]}
        checked, failures = validate(payload, source_type="email")
        self.assertEqual(checked, 1)
        self.assertEqual(failures, [])

    def test_empty_sources_fails(self):
        payload = {"new_pain_points": [
            {"pain_point_id": "PP-001", "title": "x", "sources": []}
        ]}
        checked, failures = validate(payload, source_type="fathom_meeting")
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["reason"], "no_sources")

    def test_missing_sources_field_fails(self):
        payload = {"new_pain_points": [
            {"pain_point_id": "PP-001", "title": "x"}
        ]}
        checked, failures = validate(payload, source_type="fathom_meeting")
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["reason"], "no_sources")

    def test_fathom_entry_missing_timestamp_fails(self):
        bad = _fathom_src()
        del bad["timestamp_seconds"]
        payload = {"new_steps": [
            {"step_id": "ACQ-001", "description": "x", "sources": [bad]}
        ]}
        checked, failures = validate(payload, source_type="fathom_meeting")
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["reason"], "invalid_source_entries")
        self.assertIn("timestamp_seconds", failures[0]["missing_fields"][0])

    def test_document_entry_missing_path_fails(self):
        bad = _doc_src()
        bad["document_path"] = ""
        payload = {"new_optimisations": [
            {"optimisation_id": "OPT-001", "description": "x", "sources": [bad]}
        ]}
        checked, failures = validate(payload, source_type="pdf")
        self.assertEqual(len(failures), 1)
        self.assertIn("document_path", failures[0]["missing_fields"][0])

    def test_contradiction_needs_two_sources(self):
        payload = {"new_contradictions": [
            {"contradiction_id": "CTR-001", "topic": "x",
             "sources": [_fathom_src(session_id=1)]}
        ]}
        checked, failures = validate(payload, source_type="fathom_meeting")
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["reason"], "contradiction_needs_two_sources")

    def test_contradiction_with_two_valid_sources_passes(self):
        payload = {"new_contradictions": [
            {"contradiction_id": "CTR-001", "topic": "x",
             "sources": [_fathom_src(session_id=1, ts=100),
                         _fathom_src(session_id=2, ts=200, speaker="Priya")]}
        ]}
        checked, failures = validate(payload, source_type="fathom_meeting")
        self.assertEqual(failures, [])

    def test_tool_update_action_skipped(self):
        # tool_updates with action != "create" don't need full attribution
        payload = {"tool_updates": [
            {"tool_name": "HubSpot", "action": "update_existing"}
        ]}
        checked, failures = validate(payload, source_type="fathom_meeting")
        self.assertEqual(checked, 0)
        self.assertEqual(failures, [])

    def test_tool_create_needs_sources(self):
        payload = {"tool_updates": [
            {"tool_name": "HubSpot", "action": "create"}
        ]}
        checked, failures = validate(payload, source_type="fathom_meeting")
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["reason"], "no_sources")

    def test_empty_payload_passes(self):
        checked, failures = validate({}, source_type="fathom_meeting")
        self.assertEqual(checked, 0)
        self.assertEqual(failures, [])

    def test_fathom_source_type_with_document_only_item_fails_form(self):
        # If the source is a fathom meeting, the item should carry a fathom source
        payload = {"new_pain_points": [
            {"pain_point_id": "PP-001", "title": "x", "sources": [_doc_src()]}
        ]}
        checked, failures = validate(payload, source_type="fathom_meeting")
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["reason"], "wrong_form_expected_fathom")

    def test_multi_source_corroboration_passes(self):
        # Fathom + document corroboration is OK if expected_kind is matched
        payload = {"new_waste_items": [
            {"waste_id": "W-001", "activity": "x",
             "sources": [_fathom_src(), _doc_src()]}
        ]}
        checked, failures = validate(payload, source_type="fathom_meeting")
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
