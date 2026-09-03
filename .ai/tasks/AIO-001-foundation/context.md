# AIO-001 — Context

## Objective

AI Engineering Orchestra needs a stable provider-independent foundation before Roles, Workflows, routing, Provider Adapters, or automation are introduced.

This Task establishes the vocabulary and core behavioral contract that later Orchestra versions will depend on.

## Current Version

Target:

0.1.0

## Project Type

Framework

## Lifecycle

Greenfield

## Important Constraints

The foundation must remain:

- model-agnostic
- provider-agnostic
- stack-agnostic
- programming-language-agnostic
- repository-layout-agnostic where practical

Claude, Codex, Antigravity, and future AI systems must be treated as Providers or execution environments rather than permanent architectural dependencies.

## Future Compatibility

The v0.1 foundation must leave clean extension points for:

- Brownfield onboarding in v0.2
- command security in v0.2
- Stack Modules in v0.3
- Provider Adapters in v0.4
- routing and quota management in v0.5
- CLI support in v0.6
- package distribution in v0.7

Future functionality must not be prematurely implemented as part of AIO-001.
