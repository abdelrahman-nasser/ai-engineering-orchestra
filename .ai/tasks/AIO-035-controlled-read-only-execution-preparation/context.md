# AIO-035 Context

## Authorization and verified baseline

On 2026-09-20, the Human authorized creation of AIO-035, a separate Security
Reviewer design assessment before implementation, implementation, validation,
final Security review, independent review, final architecture/boundary review,
and preparation of the Human Control checkpoint. That implementation-phase
authorization did not include final Human approval, Task closure, staging, or
commit. On 2026-09-20, after the bounded independent re-review issued `APPROVE`
and both effective Gates passed without waiver, the Human separately gave final
acceptance, authorized Task closure, and authorized exactly one local closure
commit on `main`. Push, merge, tag, release, publication, AIO-030 work, AIO-036,
target-file access, permission changes, an execution request, and real Agent
invocation remain unauthorized.

Before Task creation, the repository was verified on branch `main` at HEAD
`b64c31973e6876738e9794edef3744dafe21278c`, subject
`feat: add Agent Execution Candidate prerequisite assessment (AIO-034)`. The
worktree and index were clean, AIO-034 was completed with 32/32 acceptance
criteria and recorded Human approval, and AIO-035 was absent. No fetch, pull,
remote query, branch switch, reset, stash, discard, stage, or commit was
performed.

AIO-030 remains parked on local branch
`feature/aio-030-vscode-control-center` at
`5a4dae8ffcca8f986c0eb42755db9a958c57d187`. It is not a dependency. Its branch,
files, ignored extension dependencies, generated outputs, and local exclusions
remain outside AIO-035.

## Need and dependency boundary

The post-AIO-034 investigation found that another reusable domain contract
would be premature. AIO-035 therefore depends on AIO-034 and accepts its full
immutable candidate result without recomputing prerequisites. The harness
preserves the seven-part candidate identity and composes it only with explicit,
caller-supplied facts for one future read-only action.

The harness may accept a coherent valid AIO-034 result whose ordinary outcome
is `satisfied`, `blocked`, or `unresolved` so that the upstream outcomes remain
observable in the mandated scenarios. Only `satisfied` can contribute to the
strongest preparation diagnostic; downstream evidence cannot repair a blocked
or unresolved candidate.

## Security design lock

On 2026-09-20, before feature implementation, a separate non-implementing
Security Reviewer approved the bounded design. The lock established:

- the single abstract operation literal `repository_file_read`;
- the sole controlled requirement resource `workflows/README.md`;
- case-sensitive, lexical-only repository-relative Markdown path validation;
- an opaque caller-supplied environment identifier;
- separate frozen capability, permission, and authorization evidence;
- capability scope of exact Runtime plus operation;
- permission scope of exact Runtime, environment, operation, and resource;
- authorization scope of all seven candidate identifiers plus environment,
  operation, and resource;
- explicit permission freshness states `current`, `stale`, and `unknown`;
- authorization provenance as Human-provided, policy-provided, or not supplied;
- atomic invalid-input results and ordinary exact-scope mismatch diagnostics;
- `potentially_executable`, `blocked`, and `unresolved` outcomes with fixed
  deterministic reason order and explicit cross-fact distinctions; and
- no I/O, target access, discovery, permission change, prose parsing, cache,
  token lifecycle, request construction, adapter, dispatch, or invocation.

The Reviewer concluded that no generic permission or authorization contract is
required. Needing discovery, reusable grants, policy resolution, persistence,
clocks, adapters, or invocation would be a scope conflict and must stop the
Task rather than expand it.

The lock intentionally gives authorization no timestamp or reusable freshness
contract. It is a caller-supplied, non-persisted assertion for one pure call and
must be supplied anew; permission freshness remains explicit. Neither source
provenance nor repository Human approval is treated as machine-verifiable
runtime authority.

## Default-deny and no-I/O boundary

Only a satisfied candidate, present exact capability, current exact allowed
permission, and exact granted authorization may produce
`potentially_executable`. That phrase means only that the supplied preparation
evidence is positive. It is not permission to execute, does not create an
Execution Contract or request, and performs no invocation.

The target path is data. The production module and controlled-action call path
may validate and compare its characters but may never open, read, stat, hash,
resolve, or check the existence or permissions of the target. It receives
permission evidence rather than querying the environment, and it never parses
Task or approval prose. The explicitly required repository-wide Markdown and
aggregate validation is external validation, not the controlled action; those
tools may scan the unchanged target as part of their authorized source checks.

## Review-process scope incident

During the final boundary review, the Reviewer accidentally ran a recursive
`rg` search without excluding `workflows/README.md`. The search scanned the
controlled target and returned one matching line. This exceeded the Human's
explicit target-access authorization and is recorded as a material governance
finding. It did not originate from the production harness or controlled-action
path, did not change the file or permissions, and supplied no capability,
permission, authorization, or outcome evidence. The returned content is not
reproduced here. The access is non-reversible. On 2026-09-20, the Human accepted
the disclosed incident for continuation without retroactively authorizing it,
approving it as behavior, waiving a Quality Gate, completing an acceptance
criterion, or granting final approval. The independent-review gate still
requires a successful bounded re-review.

## Governance and classification

`complexity: high` reflects exact identity and scope matching, freshness,
atomic validation, deterministic reason precedence, and exhaustive no-I/O
proof. `risk: high` reflects the safety impact of a false positive near a later
execution boundary even though this Task cannot execute. `execution.mode:
deep` is selected for the required security analysis, mismatch testing,
regression coverage, and evidence review; it grants no runtime capability.

The bound `security-sensitive-change` Workflow requires Security Reviewer
analysis before implementation, Software Engineer implementation, Security and
independent Reviewer review, the `documentation_consistency` and
`independent_review` Quality Gates, and a review-stage Human Control checkpoint.
The final boundary assessment confirmed that the harness is internal and
introduces no Core, schema, public, or cross-contract change, so the Workflow
does not require an Architect role. The implementation architecture passed that
assessment; its original overall governance verdict failed because the
review-process incident was then undispositioned. The Human disposition now
permits bounded independent re-review without retroactive authorization or
waiver. That re-review subsequently issued `APPROVE` with no material findings
and confirmed that it did not access the protected target.

## Human Control status

Security design approval, implementation, validation, and final technical
Security review are complete. Independent review approved the implementation
quality but issued `CHANGES REQUIRED`, and the final boundary review passed the
implementation architecture but failed overall governance, because the
unauthorized review-tool target read was then an undispositioned material
finding. The Human has since accepted that disclosed incident for continuation,
without retroactive authorization or waiver. The `documentation_consistency`
Quality Gate passed after the incident record was updated and independently
rechecked. The bounded independent re-review approved the reconciled evidence,
so the `independent_review` Quality Gate also passes without waiver. Acceptance
was then **32/33**. On 2026-09-20, the Human explicitly granted final acceptance,
accepted the preserved incident history without retroactive authorization,
completed criterion 33, authorized Task closure, and authorized exactly one
local closure commit on `main`. All **33/33** criteria are complete and the Task
is closed as `completed`. No push, merge, tag, release, or publication is
authorized.
