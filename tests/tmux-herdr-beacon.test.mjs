import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import beaconExtension, {
  beaconDirectory,
  openPrivateDirectory,
  publishBeacon,
  publishBeaconFile,
  runDarwinHelper,
  sessionReference,
  SESSION_ID_MAX_BYTES,
  DARWIN_HELPER_REQUEST_MAX_BYTES,
  validateDarwinHelper,
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

function linuxFixtureOptions(_root) {
  let openedDirectory;
  return {
    platform: "linux",
    processStartIdentity: () => "fixture-start-time",
    openPrivateDirectory(target) {
      openedDirectory = target;
      fs.mkdirSync(target, { recursive: true, mode: 0o700 });
      fs.chmodSync(target, 0o700);
      return fs.openSync("/dev/null", "r");
    },
    publishBeaconFile(_directoryFd, pid, payload) {
      assert.ok(openedDirectory);
      const destination = path.join(openedDirectory, `${pid}.json`);
      const temporary = path.join(openedDirectory, `.${pid}.fixture.tmp`);
      fs.writeFileSync(temporary, payload, { mode: 0o600 });
      fs.chmodSync(temporary, 0o600);
      fs.renameSync(temporary, destination);
      fs.chmodSync(destination, 0o600);
    },
  };
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
  beaconExtension(pi, linuxFixtureOptions(root));
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
    const sessionFile = path.join(
      sessions,
      'space "quote" \\ slash-日本語.jsonl',
    );
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
            "Herdr session beacon was not published (tmux_pane_missing).",
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

test("explicit command reports missing session reference with a non-sensitive reason", () => {
  const f = fixture();
  const env = {
    XDG_RUNTIME_DIR: path.join(f.root, "runtime"),
    HOME: f.root,
    TMUX_PANE: "%10",
  };
  try {
    withEnvironment(env, () => {
      f.registrations.commands
        .get("herdr-beacon")
        .handler("", f.context(undefined));
      assert.deepEqual(f.notifications, [
        {
          message:
            "Herdr session beacon was not published (session_reference_missing).",
          level: "error",
        },
      ]);
      assert.equal(
        JSON.stringify(f.notifications).includes("undefined"),
        false,
      );
    });
  } finally {
    fs.rmSync(f.root, { recursive: true, force: true });
  }
});

test(
  "pinned directory operations remain in the opened inode after pathname replacement",
  {
    skip:
      process.platform === "linux" ? false : "requires Linux /proc semantics",
  },
  () => {
    const f = fixture();
    const original = path.join(f.root, "beacons");
    const moved = path.join(f.root, "moved");
    const attacker = path.join(f.root, "attacker");
    fs.mkdirSync(original, { mode: 0o700 });
    fs.chmodSync(original, 0o700);
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
      assert.equal(
        fs.existsSync(path.join(moved, `${process.pid}.json`)),
        true,
      );
      assert.equal(fs.readdirSync(attacker).length, 0);
    } finally {
      fs.closeSync(fd);
      fs.rmSync(f.root, { recursive: true, force: true });
    }
  },
);

test("session identifiers enforce the shared UTF-8 byte boundary", () => {
  const exact = "a".repeat(SESSION_ID_MAX_BYTES);
  assert.deepEqual(
    sessionReference({
      sessionManager: {
        getSessionFile: () => undefined,
        getHeader: () => ({ id: exact }),
      },
    }),
    { kind: "id", value: exact },
  );
  assert.equal(
    sessionReference({
      sessionManager: {
        getSessionFile: () => undefined,
        getHeader: () => ({ id: `${exact}a` }),
      },
    }),
    undefined,
  );
});

test("Darwin helper request accepts exactly 16,384 bytes and rejects 16,385", () => {
  const reply = JSON.stringify({ ok: false, reason: "invalid" });
  const exact = "x".repeat(DARWIN_HELPER_REQUEST_MAX_BYTES);
  assert.deepEqual(
    runDarwinHelper("resolve", exact, { darwinHelper: () => reply }),
    { ok: false, reason: "invalid" },
  );
  assert.throws(
    () =>
      runDarwinHelper("resolve", `${exact}x`, { darwinHelper: () => reply }),
    /helper_process_failure/,
  );
});

test("Darwin resolve response accepts maximum escaped path output", () => {
  const value = `/${"\\".repeat(4095)}`;
  const response = runDarwinHelper("resolve", "{}", {
    darwinHelper: () =>
      JSON.stringify({
        ok: true,
        kind: "path",
        value,
        pid: 42,
        start_time: "123.000000",
      }),
  });
  assert.equal(response.value, value);
});

test("Darwin resolve response accepts the documented timestamp format", () => {
  const response = runDarwinHelper("resolve", "{}", {
    darwinHelper: () =>
      JSON.stringify({
        ok: true,
        kind: "id",
        value: "session",
        pid: 42,
        start_time: "123.000000",
      }),
  });
  assert.equal(response.start_time, "123.000000");
});

test("Darwin helper requires exact 0700 helper and parent modes", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "pi-herdr-helper-mode-"));
  const helper = path.join(root, "tmux-herdr-darwin-helper");
  fs.writeFileSync(helper, "helper");
  fs.chmodSync(root, 0o700);
  fs.chmodSync(helper, 0o700);
  assert.doesNotThrow(() => validateDarwinHelper(helper));
  for (const mode of [0o744, 0o755, 0o600]) {
    fs.chmodSync(helper, mode);
    assert.throws(() => validateDarwinHelper(helper), /helper_build_failure/);
  }
  fs.chmodSync(helper, 0o700);
  for (const mode of [0o744, 0o755, 0o750]) {
    fs.chmodSync(root, mode);
    assert.throws(() => validateDarwinHelper(helper), /helper_build_failure/);
  }
});

test("Darwin publisher reports a missing managed helper", () => {
  const f = fixture();
  const env = {
    XDG_RUNTIME_DIR: path.join(f.root, "runtime"),
    HOME: f.root,
    TMUX_PANE: "%11",
  };
  try {
    withEnvironment(env, () => {
      assert.deepEqual(
        publishBeacon(f.context("safe-id"), { platform: "darwin" }),
        { published: false, reason: "helper_missing" },
      );
    });
  } finally {
    fs.rmSync(f.root, { recursive: true, force: true });
  }
});

test("Darwin publisher sends bounded metadata on stdin to the helper", () => {
  const f = fixture();
  const env = {
    XDG_RUNTIME_DIR: path.join(f.root, "runtime"),
    HOME: f.root,
    TMUX_PANE: "%12",
  };
  const calls = [];
  try {
    withEnvironment(env, () => {
      const result = publishBeacon(f.context("mac-id"), {
        platform: "darwin",
        darwinHelper(action, request) {
          calls.push({ action, request: JSON.parse(request) });
          return JSON.stringify({ ok: true });
        },
      });
      assert.deepEqual(result, { published: true });
      assert.deepEqual(calls, [
        {
          action: "publish",
          request: {
            v: 1,
            op: "publish",
            directory: path.join(f.root, "runtime", "pi-herdr-sessions"),
            publisher_pid: process.pid,
            pane_id: "%12",
            session_kind: "id",
            session_value: "mac-id",
          },
        },
      ]);
      for (const malformed of [
        '{"ok":true,"extra":1}',
        '{"ok":false}',
        '{"ok":false,"reason":"unknown"}',
        '{"ok":false,"reason":"io","reason":"stale"}',
      ]) {
        assert.deepEqual(
          publishBeacon(f.context("mac-id"), {
            platform: "darwin",
            darwinHelper: () => malformed,
          }),
          { published: false, reason: "helper_process_failure" },
        );
      }
      assert.deepEqual(
        publishBeacon(f.context("mac-id"), {
          platform: "darwin",
          darwinHelper: () => "not-json",
        }),
        { published: false, reason: "helper_process_failure" },
      );
      assert.deepEqual(
        publishBeacon(f.context("mac-id"), {
          platform: "darwin",
          darwinHelper: () => {
            throw new Error("timeout");
          },
        }),
        { published: false, reason: "helper_process_failure" },
      );
    });
  } finally {
    fs.rmSync(f.root, { recursive: true, force: true });
  }
});

test("Darwin descriptor storage rejects pathname fallbacks", () => {
  const f = fixture();
  const directory = path.join(f.root, "beacons");
  fs.mkdirSync(directory);
  assert.throws(
    () => openPrivateDirectory(directory, process.getuid(), "darwin"),
    /descriptor-pinned beacon storage is unavailable/,
  );
  assert.throws(
    () => publishBeaconFile(0, process.pid, "{}", process.getuid(), "darwin"),
    /descriptor-pinned beacon storage is unavailable/,
  );
  fs.rmSync(f.root, { recursive: true, force: true });
});

test(
  "directory walk rejects symlink components and enforces final directory mode",
  {
    skip:
      process.platform === "linux" ? false : "requires Linux /proc semantics",
  },
  () => {
    const f = fixture();
    const real = path.join(f.root, "real");
    const link = path.join(f.root, "link");
    fs.mkdirSync(real);
    fs.symlinkSync(real, link);
    assert.throws(() => openPrivateDirectory(path.join(link, "beacons")));
    const loose = path.join(real, "beacons");
    fs.mkdirSync(loose, { mode: 0o755 });
    fs.chmodSync(loose, 0o755);
    assert.throws(
      () => openPrivateDirectory(loose),
      /untrusted beacon directory/,
    );
    fs.chmodSync(loose, 0o700);
    const fd = openPrivateDirectory(loose);
    try {
      assert.equal(fs.fstatSync(fd).mode & 0o777, 0o700);
    } finally {
      fs.closeSync(fd);
      fs.rmSync(f.root, { recursive: true, force: true });
    }
  },
);

test(
  "openPrivateDirectory closes descriptors exactly once without double-close on symlink rejection",
  {
    skip:
      process.platform === "linux" ? false : "requires Linux /proc semantics",
  },
  () => {
    const f = fixture();
    const real = path.join(f.root, "real");
    const link = path.join(f.root, "link");
    fs.mkdirSync(real);
    fs.symlinkSync(real, link);

    const activeFds = new Set();
    let doubleClose = false;
    let ebadfOccurred = false;
    let totalOpened = 0;
    const originalOpen = fs.openSync;
    const originalClose = fs.closeSync;

    fs.openSync = (...args) => {
      const fd = originalOpen(...args);
      activeFds.add(fd);
      totalOpened++;
      return fd;
    };
    fs.closeSync = (fd) => {
      if (!activeFds.has(fd)) {
        doubleClose = true;
      }
      activeFds.delete(fd);
      try {
        return originalClose(fd);
      } catch (err) {
        if (err.code === "EBADF") ebadfOccurred = true;
        throw err;
      }
    };

    try {
      assert.throws(
        () => openPrivateDirectory(path.join(link, "beacons")),
        (error) => {
          assert.notEqual(error.code, "EBADF");
          assert.ok(
            error.code === "ELOOP" ||
              error.code === "ENOTDIR" ||
              /ELOOP|symlink/i.test(error.message),
          );
          return true;
        },
      );
      assert.equal(doubleClose, false, "double-close must not occur on symlink error");
      assert.equal(ebadfOccurred, false, "EBADF must not occur during cleanup");
      assert.equal(activeFds.size, 0, "all opened descriptors must be closed");
      assert.ok(totalOpened > 0, "at least one descriptor must have been opened");
    } finally {
      fs.openSync = originalOpen;
      fs.closeSync = originalClose;
      fs.rmSync(f.root, { recursive: true, force: true });
    }
  },
);

test(
  "openPrivateDirectory closes descriptors exactly once without double-close on unexpected error",
  {
    skip:
      process.platform === "linux" ? false : "requires Linux /proc semantics",
  },
  () => {
    const f = fixture();
    const targetDir = path.join(f.root, "nested", "beacon-test");
    fs.mkdirSync(targetDir, { recursive: true, mode: 0o700 });

    const activeFds = new Set();
    let doubleClose = false;
    let ebadfOccurred = false;
    let totalOpened = 0;
    const originalOpen = fs.openSync;
    const originalClose = fs.closeSync;

    fs.openSync = (...args) => {
      const fd = originalOpen(...args);
      activeFds.add(fd);
      totalOpened++;
      return fd;
    };
    fs.closeSync = (fd) => {
      if (!activeFds.has(fd)) {
        doubleClose = true;
      }
      activeFds.delete(fd);
      try {
        return originalClose(fd);
      } catch (err) {
        if (err.code === "EBADF") ebadfOccurred = true;
        throw err;
      }
    };

    const originalFstat = fs.fstatSync;
    let injectedErrorFired = false;
    fs.fstatSync = (fd, options) => {
      const stats = originalFstat(fd, options);
      if (!injectedErrorFired && stats.isDirectory()) {
        injectedErrorFired = true;
        const err = new Error("unexpected disk error");
        err.code = "EIO";
        throw err;
      }
      return stats;
    };

    try {
      assert.throws(
        () => openPrivateDirectory(targetDir),
        (error) => {
          assert.equal(error.message, "unexpected disk error");
          assert.notEqual(error.code, "EBADF");
          return true;
        },
      );
      assert.equal(injectedErrorFired, true, "injected error must have been triggered");
      assert.equal(doubleClose, false, "double-close must not occur on unexpected error");
      assert.equal(ebadfOccurred, false, "EBADF must not occur during cleanup");
      assert.equal(activeFds.size, 0, "all opened descriptors must be closed");
      assert.ok(totalOpened >= 2, "both current and next descriptors must have been opened");
    } finally {
      fs.openSync = originalOpen;
      fs.closeSync = originalClose;
      fs.fstatSync = originalFstat;
      fs.rmSync(f.root, { recursive: true, force: true });
    }
  },
);

test("lifecycle publication fails closed without crashing listener on storage errors", () => {
  const f = fixture();
  const registrations = { events: new Map(), commands: new Map() };
  const pi = {
    on(name, handler) {
      registrations.events.set(name, handler);
    },
    registerCommand(name, command) {
      registrations.commands.set(name, command);
    },
  };
  beaconExtension(pi, {
    platform: "linux",
    processStartIdentity: () => "fixture-start-time",
    openPrivateDirectory() {
      const err = new Error("untrusted beacon directory");
      err.code = "EACCES";
      throw err;
    },
  });
  withEnvironment(
    { TMUX_PANE: "%1", HOME: f.root, XDG_RUNTIME_DIR: f.root },
    () => {
      assert.doesNotThrow(() => {
        registrations.events.get("session_start")({}, f.context("test-session"));
      });
      assert.doesNotThrow(() => {
        registrations.events.get("session_tree")({}, f.context("test-session"));
      });
      const result = publishBeacon(f.context("test-session"), {
        platform: "linux",
        processStartIdentity: () => "fixture-start-time",
        openPrivateDirectory() {
          throw new Error("untrusted beacon directory");
        },
      });
      assert.deepEqual(result, {
        published: false,
        reason: "secure_storage_unavailable",
      });
    },
  );
  fs.rmSync(f.root, { recursive: true, force: true });
});
