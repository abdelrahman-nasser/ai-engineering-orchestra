# AIO-003 — Context

## Objective

AIO-002 established the canonical human-readable Project Manifest contract.

AIO-003 must provide a machine-readable schema capable of validating that contract without changing its semantics.

The canonical contract remains:

`core/project-manifest.md`

The schema implements validation for that contract; it does not replace it.

## Inputs

Primary inputs:

- `core/project-manifest.md`
- `templates/project.yaml`
- `.ai/project.yaml`

## Architectural Constraints

The schema must remain:

- Provider-agnostic
- model-agnostic
- language-agnostic
- framework-agnostic
- deterministic
- suitable for future CLI validation

The schema must not introduce configuration fields that are absent from the canonical Project Manifest specification.

## Compatibility

Both of these files must conform to the resulting schema:

- `templates/project.yaml`
- `.ai/project.yaml`

## Future Compatibility

The schema should leave room for future schema versions without implementing future Orchestra functionality.

CLI-based validation remains outside AIO-003.
