# ITRU-063 design lock

## Current checkpoint: final Human closure COMPLETE / Task completed and closed

Human authorization: APPROVE ITRU-063 FINAL HUMAN CLOSURE ONLY.
Final Human closure COMPLETE; H01 COMPLETE; acceptance 22/22; task.yaml status
completed. The accepted final basis remains FQ-DC-1 PASS, FQ-IR-1 PASS and
publication readback PASS, frozen procedures unchanged, 96 passing tests and
5/5 independent specialist approvals current, unresolved B/H/M/L 0/0/0/0.
ITRU-060/061/062 and persistence migrations remain preserved. Concurrency
selection stays snapshot-scoped; the caller must serialize registration.
Only the five existing Task evidence/status files are updated for this closure.
Complete validation, specialist, three Medium/remediation, gate and readback
histories below and in review.md/completion-report.md are retained. Earlier
OPEN/21-of-22/closure-pending statements are historical checkpoints, superseded
only for final Human closure. No production, specification, test or persistence
change, validation/review/gate rerun, Git mutation, publication or ITRU-064 start.
No further Human authorization is needed for ITRU-063 closure.
STOP AT HUMAN CONTROL.

## Historical checkpoint: locked final gates PASS / STOP AT HUMAN CONTROL

Implementation, prevalidation static audit, exact V1-V4 and all five fresh
independent specialist reviews are finished. Current basis: V1 37 / V2 59 passed,
zero skips; V3/V4 exit 0. Three Medium findings were minimally remediated and
independently resolved; unresolved Blocker/High/Medium/Low 0/0/0/0.
All five specialists APPROVE the same five product fingerprints retained in
completion-report.md. The Human subsequently authorized exactly
APPROVE ITRU-063 LOCKED FINAL QUALITY GATES ONLY.
The exact frozen FQ-DC-1 command completed exit 0; all five product hashes match
and DC-01..DC-07 PASS. Only then the exact FQ-IR-1 command completed exit 0;
IR-01..IR-05 PASS on existing independent review receipts. Both gates PASS.
Acceptance 21/22: G01 complete, H01 Human closure still unchecked. Task remains
in_progress and OPEN. Only the five existing Task evidence/status files are
updated. The required same-five-file readback must contain no contradiction;
contradiction invalidates the relevant gate under the unchanged frozen procedure.
The frozen procedure text below, including its design-time pre-execution labels,
is retained verbatim. Its NOT EXECUTED/future-authorization wording is historical
definition context; the current execution status is the PASS receipt above and
the check-by-check receipt in review.md. Implementation-cycle no-gate exclusions
remain historical; this new Human authorization covers locked gates only.
No production/test/specification/schema/persistence/migration or scheduler
authority change, new tests/reviews, catalog traversal or protected-path access.
No staging, commit, pull, push or merge. Only the originally requested branch
creation changed Git metadata. Exact next Human authorization needed:
APPROVE ITRU-063 FINAL HUMAN CLOSURE ONLY.

## Historical implementation-cycle authorization and baseline

SCRUM-20 / Developer Alpha. Baseline
b3a433f8ba31354cfe61054176789392b5a2f7d7 verified in
D:\Dev\ai-engineering-orchestra with clean working tree before changes.
Branch: itru-063-minimal-dag-scheduler-foundation. ITRU-062 is closed 30/30.
The Human authorized this design lock through implementation, audit, validation,
fresh specialist reviews and evidence updates. Final gates and closure are NOT
authorized. Stop for Blocker/High, upstream contract or migration change, scope
widening, material authority/security change, unsafe/ambiguous validation or any
requirement to access workflows/README.md. Medium/Low inside this lock: record,
minimally fix, validate affected behavior, reassess and continue.

## Frozen design before implementation

Canonical Task IDs and definition references are exact case-sensitive opaque
nonempty strings. An immutable TaskNode pins task_id/definition_reference.
TaskDependency identity is the ordered pair (task_id, prerequisite_task_id).
TaskGraph is a closed caller-supplied set of nodes and edges, normalized by exact
lexical identity. Reject duplicate nodes/edges, unknown endpoints, self-edges and
cycles as a whole. Empty graphs are valid. Deterministic Kahn traversal uses the
lexically smallest available node. Bound to 1000 nodes and 10000 edges.
The caller translates explicitly resolved task.yaml dependencies; no filesystem,
Task/Workflow catalog scan or implicit dependency discovery exists.

SchedulingSnapshot pins store_id/project_id and a tuple of unchanged ITRU-062
TaskSnapshots. It contains the complete graph scheduling domain: no extra Task
is permitted, and missing Tasks remain unresolved, never implicitly planned.
Missing observations suspend new selection for the whole domain because their
occupancy is unknown. Definition mismatches and observably incoherent state
invalidate input. Snapshots are caller-attested descriptive evidence; validating
them cannot authenticate Store origin or temporal currency.

Dependency readiness requires every immediate prerequisite's operational Task
state completed. Success of a Run alone, cancelled Tasks, Journal summaries and
task.yaml status do not satisfy an enrolled dependency. Every Task gets ordered
dependency evidence with all unsatisfied prerequisite IDs. Only planned Tasks
with no Run history and satisfied dependencies can be selected. Pending/running
Runs count as occupied slots and are never selected or replayed. Any historical
interrupted/effect_ambiguous Run prevents automatic selection. All other prior
attempts/in_progress/blocked Tasks require explicit lifecycle/governance handling;
this scheduler never initiates continuation, including failure-before-effect.

Selection is lexical task_id order, within max_concurrency (exact int 1..100).
Capacity is graph-domain scoped. Over-capacity input produces zero new selection
and explicit evidence, preserving existing occupancy. Decisions contain the
canonical graph, canonical snapshot, limit, occupied Run IDs, per-Task evaluations
and selected Task IDs. No clock, random input, callback, Tool resolution, native
execution, Store access, reservation or mutation is part of evaluation.

Assignment handoff re-evaluates the supplied snapshot and checks the externally
chosen unchanged Assignment's exact fields and Task selection. It returns that
Assignment, the ITRU-062 Checkpoint and the complete decision as descriptive
evidence only. Contextual Assignment validation remains with the existing API.
The single local caller must serialize evaluation plus registration, supply a
complete coherent current domain snapshot, recheck all dependency revisions and
capacity before registration, and use existing revision CAS. A decision is not a
reservation or enforceable global concurrency limit. Persisted or copied decisions
cannot bypass fresh mode/prerequisites, ownership, Grant/authentication/admission,
claim/JIT/controlled invocation or original Result provenance. No Run is created.

No new durable format, migration or serializer is introduced. All new scheduler
values are immutable in-memory evidence. Existing upstream contracts remain exact.

## Exact implementation whitelist (ten files)

1. .ai/tasks/ITRU-063-minimal-dag-scheduler-foundation/task.yaml
2. .ai/tasks/ITRU-063-minimal-dag-scheduler-foundation/context.md
3. .ai/tasks/ITRU-063-minimal-dag-scheduler-foundation/acceptance-criteria.md
4. .ai/tasks/ITRU-063-minimal-dag-scheduler-foundation/review.md
5. .ai/tasks/ITRU-063-minimal-dag-scheduler-foundation/completion-report.md
6. core/task-scheduler-specification.md
7. itru/task_dependency.py
8. itru/task_scheduler.py
9. tests/test_task_dependency.py
10. tests/test_task_scheduler.py

Task directory and completion-report path are exactly entries 1-5 above.
No other file changes are authorized. No staging or Git history/network mutation.

## Static safety audit and exact validation commands

Before tests, inspect the five new product/spec/test files and the exact upstream
test/source dependencies below. Verify no target invocation, authority producer,
operational registry, catalog scan, network or uncontained cleanup. New SQLite
fixtures use only nonce-owned itru-063-scheduler-* directories under resolved OS
temp, verify containment and plain descendants before cleanup, and assert absence.

Run from the verified repository, using this exact Python executable:
C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe.

V1:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest tests.test_task_dependency tests.test_task_scheduler -v
```

V2:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest tests.test_task_run_state tests.test_sqlite_task_run_state tests.test_agent_execution_result tests.test_agent_execution_journal -v
```

V3: `git diff --check`

V4: offline local JSON Schema validation of exactly this task.yaml against
schemas/task.schema.json via yaml.safe_load and jsonschema.Draft202012Validator;
no resolver network access or repository enumeration. The exact literal command:

```powershell
$itru063TaskCheck = @'
from pathlib import Path
import json, yaml
from jsonschema import Draft202012Validator
schema = json.loads(Path('schemas/task.schema.json').read_text(encoding='utf-8'))
task = yaml.safe_load(Path('.ai/tasks/ITRU-063-minimal-dag-scheduler-foundation/task.yaml').read_text(encoding='utf-8'))
Draft202012Validator.check_schema(schema)
Draft202012Validator(schema).validate(task)
print('ITRU063_TASK_SCHEMA_PASS')
'@
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -c $itru063TaskCheck
```

Success requires exit 0, all tests pass, zero skipped tests and fixture cleanup
absence receipts. Repeat only for failures, relevant changes or review remedies.
No aggregate verification, discovery, broad lint or final gates during this cycle.

## Exact review and audit read whitelist

The ten changed paths above; AGENTS.md; .ai/project.yaml;
core/principles.md; core/terminology.md; core/precedence.md;
core/human-control.md; core/task-specification.md;
core/task-run-state-specification.md; core/assignment-specification.md;
core/agent-execution-result-specification.md;
core/agent-execution-journal-specification.md;
workflows/standard-change.yaml; roles/architect.yaml; roles/software-engineer.yaml;
roles/reviewer.yaml; roles/security-reviewer.yaml;
quality-gates/documentation-consistency.md; quality-gates/independent-review.md
(definitions only, no final-gate evaluation);
itru/task_run_state.py; itru/sqlite_task_run_state.py; itru/assignment.py;
itru/agent_execution_run.py; itru/agent_execution_contract.py;
itru/agent_operation_tool_binding.py; itru/authorization_domain_ownership.py;
itru/agent_execution_result.py; itru/agent_execution_journal.py;
itru/_execution_entry_and_controlled_invocation.py;
itru/windows_local_authorization_domain_owner.py;
tests/test_task_run_state.py; tests/test_sqlite_task_run_state.py;
tests/test_agent_execution_result.py; tests/test_agent_execution_journal.py;
schemas/task.schema.json; pyproject.toml.

Five fresh independent specialist executions: DAG/architecture, deterministic
selection/concurrency, persistence/restart, authority/Assignment handoff, and
test/process/documentation. Maximum two reviewers concurrently. Read-only review;
no gate evaluation or reviewer edits. Each must inspect actual implementation,
relevant tests and evidence and give severity-coded findings plus recommendation.
Record exact reviewed fingerprints and follow-up reassessment after remediation.

## FINAL QUALITY GATE procedures frozen now (NOT EXECUTED)

Future execution requires explicit Human authorization. These definitions do not
evaluate either gate. No alternate procedure, new runtime validation or additional
review is implicitly authorized by a future gate-only request.

### FQ-DC-1 / documentation_consistency

Exact read whitelist: the ten implementation-whitelist files above and
quality-gates/documentation-consistency.md. No linked-path traversal.
Exact commands, in order:

```powershell
$itru063FinalFiles = @(
  '.ai/tasks/ITRU-063-minimal-dag-scheduler-foundation/task.yaml',
  '.ai/tasks/ITRU-063-minimal-dag-scheduler-foundation/context.md',
  '.ai/tasks/ITRU-063-minimal-dag-scheduler-foundation/acceptance-criteria.md',
  '.ai/tasks/ITRU-063-minimal-dag-scheduler-foundation/review.md',
  '.ai/tasks/ITRU-063-minimal-dag-scheduler-foundation/completion-report.md',
  'core/task-scheduler-specification.md',
  'itru/task_dependency.py',
  'itru/task_scheduler.py',
  'tests/test_task_dependency.py',
  'tests/test_task_scheduler.py',
  'quality-gates/documentation-consistency.md'
)
foreach ($itru063File in $itru063FinalFiles) {
  Write-Output ('READ ' + $itru063File)
  Get-Content -LiteralPath $itru063File -Encoding utf8 -ErrorAction Stop
}
$itru063Products = $itru063FinalFiles[5..9]
foreach ($itru063File in $itru063Products) {
  Get-FileHash -LiteralPath $itru063File -Algorithm SHA256 -ErrorAction Stop
}
```

DC-01 compare five hashes to the final retained validation/review receipt.
DC-02 compare exact graph identity/limits/cycles and ordering with implementation
and test coverage. DC-03 compare persisted-state readiness, all outcomes, missing
occupancy and definition checks. DC-04 compare bounded capacity and serialized
caller obligations without reservation/authority claims. DC-05 compare handoff,
fresh authority, Journal/Result boundaries and upstream preservation evidence.
DC-06 verify all five review identities, validation counts, remedies, severity
inventory and acceptance status agree across the five Task files. DC-07 verify
only G01/H01 may remain pending and no final approval/closure is claimed early.
Check referenced paths only by matching this locked inventory and retained
receipts; do not open link targets. A missing corroborating path receipt fails.

PASS iff all commands succeed, all five hashes match, DC-01..07 hold and no
unresolved material contradiction exists. FAIL on any mismatch, incomplete check,
missing evidence, unresolved Blocker/High or unsafe/ambiguous result; stop without
repair or expansion. Record check-by-check actual evidence, never infer a pass.

### FQ-IR-1 / independent_review

Execute only after FQ-DC-1 PASS. Exact read whitelist: the five Task files at
entries 1-5, plus quality-gates/independent-review.md. Exact commands:

```powershell
$itru063ReviewFiles = @(
  '.ai/tasks/ITRU-063-minimal-dag-scheduler-foundation/task.yaml',
  '.ai/tasks/ITRU-063-minimal-dag-scheduler-foundation/context.md',
  '.ai/tasks/ITRU-063-minimal-dag-scheduler-foundation/acceptance-criteria.md',
  '.ai/tasks/ITRU-063-minimal-dag-scheduler-foundation/review.md',
  '.ai/tasks/ITRU-063-minimal-dag-scheduler-foundation/completion-report.md',
  'quality-gates/independent-review.md'
)
foreach ($itru063File in $itru063ReviewFiles) {
  Write-Output ('READ ' + $itru063File)
  Get-Content -LiteralPath $itru063File -Encoding utf8 -ErrorAction Stop
}
```

IR-01 verify five distinct independent executions differ from implementer and
reviewed actual files on the five final product fingerprints. IR-02 compare
recorded scope/acceptance coverage and exact successful validation receipts.
IR-03 verify every finding disposition and required independent reassessment;
no unresolved Blocker/High or unremediated required change. IR-04 verify explicit
APPROVE from all five specialists on current scope; no self-approval substitution.
IR-05 verify FQ-DC-1 PASS, Task still in_progress and Human closure still pending.
PASS iff commands succeed and IR-01..05 all hold; otherwise FAIL and stop.

After authorized successful gate execution, update only the five Task evidence
files, mark G01, and read those same five files back using the exact IR command
with its final gate-definition entry omitted. Contradictory publication invalidates
the relevant gate; no silent fix. H01 and Task closure remain for separate Human
approval. No tests, new reviews, catalogs, broad reads, protected path access,
staging, commit, pull, push or merge is part of either final procedure.
