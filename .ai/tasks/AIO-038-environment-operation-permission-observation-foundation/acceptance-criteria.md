# AIO-038 Acceptance Criteria

Checklist count: 55.

- [x] The Architect locks the canonical term and definition before implementation.
- [x] A separate Security Reviewer approves Observation, Permission Decision, and Human/policy authorization separation before implementation.
- [x] The observation contains exactly five fields in the locked order.
- [x] Exact identity excludes `state`.
- [x] No synthetic permission ID is introduced.
- [x] States are exactly `allowed`, `denied`, and `unknown`.
- [x] Observation states remain distinct from Permission Decision vocabulary.
- [x] `ask` and `always-ask` are absent from the observation contract.
- [x] Runtime Option ID remains required.
- [x] Opaque snapshot-scoped environment ID remains required.
- [x] No Environment Definition or registry is introduced.
- [x] Operation ID validation reuses the canonical Core vocabulary.
- [x] Resource validation reuses one canonical shared repository-resource grammar.
- [x] No freshness, timestamp, expiry, source, or provenance field is introduced.
- [x] A missing exact observation semantically means unknown, never denied.
- [x] Validation creates no resource Cartesian product or synthetic observation.
- [x] The canonical Runtime Option inventory validator is reused.
- [x] An unknown Runtime reference atomically invalidates the snapshot.
- [x] An environment-scope mismatch atomically invalidates the snapshot.
- [x] Malformed operation syntax remains distinct from unsupported operation vocabulary.
- [x] An invalid lexical resource atomically invalidates the snapshot without filesystem access.
- [x] Identical duplicate observations invalidate the complete snapshot.
- [x] Conflicting observations invalidate the complete snapshot.
- [x] `allowed + denied` is an invalid conflict.
- [x] `allowed + unknown` is an invalid conflict.
- [x] `denied + unknown` is an invalid conflict.
- [x] No first-wins conflict resolution exists.
- [x] No last-wins conflict resolution exists.
- [x] No latest-wins conflict resolution exists.
- [x] No deny-wins conflict resolution exists.
- [x] No stricter-wins conflict resolution exists.
- [x] A conflict is not converted to `unknown`.
- [x] A conflict is not converted to `denied`.
- [x] A conflict is not converted to a Permission Decision.
- [x] Conflict reconciliation remains caller/environment-owned.
- [x] Conflict findings are deterministic and declaration-order independent.
- [x] Declaration order creates no precedence for any repeated observation.
- [x] Valid supplied observations use canonical exact four-part ordering.
- [x] Every invalid result is atomic and contains no normalized observations.
- [x] Caller iterables are captured once and caller values remain unmodified.
- [x] The JSON Schema remains structural only.
- [x] Runtime Operation Capability semantics remain unchanged.
- [x] Agent Runtime Option Availability semantics remain unchanged.
- [x] Permission Decision semantics remain unchanged.
- [x] No Human/policy authorization result or approval parsing is introduced.
- [x] No discovery, polling, enforcement, permission mutation, or ambient-state dependency is introduced.
- [x] No Execution Contract, request, dispatch, execution, or invocation is introduced.
- [x] All twelve authorized investigation scenarios pass.
- [x] All six conflict permutations pass with identical conflict semantics.
- [x] AIO-036 public behavior remains unchanged after resource-helper extraction.
- [x] Source, editable-install, and normal-wheel behavior agree without source fallback.
- [x] Package modules, schema resources, and exact payload checks are correct.
- [x] Specification, terminology, README, changelog, Sources of Truth, adjacent boundaries, and Task evidence are consistent.
- [x] Architect final review, Security final review, independent review, and both effective Quality Gates pass with all material findings resolved.
- [x] Explicit Human architecture/schema/security approval and final acceptance are recorded before Task closure.

Criteria 1 and 2 were completed before implementation. Criteria 3 through 54
are supported by implementation, validation, final specialist reviews,
independent review, and both effective Quality Gates. On 2026-09-21, the Human
supplied the separately required final architecture, schema, security-boundary,
and acceptance approvals. Criterion 55 is complete, for a final count of 55/55.
