export const CODEX_SOURCE_ID = "codex.lifecycle-hooks/v1" as const;
export const CODEX_MONITOR_OWNER = "aio-control-center-dev/v1" as const;
export const CODEX_WIRE_PROTOCOL = "aio.codex-monitor/1" as const;
export const CODEX_REGISTRY_PROTOCOL = "aio.codex-monitor-registry/1" as const;

// Updated whenever observer/codex_hook_observer.py changes. Setup refuses to
// register an observer whose installed bytes do not match this build pin.
export const CODEX_OBSERVER_SHA256 =
  "a36e1b645d302c1ef80d76de0835e17465b051a51b8b662a01fa6f08ad6cbaf5" as const;

export const CODEX_SUPPORTED_EVENTS = [
  "SessionStart",
  "SessionEnd",
  "SubagentStart",
  "SubagentStop",
  "PostToolUse",
  "PostCompact",
  "Stop",
  "Interrupt",
] as const;

export const MAX_FRAME_BYTES = 64 * 1024;
export const MAX_IDENTIFIER_SCALARS = 512;
export const MAX_LABEL_SCALARS = 128;
export const MAX_TIMELINE_EVENTS = 200;
export const MAX_DISPLAYED_SESSIONS = 20;
export const MAX_REPLAY_ENTRIES = 1_024;
export const MAX_ATTEMPTS_PER_MINUTE = 120;
export const DESCRIPTOR_LEASE_MS = 90_000;
export const DESCRIPTOR_RENEWAL_MS = 30_000;
export const FRESHNESS_MS = 5 * 60_000;
