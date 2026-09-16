# AIO-006 - Acceptance Criteria

AIO-006 may be closed only after all applicable criteria are verified and the required Human approval is recorded.

## Role Contract

- [x] A canonical Role specification exists.
- [x] The v0.1 Role contract contains only `id`, `name`, `purpose`, `responsibilities`, `required_capabilities`, and optional `applicable_task_types`.
- [x] A Role is defined as declarative and not directly executable.
- [x] A Role does not identify, configure, instantiate, or control its fulfilling Agent or Human.
- [x] A Role does not contain prompts, personas, model instructions, or runtime behavior.
- [x] A Role does not grant runtime permissions.
- [x] Capability is explicitly distinct from authority and permission.
- [x] Role eligibility is explicitly distinct from execution permission and approval authority.
- [x] A Role does not own Task scope, objectives, dependencies, results, or lifecycle status.
- [x] A Role does not own Workflow sequencing or Execution Mode.
- [x] A Role does not decide whether a Human or Agent fulfils it.
- [x] Required capabilities describe stable engineering competencies rather than runtime tools or operations.
- [x] Applicable Task types are advisory and do not assign or authorize a Role.
- [x] Approval, escalation, assignment, separation of duties, and runtime execution remain external concerns.

## Initial Role Library

- [x] Architect is defined.
- [x] Software Engineer is defined.
- [x] Reviewer is defined.
- [x] Security Reviewer is defined.
- [x] Documentation Specialist is defined.
- [x] Human Approver is not introduced as an ordinary canonical engineering Role.

## Architecture and Scope

- [x] The contract remains Provider- and model-independent.
- [x] No Task schema or Task-to-Role assignment structure is introduced.
- [x] No Agent implementation, Provider integration, prompt system, Workflow execution, permission system, or Assignment Contract is introduced.
- [x] AIO-005 remains untouched.
- [x] The specification-to-schema split is preserved for AIO-007.
- [x] Role documentation references the canonical specification and initial definitions.

## Quality and Closure

- [x] `documentation_consistency` passes.
- [x] `independent_review` passes.
- [x] Canonical Task validation includes AIO-006.
- [x] Final Human approval is obtained before Task closure.
