# Changelog

All notable changes to AI Engineering Orchestra will be documented in this file.

The format follows Semantic Versioning concepts.

---

## [0.1.0] — Foundation

Status: In Development

### Added

- initial repository structure
- canonical terminology
- core engineering principles
- Rule and Policy precedence model
- project lifecycle model
- progressive context loading policy
- Human control model
- root `AGENTS.md`
- initial `.ai/project.yaml`
- self-hosted Orchestra Task structure
- initial project documentation
- canonical Quality Gate definitions for `documentation_consistency` and `independent_review`
- canonical Project Manifest specification in `core/project-manifest.md`
- reusable Project Manifest template in `templates/project.yaml`
- machine-readable Project Manifest JSON Schema in `schemas/project-manifest.schema.json`
- Project Manifest schema validation fixtures and test tooling in `schemas/tests/`
- canonical Task specification in `core/task-specification.md`
- reusable canonical Task template in `templates/task/`
- machine-readable Task JSON Schema in `schemas/task.schema.json`
- Task schema validation fixtures in `schemas/tests/task/`
- repository-local Task schema validation tooling in `schemas/tests/validate_task.py`
- canonical Role specification in `core/role-specification.md`
- initial canonical engineering Role library in `roles/`
- machine-readable Role JSON Schema in `schemas/role.schema.json`
- Role schema validation fixtures in `schemas/tests/role/`
- repository-local Role schema validation tooling in `schemas/tests/validate_role.py`
- canonical machine-readable YAML Role instances with historical Markdown
  compatibility stubs
- package-safe runtime Role catalog and packaged Role schema/instance resources
- semantic Workflow-to-Role reference validation using framework-owned Roles
- canonical five-field Assignment responsibility-binding specification and schema
- pure individual and sequence Assignment validation with competency reuse,
  duplicate-binding detection, completeness, unassigned-requirement reporting,
  and narrow implementer/Reviewer identity-conflict evidence
- canonical two-field Actor Availability Observation specification and schema
- immutable availability values and pure snapshot validation with explicit
  unknown normalization and deterministic duplicate handling
- canonical Actor Selection specification and pure deterministic runtime
  resolution with selected, ambiguous, indeterminate, and no-candidate outcomes
- immutable Actor-ID selection evidence composed from existing competency
  coverage and normalized availability, without ranking or Assignment creation
- immutable canonical Execution Mode order and pure minimum-satisfaction helper
  with schema-synchronization, relation, inheritance, and Workflow-invariance tests
- canonical three-field Inference Option Definition specification and schema,
  with opaque option, Provider, and Provider-scoped model identity
- canonical two-field Inference Option Availability Observation specification
  and schema with explicit unknown normalization
- immutable Inference Option values and pure deterministic inventory and
  availability validation, including duplicate and unknown-reference handling
- canonical one-field Agent Runtime Option Definition specification and schema,
  with opaque caller/environment-supplied execution-surface identity
- canonical two-field Agent Runtime Option Availability Observation
  specification and schema with explicit unknown normalization
- immutable Agent Runtime Option values and pure deterministic inventory and
  availability validation, including duplicate and unknown-reference handling
- canonical two-field Actor-to-Runtime Applicability Evidence specification and
  schema for a separate positive Agent-only many-to-many relation
- pure deterministic applicability validation with captured one-shot inputs,
  reused Runtime inventory validation, Agent-only Actor endpoints, stable
  diagnostics, canonical pair ordering, and atomic invalid results
- canonical two-field Runtime-to-Inference Compatibility Evidence specification
  and schema for separate positive many-to-many support edges
- pure deterministic compatibility-relation validation that reuses both
  endpoint inventory validators and rejects duplicate or unknown-reference
  input atomically
- canonical Runtime-to-Inference Pair Availability Assessment specification
  and immutable pure API with exhaustive three-state endpoint composition
- deterministic compatibility-first validation, atomic converted diagnostics,
  and one pair-sorted assessment per supplied positive compatibility edge
- canonical Agent Execution Candidate Prerequisite Assessment specification and
  immutable pure API for one explicit Assignment, Runtime Option, and Inference
  Option candidate, with `satisfied`, `blocked`, and `unresolved` outcomes
- capture-once composition of Assignment, Actor availability,
  Actor-to-Runtime applicability, and pair availability with deterministic
  reasons, atomic invalid findings, and explicit Human non-applicability
- canonical two-field Operation Requirement specification and schema for one
  Core-defined abstract operation against one exact lexical
  repository-relative resource
- immutable Operation Requirement values and pure deterministic semantic
  validation for operation syntax/support and extension-neutral resource
  grammar, with atomic findings and no filesystem access or normalization
- canonical three-field Runtime Operation Capability Observation specification
  and schema for Runtime/Core-operation technical-support states
- immutable capability observations and pure deterministic snapshot validation
  with `present`, `absent`, and `unknown`, full missing-pair unknown
  normalization, duplicate/reference rejection, pair ordering, and atomic
  invalid results
- one package-internal Core operation vocabulary shared by Operation
  Requirement, Runtime Operation Capability, and Environment Operation
  Permission Observation validation without changing AIO-036 or AIO-037 public
  behavior
- canonical five-field Environment Operation Permission Observation
  specification and schema for exact Runtime-, environment-, operation-, and
  lexical-resource-scoped `allowed`, `denied`, and `unknown` evidence
- immutable permission observations and pure deterministic snapshot validation
  with Runtime inventory and environment-scope checks, canonical supplied-only
  ordering, mutually exclusive duplicate/conflict findings, and atomic invalid
  results
- one package-internal lexical repository-resource validator shared by
  Operation Requirement and Environment Operation Permission Observation
  validation while preserving AIO-036 public codes, messages, precedence, API,
  and behavior
- canonical fourteen-field Agent Execution Authorization Evidence specification
  and schema for caller-attested `human` or `policy` assertions about one exact
  assigned external-inference Agent action
- immutable authorization evidence and pure deterministic validation with exact
  Assignment, Runtime, Inference, environment, operation, and lexical-resource
  checks; mutually exclusive conflict, multi-authority, and duplicate handling;
  canonical supplied-only output; and atomic invalid results
- explicit separation of authorization evidence from authenticated authority,
  Task approval, Assignment, candidate satisfaction, capability, environment
  permission, Permission Decision, lifecycle, enforcement, and execution
- private controlled read-only execution preparation dry run for the single
  provisional `repository_file_read` operation and one exact canonical
  repository-relative Markdown resource
- separate caller-supplied capability, environment-permission/freshness, and
  Human/policy authorization evidence with exact scope matching,
  deterministic `potentially_executable`, `blocked`, and `unresolved` results,
  and lexical resource validation without target access
- canonical Workflow specification in `core/workflow-specification.md`
- initial canonical engineering Workflow library in `workflows/` (`standard-change`, `architecture-change`, `security-sensitive-change`)
- normalized Workflow JSON Schema in `schemas/workflow.schema.json`
- registered Workflow fixtures and strict repository-local Markdown projection tests in `schemas/tests/validate_workflow.py`

### Architecture

- established Provider-independent Core
- separated Providers from engineering Roles
- established explicit Sources of Truth
- introduced Risk and Complexity as separate concepts
- introduced Execution Modes
- established progressive context loading
- established Human authority and approval concepts
- defined the canonical Project Manifest contract and structural validation model
- defined the canonical Task contract and Task directory responsibilities
- defined Task lifecycle and closure semantics
- defined Task scope, Project-default inheritance, Quality Gate requirements, and Human control behavior
- established persistent Task review and approval evidence
- registered the Project Manifest and Task contracts as repository Sources of Truth
- established machine-readable structural validation for the canonical Task contract
- documented the boundary between structural Task validation and repository-level or historical Task semantics
- defined the canonical Role contract separating abstract engineering responsibilities and competencies from runtime agents, providers, permissions, and authority
- established machine-readable structural validation for normalized Role objects
- separated Actor eligibility from immutable Assignment responsibility binding,
  authority, availability, execution, Workflow state, and Quality Gate results
- separated ephemeral Actor availability observations from Actor identity,
  competency eligibility, Assignment validity, authority, execution, Provider
  state, persistence, and selection
- separated deterministic Actor Selection decision evidence from Assignment,
  authorization, reservation, execution, Quality Gate results, Provider/model
  routing, persistence, and Selection Policy
- defined Execution Mode as a Provider-neutral, Task-wide minimum engineering
  posture ordered `lite < standard < deep < critical`, with higher modes
  satisfying lower minimums
- separated Complexity, Risk, and Execution Mode from automatic Workflow,
  Provider/model, authority, approval, and Quality Gate mappings
- established that mode changes depth inside unchanged Workflow choreography and
  provides no Stage-, Role-, or responsibility-specific override
- deprecated the mixed-axis Model Tier values as non-consumable, with no
  replacement tier, capability scale, reasoning mapping, or routing behavior
- separated caller-supplied Inference Option identity from model identity,
  Runtime Option, Agent Service, capabilities, credentials, selection,
  authorization, and invocation
- separated ephemeral Inference Option availability from static option identity,
  with `unknown != unavailable` and no implication of runtime availability,
  Execution Mode fit, quota, selection, authorization, or execution
- separated Agent Runtime Option execution-surface identity from Actor,
  executable Agent definition, execution instance, Inference Option, Agent
  Service, authorization, credentials, and invocation
- separated ephemeral Agent Runtime Option availability from static Runtime
  Option identity, with `unknown != unavailable` and no implication of Actor or
  Inference compatibility, selection, capacity, authorization, or execution
- established caller-scoped Runtime Option inventories without Actor mappings,
  project persistence, runtime type enums, or capability fields
- established a separate positive Actor-to-Runtime applicability relation
  without changing Actor, Runtime Option, Selection, Assignment, availability,
  Task, Execution Mode, permission, authority, or invocation contracts
- established that a missing Actor-to-Runtime edge means no supplied positive
  applicability evidence, not incompatibility, unavailability, prohibition, or
  non-executability
- separated positive Runtime-to-Inference Compatibility Evidence from endpoint
  Definitions, all availability contracts, Actor mapping, configuration
  viability, selection, authority, execution, and invocation
- established that an absent compatibility edge means no supplied positive
  external evidence, not explicit incompatibility or non-executability, while
  preserving Runtime-owned inference without synthetic edges
- composed compatibility and normalized endpoint availability into bounded
  `established`, `blocked`, and `unresolved` per-edge evidence without adding
  configuration viability, selection, authority, execution, or a new schema
- composed existing responsibility, availability, applicability, and pair
  evidence for one caller-designated external-inference Agent candidate without
  adding a Candidate entity, Actor-to-Inference relation, selection,
  authorization, Execution Contract, invocation, or schema
- established that assessment `satisfied` means only that currently modeled
  hard prerequisites are positive, while missing positive evidence remains
  `unresolved` and explicit unavailability dominates as `blocked`
- kept the AIO-035 preparation experiment private and non-invoking: it consumes
  evidence without discovering or changing permissions, parsing approval prose,
  touching the target, creating an Execution Contract, dispatching, or adding a
  public export, CLI, schema, adapter, or stable Core contract
- preserved capability, environment permission, and Human/policy authorization
  as independent facts; only exact, current positives in every required
  dimension produce the cautious `potentially_executable` diagnostic
- separated Runtime operation capability from Runtime identity, Operation
  Requirement, Runtime availability, resource permission, Human/policy
  authorization, tool binding, discovery, dispatch, and execution
- established that missing Runtime/Core-operation observations normalize to
  unknown while explicit non-support remains absent, with both states remaining
  distinct for future composition
- separated Environment Operation Permission Observation from requirement,
  Runtime capability and availability, Permission Decision, Human/policy
  authorization, enforcement, mutation, dispatch, and execution
- established opaque caller-owned environment scope and exact
  Runtime/environment/operation/resource identity without an Environment
  Definition, registry, freshness field, discovery, polling, or native-state
  verification
- established that missing exact permission evidence means unknown without
  Cartesian synthesis, while valid snapshots preserve only supplied observations
  in canonical exact-identity order
- established identical repeated permission evidence and differing-state
  conflicts as mutually exclusive invalid-input categories; conflicts invalidate
  the entire snapshot without first-, last-, latest-, allowed-, deny-, or
  stricter-wins resolution and remain caller/environment-owned for reconciliation
- established the Role authority hierarchy from semantic specification to
  structural schema, canonical YAML instances, compatibility Markdown, and
  regression tooling
- defined the canonical Workflow contract establishing declarative governance choreography stages, canonical Role references, Quality Gate composition semantics, Human Control checkpoint boundaries, and external-runtime delegation boundaries
- established Quality Gate three-source composition (Project ∪ Workflow ∪ Task) and non-weakening invariant
- defined non-blocking Human Control checkpoint evaluation semantics
- established the architectural boundary between declarative AIO governance choreography and executable workflow runtimes
- added structural Workflow validation subordinate to the approved specification, with separately labelled repository semantic ID-uniqueness checks; no runtime serialization or automatic Workflow selection is introduced

### Reserved for v0.2

- Brownfield deep onboarding
- repository health analysis
- technical-debt prioritization
- safe phased refactoring
- command permission enforcement
- allow / ask / always-ask / deny policies
- command audit controls

### Reserved for Later Versions

- Stack Modules
- Provider Adapters
- automatic model routing
- quota-aware fallback
- Agent spawning control
- CLI tooling
- package distribution
