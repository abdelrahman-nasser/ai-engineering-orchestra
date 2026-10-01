"""Focused immutable registry, selection, and history tests for AIO-051."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields
from pathlib import Path
from types import MappingProxyType
import unittest
from unittest.mock import patch

import engineering_orchestration
import engineering_orchestration.agent_operation_tool_registry as subject
from engineering_orchestration.agent_operation_tool_registry import (
    _AEO_NATIVE_REPOSITORY_FILE_READ_TOOL_ID,
    _AgentOperationToolImplementationSelector,
    _AgentOperationToolRegistration,
    _AgentOperationToolRegistryAuditMaterial,
    _AgentOperationToolRegistryBuildResult,
    _AgentOperationToolRegistryOutcome,
    _AgentOperationToolRegistryRetryDisposition,
    _AgentOperationToolRoute,
    _AgentOperationToolRouteSelectionResult,
    _ResolvedAgentOperationToolRegistration,
    _SelectedAgentOperationToolRoute,
    _TrustedAgentOperationToolRegistrySnapshot,
    _agent_operation_tool_registry_retry_disposition,
    _build_trusted_agent_operation_tool_registry_snapshot,
    _make_aeo_native_repository_file_read_registration,
    _resolve_agent_operation_tool_registration,
    _select_agent_operation_tool_route,
)


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT / "engineering_orchestration" / "agent_operation_tool_registry.py"
)
RUNTIME_ID = "runtime::synthetic"
ENVIRONMENT_ID = "environment::synthetic"
OPERATION_ID = "repository_file_read"
TOOL_ID = "tool::synthetic-repository-reader::v1"
SELECTOR = (
    _AgentOperationToolImplementationSelector.
    AEO_NATIVE_REPOSITORY_FILE_READ_V1
)


def route(
    runtime_option_id: object = RUNTIME_ID,
    environment_id: object = ENVIRONMENT_ID,
    operation_id: object = OPERATION_ID,
) -> _AgentOperationToolRoute:
    return _AgentOperationToolRoute(
        runtime_option_id,  # type: ignore[arg-type]
        environment_id,  # type: ignore[arg-type]
        operation_id,  # type: ignore[arg-type]
    )


def registration(
    *,
    runtime_option_id: object = RUNTIME_ID,
    environment_id: object = ENVIRONMENT_ID,
    operation_id: object = OPERATION_ID,
    tool_id: object = TOOL_ID,
    selector: object = SELECTOR,
) -> _AgentOperationToolRegistration:
    return _AgentOperationToolRegistration(
        runtime_option_id,  # type: ignore[arg-type]
        environment_id,  # type: ignore[arg-type]
        operation_id,  # type: ignore[arg-type]
        tool_id,  # type: ignore[arg-type]
        selector,  # type: ignore[arg-type]
    )


def build(
    registrations: object | None = None,
    **kwargs: object,
) -> _AgentOperationToolRegistryBuildResult:
    supplied = (registration(),) if registrations is None else registrations
    return _build_trusted_agent_operation_tool_registry_snapshot(
        supplied,  # type: ignore[arg-type]
        **kwargs,  # type: ignore[arg-type]
    )


def built_snapshot(
    registrations: object | None = None,
    **kwargs: object,
) -> _TrustedAgentOperationToolRegistrySnapshot:
    result = build(registrations, **kwargs)
    if result.outcome is not _AgentOperationToolRegistryOutcome.RESOLVED:
        raise AssertionError(f"snapshot build failed: {result.outcome}")
    if type(result.snapshot) is not _TrustedAgentOperationToolRegistrySnapshot:
        raise AssertionError("snapshot build returned no exact snapshot")
    return result.snapshot


class RegistryFixture(unittest.TestCase):
    def assert_build_rejected(
        self,
        result: _AgentOperationToolRegistryBuildResult,
        outcome: _AgentOperationToolRegistryOutcome,
    ) -> None:
        self.assertIs(type(result), _AgentOperationToolRegistryBuildResult)
        self.assertIs(result.outcome, outcome)
        self.assertIs(
            result.retry_disposition,
            _agent_operation_tool_registry_retry_disposition(outcome),
        )
        self.assertIsNone(result.snapshot)
        self.assertIs(type(result.audit), _AgentOperationToolRegistryAuditMaterial)
        self.assertIs(result.audit.outcome, outcome)
        self.assertIs(result.audit.retry_disposition, result.retry_disposition)

    def assert_selection_rejected(
        self,
        result: _AgentOperationToolRouteSelectionResult,
        outcome: _AgentOperationToolRegistryOutcome,
    ) -> None:
        self.assertIs(type(result), _AgentOperationToolRouteSelectionResult)
        self.assertIs(result.outcome, outcome)
        self.assertIsNone(result.selected_route)
        self.assertIs(
            result.retry_disposition,
            _agent_operation_tool_registry_retry_disposition(outcome),
        )


class RegistryPrivateContractTests(RegistryFixture):
    def test_private_types_are_closed_frozen_slotted_and_exactly_shaped(
        self,
    ) -> None:
        self.assertEqual(subject.__all__, ())
        self.assertFalse(
            hasattr(engineering_orchestration, "TrustedAgentOperationToolRegistry")
        )
        self.assertEqual(
            [item.name for item in fields(_AgentOperationToolRoute)],
            ["runtime_option_id", "environment_id", "operation_id"],
        )
        self.assertEqual(
            [item.name for item in fields(_AgentOperationToolRegistration)],
            [
                "runtime_option_id",
                "environment_id",
                "operation_id",
                "tool_id",
                "implementation_selector",
            ],
        )
        self.assertEqual(
            [item.name for item in fields(_SelectedAgentOperationToolRoute)],
            ["route", "tool_id"],
        )
        self.assertEqual(
            [
                item.name
                for item in fields(_ResolvedAgentOperationToolRegistration)
            ],
            ["route", "registration", "snapshot_fingerprint"],
        )
        for value in (
            route(),
            registration(),
            _SelectedAgentOperationToolRoute(route(), TOOL_ID),
        ):
            self.assertFalse(hasattr(value, "__dict__"))
            with self.assertRaises(FrozenInstanceError):
                setattr(value, fields(value)[0].name, "changed")

    def test_closed_outcome_and_retry_vocabularies_match_the_design(self) -> None:
        self.assertEqual(
            tuple(item.value for item in _AgentOperationToolRegistryOutcome),
            (
                "resolved",
                "registry_invalid",
                "registry_unavailable",
                "registration_invalid",
                "unknown_route",
                "unknown_tool",
                "duplicate_route",
                "duplicate_tool_id",
                "tool_id_rebind",
                "alias_invalid",
                "alias_target_unknown",
                "runtime_mismatch",
                "environment_mismatch",
                "operation_mismatch",
                "resource_widening",
                "tool_retired",
                "historical_mapping_missing",
                "adapter_kind_unknown",
                "fingerprint_mismatch",
                "integrity_failure",
            ),
        )
        self.assertEqual(
            tuple(
                item.value
                for item in _AgentOperationToolRegistryRetryDisposition
            ),
            (
                "no_retry_needed",
                "new_run_required",
                "registry_remediation_required",
                "package_or_configuration_remediation_required",
                "historical_mapping_remediation_required",
                "do_not_retry_same_run",
            ),
        )
        self.assertEqual(
            {
                outcome:
                    _agent_operation_tool_registry_retry_disposition(outcome)
                for outcome in _AgentOperationToolRegistryOutcome
            },
            dict(subject._OUTCOME_RETRY_DISPOSITIONS),
        )

    def test_native_registration_factory_is_exact_identity_only_and_closed(
        self,
    ) -> None:
        supplied = _make_aeo_native_repository_file_read_registration(
            RUNTIME_ID,
            ENVIRONMENT_ID,
        )
        self.assertEqual(
            supplied,
            registration(tool_id=_AEO_NATIVE_REPOSITORY_FILE_READ_TOOL_ID),
        )
        self.assertIs(type(supplied), _AgentOperationToolRegistration)
        self.assertIs(type(supplied.implementation_selector), type(SELECTOR))
        self.assertFalse(callable(supplied.implementation_selector))
        self.assertNotIn("callable", {item.name for item in fields(supplied)})
        self.assertNotIn("resource", {item.name for item in fields(supplied)})

        class DerivedIdentifier(str):
            pass

        for bad_runtime, bad_environment in (
            ("", ENVIRONMENT_ID),
            (DerivedIdentifier(RUNTIME_ID), ENVIRONMENT_ID),
            (RUNTIME_ID, ""),
            (RUNTIME_ID, DerivedIdentifier(ENVIRONMENT_ID)),
        ):
            with self.subTest(
                runtime=bad_runtime,
                environment=bad_environment,
            ), self.assertRaises(ValueError):
                _make_aeo_native_repository_file_read_registration(
                    bad_runtime,  # type: ignore[arg-type]
                    bad_environment,  # type: ignore[arg-type]
                )

    def test_snapshot_cannot_be_directly_constructed(self) -> None:
        with self.assertRaises(TypeError):
            _TrustedAgentOperationToolRegistrySnapshot()


class RegistryConstructionTests(RegistryFixture):
    def test_strict_utf8_identifiers_accept_ascii_and_valid_unicode(
        self,
    ) -> None:
        ascii_result = build((registration(),))
        self.assertIs(
            ascii_result.outcome,
            _AgentOperationToolRegistryOutcome.RESOLVED,
        )
        self.assertIsNotNone(ascii_result.snapshot)

        unicode_registration = registration(
            runtime_option_id="runtime::\u8fd0\u884c\u65f6",
            environment_id="environment::caf\u00e9",
            tool_id="tool::\u9605\u8bfb\u5668::v1",
        )
        unicode_route = route(
            runtime_option_id=unicode_registration.runtime_option_id,
            environment_id=unicode_registration.environment_id,
        )
        unicode_alias = "reader::\u8bfb\u53d6"
        first = build(
            (unicode_registration,),
            aliases=((unicode_alias, unicode_route),),
        )
        second = build(
            (unicode_registration,),
            aliases=((unicode_alias, unicode_route),),
        )

        for result in (first, second):
            self.assertIs(
                result.outcome,
                _AgentOperationToolRegistryOutcome.RESOLVED,
            )
            self.assertIsNotNone(result.snapshot)
        assert first.snapshot is not None
        assert second.snapshot is not None
        self.assertEqual(
            first.snapshot._registrations,
            (unicode_registration,),
        )
        self.assertEqual(
            first.snapshot._aliases,
            ((unicode_alias, unicode_route),),
        )
        self.assertEqual(
            first.snapshot._registration_fingerprint,
            second.snapshot._registration_fingerprint,
        )

    def test_unpaired_surrogates_in_canonical_identifiers_fail_closed(
        self,
    ) -> None:
        for surrogate_name, surrogate in (
            ("high", "\ud800"),
            ("low", "\udfff"),
        ):
            for field_name in (
                "runtime_option_id",
                "environment_id",
                "operation_id",
                "tool_id",
            ):
                with self.subTest(
                    surrogate=surrogate_name,
                    field=field_name,
                ):
                    supplied = registration(
                        **{field_name: f"identifier::{surrogate}"}
                    )
                    try:
                        result = build((supplied,))
                    except UnicodeEncodeError as error:
                        self.fail(
                            "UnicodeEncodeError escaped registry construction: "
                            f"{error.reason}"
                        )
                    self.assert_build_rejected(
                        result,
                        _AgentOperationToolRegistryOutcome.
                        REGISTRATION_INVALID,
                    )

    def test_surrogate_alias_and_fingerprint_encoding_fail_closed(
        self,
    ) -> None:
        for surrogate_name, surrogate in (
            ("high", "\ud800"),
            ("low", "\udfff"),
        ):
            with self.subTest(surrogate=surrogate_name):
                result = build(
                    aliases=((f"reader::{surrogate}", route()),)
                )
                self.assert_build_rejected(
                    result,
                    _AgentOperationToolRegistryOutcome.ALIAS_INVALID,
                )

        encoding_error = UnicodeEncodeError(
            "utf-8",
            "\ud800",
            0,
            1,
            "surrogates not allowed",
        )
        with patch.object(
            subject,
            "_registration_fingerprint",
            side_effect=encoding_error,
        ):
            self.assert_build_rejected(
                build(),
                _AgentOperationToolRegistryOutcome.REGISTRATION_INVALID,
            )

    def test_atomic_build_owns_deeply_immutable_canonical_state(self) -> None:
        first = registration()
        second = registration(
            runtime_option_id="runtime::next",
            environment_id="environment::next",
            tool_id="tool::reader::v2",
        )
        first_route = route()
        alias_entries = [("reader-current", first_route)]
        retired_entries: list[_AgentOperationToolRoute] = []
        declarations = [second, first]
        result = build(
            declarations,
            aliases=alias_entries,
            retired_routes=retired_entries,
        )
        self.assertIs(result.outcome, _AgentOperationToolRegistryOutcome.RESOLVED)
        self.assertIs(
            result.retry_disposition,
            _AgentOperationToolRegistryRetryDisposition.NO_RETRY_NEEDED,
        )
        snapshot = result.snapshot
        self.assertIs(type(snapshot), _TrustedAgentOperationToolRegistrySnapshot)
        assert snapshot is not None
        self.assertIs(type(snapshot._registrations), tuple)
        self.assertIs(type(snapshot._aliases), tuple)
        self.assertIs(type(snapshot._retired_routes), frozenset)
        self.assertIs(type(snapshot._registrations_by_route), type(MappingProxyType({})))
        self.assertIs(
            type(snapshot._registrations_by_scoped_tool_id),
            type(MappingProxyType({})),
        )
        self.assertIs(type(snapshot._aliases_by_name), type(MappingProxyType({})))
        self.assertEqual(
            snapshot._registrations,
            tuple(sorted((first, second), key=subject._canonical_registration_key)),
        )

        declarations.clear()
        alias_entries.clear()
        retired_entries.append(first_route)
        self.assertEqual(len(snapshot._registrations), 2)
        self.assertEqual(snapshot._aliases, (("reader-current", first_route),))
        self.assertEqual(snapshot._retired_routes, frozenset())
        with self.assertRaises(TypeError):
            snapshot._registrations_by_route[first_route] = first  # type: ignore[index]
        with self.assertRaises(FrozenInstanceError):
            snapshot._registration_fingerprint = "changed"  # type: ignore[misc]

    def test_missing_invalid_and_unsupported_declarations_fail_atomically(
        self,
    ) -> None:
        self.assert_build_rejected(
            build(()),
            _AgentOperationToolRegistryOutcome.REGISTRY_UNAVAILABLE,
        )
        self.assert_build_rejected(
            build(7),
            _AgentOperationToolRegistryOutcome.REGISTRY_INVALID,
        )
        self.assert_build_rejected(
            build((object(),)),
            _AgentOperationToolRegistryOutcome.REGISTRATION_INVALID,
        )
        for supplied in (
            registration(runtime_option_id=""),
            registration(environment_id=""),
            registration(tool_id=""),
        ):
            with self.subTest(registration=supplied):
                self.assert_build_rejected(
                    build((supplied,)),
                    _AgentOperationToolRegistryOutcome.REGISTRATION_INVALID,
                )
        self.assert_build_rejected(
            build((registration(operation_id="repository_file_write"),)),
            _AgentOperationToolRegistryOutcome.OPERATION_MISMATCH,
        )
        self.assert_build_rejected(
            build((registration(selector="dynamic.import.path"),)),
            _AgentOperationToolRegistryOutcome.ADAPTER_KIND_UNKNOWN,
        )

    def test_every_duplicate_route_including_equal_and_changed_fails_closed(
        self,
    ) -> None:
        original = registration()
        self.assert_build_rejected(
            build((original, original)),
            _AgentOperationToolRegistryOutcome.DUPLICATE_ROUTE,
        )
        equal_copy = registration()
        self.assertIsNot(equal_copy, original)
        self.assert_build_rejected(
            build((original, equal_copy)),
            _AgentOperationToolRegistryOutcome.DUPLICATE_ROUTE,
        )
        self.assert_build_rejected(
            build(
                (
                    original,
                    registration(tool_id="tool::synthetic-reader::v2"),
                )
            ),
            _AgentOperationToolRegistryOutcome.DUPLICATE_ROUTE,
        )
        self.assert_build_rejected(
            build(
                (
                    original,
                    registration(selector=object()),
                )
            ),
            _AgentOperationToolRegistryOutcome.ADAPTER_KIND_UNKNOWN,
        )

    def test_aliases_are_exact_ordered_pre_run_routes_not_tool_shortcuts(
        self,
    ) -> None:
        target = route()
        snapshot = built_snapshot(
            aliases=(("reader-current", target), ("Reader-Current", target))
        )
        for alias in ("reader-current", "Reader-Current"):
            with self.subTest(alias=alias):
                selected = _select_agent_operation_tool_route(
                    snapshot,
                    alias=alias,
                )
                self.assertIs(
                    selected.outcome,
                    _AgentOperationToolRegistryOutcome.RESOLVED,
                )
                self.assertIs(
                    type(selected.selected_route),
                    _SelectedAgentOperationToolRoute,
                )
                self.assertEqual(selected.selected_route.route, target)  # type: ignore[union-attr]
                self.assertEqual(selected.selected_route.tool_id, TOOL_ID)  # type: ignore[union-attr]
        self.assert_selection_rejected(
            _select_agent_operation_tool_route(snapshot, alias="READER-CURRENT"),
            _AgentOperationToolRegistryOutcome.ALIAS_INVALID,
        )
        self.assert_selection_rejected(
            _select_agent_operation_tool_route(snapshot),
            _AgentOperationToolRegistryOutcome.REGISTRY_INVALID,
        )
        self.assert_selection_rejected(
            _select_agent_operation_tool_route(
                snapshot,
                route=target,
                alias="reader-current",
            ),
            _AgentOperationToolRegistryOutcome.REGISTRY_INVALID,
        )

    def test_duplicate_unknown_chained_and_tool_shadowing_aliases_are_rejected(
        self,
    ) -> None:
        target = route()
        self.assert_build_rejected(
            build(aliases=(("reader", target), ("reader", target))),
            _AgentOperationToolRegistryOutcome.ALIAS_INVALID,
        )
        self.assert_build_rejected(
            build(aliases=(("reader", route("runtime::unknown")),)),
            _AgentOperationToolRegistryOutcome.ALIAS_TARGET_UNKNOWN,
        )
        self.assert_build_rejected(
            build(aliases=(("reader", "another-alias"),)),
            _AgentOperationToolRegistryOutcome.ALIAS_INVALID,
        )
        self.assert_build_rejected(
            build(aliases=((TOOL_ID, target),)),
            _AgentOperationToolRegistryOutcome.ALIAS_INVALID,
        )

    def test_retirement_blocks_new_direct_and_alias_selection_only(self) -> None:
        target = route()
        snapshot = built_snapshot(
            aliases=(("reader", target),),
            retired_routes=(target,),
        )
        self.assert_selection_rejected(
            _select_agent_operation_tool_route(snapshot, route=target),
            _AgentOperationToolRegistryOutcome.TOOL_RETIRED,
        )
        self.assert_selection_rejected(
            _select_agent_operation_tool_route(snapshot, alias="reader"),
            _AgentOperationToolRegistryOutcome.TOOL_RETIRED,
        )
        outcome, resolved = _resolve_agent_operation_tool_registration(
            snapshot,
            target,
        )
        self.assertIs(outcome, _AgentOperationToolRegistryOutcome.RESOLVED)
        self.assertIs(type(resolved), _ResolvedAgentOperationToolRegistration)
        self.assertEqual(resolved.registration, registration())  # type: ignore[union-attr]

    def test_unknown_retirement_and_duplicate_retirement_fail_closed(self) -> None:
        target = route()
        self.assert_build_rejected(
            build(retired_routes=(route("runtime::unknown"),)),
            _AgentOperationToolRegistryOutcome.UNKNOWN_ROUTE,
        )
        self.assert_build_rejected(
            build(retired_routes=(target, target)),
            _AgentOperationToolRegistryOutcome.REGISTRY_INVALID,
        )


class RegistryHistoryAndIntegrityTests(RegistryFixture):
    def test_restart_and_declaration_order_have_identical_fingerprint(self) -> None:
        old = registration()
        added = registration(
            runtime_option_id="runtime::next",
            environment_id="environment::next",
            tool_id="tool::synthetic-reader::v2",
        )
        first = built_snapshot((old, added))
        restarted = built_snapshot((added, old))
        self.assertEqual(
            first._registration_fingerprint,
            restarted._registration_fingerprint,
        )
        self.assertEqual(first._registrations, restarted._registrations)
        accepted = build(
            (added, old),
            expected_fingerprint=first._registration_fingerprint,
        )
        self.assertIs(
            accepted.outcome,
            _AgentOperationToolRegistryOutcome.RESOLVED,
        )
        self.assert_build_rejected(
            build((old, added), expected_fingerprint="sha256:not-the-set"),
            _AgentOperationToolRegistryOutcome.FINGERPRINT_MISMATCH,
        )

    def test_append_only_upgrade_preserves_old_lookup_and_allows_new_route(
        self,
    ) -> None:
        old_registration = registration()
        old_snapshot = built_snapshot(
            (old_registration,),
            aliases=(("reader-current", route()),),
        )
        new_registration = registration(
            runtime_option_id="runtime::next",
            environment_id="environment::next",
            tool_id="tool::synthetic-reader::v2",
        )
        new_route = route("runtime::next", "environment::next")
        upgraded = build(
            (new_registration, old_registration),
            aliases=(("reader-current", new_route),),
            prior_snapshot=old_snapshot,
        )
        self.assertIs(
            upgraded.outcome,
            _AgentOperationToolRegistryOutcome.RESOLVED,
        )
        assert upgraded.snapshot is not None
        old_outcome, old_resolved = _resolve_agent_operation_tool_registration(
            upgraded.snapshot,
            route(),
        )
        new_outcome, new_resolved = _resolve_agent_operation_tool_registration(
            upgraded.snapshot,
            new_route,
        )
        self.assertIs(old_outcome, _AgentOperationToolRegistryOutcome.RESOLVED)
        self.assertIs(new_outcome, _AgentOperationToolRegistryOutcome.RESOLVED)
        self.assertEqual(old_resolved.registration, old_registration)  # type: ignore[union-attr]
        self.assertEqual(new_resolved.registration, new_registration)  # type: ignore[union-attr]
        selected = _select_agent_operation_tool_route(
            upgraded.snapshot,
            alias="reader-current",
        )
        self.assertEqual(selected.selected_route.route, new_route)  # type: ignore[union-attr]

    def test_prior_snapshot_detects_deletion_rebind_and_retirement_reactivation(
        self,
    ) -> None:
        old_registration = registration()
        additional = registration(
            runtime_option_id="runtime::additional",
            environment_id="environment::additional",
            tool_id="tool::additional::v1",
        )
        old_snapshot = built_snapshot((old_registration, additional))
        self.assert_build_rejected(
            build((additional,), prior_snapshot=old_snapshot),
            _AgentOperationToolRegistryOutcome.HISTORICAL_MAPPING_MISSING,
        )
        self.assert_build_rejected(
            build(
                (
                    registration(tool_id="tool::rebound::v2"),
                    additional,
                ),
                prior_snapshot=old_snapshot,
            ),
            _AgentOperationToolRegistryOutcome.TOOL_ID_REBIND,
        )

        retired_old = built_snapshot(
            (old_registration,),
            retired_routes=(route(),),
        )
        self.assert_build_rejected(
            build((old_registration,), prior_snapshot=retired_old),
            _AgentOperationToolRegistryOutcome.INTEGRITY_FAILURE,
        )
        retained_retirement = build(
            (old_registration,),
            retired_routes=(route(),),
            prior_snapshot=retired_old,
        )
        self.assertIs(
            retained_retirement.outcome,
            _AgentOperationToolRegistryOutcome.RESOLVED,
        )

    def test_missing_historical_route_never_falls_back(self) -> None:
        snapshot = built_snapshot()
        missing = route("runtime::missing", "environment::missing")
        outcome, resolved = _resolve_agent_operation_tool_registration(
            snapshot,
            missing,
        )
        self.assertIs(
            outcome,
            _AgentOperationToolRegistryOutcome.HISTORICAL_MAPPING_MISSING,
        )
        self.assertIsNone(resolved)
        selection = _select_agent_operation_tool_route(snapshot, route=missing)
        self.assert_selection_rejected(
            selection,
            _AgentOperationToolRegistryOutcome.UNKNOWN_ROUTE,
        )

    def test_exact_route_validation_is_case_sensitive_and_never_normalized(
        self,
    ) -> None:
        snapshot = built_snapshot()
        for changed, expected in (
            (
                route(runtime_option_id="RUNTIME::synthetic"),
                _AgentOperationToolRegistryOutcome.RUNTIME_MISMATCH,
            ),
            (
                route(environment_id="ENVIRONMENT::synthetic"),
                _AgentOperationToolRegistryOutcome.ENVIRONMENT_MISMATCH,
            ),
            (
                route(operation_id="Repository_File_Read"),
                _AgentOperationToolRegistryOutcome.OPERATION_MISMATCH,
            ),
            (
                route(runtime_option_id=""),
                _AgentOperationToolRegistryOutcome.RUNTIME_MISMATCH,
            ),
            (
                route(environment_id=""),
                _AgentOperationToolRegistryOutcome.ENVIRONMENT_MISMATCH,
            ),
        ):
            with self.subTest(route=changed):
                result = _select_agent_operation_tool_route(
                    snapshot,
                    route=changed,
                )
                self.assert_selection_rejected(result, expected)

    def test_integrity_corruption_and_fingerprint_mismatch_fail_closed(self) -> None:
        snapshot = built_snapshot()
        object.__setattr__(
            snapshot,
            "_registration_fingerprint",
            "sha256:corrupted",
        )
        outcome, resolved = _resolve_agent_operation_tool_registration(
            snapshot,
            route(),
        )
        self.assertIs(
            outcome,
            _AgentOperationToolRegistryOutcome.FINGERPRINT_MISMATCH,
        )
        self.assertIsNone(resolved)

        missing_tool_index = built_snapshot()
        object.__setattr__(
            missing_tool_index,
            "_registrations_by_scoped_tool_id",
            MappingProxyType({}),
        )
        outcome, resolved = _resolve_agent_operation_tool_registration(
            missing_tool_index,
            route(),
        )
        self.assertIs(outcome, _AgentOperationToolRegistryOutcome.UNKNOWN_TOOL)
        self.assertIsNone(resolved)

    def test_audit_is_closed_nonsecret_and_never_a_catalog_or_authority(self) -> None:
        snapshot = built_snapshot(aliases=(("reader", route()),))
        selected = _select_agent_operation_tool_route(
            snapshot,
            alias="reader",
        )
        audit = selected.audit
        self.assertEqual(
            [item.name for item in fields(audit)],
            [
                "outcome",
                "retry_disposition",
                "run_id",
                "route",
                "tool_id",
                "implementation_id",
                "snapshot_fingerprint",
            ],
        )
        self.assertEqual(
            audit.implementation_id,
            "trusted-agent-operation-tool-binding-resolver::v1",
        )
        prohibited = {
            "registrations",
            "aliases",
            "selector",
            "resource",
            "path",
            "command",
            "endpoint",
            "credential",
            "secret",
            "exception",
            "stack_trace",
            "authority",
        }
        self.assertTrue(prohibited.isdisjoint({item.name for item in fields(audit)}))
        self.assertNotIn("reader", repr(snapshot))
        self.assertNotIn(TOOL_ID, repr(snapshot))


class RegistrySafetyTests(RegistryFixture):
    def test_module_has_no_io_discovery_persistence_or_execution_calls(self) -> None:
        tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
        imported_roots: set[str] = set()
        called_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(
                    item.name.split(".", 1)[0] for item in node.names
                )
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".", 1)[0])
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called_names.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    called_names.add(node.func.attr)

        self.assertTrue(
            imported_roots.isdisjoint(
                {
                    "glob",
                    "importlib",
                    "os",
                    "pathlib",
                    "socket",
                    "sqlite3",
                    "subprocess",
                    "urllib",
                }
            )
        )
        self.assertTrue(
            called_names.isdisjoint(
                {
                    "open",
                    "read_text",
                    "read_bytes",
                    "write_text",
                    "write_bytes",
                    "resolve",
                    "stat",
                    "listdir",
                    "scandir",
                    "getenv",
                    "system",
                    "Popen",
                    "connect",
                    "urlopen",
                    "discover",
                    "probe",
                    "rank",
                    "fallback",
                    "persist",
                    "dispatch",
                    "execute",
                    "invoke",
                }
            )
        )

    def test_registry_values_contain_no_callable_secret_or_resource_fields(
        self,
    ) -> None:
        snapshot = built_snapshot()
        values = (
            registration(),
            snapshot._registrations,
            snapshot._aliases,
            snapshot._retired_routes,
            snapshot._registrations_by_route,
            snapshot._registrations_by_scoped_tool_id,
        )
        self.assertFalse(any(callable(item) for item in values))
        field_names = {
            item.name for item in fields(_AgentOperationToolRegistration)
        }
        self.assertTrue(
            {
                "resource",
                "callable",
                "adapter",
                "endpoint",
                "command",
                "credential",
                "secret",
                "availability",
                "health",
            }.isdisjoint(field_names)
        )


if __name__ == "__main__":
    unittest.main()
