# AIO-039 Acceptance Criteria

Checklist count: 73.

- [x] A separate non-implementing Architect approves the exact design before implementation.
- [x] A separate Security Reviewer approves the exact security boundary before implementation.
- [x] The canonical category is Evidence, not Observation, Grant, or Decision.
- [x] The canonical term is Agent Execution Authorization Evidence.
- [x] The value contains exactly fourteen fields.
- [x] The exact fourteen-field order is locked and implemented.
- [x] The exact ten-part action subject is locked and implemented.
- [x] The complete Assignment value is bound.
- [x] Runtime Option identity is bound.
- [x] External Inference Option identity is bound.
- [x] Opaque evaluation environment identity is bound.
- [x] Core operation identity is bound.
- [x] One exact lexical repository resource is bound.
- [x] `authority_kind` is exactly `human` or `policy`.
- [x] Exact opaque `authority_id` is required.
- [x] Exact opaque `provenance_reference` is required.
- [x] Authority and provenance are never claimed to be authenticated by Core.
- [x] States are exactly `granted` and `denied`.
- [x] No serialized `unknown` state exists.
- [x] Missing exact evidence is represented by absence.
- [x] Missing evidence remains distinct from explicit denial.
- [x] No `authorization_id` or equivalent grant identity exists.
- [x] No Execution Run or execution identifier exists.
- [x] No timestamp or issued-at field exists.
- [x] No expiry field exists.
- [x] Validation performs no clock access.
- [x] No single-use or reusable-grant behavior is claimed.
- [x] No replay protection is claimed or implemented.
- [x] No revocation lifecycle is claimed or implemented.
- [x] No authorization persistence or registry is introduced.
- [x] Exact duplicate evidence invalidates the complete snapshot.
- [x] Same-subject differing-state evidence is an invalid conflict.
- [x] Same-subject/state differing-authority or provenance evidence is invalid unsupported multi-authority evidence.
- [x] No first-, last-, or latest-wins resolution exists.
- [x] No grant-wins conflict resolution exists.
- [x] No deny-wins conflict resolution exists.
- [x] No stricter-wins conflict resolution exists.
- [x] Conflict reconciliation remains caller or authority-producer owned.
- [x] No Cartesian authorization evidence is synthesized.
- [x] Valid supplied evidence is canonically ordered by exact subject.
- [x] Every invalid result is atomic and contains no normalized evidence.
- [x] Caller iterables are captured once and caller values remain unmodified.
- [x] Canonical Assignment validation and reference behavior are reused.
- [x] Canonical Agent Runtime Option inventory validation is reused.
- [x] Canonical Inference Option inventory validation is reused.
- [x] Canonical Core operation vocabulary validation is reused.
- [x] Canonical lexical repository-resource validation is reused.
- [x] AIO-023 Assignment behavior remains unchanged.
- [x] AIO-034 candidate prerequisite behavior remains unchanged.
- [x] AIO-036 Operation Requirement behavior remains unchanged.
- [x] AIO-037 Runtime capability behavior remains unchanged.
- [x] AIO-038 environment permission behavior remains unchanged.
- [x] Task Human approval remains distinct from execution authorization.
- [x] Permission Decision remains distinct from execution authorization evidence.
- [x] Environment permission remains distinct from authorization evidence.
- [x] Core issues and invents no authority.
- [x] No Task, review, chat, commit, or approval prose is parsed.
- [x] No authority lookup, authentication, entitlement, or signature verification occurs.
- [x] No permission, environment, Runtime, inference, or resource discovery occurs.
- [x] No permission or authorization enforcement occurs.
- [x] No Execution Contract is introduced.
- [x] No Execution Run is introduced.
- [x] No dispatch, tool call, Agent execution, or invocation occurs.
- [x] All eighteen authorized investigation scenarios have focused synthetic coverage.
- [x] Structural schema responsibility remains separate from semantic runtime validation.
- [x] Source, editable-install, and normal-wheel behavior agree without source fallback.
- [x] Package modules, schema resources, and exact payload checks are correct.
- [x] Specification, terminology, README, changelog, Sources of Truth, adjacent boundaries, and Task evidence are consistent.
- [x] Architect final review passes with all material findings resolved.
- [x] Security final review passes with all material findings resolved.
- [x] Fresh independent review passes with all material findings resolved.
- [x] `documentation_consistency` and `independent_review` both pass without waiver.
- [x] Explicit Human architecture, schema, security-boundary, and final acceptance are recorded before closure.

Criteria 1 and 2 were completed before implementation. Criteria 3 through 72
were completed through implementation, validation, final specialist reviews,
independent review, and Gate evidence. Criterion 73 was completed by direct
Human architecture, schema, security-boundary, and final acceptance approval
on 2026-09-21.
