# AIO-036 Review

Status: Completed

## Initial authorization and baseline

- Authorization source: direct Human instruction on 2026-09-21.
- Authorized phase: Task creation, Architect design lock, implementation,
  validation, Architect final review, independent review, Gate evaluation, and
  Human-checkpoint preparation.
- Verified baseline: clean `main` at
  `d089bd69e56e9b38d538955eb6e97d08a850884c`.
- AIO-035 is completed and is the sole Task dependency.
- AIO-030 remains parked at
  `5a4dae8ffcca8f986c0eb42755db9a958c57d187` and untouched.
- Under the initial authorization, final Human approval, Task closure, staging,
  commit, push, merge, tag, release, publication, and AIO-037 were
  unauthorized pending a direct Human follow-up.

## Architect design lock

Status: **APPROVE - ISSUED BEFORE IMPLEMENTATION**

On 2026-09-21, a separate non-implementing Architect approved this exact lock:

- Canonical term: **Operation Requirement**.
- Definition: an immutable, caller-supplied declaration that one Core-defined
  abstract operation is required against one exact lexical
  repository-relative resource within the caller-owned evaluation context.
- Exact frozen value fields, in order: `operation_id`, `resource`.
- Exact case-sensitive identity: `(operation_id, resource)`; no synthetic ID,
  aliases, normalization, or case folding.
- Public submodule API:
  `OperationRequirement`, `OperationRequirementFinding`,
  `OperationRequirementValidationResult`, and
  `validate_operation_requirement(requirement)`; no package-root re-export.
- Result fields, in order: `valid`, `findings`, `requirement`. A valid result
  returns the exact supplied object. An invalid result has nonempty tuple
  findings and `requirement: None`.
- Exact operation syntax:
  `^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$`. AIO-036 supports exactly
  `repository_file_read`; unknown well-formed identifiers are unsupported and
  malformed identifiers are not support-checked.
- Validation order: exact value type; field types in `operation_id`, `resource`
  order; operation syntax; operation support; resource lexical grammar.
- Stable resource finding precedence:
  `resource_empty`, `resource_control_character`, `resource_unc_path`,
  `resource_absolute_path`, `resource_drive_qualified_path`,
  `resource_uri_scheme`, `resource_leading_tilde`, `resource_backslash`,
  `resource_trailing_slash`, `resource_empty_segment`,
  `resource_dot_segment`, `resource_parent_segment`, `resource_glob_meta`.
  At most the first resource finding is returned.
- UNC means a `//` or `\\` prefix; absolute means another leading `/`; drive
  qualification means an ASCII letter plus `:` at the start; URI scheme means
  `[A-Za-z][A-Za-z0-9+.-]*:` at the start after drive checking; controls are
  U+0000-U+001F and U+007F-U+009F; separators are `/`; exact empty, `.`, and
  `..` segments are invalid; and the exact glob/meta set is `*?[]{}`.
- All other segment content is opaque and preserved, including case, Unicode,
  spaces, punctuation, inner dots, extensions, and extensionless names. A
  colon is allowed after a slash when it is not a start-of-string drive or URI
  prefix. No Markdown restriction exists.
- The JSON Schema owns structure only: root object, exactly the two required
  nonempty string properties, and no additional properties. Core
  specification and runtime validation own operation vocabulary and lexical
  resource semantics.
- Presence states only caller-declared need. Absence means only that no
  requirement was supplied in this evaluation context; there is no negative
  requirement state.
- Core owns operation meaning, syntax, and validation. The caller/planner owns
  declaration truth, repository context, and external Task/candidate
  association.
- Implementation is pure string/dataclass logic. It must not access or infer a
  repository root; access files or metadata; resolve paths or links; discover
  environment state; use network, process, clock, hashing, or persistence; bind
  a tool; authorize; create an execution contract; dispatch; or invoke.
- No Task, Assignment, candidate, Runtime Option, Project Manifest, CLI,
  adapter, permission, authorization, capability, persistence, or registry
  contract changes are permitted.

The Architect found no scope conflict and issued `APPROVE` subject to exact
implementation of this lock.

## Implementation and validation evidence

Status: **IMPLEMENTED AND VALIDATED**

The implementation adds the locked two-field frozen value, finding, atomic
result, and pure validator in `engineering_orchestration.operation_requirement`.
The Core specification is semantic authority; the JSON Schema remains
structural only. The schema is registered as an installed resource without a
package-root API re-export or new dependency.

All resource examples used by AIO-036 are synthetic. The production module
imports only `dataclasses` and `re` plus `__future__`. Static AST checks reject
filesystem, metadata, resolution, globbing, hashing, process, network, and
persistence calls. Dynamic guards cover source and installed valid,
unsupported-operation, invalid-resource, and invalid-type paths.

Validation used CPython 3.12.10:

- focused Operation Requirement suite: **27/27 passed**;
- Operation Requirement fixtures: **28/28 structural checks passed** and
  **20/20 semantic checks passed**;
- complete unit discovery: **732 total: 728 passed, 4 skipped, 0
  failures/errors**;
- skips: three Windows directory-symlink tests lacked the required OS
  privilege, and one POSIX-signal test is not applicable on Windows;
- package-boundary regressions: **13/13 passed**;
- Task validation: **52/52** schema cases and **24/24** Workflow references;
- Workflow validation: **43/43**;
- Role validation: **28/28**;
- Actor validation: **14/14**;
- Actor Availability validation: **13/13**;
- Actor-to-Runtime Applicability validation: **10/10**;
- Assignment validation: **13/13**;
- Agent Runtime Option and availability validation: **11/11** each;
- Inference Option validation: **12/12**;
- Inference Option Availability validation: **11/11**;
- Runtime-to-Inference Compatibility validation: **12/12**;
- Project Manifest validation: **66/66**;
- target-safe structural aggregate verification: **PASS**;
- targeted Markdown lint for seven changed safe documentation files: **0
  issues**; and
- `git diff --check`: **PASS**, with line-ending conversion warnings only.

The full repository-declared aggregate verification and repository-wide
Markdown lint were deliberately not run because their broad Markdown pattern
could access the protected target. The changed `core/terminology.md` file has
three pre-existing MD046 findings outside the added Operation Requirement hunk;
they were not modified because they are unrelated. The new terminology hunk was
manually compared with the specification, README, schema, and runtime behavior.

Target-safe editable and normal-wheel installation smoke passed. The smoke
uses a disposable explicit package-input snapshot containing only package
metadata, top-level runtime modules, schemas, and Roles; it cannot copy the
protected workflow target. The strict wheel payload contains
`operation_requirement.py` and `operation-requirement.schema.json`, contains no
unexpected generated or vendor payload, and matches canonical schema bytes.
Both install modes pass valid, unsupported-operation, and invalid-resource
probes under no-I/O guards, run outside the checkout, uninstall cleanly, and
remove their temporary environments. The normal install imports its module and
schema only from the disposable environment, proving no source-checkout
fallback.

An initial normal-wheel attempt correctly failed the strict payload assertion
because an ignored stale `build/` artifact from unrelated parked work entered a
root-based setuptools build. No unrelated file was changed or deleted. The
smoke was made target-safe and reproducible by building the normal wheel from
the explicit disposable package-input snapshot; the rerun and a final rerun
with installed no-I/O guards both passed.

## Architect final review

Status: **APPROVE - NO MATERIAL FINDINGS**

On 2026-09-21, the same non-implementing Architect performed the final
architecture review and confirmed:

- exact conformance to the pre-implementation design lock, including the
  two-field identity, operation grammar and vocabulary, resource grammar and
  13-category first-finding precedence, atomic result, and package surface;
- the structural-schema/runtime-semantics split and all adjacent-contract
  boundaries remain intact;
- lexical-only behavior introduces no filesystem, metadata, resolution,
  capability, permission, authorization, tool-binding, execution, or
  invocation surface;
- documentation is mutually consistent and the three disclosed MD046 findings
  are pre-existing outside the AIO-036 terminology hunk; and
- the focused suite independently reran at **27/27 passed**.

The Architect made no changes, ran no broad repository traversal, and did not
access the protected target. The Architect assessed
`documentation_consistency` as **PASS**. At that review checkpoint, Human
architecture/schema approval and final acceptance remained pending.

## Independent review

Status: **APPROVE - NO MATERIAL FINDINGS**

On 2026-09-21, a separate independent Reviewer confirmed the design-lock
conformance, exact two-field contract, schema/semantic split, deterministic
finding order, lexical-only/no-I/O behavior, package/public API, adjacent
contract exclusions, documentation consistency, fixtures, focused tests, and
package evidence. The Reviewer independently reran the focused suite at
**27/27 passed** and an exact-safe-path `git diff --check` at **PASS** with
line-ending warnings only.

The Reviewer made no changes, ran no broad repository traversal, and did not
access the protected target. The Reviewer assessed both effective Gates as
**PASS**. At that review checkpoint, only explicit Human approval remained
pending.

## Quality Gates

- `documentation_consistency`: **PASS** - the Architect and independent
  Reviewer found the changed specification, terminology, public documentation,
  schema/runtime split, and Task evidence mutually consistent, with no
  material findings.
- `independent_review`: **PASS** - a separate Reviewer approved the complete
  AIO-036 evidence and independently reran the focused suite and exact-safe-path
  diff check.

## Human Control

- Approval source: direct Human instruction on 2026-09-21.
- Human architecture/schema approval: **APPROVED**
- Human final acceptance: **APPROVED**
- Architect design lock: **APPROVE**
- Architect final review: **APPROVE**
- Independent review: **APPROVE**
- `documentation_consistency`: **PASS**
- `independent_review`: **PASS**
- Waiver or exception: **NONE REQUIRED**
- Acceptance criteria: **37/37 COMPLETE; 0/37 PENDING**
- Task status: `completed`
- Task closure: **AUTHORIZED AND COMPLETED**
- Exactly one local implementation-and-closure commit on `main`:
  **AUTHORIZED**
- Push, merge, tag, release, or publication: **NOT AUTHORIZED**
