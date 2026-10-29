"""Local tests for pi-profile, without starting Pi or GitHub Actions."""

import contextlib
import io
import runpy
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


PROFILE = runpy.run_path(str(Path(__file__).resolve().parents[1] / "pi-profile"))


class PiProfileTests(unittest.TestCase):
    def test_discovers_relative_sources_and_deduplicates_paths(self):
        output = """User packages:
  npm:pi-token-speed
    /home/chris/.pi/agent/npm/node_modules/pi-token-speed
  ../../workspace/pi-ssh-remote-autocomplete-fix
    /home/chris/workspace/pi-ssh-remote-autocomplete-fix
  npm:pi-sandbox
    /home/chris/.pi/agent/npm/node_modules/pi-sandbox

../../workspace/pi-ssh-remote-autocomplete-fix
    /home/chris/workspace/pi-ssh-remote-autocomplete-fix
"""
        with patch.object(PROFILE["subprocess"], "run", return_value=SimpleNamespace(stdout=output)) as run:
            extensions = PROFILE["get_extensions"]()
        run.assert_called_once_with(["pi", "list"], check=True, text=True, capture_output=True)
        self.assertEqual(extensions, [
            ("npm:pi-token-speed", "/home/chris/.pi/agent/npm/node_modules/pi-token-speed"),
            ("../../workspace/pi-ssh-remote-autocomplete-fix", "/home/chris/workspace/pi-ssh-remote-autocomplete-fix"),
            ("npm:pi-sandbox", "/home/chris/.pi/agent/npm/node_modules/pi-sandbox"),
        ])

    def test_handles_absolute_local_source(self):
        output = """User packages:
  /home/chris/workspace/pi-ssh-remote
    /home/chris/workspace/pi-ssh-remote
"""
        with patch.object(PROFILE["subprocess"], "run", return_value=SimpleNamespace(stdout=output)):
            self.assertEqual(PROFILE["get_extensions"](), [
                ("/home/chris/workspace/pi-ssh-remote", "/home/chris/workspace/pi-ssh-remote")
            ])

    def test_excludes_multiple_names_in_local_profile(self):
        should_load = PROFILE["should_load"]
        self.assertFalse(should_load("local", "../../workspace/pi-ssh-remote-autocomplete-fix", "/home/chris/workspace/pi-ssh-remote-autocomplete-fix"))
        self.assertFalse(should_load("local", "npm:pi-ssh-remote", "/home/chris/.pi/agent/npm/node_modules/pi-ssh-remote"))
        self.assertTrue(should_load("local", "npm:pi-sandbox", "/tmp/pi-sandbox"))
        self.assertTrue(should_load("remote", "../../workspace/pi-ssh-remote-autocomplete-fix", "/home/chris/workspace/pi-ssh-remote-autocomplete-fix"))
        self.assertFalse(should_load("remote", "npm:pi-sandbox", "/tmp/pi-sandbox"))

    def test_main_passes_only_remote_extensions_once(self):
        extensions = [
            ("npm:pi-sandbox", "/tmp/pi-sandbox"),
            ("../../workspace/pi-ssh-remote-autocomplete-fix", "/tmp/pi-ssh-remote-autocomplete-fix"),
            ("npm:pi-token-speed", "/tmp/pi-token-speed"),
        ]
        with patch.dict(PROFILE["main"].__globals__, {"get_extensions": lambda: extensions}), \
             patch.object(sys, "argv", ["pi-profile", "remote", "--print"]), \
             patch.object(PROFILE["os"], "execvp") as execvp:
            PROFILE["main"]()
        execvp.assert_called_once_with("pi", [
            "pi", "--no-extensions", "-e", "/tmp/pi-ssh-remote-autocomplete-fix",
            "-e", "/tmp/pi-token-speed", "--print",
        ])


    def test_show_before_remote_profile(self):
        extensions = [
            ("npm:pi-sandbox", "/tmp/pi-sandbox"),
            ("file:pi-ssh-remote", "/tmp/pi-ssh-remote"),
        ]
        output = io.StringIO()
        with patch.dict(PROFILE["main"].__globals__, {"get_extensions": lambda: extensions}), \
             patch.object(sys, "argv", ["pi-profile", "--show", "remote"]), \
             patch.object(PROFILE["os"], "execvp") as execvp, \
             contextlib.redirect_stdout(output):
            PROFILE["main"]()
        execvp.assert_not_called()
        self.assertIn("SKIP", output.getvalue())
        self.assertIn("pi-ssh-remote", output.getvalue())

    def test_show_before_local_profile(self):
        extensions = [
            ("npm:pi-sandbox", "/tmp/pi-sandbox"),
            ("file:pi-ssh-remote", "/tmp/pi-ssh-remote"),
        ]
        output = io.StringIO()
        with patch.dict(PROFILE["main"].__globals__, {"get_extensions": lambda: extensions}), \
             patch.object(sys, "argv", ["pi-profile", "--show", "local"]), \
             patch.object(PROFILE["os"], "execvp") as execvp, \
             contextlib.redirect_stdout(output):
            PROFILE["main"]()
        execvp.assert_not_called()
        self.assertIn("SKIP", output.getvalue())
        self.assertIn("pi-ssh-remote", output.getvalue())

    def test_show_after_profile_is_forwarded(self):
        with patch.dict(PROFILE["main"].__globals__, {"get_extensions": lambda: []}), \
             patch.object(sys, "argv", ["pi-profile", "remote", "--show"]), \
             patch.object(PROFILE["os"], "execvp") as execvp:
            PROFILE["main"]()
        execvp.assert_called_once_with("pi", ["pi", "--no-extensions", "--show"])

    def test_missing_profile_after_show_is_usage_error(self):
        with patch.object(sys, "argv", ["pi-profile", "--show"]), \
             contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as error:
                PROFILE["main"]()
        self.assertEqual(error.exception.code, 2)
        self.assertIn("pi-profile [--show] {local|remote}", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
