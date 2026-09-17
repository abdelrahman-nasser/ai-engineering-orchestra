# AIO-020 Review

Status: Completed; Human-approved

## Workflow evidence

The Task follows `security-sensitive-change` in canonical stage order. Security
analysis, implementation, validation, independent review, security review, and
the Human Control checkpoint are recorded here as evidence becomes available.

The separate security-reviewer completed pre-implementation analysis without
editing files. It treated execution transparency, a single Manifest source,
structural-only isolation, brand-neutral recursion protection, planning-based
gating, diagnostic deduplication, honest authority claims, and entry-point
convergence as release-blocking controls. The four-field contract was found
sufficient. The implementation accepted those controls; the Human-specified
allowance for an inherited marker value of exactly `0` takes precedence over the
reviewer's stricter initial suggestion to reject every present marker.

## Implementation evidence

`engineering_orchestration.project_verification` now provides the thin aggregate
`ProjectVerificationResult` and `verify_project()` composition. Structural-only
mode returns before planning or execution operations. Full mode validates
structure, independently plans declarations, executes only when
`planning.is_ready`, scopes `ENGINEERING_ORCHESTRATION_VERIFY_DEPTH=1` around the
runner with `finally` restoration, and aggregates PASS/FAIL/ERROR into exit codes
0/1/2. `KeyboardInterrupt` remains propagated by the runner and maps to 130 at the
CLI boundary.

The CLI discloses repository-controlled execution, inherited caller authority,
the lack of sandboxing, `.ai/project.yaml`, and ordered Check IDs before launch.
Failure output includes duration, return code where available, runner error, and
bounded stdout/stderr; PASS output remains suppressed. No Quality Gate success
language or result mapping was added.

Orchestra's Manifest owns the exact seven declarations in legacy order. The
fixed `DEFAULT_CHECKS` registry and separate legacy runner were removed.
`run_preflight` is a compatibility delegate, and `scripts/verify_repo.py` routes
through the same public command implementation. The schema still exposes exactly
`id`, `command`, `cwd`, and `timeout_seconds`.

## Validation evidence

- Legacy migration baseline: AIO-019 recorded live `7/7` preflight success at
  `fe1d20dce5343e1d5fde9118124ffd871aa8a593`; inspection of that commit recorded
  unit tests, Task/Workflow/Role/Manifest validators, Markdown lint, and Git diff
  check in the same order now declared by the Manifest.
- Windows PATH Python resolved to
  `C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe`,
  version 3.12.10. The restricted shell itself had no `python`, confirming the
  documented supported/activated-environment requirement.
- Focused migration/CLI/runner/packaging tests: 132 ran before the final fixture
  additions; 127 passed, four platform-specific cases skipped, and one wrapped
  help-text assertion was corrected. A recursion-inherited focused rerun passed
  22/22; two final focused cases were subsequently added for duplicate Manifest
  diagnostics and exceptional marker restoration.
- Final full Windows unit discovery passed 214 tests with four expected skips: three
  directory-symlink cases unavailable under the host privilege and one POSIX
  signal case. The later live dogfood reran the full unit check successfully
  under the inherited recursion marker.
- Task validation passed 37/37 plus 10/10 Workflow references; Workflow 42/42;
  Role 34/34; Project Manifest 66/66.
- Live Windows source `python -B aio.py verify` and compatibility
  `python -B scripts/verify_repo.py` each ran the seven Manifest checks in order
  and reported 7 PASS, including `npx.cmd` Markdown lint and Git.
- `aio.py verify --structure`, help disclosure, recursion rejection with exit 2,
  marker restoration tests, external adopter, zero checks, FAIL/ERROR dominance,
  invalid structural data with continued execution, planning prevention, missing
  executable continuation, and interruption mapping passed.
- Editable and normal-wheel smoke passed. Both installed `aio verify` and
  `aio verify --structure` worked; normal imports and schemas came only from the
  temporary site-packages. External and zero-check projects passed, uninstall
  and temporary cleanup completed, and authoritative source digests were stable.
- Disposable Linux/amd64 Python 3.12.14 passed 122 focused tests: 114 passed and
  eight Windows-only cases skipped. A separate normal-install live probe loaded
  `/usr/local/lib/python3.12/site-packages/engineering_orchestration`, and passed
  installed/source/compatibility entrypoints, external adopter, zero checks,
  PASS/FAIL/ERROR, structural FAIL plus execution, planning prevention, recursion,
  and structural-only mode. This is Linux evidence, not a macOS claim.
- The migrated live path passed Markdown lint and `git diff --check`. Docker
  Desktop was started only for disposable Linux validation, no other containers
  were running, and it was stopped afterward.

## Security review

Outcome: PASS.

The same separate security-reviewer performed pre-implementation analysis and
final source/diff review without editing files or invoking aggregate verification.
No remediation-required security findings remain. Review covered public execution
disclosure and flush ordering, caller authority, inherited credentials/environment,
bounded unsanitized output, no sandbox or trust claims, structural-only isolation,
recursion rejection/restoration and removable-marker limits, planning gating,
Manifest diagnostic deduplication, exit semantics, interruption cleanup, one
declaration/runner source, compatibility convergence, rename neutrality, Agent
authority, and the unchanged four-field contract.

After independent review found that structural-mode interruption sat outside the
verify-specific handler, the implementer moved both full and structural-only paths
inside that boundary and added a regression test. The security-reviewer inspected
the remediation and reconfirmed PASS.

## Independent review

Outcome: APPROVE.

The separate reviewer inspected the actual diff, requirements, tests,
documentation, packaging, and recorded Windows/Linux evidence. It initially found
that `KeyboardInterrupt` during `--structure` could escape rather than map to 130.
The implementer remediated that issue without broadening interruption handling to
other commands. Focused remediation tests passed 9/9; the reviewer independently
reported 68/68 focused CLI/aggregate tests and 13/13 post-remediation
interruption/recursion tests passing, then issued APPROVE with no remaining
findings.

## Observations

- Migration safety: legacy coverage and order are preserved while the fixed
  battery has been retired; no dual execution ships.
- Contract sufficiency: the seven checks and adopter probes fit the four existing
  fields without environment, shell, dependency, retry, or interpreter additions.
- Python interpreter friction: PATH-selected Python is intentionally portable but
  requires an activated/supported development environment.
- Recursion: inherited ordinary nesting is blocked and environment state is
  restored, but wrappers may remove the marker and descendants are not contained.
- Adopter portability: external custom and zero-check projects work through
  installed, source, and compatibility entrypoints without an Orchestra fallback.
- User trust: the CLI exposes source, ordered IDs, caller authority, and lack of
  isolation before commands run; no persisted trust decision was introduced.
- Quality Gate boundary: verification results remain evidence only and do not
  update or satisfy Gate state.
- Authority pressure: the mechanism still does not authorize Agent invocation or
  grant command, filesystem, network, or credential authority.

Dogfooding proves the current four-field contract sufficient for ordered local
sequential verification. The most concrete next product limitation is that public
distribution and broader CLI lifecycle remain future work; portable local
verification now exists, but it is not a permission engine or Agent execution
contract.

## Quality Gates

- `documentation_consistency`: pass
- `independent_review`: pass

Security review is Workflow and review scope, not a new Quality Gate. Project
Verification Check results remain mechanical evidence and do not establish
Quality Gate PASS.

## Human control

Human approval date: 2026-09-17.

The Human approved AIO-020's reviewed implementation, documentation, validation,
security review outcome of PASS, independent review outcome of APPROVE, Quality
Gate evidence, and Task closure. This approval authorizes changing the Task to
`completed` and committing the approved AIO-020 change set with the specified
commit message. It does not authorize AIO-021 or any excluded scope.

Manifest-driven verification is now the active public behavior. Orchestra
dogfoods the same Project Verification Check planning and runner mechanism used
by adopting projects, with `.ai/project.yaml` as the one active source for its
seven checks. The legacy fixed battery is no longer an active source of truth,
and no hidden Orchestra fallback remains.

Agent auto-execution remains unauthorized: the existence of the verification
mechanism does not grant execution authority. Verification results remain
mechanical evidence only and neither map to nor satisfy Quality Gates. With these
boundaries preserved, the Human explicitly authorizes AIO-020 closure.
