"""Focused deterministic and AIO-047 integration tests for AIO-051."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from inspect import signature
import unittest
from unittest.mock import patch

import engineering_orchestration
import engineering_orchestration.agent_operation_tool_resolver as subject
from engineering_orchestration.agent_execution_authorization_grant import (
    AgentExecutionAuthorizationGrant,
)
from engineering_orchestration.agent_execution_contract import (
    AgentExecutionContract,
)
from engineering_orchestration.agent_execution_dispatch_admission_store import (
    AgentExecutionDispatchAdmissionCoordinator,
    AgentExecutionDispatchAdmissionStoreOutcome,
)
from engineering_orchestration.agent_execution_run import AgentExecutionRun
from engineering_orchestration.agent_operation_tool_binding import (
    AgentOperationToolBinding,
)
from engineering_orchestration.agent_operation_tool_registry import (
    _AEO_NATIVE_REPOSITORY_FILE_READ_TOOL_ID,
    _AgentOperationToolImplementationSelector,
    _AgentOperationToolRegistration,
    _AgentOperationToolRegistryOutcome,
    _AgentOperationToolRegistryRetryDisposition,
    _AgentOperationToolRoute,
    _build_trusted_agent_operation_tool_registry_snapshot,
    _make_aeo_native_repository_file_read_registration,
)
from engineering_orchestration.agent_operation_tool_resolver import (
    TrustedAgentOperationToolBindingResolver,
)


RUNTIME_OPTION_ID = "runtime::synthetic"
ENVIRONMENT_ID = "environment::synthetic"
OPERATION_ID = "repository_file_read"
RESOURCE = "synthetic/input.txt"
TOOL_ID = _AEO_NATIVE_REPOSITORY_FILE_READ_TOOL_ID


def make_run(
    *,
    run_id: str = "run::synthetic",
    runtime_option_id: str = RUNTIME_OPTION_ID,
    environment_id: str = ENVIRONMENT_ID,
    operation_id: str = OPERATION_ID,
    resource: str = RESOURCE,
) -> AgentExecutionRun:
    return AgentExecutionRun(
        run_id=run_id,
        contract=AgentExecutionContract(
            task_id="AIO-051",
            workflow_id="architecture-change",
            stage_id="implement",
            role_id="software-engineer",
            actor_id="actor::synthetic",
            runtime_option_id=runtime_option_id,
            option_id="inference::synthetic",
            environment_id=environment_id,
            operation_id=operation_id,
            resource=resource,
            execution_mode="critical",
        ),
    )


def make_grant(
    *,
    run: AgentExecutionRun | None = None,
    grant_id: str = "grant::synthetic",
) -> AgentExecutionAuthorizationGrant:
    return AgentExecutionAuthorizationGrant(
        grant_id=grant_id,
        run=run or make_run(),
        authorization_domain_id="authorization-domain::synthetic",
        issuer_kind="policy",
        issuer_id="issuer::synthetic",
        provenance_reference="provenance::synthetic",
        issued_at="2026-01-01T00:00:00Z",
        expires_at="2027-01-01T00:00:00Z",
    )


def make_registration(
    *,
    runtime_option_id: str = RUNTIME_OPTION_ID,
    environment_id: str = ENVIRONMENT_ID,
    tool_id: str = TOOL_ID,
) -> _AgentOperationToolRegistration:
    return _AgentOperationToolRegistration(
        runtime_option_id=runtime_option_id,
        environment_id=environment_id,
        operation_id=OPERATION_ID,
        tool_id=tool_id,
        implementation_selector=(
            _AgentOperationToolImplementationSelector.
            AEO_NATIVE_REPOSITORY_FILE_READ_V1
        ),
    )


def build_snapshot(
    registrations: tuple[_AgentOperationToolRegistration, ...],
    *,
    aliases: tuple[tuple[str, _AgentOperationToolRoute], ...] = (),
    retired_routes: tuple[_AgentOperationToolRoute, ...] = (),
    prior_snapshot: object | None = None,
):
    result = _build_trusted_agent_operation_tool_registry_snapshot(
        registrations,
        aliases=aliases,
        retired_routes=retired_routes,
        prior_snapshot=prior_snapshot,  # type: ignore[arg-type]
    )
    if (
        result.outcome is not _AgentOperationToolRegistryOutcome.RESOLVED
        or result.snapshot is None
    ):
        raise AssertionError(f"synthetic snapshot failed: {result.outcome}")
    return result.snapshot


class TrustedAgentOperationToolBindingResolverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registration = (
            _make_aeo_native_repository_file_read_registration(
                RUNTIME_OPTION_ID,
                ENVIRONMENT_ID,
            )
        )
        self.route = _AgentOperationToolRoute(
            RUNTIME_OPTION_ID,
            ENVIRONMENT_ID,
            OPERATION_ID,
        )
        self.snapshot = build_snapshot((self.registration,))
        self.resolver = TrustedAgentOperationToolBindingResolver(self.snapshot)

    def test_direct_module_api_result_shape_and_frozen_resolver(self) -> None:
        self.assertEqual(
            subject.__all__,
            ("TrustedAgentOperationToolBindingResolver",),
        )
        self.assertFalse(
            hasattr(
                engineering_orchestration,
                "TrustedAgentOperationToolBindingResolver",
            )
        )
        self.assertEqual(
            tuple(
                signature(
                    TrustedAgentOperationToolBindingResolver.
                    resolve_tool_binding
                ).parameters
            ),
            ("self", "grant"),
        )
        self.assertEqual(
            [
                item.name
                for item in fields(subject._AgentOperationToolResolutionResult)
            ],
            [
                "outcome",
                "retry_disposition",
                "resolved_registration",
                "binding",
                "audit",
            ],
        )
        result = self.resolver.resolve(make_grant())
        with self.assertRaises(FrozenInstanceError):
            result.binding = None  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            self.resolver._snapshot = self.snapshot  # type: ignore[misc]
        with self.assertRaises(TypeError):
            TrustedAgentOperationToolBindingResolver(object())

    def test_known_exact_route_constructs_canonical_binding(self) -> None:
        grant = make_grant()
        result = self.resolver.resolve(grant)

        self.assertIs(
            result.outcome,
            _AgentOperationToolRegistryOutcome.RESOLVED,
        )
        self.assertIs(
            result.retry_disposition,
            _AgentOperationToolRegistryRetryDisposition.NO_RETRY_NEEDED,
        )
        self.assertIs(type(result.binding), AgentOperationToolBinding)
        self.assertIs(result.binding.run, grant.run)
        self.assertEqual(result.binding.run, grant.run)
        self.assertIs(result.binding.run.contract, grant.run.contract)
        self.assertEqual(result.binding.tool_id, TOOL_ID)
        self.assertEqual(
            [item.name for item in fields(result.binding)],
            ["run", "tool_id"],
        )
        self.assertIs(
            self.resolver.resolve_tool_binding(grant).run,
            grant.run,
        )

        self.assertIs(result.audit.outcome, result.outcome)
        self.assertIs(
            result.audit.retry_disposition,
            result.retry_disposition,
        )
        self.assertEqual(result.audit.run_id, grant.run.run_id)
        self.assertEqual(result.audit.route, self.route)
        self.assertEqual(result.audit.tool_id, TOOL_ID)
        self.assertEqual(
            result.audit.implementation_id,
            "trusted-agent-operation-tool-binding-resolver::v1",
        )
        self.assertFalse(hasattr(result.audit, "resource"))
        self.assertFalse(hasattr(result.audit, "registration_catalog"))
        self.assertFalse(hasattr(result.audit, "implementation_selector"))

    def test_invalid_grant_type_and_intrinsic_value_fail_before_lookup(
        self,
    ) -> None:
        invalid = replace(make_grant(), grant_id="")
        with patch.object(
            subject,
            "_resolve_agent_operation_tool_registration",
            side_effect=AssertionError("registry lookup occurred"),
        ) as lookup:
            wrong_type = self.resolver.resolve(object())
            malformed = self.resolver.resolve(invalid)

        self.assertEqual(lookup.call_count, 0)
        for result in (wrong_type, malformed):
            self.assertIs(
                result.outcome,
                _AgentOperationToolRegistryOutcome.INTEGRITY_FAILURE,
            )
            self.assertIsNone(result.resolved_registration)
            self.assertIsNone(result.binding)
        self.assertIsNone(self.resolver.resolve_tool_binding(object()))
        self.assertIsNone(self.resolver.resolve_tool_binding(invalid))

    def test_unknown_runtime_environment_and_wrong_operation_fail_closed(
        self,
    ) -> None:
        cases = (
            make_grant(
                run=make_run(runtime_option_id="runtime::unknown")
            ),
            make_grant(
                run=make_run(environment_id="environment::unknown")
            ),
        )
        for grant in cases:
            with self.subTest(contract=grant.run.contract):
                result = self.resolver.resolve(grant)
                self.assertIs(
                    result.outcome,
                    _AgentOperationToolRegistryOutcome.
                    HISTORICAL_MAPPING_MISSING,
                )
                self.assertIs(
                    result.retry_disposition,
                    _AgentOperationToolRegistryRetryDisposition.
                    HISTORICAL_MAPPING_REMEDIATION_REQUIRED,
                )
                self.assertIsNone(result.binding)
                self.assertIsNone(self.resolver.resolve_tool_binding(grant))

        wrong_operation = make_grant(
            run=make_run(operation_id="repository_file_write")
        )
        operation_result = self.resolver.resolve(wrong_operation)
        self.assertIs(
            operation_result.outcome,
            _AgentOperationToolRegistryOutcome.INTEGRITY_FAILURE,
        )
        self.assertIsNone(operation_result.binding)
        self.assertIsNone(
            self.resolver.resolve_tool_binding(wrong_operation)
        )

    def test_exact_run_resource_and_all_contract_scope_are_preserved(self) -> None:
        resources = (
            "synthetic/input.txt",
            "synthetic/nested/other.txt",
        )
        for index, resource in enumerate(resources):
            with self.subTest(resource=resource):
                grant = make_grant(
                    run=make_run(
                        run_id=f"run::resource-{index}",
                        resource=resource,
                    ),
                    grant_id=f"grant::resource-{index}",
                )
                binding = self.resolver.resolve_tool_binding(grant)
                self.assertIsNotNone(binding)
                assert binding is not None
                self.assertIs(binding.run, grant.run)
                self.assertIs(binding.run.contract, grant.run.contract)
                self.assertEqual(binding.run.contract.resource, resource)
                self.assertEqual(
                    binding.run.contract.runtime_option_id,
                    RUNTIME_OPTION_ID,
                )
                self.assertEqual(
                    binding.run.contract.environment_id,
                    ENVIRONMENT_ID,
                )
                self.assertEqual(
                    binding.run.contract.operation_id,
                    OPERATION_ID,
                )
                self.assertEqual(binding.run.contract.execution_mode, "critical")

    def test_restart_rebuild_reproduces_same_historical_binding(self) -> None:
        grant = make_grant()
        first = self.resolver.resolve_tool_binding(grant)
        rebuilt_snapshot = build_snapshot(
            (
                _make_aeo_native_repository_file_read_registration(
                    RUNTIME_OPTION_ID,
                    ENVIRONMENT_ID,
                ),
            )
        )
        restarted = TrustedAgentOperationToolBindingResolver(rebuilt_snapshot)
        second = restarted.resolve_tool_binding(grant)

        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        self.assertEqual(first, second)
        self.assertIs(first.run, grant.run)
        self.assertIs(second.run, grant.run)

    def test_append_only_upgrade_preserves_old_and_resolves_new_route(self) -> None:
        old_grant = make_grant()
        old_binding = self.resolver.resolve_tool_binding(old_grant)
        new_registration = make_registration(
            runtime_option_id="runtime::synthetic-v2",
            tool_id="tool::aeo-native-repository-file-read::v2",
        )
        upgraded_snapshot = build_snapshot(
            (self.registration, new_registration),
            prior_snapshot=self.snapshot,
        )
        upgraded = TrustedAgentOperationToolBindingResolver(upgraded_snapshot)

        self.assertEqual(
            upgraded.resolve_tool_binding(old_grant),
            old_binding,
        )
        new_grant = make_grant(
            run=make_run(
                run_id="run::synthetic-v2",
                runtime_option_id="runtime::synthetic-v2",
            ),
            grant_id="grant::synthetic-v2",
        )
        new_binding = upgraded.resolve_tool_binding(new_grant)
        self.assertIsNotNone(new_binding)
        assert new_binding is not None
        self.assertIs(new_binding.run, new_grant.run)
        self.assertEqual(
            new_binding.tool_id,
            "tool::aeo-native-repository-file-read::v2",
        )
        self.assertNotEqual(new_binding, old_binding)

    def test_retired_registration_remains_total_for_historical_resolution(
        self,
    ) -> None:
        retired_snapshot = build_snapshot(
            (self.registration,),
            retired_routes=(self.route,),
        )
        retired_resolver = TrustedAgentOperationToolBindingResolver(
            retired_snapshot
        )
        grant = make_grant()
        binding = retired_resolver.resolve_tool_binding(grant)

        self.assertIsNotNone(binding)
        assert binding is not None
        self.assertIs(binding.run, grant.run)
        self.assertEqual(binding.tool_id, TOOL_ID)
        self.assertIs(
            retired_resolver.resolve(grant).outcome,
            _AgentOperationToolRegistryOutcome.RESOLVED,
        )

    def test_missing_history_and_alias_cannot_remap_or_fallback(self) -> None:
        alternate_route = _AgentOperationToolRoute(
            "runtime::alternate",
            "environment::alternate",
            OPERATION_ID,
        )
        alternate = make_registration(
            runtime_option_id=alternate_route.runtime_option_id,
            environment_id=alternate_route.environment_id,
            tool_id="tool::alternate::v1",
        )
        snapshot = build_snapshot(
            (alternate,),
            aliases=(("reader", alternate_route),),
        )
        resolver = TrustedAgentOperationToolBindingResolver(snapshot)
        grant = make_grant()
        result = resolver.resolve(grant)

        self.assertIs(
            result.outcome,
            _AgentOperationToolRegistryOutcome.HISTORICAL_MAPPING_MISSING,
        )
        self.assertIsNone(result.resolved_registration)
        self.assertIsNone(result.binding)
        self.assertIsNone(result.audit.tool_id)
        self.assertEqual(result.audit.route, self.route)
        self.assertIsNone(resolver.resolve_tool_binding(grant))

    def test_ordinary_exceptions_fail_closed_but_base_exceptions_propagate(
        self,
    ) -> None:
        grant = make_grant()
        with patch.object(
            subject,
            "_resolve_agent_operation_tool_registration",
            side_effect=RuntimeError("synthetic failure"),
        ):
            result = self.resolver.resolve(grant)
            self.assertIs(
                result.outcome,
                _AgentOperationToolRegistryOutcome.INTEGRITY_FAILURE,
            )
            self.assertIsNone(result.binding)
            self.assertIsNone(self.resolver.resolve_tool_binding(grant))

        for exception in (KeyboardInterrupt(), SystemExit()):
            with self.subTest(exception=type(exception).__name__), patch.object(
                subject,
                "_resolve_agent_operation_tool_registration",
                side_effect=exception,
            ):
                with self.assertRaises(type(exception)):
                    self.resolver.resolve_tool_binding(grant)

    def test_aio_047_coordinator_consumes_only_the_configured_port_result(
        self,
    ) -> None:
        coordinator = AgentExecutionDispatchAdmissionCoordinator(
            authorization_domain_id="authorization-domain::synthetic",
            store=object(),  # type: ignore[arg-type]
            grant_authentication=object(),  # type: ignore[arg-type]
            tool_binding_resolver=self.resolver,
            fresh_prerequisite_source=object(),  # type: ignore[arg-type]
            execution_mode_resolver=object(),  # type: ignore[arg-type]
            revocation_authentication=object(),  # type: ignore[arg-type]
        )
        grant = make_grant()
        binding, rejection = coordinator._resolve_binding(grant)
        self.assertIsNone(rejection)
        self.assertIs(type(binding), AgentOperationToolBinding)
        self.assertIs(binding.run, grant.run)

        unknown = make_grant(
            run=make_run(runtime_option_id="runtime::unknown")
        )
        missing, rejection = coordinator._resolve_binding(unknown)
        self.assertIsNone(missing)
        self.assertIsNotNone(rejection)
        assert rejection is not None
        self.assertIs(
            rejection.outcome,
            AgentExecutionDispatchAdmissionStoreOutcome.
            UNTRUSTED_TOOL_BINDING,
        )
        self.assertFalse(hasattr(self.resolver, "dispatch"))
        self.assertFalse(hasattr(self.resolver, "invoke"))
        self.assertFalse(hasattr(self.resolver, "discover"))
        self.assertFalse(hasattr(self.resolver, "fallback"))


if __name__ == "__main__":
    unittest.main()
