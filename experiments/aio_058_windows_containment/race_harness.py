"""The locked AIO-058 cooperative native race experiment, never production code.

Only the caller's already-owned workspace is used. No process lookup, external
command, runtime discovery, policy change or ordinary reader fallback exists.
Each actor is an explicitly owned non-daemon thread. Event barriers hold the
reader at its selected cut until the actor attempted its native mutation. The
five-second threshold is an observation gate, not safe cancellation proof.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import threading
import time
from typing import Any

CUTS = (
    "before_component_open", "after_ancestor_pin",
    "after_final_open_before_metadata", "before_first_content_read",
)
RACE_VARIANTS = (
    ("I07", "root_rename_then_outside_junction"),
    ("I08", "intermediate_rename_then_outside_junction"),
    ("I09", "final_rename_then_outside_symlink"),
    ("I15", "growth"), ("I15", "truncation"), ("I15", "same_size_write"),
    ("I15", "native_hard_link_create_remove"),
    ("I15", "native_posix_link_replacement"),
    ("I15", "native_posix_rename_replacement"),
)
REPETITIONS = 100
RACE_ATTEMPTS = len(RACE_VARIANTS) * len(CUTS) * REPETITIONS
STATIC_DISTRIBUTION = (
    ("I01", 1), ("I02", 4), ("I03", 2), ("I04", 3), ("I05", 12),
    ("I06", 8), ("I10", 2), ("I11", 3), ("I12", 2), ("I13", 2),
    ("I14", 3), ("I16", 6), ("I17", 5), ("I18", 3),
)
OBSERVATION_SECONDS = 5.0
FILE_WRITE_DATA = 0x0002
FILE_READ_ATTRIBUTES = 0x0080
DELETE = 0x00010000
FILE_SHARE_READ = 0x0001
FILE_SHARE_ALL = 0x0007
INITIAL_BYTES = b"AIO058 contained race fixture\n"
REPLACEMENT_BYTES = b"B" * len(INITIAL_BYTES)
RESOURCE = "fixtures/selected/file.bin"


class RaceInfrastructureFailure(RuntimeError):
    """A required cut, fixture, native API or bookkeeping was unavailable."""


@dataclass
class RaceAccounting:
    total: int = 0
    safe: int = 0
    violation: int = 0
    infrastructure_failure: int = 0
    owned_threads_created: int = 0
    owned_threads_reaped: int = 0
    unauthorized_bytes_returned: int = 0
    unauthorized_data_requests: int = 0
    handles_restored: bool = True
    buckets: dict[tuple[str, str, str], dict[str, int]] = field(default_factory=dict)

    def add(self, case: str, variant: str, cut: str, classification: str) -> None:
        self.total += 1
        name = {"SAFE": "safe", "VIOLATION": "violation",
                "INFRASTRUCTURE_FAILURE": "infrastructure_failure"}[classification]
        setattr(self, name, getattr(self, name) + 1)
        bucket = self.buckets.setdefault(
            (case, variant, cut),
            {"total": 0, "safe": 0, "violation": 0, "infrastructure_failure": 0})
        bucket["total"] += 1
        bucket[name] += 1


@dataclass
class AttackEvidence:
    attempted: bool = False
    succeeded: bool = False
    operations: list[dict[str, Any]] = field(default_factory=list)
    infrastructure_reason: str | None = None
    elapsed: float = 0.0


def _error_category(exc: BaseException) -> str:
    """Only actual access/share denials count as the specified blocked attack."""
    winerror = getattr(exc, "winerror", None)
    status = getattr(exc, "status", getattr(exc, "ntstatus", None))
    if isinstance(status, int):
        status &= 0xFFFFFFFF
    if winerror == 5 or status == 0xC0000022:
        return "access_denied"
    if winerror == 32 or status == 0xC0000043:
        return "sharing_violation"
    if isinstance(status, int):
        return f"unsupported_or_error_ntstatus_{status:08x}"
    if isinstance(winerror, int):
        return f"unsupported_or_error_winerror_{winerror}"
    return f"infrastructure_{type(exc).__name__}"


def _one_operation(evidence: AttackEvidence, name: str, action: Any) -> bool:
    # Mark before crossing the native boundary: denial of the mutation's needed
    # native open is an attempted mutation rather than an unattempted cut.
    evidence.attempted = True
    started = time.perf_counter()
    try:
        action()
    except Exception as exc:
        category = _error_category(exc)
        evidence.operations.append({"operation": name, "status": category})
        if category not in ("access_denied", "sharing_violation"):
            evidence.infrastructure_reason = category
        return False
    finally:
        if time.perf_counter() - started > OBSERVATION_SECONDS:
            evidence.infrastructure_reason = "mutation_native_observation_overrun"
    evidence.succeeded = True
    evidence.operations.append({"operation": name, "status": "mutation_completed"})
    return True


def _notify(reporter: Any, method: str) -> None:
    callback = getattr(reporter, method, None)
    if callback is not None:
        callback()


def _close(handle: Any) -> None:
    if handle is not None:
        handle.close()


def _handle_count(native: Any) -> int:
    value = native.handle_count
    return int(value() if callable(value) else value)


def _bytes_allowed(variant: str) -> tuple[bytes, ...]:
    if variant == "truncation":
        return INITIAL_BYTES, INITIAL_BYTES[:3]
    if variant == "same_size_write":
        return INITIAL_BYTES, REPLACEMENT_BYTES
    # Growth exceeds the limit and rejects. Link/rename substitution selects a
    # different identity and must reject before data acquisition.
    return (INITIAL_BYTES,)


def _expected_reader_rejection(result: Any, variant: str) -> bool:
    """Only a closed, relevant containment outcome can count as SAFE."""
    reason = result.reason
    if reason in {"containment_rejected", "outside_identity", "unexpected_identity",
                  "hard_link_rejected", "resource_changed"}:
        return True
    if reason == "size_limit_exceeded":
        return variant == "growth"
    if reason.startswith("native_status_"):
        try:
            status = int(reason.split("_")[2], 16)
        except (IndexError, ValueError):
            return False
        # Actual share/access denials or encountered substitutions. Invalid API
        # flags/ABI, query failures, pending completion and arbitrary statuses
        # stay infrastructure failures, even though the reader failed closed.
        return status in {0xC0000022, 0xC0000043, 0xC0000034, 0xC000003A,
                          0xC000000F, 0xC000050B, 0x8000002D, 0xC0000279}
    return False


def _attack(native: Any, workspace: Any, variant: str, fixture: dict[str, Any],
            evidence: AttackEvidence) -> None:
    """One selected attack; no alternate flags or fallback mechanisms."""
    root, final, intermediate = (
        fixture["root"], fixture["final"], fixture["intermediate"])

    def rename_then_replace(source: Any, moved: Any, directory: bool) -> None:
        handle = None
        try:
            handle = native.control_open(source, access=DELETE,
                                         share=FILE_SHARE_ALL, directory=directory)
            native.native_rename(handle, moved, posix=False, replace=False)
            # Remap only known records; never enumerate a renamed tree.
            workspace.relocate_known(source, moved)
        finally:
            _close(handle)
        if directory:
            workspace.junction(source, workspace.outside)
        else:
            workspace.symlink(source, fixture["sentinel"], directory=False)

    if variant == "root_rename_then_outside_junction":
        _one_operation(evidence, "root_rename_then_junction",
                       lambda: rename_then_replace(root, fixture["root_moved"], True))
    elif variant == "intermediate_rename_then_outside_junction":
        _one_operation(evidence, "intermediate_rename_then_junction",
                       lambda: rename_then_replace(
                           intermediate, fixture["dir_moved"], True))
    elif variant == "final_rename_then_outside_symlink":
        _one_operation(evidence, "final_rename_then_symlink",
                       lambda: rename_then_replace(final, fixture["file_moved"], False))
    elif variant in ("growth", "truncation", "same_size_write"):
        def write_change() -> None:
            handle = None
            try:
                handle = native.control_open(final, access=FILE_WRITE_DATA,
                                             share=FILE_SHARE_ALL)
                if variant == "growth":
                    native.set_end_of_file(handle, 65537)
                    native.write_at(handle, b"A", 65536)
                elif variant == "truncation":
                    native.set_end_of_file(handle, 3)
                else:
                    native.write_at(handle, REPLACEMENT_BYTES, 0)
            finally:
                _close(handle)
        _one_operation(evidence, variant, write_change)
    elif variant == "native_hard_link_create_remove":
        alias = fixture["alias"]
        def add_link() -> None:
            native.native_link(fixture["source_handle"], alias,
                               posix=False, replace=False)
            workspace.note(alias, directory=False)
        if _one_operation(evidence, "native_hard_link_add", add_link):
            def remove_link() -> None:
                handle = None
                try:
                    handle = native.control_open(alias, access=DELETE,
                                                 share=FILE_SHARE_ALL)
                    native.native_unlink(handle, posix=False)
                    workspace.forget(alias)
                finally:
                    _close(handle)
            # Denied removal leaves the known alias for exact final cleanup
            # after the reader and zero-access source handles close.
            _one_operation(evidence, "native_hard_link_remove", remove_link)
    elif variant == "native_posix_link_replacement":
        _one_operation(evidence, "native_posix_link_replace",
                       lambda: native.native_link(
                           fixture["outside_handle"], final, posix=True, replace=True))
    elif variant == "native_posix_rename_replacement":
        def replace_rename() -> None:
            native.native_rename(fixture["replacement_handle"], final,
                                 posix=True, replace=True)
            workspace.forget(fixture["replacement"])
        _one_operation(evidence, "native_posix_rename_replace", replace_rename)
    else:
        raise RaceInfrastructureFailure("unknown_locked_race_variant")


def _fixture(native: Any, workspace: Any, attempt_number: int, variant: str,
             outside_handle: Any, sentinel: Any) -> dict[str, Any]:
    """Fresh explicitly named objects; no fixture catalog scanning."""
    root = workspace.mkdir(f"repo/race-{attempt_number:04d}")
    directory = workspace.mkdir(root / "fixtures")
    intermediate = workspace.mkdir(directory / "selected")
    final = workspace.file(intermediate / "file.bin", INITIAL_BYTES)
    fixture = {
        "root": root, "intermediate": intermediate, "final": final,
        "expected_identity": native.identity(final),
        "sentinel": sentinel, "outside_handle": outside_handle,
        "root_moved": root.with_name(root.name + "-moved"),
        "dir_moved": directory / "selected-moved",
        "file_moved": intermediate / "file-moved.bin",
        "alias": intermediate / "native-alias.bin",
        "source_handle": None, "replacement_handle": None, "replacement": None,
    }
    if variant == "native_hard_link_create_remove":
        # The retained source predates the reader and requests zero access.
        # Link APIs do not establish protection from topology history changes.
        fixture["source_handle"] = native.control_open(
            final, access=0, share=FILE_SHARE_ALL)
    elif variant == "native_posix_rename_replacement":
        replacement = workspace.file(
            intermediate / "replacement.bin", REPLACEMENT_BYTES)
        fixture["replacement"] = replacement
        fixture["replacement_handle"] = native.control_open(
            replacement, access=DELETE, share=FILE_SHARE_ALL)
    return fixture


def _run_one(native: Any, workspace: Any, reporter: Any, accounting: RaceAccounting,
             attempt_number: int, case: str, variant: str, cut: str,
             repetition: int, outside_identity: Any, outside_handle: Any,
             sentinel: Any) -> None:
    baseline = _handle_count(native)
    started = time.perf_counter()
    fixture = actor = cap = result = None
    trigger, done, cancel = threading.Event(), threading.Event(), threading.Event()
    cut_reached = cut_overrun = actor_started = False
    actor_error = infra_reason = None
    actor_fatal = None
    unauthorized_bytes = unauthorized_requests = 0
    evidence = AttackEvidence()
    classification = "INFRASTRUCTURE_FAILURE"
    try:
        fixture = _fixture(native, workspace, attempt_number, variant,
                           outside_handle, sentinel)
        # Trusted-root provisioning precedes every reader hook, so root attacks
        # challenge the acquired actual pin, never a caller pathname assumption.
        cap = native.pin_root(fixture["root"])
        cap.forbidden_ids.add(outside_identity)

        def worker() -> None:
            nonlocal actor_error, actor_fatal
            trigger.wait()
            if cancel.is_set():
                return
            attack_started = time.perf_counter()
            try:
                _attack(native, workspace, variant, fixture, evidence)
            except BaseException as exc:
                if isinstance(exc, Exception):
                    actor_error = _error_category(exc)
                    evidence.infrastructure_reason = actor_error
                else:
                    # Unsupported unverified completion and Human interrupts
                    # stop the matrix after this owned actor is joined.
                    actor_fatal = exc
            finally:
                evidence.elapsed = time.perf_counter() - attack_started
                if evidence.elapsed > OBSERVATION_SECONDS:
                    evidence.infrastructure_reason = "attack_observation_overrun"
                done.set()

        actor = threading.Thread(
            target=worker, name=f"aio058-owned-race-{attempt_number:04d}", daemon=False)
        actor.start()
        actor_started = True
        accounting.owned_threads_created += 1
        _notify(reporter, "owned_thread_created")

        # I07 selects the first child of the root; I08 selects the intermediate;
        # I09/I15 select the final component. Each final-hook cut occurs once.
        relevant_index = 0 if case == "I07" else 1 if case == "I08" else 2

        def hook(reached_cut: str, context: dict[str, Any]) -> None:
            nonlocal cut_reached, cut_overrun
            if reached_cut != cut or cut_reached:
                return
            if cut in ("before_component_open", "after_ancestor_pin"):
                if context["component_index"] != relevant_index:
                    return
            cut_reached = True
            trigger.set()
            if not done.wait(OBSERVATION_SECONDS):
                cut_overrun = True
                # Do not abandon a live native actor or release its pins. This
                # intentionally does not claim hard in-process cancellation:
                # Human external supervision may stop a hung unsupported run.
                done.wait()
            if actor_fatal is not None:
                raise actor_fatal
            if actor_error is not None:
                raise RaceInfrastructureFailure(actor_error)
            if evidence.infrastructure_reason is not None:
                raise RaceInfrastructureFailure(evidence.infrastructure_reason)

        result = native.read(cap, RESOURCE,
                             expected_identity=fixture["expected_identity"], hook=hook)
        if not cut_reached:
            infra_reason = "required_cut_unreachable"
        elif not evidence.attempted:
            infra_reason = "mutation_not_attempted"
        elif evidence.infrastructure_reason or cut_overrun:
            infra_reason = evidence.infrastructure_reason or "cut_observation_overrun"
        elif (result.data_requests > 17 or result.physical_bytes > 65537
              or result.native_calls > 253 or result.retained_peak > 48
              or result.opens > 16 or max(result.metadata_per_handle, default=0) > 12
              or sum(row["requested"] for row in result.trace if row.get("event") == "data_request") > 65537):
            classification = "VIOLATION"
        elif result.elapsed > OBSERVATION_SECONDS or result.native_maxcall_seconds > OBSERVATION_SECONDS:
            infra_reason = "reader_observation_overrun"
        elif not result.leak_free:
            infra_reason = "reader_handle_leak"
        elif result.accepted:
            if (result.identity != fixture["expected_identity"]
                    or result.identity == outside_identity
                    or result.data not in _bytes_allowed(variant)
                    or len(result.data) > 65536):
                classification = "VIOLATION"
                unauthorized_bytes = len(result.data)
                accounting.unauthorized_bytes_returned += unauthorized_bytes
            else:
                classification = "SAFE"
        elif result.data not in (None, b""):
            classification = "VIOLATION"
            unauthorized_bytes = len(result.data)
            accounting.unauthorized_bytes_returned += unauthorized_bytes
        elif _expected_reader_rejection(result, variant):
            classification = "SAFE"
        else:
            infra_reason = result.reason
        # Outside content requests violate the oracle even when output was
        # subsequently discarded. Trace contains only bounded fixed metadata.
        unauthorized_requests = sum(
            1 for item in result.trace
            if item.get("event") == "data_request"
            and item.get("identity") == outside_identity)
        if unauthorized_requests:
            accounting.unauthorized_data_requests += unauthorized_requests
            classification = "VIOLATION"
        if result.unauthorized_reads:
            accounting.unauthorized_data_requests += result.unauthorized_reads
            classification = "VIOLATION"
    except Exception as exc:
        infra_reason = _error_category(exc)
    finally:
        # Join only our actor. An unreachable cut wakes it solely in cancelled
        # mode, giving no credit for an unattempted mutation.
        if actor_started:
            if not trigger.is_set():
                cancel.set()
                trigger.set()
            actor.join()
            if not actor.is_alive():
                accounting.owned_threads_reaped += 1
                _notify(reporter, "owned_thread_reaped")
            else:
                infra_reason = "owned_actor_not_reaped"
        handles = ([fixture["source_handle"], fixture["replacement_handle"]]
                   if fixture is not None else [])
        handles.append(cap)
        for handle in handles:
            try:
                _close(handle)
            except BaseException as exc:
                infra_reason = "owned_handle_cleanup_" + _error_category(exc)
        restored = _handle_count(native) == baseline
        if not restored:
            accounting.handles_restored = False
            infra_reason = "attempt_handle_count_not_restored"
        elapsed = time.perf_counter() - started
        if elapsed > OBSERVATION_SECONDS:
            infra_reason = "attempt_observation_overrun"
        if infra_reason is not None and classification != "VIOLATION":
            classification = "INFRASTRUCTURE_FAILURE"
        accounting.add(case, variant, cut, classification)
        reporter.race({
            "case": case, "variant": variant, "cut": cut,
            "repetition": repetition, "classification": classification,
            "cut_reached": cut_reached,
            "mutation_attempted": evidence.attempted,
            "mutation_succeeded": evidence.succeeded,
            "unauthorized_bytes_returned": unauthorized_bytes,
            "unauthorized_data_requests": unauthorized_requests,
            "mutation_operations": evidence.operations,
            "infrastructure_reason": infra_reason,
            "reader_reason": getattr(result, "reason", "reader_not_started"),
            "byte_count": len(result.data) if result is not None and result.data else 0,
            "data_requests": getattr(result, "data_requests", 0),
            "physical_bytes": getattr(result, "physical_bytes", 0),
            "requested_bytes": sum(row["requested"] for row in getattr(result, "trace", ())
                                   if row.get("event") == "data_request"),
            "native_calls": getattr(result, "native_calls", 0),
            "retained_peak": getattr(result, "retained_peak", 0),
            "opens": getattr(result, "opens", 0),
            "metadata_per_handle_max": max(getattr(result, "metadata_per_handle", ()), default=0),
            "native_maxcall_seconds": round(getattr(result, "native_maxcall_seconds", 0.0), 6),
            "unauthorized_bytes_returned": bool(result is not None and result.accepted
                                                and (result.identity != fixture["expected_identity"]
                                                     or result.identity == outside_identity)),
            "unauthorized_data_requests": (sum(1 for row in getattr(result, "trace", ())
                                                if row.get("event") == "data_request"
                                                and row.get("identity") == outside_identity)
                                           + getattr(result, "unauthorized_reads", 0)),
            "elapsed": round(elapsed, 6), "handles_restored": restored,
        })


def run_races(native: Any, workspace: Any, reporter: Any) -> RaceAccounting:
    """Run 9 x 4 x 100 attempts, retaining explicit non-SAFE failures."""
    if RACE_ATTEMPTS != 3600 or sum(n for _, n in STATIC_DISTRIBUTION) != 56:
        raise RaceInfrastructureFailure("locked_matrix_constants_changed")
    accounting = RaceAccounting()
    sentinel = workspace.outside / "sentinel.bin"
    outside_cap = outside_handle = None
    baseline = _handle_count(native)
    try:
        # Sentinel identity and ancestry remain protected throughout every
        # substitution; no actor removes or renames an outside object.
        outside_cap = native.pin_root(workspace.outside)
        outside_handle = native.control_open(
            sentinel, access=FILE_READ_ATTRIBUTES, share=FILE_SHARE_READ)
        outside_identity = native.metadata(outside_handle).identity
        attempt_number = 0
        for case, variant in RACE_VARIANTS:
            for cut in CUTS:
                for repetition in range(1, REPETITIONS + 1):
                    attempt_number += 1
                    _run_one(native, workspace, reporter, accounting,
                             attempt_number, case, variant, cut, repetition,
                             outside_identity, outside_handle, sentinel)
        if accounting.total != RACE_ATTEMPTS:
            raise RaceInfrastructureFailure("race_attempt_accounting_mismatch")
        if len(accounting.buckets) != 36 or any(
            bucket["total"] != REPETITIONS for bucket in accounting.buckets.values()
        ):
            raise RaceInfrastructureFailure("race_bucket_accounting_mismatch")
    finally:
        cleanup_failed = False
        for handle in (outside_handle, outside_cap):
            try:
                _close(handle)
            except Exception:
                cleanup_failed = True
                accounting.handles_restored = False
        if _handle_count(native) != baseline:
            accounting.handles_restored = False
        if cleanup_failed:
            raise RaceInfrastructureFailure("outside_pin_cleanup_failed")
    return accounting
