# AIO-017 Context

## Context Completion

1. Change: extract a small read-only installed structural API and share Manifest
   Task path resolution across inventory, inspection, and structural validation.
2. Reason: managed projects should not copy Orchestra regression harnesses to
   validate their AIO data. The Manifest already owns Task-directory configuration.
3. Preserve: seven-check development preflight, schema semantics, declared IDs,
   caller-based root discovery, source wrappers, and historical Task artifacts.
4. Rules: Core principles, precedence, context completion, Manifest path contract,
   standard-change, software-engineer, reviewer, and both required gates apply.
   No Project Rules currently exist in the configured rules directory.
5. Evidence: full regressions, installed external-project validation with custom
   Task paths, typed failure evidence, package isolation, and separate review.
   The initial instruction required stopping at the Human checkpoint with status
   in_progress and no commit. Explicit Human approval on 2026-09-17 subsequently
   authorized completion and the closure commit; see review.md.

## Boundaries and Ownership

The seven development checks are Python unittest discovery, four schema regression
harnesses, Markdown lint, and Git diff whitespace checks. They remain mandatory
Orchestra development evidence. Only schema evaluation and declared identity /
Workflow-reference checks are portable. Fixtures, negative-error registries,
template checks, schema self-tests, and historical coverage remain development tests.

The target owns its Manifest, configured Task directory, and workflows/ YAMLs.
The tool owns canonical Task, Workflow, and Manifest schemas. Packaging uses the
existing explicit resource mapping from canonical schemas/ into the private
resource package. A normal installation never consults a checkout for resources;
the existing uninstalled source-wrapper compatibility path remains tool-local.
Task paths default to .ai/tasks/ only when omitted, per the existing Manifest
contract. Directory names do not define identity. Workflow paths are not configurable.

Role Markdown extraction is test-only under core/role-specification.md. Portable
Role project validation is outside coverage; no Role schema resource or new
representation is needed. Structural PASS never establishes either required gate.
The API reads data only, without commands, Git, Node, test discovery, lifecycle
selection, stage state, result persistence, or mutation.

## Product Decision and Future Evidence

Use validate_project(start=None) in engineering_orchestration.validation; keep
results separate from formatting. No new CLI command is needed to prove installed
operation. PASS means supported rules conform; FAIL means project data does not;
ERROR means evaluation could not finish correctly. No SKIP state is introduced.

The eventual intended verify direction is structural validation followed by
project-declared mechanical checks. Only the prerequisite structural capability is
implemented here. A later Task would need to separately establish command IDs,
argument arrays, shell=False, cwd containment, timeout, trust, Windows behavior,
and execution authority. This evidence does not authorize those mechanisms now.
