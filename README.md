# AI Engineering Orchestra

AI Engineering Orchestra is a reusable, versioned, model-agnostic framework for organizing AI-assisted software engineering.

It provides a common structure for:

- AI Agent Roles
- engineering Workflows
- project Rules
- Quality Gates
- Risk and Complexity handling
- Human approval
- project context
- future Provider routing and security controls

The framework is designed to work independently of any specific AI Provider, model, programming language, framework, or application architecture.

---

## Current Version

```text
0.1.0
```

## Local CLI Installation

Python 3.12 or newer is required for the locally installable CLI. AIO-016
establishes this initial packaging baseline; it is not a historical support claim.
From this checkout, in a virtual environment:

```powershell
python -m pip install -e .
aio --help
aio tasks
aio inspect AIO-015
aio verify
```

For a normal installation, use `python -m pip install .` instead. The command is
available when the installing environment's `Scripts` (Windows) or `bin` directory
is on PATH, usually by activating the environment. Editable installations follow
source edits; metadata/console-name changes require reinstalling. Normal installs
must be reinstalled to receive source changes. Uninstall with
`python -m pip uninstall ai-engineering-orchestra`; the checkout remains intact.

Run commands from the managed project or a subdirectory. The nearest ancestor
containing `.ai/project.yaml` determines the active project, never the installed
package location. `tasks` and `inspect` currently assume `.ai/tasks/` and
`workflows/`; they do not yet honor a custom Manifest Task directory. Workflows
belong to the target project; Task and Workflow schemas belong to the tool.

**`verify` remains Orchestra development tooling, not generic project verification.**
It requires this repository's `tests/`, four `schemas/tests/validate_*.py`
programs and their fixtures/canonical inputs, Markdown lint setup, and Git working
tree. Git and Node/npm (`npx`) must already be available on PATH. They are not
Python dependencies and are not automatically installed. Python checks use the
CLI environment's interpreter. All seven checks remain mandatory; mechanical
PASS is not Quality Gate satisfaction or Human approval.

Source commands (`python -B aio.py ...` and `python -B scripts/list_tasks.py`,
`scripts/inspect_task.py`, `scripts/verify_repo.py`) remain available. Normal console
launchers may write Python bytecode; suppressing installed `__pycache__` is not a
product requirement. Preflight Python subprocesses retain their explicit `-B`.

The local distribution name `ai-engineering-orchestra`, temporary console name
`aio`, technical namespace `engineering_orchestration`, product display name,
and historical `AIO-*` Task IDs are separate identities. Another console name can
target the same router without changing capabilities. The static distribution
version `0.1.0` identifies installed code; Manifest `orchestra.version` expresses
the managed project's framework expectation. No version synchronization is implied.

This is an explicitly authorized local-installability experiment. It does not
complete the future public distribution milestone. No PyPI publication, public
name reservation, release automation, or generic verifier is provided.
