import type { CODEX_SOURCE_ID, CODEX_SUPPORTED_EVENTS } from "./constants";

export type CodexEventType = (typeof CODEX_SUPPORTED_EVENTS)[number];

export type CodexMonitorState =
  | "not_configured"
  | "configured_no_observations"
  | "receiving"
  | "stale"
  | "disconnected"
  | "unsupported"
  | "error";

export type CodexListenerState = "stopped" | "listening" | "error";
export type CodexSetupState = "not_configured" | "unverified";

export interface CodexSessionIdentity {
  readonly source: typeof CODEX_SOURCE_ID;
  readonly collectorInstance: string;
  readonly rootFingerprint: string;
  readonly sessionId: string;
  readonly scope:
    | { readonly kind: "root" }
    | { readonly kind: "subagent"; readonly subagentId: string };
}

export interface CodexObservedEvent {
  readonly source: typeof CODEX_SOURCE_ID;
  readonly collectorInstance: string;
  readonly rootFingerprint: string;
  readonly deliveryId: string;
  readonly sessionId: string;
  readonly turnId?: string;
  readonly subagentId?: string;
  readonly toolCallId?: string;
  readonly eventType: CodexEventType;
  readonly receivedAt: string;
  readonly receiptSequence: number;
  readonly toolLabel?: string;
  readonly agentType?: string;
  readonly model?: string;
}

export interface CodexObservedSession {
  readonly identity: CodexSessionIdentity;
  readonly lastEventType: CodexEventType;
  readonly lastReceivedAt: string;
  readonly lastReceiptSequence: number;
  readonly model?: string;
}

export interface CodexMonitorSnapshot {
  readonly state: CodexMonitorState;
  readonly listener: CodexListenerState;
  readonly setup: CodexSetupState;
  readonly source: typeof CODEX_SOURCE_ID;
  readonly rootFingerprint: string;
  readonly lastReceivedAt?: string;
  readonly events: readonly CodexObservedEvent[];
  readonly sessions: readonly CodexObservedSession[];
  readonly error?: string;
}

export interface CodexMonitorClock {
  readonly wallNow: () => number;
  readonly monotonicNow: () => number;
}

export interface CodexMonitorOptions {
  readonly registryDirectory: string;
  readonly canonicalRoot: string;
  readonly onDidChange?: (snapshot: CodexMonitorSnapshot) => void;
  /** Injectable only for deterministic tests; production callers should omit it. */
  readonly clock?: CodexMonitorClock;
}

export type CodexMonitorStopReason =
  | "user"
  | "root-changed"
  | "interpreter-changed"
  | "dispose"
  | "error";

export interface CodexHookSetupPlan {
  readonly owner: string;
  readonly observerSha256: string;
  readonly source: typeof CODEX_SOURCE_ID;
  readonly command: string;
  readonly commandWindows: string;
  readonly configFragment: Readonly<Record<string, unknown>>;
  readonly capturedMetadata: readonly string[];
  readonly excludedData: readonly string[];
  readonly destination: string;
  readonly trustNotice: string;
  readonly removalNotice: string;
}

export interface CreateCodexHookSetupOptions {
  readonly pythonPath: string;
  readonly observerPath: string;
  readonly observerSha256: string;
  readonly registryDirectory: string;
}

export interface InstalledObserverAsset {
  readonly observerPath: string;
  readonly sha256: string;
}
