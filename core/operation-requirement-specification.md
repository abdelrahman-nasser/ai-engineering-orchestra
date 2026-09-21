# AI Engineering Orchestra - Operation Requirement Specification

Version: 0.1.0

This document defines the canonical Operation Requirement contract for AI
Engineering Orchestra v0.1.

---

## 1. Purpose

An **Operation Requirement** is an immutable, caller-supplied declaration that
one Core-defined abstract operation is required against one exact lexical
repository-relative resource within the caller-owned evaluation context.

It answers only:

> What abstract operation does the caller declare is needed against what exact
> repository-relative resource in this evaluation context?

It states need only. The following separation is mandatory:

```text
requirement
!= capability
!= permission
!= authorization
!= execution
```

Core validates the declaration but does not independently verify why it is
needed or associate it with a Task, candidate, Runtime, environment, or tool.

---

## 2. Canonical Value and Identity

The value contains exactly these fields, in order:

| Field | Required | Purpose |
| --- | --- | --- |
| `operation_id` | Yes | Exact identifier of one Core-defined abstract operation |
| `resource` | Yes | Exact lexical repository-relative resource path |

```yaml
operation_id: repository_file_read
resource: synthetic/input.txt
```

Its exact identity is:

```text
(operation_id, resource)
```

Both parts are case-sensitive. Core never trims, normalizes, case-folds,
rewrites, resolves, or aliases either value. There is no `requirement_id` or
other synthetic identity.

---

## 3. Operation Identifier Contract

`operation_id` uses this exact ASCII lower-snake-case grammar:

```regex
^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$
```

The first character must be an ASCII lowercase letter. Later characters may be
ASCII lowercase letters or digits, with single underscores separating
nonempty parts. Uppercase letters, non-ASCII letters, leading or trailing
underscores, consecutive underscores, whitespace, hyphens, and other
punctuation are invalid.

AIO-036 supports exactly:

```text
repository_file_read
```

`repository_file_read` means the abstract need to access or read the content of
the one repository file lexically named by `resource` under the caller-owned
repository root. It says nothing about a concrete tool, encoding, existence,
file kind, Runtime capability, environment permission, authorization, or
execution.

The vocabulary is framework-defined and extensible only through a future
explicit Core definition. An unknown well-formed identifier is unsupported;
it is not inferred from a tool or Provider and has no alias. This contract does
not create a generic registry service.

Operation Requirement, Runtime Operation Capability Observation, and
Environment Operation Permission Observation consume one package-internal Core
source of truth for this syntax and supported vocabulary. The capability and
permission-observation contracts are defined separately in
`core/runtime-operation-capability-specification.md` and
`core/environment-operation-permission-specification.md`. Sharing the
vocabulary does not change this contract's demand-only meaning, public
findings, messages, validation order, or result semantics.

---

## 4. Resource Contract

`resource` is one exact lexical repository-relative path. Its separator is the
literal forward slash `/`. Repository root identity remains external,
caller-owned context and is never an input to this contract.

The resource grammar rejects, in the fixed precedence shown:

1. the empty string;
2. control code points U+0000-U+001F or U+007F-U+009F, including NUL;
3. a UNC prefix, exactly `//` or `\\`;
4. any other leading `/` absolute path;
5. a leading ASCII letter plus `:`, including drive-relative and
   drive-absolute forms;
6. a start-of-string URI scheme matching `[A-Za-z][A-Za-z0-9+.-]*:` after the
   drive check;
7. a leading `~`;
8. any backslash;
9. a trailing `/`;
10. any remaining empty slash-separated segment;
11. an exact `.` segment;
12. an exact `..` segment; and
13. any glob/meta character from the exact set `*?[]{}`.

At most the first matching resource finding is emitted. Everything not excluded
above remains opaque and exact, including case, Unicode, spaces, punctuation,
dots inside non-dot segments, extensions, and extensionless names. A colon
after a slash is permitted when it cannot form a start-of-string drive or URI
prefix.

The contract is extension-neutral. In particular, it has no Markdown-only
restriction. One requirement identifies one resource; callers represent
multiple resources with multiple values.

The canonical first-issue resource validation is implemented once in the
package-internal `engineering_orchestration._repository_resource` helper and is
also consumed by Environment Operation Permission Observation validation. The
helper extraction preserves every Operation Requirement resource code, message,
precedence rule, public API, and atomic result exactly.

---

## 5. Lexical-Only and No-I/O Boundary

Resource validation operates only on supplied string characters. It never:

- opens, reads, writes, stats, hashes, or existence-checks a path;
- resolves a path or consults a current working directory or repository root;
- lists a directory or expands a glob;
- interprets a symlink, junction, mount, or filesystem case behavior;
- discovers capabilities, permissions, environment state, or credentials;
- uses a network, subprocess, clock, cache, database, or persistent store.

Lexical validity does not prove that the resource exists, is a file, remains
inside a physical repository after link traversal, or can be accessed. Those
facts are deliberately outside this value contract.

---

## 6. Validation and Deterministic Findings

`validate_operation_requirement` validates one supplied object in this order:

1. exact `OperationRequirement` value type;
2. exact string field types, `operation_id` before `resource`;
3. operation identifier syntax;
4. supported operation vocabulary; and
5. resource lexical grammar.

If the value type is wrong, only `operation_requirement_invalid_type` is
returned. Field-type findings are `operation_id_invalid_type` followed by
`resource_invalid_type`; semantic validation does not cascade past invalid
field types. A malformed operation produces `operation_id_invalid_syntax` and
is not support-checked. An unknown well-formed operation produces
`operation_id_not_supported`.

Resource findings use this exact ordered taxonomy:

```text
resource_empty
resource_control_character
resource_unc_path
resource_absolute_path
resource_drive_qualified_path
resource_uri_scheme
resource_leading_tilde
resource_backslash
resource_trailing_slash
resource_empty_segment
resource_dot_segment
resource_parent_segment
resource_glob_meta
```

An operation finding always precedes a resource finding. Fixed codes, fixed
messages, and fixed precedence make validation deterministic.

---

## 7. Result Atomicity and Immutability

Runtime values are frozen dataclasses and findings are tuples. A valid result
has:

```text
valid: true
findings: ()
requirement: the exact supplied OperationRequirement object
```

An invalid result has:

```text
valid: false
findings: one or more deterministic findings
requirement: null
```

There is no partial validated value, correction, deduplication, normalization,
or mutation of the caller's object.

---

## 8. Missing Semantics

Presence means only:

```text
the caller declared this operation/resource requirement
```

Absence means only:

```text
no requirement was supplied in this evaluation context
```

Absence does not mean unnecessary, forbidden, unsupported, permitted,
authorized, unavailable, or incapable. No negative requirement state exists.

---

## 9. Structural and Semantic Authority

The machine-readable structural schema is:

`schemas/operation-requirement.schema.json`

It validates one object with exactly the two required nonempty string fields
and rejects additional properties. It intentionally contains no operation enum
or pattern and no resource-path format or pattern.

This specification is the semantic authority. The pure runtime validator owns
exact type robustness, operation syntax and support, lexical resource grammar,
finding order, and result atomicity. A value may therefore be structurally
valid while semantically invalid.

---

## 10. Ownership and Association

Ownership remains:

```text
Framework/Core
-> operation meaning, identifier syntax, resource grammar, validation

Caller/planner
-> declaration truth, repository evaluation context, external association
   with a Task, candidate, plan, or other evaluation subject
```

Operation Requirement is standalone caller-supplied evidence. It is not a
field on Task, Assignment, Runtime Option, or Agent Execution Candidate. A
requirement may exist before any candidate. A separate Runtime Operation
Capability Observation may exist for an operation that is not currently
required, and a requirement may exist when Runtime capability is unknown. A
separate Environment Operation Permission Observation may likewise exist
independently; it supplies an environment-scoped permission fact for one exact
Runtime, operation, and resource and neither creates nor satisfies a
requirement.

Agent Execution Authorization Evidence may independently refer to the same
exact operation and lexical resource as part of a larger assigned-action
subject. A requirement neither creates that evidence nor becomes authorized by
its presence. Authorization evidence is caller-attested and does not create or
satisfy an Operation Requirement. Its separate contract is defined in
`core/agent-execution-authorization-evidence-specification.md`.

Agent Action Prerequisite Assessment may validate exactly one Operation
Requirement and join its exact operation/resource identity with independently
validated candidate, capability, permission, and authorization results. That
derived diagnostic composition does not change this demand-only contract and
is defined in `core/agent-action-prerequisite-specification.md`.

Agent Execution Contract intrinsic validation projects its `operation_id` and
`resource` through this validator, and canonical preparation copies the same
exact pair from one coherent satisfied Agent Action Prerequisite Assessment.
Embedding the pair in declarative intent does not create or consume a
requirement, access the resource, bind a tool, preserve prerequisite freshness,
or establish capability, permission, authorization, readiness, or execution.
That separate contract is defined in
`core/agent-execution-contract-specification.md`.

---

## 11. Runtime and Package API

Immutable values and pure validation are defined in:

`engineering_orchestration.operation_requirement`

The submodule exposes:

- `OperationRequirement`
- `OperationRequirementFinding`
- `OperationRequirementValidationResult`
- `validate_operation_requirement`

The result fields are exactly `valid`, `findings`, and `requirement`. The package
root does not re-export these names. The structural schema is a packaged schema
resource.

Operation syntax and support are implemented through the package-internal
`engineering_orchestration._operation_vocabulary` helper shared with Runtime
Operation Capability and Environment Operation Permission Observation
validation. Resource grammar is implemented through the package-internal
`engineering_orchestration._repository_resource` helper shared with Environment
Operation Permission Observation validation. These internal helpers do not
change the public Operation Requirement API or behavior.

---

## 12. Exclusions

The first contract contains no:

- requirement ID, Task, Workflow, Stage, Role, Actor, Runtime, Inference,
  environment, state, source, reason, timestamp, expiry, metadata, or extension
  field;
- negative requirement state, completeness claim, or inferred requirement;
- capability, supported-tool, availability, permission, authorization,
  approval, policy-decision, or credential semantics;
- tool name, Provider binding, adapter, filesystem implementation, or command;
- Task schema, Assignment, candidate, Runtime Option, or Project Manifest
  change;
- registry, discovery, persistence, cache, database, CLI, Execution Contract,
  request, dispatch, execution, or invocation.

The Agent Execution Contract and any future action-layer contract may refer to
this exact operation/resource pair only while preserving its need-only and
lexical-only meaning.
