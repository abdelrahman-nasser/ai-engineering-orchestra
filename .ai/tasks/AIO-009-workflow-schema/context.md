# AIO-009 — Context

## Authority and scope

Direct dependency: AIO-008, closed at `aee008ee092bce995e795797239f4fc0d4cd19c3`.
The Human approved the AIO-009 proposal and authorized implementation with status
`in_progress`. AIO-008 records and approved Workflow semantics remain unchanged.
Only Section 15 of the Workflow specification receives a factual validation-status
update, explicitly authorized by the Human. AIO-003, AIO-005, and AIO-007 provide
schema/test precedents, not additional semantic authority.

The governing process is `architecture-change`, explicitly selected for this
structural framework change and recorded here rather than in an unsupported Task
field. Architect analysis was performed in the approved proposal; implementation
uses the Software Engineer Role. Independent review and final Human approval are
required before closure. Proposal approval is not final approval of implementation.

## Structural constraints

JSON Schema Draft 2020-12 validates exactly the approved Workflow and Stage fields.
Both objects reject unknown fields. `stages` requires at least one item. Only
Workflow `name` and Stage `purpose` have `minLength: 1`, as explicitly authorized
by AIO-008. IDs, Workflow purpose, and list items remain strings without added
length or naming constraints. There are no enums, defaults, extensions, or
`uniqueItems`. Optional arrays can be empty; references can repeat.

The omission of `human_control_checkpoint` remains omission. When present it is
boolean, and it does not create approval authority.

Schema-valid does not imply semantically acceptable, useful, or approved.
Structural edge fixtures intentionally demonstrate empty unconstrained strings,
empty optional arrays, repeated references, and repeated Stage IDs. They are not
recommended semantic designs. Workflow and Stage ID uniqueness are separately
checked across inspected canonical projections; this is repository semantic
validation. Role/Gate reference existence is manually reviewed, not resolved by
the schema or a new generalized resolver.

## Markdown projection boundary

The extractor is repository-local and test-only, restricted to the current
canonical document structure. It preserves order and optional-field omission,
inserts no defaults, and infers no missing fields. Exact Stage numbering and
heading/explicit-ID agreement are checked. Unsupported syntax, duplicate/unknown
fields or sections, malformed lists, and ambiguous scalar formatting fail visibly.
The recognized title and boundary notice are checked rather than arbitrary prose
being silently discarded. Strict document formatting is not an identifier grammar
or a new restriction on normalized Workflow objects.

This establishes no public parser, runtime serialization, persistence, API, CLI,
Markdown AST framework, Assignment Contract, or Execution Contract.

## Known post-foundation integration gap

AIO-008 conceptually documents Task `workflow` and Project `workflows.default`.
The current Task and Project Manifest schemas do not support these fields.
AIO-009 does NOT provide machine-readable Task-to-Workflow or Project-default
Workflow selection and does not claim end-to-end automatic Workflow resolution.
The first vertical slice may use explicit Human/orchestrator Workflow selection.
A future narrowly scoped compatibility task may address machine-readable selection
only if the vertical slice demonstrates the need. This gap is not fixed here.

## Validation limits

Neither schema validity nor the limited uniqueness checks prove historical ID
stability, project-wide uniqueness outside inspected definitions, reference
suitability, meaningful governance, Task suitability, actor qualification,
assignment independence, separation of duties, approval truth, Quality Gate union
enforcement, sequential execution, Stage completion, or legitimate Task closure.

Required regressions: Workflow, Task, Role, and Project Manifest validators, plus
`git diff --check`. The new validator must demonstrate real mismatch/nonzero exit
behavior and fixture coverage failures. Evidence belongs in `review.md`.
