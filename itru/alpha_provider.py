"""Advisory text planning only. A Provider can never select or invoke Tools."""
from __future__ import annotations

import ipaddress
import json
import os
import re
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler

from itru.alpha_diagnostics import AlphaDiagnosticError, diagnostic

PROVIDER_KEYS = {'kind', 'endpoint', 'model', 'key_env', 'timeout_seconds'}


class ProviderError(AlphaDiagnosticError, RuntimeError):
    def __init__(self, code='provider_request_failed'):
        super().__init__(code if type(code) is str and code in (
            'provider_config_missing', 'provider_unsupported', 'provider_config_invalid',
            'provider_credential_missing', 'provider_request_failed',
            'provider_response_rejected', 'provider_redirect_rejected') else 'provider_request_failed')


def provider_diagnostic(exc):
    code = getattr(exc, 'code', None) if isinstance(exc, ProviderError) else None
    return diagnostic(ProviderError(code).code)


def validate_endpoint(endpoint):
    try:
        if (type(endpoint) is not str or not endpoint
                or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in endpoint)):
            raise ValueError('invalid provider endpoint')
        url = urlsplit(endpoint)
        local = url.hostname == 'localhost'
        if not local:
            try:
                local = ipaddress.ip_address(url.hostname or '').is_loopback
            except ValueError:
                local = False
        if (url.scheme not in ('http', 'https') or not url.hostname
                or url.username is not None or url.password is not None or url.fragment or url.query
                or url.scheme == 'http' and not local):
            raise ValueError('provider requires HTTPS or loopback HTTP, without embedded credentials/query')
        _ = url.port
    except (TypeError, ValueError) as exc:
        raise ValueError('invalid provider endpoint') from exc


def validate_provider(provider):
    if type(provider) is not dict or not PROVIDER_KEYS <= set(provider):
        raise ProviderError('provider_config_missing')
    if set(provider) != PROVIDER_KEYS:
        raise ProviderError('provider_config_invalid')
    if type(provider['kind']) is not str or provider['kind'] not in ('demo', 'compatible'):
        raise ProviderError('provider_unsupported')
    model = provider['model']
    if (type(model) is not str or not model.strip() or len(model) > 4096
            or any(ord(c) < 32 for c in model)
            or type(provider['endpoint']) is not str or type(provider['key_env']) is not str
            or provider['key_env'] and not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', provider['key_env'])
            or type(provider['timeout_seconds']) is not int
            or not 1 <= provider['timeout_seconds'] <= 120):
        raise ProviderError('provider_config_invalid')
    if provider['kind'] == 'compatible':
        try:
            validate_endpoint(provider['endpoint'])
        except ValueError:
            raise ProviderError('provider_config_invalid') from None


def check_credential(provider):
    if provider['kind'] == 'demo':
        return 'not_required'
    if not provider['key_env']:
        return 'not_configured'
    if not os.environ.get(provider['key_env']):
        raise ProviderError('provider_credential_missing')
    return 'present_not_verified'


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ProviderError('provider_redirect_rejected')


def plan_task(provider, task):
    if provider['kind'] == 'demo':
        return '[offline demo; no model inference] Read the approved resource: ' + task['resource']
    validate_provider(provider)
    check_credential(provider)
    key = os.environ.get(provider['key_env']) if provider['key_env'] else None
    body = json.dumps({'model': provider['model'], 'messages': [
        {'role': 'system', 'content': 'Provide a short advisory plan for the exact read task. You have no tools or execution authority.'},
        {'role': 'user', 'content': json.dumps({'objective': task['objective'], 'resource': task['resource']})}],
        'stream': False}).encode('utf-8')
    headers = {'Content-Type': 'application/json'}
    if key:
        headers['Authorization'] = 'Bearer ' + key
    try:
        opener = build_opener(ProxyHandler({}), _NoRedirect())
        with opener.open(Request(provider['endpoint'], data=body, headers=headers),
                         timeout=provider['timeout_seconds']) as response:
            raw = response.read(65537)
    except ProviderError:
        raise
    except Exception:
        # Never emit HTTP exception bodies, credentials or transport diagnostics.
        raise ProviderError('provider_request_failed') from None
    try:
        if len(raw) > 65536:
            raise ProviderError('provider_response_rejected')
        obj = json.loads(raw)
        message = obj['choices'][0]['message']
        value = message['content']
        if (message.get('tool_calls') or message.get('function_call')
                or type(value) is not str or not value.strip() or len(value) > 16384):
            raise ProviderError('provider_response_rejected')
        return value
    except ProviderError:
        raise
    except Exception:
        raise ProviderError('provider_response_rejected') from None
