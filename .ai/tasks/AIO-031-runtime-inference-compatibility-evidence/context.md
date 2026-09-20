# AIO-031 Context

## Authorization and verified baseline

The Human authorized creation, Architect design, implementation, validation,
independent reviews, and preparation of the AIO-031 Human Control checkpoint in
the attached Task request received on 2026-09-20. That initial authorization
explicitly withheld final Human architecture/schema approval, final acceptance,
Task closure, commit, push, merge, release, publication, and AIO-032 work.

Before any file was changed, the repository was verified on branch `main` at
HEAD `5cca2fc5010defa2d789fb08795602c1ca038f55`. Working tree and index status,
both diff summaries, and the untracked-file inventory were empty. All 28 Task
records on `main` were completed, AIO-029 was the latest completed Core Task,
and no AIO-031 directory or reachable historical AIO-031 path existed. No
fetch, pull, or live remote query was performed.

AIO-030 remains an independent parked workstream on local branch
`feature/aio-030-vscode-control-center` at checkpoint
`5a4dae8ffcca8f986c0eb42755db9a958c57d187`, with its Task `in_progress`.
Neither that branch nor its Task records were entered or modified. Ignored
`apps/vscode/out/` artifacts and the existing local exclude rule remain
untouched. Local tracking-reference observations are not claims about live
remote state.

## Current limitation and dependencies

AIO-028 established caller-supplied Inference Option identity and inventory
validation. AIO-029 directly established caller-supplied Agent Runtime Option
identity and inventory validation and concluded that a later separate positive
compatibility relation was justified. Before AIO-031, Core had no contract
through which callers could report which externally selectable Inference
Options a Runtime Option supports invoking.

AIO-031 directly depends on completed AIO-029 and transitively consumes the
AIO-028 public API. It reuses
`validate_agent_runtime_option_inventory` and
`validate_inference_option_inventory`. It has no dependency on AIO-030,
availability composition, Actor Selection, Assignment, Execution Mode matching,
Provider Adapters, or invocation.

## Architect design lock

Before implementation, a non-implementing Architect execution reviewed the
governing contracts and issued `APPROVE`. The locked canonical term is
**Runtime-to-Inference Compatibility Evidence**, defined as:

> An immutable, caller-supplied positive evidence value reporting that one
> Agent Runtime Option supports invoking one externally selectable Inference
> Option within the supplied evaluation context.

This is supplied evidence. It is not live verification of an integration,
proof of current availability, a viable or selected configuration, execution
permission, or an invocation guarantee. Absence of a provenance field does not
mean that Core independently verified the evidence.

The immutable value and exact edge identity contain only, in this order:

```text
(runtime_option_id, option_id)
```

Both references are required, nonempty under the structural schema, opaque,
exact, and case-sensitive. Core does not trim, normalize, parse, synthesize, or
replace them with Provider or model identity. The endpoint Definitions and
their schemas remain unchanged.

The locked public API is the module
`engineering_orchestration.runtime_inference_compatibility` exposing:

- `RuntimeInferenceCompatibilityEvidence`
- `RuntimeInferenceCompatibilityFinding`
- `RuntimeInferenceCompatibilityValidationResult`
- `validate_runtime_inference_compatibility(evidence, runtime_options, inference_options)`

The result fields are exactly `valid`, `findings`, and `normalized_evidence`.
No package-root re-export is required by the existing module-scoped convention.

Both foundational inventory validators run first, Runtime then Inference,
before evidence is inspected. If either inventory is invalid, their existing
finding codes and messages are converted to the compatibility finding type and
concatenated Runtime first, then Inference, while preserving each validator's
order. Relation processing does not begin and no partial evidence is returned.

With valid inventories, finding categories are ordered as follows:

1. duplicate exact pairs sorted by `(runtime_option_id, option_id)`;
2. unknown Runtime Option IDs sorted exactly;
3. unknown Inference Option IDs sorted exactly.

The locked relation diagnostic codes are:

- `duplicate_runtime_inference_compatibility`
- `agent_runtime_option_not_found`
- `inference_option_not_found`

Foundational inventory diagnostics remain owned by their existing validators.
Any finding invalidates the complete supplied relation and yields
`normalized_evidence: ()`. A valid result contains the supplied unique evidence
sorted by the exact edge identity. Ordering is canonicalization only, never
preference, priority, routing, fallback, or selection.

The schema describes one evidence object, not an inventory wrapper. It enforces
exactly the two required nonempty string fields and no additional properties.
It does not validate inventory uniqueness, duplicate edges, or foreign
references; those are runtime relation semantics.

## Relation semantics and boundaries

The relation is many-to-many and imposes no totality requirement. An empty
relation is valid whenever both supplied inventories are valid, including
valid empty/nonempty inventory combinations. A missing edge means only:

```text
No supplied positive external compatibility evidence
```

It does not mean explicit incompatibility, unavailability, inability to
execute, or prohibition. Runtime Options may own or hide inference selection
and therefore need no external edge. No negative evidence, wildcard, null edge,
synthetic option, or convenience compatibility boolean is introduced.

Compatibility remains separate from Actor identity or applicability, all three
availability contracts, Actor Selection, Assignment, Execution Mode and
capability satisfaction, configuration viability, selection, authority,
Execution Contracts, and invocation. Validation is pure and caller-owned: no
global state, persistence, project inventory, discovery, Provider SDK, network
call, or new dependency is introduced.

## Classification rationale

`complexity: high` reflects a new semantic authority and schema, validation
across two existing inventories, deterministic multi-category diagnostics,
atomicity, packaging, and independent architectural review. `risk: medium`
reflects an additive, pure, in-memory, non-authorizing contract whose mistakes
could shape later execution work but cannot invoke anything. `execution.mode:
deep` is explicitly selected for boundary analysis, edge-case validation,
installation proof, and independent review; it is not inferred from Complexity
or Risk. The explicitly bound `architecture-change` Workflow supplies the
understand, design, implement, validate, and review choreography.

At the design and review checkpoints, Human architecture/schema approval
remained pending. The Architect design lock did not satisfy or bypass that
Human Control requirement.

## Human approval and closure authorization

On 2026-09-20, the Human explicitly approved the reviewed AIO-031 architecture
and schema, final implementation and product scope, reconciled verification and
review evidence, completion of the existing acceptance criteria, Task closure,
and one local implementation-and-closure commit. The approval source is the
attached Human approval request for AIO-031 received on that date.

The Human expressly acknowledged the earlier full-verifier no-result, the
vendor-inclusive Markdown failure, the complete passing first-party Markdown
scope, and the later passing exact aggregate unit-test invocation. No Quality
Gate waiver or Human exception was requested or granted. The approval does not
authorize push, merge, release, publication, AIO-030 work, AIO-032 creation, or
any deferred configuration, selection, authorization, adapter, or invocation
layer.
