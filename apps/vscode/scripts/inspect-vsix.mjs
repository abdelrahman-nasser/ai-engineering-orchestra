import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { inflateRawSync } from "node:zlib";

const MAX_ARCHIVE_BYTES = 64 * 1024 * 1024;
const MAX_ENTRIES = 4_096;
const MAX_ENTRY_BYTES = 4 * 1024 * 1024;
const MAX_TOTAL_UNCOMPRESSED_BYTES = 16 * 1024 * 1024;
const EOCD_SIGNATURE = 0x06054b50;
const CENTRAL_SIGNATURE = 0x02014b50;
const LOCAL_SIGNATURE = 0x04034b50;

const requiredFiles = new Set([
  "[Content_Types].xml",
  "extension.vsixmanifest",
  "extension/package.json",
  "extension/readme.md",
  "extension/media/activity.svg",
  "extension/observer/codex_hook_observer.py",
  "extension/out/src/extension.js",
  "extension/out/src/monitoring/codex/constants.js",
  "extension/webview/main.js",
  "extension/webview/styles.css",
]);

const forbiddenSegments = new Set([
  ".ai",
  ".cache",
  ".git",
  ".npm",
  ".vscode-test",
  "__pycache__",
  "build",
  "coverage",
  "dist",
  "downloads",
  "fixtures",
  "hook_outputs",
  "node_modules",
  "sessions",
  "tests",
  "transcripts",
]);

const sensitiveBasenames = /^(?:\.env(?:\..+)?|credentials?(?:\..+)?|id_(?:rsa|dsa|ecdsa|ed25519)(?:\.pub)?|secrets?(?:\..+)?|.*\.(?:key|p12|pfx|pem))$/iu;
const pythonCheckoutBasenames = /^(?:pyproject\.toml|setup\.cfg|setup\.py)$/iu;
const homePathPatterns = [
  /[A-Za-z]:[\\/](?:Users|Documents and Settings)[\\/][^\\/\s"'<>]+/u,
  /(?:^|[\s"'(])\/(?:home|Users)\/[A-Za-z0-9._-]+(?:\/|[\s"')])/u,
  /\\\\[^\\\s]+\\(?:Users|home)\\[^\\\s"'<>]+/iu,
];
const credentialPatterns = [
  /-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----/u,
  /\bAKIA[0-9A-Z]{16}\b/u,
  /\bgh[opusr]_[A-Za-z0-9]{20,}\b/u,
  /\bsk-[A-Za-z0-9_-]{20,}\b/u,
  /\bxox[baprs]-[A-Za-z0-9-]{20,}\b/u,
];

function fail(message) {
  throw new Error(`VSIX inspection failed: ${message}`);
}

function requireBounds(buffer, offset, length, label) {
  if (!Number.isSafeInteger(offset) || !Number.isSafeInteger(length) || offset < 0 || length < 0 || offset + length > buffer.length) {
    fail(`${label} is outside the archive bounds.`);
  }
}

function findEndOfCentralDirectory(buffer) {
  const firstCandidate = Math.max(0, buffer.length - 65_557);
  for (let offset = buffer.length - 22; offset >= firstCandidate; offset -= 1) {
    if (buffer.readUInt32LE(offset) !== EOCD_SIGNATURE) {
      continue;
    }
    requireBounds(buffer, offset, 22, "end-of-central-directory record");
    const commentLength = buffer.readUInt16LE(offset + 20);
    if (offset + 22 + commentLength === buffer.length) {
      return offset;
    }
  }
  fail("the ZIP end-of-central-directory record is missing or malformed");
}

function decodeName(bytes) {
  const value = bytes.toString("utf8");
  if (value.includes("\uFFFD") || Buffer.from(value, "utf8").compare(bytes) !== 0) {
    fail("an archive entry name is not canonical UTF-8");
  }
  return value;
}

function validatePath(name) {
  if (!name || name.includes("\\") || name.includes("\0") || name.startsWith("/") || name.startsWith("//") || /^[A-Za-z]:/u.test(name)) {
    fail(`unsafe archive path: ${JSON.stringify(name)}`);
  }
  const isDirectory = name.endsWith("/");
  const trimmed = isDirectory ? name.slice(0, -1) : name;
  const parts = trimmed.split("/");
  if (parts.some((part) => !part || part === "." || part === ".." || /[\u0000-\u001F\u007F]/u.test(part))) {
    fail(`non-canonical archive path: ${JSON.stringify(name)}`);
  }

  const foldedParts = parts.map((part) => part.toLowerCase());
  const basename = parts.at(-1) ?? "";
  if (foldedParts.some((part) => forbiddenSegments.has(part))) {
    fail(`forbidden evidence, session, dependency, cache, or test path: ${name}`);
  }
  if (sensitiveBasenames.test(basename)) {
    fail(`credential-like file is not permitted: ${name}`);
  }
  if (foldedParts.includes("engineering_orchestration") || pythonCheckoutBasenames.test(basename)) {
    fail(`Python checkout content is not permitted: ${name}`);
  }
  if (/\.(?:pyc|pyo|whl)$/iu.test(basename)) {
    fail(`Python build/runtime artifact is not permitted: ${name}`);
  }
  if (/\.py$/iu.test(basename) && name !== "extension/observer/codex_hook_observer.py") {
    fail(`only the pinned observer Python asset is permitted: ${name}`);
  }
  if (/\.(?:map|ts|tsx)$/iu.test(basename)) {
    fail(`source or source-map output is not permitted: ${name}`);
  }

  if (isDirectory) {
    if (!/^extension(?:\/(?:media|observer|out(?:\/src(?:\/[A-Za-z0-9._-]+)*)?|webview))?\/$/u.test(name)) {
      fail(`unexpected directory entry: ${name}`);
    }
    return;
  }

  const allowed = requiredFiles.has(name)
    || /^extension\/out\/src\/(?:[A-Za-z0-9._-]+\/)*[A-Za-z0-9._-]+\.js$/u.test(name);
  if (!allowed) {
    fail(`unexpected file (including source, dependency, cache, or unrelated documentation): ${name}`);
  }
}

function parseCentralDirectory(buffer) {
  const eocd = findEndOfCentralDirectory(buffer);
  const disk = buffer.readUInt16LE(eocd + 4);
  const centralDisk = buffer.readUInt16LE(eocd + 6);
  const entriesOnDisk = buffer.readUInt16LE(eocd + 8);
  const entryCount = buffer.readUInt16LE(eocd + 10);
  const centralSize = buffer.readUInt32LE(eocd + 12);
  const centralOffset = buffer.readUInt32LE(eocd + 16);
  if (disk !== 0 || centralDisk !== 0 || entriesOnDisk !== entryCount) {
    fail("multi-disk ZIP archives are not permitted");
  }
  if (entryCount === 0 || entryCount === 0xffff || centralSize === 0xffffffff || centralOffset === 0xffffffff) {
    fail("empty and ZIP64 archives are not permitted");
  }
  if (entryCount > MAX_ENTRIES) {
    fail(`archive contains more than ${MAX_ENTRIES} entries`);
  }
  requireBounds(buffer, centralOffset, centralSize, "central directory");
  if (centralOffset + centralSize > eocd) {
    fail("central directory overlaps its trailer");
  }

  const entries = [];
  const names = new Set();
  const foldedNames = new Set();
  let offset = centralOffset;
  let totalUncompressed = 0;
  for (let index = 0; index < entryCount; index += 1) {
    requireBounds(buffer, offset, 46, "central directory entry");
    if (buffer.readUInt32LE(offset) !== CENTRAL_SIGNATURE) {
      fail(`invalid central directory signature at entry ${index}`);
    }
    const flags = buffer.readUInt16LE(offset + 8);
    const method = buffer.readUInt16LE(offset + 10);
    const compressedSize = buffer.readUInt32LE(offset + 20);
    const uncompressedSize = buffer.readUInt32LE(offset + 24);
    const nameLength = buffer.readUInt16LE(offset + 28);
    const extraLength = buffer.readUInt16LE(offset + 30);
    const commentLength = buffer.readUInt16LE(offset + 32);
    const diskStart = buffer.readUInt16LE(offset + 34);
    const localOffset = buffer.readUInt32LE(offset + 42);
    const recordLength = 46 + nameLength + extraLength + commentLength;
    requireBounds(buffer, offset, recordLength, "central directory entry data");
    if ((flags & 0x1) !== 0) {
      fail("encrypted ZIP entries are not permitted");
    }
    if (![0, 8].includes(method)) {
      fail(`unsupported compression method ${method}`);
    }
    if (diskStart !== 0 || compressedSize === 0xffffffff || uncompressedSize === 0xffffffff || localOffset === 0xffffffff) {
      fail("multi-disk and ZIP64 entries are not permitted");
    }
    if (uncompressedSize > MAX_ENTRY_BYTES) {
      fail(`entry ${index} exceeds the ${MAX_ENTRY_BYTES}-byte limit`);
    }
    totalUncompressed += uncompressedSize;
    if (totalUncompressed > MAX_TOTAL_UNCOMPRESSED_BYTES) {
      fail(`expanded archive exceeds ${MAX_TOTAL_UNCOMPRESSED_BYTES} bytes`);
    }
    const name = decodeName(buffer.subarray(offset + 46, offset + 46 + nameLength));
    validatePath(name);
    const folded = name.toLowerCase();
    if (names.has(name) || foldedNames.has(folded)) {
      fail(`duplicate or Windows-colliding archive path: ${name}`);
    }
    names.add(name);
    foldedNames.add(folded);
    entries.push({ name, flags, method, compressedSize, uncompressedSize, localOffset });
    offset += recordLength;
  }
  if (offset !== centralOffset + centralSize) {
    fail("central directory length does not match its declared size");
  }
  return entries;
}

function extractEntry(buffer, entry) {
  requireBounds(buffer, entry.localOffset, 30, `local header for ${entry.name}`);
  if (buffer.readUInt32LE(entry.localOffset) !== LOCAL_SIGNATURE) {
    fail(`invalid local header for ${entry.name}`);
  }
  const localFlags = buffer.readUInt16LE(entry.localOffset + 6);
  const localMethod = buffer.readUInt16LE(entry.localOffset + 8);
  const nameLength = buffer.readUInt16LE(entry.localOffset + 26);
  const extraLength = buffer.readUInt16LE(entry.localOffset + 28);
  if (localFlags !== entry.flags || localMethod !== entry.method) {
    fail(`central/local header mismatch for ${entry.name}`);
  }
  requireBounds(buffer, entry.localOffset + 30, nameLength + extraLength, `local name for ${entry.name}`);
  const localName = decodeName(buffer.subarray(entry.localOffset + 30, entry.localOffset + 30 + nameLength));
  if (localName !== entry.name) {
    fail(`central/local name mismatch for ${entry.name}`);
  }
  const dataOffset = entry.localOffset + 30 + nameLength + extraLength;
  requireBounds(buffer, dataOffset, entry.compressedSize, `compressed data for ${entry.name}`);
  const compressed = buffer.subarray(dataOffset, dataOffset + entry.compressedSize);
  let expanded;
  try {
    expanded = entry.method === 0
      ? Buffer.from(compressed)
      : inflateRawSync(compressed, { maxOutputLength: MAX_ENTRY_BYTES });
  } catch (error) {
    fail(`cannot expand ${entry.name}: ${error instanceof Error ? error.message : String(error)}`);
  }
  if (expanded.length !== entry.uncompressedSize) {
    fail(`expanded size mismatch for ${entry.name}`);
  }
  return expanded;
}

function inspectText(name, bytes) {
  if (!/\.(?:css|js|json|md|py|svg|xml)$/iu.test(name) && name !== "extension.vsixmanifest") {
    return;
  }
  const text = bytes.toString("utf8");
  if (text.includes("\uFFFD")) {
    fail(`text asset is not valid UTF-8: ${name}`);
  }
  for (const pattern of homePathPatterns) {
    if (pattern.test(text)) {
      fail(`host home path leaked into ${name}`);
    }
  }
  for (const pattern of credentialPatterns) {
    if (pattern.test(text)) {
      fail(`credential-like material found in ${name}`);
    }
  }
}

async function main() {
  const argument = process.argv[2];
  if (!argument || process.argv.length !== 3) {
    fail("usage: node scripts/inspect-vsix.mjs <path-to-vsix>");
  }
  const archive = await readFile(argument);
  if (archive.length === 0 || archive.length > MAX_ARCHIVE_BYTES) {
    fail(`archive must be between 1 and ${MAX_ARCHIVE_BYTES} bytes`);
  }
  const entries = parseCentralDirectory(archive);
  const files = new Map();
  for (const entry of entries) {
    if (entry.name.endsWith("/")) {
      continue;
    }
    const bytes = extractEntry(archive, entry);
    inspectText(entry.name, bytes);
    files.set(entry.name, bytes);
  }

  for (const required of requiredFiles) {
    if (!files.has(required)) {
      fail(`required runtime asset is missing: ${required}`);
    }
  }

  let packageDocument;
  try {
    packageDocument = JSON.parse(files.get("extension/package.json").toString("utf8"));
  } catch (error) {
    fail(`extension/package.json is invalid: ${error instanceof Error ? error.message : String(error)}`);
  }
  if (packageDocument.name !== "aio-control-center-dev" || packageDocument.publisher !== "aio-local-dev" || packageDocument.version !== "0.0.1" || packageDocument.private !== true) {
    fail("package identity must remain the explicit local development identity");
  }
  if (Object.hasOwn(packageDocument, "license")) {
    fail("a license has not been selected for this development package");
  }

  const constants = files.get("extension/out/src/monitoring/codex/constants.js").toString("utf8");
  const pinnedHash = constants.match(/CODEX_OBSERVER_SHA256\s*=\s*["']([0-9a-f]{64})["']/u)?.[1];
  if (!pinnedHash) {
    fail("compiled observer SHA-256 pin is missing");
  }
  const observerHash = createHash("sha256")
    .update(files.get("extension/observer/codex_hook_observer.py"))
    .digest("hex");
  if (observerHash !== pinnedHash) {
    fail("bundled observer does not match the compiled SHA-256 pin");
  }

  console.log(`VSIX inspection passed: ${entries.length} entries, ${archive.length} archive bytes.`);
  for (const name of [...files.keys()].sort()) {
    console.log(name);
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
