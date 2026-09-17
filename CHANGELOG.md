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
