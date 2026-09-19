import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

import { runTests } from "@vscode/test-electron";

async function main(): Promise<void> {
  const extensionDevelopmentPath = path.resolve(__dirname, "../../..");
  const extensionTestsPath = path.resolve(__dirname, "suite", "index.js");
  const fixturePath = path.join(extensionDevelopmentPath, "tests", "fixtures", "external-project");
  const userDataDirectory = await mkdtemp(path.join(tmpdir(), "aio-vscode-profile-"));
  const extensionsDirectory = await mkdtemp(path.join(tmpdir(), "aio-vscode-extensions-"));
  const vscodeExecutablePath = process.env.AIO_TEST_VSCODE_EXECUTABLE;
  const electronRunAsNode = process.env.ELECTRON_RUN_AS_NODE;
  try {
    // The Codex host itself uses Electron's Node mode. An Extension Development
    // Host must not inherit that launcher-only setting.
    delete process.env.ELECTRON_RUN_AS_NODE;
    await runTests({
      extensionDevelopmentPath,
      extensionTestsPath,
      ...(vscodeExecutablePath ? { vscodeExecutablePath } : {}),
      launchArgs: [
        fixturePath,
        "--disable-workspace-trust",
        "--skip-welcome",
        "--skip-release-notes",
        "--user-data-dir",
        userDataDirectory,
        "--extensions-dir",
        extensionsDirectory,
      ],
    });
  } finally {
    if (electronRunAsNode === undefined) {
      delete process.env.ELECTRON_RUN_AS_NODE;
    } else {
      process.env.ELECTRON_RUN_AS_NODE = electronRunAsNode;
    }
    await rm(userDataDirectory, {
      recursive: true,
      force: true,
      maxRetries: 5,
      retryDelay: 100,
    });
    await rm(extensionsDirectory, {
      recursive: true,
      force: true,
      maxRetries: 5,
      retryDelay: 100,
    });
  }
}

void main().catch((error: unknown) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
