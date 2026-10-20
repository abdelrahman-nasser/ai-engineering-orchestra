"""Fixed CLI-only Alpha diagnostics. Never render caller or exception text."""
from __future__ import annotations


_MESSAGES = {
    'alpha_arguments_invalid': (
        'Alpha command arguments are invalid; argument values are withheld.',
        'Check alpha --help and alpha <command> --help for supported arguments. Never put credential values on the command line.'),
    'config_missing': (
        'Alpha configuration file was not found.',
        'Check --config points to the existing workspace/alpha.json. For a first run, follow docs/developer-alpha-first-run.md; do not rerun init over an existing path.'),
    'config_unreadable': (
        'Alpha configuration could not be read safely.',
        'Inspect the private local file, permissions and plain-directory path with its Human owner. Do not relocate storage or bypass path/security checks.'),
    'config_invalid': (
        'Alpha configuration is invalid.',
        'Check the closed format_version 1 configuration in docs/developer-alpha.md. Keep generated workspace and identity fields unchanged; no input values are displayed.'),
    'provider_config_missing': (
        'Provider configuration is missing or incomplete.',
        'Supply all five provider fields: kind, endpoint, model, key_env and timeout_seconds. See docs/developer-alpha.md; never put a credential value in JSON.'),
    'provider_unsupported': (
        'Provider selection is unsupported.',
        'Use kind demo for labelled offline planning or compatible for the documented chat adapter. No adapter is selected automatically.'),
    'provider_config_invalid': (
        'Provider configuration is invalid.',
        'Check the five provider fields: nonempty bounded model, HTTPS or loopback HTTP endpoint without credentials/query/fragment, environment-variable name or empty key_env, and integer timeout_seconds 1..120. See docs/developer-alpha.md.'),
    'provider_credential_missing': (
        'The configured credential environment variable is missing or empty.',
        'Supply it privately in this process environment, then rerun alpha diagnose. Do not paste credential values into commands, JSON or reports. Empty key_env is only for an intentionally credential-free endpoint.'),
    'provider_request_failed': (
        'Provider request failed before the Tool was invoked; the remote cause is unknown.',
        'Check private provider setup and service availability separately. Local diagnostics cannot test connectivity, credentials or remote authorization. Inspect history deliberately; only eligible continuation may use a fresh resume plan and explicit Human approval. No automatic retry.'),
    'provider_response_rejected': (
        'Provider response was rejected; bounded advisory text only is supported.',
        'Check adapter/protocol compatibility privately. Responses must contain bounded nonempty chat text without tool/function calls. Inspect history before any separately approved eligible resume; no automatic retry.'),
    'provider_redirect_rejected': (
        'Provider redirect was rejected before the Tool was invoked.',
        'Configure the intended final HTTPS or loopback endpoint directly. Inspect history and obtain a fresh plan and Human approval before any eligible continuation.'),
    'human_approval_required': (
        'fresh exact Human approval required; inspect alpha plan and pass its digest with --approve',
        'Review the current plan and exact selected subjects. Only the Human may approve that digest. Config, work or lifecycle changes require a new plan; provider credentials never supply Human approval.'),
    'alpha_owner_busy': (
        'The lifecycle Store is already owned by another process.',
        'Coordinate with its Human operator. Do not seize ownership; stop cannot acquire another process owner. Diagnostics do not prove owner availability.'),
    'alpha_commit_uncertain': (
        'The lifecycle commit outcome is uncertain.',
        'Stop for Human inspection; deliberately query history without repeating the operation. Missing Result evidence never proves no effect. Do not retry automatically.'),
    'alpha_operation_failed': (
        'Alpha operation failed; private error details are withheld.',
        'Stop and inspect local state with the Human owner. Partial setup or execution may have effects: do not rerun init, delete storage or retry automatically. See docs/developer-alpha-first-run.md. alpha diagnose checks configuration only; history opens the lifecycle owner and can perform startup recovery.'),
}


class AlphaDiagnosticError(ValueError):
    def __init__(self, code):
        self.code = code if type(code) is str and code in _MESSAGES else 'alpha_operation_failed'
        super().__init__(_MESSAGES[self.code][0])


def diagnostic(code):
    # Only catalogue text may cross the CLI boundary, even for an unknown code.
    if type(code) is not str or code not in _MESSAGES:
        code = 'alpha_operation_failed'
    reason, recovery = _MESSAGES[code]
    return {'code': code, 'reason': reason, 'recovery': recovery}


def exception_diagnostic(exc):
    from itru.sqlite_task_run_state import StateStoreBusyError, StateCommitUnknownError
    if isinstance(exc, StateStoreBusyError):
        return diagnostic('alpha_owner_busy')
    if isinstance(exc, StateCommitUnknownError):
        return diagnostic('alpha_commit_uncertain')
    return diagnostic(exc.code if isinstance(exc, AlphaDiagnosticError) else None)
