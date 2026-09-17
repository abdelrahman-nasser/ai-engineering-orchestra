# AIO-022 Context

## Current limitation and objective

Workflow stages already declare Role IDs, and AIO-021 can compare a normalized
Role with a supplied Actor, but Role instances exist only in Markdown. The only
machine-readable conversion is a test-only extractor in the Role schema
validator. Runtime code therefore cannot resolve a Workflow Role reference to
its required competencies.

AIO-022 replaces that gap with canonical packaged YAML Role instances and a
concrete framework-owned Role catalog. The resulting composition is Workflow
stage Role ID to Role catalog to required competencies to the existing pure
Actor coverage evaluator. The result is eligibility evidence only.

## Representation and authority decision

The representation decision is locked: YAML is canonical and Markdown is
compatibility-only. Authority descends from `core/role-specification.md` as the
semantic contract, to `schemas/role.schema.json` as structural authority, to
`roles/*.yaml` as canonical instances, to `roles/*.md` as non-authoritative
compatibility stubs. `schemas/tests/validate_role.py` remains regression tooling.

The five YAML instances preserve the exact approved names, purposes,
responsibilities, required capabilities, and applicable Task types from the
former Markdown definitions. The existing schema represents those objects
without change, and the nine-identifier competency vocabulary remains unchanged.

## Historical compatibility

All five historical `roles/*.md` paths remain. Each is reduced to a minimal stub
that links to its authoritative YAML counterpart without duplicating Role
contract content. Historical AIO-001 through AIO-021 artifacts remain untouched.

## Framework ownership and packaging

Roles are framework-owned. The Role schema and canonical YAML instances are
mapped directly from their canonical source directories into private installed
resource packages. Runtime loading uses package-safe resource access anchored to
the tool, never CWD or the active project. An adopter's own `roles/` directory is
ignored; there is no override, extension, precedence, or Project Manifest field.

## Runtime catalog and Workflow integration

The concrete Role catalog safe-loads YAML, requires object roots, validates each
object with the packaged Role schema, rejects duplicate declared IDs, and indexes
by the declared `id`, not filename. It provides deterministic ID enumeration and
unknown lookup returns `None`. Missing or corrupt framework resources are
distinguished as infrastructure failures.

Portable validation resolves every schema-valid Workflow `required_roles`
reference through the framework catalog. An unknown reference is adopter data
and produces `FAIL`. A broken framework catalog produces one catalog-level
`ERROR` and suppresses misleading per-reference cascades. Role existence remains
semantic cross-resource validation and does not change the Workflow schema.

## Scope and completion evidence

The Task does not add Assignment, Actor inventories, availability, selection,
ranking, Provider/model/runtime fields, permissions, execution, Role CLI, custom
project Roles, a capability registry, or a generic catalog abstraction. The
Actor schema and coverage evaluator remain unchanged; empty Role requirements
still load when schema-valid and remain non-matchable in the evaluator.

Completion evidence consists of focused Role catalog and Workflow-reference
tests, standalone schema validators, full repository verification, Markdown and
diff checks, editable and normal-wheel installation smoke tests, and genuinely
separate reviewer and architect approval. The `architecture-change` Workflow
governs the Task. Explicit Human approval was recorded on 2026-09-18, authorizing
Task closure and the approved AIO-022 commit without creating AIO-023.
