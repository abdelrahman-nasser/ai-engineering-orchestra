import { createHash, createHmac, timingSafeEqual } from "node:crypto";
import type { Socket } from "node:net";
import { TextDecoder } from "node:util";

import { MAX_FRAME_BYTES } from "./constants";

export class ProtocolViolation extends Error {
  public constructor() {
    super("Invalid Codex monitor transport message.");
    this.name = "ProtocolViolation";
  }
}

function canonicalValue(value: unknown): unknown {
  if (value === null || typeof value === "string" || typeof value === "boolean") {
    return value;
  }
  if (typeof value === "number") {
    if (!Number.isFinite(value)) {
      throw new ProtocolViolation();
    }
    return value;
  }
  if (Array.isArray(value)) {
    return value.map(canonicalValue);
  }
  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    const result: Record<string, unknown> = {};
    for (const key of Object.keys(record).sort()) {
      const item = record[key];
      if (item === undefined) {
        throw new ProtocolViolation();
      }
      result[key] = canonicalValue(item);
    }
    return result;
  }
  throw new ProtocolViolation();
}

export function canonicalJson(value: unknown): Buffer {
  return Buffer.from(JSON.stringify(canonicalValue(value)), "utf8");
}

export function sha256Hex(value: Buffer | string): string {
  return createHash("sha256").update(value).digest("hex");
}

export function hmacProof(secret: Buffer, parts: readonly string[]): string {
  return createHmac("sha256", secret).update(parts.join("\n"), "utf8").digest("hex");
}

export function proofMatches(actual: unknown, expected: string): boolean {
  if (typeof actual !== "string" || !/^[0-9a-f]{64}$/.test(actual)) {
    return false;
  }
  return timingSafeEqual(Buffer.from(actual, "ascii"), Buffer.from(expected, "ascii"));
}

export function base64Url(value: Buffer): string {
  return value.toString("base64url");
}

export function writeFrame(socket: Socket, value: unknown): Promise<void> {
  const encoded = canonicalJson(value);
  if (encoded.length === 0 || encoded.length > MAX_FRAME_BYTES) {
    return Promise.reject(new ProtocolViolation());
  }
  const header = Buffer.allocUnsafe(4);
  header.writeUInt32BE(encoded.length, 0);
  return new Promise((resolve, reject) => {
    socket.write(Buffer.concat([header, encoded]), (error?: Error | null) => {
      if (error) {
        reject(error);
      } else {
        resolve();
      }
    });
  });
}

export function readFrame(socket: Socket, timeoutMs = 1_000): Promise<unknown> {
  return new Promise((resolve, reject) => {
    let buffered = Buffer.alloc(0);
    let expectedLength: number | undefined;
    let settled = false;

    const finish = (error?: Error, value?: unknown): void => {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timer);
      socket.off("data", onData);
      socket.off("error", onError);
      socket.off("close", onClose);
      if (error) {
        reject(error);
      } else {
        resolve(value);
      }
    };
    const onError = (): void => finish(new ProtocolViolation());
    const onClose = (): void => finish(new ProtocolViolation());
    const onData = (chunk: Buffer): void => {
      if (buffered.length + chunk.length > MAX_FRAME_BYTES + 4) {
        finish(new ProtocolViolation());
        return;
      }
      buffered = Buffer.concat([buffered, chunk]);
      if (expectedLength === undefined && buffered.length >= 4) {
        expectedLength = buffered.readUInt32BE(0);
        if (expectedLength <= 0 || expectedLength > MAX_FRAME_BYTES) {
          finish(new ProtocolViolation());
          return;
        }
      }
      if (expectedLength !== undefined && buffered.length >= expectedLength + 4) {
        if (buffered.length !== expectedLength + 4) {
          finish(new ProtocolViolation());
          return;
        }
        try {
          const payload = buffered.subarray(4);
          const text = new TextDecoder("utf-8", { fatal: true }).decode(payload);
          const value = JSON.parse(text) as unknown;
          // The observer and listener both write canonical JSON. Requiring the
          // canonical representation also rejects duplicate keys and ambiguous
          // alternate encodings before any authenticated value is consumed.
          if (!canonicalJson(value).equals(payload)) {
            finish(new ProtocolViolation());
            return;
          }
          finish(undefined, value);
        } catch {
          finish(new ProtocolViolation());
        }
      }
    };
    const timer = setTimeout(() => finish(new ProtocolViolation()), timeoutMs);
    timer.unref();
    socket.on("data", onData);
    socket.once("error", onError);
    socket.once("close", onClose);
  });
}

export function isClosedRecord(
  value: unknown,
  requiredKeys: readonly string[],
  optionalKeys: readonly string[] = [],
): value is Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return false;
  }
  const keys = Object.keys(value as object);
  const allowed = new Set([...requiredKeys, ...optionalKeys]);
  return requiredKeys.every((key) => keys.includes(key)) && keys.every((key) => allowed.has(key));
}
