import { spawnSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import * as fsModule from "node:fs";
const fs = fsModule.default ?? fsModule;
import * as path from "node:path";
import type {
  ExtensionAPI,
  ExtensionContext,
} from "@earendil-works/pi-coding-agent";

const SCHEMA = 1;
export const DARWIN_HELPER_REQUEST_MAX_BYTES = 16 * 1024;
export const DARWIN_HELPER_RESPONSE_MAX_BYTES = 16 * 1024;
export const SESSION_ID_MAX_BYTES = 256;
export const SESSION_PATH_MAX_BYTES = 4096;
const DIRECTORY_FLAGS =
  fs.constants.O_RDONLY | fs.constants.O_DIRECTORY | fs.constants.O_NOFOLLOW;
type PiProcess = {
  env: Record<string, string | undefined>;
  pid: number;
  platform: string;
  getuid: () => number;
};
type PublishResult =
  | { published: true }
  | {
      published: false;
      reason:
        | "tmux_pane_missing"
        | "session_reference_missing"
        | "unsupported_platform"
        | "secure_storage_unavailable"
        | "helper_missing"
        | "helper_build_failure"
        | "helper_process_failure"
        | "process_identity_unavailable"
        | "tty_unavailable"
        | "proc_permission_denied"
        | "process_identity_stale"
        | "invalid_request";
    };
type DarwinHelperReply =
  | { ok: true }
  | {
      ok: true;
      kind: string;
      value: string;
      pid: number;
      start_time: string;
    }
  | { ok: false; reason: string };
const DARWIN_HELPER_FAILURE_REASONS = {
  publish: new Set([
    "denied",
    "invalid",
    "io",
    "no_tty",
    "stale",
    "unsupported",
  ]),
  resolve: new Set([
    "ambiguous_beacons",
    "beacon_missing",
    "denied",
    "invalid",
    "io",
    "no_tty",
    "process_disappeared",
    "process_tree_too_large",
    "stale",
    "unsupported",
  ]),
};
type BeaconOptions = {
  platform?: string;
  darwinHelper?: (action: string, request: string) => string;
  processStartIdentity?: (pid: number) => string | undefined;
  openPrivateDirectory?: (target: string, uid?: number) => number;
  publishBeaconFile?: (
    directoryFd: number,
    pid: number,
    payload: string,
    uid?: number,
  ) => void;
};

class SecureStorageUnavailableError extends Error {
  readonly code = "secure_storage_unavailable";
}
const piProcess = (globalThis as typeof globalThis & { process: PiProcess })
  .process;

export function beaconDirectory(
  env: Record<string, string | undefined>,
): string | undefined {
  const runtime = env.XDG_RUNTIME_DIR;
  if (runtime && path.isAbsolute(runtime))
    return path.join(runtime, "pi-herdr-sessions");
  const home = env.HOME;
  if (home && path.isAbsolute(home))
    return path.join(home, ".cache", "pi-herdr-sessions");
  return undefined;
}

class DarwinHelperError extends Error {
  readonly reason:
    | "helper_missing"
    | "helper_build_failure"
    | "helper_process_failure";

  constructor(
    reason:
      | "helper_missing"
      | "helper_build_failure"
      | "helper_process_failure",
  ) {
    super(reason);
    this.reason = reason;
  }
}

function darwinHelperPath(
  env: Record<string, string | undefined>,
): string | undefined {
  const home = env.HOME;
  return home && path.isAbsolute(home)
    ? path.join(home, ".local", "libexec", "tmux-herdr-darwin-helper")
    : undefined;
}

export function validateDarwinHelper(helper: string): void {
  let info: fs.Stats;
  let parent: fs.Stats;
  try {
    info = fs.lstatSync(helper);
    parent = fs.lstatSync(path.dirname(helper));
  } catch {
    throw new DarwinHelperError("helper_missing");
  }
  if (
    !parent.isDirectory() ||
    parent.uid !== piProcess.getuid() ||
    (parent.mode & 0o777) !== 0o700 ||
    !info.isFile() ||
    info.uid !== piProcess.getuid() ||
    info.nlink !== 1 ||
    (info.mode & 0o777) !== 0o700
  ) {
    throw new DarwinHelperError("helper_build_failure");
  }
}

function topLevelJsonKeys(text: string): string[] | undefined {
  let index = 0;
  const keys: string[] = [];
  const skipWhitespace = () => {
    while (/\s/u.test(text[index] ?? "")) index += 1;
  };
  const skipString = () => {
    if (text[index] !== '"') return false;
    index += 1;
    while (index < text.length) {
      if (text[index] === "\\") index += 2;
      else if (text[index++] === '"') return true;
    }
    return false;
  };
  skipWhitespace();
  if (text[index++] !== "{") return undefined;
  for (;;) {
    skipWhitespace();
    if (text[index] === "}") {
      index += 1;
      skipWhitespace();
      return index === text.length ? keys : undefined;
    }
    const keyStart = index;
    if (!skipString()) return undefined;
    const key = JSON.parse(text.slice(keyStart, index)) as unknown;
    if (typeof key !== "string") return undefined;
    keys.push(key);
    skipWhitespace();
    if (text[index++] !== ":") return undefined;
    skipWhitespace();
    let depth = 0;
    while (index < text.length) {
      if (text[index] === '"') {
        if (!skipString()) return undefined;
        continue;
      }
      if (text[index] === "{" || text[index] === "[") depth += 1;
      else if (text[index] === "}" || text[index] === "]") {
        if (depth === 0) break;
        depth -= 1;
      } else if (text[index] === "," && depth === 0) {
        index += 1;
        break;
      }
      index += 1;
    }
    if (index >= text.length) return undefined;
  }
}

export function runDarwinHelper(
  action: string,
  request: string,
  options: BeaconOptions,
): DarwinHelperReply {
  if (Buffer.byteLength(request, "utf8") > DARWIN_HELPER_REQUEST_MAX_BYTES)
    throw new DarwinHelperError("helper_process_failure");
  let output: string;
  let exitStatus: number | undefined;
  if (options.darwinHelper) {
    output = options.darwinHelper(action, request);
  } else {
    const helper = darwinHelperPath(piProcess.env);
    if (!helper) throw new DarwinHelperError("helper_missing");
    validateDarwinHelper(helper);
    const result = spawnSync(helper, [action], {
      input: request,
      encoding: "utf8",
      timeout: 1500,
      maxBuffer: DARWIN_HELPER_RESPONSE_MAX_BYTES,
      shell: false,
      env: { PATH: "/usr/bin:/bin" },
      stdio: ["pipe", "pipe", "ignore"],
    });
    if (result.error || result.signal)
      throw new DarwinHelperError("helper_process_failure");
    exitStatus = result.status ?? undefined;
    output = result.stdout;
  }
  if (Buffer.byteLength(output, "utf8") > DARWIN_HELPER_RESPONSE_MAX_BYTES)
    throw new DarwinHelperError("helper_process_failure");
  try {
    const reply = JSON.parse(output) as Record<string, unknown>;
    const keys = topLevelJsonKeys(output);
    if (!keys || keys.length !== new Set(keys).size)
      throw new Error("duplicate");
    if (typeof reply.ok !== "boolean") throw new Error("malformed");
    if (exitStatus !== undefined && (exitStatus === 0) !== (reply.ok === true))
      throw new Error("status mismatch");
    if (!reply.ok) {
      if (
        keys.length !== 2 ||
        !keys.includes("reason") ||
        typeof reply.reason !== "string" ||
        !(
          DARWIN_HELPER_FAILURE_REASONS[
            action === "publish" ? "publish" : "resolve"
          ] as Set<string>
        ).has(reply.reason)
      )
        throw new Error("malformed");
      return reply as DarwinHelperReply;
    }
    if (action === "publish") {
      if (keys.length !== 1) throw new Error("malformed");
      return reply as DarwinHelperReply;
    }
    if (
      keys.length !== 5 ||
      !keys.includes("kind") ||
      !keys.includes("value") ||
      !keys.includes("pid") ||
      !keys.includes("start_time") ||
      typeof reply.kind !== "string" ||
      typeof reply.value !== "string" ||
      typeof reply.pid !== "number" ||
      !Number.isInteger(reply.pid) ||
      reply.pid <= 0 ||
      typeof reply.start_time !== "string" ||
      !/^[0-9]+\.[0-9]{6}$/.test(reply.start_time)
    )
      throw new Error("malformed");
    return reply as DarwinHelperReply;
  } catch {
    throw new DarwinHelperError("helper_process_failure");
  }
}

function publishDarwinBeacon(
  paneId: string,
  sessionRef: { kind: "path" | "id"; value: string },
  options: BeaconOptions,
): PublishResult {
  const directory = beaconDirectory(piProcess.env);
  if (!directory)
    return { published: false, reason: "secure_storage_unavailable" };
  const request = JSON.stringify({
    v: 1,
    op: "publish",
    directory,
    publisher_pid: piProcess.pid,
    pane_id: paneId,
    session_kind: sessionRef.kind,
    session_value: sessionRef.value,
  });
  try {
    const reply = runDarwinHelper("publish", request, options);
    if (reply.ok) return { published: true };
    if (reply.reason === "unsupported")
      return { published: false, reason: "helper_build_failure" };
    if (reply.reason === "io")
      return { published: false, reason: "secure_storage_unavailable" };
    if (reply.reason === "no_tty")
      return { published: false, reason: "tty_unavailable" };
    if (reply.reason === "denied")
      return { published: false, reason: "proc_permission_denied" };
    if (reply.reason === "stale")
      return { published: false, reason: "process_identity_stale" };
    if (reply.reason === "invalid")
      return { published: false, reason: "invalid_request" };
    return { published: false, reason: "process_identity_unavailable" };
  } catch (error) {
    if (error instanceof DarwinHelperError)
      return { published: false, reason: error.reason };
    return { published: false, reason: "helper_process_failure" };
  }
}

function procFdChild(fd: number, name: string): string {
  return `/proc/self/fd/${fd}/${name}`;
}

/** Walk from / through pinned directory fds; all child operations stay on these inodes. */
export function openPrivateDirectory(
  target: string,
  uid = piProcess.getuid(),
  platform = piProcess.platform,
): number {
  if (platform !== "linux") {
    throw new SecureStorageUnavailableError(
      "descriptor-pinned beacon storage is unavailable on this platform",
    );
  }
  if (
    !path.isAbsolute(target) ||
    !fs.constants.O_NOFOLLOW ||
    !fs.constants.O_DIRECTORY
  ) {
    throw new SecureStorageUnavailableError(
      "safe beacon directory operations unavailable",
    );
  }
  let currentFd: number | undefined = fs.openSync("/", DIRECTORY_FLAGS);
  let nextFd: number | undefined = undefined;

  const closeFd = (fd: number | undefined): void => {
    if (fd !== undefined) {
      try {
        fs.closeSync(fd);
      } catch {
        // Do not mask existing errors
      }
    }
  };

  try {
    const components = path.resolve(target).split(path.sep).filter(Boolean);
    for (const [index, component] of components.entries()) {
      const child = procFdChild(currentFd!, component);
      try {
        nextFd = fs.openSync(child, DIRECTORY_FLAGS);
      } catch (error) {
        if ((error as { code?: string }).code !== "ENOENT") throw error;
        try {
          fs.mkdirSync(child, { mode: 0o700 });
        } catch (mkdirError) {
          if ((mkdirError as { code?: string }).code !== "EEXIST")
            throw mkdirError;
        }
        nextFd = fs.openSync(child, DIRECTORY_FLAGS);
      }
      const info = fs.fstatSync(nextFd);
      const final = index === components.length - 1;
      const trusted = final
        ? info.isDirectory() &&
          info.uid === uid &&
          (info.mode & 0o777) === 0o700
        : info.isDirectory() &&
          (info.uid === uid || info.uid === 0) &&
          ((info.mode & 0o022) === 0 ||
            (info.uid === 0 && (info.mode & 0o7777) === 0o1777));
      if (!trusted) {
        throw new Error("untrusted beacon directory");
      }
      const oldFd = currentFd;
      currentFd = undefined;
      fs.closeSync(oldFd!);
      currentFd = nextFd;
      nextFd = undefined;
    }
    const info = fs.fstatSync(currentFd!);
    if (!info.isDirectory() || info.uid !== uid)
      throw new Error("untrusted beacon directory");
    if ((info.mode & 0o777) !== 0o700) fs.fchmodSync(currentFd!, 0o700);
    const verified = fs.fstatSync(currentFd!);
    if (
      !verified.isDirectory() ||
      verified.uid !== uid ||
      (verified.mode & 0o777) !== 0o700
    ) {
      throw new Error("untrusted beacon directory");
    }
    const leafFd = currentFd!;
    currentFd = undefined;
    return leafFd;
  } catch (error) {
    const toCloseNext = nextFd;
    nextFd = undefined;
    closeFd(toCloseNext);

    const toCloseCurrent = currentFd;
    currentFd = undefined;
    closeFd(toCloseCurrent);

    throw error;
  }
}

/** Publish through a pinned directory descriptor; procfs-unavailable operations fail closed. */
export function publishBeaconFile(
  directoryFd: number,
  pid: number,
  payload: string,
  uid = piProcess.getuid(),
  platform = piProcess.platform,
): void {
  if (platform !== "linux") {
    throw new SecureStorageUnavailableError(
      "descriptor-pinned beacon storage is unavailable on this platform",
    );
  }
  const destination = `${pid}.json`;
  if (Buffer.byteLength(payload, "utf8") > 16 * 1024)
    throw new Error("beacon payload is oversized");
  const temporary = `.${pid}.${uid}.${randomBytes(16).toString("hex")}.tmp`;
  const temporaryPath = procFdChild(directoryFd, temporary);
  const destinationPath = procFdChild(directoryFd, destination);
  const fileFd = fs.openSync(
    temporaryPath,
    fs.constants.O_WRONLY |
      fs.constants.O_CREAT |
      fs.constants.O_EXCL |
      fs.constants.O_NOFOLLOW,
    0o600,
  );
  try {
    fs.fchmodSync(fileFd, 0o600);
    fs.writeFileSync(fileFd, payload, { encoding: "utf8" });
    fs.fsyncSync(fileFd);
    const info = fs.fstatSync(fileFd);
    if (
      !info.isFile() ||
      info.uid !== uid ||
      info.nlink !== 1 ||
      (info.mode & 0o777) !== 0o600 ||
      info.size !== Buffer.byteLength(payload, "utf8")
    )
      throw new Error("beacon temporary changed");
  } catch (error) {
    // Leave the unique temp file behind; pathname cleanup could unlink a replacement.
    throw error;
  } finally {
    fs.closeSync(fileFd);
  }
  try {
    fs.renameSync(temporaryPath, destinationPath);
    fs.fsyncSync(directoryFd);
  } catch (error) {
    // Leave the unique temp file behind; pathname cleanup could unlink a replacement.
    throw error;
  }
}

function processStartIdentity(pid: number): string | undefined {
  if (piProcess.platform !== "linux") return undefined;
  const raw = fs.readFileSync(`/proc/${pid}/stat`, "utf8");
  const close = raw.lastIndexOf(")");
  if (close < 0) return undefined;
  const fields = raw
    .slice(close + 1)
    .trim()
    .split(/\s+/);
  return fields.length >= 20 ? fields[19] : undefined;
}

export function sessionReference(
  ctx: ExtensionContext,
): { kind: "path" | "id"; value: string } | undefined {
  const home = piProcess.env.HOME;
  const sessionFile = ctx.sessionManager.getSessionFile();
  if (sessionFile && home && path.isAbsolute(home)) {
    try {
      const sessions = path.resolve(home, ".pi", "agent", "sessions");
      const realSessions = fs.realpathSync(sessions);
      const realFile = fs.realpathSync(sessionFile);
      const relative = path.relative(realSessions, realFile);
      const info = fs.statSync(realFile);
      if (
        relative &&
        !relative.startsWith(`..${path.sep}`) &&
        relative !== ".." &&
        !path.isAbsolute(relative) &&
        info.isFile() &&
        realFile.endsWith(".jsonl") &&
        !/[\u0000-\u001f\u007f]/u.test(realFile) &&
        Buffer.byteLength(realFile, "utf8") <= SESSION_PATH_MAX_BYTES &&
        info.uid === piProcess.getuid()
      ) {
        return { kind: "path", value: realFile };
      }
    } catch {
      // Fall through to the validated session ID when the file is unavailable.
    }
  }
  const id = ctx.sessionManager.getHeader()?.id;
  if (
    typeof id === "string" &&
    Buffer.byteLength(id, "utf8") <= SESSION_ID_MAX_BYTES &&
    /^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$/.test(id)
  ) {
    return { kind: "id", value: id };
  }
  return undefined;
}

export function publishBeacon(
  ctx: ExtensionContext,
  options: BeaconOptions = {},
): PublishResult {
  const platform = options.platform ?? piProcess.platform;
  const paneId = piProcess.env.TMUX_PANE;
  if (!paneId) return { published: false, reason: "tmux_pane_missing" };
  if (platform === "darwin") {
    const sessionRef = sessionReference(ctx);
    if (!sessionRef)
      return { published: false, reason: "session_reference_missing" };
    return publishDarwinBeacon(paneId, sessionRef, options);
  }
  if (platform !== "linux")
    return { published: false, reason: "unsupported_platform" };
  const sessionRef = sessionReference(ctx);
  if (!sessionRef)
    return { published: false, reason: "session_reference_missing" };
  const directory = beaconDirectory(piProcess.env);
  const startTime = (options.processStartIdentity ?? processStartIdentity)(
    piProcess.pid,
  );
  if (!directory || !startTime)
    return { published: false, reason: "secure_storage_unavailable" };
  const payload = JSON.stringify({
    schema: SCHEMA,
    pid: piProcess.pid,
    pane_id: paneId,
    start_time: startTime,
    session_ref: sessionRef,
  });
  const openDirectory = options.openPrivateDirectory ?? openPrivateDirectory;
  const publishFile = options.publishBeaconFile ?? publishBeaconFile;
  try {
    const directoryFd = openDirectory(directory);
    try {
      publishFile(directoryFd, piProcess.pid, payload);
    } finally {
      fs.closeSync(directoryFd);
    }
  } catch {
    return { published: false, reason: "secure_storage_unavailable" };
  }
  return { published: true };
}

export default function tmuxHerdrBeacon(
  pi: ExtensionAPI,
  options: BeaconOptions = {},
): void {
  pi.on("session_start", (_event: unknown, ctx: ExtensionContext) => {
    try {
      publishBeacon(ctx, options);
    } catch {
      // Fail closed without crashing the extension listener
    }
  });
  pi.on("session_tree", (_event: unknown, ctx: ExtensionContext) => {
    try {
      publishBeacon(ctx, options);
    } catch {
      // Fail closed without crashing the extension listener
    }
  });
  pi.registerCommand("herdr-beacon", {
    description: "Republish the private tmux session beacon for Herdr",
    handler: async (_args: string, ctx: ExtensionContext) => {
      try {
        const result = publishBeacon(ctx, options);
        if (!result.published) {
          ctx.ui.notify(
            `Herdr session beacon was not published (${result.reason}).`,
            "error",
          );
          return;
        }
        ctx.ui.notify("Herdr session beacon published.", "info");
      } catch {
        ctx.ui.notify(
          "Herdr session beacon was not published (secure_storage_unavailable).",
          "error",
        );
      }
    },
  });
}
