# Evidence archival verification and review

Date: October 17, 2026. Scope: documentation and inert experimental evidence only.
Current Human instruction and boundaries are recorded in
[Human decisions](../human-decisions.md#october-17-2026--evidence-archival-and-first-run-documentation-authorization).

## Baseline and identity

Core branch: `feature/control-center-s0-feasibility`.
Pre-archive HEAD: `1a8ed01232796d0da2387e349cbd09a79623ed13`.
Tracked worktree/index were clean; exactly 31 untracked experimental artifacts
were inventoried before relocation. The manifest records all original hashes
and sizes: 8 S0, 11 S0-R, 12 S0-C, totaling 1,294,345 bytes.

All 31 filesystem copies matched that inventory before the 28 relocated
originals were removed. The three reports retain their original paths and bytes.
No unrelated cleanup occurred. No superseded source was reconstructed.
The investigation, addendum, approved v2 and approved plan retain the canonical
hashes published in the [architecture index](../README.md).

UI was inspected read-only: branch `ui/developer-alpha-integration-qa-polish`,
HEAD `0485a5fe84746252b3f8f3bcd4f0d9e85e2a7a67`; parked
`ui/itru-062-contract-i18n-rtl` remains
`61e817c1f7a2c3987710a73366b516d792402520`. Its existing untracked
`ui/control-center/docs/ITRU-064-ui-runtime-integration-readiness.md` is outside
this change and remains untouched (15,867 bytes; SHA-256
`21478d4423c9e4761971507f95cafa0fb7ef9e848790d447b512bfdffb3c3be3`).

## Validation and independent review

Index identity verified: all 31 staged blobs match the original SHA-256 and byte
counts. The 37 staged paths are confined to `docs/architecture/control-center/`:
31 evidence artifacts, the archive guide/manifest/review, scoped Git attributes,
and the existing index/decision record. No package, production or test path is
staged. The new manifest uses LF line endings.

The default staged whitespace check returned exit 2: the unchanged historical
`s0-c/tests/fixtures/control_center/s0c/final-state.json` has 288 CRLF lines,
which Git reports as trailing whitespace when evidence is marked `-text`.
The initial check also flagged CRLF in the newly generated manifest; that new
metadata was corrected to LF. No historical artifact was rewritten. With
`-c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol`, the
staged check returned exit 0 and no diagnostics. This recognizes preserved CRLF
while retaining trailing-space, final-blank-line and space-before-tab checks;
the unconfigured command's failure is not reported as a PASS.

Scoped relative-link checks, absence of executable Python in the archive,
manifest completeness, absence of unintended untracked files and empty unstaged
tracked differences were also verified statically.

| Independent reviewer | Scope | Outcome and disposition |
| --- | --- | --- |
| `/root/integrity_review` | Original in-memory inventory against all 31 raw staged blobs; phase counts, historical baselines/receipts, protected-document hashes, staged scope, attributes and whitespace | **APPROVE**. Exact identity for all 31 artifacts; no omissions or unresolved findings. Independently reproduced the 288 CRLF-only default findings and configured check PASS. |
| `/root/packaging_review` | Actual staged diff, package/builder payload and test-discovery boundaries, authority/governance and static-only limitations | **APPROVE**. Independently verified all 31 staged blob hashes/sizes, all 28 relocated paths absent and all 37 staged paths scoped. No unresolved findings; static exclusions and sdist limitations accurately described. |

Both reviewers are separate Agent execution instances from the implementer and
performed read-only review. Documentation consistency and independent review
Quality Gates pass within this explicitly static scope. The final commit must
retain the verified staged evidence identity; committed blobs are rechecked
before proceeding to Phase B.

Packaging/discovery conclusions and their limitations are in the
[archive guide](README.md#static-packaging-and-discovery-boundary).
No build-verified exclusion is claimed. Product tests, schema validators,
aggregate verification, package builds, installation, product CLI/runtime,
inference/authentication and network-capable Markdown lint were not run, as
required by this task's explicit static-only scope. Historical test/measurement
results in archived reports were not rerun and are not fresh Quality Gate results.

Final Human acceptance remains required. No push, merge, tag, publication,
reader admission, UI change or additional feature work is authorized.
