import assert from "node:assert/strict";
import { randomBytes, randomUUID } from "node:crypto";
import { mkdtemp, readFile, readdir, rm } from "node:fs/promises";
import { connect, type Socket } from "node:net";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import {
  CODEX_SOURCE_ID,
  CODEX_WIRE_PROTOCOL,
  CodexMonitor,
  type CodexMonitorClock,
} from "../../src/monitoring/codex";
import {
  base64Url,
  canonicalJson,
  hmacProof,
  proofMatches,
  readFrame,
  sha256Hex,
  writeFrame,
} from "../../src/monitoring/codex/protocol";

interface TestDescriptor {
  collector_instance: string;
  root_fingerprint: string;
  secret: string;
  port: number;
}

interface TestEvent {
  source: typeof CODEX_SOURCE_ID;
  collector_instance: string;
  root_fingerprint: string;
  delivery_id: string;
  session_id: string;
  event_type: "PostToolUse" | "SessionStart";
  turn_id?: string;
  tool_call_id?: string;
  tool_label?: string;
  model?: string;
  prompt?: string;
}

interface MonitorLifecycleAccess {
  publishDescriptor(epoch: number): Promise<void>;
  renewDescriptor(): Promise<void>;
}

function deferred(): { readonly promise: Promise<void>; readonly resolve: () => void } {
  let resolvePromise: (() => void) | undefined;
  const promise = new Promise<void>((resolve) => {
    resolvePromise = resolve;
  });
  return { promise, resolve: () => resolvePromise?.() };
}

async function withTempDirectory(run: (directory: string) => Promise<void>): Promise<void> {
  const directory = await mkdtemp(join(tmpdir(), "aio-monitor-transport-"));
  try {
    await run(directory);
  } finally {
    await rm(directory, { force: true, recursive: true });
  }
}

async function descriptorFrom(registry: string): Promise<TestDescriptor> {
  const names = (await readdir(registry)).filter((name) => name.endsWith(".json"));
  assert.equal(names.length, 1);
  return JSON.parse(await readFile(join(registry, names[0]!), "utf8")) as TestDescriptor;
}

async function openSocket(port: number): Promise<Socket> {
  return new Promise((resolveSocket, rejectSocket) => {
    const socket = connect({ host: "127.0.0.1", port }, () => resolveSocket(socket));
    socket.once("error", rejectSocket);
  });
}

async function sendAuthenticatedEvent(
  descriptor: TestDescriptor,
  event: TestEvent,
  proofSecret?: Buffer,
): Promise<"accepted" | "replay" | "rejected"> {
  const socket = await openSocket(descriptor.port);
  const secret = proofSecret ?? Buffer.from(descriptor.secret, "base64url");
  try {
    const clientNonce = base64Url(randomBytes(32));
    await writeFrame(socket, {
      protocol: CODEX_WIRE_PROTOCOL,
      type: "client_hello",
      collector_instance: descriptor.collector_instance,
      root_fingerprint: descriptor.root_fingerprint,
      client_nonce: clientNonce,
      proof: hmacProof(secret, [
        CODEX_WIRE_PROTOCOL,
        "client",
        descriptor.collector_instance,
        descriptor.root_fingerprint,
        clientNonce,
      ]),
    });
    let challenge: Record<string, unknown>;
    try {
      challenge = (await readFrame(socket, 500)) as Record<string, unknown>;
    } catch {
      return "rejected";
    }
    const serverNonce = challenge.server_nonce;
    if (typeof serverNonce !== "string") {
      return "rejected";
    }
    const expectedChallenge = hmacProof(secret, [
      CODEX_WIRE_PROTOCOL,
      "server",
      descriptor.collector_instance,
      descriptor.root_fingerprint,
      clientNonce,
      serverNonce,
    ]);
    assert.equal(proofMatches(challenge.proof, expectedChallenge), true);
    await writeFrame(socket, {
      protocol: CODEX_WIRE_PROTOCOL,
      type: "event",
      event,
      proof: hmacProof(secret, [
        CODEX_WIRE_PROTOCOL,
        "event",
        descriptor.collector_instance,
        descriptor.root_fingerprint,
        clientNonce,
        serverNonce,
        sha256Hex(canonicalJson(event)),
      ]),
    });
    try {
      const acknowledgement = (await readFrame(socket, 500)) as Record<string, unknown>;
      return acknowledgement.status as "accepted" | "replay";
    } catch {
      return "rejected";
    }
  } catch {
    return "rejected";
  } finally {
    socket.destroy();
  }
}

function makeEvent(
  descriptor: TestDescriptor,
  sessionId: string,
  deliveryId = randomUUID(),
): TestEvent {
  return {
    source: CODEX_SOURCE_ID,
    collector_instance: descriptor.collector_instance,
    root_fingerprint: descriptor.root_fingerprint,
    delivery_id: deliveryId,
    session_id: sessionId,
    event_type: "PostToolUse",
    turn_id: `turn-${sessionId}`,
    tool_call_id: `call-${deliveryId}`,
    tool_label: "apply_patch",
    model: "source-reported-model",
  };
}

test("monitor mutually authenticates, rejects non-allowlisted data, and handles replay", async (context) => {
  if (process.platform !== "win32") {
    context.skip("AIO-030 monitoring is Windows-only.");
    return;
  }
  await withTempDirectory(async (directory) => {
    const root = join(directory, "project");
    const registry = join(directory, "registry");
    const { mkdir } = await import("node:fs/promises");
    await mkdir(root);
    const monitor = new CodexMonitor({ registryDirectory: registry, canonicalRoot: root });
    assert.equal((await monitor.start()).state, "configured_no_observations");
    const descriptor = await descriptorFrom(registry);

    const unauthorized = await sendAuthenticatedEvent(
      descriptor,
      makeEvent(descriptor, "session-unauthorized"),
      randomBytes(32),
    );
    assert.equal(unauthorized, "rejected");
    assert.equal(monitor.snapshot().events.length, 0);

    const overFielded = { ...makeEvent(descriptor, "session-private"), prompt: "must never enter" };
    assert.equal(await sendAuthenticatedEvent(descriptor, overFielded), "rejected");
    assert.equal(monitor.snapshot().events.length, 0);

    const deliveryId = randomUUID();
    const event = makeEvent(descriptor, "session-1", deliveryId);
    assert.equal(await sendAuthenticatedEvent(descriptor, event), "accepted");
    assert.equal(await sendAuthenticatedEvent(descriptor, event), "replay");
    const snapshot = monitor.snapshot();
    assert.equal(snapshot.state, "receiving");
    assert.equal(snapshot.events.length, 1);
    assert.equal(snapshot.events[0]?.receiptSequence, 1);
    assert.equal(snapshot.events[0]?.sessionId, "session-1");
    assert.equal("prompt" in (snapshot.events[0] ?? {}), false);
    assert.equal(snapshot.sessions.length, 1);
    await monitor.stop();
    assert.equal((await readdir(registry)).filter((name) => name.endsWith(".json")).length, 0);
    assert.equal(monitor.snapshot().events.length, 0);
    assert.equal(monitor.snapshot().state, "disconnected");
  });
});

test("monitor bounds timeline and sessions, orders by receipt, reports stale, and rotates on restart", async (context) => {
  if (process.platform !== "win32") {
    context.skip("AIO-030 monitoring is Windows-only.");
    return;
  }
  await withTempDirectory(async (directory) => {
    const { mkdir } = await import("node:fs/promises");
    const root = join(directory, "project");
    const registry = join(directory, "registry");
    await mkdir(root);
    let wall = Date.UTC(2026, 8, 19, 0, 0, 0);
    let monotonic = 0;
    const clock: CodexMonitorClock = {
      wallNow: () => wall,
      monotonicNow: () => monotonic,
    };
    const monitor = new CodexMonitor({ registryDirectory: registry, canonicalRoot: root, clock });
    await monitor.start();
    const firstDescriptor = await descriptorFrom(registry);
    for (let index = 0; index < 205; index += 1) {
      monotonic += 1_001;
      const result = await sendAuthenticatedEvent(
        firstDescriptor,
        makeEvent(firstDescriptor, `session-${index % 25}`),
      );
      assert.equal(result, "accepted");
    }
    let snapshot = monitor.snapshot();
    assert.equal(snapshot.events.length, 200);
    assert.equal(snapshot.sessions.length, 20);
    assert.equal(snapshot.events[0]?.receiptSequence, 6);
    assert.equal(snapshot.events.at(-1)?.receiptSequence, 205);
    assert.equal(snapshot.sessions[0]?.identity.sessionId, "session-4");

    monotonic += 5 * 60_000;
    assert.equal(monitor.snapshot().state, "stale");
    await monitor.stop();
    wall += 1_000;
    monotonic += 1_000;
    await monitor.start();
    const secondDescriptor = await descriptorFrom(registry);
    assert.notEqual(secondDescriptor.collector_instance, firstDescriptor.collector_instance);
    snapshot = monitor.snapshot();
    assert.equal(snapshot.events.length, 0);
    assert.equal(snapshot.state, "configured_no_observations");
    await monitor.dispose();
  });
});

test("concurrent starts serialize descriptor publication", async (context) => {
  if (process.platform !== "win32") {
    context.skip("AIO-030 monitoring is Windows-only.");
    return;
  }
  await withTempDirectory(async (directory) => {
    const { mkdir } = await import("node:fs/promises");
    const root = join(directory, "project");
    const registry = join(directory, "registry");
    await mkdir(root);
    const monitor = new CodexMonitor({ registryDirectory: registry, canonicalRoot: root });
    const lifecycle = monitor as unknown as MonitorLifecycleAccess;
    const publish = lifecycle.publishDescriptor.bind(monitor);
    let publications = 0;
    lifecycle.publishDescriptor = async (epoch) => {
      publications += 1;
      await publish(epoch);
    };

    const [first, second] = await Promise.all([monitor.start(), monitor.start()]);
    assert.equal(first.listener, "listening");
    assert.equal(second.listener, "listening");
    assert.equal(publications, 1);
    assert.equal((await readdir(registry)).filter((name) => name.endsWith(".json")).length, 1);
    await monitor.dispose();
  });
});

test("stop invalidates a start paused before descriptor publication", async (context) => {
  if (process.platform !== "win32") {
    context.skip("AIO-030 monitoring is Windows-only.");
    return;
  }
  await withTempDirectory(async (directory) => {
    const { mkdir } = await import("node:fs/promises");
    const root = join(directory, "project");
    const registry = join(directory, "registry");
    await mkdir(root);
    const monitor = new CodexMonitor({ registryDirectory: registry, canonicalRoot: root });
    const lifecycle = monitor as unknown as MonitorLifecycleAccess;
    const publish = lifecycle.publishDescriptor.bind(monitor);
    const entered = deferred();
    const release = deferred();
    lifecycle.publishDescriptor = async (epoch) => {
      entered.resolve();
      await release.promise;
      await publish(epoch);
    };

    const starting = monitor.start();
    await entered.promise;
    const stopping = monitor.stop("user");
    release.resolve();
    await Promise.all([starting, stopping]);

    assert.equal(monitor.snapshot().listener, "stopped");
    assert.equal(monitor.snapshot().state, "disconnected");
    assert.equal((await readdir(registry)).filter((name) => name.endsWith(".json")).length, 0);
    await monitor.dispose();
  });
});

test("stop waits for and invalidates a paused descriptor renewal", async (context) => {
  if (process.platform !== "win32") {
    context.skip("AIO-030 monitoring is Windows-only.");
    return;
  }
  await withTempDirectory(async (directory) => {
    const { mkdir } = await import("node:fs/promises");
    const root = join(directory, "project");
    const registry = join(directory, "registry");
    await mkdir(root);
    const monitor = new CodexMonitor({ registryDirectory: registry, canonicalRoot: root });
    await monitor.start();
    const lifecycle = monitor as unknown as MonitorLifecycleAccess;
    const publish = lifecycle.publishDescriptor.bind(monitor);
    const entered = deferred();
    const release = deferred();
    lifecycle.publishDescriptor = async (epoch) => {
      entered.resolve();
      await release.promise;
      await publish(epoch);
    };

    const renewal = lifecycle.renewDescriptor();
    await entered.promise;
    const stopping = monitor.stop("user");
    release.resolve();
    await Promise.all([renewal, stopping]);

    assert.equal(monitor.snapshot().listener, "stopped");
    assert.equal((await readdir(registry)).filter((name) => name.endsWith(".json")).length, 0);
    await monitor.dispose();
  });
});

test("listener rate limit rejects excess attempts and recovers after its monotonic window", async (context) => {
  if (process.platform !== "win32") {
    context.skip("AIO-030 monitoring is Windows-only.");
    return;
  }
  await withTempDirectory(async (directory) => {
    const { mkdir } = await import("node:fs/promises");
    const root = join(directory, "project");
    const registry = join(directory, "registry");
    await mkdir(root);
    let monotonic = 0;
    const clock: CodexMonitorClock = {
      wallNow: () => Date.UTC(2026, 8, 19, 0, 0, 0),
      monotonicNow: () => monotonic,
    };
    const monitor = new CodexMonitor({ registryDirectory: registry, canonicalRoot: root, clock });
    await monitor.start();
    const descriptor = await descriptorFrom(registry);
    for (let attempt = 0; attempt < 120; attempt += 1) {
      assert.equal(
        await sendAuthenticatedEvent(
          descriptor,
          makeEvent(descriptor, `unauthorized-${attempt}`),
          randomBytes(32),
        ),
        "rejected",
      );
    }
    assert.equal(
      await sendAuthenticatedEvent(descriptor, makeEvent(descriptor, "rate-limited")),
      "rejected",
    );
    assert.equal(monitor.snapshot().events.length, 0);
    monotonic = 60_001;
    assert.equal(
      await sendAuthenticatedEvent(descriptor, makeEvent(descriptor, "after-window")),
      "accepted",
    );
    assert.equal(monitor.snapshot().events.length, 1);
    await monitor.dispose();
  });
});

test("unsupported platforms do not bind or publish descriptors", async (context) => {
  if (process.platform === "win32") {
    context.skip("The production platform is supported in this run.");
    return;
  }
  await withTempDirectory(async (directory) => {
    const monitor = new CodexMonitor({
      registryDirectory: join(directory, "registry"),
      canonicalRoot: directory,
    });
    const snapshot = await monitor.start();
    assert.equal(snapshot.state, "unsupported");
    assert.equal(snapshot.listener, "stopped");
    await monitor.dispose();
  });
});
