# AIO-036 Acceptance Criteria

Checklist count: 37.

- [x] The Architect approved the canonical term and definition before implementation.
- [x] The canonical value contains exactly `operation_id` and `resource`.
- [x] No `requirement_id` is introduced.
- [x] `operation_id` is exact and case-sensitive.
- [x] `operation_id` uses the locked ASCII lower-snake-case syntax.
- [x] Only `repository_file_read` is supported in AIO-036.
- [x] The operation vocabulary is extensible only through explicit future Core definitions.
- [x] `resource` is exact and case-sensitive.
- [x] `resource` has repository-relative lexical semantics.
- [x] Only forward slashes act as resource separators.
- [x] Absolute, drive-qualified, UNC, URI, and leading-tilde resources are rejected.
- [x] Backslashes are rejected.
- [x] NUL and control characters are rejected.
- [x] Empty, dot, and dot-dot path segments are rejected.
- [x] A trailing slash is rejected.
- [x] Wildcard and glob-meta forms are rejected.
- [x] Resource validation is extension-neutral.
- [x] Caller values are never normalized.
- [x] Validation performs no filesystem access.
- [x] Validation performs no target metadata access.
- [x] Validation performs no path resolution.
- [x] The Task schema and contract remain unchanged.
- [x] Assignment remains unchanged.
- [x] The AIO-034 candidate contract remains unchanged.
- [x] Runtime Option contracts gain no capability semantics.
- [x] No permission semantics are added.
- [x] No authorization semantics are added.
- [x] No concrete tool binding is added.
- [x] No Execution Contract or request is added.
- [x] No execution, dispatch, or invocation is performed.
- [x] The structural schema is registered and packaged.
- [x] Runtime semantic validation and findings are deterministic.
- [x] Every invalid result is atomic with no partial validated value.
- [x] Validation leaves its input unchanged.
- [x] Source and installed editable and normal-wheel behavior agree.
- [x] Documentation consistency and independent review Quality Gates pass with all material findings resolved.
- [x] Explicit Human architecture/schema approval and final acceptance are recorded before Task closure.

At closure, **37/37** criteria are complete and **0/37** remain pending. The
Human explicitly approved the architecture and schema and granted final
acceptance on 2026-09-21. The Architect final review and independent Reviewer
both approved the implementation with no material findings, satisfying both
effective Quality Gates.
