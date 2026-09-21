# AIO-037 Acceptance Criteria

Checklist count: 35.

- [x] The Architect approves the canonical term, definition, API, validation, normalization, boundaries, and exclusions before implementation.
- [x] The canonical observation contains exactly `runtime_option_id`, `operation_id`, and `state`.
- [x] The exact identity is `(runtime_option_id, operation_id)` and excludes `state`.
- [x] The states are exactly `present`, `absent`, and `unknown`.
- [x] A missing known Runtime/Core-operation observation normalizes to `unknown`.
- [x] Explicit `absent` remains distinct from explicit or synthesized `unknown`.
- [x] The captured Runtime Option inventory is validated through `validate_agent_runtime_option_inventory`.
- [x] Operation Requirement and capability validation use one shared package-internal Core operation vocabulary.
- [x] AIO-036 public types, validator signature, findings, messages, supported operation, resource grammar, ordering, and atomicity remain unchanged.
- [x] Malformed operation syntax is reported separately from a well-formed unsupported operation.
- [x] An observation referencing an unknown Runtime Option invalidates the snapshot.
- [x] Duplicate identical observation pairs invalidate the snapshot.
- [x] Duplicate conflicting observation pairs invalidate the snapshot.
- [x] Declaration order creates no first-wins, last-wins, deduplication, or temporal precedence.
- [x] Valid normalized observations use exact case-sensitive `(runtime_option_id, operation_id)` ordering.
- [x] Every invalid result is atomic and contains no partial normalized observations.
- [x] Runtime and observation inputs are captured once and remain unmodified.
- [x] Resource is absent from the capability contract.
- [x] Tool identity and binding are absent from the capability contract.
- [x] Timestamp, freshness, expiry, source, reason, metadata, and extensions are absent.
- [x] Agent Runtime Option Definition and its schema remain identity-only and unchanged.
- [x] Operation Requirement value/schema semantics remain need-only and unchanged.
- [x] Agent Runtime Option Availability semantics and schema remain unchanged.
- [x] No environment-permission or Permission Decision semantics are introduced.
- [x] No Human/policy authorization or approval semantics are introduced.
- [x] No discovery, polling, Provider Adapter, host inspection, or external integration is introduced.
- [x] No Actor applicability, Assignment, candidate, selection, Execution Contract, dispatch, execution, or invocation semantics are introduced.
- [x] The JSON Schema validates only the exact structural observation shape and closed state enum.
- [x] The schema, runtime modules, and shared vocabulary helper are registered and packaged correctly.
- [x] Focused tests cover all twelve investigation scenarios with synthetic values only.
- [x] Static and dynamic evidence proves validation performs no filesystem, environment, subprocess, network, clock, persistence, discovery, or protected-target access.
- [x] Source, editable-install, and normal-wheel behavior agree without source fallback or new dependencies.
- [x] Canonical documentation and terminology are mutually consistent with implementation.
- [x] Independent review and both effective Quality Gates pass with all material findings resolved.
- [x] Explicit Human architecture/schema approval and final acceptance remain required before Task closure or commit.

The Task remained `in_progress`, and the final criterion remained pending,
until the Human supplied explicit architecture/schema approval and final
acceptance on 2026-09-21.
