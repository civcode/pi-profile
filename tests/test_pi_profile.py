"""Local tests for pi-profile, without starting Pi or GitHub Actions."""

import contextlib
import io
import json
import runpy
import subprocess
import shutil
import tempfile
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


PROFILE = runpy.run_path(str(Path(__file__).resolve().parents[1] / "pi-profile"))


class PiProfileTests(unittest.TestCase):
    def setUp(self):
        # Keep launch tests deterministic; discovery has separate real-Node tests.
        builtin_names = [
            "builtin:mcp", "builtin:llama.cpp",
            "builtin:codemode", "builtin:tool-search",
        ]
        patched = patch.dict(
            PROFILE["main"].__globals__,
            {"get_builtin_extensions": lambda: builtin_names},
        )
        patched.start()
        self.addCleanup(patched.stop)

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
            "pi", "--no-extensions",
            "-e", "builtin:mcp",
            "-e", "builtin:llama.cpp",
            "-e", "builtin:codemode",
            "-e", "builtin:tool-search",
            "-e", "/tmp/pi-ssh-remote-autocomplete-fix",
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
        execvp.assert_called_once_with("pi", [
            "pi", "--no-extensions",
            "-e", "builtin:mcp",
            "-e", "builtin:llama.cpp",
            "-e", "builtin:codemode",
            "-e", "builtin:tool-search",
            "--show",
        ])

    def test_builtins_loaded_in_local_profile(self):
        # Local profile excludes ssh extensions, but preserves built-ins.
        extensions = [("file:pi-ssh-remote", "/tmp/pi-ssh-remote")]
        with patch.dict(PROFILE["main"].__globals__, {"get_extensions": lambda: extensions}), \
             patch.object(sys, "argv", ["pi-profile", "local"]), \
             patch.object(PROFILE["os"], "execvp") as execvp:
            PROFILE["main"]()

        argv = execvp.call_args.args[1]
        self.assertEqual(argv[:4], ["pi", "--no-extensions", "-e", "builtin:mcp"])
        self.assertIn("builtin:llama.cpp", argv)
        self.assertEqual(argv.count("builtin:llama.cpp"), 1)
        self.assertNotIn("/tmp/pi-ssh-remote", argv)

    def test_builtin_shown_in_preview(self):
        output = io.StringIO()
        with patch.dict(PROFILE["main"].__globals__, {"get_extensions": lambda: []}), \
             patch.object(sys, "argv", ["pi-profile", "--show", "local"]), \
             patch.object(PROFILE["os"], "execvp") as execvp, \
             contextlib.redirect_stdout(output):
            PROFILE["main"]()

        execvp.assert_not_called()
        self.assertIn("builtin:llama.cpp", output.getvalue())
        self.assertIn("builtin:mcp", output.getvalue())
        self.assertNotIn("SKIP", output.getvalue())


    @unittest.skipUnless(shutil.which("node"), "requires Node.js")
    def test_discovers_current_names_from_resolved_pi_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            app = root / "app"
            executable = app / "bin" / "pi.js"
            registry = app / "extensions" / "index.js"
            executable.parent.mkdir(parents=True)
            registry.parent.mkdir(parents=True)
            (app / "package.json").write_text(json.dumps({"type": "module"}))
            executable.write_text("#!/usr/bin/env node\\n")
            registry.write_text(
                'export const builtInExtensions = ['
                '{name: "llama.cpp"}, {name: "a-new-builtin"}, '
                '{name: "llama.cpp"}];\\n'
            )
            shim = root / "pi"
            shim.symlink_to(executable)

            with patch.object(PROFILE["shutil"], "which", return_value=str(shim)):
                names = PROFILE["get_builtin_extensions"]()
            self.assertEqual(names, ["builtin:llama.cpp", "builtin:a-new-builtin"])

    def test_registry_failure_is_not_silently_ignored(self):
        with patch.object(PROFILE["shutil"], "which", return_value="/fake/bin/pi"), \\
             patch.object(
                 PROFILE["subprocess"],
                 "run",
                 side_effect=subprocess.CalledProcessError(
                     1, ["node"], stderr="registry not found"
                 ),
             ):
            with self.assertRaisesRegex(RuntimeError, "registry not found"):
                PROFILE["get_builtin_extensions"]()

    def test_invalid_registry_output_is_rejected(self):
        with patch.object(PROFILE["shutil"], "which", return_value="/fake/bin/pi"), \\
             patch.object(
                 PROFILE["subprocess"],
                 "run",
                 return_value=SimpleNamespace(stdout="unexpected line\\n"),
             ):
            with self.assertRaisesRegex(RuntimeError, "Unexpected output"):
                PROFILE["get_builtin_extensions"]()

    def test_launch_fails_cleanly_if_registry_unavailable(self):
        def fail():
            raise RuntimeError("registry not found")

        with patch.dict(
            PROFILE["main"].__globals__,
            {"get_builtin_extensions": fail, "get_extensions": lambda: []},
        ), patch.object(sys, "argv", ["pi-profile", "local"]), \\
             patch.object(PROFILE["os"], "execvp") as execvp, \\
             contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as error:
                PROFILE["main"]()
        self.assertEqual(error.exception.code, 1)
        self.assertIn("registry not found", stderr.getvalue())
        execvp.assert_not_called()

    def test_new_builtin_is_launched_without_changing_profile_code(self):
        with patch.dict(
            PROFILE["main"].__globals__,
            {
                "get_builtin_extensions": lambda: ["builtin:llama.cpp", "builtin:new-name"],
                "get_extensions": lambda: [],
            },
        ), patch.object(sys, "argv", ["pi-profile", "remote"]), \\
             patch.object(PROFILE["os"], "execvp") as execvp:
            PROFILE["main"]()
        execvp.assert_called_once_with("pi", [
            "pi", "--no-extensions", "-e", "builtin:llama.cpp", "-e", "builtin:new-name"
        ])

    def test_missing_profile_after_show_is_usage_error(self):
        with patch.object(sys, "argv", ["pi-profile", "--show"]), \
             contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as error:
                PROFILE["main"]()
        self.assertEqual(error.exception.code, 2)
        self.assertIn("pi-profile [--show] {local|remote}", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
