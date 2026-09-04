# AIO-002 — Context

## Objective

AI Engineering Orchestra requires a stable Project Manifest contract before automated validation, Profiles, routing, Provider Adapters, or CLI tooling can be safely introduced.

The default Project Manifest location is:

`.ai/project.yaml`

AIO-001 introduced an initial manifest for the Orchestra repository itself.

AIO-002 must now turn that initial configuration into a formally documented, reusable specification.

## Why This Matters

The Project Manifest is intended to become the primary Source of Truth describing how a repository uses AI Engineering Orchestra.

Future systems may rely on it for:

- future Workflow selection or routing that may reference Project Manifest configuration
- Risk and Complexity defaults
- Human control requirements
- Quality Gate requirements
- context strategy
- future Stack Module selection that may reference Project Manifest configuration
- Provider configuration references
- model and Provider routing
- CLI validation
- package installation and upgrades

Because many future features will depend on this contract, ambiguity introduced here may become expensive to correct later.

## Architectural Constraints

The Project Manifest must remain:

- Provider-agnostic
- model-agnostic
- programming-language-agnostic
- framework-agnostic
- usable by Greenfield and future Brownfield Projects
- extensible without encouraging arbitrary configuration

The manifest must describe Orchestra configuration without becoming a dumping ground for application configuration.

## Existing Example

The current repository already contains:

`.ai/project.yaml`

This file is an implementation example from AIO-001.

AIO-002 may refine its structure where justified, but any breaking change requires explicit review and Human approval.

## Future Compatibility

The specification must leave clean extension points for:

- v0.2 Brownfield configuration
- v0.2 command security Policies
- v0.3 Stack Modules
- v0.4 Provider Adapters
- v0.5 routing and quota Policies
- v0.6 CLI validation
- v0.7 package/version management

These future capabilities must not be implemented as part of AIO-002.

## Deliverable

AIO-002 should produce a canonical Project Manifest specification document and one canonical example manifest.

JSON Schema implementation will be handled by a later Task.
