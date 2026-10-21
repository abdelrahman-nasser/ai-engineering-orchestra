"""Task-local evidence support; no discovery, source restoration or Git writes."""
from __future__ import annotations

import ast
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
EVIDENCE = TASK / "evidence"
BASE = "4775d649e13639504a8007e57890f80c699bb1be"
BRANCH = "feature/core-verification-debt-phase1"
PYTHON = Path(r"C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe")
TEST = "tests/test_packaging.py"
PREFIX = "tests.test_packaging.PackagingTests."
METHODS = (
    "test_explicit_resource_allowlist",
    "test_metadata_and_only_temporary_console",
    "test_packaged_schema_content_matches_canonical_source",
    "test_schema_lookup_does_not_consult_cwd",
)

CHILD = r'''
import importlib.util, json, os, sqlite3, sys, types, unittest
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
root = Path(sys.argv[1]).resolve()
mode = sys.argv[2]
assert sys.flags.isolated == 1 and sys.flags.dont_write_bytecode == 1
assert sys.version_info[:2] == (3, 12)
denied = []
forbidden_modules = (
    "itru.windows_", "itru._native_", "itru.alpha_", "itru.developer_alpha",
    "itru.sqlite_agent_execution_journal_store", "experiments",
)
def audit(event, args):
    prohibited = (
        event.startswith(("socket.", "subprocess.", "ctypes.", "winreg."))
        or event in {"sqlite3.connect", "os.system", "os.fork", "os.posix_spawn",
            "os.spawn", "os.exec", "os.startfile", "os.remove", "os.rmdir",
            "os.mkdir", "os.rename", "os.link", "os.symlink", "os.truncate",
            "os.chmod", "os.chown", "os.utime", "tempfile.mkstemp", "tempfile.mkdtemp"}
    )
    if event == "open":
        access, flags = args[1:3]
        prohibited |= (
            isinstance(access, str) and any(c in access for c in "wax+")
        ) or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
    if event == "import":
        name = args[0]
        prohibited |= name.startswith(forbidden_modules) or (
            name.startswith("tests.") and name != "tests.test_packaging"
        )
    if prohibited:
        denied.append(event)
        raise AssertionError("Phase 2 prohibited operation: " + event)
sys.addaudithook(audit)
sys.path.insert(0, str(root))
import itru
assert Path(itru.__file__).resolve() == root / "itru/__init__.py"
assert "tests" not in sys.modules
namespace = types.ModuleType("tests")
namespace.__path__ = [str(root / "tests")]
sys.modules["tests"] = namespace
spec = importlib.util.spec_from_file_location("tests.test_packaging", root / "tests/test_packaging.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
assert Path(module.__file__).resolve() == root / "tests/test_packaging.py"
methods = (
    "test_explicit_resource_allowlist", "test_metadata_and_only_temporary_console",
    "test_packaged_schema_content_matches_canonical_source", "test_schema_lookup_does_not_consult_cwd",
)
names = methods[:1] if mode == "before" else methods
suite = unittest.TestSuite(module.PackagingTests(name) for name in names)
assert [test.id() for test in suite] == ["tests.test_packaging.PackagingTests." + name for name in names]
locations = {}
for name, value in list(sys.modules.items()):
    if name == "itru" or name.startswith("itru."):
        location = getattr(value, "__file__", None)
        if location is not None:
            resolved = Path(location).resolve()
            assert resolved.is_relative_to(root / "itru"), (name, location)
            locations[name] = str(resolved)
print("IMPORT_ROOT", module.__file__, "isolated", sys.flags.isolated,
      "bytecode_disabled", sys.flags.dont_write_bytecode, flush=True)
result = unittest.TextTestRunner(verbosity=2).run(suite)
summary = dict(tests=result.testsRun, failures=[t.id() for t, _ in result.failures],
    errors=[t.id() for t, _ in result.errors], skips=[t.id() for t, _ in result.skipped],
    expected_failures=[t.id() for t, _ in result.expectedFailures],
    unexpected_successes=[t.id() for t in result.unexpectedSuccesses],
    prohibited_attempts=denied, import_locations=locations)
print("PHASE2_RESULT " + json.dumps(summary, sort_keys=True), flush=True)
sys.exit(2 if denied else int(not result.wasSuccessful()))
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value, *, exclusive=False):
    with path.open("x" if exclusive else "w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, indent=2) + "\n")


def command(argv):
    process = subprocess.run(argv, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.returncode == 0, (argv, process.returncode, process.stderr.decode("utf-8", "replace"))
    return process.stdout.decode("utf-8").strip()


def git(*args):
    return command(["git", *args])


def identity():
    assert git("rev-parse", "HEAD") == BASE
    assert git("branch", "--show-current") == BRANCH
    assert not git("diff", "--cached", "--name-only")
    assert Path(sys.executable).resolve() == PYTHON.resolve()
    assert sys.version_info[:2] == (3, 12)
    assert sys.flags.isolated == sys.flags.dont_write_bytecode == 1


def expected_after(original):
    start = original.index(b"    def test_explicit_resource_allowlist(self):")
    end = original.index(b"    def test_documented_scope_is_local_and_verify_is_portable", start)
    method = original[start:end]
    newline = b"\r\n" if b"\r\n" in method else b"\n"
    replacements = (
        (b'"itru._sqlite_admission_migrations"])',
         b'"itru._sqlite_admission_migrations",' + newline + b'                          "itru._sqlite_journal_migrations"])'),
        (b'"itru._schemas": list(PACKAGED_SCHEMAS),',
         b'"itru._schemas": ["task-run-state-event.schema.json", *PACKAGED_SCHEMAS],'),
        (b'"itru._sqlite_admission_migrations": ["*.sql"],',
         b'"itru._sqlite_admission_migrations": ["*.sql"],' + newline + b'            "itru._sqlite_journal_migrations": ["*.sql"],'),
    )
    for old, new in replacements:
        assert method.count(old) == 1
        method = method.replace(old, new, 1)
    return original[:start] + method + original[end:]


def baseline():
    return json.loads((EVIDENCE / "baseline.json").read_text(encoding="utf-8"))


def preserved(data):
    for name, digest in data["protected_tracked_sha256"].items():
        assert sha(ROOT / name) == digest, "Tracked input changed: " + name
    for name, digest in data["historical_sha256"].items():
        assert sha(ROOT / name) == digest, "Historical receipt changed: " + name


def freeze():
    identity()
    assert not git("diff", "--name-only")
    tracked = git("ls-files").splitlines()
    inventory_path = ".ai/tasks/ITRU-065-scrum-86-verification-debt-phase1/failure-inventory.json"
    inventory = json.loads((ROOT / inventory_path).read_text(encoding="utf-8"))
    historical = {name: sha(ROOT / name) for name in inventory["sources"]}
    for name, item in inventory["sources"].items():
        assert historical[name] == item["sha256"]
    for name in (".tmp/usability-p0-alpha-tests.log", ".tmp/p0-final-verification/current-assertions.log",
                 ".tmp/p0-final-verification/baseline-assertions.log", ".tmp/p0-final-verification/journal-byte-evidence.json"):
        historical[name] = sha(ROOT / name)
    original = (ROOT / TEST).read_bytes()
    ast.parse(original.decode("utf-8"))
    save(EVIDENCE / "baseline.json", dict(
        time_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        command=[sys.executable, "-I", "-B", str(Path(__file__).resolve()), "freeze"],
        cwd=str(ROOT), branch=BRANCH, head=BASE,
        entry_clean_observed=True, freeze_status=git("status", "--short"),
        interpreter=dict(path=sys.executable, version=sys.version, platform=platform.platform(),
            isolated=sys.flags.isolated, bytecode_disabled=sys.flags.dont_write_bytecode,
            packages={name: importlib.metadata.version(name) for name in ("PyYAML", "jsonschema", "referencing")}),
        original_test_sha256=sha(ROOT / TEST), original_test_source=original.decode("utf-8"),
        approved_after_sha256=hashlib.sha256(expected_after(original)).hexdigest(),
        protected_tracked_sha256={name: sha(ROOT / name) for name in tracked if name != TEST},
        historical_sha256=historical, historical_summary=inventory["historical_summary"],
    ), exclusive=True)
    print("PASS: baseline frozen; no tests executed; tracked inputs and historical raw receipts hashed.")


def run_tests(mode):
    identity()
    data = baseline()
    preserved(data)
    expected = data["original_test_sha256" if mode == "before" else "approved_after_sha256"]
    assert sha(ROOT / TEST) == expected, "Test source differs; no automatic source restoration"
    assert not (EVIDENCE / (mode + ".txt")).exists(), "Preserve existing test receipt"
    argv = [str(PYTHON), "-I", "-B", "-c", CHILD, str(ROOT), mode]
    started = time.monotonic()
    execution_error = None
    try:
        process = subprocess.run(argv, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
        raw, exit_code = process.stdout, process.returncode
    except subprocess.TimeoutExpired as error:
        raw, exit_code = error.stdout or b"", None
        execution_error = dict(kind="TimeoutExpired", timeout_seconds=60)
    except OSError as error:
        raw, exit_code = str(error).encode("utf-8"), None
        execution_error = dict(kind=type(error).__name__, detail=str(error))
    (EVIDENCE / (mode + ".txt")).write_bytes(raw)
    lines = raw.decode("utf-8", "replace").splitlines()
    summaries = [json.loads(line.removeprefix("PHASE2_RESULT ")) for line in lines if line.startswith("PHASE2_RESULT ")]
    record = dict(phase=mode, argv=argv, cwd=str(ROOT), exit_code=exit_code, execution_error=execution_error,
        seconds=round(time.monotonic() - started, 3), test_names=[PREFIX + m for m in (METHODS[:1] if mode == "before" else METHODS)],
        output=mode + ".txt", output_sha256=sha(EVIDENCE / (mode + ".txt")),
        test_source_sha256=sha(ROOT / TEST), runner_sha256=sha(Path(__file__)),
        summary=summaries[0] if len(summaries) == 1 else None)
    with (EVIDENCE / "commands.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(record) + "\n")
    print(raw.decode("utf-8", "replace"), flush=True)
    assert execution_error is None, "Launch/timeout failure retained; no automatic retry"
    summary = record["summary"]
    assert summary is not None, "Missing result summary; raw child outcome retained"
    for key in ("errors", "skips", "expected_failures", "unexpected_successes", "prohibited_attempts"):
        assert summary[key] == [], (key, summary[key])
    assert summary["tests"] == (1 if mode == "before" else 4)
    assert summary["failures"] == ([PREFIX + METHODS[0]] if mode == "before" else [])
    assert exit_code == (1 if mode == "before" else 0)
    if mode == "before":
        assert "AssertionError: Lists differ:" in "\n".join(lines)
        assert "itru._sqlite_journal_migrations" in "\n".join(lines)
    preserved(data)
    return exit_code


def checks():
    import yaml
    from jsonschema import Draft202012Validator
    identity()
    data = baseline()
    preserved(data)
    assert (ROOT / TEST).read_bytes() == expected_after(data["original_test_source"].encode("utf-8"))
    config = yaml.safe_load((TASK / "task.yaml").read_text(encoding="utf-8"))
    schema_names = {"task": config, "workflow": yaml.safe_load((ROOT / "workflows/standard-change.yaml").read_text(encoding="utf-8"))}
    for kind, value in schema_names.items():
        schema = json.loads((ROOT / ("schemas/" + kind + ".schema.json")).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(value)
    assert config["id"] == "ITRU-067" and config["status"] == "in_progress"
    assert TASK.name.startswith(config["id"] + "-")
    assert (config["type"], config["complexity"], config["risk"], config["execution"]["mode"]) == ("bugfix", "medium", "low", "standard")
    assert config["workflow"] == schema_names["workflow"]["id"] == "standard-change"
    assert config["type"] in schema_names["workflow"]["applicable_task_types"]
    assert config["dependencies"] == ["ITRU-065"]
    dependency = yaml.safe_load((ROOT / ".ai/tasks/ITRU-065-scrum-86-verification-debt-phase1/task.yaml").read_text(encoding="utf-8"))
    assert dependency["id"] == "ITRU-065" and dependency["status"] == "completed"
    assert config["quality_gates"] == ["documentation_consistency", "independent_review"]
    assert all(config["human_control"].values())
    used_roles = {"software-engineer", "reviewer", "security-reviewer"}
    for stage in schema_names["workflow"]["stages"]:
        assert set(stage.get("required_roles", [])) <= used_roles
    role_schema = json.loads((ROOT / "schemas/role.schema.json").read_text(encoding="utf-8"))
    for role in used_roles:
        value = yaml.safe_load((ROOT / ("roles/" + role + ".yaml")).read_text(encoding="utf-8"))
        Draft202012Validator(role_schema).validate(value)
        assert value["id"] == role
    for gate in config["quality_gates"]:
        assert (ROOT / ("quality-gates/" + gate.replace("_", "-") + ".md")).is_file()
    assert git("diff", "--name-only").splitlines() == [TEST]
    prefix = TASK.relative_to(ROOT).as_posix() + "/"
    assert all(name.startswith(prefix) for name in git("ls-files", "--others", "--exclude-standard").splitlines())
    receipts = [json.loads(line) for line in (EVIDENCE / "commands.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [r["phase"] for r in receipts] == ["before", "after"]
    assert [r["exit_code"] for r in receipts] == [1, 0]
    for receipt in receipts:
        assert sha(EVIDENCE / receipt["output"]) == receipt["output_sha256"]
        assert receipt["runner_sha256"] == sha(Path(__file__))
    references = 0
    for path in TASK.glob("*.md"):
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
                continue
            target = target.split("#", 1)[0]
            if target:
                assert (path.parent / target).resolve().is_file(), (path.name, target)
                references += 1
    files = sorted(path for path in TASK.rglob("*") if path.is_file() and path.name != "governance-checks.json")
    for path in [*files, ROOT / TEST]:
        if path.suffix == ".txt":
            continue  # Raw failed/passing child output is never rewritten.
        value = path.read_text(encoding="utf-8")
        assert value.endswith("\n") and all(line == line.rstrip(" \t") for line in value.splitlines()), path.name
    assert not git("diff", "--check")
    record = dict(result="PASS", command=[sys.executable, "-I", "-B", str(Path(__file__).resolve()), "checks"],
        cwd=str(ROOT), time_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        checks=["Task/Workflow/used Role schemas", "Task/dependency/Role/Gate identities and references",
            "exact three-correction byte diff", "protected tracked and historical receipt hashes",
            "source-bound one-failure/four-PASS receipts", "HEAD/branch/empty index and exact path scope",
            "local Markdown references", "nonreceipt whitespace", "git diff --check"],
        markdown_references=references, markdown_lint="NONMANDATORY / NOT RUN; independent documentation comparison required",
        inputs_sha256={path.relative_to(ROOT).as_posix(): sha(path) for path in [*files, ROOT / TEST]},
        candidate_paths=sorted([path.relative_to(ROOT).as_posix() for path in [*files, ROOT / TEST]] + [prefix + "evidence/governance-checks.json"]))
    output = EVIDENCE / "governance-checks.json"
    previous = json.loads(output.read_text(encoding="utf-8"))["runs"] if output.exists() else []
    save(output, {"runs": [*previous, record]})
    print("PASS: scoped schemas/references, exact diff, protected hashes, receipts and whitespace. No tests executed.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    EVIDENCE.mkdir(exist_ok=True)
    mode = sys.argv[1]
    if mode == "freeze":
        freeze()
    elif mode in ("before", "after"):
        raise SystemExit(run_tests(mode))
    elif mode == "checks":
        checks()
    else:
        raise SystemExit("Expected freeze, before, after or checks")
