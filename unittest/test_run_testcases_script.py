#!/usr/bin/env python3

import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

RUN_TESTCASES = Path(__file__).with_name("run_testcases.sh")


class RunTestcasesScriptTestCase(unittest.TestCase):
    def _run_script(self, extra_env=None):
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_dir = Path(tmp_dir)
            capture_path = temp_dir / "captured.txt"
            fake_python = temp_dir / "python3"
            fake_python.write_text(textwrap.dedent(f"""\
                    #!{sys.executable}
                    import os
                    import sys

                    with open({str(capture_path)!r}, "w", encoding="utf-8") as handle:
                        handle.write(f"PMM_TEST_LEVEL={{os.getenv('PMM_TEST_LEVEL')}}\\n")
                        handle.write(f"ARGS={{' '.join(sys.argv[1:])}}\\n")
                        handle.write(f"CWD={{os.getcwd()}}\\n")
                    """))
            fake_python.chmod(0o755)

            env = os.environ.copy()
            env["PATH"] = f"{temp_dir}{os.pathsep}{env.get('PATH', os.defpath)}"
            env.pop("PMM_TEST_LEVEL", None)
            if extra_env:
                env.update(extra_env)

            result = subprocess.run(
                ["bash", str(RUN_TESTCASES)],
                cwd=RUN_TESTCASES.parent.parent,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )

            return result.stdout, capture_path.read_text(encoding="utf-8")

    def test_run_testcases_defaults_pmm_test_level_to_zero(self):
        stdout, captured = self._run_script()

        self.assertIn("Running unittest suite with PMM_TEST_LEVEL=0", stdout)
        self.assertIn("PMM_TEST_LEVEL=0\n", captured)
        self.assertIn("ARGS=-m unittest -vv --buffer\n", captured)
        self.assertIn(f"CWD={RUN_TESTCASES.parent}\n", captured)

    def test_run_testcases_preserves_explicit_pmm_test_level(self):
        stdout, captured = self._run_script({"PMM_TEST_LEVEL": "2"})

        self.assertIn("Running unittest suite with PMM_TEST_LEVEL=2", stdout)
        self.assertIn("PMM_TEST_LEVEL=2\n", captured)


if __name__ == "__main__":
    unittest.main()
