# Workflows

This directory contains canonical Workflow definitions used by AI Engineering Orchestra.

A Workflow defines the ordered engineering stages used to complete a class of Task.

Examples may include:

- feature development
- bug fixing
- refactoring
- architecture changes
- documentation changes

## v0.1 Status

Detailed Workflow specifications are not part of task `AIO-001`.

At the current Foundation stage, the Orchestra defines the concept of a Workflow and the default Execution Modes, but task-specific Workflow definitions have not yet been established.

Agents must not invent missing Workflow definitions.

If a Task references a Workflow that does not yet exist, the missing definition must be reported rather than inferred as an authoritative Orchestra Workflow.

## Planned v0.1 Work

Later v0.1 Tasks will define the initial Workflow contract and the first reusable Workflows.

Until then, this directory acts as the canonical location for Workflow definitions but does not claim that those definitions already exist.
