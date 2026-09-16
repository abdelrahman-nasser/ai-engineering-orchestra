# Standard Change

## `id`

`standard-change`

## `name`

Standard Change

## `purpose`

Govern standard engineering work through disciplined understanding, implementation, validation, and review.

## `applicable_task_types`

- `implementation`
- `bugfix`
- `refactoring`
- `migration`
- `maintenance`
- `documentation`

## `stages`

### Stage 1: `understand`

- **`id`**: `understand`
- **`purpose`**: Acquire necessary context, verify task scope, and understand requirements before implementation.

### Stage 2: `implement`

- **`id`**: `implement`
- **`purpose`**: Execute scoped implementation changes according to task acceptance criteria.
- **`required_roles`**:
  - `software-engineer`

### Stage 3: `validate`

- **`id`**: `validate`
- **`purpose`**: Execute tests, builds, and automated verification to establish evidence of correctness.

### Stage 4: `review`

- **`id`**: `review`
- **`purpose`**: Evaluate changes against acceptance criteria and verify ready state for human evaluation.
- **`required_roles`**:
  - `reviewer`
- **`human_control_checkpoint`**: `true`

---

This Workflow is declarative governance choreography. It does not select actors, grant permissions, or execute commands.
