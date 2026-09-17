# AIO-022 Acceptance Criteria

- [x] Exactly five canonical `roles/*.yaml` instances preserve the approved Role
  fields, values, list ordering, and nine-identifier competency vocabulary.
- [x] `core/role-specification.md` remains semantic authority,
  `schemas/role.schema.json` remains unchanged structural authority, YAML is
  canonical instance authority, and Markdown is compatibility-only.
- [x] All five historical Role Markdown paths remain as minimal stubs linking to
  their YAML counterparts without duplicated contract semantics.
- [x] A concrete framework-owned Role catalog loads package-safe YAML resources,
  validates them with the packaged schema, indexes by declared ID, rejects
  duplicates, and enumerates IDs deterministically.
- [x] Unknown Role lookup returns `None`; filenames do not define identity; no
  runtime Markdown parser, generated projection, or generic catalog framework is
  introduced.
- [x] The installed package contains the Role schema and five canonical Role YAML
  resources directly from their Sources of Truth without checkout or CWD fallback.
- [x] Portable validation reports unknown Workflow Role references as `FAIL` and
  a broken framework Role catalog as one infrastructure `ERROR` without cascades.
- [x] External project Role directories are ignored, Workflow and Role schemas
  remain unchanged, and `applicable_task_types` remains advisory.
- [x] Loaded Roles compose unchanged with Actor coverage for Human and Agent
  candidates, including missing-competency and empty-requirement behavior.
- [x] No Assignment, Actor catalog, Role override, Provider/model/runtime concept,
  execution behavior, Role CLI, capability registry, or AIO-023 is added.
- [x] Full unit, standalone schema, repository, packaging, Markdown, and Git diff
  validation pass or any failure or skip is recorded.
- [x] Separate reviewer and architect reviews approve the actual change and the
  `documentation_consistency` and `independent_review` Gates pass.
- [x] Human approval is recorded before the Task is marked `completed` or any
  commit is created.
