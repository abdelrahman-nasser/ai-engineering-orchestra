# AIO-007 — Context

## Objective

AIO-007 defines the structural schema for normalized Role objects in AI Engineering Orchestra v0.1.

The canonical Role specification was established in `core/role-specification.md` under AIO-006. AIO-007 provides machine-readable JSON Schema validation and repository-local test coverage without extending or altering the AIO-006 contract.

## Architectural Boundaries and Clarifications

### Clarification 1 — Schema vs Serialization Format

`schemas/role.schema.json` defines the structural schema of a **normalized Role object**.

AIO-007 does NOT define Markdown as a public machine-readable Role serialization format.

The existing canonical Role definitions remain Markdown.

The Markdown extractor implemented for repository validation is:

- test-only,
- repository-local,
- intentionally minimal,
- limited to the current canonical Role document structure,
- unable to infer missing values,
- unable to supply defaults,
- strict about duplicate or ambiguous sections,
- visibly failing when extraction cannot be performed safely.

The extractor is not exposed as a public Role parser, library, CLI contract, or runtime serialization mechanism.

> AIO-007 validates a normalized in-memory projection of the current canonical Markdown Role definitions. It does not establish Markdown as the future runtime Role serialization format.

A future task may separately decide the runtime/persistence representation of Role instances.

### Clarification 2 — Structurally Valid vs Semantically Recommended

The schema enforces only the structural constraints approved under AIO-006:

- root `type: object` with `additionalProperties: false`,
- required fields: `id`, `name`, `purpose`, `responsibilities`, `required_capabilities`,
- optional field: `applicable_task_types`,
- non-empty string types for scalar fields,
- array of non-empty strings for list fields.

AIO-006 did not authorize undocumented constraints such as `minItems`, `uniqueItems`, identifier pattern regexes, or vocabulary enums. Therefore, empty arrays and duplicate items remain structurally accepted by the schema.

Fixtures demonstrating empty arrays or duplicates establish **structural permissiveness only**, not recommended Role design.

> Schema-valid does not imply semantically valid, useful, recommended, or review-approved.

Semantic review remains responsible for determining whether Role responsibilities and capabilities satisfy the AIO-006 contract.

### Clarification 3 — Task Lifecycle

AIO-007 begins in the `in_progress` status under the existing Task contract. It is not marked `completed` until independent review is satisfied and explicit Human approval is granted.

## Prohibited Extensions

AIO-007 does not introduce:

- `schema_version` as an instance field
- `extensions`
- Provider or model configuration
- Agent or Human identity
- Prompt or persona concepts
- Runtime tools or permissions
- Authority or approval concepts
- Task-to-Role assignment contracts
- Workflow definitions or execution
- Execution modes or contracts
- Estimates, billing, or Task relationships
