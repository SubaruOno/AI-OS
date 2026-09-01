"""BPMN 2.0 process map renderer.

Takes a `process` dict from extraction.json (with `lanes`, `steps`, `sequence_flows`)
and produces:
  - A BPMN 2.0 XML file with full BPMNDiagram layout coordinates
  - A per-process HTML page that renders the BPMN via bpmn-js with Fathom citation overlays
  - A landscape index HTML page (folder/card hub grouped by stage)

Module is self-contained: no external Python dependencies beyond stdlib.

Public entry points:
  - render_bpmn_processes(audit_data, client_meta, output_dir), top-level orchestrator
  - extraction_to_bpmn_xml(process), emit just the BPMN XML for one process

Schema expectations on each `process`:
  {
    "stage": "quoting",
    "name": "Quote turnaround",
    "process_id": "QUOT-quote-turnaround",
    "version": "1.0",
    "called_from": ["..."],
    "calls": ["..."],
    "lanes": [{"id", "name", "type": "role|system|external", "order": int}],
    "steps": [{"step_id", "bpmn_id", "title", "task_type", "lane_id",
               "type": "step|pain|optimisation|automation|decision",
               "owner", "tool_ids", "meeting_references": [...]}],
    "sequence_flows": [{"id", "source_ref", "target_ref", "condition_label?"}]
  }
"""

from __future__ import annotations

import html
import re
import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape as xml_escape


# ---------------------------------------------------------------------------
# Layout constants (BPMN coordinate space, bpmn-js consumes these directly)
# ---------------------------------------------------------------------------

POOL_X = 120
POOL_Y = 80
LANE_LABEL_WIDTH = 30          # vertical text column on the left of each lane
COL_WIDTH = 170                # horizontal spacing between task columns
DEFAULT_LANE_HEIGHT = 180
EVENT_LANE_HEIGHT = 140        # shorter lanes for external (events-only) participants

TASK_W, TASK_H = 120, 80
GATEWAY_W, GATEWAY_H = 50, 50
EVENT_W, EVENT_H = 36, 36

START_COL_PAD = 90             # left padding inside lane before first node
END_COL_PAD = 90               # right padding after last node


# ---------------------------------------------------------------------------
# Task-type → BPMN element name mapping
# ---------------------------------------------------------------------------

TASK_TYPE_TO_BPMN = {
    "user_task": "userTask",
    "service_task": "serviceTask",
    "send_task": "sendTask",
    "receive_task": "receiveTask",
    "manual_task": "manualTask",
    "business_rule_task": "businessRuleTask",
    "script_task": "scriptTask",
    "task": "task",
}


# ---------------------------------------------------------------------------
# Step type → BPMN-in-Color (paint pain points / optimisations / automations)
# ---------------------------------------------------------------------------

COLOR_BY_TYPE: dict[str, dict[str, str]] = {
    "pain":         {"stroke": "#c62828", "fill": "#ffebee"},
    "optimisation": {"stroke": "#2e7d32", "fill": "#e8f5e9"},
    "automation":   {"stroke": "#1565c0", "fill": "#e3f2fd"},
}


# ---------------------------------------------------------------------------
# Performer palette, same 9 colours as generate.py's OWNER_TAG_PALETTE so
# performers stay visually consistent across all client deliverables.
# ---------------------------------------------------------------------------

OWNER_TAG_PALETTE: list[tuple[str, str]] = [
    ("tag-pink",    "#d63384"),
    ("tag-orange",  "#c75000"),
    ("tag-teal",    "#0d9488"),
    ("tag-purple",  "#7b2fbe"),
    ("tag-amber",   "#d97706"),
    ("tag-blue",    "#2563EB"),
    ("tag-green",   "#198754"),
    ("tag-health",  "#0891b2"),
    ("tag-rose",    "#be185d"),
]

# Owner strings that look like tools/automation get the gear icon instead of
# initials, and no stripe (the lane IS the system).
_TOOL_KEYWORDS = {
    "automated", "automation", "system", "auto", "trigger", "scheduled",
    "hubspot", "monday", "twilio", "xero", "foundu", "google", "sheets",
    "zapier", "slack", "notion", "airtable", "asana", "jira", "salesforce",
    "stripe", "quickbooks", "myob", "deputy", "employment hero",
    "squarespace", "calendly", "gmail", "excel",
}

# External owners share a single neutral chip so the palette isn't fragmented
# across customers/prospects/suppliers.
_EXTERNAL_KEYWORDS = {
    "customer", "client", "prospect", "lead", "supplier", "vendor", "partner",
    "external", "regulator", "auditor", "investor",
}

EXTERNAL_CHIP_COLOR = "#6b7280"   # neutral grey
AUTOMATION_CHIP_COLOR = "#475569" # slate, distinct from external grey


def build_performer_palette(audit_data: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Map every distinct owner string across all processes to a stable colour.

    Returns:
        {
          owner_str: {
            "css_class": "tag-pink",
            "hex": "#d63384",
            "initials": "SR",
            "kind": "role" | "automation" | "external" | "unknown"
          }
        }
    """
    palette: dict[str, dict[str, str]] = {}
    idx = 0
    processes = audit_data.get("processes") or audit_data.get("extraction", {}).get("processes") or []
    seen_order: list[str] = []
    for proc in processes:
        for step in proc.get("steps") or []:
            owner = (step.get("owner") or "").strip()
            if not owner or owner in palette:
                continue
            kind = _classify_owner(owner)
            if kind == "automation":
                palette[owner] = {
                    "css_class": "perf-auto", "hex": AUTOMATION_CHIP_COLOR,
                    "initials": "AU", "kind": "automation",
                }
            elif kind == "external":
                palette[owner] = {
                    "css_class": "perf-external", "hex": EXTERNAL_CHIP_COLOR,
                    "initials": _initials_for_role(owner), "kind": "external",
                }
            else:
                css, hex_ = OWNER_TAG_PALETTE[idx % len(OWNER_TAG_PALETTE)]
                idx += 1
                palette[owner] = {
                    "css_class": css, "hex": hex_,
                    "initials": _initials_for_role(owner), "kind": "role",
                }
            seen_order.append(owner)
    return palette


def _classify_owner(owner: str) -> str:
    """Return 'automation' | 'external' | 'role'."""
    lo = owner.lower()
    if any(k == lo or k in lo.split() for k in _TOOL_KEYWORDS):
        return "automation"
    if any(k == lo or k in lo.split() for k in _EXTERNAL_KEYWORDS):
        return "external"
    return "role"


def _initials_for_role(role: str) -> str:
    """Two-letter initials from a role string: 'Sales Rep' → 'SR', 'Owner' → 'OW'."""
    role = (role or "").strip()
    if not role:
        return "?"
    words = [w for w in re.split(r'[\s/&-]+', role) if w]
    if len(words) >= 2:
        return (words[0][0] + words[1][0]).upper()
    word = words[0]
    return (word[:2]).upper() if len(word) >= 2 else (word[0] + word[0]).upper()


def format_duration_for_step(step: dict[str, Any]) -> str | None:
    """Prefer per-instance, fall back to weekly aggregate, else None."""
    per_instance = step.get("duration_per_instance_minutes")
    if isinstance(per_instance, (int, float)) and per_instance > 0:
        if per_instance < 60:
            mins = int(round(per_instance))
            return f"{mins} min"
        hours = per_instance / 60
        if hours == int(hours):
            return f"{int(hours)} hr"
        return f"{hours:.1f} hr"
    weekly = step.get("time_estimate_hours_per_week")
    if isinstance(weekly, (int, float)) and weekly > 0:
        if weekly < 1:
            mins = int(round(weekly * 60))
            return f"{mins} min/wk"
        if weekly == int(weekly):
            return f"{int(weekly)} hrs/wk"
        return f"{weekly:.1f} hrs/wk"
    return None


# ===========================================================================
# 1.  LAYOUT
# ===========================================================================

def compute_layout(process: dict[str, Any]) -> dict[str, Any]:
    """Assign (x, y, width, height) to every flow node and waypoints to every edge.

    Returns:
        {
          "pool":   {"x", "y", "width", "height"},
          "lanes":  {lane_id: {"x", "y", "width", "height", "name"}},
          "nodes":  {node_id: {"x", "y", "width", "height", "kind", "name", "lane_id"}},
          "edges":  {edge_id: {"waypoints": [(x, y), ...], "label_pos": (x, y) | None}},
        }
    """
    lanes = sorted(process.get("lanes", []), key=lambda l: l.get("order", 0))
    if not lanes:
        raise ValueError(f"process {process.get('name')} has no lanes")

    steps = process.get("steps", [])
    flows = process.get("sequence_flows", [])

    # ---- 1a. Collect every flow node referenced anywhere ----
    nodes_by_id: dict[str, dict[str, Any]] = {}

    for s in steps:
        node_id = s.get("bpmn_id") or s.get("step_id")
        if not node_id:
            continue
        kind = _node_kind_for_step(s)
        nodes_by_id[node_id] = {
            "id": node_id,
            "name": s.get("title", ""),
            "kind": kind,
            "task_type": s.get("task_type", "task"),
            "lane_id": s.get("lane_id"),
            "type": s.get("type", "step"),
            "step": s,
        }

    # Synthesise start/end events if not present in steps
    all_refs: set[str] = set()
    for f in flows:
        all_refs.add(f.get("source_ref"))
        all_refs.add(f.get("target_ref"))
    for ref in all_refs:
        if ref and ref not in nodes_by_id:
            # Guess kind by id prefix
            if ref.lower().startswith("startevent"):
                nodes_by_id[ref] = {"id": ref, "name": "Start", "kind": "startEvent",
                                    "lane_id": lanes[0]["id"], "type": "step", "step": None}
            elif ref.lower().startswith("endevent"):
                nodes_by_id[ref] = {"id": ref, "name": "End", "kind": "endEvent",
                                    "lane_id": lanes[0]["id"], "type": "step", "step": None}
            elif ref.lower().startswith("gateway"):
                nodes_by_id[ref] = {"id": ref, "name": "", "kind": "exclusiveGateway",
                                    "lane_id": lanes[0]["id"], "type": "decision", "step": None}

    # ---- 1b. Topological rank (column = longest distance from any start) ----
    incoming: dict[str, list[str]] = defaultdict(list)
    outgoing: dict[str, list[str]] = defaultdict(list)
    for f in flows:
        s, t = f.get("source_ref"), f.get("target_ref")
        if s and t:
            outgoing[s].append(t)
            incoming[t].append(s)

    ranks = _longest_path_ranks(nodes_by_id.keys(), incoming, outgoing)

    # ---- 1c. Build lane y-offsets ----
    lane_layout: dict[str, dict[str, Any]] = {}
    cursor_y = POOL_Y
    for lane in lanes:
        # Shorter lanes for external/events-only participants
        is_events_only = _lane_has_only_events(lane["id"], nodes_by_id)
        h = EVENT_LANE_HEIGHT if is_events_only else DEFAULT_LANE_HEIGHT
        lane_layout[lane["id"]] = {
            "name": lane.get("name", lane["id"]),
            "type": lane.get("type", "role"),
            "order": lane.get("order", 0),
            "y": cursor_y,
            "height": h,
        }
        cursor_y += h
    pool_height = cursor_y - POOL_Y

    # ---- 1d. Position each node within its lane at its rank column ----
    max_col = max(ranks.values()) if ranks else 0
    pool_width = LANE_LABEL_WIDTH + START_COL_PAD + (max_col * COL_WIDTH) + END_COL_PAD
    # Make sure pool is wide enough for at least the start + end column
    pool_width = max(pool_width, 800)

    for lane_info in lane_layout.values():
        lane_info["x"] = POOL_X
        lane_info["width"] = pool_width

    # Group nodes by (lane, column) so we can stack same-column same-lane nodes vertically
    bucket: dict[tuple[str, int], list[str]] = defaultdict(list)
    for node_id, node in nodes_by_id.items():
        col = ranks.get(node_id, 0)
        lane_id = node.get("lane_id") or lanes[0]["id"]
        bucket[(lane_id, col)].append(node_id)

    laid_out: dict[str, dict[str, Any]] = {}
    for (lane_id, col), node_ids in bucket.items():
        lane = lane_layout.get(lane_id)
        if not lane:
            continue
        lane_cx_anchor = POOL_X + LANE_LABEL_WIDTH + START_COL_PAD + (col * COL_WIDTH)
        # Stack multiple same-column nodes vertically inside the lane
        n = len(node_ids)
        for i, node_id in enumerate(node_ids):
            node = nodes_by_id[node_id]
            w, h = _shape_dimensions(node["kind"])
            # Center horizontally in the column
            x = lane_cx_anchor - w // 2
            # Distribute vertically within lane
            band = lane["height"] / (n + 1)
            cy = lane["y"] + band * (i + 1)
            y = int(cy - h / 2)
            laid_out[node_id] = {
                **node, "x": x, "y": y, "width": w, "height": h,
                "lane_id": lane_id, "col": col,
            }

    # ---- 1e. Compute edge waypoints ----
    edges: dict[str, dict[str, Any]] = {}
    for f in flows:
        eid = f.get("id")
        src = laid_out.get(f.get("source_ref"))
        tgt = laid_out.get(f.get("target_ref"))
        if not (eid and src and tgt):
            continue
        edges[eid] = {
            "waypoints": _route_edge(src, tgt),
            "label": f.get("condition_label") or f.get("name") or "",
            "source_ref": f.get("source_ref"),
            "target_ref": f.get("target_ref"),
        }

    return {
        "pool": {"x": POOL_X, "y": POOL_Y, "width": pool_width, "height": pool_height},
        "lanes": lane_layout,
        "nodes": laid_out,
        "edges": edges,
    }


def _longest_path_ranks(node_ids, incoming, outgoing) -> dict[str, int]:
    """Compute the longest path from any start node to each node (= column index).

    Cycles are broken by visiting in topological-ish order with a fallback BFS.
    """
    ids = list(node_ids)
    rank: dict[str, int] = {nid: 0 for nid in ids}
    in_degree = {nid: len(incoming.get(nid, [])) for nid in ids}

    # Start with all nodes that have no incoming edge
    queue = deque([nid for nid in ids if in_degree[nid] == 0])
    visited: set[str] = set()
    while queue:
        nid = queue.popleft()
        if nid in visited:
            continue
        visited.add(nid)
        for tgt in outgoing.get(nid, []):
            if rank.get(tgt, 0) < rank[nid] + 1:
                rank[tgt] = rank[nid] + 1
            in_degree[tgt] -= 1
            if in_degree[tgt] <= 0:
                queue.append(tgt)

    # Any unvisited (in a cycle) get rank based on max-incoming + 1
    for nid in ids:
        if nid not in visited:
            sources = incoming.get(nid, [])
            rank[nid] = max((rank.get(s, 0) + 1 for s in sources), default=0)

    return rank


def _lane_has_only_events(lane_id: str, nodes_by_id: dict[str, dict]) -> bool:
    kinds = [n["kind"] for n in nodes_by_id.values() if n.get("lane_id") == lane_id]
    return len(kinds) > 0 and all(k in ("startEvent", "endEvent") for k in kinds)


def _shape_dimensions(kind: str) -> tuple[int, int]:
    if kind in ("startEvent", "endEvent", "intermediateThrowEvent", "intermediateCatchEvent"):
        return EVENT_W, EVENT_H
    if kind in ("exclusiveGateway", "parallelGateway", "inclusiveGateway", "eventBasedGateway"):
        return GATEWAY_W, GATEWAY_H
    return TASK_W, TASK_H


def _node_kind_for_step(step: dict[str, Any]) -> str:
    """Map an extraction step to a BPMN element kind."""
    stype = step.get("type", "step")
    if stype == "decision":
        return "exclusiveGateway"
    if stype == "start":
        return "startEvent"
    if stype == "end":
        return "endEvent"
    task_type = step.get("task_type", "task")
    return TASK_TYPE_TO_BPMN.get(task_type, "task")


def _route_edge(src: dict, tgt: dict) -> list[tuple[int, int]]:
    """Orthogonal waypoints from source center-right to target center-left.

    Three cases:
      same lane, same col: bend up around
      same lane, src.col < tgt.col: straight horizontal
      different lane: out-right, vertical at mid-x, in-left
    """
    sx, sy = src["x"] + src["width"] // 2, src["y"] + src["height"] // 2
    tx, ty = tgt["x"] + tgt["width"] // 2, tgt["y"] + tgt["height"] // 2

    # Source exit point
    sx_right = src["x"] + src["width"]
    sx_left = src["x"]
    sy_top = src["y"]
    sy_bot = src["y"] + src["height"]

    # Target entry point
    tx_left = tgt["x"]
    tx_right = tgt["x"] + tgt["width"]
    ty_top = tgt["y"]
    ty_bot = tgt["y"] + tgt["height"]

    if src["lane_id"] == tgt["lane_id"]:
        if sy == ty and sx < tx:
            return [(sx_right, sy), (tx_left, ty)]
        # Same lane, different y (rare) or going backward
        return [(sx_right, sy), (sx_right + 20, sy), (sx_right + 20, ty), (tx_left, ty)]

    # Different lanes, go horizontal first, then vertical, then horizontal
    if sx < tx:
        mid_x = (sx_right + tx_left) // 2
        # Target is below source → exit right, descend, enter left
        if ty > sy:
            return [(sx_right, sy), (mid_x, sy), (mid_x, ty), (tx_left, ty)]
        # Target is above → exit right, ascend, enter left
        return [(sx_right, sy), (mid_x, sy), (mid_x, ty), (tx_left, ty)]

    if sx > tx:
        # Going backward (loop back), go right, down/up, back across, into target
        mid_x = sx_right + 30
        return [(sx_right, sy), (mid_x, sy), (mid_x, ty), (tx_right, ty)]

    # Same x, different lanes (vertical between stacked nodes)
    if ty > sy:
        return [(sx, sy_bot), (tx, ty_top)]
    return [(sx, sy_top), (tx, ty_bot)]


# ===========================================================================
# 2.  BPMN XML EMIT
# ===========================================================================

def extraction_to_bpmn_xml(process: dict[str, Any]) -> str:
    """Render one process to a complete BPMN 2.0 XML document string."""
    layout = compute_layout(process)
    proc_id = _sanitise_id(process.get("process_id") or process.get("name") or "Process")
    proc_name = xml_escape(process.get("name", proc_id))
    participant_id = f"Participant_{proc_id}"
    process_xml_id = f"Process_{proc_id}"
    collab_id = f"Collaboration_{proc_id}"
    diagram_id = f"BPMNDiagram_{proc_id}"
    plane_id = f"BPMNPlane_{proc_id}"

    # Group nodes by lane for laneSet emission
    lane_node_ids: dict[str, list[str]] = defaultdict(list)
    for nid, node in layout["nodes"].items():
        lane_node_ids[node["lane_id"]].append(nid)

    parts: list[str] = []
    parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    parts.append(
        '<bpmn:definitions '
        'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
        'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" '
        'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
        'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xmlns:bioc="http://bpmn.io/schema/bpmn/biocolor/1.0" '
        'xmlns:color="http://www.omg.org/spec/BPMN/non-normative/color/1.0" '
        f'id="Definitions_{proc_id}" targetNamespace="http://bosar.agency/bpmn">'
    )

    # Collaboration + Participant
    parts.append(f'<bpmn:collaboration id="{collab_id}">')
    parts.append(
        f'<bpmn:participant id="{participant_id}" name="{proc_name}" '
        f'processRef="{process_xml_id}" />'
    )
    parts.append('</bpmn:collaboration>')

    # Process body
    parts.append(f'<bpmn:process id="{process_xml_id}" name="{proc_name}" isExecutable="false">')

    # Lane set
    parts.append('<bpmn:laneSet id="LaneSet_1">')
    for lane in sorted(process.get("lanes", []), key=lambda l: l.get("order", 0)):
        lane_id = lane["id"]
        lane_name = xml_escape(lane.get("name", lane_id))
        parts.append(f'<bpmn:lane id="{lane_id}" name="{lane_name}">')
        for nid in lane_node_ids.get(lane_id, []):
            parts.append(f'<bpmn:flowNodeRef>{nid}</bpmn:flowNodeRef>')
        parts.append('</bpmn:lane>')
    parts.append('</bpmn:laneSet>')

    # Flow nodes
    flows_by_source: dict[str, list[str]] = defaultdict(list)
    flows_by_target: dict[str, list[str]] = defaultdict(list)
    for f in process.get("sequence_flows", []):
        src = f.get("source_ref") or f.get("from")
        tgt = f.get("target_ref") or f.get("to")
        if not src or not tgt:
            continue
        flows_by_source[src].append(f["id"])
        flows_by_target[tgt].append(f["id"])

    for nid, node in layout["nodes"].items():
        kind = node["kind"]
        name = xml_escape(node.get("name", ""))
        incoming = [f'<bpmn:incoming>{fid}</bpmn:incoming>' for fid in flows_by_target.get(nid, [])]
        outgoing = [f'<bpmn:outgoing>{fid}</bpmn:outgoing>' for fid in flows_by_source.get(nid, [])]
        gw_attr = ' isMarkerVisible="true"' if kind == "exclusiveGateway" else ''
        parts.append(f'<bpmn:{kind} id="{nid}" name="{name}"{gw_attr}>')
        parts.extend(incoming + outgoing)
        parts.append(f'</bpmn:{kind}>')

    # Sequence flows
    for f in process.get("sequence_flows", []):
        src = f.get("source_ref") or f.get("from")
        tgt = f.get("target_ref") or f.get("to")
        if not src or not tgt:
            continue
        fid = f["id"]
        label = xml_escape(f.get("condition_label") or f.get("name") or "")
        name_attr = f' name="{label}"' if label else ''
        parts.append(
            f'<bpmn:sequenceFlow id="{fid}"{name_attr} '
            f'sourceRef="{src}" targetRef="{tgt}" />'
        )

    parts.append('</bpmn:process>')

    # BPMNDiagram section
    parts.append(f'<bpmndi:BPMNDiagram id="{diagram_id}">')
    parts.append(f'<bpmndi:BPMNPlane id="{plane_id}" bpmnElement="{collab_id}">')

    # Pool shape
    pool = layout["pool"]
    parts.append(
        f'<bpmndi:BPMNShape id="{participant_id}_di" bpmnElement="{participant_id}" isHorizontal="true">'
        f'<dc:Bounds x="{pool["x"]}" y="{pool["y"]}" width="{pool["width"]}" height="{pool["height"]}" />'
        '</bpmndi:BPMNShape>'
    )

    # Lane shapes
    for lane_id, info in layout["lanes"].items():
        parts.append(
            f'<bpmndi:BPMNShape id="{lane_id}_di" bpmnElement="{lane_id}" isHorizontal="true">'
            f'<dc:Bounds x="{info["x"] + LANE_LABEL_WIDTH}" y="{info["y"]}" '
            f'width="{info["width"] - LANE_LABEL_WIDTH}" height="{info["height"]}" />'
            '</bpmndi:BPMNShape>'
        )

    # Node shapes, confidence-aware coloring via _color_attrs_for_node
    for nid, node in layout["nodes"].items():
        color_attrs = _color_attrs_for_node(node)
        parts.append(
            f'<bpmndi:BPMNShape id="{nid}_di" bpmnElement="{nid}"{color_attrs}>'
            f'<dc:Bounds x="{node["x"]}" y="{node["y"]}" '
            f'width="{node["width"]}" height="{node["height"]}" />'
            '</bpmndi:BPMNShape>'
        )

    # Edge shapes
    for eid, edge in layout["edges"].items():
        wp_str = ''.join(
            f'<di:waypoint x="{x}" y="{y}" />' for (x, y) in edge["waypoints"]
        )
        parts.append(
            f'<bpmndi:BPMNEdge id="{eid}_di" bpmnElement="{eid}">{wp_str}</bpmndi:BPMNEdge>'
        )

    parts.append('</bpmndi:BPMNPlane>')
    parts.append('</bpmndi:BPMNDiagram>')
    parts.append('</bpmn:definitions>')

    return '\n'.join(parts)


def _color_attrs_for_step_type(stype: str) -> str:
    colors = COLOR_BY_TYPE.get(stype)
    if not colors:
        return ''
    return (
        f' bioc:stroke="{colors["stroke"]}" bioc:fill="{colors["fill"]}"'
        f' color:background-color="{colors["fill"]}" color:border-color="{colors["stroke"]}"'
    )


_TASK_KINDS = frozenset({
    "task", "userTask", "serviceTask", "sendTask",
    "receiveTask", "manualTask", "businessRuleTask", "scriptTask",
})


def _color_attrs_for_node(node: dict) -> str:
    """Return bioc color attributes for a BPMNShape node.

    For gateway and event nodes, type-based annotation colors are used (pain=red,
    optimisation=green, automation=blue). For task nodes, confidence overrides the
    stroke: MEDIUM = amber, LOW or has _gaps = red. HIGH keeps the type coloring.
    """
    kind = node["kind"]
    stype = node.get("type", "step")

    # Events and gateways keep their semantic type coloring regardless of confidence
    if kind not in _TASK_KINDS:
        return _color_attrs_for_step_type(stype)

    step = node.get("step") or {}
    confidence = (step.get("confidence") or "HIGH").upper()
    gaps_obj = step.get("_gaps") or {}
    has_gaps = bool(gaps_obj)

    type_colors = COLOR_BY_TYPE.get(stype)
    type_fill = type_colors["fill"] if type_colors else "#ffffff"

    if has_gaps or confidence == "LOW":
        stroke, fill = "#EF4444", type_fill
        return (
            f' bioc:stroke="{stroke}" bioc:fill="{fill}"'
            f' color:background-color="{fill}" color:border-color="{stroke}"'
        )
    if confidence == "MEDIUM":
        stroke, fill = "#F59E0B", type_fill
        return (
            f' bioc:stroke="{stroke}" bioc:fill="{fill}"'
            f' color:background-color="{fill}" color:border-color="{stroke}"'
        )
    # HIGH confidence, use type-based coloring
    return _color_attrs_for_step_type(stype)


def _sanitise_id(text: str) -> str:
    """BPMN IDs must be XML names, letters, digits, underscores; cannot start with digit."""
    cleaned = re.sub(r'[^A-Za-z0-9_]', '_', text)
    if cleaned and cleaned[0].isdigit():
        cleaned = '_' + cleaned
    return cleaned or 'Anon'


# ===========================================================================
# 3.  HTML, per-process viewer page
# ===========================================================================

PROCESS_PAGE_CSS = """
:root { --bg:#f7f8fa; --surface:#fff; --border:#e3e7ed; --text:#1a1f29; --muted:#6b7280; --accent:#1f6feb; --pain:#c62828; --opp:#2e7d32; --auto:#1565c0; --warn:#92400e; }
* { box-sizing: border-box; }
html, body { margin:0; padding:0; height:100%; font-family:-apple-system,BlinkMacSystemFont,"Inter","Segoe UI",Roboto,sans-serif; color:var(--text); background:var(--bg); }
body { display:flex; flex-direction:column; }
.topbar { display:flex; align-items:center; justify-content:space-between; padding:14px 22px; background:var(--surface); border-bottom:1px solid var(--border); }
.breadcrumb { font-size:13px; color:var(--muted); }
.breadcrumb a { color:var(--muted); text-decoration:none; }
.breadcrumb a:hover { color:var(--accent); }
.breadcrumb .sep { margin:0 6px; color:#d1d5db; }
.breadcrumb .current { color:var(--text); font-weight:500; }
.topbar-actions { display:flex; gap:10px; align-items:center; }
.version-pill { background:#e8f5e9; color:#2e7d32; font-size:11px; font-weight:600; padding:3px 8px; border-radius:999px; letter-spacing:.4px; }
.btn { font-size:13px; padding:7px 13px; border-radius:6px; border:1px solid var(--border); background:var(--surface); color:var(--text); cursor:pointer; text-decoration:none; display:inline-flex; align-items:center; gap:6px; font-weight:500; }
.btn:hover { border-color:#c1c8d3; }
.title-strip { padding:18px 22px 12px; background:var(--surface); border-bottom:1px solid var(--border); }
.title-strip h1 { margin:0 0 4px; font-size:20px; font-weight:600; }
.title-strip .subtitle { font-size:13px; color:var(--muted); }

/* Lane chips: tools-as-lanes model, system/external/offline. */
.lane-chips { margin-top:10px; display:flex; flex-wrap:wrap; gap:6px; }
.lane-chip { font-size:11px; padding:3px 9px; border-radius:999px; border:1px solid var(--border); background:#fafbfc; color:#4b5563; font-weight:500; display:inline-flex; align-items:center; gap:5px; }
.lane-chip .glyph { font-size:9.5px; opacity:.7; }
.lane-chip.system { background:#fef3c7; border-color:#fde68a; color:#92400e; }
.lane-chip.external { background:#f3f4f6; border-color:#d1d5db; color:#4b5563; }
.lane-chip.offline { background:#e0e7ff; border-color:#c7d2fe; color:#3730a3; }
/* Legacy: role lanes are deprecated. Render with a warning halo so they're
   visible during the rollout but obviously wrong. */
.lane-chip.role { background:#fef2f2; border-color:#fecaca; color:#991b1b; text-decoration:line-through dotted; }

.main { flex:1; display:grid; grid-template-columns:1fr 360px; min-height:0; }
.canvas-wrap { position:relative; background:var(--surface); margin:14px 0 14px 14px; border:1px solid var(--border); border-radius:8px; overflow:hidden; }
#canvas { width:100%; height:100%; }
.sidebar { padding:14px 18px 14px 14px; overflow-y:auto; }
.panel { background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:14px 16px; margin-bottom:12px; }
.panel h3 { margin:0 0 10px; font-size:12px; text-transform:uppercase; letter-spacing:.6px; color:var(--muted); font-weight:600; }
.panel .field { display:flex; justify-content:space-between; padding:4px 0; font-size:13px; }
.panel .field .label { color:var(--muted); }
.panel .field .value { font-weight:500; }
.source-item { font-size:12.5px; padding:8px 0; border-top:1px solid #f3f4f6; }
.source-item:first-child { border-top:0; }
.source-item .title { font-weight:500; margin-bottom:2px; }
.source-item .meta { color:var(--muted); font-size:11.5px; }
.source-item a { color:var(--accent); text-decoration:none; font-size:11.5px; }
.pain-row { display:flex; align-items:center; gap:8px; font-size:12.5px; padding:6px 0; border-top:1px solid #f3f4f6; }
.pain-row:first-of-type { border-top:0; }
.pain-dot { width:8px; height:8px; border-radius:50%; background:var(--pain); flex-shrink:0; }
.pain-row .text { flex:1; }

/* Citation pill (transcript source), bottom-right of task. */
.citation-overlay { position:relative; }
.citation-pill { background:#fff; border:1px solid var(--border); border-radius:12px; padding:3px 9px; font-size:10.5px; color:var(--muted); cursor:pointer; box-shadow:0 1px 2px rgba(0,0,0,.06); font-weight:500; line-height:1.4; user-select:none; transition:border-color 120ms; white-space:nowrap; }
.citation-pill:hover { border-color:var(--accent); color:var(--accent); }
.citation-pill .icon { margin-right:3px; }
.citation-popup { display:none; position:absolute; top:100%; left:0; margin-top:4px; background:#fff; border:1px solid var(--border); border-radius:8px; box-shadow:0 4px 16px rgba(0,0,0,.10); padding:12px 14px; width:320px; font-size:12px; line-height:1.55; z-index:50; }
.citation-popup.open { display:block; }
.citation-popup .speaker { font-weight:600; color:var(--text); margin-bottom:4px; }
.citation-popup .quote { color:#374151; font-style:italic; margin-bottom:8px; }
.citation-popup .fathom-link { font-size:11.5px; color:var(--accent); text-decoration:none; }
.pain-indicator { background:var(--pain); color:#fff; font-size:9.5px; font-weight:700; padding:2px 7px; border-radius:999px; letter-spacing:.4px; box-shadow:0 1px 3px rgba(198,40,40,.35); white-space:nowrap; }

/* Performer overlays, left-edge stripe + initials chip top-left. */
.performer-stripe { width:4px; height:80px; border-radius:2px 0 0 2px; box-shadow:inset 0 0 0 1px rgba(0,0,0,.04); }
.performer-chip { width:22px; height:22px; border-radius:50%; color:#fff; font-size:9.5px; font-weight:700; letter-spacing:.4px; display:flex; align-items:center; justify-content:center; box-shadow:0 1px 3px rgba(0,0,0,.18); cursor:default; user-select:none; }
.performer-chip.auto { background:#475569; }
.performer-chip.auto::before { content:"\\2699"; font-size:13px; font-weight:400; }
.performer-chip.auto .initials { display:none; }

/* Duration badge, bottom-left of task. */
.duration-badge { background:#f3f4f6; border:1px solid #e5e7eb; color:#4b5563; font-size:10.5px; font-weight:500; padding:2px 7px; border-radius:6px; box-shadow:0 1px 2px rgba(0,0,0,.04); white-space:nowrap; }

/* Legend panel, right-rail reference shown on every process page. */
.legend-section { padding:8px 0; border-top:1px solid #f3f4f6; }
.legend-section:first-of-type { border-top:0; padding-top:0; }
.legend-section h4 { margin:0 0 8px; font-size:11px; font-weight:600; color:var(--muted); text-transform:uppercase; letter-spacing:.5px; }
.legend-row { display:flex; align-items:center; gap:8px; padding:3px 0; font-size:12.5px; line-height:1.35; }
.legend-row .meta { margin-left:auto; color:var(--muted); font-size:11px; }
.legend-swatch { width:14px; height:14px; border-radius:4px; flex-shrink:0; }
.legend-swatch.stripe { width:4px; height:18px; border-radius:2px; }
.legend-mini-chip { width:18px; height:18px; border-radius:50%; color:#fff; font-size:8.5px; font-weight:700; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.legend-mini-chip.auto::before { content:"\\2699"; font-size:11px; font-weight:400; }
.legend-icon { width:16px; text-align:center; color:var(--muted); font-size:13px; }
.legend-icon.system { color:#92400e; }
.legend-icon.external { color:#4b5563; }
.legend-icon.offline { color:#3730a3; }
.notation-block { display:flex; flex-wrap:wrap; gap:6px; }
.notation-pill { font-size:10.5px; padding:2px 7px; border-radius:999px; border:1px solid var(--border); background:#fff; color:var(--muted); }
.notation-pill.pain { border-color:#fecaca; color:var(--pain); background:#fef2f2; }
.notation-pill.opp { border-color:#bbf7d0; color:var(--opp); background:#f0fdf4; }
.notation-pill.auto { border-color:#bfdbfe; color:var(--auto); background:#eff6ff; }

/* Time rollup panel, per-performer and per-tool totals. */
.rollup-row { display:flex; align-items:center; gap:8px; padding:5px 0; border-top:1px solid #f3f4f6; font-size:12.5px; }
.rollup-row:first-of-type { border-top:0; }
.rollup-row .label { flex:1; }
.rollup-row .meta { color:var(--muted); font-size:11.5px; }

.djs-label { font-family:-apple-system,BlinkMacSystemFont,"Inter","Segoe UI",Roboto,sans-serif !important; }
"""


LANE_TYPE_GLYPH = {
    "system":   "&#x2699;",   # gear
    "external": "&#x2197;",   # north-east arrow (data leaves the company)
    "offline":  "&#x270E;",   # pencil (paper / verbal / off-system)
    "role":     "&#x26A0;",   # warning (deprecated)
}


def build_process_page_html(process: dict[str, Any], bpmn_filename: str,
                            client_meta: dict[str, Any] | None = None,
                            index_href: str = "../../2-process-map.html",
                            palette: dict[str, dict[str, str]] | None = None,
                            bpmn_xml: str | None = None) -> str:
    """Render the per-process HTML page (bpmn-js viewer + sidebar + legend + rollups).

    ``palette`` should be the client-wide performer palette built once by the
    orchestrator so colours stay consistent across all process pages. When
    ``None`` (e.g. standalone calls) a per-process palette is built.
    """
    stage_label = (process.get("stage") or "process").title()
    name = process.get("name", "Process")
    confidence = (process.get("confidence") or "MEDIUM").upper()
    step_count = len(process.get("steps", []))

    if palette is None:
        palette = build_performer_palette({"processes": [process]})

    # Lane chips (with type glyph)
    lane_chips: list[str] = []
    for lane in sorted(process.get("lanes", []), key=lambda l: l.get("order", 0)):
        cls = lane.get("type", "system")
        glyph = LANE_TYPE_GLYPH.get(cls, "")
        lane_chips.append(
            f'<span class="lane-chip {html.escape(cls)}">'
            f'<span class="glyph">{glyph}</span>{html.escape(lane.get("name", lane["id"]))}</span>'
        )

    # Build per-step overlay data (citations, performer, duration, pain)
    citations: dict[str, dict[str, str]] = {}
    performers_js: dict[str, dict[str, str]] = {}
    durations_js: dict[str, str] = {}
    pain_steps: list[dict[str, str]] = []
    performer_step_counts: dict[str, int] = defaultdict(int)
    for s in process.get("steps", []):
        nid = s.get("bpmn_id") or s.get("step_id")
        if not nid:
            continue
        refs = s.get("meeting_references", []) or []
        if refs:
            first = refs[0]
            citations[nid] = {
                "speaker": first.get("speaker", s.get("speaker", "")),
                "meeting": first.get("meeting_title", "Source meeting"),
                "quote": first.get("quote", s.get("source_quote", "")),
                "url": _fathom_url(first),
            }
            if s.get("type") == "pain":
                citations[nid]["pain"] = "Pain point"
        if s.get("type") == "pain":
            pain_steps.append({"title": s.get("title", ""), "id": nid})

        # Skip non-task BPMN nodes for performer/duration overlays
        if s.get("type") in ("start", "end", "decision"):
            continue

        owner = (s.get("owner") or "").strip()
        if owner and owner in palette:
            p = palette[owner]
            performers_js[nid] = {
                "owner": owner, "initials": p["initials"],
                "hex": p["hex"], "kind": p["kind"],
            }
            performer_step_counts[owner] += 1

        dur = format_duration_for_step(s)
        if dur:
            durations_js[nid] = dur

    pain_rows = ''.join(
        f'<div class="pain-row"><div class="pain-dot"></div><div class="text"><strong>{html.escape(p["title"])}</strong></div></div>'
        for p in pain_steps
    ) or '<div class="pain-row" style="border-top:0;"><div class="text" style="color:var(--muted);">No pain points flagged.</div></div>'

    sources_html = _source_meetings_html(process)

    called_from = process.get("called_from") or []
    calls = process.get("calls") or []
    called_from_str = ', '.join(html.escape(c) for c in called_from) or '-'
    calls_str = ', '.join(html.escape(c) for c in calls) or '-'

    client_name = (client_meta or {}).get("name", "")
    client_str = html.escape(client_name) if client_name else "APG audit"

    legend_html = _render_legend_panel_html(process, palette, performer_step_counts)
    rollup_html = _render_time_rollup_html(process, palette)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{html.escape(name)} &middot; {client_str}</title>
<link rel="stylesheet" href="https://unpkg.com/bpmn-js@18/dist/assets/diagram-js.css" />
<link rel="stylesheet" href="https://unpkg.com/bpmn-js@18/dist/assets/bpmn-font/css/bpmn.css" />
<link rel="stylesheet" href="https://unpkg.com/bpmn-js@18/dist/assets/bpmn-js.css" />
<style>{PROCESS_PAGE_CSS}</style>
</head>
<body>
<div class="topbar">
  <div class="breadcrumb">
    <a href="{index_href}">Process landscape</a><span class="sep">/</span>
    <a href="{index_href}#stage-{html.escape(process.get("stage", ""))}">{html.escape(stage_label)}</a><span class="sep">/</span>
    <span class="current">{html.escape(name)}</span>
  </div>
  <div class="topbar-actions">
    <span class="version-pill">V{html.escape(str(process.get("version", "1.0")))} &middot; CURRENT STATE</span>
    <a class="btn" href="{html.escape(bpmn_filename)}" download>&darr; Download .bpmn</a>
    <button class="btn" onclick="bpmnViewer.get('canvas').zoom('fit-viewport')">Fit to screen</button>
  </div>
</div>

<div class="title-strip">
  <h1>{html.escape(name)}</h1>
  <div class="subtitle">{step_count} steps &middot; {html.escape(confidence)} confidence</div>
  <div class="lane-chips">{''.join(lane_chips)}</div>
</div>

<div class="main">
  <div class="canvas-wrap"><div id="canvas"></div></div>
  <div class="sidebar">
    <div class="panel">
      <h3>Process</h3>
      <div class="field"><span class="label">Stage</span><span class="value">{html.escape(stage_label)}</span></div>
      <div class="field"><span class="label">Process owner</span><span class="value">{html.escape(process.get("owner") or "-")}</span></div>
      <div class="field"><span class="label">Confidence</span><span class="value">{html.escape(confidence)}</span></div>
      <div class="field"><span class="label">Steps</span><span class="value">{step_count}</span></div>
    </div>

    {rollup_html}

    <div class="panel">
      <h3>Legend</h3>
      {legend_html}
    </div>

    <div class="panel">
      <h3>Pain points on this process</h3>
      {pain_rows}
    </div>

    {sources_html}

    <div class="panel">
      <h3>Called from / Calls</h3>
      <div class="field"><span class="label">Called from</span><span class="value">{called_from_str}</span></div>
      <div class="field"><span class="label">Calls</span><span class="value">{calls_str}</span></div>
    </div>
  </div>
</div>

<script src="https://unpkg.com/bpmn-js@18/dist/bpmn-viewer.production.min.js"></script>
<script>
const bpmnViewer = new BpmnJS({{ container: '#canvas' }});
const citations = {json.dumps(citations)};
const performers = {json.dumps(performers_js)};
const durations  = {json.dumps(durations_js)};

const BPMN_XML_INLINE = {json.dumps(bpmn_xml) if bpmn_xml else 'null'};

async function load() {{
  let xml;
  if (BPMN_XML_INLINE) {{
    xml = BPMN_XML_INLINE;
  }} else {{
    const res = await fetch({json.dumps(bpmn_filename)});
    xml = await res.text();
  }}
  await bpmnViewer.importXML(xml);
  bpmnViewer.get('canvas').zoom('fit-viewport');
  attachOverlays();
}}

function escapeHtml(s) {{
  return (s || '').replace(/[<>&"']/g, c => ({{'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;',"'":'&#39;'}}[c]));
}}

function attachOverlays() {{
  const overlays = bpmnViewer.get('overlays');

  // 1. Citation pill (bottom-right)
  Object.entries(citations).forEach(([elementId, data]) => {{
    const wrap = document.createElement('div');
    wrap.className = 'citation-overlay';
    wrap.innerHTML = `
      <div class="citation-pill" data-target="popup-${{elementId}}">
        <span class="icon">&#9656;</span> source
      </div>
      <div class="citation-popup" id="popup-${{elementId}}">
        <div class="speaker">${{escapeHtml(data.speaker)}} &middot; ${{escapeHtml(data.meeting)}}</div>
        <div class="quote">${{escapeHtml(data.quote)}}</div>
        ${{data.url ? `<a class="fathom-link" href="${{data.url}}" target="_blank" rel="noopener">Open at timestamp &rarr;</a>` : ''}}
      </div>
    `;
    const pill = wrap.querySelector('.citation-pill');
    const popup = wrap.querySelector('.citation-popup');
    pill.addEventListener('click', e => {{
      e.stopPropagation();
      document.querySelectorAll('.citation-popup.open').forEach(p => {{ if (p !== popup) p.classList.remove('open'); }});
      popup.classList.toggle('open');
    }});
    try {{ overlays.add(elementId, 'citation', {{ position: {{ bottom: 4, right: 4 }}, html: wrap }}); }} catch (e) {{ console.warn('citation overlay failed for', elementId, e.message); }}

    if (data.pain) {{
      const painEl = document.createElement('div');
      painEl.className = 'pain-indicator';
      painEl.textContent = data.pain;
      try {{ overlays.add(elementId, 'pain', {{ position: {{ top: -10, right: -10 }}, html: painEl }}); }} catch (e) {{}}
    }}
  }});

  // 2. Performer overlays: left-edge stripe + top-left initials chip
  Object.entries(performers).forEach(([elementId, perf]) => {{
    const isAuto = perf.kind === 'automation';
    if (!isAuto) {{
      const stripe = document.createElement('div');
      stripe.className = 'performer-stripe';
      stripe.style.background = perf.hex;
      try {{ overlays.add(elementId, 'performer-stripe', {{ position: {{ top: 0, left: 0 }}, html: stripe }}); }} catch (e) {{}}
    }}
    const chip = document.createElement('div');
    chip.className = 'performer-chip' + (isAuto ? ' auto' : '');
    chip.style.background = perf.hex;
    chip.title = (perf.owner || '') + (perf.kind === 'role' ? ' (role)' : perf.kind === 'external' ? ' (external)' : ' (automation)');
    if (!isAuto) {{
      const initialsSpan = document.createElement('span');
      initialsSpan.className = 'initials';
      initialsSpan.textContent = perf.initials;
      chip.appendChild(initialsSpan);
    }}
    try {{ overlays.add(elementId, 'performer-chip', {{ position: {{ top: -8, left: -10 }}, html: chip }}); }} catch (e) {{}}
  }});

  // 3. Duration badges: bottom-left
  Object.entries(durations).forEach(([elementId, text]) => {{
    const badge = document.createElement('div');
    badge.className = 'duration-badge';
    badge.textContent = text;
    try {{ overlays.add(elementId, 'duration', {{ position: {{ bottom: -10, left: 4 }}, html: badge }}); }} catch (e) {{}}
  }});

  document.addEventListener('click', () => {{
    document.querySelectorAll('.citation-popup.open').forEach(p => p.classList.remove('open'));
  }});
}}

load().catch(err => {{
  console.error(err);
  document.getElementById('canvas').innerHTML = '<div style="padding:40px;color:#c62828;font-family:monospace;">Failed to load BPMN. Serve this page via HTTP (not file://).</div>';
}});
</script>
</body></html>
"""


def _render_legend_panel_html(process: dict[str, Any],
                              palette: dict[str, dict[str, str]],
                              step_counts: dict[str, int]) -> str:
    """Three-section legend: tools (lanes), performers, notation."""
    # Tools / lanes
    lane_counts: dict[str, int] = defaultdict(int)
    for s in process.get("steps", []):
        lid = s.get("lane_id")
        if lid:
            lane_counts[lid] += 1
    lane_rows = []
    for lane in sorted(process.get("lanes", []), key=lambda l: l.get("order", 0)):
        ltype = lane.get("type", "system")
        glyph = LANE_TYPE_GLYPH.get(ltype, "")
        n = lane_counts.get(lane["id"], 0)
        lane_rows.append(
            f'<div class="legend-row">'
            f'<span class="legend-icon {html.escape(ltype)}">{glyph}</span>'
            f'<span>{html.escape(lane.get("name", lane["id"]))}</span>'
            f'<span class="meta">{n} step{"s" if n != 1 else ""}</span>'
            f'</div>'
        )
    lane_block = (
        '<div class="legend-section"><h4>Tools (lanes)</h4>' + ''.join(lane_rows) + '</div>'
        if lane_rows else ''
    )

    # Performers, only those actually present in this process
    used_owners = set(step_counts.keys())
    perf_rows = []
    for owner in sorted(used_owners):
        p = palette.get(owner) or {"hex": "#9ca3af", "initials": "?", "kind": "unknown"}
        is_auto = p["kind"] == "automation"
        chip_class = 'legend-mini-chip' + (' auto' if is_auto else '')
        chip_inner = '' if is_auto else html.escape(p["initials"])
        n = step_counts[owner]
        perf_rows.append(
            f'<div class="legend-row">'
            f'<span class="{chip_class}" style="background:{html.escape(p["hex"])}">{chip_inner}</span>'
            f'<span>{html.escape(owner)}</span>'
            f'<span class="meta">{n} step{"s" if n != 1 else ""}</span>'
            f'</div>'
        )
    perf_block = (
        '<div class="legend-section"><h4>Performers (colour code)</h4>' + ''.join(perf_rows) + '</div>'
        if perf_rows else ''
    )

    # Notation, fixed reference
    notation_block = '''
<div class="legend-section">
  <h4>Notation</h4>
  <div class="notation-block">
    <span class="notation-pill pain">Pain point</span>
    <span class="notation-pill opp">Optimisation</span>
    <span class="notation-pill auto">Automation</span>
  </div>
  <div class="legend-row" style="margin-top:8px;font-size:11.5px;color:var(--muted);">
    <span>Pills on tasks: initials = performer, time = duration, &#9656; source = transcript.</span>
  </div>
</div>'''

    return lane_block + perf_block + notation_block


def _render_time_rollup_html(process: dict[str, Any],
                             palette: dict[str, dict[str, str]]) -> str:
    """Per-performer and per-tool weekly time totals for this process."""
    per_performer_hrs: dict[str, float] = defaultdict(float)
    per_performer_count: dict[str, int] = defaultdict(int)
    per_tool_hrs: dict[str, float] = defaultdict(float)
    per_tool_count: dict[str, int] = defaultdict(int)

    lane_name_by_id = {l["id"]: l.get("name", l["id"]) for l in process.get("lanes", [])}
    lane_type_by_id = {l["id"]: l.get("type", "system") for l in process.get("lanes", [])}

    for s in process.get("steps", []):
        if s.get("type") in ("start", "end", "decision"):
            continue
        owner = (s.get("owner") or "").strip()
        weekly = s.get("time_estimate_hours_per_week")
        # Per-instance is not weekly, only count weekly here so totals are comparable
        if isinstance(weekly, (int, float)) and weekly > 0:
            if owner:
                per_performer_hrs[owner] += weekly
                per_performer_count[owner] += 1
            lid = s.get("lane_id")
            if lid:
                per_tool_hrs[lid] += weekly
                per_tool_count[lid] += 1

    if not per_performer_hrs and not per_tool_hrs:
        return ''

    def _fmt(h: float) -> str:
        if h < 1: return f"{int(round(h * 60))} min/wk"
        if h == int(h): return f"{int(h)} hrs/wk"
        return f"{h:.1f} hrs/wk"

    perf_rows = []
    for owner in sorted(per_performer_hrs, key=lambda o: -per_performer_hrs[o]):
        n = per_performer_count[owner]
        hrs = _fmt(per_performer_hrs[owner])
        perf_rows.append(
            f'<div class="rollup-row"><span class="label">{html.escape(owner)}</span>'
            f'<span class="meta">{hrs} &middot; {n} step{"s" if n != 1 else ""}</span></div>'
        )
    tool_rows = []
    for lid in sorted(per_tool_hrs, key=lambda l: -per_tool_hrs[l]):
        name = lane_name_by_id.get(lid, lid)
        ltype = lane_type_by_id.get(lid, "system")
        glyph = LANE_TYPE_GLYPH.get(ltype, "")
        n = per_tool_count[lid]
        hrs = _fmt(per_tool_hrs[lid])
        tool_rows.append(
            f'<div class="rollup-row"><span class="label">'
            f'<span class="legend-icon {html.escape(ltype)}">{glyph}</span> {html.escape(name)}'
            f'</span><span class="meta">{hrs} &middot; {n} step{"s" if n != 1 else ""}</span></div>'
        )

    perf_block = (
        '<h4 style="margin:0 0 6px;font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;">By performer</h4>'
        + ''.join(perf_rows)
    ) if perf_rows else ''
    tool_block = (
        '<h4 style="margin:14px 0 6px;font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;">By tool</h4>'
        + ''.join(tool_rows)
    ) if tool_rows else ''

    return f'<div class="panel"><h3>Time on this process (weekly)</h3>{perf_block}{tool_block}</div>'


def _fathom_url(ref: dict[str, Any]) -> str:
    url = ref.get("fathom_url") or ref.get("url")
    if url:
        return html.escape(url)
    call_id = ref.get("meeting_id") or ref.get("call_id")
    ts = ref.get("timestamp_seconds") or ref.get("timestamp")
    if call_id:
        return html.escape(f"https://fathom.video/calls/{call_id}?t={ts or 0}")
    return ""


def _source_meetings_html(process: dict[str, Any]) -> str:
    """Aggregate distinct source meetings across all steps."""
    meetings: dict[str, dict[str, Any]] = {}
    for s in process.get("steps", []):
        for ref in s.get("meeting_references", []) or []:
            mid = ref.get("meeting_id") or ref.get("call_id") or ref.get("meeting_title", "")
            if not mid:
                continue
            if mid not in meetings:
                meetings[mid] = {
                    "title": ref.get("meeting_title", "Source meeting"),
                    "date": ref.get("meeting_date", ""),
                    "url": _fathom_url(ref),
                    "count": 0,
                }
            meetings[mid]["count"] += 1
    if not meetings:
        return ''
    items = []
    for m in meetings.values():
        link = f'<a href="{m["url"]}" target="_blank" rel="noopener">Open in Fathom &rarr;</a>' if m["url"] else ''
        items.append(
            f'<div class="source-item">'
            f'<div class="title">{html.escape(m["title"])}</div>'
            f'<div class="meta">{html.escape(m["date"])} &middot; {m["count"]} reference{"s" if m["count"]!=1 else ""}</div>'
            f'{link}</div>'
        )
    return f'<div class="panel"><h3>Source meetings</h3>{"".join(items)}</div>'


# ===========================================================================
# 4.  HTML, landscape index (folder/card hub)
# ===========================================================================

INDEX_CSS = """
:root { --bg:#f7f8fa; --surface:#fff; --border:#e3e7ed; --text:#1a1f29; --muted:#6b7280; --accent:#1f6feb; --pain:#c62828; --opp:#2e7d32; }
* { box-sizing: border-box; }
html, body { margin:0; padding:0; font-family:-apple-system,BlinkMacSystemFont,"Inter","Segoe UI",Roboto,sans-serif; color:var(--text); background:var(--bg); }
.topbar { display:flex; align-items:center; justify-content:space-between; padding:14px 22px; background:var(--surface); border-bottom:1px solid var(--border); }
.topbar .brand { font-weight:600; font-size:14px; }
.topbar .brand .muted { color:var(--muted); font-weight:400; }
.version-pill { background:#e8f5e9; color:#2e7d32; font-size:11px; font-weight:600; padding:3px 8px; border-radius:999px; letter-spacing:.4px; }
.header { padding:36px 22px 24px; max-width:1280px; margin:0 auto; }
.header h1 { margin:0 0 6px; font-size:28px; font-weight:600; letter-spacing:-.3px; }
.header .subtitle { font-size:14px; color:var(--muted); }
.header .quick-stats { margin-top:18px; display:flex; gap:24px; flex-wrap:wrap; }
.stat { background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:12px 18px; min-width:140px; }
.stat .num { font-size:22px; font-weight:600; letter-spacing:-.5px; }
.stat .num.pain { color:var(--pain); }
.stat .num.opp { color:var(--opp); }
.stat .label { font-size:11.5px; color:var(--muted); text-transform:uppercase; letter-spacing:.5px; margin-top:2px; }
.stages { max-width:1280px; margin:0 auto; padding:8px 22px 64px; }
.stage { margin-bottom:36px; scroll-margin-top:20px; }
.stage-header { display:flex; align-items:baseline; gap:12px; margin-bottom:14px; padding:0 4px; }
.stage-header h2 { margin:0; font-size:16px; font-weight:600; text-transform:uppercase; letter-spacing:.7px; color:var(--text); }
.stage-header .count { font-size:12px; color:var(--muted); font-weight:500; }
.stage-header .stage-icon { width:8px; height:8px; border-radius:50%; background:var(--accent); display:inline-block; margin-right:2px; }
.stage-header.s1 .stage-icon { background:#1f6feb; }
.stage-header.s2 .stage-icon { background:#8b5cf6; }
.stage-header.s3 .stage-icon { background:#10b981; }
.stage-header.s4 .stage-icon { background:#f59e0b; }
.stage-header.s5 .stage-icon { background:#ec4899; }
.card-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:12px; }
.card { background:var(--surface); border:1px solid var(--border); border-radius:10px; padding:16px 18px 14px; text-decoration:none; color:var(--text); transition:border-color 120ms,transform 120ms,box-shadow 120ms; display:flex; flex-direction:column; min-height:168px; }
.card:hover { border-color:var(--accent); transform:translateY(-1px); box-shadow:0 4px 14px rgba(31,111,235,.08); }
.card .card-icon { font-size:18px; color:var(--accent); margin-bottom:6px; opacity:.8; }
.card h3 { margin:0 0 4px; font-size:15px; font-weight:600; line-height:1.3; }
.card .card-sub { font-size:12.5px; color:var(--muted); margin-bottom:10px; line-height:1.45; }
.lane-chips { display:flex; flex-wrap:wrap; gap:4px; margin-bottom:10px; }
.lane-chip { font-size:10.5px; padding:2px 7px; border-radius:999px; border:1px solid var(--border); background:#fafbfc; color:#4b5563; font-weight:500; }
.lane-chip.system { background:#fef3c7; border-color:#fde68a; color:#92400e; }
.lane-chip.external { background:#f3f4f6; border-color:#d1d5db; color:#4b5563; }
.lane-chip.offline { background:#e0e7ff; border-color:#c7d2fe; color:#3730a3; }
.lane-chip.role { background:#fef2f2; border-color:#fecaca; color:#991b1b; text-decoration:line-through dotted; }

/* Condensed legend strip on the index. */
.condensed-legend { max-width:1280px; margin:18px auto 0; padding:0 22px; display:flex; gap:24px; flex-wrap:wrap; align-items:center; font-size:11.5px; color:var(--muted); }
.condensed-legend .group { display:flex; gap:8px; flex-wrap:wrap; align-items:center; padding:6px 12px; background:var(--surface); border:1px solid var(--border); border-radius:8px; }
.condensed-legend .group-label { font-weight:600; color:var(--text); margin-right:6px; text-transform:uppercase; font-size:10.5px; letter-spacing:.5px; }
.condensed-legend .mini-chip { width:18px; height:18px; border-radius:50%; color:#fff; font-size:8.5px; font-weight:700; display:flex; align-items:center; justify-content:center; }
.condensed-legend .mini-chip.auto::before { content:"\\2699"; font-size:11px; font-weight:400; }
.condensed-legend .pill { font-size:10.5px; padding:2px 7px; border-radius:999px; border:1px solid var(--border); background:#fff; }
.condensed-legend .pill.pain { border-color:#fecaca; color:var(--pain); background:#fef2f2; }
.condensed-legend .pill.opp { border-color:#bbf7d0; color:var(--opp); background:#f0fdf4; }
.condensed-legend .pill.auto { border-color:#bfdbfe; color:#1565c0; background:#eff6ff; }
.condensed-legend .pf-row { display:flex; align-items:center; gap:6px; }

.card .card-foot { margin-top:auto; display:flex; align-items:center; justify-content:space-between; padding-top:10px; border-top:1px solid #f3f4f6; font-size:11.5px; color:var(--muted); }
.card .pain-flag { color:var(--pain); font-weight:600; }
.card .pain-flag .dot { display:inline-block; width:6px; height:6px; border-radius:50%; background:var(--pain); margin-right:4px; vertical-align:middle; }
.card .confidence.high { color:var(--opp); font-weight:500; }
.card .confidence.medium { color:#f59e0b; font-weight:500; }
.card .confidence.low { color:var(--pain); font-weight:500; }
.stage-empty { background:var(--surface); border:1px dashed var(--border); border-radius:10px; padding:22px; color:var(--muted); font-size:13px; text-align:center; }
"""


STAGE_ORDER = ["acquisition", "quoting", "onboarding", "fulfilment", "retention"]


def build_index_html(processes: list[dict[str, Any]],
                     client_meta: dict[str, Any] | None = None,
                     palette: dict[str, dict[str, str]] | None = None) -> str:
    """Render the landscape index page with condensed legend."""
    client_name = (client_meta or {}).get("name", "APG audit")
    audit_version = (client_meta or {}).get("audit_version", "1.0")
    if palette is None:
        palette = build_performer_palette({"processes": processes})

    # Group by stage; preserve canonical order then append any unknown stages
    by_stage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for p in processes:
        by_stage[p.get("stage", "other")].append(p)
    ordered_stages: list[str] = [s for s in STAGE_ORDER if s in by_stage]
    for s in by_stage:
        if s not in ordered_stages:
            ordered_stages.append(s)

    # Quick stats
    total_processes = sum(len(v) for v in by_stage.values())
    total_steps = sum(len(p.get("steps", [])) for p in processes)
    total_pain = sum(1 for p in processes for s in p.get("steps", []) if s.get("type") == "pain")
    total_opp = sum(1 for p in processes for s in p.get("steps", []) if s.get("type") in ("optimisation", "automation"))

    # Condensed legend strip, performers and notation only (lanes vary per process)
    used_owners: dict[str, int] = defaultdict(int)
    for p in processes:
        for s in p.get("steps", []):
            if s.get("type") in ("start", "end", "decision"):
                continue
            owner = (s.get("owner") or "").strip()
            if owner:
                used_owners[owner] += 1

    perf_chips: list[str] = []
    for owner in sorted(used_owners.keys()):
        info = palette.get(owner) or {"hex": "#9ca3af", "initials": "?", "kind": "unknown"}
        is_auto = info["kind"] == "automation"
        chip_inner = '' if is_auto else html.escape(info["initials"])
        chip_class = "mini-chip" + (" auto" if is_auto else "")
        perf_chips.append(
            f'<div class="pf-row" title="{html.escape(owner)} &middot; {used_owners[owner]} steps">'
            f'<span class="{chip_class}" style="background:{html.escape(info["hex"])}">{chip_inner}</span>'
            f'<span>{html.escape(owner)}</span></div>'
        )
    condensed_legend_html = ''
    if perf_chips:
        condensed_legend_html = (
            '<div class="condensed-legend">'
            '<div class="group"><span class="group-label">Performers</span>'
            + ''.join(perf_chips) + '</div>'
            '<div class="group"><span class="group-label">Notation</span>'
            '<span class="pill pain">Pain</span>'
            '<span class="pill opp">Optimisation</span>'
            '<span class="pill auto">Automation</span></div>'
            '</div>'
        )

    # Stage sections
    stage_html_parts: list[str] = []
    for i, stage in enumerate(ordered_stages, start=1):
        stage_class = f"s{i}" if i <= 5 else "s5"
        cards = [_render_process_card(p) for p in by_stage[stage]]
        stage_label = stage.title()
        plural = "es" if len(by_stage[stage]) != 1 else ""
        stage_html_parts.append(f"""
<div class="stage" id="stage-{html.escape(stage)}">
  <div class="stage-header {stage_class}">
    <span class="stage-icon"></span>
    <h2>{html.escape(stage_label)}</h2>
    <span class="count">{len(by_stage[stage])} process{plural}</span>
  </div>
  <div class="card-grid">{''.join(cards)}</div>
</div>""")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Process landscape &middot; {html.escape(client_name)}</title>
<style>{INDEX_CSS}</style>
</head>
<body>

<div class="topbar">
  <div class="brand">{html.escape(client_name)} <span class="muted">&middot; Current-state audit</span></div>
  <div><span class="version-pill">V{html.escape(str(audit_version))} &middot; CURRENT STATE</span></div>
</div>

<div class="header">
  <h1>Process landscape</h1>
  <div class="subtitle">Every process we captured in your business, grouped by stage. Click any process to see its BPMN diagram.</div>
  <div class="quick-stats">
    <div class="stat"><div class="num">{total_processes}</div><div class="label">Processes</div></div>
    <div class="stat"><div class="num">{total_steps}</div><div class="label">Steps captured</div></div>
    <div class="stat"><div class="num pain">{total_pain}</div><div class="label">Pain points</div></div>
    <div class="stat"><div class="num opp">{total_opp}</div><div class="label">Opportunities</div></div>
  </div>
</div>

{condensed_legend_html}

<div class="stages">
{''.join(stage_html_parts)}
</div>

</body></html>
"""


def _render_process_card(process: dict[str, Any]) -> str:
    name = process.get("name", "Process")
    desc = process.get("description", "")
    stage = process.get("stage", "process")
    slug = _slugify(process.get("process_id") or name)
    href = f"processes/{html.escape(stage)}/{html.escape(slug)}.html"
    confidence = (process.get("confidence") or "MEDIUM").upper()
    pain_count = sum(1 for s in process.get("steps", []) if s.get("type") == "pain")
    lanes = sorted(process.get("lanes", []), key=lambda l: l.get("order", 0))[:5]
    lane_chips = ''.join(
        f'<span class="lane-chip {html.escape(l.get("type", "system"))}">{html.escape(l.get("name", l["id"]))}</span>'
        for l in lanes
    )
    pain_text = (
        f'<span class="pain-flag"><span class="dot"></span>{pain_count} pain point{"s" if pain_count!=1 else ""}</span>'
        if pain_count > 0
        else '<span></span>'
    )
    return f"""<a class="card" href="{href}">
  <div class="card-icon">&#9636;</div>
  <h3>{html.escape(name)}</h3>
  <div class="card-sub">{html.escape(desc)}</div>
  <div class="lane-chips">{lane_chips}</div>
  <div class="card-foot">{pain_text}<span class="confidence {confidence.lower()}">{html.escape(confidence)}</span></div>
</a>"""


def _slugify(text: str) -> str:
    s = re.sub(r'[^a-zA-Z0-9]+', '-', text or '').strip('-').lower()
    return s or 'process'


# ===========================================================================
# 5.  TOP-LEVEL ORCHESTRATOR
# ===========================================================================

def render_bpmn_processes(audit_data: dict[str, Any],
                          client_meta: dict[str, Any],
                          output_dir: Path) -> dict[str, list[Path]]:
    """Render the complete BPMN deliverable set.

    Writes:
      - {output_dir}/2-process-map.html       (landscape index)
      - {output_dir}/processes/{stage}/{slug}.html
      - {output_dir}/processes/{stage}/{slug}.bpmn

    Returns a dict listing the written files (for logging / hooks).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    processes = _extract_processes_with_lanes(audit_data)
    if not processes:
        raise ValueError("No processes with BPMN lanes/flows found in audit data")

    # Build the performer palette ONCE across all processes so colours stay
    # stable across pages and so the index legend matches per-process legends.
    palette = build_performer_palette({"processes": processes})

    written = {"index": [], "pages": [], "bpmn": []}

    for p in processes:
        stage = p.get("stage", "other")
        slug = _slugify(p.get("process_id") or p.get("name") or "process")
        proc_dir = output_dir / "processes" / stage
        proc_dir.mkdir(parents=True, exist_ok=True)

        bpmn_path = proc_dir / f"{slug}.bpmn"
        html_path = proc_dir / f"{slug}.html"

        bpmn_xml = extraction_to_bpmn_xml(p)
        bpmn_path.write_text(bpmn_xml, encoding="utf-8")
        written["bpmn"].append(bpmn_path)

        page_html = build_process_page_html(
            p, bpmn_filename=f"{slug}.bpmn", client_meta=client_meta,
            palette=palette, bpmn_xml=bpmn_xml,
        )
        html_path.write_text(page_html, encoding="utf-8")
        written["pages"].append(html_path)

    index_html = build_index_html(processes, client_meta=client_meta, palette=palette)
    index_path = output_dir / "2-process-map.html"
    index_path.write_text(index_html, encoding="utf-8")
    written["index"].append(index_path)

    return written


def _extract_processes_with_lanes(audit_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Pull processes from v4/v3/v2 audit data shapes; only those with lanes + flows.

    Returns empty list if no process has the BPMN fields set, signals
    caller to fall back to the legacy zone renderer.
    """
    candidates = (
        audit_data.get("processes")
        or audit_data.get("extraction", {}).get("processes")
        or []
    )
    return [
        p for p in candidates
        if p.get("lanes") and p.get("sequence_flows")
    ]
