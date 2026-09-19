import { randomBytes, randomUUID } from "node:crypto";
import {
  chmod,
  lstat,
  mkdir,
  open,
  realpath,
  rename,
  unlink,
} from "node:fs/promises";
import { createServer, type Server, type Socket } from "node:net";
import { isAbsolute, join, normalize, parse, resolve, sep } from "node:path";
import { performance } from "node:perf_hooks";

import {
  CODEX_MONITOR_OWNER,
  CODEX_OBSERVER_SHA256,
  CODEX_REGISTRY_PROTOCOL,
  CODEX_SOURCE_ID,
  CODEX_SUPPORTED_EVENTS,
  CODEX_WIRE_PROTOCOL,
  DESCRIPTOR_LEASE_MS,
  DESCRIPTOR_RENEWAL_MS,
  FRESHNESS_MS,
  MAX_ATTEMPTS_PER_MINUTE,
  MAX_DISPLAYED_SESSIONS,
  MAX_IDENTIFIER_SCALARS,
  MAX_LABEL_SCALARS,
  MAX_REPLAY_ENTRIES,
  MAX_TIMELINE_EVENTS,
} from "./constants";
import {
  base64Url,
  canonicalJson,
  hmacProof,
  isClosedRecord,
  proofMatches,
  readFrame,
  sha256Hex,
  writeFrame,
} from "./protocol";
import type {
  CodexEventType,
  CodexListenerState,
  CodexMonitorClock,
  CodexMonitorOptions,
  CodexMonitorSnapshot,
  CodexMonitorState,
  CodexMonitorStopReason,
  CodexObservedEvent,
  CodexObservedSession,
  CodexSessionIdentity,
  CodexSetupState,
} from "./types";

interface TransportEvent {
  readonly source: typeof CODEX_SOURCE_ID;
  readonly collector_instance: string;
  readonly root_fingerprint: string;
  readonly delivery_id: string;
  readonly session_id: string;
  readonly event_type: CodexEventType;
  readonly turn_id?: string;
  readonly subagent_id?: string;
  readonly tool_call_id?: string;
  readonly tool_label?: string;
  readonly agent_type?: string;
  readonly model?: string;
}

interface CollectorDescriptor {
  readonly schema_version: typeof CODEX_REGISTRY_PROTOCOL;
  readonly owner: typeof CODEX_MONITOR_OWNER;
  readonly observer_sha256: typeof CODEX_OBSERVER_SHA256;
  readonly source: typeof CODEX_SOURCE_ID;
  readonly canonical_root: string;
  readonly root_fingerprint: string;
  readonly collector_instance: string;
  readonly secret: string;
  readonly port: number;
  readonly issued_at: string;
  readonly lease_expires_at: string;
}

class LifecycleSuperseded extends Error {
  public constructor() {
    super("Codex monitor lifecycle operation was superseded.");
  }
}

const HELLO_KEYS = [
  "protocol",
  "type",
  "collector_instance",
  "root_fingerprint",
  "client_nonce",
  "proof",
] as const;
const EVENT_ENVELOPE_KEYS = ["protocol", "type", "event", "proof"] as const;
const EVENT_REQUIRED_KEYS = [
  "source",
  "collector_instance",
  "root_fingerprint",
  "delivery_id",
  "session_id",
  "event_type",
] as const;
const EVENT_OPTIONAL_KEYS = [
  "turn_id",
  "subagent_id",
  "tool_call_id",
  "tool_label",
  "agent_type",
  "model",
] as const;

function defaultClock(): CodexMonitorClock {
  return {
    wallNow: () => Date.now(),
    monotonicNow: () => performance.now(),
  };
}

function scalarLength(value: string): number {
  return [...value].length;
}

function validIdentifier(value: unknown): value is string {
  return typeof value === "string" && scalarLength(value) > 0 && scalarLength(value) <= MAX_IDENTIFIER_SCALARS;
}

function validLabel(value: unknown): value is string {
  return typeof value === "string" && scalarLength(value) > 0 && scalarLength(value) <= MAX_LABEL_SCALARS;
}

function validLowerHex(value: unknown, length: number): value is string {
  return typeof value === "string" && value.length === length && /^[0-9a-f]+$/u.test(value);
}

function validBase64Url32(value: unknown): value is string {
  if (typeof value !== "string" || !/^[A-Za-z0-9_-]{43}$/u.test(value)) {
    return false;
  }
  try {
    const decoded = Buffer.from(value, "base64url");
    return decoded.length === 32 && decoded.toString("base64url") === value;
  } catch {
    return false;
  }
}

function validDeliveryId(value: unknown): value is string {
  return (
    typeof value === "string" &&
    /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/u.test(value)
  );
}

function isSupportedEvent(value: unknown): value is CodexEventType {
  return typeof value === "string" && (CODEX_SUPPORTED_EVENTS as readonly string[]).includes(value);
}

function pathIdentity(pathValue: string, platform: NodeJS.Platform): string {
  let result = normalize(pathValue);
  const root = parse(result).root;
  while (result.length > root.length && result.endsWith(sep)) {
    result = result.slice(0, -1);
  }
  return platform === "win32" ? result.toLowerCase() : result;
}

function pathFingerprint(pathValue: string, platform: NodeJS.Platform): string {
  return sha256Hex(pathIdentity(pathValue, platform));
}

function safeErrorMessage(): string {
  return "The local Codex observation listener failed. Stop and start observation to retry.";
}

function copyEvent(event: CodexObservedEvent): CodexObservedEvent {
  return Object.freeze({ ...event });
}

function copySession(session: CodexObservedSession): CodexObservedSession {
  const scope = Object.freeze({ ...session.identity.scope }) as CodexSessionIdentity["scope"];
  return Object.freeze({
    ...session,
    identity: Object.freeze({ ...session.identity, scope }),
  });
}

function sameSessionIdentity(left: CodexSessionIdentity, right: CodexSessionIdentity): boolean {
  return (
    left.source === right.source &&
    left.collectorInstance === right.collectorInstance &&
    left.rootFingerprint === right.rootFingerprint &&
    left.sessionId === right.sessionId &&
    left.scope.kind === right.scope.kind &&
    (left.scope.kind === "root" ||
      (right.scope.kind === "subagent" && left.scope.subagentId === right.scope.subagentId))
  );
}

async function closeServer(server: Server | undefined): Promise<void> {
  if (server === undefined || !server.listening) {
    return;
  }
  await new Promise<void>((resolveClose) => server.close(() => resolveClose()));
}

function validateTransportEvent(value: unknown): TransportEvent | undefined {
  if (!isClosedRecord(value, EVENT_REQUIRED_KEYS, EVENT_OPTIONAL_KEYS)) {
    return undefined;
  }
  if (
    value.source !== CODEX_SOURCE_ID ||
    !validIdentifier(value.collector_instance) ||
    !validLowerHex(value.root_fingerprint, 64) ||
    !validDeliveryId(value.delivery_id) ||
    !validIdentifier(value.session_id) ||
    !isSupportedEvent(value.event_type)
  ) {
    return undefined;
  }
  for (const field of ["turn_id", "subagent_id", "tool_call_id"] as const) {
    if (value[field] !== undefined && !validIdentifier(value[field])) {
      return undefined;
    }
  }
  for (const field of ["tool_label", "agent_type", "model"] as const) {
    if (value[field] !== undefined && !validLabel(value[field])) {
      return undefined;
    }
  }
  return value as unknown as TransportEvent;
}

export class CodexMonitor {
  private readonly onDidChange: ((snapshot: CodexMonitorSnapshot) => void) | undefined;
  private readonly clock: CodexMonitorClock;
  private readonly platform: NodeJS.Platform;
  private readonly requestedRegistryDirectory: string;
  private readonly requestedCanonicalRoot: string;

  private canonicalRoot: string;
  private registryDirectory: string;
  private rootFingerprintValue: string;
  private collectorInstance = "";
  private secret: Buffer | undefined;
  private issuedAt = "";
  private leaseExpiresAt = 0;
  private descriptorPath: string | undefined;
  private readonly ownedDescriptorPaths = new Set<string>();
  private server: Server | undefined;
  private readonly sockets = new Set<Socket>();
  private renewalTimer: NodeJS.Timeout | undefined;
  private freshnessTimer: NodeJS.Timeout | undefined;
  private renewalInFlight: Promise<void> | undefined;
  private starting: { readonly epoch: number; readonly promise: Promise<CodexMonitorSnapshot> } | undefined;
  private stopping: Promise<CodexMonitorSnapshot> | undefined;
  private lifecycleEpoch = 0;
  private disposed = false;

  private baseState: CodexMonitorState = "not_configured";
  private listenerState: CodexListenerState = "stopped";
  private setupState: CodexSetupState = "not_configured";
  private errorMessage: string | undefined;
  private lastReceivedAt: string | undefined;
  private lastReceivedMonotonic: number | undefined;
  private receiptSequence = 0;
  private readonly events: CodexObservedEvent[] = [];
  private readonly sessions: CodexObservedSession[] = [];
  private readonly replayByCollector = new Map<string, Map<string, true>>();
  private readonly replayOrder: Array<{ collectorInstance: string; deliveryId: string }> = [];
  private readonly attemptTimes: number[] = [];

  public constructor(options: CodexMonitorOptions) {
    if (!isAbsolute(options.registryDirectory) || !isAbsolute(options.canonicalRoot)) {
      throw new Error("Codex monitor registry and selected root must be absolute paths.");
    }
    if (
      options.registryDirectory.includes("\0") ||
      options.canonicalRoot.includes("\0") ||
      options.registryDirectory.length > 4096 ||
      options.canonicalRoot.length > 4096
    ) {
      throw new Error("Codex monitor path is invalid.");
    }
    this.requestedRegistryDirectory = resolve(options.registryDirectory);
    this.requestedCanonicalRoot = resolve(options.canonicalRoot);
    this.registryDirectory = this.requestedRegistryDirectory;
    this.canonicalRoot = this.requestedCanonicalRoot;
    this.platform = process.platform;
    this.rootFingerprintValue = pathFingerprint(this.canonicalRoot, this.platform);
    this.clock = options.clock ?? defaultClock();
    this.onDidChange = options.onDidChange;
  }

  public async start(): Promise<CodexMonitorSnapshot> {
    if (this.disposed) {
      throw new Error("Codex monitor is disposed.");
    }
    if (this.listenerState === "listening" && this.stopping === undefined) {
      return this.snapshot();
    }
    if (this.starting !== undefined && this.starting.epoch === this.lifecycleEpoch) {
      return this.starting.promise;
    }

    const previousStart = this.starting?.promise;
    const previousStop = this.stopping;
    const epoch = ++this.lifecycleEpoch;
    const promise = this.performStart(epoch, previousStart, previousStop);
    this.starting = { epoch, promise };
    try {
      return await promise;
    } finally {
      if (this.starting?.promise === promise) {
        this.starting = undefined;
      }
    }
  }

  private async performStart(
    epoch: number,
    previousStart: Promise<CodexMonitorSnapshot> | undefined,
    previousStop: Promise<CodexMonitorSnapshot> | undefined,
  ): Promise<CodexMonitorSnapshot> {
    try {
      await Promise.allSettled([previousStart, previousStop].filter((item) => item !== undefined));
      this.assertLifecycleCurrent(epoch);
      this.clearMemory();
      this.errorMessage = undefined;
      this.setupState = "unverified";
      if (this.platform !== "win32") {
        this.baseState = "unsupported";
        this.listenerState = "stopped";
        this.setupState = "not_configured";
        this.emitChange();
        return this.snapshot();
      }

      this.canonicalRoot = await realpath(this.requestedCanonicalRoot);
      this.assertLifecycleCurrent(epoch);
      const rootInfo = await lstat(this.canonicalRoot);
      this.assertLifecycleCurrent(epoch);
      if (!rootInfo.isDirectory()) {
        throw new Error("Selected root is not a directory.");
      }
      this.rootFingerprintValue = pathFingerprint(this.canonicalRoot, this.platform);

      await mkdir(this.requestedRegistryDirectory, { recursive: true, mode: 0o700 });
      this.assertLifecycleCurrent(epoch);
      const registryInfo = await lstat(this.requestedRegistryDirectory);
      this.assertLifecycleCurrent(epoch);
      if (!registryInfo.isDirectory() || registryInfo.isSymbolicLink()) {
        throw new Error("Registry is not a regular directory.");
      }
      this.registryDirectory = await realpath(this.requestedRegistryDirectory);
      this.assertLifecycleCurrent(epoch);

      this.collectorInstance = randomUUID();
      this.secret = randomBytes(32);
      this.issuedAt = new Date(this.clock.wallNow()).toISOString();
      this.server = createServer((socket) => this.acceptSocket(socket));
      this.server.maxConnections = 32;
      await new Promise<void>((resolveListen, rejectListen) => {
        const server = this.server!;
        const onError = (error: Error): void => rejectListen(error);
        server.once("error", onError);
        server.listen({ host: "127.0.0.1", port: 0, exclusive: true }, () => {
          server.off("error", onError);
          resolveListen();
        });
      });
      this.assertLifecycleCurrent(epoch);
      this.server.on("error", () => void this.fail());
      // Publish only after the socket can authenticate deliveries. No state is
      // emitted to the UI until the descriptor has been published successfully.
      this.listenerState = "listening";
      await this.publishDescriptor(epoch);
      this.assertLifecycleCurrent(epoch);
      this.baseState = "configured_no_observations";
      this.renewalTimer = setInterval(() => void this.renewDescriptor(), DESCRIPTOR_RENEWAL_MS);
      this.renewalTimer.unref();
      this.emitChange();
    } catch (error) {
      await this.cleanupAfterFailedStart();
      if (error instanceof LifecycleSuperseded || !this.lifecycleIsCurrent(epoch)) {
        this.listenerState = "stopped";
        this.setupState = "not_configured";
        return this.snapshot();
      }
      this.listenerState = "error";
      this.baseState = "error";
      this.errorMessage = safeErrorMessage();
      this.emitChange();
    }
    return this.snapshot();
  }

  public snapshot(): CodexMonitorSnapshot {
    let state = this.baseState;
    if (this.listenerState === "listening") {
      if (this.lastReceivedMonotonic === undefined) {
        state = "configured_no_observations";
      } else if (this.clock.monotonicNow() - this.lastReceivedMonotonic >= FRESHNESS_MS) {
        state = "stale";
      } else {
        state = "receiving";
      }
    }
    return Object.freeze({
      state,
      listener: this.listenerState,
      setup: this.setupState,
      source: CODEX_SOURCE_ID,
      rootFingerprint: this.rootFingerprintValue,
      ...(this.lastReceivedAt === undefined ? {} : { lastReceivedAt: this.lastReceivedAt }),
      events: Object.freeze(this.events.map(copyEvent)),
      sessions: Object.freeze(this.sessions.map(copySession)),
      ...(this.errorMessage === undefined ? {} : { error: this.errorMessage }),
    });
  }

  public async stop(reason: CodexMonitorStopReason = "user"): Promise<CodexMonitorSnapshot> {
    ++this.lifecycleEpoch;
    if (this.stopping !== undefined) {
      return this.stopping;
    }
    const pendingStart = this.starting?.promise;
    const pendingRenewal = this.renewalInFlight;
    this.stopping = this.performStop(reason, pendingStart, pendingRenewal);
    try {
      return await this.stopping;
    } finally {
      this.stopping = undefined;
    }
  }

  public async dispose(): Promise<void> {
    if (this.disposed) {
      return;
    }
    this.disposed = true;
    await this.stop("dispose");
  }

  private acceptSocket(socket: Socket): void {
    const now = this.clock.monotonicNow();
    while (this.attemptTimes.length > 0 && now - this.attemptTimes[0]! >= 60_000) {
      this.attemptTimes.shift();
    }
    if (
      this.listenerState !== "listening" ||
      socket.remoteAddress !== "127.0.0.1" ||
      this.attemptTimes.length >= MAX_ATTEMPTS_PER_MINUTE
    ) {
      socket.destroy();
      return;
    }
    this.attemptTimes.push(now);
    this.sockets.add(socket);
    socket.setNoDelay(true);
    socket.setTimeout(1_500, () => socket.destroy());
    socket.on("error", () => undefined);
    socket.once("close", () => this.sockets.delete(socket));
    void this.handleSocket(socket)
      .catch(() => undefined)
      .finally(() => socket.destroy());
  }

  private async handleSocket(socket: Socket): Promise<void> {
    const secret = this.secret;
    if (
      secret === undefined ||
      this.listenerState !== "listening" ||
      this.clock.wallNow() >= this.leaseExpiresAt
    ) {
      return;
    }
    const hello = await readFrame(socket);
    if (!isClosedRecord(hello, HELLO_KEYS)) {
      return;
    }
    const clientNonce = hello.client_nonce;
    if (
      hello.protocol !== CODEX_WIRE_PROTOCOL ||
      hello.type !== "client_hello" ||
      hello.collector_instance !== this.collectorInstance ||
      hello.root_fingerprint !== this.rootFingerprintValue ||
      !validBase64Url32(clientNonce)
    ) {
      return;
    }
    const helloProof = hmacProof(secret, [
      CODEX_WIRE_PROTOCOL,
      "client",
      this.collectorInstance,
      this.rootFingerprintValue,
      clientNonce,
    ]);
    if (!proofMatches(hello.proof, helloProof)) {
      return;
    }

    const serverNonce = base64Url(randomBytes(32));
    const challengeProof = hmacProof(secret, [
      CODEX_WIRE_PROTOCOL,
      "server",
      this.collectorInstance,
      this.rootFingerprintValue,
      clientNonce,
      serverNonce,
    ]);
    await writeFrame(socket, {
      protocol: CODEX_WIRE_PROTOCOL,
      type: "server_challenge",
      server_nonce: serverNonce,
      proof: challengeProof,
    });

    const envelope = await readFrame(socket);
    if (!isClosedRecord(envelope, EVENT_ENVELOPE_KEYS)) {
      return;
    }
    const event = validateTransportEvent(envelope.event);
    if (
      envelope.protocol !== CODEX_WIRE_PROTOCOL ||
      envelope.type !== "event" ||
      event === undefined ||
      event.collector_instance !== this.collectorInstance ||
      event.root_fingerprint !== this.rootFingerprintValue
    ) {
      return;
    }
    const eventDigest = sha256Hex(canonicalJson(event));
    const expectedEventProof = hmacProof(secret, [
      CODEX_WIRE_PROTOCOL,
      "event",
      this.collectorInstance,
      this.rootFingerprintValue,
      clientNonce,
      serverNonce,
      eventDigest,
    ]);
    if (!proofMatches(envelope.proof, expectedEventProof)) {
      return;
    }

    const replay = this.hasReplay(event.collector_instance, event.delivery_id);
    const status = replay ? "replay" : "accepted";
    if (!replay) {
      this.rememberReplay(event.collector_instance, event.delivery_id);
      this.retainEvent(event);
    }
    const acknowledgementProof = hmacProof(secret, [
      CODEX_WIRE_PROTOCOL,
      "ack",
      this.collectorInstance,
      this.rootFingerprintValue,
      clientNonce,
      serverNonce,
      event.delivery_id,
      status,
    ]);
    await writeFrame(socket, {
      protocol: CODEX_WIRE_PROTOCOL,
      type: "ack",
      delivery_id: event.delivery_id,
      status,
      proof: acknowledgementProof,
    });
    if (!replay) {
      this.emitChange();
    }
  }

  private retainEvent(event: TransportEvent): void {
    const receiptSequence = ++this.receiptSequence;
    const receivedWall = this.clock.wallNow();
    const receivedAt = new Date(receivedWall).toISOString();
    this.lastReceivedAt = receivedAt;
    this.lastReceivedMonotonic = this.clock.monotonicNow();
    const observed: CodexObservedEvent = Object.freeze({
      source: CODEX_SOURCE_ID,
      collectorInstance: event.collector_instance,
      rootFingerprint: event.root_fingerprint,
      deliveryId: event.delivery_id,
      sessionId: event.session_id,
      eventType: event.event_type,
      receivedAt,
      receiptSequence,
      ...(event.turn_id === undefined ? {} : { turnId: event.turn_id }),
      ...(event.subagent_id === undefined ? {} : { subagentId: event.subagent_id }),
      ...(event.tool_call_id === undefined ? {} : { toolCallId: event.tool_call_id }),
      ...(event.tool_label === undefined ? {} : { toolLabel: event.tool_label }),
      ...(event.agent_type === undefined ? {} : { agentType: event.agent_type }),
      ...(event.model === undefined ? {} : { model: event.model }),
    });
    this.events.push(observed);
    if (this.events.length > MAX_TIMELINE_EVENTS) {
      this.events.splice(0, this.events.length - MAX_TIMELINE_EVENTS);
    }
    this.updateSession(observed);
    this.scheduleFreshnessTransition();
  }

  private updateSession(event: CodexObservedEvent): void {
    const identity: CodexSessionIdentity = Object.freeze({
      source: CODEX_SOURCE_ID,
      collectorInstance: event.collectorInstance,
      rootFingerprint: event.rootFingerprint,
      sessionId: event.sessionId,
      scope:
        event.subagentId === undefined
          ? Object.freeze({ kind: "root" as const })
          : Object.freeze({ kind: "subagent" as const, subagentId: event.subagentId }),
    });
    const existingIndex = this.sessions.findIndex((session) =>
      sameSessionIdentity(session.identity, identity),
    );
    const previous = existingIndex >= 0 ? this.sessions.splice(existingIndex, 1)[0] : undefined;
    const retainedModel = event.model ?? previous?.model;
    const session: CodexObservedSession = Object.freeze({
      identity,
      lastEventType: event.eventType,
      lastReceivedAt: event.receivedAt,
      lastReceiptSequence: event.receiptSequence,
      ...(retainedModel === undefined ? {} : { model: retainedModel }),
    });
    this.sessions.unshift(session);
    if (this.sessions.length > MAX_DISPLAYED_SESSIONS) {
      this.sessions.length = MAX_DISPLAYED_SESSIONS;
    }
  }

  private hasReplay(collectorInstance: string, deliveryId: string): boolean {
    return this.replayByCollector.get(collectorInstance)?.has(deliveryId) === true;
  }

  private rememberReplay(collectorInstance: string, deliveryId: string): void {
    let deliveries = this.replayByCollector.get(collectorInstance);
    if (deliveries === undefined) {
      deliveries = new Map<string, true>();
      this.replayByCollector.set(collectorInstance, deliveries);
    }
    deliveries.set(deliveryId, true);
    this.replayOrder.push({ collectorInstance, deliveryId });
    while (this.replayOrder.length > MAX_REPLAY_ENTRIES) {
      const removed = this.replayOrder.shift()!;
      const collectorDeliveries = this.replayByCollector.get(removed.collectorInstance);
      collectorDeliveries?.delete(removed.deliveryId);
      if (collectorDeliveries?.size === 0) {
        this.replayByCollector.delete(removed.collectorInstance);
      }
    }
  }

  private scheduleFreshnessTransition(): void {
    if (this.freshnessTimer !== undefined) {
      clearTimeout(this.freshnessTimer);
    }
    this.freshnessTimer = setTimeout(() => {
      this.freshnessTimer = undefined;
      if (this.snapshot().state === "stale") {
        this.emitChange();
      }
    }, FRESHNESS_MS + 1);
    this.freshnessTimer.unref();
  }

  private async publishDescriptor(epoch: number): Promise<void> {
    this.assertLifecycleCurrent(epoch);
    const serverAddress = this.server?.address();
    if (serverAddress === undefined || serverAddress === null || typeof serverAddress === "string") {
      throw new Error("Listener address is unavailable.");
    }
    const now = this.clock.wallNow();
    this.leaseExpiresAt = now + DESCRIPTOR_LEASE_MS;
    const descriptor: CollectorDescriptor = {
      schema_version: CODEX_REGISTRY_PROTOCOL,
      owner: CODEX_MONITOR_OWNER,
      observer_sha256: CODEX_OBSERVER_SHA256,
      source: CODEX_SOURCE_ID,
      canonical_root: this.canonicalRoot,
      root_fingerprint: this.rootFingerprintValue,
      collector_instance: this.collectorInstance,
      secret: base64Url(this.secret!),
      port: serverAddress.port,
      issued_at: this.issuedAt,
      lease_expires_at: new Date(this.leaseExpiresAt).toISOString(),
    };
    const encoded = canonicalJson(descriptor);
    if (encoded.length > 16 * 1024) {
      throw new Error("Collector descriptor exceeded its internal limit.");
    }

    const generation = randomUUID();
    const temporary = join(
      this.registryDirectory,
      `.aio-codex-${this.collectorInstance}-${generation}.tmp`,
    );
    const target = join(
      this.registryDirectory,
      `aio-codex-${this.collectorInstance}-${generation}.json`,
    );
    let renamed = false;
    try {
      const handle = await open(temporary, "wx", 0o600);
      try {
        this.assertLifecycleCurrent(epoch);
        await handle.writeFile(encoded);
        this.assertLifecycleCurrent(epoch);
        await handle.sync();
        this.assertLifecycleCurrent(epoch);
      } finally {
        await handle.close();
      }
      this.assertLifecycleCurrent(epoch);
      await chmod(temporary, 0o600);
      this.assertLifecycleCurrent(epoch);
      await rename(temporary, target);
      renamed = true;
      this.assertLifecycleCurrent(epoch);
      const published = await lstat(target);
      this.assertLifecycleCurrent(epoch);
      if (!published.isFile() || published.isSymbolicLink()) {
        throw new Error("Published collector descriptor is not a regular file.");
      }
    } catch (error) {
      await unlink(renamed ? target : temporary).catch(() => undefined);
      throw error;
    }
    this.ownedDescriptorPaths.add(target);
    const previous = this.descriptorPath;
    this.descriptorPath = target;
    if (previous !== undefined) {
      try {
        await unlink(previous);
        this.ownedDescriptorPaths.delete(previous);
      } catch {
        // The old generation has a short lease and remains tracked for stop.
      }
      this.assertLifecycleCurrent(epoch);
    }
  }

  private renewDescriptor(): Promise<void> {
    if (this.renewalInFlight !== undefined) {
      return this.renewalInFlight;
    }
    if (this.listenerState !== "listening") {
      return Promise.resolve();
    }
    const epoch = this.lifecycleEpoch;
    let failed = false;
    const operation = (async () => {
      try {
        await this.publishDescriptor(epoch);
        this.assertLifecycleCurrent(epoch);
      } catch (error) {
        if (!(error instanceof LifecycleSuperseded) && this.lifecycleIsCurrent(epoch)) {
          failed = true;
        }
      }
    })();
    this.renewalInFlight = operation;
    void operation.finally(() => {
      if (this.renewalInFlight === operation) {
        this.renewalInFlight = undefined;
      }
      if (failed && this.lifecycleIsCurrent(epoch)) {
        void this.fail();
      }
    });
    return operation;
  }

  private async fail(): Promise<void> {
    if (this.baseState === "error" || this.stopping !== undefined) {
      return;
    }
    this.errorMessage = safeErrorMessage();
    await this.stop("error");
  }

  private async performStop(
    reason: CodexMonitorStopReason,
    pendingStart: Promise<CodexMonitorSnapshot> | undefined,
    pendingRenewal: Promise<void> | undefined,
  ): Promise<CodexMonitorSnapshot> {
    if (this.renewalTimer !== undefined) {
      clearInterval(this.renewalTimer);
      this.renewalTimer = undefined;
    }
    if (this.freshnessTimer !== undefined) {
      clearTimeout(this.freshnessTimer);
      this.freshnessTimer = undefined;
    }
    await Promise.allSettled(
      [pendingStart, pendingRenewal].filter((item) => item !== undefined),
    );
    // Invalidate registry discovery before closing the listener.
    await Promise.all(
      [...this.ownedDescriptorPaths].map(async (pathValue) => {
        try {
          const info = await lstat(pathValue);
          if (info.isFile() && !info.isSymbolicLink()) {
            await unlink(pathValue);
          }
        } catch (error) {
          if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
            // Lease expiry and mutual authentication remain the fallback.
          }
        }
      }),
    );
    this.ownedDescriptorPaths.clear();
    this.descriptorPath = undefined;
    for (const socket of this.sockets) {
      socket.destroy();
    }
    this.sockets.clear();
    const server = this.server;
    this.server = undefined;
    await closeServer(server).catch(() => undefined);
    this.secret?.fill(0);
    this.secret = undefined;
    this.listenerState = reason === "error" ? "error" : "stopped";
    this.baseState = reason === "error" ? "error" : "disconnected";
    if (reason === "error") {
      this.errorMessage = safeErrorMessage();
    } else {
      this.errorMessage = undefined;
    }
    this.clearMemory();
    this.emitChange();
    return this.snapshot();
  }

  private lifecycleIsCurrent(epoch: number): boolean {
    return !this.disposed && epoch === this.lifecycleEpoch;
  }

  private assertLifecycleCurrent(epoch: number): void {
    if (!this.lifecycleIsCurrent(epoch)) {
      throw new LifecycleSuperseded();
    }
  }

  private async cleanupAfterFailedStart(): Promise<void> {
    for (const pathValue of this.ownedDescriptorPaths) {
      await unlink(pathValue).catch(() => undefined);
    }
    this.ownedDescriptorPaths.clear();
    this.descriptorPath = undefined;
    for (const socket of this.sockets) {
      socket.destroy();
    }
    this.sockets.clear();
    await closeServer(this.server).catch(() => undefined);
    this.server = undefined;
    this.secret?.fill(0);
    this.secret = undefined;
    this.clearMemory();
  }

  private clearMemory(): void {
    this.events.length = 0;
    this.sessions.length = 0;
    this.replayByCollector.clear();
    this.replayOrder.length = 0;
    this.attemptTimes.length = 0;
    this.receiptSequence = 0;
    this.lastReceivedAt = undefined;
    this.lastReceivedMonotonic = undefined;
  }

  private emitChange(): void {
    if (this.onDidChange === undefined) {
      return;
    }
    try {
      this.onDidChange(this.snapshot());
    } catch {
      // UI callback failures cannot affect intake or Codex hook behavior.
    }
  }
}
