import json
import os
import pathlib
import runpy
import subprocess
import sys
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).parents[1] / "bin/executable_tmux-herdr-diagnose"
module = runpy.run_path(str(SCRIPT), run_name="tmux_herdr_diagnose_test")


class TmuxHerdrDiagnoseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base = pathlib.Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_storage_base_type_resolution(self):
        # 1. Absolute XDG_RUNTIME_DIR
        env = {
            "XDG_RUNTIME_DIR": str(self.base / "xdg"),
            "HOME": str(self.base / "home"),
        }
        base_type, target = module["resolve_storage_target"](env)
        self.assertEqual(base_type, "xdg_runtime_dir")
        self.assertEqual(target, self.base / "xdg" / "pi-herdr-sessions")

        # 2. Non-absolute XDG_RUNTIME_DIR falls back to HOME
        env = {
            "XDG_RUNTIME_DIR": "relative/xdg",
            "HOME": str(self.base / "home"),
        }
        base_type, target = module["resolve_storage_target"](env)
        self.assertEqual(base_type, "home_fallback")
        self.assertEqual(target, self.base / "home" / ".cache" / "pi-herdr-sessions")

        # 3. Empty string XDG_RUNTIME_DIR falls back to HOME
        env = {
            "XDG_RUNTIME_DIR": "",
            "HOME": str(self.base / "home"),
        }
        base_type, target = module["resolve_storage_target"](env)
        self.assertEqual(base_type, "home_fallback")
        self.assertEqual(target, self.base / "home" / ".cache" / "pi-herdr-sessions")

        # 4. Unset XDG_RUNTIME_DIR uses HOME
        env = {"HOME": str(self.base / "home")}
        base_type, target = module["resolve_storage_target"](env)
        self.assertEqual(base_type, "home_fallback")
        self.assertEqual(target, self.base / "home" / ".cache" / "pi-herdr-sessions")

        # 5. Non-absolute HOME with non-absolute XDG -> unavailable
        env = {"XDG_RUNTIME_DIR": "rel/xdg", "HOME": "rel/home"}
        base_type, target = module["resolve_storage_target"](env)
        self.assertEqual(base_type, "unavailable")
        self.assertIsNone(target)

    def test_darwin_storage_canonicalization_with_symlink_ancestor(self):
        real_run = self.base / "real_run"
        real_run.mkdir(mode=0o700)
        symlink_run = self.base / "symlink_run"
        symlink_run.symlink_to(real_run)
        home = self.base / "home"
        home.mkdir(mode=0o700)

        # 1. resolve_storage_target on Darwin resolves symlinked base
        env = {"XDG_RUNTIME_DIR": str(symlink_run), "HOME": str(home)}
        base_type, target = module["resolve_storage_target"](env, platform="darwin")
        canonical_expected = real_run.resolve() / "pi-herdr-sessions"
        self.assertEqual(base_type, "xdg_runtime_dir")
        self.assertEqual(target, canonical_expected)

        # 2. diagnose on Darwin uses the canonical path and does not report resolved symlink as unsafe
        results = module["diagnose"](
            environ=env, platform="darwin", skip_fsync_probe=True
        )
        self.assertEqual(results["storage_base_type"], "xdg_runtime_dir")
        self.assertEqual(results["storage_path_symlinks"], "none")
        self.assertEqual(results["storage_leaf_status"], "missing_creatable")
        self.assertEqual(results["storage_path_status"], "missing_creatable")

        # 3. Create leaf directory and verify clean ok status
        canonical_expected.mkdir(mode=0o700)
        results = module["diagnose"](
            environ=env, platform="darwin", skip_fsync_probe=True
        )
        self.assertEqual(results["storage_path_symlinks"], "none")
        self.assertEqual(results["storage_leaf_status"], "ok")
        self.assertEqual(results["storage_path_status"], "ok")

    def test_darwin_storage_failed_realpath_fallback(self):
        home = self.base / "home"
        home.mkdir(mode=0o700)
        broken_symlink = self.base / "broken_symlink"
        broken_symlink.symlink_to(self.base / "nonexistent")

        # 1. Non-existent path on Darwin falls back to home_fallback
        env = {
            "XDG_RUNTIME_DIR": str(self.base / "absent"),
            "HOME": str(home),
        }
        base_type, target = module["resolve_storage_target"](env, platform="darwin")
        self.assertEqual(base_type, "home_fallback")
        self.assertEqual(target, home.resolve() / ".cache/pi-herdr-sessions")

        # 2. Broken symlink on Darwin falls back to home_fallback
        env = {
            "XDG_RUNTIME_DIR": str(broken_symlink),
            "HOME": str(home),
        }
        base_type, target = module["resolve_storage_target"](env, platform="darwin")
        self.assertEqual(base_type, "home_fallback")
        self.assertEqual(target, home.resolve() / ".cache/pi-herdr-sessions")

        # 3. Both unresolvable XDG and invalid HOME -> unavailable
        env = {
            "XDG_RUNTIME_DIR": str(broken_symlink),
            "HOME": "relative/home",
        }
        base_type, target = module["resolve_storage_target"](env, platform="darwin")
        self.assertEqual(base_type, "unavailable")
        self.assertIsNone(target)

    def test_darwin_storage_untrusted_canonical_target_rejection(self):
        untrusted_run = self.base / "untrusted_run"
        untrusted_run.mkdir(mode=0o775)
        untrusted_run.chmod(0o775)
        symlink_run = self.base / "symlink_run"
        symlink_run.symlink_to(untrusted_run)
        home = self.base / "home"
        home.mkdir(mode=0o700)

        env = {"XDG_RUNTIME_DIR": str(symlink_run), "HOME": str(home)}
        base_type, target = module["resolve_storage_target"](env, platform="darwin")
        self.assertEqual(base_type, "xdg_runtime_dir")
        self.assertEqual(target, untrusted_run.resolve() / "pi-herdr-sessions")

        # Leaf creatable inside untrusted ancestor
        results = module["diagnose"](
            environ=env, platform="darwin", skip_fsync_probe=True
        )
        self.assertEqual(results["storage_path_permissions"], "untrusted_detected")
        self.assertEqual(results["storage_path_status"], "untrusted_mode")

    def test_linux_storage_unchanged_behavior(self):
        real_run = self.base / "real_run"
        real_run.mkdir(mode=0o700)
        symlink_run = self.base / "symlink_run"
        symlink_run.symlink_to(real_run)
        home = self.base / "home"
        home.mkdir(mode=0o700)

        # Linux retains uncanonicalized path
        env = {"XDG_RUNTIME_DIR": str(symlink_run), "HOME": str(home)}
        base_type, target = module["resolve_storage_target"](env, platform="linux")
        self.assertEqual(base_type, "xdg_runtime_dir")
        self.assertEqual(target, symlink_run / "pi-herdr-sessions")

        # Linux diagnose detects the symlink component
        results = module["diagnose"](
            environ=env, platform="linux", skip_fsync_probe=True
        )
        self.assertEqual(results["storage_path_symlinks"], "symlink_detected")
        self.assertEqual(results["storage_path_status"], "symlink_detected")

    def test_helper_metadata_validation(self):
        parent = self.base / ".local/libexec"
        helper = parent / "tmux-herdr-darwin-helper"

        # Missing initially
        meta = module["check_helper_metadata"](parent, helper, os.getuid())
        self.assertEqual(meta["helper_overall_status"], "missing")
        self.assertFalse(meta["helper_file_exists"])
        self.assertFalse(meta["helper_parent_exists"])

        # Create parent with 0755 (loose)
        parent.mkdir(parents=True, mode=0o755)
        helper.touch(mode=0o700)
        helper.chmod(0o700)
        meta = module["check_helper_metadata"](parent, helper, os.getuid())
        self.assertEqual(meta["helper_parent_mode"], "untrusted_mode")
        self.assertEqual(meta["helper_overall_status"], "build_failure")

        # Fix parent to 0700, but helper file has 0755
        parent.chmod(0o700)
        helper.chmod(0o755)
        meta = module["check_helper_metadata"](parent, helper, os.getuid())
        self.assertEqual(meta["helper_parent_mode"], "exact_0700")
        self.assertEqual(meta["helper_file_mode"], "untrusted_mode")
        self.assertEqual(meta["helper_overall_status"], "build_failure")

        # Helper with hardlink count > 1
        helper.chmod(0o700)
        hardlink = parent / "helper-hardlink"
        os.link(helper, hardlink)
        meta = module["check_helper_metadata"](parent, helper, os.getuid())
        self.assertEqual(meta["helper_file_link_count"], "multiple")
        self.assertEqual(meta["helper_overall_status"], "build_failure")
        hardlink.unlink()

        # Helper file is a symlink
        helper.unlink()
        target = self.base / "target-bin"
        target.touch(mode=0o700)
        helper.symlink_to(target)
        meta = module["check_helper_metadata"](parent, helper, os.getuid())
        self.assertEqual(meta["helper_file_type"], "symlink")
        self.assertEqual(meta["helper_overall_status"], "build_failure")
        helper.unlink()
        target.unlink()

        # Valid helper configuration
        helper.touch(mode=0o700)
        helper.chmod(0o700)
        meta = module["check_helper_metadata"](parent, helper, os.getuid())
        self.assertEqual(meta["helper_parent_type"], "directory")
        self.assertEqual(meta["helper_parent_owner"], "trusted_self")
        self.assertEqual(meta["helper_parent_mode"], "exact_0700")
        self.assertEqual(meta["helper_file_type"], "regular")
        self.assertEqual(meta["helper_file_owner"], "trusted_self")
        self.assertEqual(meta["helper_file_mode"], "exact_0700")
        self.assertEqual(meta["helper_file_link_count"], "single")
        self.assertTrue(meta["helper_file_executable"])
        self.assertEqual(meta["helper_overall_status"], "ok")

    def test_helper_selftest_handling(self):
        helper_path = self.base / "helper"

        # 1. Skipped when missing or invalid
        self.assertEqual(
            module["check_helper_selftest"](helper_path, "missing"),
            "skipped_helper_missing",
        )
        self.assertEqual(
            module["check_helper_selftest"](helper_path, "build_failure"),
            "skipped_helper_invalid",
        )

        # 2. Mock runner returning ok
        res = module["check_helper_selftest"](
            helper_path, "ok", helper_runner=lambda act: json.dumps({"ok": True})
        )
        self.assertEqual(res, "ok")

        # 3. Mock runner returning unsupported
        res = module["check_helper_selftest"](
            helper_path,
            "ok",
            helper_runner=lambda act: json.dumps(
                {"ok": False, "reason": "unsupported"}
            ),
        )
        self.assertEqual(res, "unsupported")

        # 4. Mock runner returning process failure
        res = module["check_helper_selftest"](
            helper_path,
            "ok",
            helper_runner=lambda act: json.dumps({"ok": False, "reason": "denied"}),
        )
        self.assertEqual(res, "process_failure")

        # 5. Mock runner timing out
        def raise_timeout(act):
            raise TimeoutError()

        res = module["check_helper_selftest"](
            helper_path, "ok", helper_runner=raise_timeout
        )
        self.assertEqual(res, "timeout")

        # 6. Real executable helper script
        helper_path.write_text("#!/bin/sh\nprintf '{\"ok\":true}\\n'\n")
        helper_path.chmod(0o700)
        res = module["check_helper_selftest"](helper_path, "ok")
        self.assertEqual(res, "ok")

        # 7. Helper script returning failure exit code
        helper_path.write_text("#!/bin/sh\nexit 1\n")
        res = module["check_helper_selftest"](helper_path, "ok")
        self.assertEqual(res, "process_failure")

        # 8. Helper script outputting non-json
        helper_path.write_text("#!/bin/sh\necho not-json\n")
        res = module["check_helper_selftest"](helper_path, "ok")
        self.assertEqual(res, "malformed")

    def test_storage_path_components_darwin_rules(self):
        # Build a valid directory chain
        home = self.base / "userhome"
        home.mkdir(mode=0o700)
        cache = home / ".cache"
        cache.mkdir(mode=0o700)
        sessions = cache / "pi-herdr-sessions"
        sessions.mkdir(mode=0o700)

        # 1. Valid path
        components, summary, leaf_fd = module["check_storage_path_components"](
            sessions, os.getuid()
        )
        self.assertIsNotNone(leaf_fd)
        if leaf_fd is not None:
            os.close(leaf_fd)
        self.assertEqual(summary["storage_path_status"], "ok")
        self.assertEqual(summary["storage_leaf_status"], "ok")
        self.assertEqual(summary["storage_path_symlinks"], "none")
        self.assertEqual(summary["storage_path_owners"], "trusted")
        self.assertEqual(summary["storage_path_permissions"], "trusted")

        # 2. Leaf directory with wrong mode (0755)
        sessions.chmod(0o755)
        _, summary, leaf_fd = module["check_storage_path_components"](
            sessions, os.getuid()
        )
        self.assertIsNone(leaf_fd)
        self.assertEqual(summary["storage_leaf_mode"], "untrusted_mode")
        self.assertEqual(summary["storage_leaf_status"], "untrusted_mode")
        self.assertEqual(summary["storage_path_status"], "untrusted_mode")
        sessions.chmod(0o700)

        # 3. Intermediate component with group-writable permissions (0775)
        cache.chmod(0o775)
        _, summary, leaf_fd = module["check_storage_path_components"](
            sessions, os.getuid()
        )
        self.assertIsNone(leaf_fd)
        self.assertEqual(summary["storage_path_permissions"], "untrusted_detected")
        self.assertEqual(summary["storage_path_status"], "untrusted_mode")
        cache.chmod(0o700)

        # 4. Intermediate component as symlink
        sessions.rmdir()
        cache.rmdir()
        real_cache = home / "real_cache"
        real_cache.mkdir(mode=0o700)
        cache.symlink_to(real_cache)
        real_sessions = real_cache / "pi-herdr-sessions"
        real_sessions.mkdir(mode=0o700)

        _, summary, leaf_fd = module["check_storage_path_components"](
            sessions, os.getuid()
        )
        self.assertIsNone(leaf_fd)
        self.assertEqual(summary["storage_path_symlinks"], "symlink_detected")
        self.assertEqual(summary["storage_path_status"], "symlink_detected")

        # Clean up symlink
        cache.unlink()
        cache.mkdir(mode=0o700)

        # 5. Missing leaf directory (creatable)
        _, summary, leaf_fd = module["check_storage_path_components"](
            sessions, os.getuid()
        )
        self.assertIsNone(leaf_fd)
        self.assertFalse(summary["storage_leaf_exists"])
        self.assertEqual(summary["storage_leaf_status"], "missing_creatable")
        self.assertEqual(summary["storage_path_status"], "missing_creatable")

    def test_existing_beacon_leaf_validation(self):
        sessions = self.base / "pi-herdr-sessions"
        sessions.mkdir(mode=0o700)
        open_flags = (
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
        )
        dir_fd = os.open(sessions, open_flags)
        try:
            # 1. No beacon files
            res = module["check_existing_beacon_leaf"](dir_fd, os.getuid())
            self.assertFalse(res["beacon_leaf_present"])
            self.assertEqual(res["beacon_leaf_status"], "none_present")

            # 2. Valid beacon file (0600)
            beacon = sessions / "12345.json"
            beacon.write_text('{"schema":1}')
            beacon.chmod(0o600)
            res = module["check_existing_beacon_leaf"](dir_fd, os.getuid())
            self.assertTrue(res["beacon_leaf_present"])
            self.assertEqual(res["beacon_leaf_type"], "regular")
            self.assertEqual(res["beacon_leaf_owner"], "trusted_self")
            self.assertEqual(res["beacon_leaf_mode"], "exact_0600")
            self.assertEqual(res["beacon_leaf_link_count"], "single")
            self.assertEqual(res["beacon_leaf_status"], "ok")

            # 3. Beacon file with loose mode (0644)
            beacon.chmod(0o644)
            res = module["check_existing_beacon_leaf"](dir_fd, os.getuid())
            self.assertEqual(res["beacon_leaf_mode"], "untrusted_mode")
            self.assertEqual(res["beacon_leaf_status"], "untrusted_beacon_file")
            beacon.chmod(0o600)

            # 4. Beacon file is a symlink
            beacon.unlink()
            target_beacon = self.base / "other.json"
            target_beacon.write_text('{"schema":1}')
            beacon.symlink_to(target_beacon)
            res = module["check_existing_beacon_leaf"](dir_fd, os.getuid())
            self.assertEqual(res["beacon_leaf_type"], "symlink_detected")
            self.assertEqual(res["beacon_leaf_status"], "untrusted_beacon_file")
            beacon.unlink()
            target_beacon.unlink()

            # 5. Beacon file with multiple hardlinks
            beacon.write_text('{"schema":1}')
            beacon.chmod(0o600)
            hardlink = sessions / "67890.json"
            os.link(beacon, hardlink)
            res = module["check_existing_beacon_leaf"](dir_fd, os.getuid())
            self.assertEqual(res["beacon_leaf_link_count"], "multiple_links")
            self.assertEqual(res["beacon_leaf_status"], "untrusted_beacon_file")
            hardlink.unlink()
            beacon.unlink()
        finally:
            os.close(dir_fd)

    def test_fsync_probe_execution_and_cleanup(self):
        sessions = self.base / "pi-herdr-sessions"
        sessions.mkdir(mode=0o700)
        open_flags = (
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
        )
        dir_fd = os.open(sessions, open_flags)
        try:
            # 1. Normal safe probe run
            res = module["check_fsync_probe"](
                dir_fd, skip_probe=False, platform="linux"
            )
            self.assertEqual(res["fsync_directory"], "ok")
            self.assertEqual(res["fsync_file"], "ok")
            self.assertEqual(res["fsync_temp_cleanup"], "ok")
            self.assertEqual(res["fsync_probe_status"], "ok")

            # Verify that the probe temporary entry was cleaned up and directory is empty!
            remaining = os.listdir(sessions)
            self.assertEqual(remaining, [])

            # 2. Skip probe with flag
            res = module["check_fsync_probe"](dir_fd, skip_probe=True, platform="linux")
            self.assertEqual(res["fsync_probe_status"], "skipped_by_flag")

            # 3. None directory descriptor
            res = module["check_fsync_probe"](None, skip_probe=False, platform="linux")
            self.assertEqual(res["fsync_probe_status"], "skipped_storage_not_ready")
        finally:
            os.close(dir_fd)

    def test_privacy_sentinel_invariance(self):
        """CRITICAL: Ensure that NO sensitive path, PID, pane ID, username, or session leaks in output."""
        sentinel_home = str(self.base / "sensitive_home_dir_xyz_12345")
        sentinel_user = "sensitive_user_alpha_9999"
        sentinel_pane = "%sensitive_pane_id_8888"
        sentinel_session = "sensitive_session_uuid_7777"
        sentinel_env = "sensitive_env_secret_6666"

        home_path = pathlib.Path(sentinel_home)
        home_path.mkdir(mode=0o700)
        cache_path = home_path / ".cache"
        cache_path.mkdir(mode=0o700)
        sessions_path = cache_path / "pi-herdr-sessions"
        sessions_path.mkdir(mode=0o700)

        helper_parent = home_path / ".local/libexec"
        helper_parent.mkdir(parents=True, mode=0o700)
        helper_bin = helper_parent / "tmux-herdr-darwin-helper"
        helper_bin.write_text("#!/bin/sh\nprintf '{\"ok\":true}\\n'\n")
        helper_bin.chmod(0o700)

        beacon_file = sessions_path / "12345.json"
        beacon_file.write_text(f'{{"session":"{sentinel_session}"}}')
        beacon_file.chmod(0o600)

        environ = {
            "HOME": sentinel_home,
            "USER": sentinel_user,
            "TMUX_PANE": sentinel_pane,
            "PI_SESSION_ID": sentinel_session,
            "SECRET_VAR": sentinel_env,
            "PATH": "/usr/bin:/bin",
        }

        # 1. Programmatic diagnose() output
        findings = module["diagnose"](
            environ=environ,
            platform="darwin",
            current_uid=os.getuid(),
            skip_fsync_probe=False,
        )
        text_output = module["format_diagnostic_text"](findings)
        json_output = json.dumps(findings)

        # 2. Executable subprocess output
        cli_result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            env=environ,
            text=True,
            capture_output=True,
            check=True,
        )
        cli_stdout = cli_result.stdout
        cli_stderr = cli_result.stderr

        cli_json_result = subprocess.run(
            [sys.executable, str(SCRIPT), "--json"],
            env=environ,
            text=True,
            capture_output=True,
            check=True,
        )
        cli_json_stdout = cli_json_result.stdout

        all_outputs = [
            text_output,
            json_output,
            cli_stdout,
            cli_stderr,
            cli_json_stdout,
        ]

        # Verify that NONE of the sentinels appear in any output
        for out in all_outputs:
            self.assertNotIn(sentinel_home, out)
            self.assertNotIn("sensitive_home_dir", out)
            self.assertNotIn(sentinel_user, out)
            self.assertNotIn(sentinel_pane, out)
            self.assertNotIn("%sensitive", out)
            self.assertNotIn(sentinel_session, out)
            self.assertNotIn(sentinel_env, out)
            # Ensure no absolute paths appear in keys or values
            for line in out.splitlines():
                if ":" in line:
                    val = line.split(":", 1)[1].strip()
                    self.assertFalse(val.startswith("/"), f"Path leak detected: {line}")

    def test_cli_flags_and_exit_code(self):
        # 1. --help exits 0
        res = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("usage", res.stdout.lower())

        # 2. Default run exits 0
        res = subprocess.run(
            [sys.executable, str(SCRIPT)],
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("platform:", res.stdout)
        self.assertIn("overall_status:", res.stdout)

        # 3. --no-fsync-probe flag
        res = subprocess.run(
            [sys.executable, str(SCRIPT), "--no-fsync-probe"],
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("fsync_probe_status: skipped_by_flag", res.stdout)

        # 4. --json flag
        res = subprocess.run(
            [sys.executable, str(SCRIPT), "--json"],
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(res.returncode, 0)
        parsed = json.loads(res.stdout)
        self.assertIsInstance(parsed, dict)
        self.assertIn("platform", parsed)
        self.assertIn("overall_status", parsed)


if __name__ == "__main__":
    unittest.main()
