"""Minimal Codex lifecycle-hook observer for the AIO Control Center.

This file intentionally depends only on the Python standard library.  It never
logs or persists hook input.  A bounded, freshly constructed allowlist record
is sent only to authenticated collectors whose live descriptors match the
event working directory.
"""

from __future__ import annotations

import base64
import datetime as _datetime
import hashlib
import hmac
import json
import os
import secrets
import socket
import stat
import struct
import sys
import time
import uuid
from typing import Any, Iterable


SOURCE_ID = "codex.lifecycle-hooks/v1"
WIRE_PROTOCOL = "aio.codex-monitor/1"
REGISTRY_PROTOCOL = "aio.codex-monitor-registry/1"
FIXED_OWNER = "aio-control-center-dev/v1"

SUPPORTED_EVENTS = frozenset(
    {
        "SessionStart",
        "SessionEnd",
        "SubagentStart",
        "SubagentStop",
        "PostToolUse",
        "PostCompact",
        "Stop",
        "Interrupt",
    }
)
EMPTY_OUTPUT_EVENTS = frozenset({"SessionEnd", "Interrupt"})

MAX_INPUT_BYTES = 64 * 1024
MAX_FRAME_BYTES = 64 * 1024
MAX_DESCRIPTOR_BYTES = 16 * 1024
MAX_DESCRIPTORS = 32
MAX_REGISTRY_ENTRIES_SCANNED = 128
MAX_EXPIRED_DESCRIPTORS_REMOVED = 32
MAX_FANOUT = 4
MAX_ID_SCALARS = 512
MAX_LABEL_SCALARS = 128
NETWORK_BUDGET_SECONDS = 0.60
SOCKET_STEP_TIMEOUT_SECONDS = 0.15

_DESCRIPTOR_KEYS = frozenset(
    {
        "schema_version",
        "owner",
        "observer_sha256",
        "source",
        "canonical_root",
        "root_fingerprint",
        "collector_instance",
        "secret",
        "port",
        "issued_at",
        "lease_expires_at",
    }
)


class _Rejected(Exception):
    """Internal fail-closed signal.  Its text is deliberately never emitted."""


def _read_bounded_stdin() -> bytes | None:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = sys.stdin.buffer.read(min(8192, MAX_INPUT_BYTES + 1 - total))
        if not chunk:
            return b"".join(chunks)
        total += len(chunk)
        if total > MAX_INPUT_BYTES:
            return None
        chunks.append(chunk)


def _reject_duplicate_keys(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise _Rejected()
        value[key] = item
    return value


def _parse_json_object(raw: bytes) -> dict[str, Any] | None:
    try:
        decoded = raw.decode("utf-8", errors="strict")
        value = json.loads(
            decoded,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda _value: (_ for _ in ()).throw(_Rejected()),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, _Rejected, RecursionError):
        return None
    return value if isinstance(value, dict) else None


def _parse_arguments(argv: list[str]) -> tuple[str, str, str] | None:
    if len(argv) != 6:
        return None
    values: dict[str, str] = {}
    for index in range(0, len(argv), 2):
        name = argv[index]
        value = argv[index + 1]
        if name not in {"--registry", "--owner", "--observer-sha256"} or name in values:
            return None
        values[name] = value
    registry = values.get("--registry")
    owner = values.get("--owner")
    observer_sha256 = values.get("--observer-sha256")
    if not registry or owner != FIXED_OWNER:
        return None
    if not _is_lower_hex(observer_sha256, 64):
        return None
    return registry, owner, observer_sha256


def _is_lower_hex(value: Any, length: int) -> bool:
    return (
        isinstance(value, str)
        and len(value) == length
        and all(character in "0123456789abcdef" for character in value)
    )


def _is_b64url(value: Any, decoded_length: int) -> bool:
    if not isinstance(value, str) or not value or "=" in value:
        return False
    try:
        decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, TypeError):
        return False
    return len(decoded) == decoded_length and _b64url(decoded) == value


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _own_content_hash() -> str | None:
    try:
        digest = hashlib.sha256()
        with open(__file__, "rb") as observer:
            while True:
                chunk = observer.read(64 * 1024)
                if not chunk:
                    return digest.hexdigest()
                digest.update(chunk)
    except (OSError, ValueError):
        return None


def _canonical_path(value: str) -> str | None:
    if not value or "\x00" in value or not os.path.isabs(value):
        return None
    try:
        canonical = os.path.realpath(value)
        if not os.path.isdir(canonical):
            return None
        return canonical
    except (OSError, ValueError):
        return None


def _path_identity(value: str) -> str:
    return os.path.normcase(os.path.normpath(value))


def _root_fingerprint(canonical_root: str) -> str:
    return hashlib.sha256(_path_identity(canonical_root).encode("utf-8")).hexdigest()


def _contains(root: str, candidate: str) -> bool:
    try:
        return os.path.commonpath((_path_identity(root), _path_identity(candidate))) == _path_identity(root)
    except (OSError, ValueError):
        return False


def _parse_utc(value: Any) -> _datetime.datetime | None:
    if not isinstance(value, str) or len(value) > 64:
        return None
    try:
        parsed = _datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(_datetime.timezone.utc)


def _owned_descriptor_name(path: str, collector: str) -> bool:
    try:
        if str(uuid.UUID(collector)) != collector:
            return False
        name = os.path.basename(path)
        prefix = f"aio-codex-{collector}-"
        if not name.startswith(prefix) or not name.endswith(".json"):
            return False
        generation = name[len(prefix) : -len(".json")]
        return str(uuid.UUID(generation)) == generation
    except (ValueError, AttributeError):
        return False


def _read_descriptor(
    path: str,
    expected_owner: str,
    expected_hash: str,
) -> tuple[dict[str, Any] | None, tuple[int, int] | None]:
    try:
        path_stat = os.lstat(path)
        if stat.S_ISLNK(path_stat.st_mode) or not stat.S_ISREG(path_stat.st_mode):
            return None, None
        if path_stat.st_size <= 0 or path_stat.st_size > MAX_DESCRIPTOR_BYTES:
            return None, None
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor_fd = os.open(path, flags)
        try:
            opened_stat = os.fstat(descriptor_fd)
            if not stat.S_ISREG(opened_stat.st_mode):
                return None, None
            if (
                opened_stat.st_dev != path_stat.st_dev
                or opened_stat.st_ino != path_stat.st_ino
            ):
                return None, None
            descriptor_chunks: list[bytes] = []
            descriptor_size = 0
            while descriptor_size <= MAX_DESCRIPTOR_BYTES:
                chunk = os.read(
                    descriptor_fd,
                    min(4096, MAX_DESCRIPTOR_BYTES + 1 - descriptor_size),
                )
                if not chunk:
                    break
                descriptor_chunks.append(chunk)
                descriptor_size += len(chunk)
            raw = b"".join(descriptor_chunks)
        finally:
            os.close(descriptor_fd)
    except (OSError, ValueError):
        return None, None

    if len(raw) > MAX_DESCRIPTOR_BYTES:
        return None, None
    descriptor = _parse_json_object(raw)
    if descriptor is None or frozenset(descriptor) != _DESCRIPTOR_KEYS:
        return None, None
    if (
        descriptor.get("schema_version") != REGISTRY_PROTOCOL
        or descriptor.get("owner") != expected_owner
        or descriptor.get("observer_sha256") != expected_hash
        or descriptor.get("source") != SOURCE_ID
    ):
        return None, None
    collector = descriptor.get("collector_instance")
    root_fingerprint = descriptor.get("root_fingerprint")
    port = descriptor.get("port")
    if not _valid_identifier(collector) or not _is_lower_hex(root_fingerprint, 64):
        return None, None
    if not isinstance(port, int) or isinstance(port, bool) or not 1 <= port <= 65535:
        return None, None
    if not _is_b64url(descriptor.get("secret"), 32):
        return None, None
    issued = _parse_utc(descriptor.get("issued_at"))
    expires = _parse_utc(descriptor.get("lease_expires_at"))
    now = _datetime.datetime.now(_datetime.timezone.utc)
    if issued is None or expires is None or issued > now + _datetime.timedelta(minutes=5):
        return None, None
    if expires <= now:
        identity = (opened_stat.st_dev, opened_stat.st_ino)
        return None, identity if _owned_descriptor_name(path, collector) else None

    root_value = descriptor.get("canonical_root")
    if not isinstance(root_value, str) or len(root_value) > 4096:
        return None, None
    canonical_root = _canonical_path(root_value)
    if canonical_root is None or _path_identity(canonical_root) != _path_identity(root_value):
        return None, None
    if _root_fingerprint(canonical_root) != root_fingerprint:
        return None, None
    descriptor["canonical_root"] = canonical_root
    descriptor["_lease_time"] = expires.timestamp()
    return descriptor, None


def _remove_expired_descriptor(path: str, identity: tuple[int, int]) -> None:
    try:
        current = os.lstat(path)
        if (
            stat.S_ISLNK(current.st_mode)
            or not stat.S_ISREG(current.st_mode)
            or (current.st_dev, current.st_ino) != identity
        ):
            return
        os.unlink(path)
    except (OSError, ValueError):
        return


def _load_matching_descriptors(
    registry: str,
    event_cwd: str,
    expected_owner: str,
    expected_hash: str,
) -> list[dict[str, Any]]:
    try:
        registry_stat = os.lstat(registry)
        if stat.S_ISLNK(registry_stat.st_mode) or not stat.S_ISDIR(registry_stat.st_mode):
            return []
        entries = os.scandir(registry)
    except (OSError, ValueError):
        return []

    descriptors: list[dict[str, Any]] = []
    candidate_count = 0
    scanned_count = 0
    removed_count = 0
    incomplete = False
    try:
        for entry in entries:
            scanned_count += 1
            if scanned_count > MAX_REGISTRY_ENTRIES_SCANNED:
                incomplete = True
                break
            try:
                if entry.is_symlink() or not entry.is_file(follow_symlinks=False):
                    continue
            except OSError:
                continue
            descriptor, expired_identity = _read_descriptor(
                entry.path,
                expected_owner,
                expected_hash,
            )
            if expired_identity is not None:
                if removed_count < MAX_EXPIRED_DESCRIPTORS_REMOVED:
                    _remove_expired_descriptor(entry.path, expired_identity)
                    removed_count += 1
                continue
            candidate_count += 1
            if candidate_count > MAX_DESCRIPTORS:
                incomplete = True
                continue
            if descriptor is not None:
                descriptors.append(descriptor)
    finally:
        entries.close()

    # Discovery is fail-closed: routing from a truncated candidate set could
    # select a less-specific root simply because a later entry was not read.
    if incomplete:
        return []

    # Atomic lease replacement can make two generations briefly visible.  Use
    # only the newest live descriptor for each collector instance.
    newest: dict[str, dict[str, Any]] = {}
    for descriptor in descriptors:
        collector = descriptor["collector_instance"]
        previous = newest.get(collector)
        if previous is None or descriptor["_lease_time"] > previous["_lease_time"]:
            newest[collector] = descriptor

    matching = [
        descriptor
        for descriptor in newest.values()
        if _contains(descriptor["canonical_root"], event_cwd)
    ]
    if not matching:
        return []
    most_specific = max(len(_path_identity(item["canonical_root"])) for item in matching)
    selected_identity = min(
        _path_identity(item["canonical_root"])
        for item in matching
        if len(_path_identity(item["canonical_root"])) == most_specific
    )
    selected = [
        item for item in matching if _path_identity(item["canonical_root"]) == selected_identity
    ]
    selected.sort(key=lambda item: item["collector_instance"])
    return selected[:MAX_FANOUT]


def _valid_identifier(value: Any) -> bool:
    return isinstance(value, str) and 0 < len(value) <= MAX_ID_SCALARS


def _optional_identifier(payload: dict[str, Any], key: str) -> tuple[bool, str | None]:
    if key not in payload or payload[key] is None:
        return True, None
    value = payload[key]
    if not _valid_identifier(value):
        return False, None
    return True, value


def _bounded_label(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    if len(value) <= MAX_LABEL_SCALARS:
        return value
    return value[: MAX_LABEL_SCALARS - 1] + "…"


def _normalize(payload: dict[str, Any]) -> tuple[dict[str, Any], str] | None:
    event_type = payload.get("hook_event_name")
    session_id = payload.get("session_id")
    cwd = payload.get("cwd")
    if event_type not in SUPPORTED_EVENTS or not _valid_identifier(session_id):
        return None
    if not isinstance(cwd, str) or len(cwd) > 4096:
        return None
    canonical_cwd = _canonical_path(cwd)
    if canonical_cwd is None:
        return None

    optional_fields = {
        "turn_id": "turn_id",
        "agent_id": "subagent_id",
        "tool_use_id": "tool_call_id",
    }
    normalized: dict[str, Any] = {
        "source": SOURCE_ID,
        "delivery_id": str(uuid.uuid4()),
        "session_id": session_id,
        "event_type": event_type,
    }
    for source_key, target_key in optional_fields.items():
        valid, value = _optional_identifier(payload, source_key)
        if not valid:
            return None
        if value is not None:
            normalized[target_key] = value

    labels = {
        "tool_name": "tool_label",
        "agent_type": "agent_type",
        "model": "model",
    }
    for source_key, target_key in labels.items():
        value = _bounded_label(payload.get(source_key))
        if value is not None:
            normalized[target_key] = value
    return normalized, canonical_cwd


def _canonical_json(value: dict[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _proof(secret: bytes, parts: Iterable[str]) -> str:
    message = "\n".join(parts).encode("utf-8")
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def _send_frame(connection: socket.socket, value: dict[str, Any]) -> None:
    encoded = _canonical_json(value)
    if len(encoded) > MAX_FRAME_BYTES:
        raise _Rejected()
    connection.sendall(struct.pack("!I", len(encoded)) + encoded)


def _remaining_timeout(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise _Rejected()
    return min(SOCKET_STEP_TIMEOUT_SECONDS, remaining)


def _receive_exact(connection: socket.socket, count: int, deadline: float) -> bytes:
    chunks: list[bytes] = []
    received = 0
    while received < count:
        connection.settimeout(_remaining_timeout(deadline))
        chunk = connection.recv(count - received)
        if not chunk:
            raise _Rejected()
        chunks.append(chunk)
        received += len(chunk)
    return b"".join(chunks)


def _receive_frame(connection: socket.socket, deadline: float) -> dict[str, Any]:
    header = _receive_exact(connection, 4, deadline)
    length = struct.unpack("!I", header)[0]
    if length <= 0 or length > MAX_FRAME_BYTES:
        raise _Rejected()
    value = _parse_json_object(_receive_exact(connection, length, deadline))
    if value is None:
        raise _Rejected()
    return value


def _secret_bytes(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _deliver(descriptor: dict[str, Any], base_event: dict[str, Any], deadline: float) -> None:
    secret = _secret_bytes(descriptor["secret"])
    collector = descriptor["collector_instance"]
    root_fingerprint = descriptor["root_fingerprint"]
    client_nonce = _b64url(secrets.token_bytes(32))
    hello_parts = [WIRE_PROTOCOL, "client", collector, root_fingerprint, client_nonce]
    hello = {
        "protocol": WIRE_PROTOCOL,
        "type": "client_hello",
        "collector_instance": collector,
        "root_fingerprint": root_fingerprint,
        "client_nonce": client_nonce,
        "proof": _proof(secret, hello_parts),
    }

    with socket.create_connection(
        ("127.0.0.1", descriptor["port"]), timeout=_remaining_timeout(deadline)
    ) as connection:
        connection.settimeout(_remaining_timeout(deadline))
        _send_frame(connection, hello)
        challenge = _receive_frame(connection, deadline)
        if frozenset(challenge) != frozenset({"protocol", "type", "server_nonce", "proof"}):
            raise _Rejected()
        server_nonce = challenge.get("server_nonce")
        if (
            challenge.get("protocol") != WIRE_PROTOCOL
            or challenge.get("type") != "server_challenge"
            or not _is_b64url(server_nonce, 32)
        ):
            raise _Rejected()
        challenge_parts = [
            WIRE_PROTOCOL,
            "server",
            collector,
            root_fingerprint,
            client_nonce,
            server_nonce,
        ]
        if not hmac.compare_digest(challenge["proof"], _proof(secret, challenge_parts)):
            raise _Rejected()

        event = dict(base_event)
        event["collector_instance"] = collector
        event["root_fingerprint"] = root_fingerprint
        event_digest = hashlib.sha256(_canonical_json(event)).hexdigest()
        event_parts = [
            WIRE_PROTOCOL,
            "event",
            collector,
            root_fingerprint,
            client_nonce,
            server_nonce,
            event_digest,
        ]
        connection.settimeout(_remaining_timeout(deadline))
        _send_frame(
            connection,
            {
                "protocol": WIRE_PROTOCOL,
                "type": "event",
                "event": event,
                "proof": _proof(secret, event_parts),
            },
        )
        acknowledgement = _receive_frame(connection, deadline)
        if frozenset(acknowledgement) != frozenset(
            {"protocol", "type", "delivery_id", "status", "proof"}
        ):
            raise _Rejected()
        status = acknowledgement.get("status")
        if (
            acknowledgement.get("protocol") != WIRE_PROTOCOL
            or acknowledgement.get("type") != "ack"
            or acknowledgement.get("delivery_id") != event["delivery_id"]
            or status not in {"accepted", "replay"}
        ):
            raise _Rejected()
        acknowledgement_parts = [
            WIRE_PROTOCOL,
            "ack",
            collector,
            root_fingerprint,
            client_nonce,
            server_nonce,
            event["delivery_id"],
            status,
        ]
        if not hmac.compare_digest(
            acknowledgement["proof"], _proof(secret, acknowledgement_parts)
        ):
            raise _Rejected()


def _neutral_output(event_type: Any) -> bytes:
    return (
        b""
        if isinstance(event_type, str) and event_type in EMPTY_OUTPUT_EVENTS
        else b"{}\n"
    )


def main() -> int:
    neutral = b"{}\n"
    try:
        raw = _read_bounded_stdin()
        payload = _parse_json_object(raw) if raw is not None else None
        event_type = payload.get("hook_event_name") if payload is not None else None
        neutral = _neutral_output(event_type)
        arguments = _parse_arguments(sys.argv[1:])
        if raw is None or payload is None or arguments is None:
            raise _Rejected()
        registry, owner, expected_hash = arguments
        if _own_content_hash() != expected_hash:
            raise _Rejected()
        normalized = _normalize(payload)
        if normalized is None:
            raise _Rejected()
        base_event, canonical_cwd = normalized
        descriptors = _load_matching_descriptors(registry, canonical_cwd, owner, expected_hash)
        # One delivery UUID is shared by the bounded same-root fan-out.
        deadline = time.monotonic() + NETWORK_BUDGET_SECONDS
        for descriptor in descriptors:
            if time.monotonic() >= deadline:
                break
            try:
                _deliver(descriptor, base_event, deadline)
            except (OSError, ValueError, TypeError, _Rejected, UnicodeEncodeError, OverflowError):
                continue
    except BaseException:
        # Hook observation is deliberately lossy and fail-open.  Never expose
        # event data or diagnostics through stdout/stderr.
        pass
    try:
        sys.stdout.buffer.write(neutral)
        sys.stdout.buffer.flush()
    except BaseException:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
