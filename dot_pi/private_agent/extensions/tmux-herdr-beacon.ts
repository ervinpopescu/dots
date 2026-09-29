import * as fs from "node:fs";
import * as path from "node:path";
import type {
  ExtensionAPI,
  ExtensionContext,
} from "@earendil-works/pi-coding-agent";

const SCHEMA = 1;
const DIRECTORY_FLAGS =
  fs.constants.O_RDONLY | fs.constants.O_DIRECTORY | fs.constants.O_NOFOLLOW;
type PiProcess = {
  env: Record<string, string | undefined>;
  pid: number;
  platform: string;
  getuid: () => number;
};
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

function procFdChild(fd: number, name: string): string {
  return `/proc/self/fd/${fd}/${name}`;
}

/** Walk from / through pinned directory fds; all child operations stay on these inodes. */
export function openPrivateDirectory(
  target: string,
  uid = piProcess.getuid(),
): number {
  if (
    piProcess.platform !== "linux" ||
    !path.isAbsolute(target) ||
    !fs.constants.O_NOFOLLOW ||
    !fs.constants.O_DIRECTORY
  ) {
    throw new Error("safe beacon directory operations unavailable");
  }
  let fd = fs.openSync("/", DIRECTORY_FLAGS);
  try {
    for (const component of path
      .resolve(target)
      .split(path.sep)
      .filter(Boolean)) {
      const child = procFdChild(fd, component);
      let childFd: number;
      try {
        childFd = fs.openSync(child, DIRECTORY_FLAGS);
      } catch (error) {
        if ((error as { code?: string }).code !== "ENOENT") throw error;
        try {
          fs.mkdirSync(child, { mode: 0o700 });
        } catch (mkdirError) {
          if ((mkdirError as { code?: string }).code !== "EEXIST")
            throw mkdirError;
        }
        childFd = fs.openSync(child, DIRECTORY_FLAGS);
      }
      fs.closeSync(fd);
      fd = childFd;
    }
    const info = fs.fstatSync(fd);
    if (!info.isDirectory() || info.uid !== uid)
      throw new Error("untrusted beacon directory");
    if ((info.mode & 0o777) !== 0o700) fs.fchmodSync(fd, 0o700);
    const verified = fs.fstatSync(fd);
    if (
      !verified.isDirectory() ||
      verified.uid !== uid ||
      (verified.mode & 0o777) !== 0o700
    ) {
      throw new Error("untrusted beacon directory");
    }
    return fd;
  } catch (error) {
    fs.closeSync(fd);
    throw error;
  }
}

/** Publish through a pinned directory descriptor; procfs-unavailable operations fail closed. */
export function publishBeaconFile(
  directoryFd: number,
  pid: number,
  payload: string,
  uid = piProcess.getuid(),
): void {
  const destination = `${pid}.json`;
  const temporary = `.${pid}.${uid}.${Date.now()}.${Math.random().toString(16).slice(2)}.tmp`;
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
  } catch (error) {
    try {
      fs.unlinkSync(temporaryPath);
    } catch {
      /* best-effort temp cleanup, still fd-relative */
    }
    throw error;
  } finally {
    fs.closeSync(fileFd);
  }
  try {
    fs.renameSync(temporaryPath, destinationPath);
    fs.fsyncSync(directoryFd);
  } catch (error) {
    try {
      fs.unlinkSync(temporaryPath);
    } catch {
      /* best-effort temp cleanup, still fd-relative */
    }
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

function sessionReference(
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
    /^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$/.test(id)
  ) {
    return { kind: "id", value: id };
  }
  return undefined;
}

function publish(ctx: ExtensionContext): boolean {
  const paneId = piProcess.env.TMUX_PANE;
  if (!paneId) return false;
  const directory = beaconDirectory(piProcess.env);
  const startTime = processStartIdentity(piProcess.pid);
  const sessionRef = sessionReference(ctx);
  if (!directory || !startTime || !sessionRef) return false;
  const payload = JSON.stringify({
    schema: SCHEMA,
    pid: piProcess.pid,
    pane_id: paneId,
    start_time: startTime,
    session_ref: sessionRef,
  });
  const directoryFd = openPrivateDirectory(directory);
  try {
    publishBeaconFile(directoryFd, piProcess.pid, payload);
  } finally {
    fs.closeSync(directoryFd);
  }
  return true;
}

export default function tmuxHerdrBeacon(pi: ExtensionAPI): void {
  pi.on("session_start", (_event: unknown, ctx: ExtensionContext) =>
    publish(ctx),
  );
  pi.on("session_tree", (_event: unknown, ctx: ExtensionContext) =>
    publish(ctx),
  );
  pi.registerCommand("herdr-beacon", {
    description: "Republish the private tmux session beacon for Herdr",
    handler: async (_args: string, ctx: ExtensionContext) => {
      try {
        if (!publish(ctx)) {
          ctx.ui.notify(
            "Herdr session beacon was not published (no tmux pane or valid session reference).",
            "error",
          );
          return;
        }
        ctx.ui.notify("Herdr session beacon published.", "info");
      } catch {
        ctx.ui.notify("Herdr session beacon could not be published.", "error");
      }
    },
  });
}
