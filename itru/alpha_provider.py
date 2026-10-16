"""Advisory text planning only. A Provider can never select or invoke Tools."""
from __future__ import annotations

import ipaddress
import json
import os
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler


class ProviderError(RuntimeError):
    pass


def validate_endpoint(endpoint):
    try:
        url = urlsplit(endpoint)
        local = url.hostname == 'localhost'
        if not local:
            try:
                local = ipaddress.ip_address(url.hostname or '').is_loopback
            except ValueError:
                local = False
        if (url.scheme not in ('http', 'https') or not url.hostname
                or url.username or url.password or url.fragment or url.query
                or url.scheme == 'http' and not local):
            raise ValueError('provider requires HTTPS or loopback HTTP, without embedded credentials/query')
        _ = url.port
    except (TypeError, ValueError) as exc:
        raise ValueError('invalid provider endpoint') from exc


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ProviderError('provider redirects are disabled')


def plan_task(provider, task):
    if provider['kind'] == 'demo':
        return '[offline demo; no model inference] Read the approved resource: ' + task['resource']
    validate_endpoint(provider['endpoint'])
    key = os.environ.get(provider['key_env']) if provider['key_env'] else None
    if provider['key_env'] and not key:
        raise ProviderError('configured credential environment variable is missing')
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
        if len(raw) > 65536:
            raise ProviderError('provider response exceeds 64 KiB')
        obj = json.loads(raw)
        message = obj['choices'][0]['message']
        value = message['content']
        if (message.get('tool_calls') or message.get('function_call')
                or type(value) is not str or not value.strip() or len(value) > 16384):
            raise ProviderError('provider must return bounded advisory text only')
        return value
    except ProviderError:
        raise
    except Exception:
        # Never emit HTTP exception bodies, credentials or transport diagnostics.
        raise ProviderError('provider request failed; no Tool was invoked') from None
