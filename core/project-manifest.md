# AI Engineering Orchestra — Project Manifest Specification

Version: 0.1.0
Manifest Schema Version: 0.1

This document defines the canonical Project Manifest contract for AI Engineering Orchestra v0.1.

---

## 1. Purpose

The Project Manifest is the primary Source of Truth describing how a repository uses AI Engineering Orchestra.

Its default location is:

`.ai/project.yaml`

The manifest describes Orchestra engineering configuration.

It must not become a replacement for application runtime configuration, environment configuration, deployment secrets, or Provider-specific configuration.

---

## 2. Design Goals

The Project Manifest must remain:

- Provider-agnostic
- model-agnostic
- programming-language-agnostic
- framework-agnostic
- human-readable
- versioned
- deterministic
- extensible
- suitable for automated validation in future Orchestra versions

The manifest should contain only information required to configure or locate Orchestra behavior for the Project.

---

## 3. Configuration Boundaries

The Project Manifest may describe:

- Project identity
- Orchestra version
- Project lifecycle
- default Complexity
- default Risk
- default Execution Mode
- Human control requirements
- Quality Gate requirements
- Agent execution limits
- context-loading behavior
- Project Rule locations
- Task locations
- Override locations
- approved future extension namespaces

The Project Manifest must not directly contain:

- application connection strings
- application runtime settings
- secrets
- passwords
- API keys
- access tokens
- production credentials
- business data
- environment-specific deployment secrets
- hardcoded AI model names in Orchestra Core configuration
- Provider-specific configuration that belongs to a Provider Adapter

---

## 4. File Format

The canonical Project Manifest format is YAML.

Default location:

`.ai/project.yaml`

A Project must have at most one canonical Project Manifest at this location unless a future Orchestra specification explicitly introduces another mechanism.

---

## 5. Canonical Example Manifest

The canonical reusable example Project Manifest is:

`templates/project.yaml`

This file provides a complete example of a Project Manifest that conforms to schema version `0.1`.

The template is illustrative and reusable.

Projects may change its values to match their own identity and requirements, but the resulting manifest must still conform to this specification.

The canonical example does not replace this specification. Where a conflict exists, this specification is authoritative.

---

## 6. Schema Version

The top-level `schema_version` field identifies the Project Manifest schema version.

Example:

```yaml
schema_version: "0.1"
```

### Schema Version Requirements

- `schema_version` is required.
- The value must be a string.
- For Orchestra v0.1, the supported value is `"0.1"`.
- Consumers must not silently interpret an unsupported schema version as `"0.1"`.

The schema version describes the manifest contract.

It is separate from the Orchestra framework version.

---

## 7. Canonical Top-Level Sections

The v0.1 Project Manifest defines these canonical top-level sections:

| Section | Required | Purpose |
| --- | --- | --- |
| `schema_version` | Yes | Manifest contract version |
| `project` | Yes | Project identity and lifecycle |
| `orchestra` | Yes | Orchestra framework configuration |
| `complexity` | Yes | default Task Complexity |
| `risk` | Yes | default Task Risk |
| `execution` | Yes | default Execution Mode |
| `human_control` | Yes | Human approval requirements |
| `quality` | Yes | required Quality Gates |
| `agents` | No | Agent execution limits |
| `context` | No | context-loading configuration |
| `project_rules` | No | Project Rule location |
| `tasks` | No | Task location |
| `overrides` | No | Project Override location |
| `extensions` | No | namespaced future extension configuration |

Unknown top-level sections are not automatically valid extensions.

---

## 8. `project`

The `project` section identifies the Project.

Example:

```yaml
project:
  id: ai-engineering-orchestra
  name: AI Engineering Orchestra
  type: framework
  lifecycle: greenfield
```

### Required `project` Fields

#### `project.id`

A stable machine-readable Project identifier.

Requirements:

- required
- non-empty string
- should remain stable after initial adoption
- should be suitable for use in Tasks, tooling, logs, and future automation

Recommended format:

lowercase words separated by hyphens.

Example:

```yaml
id: customer-portal
```

#### `project.name`

Human-readable Project name.

Requirements:

- required
- non-empty string

Example:

```yaml
name: Customer Portal
```

#### `project.type`

Describes the broad Project type.

Examples may include:

- framework
- web-application
- backend-api
- library
- mobile-application
- service
- saas
- infrastructure

Requirements:

- required
- non-empty string

The value is intentionally open in v0.1 because Project types are extensible.

Consumers must not infer security or Workflow behavior solely from `project.type`.

#### `project.lifecycle`

Defines the Project lifecycle.

Allowed v0.1 values:

- `greenfield`
- `brownfield`
- `modernization`
- `maintenance`

Requirements:

- required
- must match a lifecycle defined in `core/lifecycle.md`

Example:

```yaml
lifecycle: greenfield
```

---

## 9. `orchestra`

The `orchestra` section identifies the Orchestra framework version expected by the Project.

Example:

```yaml
orchestra:
  version: "0.1.0"
```

### `orchestra.version`

Requirements:

- required
- non-empty string
- must identify the Orchestra framework version targeted by the Project

The framework version is separate from `schema_version`.

Example:

```text
schema_version = Project Manifest contract
orchestra.version = Orchestra framework release
```

Future package-management versions may use this field during compatibility checks.

No package resolution behavior is implemented in v0.1.

---

## 10. `complexity`

Defines the default Task Complexity when a Task does not explicitly provide one.

Example:

```yaml
complexity:
  default: medium
```

Allowed values:

- `low`
- `medium`
- `high`
- `critical`

### `complexity` Requirements

- the section is required
- `default` is required

Task-specific Complexity overrides the Project default where permitted.

Complexity remains independent from Risk.

---

## 11. `risk`

Defines the default Task Risk when a Task does not explicitly provide one.

Example:

```yaml
risk:
  default: medium
```

Allowed values:

- `low`
- `medium`
- `high`
- `critical`

### `risk` Requirements

- the section is required
- `default` is required

Task-specific Risk overrides the Project default where permitted.

Risk remains independent from Complexity.

---

## 12. `execution`

Defines the default Execution Mode.

Example:

```yaml
execution:
  default_mode: standard
```

Allowed values:

- `lite`
- `standard`
- `deep`
- `critical`

### `execution` Requirements

- the section is required
- `default_mode` is required

A Task may select a different Execution Mode when permitted by applicable Policies and Workflows.

A lower Execution Mode must not silently weaken protected requirements.

---

## 13. `human_control`

Defines Project-level Human approval requirements.

Example:

```yaml
human_control:
  final_review_required: true
  architecture_changes_require_approval: true
  breaking_schema_changes_require_approval: true
  breaking_contract_changes_require_approval: true
```

### Supported `human_control` Fields

Supported v0.1 fields are:

- `final_review_required`
- `architecture_changes_require_approval`
- `breaking_schema_changes_require_approval`
- `breaking_contract_changes_require_approval`

### `human_control` Field Semantics

- `final_review_required: true` requires final Human review and approval before the Task may be closed.
- `architecture_changes_require_approval: true` requires Human approval before a material architecture change is accepted as complete.
- `breaking_schema_changes_require_approval: true` requires Human approval before a breaking data or persistence schema change is accepted as complete.
- `breaking_contract_changes_require_approval: true` requires Human approval before a breaking public or framework contract change is accepted as complete.

A `false` value removes only the Project Manifest's own requirement. It does not override an approval requirement imposed by a higher-precedence Policy, Task, Workflow, or protected rule.

These fields define approval requirements only. They do not grant permission to perform otherwise protected actions.

Detailed approval behavior is defined in `core/human-control.md`.

### `human_control` Requirements

- the section is required
- supported fields are optional unless another applicable Policy requires them
- values must be boolean in schema version `0.1`

Projects should include only fields relevant to their Human control requirements.

A missing field must not be interpreted as approval for a protected action when another applicable Policy requires approval.

Human control behavior must follow:

`core/human-control.md`

Protected Policies cannot be weakened through this section.

---

## 14. `quality`

Defines Project-level Quality Gate requirements.

Example:

```yaml
quality:
  require_independent_review: true
  require_documentation_consistency: true
```

### `quality` Requirements

- the section is required
- individual Quality Gate requirement fields are optional unless required by an applicable Policy or Workflow
- canonical Quality Gate requirement fields must correspond to defined Quality Gate identifiers
- values must be boolean in schema version `0.1`

The naming convention is:

```text
require_<quality_gate_id>
```

Example:

```text
Quality Gate ID:
independent_review

Manifest field:
require_independent_review
```

### `quality` Field Semantics

- `require_independent_review: true` requires the applicable `independent_review` Quality Gate to be completed successfully before the Task may be closed.
- `require_documentation_consistency: true` requires the applicable `documentation_consistency` Quality Gate to be completed successfully before the Task may be closed.

A `false` value removes only the Project Manifest's own requirement for that Gate. It does not override a requirement imposed by a higher-precedence Policy, Task, Workflow, or protected rule.

An omitted Quality Gate field means that Gate is not required by the Project Manifest alone.

Quality Gate behavior and pass conditions remain defined by the corresponding files in `quality-gates/`.

---

## 15. `agents`

Defines Project-level limits on Agent execution.

Example:

```yaml
agents:
  max_parallel: 3
  max_depth: 2
```

This section is optional.

### `agents.max_parallel`

Maximum number of Agent executions intended to operate concurrently for Orchestra-managed work.

Requirements:

- positive integer
- minimum value: `1`

If omitted:

```text
default = 1
```

### `agents.max_depth`

Maximum permitted subagent nesting depth below the initiating Agent or Orchestrator.

Requirements:

- integer
- minimum value: `0`

Interpretation:

```text
0 = subagent spawning disabled
1 = one child level
2 = two child levels
```

If omitted:

```text
default = 0
```

Agent spawning and automatic enforcement are not implemented in v0.1.

These fields define limits for future orchestration behavior.

---

## 16. `context`

Defines Project-level context-loading behavior.

Example:

```yaml
context:
  strategy: progressive
  prefer_relevant_only: true
```

This section is optional.

### `context.strategy`

Supported v0.1 value:

- `progressive`

If omitted:

```text
default = progressive
```

Other strategies are unsupported in schema version `0.1`.

### `context.prefer_relevant_only`

Boolean indicating whether Agents should prefer loading only context relevant to the current Task and Role.

If omitted:

```text
default = true
```

Context behavior must follow:

`core/context-policy.md`

---

## 17. `project_rules`

Defines the canonical Project Rule directory.

Example:

```yaml
project_rules:
  directory: ".ai/rules/"
```

This section is optional.

If omitted:

```text
default directory = .ai/rules/
```

The path must be repository-relative.

Project Rules located here remain subject to the precedence model.

---

## 18. `tasks`

Defines the canonical Task directory.

Example:

```yaml
tasks:
  directory: ".ai/tasks/"
```

This section is optional.

If omitted:

```text
default directory = .ai/tasks/
```

The path must be repository-relative.

---

## 19. `overrides`

Defines the canonical Project Override directory.

Example:

```yaml
overrides:
  directory: ".ai/overrides/"
```

This section is optional.

If omitted:

```text
default directory = .ai/overrides/
```

The path must be repository-relative.

Overrides must follow `core/precedence.md`.

Overrides must not weaken protected Policies.

---

## 20. `extensions`

The optional `extensions` section provides a controlled future extension point for configuration that is not part of the Orchestra Core Project Manifest contract.

Example:

```yaml
extensions:
  example.namespace:
    enabled: true
```

### Extension Namespace Format

Extension keys must use a dot-separated namespace.

Recommended format:

```text
<owner>.<extension>
```

Examples:

```text
openai.routing
company.security
team.custom-review
```

Namespace requirements:

- must contain at least one dot
- each segment must be non-empty
- segments should use lowercase letters, numbers, and hyphens
- spaces are not allowed
- extension namespaces must not use `orchestra` as the owner unless defined by Orchestra Core
- extension namespaces must not impersonate or redefine canonical Orchestra Core sections

Examples of invalid namespaces:

```text
routing
company security
.orchestration
orchestra
```

### `extensions` Requirements

- the section is optional
- extension keys must follow the namespace format defined above
- extension configuration must not redefine Orchestra Core semantics
- extension configuration must not weaken protected Policies
- extension configuration must not bypass Human control requirements
- extension configuration must not bypass Quality Gate requirements
- unknown extension namespaces must not be interpreted as Orchestra Core configuration
- consumers must not infer behavior from an unknown extension namespace

The `extensions` section exists to avoid uncontrolled top-level configuration growth.

An extension namespace does not gain authority merely because it appears in the Project Manifest. Its behavior remains subject to `core/precedence.md` and all applicable protected Policies.

Provider-specific configuration may eventually be referenced through approved Provider Adapter mechanisms.

No Provider Adapter configuration contract, extension registry, loading mechanism, or execution behavior is defined by AIO-002.

---

## 21. Unsupported and Unknown Fields

For schema version `0.1`:

- unknown top-level fields outside `extensions` are unsupported
- consumers must not silently assign semantics to unsupported fields
- unsupported fields should be reported during validation or review
- future tooling may reject unsupported fields
- Agents must not invent behavior for unknown fields

Until automated validation exists, unsupported fields must be identified through review.

---

## 22. Defaults

Defaults exist only where explicitly defined by this specification.

v0.1 defaults are:

| Field | Default |
| --- | --- |
| `agents.max_parallel` | `1` |
| `agents.max_depth` | `0` |
| `context.strategy` | `progressive` |
| `context.prefer_relevant_only` | `true` |
| `project_rules.directory` | `.ai/rules/` |
| `tasks.directory` | `.ai/tasks/` |
| `overrides.directory` | `.ai/overrides/` |

Required fields do not receive implicit defaults unless explicitly stated.

Agents must not invent defaults.

---

## 23. Path Rules

Paths declared by the Project Manifest must:

- be repository-relative unless a future specification explicitly permits otherwise
- use forward slashes in canonical documentation and generated examples
- not rely on a particular operating system
- not contain credentials or secrets

Example:

```yaml
directory: ".ai/tasks/"
```

Preferred over:

```text
D:\Projects\MyApp\.ai\tasks
```

---

## 24. Precedence

The Project Manifest is the Source of Truth for Project-level Orchestra configuration.

However, it remains subject to:

`core/precedence.md`

Project Manifest configuration must not weaken:

- protected security or safety Policies
- Orchestra Core Principles
- protected Core Policies
- higher-authority applicable Policies

Task-specific configuration may override Project defaults only where permitted.

---

## 25. Provider Independence

The Project Manifest must not require a specific Provider or model.

Orchestra Core configuration must remain valid regardless of whether execution is performed by:

- Claude
- Codex
- Antigravity
- another compatible Provider
- a Human

Future Provider-specific configuration belongs behind Provider Adapters.

Provider names may appear in extension or adapter configuration in later Orchestra versions, but they are not part of the v0.1 Core Manifest contract.

---

## 26. Stack Independence

The Project Manifest does not require a programming language, framework, database, or infrastructure platform.

Stack-specific configuration will be introduced through Stack Modules in a later Orchestra version.

The absence of Stack Module configuration in v0.1 must not be interpreted as missing Project configuration.

---

## 27. Application Configuration Boundary

The Project Manifest is not application configuration.

Examples of information that does not belong in `.ai/project.yaml`:

```text
database connection strings
SMTP settings
JWT secrets
API endpoints used by application runtime
cloud credentials
feature flags used by production code
business configuration
customer data
```

Those belong in the application's normal configuration mechanisms.

---

## 28. Forward Compatibility

Future Orchestra versions may introduce new canonical sections.

Consumers reading schema version `0.1` must not assume future fields exist.

A future manifest format that changes required structure or field semantics must use an appropriate schema version change.

Future features should prefer defined extension points rather than silently changing the meaning of existing fields.

---

## 29. Schema Version vs Orchestra Version

These values serve different purposes.

Example:

```yaml
schema_version: "0.1"

orchestra:
  version: "0.1.0"
```

`schema_version` identifies the configuration contract.

`orchestra.version` identifies the expected Orchestra framework release.

The two values may evolve independently in future versions.

---

## 30. Canonical Ownership

The Project Manifest owns Project-level Orchestra configuration.

It does not own:

- Task-specific requirements
- architecture decisions
- Project Rule content
- Workflow definitions
- Role definitions
- Quality Gate definitions

Those remain in their respective Sources of Truth.

The manifest may reference or configure those systems without duplicating their canonical content.

---

## 31. Validation Status in v0.1

AIO-002 defines the Project Manifest contract.

Automated validation is not implemented by this Task.

Until automated validation exists, conformance is verified through:

- repository review
- documentation consistency checks
- independent review

JSON Schema implementation will be handled by a later Task.

CLI validation is reserved for a later Orchestra version.

---

## 32. Canonical Conformance Rule

A Project Manifest conforms to schema version `0.1` when:

1. all required sections and fields exist
2. values use allowed types and enumerations
3. unsupported top-level fields are absent
4. paths follow canonical path rules
5. protected Policies are not weakened
6. Provider-specific configuration is not embedded in Orchestra Core sections
7. application runtime configuration is kept outside the manifest
8. explicit defaults and Source of Truth boundaries are respected
