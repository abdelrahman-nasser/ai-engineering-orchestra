# S0 feasibility evidence archive

Archived October 17, 2026 under the Human instruction
`ITRU — Evidence Archival & Developer Alpha First-Run Guide`.
S0 remains **closed at NO-GO**; reader admission and S1–S8 remain unauthorized.
This archive preserves experiments, including failures; it does not ship or
activate an experimental reader. Architecture v2, P01–P10, P07 and the approved
implementation plan are unchanged.

## Inventory and byte identity

[manifest.json](manifest.json) is the complete original-to-archive mapping:
31 artifacts, **1,294,345 bytes**, with exact original and archival paths,
SHA-256, byte count, classification and experiment phase.

| Phase | Artifacts | Location |
| --- | --- | --- |
| S0 | 8 | [s0/](s0/) and [original report](../s0-feasibility-report.md) |
| S0-R | 11 | [s0-r/](s0-r/) and [original report](../s0-r-feasibility-report.md) |
| S0-C | 12 | [s0-c/](s0-c/) and [original report](../s0-c-feasibility-report.md) |

The three reports remain at their original documentation paths. The other 28
artifacts retain their original path below the phase directory; the 14 Python
files have `.txt` appended (`.py.txt`). All 31 retain their original bytes,
encoding and line endings. Every copy was checked against the pre-move hash and
size before any original was removed. Scoped `-text` Git attributes prevent
line-ending normalization of evidence and reports. Index and committed-blob
identity must also match the manifest; hashes are integrity evidence, not
signatures, authorization or renewed experiment results.

## Historical paths and interpretation

Reports, receipts and archived source are historical evidence and remain
verbatim. Their old commands, links into `tests/`, imports from
`itru.control_center_read_budget` / `itru.control_center_read_source`, scratch
paths and untracked-status statements describe the experiment at that time.
The relocated paths no longer exist as executable/importable product or test
files. Use the manifest's `original_path` to find the corresponding
`archival_path`; do not repair historical text or restore code into `itru/` or
`tests/`. Source inspection is permitted; running these archived experiments
requires separate Human authorization and isolation.

Failed S0 receipts and both S0-C attempts are retained. S0-R's final measurement
receipt identifies five executed source hashes matching the archived S0-R
sources; the final S0-C receipt identifies six matching source hashes. The
earlier failed S0-C receipt records earlier hashes for four files (`capture.py`,
`coordination.py`, `run_experiments.py`, `test_concurrency.py`). Those superseded
source versions are not among the 31 supplied artifacts. The failed receipt is
preserved as supplied; reproducibility from the final sources is not claimed.

## Static packaging and discovery boundary

- [Package configuration](../../../../pyproject.toml) explicitly lists the five
  packages, sets `include-package-data = false`, and allowlists schema, Role and
  SQL resources. `docs/` is outside those packages.
- The supported [Alpha builder](../../../../scripts/build_developer_alpha.py)
  stages only `pyproject.toml`, `itru/*.py`, schema JSON, Role YAML, migration SQL
  and their existing package initializers. Its ZIP payload adds only the existing
  Alpha guide and two existing examples. It never traverses this archive.
  Removing the two experimental `itru/*.py` originals closes that staging risk.
- The [Manifest](../../../../.ai/project.yaml) runs unittest discovery from
  `tests/` with `test_*.py`. No archived file is under that tree. No pytest
  configuration is declared; `.py.txt` also avoids default recursive Python test
  filename collection. No `.py` or `__init__.py` exists in this archive.
- There is no declared `MANIFEST.in`, VCS file-finder plugin or docs package-data
  rule. `include-package-data = false` alone is not a universal sdist guarantee:
  arbitrary future build plugins, cached source inventories or packaging changes
  would require renewed inspection. The supported Alpha builder makes wheels
  and the selected offline ZIP, not sdists.

These are **static exclusion findings for the current configuration and supported
builder**, not build-verified payload claims. No build, installation, product
test, CLI operation, inference, authentication or network access was performed.
Packaging configuration was not changed. See [archival review](review.md).
