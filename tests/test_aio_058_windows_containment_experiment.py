"""Exact nonproduction AIO-058 entrypoint; import defines the plan only."""
from __future__ import annotations

from collections import Counter
import json
import os
import sys
import time
import unittest

from experiments.aio_058_windows_containment import windows_containment_probe as probe
from experiments.aio_058_windows_containment import race_harness as races


# Fixed executable specifications, never generated test discovery.
STATIC_SLOTS = (
    ("I01", "nested", "fixtures/nested/plain.bin", "accept"),
    ("I02", "empty", "fixtures/empty.bin", "accept"),
    ("I02", "binary", "fixtures/binary.bin", "accept"),
    ("I02", "invalid_utf8", "fixtures/invalid-utf8.bin", "accept"),
    ("I02", "bom_newline", "fixtures/bom-newline.bin", "accept"),
    ("I03", "boundary", "fixtures/boundary.bin", "accept"),
    ("I03", "oversize", "fixtures/oversize.bin", "reject_zero_reads"),
    ("I04", "missing_intermediate", "missing-dir/file.bin", "reject"),
    ("I04", "missing_final", "fixtures/missing.bin", "reject"),
    ("I04", "directory", "fixtures/dir", "reject_zero_reads"),
    ("I05", "ads", "fixtures/file.bin:stream", "lexical_reject"),
    ("I05", "drive_relative", "C:file.bin", "lexical_reject"),
    ("I05", "drive_absolute", "C:/file.bin", "lexical_reject"),
    ("I05", "unc_slashes", "//server/share/file.bin", "lexical_reject"),
    ("I05", "unc_backslashes", "\\\\server\\share\\file.bin", "lexical_reject"),
    ("I05", "extended_namespace", "\\\\?\\C:\\file.bin", "lexical_reject"),
    ("I05", "pipe_namespace", "\\\\.\\pipe\\aio058", "lexical_reject"),
    ("I05", "con", "CON", "lexical_reject"),
    ("I05", "con_extension", "con.txt", "lexical_reject"),
    ("I05", "com_digit", "COM1.txt", "lexical_reject"),
    ("I05", "lpt_digit", "LPT9", "lexical_reject"),
    ("I05", "aux_nested", "fixtures/AUX.bin", "lexical_reject"),
    ("I06", "trailing_dot", "fixtures/plain.bin.", "lexical_reject"),
    ("I06", "trailing_space", "fixtures/plain.bin ", "lexical_reject"),
    ("I06", "case_mismatch", "fixtures/Plain.bin", "reject_zero_reads"),
    ("I06", "case_sensitive", "fixtures/case-sensitive/a.bin", "accept"),
    ("I06", "short_alias", "fixtures/PLAINL~1.BIN", "reject_zero_reads"),
    ("I06", "nfc", "fixtures/caf\u00e9.bin", "accept_or_exact_reject"),
    ("I06", "nfd", "fixtures/cafe\u0301.bin", "accept_or_exact_reject"),
    ("I06", "punctuation", "fixtures/bad<name.bin", "lexical_reject"),
    ("I10", "file_symlink", "final-link", "reject_zero_reads"),
    ("I10", "directory_symlink", "intermediate-link/sentinel.bin", "reject_zero_reads"),
    ("I11", "junction", "junction/sentinel.bin", "reject_zero_reads"),
    ("I11", "volume_mount", "volume-mount/sentinel.bin", "reject_zero_reads"),
    ("I11", "opaque_guid_tag", "opaque-reparse", "reject_zero_reads"),
    ("I12", "in_root_hardlink", "fixtures/hardlink-source.bin", "reject_zero_reads"),
    ("I12", "outside_hardlink", "fixtures/outside-hardlink.bin", "reject_zero_reads"),
    ("I13", "preexisting_write", "fixtures/write-conflict.bin", "reject_zero_reads"),
    ("I13", "preexisting_delete", "fixtures/delete-conflict.bin", "reject_zero_reads"),
    ("I14", "mapping_first", "fixtures/mapped.bin", "reject_zero_reads"),
    ("I14", "section_first", "fixtures/mapped.bin", "reject_zero_reads"),
    ("I14", "reader_first", "fixtures/mapped.bin", "accept"),
    ("I16", "volume", "fixtures/fault.bin", "fault_reject"),
    ("I16", "file_id", "fixtures/fault.bin", "fault_reject"),
    ("I16", "nondisk", "fixtures/fault.bin", "fault_reject"),
    ("I16", "malformed_metadata", "fixtures/fault.bin", "fault_reject"),
    ("I16", "metadata_query_failure", "fixtures/fault.bin", "fault_reject"),
    ("I16", "delete_pending", "fixtures/fault.bin", "fault_reject"),
    ("I17", "segments_16", "/".join(["seg"] * 15 + ["file.bin"]), "accept"),
    ("I17", "segments_17", "/".join(["seg"] * 16 + ["file.bin"]), "lexical_reject"),
    ("I17", "units_4096", "u" * 4096, "boundary_safe"),
    ("I17", "units_4097", "u" * 4097, "lexical_reject"),
    ("I17", "unpaired_surrogate", "fixtures/\ud800.bin", "lexical_reject"),
    ("I18", "delay", "fixtures/fault.bin", "threshold_negative"),
    ("I18", "native_error", "fixtures/fault.bin", "fault_reject"),
    ("I18", "normal_failure_cleanup", "fixtures/missing.bin", "reject"),
)

KNOWN_BYTES = {
    "fixtures/nested/plain.bin": b"AIO058",
    "fixtures/empty.bin": b"",
    "fixtures/binary.bin": b"\x00\xff\x01",
    "fixtures/invalid-utf8.bin": b"\xc3\x28",
    "fixtures/bom-newline.bin": b"\xef\xbb\xbf\r\n",
    "fixtures/boundary.bin": b"A" * 65536,
    "fixtures/oversize.bin": b"A" * 65537,
    "fixtures/plain.bin": b"plain",
    "fixtures/case-sensitive/a.bin": b"lower",
    "fixtures/case-sensitive/A.bin": b"UPPER",
    "fixtures/PlainLongName.bin": b"long name",
    "fixtures/caf\u00e9.bin": b"NFC",
    "fixtures/cafe\u0301.bin": b"NFD",
    "fixtures/hardlink-source.bin": b"two names",
    "fixtures/write-conflict.bin": b"write conflict",
    "fixtures/delete-conflict.bin": b"delete conflict",
    "fixtures/mapped.bin": b"A" * 4096,
    "fixtures/fault.bin": b"fault fixture",
    "/".join(["seg"] * 15 + ["file.bin"]): b"sixteen",
}


def assert_plan():
    distribution = Counter(case for case, _, _, _ in STATIC_SLOTS)
    assert distribution == dict(races.STATIC_DISTRIBUTION), distribution
    assert len(STATIC_SLOTS) == 56 and races.RACE_ATTEMPTS == 3600
    assert set(distribution) | {case for case, _ in races.RACE_VARIANTS} == {
        f"I{number:02}" for number in range(1, 19)
    }


class Report:
    """Finite in-memory accounting; output contains no fixture content."""
    def __init__(self):
        self.static_records = []
        self.race_records = []
        self.owned_threads_created = 0
        self.owned_threads_reaped = 0
        self.fixture_failures = []
        self.cleanup_failures = []
        self.unauthorized_bytes_returned = False
        self.prerequisites = {}
        self.race_handles_restored = False
        self.setup_stage = "environment"

    def static(self, record):
        if len(self.static_records) >= 56:
            raise AssertionError("static accounting overflow")
        self.static_records.append(record)

    def race(self, record):
        if len(self.race_records) >= 3600:
            raise AssertionError("race accounting overflow")
        self.race_records.append(record)
        if record.get("classification") == "VIOLATION":
            self.unauthorized_bytes_returned |= bool(record.get("unauthorized_bytes_returned", False))

    def owned_thread_created(self):
        self.owned_threads_created += 1

    def owned_thread_reaped(self):
        self.owned_threads_reaped += 1

    def print_summary(self, native, workspace):
        for record in self.static_records:
            print("STATIC " + json.dumps(record, sort_keys=True, ensure_ascii=True), flush=True)
        for case, variant in races.RACE_VARIANTS:
            for cut in races.CUTS:
                rows = [row for row in self.race_records if row.get("case") == case
                        and row.get("variant") == variant and row.get("cut") == cut]
                counts = Counter(row.get("classification") for row in rows)
                bucket = {"case": case, "variant": variant, "cut": cut, "total": len(rows),
                          "safe": counts["SAFE"], "violation": counts["VIOLATION"],
                          "infrastructure_failure": counts["INFRASTRUCTURE_FAILURE"],
                          "mutation_attempted": sum(bool(r.get("mutation_attempted")) for r in rows),
                          "mutation_succeeded": sum(bool(r.get("mutation_succeeded")) for r in rows)}
                print("RACE " + json.dumps(bucket, sort_keys=True), flush=True)
        errors = [row for row in self.race_records if row.get("classification") != "SAFE"]
        for record in errors[:8]:
            print("RACE_FAILURE " + json.dumps(record, sort_keys=True, ensure_ascii=True), flush=True)
        static = Counter(row["classification"] for row in self.static_records)
        race = Counter(row["classification"] for row in self.race_records)
        properties = {}
        for case, expected in races.STATIC_DISTRIBUTION:
            rows = [row for row in self.static_records if row["case"] == case]
            properties[case] = {"planned": expected, "executed": len(rows),
                                "pass": sum(row["classification"] == "PASS" for row in rows)}
        for case, expected in (("I07", 400), ("I08", 400), ("I09", 400), ("I15", 2400)):
            rows = [row for row in self.race_records if row["case"] == case]
            properties[case] = {"planned": expected, "executed": len(rows),
                                "safe": sum(row["classification"] == "SAFE" for row in rows)}
        bounds = {name: max((row.get(name, 0) for row in self.static_records + self.race_records), default=0)
                  for name in ("byte_count", "data_requests", "physical_bytes", "native_calls",
                               "retained_peak", "metadata_per_handle_max", "native_maxcall_seconds")}
        created = getattr(workspace, "roots_created", []) if workspace is not None else []
        cleaned = getattr(workspace, "roots_cleaned", []) if workspace is not None else []
        summary = {
            "STATIC PLANNED": 56, "STATIC TOTAL": len(self.static_records),
            "STATIC PASS": static["PASS"], "STATIC FAIL": static["FAIL"], "STATIC SKIP": 0,
            "STATIC UNEXECUTED": 56 - len(self.static_records),
            "RACE PLANNED": 3600, "RACE TOTAL": len(self.race_records),
            "RACE SAFE": race["SAFE"], "RACE VIOLATION": race["VIOLATION"],
            "RACE INFRASTRUCTURE FAILURE": race["INFRASTRUCTURE_FAILURE"],
            "RACE UNEXECUTED": 3600 - len(self.race_records),
            "UNAUTHORIZED BYTES RETURNED": self.unauthorized_bytes_returned,
            "OWNED CHILDREN CREATED": getattr(native, "children_created", 0) + self.owned_threads_created,
            "OWNED CHILDREN REAPED": getattr(native, "children_reaped", 0) + self.owned_threads_reaped,
            "TEMP ROOTS CREATED": len(created), "TEMP ROOTS CLEANED": len(cleaned),
            "ROOT RECORD": created, "ROOT CLEANUP RECORD": cleaned,
            "FIXTURE FAILURES": self.fixture_failures[:8], "CLEANUP FAILURES": self.cleanup_failures[:8],
            "PREREQUISITES": self.prerequisites,
            "NATIVE HANDLES REMAIN": getattr(native, "handle_count", 0),
            "MAPPED VIEWS CREATED": getattr(native, "views_created", 0),
            "MAPPED VIEWS UNMAPPED": getattr(native, "views_unmapped", 0),
            "MAPPED VIEWS REMAIN": getattr(native, "view_count", 0),
            "PENDING COMPLETION UNVERIFIED": getattr(native, "pending_completion_unverified", False),
            "RACE HANDLES RESTORED": self.race_handles_restored,
            "SECURITY PROPERTY CASES": properties, "OBSERVED MAXIMA": bounds,
            "UNAUTHORIZED DATA REQUESTS": sum(row.get("unauthorized_data_requests", 0)
                                               for row in self.static_records + self.race_records),
            "PRODUCTION TOOL INVOCATION": False, "CANONICAL EVIDENCE MODIFIED": False,
            "ATOMIC CONTENT SNAPSHOT PROVEN": False, "HISTORICAL LINK PROVENANCE PROVEN": False,
            "I14 SUBPROOFS": [{"slot": row["slot"], "classification": row["classification"]}
                               for row in self.static_records if row["case"] == "I14"],
        }
        summary["COMPLETE SUCCESS"] = (
            summary["STATIC TOTAL"] == summary["STATIC PASS"] == 56
            and summary["RACE TOTAL"] == summary["RACE SAFE"] == 3600
            and summary["RACE VIOLATION"] == summary["RACE INFRASTRUCTURE FAILURE"] == 0
            and not summary["UNAUTHORIZED BYTES RETURNED"]
            and summary["UNAUTHORIZED DATA REQUESTS"] == 0
            and summary["NATIVE HANDLES REMAIN"] == 0 and self.race_handles_restored
            and summary["MAPPED VIEWS REMAIN"] == 0
            and summary["MAPPED VIEWS CREATED"] == summary["MAPPED VIEWS UNMAPPED"]
            and {row["slot"] for row in summary["I14 SUBPROOFS"]} == {
                "mapping_first", "section_first", "reader_first"}
            and len(summary["I14 SUBPROOFS"]) == 3
            and not summary["PENDING COMPLETION UNVERIFIED"]
            and summary["OWNED CHILDREN CREATED"] == summary["OWNED CHILDREN REAPED"]
            and summary["TEMP ROOTS CREATED"] == summary["TEMP ROOTS CLEANED"] == 1
            and not self.fixture_failures and not self.cleanup_failures
        )
        print("AIO058_SUMMARY " + json.dumps(summary, sort_keys=True, ensure_ascii=True), flush=True)
        return summary


def _identity(native, path, directory=False):
    # Capture known fixture IDs; never replace the prototype's relative open.
    with native.control_open(path, access=0x80, share=7, directory=directory) as handle:
        return native.metadata(handle).identity


def prepare_static(native, workspace, report):
    report.setup_stage = "ordinary_fixture_directories"
    workspace.mkdir("repo/fixtures/nested")
    workspace.mkdir("repo/fixtures/dir")
    workspace.mkdir("repo/fixtures/case-sensitive")
    report.setup_stage = "case_sensitive_directory"
    native.set_case_sensitive(workspace.repo / "fixtures" / "case-sensitive")
    workspace.mkdir("repo/" + "/".join(["seg"] * 15))
    report.setup_stage = "known_byte_fixtures"
    for resource, data in KNOWN_BYTES.items():
        workspace.file("repo/" + resource, data)
    report.setup_stage = "explicit_short_name"
    native.set_short_name(workspace.repo / "fixtures" / "PlainLongName.bin", "PLAINL~1.BIN")
    report.setup_stage = "file_symlink"
    workspace.symlink("repo/final-link", workspace.outside / "sentinel.bin", directory=False)
    report.setup_stage = "directory_symlink"
    workspace.symlink("repo/intermediate-link", workspace.outside, directory=True)
    report.setup_stage = "junction"
    workspace.junction("repo/junction", workspace.outside)
    report.setup_stage = "opaque_guid_reparse"
    workspace.custom_reparse("repo/opaque-reparse")
    report.setup_stage = "second_ntfs_volume_mount"
    workspace.mounted_volume("repo/volume-mount")
    report.setup_stage = "in_root_hardlink"
    workspace.hardlink("repo/fixtures/hardlink-alias.bin", workspace.repo / "fixtures" / "hardlink-source.bin")
    report.setup_stage = "outside_hardlink"
    workspace.hardlink("repo/fixtures/outside-hardlink.bin", workspace.outside / "sentinel.bin")
    report.setup_stage = "fixture_identity_verification"
    identities = {resource: _identity(native, workspace.repo.joinpath(*resource.split("/")))
                  for resource in KNOWN_BYTES}
    assert identities["fixtures/case-sensitive/a.bin"] != identities["fixtures/case-sensitive/A.bin"], "distinct case fixture IDs"
    assert identities["fixtures/caf\u00e9.bin"] != identities["fixtures/cafe\u0301.bin"], "distinct Unicode fixture IDs"
    native.prerequisites["hostile_fixture_setup"] = {
        "file_symlink": "created", "directory_symlink": "created",
        "junction": "created_and_queried", "volume_mount": "distinct_NTFS_created_and_queried",
        "opaque_guid_reparse": "created_and_queried", "hardlinks": "created",
        "case_sensitive_directory": "set_and_queried", "explicit_short_name": "set_and_queried",
    }
    return identities


def _opaque_reparse_proof(result):
    """Require the actual final-component guard, not an unrelated open failure."""
    if result.accepted or result.data_requests != 0 or result.fault_hit or result.opens != 1:
        return False
    for event in result.trace:
        if (event.get("event") != "reparse_security_check"
                or event.get("component_index") != 0 or event.get("directory") is not False
                or event.get("rejected") is not True):
            continue
        if (event.get("source") == "OBJ_DONT_REPARSE"
                and event.get("native_status") == 0xC000050B
                and event.get("object_attributes") == 0x1000
                and event.get("create_options") == 0x00200060
                and event.get("parent_relative") is True
                and result.reason.startswith("native_status_c000050b_winerror_")):
            return True
        if (event.get("source") == "opened_handle_metadata"
                and event.get("actual_directory") is False
                and event.get("reparse_attribute") is True
                and event.get("reparse_tag") == probe.CUSTOM_TAG
                and result.reason == "containment_rejected"):
            return True
    return False


def _mapping_exclusion_proof(result):
    """Attribute exclusion to the exact final reader open, not any share error."""
    if (result.accepted or result.data_requests != 0 or result.physical_bytes != 0
            or result.opens != 2 or result.fault_hit
            or result.reason != "native_status_c0000043_winerror_32"):
        return False
    return any(
        event.get("event") == "component_open_rejected"
        and event.get("operation") == "NtCreateFile"
        and event.get("component_index") == 1 and event.get("directory") is False
        and event.get("desired_access") == 0x00100081
        and event.get("share_mode") == 1 and event.get("create_options") == 0x00200060
        and event.get("object_attributes") == 0x1000
        and event.get("parent_relative") is True
        and event.get("native_status") == 0xC0000043 and event.get("winerror") == 32
        for event in result.trace)


def _protected_read_proof(result):
    """Same live handle through all data/EOF and post-read checks, then close."""
    events = result.trace
    acquired = [i for i, event in enumerate(events) if event.get("event") == "target_handle_acquired"]
    checked = [i for i, event in enumerate(events) if event.get("event") == "post_read_verified"]
    closed = [i for i, event in enumerate(events) if event.get("event") == "target_handle_closed"]
    data = [i for i, event in enumerate(events) if event.get("event") == "data_request"]
    if (not result.accepted or len(acquired) != 1 or len(checked) != 1 or len(closed) != 1
            or len(data) != 2 or not acquired[0] < data[0] <= data[-1] < checked[0] < closed[0]):
        return False
    for index in acquired + data + checked:
        if (events[index].get("target_handle_token") != 1
                or events[index].get("protection_live") is not True):
            return False
    return (events[acquired[0]].get("desired_access") == 0x00100081
            and events[acquired[0]].get("share_mode") == 1
            and events[closed[0]].get("target_handle_token") == 1
            and events[closed[0]].get("protection_live") is False
            and events[data[0]].get("offset") == 0 and events[data[0]].get("requested") == 4096
            and events[data[1]].get("offset") == 4096 and events[data[1]].get("requested") == 1)


def _writer_positive_control(native, path, identity):
    with native.fixture_writer_open(path) as writer:
        assert native.metadata(writer).identity == identity, "writer control selected wrong fixture"
    assert writer.value is None, "writer control cleanup not verified"
    return True


def _i14_existing_state(native, cap, path, resource, identity, slot, record):
    state = None
    try:
        state = native.fixture_writable_state(path, identity, kind="view" if slot == "mapping_first" else "section")
        with state:
            assert state.prove_live(), "required writable mapping/section not live"
            record["state_before_reader"] = state.snapshot()
            expected = {"origin_closed": True, "section_closed": slot == "mapping_first",
                        "view_live": slot == "mapping_first", "section_live": slot == "section_first",
                        "calibrated": True}
            assert record["state_before_reader"] == expected, "mapping/section ordering not established"
            result = cap.read(resource, expected_identity=identity)
            record["_observed_result"] = result
            assert state.prove_live(), "mapping/section lost before reader attempt completed"
            record["state_after_reader"] = state.snapshot()
            assert record["state_after_reader"] == expected, "required state not retained through attempt"
            record["explicit_final_open_share_conflict"] = _mapping_exclusion_proof(result)
            return result
    finally:
        if state is not None:
            record["state_after_cleanup"] = state.snapshot()
            assert record["state_after_cleanup"] == {
                "origin_closed": True, "section_closed": True, "view_live": False,
                "section_live": False, "calibrated": True}, "mapping/section cleanup not verified"


def _i14_reader_first(native, cap, path, resource, identity, record):
    record.update({"writer_control_before": False, "writer_control_after": False,
                   "reader_cut_reached": False, "writer_share_conflict": False,
                   "readonly_mapping_access_rejected": False, "protected_read_window": False})
    record["writer_control_before"] = _writer_positive_control(native, path, identity)
    def writer_actor(cut, context):
        if cut != "before_first_content_read":
            return
        target = context["final"]
        assert target.value and target in native._handles and context["identity"] == identity, "reader not live/verified at cut"
        record["reader_cut_reached"] = True
        record["reader_live_before_controls"] = True
        try:
            writer = native.fixture_writer_open(path)
        except probe.NativeError as error:
            record["writer_attempt"] = {"operation": error.operation, "desired_access": 0xC0000000,
                                        "share_mode": 7, "native_status": error.status,
                                        "winerror": error.winerror, "succeeded": False}
            assert error.operation == "CreateFileW" and error.status == 0 and error.winerror == 32, "unrelated writer failure"
            record["writer_share_conflict"] = True
        else:
            writer.close()
            raise AssertionError("incompatible writer acquired during reader window")
        assert target.value and target in native._handles, "reader protection lost after writer attempt"
        record["mapping_attempt"] = native.fixture_readonly_mapping_attempt(target)
        assert record["mapping_attempt"] == {
            "operation": "CreateFileMappingW", "protection": 4, "winerror": 5,
            "succeeded": False}, "readonly handle allowed writable mapping or unrelated failure"
        record["readonly_mapping_access_rejected"] = True
        assert target.value and target in native._handles, "reader protection lost after mapping attempt"
        record["reader_live_after_controls"] = True
    result = cap.read(resource, expected_identity=identity, hook=writer_actor)
    record["_observed_result"] = result
    record["writer_control_after"] = _writer_positive_control(native, path, identity)
    record["protected_read_window"] = _protected_read_proof(result)
    assert record["reader_cut_reached"] and record["writer_share_conflict"], "reader-first share cut not proved"
    assert record["readonly_mapping_access_rejected"], "readonly mapping rejection not proved"
    assert record["protected_read_window"], "reader released protection before content/metadata completion"
    return result


def _expected_rejection(slot, result):
    """An unrelated API/ABI failure cannot satisfy a negative security slot."""
    reason = result.reason
    native_status = None
    if reason.startswith("native_status_"):
        try:
            native_status = int(reason.split("_")[2], 16)
        except (IndexError, ValueError):
            pass
    missing = {0xC0000034, 0xC000003A, 0xC000000F}
    reparse = {0xC000050B, 0x8000002D, 0xC0000279}
    lexical = {"resource_unsupported", "resource_bound"}
    if slot in {"ads", "drive_relative", "drive_absolute", "unc_slashes", "unc_backslashes",
                "extended_namespace", "pipe_namespace", "con", "con_extension", "com_digit",
                "lpt_digit", "aux_nested", "trailing_dot", "trailing_space", "punctuation",
                "segments_17", "units_4097", "unpaired_surrogate"}:
        return reason in lexical
    if slot in {"missing_intermediate", "missing_final", "normal_failure_cleanup"}:
        return native_status in missing
    if slot == "directory":
        return reason == "containment_rejected" or native_status == 0xC00000BA
    if slot in {"case_mismatch", "short_alias"}:
        return reason in {"containment_rejected", "unexpected_identity"} or native_status in missing
    if slot in {"nfc", "nfd"}:
        return reason in {"containment_rejected", "unexpected_identity", "native_name_buffer"}
    if slot == "opaque_guid_tag":
        return _opaque_reparse_proof(result)
    if slot in {"file_symlink", "directory_symlink", "junction", "volume_mount"}:
        return reason == "containment_rejected" or native_status in reparse
    if slot in {"in_root_hardlink", "outside_hardlink"}:
        return reason in {"hard_link_rejected", "outside_identity", "containment_rejected"}
    if slot in {"preexisting_write", "preexisting_delete"}:
        return native_status == 0xC0000043
    if slot == "oversize":
        return reason == "size_limit_exceeded"
    if slot == "units_4096":
        return native_status in {0xC0000106, 0xC0000033}
    if slot in {"mapping_first", "section_first"}:
        return _mapping_exclusion_proof(result)
    if slot == "delay":
        return result.fault_hit and reason == "observation_threshold"
    fault_reasons = {
        "volume": {"containment_rejected"},
        "file_id": {"unexpected_identity", "file_identity_mismatch"},
        "nondisk": {"containment_rejected"},
        "malformed_metadata": {"malformed_metadata"},
        "metadata_query_failure": {"native_status_00000000_winerror_87"},
        "delete_pending": {"containment_rejected"},
        "native_error": {"native_status_c0000001_winerror_31"},
    }
    return slot in fault_reasons and result.fault_hit and reason in fault_reasons[slot]


def _check_result(result, expectation, expected_bytes, slot, forbidden_ids):
    injected_delay = slot == "delay"
    assert result.opens <= 16, "open bound"
    assert result.data_requests <= 17, "data request bound"
    assert result.physical_bytes <= 65537, "physical byte bound"
    data_calls = [row for row in result.trace if row.get("event") == "data_request"]
    requested_bytes = sum(row["requested"] for row in data_calls)
    assert requested_bytes <= 65537 and result.physical_bytes <= requested_bytes, "requested byte bound"
    assert len(data_calls) == result.data_requests, "data call accounting mismatch"
    assert result.native_calls <= 253, "native call bound"
    assert result.retained_peak <= 48, "reader retained handle bound"
    assert max(result.metadata_per_handle, default=0) <= 12, "metadata per handle bound"
    assert result.unauthorized_reads == 0, "outside identity reached data boundary"
    assert not any(row.get("event") == "data_request" and row.get("identity") in forbidden_ids
                   for row in result.trace), "outside content request"
    assert result.handles_before == result.handles_after, "handle leak"
    if not injected_delay:
        assert result.seconds <= 5.0, "uninjected attempt exceeds observation gate"
        assert result.native_maxcall_seconds <= 5.0, "uninjected native call exceeds observation gate"
    if result.accepted:
        assert type(result.data) is bytes and len(result.data) <= 65536, "immutable output bound"
    else:
        assert result.data is None, "failed read disclosed partial data"
        assert _expected_rejection(slot, result), "unrelated native failure cannot satisfy expected rejection"
    if expectation == "accept":
        assert result.accepted, result.reason
        assert result.data == expected_bytes, "exact byte mismatch"
        if slot == "boundary":
            assert result.data_requests == 17 and requested_bytes == 65537 and result.physical_bytes == 65536, "exact boundary and EOF probe"
        if slot == "empty":
            assert result.data_requests == 1 and requested_bytes == 1 and result.physical_bytes == 0, "empty EOF probe"
    elif expectation in ("reject", "reject_zero_reads", "fault_reject", "lexical_reject"):
        assert not result.accepted, "required rejection accepted"
        if expectation != "reject":
            assert result.data_requests == 0, "rejected object reached data call"
        if expectation == "lexical_reject":
            assert result.opens == 0, "lexically rejected endpoint opened"
    elif expectation == "accept_or_exact_reject":
        if result.accepted:
            assert result.data == expected_bytes, "Unicode spelling selected another object"
        else:
            assert result.data_requests == 0, "Unicode rejection after data access"
    elif expectation == "boundary_safe":
        assert not result.accepted and result.data_requests == 0, "filesystem boundary failed closed"
    elif expectation == "threshold_negative":
        assert not result.accepted and result.seconds > 5.0, "injected delay support gate failed"
    else:
        raise AssertionError("unknown fixed expectation")


def run_static(native, workspace, report, identities):
    with native.pin_root(workspace.repo) as cap:
        for index, (case, slot, resource, expectation) in enumerate(STATIC_SLOTS, 1):
            baseline = native.handle_count
            record = {"attempt": index, "case": case, "slot": slot, "classification": "FAIL"}
            started = time.perf_counter()
            result = None
            view_baseline = native.view_count
            try:
                if slot in ("segments_16", "units_4096"):
                    probe.validate_resource(resource)
                if expectation == "lexical_reject":
                    try:
                        probe.validate_resource(resource)
                    except probe.Reject:
                        pass
                    else:
                        raise AssertionError("required lexical bound/spelling accepted")
                fault = slot if case == "I16" or slot in ("delay", "native_error") else None
                if case == "I13":
                    access = 0x2 if slot == "preexisting_write" else 0x10000
                    with native.control_open(workspace.repo.joinpath(*resource.split("/")), access=access, share=7):
                        result = cap.read(resource, expected_identity=identities[resource])
                elif case == "I14":
                    path = workspace.repo / "fixtures" / "mapped.bin"
                    record["exclusion_model"] = "current_open_mutual_exclusion"
                    if slot in {"mapping_first", "section_first"}:
                        result = _i14_existing_state(native, cap, path, resource, identities[resource], slot, record)
                    else:
                        assert slot == "reader_first", "unknown I14 ordering"
                        result = _i14_reader_first(native, cap, path, resource, identities[resource], record)
                else:
                    result = cap.read(resource, fault=fault, expected_identity=identities.get(resource))
                if result.accepted and (result.identity in native.forbidden_ids or
                                        (resource in identities and result.identity != identities[resource])):
                    report.unauthorized_bytes_returned = True
                _check_result(result, expectation, KNOWN_BYTES.get(resource), slot, native.forbidden_ids)
                assert native.handle_count == baseline, "static fixture/control handle leak"
                assert native.view_count == view_baseline, "static mapped-view leak"
                record["classification"] = "PASS"
            except Exception as error:
                record["error"] = type(error).__name__
                record["failure"] = str(error)[:160] if isinstance(error, AssertionError) else "native_or_fixture_failure"
            finally:
                result = record.pop("_observed_result", result)
                record["seconds"] = round(time.perf_counter() - started, 6)
                record["mapped_views_before"] = view_baseline
                record["mapped_views_after"] = native.view_count
                if result is not None:
                    if slot == "opaque_guid_tag":
                        record["opaque_reparse_security_check_reached"] = _opaque_reparse_proof(result)
                        record["explicit_reparse_rejection"] = _opaque_reparse_proof(result)
                    record.update({"accepted": result.accepted, "reason": result.reason,
                                   "byte_count": len(result.data) if result.data is not None else 0,
                                   "data_requests": result.data_requests, "physical_bytes": result.physical_bytes,
                                   "opens": result.opens, "native_calls": result.native_calls,
                                   "retained_peak": result.retained_peak,
                                   "metadata_per_handle_max": max(result.metadata_per_handle, default=0),
                                   "native_maxcall_seconds": round(result.native_maxcall_seconds, 6),
                                   "fault_hit": result.fault_hit,
                                   "requested_bytes": sum(row["requested"] for row in result.trace if row.get("event") == "data_request"),
                                   "unauthorized_data_requests": result.unauthorized_reads})
                    if result.identity is not None:
                        record["opened_identity"] = {"volume": result.identity[0], "file_id": result.identity[1].hex()}
                report.static(record)


class AIO058WindowsContainmentExperiment(unittest.TestCase):
    def test_locked_matrix(self):
        assert_plan()
        report, native, workspace = Report(), None, None
        try:
            if os.name != "nt":
                raise RuntimeError("fixed Windows experiment required")
            if sys.executable.casefold() != r"C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe".casefold():
                raise RuntimeError("fixed interpreter required")
            if not sys.flags.isolated or not sys.flags.dont_write_bytecode:
                raise RuntimeError("-I -B required")
            native = probe.Native()
            workspace = probe.OwnedWorkspace(native)
            report.setup_stage = "trusted_workspace_provisioning"
            with workspace:
                report.prerequisites = getattr(native, "prerequisites", {})
                with native.pin_root(workspace.outside):
                    with native.control_open(workspace.outside / "sentinel.bin", access=0x80, share=1) as sentinel:
                        native.forbidden_ids.add(native.metadata(sentinel).identity)
                        identities = prepare_static(native, workspace, report)
                        report.setup_stage = "static_attempts"
                        run_static(native, workspace, report, identities)
                        report.setup_stage = "race_attempts"
                        accounting = races.run_races(native, workspace, report)
                        report.race_handles_restored = accounting.handles_restored
        except Exception as error:
            report.fixture_failures.append({"category": type(error).__name__,
                                            "winerror": getattr(error, "winerror", None),
                                            "native_status": getattr(error, "status", None),
                                            "operation": getattr(error, "operation", None),
                                            "reason": str(error) if isinstance(error, probe.Reject) else None,
                                            "stage": report.setup_stage})
        finally:
            if workspace is not None:
                report.cleanup_failures.extend(getattr(workspace, "cleanup_failures", []))
            summary = report.print_summary(native, workspace)
        self.assertTrue(summary["COMPLETE SUCCESS"], "AIO058 matrix incomplete or failed; paste AIO058_SUMMARY")


if __name__ == "__main__":
    unittest.main(argv=["aio058", "-v"])
