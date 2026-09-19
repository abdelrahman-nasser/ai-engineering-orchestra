import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { mkdtemp, mkdir, realpath, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { PassThrough } from "node:stream";
import test from "node:test";
import type { ChildProcessWithoutNullStreams } from "node:child_process";

import {
  CoreClient,
  CoreClientError,
  type SpawnBridge,
} from "../../src/coreClient/client";
import type { ProjectSnapshotResult, TaskDetailResult } from "../../src/coreClient/protocol";

interface Fixture {
  directory: string;
  python: string;
  project: string;
  origin: string;
}

class FakeChild extends EventEmitter {
  public readonly stdin = new PassThrough();
  public readonly stdout = new PassThrough();
  public readonly stderr = new PassThrough();
  public killed = false;

  public kill(): boolean {
    this.killed = true;
    return true;
  }
}

async function fixture(): Promise<Fixture> {
  const directory = await mkdtemp(path.join(tmpdir(), "aio-core-client-"));
  const project = path.join(directory, "project");
  const origin = path.join(directory, "installed-core", "engineering_orchestration");
  const python = path.join(directory, process.platform === "win32" ? "python.exe" : "python");
  await mkdir(project, { recursive: true });
  await mkdir(origin, { recursive: true });
  await writeFile(python, "synthetic executable marker", "utf8");
  return { directory, python, project, origin };
}

function snapshotResult(): ProjectSnapshotResult {
  return {
    project: { state: "managed", id: "synthetic", name: "Synthetic" },
    snapshot_at: "2026-09-19T00:00:00Z",
    tasks: [],
    anomalies: [],
    filters: { statuses: [], workflows: [] },
    validation: { status: "PASS", findings: [] },
  };
}

function bridgeSuccess(
  requestId: string,
  origin: string,
  result: ProjectSnapshotResult | TaskDetailResult = snapshotResult(),
  packageVersion = "0.1.0",
): string {
  return JSON.stringify({
    protocol: "aio.ide/1",
    request_id: requestId,
    ok: true,
    meta: { package_version: packageVersion, package_origin: origin },
    result,
    diagnostics: [],
  });
}

function bridgeFailure(requestId: string, origin: string, packageVersion: string): string {
  return JSON.stringify({
    protocol: "aio.ide/1",
    request_id: requestId,
    ok: false,
    meta: { package_version: packageVersion, package_origin: origin },
    error: { code: "internal_error", message: "Synthetic failure" },
    diagnostics: [],
  });
}

function syntheticSpawn(
  probeOrigin: string | null,
  onRequest: (child: FakeChild, request: Record<string, unknown>) => void,
  inspect?: (executable: string, args: readonly string[], options: Parameters<SpawnBridge>[2]) => void,
): SpawnBridge {
  return (executable, args, options) => {
    inspect?.(executable, args, options);
    const child = new FakeChild();
    if (args.includes("-c")) {
      queueMicrotask(() => {
        child.stdout.end(JSON.stringify({ package_origin: probeOrigin }));
        child.emit("close", 0);
      });
      child.stdin.end();
      return child as unknown as ChildProcessWithoutNullStreams;
    }
    const chunks: Buffer[] = [];
    child.stdin.on("data", (chunk: Buffer) => chunks.push(chunk));
    child.stdin.on("finish", () => {
      const request = JSON.parse(Buffer.concat(chunks).toString("utf8")) as Record<string, unknown>;
      queueMicrotask(() => onRequest(child, request));
    });
    return child as unknown as ChildProcessWithoutNullStreams;
  };
}

async function snapshotRequest(client: CoreClient, data: Fixture): Promise<unknown> {
  return client.request<ProjectSnapshotResult>(
    data.python,
    data.project,
    "project_snapshot",
    { status: null, workflow: null },
    4,
  );
}

test("Core bridge launch is isolated, bounded, and uses argument arrays", async () => {
  const data = await fixture();
  const previousPythonPath = process.env.PYTHONPATH;
  const previousPythonHome = process.env.PYTHONHOME;
  process.env.PYTHONPATH = "hostile-shadow";
  process.env.PYTHONHOME = "hostile-home";
  try {
    const canonicalPython = await realpath(data.python);
    let inspected = false;
    const launches: string[][] = [];
    const spawnBridge = syntheticSpawn(data.origin, (child, request) => {
      child.stdout.end(bridgeSuccess(String(request.request_id), data.origin));
      child.emit("close", 0);
    }, (executable, args, options) => {
      inspected = true;
      launches.push([...args]);
      assert.equal(executable, canonicalPython);
      assert.equal(options.shell, false);
      assert.equal(options.windowsHide, true);
      assert.equal(options.env.PYTHONPATH, undefined);
      assert.equal(options.env.PYTHONHOME, undefined);
      assert.equal(options.env.PYTHONUTF8, "1");
    });
    const result = await snapshotRequest(new CoreClient({ workingDirectory: data.directory, spawnBridge }), data);
    assert.equal((result as { generation: number }).generation, 4);
    assert.equal(inspected, true);
    assert.equal(launches.length, 2);
    assert.deepEqual(launches[0]?.slice(0, 5), ["-I", "-B", "-X", "utf8", "-c"]);
    assert.match(launches[0]?.[5] ?? "", /find_spec\('engineering_orchestration'\)/u);
    assert.doesNotMatch(launches[0]?.[5] ?? "", /(?:from|import)\s+engineering_orchestration/u);
    assert.deepEqual(launches[1], ["-I", "-B", "-X", "utf8", "-m", "engineering_orchestration.ide_bridge"]);
  } finally {
    if (previousPythonPath === undefined) delete process.env.PYTHONPATH;
    else process.env.PYTHONPATH = previousPythonPath;
    if (previousPythonHome === undefined) delete process.env.PYTHONHOME;
    else process.env.PYTHONHOME = previousPythonHome;
    await rm(data.directory, { recursive: true, force: true });
  }
});

test("Core package origins inside the selected checkout are rejected", async () => {
  const data = await fixture();
  const insideOrigin = path.join(data.project, "engineering_orchestration");
  await mkdir(insideOrigin, { recursive: true });
  try {
    let bridgeLaunches = 0;
    const spawnBridge = syntheticSpawn(insideOrigin, (child, request) => {
      bridgeLaunches += 1;
      child.stdout.end(bridgeSuccess(String(request.request_id), insideOrigin));
      child.emit("close", 0);
    });
    await assert.rejects(
      snapshotRequest(new CoreClient({ workingDirectory: data.directory, spawnBridge }), data),
      (error: unknown) => error instanceof CoreClientError && error.code === "unsafe_package_origin",
    );
    assert.equal(bridgeLaunches, 0, "project package code must not execute before origin rejection");
  } finally {
    await rm(data.directory, { recursive: true, force: true });
  }
});

test("post-bridge origin is verified before version and request identity", async (t) => {
  for (const competingFailure of ["version", "request_id"] as const) {
    await t.test(competingFailure, async () => {
      const data = await fixture();
      const insideOrigin = path.join(data.project, "response-core", "engineering_orchestration");
      await mkdir(insideOrigin, { recursive: true });
      try {
        const spawnBridge = syntheticSpawn(data.origin, (child, request) => {
          const requestId = competingFailure === "request_id" ? "different-request" : String(request.request_id);
          const packageVersion = competingFailure === "version" ? "0.2.0" : "0.1.0";
          child.stdout.end(bridgeSuccess(requestId, insideOrigin, snapshotResult(), packageVersion));
          child.emit("close", 0);
        });
        await assert.rejects(
          snapshotRequest(new CoreClient({ workingDirectory: data.directory, spawnBridge }), data),
          (error: unknown) => error instanceof CoreClientError && error.code === "unsafe_package_origin",
        );
      } finally {
        await rm(data.directory, { recursive: true, force: true });
      }
    });
  }
});

test("unsupported Core versions are incompatible for success and error responses", async (t) => {
  for (const responseKind of ["success", "error"] as const) {
    await t.test(responseKind, async () => {
      const data = await fixture();
      try {
        const spawnBridge = syntheticSpawn(data.origin, (child, request) => {
          const requestId = String(request.request_id);
          child.stdout.end(responseKind === "success"
            ? bridgeSuccess(requestId, data.origin, snapshotResult(), "0.2.0")
            : bridgeFailure(requestId, data.origin, "0.2.0"));
          child.emit("close", 0);
        });
        await assert.rejects(
          snapshotRequest(new CoreClient({ workingDirectory: data.directory, spawnBridge }), data),
          (error: unknown) => error instanceof CoreClientError
            && error.code === "incompatible_core"
            && /supports exactly 0\.1\.0/u.test(error.message),
        );
      } finally {
        await rm(data.directory, { recursive: true, force: true });
      }
    });
  }
});

test("Core client rejects a valid result for the wrong requested operation", async () => {
  const data = await fixture();
  const taskDetail: TaskDetailResult = {
    task: {
      id: "SYN-001",
      title: "Synthetic",
      type: "implementation",
      status: "in_progress",
      workflow: null,
      workflow_resolution: "NOT_DECLARED",
      schema_status: "VALID",
      artifact_health: {
        task_yaml: true,
        context_md: true,
        acceptance_criteria_md: true,
        review_md: true,
      },
      resource_id: "task-opaque",
    },
    effective: {
      risk: { value: null, source: "Default" },
      complexity: { value: null, source: "Default" },
      execution_mode: { value: null, source: "Default" },
      quality_gates: [],
      human_control: {},
    },
    artifacts: [],
    workflow: null,
  };
  try {
    const spawnBridge = syntheticSpawn(data.origin, (child, request) => {
      child.stdout.end(bridgeSuccess(String(request.request_id), data.origin, taskDetail));
      child.emit("close", 0);
    });
    await assert.rejects(
      snapshotRequest(new CoreClient({ workingDirectory: data.directory, spawnBridge }), data),
      (error: unknown) => error instanceof CoreClientError
        && error.code === "malformed_response"
        && /wrong result for project_snapshot/u.test(error.message),
    );
  } finally {
    await rm(data.directory, { recursive: true, force: true });
  }
});

test("missing Core, timeout, and oversized stdout are distinct host errors", async (t) => {
  await t.test("missing Core", async () => {
    const data = await fixture();
    try {
      const spawnBridge = syntheticSpawn(null, (child) => {
        child.stderr.end("No module named 'engineering_orchestration'");
        child.emit("close", 1);
      });
      await assert.rejects(
        snapshotRequest(new CoreClient({ workingDirectory: data.directory, spawnBridge }), data),
        (error: unknown) => error instanceof CoreClientError && error.code === "missing_core",
      );
    } finally {
      await rm(data.directory, { recursive: true, force: true });
    }
  });

  await t.test("timeout", async () => {
    const data = await fixture();
    try {
      const spawnBridge = syntheticSpawn(data.origin, () => undefined);
      await assert.rejects(
        snapshotRequest(new CoreClient({ workingDirectory: data.directory, spawnBridge, timeoutMs: 5 }), data),
        (error: unknown) => error instanceof CoreClientError && error.code === "timeout",
      );
    } finally {
      await rm(data.directory, { recursive: true, force: true });
    }
  });

  await t.test("stdout limit", async () => {
    const data = await fixture();
    try {
      const spawnBridge = syntheticSpawn(data.origin, (child) => {
        child.stdout.write(Buffer.alloc(2 * 1024 * 1024 + 1));
      });
      await assert.rejects(
        snapshotRequest(new CoreClient({ workingDirectory: data.directory, spawnBridge }), data),
        (error: unknown) => error instanceof CoreClientError && error.code === "stdout_limit",
      );
    } finally {
      await rm(data.directory, { recursive: true, force: true });
    }
  });
});
