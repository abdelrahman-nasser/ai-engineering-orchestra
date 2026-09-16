# Architecture Change

## `id`

`architecture-change`

## `name`

Architecture Change

## `purpose`

Govern engineering work involving architectural decisions, structural framework evolution, or specification design.

## `applicable_task_types`

- `architecture`
- `specification`

## `stages`

### Stage 1: `understand`

- **`id`**: `understand`
- **`purpose`**: Analyze current architecture, baseline dependencies, and understand problem context.

### Stage 2: `design`

- **`id`**: `design`
- **`purpose`**: Formulate architectural approach, evaluate design alternatives, and document architectural decisions.
- **`required_roles`**:
  - `architect`

### Stage 3: `implement`

- **`id`**: `implement`
- **`purpose`**: Execute structural changes or specification modifications aligned with the approved design.
- **`required_roles`**:
  - `software-engineer`

### Stage 4: `validate`

- **`id`**: `validate`
- **`purpose`**: Validate architectural consistency, run regression checks, and verify structural integrity.

### Stage 5: `review`

- **`id`**: `review`
- **`purpose`**: Conduct independent evaluation of architecture changes, verify documentation consistency, and evaluate Human Control requirements.
- **`required_roles`**:
  - `reviewer`
  - `architect`
- **`required_quality_gates`**:
  - `documentation_consistency`
  - `independent_review`
- **`human_control_checkpoint`**: `true`

---

This Workflow is declarative governance choreography. It does not select actors, grant permissions, or execute commands.
