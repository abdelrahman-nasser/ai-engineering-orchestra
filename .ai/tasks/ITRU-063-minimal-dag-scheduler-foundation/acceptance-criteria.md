# ITRU-063 acceptance criteria

- [x] D01 canonical exact Task and dependency identities; immutable closed DAG.
- [x] D02 duplicate, missing endpoint, self-edge and cycle rejection is atomic.
- [x] D03 deterministic normalization/topological ordering and bounded graph size.
- [x] D04 empty graph and disconnected/diamond DAGs supported.
- [x] S01 dependency completion uses persisted Task completion only.
- [x] S02 missing observations remain unresolved and suppress new selection.
- [x] S03 deterministic lexical selection and complete per-Task evidence.
- [x] S04 exact bounded concurrency; pending/running occupancy; over-capacity stop.
- [x] S05 persisted definitions, identities, revisions and observable state checked.
- [x] S06 restart recovery consumed without capability restoration or replay.
- [x] S07 effect_ambiguous/interrupted remain unsafe; no automatic continuation.
- [x] S08 completed/cancelled/blocked/prior-attempt Tasks never auto-selected.
- [x] H01A unchanged Assignment and Checkpoint handoff; contextual validation explicit.
- [x] H02 fresh downstream authority chain required; no hidden native/Tool execution.
- [x] E01 immutable decision/evidence and minimal query/evaluation APIs documented.
- [x] E02 ITRU-060/061/062 and all existing persistence/migrations unchanged.
- [x] V01 source/fixture static safety audit completed before runtime validation.
- [x] V02 exact V1-V4 pass with no skipped tests and fixture absence evidence.
- [x] R01 five fresh independent specialist reviews and all required remedies.
- [x] P01 exact design/implementation/review/final-gate locks retained; scope preserved.
- [x] G01 final FQ-DC-1 and FQ-IR-1 PASS (exact locked procedures authorized and executed).
- [x] H01 final Human approval and Task closure (explicit FINAL HUMAN CLOSURE ONLY authorization recorded).

Current acceptance: 22/22. Final Human closure COMPLETE; Task completed and closed.
FQ-DC-1 documentation_consistency PASS, FQ-IR-1 independent_review PASS and
publication readback PASS remain retained and unchanged. H01 is satisfied by
APPROVE ITRU-063 FINAL HUMAN CLOSURE ONLY, not inferred from technical evidence.
No validation, specialist review or final gate was rerun for closure.
