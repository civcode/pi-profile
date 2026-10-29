"""Local tests for pi-profile, without starting Pi or GitHub Actions."""

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


if __name__ == "__main__":
    unittest.main()
