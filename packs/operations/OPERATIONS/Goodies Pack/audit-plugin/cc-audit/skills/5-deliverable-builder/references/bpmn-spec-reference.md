# BPMN 2.0.2 Spec Reference (Distilled for APG Process Maps)

Source: OMG BPMN 2.0.2 (ISO/IEC 19510:2013), distilled from the bpmn-moddle JSON meta-model (`bpmn-io/bpmn-moddle`) and BPMNspector EXT constraint list. Scoped to the elements APG generates for business process audit diagrams rendered in bpmn-js@18.

This file is the single source of truth for both `generate_bpmn.py` (automated validation) and `process-review.md` (agent-driven pre-checks).

---

## Section 1: Element Catalog

### Document Structure

| Element | XML Tag | Required Attributes | Notes |
|---------|---------|-------------------|-------|
| Definitions | `bpmn:definitions` | `id`, `targetNamespace` | Root element. Must contain at least one `rootElement`. |
| Collaboration | `bpmn:collaboration` | `id` | Contains `participant` elements. One per diagram. |
| Participant | `bpmn:participant` | `id`, `processRef` | `processRef` must point to a `bpmn:process` `id` in the same document. `name` is optional but recommended. |
| Process | `bpmn:process` | `id` | Contains `laneSet`, flow elements, and artifacts. `isExecutable="false"` for non-executable models. |

### Lanes

| Element | XML Tag | Required Attributes | Notes |
|---------|---------|-------------------|-------|
| LaneSet | `bpmn:laneSet` | `id` | One per process when lanes are used. Contains `lane` children. |
| Lane | `bpmn:lane` | `id` | `name` is optional. Contains `flowNodeRef` children listing every element ID assigned to this lane. |

**Rule:** Every flow node (task, gateway, event) inside a process with a `laneSet` must appear in exactly one `lane`'s `flowNodeRef` list.

### Events

| Element | XML Tag | Required Attributes | Parent | Notes |
|---------|---------|-------------------|--------|-------|
| Start Event | `bpmn:startEvent` | `id` | `process` | Zero incoming sequence flows, 1+ outgoing. `name` is optional. |
| End Event | `bpmn:endEvent` | `id` | `process` | Zero outgoing sequence flows, 1+ incoming. `name` is optional. |
| Intermediate Catch Event | `bpmn:intermediateCatchEvent` | `id` | `process` | Must contain an event definition child (e.g., `timerEventDefinition`). 1+ incoming, 1+ outgoing. |
| Intermediate Throw Event | `bpmn:intermediateThrowEvent` | `id` | `process` | Must contain an event definition child (e.g., `messageEventDefinition`). 1+ incoming, 1+ outgoing. |
| Boundary Event | `bpmn:boundaryEvent` | `id`, `attachedToRef` | `process` | `attachedToRef` must reference a task or sub-process ID (not a gateway or event). Zero incoming, 1+ outgoing. `cancelActivity` defaults to `true`. |

**Event Definition Children** (placed inside event elements):

| Definition | XML Tag | Use Case |
|-----------|---------|----------|
| Timer | `bpmn:timerEventDefinition` | Wait periods, SLA delays, scheduled triggers |
| Message | `bpmn:messageEventDefinition` | Notification sent or received mid-process |
| Error | `bpmn:errorEventDefinition` | Exception handling on boundary events |
| Signal | `bpmn:signalEventDefinition` | Cross-process signaling |

### Tasks (Activities)

| Element | XML Tag | Marker Icon | Use Case |
|---------|---------|-------------|----------|
| Task (abstract) | `bpmn:task` | None | Generic task, avoid in favor of specific types |
| User Task | `bpmn:userTask` | Person icon | Human-performed work (default) |
| Service Task | `bpmn:serviceTask` | Gear icon | Automated/system action |
| Send Task | `bpmn:sendTask` | Filled envelope | Outbound message (email, SMS, notification) |
| Receive Task | `bpmn:receiveTask` | Open envelope | Inbound message or trigger |
| Manual Task | `bpmn:manualTask` | Hand icon | Physical/offline task |
| Script Task | `bpmn:scriptTask` | Script icon | Automated script execution |
| Business Rule Task | `bpmn:businessRuleTask` | Table icon | Decision table / rule engine |

**Common attributes:** `id` (required), `name` (recommended), `isForCompensation` (default `false`).

**Children:** `bpmn:incoming` and `bpmn:outgoing` reference sequence flow IDs. Tasks must have 1+ incoming (except if first after start event is implicit) and 1+ outgoing (except if last before end event is implicit). In practice, always generate explicit incoming/outgoing refs.

### Gateways

| Element | XML Tag | Visual | Behavior |
|---------|---------|--------|----------|
| Exclusive Gateway | `bpmn:exclusiveGateway` | Diamond with X | Routes to exactly one outgoing path. `default` attribute can reference one sequence flow ID (the fallback path with no condition). |
| Parallel Gateway | `bpmn:parallelGateway` | Diamond with + | Fork: activates all outgoing paths. Join: waits for all incoming paths. |
| Inclusive Gateway | `bpmn:inclusiveGateway` | Diamond with O | Routes to one or more outgoing paths. |
| Event-Based Gateway | `bpmn:eventBasedGateway` | Diamond with pentagon | Routes based on which event fires first. |

**Rule (fork/join balance):** Every parallel gateway used as a fork (multiple outgoing, one incoming) should have a corresponding parallel gateway used as a join (multiple incoming, one outgoing) downstream. Unbalanced forks produce tokens that never complete.

**Attribute:** `gatewayDirection` can be `Unspecified`, `Converging`, `Diverging`, or `Mixed` (default: `Unspecified`).

### Sequence Flow

| Element | XML Tag | Required Attributes | Notes |
|---------|---------|-------------------|-------|
| Sequence Flow | `bpmn:sequenceFlow` | `id`, `sourceRef`, `targetRef` | `sourceRef` and `targetRef` must reference element IDs within the same process. `name` is used for condition labels on gateway branches. |

**Rule:** Sequence flows cannot cross subprocess boundaries. Both source and target must be in the same process or subprocess.

### Artifacts (future additions)

| Element | XML Tag | Required Attributes | Notes |
|---------|---------|-------------------|-------|
| Text Annotation | `bpmn:textAnnotation` | `id` | Contains `bpmn:text` child with the annotation text. Not a flow element, does not participate in sequence flows. |
| Association | `bpmn:association` | `id`, `sourceRef`, `targetRef` | Connects an artifact to a flow element. Renders as a dashed line. `associationDirection`: `None`, `One`, or `Both`. |
| Data Object Reference | `bpmn:dataObjectReference` | `id` | Represents a data artifact. `name` attribute holds the label. |
| Sub-Process | `bpmn:subProcess` | `id` | Contains its own flow elements. `triggeredByEvent` defaults to `false`. When collapsed, shows a `+` marker. |

---

## Section 2: Validation Rules

Rules derived from BPMNspector EXT constraints, scoped to APG's element set. Rule IDs reference the BPMNspector constraint where applicable.

### Structural Rules

| # | Rule | BPMNspector | Severity |
|---|------|-------------|----------|
| V01 | Every `sequenceFlow.sourceRef` must reference an existing element `id` in the same process | EXT.021 | ERROR |
| V02 | Every `sequenceFlow.targetRef` must reference an existing element `id` in the same process | EXT.022 | ERROR |
| V03 | No duplicate `id` values anywhere in the document | EXT.036 | ERROR |
| V04 | Every `participant.processRef` must reference an existing `process.id` | EXT.028 | ERROR |
| V05 | Every `lane.flowNodeRef` must reference an existing element `id` in the same process | EXT.015 | ERROR |
| V06 | A process with lanes must have exactly one `laneSet` | EXT.015 | ERROR |

### Event Rules

| # | Rule | BPMNspector | Severity |
|---|------|-------------|----------|
| V07 | `startEvent` must have zero `incoming` sequence flows | EXT.096 | ERROR |
| V08 | `startEvent` must have at least one `outgoing` sequence flow | EXT.101 | WARNING |
| V09 | `endEvent` must have zero `outgoing` sequence flows | EXT.104 | ERROR |
| V10 | `endEvent` must have at least one `incoming` sequence flow | EXT.107 | WARNING |
| V11 | `boundaryEvent.attachedToRef` must reference a task or sub-process, not a gateway or event | EXT.147 | ERROR |
| V12 | `boundaryEvent` must have zero `incoming` sequence flows | EXT.112 | ERROR |

### Gateway Rules

| # | Rule | BPMNspector | Severity |
|---|------|-------------|----------|
| V13 | `exclusiveGateway.default` (if set) must reference an outgoing sequence flow ID | EXT.135 | ERROR |
| V14 | `parallelGateway` used as fork should have a corresponding join downstream | — | WARNING |
| V15 | Gateways must have at least one incoming and one outgoing sequence flow (except start/end positions) | EXT.135 | WARNING |

### Diagram Interchange Rules

| # | Rule | BPMNspector | Severity |
|---|------|-------------|----------|
| V16 | Every flow element must have a `BPMNShape` with matching `bpmnElement` attribute | — | ERROR |
| V17 | Every sequence flow must have a `BPMNEdge` with matching `bpmnElement` attribute | — | ERROR |
| V18 | `BPMNEdge` must have at least 2 `di:waypoint` children | — | ERROR |
| V19 | `BPMNShape` for participants and lanes must have `isHorizontal="true"` | — | WARNING |

---

## Section 3: bpmn-js@18 Rendering Notes

These are practical rendering behaviors in bpmn-js that are not part of the OMG spec but affect how diagrams display in APG portals.

### Color Extensions

The `bioc:` and `color:` namespace prefixes are bpmn.io extensions (not OMG standard). Both must be present for color to render:

```xml
xmlns:bioc="http://bpmn.io/schema/bpmn/biocolor/1.0"
xmlns:color="http://www.omg.org/spec/BPMN/non-normative/color/1.0"
```

Applied on `BPMNShape` elements:
- `bioc:stroke="#c62828" bioc:fill="#ffebee"` for pain points (red)
- `bioc:stroke="#1565c0" bioc:fill="#e3f2fd"` for automation/optimisation (blue)
- `color:background-color` and `color:border-color` duplicate the values for tools that read the non-normative namespace

### Horizontal Layout

`isHorizontal="true"` on `BPMNShape` is required for participants and lanes to render as horizontal swim lanes. Without it, bpmn-js defaults to vertical orientation.

### Label Positioning

- Task labels render centered inside the shape by default (no explicit label element needed)
- Gateway and event labels need explicit `BPMNLabel` with `dc:Bounds` to position below/beside the shape
- Sequence flow labels (condition labels on gateway branches) need `BPMNLabel` with `dc:Bounds` positioned near the first waypoint

### Waypoints

- Minimum 2 `di:waypoint` elements per `BPMNEdge`
- bpmn-js draws straight lines between consecutive waypoints
- For orthogonal routing, use 4 waypoints: source exit, first bend, second bend, target entry
- Waypoint coordinates are absolute (relative to the diagram origin, not the lane)

### Text Annotations

- Rendered as an open rectangle with text (no closed border on the right side)
- `bpmn:association` connecting to a flow element renders as a dashed line
- The annotation shape needs its own `BPMNShape` entry in the diagram section

### Task Markers

bpmn-js@18 renders task type markers automatically:
- `userTask`: person silhouette in top-left
- `serviceTask`: gear icon in top-left
- `sendTask`: filled envelope in top-left
- `receiveTask`: open envelope in top-left
- `manualTask`: hand icon in top-left
- `scriptTask`: script page icon in top-left

No additional attributes needed for markers to display.
