# ITRU-060 Review Record

## Explicit final Human approval and Task closure — 2026-10-14

Human authorization: "APPROVE ITRU-060 FINAL CLOSURE." The Human explicitly
granted final approval and authorized closure updates only. The final Human
decision accepts the historical Medium process incident as NON-BLOCKING,
S-H1 remediation, G-L1 remediation, documentation_consistency PASS and
independent_review PASS. This is the actual Human decision, not inferred approval
from an Agent verdict, Result outcome or passing check.

Closure decision: ITRU-060 / SCRUM-16 canonical repository Task is COMPLETED.
task.yaml status completed; H2 checked; acceptance 18/18. Both required final
Quality Gates PASS. Six fresh specialists and the separate formal independent
review APPROVE. Final F1/F2/F3 PASS 12/29/2 with zero skips and exact final
C1/C2/C3 PASS receipts remain unchanged below; no validator/test is rerun or
modified for this closure-only phase. Those command receipts describe their
recorded pre-closure execution state, including C1's in_progress assertion.

Original Phase-1 Medium incident and its Human NON-BLOCKING disposition are
preserved exactly, not erased, minimized or recast as compliant behavior. Original
S-H1 HIGH/STOP, its remediation/independent resolution, G-L1 failed documentation
gate/traceback, four-space remediation and successful replay remain retained.
S-M1/F-M1/C-L1 findings and resolutions, all failed receipts, final gate outcomes
and formal independent approval remain intact. Final unresolved new Blocker/High/
Medium/Low: 0/0/0/0, plus the accepted historical NON-BLOCKING Medium.

Closure-only changed paths: the four existing canonical Task artifacts and a
purely documentary final-status note in the existing Result specification.
Context requires reconciliation because its prior current checkpoint states
17/18 and pending Human approval; it now records completed/18-of-18. Result
semantics and implementation/tests are unchanged. No search, catalog enumeration,
broad traversal or protected Workflow README access occurs.

No staging, commit, push, merge or next Task action is authorized or performed.
The reviewed ITRU-060 change is ready for one separately authorized local commit
limited to the original nine-file manifest, subject to the bounded working-tree
metadata checkpoint. Completion of this repository Task does not update Jira or
authorize Git operations. Stop after recording closure.

### Bounded working-tree and commit-scope checkpoint

Only the nine already-recorded Task paths were queried. Git optional index
writes, fsmonitor and untracked-directory scanning were disabled; no Task/
Workflow catalog or whole working tree was enumerated. Scoped status reports
one unstaged tracked modification, the controlled coordinator. The exact-path
index query contains only that coordinator at stage 0; the other eight known
scope files are not indexed. No scoped path is staged. This is a bounded scope
report, not a claim that the entire repository has no other changes.

All four production/test hashes match the final reviewed/passing fingerprints;
closure changed no implementation or tests. Ready for one local commit: YES,
limited to the exact manifest below and only after separate Git authorization.
No staging or commit was performed. Closure-turn changed files are the four
Task artifacts and the Result spec's documentary status note.

Exact future commit scope:

- `.ai/tasks/ITRU-060-canonical-result-foundation/task.yaml`
- `.ai/tasks/ITRU-060-canonical-result-foundation/context.md`
- `.ai/tasks/ITRU-060-canonical-result-foundation/acceptance-criteria.md`
- `.ai/tasks/ITRU-060-canonical-result-foundation/review.md`
- `core/agent-execution-result-specification.md`
- `itru/agent_execution_result.py`
- `itru/_execution_entry_and_controlled_invocation.py`
- `tests/test_agent_execution_result.py`
- `tests/test_controlled_execution_result.py`

Scoped status output:

```text
 M itru/_execution_entry_and_controlled_invocation.py

```

Exact-path index output:

```text
100644 fb6c678986ba02b62876037f754be8ed8b2bf356 0	itru/_execution_entry_and_controlled_invocation.py

```


## G-L1 remediation and final Quality Gate PASS — 2026-10-14

The Human authorized whitespace-only remediation of this review artifact, exact
C1-C3 replay and final evaluation of documentation_consistency followed by
independent_review. The remediation removed exactly four U+0020 trailing spaces,
one on each pre-remediation line 1321, 1328, 1333 and 1345. It changed no word,
indentation, line ending or other content. The original G-L1 failed-attempt prefix
was verified unchanged before writing. No unrelated formatting cleanup or
implementation/test/spec change occurred. G-L1 is RESOLVED by the exact C2 PASS;
its original LOW/blocking classification, failed gate and traceback remain below
unchanged as historical evidence. The historical accepted Medium is also retained
exactly and remains NON-BLOCKING, never rewritten as compliant behavior.

C1/C2/C3 were recovered directly from existing context.md command blocks and
matched the previously recorded command strings exactly. All three ran unchanged
and passed with exit 0. Existing safety inspection still applies: C1 reads only
current Task/schema/exact selected Workflow; C2 checks only five named artifacts
and the exact Result-schema absence; C3 validates the supplied Core spec/Task ID
through static functions, without living_files or catalog discovery. No search,
protected access, broad traversal, C4, aggregate/default validator, command
substitution or F1-F3 confidence rerun occurred.

Final gate evaluation:

| Required gate | Outcome | Evidence |
| --- | --- | --- |
| documentation_consistency | PASS | Exact C1/C2/C3 passed; current Task/spec contract, forty scenario identities, namespace, artifact structure/whitespace and truthful phase/finding evidence are consistent |
| independent_review | PASS | Existing six fresh specialists, completed Process and separate /root/sh1_formal_independent_review APPROVE; original author is not approval authority; final reviewed/tested source unchanged |

The independent-review gate was evaluated only after documentation_consistency
passed. The existing formal reviewer independently checked final source hashes,
locked semantics/provenance/bindings, predecessor boundaries, 12/29/2 passing
receipts, safety inspection and retained incidents. Its verdict and all six
specialist APPROVE records remain valid; no new review or implementation change
was introduced by whitespace remediation. S-H1/S-M1/F-M1/C-L1 remain resolved.
New unresolved Blocker/High/Medium/Low: 0/0/0/0. G-L1 is closed, not erased.

Matching Task evidence updates are required by the recorded I3 closure criterion
and prior gate STOP/16-of-18 state: acceptance now marks I3 complete and records
17/18; Task/context current gate status is updated accordingly. These are only
corresponding closure-evidence updates, not semantic redesign. H2 remains
unchecked; task.yaml status remains in_progress. Both required gates PASS,
all remaining non-Human closure criteria satisfied YES, ready for final Human
approval YES. STOP at Human Control. No final Human approval, Task closure,
staging, commit, push, merge or next Task action occurred or is inferred.
Next authorization: explicit final Human approval and authorization to close
ITRU-060. Git actions remain separately unauthorized.

### Exact C1 replay and result

```powershell
@'
import json
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator
root = Path.cwd()
task_dir = root / '.ai/tasks/ITRU-060-canonical-result-foundation'
schema = json.loads((root / 'schemas/task.schema.json').read_text(encoding='utf-8'))
Draft202012Validator.check_schema(schema)
task = yaml.safe_load((task_dir / 'task.yaml').read_text(encoding='utf-8'))
Draft202012Validator(schema).validate(task)
assert task['id'] == 'ITRU-060' and task['status'] == 'in_progress'
assert task['execution']['mode'] == 'deep'
workflow = yaml.safe_load((root / 'workflows/standard-change.yaml').read_text(encoding='utf-8'))
assert task['workflow'] == workflow['id'] == 'standard-change'
assert any(stage.get('human_control_checkpoint') is True for stage in workflow['stages'])
assert set(task['quality_gates']) == {'documentation_consistency', 'independent_review'}
assert all(task['human_control'].values())
print('C1 PASS: exact current Task and selected Workflow; no catalog')
'@ | & 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -I -B -
```

Exit 0.

```text
C1 PASS: exact current Task and selected Workflow; no catalog

```

### Exact C2 replay and result

```powershell
@'
from pathlib import Path
import re
paths = (
    '.ai/tasks/ITRU-060-canonical-result-foundation/task.yaml',
    '.ai/tasks/ITRU-060-canonical-result-foundation/context.md',
    '.ai/tasks/ITRU-060-canonical-result-foundation/acceptance-criteria.md',
    '.ai/tasks/ITRU-060-canonical-result-foundation/review.md',
    'core/agent-execution-result-specification.md',
)
texts = {}
for path in paths:
    text = Path(path).read_text(encoding='utf-8')
    assert text and '\x00' not in text, path
    assert all(line == line.rstrip() for line in text.splitlines()), path
    if path.endswith('.md'):
        assert text.startswith('# ') and len(re.findall(r'^```', text, flags=re.M)) % 2 == 0, path
    texts[path] = text
context = texts[paths[1]]
ids = re.findall(r'^\| (R\d{2}) \|', context, flags=re.M)
assert ids == [f'R{n:02d}' for n in range(1, 41)], ids
assert len(set(ids)) == 40
spec = texts[paths[4]]
for literal in ('succeeded', 'failed_before_effect', 'effect_ambiguous', '65536', '65537', 'repository_file_read'):
    assert literal in spec, literal
assert not Path('schemas/agent-execution-result.schema.json').exists()
print('C2 PASS: five artifacts, whitespace/fences, 40 unique design rows, no Result schema')
'@ | & 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -I -B -
```

Exit 0.

```text
C2 PASS: five artifacts, whitespace/fences, 40 unique design rows, no Result schema

```

### Exact C3 replay and result

```powershell
@'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from tests.test_itru_namespace import check_namespace, new_task_candidate
path = 'core/agent-execution-result-specification.md'
findings = check_namespace({path: Path(path).read_text(encoding='utf-8')})
assert not findings, findings
assert new_task_candidate('ITRU-060', 'ITRU-060-canonical-result-foundation', cutover_closed=True)
print('C3 PASS: supplied Core spec and prospective Task ID; no catalog')
'@ | & 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -I -B -
```

Exit 0.

```text
C3 PASS: supplied Core spec and prospective Task ID; no catalog

```


## Final Quality Gate evaluation STOP — 2026-10-14

The Human authorized only the two named final gates and required STOP if either
fails. documentation_consistency: FAIL. Exact recovered C1 passed (exit 0), but
exact recovered C2 failed (exit 1) at its line-14 whitespace assertion for
`.ai/tasks/ITRU-060-canonical-result-foundation/review.md`. The assertion requires
each line to equal its rstrip() value; the current review artifact did not satisfy
that check. No specific offending line number is emitted by this unchanged
runner. No new diagnostic/search command or whitespace correction was performed.

G-L1: LOW documentation hygiene, blocking this gate. No new Blocker/High or
contract/implementation defect is established. The accepted historical Medium
remains NON-BLOCKING and exact; all original S-H1/S-M1/F-M1/C-L1 history remains.
The failed check and this new finding are retained, not silently repaired.

STOP occurred immediately after C2. C3 was recovered but NOT EXECUTED.
independent_review: NOT EVALUATED in this closure phase after the mandatory STOP;
its existing six-specialist and separate formal APPROVE evidence remains intact
and is not revoked or falsely reported as a final gate PASS. No F1/F2/F3 replay,
C4/default/aggregate command, protected access, catalog/traversal/search or Git
write occurred. Gate result: STOP, 0/2 final gate PASS outcomes established.

Acceptance remains 16/18. I3/H2 unchecked; Task remains in_progress. All remaining
non-Human closure criteria satisfied: NO. Ready for final Human approval: NO.
Next authorization: bounded whitespace-only remediation of the exact current
review.md, preservation of G-L1/C2 failure history, and replay of the exact
recorded C1-C3 plus final evaluation of both named gates under the same safety
boundary. Final Human approval, Task closure and Git actions remain separate.

### Exact C1 command and result

```powershell
@'
import json
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator
root = Path.cwd()
task_dir = root / '.ai/tasks/ITRU-060-canonical-result-foundation'
schema = json.loads((root / 'schemas/task.schema.json').read_text(encoding='utf-8'))
Draft202012Validator.check_schema(schema)
task = yaml.safe_load((task_dir / 'task.yaml').read_text(encoding='utf-8'))
Draft202012Validator(schema).validate(task)
assert task['id'] == 'ITRU-060' and task['status'] == 'in_progress'
assert task['execution']['mode'] == 'deep'
workflow = yaml.safe_load((root / 'workflows/standard-change.yaml').read_text(encoding='utf-8'))
assert task['workflow'] == workflow['id'] == 'standard-change'
assert any(stage.get('human_control_checkpoint') is True for stage in workflow['stages'])
assert set(task['quality_gates']) == {'documentation_consistency', 'independent_review'}
assert all(task['human_control'].values())
print('C1 PASS: exact current Task and selected Workflow; no catalog')
'@ | & 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -I -B -
```

Exit 0.

```text
C1 PASS: exact current Task and selected Workflow; no catalog

```

### Exact C2 command and failure

```powershell
@'
from pathlib import Path
import re
paths = (
    '.ai/tasks/ITRU-060-canonical-result-foundation/task.yaml',
    '.ai/tasks/ITRU-060-canonical-result-foundation/context.md',
    '.ai/tasks/ITRU-060-canonical-result-foundation/acceptance-criteria.md',
    '.ai/tasks/ITRU-060-canonical-result-foundation/review.md',
    'core/agent-execution-result-specification.md',
)
texts = {}
for path in paths:
    text = Path(path).read_text(encoding='utf-8')
    assert text and '\x00' not in text, path
    assert all(line == line.rstrip() for line in text.splitlines()), path
    if path.endswith('.md'):
        assert text.startswith('# ') and len(re.findall(r'^```', text, flags=re.M)) % 2 == 0, path
    texts[path] = text
context = texts[paths[1]]
ids = re.findall(r'^\| (R\d{2}) \|', context, flags=re.M)
assert ids == [f'R{n:02d}' for n in range(1, 41)], ids
assert len(set(ids)) == 40
spec = texts[paths[4]]
for literal in ('succeeded', 'failed_before_effect', 'effect_ambiguous', '65536', '65537', 'repository_file_read'):
    assert literal in spec, literal
assert not Path('schemas/agent-execution-result.schema.json').exists()
print('C2 PASS: five artifacts, whitespace/fences, 40 unique design rows, no Result schema')
'@ | & 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -I -B -
```

Exit 1.

```text
Traceback (most recent call last):
  File "<stdin>", line 14, in <module>
AssertionError: .ai/tasks/ITRU-060-canonical-result-foundation/review.md

```


## Human-authorized final Quality Gate evaluation — 2026-10-14

The Human authorizes evaluation only of documentation_consistency and
independent_review using existing exact ITRU-060 records/checks, with no search,
catalog enumeration, traversal or protected Workflow README access. Final Human
approval and Task closure remain unauthorized. I3 remains unchecked until both
gate outcomes are established; H2 remains unchecked throughout this phase.

Existing final tested-source hashes, F1/F2/F3 12/29/2 PASS receipts, six fresh
specialist approvals, completed Process and separate formal independent APPROVE
are recovered from the retained evidence. No implementation/test behavior changed
after these receipts. S-H1/S-M1/F-M1/C-L1 resolution and the verbatim accepted
historical Medium are preserved, including all original STOP/failure chronology.

Before execution, C1/C2/C3 were recovered exactly from the existing context.md
command blocks. C1 reads only current Task YAML, the recorded Task schema and
exact selected standard-change Workflow; schema references are local. C2 reads
only the five recorded Task/spec artifacts, validates whitespace/fences/forty
scenario rows/locked literals and checks the exact absent Result-schema path.
C3 uses the already-inspected static namespace module's supplied-file functions
on the one Core spec and exact Task ID; no living_files/catalog/test runner is
called. Imports/definitions perform no catalog or protected-target operation.
No command is reconstructed, substituted, broadened or newly invented.

The historic C4 Git-wide metadata commands are not executed: they are broader
repository scope/hygiene checks, not either named gate's bounded document or
independent-review evaluation, and cannot satisfy the latest no-traversal and
no-protected-access boundary. The Human's current gate-only restriction governs
over the retained Phase-1 future C1-C4 replay plan. No alternate Git command is
substituted and no Git outcome is claimed. Aggregate/hostile/default validators
remain HOLD. F1/F2/F3 are reused as completed evidence, not rerun for confidence.
Gate outcomes and exact C1-C3 receipts are pending.

## Final S-H1 remediation checkpoint at Human Control — 2026-10-14

ITRU-060 remains in_progress. Bounded Human-authorized remediation, exact
revalidation, six fresh specialist reviews and one separate formal independent
review are complete. No Task closure, final Human approval, staging, commit,
push, merge or next Task action occurred. Locked contract preserved; no design
contradiction. Original findings, initial verdicts, mandatory STOP, corrections,
failed receipts and the exact accepted incident remain retained below.

Root cause: frozen/slotted dataclass generated restoration hooks could overwrite
canonical fields, and original exact-object-only recognition did not detect
altered state. Fix rejects state extraction/restoration on Result/payload/
diagnostic and binds passive recognition to original published references and
typed immutable nested leaves. Detected mismatch permanently removes recognition;
reconstruction cannot inherit publication membership. Only original trusted
invocation still positively constructs Result. S-M1's temporary Run alias
assumption was corrected to capture the actual published Binding Run/Contract,
preserving complete value equality. All observed fixes stay in the locked design.

Current-turn production change: `itru/agent_execution_result.py`.
Current-turn test changes: `tests/test_agent_execution_result.py` and
`tests/test_controlled_execution_result.py`. The authorized coordinator remains
unchanged by S-H1/S-M1; its previous F-M1 fix is retained. Overall original Task
manifest remains two production/two tests/five Task/spec evidence files, with
no additional implementation path. Latest exact F1/F2/F3: PASS 12/12, 29/29,
2/2, zero skips; safety inspection, unchanged commands, complete receipts and
final four source hashes are retained in the next sections.

| Fresh specialist | Independent execution | Final verdict | Unresolved new B/H/M/L |
| --- | --- | --- | --- |
| Architect | /root/final060_architect | APPROVE | 0/0/0/0 |
| Result/Domain | /root/final060_domain | APPROVE | 0/0/0/0 |
| Security/Authority | /root/final060_security | APPROVE | 0/0/0/0 |
| Serialization/Schema | /root/final060_serialization | APPROVE | 0/0/0/0 |
| Compatibility/Regression | /root/final060_compatibility | APPROVE after justified rerun | 0/0/0/0 |
| Process/Validation Safety | /root/final060_process | APPROVE after fresh completion | 0/0/0/0 |

Six-specialist result: 6/6 APPROVE. Compatibility reran because standard
restoration/extraction rejection is observable behavior; it enforces the locked
immutable/no-format contract, preserving field shapes and value-equality APIs.

Formal independent review: /root/sh1_formal_independent_review, APPROVE.
The separate reviewer directly read current implementation/tests/spec/evidence
and exact necessary predecessors, verified all four hashes, source/receipt/safety
consistency and original S-H1 STOP plus verbatim discovery incident. It did not
adopt specialist verdicts as its own approval. It independently RESOLVES S-H1 and
S-M1, confirms exact ledger/Entry/Run/Tool binding, immutable terminal outcomes,
bounded bytes/no failure content, original-frame acknowledged construction,
scope-unwound publication and permanent Entry consumption. Existing native/JIT/
Admission/Claim-Lease/fencing/continuation/history/restart boundaries remain
unwidened. No trust bypass, serialized format/schema, persistence, Journal,
Task/Run state, scheduler/DAG, UI, new Tool, exactly-once claim or replay appears.
Formal unresolved findings: 0 Blocker / 0 High / 0 Medium / 0 Low.

Historical accepted process Medium remains NON-BLOCKING, exact and accurately
disclosed; S-H1, S-M1, F-M1 and C-L1 are independently RESOLVED, not erased.
Current aggregate unresolved Blocker/High/new Medium/Low: 0/0/0/0, plus one
historical Human-accepted NON-BLOCKING Medium. No review used search tools,
runtime imports/tests, unlisted context, protected access or edits; root alone
authored the bounded fixes/evidence and is not an approval authority.

Acceptance remains 16/18: I1/I2 complete, I3's review portion complete but separate
closure gate evaluation pending, H2 final Human approval pending. Quality Gate
readiness: READY for separate bounded closure evaluation. READY FOR FINAL HUMAN
CONTROL: YES. Next authorization: bounded final Quality Gate closure evaluation,
then explicit Human approval of Task closure after gates pass. Git actions remain
separately unauthorized. No gate closure or Human decision is inferred here.

Practical limits retained: cooperative trusted interpreter; no claim to detect
hostile raw mutation restored before observation; R26 is component restart/foreign
PID rather than subprocess crash; unchanged F3 runner does not print individual
nonces. Review approval and passing tests do not remove these limits or create
execution/replay/retention authority.

## S-M1 corrected-revision exact revalidation receipts — 2026-10-14

The corrective safety inspection in context.md preceded replay of the same exact retained F1-F3. The source changed after the initial S-H1 pass, so each exact command ran again once on this revision; no broad or extra confidence command. All passed with zero skips: F1 12/12, F2 29/29 including equal-but-distinct Run/Contract R19, F3 2/2. Both S-H1 and S-M1 source findings and initial passing receipts remain preserved. Security also independently confirmed S-M1 as Medium/blocking and withheld approval pending corrected-source recheck (0 Blocker/0 High/1 new Medium/0 Low). Neither root tests nor author correction approve resolution.

### Final remediation source fingerprints

```text


Path : D:\Dev\ai-engineering-orchestra\itru\agent_execution_result.py
Hash : FCD68E58B6940CED6063AC3B9D504B6D451E452541449B12F76BE1212A5E44C1

Path : D:\Dev\ai-engineering-orchestra\itru\_execution_entry_and_controlled_invocation.py
Hash : 243B66E330E74EACA82DDB65B14B2891EEE79182B5995BF679A5E7E35175E22D

Path : D:\Dev\ai-engineering-orchestra\tests\test_agent_execution_result.py
Hash : 89AFB795FE9A83DC14110B734829871F769A42727CFF52F10EC39B86DD25B6E7

Path : D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py
Hash : ABA600EDE6EFDDD05DE76CD834377A55459C45D8045D5DB83E494ED2AFFEE29C




```

### F1 unchanged command and complete corrective output

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -I -B -c "import sys, pathlib, unittest; sys.path.insert(0, str(pathlib.Path.cwd())); suite = unittest.defaultTestLoader.loadTestsFromName('tests.test_agent_execution_result.ResultContractTests'); result = unittest.TextTestRunner(verbosity=2).run(suite); sys.exit(0 if result.wasSuccessful() and result.testsRun == 12 and not result.skipped else 1)"
```

Exit 0.

```text
test_R16_unsupported_private_taxonomy (tests.test_agent_execution_result.ResultContractTests.test_R16_unsupported_private_taxonomy) ... ok
test_R17_malformed_success_is_sanitized (tests.test_agent_execution_result.ResultContractTests.test_R17_malformed_success_is_sanitized) ... ok
test_R28_construction_copy_and_subclass_are_rejected (tests.test_agent_execution_result.ResultContractTests.test_R28_construction_copy_and_subclass_are_rejected) ... ok
test_R29_closed_diagnostics_only (tests.test_agent_execution_result.ResultContractTests.test_R29_closed_diagnostics_only) ... ok
test_R30_unsuccessful_content_is_rejected (tests.test_agent_execution_result.ResultContractTests.test_R30_unsuccessful_content_is_rejected) ... ok
test_R31_exact_payload_types (tests.test_agent_execution_result.ResultContractTests.test_R31_exact_payload_types) ... ok
test_R36_reports_have_no_trust_or_deserializer (tests.test_agent_execution_result.ResultContractTests.test_R36_reports_have_no_trust_or_deserializer) ... ok
test_R37_physical_identity_does_not_replace_evidence (tests.test_agent_execution_result.ResultContractTests.test_R37_physical_identity_does_not_replace_evidence) ... ok
test_R38_empty_success_is_not_absent (tests.test_agent_execution_result.ResultContractTests.test_R38_empty_success_is_not_absent) ... ok
test_R39_code_outcome_coherence (tests.test_agent_execution_result.ResultContractTests.test_R39_code_outcome_coherence) ... ok
test_R40_immutable_evidence_has_no_execution_api (tests.test_agent_execution_result.ResultContractTests.test_R40_immutable_evidence_has_no_execution_api) ... ok
test_closed_shape (tests.test_agent_execution_result.ResultContractTests.test_closed_shape) ... ok

----------------------------------------------------------------------
Ran 12 tests in 0.001s

OK

```

### F2 unchanged command and complete corrective output

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -I -B -c "import sys, pathlib, unittest; sys.path.insert(0, str(pathlib.Path.cwd())); suite = unittest.defaultTestLoader.loadTestsFromName('tests.test_controlled_execution_result.ControlledResultScenarios'); result = unittest.TextTestRunner(verbosity=2).run(suite); sys.exit(0 if result.wasSuccessful() and result.testsRun == 29 and not result.skipped else 1)"
```

Exit 0.

```text
test_R01_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R01_success) ... ITRU060_FIXTURE test_R01_success parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-ip1m9qgw registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-ip1m9qgw\local-appdata ledger=ledger::itru-060::05ffaace26184f6d9d602049d69cc811
ok
test_R02_empty_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R02_empty_success) ... ITRU060_FIXTURE test_R02_empty_success parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-of07y7jp registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-of07y7jp\local-appdata ledger=ledger::itru-060::dcf74167827c4c0ab5c82dbcd0701758
ok
test_R03_maximum_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R03_maximum_success) ... ITRU060_FIXTURE test_R03_maximum_success parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-it3x1sg4 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-it3x1sg4\local-appdata ledger=ledger::itru-060::0e45b8e583034dc38bd8d96709ecdad5
ok
test_R04_pre_read_size_limit (tests.test_controlled_execution_result.ControlledResultScenarios.test_R04_pre_read_size_limit) ... ITRU060_FIXTURE test_R04_pre_read_size_limit parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-lp725_7x registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-lp725_7x\local-appdata ledger=ledger::itru-060::73a64bdcb04c489eaf0b3d0bd8af0db9
ok
test_R05_missing_resource (tests.test_controlled_execution_result.ControlledResultScenarios.test_R05_missing_resource) ... ITRU060_FIXTURE test_R05_missing_resource parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-wuxmolgp registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-wuxmolgp\local-appdata ledger=ledger::itru-060::aeae12dbe8a5479aabb09f6fb4793896
ok
test_R06_containment_rejection (tests.test_controlled_execution_result.ControlledResultScenarios.test_R06_containment_rejection) ... ITRU060_FIXTURE test_R06_containment_rejection parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-ndz3km2z registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-ndz3km2z\local-appdata ledger=ledger::itru-060::3616a6c785684a24b3ab5695b2be6155
ok
test_R07_adapter_unavailable (tests.test_controlled_execution_result.ControlledResultScenarios.test_R07_adapter_unavailable) ... ITRU060_FIXTURE test_R07_adapter_unavailable parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-q4j3ij09 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-q4j3ij09\local-appdata ledger=ledger::itru-060::778ce361c5c94d21a8c10dca621d3922
ok
test_R08_proven_pre_content_read_failure (tests.test_controlled_execution_result.ControlledResultScenarios.test_R08_proven_pre_content_read_failure) ... ITRU060_FIXTURE test_R08_proven_pre_content_read_failure parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-8db3wn28 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-8db3wn28\local-appdata ledger=ledger::itru-060::8494fc438c2c41f5b2e268c7d5238428
ok
test_R09_proven_pre_content_resource_changed (tests.test_controlled_execution_result.ControlledResultScenarios.test_R09_proven_pre_content_resource_changed) ... ITRU060_FIXTURE test_R09_proven_pre_content_resource_changed parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-6ebgyx5z registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-6ebgyx5z\local-appdata ledger=ledger::itru-060::9315bb78984c4044b79a07ff8c8d0982
ok
test_R10_guard_lost_before_start (tests.test_controlled_execution_result.ControlledResultScenarios.test_R10_guard_lost_before_start) ... ITRU060_FIXTURE test_R10_guard_lost_before_start parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-i3tco9oe registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-i3tco9oe\local-appdata ledger=ledger::itru-060::deb7e25db7bb40adb32eb17c9b107455
ok
test_R11_ownership_lost_before_start (tests.test_controlled_execution_result.ControlledResultScenarios.test_R11_ownership_lost_before_start) ... ITRU060_FIXTURE test_R11_ownership_lost_before_start parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-v2plj10g registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-v2plj10g\local-appdata ledger=ledger::itru-060::9b5a713161b54933ae31bfe71f32caec
ok
test_R12_post_request_failure_codes (tests.test_controlled_execution_result.ControlledResultScenarios.test_R12_post_request_failure_codes) ... ITRU060_FIXTURE test_R12_post_request_failure_codes parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-jrehxfn6 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-jrehxfn6\local-appdata ledger=ledger::itru-060::07de423da1a74508b58e171e45ccc9b5
ITRU060_FIXTURE test_R12_post_request_failure_codes parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-81_cx0gc registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-81_cx0gc\local-appdata ledger=ledger::itru-060::3de7d96d450e48dbbdb501c5fafbb1c5
ok
test_R13_final_metadata_changed (tests.test_controlled_execution_result.ControlledResultScenarios.test_R13_final_metadata_changed) ... ITRU060_FIXTURE test_R13_final_metadata_changed parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-lfi82sus registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-lfi82sus\local-appdata ledger=ledger::itru-060::728edbb5ce294ae68b051eceb0bd05c6
ok
test_R14_outer_ownership_postcheck (tests.test_controlled_execution_result.ControlledResultScenarios.test_R14_outer_ownership_postcheck) ... ITRU060_FIXTURE test_R14_outer_ownership_postcheck parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-hfhepwod registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-hfhepwod\local-appdata ledger=ledger::itru-060::98386ec90aa043a390deb2c8ac1419dd
ok
test_R15_cleanup_dominates_no_content (tests.test_controlled_execution_result.ControlledResultScenarios.test_R15_cleanup_dominates_no_content) ... ITRU060_FIXTURE test_R15_cleanup_dominates_no_content parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-rjr4nll_ registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-rjr4nll_\local-appdata ledger=ledger::itru-060::350d1982509c47c2ad7bf71a5b5a77b6
ok
test_R18_reconstructed_entry_is_not_acknowledgement (tests.test_controlled_execution_result.ControlledResultScenarios.test_R18_reconstructed_entry_is_not_acknowledgement) ... ITRU060_FIXTURE test_R18_reconstructed_entry_is_not_acknowledgement parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-qy51newh registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-qy51newh\local-appdata ledger=ledger::itru-060::f8b611f163cb48d4baf5d749f6da7697
ok
test_R19_same_run_id_changed_contract (tests.test_controlled_execution_result.ControlledResultScenarios.test_R19_same_run_id_changed_contract) ... ITRU060_FIXTURE test_R19_same_run_id_changed_contract parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-sdis84at registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-sdis84at\local-appdata ledger=ledger::itru-060::4ab0eed59fdc48c4bac6b04d55c0b0a5
ITRU060_FIXTURE test_R19_same_run_id_changed_contract parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-tkayqvth registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-tkayqvth\local-appdata ledger=ledger::itru-060::ce09f9b3e56d47abbe7b8269646f016b
ITRU060_FIXTURE test_R19_same_run_id_changed_contract parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-g5oad_w4 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-g5oad_w4\local-appdata ledger=ledger::itru-060::f054a5d8d71a4243a2398583a4ebcc44
ok
test_R20_tool_substitution (tests.test_controlled_execution_result.ControlledResultScenarios.test_R20_tool_substitution) ... ITRU060_FIXTURE test_R20_tool_substitution parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-gxwxpo48 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-gxwxpo48\local-appdata ledger=ledger::itru-060::0560c3a149224ade8b689f7d79c686bc
ok
test_R21_ledger_scoping_and_foreign_subject (tests.test_controlled_execution_result.ControlledResultScenarios.test_R21_ledger_scoping_and_foreign_subject) ... ITRU060_FIXTURE test_R21_ledger_scoping_and_foreign_subject parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-33kkhjkd registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-33kkhjkd\local-appdata ledger=ledger::itru-060::36cc429ba89c4d2eaa7cce3c8c602f29
ITRU060_FIXTURE test_R21_ledger_scoping_and_foreign_subject parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-m9k5nds_ registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-m9k5nds_\local-appdata ledger=ledger::itru-060::1b69fd2054d840839b9e44b817001d6a
ITRU060_FIXTURE test_R21_ledger_scoping_and_foreign_subject parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-akr7v2av registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-akr7v2av\local-appdata ledger=ledger::itru-060::df0debbf62ad452d9ce3720d4c4f8f4e
ok
test_R22_exact_claim_executor_generation (tests.test_controlled_execution_result.ControlledResultScenarios.test_R22_exact_claim_executor_generation) ... ITRU060_FIXTURE test_R22_exact_claim_executor_generation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-oj4n6efk registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-oj4n6efk\local-appdata ledger=ledger::itru-060::ea480ff780ab426188f46f5b2805ba0d
ITRU060_FIXTURE test_R22_exact_claim_executor_generation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-zybft2l1 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-zybft2l1\local-appdata ledger=ledger::itru-060::4c2bab2a93794448bb520efe7d96edc8
ITRU060_FIXTURE test_R22_exact_claim_executor_generation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-qvrklha7 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-qvrklha7\local-appdata ledger=ledger::itru-060::43b23a58cfef4847aee059b35c79675f
ok
test_R23_rejected_entry_preserves_diagnostic (tests.test_controlled_execution_result.ControlledResultScenarios.test_R23_rejected_entry_preserves_diagnostic) ... ITRU060_FIXTURE test_R23_rejected_entry_preserves_diagnostic parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-k6xdpm8j registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-k6xdpm8j\local-appdata ledger=ledger::itru-060::8dbe5a9b9e4343ebbc678488df50bf9f
ITRU060_FIXTURE test_R23_rejected_entry_preserves_diagnostic parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-gwhllrgb registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-gwhllrgb\local-appdata ledger=ledger::itru-060::891292d9d16f419f83439a039f8de2fe
ITRU060_FIXTURE test_R23_rejected_entry_preserves_diagnostic parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-whzu6e5u registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-whzu6e5u\local-appdata ledger=ledger::itru-060::a29e77b9c4e244a9a6842cbed06be87e
ok
test_R24_commit_unknown_no_result_or_effect (tests.test_controlled_execution_result.ControlledResultScenarios.test_R24_commit_unknown_no_result_or_effect) ... ITRU060_FIXTURE test_R24_commit_unknown_no_result_or_effect parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-l981vgh5 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-l981vgh5\local-appdata ledger=ledger::itru-060::ec4233eff5c84c3b9800596874f62dd2
ok
test_R25_history_has_no_result_factory (tests.test_controlled_execution_result.ControlledResultScenarios.test_R25_history_has_no_result_factory) ... ITRU060_FIXTURE test_R25_history_has_no_result_factory parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-__xm1f3y registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-__xm1f3y\local-appdata ledger=ledger::itru-060::44c71d8715fc4b2f93731e5053294306
ok
test_R26_component_restart_never_recovers_invocation (tests.test_controlled_execution_result.ControlledResultScenarios.test_R26_component_restart_never_recovers_invocation) ... ITRU060_FIXTURE test_R26_component_restart_never_recovers_invocation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-5r1un66z registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-5r1un66z\local-appdata ledger=ledger::itru-060::f9fce8dc3f044ee99fd93caee12570a0
ok
test_R27_repeated_invocation_cannot_publish_again (tests.test_controlled_execution_result.ControlledResultScenarios.test_R27_repeated_invocation_cannot_publish_again) ... ITRU060_FIXTURE test_R27_repeated_invocation_cannot_publish_again parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-shxlieux registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-shxlieux\local-appdata ledger=ledger::itru-060::340274373a9b434080bd65998810765b
ok
test_R32_historical_and_noncanonical_work_rejected (tests.test_controlled_execution_result.ControlledResultScenarios.test_R32_historical_and_noncanonical_work_rejected) ... ITRU060_FIXTURE test_R32_historical_and_noncanonical_work_rejected parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-xu23401z registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-xu23401z\local-appdata ledger=ledger::itru-060::d4d1696ab2f94390989d26ceeaa25d86
ITRU060_FIXTURE test_R32_historical_and_noncanonical_work_rejected parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-_aou8ug6 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-_aou8ug6\local-appdata ledger=ledger::itru-060::bac44f9ee0684ddc902e24a0727ad36e
ok
test_R33_fatal_interruption_preserved (tests.test_controlled_execution_result.ControlledResultScenarios.test_R33_fatal_interruption_preserved) ... ITRU060_FIXTURE test_R33_fatal_interruption_preserved parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-379xron9 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-379xron9\local-appdata ledger=ledger::itru-060::42812c9e603f4977a6cc5dac0b1a9331
ok
test_R34_success_suppressed_by_cleanup_or_construction (tests.test_controlled_execution_result.ControlledResultScenarios.test_R34_success_suppressed_by_cleanup_or_construction) ... ITRU060_FIXTURE test_R34_success_suppressed_by_cleanup_or_construction parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-7unf144f registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-7unf144f\local-appdata ledger=ledger::itru-060::ccd176a881714709a3067bc0ccf14345
ITRU060_FIXTURE test_R34_success_suppressed_by_cleanup_or_construction parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-4fs_mejg registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-4fs_mejg\local-appdata ledger=ledger::itru-060::fe3ae54cb565438e969796b53bae1adc
ok
test_R35_first_request_and_empty_probe_failure (tests.test_controlled_execution_result.ControlledResultScenarios.test_R35_first_request_and_empty_probe_failure) ... ITRU060_FIXTURE test_R35_first_request_and_empty_probe_failure parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-sx6kcvg7 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-sx6kcvg7\local-appdata ledger=ledger::itru-060::deaca635d391470f897bebe58894c820
ITRU060_FIXTURE test_R35_first_request_and_empty_probe_failure parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-hry9g37p registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-hry9g37p\local-appdata ledger=ledger::itru-060::2ed158ec70634e90a87f9f82374b93be
ok

----------------------------------------------------------------------
Ran 29 tests in 17.612s

OK

```

### F3 unchanged command and complete corrective output

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -I -B -c "import sys, pathlib, unittest; sys.path.insert(0, str(pathlib.Path.cwd())); suite = unittest.defaultTestLoader.loadTestsFromName('tests.test_durable_execution_entry_and_controlled_invocation.ItruControlledInvocationIdentityTests'); result = unittest.TextTestRunner(verbosity=2).run(suite); sys.exit(0 if result.wasSuccessful() and result.testsRun == 2 and not result.skipped else 1)"
```

Exit 0.

```text
test_historical_capability_and_legacy_binding_cannot_enter_or_invoke (tests.test_durable_execution_entry_and_controlled_invocation.ItruControlledInvocationIdentityTests.test_historical_capability_and_legacy_binding_cannot_enter_or_invoke) ... ok
test_itru_binding_executes_the_original_chain_once (tests.test_durable_execution_entry_and_controlled_invocation.ItruControlledInvocationIdentityTests.test_itru_binding_executes_the_original_chain_once) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.772s

OK

```


## S-M1 fresh review finding and bounded correction — 2026-10-14

/root/final060_serialization independently resolved S-H1's direct restoration
path but returned CHANGES REQUIRED for S-M1: MEDIUM, blocking closure, 0 Blocker /
0 High / 1 new Medium / 0 Low. Initial remediation publication captured the
subject Run/Contract identities while recognition required the published binding
to share them. Existing exact binding means complete value equality, and the
existing subject path permits equal-but-distinct Run/Contract objects. An unchanged
valid Result could therefore be rejected. The first S-H1 passing receipts below
did not cover this alias case; those receipts and verdict remain historical.

Author correction changes only the two capture expressions to the actual
published binding's Run/Contract references. Existing R19 adds an equal/distinct
Run and Contract via dataclass replacement, genuine trusted successful invocation,
and negative recognition for later equal-valued binding Run replacement followed
by restoration. No semantic redesign or new authority/construction route.
It uses one additional call to the same recorded plain owned rig within R19;
no new harness, resource, import, test identity, command or target class is added.
Independent recheck and revised exact F1-F3 receipts are pending. S-M1 is not
author-approved or erased; only its independent reviewer may resolve it.

## Current S-H1 remediation review ledger — 2026-10-14

Human-authorized remediation is implemented and exact F1/F2/F3 passed 12/29/2,
zero skips. Fresh independent verdicts below are required; earlier approvals
and the author's tests do not resolve S-H1. Source fingerprints and complete
current receipts are in the next section. Root authors implementation/evidence
and cannot approve it. All review uses the retained exact whitelist, literal
reads/allowed hashes, no search/discovery/runtime/edits/protected access.

| Fresh remediation specialist | Independent execution | Verdict | Blocker | High | New Medium | Low |
| --- | --- | --- | --- | --- | --- | --- |
| Architect | /root/final060_architect | APPROVE; S-H1 and S-M1 independently RESOLVED | 0 | 0 | 0 | 0 |
| Result/Domain | /root/final060_domain | APPROVE; S-H1 and S-M1 independently RESOLVED | 0 | 0 | 0 | 0 |
| Security/Authority | /root/final060_security | APPROVE; S-H1 and S-M1 independently RESOLVED | 0 | 0 | 0 | 0 |
| Serialization/Schema | /root/final060_serialization | APPROVE; S-H1 and S-M1 independently RESOLVED | 0 | 0 | 0 | 0 |
| Compatibility/Regression | /root/final060_compatibility | APPROVE after rerun; evidence Low independently RESOLVED | 0 | 0 | 0 | 0 |
| Process/Validation Safety | /root/final060_process | APPROVE; resumed fresh complete remediation review | 0 | 0 | 0 | 0 |

Six of six fresh remediation specialists APPROVE, zero unresolved new findings.
Separate formal independent review: /root/sh1_formal_independent_review APPROVE,
zero unresolved findings; separate closure gate evaluation/Human approval pending.

Process independently completed its fresh resumed review: APPROVE, zero new
Blocker/High/Medium/Low. It verified exact four source/test and five evidence
paths, authorization before safety inspection/reruns, unchanged twelve/twenty-nine
test identities and forty scenario rows, final fingerprints and exact 12/29/2
receipts with zero skips. S-H1 mandatory STOP, S-M1 initial CHANGES REQUIRED,
F-M1/failing-receipt chronology and the verbatim historical discovery incident
remain accurate. The accepted Medium remains NON-BLOCKING, never rewritten as
compliance. Retained transitive safety inspection, F3 nonce-output limitation and
R26 component-restart limitation remain explicit. Acceptance 16/18 is accurate;
I3/H2 and Task closure/closure gate evaluation/final Human approval remain pending.
Only whitelist literal reads/four hashes, no search/runtime/edit/discovery or
protected access. Process confirms readiness for separate formal review.

Compatibility rerun APPROVE on the final tested revision. It independently
verified observable hook rejection enforces the existing immutable/no-format
contract, preserves six-field/equality/payload/diagnostic and legacy coordinator
APIs, accepts original equal/distinct Run/Contract values and rejects later
replacement. Existing Entry/Admission/Claim-Lease/fencing/JIT/continuation/fatal/
history boundaries and F-M1 correction remain intact. Four current fingerprints
match exact latest F1/F2/F3 receipts. No implementation findings.

C-L1: LOW, NON-BLOCKING evidence wording noted by Compatibility: a current pending
sentence conflicted with the current Architect/Domain approvals. Root corrected
that sentence and recorded the original note/correction below. Compatibility
independently read the exact corrected evidence slice and marked C-L1 RESOLVED;
APPROVE retained, zero unresolved new findings. No source rerun or extra validation
was needed; all initial finding/incident/STOP chronology remains intact.

Serialization and Security independently rechecked the final corrected source,
R19 and all four fingerprints against the latest exact passing receipts. Both
APPROVE with zero unresolved new findings and explicitly RESOLVE S-H1 and S-M1.
Result lines 282-283 capture the actual published Binding Run/Contract, preserving
the complete-value equality contract. R19 proves genuine equal/distinct values,
successful authoritative publication and permanent rejection after later
replacement/restoration. Explicit state hooks reject on Result/payload/diagnostic;
membership checks exact references, typed leaves and original object provenance.
Security retains the locked cooperative interpreter limit: no OS sandbox or
detection of raw mutations restored before observation is claimed. The rejected
provided hooks cannot perform such mutation; hostile raw interpreter manipulation
remains outside the locked boundary. No new positive authority or excluded scope.
Result/Domain separately read the full current Result/coordinator/test/spec/
evidence surface and confirmed the four final fingerprints and 12/29/2 receipts.
APPROVE, zero unresolved new findings; independently RESOLVES S-H1 and S-M1.
It checked all six fields, ledger identity and complete binding, nested exact
types, all three terminal/content/diagnostic dispositions, absence/history/
restart and unchanged forty scenario identities. R26's component-restart limit
and the raw-hostile-interpreter limit remain explicit. No search/runtime/edit/
protected access or closure/Human approval was performed.

These are current independent approvals; earlier HIGH/Medium/CHANGES REQUIRED
records remain intact. All six specialists and separate formal review APPROVE,
without Task closure, closure gate evaluation or final Human approval.
Compatibility noted a non-blocking stale pending-status sentence here; root
reconciled this current wording to the actual approvals without changing any
production/test source or historical finding/STOP evidence. Compatibility will
independently confirm that evidence correction in its final verdict.
Historical Medium remains Human-accepted NON-BLOCKING; F-M1 remains resolved.
Original S-H1 HIGH and mandatory STOP remain intact below. Architect, Domain,
Security and Serialization independently RESOLVE S-H1/S-M1 and APPROVE the
final tested revision. I1 is complete again; I3/H2 remain unchecked (16/18).
Task remains in_progress,
and final closure evaluation/Human approval/Git writes are unperformed.

Architect fresh final remediation review APPROVE, zero unresolved new findings
and no architectural contradiction. It verified rejecting hooks, all exact
published references and typed leaves, original construction/acknowledgement,
R19 value-equality compatibility, and retirement clearing every live execution
reference. Retained state is descriptive/passive only: no Store, capability,
frame, native handle or recovery authority. Four fingerprints and exact receipts
match. This independent verdict grants no Task closure, final Quality Gate
closure approval or Human final approval. Five technical reviews now APPROVE;
Formal review subsequently APPROVED after Process completion.

## S-H1 exact revalidation receipts — 2026-10-14

Recorded safety inspection in context.md preceded all three commands. Each was recovered exactly from existing evidence, matched the retained command byte-for-byte and ran once for S-H1. All passed with zero skips and no failed S-H1 attempt: F1 12/12, F2 29/29, F3 2/2. F2/F3 used the same previously approved sandbox escalation boundary for owned disposable synthetic fixtures/native ancestor metadata; no automatic approval rejection occurred. Complete outputs below retain F2 parent/registry/ledger nonces and the unchanged F3 nonce-output limitation. No extra validation command, discovery or catalog/protected-target access occurred.

### Tested source fingerprints

```text


Path : D:\Dev\ai-engineering-orchestra\itru\agent_execution_result.py
Hash : EDCF93FC9D71F6A60D6E5EE0089A34C605D50FDA4523C202977B402CDCFE659D

Path : D:\Dev\ai-engineering-orchestra\itru\_execution_entry_and_controlled_invocation.py
Hash : 243B66E330E74EACA82DDB65B14B2891EEE79182B5995BF679A5E7E35175E22D

Path : D:\Dev\ai-engineering-orchestra\tests\test_agent_execution_result.py
Hash : 89AFB795FE9A83DC14110B734829871F769A42727CFF52F10EC39B86DD25B6E7

Path : D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py
Hash : CE6BF5C34E2FD62B3D3858219E7ADCA74674E28CB83458293C9E75A37BDEC75E




```

Current-turn implementation/test changes are exactly `itru/agent_execution_result.py`, `tests/test_agent_execution_result.py`, `tests/test_controlled_execution_result.py`. Coordinator's fingerprint remains the F-M1 passing revision, unchanged by S-H1. Overall ITRU-060 manifest remains the original two production/two test/five evidence paths; current remediation adds no path. Root author evidence only; independent resolution is pending.

### F1 exact command and result

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -I -B -c "import sys, pathlib, unittest; sys.path.insert(0, str(pathlib.Path.cwd())); suite = unittest.defaultTestLoader.loadTestsFromName('tests.test_agent_execution_result.ResultContractTests'); result = unittest.TextTestRunner(verbosity=2).run(suite); sys.exit(0 if result.wasSuccessful() and result.testsRun == 12 and not result.skipped else 1)"
```

Exit 0.

```text
test_R16_unsupported_private_taxonomy (tests.test_agent_execution_result.ResultContractTests.test_R16_unsupported_private_taxonomy) ... ok
test_R17_malformed_success_is_sanitized (tests.test_agent_execution_result.ResultContractTests.test_R17_malformed_success_is_sanitized) ... ok
test_R28_construction_copy_and_subclass_are_rejected (tests.test_agent_execution_result.ResultContractTests.test_R28_construction_copy_and_subclass_are_rejected) ... ok
test_R29_closed_diagnostics_only (tests.test_agent_execution_result.ResultContractTests.test_R29_closed_diagnostics_only) ... ok
test_R30_unsuccessful_content_is_rejected (tests.test_agent_execution_result.ResultContractTests.test_R30_unsuccessful_content_is_rejected) ... ok
test_R31_exact_payload_types (tests.test_agent_execution_result.ResultContractTests.test_R31_exact_payload_types) ... ok
test_R36_reports_have_no_trust_or_deserializer (tests.test_agent_execution_result.ResultContractTests.test_R36_reports_have_no_trust_or_deserializer) ... ok
test_R37_physical_identity_does_not_replace_evidence (tests.test_agent_execution_result.ResultContractTests.test_R37_physical_identity_does_not_replace_evidence) ... ok
test_R38_empty_success_is_not_absent (tests.test_agent_execution_result.ResultContractTests.test_R38_empty_success_is_not_absent) ... ok
test_R39_code_outcome_coherence (tests.test_agent_execution_result.ResultContractTests.test_R39_code_outcome_coherence) ... ok
test_R40_immutable_evidence_has_no_execution_api (tests.test_agent_execution_result.ResultContractTests.test_R40_immutable_evidence_has_no_execution_api) ... ok
test_closed_shape (tests.test_agent_execution_result.ResultContractTests.test_closed_shape) ... ok

----------------------------------------------------------------------
Ran 12 tests in 0.001s

OK

```

### F2 exact command and result

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -I -B -c "import sys, pathlib, unittest; sys.path.insert(0, str(pathlib.Path.cwd())); suite = unittest.defaultTestLoader.loadTestsFromName('tests.test_controlled_execution_result.ControlledResultScenarios'); result = unittest.TextTestRunner(verbosity=2).run(suite); sys.exit(0 if result.wasSuccessful() and result.testsRun == 29 and not result.skipped else 1)"
```

Exit 0.

```text
test_R01_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R01_success) ... ITRU060_FIXTURE test_R01_success parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-zzaay23a registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-zzaay23a\local-appdata ledger=ledger::itru-060::3af00d4d82fb4579b0e2dcdb5f63b968
ok
test_R02_empty_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R02_empty_success) ... ITRU060_FIXTURE test_R02_empty_success parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-cade0cfg registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-cade0cfg\local-appdata ledger=ledger::itru-060::6909e90833394ea3baecdb10051dbf8d
ok
test_R03_maximum_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R03_maximum_success) ... ITRU060_FIXTURE test_R03_maximum_success parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-1dhkdiet registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-1dhkdiet\local-appdata ledger=ledger::itru-060::35d2b1580fd44a888d5801b9a4bd5f5b
ok
test_R04_pre_read_size_limit (tests.test_controlled_execution_result.ControlledResultScenarios.test_R04_pre_read_size_limit) ... ITRU060_FIXTURE test_R04_pre_read_size_limit parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-ml53ba83 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-ml53ba83\local-appdata ledger=ledger::itru-060::97db202707da49a68c23e2ee6b9d2fe1
ok
test_R05_missing_resource (tests.test_controlled_execution_result.ControlledResultScenarios.test_R05_missing_resource) ... ITRU060_FIXTURE test_R05_missing_resource parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-sfvcmje3 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-sfvcmje3\local-appdata ledger=ledger::itru-060::54e61b766c7b41aa9f1808d147532daa
ok
test_R06_containment_rejection (tests.test_controlled_execution_result.ControlledResultScenarios.test_R06_containment_rejection) ... ITRU060_FIXTURE test_R06_containment_rejection parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-z1zkz0j7 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-z1zkz0j7\local-appdata ledger=ledger::itru-060::c025f9b621f84c09945408a283fd8d42
ok
test_R07_adapter_unavailable (tests.test_controlled_execution_result.ControlledResultScenarios.test_R07_adapter_unavailable) ... ITRU060_FIXTURE test_R07_adapter_unavailable parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-c16gy5kk registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-c16gy5kk\local-appdata ledger=ledger::itru-060::9ebcf86293a1469fb84cc261f3f46b80
ok
test_R08_proven_pre_content_read_failure (tests.test_controlled_execution_result.ControlledResultScenarios.test_R08_proven_pre_content_read_failure) ... ITRU060_FIXTURE test_R08_proven_pre_content_read_failure parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-lsko98jc registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-lsko98jc\local-appdata ledger=ledger::itru-060::d3220c74e446456aae4bc472526c07fd
ok
test_R09_proven_pre_content_resource_changed (tests.test_controlled_execution_result.ControlledResultScenarios.test_R09_proven_pre_content_resource_changed) ... ITRU060_FIXTURE test_R09_proven_pre_content_resource_changed parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-shlf4leo registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-shlf4leo\local-appdata ledger=ledger::itru-060::bdcfb784557640368e530ac2bb218765
ok
test_R10_guard_lost_before_start (tests.test_controlled_execution_result.ControlledResultScenarios.test_R10_guard_lost_before_start) ... ITRU060_FIXTURE test_R10_guard_lost_before_start parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-sjinotxb registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-sjinotxb\local-appdata ledger=ledger::itru-060::d884dded33bc4d2e82455b1a8e89b7c3
ok
test_R11_ownership_lost_before_start (tests.test_controlled_execution_result.ControlledResultScenarios.test_R11_ownership_lost_before_start) ... ITRU060_FIXTURE test_R11_ownership_lost_before_start parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-rmyx_pi1 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-rmyx_pi1\local-appdata ledger=ledger::itru-060::94f2bd6f7219400bb124bedb7d2cd2dc
ok
test_R12_post_request_failure_codes (tests.test_controlled_execution_result.ControlledResultScenarios.test_R12_post_request_failure_codes) ... ITRU060_FIXTURE test_R12_post_request_failure_codes parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-2rsj9szy registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-2rsj9szy\local-appdata ledger=ledger::itru-060::d92fa5f3e57c47159570314db941bf42
ITRU060_FIXTURE test_R12_post_request_failure_codes parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-fd12tsma registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-fd12tsma\local-appdata ledger=ledger::itru-060::cd7df57042a2400ba403ec6e8f3b966d
ok
test_R13_final_metadata_changed (tests.test_controlled_execution_result.ControlledResultScenarios.test_R13_final_metadata_changed) ... ITRU060_FIXTURE test_R13_final_metadata_changed parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-0zkcumt5 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-0zkcumt5\local-appdata ledger=ledger::itru-060::0652e83b65834707a0777de6e942081a
ok
test_R14_outer_ownership_postcheck (tests.test_controlled_execution_result.ControlledResultScenarios.test_R14_outer_ownership_postcheck) ... ITRU060_FIXTURE test_R14_outer_ownership_postcheck parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-gsepbm7o registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-gsepbm7o\local-appdata ledger=ledger::itru-060::a60602f17bc64120a7f8dae19fd3c0fb
ok
test_R15_cleanup_dominates_no_content (tests.test_controlled_execution_result.ControlledResultScenarios.test_R15_cleanup_dominates_no_content) ... ITRU060_FIXTURE test_R15_cleanup_dominates_no_content parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-5tp7uio9 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-5tp7uio9\local-appdata ledger=ledger::itru-060::a0c7cea3fdba42a69dc5d4806f66f154
ok
test_R18_reconstructed_entry_is_not_acknowledgement (tests.test_controlled_execution_result.ControlledResultScenarios.test_R18_reconstructed_entry_is_not_acknowledgement) ... ITRU060_FIXTURE test_R18_reconstructed_entry_is_not_acknowledgement parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-jv6n3qan registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-jv6n3qan\local-appdata ledger=ledger::itru-060::6746991dd4054d988922fffa47b19143
ok
test_R19_same_run_id_changed_contract (tests.test_controlled_execution_result.ControlledResultScenarios.test_R19_same_run_id_changed_contract) ... ITRU060_FIXTURE test_R19_same_run_id_changed_contract parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-464lkoux registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-464lkoux\local-appdata ledger=ledger::itru-060::f9e7a7550a34491e9b57449acefef074
ITRU060_FIXTURE test_R19_same_run_id_changed_contract parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-xetjrcd5 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-xetjrcd5\local-appdata ledger=ledger::itru-060::6c6c915a8985466180f1cce2f7534a35
ok
test_R20_tool_substitution (tests.test_controlled_execution_result.ControlledResultScenarios.test_R20_tool_substitution) ... ITRU060_FIXTURE test_R20_tool_substitution parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-gm4a_ico registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-gm4a_ico\local-appdata ledger=ledger::itru-060::a0c0a08723b04f04b773d77ccf2b18d4
ok
test_R21_ledger_scoping_and_foreign_subject (tests.test_controlled_execution_result.ControlledResultScenarios.test_R21_ledger_scoping_and_foreign_subject) ... ITRU060_FIXTURE test_R21_ledger_scoping_and_foreign_subject parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-iyrn6dl4 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-iyrn6dl4\local-appdata ledger=ledger::itru-060::4369acf28b9a45e2bbb67b514f1ee472
ITRU060_FIXTURE test_R21_ledger_scoping_and_foreign_subject parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-46egellq registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-46egellq\local-appdata ledger=ledger::itru-060::6d94666652e349578d5f06b6efe9d3f1
ITRU060_FIXTURE test_R21_ledger_scoping_and_foreign_subject parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-_3g1q083 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-_3g1q083\local-appdata ledger=ledger::itru-060::d4dcba128a9746489a8339b9461e296a
ok
test_R22_exact_claim_executor_generation (tests.test_controlled_execution_result.ControlledResultScenarios.test_R22_exact_claim_executor_generation) ... ITRU060_FIXTURE test_R22_exact_claim_executor_generation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-ayud_ytq registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-ayud_ytq\local-appdata ledger=ledger::itru-060::1bf3563631be43fe8a97959f87e2e1f1
ITRU060_FIXTURE test_R22_exact_claim_executor_generation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-x2w87l_g registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-x2w87l_g\local-appdata ledger=ledger::itru-060::2c7e401b5f9f43da9769823c165ef46a
ITRU060_FIXTURE test_R22_exact_claim_executor_generation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-b3agdx5t registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-b3agdx5t\local-appdata ledger=ledger::itru-060::449975a5529d419c9ebb6114d593f965
ok
test_R23_rejected_entry_preserves_diagnostic (tests.test_controlled_execution_result.ControlledResultScenarios.test_R23_rejected_entry_preserves_diagnostic) ... ITRU060_FIXTURE test_R23_rejected_entry_preserves_diagnostic parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-lfs5yk3r registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-lfs5yk3r\local-appdata ledger=ledger::itru-060::2e94849586734df1baff4f43b80385a9
ITRU060_FIXTURE test_R23_rejected_entry_preserves_diagnostic parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-5hagen33 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-5hagen33\local-appdata ledger=ledger::itru-060::93edde04b00f483b8553a912f6baa50e
ITRU060_FIXTURE test_R23_rejected_entry_preserves_diagnostic parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-57pls381 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-57pls381\local-appdata ledger=ledger::itru-060::19a57992b8de45d2b3820da235e9628e
ok
test_R24_commit_unknown_no_result_or_effect (tests.test_controlled_execution_result.ControlledResultScenarios.test_R24_commit_unknown_no_result_or_effect) ... ITRU060_FIXTURE test_R24_commit_unknown_no_result_or_effect parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-lct50kp9 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-lct50kp9\local-appdata ledger=ledger::itru-060::0c7939bf9f3b4803950efa3748c3d6a3
ok
test_R25_history_has_no_result_factory (tests.test_controlled_execution_result.ControlledResultScenarios.test_R25_history_has_no_result_factory) ... ITRU060_FIXTURE test_R25_history_has_no_result_factory parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-qo4t3ex0 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-qo4t3ex0\local-appdata ledger=ledger::itru-060::24c2e12b4a7b460291bb124ab95e8345
ok
test_R26_component_restart_never_recovers_invocation (tests.test_controlled_execution_result.ControlledResultScenarios.test_R26_component_restart_never_recovers_invocation) ... ITRU060_FIXTURE test_R26_component_restart_never_recovers_invocation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-da13swt4 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-da13swt4\local-appdata ledger=ledger::itru-060::dbb63ed70db14860ac8459cb3d1e0066
ok
test_R27_repeated_invocation_cannot_publish_again (tests.test_controlled_execution_result.ControlledResultScenarios.test_R27_repeated_invocation_cannot_publish_again) ... ITRU060_FIXTURE test_R27_repeated_invocation_cannot_publish_again parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-g9hmvrpm registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-g9hmvrpm\local-appdata ledger=ledger::itru-060::d7587d9d803b42e48ef213de170855f2
ok
test_R32_historical_and_noncanonical_work_rejected (tests.test_controlled_execution_result.ControlledResultScenarios.test_R32_historical_and_noncanonical_work_rejected) ... ITRU060_FIXTURE test_R32_historical_and_noncanonical_work_rejected parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-7x6shaw6 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-7x6shaw6\local-appdata ledger=ledger::itru-060::a47a9fd843d74c4f84527399f6f13e6e
ITRU060_FIXTURE test_R32_historical_and_noncanonical_work_rejected parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-upc9rfts registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-upc9rfts\local-appdata ledger=ledger::itru-060::68d82d13ac5242fe8143e23acb184b7f
ok
test_R33_fatal_interruption_preserved (tests.test_controlled_execution_result.ControlledResultScenarios.test_R33_fatal_interruption_preserved) ... ITRU060_FIXTURE test_R33_fatal_interruption_preserved parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-mbevd79q registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-mbevd79q\local-appdata ledger=ledger::itru-060::0ea5dbffb106428e8255a3ffa94f1f1f
ok
test_R34_success_suppressed_by_cleanup_or_construction (tests.test_controlled_execution_result.ControlledResultScenarios.test_R34_success_suppressed_by_cleanup_or_construction) ... ITRU060_FIXTURE test_R34_success_suppressed_by_cleanup_or_construction parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-n4lqqg42 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-n4lqqg42\local-appdata ledger=ledger::itru-060::74cc17e6ffde4585ab3fe8d01e6bfc86
ITRU060_FIXTURE test_R34_success_suppressed_by_cleanup_or_construction parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-9agmnjh0 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-9agmnjh0\local-appdata ledger=ledger::itru-060::f141aff07ce24c5ebc6da1888f6c069e
ok
test_R35_first_request_and_empty_probe_failure (tests.test_controlled_execution_result.ControlledResultScenarios.test_R35_first_request_and_empty_probe_failure) ... ITRU060_FIXTURE test_R35_first_request_and_empty_probe_failure parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-y5c29d6v registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-y5c29d6v\local-appdata ledger=ledger::itru-060::3bc4526fb3494f9b80e67731c4393bb8
ITRU060_FIXTURE test_R35_first_request_and_empty_probe_failure parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-726e_x4h registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-726e_x4h\local-appdata ledger=ledger::itru-060::6dcaa0bf08154e15873cc891d38e442a
ok

----------------------------------------------------------------------
Ran 29 tests in 13.363s

OK

```

### F3 exact command and result

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -I -B -c "import sys, pathlib, unittest; sys.path.insert(0, str(pathlib.Path.cwd())); suite = unittest.defaultTestLoader.loadTestsFromName('tests.test_durable_execution_entry_and_controlled_invocation.ItruControlledInvocationIdentityTests'); result = unittest.TextTestRunner(verbosity=2).run(suite); sys.exit(0 if result.wasSuccessful() and result.testsRun == 2 and not result.skipped else 1)"
```

Exit 0.

```text
test_historical_capability_and_legacy_binding_cannot_enter_or_invoke (tests.test_durable_execution_entry_and_controlled_invocation.ItruControlledInvocationIdentityTests.test_historical_capability_and_legacy_binding_cannot_enter_or_invoke) ... ok
test_itru_binding_executes_the_original_chain_once (tests.test_durable_execution_entry_and_controlled_invocation.ItruControlledInvocationIdentityTests.test_itru_binding_executes_the_original_chain_once) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.872s

OK

```


## Human-authorized S-H1 remediation — 2026-10-14

The Human explicitly approved bounded remediation, exact retained F1-F3 after
recorded safety inspection, fresh affected Architect/Domain/Security/Serialization
reviews, conditional Compatibility, Process completion and a separate formal
independent review. Original S-H1 HIGH/STOP chronology below remains verbatim.
No closure, final Human approval, Git write or next Task is authorized.

Root is the implementation author, not review approval authority. Explicit
rejecting state hooks on Result/payload/diagnostic remove generated restoration.
Original publication captures exact canonical references and typed nested leaves;
passive membership comparison rejects alteration and irreversibly removes observed
invalid membership. No caller authority flag or new positive construction route.
Only Result module and the two existing test files changed this remediation;
coordinator/native/Store/fixtures/contracts remain unchanged. Tests retain exact
12/29 class sizes and forty scenario identities with added restoration/mutation
subcases. Compatibility will be rerun for observable state-hook rejection.

Source/fixture/command safety inspection completed before execution and recorded
in context.md. Exact F1-F3 recovered unchanged; validation and fresh verdicts
pending. S-H1 is author-corrected but not independently resolved yet. The accepted
historical Medium and resolved F-M1 remain accurately preserved.

## Mandatory final-review STOP — 2026-10-14

Serialization/Schema independently found S-H1, HIGH and blocking. The Human
requires STOP on any Blocker/High. Root stopped review immediately, interrupted
Process before its final verdict, and did not start formal independent review.
No S-H1 production/test fix, runtime reproduction or new validation was performed.
Task remains in_progress; no final Human approval, closure or Git write occurred.

S-H1: `itru/agent_execution_result.py:67` declares `AgentExecutionResult` with
`frozen=True, slots=True`. Its six fields are at 69-74 and its explicit rejection
hooks at 76-92 do not override the dataclass-generated `__setstate__`. Python
3.12 frozen/slotted dataclasses generate a standard restoration hook which writes
fields through `object.__setattr__`. Calling that class-provided hook on an
already-genuine Result can replace ledger/Entry/Tool/outcome/payload/diagnostic
while retaining inherited `_production`. `_is_authoritative_result` at 275-282
authenticates exact object membership but does not detect the altered fields.
The changed object therefore retains authority membership for evidence that the
original invocation did not publish. This contradicts the locked terminal,
immutable, exact-binding and original-publication contract (specification
sections 3, 4 and 9). A provided standard restoration hook is distinct from
deliberate raw interpreter mutation under the explicit hostile-code exclusion.
This is a static source finding, not an executed exploit; no unlisted context
or runtime access was required. Reviewer: /root/final060_serialization;
CHANGES REQUIRED, 0 Blocker / 1 High / 0 new Medium / 0 Low.

| Final specialist | Verdict at mandatory STOP |
| --- | --- |
| Architect | APPROVE after corrected-source recheck, before S-H1 disclosure |
| Result/Domain | APPROVE after corrected-source recheck, before S-H1 disclosure |
| Security/Authority | APPROVE after corrected-source recheck, before S-H1 disclosure |
| Compatibility/Regression | APPROVE after corrected-source recheck; F-M1 RESOLVED |
| Serialization/Schema Boundary | CHANGES REQUIRED; S-H1 HIGH, blocking |
| Process/Validation Safety | STOPPED; partial observations only, no final verdict |

Six-specialist result: 4/6 APPROVE; target 6/6 not reached. The four retained
approvals do not waive or resolve S-H1. Formal independent review: NOT STARTED
because of the mandatory STOP. Process's partial literal-read observations
confirm authorization/whitelist, exact F1-F3 count guards and failed/passing
receipts, the prior 16/18 checkpoint and accurately preserved historical Medium;
these observations are not a completed specialist verdict.

Current findings: 0 Blocker / 1 High / 1 historical Human-accepted NON-BLOCKING
Medium / 0 Low. Additional review Medium F-M1 is independently RESOLVED and its
initial CHANGES REQUIRED evidence remains retained below. No incident is erased,
minimized or retrospectively made compliant. Current acceptance is 15/18: I1 is
reopened for S-H1; I2's bounded passing test evidence remains valid but did not
detect this hook. I3 and H2 remain unchecked. Original Phase-2 16/18 is historical.

Quality Gate readiness: NOT READY; independent review is incomplete and a High
finding is unresolved. Final closure evaluation and Human final approval remain
unperformed. READY FOR FINAL HUMAN CONTROL: NO. Next authorization needed:
authorize bounded remediation of S-H1 in the existing Result/test paths,
explicit safety inspection and exact retained F1-F3 revalidation, followed by
fresh affected specialist reviews, completion of Process and a separate formal
independent review over the same whitelist. No contract redesign, Task closure
or Git action is authorized by this checkpoint.

## Final-review real-issue revalidation receipts — 2026-10-14

F-M1 author correction is confined to the coordinator's once-only retirement guards and existing F2 R23. The first R23 fatal injection used ownership-exit revalidation, which the existing adapter converted to closed ownership loss rather than propagating KeyboardInterrupt. That test expectation failed (29 tests, one failed subcase, exit 1); the production correction did not change. The final test injects ordinary ownership-exit loss and fatal outer root-retention exit separately. The original root scope is exited before raising the exact fatal object; the ownership scope is not widened or redesigned. Both cases assert no Entry row, no target open and no Result. No new import, fixture, test identity, target or command was introduced.

Exact source fingerprints after corrective validation:

```text


Path : D:\Dev\ai-engineering-orchestra\itru\agent_execution_result.py
Hash : 6EB8A580686B93EA11BFDFA825ABCC46B12912CB9DA300A9DFAEFF5F2BA4284D

Path : D:\Dev\ai-engineering-orchestra\itru\_execution_entry_and_controlled_invocation.py
Hash : 243B66E330E74EACA82DDB65B14B2891EEE79182B5995BF679A5E7E35175E22D

Path : D:\Dev\ai-engineering-orchestra\tests\test_agent_execution_result.py
Hash : 69A580C45F26C2B5234A6191250981A4BE4337B414319DF6D6C5DB7CBC487D5C

Path : D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py
Hash : 947BCEC4E3823111559048F32F300384D4986B7858EA32CEC75CDFFD526B59CF




```

All complete corrective runner receipts follow, including the failed attempt. Commands are the exact retained F1-F3, unchanged. F2/F3 used previously approved sandbox escalation only to permit native ancestor metadata checks for the same owned synthetic fixtures; no approval rejection occurred. F1 final PASS 12/12; F2 final PASS 29/29; F3 final PASS 2/2; zero skips. No broader regression, runtime discovery or protected target operation was performed. Independent rechecks remain pending; author tests are not reviewer approval.

### F1 exact command

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -I -B -c "import sys, pathlib, unittest; sys.path.insert(0, str(pathlib.Path.cwd())); suite = unittest.defaultTestLoader.loadTestsFromName('tests.test_agent_execution_result.ResultContractTests'); result = unittest.TextTestRunner(verbosity=2).run(suite); sys.exit(0 if result.wasSuccessful() and result.testsRun == 12 and not result.skipped else 1)"
```

F1 corrective attempt 1: exit 0.

```text
test_R16_unsupported_private_taxonomy (tests.test_agent_execution_result.ResultContractTests.test_R16_unsupported_private_taxonomy) ... ok
test_R17_malformed_success_is_sanitized (tests.test_agent_execution_result.ResultContractTests.test_R17_malformed_success_is_sanitized) ... ok
test_R28_construction_copy_and_subclass_are_rejected (tests.test_agent_execution_result.ResultContractTests.test_R28_construction_copy_and_subclass_are_rejected) ... ok
test_R29_closed_diagnostics_only (tests.test_agent_execution_result.ResultContractTests.test_R29_closed_diagnostics_only) ... ok
test_R30_unsuccessful_content_is_rejected (tests.test_agent_execution_result.ResultContractTests.test_R30_unsuccessful_content_is_rejected) ... ok
test_R31_exact_payload_types (tests.test_agent_execution_result.ResultContractTests.test_R31_exact_payload_types) ... ok
test_R36_reports_have_no_trust_or_deserializer (tests.test_agent_execution_result.ResultContractTests.test_R36_reports_have_no_trust_or_deserializer) ... ok
test_R37_physical_identity_does_not_replace_evidence (tests.test_agent_execution_result.ResultContractTests.test_R37_physical_identity_does_not_replace_evidence) ... ok
test_R38_empty_success_is_not_absent (tests.test_agent_execution_result.ResultContractTests.test_R38_empty_success_is_not_absent) ... ok
test_R39_code_outcome_coherence (tests.test_agent_execution_result.ResultContractTests.test_R39_code_outcome_coherence) ... ok
test_R40_immutable_evidence_has_no_execution_api (tests.test_agent_execution_result.ResultContractTests.test_R40_immutable_evidence_has_no_execution_api) ... ok
test_closed_shape (tests.test_agent_execution_result.ResultContractTests.test_closed_shape) ... ok

----------------------------------------------------------------------
Ran 12 tests in 0.001s

OK

```

### F2 exact command

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -I -B -c "import sys, pathlib, unittest; sys.path.insert(0, str(pathlib.Path.cwd())); suite = unittest.defaultTestLoader.loadTestsFromName('tests.test_controlled_execution_result.ControlledResultScenarios'); result = unittest.TextTestRunner(verbosity=2).run(suite); sys.exit(0 if result.wasSuccessful() and result.testsRun == 29 and not result.skipped else 1)"
```

F2 corrective attempt 1: exit 1.

```text
test_R01_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R01_success) ... ITRU060_FIXTURE test_R01_success parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-c0d3nr_r registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-c0d3nr_r\local-appdata ledger=ledger::itru-060::99931d7923254ddbbf04edca54fb5eb5
ok
test_R02_empty_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R02_empty_success) ... ITRU060_FIXTURE test_R02_empty_success parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-d7m59wy4 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-d7m59wy4\local-appdata ledger=ledger::itru-060::57ec120331ff4456aa06a2d8ae074ef0
ok
test_R03_maximum_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R03_maximum_success) ... ITRU060_FIXTURE test_R03_maximum_success parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-r6y8u2cx registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-r6y8u2cx\local-appdata ledger=ledger::itru-060::54af087efd08468e8ada9300b1a81116
ok
test_R04_pre_read_size_limit (tests.test_controlled_execution_result.ControlledResultScenarios.test_R04_pre_read_size_limit) ... ITRU060_FIXTURE test_R04_pre_read_size_limit parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-9_fh766u registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-9_fh766u\local-appdata ledger=ledger::itru-060::38e0333c20e542368648902e6594461d
ok
test_R05_missing_resource (tests.test_controlled_execution_result.ControlledResultScenarios.test_R05_missing_resource) ... ITRU060_FIXTURE test_R05_missing_resource parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-676qhk_l registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-676qhk_l\local-appdata ledger=ledger::itru-060::89f0395962a14ef3bbb94bb3413ef729
ok
test_R06_containment_rejection (tests.test_controlled_execution_result.ControlledResultScenarios.test_R06_containment_rejection) ... ITRU060_FIXTURE test_R06_containment_rejection parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-b_61y60d registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-b_61y60d\local-appdata ledger=ledger::itru-060::697da5c3d113423691be1809d4bd4e8d
ok
test_R07_adapter_unavailable (tests.test_controlled_execution_result.ControlledResultScenarios.test_R07_adapter_unavailable) ... ITRU060_FIXTURE test_R07_adapter_unavailable parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-4ha2k184 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-4ha2k184\local-appdata ledger=ledger::itru-060::23fe1487d190483c99d9dba684131348
ok
test_R08_proven_pre_content_read_failure (tests.test_controlled_execution_result.ControlledResultScenarios.test_R08_proven_pre_content_read_failure) ... ITRU060_FIXTURE test_R08_proven_pre_content_read_failure parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-1jvq9vmx registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-1jvq9vmx\local-appdata ledger=ledger::itru-060::bcf249e9bac848588c03c258383ab23d
ok
test_R09_proven_pre_content_resource_changed (tests.test_controlled_execution_result.ControlledResultScenarios.test_R09_proven_pre_content_resource_changed) ... ITRU060_FIXTURE test_R09_proven_pre_content_resource_changed parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-jgcvqy87 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-jgcvqy87\local-appdata ledger=ledger::itru-060::4c193cd60c5f4942b8e3ea1284eb317b
ok
test_R10_guard_lost_before_start (tests.test_controlled_execution_result.ControlledResultScenarios.test_R10_guard_lost_before_start) ... ITRU060_FIXTURE test_R10_guard_lost_before_start parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-lts1svkv registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-lts1svkv\local-appdata ledger=ledger::itru-060::0642a0dba1504619bc2aa6fe3f605f03
ok
test_R11_ownership_lost_before_start (tests.test_controlled_execution_result.ControlledResultScenarios.test_R11_ownership_lost_before_start) ... ITRU060_FIXTURE test_R11_ownership_lost_before_start parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-eg3t08ma registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-eg3t08ma\local-appdata ledger=ledger::itru-060::792917a8ef1b462d9902a28bb00450ba
ok
test_R12_post_request_failure_codes (tests.test_controlled_execution_result.ControlledResultScenarios.test_R12_post_request_failure_codes) ... ITRU060_FIXTURE test_R12_post_request_failure_codes parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-2fpytl9u registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-2fpytl9u\local-appdata ledger=ledger::itru-060::2806074bbf0445c6aa05d2d6ccfb042b
ITRU060_FIXTURE test_R12_post_request_failure_codes parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-f4cjt6ue registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-f4cjt6ue\local-appdata ledger=ledger::itru-060::675743d471c24271b798dbc8e8f69438
ok
test_R13_final_metadata_changed (tests.test_controlled_execution_result.ControlledResultScenarios.test_R13_final_metadata_changed) ... ITRU060_FIXTURE test_R13_final_metadata_changed parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-yy7qleq9 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-yy7qleq9\local-appdata ledger=ledger::itru-060::0e2cd4e5f67649938260427ddac3adb0
ok
test_R14_outer_ownership_postcheck (tests.test_controlled_execution_result.ControlledResultScenarios.test_R14_outer_ownership_postcheck) ... ITRU060_FIXTURE test_R14_outer_ownership_postcheck parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-kwiqvw93 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-kwiqvw93\local-appdata ledger=ledger::itru-060::f6d677bdec5b44b5bf0526a6940b7a71
ok
test_R15_cleanup_dominates_no_content (tests.test_controlled_execution_result.ControlledResultScenarios.test_R15_cleanup_dominates_no_content) ... ITRU060_FIXTURE test_R15_cleanup_dominates_no_content parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-8a8vzq_5 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-8a8vzq_5\local-appdata ledger=ledger::itru-060::c358c81f59d84cfd9bb3ea53d2fdc8f8
ok
test_R18_reconstructed_entry_is_not_acknowledgement (tests.test_controlled_execution_result.ControlledResultScenarios.test_R18_reconstructed_entry_is_not_acknowledgement) ... ITRU060_FIXTURE test_R18_reconstructed_entry_is_not_acknowledgement parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-xgwes7qe registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-xgwes7qe\local-appdata ledger=ledger::itru-060::a2a26a573ab4403e948bfb660091d8fb
ok
test_R19_same_run_id_changed_contract (tests.test_controlled_execution_result.ControlledResultScenarios.test_R19_same_run_id_changed_contract) ... ITRU060_FIXTURE test_R19_same_run_id_changed_contract parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-f7cfcxeo registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-f7cfcxeo\local-appdata ledger=ledger::itru-060::e558e070cb6a4e43b400b0c9e63c53c8
ITRU060_FIXTURE test_R19_same_run_id_changed_contract parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-zeq8mcwb registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-zeq8mcwb\local-appdata ledger=ledger::itru-060::c10e46b3241b40059c32826f970f4e2a
ok
test_R20_tool_substitution (tests.test_controlled_execution_result.ControlledResultScenarios.test_R20_tool_substitution) ... ITRU060_FIXTURE test_R20_tool_substitution parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-9d2d80rq registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-9d2d80rq\local-appdata ledger=ledger::itru-060::5dc2a4bd838f4dd4b7feebfb65b8663a
ok
test_R21_ledger_scoping_and_foreign_subject (tests.test_controlled_execution_result.ControlledResultScenarios.test_R21_ledger_scoping_and_foreign_subject) ... ITRU060_FIXTURE test_R21_ledger_scoping_and_foreign_subject parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-4dki8ibo registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-4dki8ibo\local-appdata ledger=ledger::itru-060::3949585def3f454cbf64335c02ef0cb7
ITRU060_FIXTURE test_R21_ledger_scoping_and_foreign_subject parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-q9zck3z5 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-q9zck3z5\local-appdata ledger=ledger::itru-060::c53f4dc0391045c293295247ff1a63b2
ITRU060_FIXTURE test_R21_ledger_scoping_and_foreign_subject parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-0hbvt0ll registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-0hbvt0ll\local-appdata ledger=ledger::itru-060::214898ab58174672a677c21e70e0fa56
ok
test_R22_exact_claim_executor_generation (tests.test_controlled_execution_result.ControlledResultScenarios.test_R22_exact_claim_executor_generation) ... ITRU060_FIXTURE test_R22_exact_claim_executor_generation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-drtyqzmg registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-drtyqzmg\local-appdata ledger=ledger::itru-060::c99ae6000f5047ae9961378bca3394f8
ITRU060_FIXTURE test_R22_exact_claim_executor_generation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-_e9ribix registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-_e9ribix\local-appdata ledger=ledger::itru-060::6c2a6e01396047b1b8533f1f4af6ebf6
ITRU060_FIXTURE test_R22_exact_claim_executor_generation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-cvujw54w registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-cvujw54w\local-appdata ledger=ledger::itru-060::0dff3707c8784a17b3c9e50ff662065c
ok
test_R23_rejected_entry_preserves_diagnostic (tests.test_controlled_execution_result.ControlledResultScenarios.test_R23_rejected_entry_preserves_diagnostic) ... ITRU060_FIXTURE test_R23_rejected_entry_preserves_diagnostic parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-ivxu71nb registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-ivxu71nb\local-appdata ledger=ledger::itru-060::db5daf5064cd4d3eb1fbd880766eada1
ITRU060_FIXTURE test_R23_rejected_entry_preserves_diagnostic parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-37_7ew3t registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-37_7ew3t\local-appdata ledger=ledger::itru-060::f5222d3341984196b4dcb5c0c3267b78
ITRU060_FIXTURE test_R23_rejected_entry_preserves_diagnostic parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-0490b6n4 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-0490b6n4\local-appdata ledger=ledger::itru-060::16df285d5ec740e8955f553a3fd612e4

  test_R23_rejected_entry_preserves_diagnostic (tests.test_controlled_execution_result.ControlledResultScenarios.test_R23_rejected_entry_preserves_diagnostic) (failure='KeyboardInterrupt') ... FAIL
test_R24_commit_unknown_no_result_or_effect (tests.test_controlled_execution_result.ControlledResultScenarios.test_R24_commit_unknown_no_result_or_effect) ... ITRU060_FIXTURE test_R24_commit_unknown_no_result_or_effect parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-_fbb0w65 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-_fbb0w65\local-appdata ledger=ledger::itru-060::cf0fdb89a96e4ccaa7e18e699bf17c47
ok
test_R25_history_has_no_result_factory (tests.test_controlled_execution_result.ControlledResultScenarios.test_R25_history_has_no_result_factory) ... ITRU060_FIXTURE test_R25_history_has_no_result_factory parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-bkh_mxpo registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-bkh_mxpo\local-appdata ledger=ledger::itru-060::1a58c2628b0048d993cb08d592431f9d
ok
test_R26_component_restart_never_recovers_invocation (tests.test_controlled_execution_result.ControlledResultScenarios.test_R26_component_restart_never_recovers_invocation) ... ITRU060_FIXTURE test_R26_component_restart_never_recovers_invocation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-zx4mso55 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-zx4mso55\local-appdata ledger=ledger::itru-060::c6b649b8c3e44d4f84199e1a0888a2fa
ok
test_R27_repeated_invocation_cannot_publish_again (tests.test_controlled_execution_result.ControlledResultScenarios.test_R27_repeated_invocation_cannot_publish_again) ... ITRU060_FIXTURE test_R27_repeated_invocation_cannot_publish_again parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-d9q8dsze registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-d9q8dsze\local-appdata ledger=ledger::itru-060::845307cb8eea44f69b58bfe4930855fb
ok
test_R32_historical_and_noncanonical_work_rejected (tests.test_controlled_execution_result.ControlledResultScenarios.test_R32_historical_and_noncanonical_work_rejected) ... ITRU060_FIXTURE test_R32_historical_and_noncanonical_work_rejected parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-ljh5jdys registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-ljh5jdys\local-appdata ledger=ledger::itru-060::4ca982646870414fb2294fdb9980457e
ITRU060_FIXTURE test_R32_historical_and_noncanonical_work_rejected parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-i16oh_jq registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-i16oh_jq\local-appdata ledger=ledger::itru-060::b6a39a40d66f4f288e71a0f80d55e520
ok
test_R33_fatal_interruption_preserved (tests.test_controlled_execution_result.ControlledResultScenarios.test_R33_fatal_interruption_preserved) ... ITRU060_FIXTURE test_R33_fatal_interruption_preserved parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-ubfrugrv registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-ubfrugrv\local-appdata ledger=ledger::itru-060::65a6b3ed4d7a4af6bf0358803630d337
ok
test_R34_success_suppressed_by_cleanup_or_construction (tests.test_controlled_execution_result.ControlledResultScenarios.test_R34_success_suppressed_by_cleanup_or_construction) ... ITRU060_FIXTURE test_R34_success_suppressed_by_cleanup_or_construction parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-bxdk81qi registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-bxdk81qi\local-appdata ledger=ledger::itru-060::3ed4ec9e123648b792417397d54e97c1
ITRU060_FIXTURE test_R34_success_suppressed_by_cleanup_or_construction parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-p0rpo_t_ registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-p0rpo_t_\local-appdata ledger=ledger::itru-060::b463f946fcbb4081989ba0c037db30e3
ok
test_R35_first_request_and_empty_probe_failure (tests.test_controlled_execution_result.ControlledResultScenarios.test_R35_first_request_and_empty_probe_failure) ... ITRU060_FIXTURE test_R35_first_request_and_empty_probe_failure parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-72dvxrtc registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-72dvxrtc\local-appdata ledger=ledger::itru-060::f627b34853ef4dc28d4d0f36ff631025
ITRU060_FIXTURE test_R35_first_request_and_empty_probe_failure parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-88yuymcp registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-88yuymcp\local-appdata ledger=ledger::itru-060::24dbe5faea4e498aa473b45290468a29
ok

======================================================================
FAIL: test_R23_rejected_entry_preserves_diagnostic (tests.test_controlled_execution_result.ControlledResultScenarios.test_R23_rejected_entry_preserves_diagnostic) (failure='KeyboardInterrupt')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 278, in test_R23_rejected_entry_preserves_diagnostic
    with self.assertRaises(KeyboardInterrupt) as caught:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: KeyboardInterrupt not raised

----------------------------------------------------------------------
Ran 29 tests in 26.010s

FAILED (failures=1)

```

F2 corrective attempt 2: exit 0.

```text
test_R01_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R01_success) ... ITRU060_FIXTURE test_R01_success parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-9wajwhg7 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-9wajwhg7\local-appdata ledger=ledger::itru-060::86351885cab046d8a43940d5e14ae080
ok
test_R02_empty_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R02_empty_success) ... ITRU060_FIXTURE test_R02_empty_success parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-dfur6z75 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-dfur6z75\local-appdata ledger=ledger::itru-060::dd402745ec7449f28e3003e631a8073c
ok
test_R03_maximum_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R03_maximum_success) ... ITRU060_FIXTURE test_R03_maximum_success parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-ek_jzlk4 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-ek_jzlk4\local-appdata ledger=ledger::itru-060::1380d8fc5c904801922d2400756211e1
ok
test_R04_pre_read_size_limit (tests.test_controlled_execution_result.ControlledResultScenarios.test_R04_pre_read_size_limit) ... ITRU060_FIXTURE test_R04_pre_read_size_limit parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-tsr1zgh3 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-tsr1zgh3\local-appdata ledger=ledger::itru-060::7677b4097d6b471596a9924d0ad592bc
ok
test_R05_missing_resource (tests.test_controlled_execution_result.ControlledResultScenarios.test_R05_missing_resource) ... ITRU060_FIXTURE test_R05_missing_resource parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-guglsh3m registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-guglsh3m\local-appdata ledger=ledger::itru-060::aa09cad5f6604a9fa69a5f88dc9e74ed
ok
test_R06_containment_rejection (tests.test_controlled_execution_result.ControlledResultScenarios.test_R06_containment_rejection) ... ITRU060_FIXTURE test_R06_containment_rejection parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-82_rzkug registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-82_rzkug\local-appdata ledger=ledger::itru-060::3287d3ce0a9945a9957467f294cf6313
ok
test_R07_adapter_unavailable (tests.test_controlled_execution_result.ControlledResultScenarios.test_R07_adapter_unavailable) ... ITRU060_FIXTURE test_R07_adapter_unavailable parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-awmgqfcj registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-awmgqfcj\local-appdata ledger=ledger::itru-060::2f0e970b27bf4468935bf92deb948bd6
ok
test_R08_proven_pre_content_read_failure (tests.test_controlled_execution_result.ControlledResultScenarios.test_R08_proven_pre_content_read_failure) ... ITRU060_FIXTURE test_R08_proven_pre_content_read_failure parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-vcggl77t registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-vcggl77t\local-appdata ledger=ledger::itru-060::06161e9c2e624931811c898bf9d01d0f
ok
test_R09_proven_pre_content_resource_changed (tests.test_controlled_execution_result.ControlledResultScenarios.test_R09_proven_pre_content_resource_changed) ... ITRU060_FIXTURE test_R09_proven_pre_content_resource_changed parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-uyxhc0v8 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-uyxhc0v8\local-appdata ledger=ledger::itru-060::e3fe84ce3906446a89c44ff609909803
ok
test_R10_guard_lost_before_start (tests.test_controlled_execution_result.ControlledResultScenarios.test_R10_guard_lost_before_start) ... ITRU060_FIXTURE test_R10_guard_lost_before_start parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-ck5g6yow registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-ck5g6yow\local-appdata ledger=ledger::itru-060::1a00523fcd3240d595b385600a4c0e06
ok
test_R11_ownership_lost_before_start (tests.test_controlled_execution_result.ControlledResultScenarios.test_R11_ownership_lost_before_start) ... ITRU060_FIXTURE test_R11_ownership_lost_before_start parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-80qbfznd registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-80qbfznd\local-appdata ledger=ledger::itru-060::c771dca4eeab44e78a3632c0db4d38af
ok
test_R12_post_request_failure_codes (tests.test_controlled_execution_result.ControlledResultScenarios.test_R12_post_request_failure_codes) ... ITRU060_FIXTURE test_R12_post_request_failure_codes parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-7rvh11o7 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-7rvh11o7\local-appdata ledger=ledger::itru-060::440c76ba47e94a89a55bdaa0f900fda9
ITRU060_FIXTURE test_R12_post_request_failure_codes parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-q8bx1sfz registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-q8bx1sfz\local-appdata ledger=ledger::itru-060::ae19b39f148c4ad2a4dbf45cb3494f78
ok
test_R13_final_metadata_changed (tests.test_controlled_execution_result.ControlledResultScenarios.test_R13_final_metadata_changed) ... ITRU060_FIXTURE test_R13_final_metadata_changed parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-a22a3d8l registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-a22a3d8l\local-appdata ledger=ledger::itru-060::5e6819d6a1de4217b7677eecf17292bb
ok
test_R14_outer_ownership_postcheck (tests.test_controlled_execution_result.ControlledResultScenarios.test_R14_outer_ownership_postcheck) ... ITRU060_FIXTURE test_R14_outer_ownership_postcheck parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-vwktrtbp registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-vwktrtbp\local-appdata ledger=ledger::itru-060::d56fa0d6c4744dd0be4557fa7daaf12c
ok
test_R15_cleanup_dominates_no_content (tests.test_controlled_execution_result.ControlledResultScenarios.test_R15_cleanup_dominates_no_content) ... ITRU060_FIXTURE test_R15_cleanup_dominates_no_content parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-td3wajeh registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-td3wajeh\local-appdata ledger=ledger::itru-060::56f823b93d044e9a8af399147f05cc3e
ok
test_R18_reconstructed_entry_is_not_acknowledgement (tests.test_controlled_execution_result.ControlledResultScenarios.test_R18_reconstructed_entry_is_not_acknowledgement) ... ITRU060_FIXTURE test_R18_reconstructed_entry_is_not_acknowledgement parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-8w7j7ir1 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-8w7j7ir1\local-appdata ledger=ledger::itru-060::85c1020fe3914261b7bae1ebde6ac65b
ok
test_R19_same_run_id_changed_contract (tests.test_controlled_execution_result.ControlledResultScenarios.test_R19_same_run_id_changed_contract) ... ITRU060_FIXTURE test_R19_same_run_id_changed_contract parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-dsqx5zb2 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-dsqx5zb2\local-appdata ledger=ledger::itru-060::bd910b0584a74ec99083e5cc886ec2b2
ITRU060_FIXTURE test_R19_same_run_id_changed_contract parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-vp31_m3l registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-vp31_m3l\local-appdata ledger=ledger::itru-060::603161e6971a467d91eb2168c3c6f4b6
ok
test_R20_tool_substitution (tests.test_controlled_execution_result.ControlledResultScenarios.test_R20_tool_substitution) ... ITRU060_FIXTURE test_R20_tool_substitution parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-htomlrtf registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-htomlrtf\local-appdata ledger=ledger::itru-060::caedff7881ea4a25a9d8ce3b20ac32d5
ok
test_R21_ledger_scoping_and_foreign_subject (tests.test_controlled_execution_result.ControlledResultScenarios.test_R21_ledger_scoping_and_foreign_subject) ... ITRU060_FIXTURE test_R21_ledger_scoping_and_foreign_subject parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-9qkw7fpo registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-9qkw7fpo\local-appdata ledger=ledger::itru-060::56e3c40989214bd38d6728872ce0b52b
ITRU060_FIXTURE test_R21_ledger_scoping_and_foreign_subject parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-8ly0yfmg registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-8ly0yfmg\local-appdata ledger=ledger::itru-060::324a3d26b2964754832da6731c5c056d
ITRU060_FIXTURE test_R21_ledger_scoping_and_foreign_subject parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-58kq9dqi registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-58kq9dqi\local-appdata ledger=ledger::itru-060::d77176e3089c4819b2accad269de7b51
ok
test_R22_exact_claim_executor_generation (tests.test_controlled_execution_result.ControlledResultScenarios.test_R22_exact_claim_executor_generation) ... ITRU060_FIXTURE test_R22_exact_claim_executor_generation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-84tacfb4 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-84tacfb4\local-appdata ledger=ledger::itru-060::7d8fdcb65626499189959f2ec5a8ddb2
ITRU060_FIXTURE test_R22_exact_claim_executor_generation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-do1zburz registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-do1zburz\local-appdata ledger=ledger::itru-060::352cbe986d4d4e35bde85583ba58ae3a
ITRU060_FIXTURE test_R22_exact_claim_executor_generation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-cs45gtbm registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-cs45gtbm\local-appdata ledger=ledger::itru-060::a30c5a43050447ef81c49c6588e9c0b5
ok
test_R23_rejected_entry_preserves_diagnostic (tests.test_controlled_execution_result.ControlledResultScenarios.test_R23_rejected_entry_preserves_diagnostic) ... ITRU060_FIXTURE test_R23_rejected_entry_preserves_diagnostic parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-gvo00yrw registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-gvo00yrw\local-appdata ledger=ledger::itru-060::eaa0f71095c54728aa6bc0cbbdb73fa0
ITRU060_FIXTURE test_R23_rejected_entry_preserves_diagnostic parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-pjep3fbc registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-pjep3fbc\local-appdata ledger=ledger::itru-060::1c155658c7824ab392ce4146afcc4355
ITRU060_FIXTURE test_R23_rejected_entry_preserves_diagnostic parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-p4viuvl3 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-p4viuvl3\local-appdata ledger=ledger::itru-060::7354c480838c4c138ef15f43bc68b782
ok
test_R24_commit_unknown_no_result_or_effect (tests.test_controlled_execution_result.ControlledResultScenarios.test_R24_commit_unknown_no_result_or_effect) ... ITRU060_FIXTURE test_R24_commit_unknown_no_result_or_effect parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-9sqt9_45 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-9sqt9_45\local-appdata ledger=ledger::itru-060::34b4247328cd4e69a83a89f23291eb12
ok
test_R25_history_has_no_result_factory (tests.test_controlled_execution_result.ControlledResultScenarios.test_R25_history_has_no_result_factory) ... ITRU060_FIXTURE test_R25_history_has_no_result_factory parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-givu5csd registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-givu5csd\local-appdata ledger=ledger::itru-060::086e57b077d547e1838ab41697a8be15
ok
test_R26_component_restart_never_recovers_invocation (tests.test_controlled_execution_result.ControlledResultScenarios.test_R26_component_restart_never_recovers_invocation) ... ITRU060_FIXTURE test_R26_component_restart_never_recovers_invocation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-mzlepgwe registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-mzlepgwe\local-appdata ledger=ledger::itru-060::e11fb142841c405ea41c8a44a6ba55d4
ok
test_R27_repeated_invocation_cannot_publish_again (tests.test_controlled_execution_result.ControlledResultScenarios.test_R27_repeated_invocation_cannot_publish_again) ... ITRU060_FIXTURE test_R27_repeated_invocation_cannot_publish_again parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-_pe36q32 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-_pe36q32\local-appdata ledger=ledger::itru-060::f111dbe13a644fa2b2a7094cce6421fa
ok
test_R32_historical_and_noncanonical_work_rejected (tests.test_controlled_execution_result.ControlledResultScenarios.test_R32_historical_and_noncanonical_work_rejected) ... ITRU060_FIXTURE test_R32_historical_and_noncanonical_work_rejected parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-coi21tdo registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-coi21tdo\local-appdata ledger=ledger::itru-060::db4c20913f9f48eb9f718ea69553e04f
ITRU060_FIXTURE test_R32_historical_and_noncanonical_work_rejected parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-5gotonsc registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-5gotonsc\local-appdata ledger=ledger::itru-060::31fffdaedec94cf48226ebf30a8706a8
ok
test_R33_fatal_interruption_preserved (tests.test_controlled_execution_result.ControlledResultScenarios.test_R33_fatal_interruption_preserved) ... ITRU060_FIXTURE test_R33_fatal_interruption_preserved parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-sr73q2pz registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-sr73q2pz\local-appdata ledger=ledger::itru-060::aade44fb271b4baea8e8ab3ba342fb78
ok
test_R34_success_suppressed_by_cleanup_or_construction (tests.test_controlled_execution_result.ControlledResultScenarios.test_R34_success_suppressed_by_cleanup_or_construction) ... ITRU060_FIXTURE test_R34_success_suppressed_by_cleanup_or_construction parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-xq1x1xz6 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-xq1x1xz6\local-appdata ledger=ledger::itru-060::023160cbed7844e09fc04b88eb0e2c60
ITRU060_FIXTURE test_R34_success_suppressed_by_cleanup_or_construction parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-e127sizl registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-e127sizl\local-appdata ledger=ledger::itru-060::9ec0eb9c7ccd4141adae5cbbf24d38f3
ok
test_R35_first_request_and_empty_probe_failure (tests.test_controlled_execution_result.ControlledResultScenarios.test_R35_first_request_and_empty_probe_failure) ... ITRU060_FIXTURE test_R35_first_request_and_empty_probe_failure parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-d9ihcllr registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-d9ihcllr\local-appdata ledger=ledger::itru-060::0becd3d0c6594b6bb4a5958184d43f46
ITRU060_FIXTURE test_R35_first_request_and_empty_probe_failure parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-rm2ts7wn registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-rm2ts7wn\local-appdata ledger=ledger::itru-060::1a25a7f29409403a8d88093c7bc1559e
ok

----------------------------------------------------------------------
Ran 29 tests in 13.445s

OK

```

### F3 exact command

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -I -B -c "import sys, pathlib, unittest; sys.path.insert(0, str(pathlib.Path.cwd())); suite = unittest.defaultTestLoader.loadTestsFromName('tests.test_durable_execution_entry_and_controlled_invocation.ItruControlledInvocationIdentityTests'); result = unittest.TextTestRunner(verbosity=2).run(suite); sys.exit(0 if result.wasSuccessful() and result.testsRun == 2 and not result.skipped else 1)"
```

F3 corrective attempt 1: exit 0.

```text
test_historical_capability_and_legacy_binding_cannot_enter_or_invoke (tests.test_durable_execution_entry_and_controlled_invocation.ItruControlledInvocationIdentityTests.test_historical_capability_and_legacy_binding_cannot_enter_or_invoke) ... ok
test_itru_binding_executes_the_original_chain_once (tests.test_durable_execution_entry_and_controlled_invocation.ItruControlledInvocationIdentityTests.test_itru_binding_executes_the_original_chain_once) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.594s

OK

```


## Fresh final review phase — 2026-10-14

Human authorization: FINAL REVIEW ONLY. Six fresh independent specialist
executions evaluate the current Phase-2 implementation; a separate formal
independent execution follows. All use only the exact recovered whitelist in
context.md with direct literal reads, no search/discovery/traversal, no protected
Workflow README access and no reviewer runtime execution or edits. Routine changes
or test reruns are outside review; the Human's explicit real-issue exception
permits the bounded author correction/revalidation recorded below. A blocker/high
or required unlisted path stops review. Medium/Low findings require explicit
blocking disposition. No final Human approval, Task closure or Git write occurs.

The design/implementation author coordinates evidence and is not an approval
authority. Phase-1 approvals are retained historical evidence, not Phase-2 review
verdicts. Four literal source hashes match the recorded final passing revision.
Original Phase-2 F1/F2/F3 evidence remains 12/29/2 PASS with zero skips.
Real-issue corrective reruns and revised fingerprints are recorded above.
The historical MEDIUM incident remains Human-accepted NON-BLOCKING and accurate.

| Fresh specialist | Independent execution | Verdict | Blocker | High | Medium | Low |
| --- | --- | --- | --- | --- | --- | --- |
| Architect | /root/final060_architect | APPROVE after corrected-source recheck | 0 | 0 | 0 | 0 |
| Result/Domain | /root/final060_domain | APPROVE after corrected-source recheck | 0 | 0 | 0 | 0 |
| Security/Authority | /root/final060_security | APPROVE after corrected-source recheck | 0 | 0 | 0 | 0 |
| Compatibility/Regression | /root/final060_compatibility | APPROVE; F-M1 resolved by independent recheck | 0 | 0 | 0 | 0 |
| Serialization/Schema Boundary | /root/final060_serialization | CHANGES REQUIRED; S-H1 HIGH | 0 | 1 | 0 | 0 |
| Process/Validation Safety | /root/final060_process | STOPPED before final verdict | — | — | — | — |

Formal independent review: NOT STARTED; mandatory STOP on S-H1 before six approvals.

Corrected-revision rechecks: Architect, Compatibility and Security independently
read current source, R23, evidence and the four permitted fingerprints. Each
APPROVE, zero unresolved new findings. Cleanup sites 246/258/262/274 skip only
already-closed production without weakening original-frame acknowledgement,
publication or membership. R23 256-297 preserves ordinary ownership-loss Entry
diagnostics and the identical fatal outer-root exception with no Entry, target
open or Result. Exact corrective F1/F2/F3 receipts match the revised hashes.
Compatibility explicitly closes F-M1 as RESOLVED; its initial finding and
CHANGES REQUIRED verdict below remain retained. These verdicts confer neither
Task closure nor final Human approval. Domain recheck and two remaining fresh
specialists are pending.

Result/Domain corrected-source recheck independently APPROVE, zero unresolved
new findings. It rechecked the six-field domain contract, all three terminal
outcomes, exact ledger/Entry/Run/Tool binding, bounded immutable success bytes,
closed content-free diagnostics, absence/fatal/restart boundaries and no replay
or excluded subsystem. R23 adds subcases within the same forty scenario identities;
current fingerprints and complete corrective receipts match. No design
contradiction or required missing context. Four fresh specialists now APPROVE;
Serialization and Process remain pending.

F-M1 — MEDIUM, blocking closure, Compatibility/Regression: coordinator line 210
retires before a non-entered return's scopes exit; ordinary/fatal scope-exit errors
then call retirement again at original lines 259/247. Closed producer rejection
masks the expected Entry failure classification or original fatal propagation.
Initial verdict CHANGES REQUIRED (0 blocker/0 high/1 new Medium/0 low) is retained.
The author invoked the Human's real-issue exception for a minimal once-only
retirement guard and bounded ordinary/fatal variants in existing F2 R23.
Only the authorized coordinator and controlled test file changed; no locked
semantics or new path/command was introduced. Source safety reinspection is in
context.md. Exact F1-F3 revalidation passed 12/29/2 with zero skips; all four
affected independent rechecks subsequently APPROVED, and Compatibility resolved
F-M1. Their approvals do not resolve the later S-H1 HIGH finding. Acceptance was
16/18 at the F-M1 checkpoint and is now 15/18 after reopening I1 for S-H1.
Review/Quality Gate readiness is NOT READY, without Task closure or Human approval.

Architect independently read current Result/coordinator/test/spec/evidence and
bounded predecessor/native/Store sources. It verified exact source fingerprints,
ledger identity and complete binding, original-frame single publication,
scope-unwound disclosure and preservation of permanent Entry/authority behavior.
APPROVE, zero new findings; historical Medium remains accepted NON-BLOCKING.

Result/Domain independently read current source, all 40 scenario definitions,
both new tests, native/JIT predecessors and bounded receipts. It verified exact
terminal/payload/diagnostic semantics, acknowledged Entry provenance, no failed
content or replay, missing Result and fatal/restart boundaries, and scenario
counts 11 pure + 29 integration plus one pure shape case. Current four hashes
match 12/29/2 passing receipts. APPROVE, zero new findings; R26's component
restart/foreign-PID limitation and the historical Medium remain accurately stated.

## Phase 2 Human authorization — 2026-10-14

The Human explicitly APPROVED the Phase-1 architecture/design and accepted the
recorded MEDIUM process incident as NON-BLOCKING, instructing preservation of
the exact incident evidence. Its original chronology and Discovery scope incident
section below are retained verbatim, including their historical pending state.
The current disposition is Human-accepted non-blocking; the incident remains a
real boundary failure and is not retrospectively compliant or erased.

Phase 2 alone is authorized: the four exact production/test paths in context.md,
current Task/spec evidence updates and only exact F1-F3 validation after safety
inspection. No fresh final specialist review, formal independent review, final
Quality Gate closure evaluation, Human final approval or Git write is authorized.
No sub-agent review is invoked. Task remains in_progress. Implementation and
validation results are recorded as author evidence, not new review approval.

Pre-execution author safety inspection is recorded in context.md. The exact
F1-F3 commands were recovered from that existing evidence, not reconstructed.
F1/F2/F3 final results: PASS 12/29/2, zero skips. Phase 2 implementation and
bounded validation are complete as author evidence; no fresh final/independent
review or closure Quality Gate assessment has occurred. Acceptance: 16/18.

The exact changed-file manifest is two production files, two test files and the
five existing Task/spec evidence paths, listed in context.md. Locked semantics
are preserved; no genuine design contradiction or additional implementation path
was encountered. One MEDIUM historical process incident remains visible with
Human-accepted NON-BLOCKING disposition; no observed blocker/high finding remains.

### Phase 2 tested source fingerprints

The four authorized production/test paths at the final passing revision:

| Path | SHA-256 |
| --- | --- |
| `itru/agent_execution_result.py` | `6eb8a580686b93ea11bfdfa825abcc46b12912cb9da300a9dfaeff5f2ba4284d` |
| `itru/_execution_entry_and_controlled_invocation.py` | `b064f76b73ee2e34e5c2ac9b6766c0df7c5f409cf904847ac47a03fa2b180e2c` |
| `tests/test_agent_execution_result.py` | `69a580c45f26c2b5234a6191250981a4be4337b414319df6d6c5db7cbc487d5c` |
| `tests/test_controlled_execution_result.py` | `a3f8a4ead21ef03f596240f1d5965c5d5aa2cbb12dc033460245280c5c1945d3` |

F3 passed against this unchanged production pair before the final test-only R32
variant. Only F2 needed replay after that variant. F1 production/test source
did not change after its passing run. No additional confidence/regression
commands or final closure checks were run.

## Retained Phase 1 evidence

## Checkpoint status

Phase: 1 — design, contract lock, validation planning and specialist review.
Task: in_progress. Human architecture/Phase-2 approval: PENDING.
No production Result behavior, schema, Journal, persistence or UI implemented.
Phase-1 design checkpoint: READY at Human Control, 2026-10-13.
Six of six independent specialists APPROVE. Zero blocker/high findings remain.
One contained MEDIUM discovery scope incident awaits explicit Human disposition.

Locked technical evidence SHA-256:

- `core/agent-execution-result-specification.md`:
  `ebd59c27e24674987654fc747e63571d6c44247f68850f4598c883bb39bd5222`.
- Current `context.md` (scenario/safety matrices and exact commands):
  `1fdd05a5cc5c210a74b9e74d591462c699d1debeab1edd8f21cc4f2b0c579aa2`.

Final review/checklist updates reconcile evidence only; no contract or command
change follows these fingerprints.

## Fresh independent review ledger

| Specialist | Independent execution | Verdict | Blocker | High | Medium |
| --- | --- | --- | --- | --- | --- |
| Architect | /root/result_architect_review | APPROVE | 0 | 0 | 0 |
| Result/Domain | /root/result_domain_review | APPROVE | 0 | 0 | 0 |
| Security/Authority | /root/result_security_review | APPROVE | 0 | 0 | 0 |
| Compatibility | /root/result_compatibility_review | APPROVE | 0 | 0 | 0 |
| Serialization/Schema | /root/result_serialization_review | APPROVE | 0 | 0 | 0 |
| Process/Validation | /root/result_process_review | APPROVE | 0 | 0 | 1 |

Each reviewer must read actual changed artifacts and its necessary authoritative
context, remain read-only, and report its own finding disposition. The design
author is not a review authority. Findings and re-review evidence are recorded
below as they occur; no verdict is inferred from silence.

## Validation and gates

Targeted checks C1-C4 PASS on the current design tree. C1 validates only the
current Task schema and exact selected Workflow. C2 checks all five artifacts,
untracked-file whitespace/fences and the 40 unique scenario rows. C3 checks only
the supplied Core file and Task candidate identity. C4 confirms clean diff
whitespace, only the new Task directory/specification and no staged changes.
Exact commands and safety classification are in context.md. Scenario rows are
design dispositions, not executed runtime tests. Runtime tests and implementation
remain unexecuted under the Phase-1 boundary; broad checks X1-X5 are held for
explicit safety/scope reasons and are not claimed as passed. X6 is not applicable.

Initial C1 attempt FAILED before Python execution because `python` was absent
from PATH; replay with the existing exact Python312 executable passed. Initial
C2 attempt FAILED because its fence assertion counted its own literal fence
string; corrected line-start fence matching passed. Neither failure was hidden
or treated as a gate waiver. No dependency installation occurred.

Required Phase-1 gates: documentation_consistency PASS and independent_review
PASS for the design checkpoint, supported by six independent verdicts, actual
artifact read-back and targeted C1-C4 replay. No required Phase-1 Quality Gate
failed or was skipped. These are not implementation/Task-closure gate results.
Task implementation/closure checks remain deferred to explicit Phase 2.

## Finding chronology

- D1 — HIGH, Result/Domain review: native pending/read_data can report
  `adapter_unavailable` after a content request, while the draft forbade that
  diagnostic under ambiguity. Corrected the canonical code/outcome table to allow
  it and expanded R12 to cover post-request native support/completion failure.
  Result/Domain independently verified the correction and issued APPROVE; resolved.
- A1 — LOW, Architect review: F3 matrix label incorrectly said three tests while
  its command/class contained two. Corrected the label to two. Independent final
  disposition: Architect independently verified the correction and issued APPROVE;
  resolved.
- D2 — Clarification from Result/Domain review: explicitly reject private
  successful-byte fallback when canonical construction fails; require a sanitized
  internal-integrity exception and keep Entry consumed. Specification sections
  9/11 and R17/R34 now state this. Architect and Result/Domain independently
  verified the clarified boundary; resolved.
- D3 — LOW, Result/Domain review: qualify R35's failure as `read_failure` to match
  its exact expected diagnostic, leaving the other native code variant in R12.
  Corrected and independently verified by Result/Domain; resolved.

Architect checked actual immutable Entry/commit semantics, complete binding,
native effect/cleanup and ownership postchecks, no-persistence/schema choice and
bounded implementation plan. A fresh recheck confirmed the final integrity-failure
non-disclosure clarification. Result/Domain checked all 40 design dispositions,
exact native code mapping, missing-result semantics and payload/provenance rules.
Both approvals apply to Phase 1 only and confer no implementation authority.

Security/Authority independently checked original-frame membership and pinned
ledger provenance, permanent consumption/no replay, diagnostic and payload
non-disclosure including constructor rejection, conservative ambiguity/fatal
handling and the fixture safety envelope. Compatibility independently checked
complete Run/Contract equality, active-only canonical Tool selection, unchanged
historical evidence/SQL/schema boundaries, preserved public Admission union and
the explicit private Result extension/integrity-failure exception. Both APPROVE
with zero findings; neither ran tests or authorized Phase 2.

Serialization/Schema independently checked the closed six-field contract,
existing nested types/schemas, binary/empty/absent payload rules, closed diagnostic
model, reconstruction rejection and the justified no-persistence/schema/serializer
decision. Future Journal projection requires separate governance. APPROVE with
zero findings; no tests or mutations performed.

Process/Validation independently read the five artifacts and corrected scope
record, Task/manifest/Workflow/Human contracts, actual validator/namespace sources
and the named native identity fixture. It confirmed 40 design rows, 11 pure plus
29 integration rows, planned test counts 12/29/2, exact safe-current versus
conditional-future commands, deferred broad/hostile checks and the Human stop.
APPROVE with one MEDIUM contained process incident requiring Human disposition;
zero blocker/high findings. This is design approval, not a waiver or retrospective
authorization of discovery. No reviewer executed runtime tests or changed files.

### Discovery scope incident

The author self-audit identified the initial filtered filename pipeline
`rg --files .ai/tasks | rg '060|SCRUM-16|scrum-16'`: it internally enumerated Task
filenames despite the Human restriction, although it returned no matching Task
paths. No catalog loader, production action, protected-target effect or file
mutation resulted. Discovery stopped; all remaining work uses exact Task/Workflow
paths. This incident cannot be undone or reported as never having happened.
The context now states the actual command and boundary failure. The independent
Process/Validation reviewer classified it as one bounded MEDIUM scope incident,
not a blocker/high design defect. Containment is complete: stop discovery,
continue with exact paths and correct all flawless-compliance claims. P13 now
requires a truthful checkpoint including disclosed incidents. Human disposition
of the incident is explicitly part of the next architecture/Phase-2 authorization;
it remains PENDING and no retroactive permission or exception is inferred.
Process/Validation independently read back the corrections and issued APPROVE.
It explicitly supports the Phase-1 documentation consistency and independent
review gates after final evidence reconciliation and C1-C4 replay. Human incident
disposition, architecture approval, Phase 2 and Task closure remain pending.

## Human Control

Stopped here after all Phase-1 checks and six APPROVE verdicts, with zero
unresolved blocker/high findings. READY FOR PHASE 2: YES as a reviewable design;
execution authorization is still NO. The Human must explicitly disposition the
recorded MEDIUM scope incident, approve the locked Result architecture and
authorize the bounded Phase-2 write set and F1-F3 safety-conditioned validation
envelope in context.md. The requirement comes from the Human's explicit stop,
the Project Manifest's architecture/final-review controls and
core/human-control.md; the incident is not silently waived.

No approval is inferred for persistence, protected fixtures, Git write operations
or Task closure. No production behavior/schema/tests or Journal were implemented.
Task status remains in_progress; H1/I1-I3/H2 remain unchecked.

## Phase 2 exact commands and output receipts — 2026-10-14

These are author validation receipts, not fresh review or closure Gate results.
Only the retained F1-F3 commands ran. Each failed attempt is preserved. Console
line endings are normalized to LF in these Markdown records. The first F2 tool
receipt is explicitly tool-truncated; missing console output is not reconstructed.

### F1 exact command

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -I -B -c "import sys, pathlib, unittest; sys.path.insert(0, str(pathlib.Path.cwd())); suite = unittest.defaultTestLoader.loadTestsFromName('tests.test_agent_execution_result.ResultContractTests'); result = unittest.TextTestRunner(verbosity=2).run(suite); sys.exit(0 if result.wasSuccessful() and result.testsRun == 12 and not result.skipped else 1)"
```

#### F1 attempt 1

Exit code: 0. PASS 12/12; no skips.

```text
test_R16_unsupported_private_taxonomy (tests.test_agent_execution_result.ResultContractTests.test_R16_unsupported_private_taxonomy) ... ok
test_R17_malformed_success_is_sanitized (tests.test_agent_execution_result.ResultContractTests.test_R17_malformed_success_is_sanitized) ... ok
test_R28_construction_copy_and_subclass_are_rejected (tests.test_agent_execution_result.ResultContractTests.test_R28_construction_copy_and_subclass_are_rejected) ... ok
test_R29_closed_diagnostics_only (tests.test_agent_execution_result.ResultContractTests.test_R29_closed_diagnostics_only) ... ok
test_R30_unsuccessful_content_is_rejected (tests.test_agent_execution_result.ResultContractTests.test_R30_unsuccessful_content_is_rejected) ... ok
test_R31_exact_payload_types (tests.test_agent_execution_result.ResultContractTests.test_R31_exact_payload_types) ... ok
test_R36_reports_have_no_trust_or_deserializer (tests.test_agent_execution_result.ResultContractTests.test_R36_reports_have_no_trust_or_deserializer) ... ok
test_R37_physical_identity_does_not_replace_evidence (tests.test_agent_execution_result.ResultContractTests.test_R37_physical_identity_does_not_replace_evidence) ... ok
test_R38_empty_success_is_not_absent (tests.test_agent_execution_result.ResultContractTests.test_R38_empty_success_is_not_absent) ... ok
test_R39_code_outcome_coherence (tests.test_agent_execution_result.ResultContractTests.test_R39_code_outcome_coherence) ... ok
test_R40_immutable_evidence_has_no_execution_api (tests.test_agent_execution_result.ResultContractTests.test_R40_immutable_evidence_has_no_execution_api) ... ok
test_closed_shape (tests.test_agent_execution_result.ResultContractTests.test_closed_shape) ... ok

----------------------------------------------------------------------
Ran 12 tests in 0.001s

OK
```

### F2 exact command

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -I -B -c "import sys, pathlib, unittest; sys.path.insert(0, str(pathlib.Path.cwd())); suite = unittest.defaultTestLoader.loadTestsFromName('tests.test_controlled_execution_result.ControlledResultScenarios'); result = unittest.TextTestRunner(verbosity=2).run(suite); sys.exit(0 if result.wasSuccessful() and result.testsRun == 29 and not result.skipped else 1)"
```

#### F2 attempt 1 — TOOL-TRUNCATED RETURNED OUTPUT

Exit code: 1. Sandbox fixture setup failed before Result execution; 29 tests, 34 errors. Tool reported 28674 original output tokens and returned a truncated receipt. This is the exact available receipt, not a full-output claim.

```text
Warning: truncated output (original token count: 28674)
Total output lines: 1523

test_R01_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R01_success) ... ERROR
test_R02_empty_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R02_empty_success) ... ERROR
test_R03_maximum_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R03_maximum_success) ... ERROR
test_R04_pre_read_size_limit (tests.test_controlled_execution_result.ControlledResultScenarios.test_R04_pre_read_size_limit) ... ERROR
test_R05_missing_resource (tests.test_controlled_execution_result.ControlledResultScenarios.test_R05_missing_resource) ... ERROR
test_R06_containment_rejection (tests.test_controlled_execution_result.ControlledResultScenarios.test_R06_containment_rejection) ... ERROR
test_R07_adapter_unavailable (tests.test_controlled_execution_result.ControlledResultScenarios.test_R07_adapter_unavailable) ... ERROR
test_R08_proven_pre_content_read_failure (tests.test_controlled_execution_result.ControlledResultScenarios.test_R08_proven_pre_content_read_failure) ... ERROR
test_R09_proven_pre_content_resource_changed (tests.test_controlled_execution_result.ControlledResultScenarios.test_R09_proven_pre_content_resource_changed) ... ERROR
test_R10_guard_lost_before_start (tests.test_controlled_execution_result.ControlledResultScenarios.test_R10_guard_lost_before_start) ... ERROR
test_R11_ownership_lost_before_start (tests.test_controlled_execution_result.ControlledResultScenarios.test_R11_ownership_lost_before_start) ... ERROR
test_R12_post_request_failure_codes (tests.test_controlled_execution_result.ControlledResultScenarios.test_R12_post_request_failure_codes) ...
  test_R12_post_request_failure_codes (tests.test_controlled_execution_result.ControlledResultScenarios.test_R12_post_request_failure_codes) (code='read_failure') ... ERROR
  test_R12_post_request_failure_codes (tests.test_controlled_execution_result.ControlledResultScenarios.test_R12_post_request_failure_codes) (code='adapter_unavailable') ... ERROR
test_R13_final_metadata_changed (tests.test_controlled_execution_result.ControlledResultScenarios.test_R13_final_metadata_changed) ... ERROR
test_R14_outer_ownership_postcheck (tests.test_controlled_execution_result.ControlledResultScenarios.test_R14_outer_ownership_postcheck) ... ERROR
test_R15_cleanup_dominates_no_content (tests.test_controlled_execution_result.ControlledResultScenarios.test_R15_cleanup_dominates_no_content) ... ERROR
test_R18_reconstructed_entry_is_not_acknowledgement (tests.test_controlled_execution_result.ControlledResultScenarios.test_R18_reconstructed_entry_is_not_acknowledgement) ... ERROR
test_R19_same_run_id_changed_contract (tests.test_controlled_execution_result.ControlledResultScenarios.test_R19_same_run_id_changed_contract) ...
  test_R19_same_run_id_changed_contract (tests.test_controlled_execution_result.ControlledResultScenarios.test_R19_same_run_id_changed_contract) (field='resource') ... ERROR
  test_R19_same_run_id_changed_contract (tests.test_controlled_execution_result.ControlledResultScenarios.test_R19_same_run_id_changed_contract) (field='execution_mode') ... ERROR
test_R20_tool_substitution (tests.test_controlled_execution_result.ControlledResultScenarios.test_R20_tool_substitution) ... ERROR
test_R21_ledger_scoping_and_foreign_subject (tests.test_controlled_execution_result.ControlledResultScenarios.test_R21_ledger_scoping_and_foreign_subject) ... ERROR
test_R22_exact_claim_executor_generation (tests.test_controlled_execution_result.ControlledResultScenarios.test_R22_exact_claim_executor_generation) ...
  test_R22_exact_claim_executor_generation (tests.test_controlled_execution_result.ControlledResultScenarios.test_R22_exact_claim_executor_generation) (field='claim_id') ... ERROR
  test_R22_exact_claim_executor_generation (tests.test_controlled_execution_result.ControlledResultScenarios.test_R22_exact_claim_executor_generation) (field='executor_id') ... ERROR
  test_R22_exact_claim_executor_generation (tests.test_controlled_execution_result.ControlledResultScenarios.test_R22_exact_claim_executor_generation) (field='lease_generation') ... ERROR
test_R23_rejected_entry_preserves_diagnostic (tests.test_controlled_execution_result.ControlledResultScenarios.test_R23_rejected_entry_preserves_diagnostic) ... ERROR
test_R24_commit_unknown_no_result_or_effect (tests.test_controlled_execution_result.ControlledResultScenarios.test_R24_commit_unknown_no_result_or_effect) ... ERROR
test_R25_history_has_no_result_factory (tests.test_controlled_execution_result.ControlledResultScenarios.test_R25_history_has_no_result_factory) ... ERROR
test_R26_component_restart_never_recovers_invocation (tests.test_controlled_execution_result.ControlledResultScenarios.test_R26_component_restart_never_recovers_invocation) ... ERROR
test_R27_repeated_invocation_cannot_publish_again (tests.test_controlled_execution_result.ControlledResultScenarios.test_R27_repeated_invocation_cannot_publish_again) ... ERROR
test_R32_historical_and_noncanonical_work_rejected (tests.test_controlled_execution_result.ControlledResultScenarios.test_R32_historical_and_noncanonical_work_rejected) ... ERROR
test_R33_fatal_interruption_preserved (tests.test_controlled_execution_result.ControlledResultScenarios.test_R33_fatal_interruption_preserved) ... ERROR
test_R34_success_suppressed_by_cleanup_or_construction (tests.test_controlled_execution_result.ControlledResultScenarios.test_R34_success_suppressed_by_cleanup_or_construction) ... ERROR
test_R35_first_request_and_empty_probe_failure (tests.test_controlled_execution_result.ControlledResultScenarios.test_R35_first_request_and_empty_probe_failure) ...
  test_R35_first_request_and_empty_probe_failure (tests.test_controlled_execution_result.ControlledResultScenarios.test_R35_first_request_and_empty_probe_failure) (empty=False) ... ERROR
  test_R35_first_request_and_empty_probe_failure (tests.test_controlled_execution_result.ControlledResultScenarios.test_R35_first_request_and_empty_probe_failure) (empty=True) ... ERROR

======================================================================
ERROR: test_R01_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R01_success)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 104, in test_R01_success
    outcome = self.terminal(self.rig(), "succeeded")
                            ^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 40, in rig
    rig = original._NativeRig(self, resource=RESOURCE, data=data)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_durable_execution_entry_and_controlled_invocation.py", line 490, in __init__
    self.h=integrated._WindowsHarness(test)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 38, in fresh_harness
    return harness(case, ledger_id=ledger_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_local_operational_trust.py", line 645, in __init__
    provisioned = administration.provision(self.configuration)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1966, in provision
    with _lock_registry(configuration.authorization_domain_id) as registry:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1759, in _lock_registry
    root = _create_registry_namespace(sid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 823, in _create_registry_namespace
    _reject_reparse_components(root, terminal_directory=True)
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 988, in _reject_reparse_components
    handle = _open_file(
             ^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 848, in _open_file
    raise _win32_error(f"CreateFileW failed for {path.name!r}")
PermissionError: [WinError 5] CreateFileW failed for 'Abdelrahman'

======================================================================
ERROR: test_R02_empty_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R02_empty_success)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 113, in test_R02_empty_success
    rig = self.rig(b"")
          ^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 40, in rig
    rig = original._NativeRig(self, resource=RESOURCE, data=data)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_durable_execution_entry_and_controlled_invocation.py", line 490, in __init__
    self.h=integrated._WindowsHarness(test)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 38, in fresh_harness
    return harness(case, ledger_id=ledger_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_local_operational_trust.py", line 645, in __init__
    provisioned = administration.provision(self.configuration)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1966, in provision
    with _lock_registry(configuration.authorization_domain_id) as registry:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1759, in _lock_registry
    root = _create_registry_namespace(sid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 823, in _create_registry_namespace
    _reject_reparse_components(root, terminal_directory=True)
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 988, in _reject_reparse_components
    handle = _open_file(
             ^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 848, in _open_file
    raise _win32_error(f"CreateFileW failed for {path.name!r}")
PermissionError: [WinError 5] CreateFileW failed for 'Abdelrahman'

======================================================================
ERROR: test_R03_maximum_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R03_maximum_success)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 123, in test_R03_maximum_success
    rig = self.rig(data)
          ^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 40, in rig
    rig = original._NativeRig(self, resource=RESOURCE, data=data)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_durable_execution_entry_and_controlled_invocation.py", line 490, in __init__
    self.h=integrated._WindowsHarness(test)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 38, in fresh_harness
    return harness(case, ledger_id=ledger_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_local_operational_trust.py", line 645, in __init__
    provisioned = administration.provision(self.configuration)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1966, in provision
    with _lock_registry(configuration.authorization_domain_id) as registry:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1759, in _lock_registry
    root = _create_registry_namespace(sid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 823, in _create_registry_namespace
    _reject_reparse_components(root, terminal_directory=True)
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 988, in _reject_reparse_components
    handle = _open_file(
             ^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 848, in _open_file
    raise _win32_error(f"CreateFileW failed for {path.name!r}")
PermissionError: [WinError 5] CreateFileW failed for 'Abdelrahman'

======================================================================
ERROR: test_R04_pre_read_size_limit (tests.test_controlled_execution_result.ControlledResultScenarios.test_R04_pre_read_size_limit)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 132, in test_R04_pre_read_size_limit
    rig = self.rig(b"x" * 65537)
          ^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 40, in rig
    rig = original._NativeRig(self, resource=RESOURCE, data=data)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_durable_execution_entry_and_controlled_invocation.py", line 490, in __init__
    self.h=integrated._WindowsHarness(test)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 38, in fresh_harness
    return harness(case, ledger_id=ledger_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_local_operational_trust.py", line 645, in __init__
    provisioned = administration.provision(self.configuration)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1966, in provision
    with _lock_registry(configuration.authorization_domain_id) as registry:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1759, in _lock_registry
    root = _create_registry_namespace(sid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 823, in _create_registry_namespace
    _reject_reparse_components(root, terminal_directory=True)
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 988, in _reject_reparse_components
    handle = _open_file(
             ^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 848, in _open_file
    raise _win32_error(f"CreateFileW failed for {path.name!r}")
PermissionError: [WinError 5] CreateFileW failed for 'Abdelrahman'

======================================================================
ERROR: test_R05_missing_resource (tests.test_controlled_execution_result.ControlledResultScenarios.test_R05_missing_resource)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 138, in test_R05_missing_resource
    self.terminal(self.rig(None), "failed_before_effect", "resource_missing")
                  ^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 40, in rig
    rig = original._NativeRig(self, resource=RESOURCE, data=data)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_durable_execution_entry_and_controlled_invocation.py", line 490, in __init__
    self.h=integrated._WindowsHarness(test)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 38, in fresh_harness
    return harness(case, ledger_id=ledger_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_local_operational_trust.py", line 645, in __init__
    provisioned = administration.provision(self.configuration)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1966, in provision
    with _lock_registry(configuration.authorization_domain_id) as registry:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1759, in _lock_registry
    root = _create_registry_namespace(sid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 823, in _create_registry_namespace
    _reject_reparse_components(root, terminal_directory=True)
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 988, in _reject_reparse_components
    handle = _open_file(
             ^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 848, in _open_file
    raise _win32_error(f"CreateFileW failed for {path.name!r}")
PermissionError: [WinError 5] CreateFileW failed for 'Abdelrahman'

======================================================================
ERROR: test_R06_containment_rejection (tests.test_controlled_execution_result.ControlledResultScenarios.test_R06_containment_rejection)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 141, in test_R06_containment_rejection
    self.before("containment_rejected")
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 76, in before
    rig = self.rig()
          ^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 40, in rig
    rig = original._NativeRig(self, resource=RESOURCE, data=data)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_durable_execution_entry_and_controlled_invocation.py", line 490, in __init__
    self.h=integrated._WindowsHarness(test)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 38, in fresh_harness
    return harness(case, ledger_id=ledger_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_local_operational_trust.py", line 645, in __init__
    provisioned = administration.provision(self.configuration)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1966, in provision
    with _lock_registry(configuration.authorization_domain_id) as registry:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1759, in _lock_registry
    root = _create_registry_namespace(sid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 823, in _create_registry_namespace
    _reject_reparse_components(root, terminal_directory=True)
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 988, in _reject_reparse_components
    handle = _open_file(
             ^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 848, in _open_file
    raise _win32_error(f"CreateFileW failed for {path.name!r}")
PermissionError: [WinError 5] CreateFileW failed for 'Abdelrahman'

======================================================================
ERROR: test_R07_adapter_unavailable (tests.test_controlled_execution_result.ControlledResultScenarios.test_R07_adapter_unavailable)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 144, in test_R07_adapter_unavailable
    rig = self.rig()
          ^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 40, in rig
    rig = original._NativeRig(self, resource=RESOURCE, data=data)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_durable_execution_entry_and_controlled_invocation.py", line 490, in __init__
    self.h=integrated._WindowsHarness(test)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 38, in fresh_harness
    return harness(case, ledger_id=ledger_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_local_operational_trust.py", line 645, in __init__
    provisioned = administration.provision(self.configuration)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1966, in provision
    with _lock_registry(configuration.authorization_domain_id) as registry:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1759, in _lock_registry
    root = _create_registry_namespace(sid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 823, in _create_registry_namespace
    _reject_reparse_components(root, terminal_directory=True)
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 988, in _reject_reparse_components
    handle = _open_file(
             ^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 848, in _open_file
    raise _win32_error(f"CreateFileW failed for {path.name!r}")
PermissionError: [WinError 5] CreateFileW failed for 'Abdelrahman'

======================================================================
ERROR: test_R08_proven_pre_content_read_failure (tests.test_controlled_execution_result.ControlledResultScenarios.test_R08_proven_pre_content_read_failure)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 149, in test_R08_proven_pre_content_read_failure
    self.before("read_failure")
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 76, in before
    rig = self.rig()
          ^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 40, in rig
    rig = original._NativeRig(self, resource=RESOURCE, data=data)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_durable_execution_entry_and_controlled_invocation.py", line 490, in __init__
    self.h=integrated._WindowsHarness(test)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 38, in fresh_harness
    return harness(case, ledger_id=ledger_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_local_operational_trust.py", line 645, in __init__
    provisioned = administration.provision(self.configuration)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1966, in provision
    with _lock_registry(configuration.authorization_domain_id) as registry:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1759, in _lock_registry
    root = _create_registry_namespace(sid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 823, in _create_registry_namespace
    _reject_reparse_components(root, terminal_directory=True)
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 988, in _reject_reparse_components
    handle = _open_file(
             ^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 848, in _open_file
    raise _win32_error(f"CreateFileW failed for {path.name!r}")
PermissionError: [WinError 5] CreateFileW failed for 'Abdelrahman'

======================================================================
ERROR: test_R09_proven_pre_content_resource_changed (tests.test_controlled_execution_result.ControlledResultScenarios.test_R09_proven_pre_content_resource_changed)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 152, in test_R09_proven_pre_content_resource_changed
    self.before("resource_changed")
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 76, in before
    rig = self.rig()
          ^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 40, in rig
    rig = original._NativeRig(self, resource=RESOURCE, data=data)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_durable_execution_entry_and_controlled_invocation.py", line 490, in __init__
    self.h=integrated._WindowsHarness(test)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 38, in fresh_harness
    return harness(case, ledger_id=ledger_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_local_operational_trust.py", line 645, in __init__
    provisioned = administration.provision(self.configuration)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1966, in provision
    with _lock_registry(configuration.authorization_domain_id) as registry:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1759, in _lock_registry
    root = _create_registry_namespace(sid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 823, in _create_registry_namespace
    _reject_reparse_components(root, terminal_directory=True)
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 988, in _reject_reparse_components
    handle = _open_file(
             ^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 848, in _open_file
    raise _win32_error(f"CreateFileW failed for {path.name!r}")
PermissionError: [WinError 5] CreateFileW failed for 'Abdelrahman'

======================================================================
ERROR: test_R10_guard_lost_before_start (tests.test_controlled_execution_result.ControlledResultScenarios.test_R10_guard_lost_before_start)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 155, in test_R10_guard_lost_before_start
    rig = self.rig()
          ^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 40, in rig
    rig = original._NativeRig(self, resource=RESOURCE, data=data)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_durable_execution_entry_and_controlled_invocation.py", line 490, in __init__
    self.h=integrated._WindowsHarness(test)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 38, in fresh_harness
    return harness(case, ledger_id=ledger_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_local_operational_trust.py", line 645, in __init__
    provisioned = administration.provision(self.configuration)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1966, in provision
    with _lock_registry(configuration.authorization_domain_id) as registry:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1759, in _lock_registry
    root = _create_registry_namespace(sid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 823, in _create_registry_namespace
    _reject_reparse_components(root, terminal_directory=True)
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 988, in _reject_reparse_components
    handle = _open_file(
             ^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 848, in _open_file
    raise _win32_error(f"CreateFileW failed for {path.name!r}")
PermissionError: [WinError 5] CreateFileW failed for 'Abdelrahman'

======================================================================
ERROR: test_R11_ownership_lost_before_start (tests.test_controlled_execution_result.ControlledResultScenarios.test_R11_ownership_lost_before_start)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 160, in test_R11_ownership_lost_before_start
    rig = self.rig()
          ^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 40, in rig
    rig = original._NativeRig(self, resource=RESOURCE, data=data)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_durable_execution_entry_and_controlled_invocation.py", line 490, in __init__
    self.h=integrated._WindowsHarness(test)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 38, in fresh_harness
    return harness(case, ledger_id=ledger_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_local_operational_trust.py", line 645, in __init__
    provisioned = administration.provision(self.configuration)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1966, in provision
    with _lock_registry(configuration.authorization_domain_id) as registry:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
…8674 tokens truncated…ct(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 38, in fresh_harness
    return harness(case, ledger_id=ledger_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_local_operational_trust.py", line 645, in __init__
    provisioned = administration.provision(self.configuration)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1966, in provision
    with _lock_registry(configuration.authorization_domain_id) as registry:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1759, in _lock_registry
    root = _create_registry_namespace(sid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 823, in _create_registry_namespace
    _reject_reparse_components(root, terminal_directory=True)
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 988, in _reject_reparse_components
    handle = _open_file(
             ^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 848, in _open_file
    raise _win32_error(f"CreateFileW failed for {path.name!r}")
PermissionError: [WinError 5] CreateFileW failed for 'Abdelrahman'

======================================================================
ERROR: test_R22_exact_claim_executor_generation (tests.test_controlled_execution_result.ControlledResultScenarios.test_R22_exact_claim_executor_generation) (field='executor_id')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 245, in test_R22_exact_claim_executor_generation
    self.tamper_after_read(lambda s: replace(s, **{field: value}))
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 83, in tamper_after_read
    rig = self.rig()
          ^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 40, in rig
    rig = original._NativeRig(self, resource=RESOURCE, data=data)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_durable_execution_entry_and_controlled_invocation.py", line 490, in __init__
    self.h=integrated._WindowsHarness(test)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 38, in fresh_harness
    return harness(case, ledger_id=ledger_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_local_operational_trust.py", line 645, in __init__
    provisioned = administration.provision(self.configuration)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1966, in provision
    with _lock_registry(configuration.authorization_domain_id) as registry:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1759, in _lock_registry
    root = _create_registry_namespace(sid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 823, in _create_registry_namespace
    _reject_reparse_components(root, terminal_directory=True)
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 988, in _reject_reparse_components
    handle = _open_file(
             ^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 848, in _open_file
    raise _win32_error(f"CreateFileW failed for {path.name!r}")
PermissionError: [WinError 5] CreateFileW failed for 'Abdelrahman'

======================================================================
ERROR: test_R22_exact_claim_executor_generation (tests.test_controlled_execution_result.ControlledResultScenarios.test_R22_exact_claim_executor_generation) (field='lease_generation')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 245, in test_R22_exact_claim_executor_generation
    self.tamper_after_read(lambda s: replace(s, **{field: value}))
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 83, in tamper_after_read
    rig = self.rig()
          ^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 40, in rig
    rig = original._NativeRig(self, resource=RESOURCE, data=data)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_durable_execution_entry_and_controlled_invocation.py", line 490, in __init__
    self.h=integrated._WindowsHarness(test)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 38, in fresh_harness
    return harness(case, ledger_id=ledger_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_local_operational_trust.py", line 645, in __init__
    provisioned = administration.provision(self.configuration)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1966, in provision
    with _lock_registry(configuration.authorization_domain_id) as registry:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1759, in _lock_registry
    root = _create_registry_namespace(sid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 823, in _create_registry_namespace
    _reject_reparse_components(root, terminal_directory=True)
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 988, in _reject_reparse_components
    handle = _open_file(
             ^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 848, in _open_file
    raise _win32_error(f"CreateFileW failed for {path.name!r}")
PermissionError: [WinError 5] CreateFileW failed for 'Abdelrahman'

======================================================================
ERROR: test_R23_rejected_entry_preserves_diagnostic (tests.test_controlled_execution_result.ControlledResultScenarios.test_R23_rejected_entry_preserves_diagnostic)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 248, in test_R23_rejected_entry_preserves_diagnostic
    rig = self.rig()
          ^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 40, in rig
    rig = original._NativeRig(self, resource=RESOURCE, data=data)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_durable_execution_entry_and_controlled_invocation.py", line 490, in __init__
    self.h=integrated._WindowsHarness(test)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 38, in fresh_harness
    return harness(case, ledger_id=ledger_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_local_operational_trust.py", line 645, in __init__
    provisioned = administration.provision(self.configuration)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1966, in provision
    with _lock_registry(configuration.authorization_domain_id) as registry:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1759, in _lock_registry
    root = _create_registry_namespace(sid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 823, in _create_registry_namespace
    _reject_reparse_components(root, terminal_directory=True)
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 988, in _reject_reparse_components
    handle = _open_file(
             ^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 848, in _open_file
    raise _win32_error(f"CreateFileW failed for {path.name!r}")
PermissionError: [WinError 5] CreateFileW failed for 'Abdelrahman'

======================================================================
ERROR: test_R24_commit_unknown_no_result_or_effect (tests.test_controlled_execution_result.ControlledResultScenarios.test_R24_commit_unknown_no_result_or_effect)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 258, in test_R24_commit_unknown_no_result_or_effect
    rig = self.rig()
          ^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 40, in rig
    rig = original._NativeRig(self, resource=RESOURCE, data=data)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_durable_execution_entry_and_controlled_invocation.py", line 490, in __init__
    self.h=integrated._WindowsHarness(test)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 38, in fresh_harness
    return harness(case, ledger_id=ledger_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_local_operational_trust.py", line 645, in __init__
    provisioned = administration.provision(self.configuration)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1966, in provision
    with _lock_registry(configuration.authorization_domain_id) as registry:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1759, in _lock_registry
    root = _create_registry_namespace(sid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 823, in _create_registry_namespace
    _reject_reparse_components(root, terminal_directory=True)
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 988, in _reject_reparse_components
    handle = _open_file(
             ^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 848, in _open_file
    raise _win32_error(f"CreateFileW failed for {path.name!r}")
PermissionError: [WinError 5] CreateFileW failed for 'Abdelrahman'

======================================================================
ERROR: test_R25_history_has_no_result_factory (tests.test_controlled_execution_result.ControlledResultScenarios.test_R25_history_has_no_result_factory)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 272, in test_R25_history_has_no_result_factory
    rig = self.rig()
          ^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 40, in rig
    rig = original._NativeRig(self, resource=RESOURCE, data=data)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_durable_execution_entry_and_controlled_invocation.py", line 490, in __init__
    self.h=integrated._WindowsHarness(test)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 38, in fresh_harness
    return harness(case, ledger_id=ledger_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_local_operational_trust.py", line 645, in __init__
    provisioned = administration.provision(self.configuration)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1966, in provision
    with _lock_registry(configuration.authorization_domain_id) as registry:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1759, in _lock_registry
    root = _create_registry_namespace(sid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 823, in _create_registry_namespace
    _reject_reparse_components(root, terminal_directory=True)
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 988, in _reject_reparse_components
    handle = _open_file(
             ^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 848, in _open_file
    raise _win32_error(f"CreateFileW failed for {path.name!r}")
PermissionError: [WinError 5] CreateFileW failed for 'Abdelrahman'

======================================================================
ERROR: test_R26_component_restart_never_recovers_invocation (tests.test_controlled_execution_result.ControlledResultScenarios.test_R26_component_restart_never_recovers_invocation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 286, in test_R26_component_restart_never_recovers_invocation
    rig = self.rig()
          ^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 40, in rig
    rig = original._NativeRig(self, resource=RESOURCE, data=data)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_durable_execution_entry_and_controlled_invocation.py", line 490, in __init__
    self.h=integrated._WindowsHarness(test)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 38, in fresh_harness
    return harness(case, ledger_id=ledger_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_local_operational_trust.py", line 645, in __init__
    provisioned = administration.provision(self.configuration)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1966, in provision
    with _lock_registry(configuration.authorization_domain_id) as registry:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1759, in _lock_registry
    root = _create_registry_namespace(sid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 823, in _create_registry_namespace
    _reject_reparse_components(root, terminal_directory=True)
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 988, in _reject_reparse_components
    handle = _open_file(
             ^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 848, in _open_file
    raise _win32_error(f"CreateFileW failed for {path.name!r}")
PermissionError: [WinError 5] CreateFileW failed for 'Abdelrahman'

======================================================================
ERROR: test_R27_repeated_invocation_cannot_publish_again (tests.test_controlled_execution_result.ControlledResultScenarios.test_R27_repeated_invocation_cannot_publish_again)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 303, in test_R27_repeated_invocation_cannot_publish_again
    rig = self.rig()
          ^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 40, in rig
    rig = original._NativeRig(self, resource=RESOURCE, data=data)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_durable_execution_entry_and_controlled_invocation.py", line 490, in __init__
    self.h=integrated._WindowsHarness(test)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 38, in fresh_harness
    return harness(case, ledger_id=ledger_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_local_operational_trust.py", line 645, in __init__
    provisioned = administration.provision(self.configuration)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1966, in provision
    with _lock_registry(configuration.authorization_domain_id) as registry:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1759, in _lock_registry
    root = _create_registry_namespace(sid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 823, in _create_registry_namespace
    _reject_reparse_components(root, terminal_directory=True)
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 988, in _reject_reparse_components
    handle = _open_file(
             ^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 848, in _open_file
    raise _win32_error(f"CreateFileW failed for {path.name!r}")
PermissionError: [WinError 5] CreateFileW failed for 'Abdelrahman'

======================================================================
ERROR: test_R32_historical_and_noncanonical_work_rejected (tests.test_controlled_execution_result.ControlledResultScenarios.test_R32_historical_and_noncanonical_work_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 317, in test_R32_historical_and_noncanonical_work_rejected
    rig = self.rig()
          ^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 40, in rig
    rig = original._NativeRig(self, resource=RESOURCE, data=data)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_durable_execution_entry_and_controlled_invocation.py", line 490, in __init__
    self.h=integrated._WindowsHarness(test)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 38, in fresh_harness
    return harness(case, ledger_id=ledger_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_local_operational_trust.py", line 645, in __init__
    provisioned = administration.provision(self.configuration)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1966, in provision
    with _lock_registry(configuration.authorization_domain_id) as registry:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1759, in _lock_registry
    root = _create_registry_namespace(sid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 823, in _create_registry_namespace
    _reject_reparse_components(root, terminal_directory=True)
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 988, in _reject_reparse_components
    handle = _open_file(
             ^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 848, in _open_file
    raise _win32_error(f"CreateFileW failed for {path.name!r}")
PermissionError: [WinError 5] CreateFileW failed for 'Abdelrahman'

======================================================================
ERROR: test_R33_fatal_interruption_preserved (tests.test_controlled_execution_result.ControlledResultScenarios.test_R33_fatal_interruption_preserved)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 338, in test_R33_fatal_interruption_preserved
    rig = self.rig()
          ^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 40, in rig
    rig = original._NativeRig(self, resource=RESOURCE, data=data)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_durable_execution_entry_and_controlled_invocation.py", line 490, in __init__
    self.h=integrated._WindowsHarness(test)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 38, in fresh_harness
    return harness(case, ledger_id=ledger_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_local_operational_trust.py", line 645, in __init__
    provisioned = administration.provision(self.configuration)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1966, in provision
    with _lock_registry(configuration.authorization_domain_id) as registry:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1759, in _lock_registry
    root = _create_registry_namespace(sid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 823, in _create_registry_namespace
    _reject_reparse_components(root, terminal_directory=True)
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 988, in _reject_reparse_components
    handle = _open_file(
             ^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 848, in _open_file
    raise _win32_error(f"CreateFileW failed for {path.name!r}")
PermissionError: [WinError 5] CreateFileW failed for 'Abdelrahman'

======================================================================
ERROR: test_R34_success_suppressed_by_cleanup_or_construction (tests.test_controlled_execution_result.ControlledResultScenarios.test_R34_success_suppressed_by_cleanup_or_construction)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 348, in test_R34_success_suppressed_by_cleanup_or_construction
    rig = self.rig()
          ^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 40, in rig
    rig = original._NativeRig(self, resource=RESOURCE, data=data)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_durable_execution_entry_and_controlled_invocation.py", line 490, in __init__
    self.h=integrated._WindowsHarness(test)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 38, in fresh_harness
    return harness(case, ledger_id=ledger_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_local_operational_trust.py", line 645, in __init__
    provisioned = administration.provision(self.configuration)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1966, in provision
    with _lock_registry(configuration.authorization_domain_id) as registry:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1759, in _lock_registry
    root = _create_registry_namespace(sid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 823, in _create_registry_namespace
    _reject_reparse_components(root, terminal_directory=True)
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 988, in _reject_reparse_components
    handle = _open_file(
             ^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 848, in _open_file
    raise _win32_error(f"CreateFileW failed for {path.name!r}")
PermissionError: [WinError 5] CreateFileW failed for 'Abdelrahman'

======================================================================
ERROR: test_R35_first_request_and_empty_probe_failure (tests.test_controlled_execution_result.ControlledResultScenarios.test_R35_first_request_and_empty_probe_failure) (empty=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 370, in test_R35_first_request_and_empty_probe_failure
    rig = self.rig(data)
          ^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 40, in rig
    rig = original._NativeRig(self, resource=RESOURCE, data=data)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_durable_execution_entry_and_controlled_invocation.py", line 490, in __init__
    self.h=integrated._WindowsHarness(test)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 38, in fresh_harness
    return harness(case, ledger_id=ledger_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_local_operational_trust.py", line 645, in __init__
    provisioned = administration.provision(self.configuration)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1966, in provision
    with _lock_registry(configuration.authorization_domain_id) as registry:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1759, in _lock_registry
    root = _create_registry_namespace(sid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 823, in _create_registry_namespace
    _reject_reparse_components(root, terminal_directory=True)
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 988, in _reject_reparse_components
    handle = _open_file(
             ^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 848, in _open_file
    raise _win32_error(f"CreateFileW failed for {path.name!r}")
PermissionError: [WinError 5] CreateFileW failed for 'Abdelrahman'

======================================================================
ERROR: test_R35_first_request_and_empty_probe_failure (tests.test_controlled_execution_result.ControlledResultScenarios.test_R35_first_request_and_empty_probe_failure) (empty=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 370, in test_R35_first_request_and_empty_probe_failure
    rig = self.rig(data)
          ^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 40, in rig
    rig = original._NativeRig(self, resource=RESOURCE, data=data)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_durable_execution_entry_and_controlled_invocation.py", line 490, in __init__
    self.h=integrated._WindowsHarness(test)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 38, in fresh_harness
    return harness(case, ledger_id=ledger_id)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\tests\test_local_operational_trust.py", line 645, in __init__
    provisioned = administration.provision(self.configuration)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1966, in provision
    with _lock_registry(configuration.authorization_domain_id) as registry:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 1759, in _lock_registry
    root = _create_registry_namespace(sid)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 823, in _create_registry_namespace
    _reject_reparse_components(root, terminal_directory=True)
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 988, in _reject_reparse_components
    handle = _open_file(
             ^^^^^^^^^^^
  File "D:\Dev\ai-engineering-orchestra\itru\windows_local_authorization_domain_owner.py", line 848, in _open_file
    raise _win32_error(f"CreateFileW failed for {path.name!r}")
PermissionError: [WinError 5] CreateFileW failed for 'Abdelrahman'

----------------------------------------------------------------------
Ran 29 tests in 0.317s

FAILED (errors=34)
```

#### F2 attempt 2

Exit code: 1. Reviewed native execution boundary; 29 tests, 1 test-only read-only fault-hook error. Corrected within the authorized new test file.

```text
test_R01_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R01_success) ... ITRU060_FIXTURE test_R01_success parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-fgu63ubt registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-fgu63ubt\local-appdata ledger=ledger::itru-060::463dab7db2c44d36b02a47948956afd8
ok
test_R02_empty_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R02_empty_success) ... ITRU060_FIXTURE test_R02_empty_success parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-eedcce_9 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-eedcce_9\local-appdata ledger=ledger::itru-060::cb98d3c6a3cb4a5894091d356a9bbe9c
ok
test_R03_maximum_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R03_maximum_success) ... ITRU060_FIXTURE test_R03_maximum_success parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-7xuphek0 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-7xuphek0\local-appdata ledger=ledger::itru-060::0cee9859c9aa434686507abe8fcc0814
ok
test_R04_pre_read_size_limit (tests.test_controlled_execution_result.ControlledResultScenarios.test_R04_pre_read_size_limit) ... ITRU060_FIXTURE test_R04_pre_read_size_limit parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-h_j6et2x registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-h_j6et2x\local-appdata ledger=ledger::itru-060::a0c4269a2c0248298ebae8a052acc206
ok
test_R05_missing_resource (tests.test_controlled_execution_result.ControlledResultScenarios.test_R05_missing_resource) ... ITRU060_FIXTURE test_R05_missing_resource parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-sahqfjwd registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-sahqfjwd\local-appdata ledger=ledger::itru-060::c6e0c108c8d14745a08ab906594b6a00
ok
test_R06_containment_rejection (tests.test_controlled_execution_result.ControlledResultScenarios.test_R06_containment_rejection) ... ITRU060_FIXTURE test_R06_containment_rejection parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-i0lc7xjx registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-i0lc7xjx\local-appdata ledger=ledger::itru-060::2ce45e5f40dd4c818518f2e6a7259bba
ok
test_R07_adapter_unavailable (tests.test_controlled_execution_result.ControlledResultScenarios.test_R07_adapter_unavailable) ... ITRU060_FIXTURE test_R07_adapter_unavailable parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-30qdu_i7 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-30qdu_i7\local-appdata ledger=ledger::itru-060::d07c34b9090d41b4863dda92580fad1e
ok
test_R08_proven_pre_content_read_failure (tests.test_controlled_execution_result.ControlledResultScenarios.test_R08_proven_pre_content_read_failure) ... ITRU060_FIXTURE test_R08_proven_pre_content_read_failure parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-u1v9yb4s registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-u1v9yb4s\local-appdata ledger=ledger::itru-060::9d604d7c813749389bf61ae8d2ca5aa4
ok
test_R09_proven_pre_content_resource_changed (tests.test_controlled_execution_result.ControlledResultScenarios.test_R09_proven_pre_content_resource_changed) ... ITRU060_FIXTURE test_R09_proven_pre_content_resource_changed parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-p7ix0ewt registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-p7ix0ewt\local-appdata ledger=ledger::itru-060::ae96a7f69fa843cb8375aed0aa7ac03b
ok
test_R10_guard_lost_before_start (tests.test_controlled_execution_result.ControlledResultScenarios.test_R10_guard_lost_before_start) ... ITRU060_FIXTURE test_R10_guard_lost_before_start parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-54mt8ym5 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-54mt8ym5\local-appdata ledger=ledger::itru-060::c9ba7a04dede4b19bd9f940ae0f01098
ok
test_R11_ownership_lost_before_start (tests.test_controlled_execution_result.ControlledResultScenarios.test_R11_ownership_lost_before_start) ... ITRU060_FIXTURE test_R11_ownership_lost_before_start parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-kk5ko91r registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-kk5ko91r\local-appdata ledger=ledger::itru-060::1bb80f06689c485c9311999ef8acd31d
ok
test_R12_post_request_failure_codes (tests.test_controlled_execution_result.ControlledResultScenarios.test_R12_post_request_failure_codes) ... ITRU060_FIXTURE test_R12_post_request_failure_codes parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-txcd1tgu registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-txcd1tgu\local-appdata ledger=ledger::itru-060::356d34a194ab44568af7dedb8c63213f
ITRU060_FIXTURE test_R12_post_request_failure_codes parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-2dg1y5xr registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-2dg1y5xr\local-appdata ledger=ledger::itru-060::27410e0f6d9b47029cb5e857fd61a8d7
ok
test_R13_final_metadata_changed (tests.test_controlled_execution_result.ControlledResultScenarios.test_R13_final_metadata_changed) ... ITRU060_FIXTURE test_R13_final_metadata_changed parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-dgs08nyb registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-dgs08nyb\local-appdata ledger=ledger::itru-060::cf1401d6a9e84c94b60880e5c359a4f0
ok
test_R14_outer_ownership_postcheck (tests.test_controlled_execution_result.ControlledResultScenarios.test_R14_outer_ownership_postcheck) ... ITRU060_FIXTURE test_R14_outer_ownership_postcheck parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-mt7nm_bu registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-mt7nm_bu\local-appdata ledger=ledger::itru-060::e42cb33b7a5f48b690570d7ec43d8b81
ERROR
test_R15_cleanup_dominates_no_content (tests.test_controlled_execution_result.ControlledResultScenarios.test_R15_cleanup_dominates_no_content) ... ITRU060_FIXTURE test_R15_cleanup_dominates_no_content parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-4epsvil_ registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-4epsvil_\local-appdata ledger=ledger::itru-060::ab00138dc8a0400c8d7367489b5e95c2
ok
test_R18_reconstructed_entry_is_not_acknowledgement (tests.test_controlled_execution_result.ControlledResultScenarios.test_R18_reconstructed_entry_is_not_acknowledgement) ... ITRU060_FIXTURE test_R18_reconstructed_entry_is_not_acknowledgement parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-cjf6nywo registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-cjf6nywo\local-appdata ledger=ledger::itru-060::87c4f2a2f8d04a8e96e15873821854b5
ok
test_R19_same_run_id_changed_contract (tests.test_controlled_execution_result.ControlledResultScenarios.test_R19_same_run_id_changed_contract) ... ITRU060_FIXTURE test_R19_same_run_id_changed_contract parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-2ioci3m5 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-2ioci3m5\local-appdata ledger=ledger::itru-060::bcdc756c96b34022b76861365102b08b
ITRU060_FIXTURE test_R19_same_run_id_changed_contract parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-d8k6ldkg registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-d8k6ldkg\local-appdata ledger=ledger::itru-060::5826868661604fe38af13eda4efcaf50
ok
test_R20_tool_substitution (tests.test_controlled_execution_result.ControlledResultScenarios.test_R20_tool_substitution) ... ITRU060_FIXTURE test_R20_tool_substitution parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-k54u70nb registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-k54u70nb\local-appdata ledger=ledger::itru-060::3fffe0e64a8a4724aea2e6ff3e005922
ok
test_R21_ledger_scoping_and_foreign_subject (tests.test_controlled_execution_result.ControlledResultScenarios.test_R21_ledger_scoping_and_foreign_subject) ... ITRU060_FIXTURE test_R21_ledger_scoping_and_foreign_subject parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-k4e9hfwh registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-k4e9hfwh\local-appdata ledger=ledger::itru-060::9335524b19644197b6d313f2797e7e31
ITRU060_FIXTURE test_R21_ledger_scoping_and_foreign_subject parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-n9889xgt registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-n9889xgt\local-appdata ledger=ledger::itru-060::fb5f753a569f4c8f867eb67190b8e80e
ITRU060_FIXTURE test_R21_ledger_scoping_and_foreign_subject parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-8h3552ea registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-8h3552ea\local-appdata ledger=ledger::itru-060::43e3f78e8e664cc69c4c62c74936263b
ok
test_R22_exact_claim_executor_generation (tests.test_controlled_execution_result.ControlledResultScenarios.test_R22_exact_claim_executor_generation) ... ITRU060_FIXTURE test_R22_exact_claim_executor_generation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-5hch5ajq registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-5hch5ajq\local-appdata ledger=ledger::itru-060::7b15495dfc39403dbc18bf66e2667430
ITRU060_FIXTURE test_R22_exact_claim_executor_generation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-k39qwmx6 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-k39qwmx6\local-appdata ledger=ledger::itru-060::374d936f299b49d9a685d76e8bd13fa7
ITRU060_FIXTURE test_R22_exact_claim_executor_generation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-frsn0xiu registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-frsn0xiu\local-appdata ledger=ledger::itru-060::ebe7126c8c8e4c6f96d5d630659c9866
ok
test_R23_rejected_entry_preserves_diagnostic (tests.test_controlled_execution_result.ControlledResultScenarios.test_R23_rejected_entry_preserves_diagnostic) ... ITRU060_FIXTURE test_R23_rejected_entry_preserves_diagnostic parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-4zyrcjlz registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-4zyrcjlz\local-appdata ledger=ledger::itru-060::db37816d0ee54459a21d88bfab8e367e
ok
test_R24_commit_unknown_no_result_or_effect (tests.test_controlled_execution_result.ControlledResultScenarios.test_R24_commit_unknown_no_result_or_effect) ... ITRU060_FIXTURE test_R24_commit_unknown_no_result_or_effect parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-gcqk84xu registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-gcqk84xu\local-appdata ledger=ledger::itru-060::d70500fb3732470fb8e4f7f7a74e65b8
ok
test_R25_history_has_no_result_factory (tests.test_controlled_execution_result.ControlledResultScenarios.test_R25_history_has_no_result_factory) ... ITRU060_FIXTURE test_R25_history_has_no_result_factory parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-rt9jrdwn registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-rt9jrdwn\local-appdata ledger=ledger::itru-060::74c820f4449d41469a06b7cdbc6c00ce
ok
test_R26_component_restart_never_recovers_invocation (tests.test_controlled_execution_result.ControlledResultScenarios.test_R26_component_restart_never_recovers_invocation) ... ITRU060_FIXTURE test_R26_component_restart_never_recovers_invocation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-p90q9bch registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-p90q9bch\local-appdata ledger=ledger::itru-060::44a2d77258a84e38a8bd0978a67ed69f
ok
test_R27_repeated_invocation_cannot_publish_again (tests.test_controlled_execution_result.ControlledResultScenarios.test_R27_repeated_invocation_cannot_publish_again) ... ITRU060_FIXTURE test_R27_repeated_invocation_cannot_publish_again parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-p1v2c990 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-p1v2c990\local-appdata ledger=ledger::itru-060::6ded4bd2edfc43bcbb745b830fa1d5e1
ok
test_R32_historical_and_noncanonical_work_rejected (tests.test_controlled_execution_result.ControlledResultScenarios.test_R32_historical_and_noncanonical_work_rejected) ... ITRU060_FIXTURE test_R32_historical_and_noncanonical_work_rejected parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-bo_tel8b registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-bo_tel8b\local-appdata ledger=ledger::itru-060::113c88186c0540f69e96a38518819e53
ok
test_R33_fatal_interruption_preserved (tests.test_controlled_execution_result.ControlledResultScenarios.test_R33_fatal_interruption_preserved) ... ITRU060_FIXTURE test_R33_fatal_interruption_preserved parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-m9m1zx61 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-m9m1zx61\local-appdata ledger=ledger::itru-060::73677f1762d049729550da59a85b284d
ok
test_R34_success_suppressed_by_cleanup_or_construction (tests.test_controlled_execution_result.ControlledResultScenarios.test_R34_success_suppressed_by_cleanup_or_construction) ... ITRU060_FIXTURE test_R34_success_suppressed_by_cleanup_or_construction parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-m1qupint registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-m1qupint\local-appdata ledger=ledger::itru-060::65b448c3760b4bb485b5237f2a759e92
ITRU060_FIXTURE test_R34_success_suppressed_by_cleanup_or_construction parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-r5v7oyyx registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-r5v7oyyx\local-appdata ledger=ledger::itru-060::4304863f550244ddbc66ff1e7e55b933
ok
test_R35_first_request_and_empty_probe_failure (tests.test_controlled_execution_result.ControlledResultScenarios.test_R35_first_request_and_empty_probe_failure) ... ITRU060_FIXTURE test_R35_first_request_and_empty_probe_failure parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-n_mhavq0 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-n_mhavq0\local-appdata ledger=ledger::itru-060::2c52acf5c4fe4b9f9d1f190c33986b4f
ITRU060_FIXTURE test_R35_first_request_and_empty_probe_failure parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-fpw5q_yd registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-fpw5q_yd\local-appdata ledger=ledger::itru-060::2342a5d318344fa29ba623b7e7aaad61
ok

======================================================================
ERROR: test_R14_outer_ownership_postcheck (tests.test_controlled_execution_result.ControlledResultScenarios.test_R14_outer_ownership_postcheck)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1581, in __enter__
    setattr(self.target, self.attribute, new_attr)
AttributeError: '_WindowsOwnedAuthorizationDomainSession' object attribute '_revalidate' is read-only

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "D:\Dev\ai-engineering-orchestra\tests\test_controlled_execution_result.py", line 198, in test_R14_outer_ownership_postcheck
    mock.patch.object(rig.session, "_revalidate", side_effect=lost):
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1594, in __enter__
    if not self.__exit__(*sys.exc_info()):
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1605, in __exit__
    delattr(self.target, self.attribute)
AttributeError: '_WindowsOwnedAuthorizationDomainSession' object attribute '_revalidate' is read-only

----------------------------------------------------------------------
Ran 29 tests in 11.547s

FAILED (errors=1)
```

#### F2 attempt 3

Exit code: 0. PASS 29/29 after fault-hook correction; no skips.

```text
test_R01_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R01_success) ... ITRU060_FIXTURE test_R01_success parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-n_l_ewrj registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-n_l_ewrj\local-appdata ledger=ledger::itru-060::fba73baae02c40ccba04c8084d7238ec
ok
test_R02_empty_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R02_empty_success) ... ITRU060_FIXTURE test_R02_empty_success parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-bd5h_sqm registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-bd5h_sqm\local-appdata ledger=ledger::itru-060::db8c150e037343a7beb1151a3091752a
ok
test_R03_maximum_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R03_maximum_success) ... ITRU060_FIXTURE test_R03_maximum_success parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-aulfu7tx registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-aulfu7tx\local-appdata ledger=ledger::itru-060::60ded493019b4167af6ca5d53866969f
ok
test_R04_pre_read_size_limit (tests.test_controlled_execution_result.ControlledResultScenarios.test_R04_pre_read_size_limit) ... ITRU060_FIXTURE test_R04_pre_read_size_limit parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-bbp4nfy9 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-bbp4nfy9\local-appdata ledger=ledger::itru-060::c6d2b70fa6d74bd88a94d80b73164fe6
ok
test_R05_missing_resource (tests.test_controlled_execution_result.ControlledResultScenarios.test_R05_missing_resource) ... ITRU060_FIXTURE test_R05_missing_resource parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-dfmdjkf8 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-dfmdjkf8\local-appdata ledger=ledger::itru-060::827d2033a0464d71b85112c2a085b1fa
ok
test_R06_containment_rejection (tests.test_controlled_execution_result.ControlledResultScenarios.test_R06_containment_rejection) ... ITRU060_FIXTURE test_R06_containment_rejection parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-6r0ooyql registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-6r0ooyql\local-appdata ledger=ledger::itru-060::7cf036e0a5d1493693d65a47bfbf5330
ok
test_R07_adapter_unavailable (tests.test_controlled_execution_result.ControlledResultScenarios.test_R07_adapter_unavailable) ... ITRU060_FIXTURE test_R07_adapter_unavailable parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-0cx00fev registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-0cx00fev\local-appdata ledger=ledger::itru-060::9fd8aeb0bde94915a88591c49f7f6774
ok
test_R08_proven_pre_content_read_failure (tests.test_controlled_execution_result.ControlledResultScenarios.test_R08_proven_pre_content_read_failure) ... ITRU060_FIXTURE test_R08_proven_pre_content_read_failure parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-zg3n7ibz registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-zg3n7ibz\local-appdata ledger=ledger::itru-060::d22dfe679a3241fa80728885afe4dc51
ok
test_R09_proven_pre_content_resource_changed (tests.test_controlled_execution_result.ControlledResultScenarios.test_R09_proven_pre_content_resource_changed) ... ITRU060_FIXTURE test_R09_proven_pre_content_resource_changed parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-jyd1lu7d registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-jyd1lu7d\local-appdata ledger=ledger::itru-060::0e7b503d9418400dbd0118448de697ab
ok
test_R10_guard_lost_before_start (tests.test_controlled_execution_result.ControlledResultScenarios.test_R10_guard_lost_before_start) ... ITRU060_FIXTURE test_R10_guard_lost_before_start parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-le_gqn3n registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-le_gqn3n\local-appdata ledger=ledger::itru-060::bb25a48ba08c45a6b068c962ce5212c5
ok
test_R11_ownership_lost_before_start (tests.test_controlled_execution_result.ControlledResultScenarios.test_R11_ownership_lost_before_start) ... ITRU060_FIXTURE test_R11_ownership_lost_before_start parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-nrxqb50a registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-nrxqb50a\local-appdata ledger=ledger::itru-060::097d9f90f4d94d3d97362d8bb9147af7
ok
test_R12_post_request_failure_codes (tests.test_controlled_execution_result.ControlledResultScenarios.test_R12_post_request_failure_codes) ... ITRU060_FIXTURE test_R12_post_request_failure_codes parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-ejuluzes registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-ejuluzes\local-appdata ledger=ledger::itru-060::2f5e69452d394efab5e3971f860d62cb
ITRU060_FIXTURE test_R12_post_request_failure_codes parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-163biyck registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-163biyck\local-appdata ledger=ledger::itru-060::ef34bbaf5b4143159629f3aa5b42d066
ok
test_R13_final_metadata_changed (tests.test_controlled_execution_result.ControlledResultScenarios.test_R13_final_metadata_changed) ... ITRU060_FIXTURE test_R13_final_metadata_changed parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-o1xowckx registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-o1xowckx\local-appdata ledger=ledger::itru-060::6a4edebdcfa9477c866502ba41a2437f
ok
test_R14_outer_ownership_postcheck (tests.test_controlled_execution_result.ControlledResultScenarios.test_R14_outer_ownership_postcheck) ... ITRU060_FIXTURE test_R14_outer_ownership_postcheck parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-fyb19dd2 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-fyb19dd2\local-appdata ledger=ledger::itru-060::424505a417234d168bf2fb66e63a98fb
ok
test_R15_cleanup_dominates_no_content (tests.test_controlled_execution_result.ControlledResultScenarios.test_R15_cleanup_dominates_no_content) ... ITRU060_FIXTURE test_R15_cleanup_dominates_no_content parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-nbzqi5q9 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-nbzqi5q9\local-appdata ledger=ledger::itru-060::814e45111b094f5bab2d494a47c82e53
ok
test_R18_reconstructed_entry_is_not_acknowledgement (tests.test_controlled_execution_result.ControlledResultScenarios.test_R18_reconstructed_entry_is_not_acknowledgement) ... ITRU060_FIXTURE test_R18_reconstructed_entry_is_not_acknowledgement parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-x2jyn0sj registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-x2jyn0sj\local-appdata ledger=ledger::itru-060::ff86bb6f61394f4199b45cbb8d6d64fe
ok
test_R19_same_run_id_changed_contract (tests.test_controlled_execution_result.ControlledResultScenarios.test_R19_same_run_id_changed_contract) ... ITRU060_FIXTURE test_R19_same_run_id_changed_contract parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-8bdtrio1 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-8bdtrio1\local-appdata ledger=ledger::itru-060::f5b13fa4539543de9af7b39cd7aa9930
ITRU060_FIXTURE test_R19_same_run_id_changed_contract parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-sbgs2465 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-sbgs2465\local-appdata ledger=ledger::itru-060::9b5b1c43c9d646ad94674feeea6a1aa8
ok
test_R20_tool_substitution (tests.test_controlled_execution_result.ControlledResultScenarios.test_R20_tool_substitution) ... ITRU060_FIXTURE test_R20_tool_substitution parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-fvnwy2wl registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-fvnwy2wl\local-appdata ledger=ledger::itru-060::51fb4f5ea9534fc6a93f72b26c4e84d0
ok
test_R21_ledger_scoping_and_foreign_subject (tests.test_controlled_execution_result.ControlledResultScenarios.test_R21_ledger_scoping_and_foreign_subject) ... ITRU060_FIXTURE test_R21_ledger_scoping_and_foreign_subject parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-cxj420dp registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-cxj420dp\local-appdata ledger=ledger::itru-060::2e192bb4c96b403ea033e2a967cd7a03
ITRU060_FIXTURE test_R21_ledger_scoping_and_foreign_subject parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-9npjps3c registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-9npjps3c\local-appdata ledger=ledger::itru-060::d5d664c3fa5a4f57a7694fcfd74b2b05
ITRU060_FIXTURE test_R21_ledger_scoping_and_foreign_subject parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-pcprcmo5 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-pcprcmo5\local-appdata ledger=ledger::itru-060::80c7b7e4bbdd4ab7a71edcb8a982fc1a
ok
test_R22_exact_claim_executor_generation (tests.test_controlled_execution_result.ControlledResultScenarios.test_R22_exact_claim_executor_generation) ... ITRU060_FIXTURE test_R22_exact_claim_executor_generation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-70i7be_q registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-70i7be_q\local-appdata ledger=ledger::itru-060::fb0133840fd14310a22aa835fb95f3bb
ITRU060_FIXTURE test_R22_exact_claim_executor_generation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-vx2fva21 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-vx2fva21\local-appdata ledger=ledger::itru-060::9f1768445d4a464e8e62698da0307f70
ITRU060_FIXTURE test_R22_exact_claim_executor_generation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-cu046nqe registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-cu046nqe\local-appdata ledger=ledger::itru-060::f9a813b0f53e440b9c023d00c90e07e8
ok
test_R23_rejected_entry_preserves_diagnostic (tests.test_controlled_execution_result.ControlledResultScenarios.test_R23_rejected_entry_preserves_diagnostic) ... ITRU060_FIXTURE test_R23_rejected_entry_preserves_diagnostic parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-2v8p_1d9 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-2v8p_1d9\local-appdata ledger=ledger::itru-060::349769a5be5a4b78ac4884fcd3521943
ok
test_R24_commit_unknown_no_result_or_effect (tests.test_controlled_execution_result.ControlledResultScenarios.test_R24_commit_unknown_no_result_or_effect) ... ITRU060_FIXTURE test_R24_commit_unknown_no_result_or_effect parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-z5rka8j1 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-z5rka8j1\local-appdata ledger=ledger::itru-060::fa87a79771a24f369a7559627356acbd
ok
test_R25_history_has_no_result_factory (tests.test_controlled_execution_result.ControlledResultScenarios.test_R25_history_has_no_result_factory) ... ITRU060_FIXTURE test_R25_history_has_no_result_factory parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-dcnl9dqe registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-dcnl9dqe\local-appdata ledger=ledger::itru-060::0ae761daba714d729857f94bd2992b97
ok
test_R26_component_restart_never_recovers_invocation (tests.test_controlled_execution_result.ControlledResultScenarios.test_R26_component_restart_never_recovers_invocation) ... ITRU060_FIXTURE test_R26_component_restart_never_recovers_invocation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-zfduv50w registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-zfduv50w\local-appdata ledger=ledger::itru-060::65f41899c57c49fa8df700ad19ece1c4
ok
test_R27_repeated_invocation_cannot_publish_again (tests.test_controlled_execution_result.ControlledResultScenarios.test_R27_repeated_invocation_cannot_publish_again) ... ITRU060_FIXTURE test_R27_repeated_invocation_cannot_publish_again parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-t1991vwd registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-t1991vwd\local-appdata ledger=ledger::itru-060::b632d3e9b90046e68741fa8c79bda354
ok
test_R32_historical_and_noncanonical_work_rejected (tests.test_controlled_execution_result.ControlledResultScenarios.test_R32_historical_and_noncanonical_work_rejected) ... ITRU060_FIXTURE test_R32_historical_and_noncanonical_work_rejected parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-x79g52qk registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-x79g52qk\local-appdata ledger=ledger::itru-060::45cb68c7691d4a55bcfa5c71a9aa9c9a
ok
test_R33_fatal_interruption_preserved (tests.test_controlled_execution_result.ControlledResultScenarios.test_R33_fatal_interruption_preserved) ... ITRU060_FIXTURE test_R33_fatal_interruption_preserved parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-365icjat registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-365icjat\local-appdata ledger=ledger::itru-060::1d9157e0b62f40e38dfc8c2f254e2976
ok
test_R34_success_suppressed_by_cleanup_or_construction (tests.test_controlled_execution_result.ControlledResultScenarios.test_R34_success_suppressed_by_cleanup_or_construction) ... ITRU060_FIXTURE test_R34_success_suppressed_by_cleanup_or_construction parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-zm2m7z0o registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-zm2m7z0o\local-appdata ledger=ledger::itru-060::a95fc8ee16654f05ac2d80873331d113
ITRU060_FIXTURE test_R34_success_suppressed_by_cleanup_or_construction parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-i_2nxi2b registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-i_2nxi2b\local-appdata ledger=ledger::itru-060::80e5f6e07b13456fafaed02cb93c32d5
ok
test_R35_first_request_and_empty_probe_failure (tests.test_controlled_execution_result.ControlledResultScenarios.test_R35_first_request_and_empty_probe_failure) ... ITRU060_FIXTURE test_R35_first_request_and_empty_probe_failure parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-pmck_cgw registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-pmck_cgw\local-appdata ledger=ledger::itru-060::068e1dbfbbbc46769abab6776fb6afd2
ITRU060_FIXTURE test_R35_first_request_and_empty_probe_failure parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-wr9tkm2a registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-wr9tkm2a\local-appdata ledger=ledger::itru-060::9831c311392c452ab52f9386fbbb61f5
ok

----------------------------------------------------------------------
Ran 29 tests in 11.803s

OK
```

#### F2 attempt 4

Exit code: 0. Final PASS 29/29 after completing the planned R32 operation-rejection variant; no skips.

```text
test_R01_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R01_success) ... ITRU060_FIXTURE test_R01_success parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-pf39hh89 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-pf39hh89\local-appdata ledger=ledger::itru-060::7724acf2132a4fc9af16be5d28473d27
ok
test_R02_empty_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R02_empty_success) ... ITRU060_FIXTURE test_R02_empty_success parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-c8wcsv98 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-c8wcsv98\local-appdata ledger=ledger::itru-060::e761ba21d036410eb52f42a559dc4c62
ok
test_R03_maximum_success (tests.test_controlled_execution_result.ControlledResultScenarios.test_R03_maximum_success) ... ITRU060_FIXTURE test_R03_maximum_success parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-0hbtcryq registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-0hbtcryq\local-appdata ledger=ledger::itru-060::a692f365306f4f3c857c64194b20c684
ok
test_R04_pre_read_size_limit (tests.test_controlled_execution_result.ControlledResultScenarios.test_R04_pre_read_size_limit) ... ITRU060_FIXTURE test_R04_pre_read_size_limit parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-9dzd7e6z registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-9dzd7e6z\local-appdata ledger=ledger::itru-060::a446c6c8718949178e746265a10edf29
ok
test_R05_missing_resource (tests.test_controlled_execution_result.ControlledResultScenarios.test_R05_missing_resource) ... ITRU060_FIXTURE test_R05_missing_resource parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-hajzxlfl registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-hajzxlfl\local-appdata ledger=ledger::itru-060::28666b46ef00457f818227a5f465f2ef
ok
test_R06_containment_rejection (tests.test_controlled_execution_result.ControlledResultScenarios.test_R06_containment_rejection) ... ITRU060_FIXTURE test_R06_containment_rejection parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-alsn7w9m registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-alsn7w9m\local-appdata ledger=ledger::itru-060::743711bc6087424a856e66975a84c149
ok
test_R07_adapter_unavailable (tests.test_controlled_execution_result.ControlledResultScenarios.test_R07_adapter_unavailable) ... ITRU060_FIXTURE test_R07_adapter_unavailable parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-wsip5e60 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-wsip5e60\local-appdata ledger=ledger::itru-060::49f4cf6b8f2d4aa48c932cf7bcf1b400
ok
test_R08_proven_pre_content_read_failure (tests.test_controlled_execution_result.ControlledResultScenarios.test_R08_proven_pre_content_read_failure) ... ITRU060_FIXTURE test_R08_proven_pre_content_read_failure parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-lz97i7t0 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-lz97i7t0\local-appdata ledger=ledger::itru-060::b3e86b1bcf2549229f379434eaa6cc1d
ok
test_R09_proven_pre_content_resource_changed (tests.test_controlled_execution_result.ControlledResultScenarios.test_R09_proven_pre_content_resource_changed) ... ITRU060_FIXTURE test_R09_proven_pre_content_resource_changed parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-6b3oqrmx registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-6b3oqrmx\local-appdata ledger=ledger::itru-060::0c91f7c0657a41378ed201b482f31dd8
ok
test_R10_guard_lost_before_start (tests.test_controlled_execution_result.ControlledResultScenarios.test_R10_guard_lost_before_start) ... ITRU060_FIXTURE test_R10_guard_lost_before_start parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-kxz8jnwz registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-kxz8jnwz\local-appdata ledger=ledger::itru-060::79d2f96d86fd48e49dd959d165cda7a3
ok
test_R11_ownership_lost_before_start (tests.test_controlled_execution_result.ControlledResultScenarios.test_R11_ownership_lost_before_start) ... ITRU060_FIXTURE test_R11_ownership_lost_before_start parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-wv7az1to registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-wv7az1to\local-appdata ledger=ledger::itru-060::17a071057e8742b1ab363ac0ad0521e1
ok
test_R12_post_request_failure_codes (tests.test_controlled_execution_result.ControlledResultScenarios.test_R12_post_request_failure_codes) ... ITRU060_FIXTURE test_R12_post_request_failure_codes parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-zm8g18jt registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-zm8g18jt\local-appdata ledger=ledger::itru-060::7629c4a22e5b4962829e3fa611dbfe3e
ITRU060_FIXTURE test_R12_post_request_failure_codes parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-5lap0uyi registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-5lap0uyi\local-appdata ledger=ledger::itru-060::110faf42dc1041a78ab9b84fc0c01eb5
ok
test_R13_final_metadata_changed (tests.test_controlled_execution_result.ControlledResultScenarios.test_R13_final_metadata_changed) ... ITRU060_FIXTURE test_R13_final_metadata_changed parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-zjfjn0k4 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-zjfjn0k4\local-appdata ledger=ledger::itru-060::84671310563444908a2924202148e635
ok
test_R14_outer_ownership_postcheck (tests.test_controlled_execution_result.ControlledResultScenarios.test_R14_outer_ownership_postcheck) ... ITRU060_FIXTURE test_R14_outer_ownership_postcheck parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-z2jc64g1 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-z2jc64g1\local-appdata ledger=ledger::itru-060::fc7e9153ba2e4ee8bba21a8972fc0997
ok
test_R15_cleanup_dominates_no_content (tests.test_controlled_execution_result.ControlledResultScenarios.test_R15_cleanup_dominates_no_content) ... ITRU060_FIXTURE test_R15_cleanup_dominates_no_content parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-7g1mtq4f registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-7g1mtq4f\local-appdata ledger=ledger::itru-060::c5e889c20a0848f394299e3fe0483aa5
ok
test_R18_reconstructed_entry_is_not_acknowledgement (tests.test_controlled_execution_result.ControlledResultScenarios.test_R18_reconstructed_entry_is_not_acknowledgement) ... ITRU060_FIXTURE test_R18_reconstructed_entry_is_not_acknowledgement parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-nr20bk1l registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-nr20bk1l\local-appdata ledger=ledger::itru-060::b885846016734433983ef968dc5c9895
ok
test_R19_same_run_id_changed_contract (tests.test_controlled_execution_result.ControlledResultScenarios.test_R19_same_run_id_changed_contract) ... ITRU060_FIXTURE test_R19_same_run_id_changed_contract parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-_alh4n4q registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-_alh4n4q\local-appdata ledger=ledger::itru-060::0be377b8e86340339f939a5cdc558e27
ITRU060_FIXTURE test_R19_same_run_id_changed_contract parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-7y2me8mb registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-7y2me8mb\local-appdata ledger=ledger::itru-060::4d4820e481864ce3a40c0d6528728fc6
ok
test_R20_tool_substitution (tests.test_controlled_execution_result.ControlledResultScenarios.test_R20_tool_substitution) ... ITRU060_FIXTURE test_R20_tool_substitution parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-f7l7zc7x registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-f7l7zc7x\local-appdata ledger=ledger::itru-060::4607c5d113fd42c588ce9e0d5d1e7c77
ok
test_R21_ledger_scoping_and_foreign_subject (tests.test_controlled_execution_result.ControlledResultScenarios.test_R21_ledger_scoping_and_foreign_subject) ... ITRU060_FIXTURE test_R21_ledger_scoping_and_foreign_subject parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-_3vv8b7t registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-_3vv8b7t\local-appdata ledger=ledger::itru-060::113b04a99d96413796f3a7e6af8d0bfd
ITRU060_FIXTURE test_R21_ledger_scoping_and_foreign_subject parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-sbg98r81 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-sbg98r81\local-appdata ledger=ledger::itru-060::d44267cf47704ed69f7b2ee3fc0214c0
ITRU060_FIXTURE test_R21_ledger_scoping_and_foreign_subject parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-phavnohs registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-phavnohs\local-appdata ledger=ledger::itru-060::1f079ea116a8419eb17c329611a97c00
ok
test_R22_exact_claim_executor_generation (tests.test_controlled_execution_result.ControlledResultScenarios.test_R22_exact_claim_executor_generation) ... ITRU060_FIXTURE test_R22_exact_claim_executor_generation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-bjvuhxb_ registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-bjvuhxb_\local-appdata ledger=ledger::itru-060::f067df196eb54d39825465a7349b1e55
ITRU060_FIXTURE test_R22_exact_claim_executor_generation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-4uynqpk4 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-4uynqpk4\local-appdata ledger=ledger::itru-060::f78a2df40cac459997cb03f5b0e0f42e
ITRU060_FIXTURE test_R22_exact_claim_executor_generation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-o1rnov0v registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-o1rnov0v\local-appdata ledger=ledger::itru-060::47d1452bc2cb4417bd6fe603b4923072
ok
test_R23_rejected_entry_preserves_diagnostic (tests.test_controlled_execution_result.ControlledResultScenarios.test_R23_rejected_entry_preserves_diagnostic) ... ITRU060_FIXTURE test_R23_rejected_entry_preserves_diagnostic parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-yao87d82 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-yao87d82\local-appdata ledger=ledger::itru-060::2ee246ff64c34a83b65c8f4c157e2b5d
ok
test_R24_commit_unknown_no_result_or_effect (tests.test_controlled_execution_result.ControlledResultScenarios.test_R24_commit_unknown_no_result_or_effect) ... ITRU060_FIXTURE test_R24_commit_unknown_no_result_or_effect parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-1yyi3p42 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-1yyi3p42\local-appdata ledger=ledger::itru-060::fbd548bc043f49ffa6cfd660e9b1974a
ok
test_R25_history_has_no_result_factory (tests.test_controlled_execution_result.ControlledResultScenarios.test_R25_history_has_no_result_factory) ... ITRU060_FIXTURE test_R25_history_has_no_result_factory parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-080b59z7 registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-080b59z7\local-appdata ledger=ledger::itru-060::0aa55b557e674b7abe717e7975839002
ok
test_R26_component_restart_never_recovers_invocation (tests.test_controlled_execution_result.ControlledResultScenarios.test_R26_component_restart_never_recovers_invocation) ... ITRU060_FIXTURE test_R26_component_restart_never_recovers_invocation parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-r0kxjqoh registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-r0kxjqoh\local-appdata ledger=ledger::itru-060::c4075c1ecde347f2aecb7c344165754a
ok
test_R27_repeated_invocation_cannot_publish_again (tests.test_controlled_execution_result.ControlledResultScenarios.test_R27_repeated_invocation_cannot_publish_again) ... ITRU060_FIXTURE test_R27_repeated_invocation_cannot_publish_again parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-zmqx4jon registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-zmqx4jon\local-appdata ledger=ledger::itru-060::69d7e6265fd14aa78caf4ecb223b7516
ok
test_R32_historical_and_noncanonical_work_rejected (tests.test_controlled_execution_result.ControlledResultScenarios.test_R32_historical_and_noncanonical_work_rejected) ... ITRU060_FIXTURE test_R32_historical_and_noncanonical_work_rejected parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-xme4s2jm registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-xme4s2jm\local-appdata ledger=ledger::itru-060::1f120f75c30f4aef8a841c7cd4f31a8e
ITRU060_FIXTURE test_R32_historical_and_noncanonical_work_rejected parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-wz9g39cs registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-wz9g39cs\local-appdata ledger=ledger::itru-060::1e778708508c4e65b7d4d56b0e9d70ad
ok
test_R33_fatal_interruption_preserved (tests.test_controlled_execution_result.ControlledResultScenarios.test_R33_fatal_interruption_preserved) ... ITRU060_FIXTURE test_R33_fatal_interruption_preserved parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-8ibraw8l registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-8ibraw8l\local-appdata ledger=ledger::itru-060::03a025170ad84c6daf1e691a8dcba711
ok
test_R34_success_suppressed_by_cleanup_or_construction (tests.test_controlled_execution_result.ControlledResultScenarios.test_R34_success_suppressed_by_cleanup_or_construction) ... ITRU060_FIXTURE test_R34_success_suppressed_by_cleanup_or_construction parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-yhyzh3ko registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-yhyzh3ko\local-appdata ledger=ledger::itru-060::608e9a841f3d4cd8b5e15db0d2178ace
ITRU060_FIXTURE test_R34_success_suppressed_by_cleanup_or_construction parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-_tkoy4to registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-_tkoy4to\local-appdata ledger=ledger::itru-060::bfb42c32a4d745a4bf8c664752b3680b
ok
test_R35_first_request_and_empty_probe_failure (tests.test_controlled_execution_result.ControlledResultScenarios.test_R35_first_request_and_empty_probe_failure) ... ITRU060_FIXTURE test_R35_first_request_and_empty_probe_failure parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-e6v9x8yj registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-e6v9x8yj\local-appdata ledger=ledger::itru-060::38273778cd634ed6b3ee6976b6e2870a
ITRU060_FIXTURE test_R35_first_request_and_empty_probe_failure parent=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-iub25srs registry=C:\Users\Abdelrahman\AppData\Local\Temp\aio-053-local-trust-iub25srs\local-appdata ledger=ledger::itru-060::41693e1153e545c488a8d7ddf16084f3
ok

----------------------------------------------------------------------
Ran 29 tests in 12.914s

OK
```

### F3 exact command

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -I -B -c "import sys, pathlib, unittest; sys.path.insert(0, str(pathlib.Path.cwd())); suite = unittest.defaultTestLoader.loadTestsFromName('tests.test_durable_execution_entry_and_controlled_invocation.ItruControlledInvocationIdentityTests'); result = unittest.TextTestRunner(verbosity=2).run(suite); sys.exit(0 if result.wasSuccessful() and result.testsRun == 2 and not result.skipped else 1)"
```

#### F3 attempt 1

Exit code: 0. PASS 2/2; no skips.

```text
test_historical_capability_and_legacy_binding_cannot_enter_or_invoke (tests.test_durable_execution_entry_and_controlled_invocation.ItruControlledInvocationIdentityTests.test_historical_capability_and_legacy_binding_cannot_enter_or_invoke) ... ok
test_itru_binding_executes_the_original_chain_once (tests.test_durable_execution_entry_and_controlled_invocation.ItruControlledInvocationIdentityTests.test_itru_binding_executes_the_original_chain_once) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.574s

OK
```

## Phase 2 stop boundary

Phase 2 implementation and authorized validation are finished. No fresh final
specialist/formal independent review or formal closure Quality Gate evaluation
was performed. No staging, commit, push or merge occurred. Task is in_progress;
I3/H2 remain unchecked. Next authorization: fresh final specialist and formal
independent review of the exact implemented change and these receipts only.
Final closure evaluation and Human final approval are not inferred.

