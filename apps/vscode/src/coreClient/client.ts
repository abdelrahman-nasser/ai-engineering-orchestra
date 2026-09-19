import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { randomUUID } from "node:crypto";
import path from "node:path";
import type {
  BridgeOperation,
  BridgeRequest,
  BridgeResponse,
  BridgeResult,
  ProjectSnapshotPayload,
  TaskDetailPayload,
} from "./protocol";
import {
  IDE_PROTOCOL,
  SUPPORTED_CORE_PACKAGE_VERSION,
  isProjectSnapshotResult,
  isTaskDetailResult,
  parseBridgeResponse,
} from "./protocol";
import { assertPackageOriginOutsideProject, canonicalRegularFile } from "./scope";

const STDOUT_LIMIT = 2 * 1024 * 1024;
const STDERR_LIMIT = 16 * 1024;
const PROBE_OUTPUT_LIMIT = 4 * 1024;
const TIMEOUT_MS = 10_000;
const PACKAGE_ORIGIN_PROBE = [
  "import importlib.util,json,pathlib",
  "s=importlib.util.find_spec('engineering_orchestration')",
  "o=None if s is None or s.origin is None else str(pathlib.Path(s.origin).resolve().parent)",
  "print(json.dumps({'package_origin':o},separators=(',',':')))",
].join(";");

export type SpawnBridge = (
  executable: string,
  args: readonly string[],
  options: {
    cwd: string;
    env: NodeJS.ProcessEnv;
    shell: false;
    windowsHide: true;
  },
) => ChildProcessWithoutNullStreams;

export class CoreClientError extends Error {
  public constructor(
    public readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = "CoreClientError";
  }
}

export interface CoreCall<T extends BridgeResult> {
  requestId: string;
  generation: number;
  response: BridgeResponse<T>;
}

export interface CoreClientOptions {
  workingDirectory: string;
  spawnBridge?: SpawnBridge;
  timeoutMs?: number;
}

function cleanEnvironment(): NodeJS.ProcessEnv {
  const environment: NodeJS.ProcessEnv = { ...process.env };
  for (const key of ["PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONINSPECT"] as const) {
    delete environment[key];
  }
  environment.PYTHONUTF8 = "1";
  environment.PYTHONDONTWRITEBYTECODE = "1";
  return environment;
}

export class CoreClient {
  private readonly spawnBridge: SpawnBridge;
  private readonly timeoutMs: number;

  public constructor(private readonly options: CoreClientOptions) {
    this.spawnBridge = options.spawnBridge ?? ((executable, args, spawnOptions) => spawn(
      executable,
      [...args],
      spawnOptions,
    ));
    this.timeoutMs = options.timeoutMs ?? TIMEOUT_MS;
  }

  public async request<T extends BridgeResult>(
    pythonPath: string,
    projectRoot: string,
    operation: BridgeOperation,
    payload: ProjectSnapshotPayload | TaskDetailPayload,
    generation: number,
  ): Promise<CoreCall<T>> {
    const executable = await canonicalRegularFile(pythonPath).catch((error: unknown) => {
      throw new CoreClientError("missing_interpreter", error instanceof Error ? error.message : String(error));
    });
    const requestId = randomUUID();
    const request: BridgeRequest = {
      protocol: IDE_PROTOCOL,
      request_id: requestId,
      operation,
      project_root: projectRoot,
      payload,
    };
    const probedOrigin = await this.probePackageOrigin(executable, projectRoot);
    const response = await this.run<T>(executable, request);
    const responseOrigin = await assertPackageOriginOutsideProject(response.meta.package_origin, projectRoot).catch((error: unknown) => {
      throw new CoreClientError("unsafe_package_origin", error instanceof Error ? error.message : String(error));
    });
    if (path.relative(probedOrigin, responseOrigin) !== "") {
      throw new CoreClientError(
        "unsafe_package_origin",
        "Core package origin changed between the interpreter preflight and bridge response.",
      );
    }
    if (response.meta.package_version !== SUPPORTED_CORE_PACKAGE_VERSION) {
      throw new CoreClientError(
        "incompatible_core",
        `Core package version ${response.meta.package_version || "<empty>"} is incompatible; `
        + `this extension supports exactly ${SUPPORTED_CORE_PACKAGE_VERSION}.`,
      );
    }
    if (response.request_id !== requestId) {
      throw new CoreClientError("request_mismatch", "Core bridge response did not match the active request.");
    }
    return { requestId, generation, response };
  }

  private async probePackageOrigin(executable: string, projectRoot: string): Promise<string> {
    const packageOrigin = await new Promise<string>((resolve, reject) => {
      let child: ChildProcessWithoutNullStreams;
      try {
        child = this.spawnBridge(
          executable,
          ["-I", "-B", "-X", "utf8", "-c", PACKAGE_ORIGIN_PROBE],
          {
            cwd: path.resolve(this.options.workingDirectory),
            env: cleanEnvironment(),
            shell: false,
            windowsHide: true,
          },
        );
      } catch (error) {
        reject(new CoreClientError("process_start", error instanceof Error ? error.message : String(error)));
        return;
      }

      let stdoutBytes = 0;
      let stderrBytes = 0;
      const stdout: Buffer[] = [];
      const stderr: Buffer[] = [];
      let finished = false;

      const finishWithError = (error: CoreClientError): void => {
        if (finished) return;
        finished = true;
        clearTimeout(timer);
        child.kill();
        reject(error);
      };
      const timer = setTimeout(() => {
        finishWithError(new CoreClientError("timeout", "Core package-origin preflight exceeded the request timeout."));
      }, this.timeoutMs);

      child.stdout.on("data", (chunk: Buffer) => {
        stdoutBytes += chunk.length;
        if (stdoutBytes > PROBE_OUTPUT_LIMIT) {
          finishWithError(new CoreClientError("stdout_limit", "Core package-origin preflight stdout exceeded 4 KiB."));
          return;
        }
        stdout.push(chunk);
      });
      child.stderr.on("data", (chunk: Buffer) => {
        stderrBytes += chunk.length;
        if (stderrBytes > PROBE_OUTPUT_LIMIT) {
          finishWithError(new CoreClientError("stderr_limit", "Core package-origin preflight stderr exceeded 4 KiB."));
          return;
        }
        stderr.push(chunk);
      });
      child.on("error", (error) => {
        finishWithError(new CoreClientError("process_start", error.message));
      });
      child.stdin.on("error", (error) => {
        finishWithError(new CoreClientError("process_failure", `Core package-origin preflight input failed: ${error.message}`));
      });
      child.on("close", (code) => {
        if (finished) return;
        finished = true;
        clearTimeout(timer);
        const stderrText = Buffer.concat(stderr).toString("utf8").trim();
        if (code !== 0) {
          reject(new CoreClientError(
            "process_failure",
            `Core package-origin preflight exited with code ${String(code)}${stderrText ? `: ${stderrText}` : "."}`,
          ));
          return;
        }
        if (stderrText) {
          reject(new CoreClientError("unexpected_stderr", "Core package-origin preflight wrote diagnostics to stderr."));
          return;
        }
        try {
          const parsed: unknown = JSON.parse(Buffer.concat(stdout).toString("utf8"));
          if (
            typeof parsed !== "object"
            || parsed === null
            || Array.isArray(parsed)
            || Object.keys(parsed).length !== 1
            || !("package_origin" in parsed)
          ) {
            throw new Error("Package-origin preflight returned the wrong object shape.");
          }
          const origin = (parsed as { package_origin: unknown }).package_origin;
          if (origin === null) {
            reject(new CoreClientError(
              "missing_core",
              "The selected interpreter does not contain an installed AI Engineering Orchestra Core.",
            ));
            return;
          }
          if (typeof origin !== "string") {
            throw new Error("Package-origin preflight did not return a string origin.");
          }
          resolve(origin);
        } catch (error) {
          reject(new CoreClientError("malformed_response", error instanceof Error ? error.message : String(error)));
        }
      });

      child.stdin.end();
    });

    return assertPackageOriginOutsideProject(packageOrigin, projectRoot).catch((error: unknown) => {
      throw new CoreClientError("unsafe_package_origin", error instanceof Error ? error.message : String(error));
    });
  }

  private run<T extends BridgeResult>(executable: string, request: BridgeRequest): Promise<BridgeResponse<T>> {
    return new Promise((resolve, reject) => {
      let child: ChildProcessWithoutNullStreams;
      try {
        child = this.spawnBridge(
          executable,
          ["-I", "-B", "-X", "utf8", "-m", "engineering_orchestration.ide_bridge"],
          {
            cwd: path.resolve(this.options.workingDirectory),
            env: cleanEnvironment(),
            shell: false,
            windowsHide: true,
          },
        );
      } catch (error) {
        reject(new CoreClientError("process_start", error instanceof Error ? error.message : String(error)));
        return;
      }

      let stdoutBytes = 0;
      let stderrBytes = 0;
      const stdout: Buffer[] = [];
      const stderr: Buffer[] = [];
      let finished = false;

      const finishWithError = (error: CoreClientError): void => {
        if (finished) {
          return;
        }
        finished = true;
        clearTimeout(timer);
        child.kill();
        reject(error);
      };

      const timer = setTimeout(() => {
        finishWithError(new CoreClientError("timeout", "Core bridge exceeded the 10-second request timeout."));
      }, this.timeoutMs);

      child.stdout.on("data", (chunk: Buffer) => {
        stdoutBytes += chunk.length;
        if (stdoutBytes > STDOUT_LIMIT) {
          finishWithError(new CoreClientError("stdout_limit", "Core bridge stdout exceeded 2 MiB."));
          return;
        }
        stdout.push(chunk);
      });
      child.stderr.on("data", (chunk: Buffer) => {
        stderrBytes += chunk.length;
        if (stderrBytes > STDERR_LIMIT) {
          finishWithError(new CoreClientError("stderr_limit", "Core bridge stderr exceeded 16 KiB."));
          return;
        }
        stderr.push(chunk);
      });
      child.on("error", (error) => {
        finishWithError(new CoreClientError("process_start", error.message));
      });
      child.stdin.on("error", (error) => {
        finishWithError(new CoreClientError("process_failure", `Core bridge input failed: ${error.message}`));
      });
      child.on("close", (code) => {
        if (finished) {
          return;
        }
        finished = true;
        clearTimeout(timer);
        const stderrText = Buffer.concat(stderr).toString("utf8").trim();
        if (code !== 0) {
          const missing = /No module named ['\"]?engineering_orchestration/i.test(stderrText);
          reject(new CoreClientError(
            missing ? "missing_core" : "process_failure",
            missing
              ? "The selected interpreter does not contain an installed AI Engineering Orchestra Core."
              : `Core bridge exited with code ${String(code)}${stderrText ? `: ${stderrText}` : "."}`,
          ));
          return;
        }
        if (stderrText) {
          reject(new CoreClientError("unexpected_stderr", "Core bridge wrote unexpected diagnostics to stderr."));
          return;
        }
        try {
          const response = parseBridgeResponse(Buffer.concat(stdout).toString("utf8"));
          if (response.ok) {
            const expectedResult = request.operation === "project_snapshot"
              ? isProjectSnapshotResult(response.result)
              : isTaskDetailResult(response.result);
            if (!expectedResult) {
              throw new Error(`Core bridge returned the wrong result for ${request.operation}.`);
            }
          }
          resolve(response as BridgeResponse<T>);
        } catch (error) {
          reject(new CoreClientError(
            "malformed_response",
            error instanceof Error ? error.message : String(error),
          ));
        }
      });

      child.stdin.end(JSON.stringify(request), "utf8");
    });
  }
}
