import subprocess
import sys
from pathlib import Path


def test_get_map_complete_data_sandbox():
    project_root = Path(__file__).resolve().parents[2]
    script = project_root / "tools" / "gas" / "test_get_map_complete_data.js"
    completed = subprocess.run(
        ["node", str(script)],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        sys.stderr.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        raise AssertionError("Node GAS sandbox test failed")
