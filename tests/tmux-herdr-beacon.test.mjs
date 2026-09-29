import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import beaconExtension, {
  beaconDirectory,
  openPrivateDirectory,
  publishBeaconFile,
} from "../dot_pi/private_agent/extensions/tmux-herdr-beacon.ts";

function withEnvironment(values, callback) {
  const previous = new Map();
  for (const [key, value] of Object.entries(values)) {
    previous.set(key, process.env[key]);
    if (value === undefined) delete process.env[key];
    else process.env[key] = value;
  }
  try {
    return callback();
  } finally {
    for (const [key, value] of previous) {
      if (value === undefined) delete process.env[key];
      else process.env[key] = value;
    }
  }
}

function fixture() {
  const root = fs.mkdtempSync(
    path.join(os.tmpdir(), "pi-herdr-extension-test-"),
  );
  const registrations = { events: new Map(), commands: new Map() };
  const notifications = [];
  const pi = {
    on(name, handler) {
      registrations.events.set(name, handler);
    },
    registerCommand(name, command) {
      registrations.commands.set(name, command);
    },
  };
  const context = (id, sessionFile = undefined) => ({
    sessionManager: {
      getSessionFile: () => sessionFile,
      getHeader: () => ({ id }),
    },
    ui: {
      notify(message, level) {
        notifications.push({ message, level });
      },
    },
  });
  beaconExtension(pi);
  return { root, registrations, notifications, context };
}

function beaconPath(root) {
  return path.join(root, "runtime", "pi-herdr-sessions", `${process.pid}.json`);
}

test("fallback selection agrees on absolute XDG runtime and HOME rules", () => {
  assert.equal(
    beaconDirectory({ XDG_RUNTIME_DIR: "/run/user/1000", HOME: "/home/a" }),
    "/run/user/1000/pi-herdr-sessions",
  );
  assert.equal(
    beaconDirectory({ XDG_RUNTIME_DIR: "relative", HOME: "/home/a" }),
    "/home/a/.cache/pi-herdr-sessions",
  );
  assert.equal(
    beaconDirectory({ XDG_RUNTIME_DIR: "/run/user/1000" }),
    "/run/user/1000/pi-herdr-sessions",
  );
  assert.equal(
    beaconDirectory({ XDG_RUNTIME_DIR: "relative", HOME: "relative" }),
    undefined,
  );
});

test("lifecycle and command publish private minimal beacon with atomic replacement and private notification", () => {
  const f = fixture();
  const env = {
    XDG_RUNTIME_DIR: path.join(f.root, "runtime"),
    HOME: f.root,
    TMUX_PANE: "%7",
  };
  try {
    withEnvironment(env, () => {
      assert.deepEqual(
        [...f.registrations.events.keys()],
        ["session_start", "session_tree"],
      );
      assert.equal(f.registrations.commands.has("herdr-beacon"), true);
      f.registrations.events.get("session_start")({}, f.context("session-one"));
      const beacon = beaconPath(f.root);
      const firstStat = fs.statSync(beacon);
      const first = JSON.parse(fs.readFileSync(beacon, "utf8"));
      assert.equal(fs.statSync(path.dirname(beacon)).mode & 0o777, 0o700);
      assert.equal(firstStat.mode & 0o777, 0o600);
      assert.deepEqual(Object.keys(first).sort(), [
        "pane_id",
        "pid",
        "schema",
        "session_ref",
        "start_time",
      ]);
      assert.deepEqual(first.session_ref, { kind: "id", value: "session-one" });
      assert.equal(first.pid, process.pid);
      assert.equal(first.pane_id, "%7");

      f.registrations.events.get("session_tree")({}, f.context("session-two"));
      const secondStat = fs.statSync(beacon);
      assert.notEqual(secondStat.ino, firstStat.ino);
      assert.deepEqual(
        JSON.parse(fs.readFileSync(beacon, "utf8")).session_ref,
        { kind: "id", value: "session-two" },
      );

      f.registrations.commands
        .get("herdr-beacon")
        .handler("", f.context("session-three"));
      assert.deepEqual(f.notifications, [
        { message: "Herdr session beacon published.", level: "info" },
      ]);
      assert.equal(
        JSON.stringify(f.notifications).includes("session-three"),
        false,
      );
      assert.equal(JSON.stringify(f.notifications).includes(beacon), false);
      assert.equal(f.registrations.events.has("session_shutdown"), false);
      assert.equal(fs.existsSync(beacon), true);
    });
  } finally {
    fs.rmSync(f.root, { recursive: true, force: true });
  }
});

test("extension publishes a canonical in-root session-file reference", () => {
  const f = fixture();
  const env = {
    XDG_RUNTIME_DIR: path.join(f.root, "runtime"),
    HOME: f.root,
    TMUX_PANE: "%8",
  };
  try {
    const sessions = path.join(f.root, ".pi", "agent", "sessions", "project");
    fs.mkdirSync(sessions, { recursive: true, mode: 0o700 });
    const sessionFile = path.join(sessions, "session.jsonl");
    fs.writeFileSync(sessionFile, '{\\"type\\":\\"session\\"}\\n', {
      mode: 0o600,
    });
    withEnvironment(env, () => {
      f.registrations.events.get("session_start")(
        {},
        f.context("fallback-id", sessionFile),
      );
      const stored = JSON.parse(fs.readFileSync(beaconPath(f.root), "utf8"));
      assert.deepEqual(stored.session_ref, {
        kind: "path",
        value: fs.realpathSync(sessionFile),
      });
    });
  } finally {
    fs.rmSync(f.root, { recursive: true, force: true });
  }
});

test("outside-root and escaping symlink session paths fall back without disclosing paths", () => {
  const f = fixture();
  const env = {
    XDG_RUNTIME_DIR: path.join(f.root, "runtime"),
    HOME: f.root,
    TMUX_PANE: "%9",
  };
  try {
    const sessions = path.join(f.root, ".pi", "agent", "sessions");
    fs.mkdirSync(sessions, { recursive: true, mode: 0o700 });
    const outside = path.join(f.root, "outside-secret.jsonl");
    fs.writeFileSync(outside, "private", { mode: 0o600 });
    const link = path.join(sessions, "linked-session.jsonl");
    fs.symlinkSync(outside, link);
    withEnvironment(env, () => {
      for (const invalidPath of [outside, link]) {
        f.registrations.commands
          .get("herdr-beacon")
          .handler("", f.context("valid-id", invalidPath));
        const stored = JSON.parse(fs.readFileSync(beaconPath(f.root), "utf8"));
        assert.deepEqual(stored.session_ref, { kind: "id", value: "valid-id" });
        assert.equal(JSON.stringify(stored).includes(invalidPath), false);
        assert.equal(
          JSON.stringify(f.notifications).includes(invalidPath),
          false,
        );
      }
    });
  } finally {
    fs.rmSync(f.root, { recursive: true, force: true });
  }
});

test("explicit command reports missing tmux without publishing or disclosing reference", () => {
  const f = fixture();
  const env = {
    XDG_RUNTIME_DIR: path.join(f.root, "runtime"),
    HOME: f.root,
    TMUX_PANE: undefined,
  };
  try {
    withEnvironment(env, () => {
      f.registrations.commands
        .get("herdr-beacon")
        .handler("", f.context("private-session-id"));
      assert.deepEqual(f.notifications, [
        {
          message:
            "Herdr session beacon was not published (no tmux pane or valid session reference).",
          level: "error",
        },
      ]);
      assert.equal(
        JSON.stringify(f.notifications).includes("private-session-id"),
        false,
      );
      assert.equal(
        fs.existsSync(path.join(f.root, "runtime", "pi-herdr-sessions")),
        false,
      );
    });
  } finally {
    fs.rmSync(f.root, { recursive: true, force: true });
  }
});

test("pinned directory operations remain in the opened inode after pathname replacement", () => {
  const f = fixture();
  const original = path.join(f.root, "beacons");
  const moved = path.join(f.root, "moved");
  const attacker = path.join(f.root, "attacker");
  fs.mkdirSync(original);
  fs.mkdirSync(attacker);
  const fd = openPrivateDirectory(original);
  try {
    fs.renameSync(original, moved);
    fs.symlinkSync(attacker, original);
    const payload = JSON.stringify({
      schema: 1,
      pid: process.pid,
      pane_id: "%1",
      start_time: "1",
      session_ref: { kind: "id", value: "safe-id" },
    });
    publishBeaconFile(fd, process.pid, payload);
    assert.equal(fs.existsSync(path.join(moved, `${process.pid}.json`)), true);
    assert.equal(fs.readdirSync(attacker).length, 0);
  } finally {
    fs.closeSync(fd);
    fs.rmSync(f.root, { recursive: true, force: true });
  }
});

test("directory walk rejects symlink components and enforces final directory mode", () => {
  const f = fixture();
  const real = path.join(f.root, "real");
  const link = path.join(f.root, "link");
  fs.mkdirSync(real);
  fs.symlinkSync(real, link);
  assert.throws(() => openPrivateDirectory(path.join(link, "beacons")));
  const loose = path.join(real, "beacons");
  fs.mkdirSync(loose, { mode: 0o755 });
  fs.chmodSync(loose, 0o755);
  const fd = openPrivateDirectory(loose);
  try {
    assert.equal(fs.fstatSync(fd).mode & 0o777, 0o700);
  } finally {
    fs.closeSync(fd);
    fs.rmSync(f.root, { recursive: true, force: true });
  }
});
