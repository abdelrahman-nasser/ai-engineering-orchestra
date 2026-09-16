# Security-Sensitive Change

## `id`

`security-sensitive-change`

## `name`

Security-Sensitive Change

## `purpose`

Govern engineering work involving security boundaries, access controls, credentials, or protected resources.

## `applicable_task_types`

- `implementation`
- `architecture`
- `migration`

## `stages`

### Stage 1: `understand`

- **`id`**: `understand`
- **`purpose`**: Analyze security posture, identify potential threats, and understand existing security boundaries.

### Stage 2: `security-analysis`

- **`id`**: `security-analysis`
- **`purpose`**: Perform deep security analysis, evaluate control impact, and identify security risks.
- **`required_roles`**:
  - `security-reviewer`

### Stage 3: `implement`

- **`id`**: `implement`
- **`purpose`**: Execute security controls, remediate vulnerabilities, or apply defensive measures within scope.
- **`required_roles`**:
  - `software-engineer`

### Stage 4: `validate`

- **`id`**: `validate`
- **`purpose`**: Execute security testing, verify defensive assertions, and run regression suites.

### Stage 5: `review`

- **`id`**: `review`
- **`purpose`**: Conduct independent security review, verify control effectiveness, and evaluate Human Control requirements.
- **`required_roles`**:
  - `reviewer`
  - `security-reviewer`
- **`required_quality_gates`**:
  - `independent_review`
- **`human_control_checkpoint`**: `true`

---

This Workflow is declarative governance choreography. It does not select actors, grant permissions, or execute commands.
