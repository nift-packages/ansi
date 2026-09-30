#!/usr/bin/env python3
"""Deterministic black-box tests for the ansi Nift package."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


NIFT = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/nick/Repositories/nift/nift/nift").resolve()
PACKAGE = Path(__file__).resolve().parent.parent
TESTS = PACKAGE / "tests"

manifest = json.loads((PACKAGE / "manifest.json").read_text(encoding="utf-8"))
require_manifest = {
    "name": "ansi",
    "version": "0.1.0",
    "entry": "src/ansi.f",
    "description": "Deterministic ANSI SGR formatting for Nift",
}
if manifest != require_manifest:
    raise SystemExit(f"FAIL unexpected package manifest: {manifest!r}")

package_source = (PACKAGE / "src" / "ansi.f").read_text(encoding="utf-8")
exports = re.findall(r"^export\(([^)]+)\)$", package_source, re.MULTILINE)
public_methods = re.findall(r"^    fn\(([A-Za-z_][A-Za-z0-9_]*)\(", package_source, re.MULTILINE)
expected_methods = [
    "sgr", "wrap", "reset", "bold", "dim", "italic", "underline",
    "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white",
]
if exports != ["ansi"] or public_methods != expected_methods:
    raise SystemExit(f"FAIL unexpected public surface: exports={exports!r} methods={public_methods!r}")


def run(args, cwd):
    return subprocess.run(
        [str(NIFT), *args],
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )


def require(condition, message, result=None):
    if condition:
        return
    if result is not None:
        message += f"\nstdout: {result.stdout!r}\nstderr: {result.stderr!r}\nreturn code: {result.returncode}"
    raise SystemExit("FAIL " + message)


direct = run(["direct.f"], TESTS)
require(direct.returncode == 0, "direct source import failed", direct)
require(direct.stdout.splitlines() == ["true", "true"], "direct source import output", direct)

work = Path(tempfile.mkdtemp(prefix=".ansi-consumer-", dir=TESTS))
try:
    (work / ".nift").mkdir()
    added = run(["add", str(PACKAGE)], work)
    require(added.returncode == 0, "nift add into fresh consumer failed", added)

    manifest = json.loads((work / "manifest.json").read_text(encoding="utf-8"))
    dependency = manifest.get("dependencies", {}).get("ansi", {})
    require(dependency.get("source") == str(PACKAGE), "nift add recorded the wrong source")
    require(dependency.get("ref") == "local", "nift add did not create a local dependency")

    shutil.copyfile(TESTS / "package.f", work / "package.f")
    contract = run(["package.f"], work)
    require(contract.returncode == 0, "installed package contract failed", contract)
    require(contract.stdout.strip() == "PASS ansi package contract", "installed package contract output", contract)

    privacy = {
        "private-normalize.f": '@import("ansi")\nprint(ansi.normalize([31]))\n',
        "private-method.f": '@import("ansi")\nprint(ansi.sequence([31]))\n',
        "private-styled.f": '@import("ansi")\nprint(ansi.styled("x", [31]))\n',
        "private-global.f": '@import("ansi")\nprint(ansi_csi)\n',
    }
    for name, source in privacy.items():
        (work / name).write_text(source, encoding="utf-8")
        hidden = run([name], work)
        require(hidden.returncode != 0, f"privacy check unexpectedly succeeded for {name}", hidden)

    malformed = {
        "sgr-no-argument.f": '@import("ansi")\nansi.sgr()\n',
        "sgr-extra-argument.f": '@import("ansi")\nansi.sgr(1, 31)\n',
        "wrap-no-code.f": '@import("ansi")\nansi.wrap("x")\n',
        "wrap-extra-argument.f": '@import("ansi")\nansi.wrap("x", 31, 1)\n',
        "helper-no-argument.f": '@import("ansi")\nansi.red()\n',
        "helper-extra-argument.f": '@import("ansi")\nansi.bold("x", "y")\n',
    }
    for name, source in malformed.items():
        (work / name).write_text(source, encoding="utf-8")
        rejected = run([name], work)
        require(rejected.returncode != 0, f"malformed call unexpectedly succeeded for {name}", rejected)

    repeated = run(["package.f"], work)
    require(repeated.returncode == 0, "repeated package execution failed", repeated)
    require(
        (repeated.stdout, repeated.stderr) == (contract.stdout, contract.stderr),
        "repeated package execution was not deterministic",
        repeated,
    )
finally:
    shutil.rmtree(work, ignore_errors=True)

print("PASS ansi package tests")
