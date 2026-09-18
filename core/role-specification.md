# AI Engineering Orchestra - Role Specification

Version: 0.1.0

This document defines the canonical Role contract for AI Engineering Orchestra v0.1.

---

## 1. Purpose

A Role is a reusable, provider-independent description of an engineering responsibility and the abstract competencies required to perform it.

A Role describes what responsibility is required. It does not select, authorize, configure, or control the actor that fulfils the Role.

Canonical Role instances are framework-owned and maintained as YAML in:

`roles/*.yaml`

Projects may reference their IDs, but AIO-022 defines no project Role directory,
custom Role, extension, override, or precedence mechanism.

---

## 2. Architectural Boundary

The following concepts remain separate:

- **Role**: the declarative responsibility and required competencies.
- **Actor**: a concrete, identifiable Human or Agent candidate that may fulfil a
  Role, as defined by `core/actor-specification.md`.
- **Agent**: the AI Actor kind; Agent identity does not imply current execution.
- **Human**: the Human Actor kind; Human approval authority remains governed by
  Human Control.
- **Task**: the scoped work that must be performed.
- **Workflow**: the ordered stages used to complete a class of Task.
- **Provider or Model**: implementation technology behind an Agent.
- **Quality Gate**: a condition that must pass before work may progress.
- **Policy and Human Control**: authority, permission, protection, and approval requirements.
- **Assignment Contract**: the responsibility-binding contract that records a
  caller-selected eligible Actor for a required Role.
- **Execution Contract**: a future contract that may define how an assigned actor performs work.

A Role may be relevant to a Task without being assigned to it. A Role may be fulfilled by an Agent or Human without identifying which actor is selected.

---

## 3. Canonical Role Contract

The v0.1 Role contract contains these fields:

| Field | Required | Purpose |
| --- | --- | --- |
| `id` | Yes | Stable machine-readable Role identifier |
| `name` | Yes | Human-readable Role name |
| `purpose` | Yes | Concise statement of the Role responsibility |
| `responsibilities` | Yes | Declarative responsibilities associated with the Role |
| `required_capabilities` | Yes | Stable abstract engineering competencies required by the Role |
| `applicable_task_types` | No | Task categories for which the Role is commonly suitable |

These fields are descriptive. They do not by themselves assign, authorize, or execute work.

### `id`

`id` is the stable machine-readable identity of the Role.

Example:

```text
software-engineer
```

It should remain stable after the Role is established.

### `name`

`name` is the human-readable name of the Role.

Example:

```text
Software Engineer
```

### `purpose`

`purpose` briefly explains the responsibility represented by the Role.

It should describe an engineering outcome or responsibility rather than a personality, instruction prompt, or implementation technology.

### `responsibilities`

`responsibilities` lists the reusable engineering responsibilities associated with the Role.

Responsibilities should be expressed as stable, declarative responsibility identifiers or concise responsibility statements.

Examples:

- `implement-software`
- `validate-changes`
- `report-evidence`
- `evaluate-acceptance-criteria`

Responsibilities do not define Task scope, Workflow sequencing, execution commands, permissions, or approval authority.

### `required_capabilities`

`required_capabilities` lists the stable abstract engineering competencies required to fulfil the Role.

Examples:

- `software-implementation`
- `source-code-analysis`
- `architecture-analysis`
- `requirements-analysis`
- `automated-testing`
- `security-analysis`
- `documentation-analysis`
- `evidence-evaluation`

Capability identifiers SHOULD describe stable engineering competencies rather than implementation mechanisms or individual runtime operations.

The following are not Role capabilities:

- `repository-read`
- `repository-write`
- `shell-execution`
- `read-file`
- `write-file`
- `run-dotnet-test`
- `call-api`
- `create-branch`

Those concepts belong to future runtime/tooling or execution contracts, or to
Policy as applicable.

Required capabilities describe what the Role requires. They do not describe which capabilities an actor possesses.

### `applicable_task_types`

`applicable_task_types` identifies Task categories for which a Role is commonly suitable.

It is advisory and descriptive. It SHALL NOT by itself assign the Role, authorize execution, prohibit other use, or grant eligibility to an actor.

Actual responsibility binding belongs to the Assignment Contract. The Assignment
contract does not automatically match, rank, or select Actors.

A Role may be used for a Task type not listed when the applicable Assignment Contract, Policy, Workflow, and Human control requirements permit it.

---

## 4. Normative Role Invariants

The following requirements apply to every Role:

1. A Role is declarative and SHALL NOT be directly executable.
2. A Role SHALL NOT identify, configure, instantiate, or control the Agent or Human fulfilling it.
3. A Role SHALL NOT contain prompts, personas, model instructions, or runtime behavior.
4. A Role SHALL NOT grant runtime permissions.
5. Capability does not imply authority. An actor being technically capable of an action does not mean it is authorized to perform that action.
6. Role eligibility does not grant execution permission or approval authority.
7. A Role does not own Task scope, objectives, dependencies, acceptance criteria, results, or lifecycle status.
8. A Role does not own Workflow sequencing, stages, transitions, or Execution Mode.
9. A Role does not decide whether a Human or Agent fulfils it.
10. `required_capabilities` describe required engineering competencies, not possessed actor capabilities or runtime tools.
11. Approval, escalation, assignment, separation of duties, and runtime execution remain external concerns.
12. `applicable_task_types` is advisory and does not perform assignment or authorization.
13. A Role is Provider- and model-independent.
14. A Role does not grant filesystem, shell, network, API, deployment, or other operation permissions.
15. A Role must not be interpreted as a system prompt or Agent persona.

---

## 5. Ownership and Precedence

Role definitions must operate within the precedence model in `core/precedence.md`.

Role instructions are lower precedence than applicable Policies, Task requirements, Project Rules, and Workflow Rules. A Role cannot weaken a protected requirement.

Role definitions must not duplicate canonical content owned by:

- `core/task-specification.md`
- `core/project-manifest.md`
- `core/human-control.md`
- `core/context-policy.md`
- `workflows/`
- `quality-gates/`
- Provider Adapters or future runtime contracts

The absence of a Role field does not imply permission. Permission and authority must be established by the applicable Policy, Project configuration, Task, Workflow, Human Control, and future execution mechanisms.

---

## 6. External Fulfilment Boundary

The Role contract is intentionally suitable for different Actors and future
runtimes:

```text
AIO Role
  -> fulfilled by an Actor
       -> Human
       -> Agent
            -> may be supplied by a Provider
            -> may execute in a future runtime
```

AIO-006 defines no adapters, integrations, Actor assignment, or execution
behavior. The canonical Actor contract and pure competency coverage semantics
are defined separately in `core/actor-specification.md`.

---

## 7. Relationship to Workflows, Actors, and Tasks

A Task continues to own the work that must be performed.

Workflows may identify multiple Role requirements for engineering work, such as:

- implementation -> Software Engineer
- architecture review -> Architect
- security review -> Security Reviewer
- independent review -> Reviewer

Workflow stages reference canonical Role IDs through `required_roles`. The
framework Role catalog resolves those IDs to Role objects, and the pure Actor
coverage evaluator can compare a caller-supplied Actor with a resolved Role.
That result is eligibility evidence only. The Assignment Contract records a
caller-selected Actor binding, requires compatible coverage, rejects duplicate
responsibility bindings, and reports only its established narrow reviewer identity
conflict. Automatic selection and availability remain outside that contract.

The Task schema is not changed by this specification.

---

## 8. Initial Role Library

The initial reusable Roles are:

- Architect
- Software Engineer
- Reviewer
- Security Reviewer
- Documentation Specialist

These Roles are responsibility and capability contracts. They are not personas, Agents, providers, permissions, or approval authorities.

Human Approver is not an ordinary canonical engineering Role. Human approval remains governed by `core/human-control.md`.

---

## 9. Validation Status in v0.1

Role authority is deliberately ordered as follows:

1. `core/role-specification.md` is the semantic authority.
2. `schemas/role.schema.json` is the structural authority and is semantically
   subordinate to this specification.
3. `roles/*.yaml` contains the canonical Role instances.
4. `roles/*.md` contains non-authoritative compatibility/documentation stubs.
5. `schemas/tests/validate_role.py` is development regression tooling only.

A machine-readable JSON Schema for normalized Role objects is available at:

`schemas/role.schema.json`

Canonical Role YAML resources and the Role schema are packaged from those
Sources of Truth for `engineering_orchestration.role_catalog`. The catalog uses
package-safe resource access, validates each parsed object, indexes by declared
`id`, and does not consult CWD or an active project's `roles/` directory.

Repository-local regression tooling is available at:

`schemas/tests/validate_role.py`

Representative valid and invalid fixtures are available under:

`schemas/tests/role/`

### Architectural Boundary of Role Loading and Validation

`schemas/role.schema.json` defines structural validity for parsed Role objects.
Canonical YAML definitions are validated directly, without Markdown extraction
or a generated projection. Markdown compatibility stubs contain no Role contract
data and must not be parsed by runtime or validation tooling.

The Role catalog performs data access and validation only. It does not evaluate
Actor coverage, choose or rank Actors, create Assignments, inspect availability,
authorize or execute work, or evaluate Quality Gates. Actor coverage remains the
separate responsibility of `engineering_orchestration.actor_coverage`.

### Structural vs Semantic Validity

Schema-valid does not imply semantically valid, useful, recommended, or review-approved.

The Role schema validates structural shape (required fields, scalar types, array container types). It deliberately does not enforce unapproved semantic constraints such as array minimum lengths, array uniqueness, identifier regexes, or capability vocabulary enums.

Semantic review remains responsible for determining whether Role responsibilities and capabilities satisfy the AIO-006 contract.
