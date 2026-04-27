from pathlib import Path
import subprocess


def run_python_file(target: Path, timeout_sec: int = 10) -> tuple[int, str, str]:
	process = subprocess.run(
		["python", str(target)],
		capture_output=True,
		text=True,
		timeout=timeout_sec,
	)
	return process.returncode, process.stdout, process.stderr

