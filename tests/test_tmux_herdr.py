import contextlib
import copy
import io
import json
import os
import pathlib
import runpy
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

SCRIPT = pathlib.Path(__file__).parents[1] / "bin/executable_tmux-herdr"
module = runpy.run_path(str(SCRIPT), run_name="tmux_herdr_test")
_real_resolve_pi_session = module["resolve_pi_session"]


def fixture_resolve_pi_session(*args, **kwargs):
    """Use synthetic Linux process fixtures independently of the host OS."""
    kwargs.setdefault("platform", "linux")
    return _real_resolve_pi_session(*args, **kwargs)


module["resolve_pi_session"] = fixture_resolve_pi_session


def pane(kind, command, cwd="/tmp", ref=None):
    app = {"kind": kind}
    if kind == "pi":
        app["session_ref"] = ref
    return {
        "index": 1,
        "active": True,
        "cwd": cwd,
        "cwd_exists": True,
        "command": command,
        "title": "title",
        "geometry": {"x": 0, "y": 0, "width": 100, "height": 40},
        "application": app,
    }


class TmuxHerdrTests(unittest.TestCase):
    def proc_fixture(self, base, environment, extra_processes=()):
        proc = pathlib.Path(base) / "proc"
        tty = pathlib.Path(base) / "tty0"
        tty.touch()

        def setup_process(pid, ppid, pgrp, tpgid, env=b""):
            root = proc / str(pid)
            (root / "task" / str(pid)).mkdir(parents=True)
            (root / "fd").mkdir()
            (root / "task" / str(pid) / "children").write_text("")
            stat_fields = (
                ["S", str(ppid), str(pgrp), "1", "0", str(tpgid)]
                + ["0"] * 13
                + ["987654"]
            )
            (root / "stat").write_text(f"{pid} (node) {' '.join(stat_fields)}\n")
            (root / "environ").write_bytes(env)
            (root / "fd" / "0").symlink_to(tty)

        setup_process(100, 1, 100, 101)
        children = [101, *extra_processes]
        (proc / "100" / "task" / "100" / "children").write_text(
            " ".join(map(str, children))
        )
        setup_process(101, 100, 101, 101, environment)
        for pid, env in (
            extra_processes.items() if isinstance(extra_processes, dict) else ()
        ):
            setup_process(pid, 100, 101, 101, env)
        return proc, tty

    def fake_tmux_snapshot_run(self, pane_pid=100, pane_tty="/dev/null"):
        def fake_run(argv, **kwargs):
            if argv[1:3] == ["list-sessions", "-F"]:
                return "pilot\n"
            if argv[1:3] == ["list-windows", "-t"]:
                return "1\tpi\t1\tlayout\n"
            if argv[1:4] == ["display-message", "-p", "-t"]:
                return "1\n"
            if argv[1:3] == ["list-panes", "-t"]:
                fields = [
                    "0",
                    "1",
                    "/tmp",
                    "pi",
                    "Pi title",
                    "80",
                    "24",
                    "0",
                    "0",
                    "79",
                    "23",
                ]
                if "#{pane_pid}" in argv[-1]:
                    fields.extend([str(pane_pid), pane_tty, "%1"])
                return "\t".join(fields) + "\n"
            raise AssertionError(f"unexpected tmux command: {argv}")

        return fake_run

    def make_apply_mocks(self, calls):
        def fake_herdr(target, *args):
            calls.append((target, *args))
            if args[:2] == ("workspace", "list"):
                return {
                    "id": "cli:workspace:list",
                    "result": {"type": "workspace_list", "workspaces": []},
                }
            if args[:2] == ("workspace", "create"):
                return {
                    "id": "cli:workspace:create",
                    "result": {
                        "type": "workspace_created",
                        "workspace": {"workspace_id": "ws-1"},
                        "tab": {"tab_id": "tab-1"},
                        "root_pane": {"pane_id": "pane-1"},
                    },
                }
            if args[:2] == ("tab", "create"):
                return {
                    "id": "cli:tab:create",
                    "result": {
                        "type": "tab_created",
                        "tab": {"tab_id": "tab-2"},
                        "root_pane": {"pane_id": "pane-2"},
                    },
                }
            if args[:2] == ("pane", "split"):
                return {
                    "id": "cli:pane:split",
                    "result": {"type": "pane_info", "pane": {"pane_id": "pane-3"}},
                }
            if args[:2] == ("pane", "rename"):
                return {
                    "id": "cli:pane:rename",
                    "result": {"type": "pane_info", "pane": {"pane_id": args[2]}},
                }
            if args[:2] == ("pane", "run"):
                return ""
            if args[:2] == ("tab", "rename"):
                return {
                    "id": "cli:tab:rename",
                    "result": {"type": "tab_info", "tab": {"tab_id": args[2]}},
                }
            if args[:2] == ("tab", "focus"):
                return {
                    "id": "cli:tab:focus",
                    "result": {"type": "tab_info", "tab": {"tab_id": args[2]}},
                }
            raise AssertionError(f"unexpected Herdr command: {args}")

        return fake_herdr

    def apply_snapshot(self, app_kind="lazygit"):
        return {
            "schema": 1,
            "name": "pilot-source",
            "attached": True,
            "tabs": [
                {
                    "name": "first-window",
                    "active": True,
                    "panes": [
                        pane(
                            app_kind, "pi" if app_kind == "pi" else "lazygit", ref=None
                        ),
                        dict(pane("shell", "zsh"), active=False),
                    ],
                },
                {
                    "name": "second-window",
                    "active": False,
                    "panes": [pane("shell", "zsh")],
                },
            ],
        }

    def marker_path(self, home, target, snapshot):
        return module["_marker_path"](
            pathlib.Path(home) / ".local/state/tmux-herdr", target, snapshot["name"]
        )

    def write_beacon(
        self,
        home,
        pid=101,
        pane_id="%1",
        start_time="987654",
        session_ref=None,
        mode=0o600,
    ):
        directory = pathlib.Path(home) / ".cache/pi-herdr-sessions"
        directory.mkdir(parents=True, mode=0o700)
        directory.chmod(0o700)
        beacon = directory / f"{pid}.json"
        data = {
            "schema": 1,
            "pid": pid,
            "pane_id": pane_id,
            "start_time": start_time,
            "session_ref": session_ref or {"kind": "id", "value": "session-123"},
        }
        beacon.write_text(json.dumps(data))
        beacon.chmod(mode)
        return beacon

    def test_beacon_directory_fallback_matches_absolute_path_policy(self):
        fallback_home = pathlib.Path("/home/test-user")
        self.assertEqual(
            module["_beacon_directory"](
                fallback_home, {"XDG_RUNTIME_DIR": "/run/user/1000", "HOME": "/other"}
            ),
            pathlib.Path("/run/user/1000/pi-herdr-sessions"),
        )
        self.assertEqual(
            module["_beacon_directory"](
                fallback_home,
                {"XDG_RUNTIME_DIR": "relative", "HOME": "/home/test-user"},
            ),
            pathlib.Path("/home/test-user/.cache/pi-herdr-sessions"),
        )
        self.assertIsNone(
            module["_beacon_directory"](
                None, {"XDG_RUNTIME_DIR": "relative", "HOME": "relative"}
            )
        )

    def test_darwin_beacon_directory_canonicalization_with_symlink_ancestor(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            real_run = tmp_path / "real_run"
            real_run.mkdir(mode=0o700)
            symlink_run = tmp_path / "symlink_run"
            symlink_run.symlink_to(real_run)
            home = tmp_path / "home"
            home.mkdir(mode=0o700)

            darwin_dir = module["_beacon_directory"](
                home,
                {"XDG_RUNTIME_DIR": str(symlink_run), "HOME": str(home)},
                platform="darwin",
            )
            canonical_expected = real_run.resolve() / "pi-herdr-sessions"
            self.assertEqual(darwin_dir, canonical_expected)

            # Helper runner in resolve_pi_session receives the exact canonical directory
            calls = []

            def record_runner(action, request):
                calls.append((action, json.loads(request)))
                return json.dumps(
                    {
                        "ok": True,
                        "kind": "id",
                        "value": "sess-1",
                        "pid": 200,
                        "start_time": "123.456000",
                    }
                )

            self.write_beacon(home, pid=200, pane_id="%1", start_time="123.456000")
            # Create beacon in canonical directory too
            canonical_dir = canonical_expected
            canonical_dir.mkdir(parents=True, mode=0o700)
            beacon_file = canonical_dir / "200.json"
            beacon_file.write_text(
                json.dumps(
                    {
                        "schema": 1,
                        "pid": 200,
                        "pane_id": "%1",
                        "start_time": "123.456000",
                        "session_ref": {"kind": "id", "value": "sess-1"},
                    }
                )
            )
            beacon_file.chmod(0o600)

            ref, warning = module["resolve_pi_session"](
                "200",
                "/dev/ttys001",
                tmp_path,
                home=home,
                platform="darwin",
                pane_id="%1",
                environ={"XDG_RUNTIME_DIR": str(symlink_run), "HOME": str(home)},
                helper_runner=record_runner,
            )
            self.assertEqual(ref, {"kind": "id", "value": "sess-1"})
            self.assertIsNone(warning)
            self.assertEqual(calls[0][1]["directory"], str(canonical_expected))

    def test_darwin_beacon_directory_failed_realpath_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            home = tmp_path / "home"
            home.mkdir(mode=0o700)
            broken_symlink = tmp_path / "broken_symlink"
            broken_symlink.symlink_to(tmp_path / "nonexistent")

            # Non-existent path falls back to HOME/.cache/pi-herdr-sessions
            fallback_dir = module["_beacon_directory"](
                home,
                {"XDG_RUNTIME_DIR": str(tmp_path / "absent"), "HOME": str(home)},
                platform="darwin",
            )
            self.assertEqual(fallback_dir, home.resolve() / ".cache/pi-herdr-sessions")

            # Broken symlink falls back to HOME/.cache/pi-herdr-sessions
            fallback_dir = module["_beacon_directory"](
                home,
                {"XDG_RUNTIME_DIR": str(broken_symlink), "HOME": str(home)},
                platform="darwin",
            )
            self.assertEqual(fallback_dir, home.resolve() / ".cache/pi-herdr-sessions")

            # If HOME is also invalid/relative, returns None (never uncanonicalized path)
            no_dir = module["_beacon_directory"](
                None,
                {"XDG_RUNTIME_DIR": str(broken_symlink), "HOME": "relative"},
                platform="darwin",
            )
            self.assertIsNone(no_dir)

    def test_darwin_untrusted_canonical_target_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            untrusted_run = tmp_path / "untrusted_run"
            untrusted_run.mkdir(mode=0o777)
            untrusted_run.chmod(0o777)
            symlink_run = tmp_path / "symlink_run"
            symlink_run.symlink_to(untrusted_run)
            home = tmp_path / "home"

            darwin_dir = module["_beacon_directory"](
                home,
                {"XDG_RUNTIME_DIR": str(symlink_run), "HOME": str(home)},
                platform="darwin",
            )
            self.assertEqual(darwin_dir, untrusted_run.resolve() / "pi-herdr-sessions")

            # _open_beacon_directory descriptor walk must reject untrusted canonical target permissions
            target_sessions = darwin_dir
            target_sessions.mkdir(mode=0o700)
            with self.assertRaises(module["_UntrustedBeaconDirectory"]):
                module["_open_beacon_directory"](target_sessions)

    def test_linux_beacon_directory_unchanged_behavior(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            real_run = tmp_path / "real_run"
            real_run.mkdir(mode=0o700)
            symlink_run = tmp_path / "symlink_run"
            symlink_run.symlink_to(real_run)
            home = tmp_path / "home"

            # Linux does not canonicalize symlink base
            linux_dir = module["_beacon_directory"](
                home,
                {"XDG_RUNTIME_DIR": str(symlink_run), "HOME": str(home)},
                platform="linux",
            )
            self.assertEqual(linux_dir, symlink_run / "pi-herdr-sessions")

            # Linux non-existent XDG path is preserved directly
            absent = tmp_path / "absent"
            linux_absent = module["_beacon_directory"](
                home,
                {"XDG_RUNTIME_DIR": str(absent), "HOME": str(home)},
                platform="linux",
            )
            self.assertEqual(linux_absent, absent / "pi-herdr-sessions")

            # Passing symlinked base on Linux to _open_beacon_directory fails
            target_sessions = linux_dir
            real_sessions = real_run / "pi-herdr-sessions"
            real_sessions.mkdir(mode=0o700)
            with self.assertRaises(module["_UntrustedBeaconDirectory"]):
                module["_open_beacon_directory"](target_sessions)

    def test_canonical_path_parity_publisher_importer(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            real_run = tmp_path / "real_run"
            real_run.mkdir(mode=0o700)
            symlink_run = tmp_path / "symlink_run"
            symlink_run.symlink_to(real_run)
            home = tmp_path / "home"
            home.mkdir(mode=0o700)

            # Test 1: Symlinked ancestor Darwin path
            env1 = {"XDG_RUNTIME_DIR": str(symlink_run), "HOME": str(home)}
            importer_path1 = str(
                module["_beacon_directory"](home, env1, platform="darwin")
            )
            expected1 = str(real_run.resolve() / "pi-herdr-sessions")
            self.assertEqual(importer_path1, expected1)

            # Test 2: Fallback path when XDG unresolvable
            env2 = {
                "XDG_RUNTIME_DIR": str(tmp_path / "nonexistent"),
                "HOME": str(home),
            }
            importer_path2 = str(
                module["_beacon_directory"](home, env2, platform="darwin")
            )
            expected2 = str(home.resolve() / ".cache/pi-herdr-sessions")
            self.assertEqual(importer_path2, expected2)

    def test_beacon_reader_stays_bound_to_open_directory_after_path_replacement(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = pathlib.Path(tmp) / "home"
            home.mkdir()
            proc, _tty = self.proc_fixture(tmp, b"OTHER_ENV=not-retained\0")
            beacon = self.write_beacon(home)
            moved = pathlib.Path(tmp) / "moved-beacons"
            attacker = pathlib.Path(tmp) / "attacker-beacons"
            attacker.mkdir(mode=0o700)
            real_open = module["_open_beacon_directory"]
            original_parent = beacon.parent

            def replace_after_open(directory):
                fd = real_open(directory)
                original_parent.rename(moved)
                original_parent.symlink_to(attacker)
                return fd

            with patch.dict(
                module["_read_pi_beacon"].__globals__,
                {"_open_beacon_directory": replace_after_open},
            ):
                ref, warning = module["_read_pi_beacon"](
                    101, "%1", pathlib.Path(tmp) / "proc", home=home, environ={}
                )
            self.assertEqual(ref, {"kind": "id", "value": "session-123"})
            self.assertIsNone(warning)
            self.assertTrue((moved / "101.json").exists())
            self.assertEqual(list(attacker.iterdir()), [])

    def test_open_beacon_directory_handles_colliding_ancestor_and_leaf_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            target = base / "nested" / "middle" / "nested"
            target.mkdir(parents=True, mode=0o700)
            (base / "nested").chmod(0o755)
            (base / "nested" / "middle").chmod(0o755)
            target.chmod(0o700)
            fd = module["_open_beacon_directory"](target)
            self.assertIsInstance(fd, int)
            self.assertGreaterEqual(fd, 0)
            os.close(fd)

    def test_valid_beacon_preferred_over_environment_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = pathlib.Path(tmp) / "home"
            home.mkdir()
            proc, tty = self.proc_fixture(tmp, b"PI_SESSION_ID=environment-id\0")
            self.write_beacon(home)
            ref, warning = module["resolve_pi_session"](
                "100", str(tty), proc, home=home, pane_id="%1", environ={}
            )
        self.assertEqual(ref, {"kind": "id", "value": "session-123"})
        self.assertIsNone(warning)

    def test_beacon_rejects_pid_mismatch_and_wrong_owner(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = pathlib.Path(tmp) / "home"
            home.mkdir()
            proc, tty = self.proc_fixture(tmp, b"PI_SESSION_ID=fallback-id\0")
            beacon = self.write_beacon(home)
            payload = json.loads(beacon.read_text())
            payload["pid"] = 999
            beacon.write_text(json.dumps(payload))
            ref, warning = module["resolve_pi_session"](
                "100", str(tty), proc, home=home, pane_id="%1", environ={}
            )
            self.assertEqual(ref, {"kind": "id", "value": "fallback-id"})
            self.assertEqual(warning, "beacon_pid_mismatch")
            uid = os.getuid()
            with patch.object(
                module["_read_pi_beacon"].__globals__["os"],
                "getuid",
                side_effect=[uid, uid + 1],
            ):
                ref, warning = module["resolve_pi_session"](
                    "100", str(tty), proc, home=home, pane_id="%1", environ={}
                )
        self.assertEqual(ref, {"kind": "id", "value": "fallback-id"})
        self.assertEqual(warning, "beacon_wrong_owner")

    def test_missing_beacon_uses_approved_environment_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = pathlib.Path(tmp) / "home"
            home.mkdir()
            proc, tty = self.proc_fixture(tmp, b"PI_SESSION_ID=fallback-id\0")
            ref, warning = module["resolve_pi_session"](
                "100", str(tty), proc, home=home, pane_id="%1", environ={}
            )
        self.assertEqual(ref, {"kind": "id", "value": "fallback-id"})
        self.assertIsNone(warning)

    def test_beacon_rejects_stale_process_identity_and_wrong_pane(self):
        for attrs, expected in [
            ({"start_time": "987653"}, "beacon_stale_process"),
            ({"pane_id": "%9"}, "beacon_pane_mismatch"),
        ]:
            with self.subTest(attrs=attrs), tempfile.TemporaryDirectory() as tmp:
                home = pathlib.Path(tmp) / "home"
                home.mkdir()
                proc, tty = self.proc_fixture(tmp, b"PI_SESSION_ID=environment-id\0")
                self.write_beacon(
                    home,
                    pane_id=attrs.get("pane_id", "%1"),
                    start_time=attrs.get("start_time", "987654"),
                )
                ref, warning = module["resolve_pi_session"](
                    "100", str(tty), proc, home=home, pane_id="%1", environ={}
                )
            self.assertEqual(ref, {"kind": "id", "value": "environment-id"})
            self.assertEqual(warning, expected)

    def test_beacon_rejects_invalid_security_and_payload_variants(self):
        for case in (
            "mode",
            "symlink",
            "schema",
            "json",
            "directory",
            "directory_symlink",
        ):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                home = pathlib.Path(tmp) / "home"
                home.mkdir()
                proc, tty = self.proc_fixture(tmp, b"PI_SESSION_ID=fallback-id\0")
                beacon = self.write_beacon(
                    home, mode=0o644 if case == "mode" else 0o600
                )
                expected = {
                    "mode": "beacon_loose_permissions",
                    "symlink": "beacon_invalid_file_type",
                    "schema": "beacon_invalid_schema",
                    "json": "beacon_malformed",
                    "directory": "beacon_untrusted_directory",
                    "directory_symlink": "beacon_untrusted_directory",
                }[case]
                if case == "symlink":
                    beacon.unlink()
                    beacon.symlink_to(home / "outside")
                elif case == "schema":
                    beacon.write_text('{"schema":2}')
                elif case == "json":
                    beacon.write_text("{")
                elif case == "directory":
                    beacon.parent.chmod(0o755)
                elif case == "directory_symlink":
                    real_base = pathlib.Path(tmp) / "real-cache"
                    real_base.mkdir()
                    real_directory = real_base / "pi-herdr-sessions"
                    beacon.parent.rename(real_directory)
                    (home / ".cache").rmdir()
                    (home / ".cache").symlink_to(real_base)
                ref, warning = module["resolve_pi_session"](
                    "100", str(tty), proc, home=home, pane_id="%1", environ={}
                )
            self.assertEqual(ref, {"kind": "id", "value": "fallback-id"})
            self.assertEqual(warning, expected)

    def test_beacon_bad_reference_never_leaks_secret(self):
        secret = "/private/SECRET/session.jsonl"
        with tempfile.TemporaryDirectory() as tmp:
            home = pathlib.Path(tmp) / "home"
            home.mkdir()
            proc, tty = self.proc_fixture(tmp, b"OTHER_SECRET=never-export\0")
            self.write_beacon(home, session_ref={"kind": "path", "value": secret})
            ref, warning = module["resolve_pi_session"](
                "100", str(tty), proc, home=home, pane_id="%1", environ={}
            )
        self.assertIsNone(ref)
        self.assertEqual(warning, "beacon_invalid_session_reference")
        self.assertNotIn(secret, warning)

    def test_auto_resolution_prefers_valid_session_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = pathlib.Path(tmp) / "home"
            session = (
                home
                / '.pi/agent/sessions/project/space "quote" \\\\ slash-日本語.jsonl'
            )
            session.parent.mkdir(parents=True)
            session.write_text("")
            env = f"PI_SESSION_FILE={session}\0PI_SESSION_ID=550e8400-e29b-41d4-a716-446655440000\0".encode()
            proc, tty = self.proc_fixture(tmp, env)
            ref, warning = module["resolve_pi_session"](
                "100", str(tty), proc, home=home
            )
        self.assertEqual(ref, {"kind": "path", "value": str(session.resolve())})
        self.assertIsNone(warning)

    def test_auto_resolution_accepts_exact_session_id(self):
        session_id = "550e8400-e29b-41d4-a716-446655440000"
        with tempfile.TemporaryDirectory() as tmp:
            proc, tty = self.proc_fixture(tmp, f"PI_SESSION_ID={session_id}\0".encode())
            ref, warning = module["resolve_pi_session"]("100", str(tty), proc, home=tmp)
        self.assertEqual(ref, {"kind": "id", "value": session_id})
        self.assertIsNone(warning)

    def test_session_identifier_byte_boundary_matches_darwin_contract(self):
        exact = "a" * module["SESSION_ID_MAX_BYTES"]
        self.assertEqual(module["_valid_pi_session_id"](exact), exact)
        self.assertIsNone(module["_valid_pi_session_id"](exact + "a"))
        self.assertIsNone(module["_valid_pi_session_id"]("é" + "a" * 255))

    def test_auto_resolution_accepts_documented_custom_id_and_rejects_invalid_id(self):
        self.assertEqual(module["_valid_pi_session_id"]("abc123._x"), "abc123._x")
        self.assertIsNone(module["_valid_pi_session_id"]("id with spaces"))
        with tempfile.TemporaryDirectory() as tmp:
            proc, tty = self.proc_fixture(tmp, b"PI_SESSION_ID=bad id\0")
            ref, warning = module["resolve_pi_session"]("100", str(tty), proc, home=tmp)
        self.assertIsNone(ref)
        self.assertEqual(warning, "invalid_session_id")
        self.assertNotIn("bad id", warning)

    def test_pi_reference_validator_checks_path_ownership_and_regular_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = pathlib.Path(tmp) / "home"
            sessions = home / ".pi/agent/sessions/project"
            sessions.mkdir(parents=True)
            regular = sessions / "session.jsonl"
            regular.write_text("")
            uid = os.getuid()
            with patch.object(
                module["validate_pi_session_ref"].__globals__["os"],
                "getuid",
                return_value=uid + 1,
            ):
                ref, warning = module["validate_pi_session_ref"](
                    {"kind": "path", "value": str(regular)}, home
                )
            self.assertIsNone(ref)
            self.assertEqual(warning, "invalid_session_path")
            nonregular = sessions / "directory.jsonl"
            nonregular.mkdir()
            ref, warning = module["validate_pi_session_ref"](
                {"kind": "path", "value": str(nonregular)}, home
            )
            self.assertIsNone(ref)
            self.assertEqual(warning, "invalid_session_path")

    def test_auto_resolution_rejects_untrusted_file_path(self):
        session_id = "550e8400-e29b-41d4-a716-446655440000"
        with tempfile.TemporaryDirectory() as tmp:
            env = f"PI_SESSION_FILE=/etc/passwd\0PI_SESSION_ID={session_id}\0".encode()
            proc, tty = self.proc_fixture(tmp, env)
            ref, warning = module["resolve_pi_session"]("100", str(tty), proc, home=tmp)
        self.assertEqual(ref, {"kind": "id", "value": session_id})
        self.assertEqual(warning, "invalid_session_file_ignored")
        self.assertNotIn("/etc/passwd", warning)

    def test_auto_resolution_handles_duplicate_keys_and_truncated_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc, tty = self.proc_fixture(
                tmp, b"PI_SESSION_ID=first-id\0PI_SESSION_ID=second-id\0"
            )
            ref, warning = module["resolve_pi_session"]("100", str(tty), proc, home=tmp)
            self.assertIsNone(ref)
            self.assertEqual(warning, "duplicate_session_environment")
            oversized = b"UNRELATED=" + b"x" * 65600 + b"\0PI_SESSION_ID=lost\0"
            second_fixture = pathlib.Path(tmp) / "oversized"
            second_fixture.mkdir()
            proc, tty = self.proc_fixture(second_fixture, oversized)
            ref, warning = module["resolve_pi_session"]("100", str(tty), proc, home=tmp)
        self.assertIsNone(ref)
        self.assertEqual(warning, "environment_truncated")
        self.assertNotIn("first-id", warning)
        self.assertNotIn("second-id", warning)

    def test_auto_resolution_rejects_complete_chain_change(self):
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.dict(
                _real_resolve_pi_session.__globals__,
                {"_same_proc_chain": lambda _root, _chain: False},
            ),
        ):
            proc, tty = self.proc_fixture(tmp, b"PI_SESSION_ID=chain-race\0")
            ref, warning = module["resolve_pi_session"]("100", str(tty), proc, home=tmp)
        self.assertIsNone(ref)
        self.assertEqual(warning, "process_disappeared")

    def test_same_proc_chain_rejects_empty_chain(self):
        self.assertFalse(module["_same_proc_chain"](pathlib.Path("/proc"), ()))
        self.assertFalse(module["_same_proc_chain"](pathlib.Path("/proc"), []))

    def test_auto_resolution_rejects_uncaptured_candidate_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = pathlib.Path(tmp) / "home"
            home.mkdir()
            proc, tty = self.proc_fixture(tmp, b"PI_SESSION_ID=valid-id\0")
            self.write_beacon(home)
            with patch.dict(
                _real_resolve_pi_session.__globals__,
                {
                    "_proc_chain": lambda *args: (_ for _ in ()).throw(
                        ValueError("cycle")
                    )
                },
            ):
                ref, warning = module["resolve_pi_session"](
                    "100", str(tty), proc, home=home, pane_id="%1", environ={}
                )
            self.assertIsNone(ref)
            self.assertEqual(warning, "process_disappeared")

    def test_auto_resolution_fails_closed_on_multiple_foreground_candidates(self):
        session_id = "550e8400-e29b-41d4-a716-446655440000"
        with tempfile.TemporaryDirectory() as tmp:
            proc, tty = self.proc_fixture(
                tmp,
                f"PI_SESSION_ID={session_id}\0".encode(),
                {102: f"PI_SESSION_ID={session_id}\0".encode()},
            )
            ref, warning = module["resolve_pi_session"]("100", str(tty), proc, home=tmp)
        self.assertIsNone(ref)
        self.assertEqual(warning, "ambiguous_processes")

    def test_auto_resolution_handles_missing_unsupported_and_vanished_proc(self):
        with tempfile.TemporaryDirectory() as tmp:
            ref, warning = module["resolve_pi_session"](
                "100", "/dev/pts/1", pathlib.Path(tmp) / "absent"
            )
            self.assertIsNone(ref)
            self.assertEqual(warning, "proc_unavailable")
            ref, warning = module["resolve_pi_session"](
                "100", "/dev/pts/1", tmp, platform="darwin", pane_id="%1"
            )
            self.assertIsNone(ref)
            self.assertEqual(warning, "helper_missing")
            proc = pathlib.Path(tmp) / "proc"
            proc.mkdir()
            ref, warning = module["resolve_pi_session"]("123", "/dev/pts/1", proc)
            self.assertIsNone(ref)
            self.assertEqual(warning, "process_disappeared")

    def test_darwin_missing_pane_metadata_precedes_storage_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            for pane_pid, pane_tty in (
                (None, None),
                ("100", None),
                (None, "/dev/pts/1"),
            ):
                with self.subTest(pane_pid=pane_pid, pane_tty=pane_tty):
                    ref, warning = module["resolve_pi_session"](
                        pane_pid, pane_tty, tmp, platform="darwin"
                    )
                    self.assertIsNone(ref)
                    self.assertEqual(warning, "tmux_pane_missing")

    def test_darwin_resolution_never_falls_back_to_ps_or_environment(self):
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.dict(
                _real_resolve_pi_session.__globals__,
                {
                    "_read_pi_environment": lambda *args: self.fail(
                        "Darwin must not inspect process environments"
                    ),
                    "_read_pi_beacon": lambda *args, **kwargs: self.fail(
                        "Darwin must not read an unpinned beacon path"
                    ),
                },
            ),
        ):
            ref, warning = module["resolve_pi_session"](
                "100", "/dev/pts/1", tmp, platform="darwin", pane_id="%1"
            )
        self.assertIsNone(ref)
        self.assertEqual(warning, "helper_missing")

    def test_darwin_helper_streams_and_bounds_real_stdout(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = pathlib.Path(tmp) / "libexec"
            parent.mkdir(mode=0o700)
            parent.chmod(0o700)
            helper = parent / "tmux-herdr-darwin-helper"
            helper.write_text(
                "#!/usr/bin/env python3\nimport sys\nsys.stdout.write('x' * 20000)\n"
            )
            helper.chmod(0o700)
            result, warning = module["_run_darwin_helper"]("{}", helper_path=helper)
            self.assertIsNone(result)
            self.assertEqual(warning, "helper_process_failure")

    def test_darwin_helper_uses_deadline_bounded_nonblocking_stdin(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = pathlib.Path(tmp) / "libexec"
            parent.mkdir(mode=0o700)
            parent.chmod(0o700)
            helper = parent / "tmux-herdr-darwin-helper"
            helper.write_text("#!/usr/bin/env python3\nimport time\ntime.sleep(10)\n")
            helper.chmod(0o700)
            result, warning = module["_run_darwin_helper"](
                "x" * 16384, helper_path=helper
            )
        self.assertIsNone(result)
        self.assertEqual(warning, "helper_process_failure")

    def test_darwin_helper_cleanup_on_exception(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = pathlib.Path(tmp) / "libexec"
            parent.mkdir(mode=0o700)
            parent.chmod(0o700)
            helper = parent / "tmux-herdr-darwin-helper"
            helper.write_text(
                "#!/usr/bin/env python3\nimport sys\nsys.stdout.write('not-json\\n')\n"
            )
            helper.chmod(0o700)
            stopped = []
            real_stop = module["_stop_darwin_process"]

            def tracking_stop(proc):
                stopped.append(proc)
                return real_stop(proc)

            with patch.dict(
                module["_run_darwin_helper"].__globals__,
                {"_stop_darwin_process": tracking_stop},
            ):
                result, warning = module["_run_darwin_helper"]("{}", helper_path=helper)
            self.assertIsNone(result)
            self.assertEqual(warning, "helper_process_failure")
            self.assertTrue(len(stopped) > 0)

    def test_darwin_helper_timeout_expired_uses_seconds(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = pathlib.Path(tmp) / "libexec"
            parent.mkdir(mode=0o700)
            parent.chmod(0o700)
            helper = parent / "tmux-herdr-darwin-helper"
            helper.write_text("#!/usr/bin/env python3\nimport time\ntime.sleep(10)\n")
            helper.chmod(0o700)
            captured_timeouts = []
            real_timeout_init = subprocess.TimeoutExpired.__init__

            def tracking_timeout(self, cmd, timeout, output=None, stderr=None):
                captured_timeouts.append(timeout)
                return real_timeout_init(
                    self, cmd, timeout, output=output, stderr=stderr
                )

            with patch.object(subprocess.TimeoutExpired, "__init__", tracking_timeout):
                result, warning = module["_run_darwin_helper"](
                    "x" * 16384, helper_path=helper
                )
            self.assertIsNone(result)
            self.assertEqual(warning, "helper_process_failure")
            self.assertIn(1.5, captured_timeouts)
            self.assertNotIn(1500, captured_timeouts)

    def test_darwin_helper_requires_exact_0700_modes(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = pathlib.Path(tmp) / "libexec"
            parent.mkdir(mode=0o700)
            parent.chmod(0o700)
            helper = parent / "tmux-herdr-darwin-helper"
            helper.write_bytes(b"helper")
            helper.chmod(0o700)
            module["_validate_darwin_helper"](helper)
            for mode in (0o744, 0o755, 0o600):
                helper.chmod(mode)
                with self.assertRaisesRegex(ValueError, "helper_build_failure"):
                    module["_validate_darwin_helper"](helper)
            helper.chmod(0o700)
            for mode in (0o744, 0o755, 0o750):
                parent.chmod(mode)
                with self.assertRaisesRegex(ValueError, "helper_build_failure"):
                    module["_validate_darwin_helper"](helper)

    def test_darwin_helper_valid_and_malformed_responses(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls = []
            self.write_beacon(tmp, pid=101, pane_id="%1", start_time="123.000456")

            def valid_runner(action, request):
                calls.append((action, json.loads(request)))
                return json.dumps(
                    {
                        "ok": True,
                        "kind": "id",
                        "value": "mac-id",
                        "pid": 101,
                        "start_time": "123.000456",
                    }
                )

            ref, warning = module["resolve_pi_session"](
                "100",
                "/dev/ttys001",
                tmp,
                home=tmp,
                platform="darwin",
                pane_id="%1",
                environ={},
                helper_runner=valid_runner,
            )
            self.assertEqual(ref, {"kind": "id", "value": "session-123"})
            self.assertIsNone(warning)
            self.assertEqual(calls[0][0], "resolve")
            self.assertEqual(calls[0][1]["pane_pid"], 100)
            self.assertEqual(calls[0][1]["pane_id"], "%1")

            for output, expected in (
                ("{}", "helper_process_failure"),
                ('{"ok":true,"extra":1}', "helper_process_failure"),
                ('{"ok":false}', "helper_process_failure"),
                ('{"ok":false,"reason":"unknown"}', "helper_process_failure"),
                (
                    '{"ok":false,"reason":"io","reason":"stale"}',
                    "helper_process_failure",
                ),
                (json.dumps({"ok": False, "reason": "stale"}), "beacon_stale_process"),
                (
                    json.dumps({"ok": False, "reason": "process_tree_too_large"}),
                    "process_tree_too_large",
                ),
                (
                    "x" * (module["DARWIN_HELPER_OUTPUT_LIMIT"] + 1),
                    "helper_process_failure",
                ),
            ):
                ref, warning = module["resolve_pi_session"](
                    "100",
                    "/dev/ttys001",
                    tmp,
                    home=tmp,
                    platform="darwin",
                    pane_id="%1",
                    environ={},
                    helper_runner=lambda _action, _request, value=output: value,
                )
                self.assertIsNone(ref)
                self.assertEqual(warning, expected)

            ref, warning = module["resolve_pi_session"](
                "100",
                "/dev/ttys001",
                tmp,
                home=tmp,
                platform="darwin",
                pane_id="%1",
                environ={},
                helper_runner=lambda _action, _request: (_ for _ in ()).throw(
                    TimeoutError()
                ),
            )
            self.assertIsNone(ref)
            self.assertEqual(warning, "helper_process_failure")

    def test_missing_tmux_pane_has_non_sensitive_reason(self):
        ref, warning = module["resolve_pi_session"](
            None, None, "/proc", platform="linux"
        )
        self.assertIsNone(ref)
        self.assertEqual(warning, "tmux_pane_missing")

    def test_proc_permission_denied_is_non_sensitive(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc, tty = self.proc_fixture(tmp, b"PI_SESSION_ID=secret-id\0")
            with patch.dict(
                _real_resolve_pi_session.__globals__,
                {
                    "_read_pi_environment": lambda path: (_ for _ in ()).throw(
                        PermissionError()
                    )
                },
            ):
                ref, warning = module["resolve_pi_session"](
                    "100", str(tty), proc, home=tmp
                )
        self.assertIsNone(ref)
        self.assertEqual(warning, "proc_permission_denied")
        self.assertNotIn("secret-id", warning)

    def test_snapshot_output_file_is_mode_0600(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = pathlib.Path(tmp) / "snapshot.json"
            argv = ["tmux-herdr", "--snapshot", "pilot", "--output", str(output)]
            with (
                patch.object(sys, "argv", argv),
                patch.dict(
                    module["main"].__globals__,
                    {"run": self.fake_tmux_snapshot_run()},
                ),
            ):
                self.assertEqual(module["main"](), 0)
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)

    def test_snapshot_output_file_rejects_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            real_file = pathlib.Path(tmp) / "real.json"
            real_file.touch()
            symlink_output = pathlib.Path(tmp) / "symlink.json"
            symlink_output.symlink_to(real_file)
            argv = [
                "tmux-herdr",
                "--snapshot",
                "pilot",
                "--output",
                str(symlink_output),
            ]
            with (
                patch.object(sys, "argv", argv),
                patch.object(sys, "stderr", io.StringIO()),
                patch.dict(
                    module["main"].__globals__,
                    {"run": self.fake_tmux_snapshot_run()},
                ),
            ):
                self.assertEqual(module["main"](), 1)

    def test_snapshot_resolution_is_opt_in_and_never_leaks_other_environment(self):
        secret = "DO_NOT_LEAK_ENV_VALUE"
        session_id = "550e8400-e29b-41d4-a716-446655440000"
        with tempfile.TemporaryDirectory() as tmp:
            proc, tty = self.proc_fixture(
                tmp, f"OTHER_SECRET={secret}\0PI_SESSION_ID={session_id}\0".encode()
            )
            namespace = module["tmux_snapshot"].__globals__
            resolver = module["resolve_pi_session"]
            with patch.dict(
                namespace, {"run": self.fake_tmux_snapshot_run(pane_tty=str(tty))}
            ):
                with patch.dict(
                    namespace,
                    {
                        "resolve_pi_session": lambda *args, **kwargs: (
                            _ for _ in ()
                        ).throw(AssertionError("resolver ran without opt-in"))
                    },
                ):
                    disabled = module["tmux_snapshot"]("pilot")
            self.assertFalse(disabled["pi_session_resolution"]["enabled"])
            self.assertIsNone(
                disabled["tabs"][0]["panes"][0]["application"]["session_ref"]
            )
            with patch.dict(
                namespace,
                {
                    "run": self.fake_tmux_snapshot_run(pane_tty=str(tty)),
                    "resolve_pi_session": lambda *args, **kwargs: resolver(
                        *args, **{**kwargs, "home": pathlib.Path(tmp) / "home"}
                    ),
                },
            ):
                enabled = module["tmux_snapshot"](
                    "pilot", resolve_pi_sessions=True, proc_root=proc
                )
            output = json.dumps(enabled)
            self.assertEqual(enabled["pi_session_resolution"]["resolved"], 1)
            self.assertEqual(
                enabled["tabs"][0]["panes"][0]["application"]["session_ref"]["value"],
                session_id,
            )
            self.assertNotIn(secret, output)
            self.assertNotIn("OTHER_SECRET", output)

    def test_no_pi_pane_skips_beacon_resolution(self):
        def shell_tmux(argv, **kwargs):
            if argv[1:3] == ["list-sessions", "-F"]:
                return "pilot\n"
            if argv[1:3] == ["list-windows", "-t"]:
                return "1\tshell\t1\tlayout\n"
            if argv[1:4] == ["display-message", "-p", "-t"]:
                return "1\n"
            if argv[1:3] == ["list-panes", "-t"]:
                return "0\t1\t/tmp\tzsh\tshell\t80\t24\t0\t0\t79\t23\t100\t/dev/pts/1\t%1\n"
            raise AssertionError(f"unexpected tmux command: {argv}")

        namespace = module["tmux_snapshot"].__globals__
        with patch.dict(
            namespace,
            {
                "run": shell_tmux,
                "resolve_pi_session": lambda *a, **k: self.fail("non-Pi pane resolved"),
            },
        ):
            snapshot = module["tmux_snapshot"]("pilot", resolve_pi_sessions=True)
        self.assertEqual(
            snapshot["tabs"][0]["panes"][0]["application"]["kind"], "shell"
        )
        self.assertNotIn("pane_id", json.dumps(snapshot))

    def test_no_foreground_pi_candidate_has_no_session_ref(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = pathlib.Path(tmp) / "proc"
            proc.mkdir()
            ref, warning = module["resolve_pi_session"](
                "100", "/dev/pts/1", proc, pane_id="%1"
            )
        self.assertIsNone(ref)
        self.assertEqual(warning, "process_disappeared")

    def test_snapshot_invalid_pi_environment_warning_does_not_leak_values(self):
        private_path = "/private/project/session.jsonl"
        invalid_id = "invalid id"
        with tempfile.TemporaryDirectory() as tmp:
            proc, tty = self.proc_fixture(
                tmp,
                f"PI_SESSION_FILE={private_path}\0PI_SESSION_ID={invalid_id}\0".encode(),
            )
            namespace = module["tmux_snapshot"].__globals__
            resolver = module["resolve_pi_session"]
            with patch.dict(
                namespace,
                {
                    "run": self.fake_tmux_snapshot_run(pane_tty=str(tty)),
                    "resolve_pi_session": lambda *args, **kwargs: resolver(
                        *args, **{**kwargs, "home": pathlib.Path(tmp) / "home"}
                    ),
                },
            ):
                snapshot = module["tmux_snapshot"](
                    "pilot", resolve_pi_sessions=True, proc_root=proc
                )
            output = json.dumps(snapshot)
        self.assertIsNone(snapshot["tabs"][0]["panes"][0]["application"]["session_ref"])
        self.assertNotIn(private_path, output)
        self.assertNotIn(invalid_id, output)

    def test_safe_classification_and_unknown_fallback(self):
        self.assertEqual(module["classify"]("npm"), {"kind": "unknown"})
        snap = {
            "name": "pilot",
            "tabs": [{"name": "dev", "panes": [pane("unknown", "npm")]}],
        }
        item = module["plan"](snap)["operations"][0]
        self.assertIsNone(item["command"])
        self.assertIn("not replayed", item["warning"])

    def test_pi_exact_reference_and_missing_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            session_file = pathlib.Path(tmp) / ".pi/agent/sessions/project/a.jsonl"
            session_file.parent.mkdir(parents=True)
            session_file.write_text("")
            snap = {
                "name": "x",
                "tabs": [
                    {
                        "name": "pi",
                        "panes": [
                            pane(
                                "pi",
                                "pi",
                                ref={"kind": "path", "value": str(session_file)},
                            )
                        ],
                    }
                ],
            }
            with patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)):
                self.assertEqual(
                    module["plan"](snap)["operations"][0]["command"],
                    [
                        "tmux-herdr",
                        "resume-pi",
                        "path",
                        str(session_file.resolve()),
                    ],
                )
            snap["tabs"][0]["panes"][0]["application"]["session_ref"] = None
            self.assertIsNone(module["plan"](snap)["operations"][0]["command"])
            self.assertIn(
                "pi_session_unknown", module["plan"](snap)["operations"][0]["warning"]
            )

    def test_positional_pi_launcher_revalidates_and_execs(self):
        with tempfile.TemporaryDirectory() as tmp:
            session_file = pathlib.Path(tmp) / ".pi/agent/sessions/project/a.jsonl"
            session_file.parent.mkdir(parents=True)
            session_file.write_text("")
            with (
                patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)),
                patch.object(os, "execvp") as execvp,
            ):
                self.assertEqual(
                    module["launch_pi"](
                        ["resume-pi", "path", str(session_file.resolve())]
                    ),
                    0,
                )
                execvp.assert_called_once_with(
                    "pi", ["pi", "--session", str(session_file.resolve())]
                )

        with patch.object(os, "execvp") as execvp:
            self.assertEqual(module["launch_pi"](["continue-pi"]), 0)
            execvp.assert_called_once_with("pi", ["pi", "--continue"])

        with patch.object(os, "execvp") as execvp:
            with self.assertRaisesRegex(ValueError, "invalid Pi session reference"):
                module["launch_pi"](["resume-pi", "path", "/etc/passwd"])
            execvp.assert_not_called()

    def test_plan_rejects_invalid_manually_injected_pi_references(self):
        refs = [
            {"kind": "path", "value": "/etc/passwd"},
            {"kind": "id", "value": "invalid id"},
            {"kind": "path", "value": 5},
            {"kind": "other", "value": "secret-looking-value"},
        ]
        for ref in refs:
            with self.subTest(ref=ref):
                snap = {
                    "name": "manual",
                    "tabs": [{"name": "pi", "panes": [pane("pi", "pi", ref=ref)]}],
                }
                result = module["plan"](snap, allow_continue=True)
                operation = result["operations"][0]
                self.assertIsNone(operation["command"])
                self.assertIn("invalid Pi session reference", operation["warning"])
                self.assertNotIn(str(ref["value"]), operation["warning"])
                self.assertNotIn(str(ref["value"]), json.dumps(result))

    def test_lazygit_and_shell_adapter(self):
        snap = {
            "name": "x",
            "tabs": [
                {
                    "name": "apps",
                    "panes": [pane("lazygit", "lazygit"), pane("shell", "zsh")],
                }
            ],
        }
        ops = module["plan"](snap)["operations"]
        self.assertEqual(ops[0]["command"], ["lazygit"])
        self.assertIsNone(ops[1]["command"])

    def test_unavailable_cwd_warns_without_launch(self):
        p = pane("lazygit", "lazygit", "/deleted")
        p["cwd_exists"] = False
        plan = module["plan"]({"name": "x", "tabs": [{"name": "t", "panes": [p]}]})
        self.assertIsNone(plan["operations"][0]["command"])
        self.assertIn("cwd_unavailable", plan["warnings"][0])

    def test_apply_does_not_launch_manually_injected_untrusted_pi_ref(self):
        calls = []
        snapshot = self.apply_snapshot("pi")
        snapshot["tabs"][0]["panes"][0]["application"]["session_ref"] = {
            "kind": "path",
            "value": "/etc/passwd",
        }
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)),
            patch.dict(
                module["apply"].__globals__,
                {
                    "run": lambda argv: "status: running\n",
                    "herdr": self.make_apply_mocks(calls),
                },
            ),
        ):
            module["apply"](snapshot, "untrusted-pi", allow_continue=True)
        self.assertFalse(
            any(
                call[:2] == ("untrusted-pi", "pane") and call[2:4] == ("run", "pane-1")
                for call in calls
            )
        )

    def test_apply_identical_completed_repeat_is_noop(self):
        calls = []
        snapshot = self.apply_snapshot()
        fake_herdr = self.make_apply_mocks(calls)
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)),
            patch.dict(
                module["apply"].__globals__,
                {"run": lambda argv: "status: running\n", "herdr": fake_herdr},
            ),
        ):
            module["apply"](snapshot, "repeat-target")
            calls.clear()
            module["apply"](snapshot, "repeat-target")
            self.assertEqual(calls, [("repeat-target", "workspace", "list")])

    def test_apply_uses_nested_0_9_1_ids_and_expected_commands(self):
        calls = []
        snapshot = self.apply_snapshot()
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)),
            patch.dict(
                module["apply"].__globals__,
                {
                    "run": lambda argv: "status: running\n",
                    "herdr": self.make_apply_mocks(calls),
                },
            ),
        ):
            module["apply"](snapshot, "pilot-target")
            marker = self.marker_path(tmp, "pilot-target", snapshot)
            manifest = json.loads(marker.read_text())
            self.assertEqual(manifest["status"], "applied")
            self.assertEqual(marker.stat().st_mode & 0o777, 0o600)
        self.assertIn(("pilot-target", "tab", "rename", "tab-1", "first-window"), calls)
        self.assertIn(("pilot-target", "pane", "rename", "pane-1", "title"), calls)
        self.assertIn(
            (
                "pilot-target",
                "pane",
                "split",
                "--pane",
                "pane-1",
                "--direction",
                "down",
                "--ratio",
                "0.5000",
                "--cwd",
                "/tmp",
                "--no-focus",
            ),
            calls,
        )
        self.assertIn(("pilot-target", "pane", "run", "pane-1", "lazygit"), calls)
        self.assertIn(("pilot-target", "tab", "focus", "tab-1"), calls)
        self.assertIn(
            (
                "pilot-target",
                "workspace",
                "create",
                "--label",
                "tmux:pilot-source",
                "--cwd",
                "/tmp",
                "--focus",
            ),
            calls,
        )
        self.assertIn(
            (
                "pilot-target",
                "tab",
                "create",
                "--workspace",
                "ws-1",
                "--label",
                "second-window",
                "--cwd",
                "/tmp",
                "--no-focus",
            ),
            calls,
        )

    def test_list_workspaces_accepts_nested_0_9_1_envelopes(self):
        self.assertEqual(
            module["_list_workspaces"](
                {
                    "id": "cli:workspace:list",
                    "result": {"type": "workspace_list", "workspaces": []},
                }
            ),
            [],
        )
        workspaces = [{"workspace_id": "existing", "label": "unrelated"}]
        self.assertEqual(
            module["_list_workspaces"](
                {
                    "id": "cli:workspace:list",
                    "result": {"type": "workspace_list", "workspaces": workspaces},
                }
            ),
            workspaces,
        )

    def test_append_keeps_unrelated_and_previous_workspaces(self):
        first = self.apply_snapshot()
        second = copy.deepcopy(first)
        first["name"] = "source-one"
        second["name"] = "source-two"
        calls = []
        workspaces = [{"workspace_id": "unrelated", "label": "notes"}]
        base = self.make_apply_mocks(calls)

        def append_herdr(target, *args):
            if args[:2] == ("workspace", "list"):
                return {
                    "id": "cli:workspace:list",
                    "result": {
                        "type": "workspace_list",
                        "workspaces": list(workspaces),
                    },
                }
            response = base(target, *args)
            if args[:2] == ("workspace", "create"):
                workspaces.append(
                    {
                        "workspace_id": "managed-" + str(len(workspaces)),
                        "label": args[args.index("--label") + 1],
                    }
                )
            return response

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)),
            patch.dict(
                module["apply"].__globals__,
                {"run": lambda argv: "running", "herdr": append_herdr},
            ),
        ):
            module["apply"](first, "append-target")
            module["apply"](second, "append-target")
            self.assertEqual(
                {workspace["label"] for workspace in workspaces},
                {"notes", "tmux:source-one", "tmux:source-two"},
            )
            self.assertTrue(self.marker_path(tmp, "append-target", first).exists())
            self.assertTrue(self.marker_path(tmp, "append-target", second).exists())

    def test_detached_source_restores_active_tab_and_preserves_existing_focus(self):
        snapshot = self.apply_snapshot()
        snapshot["attached"] = False
        snapshot["tabs"][0]["active"] = False
        snapshot["tabs"][1]["active"] = True
        calls = []
        base = self.make_apply_mocks(calls)

        def focused_herdr(target, *args):
            if args[:2] == ("workspace", "list"):
                calls.append((target, *args))
                return {
                    "id": "cli:workspace:list",
                    "result": {
                        "type": "workspace_list",
                        "workspaces": [
                            {
                                "workspace_id": "existing",
                                "label": "notes",
                                "focused": True,
                                "active_tab_id": "existing-tab",
                            }
                        ],
                    },
                }
            return base(target, *args)

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)),
            patch.dict(
                module["apply"].__globals__,
                {"run": lambda argv: "running", "herdr": focused_herdr},
            ),
        ):
            module["apply"](snapshot, "focus-target")

        self.assertIn(
            (
                "focus-target",
                "workspace",
                "create",
                "--label",
                "tmux:pilot-source",
                "--cwd",
                "/tmp",
                "--no-focus",
            ),
            calls,
        )
        self.assertIn(("focus-target", "tab", "focus", "tab-2"), calls)
        self.assertEqual(calls[-1], ("focus-target", "tab", "focus", "existing-tab"))

    def test_strict_snapshot_json_rejected_before_herdr_mutation(self):
        base = self.apply_snapshot()
        encoded = json.dumps(base)
        malformed = (
            encoded.replace('"schema": 1', '"schema": 2', 1),
            encoded.replace(
                '"name": "pilot-source"',
                '"name": "pilot-source", "name": "duplicate"',
                1,
            ),
            encoded.replace('"attached": true', '"attached": NaN', 1),
            encoded + " trailing",
        )
        for index, content in enumerate(malformed):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as tmp:
                snapshot_path = pathlib.Path(tmp) / "snapshot.json"
                snapshot_path.write_text(content)
                calls = []
                with (
                    patch.object(
                        sys,
                        "argv",
                        [
                            "tmux-herdr",
                            "--apply",
                            str(snapshot_path),
                            "--session",
                            "strict-target",
                        ],
                    ),
                    patch.dict(
                        module["main"].__globals__,
                        {"apply": lambda *args: calls.append(args)},
                    ),
                    contextlib.redirect_stderr(io.StringIO()),
                ):
                    self.assertEqual(module["main"](), 1)
                self.assertEqual(calls, [])

    def test_snapshot_requires_exact_active_tab_and_pane_cardinality(self):
        snapshot = self.apply_snapshot()
        snapshot["tabs"][1]["active"] = True
        with self.assertRaisesRegex(ValueError, "exactly one active tab"):
            module["_validate_snapshot"](snapshot)
        snapshot = self.apply_snapshot()
        snapshot["tabs"][0]["panes"][1]["active"] = True
        with self.assertRaisesRegex(ValueError, "exactly one active pane"):
            module["_validate_snapshot"](snapshot)

    def test_malformed_snapshot_refused_before_marker_or_mutation(self):
        snapshot = self.apply_snapshot()
        del snapshot["tabs"][0]["panes"][0]["application"]
        calls = []

        def fake_herdr(target, *args):
            calls.append((target, *args))
            if args[:2] == ("workspace", "list"):
                return {
                    "id": "cli:workspace:list",
                    "result": {"type": "workspace_list", "workspaces": []},
                }
            raise AssertionError("malformed snapshot reached Herdr mutation")

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)),
            patch.dict(
                module["apply"].__globals__,
                {"run": lambda argv: "running", "herdr": fake_herdr},
            ),
        ):
            with self.assertRaisesRegex(ValueError, "missing fields"):
                module["apply"](snapshot, "malformed-snapshot")
            self.assertEqual(calls, [("malformed-snapshot", "workspace", "list")])
            self.assertFalse(
                self.marker_path(tmp, "malformed-snapshot", snapshot).exists()
            )

    def test_non_positive_geometry_refused_before_marker_or_mutation(self):
        for key, value in (("width", 0), ("height", 0), ("width", -1), ("height", -1)):
            with (
                self.subTest(key=key, value=value),
                tempfile.TemporaryDirectory() as tmp,
            ):
                snapshot = self.apply_snapshot()
                snapshot["tabs"][0]["panes"][1]["geometry"][key] = value
                calls = []

                def fake_herdr(target, *args):
                    calls.append((target, *args))
                    if args[:2] == ("workspace", "list"):
                        return {
                            "id": "cli:workspace:list",
                            "result": {"type": "workspace_list", "workspaces": []},
                        }
                    raise AssertionError("invalid geometry reached Herdr mutation")

                with (
                    patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)),
                    patch.dict(
                        module["apply"].__globals__,
                        {"run": lambda argv: "running", "herdr": fake_herdr},
                    ),
                ):
                    with self.assertRaisesRegex(ValueError, "non-positive geometry"):
                        module["apply"](snapshot, f"geometry-{key}-{value}")
                    self.assertEqual(
                        calls,
                        [(f"geometry-{key}-{value}", "workspace", "list")],
                    )
                    self.assertFalse(
                        self.marker_path(
                            tmp, f"geometry-{key}-{value}", snapshot
                        ).exists()
                    )

    def test_unknown_server_status_refused_before_workspace_list(self):
        for status in ("", "stopped", "server: stopped", "unexpected output"):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp:
                calls = []

                def should_not_list(target, *args):
                    calls.append((target, *args))
                    raise AssertionError("unknown server status reached workspace list")

                with (
                    patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)),
                    patch.dict(
                        module["apply"].__globals__,
                        {
                            "run": lambda argv, value=status: value,
                            "herdr": should_not_list,
                        },
                    ),
                ):
                    with self.assertRaisesRegex(ValueError, "not explicitly running"):
                        module["apply"](self.apply_snapshot(), "status-target")
                self.assertEqual(calls, [])

    def test_focus_is_restored_after_post_focus_failure(self):
        snapshot = self.apply_snapshot()
        calls = []
        base = self.make_apply_mocks(calls)

        def failing_herdr(target, *args):
            if args[:2] == ("workspace", "list"):
                calls.append((target, *args))
                return {
                    "id": "cli:workspace:list",
                    "result": {
                        "type": "workspace_list",
                        "workspaces": [
                            {
                                "workspace_id": "existing",
                                "label": "notes",
                                "focused": True,
                                "active_tab_id": "existing-tab",
                            }
                        ],
                    },
                }
            if args[:2] == ("tab", "focus") and args[2] == "tab-1":
                calls.append((target, *args))
                raise RuntimeError("imported focus failed")
            return base(target, *args)

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)),
            patch.dict(
                module["apply"].__globals__,
                {"run": lambda argv: "running", "herdr": failing_herdr},
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "imported focus failed"):
                module["apply"](snapshot, "focus-failure")
            self.assertEqual(
                calls[-1], ("focus-failure", "tab", "focus", "existing-tab")
            )
            self.assertTrue(self.marker_path(tmp, "focus-failure", snapshot).exists())

    def test_duplicate_desired_labels_refused(self):
        snapshot = self.apply_snapshot()
        calls = []

        def duplicate(target, *args):
            calls.append((target, *args))
            if args[:2] == ("workspace", "list"):
                return {
                    "id": "cli:workspace:list",
                    "result": {
                        "type": "workspace_list",
                        "workspaces": [
                            {"workspace_id": "one", "label": "tmux:pilot-source"},
                            {"workspace_id": "two", "label": "tmux:pilot-source"},
                        ],
                    },
                }
            raise AssertionError("duplicate labels allowed mutation")

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)),
            patch.dict(
                module["apply"].__globals__,
                {"run": lambda argv: "running", "herdr": duplicate},
            ),
        ):
            with self.assertRaisesRegex(ValueError, "duplicate workspace label"):
                module["apply"](snapshot, "duplicate-target")
        self.assertFalse(self.marker_path(tmp, "duplicate-target", snapshot).exists())

    def test_legacy_dots_marker_is_noop_and_retained(self):
        snapshot = self.apply_snapshot()
        snapshot["name"] = "dots"
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            marker_dir = pathlib.Path(tmp) / ".local/state/tmux-herdr"
            marker_dir.mkdir(parents=True)
            identity = json.dumps(
                {"snapshot": snapshot, "allow_pi_continue": False}, sort_keys=True
            )
            legacy = marker_dir / "pilot.json"
            legacy.write_text(json.dumps({"status": "applied", "identity": identity}))
            legacy.chmod(0o600)

            def legacy_herdr(target, *args):
                calls.append((target, *args))
                if args[:2] == ("workspace", "list"):
                    return {
                        "id": "cli:workspace:list",
                        "result": {
                            "type": "workspace_list",
                            "workspaces": [
                                {"workspace_id": "dots", "label": "tmux:dots"}
                            ],
                        },
                    }
                raise AssertionError("legacy no-op allowed mutation")

            with (
                patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)),
                patch.dict(
                    module["apply"].__globals__,
                    {"run": lambda argv: "running", "herdr": legacy_herdr},
                ),
            ):
                module["apply"](snapshot, "pilot")
            self.assertTrue(legacy.exists())
            self.assertFalse(self.marker_path(tmp, "pilot", snapshot).exists())
            self.assertEqual(calls, [("pilot", "workspace", "list")])

    def test_partial_or_changed_source_marker_refuses_before_herdr(self):
        snapshot = self.apply_snapshot()
        for state in (
            {"status": "applying"},
            {"status": "applied", "identity": "different"},
        ):
            with self.subTest(state=state), tempfile.TemporaryDirectory() as tmp:
                marker = self.marker_path(tmp, "marker-target", snapshot)
                marker.parent.mkdir(parents=True)
                marker.write_text(json.dumps(state))
                marker.chmod(0o600)
                with (
                    patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)),
                    patch.dict(
                        module["apply"].__globals__,
                        {
                            "run": lambda argv: (_ for _ in ()).throw(
                                AssertionError("Herdr queried for rejected marker")
                            )
                        },
                    ),
                ):
                    with self.assertRaisesRegex(ValueError, "marker"):
                        module["apply"](snapshot, "marker-target")

    def test_malformed_workspace_entry_refused(self):
        for entry in (
            None,
            "workspace",
            {"label": "missing-id"},
            {"workspace_id": 5},
            {"workspace_id": "w1", "label": "bad-focus", "focused": "yes"},
            {"workspace_id": "w1", "label": "bad-tab", "active_tab_id": ""},
        ):
            with self.subTest(entry=entry), tempfile.TemporaryDirectory() as tmp:

                def malformed(target, *args):
                    if args[:2] == ("workspace", "list"):
                        return {
                            "id": "cli:workspace:list",
                            "result": {"type": "workspace_list", "workspaces": [entry]},
                        }
                    raise AssertionError("malformed entry allowed mutation")

                with (
                    patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)),
                    patch.dict(
                        module["apply"].__globals__,
                        {"run": lambda argv: "running", "herdr": malformed},
                    ),
                ):
                    with self.assertRaisesRegex(ValueError, "workspace list entry"):
                        module["apply"](self.apply_snapshot(), "malformed-entry")

    def test_malformed_workspace_list_refused_before_marker_or_mutation(self):
        valid_result = {"type": "workspace_list", "workspaces": []}
        malformed = [
            ("wrong-id", {"id": "wrong", "result": valid_result}),
            (
                "wrong-type",
                {
                    "id": "cli:workspace:list",
                    "result": {"type": "other", "workspaces": []},
                },
            ),
            ("missing-result", {"id": "cli:workspace:list"}),
            ("result-not-object", {"id": "cli:workspace:list", "result": []}),
            (
                "workspaces-not-list",
                {
                    "id": "cli:workspace:list",
                    "result": {"type": "workspace_list", "workspaces": {}},
                },
            ),
            ("legacy-envelope", {"workspaces": []}),
            (
                "extra-field",
                {
                    "id": "cli:workspace:list",
                    "result": valid_result,
                    "extra": True,
                },
            ),
        ]
        for target, response in malformed:
            with self.subTest(target=target), tempfile.TemporaryDirectory() as tmp:
                calls = []

                def malformed_herdr(session, *args):
                    calls.append((session, *args))
                    if args[:2] == ("workspace", "list"):
                        return response
                    raise AssertionError(
                        "malformed workspace response allowed mutation"
                    )

                with (
                    patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)),
                    patch.dict(
                        module["apply"].__globals__,
                        {"run": lambda argv: "running", "herdr": malformed_herdr},
                    ),
                ):
                    with self.assertRaisesRegex(ValueError, "unrecognized response"):
                        module["apply"](self.apply_snapshot(), target)
                self.assertEqual(calls, [(target, "workspace", "list")])
                self.assertFalse(
                    self.marker_path(tmp, target, self.apply_snapshot()).exists()
                )

    def test_mutation_envelopes_require_exact_ids_types_objects_and_ids(self):
        fixtures = [
            (
                {
                    "id": "cli:workspace:create",
                    "result": {
                        "type": "workspace_created",
                        "workspace": {"workspace_id": "ws-1"},
                        "tab": {"tab_id": "tab-1"},
                        "root_pane": {"pane_id": "pane-1"},
                    },
                },
                "cli:workspace:create",
                "workspace_created",
                {"workspace", "tab", "root_pane"},
            ),
            (
                {
                    "id": "cli:tab:create",
                    "result": {
                        "type": "tab_created",
                        "tab": {"tab_id": "tab-1"},
                        "root_pane": {"pane_id": "pane-1"},
                    },
                },
                "cli:tab:create",
                "tab_created",
                {"tab", "root_pane"},
            ),
            (
                {
                    "id": "cli:tab:rename",
                    "result": {"type": "tab_info", "tab": {"tab_id": "tab-1"}},
                },
                "cli:tab:rename",
                "tab_info",
                {"tab"},
            ),
            (
                {
                    "id": "cli:tab:focus",
                    "result": {"type": "tab_info", "tab": {"tab_id": "tab-1"}},
                },
                "cli:tab:focus",
                "tab_info",
                {"tab"},
            ),
            (
                {
                    "id": "cli:pane:split",
                    "result": {"type": "pane_info", "pane": {"pane_id": "pane-1"}},
                },
                "cli:pane:split",
                "pane_info",
                {"pane"},
            ),
            (
                {
                    "id": "cli:pane:rename",
                    "result": {"type": "pane_info", "pane": {"pane_id": "pane-1"}},
                },
                "cli:pane:rename",
                "pane_info",
                {"pane"},
            ),
        ]
        for response, command_id, result_type, objects in fixtures:
            with self.subTest(command_id=command_id):
                result = module["_command_result"](
                    response, command_id, result_type, objects
                )
                self.assertIsInstance(result, dict)
                for malformed in (
                    {**response, "id": "wrong"},
                    {**response, "result": {**response["result"], "type": "wrong"}},
                    {"id": response["id"]},
                    {"id": response["id"], "result": []},
                    {**response, "extra": True},
                ):
                    with self.assertRaises(ValueError):
                        module["_command_result"](
                            malformed, command_id, result_type, objects
                        )
                for object_name in objects:
                    for invalid_id in (None, "", " ", 0, []):
                        malformed = copy.deepcopy(response)
                        id_name = (
                            "workspace_id"
                            if object_name == "workspace"
                            else ("tab_id" if object_name == "tab" else "pane_id")
                        )
                        malformed["result"][object_name][id_name] = invalid_id
                        result = module["_command_result"](
                            malformed, command_id, result_type, objects
                        )
                        with self.assertRaises(ValueError):
                            module["_object_id"](
                                result, object_name, id_name, malformed
                            )

        wrong_object = {
            "id": "cli:pane:rename",
            "result": {"type": "pane_info", "tab": {"tab_id": "tab-1"}},
        }
        with self.assertRaises(ValueError):
            module["_command_result"](
                wrong_object, "cli:pane:rename", "pane_info", {"pane"}
            )

    def test_pane_run_accepts_empty_stdout_without_json_parsing(self):
        calls = []

        def fake_run(argv):
            calls.append(argv)
            return ""

        with patch.dict(module["herdr"].__globals__, {"run": fake_run}):
            self.assertEqual(
                module["herdr"]("pilot", "pane", "run", "pane-1", "lazygit"), ""
            )
        self.assertEqual(
            calls,
            [["herdr", "--session", "pilot", "pane", "run", "pane-1", "lazygit"]],
        )

    def test_apply_missing_id_fails_and_keeps_partial_marker(self):
        def missing_id(target, *args):
            if args[:2] == ("workspace", "list"):
                return {
                    "id": "cli:workspace:list",
                    "result": {"type": "workspace_list", "workspaces": []},
                }
            return {
                "id": "cli:workspace:create",
                "result": {
                    "type": "workspace_created",
                    "workspace": {},
                    "tab": {"tab_id": "tab-1"},
                    "root_pane": {"pane_id": "pane-1"},
                },
            }

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)),
            patch.dict(
                module["apply"].__globals__,
                {"run": lambda argv: "running", "herdr": missing_id},
            ),
        ):
            with self.assertRaisesRegex(ValueError, "workspace.workspace_id"):
                module["apply"](self.apply_snapshot(), "missing-id")
            marker = self.marker_path(tmp, "missing-id", self.apply_snapshot())
            self.assertTrue(marker.exists())
            with self.assertRaisesRegex(ValueError, "matching source marker"):
                module["apply"](self.apply_snapshot(), "missing-id")

    def test_nonempty_target_refused_before_marker(self):
        calls = []

        def nonempty(target, *args):
            calls.append((target, *args))
            return {
                "id": "cli:workspace:list",
                "result": {
                    "type": "workspace_list",
                    "workspaces": [
                        {"workspace_id": "existing", "label": "tmux:pilot-source"}
                    ],
                },
            }

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)),
            patch.dict(
                module["apply"].__globals__,
                {"run": lambda argv: "running", "herdr": nonempty},
            ),
        ):
            with self.assertRaisesRegex(ValueError, "exists without a matching"):
                module["apply"](self.apply_snapshot(), "occupied")
            self.assertEqual(calls, [("occupied", "workspace", "list")])
            self.assertFalse(
                self.marker_path(tmp, "occupied", self.apply_snapshot()).exists()
            )

    def test_empty_source_snapshot_refused_before_marker_or_mutation(self):
        calls = []
        snapshot = {"schema": 1, "name": "empty", "tabs": []}

        def list_empty(target, *args):
            calls.append((target, *args))
            return {
                "id": "cli:workspace:list",
                "result": {"type": "workspace_list", "workspaces": []},
            }

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)),
            patch.dict(
                module["apply"].__globals__,
                {"run": lambda argv: "running", "herdr": list_empty},
            ),
        ):
            with self.assertRaisesRegex(ValueError, "empty tab list"):
                module["apply"](snapshot, "empty-source")
            self.assertEqual(calls, [("empty-source", "workspace", "list")])
            self.assertFalse((self.marker_path(tmp, "empty-source", snapshot)).exists())

    def test_unavailable_source_cwd_refused_before_marker_or_mutation(self):
        calls = []
        snapshot = self.apply_snapshot()
        snapshot["tabs"][0]["panes"][0]["cwd_exists"] = False
        snapshot["tabs"][0]["panes"][0]["cwd"] = "/missing/project"

        def list_empty(target, *args):
            calls.append((target, *args))
            return {
                "id": "cli:workspace:list",
                "result": {"type": "workspace_list", "workspaces": []},
            }

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)),
            patch.dict(
                module["apply"].__globals__,
                {"run": lambda argv: "running", "herdr": list_empty},
            ),
        ):
            with self.assertRaisesRegex(ValueError, "unavailable cwd"):
                module["apply"](snapshot, "missing-cwd")
            self.assertEqual(calls, [])
            self.assertFalse((self.marker_path(tmp, "missing-cwd", snapshot)).exists())

    def test_apply_rechecks_cwd_after_snapshot_and_before_marker(self):
        calls = []
        snapshot = self.apply_snapshot()
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as cwd:
            for tab in snapshot["tabs"]:
                for pane_data in tab["panes"]:
                    pane_data["cwd"] = cwd
                    pane_data["cwd_exists"] = True

            def list_empty(target, *args):
                calls.append((target, *args))
                return {
                    "id": "cli:workspace:list",
                    "result": {"type": "workspace_list", "workspaces": []},
                }

            original_prepare = module["apply"].__globals__["_precompute_import"]

            def delete_after_prepare(current, allow_continue):
                prepared = original_prepare(current, allow_continue)
                pathlib.Path(cwd).rmdir()
                return prepared

            with (
                patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)),
                patch.dict(
                    module["apply"].__globals__,
                    {
                        "run": lambda argv: "running",
                        "herdr": list_empty,
                        "_precompute_import": delete_after_prepare,
                    },
                ),
            ):
                with self.assertRaisesRegex(ValueError, "unavailable cwd"):
                    module["apply"](snapshot, "cwd-race")
            self.assertEqual(calls, [("cwd-race", "workspace", "list")])
            self.assertFalse(self.marker_path(tmp, "cwd-race", snapshot).exists())

    def test_pi_continue_option_reaches_apply_and_manifest_identity(self):
        calls = []
        snapshot = self.apply_snapshot("pi")
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)),
            patch.dict(
                module["apply"].__globals__,
                {"run": lambda argv: "running", "herdr": self.make_apply_mocks(calls)},
            ),
        ):
            module["apply"](snapshot, "pi-default", False)
            self.assertNotIn(
                (
                    "pi-default",
                    "pane",
                    "run",
                    "pane-1",
                    "tmux-herdr",
                    "continue-pi",
                ),
                calls,
            )
        calls.clear()
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)),
            patch.dict(
                module["apply"].__globals__,
                {"run": lambda argv: "running", "herdr": self.make_apply_mocks(calls)},
            ),
        ):
            module["apply"](snapshot, "pi-continue", True)
            self.assertIn(
                (
                    "pi-continue",
                    "pane",
                    "run",
                    "pane-1",
                    "tmux-herdr",
                    "continue-pi",
                ),
                calls,
            )
            identity = json.loads(
                (self.marker_path(tmp, "pi-continue", snapshot)).read_text()
            )["identity"]
            self.assertIn('"allow_pi_continue": true', identity)

    def test_real_concurrent_creators_share_exclusive_marker(self):
        snapshot = self.apply_snapshot()
        calls = []
        calls_lock = threading.Lock()
        listed = threading.Barrier(2)
        create_count = 0
        create_count_lock = threading.Lock()
        base = self.make_apply_mocks(calls)

        def concurrent_herdr(target, *args):
            nonlocal create_count
            if args[:2] == ("workspace", "list"):
                listed.wait(timeout=5)
                with calls_lock:
                    calls.append((target, *args))
                return {
                    "id": "cli:workspace:list",
                    "result": {"type": "workspace_list", "workspaces": []},
                }
            if args[:2] == ("workspace", "create"):
                with create_count_lock:
                    create_count += 1
            return base(target, *args)

        results = []

        def worker():
            try:
                module["apply"](snapshot, "concurrent-target")
            except Exception as exc:  # noqa: BLE001 - assert one race loser below
                results.append(exc)
            else:
                results.append(None)

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)),
            patch.dict(
                module["apply"].__globals__,
                {"run": lambda argv: "running", "herdr": concurrent_herdr},
            ),
        ):
            threads = [threading.Thread(target=worker) for _ in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=10)
            self.assertTrue(all(not thread.is_alive() for thread in threads))
            self.assertTrue(
                self.marker_path(tmp, "concurrent-target", snapshot).exists()
            )

        self.assertEqual(len(results), 2)
        self.assertEqual(sum(result is None for result in results), 1)
        self.assertEqual(sum(isinstance(result, ValueError) for result in results), 1)
        self.assertEqual(create_count, 1)

    def test_atomic_marker_collision_prevents_second_creator(self):
        calls = []
        snapshot = self.apply_snapshot()

        def colliding_herdr(target, *args):
            if args[:2] == ("workspace", "list"):
                return {
                    "id": "cli:workspace:list",
                    "result": {"type": "workspace_list", "workspaces": []},
                }
            with self.assertRaisesRegex(ValueError, "matching source marker"):
                module["apply"](snapshot, "race")
            return self.make_apply_mocks(calls)(target, *args)

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)),
            patch.dict(
                module["apply"].__globals__,
                {"run": lambda argv: "running", "herdr": colliding_herdr},
            ),
        ):
            module["apply"](snapshot, "race")
            self.assertTrue(self.marker_path(tmp, "race", snapshot).exists())

    def test_exclusive_marker_open_refuses_racing_creator(self):
        snapshot = self.apply_snapshot()
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(pathlib.Path, "home", return_value=pathlib.Path(tmp)),
            patch.dict(
                module["apply"].__globals__,
                {
                    "run": lambda argv: "running",
                    "herdr": lambda *args: {
                        "id": "cli:workspace:list",
                        "result": {"type": "workspace_list", "workspaces": []},
                    },
                },
            ),
            patch.object(
                module["apply"].__globals__["os"], "open", side_effect=FileExistsError
            ),
        ):
            with self.assertRaisesRegex(ValueError, "already reserved"):
                module["apply"](snapshot, "race-lock")
            self.assertFalse(
                (pathlib.Path(tmp) / ".local/state/tmux-herdr/race-lock.json").exists()
            )

    def test_cli_dry_run_is_fixture_only(self):
        snap = {
            "schema": 1,
            "name": "fixture",
            "tabs": [{"name": "shell", "panes": [pane("shell", "zsh")]}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "snapshot.json"
            path.write_text(json.dumps(snap))
            first = module["plan"](json.loads(path.read_text()))
            second = module["plan"](json.loads(path.read_text()))
        self.assertEqual(first, second)
        self.assertEqual(len(first["operations"]), 1)


if __name__ == "__main__":
    unittest.main()
