# AIO-002 — Acceptance Criteria

AIO-002 is complete when all applicable criteria below are satisfied.

## Specification

- [x] A canonical Project Manifest specification exists.
- [x] The default manifest location is defined as `.ai/project.yaml`.
- [x] The manifest's responsibility and boundaries are explicitly defined.
- [x] Required sections are identified.
- [x] Optional sections are identified.
- [x] Required fields are identified.
- [x] Optional fields are identified.
- [x] Allowed values are defined where applicable.
- [x] Defaults are defined where applicable.
- [x] Unknown or unsupported fields have defined handling rules.

## Core Configuration

- [x] Project identity configuration is specified.
- [x] Orchestra version configuration is specified.
- [x] Project lifecycle configuration is specified.
- [x] default Complexity configuration is specified.
- [x] default Risk configuration is specified.
- [x] default Execution Mode configuration is specified.
- [x] Human control configuration is specified.
- [x] Quality Gate configuration is specified.
- [x] Agent limits are specified.
- [x] context strategy configuration is specified.
- [x] Project Rules location is specified.
- [x] Task location is specified.
- [x] Override location is specified.

## Architecture

- [x] The manifest does not require a specific AI Provider.
- [x] The manifest does not require a specific AI model.
- [x] The manifest does not require a specific programming language or framework.
- [x] Provider-specific settings are not embedded directly into Orchestra Core configuration.
- [x] application runtime configuration is kept outside the Project Manifest.
- [x] extension points for future Orchestra versions are documented without implementing those future features.

## Consistency

- [x] Configuration terminology aligns with `core/terminology.md`.
- [x] Precedence behavior aligns with `core/precedence.md`.
- [x] Human control behavior aligns with `core/human-control.md`.
- [x] context behavior aligns with `core/context-policy.md`.
- [x] lifecycle values align with `core/lifecycle.md`.
- [x] Quality Gate identifiers align with `quality-gates/`.

## Example

- [x] A canonical example Project Manifest exists.
- [x] The example passes manual review against the specification.
- [x] The Orchestra repository's own `.ai/project.yaml` either conforms to the specification or is updated as part of this Task.

## Quality

- [x] `documentation_consistency` passes.
- [x] `independent_review` passes.
- [x] Final Human approval is obtained before Task closure.
