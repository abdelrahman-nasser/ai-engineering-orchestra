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
- established the architectural boundary between structural schema validation, canonical Markdown definitions, and semantic review

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
