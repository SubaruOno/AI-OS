#!/usr/bin/env python3
"""Tests for validate_bpmn_json.py — BPMN JSON structural linter."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from validate_bpmn_json import validate_bpmn_json


def _proc(stage="test", steps=None, flows=None, lanes=None):
    return {
        "stage": stage,
        "steps": steps or [],
        "sequence_flows": flows or [],
        "lanes": lanes or [],
    }


def _step(sid, element_type="task", lane_id="Lane_A"):
    return {"step_id": sid, "element_type": element_type, "lane_id": lane_id}


def _flow(fid, src, tgt, condition=None):
    f = {"id": fid, "from": src, "to": tgt}
    if condition:
        f["condition"] = condition
    return f


def _find(findings, rule):
    return [f for f in findings if f["rule"] == rule]


class TestBJ01SingleStartEvent:
    def test_no_start_events_passes(self):
        proc = _proc(steps=[_step("A"), _step("B")],
                      flows=[_flow("F1", "A", "B")])
        findings = validate_bpmn_json({"processes": [proc]})
        assert not _find(findings, "BJ01")

    def test_one_start_event_passes(self):
        proc = _proc(steps=[_step("S", "start_event"), _step("A"), _step("E", "end_event")],
                      flows=[_flow("F1", "S", "A"), _flow("F2", "A", "E")])
        findings = validate_bpmn_json({"processes": [proc]})
        assert not _find(findings, "BJ01")

    def test_two_start_events_fails(self):
        proc = _proc(steps=[_step("S1", "start_event"), _step("S2", "start_event"), _step("A")],
                      flows=[_flow("F1", "S1", "A"), _flow("F2", "S2", "A")])
        findings = validate_bpmn_json({"processes": [proc]})
        bj01 = _find(findings, "BJ01")
        assert len(bj01) == 1
        assert bj01[0]["severity"] == "blocker"


class TestBJ02EndEventRequired:
    def test_no_end_event_fails(self):
        proc = _proc(steps=[_step("S", "start_event"), _step("A"), _step("B")],
                      flows=[_flow("F1", "S", "A"), _flow("F2", "A", "B")])
        findings = validate_bpmn_json({"processes": [proc]})
        bj02 = _find(findings, "BJ02")
        assert len(bj02) == 1
        assert bj02[0]["severity"] == "blocker"

    def test_two_end_events_valid(self):
        proc = _proc(steps=[_step("A"), _step("E1", "end_event"), _step("E2", "end_event")],
                      flows=[_flow("F1", "A", "E1"), _flow("F2", "A", "E2")])
        findings = validate_bpmn_json({"processes": [proc]})
        bj02 = _find(findings, "BJ02")
        assert len(bj02) == 0


class TestBJ03BJ04FlowReferences:
    def test_valid_flows_pass(self):
        proc = _proc(steps=[_step("A"), _step("B")],
                      flows=[_flow("F1", "A", "B")])
        findings = validate_bpmn_json({"processes": [proc]})
        assert not _find(findings, "BJ03")
        assert not _find(findings, "BJ04")

    def test_dangling_source_high(self):
        proc = _proc(steps=[_step("A"), _step("B")],
                      flows=[_flow("F1", "MISSING", "B")])
        findings = validate_bpmn_json({"processes": [proc]})
        bj03 = _find(findings, "BJ03")
        assert len(bj03) == 1
        assert bj03[0]["severity"] == "high"

    def test_cross_process_target_medium(self):
        proc1 = _proc(stage="acquisition",
                       steps=[_step("ACQ-001"), _step("ACQ-002")],
                       flows=[_flow("F1", "ACQ-001", "ACQ-002"), _flow("F2", "ACQ-002", "QUA-001")])
        proc2 = _proc(stage="qualification",
                       steps=[_step("QUA-001"), _step("QUA-002")],
                       flows=[_flow("F3", "QUA-001", "QUA-002")])
        findings = validate_bpmn_json({"processes": [proc1, proc2]})
        bj04 = _find(findings, "BJ04")
        assert len(bj04) == 1
        assert bj04[0]["severity"] == "medium"
        assert "cross-process" in bj04[0]["message"]


class TestBJ05DuplicateStepIds:
    def test_no_duplicates_pass(self):
        proc = _proc(steps=[_step("A"), _step("B")])
        findings = validate_bpmn_json({"processes": [proc]})
        assert not _find(findings, "BJ05")

    def test_duplicate_fails(self):
        proc = _proc(steps=[_step("A"), _step("A")])
        findings = validate_bpmn_json({"processes": [proc]})
        bj05 = _find(findings, "BJ05")
        assert len(bj05) == 1
        assert bj05[0]["severity"] == "high"


class TestBJ06OrphanNodes:
    def test_connected_nodes_pass(self):
        proc = _proc(steps=[_step("S", "start_event"), _step("A"), _step("E", "end_event")],
                      flows=[_flow("F1", "S", "A"), _flow("F2", "A", "E")])
        findings = validate_bpmn_json({"processes": [proc]})
        assert not _find(findings, "BJ06")

    def test_orphan_sink_detected(self):
        proc = _proc(steps=[_step("S", "start_event"), _step("A"), _step("B"), _step("E", "end_event")],
                      flows=[_flow("F1", "S", "A"), _flow("F2", "A", "E")])
        findings = validate_bpmn_json({"processes": [proc]})
        bj06 = _find(findings, "BJ06")
        orphan_sinks = [f for f in bj06 if "orphan sink" in f["message"]]
        assert any("B" in f["message"] for f in orphan_sinks)

    def test_partial_ok_suppresses(self):
        proc = _proc(steps=[_step("S", "start_event"), _step("A"), _step("B"), _step("E", "end_event")],
                      flows=[_flow("F1", "S", "A"), _flow("F2", "A", "E")])
        findings = validate_bpmn_json({"processes": [proc]}, partial_ok=True)
        assert not _find(findings, "BJ06")


class TestBJ07ExclusiveGateway:
    def test_gateway_with_two_outgoing_passes(self):
        proc = _proc(steps=[_step("A"), _step("G", "exclusive_gateway"), _step("B"), _step("C")],
                      flows=[_flow("F1", "A", "G"), _flow("F2", "G", "B"), _flow("F3", "G", "C")])
        findings = validate_bpmn_json({"processes": [proc]})
        assert not _find(findings, "BJ07")

    def test_gateway_with_one_outgoing_fails(self):
        proc = _proc(steps=[_step("A"), _step("G", "exclusive_gateway"), _step("B")],
                      flows=[_flow("F1", "A", "G"), _flow("F2", "G", "B")])
        findings = validate_bpmn_json({"processes": [proc]})
        bj07 = _find(findings, "BJ07")
        assert len(bj07) == 1
        assert bj07[0]["severity"] == "medium"

    def test_partial_ok_suppresses(self):
        proc = _proc(steps=[_step("A"), _step("G", "exclusive_gateway"), _step("B")],
                      flows=[_flow("F1", "A", "G"), _flow("F2", "G", "B")])
        findings = validate_bpmn_json({"processes": [proc]}, partial_ok=True)
        assert not _find(findings, "BJ07")


class TestBJ09DuplicateFlowIds:
    def test_duplicate_flow_id(self):
        proc = _proc(steps=[_step("A"), _step("B"), _step("C")],
                      flows=[_flow("F1", "A", "B"), _flow("F1", "B", "C")])
        findings = validate_bpmn_json({"processes": [proc]})
        bj09 = _find(findings, "BJ09")
        assert len(bj09) == 1
        assert bj09[0]["severity"] == "medium"


class TestBJ10ParallelGatewayPairing:
    def test_balanced_fork_join_passes(self):
        proc = _proc(
            steps=[_step("A"), _step("PG1", "parallel_gateway"), _step("B"), _step("C"),
                   _step("PG2", "parallel_gateway"), _step("D")],
            flows=[_flow("F1", "A", "PG1"), _flow("F2", "PG1", "B"), _flow("F3", "PG1", "C"),
                   _flow("F4", "B", "PG2"), _flow("F5", "C", "PG2"), _flow("F6", "PG2", "D")])
        findings = validate_bpmn_json({"processes": [proc]})
        assert not _find(findings, "BJ10")

    def test_imbalanced_flags(self):
        proc = _proc(
            steps=[_step("PG1", "parallel_gateway"), _step("B"), _step("C"),
                   _step("PG2", "parallel_gateway"), _step("D"), _step("E")],
            flows=[_flow("F1", "PG1", "B"), _flow("F2", "PG1", "C"),
                   _flow("F3", "PG2", "D"), _flow("F4", "PG2", "E"),
                   _flow("F5", "B", "D"), _flow("F6", "C", "E")])
        findings = validate_bpmn_json({"processes": [proc]})
        bj10 = _find(findings, "BJ10")
        assert len(bj10) == 1
        assert bj10[0]["severity"] == "low"


class TestBJ17ForwardReachability:
    def test_fully_connected_passes(self):
        proc = _proc(steps=[_step("S", "start_event"), _step("A"), _step("B"), _step("E", "end_event")],
                      flows=[_flow("F1", "S", "A"), _flow("F2", "A", "B"), _flow("F3", "B", "E")])
        findings = validate_bpmn_json({"processes": [proc]})
        assert not _find(findings, "BJ17")

    def test_disconnected_node_caught(self):
        proc = _proc(steps=[_step("S", "start_event"), _step("A"), _step("B"), _step("C"), _step("E", "end_event")],
                      flows=[_flow("F1", "S", "A"), _flow("F2", "A", "E"), _flow("F3", "B", "C")])
        findings = validate_bpmn_json({"processes": [proc]})
        bj17 = _find(findings, "BJ17")
        unreachable_ids = {f["step_id"] for f in bj17}
        assert "B" in unreachable_ids
        assert "C" in unreachable_ids
        assert all(f["severity"] == "high" for f in bj17)

    def test_loop_island_caught(self):
        proc = _proc(steps=[_step("S", "start_event"), _step("A"), _step("X"), _step("Y"), _step("E", "end_event")],
                      flows=[_flow("F1", "S", "A"), _flow("F2", "A", "E"),
                             _flow("F3", "X", "Y"), _flow("F4", "Y", "X")])
        findings = validate_bpmn_json({"processes": [proc]})
        bj17 = _find(findings, "BJ17")
        unreachable_ids = {f["step_id"] for f in bj17}
        assert "X" in unreachable_ids
        assert "Y" in unreachable_ids

    def test_partial_ok_suppresses(self):
        proc = _proc(steps=[_step("S", "start_event"), _step("A"), _step("B"), _step("E", "end_event")],
                      flows=[_flow("F1", "S", "A"), _flow("F2", "A", "E")])
        findings = validate_bpmn_json({"processes": [proc]}, partial_ok=True)
        assert not _find(findings, "BJ17")


class TestBJ18BackwardReachability:
    def test_fully_connected_passes(self):
        proc = _proc(steps=[_step("S", "start_event"), _step("A"), _step("B"), _step("E", "end_event")],
                      flows=[_flow("F1", "S", "A"), _flow("F2", "A", "B"), _flow("F3", "B", "E")])
        findings = validate_bpmn_json({"processes": [proc]})
        assert not _find(findings, "BJ18")

    def test_no_path_to_end_caught(self):
        proc = _proc(steps=[_step("S", "start_event"), _step("A"), _step("B"), _step("C"), _step("E", "end_event")],
                      flows=[_flow("F1", "S", "A"), _flow("F2", "A", "B"), _flow("F3", "A", "C"), _flow("F4", "C", "E")])
        findings = validate_bpmn_json({"processes": [proc]})
        bj18 = _find(findings, "BJ18")
        unreachable_ids = {f["step_id"] for f in bj18}
        assert "B" in unreachable_ids
        assert all(f["severity"] == "high" for f in bj18)

    def test_bidirectional_loop_no_exit(self):
        proc = _proc(steps=[_step("S", "start_event"), _step("A"), _step("B"), _step("E", "end_event")],
                      flows=[_flow("F1", "S", "A"), _flow("F2", "A", "B"), _flow("F3", "B", "A")])
        findings = validate_bpmn_json({"processes": [proc]})
        bj18 = _find(findings, "BJ18")
        unreachable_ids = {f["step_id"] for f in bj18}
        assert "S" in unreachable_ids
        assert "A" in unreachable_ids
        assert "B" in unreachable_ids

    def test_partial_ok_suppresses(self):
        proc = _proc(steps=[_step("S", "start_event"), _step("A"), _step("B"), _step("E", "end_event")],
                      flows=[_flow("F1", "S", "A"), _flow("F2", "A", "B")])
        findings = validate_bpmn_json({"processes": [proc]}, partial_ok=True)
        assert not _find(findings, "BJ18")


class TestFullyValidExtraction:
    def test_clean_process_passes(self):
        proc = _proc(
            stage="onboarding",
            steps=[
                _step("S", "start_event"),
                _step("A"),
                _step("B"),
                _step("E", "end_event"),
            ],
            flows=[
                _flow("F1", "S", "A"),
                _flow("F2", "A", "B"),
                _flow("F3", "B", "E"),
            ],
        )
        findings = validate_bpmn_json({"processes": [proc]})
        assert all(f["severity"] not in ("high", "critical") for f in findings)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
