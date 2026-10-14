# ITRU — Canonical Agent Execution Result Specification

Version: 0.1.0

## 1. Status and ownership

ITRU-060 / SCRUM-16 Phase 1 defined this contract and the Human approved it.
Phase 2 production behavior is implemented in the exact authorized Result module
and original controlled coordinator. Bounded F1/F2/F3 validation passed with
12/29/2 tests and zero skips. Fresh final review stopped on blocking HIGH S-H1:
the generated standard restoration hook can mutate a genuine Result while
retaining its authority membership. Human-authorized bounded remediation now
rejects state restoration and binds membership to the exact published state;
exact F1/F2/F3 revalidation passed 12/29/2 with zero skips. Five fresh technical
specialist reviews APPROVE and independently resolve S-H1/S-M1; Process also
APPROVE. The separate formal independent review APPROVE and independently resolves
S-H1/S-M1. Both required final Quality Gates PASS. The Human explicitly approved
final closure and accepted S-H1/G-L1 remediation on 2026-10-14; ITRU-060 is
completed with 18/18 acceptance criteria. This is a documentary status note only.
This implementation finding and status update change no locked semantics.
This specification owns Result semantics; the Task artifacts own scope,
validation evidence and phase authorization.

Result means **Agent Execution Result** here. Existing prerequisite, validation,
Grant-production and Admission result containers retain their separate meanings.
This contract neither replaces them nor changes the Admission coordinator API.

## 2. Semantic boundary

A Result is immutable terminal evidence of one original controlled execution
attempt with an acknowledged, committed Execution Entry. It reports what the
trusted invocation boundary observed, rather than desired Task completion.
It is not an Execution Entry, authorization, an invocation credential, persistent
Run status, Quality Gate PASS, exactly-once evidence or a retry instruction.

An Entry permanently prevents another entry for that Dispatch. It does not prove
that the Tool started, completed, produced a Result or disclosed content.
An entered attempt can terminate without a published Result, for example through
process death, fatal interruption or Result-construction failure. Absence is
missing evidence, never an implicit success, failure or permission to replay.
There are no pending/running/cancelled/timed-out Result states in this foundation.

## 3. Closed value and identity

The `AgentExecutionResult` exposes exactly six immutable value fields:

| Field | Locked type and meaning |
| --- | --- |
| `ledger_identity` | Existing complete `AuthorizationDomainIdentity` captured by the original trusted subject: domain ID, ledger instance ID and domain generation |
| `execution_entry` | Exact existing immutable Entry: Dispatch identity, Claim ID, executor instance ID, lease generation, entry time and its validated time key |
| `tool_binding` | Exact existing `AgentOperationToolBinding`, including the complete nested `AgentExecutionRun` and its Contract |
| `outcome` | Exactly `succeeded`, `failed_before_effect` or `effect_ambiguous` |
| `payload` | `RepositoryFileReadResultPayload` on success, otherwise `None` |
| `diagnostic` | `AgentExecutionResultDiagnostic` on unsuccessful outcomes, otherwise `None` |

The derived Result identity is the exact case-sensitive five-part tuple:

```text
(ledger_identity.ledger_instance_id,
 execution_entry.identity.authorization_domain_id,
 execution_entry.identity.issuer_kind,
 execution_entry.identity.issuer_id,
 execution_entry.identity.grant_id)
```

The named components in `execution_entry.identity` are positions in the existing
four-part tuple, not a new Entry representation. No `result_id`, `entry_id`, new
Run ID, UUID, hash, timestamp or sequence number is allocated. Physical Entry
identity is ledger-scoped; the same Dispatch tuple in another ledger is distinct.
Domain generation is captured provenance, not an extra occurrence namespace or
a means of manufacturing another Result for an existing Entry.

Every other field is bound immutable evidence for that identity. Same identity
with a different Entry, generation, complete Run, Tool, outcome, diagnostic or
payload is conflicting evidence, never a replacement, update or second outcome.
Passive references to the same published object are not new Results. No global
registry, durable uniqueness claim or cross-process deduplication is introduced.

## 4. Exact binding obligations

Before publication, the trusted producer must enforce all of these together:

1. Entry comes from the original Store's acknowledged `entered` return, with
   `history_only == False`; historical, copied or caller-supplied Entry evidence
   cannot satisfy this requirement.
2. Entry Dispatch identity equals the original subject's complete Dispatch
   identity. Its domain equals the captured ledger domain.
3. Entry Claim ID, executor instance ID and lease generation equal the original
   subject and committed Claim. Entry time and time key remain exact and coherent.
4. Captured ledger identity and pinned Store belong to that original subject;
   matching strings in another Store/session are insufficient provenance.
5. `tool_binding.run` equals the original subject's complete Run and the exact
   admitted Grant/Binding Run already checked by the existing execution path.
   Equality of `run_id` alone is insufficient. All eleven Contract fields remain
   exact, including resource, environment, operation and Execution Mode.
6. Tool identity and configured route equal the original selected binding. No
   aliases, fallback, normalization, new resolution or post-attempt selection.

The existing Run, Contract, Grant, Binding, Entry, Store and SQL migration
contracts retain their shapes. Result embeds descriptive values, not proof
presentations, capabilities, native handles, credentials or Store references.

## 5. Terminal outcomes and the effect boundary

| Outcome | Required evidence | Payload | Diagnostic |
| --- | --- | --- | --- |
| `succeeded` | Original operation completed and every mandatory validation, cleanup and ownership disclosure postcheck passed | Present, including empty bytes | Absent |
| `failed_before_effect` | Trusted boundary positively proves that no content-data request began and no stronger ambiguity was observed | Absent | Present |
| `effect_ambiguous` | Content-data request began but complete validated success is unavailable, or the trusted boundary reports effect/cleanup uncertainty | Absent | Present |

For `repository_file_read`, the semantic effect boundary is **issuing the first
content-data read request**, including the EOF probe for an empty file. Metadata
queries, path traversal and handle opens are not content-data reads; they remain
security-sensitive operations under the existing authorization/containment rules.
`failed_before_effect` promises only absence of that operation's content effect,
not absence of all OS activity, access-time changes or other incidental behavior.

`effect_ambiguous` does not assert that bytes were definitely read or that a
resource was modified. It means validated completion/no-effect cannot be claimed.
A failure after content access is intentionally represented conservatively by
this outcome, even when a particular partial read is positively observed.
Cleanup uncertainty dominates a no-content observation. Adapter-start alone
does not prove a data request, but loss of reliable progress evidence after
adapter-start must remain ambiguous rather than be guessed into no-effect.

No outcome permits automatic retry. Even failed-before-effect follows permanent
Entry consumption. Any new operation requires its own separately authorized new
occurrence through existing governance; Result creates none of that authority.

## 6. Success payload

`RepositoryFileReadResultPayload` has exactly `data: bytes` and `byte_count: int`.
Both are immutable, with exact types (not subclasses, mutable buffers or bool
counts); `byte_count == len(data)` and `0 <= byte_count <= 65536`.
Empty bytes are success with count zero, distinct from absent payload.

Content is raw binary. There is no inferred UTF-8 decoding, parsing, newline
normalization, file path, content type, hash, partial prefix, truncation marker
or arbitrary user-defined payload dictionary. Existing native bounds remain:
65536 disclosed bytes, 65537 physical bytes and 17 data requests. No stronger
atomic snapshot or historical link-provenance claim is added.

Success is published only after mandatory cleanup and the outer ownership
postcheck. A provisional successful read followed by cleanup/postcheck failure
cannot publish success and cannot disclose bytes through failure diagnostics.
Successful content remains sensitive operation data; Result does not grant
permission to log, persist, forward or broaden its audience.

## 7. Failure diagnostics

`AgentExecutionResultDiagnostic` has exactly one field, `code`, chosen from this
closed table. There is no free-text message, OS exception, stack trace, native
error number, absolute path, content preview, exception object or arbitrary map.
The envelope outcome supplies the effect classification; code explains the
observed failure and cannot override that classification.

| Code | `failed_before_effect` | `effect_ambiguous` |
| --- | --- | --- |
| `adapter_unavailable` | Allowed | Allowed; native support/completion can become unavailable after a data request |
| `containment_rejected` | Allowed | Allowed |
| `resource_missing` | Allowed | Allowed |
| `resource_changed` | Allowed | Allowed |
| `size_limit_exceeded` | Allowed | Allowed |
| `read_failure` | Allowed | Allowed |
| `guard_lost` | Allowed | Forbidden; post-start uncertainty uses `effect_ambiguous` |
| `ownership_lost` | Allowed | Forbidden; post-start uncertainty uses `effect_ambiguous` |
| `effect_ambiguous` | Forbidden | Allowed |

These are stable canonical codes with no provider-specific meaning. An unknown
status/code, mismatched success code, malformed payload or incoherent binding is
an internal integrity failure: no canonical Result is constructed and no content
is released. It is not a fourth terminal outcome. This diagnostic channel is
separate from ordinary schema/validation findings about malformed inputs.

## 8. First producer and exact mapping

The first and only producer supported by this foundation is the original fixed
native `repository_file_read` chain, bound to
`tool::itru-native-repository-file-read::v1`.
No executable callback registry, generic Tool producer or alternate route is
introduced. Future operations require separately reviewed effect/payload rules.

| Existing private invocation evidence | Canonical disposition |
| --- | --- |
| Acknowledged original `entered` + `completed` / `effect_completed`, valid bytes and all postchecks | `succeeded`, exact payload, no diagnostic |
| Original `entered` + `failed_before_content` with allowed code and reliable no-content evidence | `failed_before_effect`, no payload, that code |
| Original `entered` + `failed_after_content` with allowed code | `effect_ambiguous`, no payload, that code |
| Original `entered` + `ambiguous` / `effect_ambiguous` | `effect_ambiguous`, no payload, `effect_ambiguous` |
| Rejection before Entry, `commit_unknown`, verified absence, `already_entered`, `historical_entry` or any other history-only result | No Result; preserve owning Entry diagnostic unchanged |
| Fatal `BaseException` or process termination | No guaranteed Result; preserve existing propagation and permanent Entry semantics |

The producer must not expose a public function that translates arbitrary
`_ControlledOutcome`, Entry or dictionaries into a trusted Result. Existing
private containers are freely reconstructible diagnostic data; their type and
shape alone cannot prove execution provenance. Original-frame and exact-subject
provenance must be captured by trusted composition, not supplied by an adapter.

## 9. Trusted construction authority

Only the existing original `_ControlledInvocationCoordinator.invoke` frame may
request construction, after an acknowledged Entry and the final disposition.
A private producer tied to that coordinator, process, original frame and exact
subject/Entry validates the mapping and publishes at most one Result for that
frame. Public construction, subclassing, caller-added `trusted` flags, raw
mapping conversion, adapter-returned canonical Results and a history factory
are unsupported. Pure structural checks do not authenticate origin.

The value has read-only six-field access. Its trusted origin is private
process-local membership, outside value fields and equality, never a serialized
boolean or caller-controlled seal. Copy/deepcopy/pickle reconstruction cannot
produce trusted membership and must reject for the trusted object. A caller can
fabricate a lookalike report; no trusted consumer may accept it as producer output.
Trusted membership is evidence provenance, not execution or replay authority.
Arbitrary hostile code inside the trusted interpreter is outside this boundary's
threat model; no Python object is claimed to be an OS sandbox or signed artifact.

Construction adds no I/O, clock sampling, random identifier allocation, Store
write, native call, policy decision or earlier-lock reentry. Ordinary outcomes
are published after existing S/G/P scopes unwind. If that unwind fails after
possible effect, the original trusted exception path may publish only ambiguous
evidence, with no content. A no-effect exception path may publish only its proven
no-effect outcome. It must not reacquire live effect authority to report failure.

Construction failure preserves Entry and consumed continuation; it never clears
Entry, creates a second continuation, retries the Tool or leaks a partial Result.
If validation/construction rejects after a private `completed` outcome, the
coordinator must not return `_ControlledOutcome` carrying those successful bytes.
Raise a sanitized internal-integrity exception with a fixed non-content message,
no attached payload, raw exception or exception chaining. No Result is published;
the consumed Entry remains permanent. This failure path is not an ordinary
terminal Result or a legacy success fallback.
The existing continuation's authority is burned before resource-derived actions
and remains separate from Result provenance.

## 10. Persistence and serialization decisions

**Result persistence: NO.** No table, SQL migration, file, Journal, Result cache,
Task/Run lifecycle store, recovery job or restart reconstruction is introduced.
Existing Entry persistence remains authoritative at its existing boundary.
Result disappears with its process unless retained by an authorized consumer;
this Task creates no persistence permission or retention subsystem.

**Canonical serialized Result format and schema: NONE in ITRU-060.** This is an
in-memory produced evidence contract, not a caller-supplied serialized contract.
Raw bytes and private provenance have no approved transport boundary. JSON/YAML,
base64, mapping roundtrip, pickle and schema validation cannot restore trust.
Therefore Phase 1 creates no Result JSON Schema, schema URI, serialization helper,
schema-resource registration or packaging entry. Existing schemas remain exact.

A future Journal or transport Task must separately define a descriptive recorded
Result projection, binary encoding, versioning, authority/provenance and privacy
rules. Such a projection cannot recover a live Result producer or execution
capability. The six-field shape is the semantic foundation, not advance approval
of any wire format or storage backend.

## 11. Phase 2 implementation boundary

The Human-approved Phase-2 implementation follows this bounded plan:

1. Add `itru/agent_execution_result.py` for the immutable readable value/payload/
   diagnostic types and private trusted-construction support. Expose no public
   builder, persistence, serializer, dispatch or replay API.
2. Extend the private `_ControlledOutcome` with optional `result` defaulting to
   `None`, retaining existing `entry_result` and `invocation` fields and valid
   ordinary dispositions, subject to the construction-failure non-disclosure
   rule above.
   Produce Result inside the original trusted coordinator path; the Admission
   API and its result union remain unchanged.
3. Modify `_execution_entry_and_controlled_invocation.py` only as necessary for
   provenance capture, final mapping and optional Result publication. Preserve
   existing guard ordering, native safety and fatal-exception propagation.
4. Add exact named Result unit and controlled-integration test modules from the
   Task plan. Native reader and Store behavior remain untouched; if reliable
   mapping requires changing them or another predecessor contract, stop for
   renewed scope/architecture authorization and specialist review.

Phase 1 contained no implementation. Phase 2 added the approved module/tests and
bounded original-coordinator wiring only. The Task records the exact command
outputs, source safety inspection, failed attempts and final passing results.

S-H1 remediation enforces this existing immutable-evidence boundary through
explicit rejecting restoration hooks and private publication-state comparison.
Result/payload/diagnostic expose no state serialization or restoration format.
The original producer captures exact value references and typed immutable
ledger/Entry/Run/Contract/Tool/outcome/content/diagnostic leaves. Passive membership
rejects changed evidence and permanently drops membership after an observed
mismatch; a reconstructed object fails exact-object membership. This is only
provenance validation, not a new Result outcome, positive authority path,
persistent cache or execution lifecycle. The locked six-field contract and
trusted-interpreter threat boundary remain unchanged.

## 12. Compatibility and scope invariants

Preserve every existing public Run/Contract/Grant/Binding/Admission API and schema,
immutable SQL migration bytes and durable evidence. Preserve historical Tool
identity exactly in its existing separate historical boundary. Active production
still accepts only the current canonical Tool/route; a historical capability,
retired Tool or recovered Entry cannot produce a fresh Result.

Terminal Result means the operation disposition only. Task closure, Stage
transition, Quality Gate evaluation, Human approval, scheduler/DAG and UI remain
outside this contract. No Result outcome changes persistent Task/Run state.
The Task's bounded scenario and validation-safety matrices are mandatory planning
evidence. Authorized implementation, bounded validation, fresh final reviews and
required final Quality Gates are complete. Explicit final Human approval and
ITRU-060 closure are recorded in the canonical Task evidence; neither is inferred
from a Result outcome or passing tests. No locked semantic contract changed at
closure.
