#!/bin/bash

set -euo pipefail

REPO_URL="https://github.com/orangepi-xunlong/wiringOP-Python"
REPO_BRANCH="next"
PYTHON_BIN="${PYTHON_BIN:-python}"
TMP_DIR=""
KEEP_TMP="${KEEP_TMP:-0}"

cleanup() {
        if [ "$KEEP_TMP" = "1" ]; then
                if [ -n "$TMP_DIR" ]; then
                        echo "Keeping temp directory: $TMP_DIR"
                fi
                return
        fi

        if [ -n "$TMP_DIR" ] && [ -d "$TMP_DIR" ]; then
                rm -rf "$TMP_DIR"
        fi
}
trap cleanup EXIT

need_cmd() {
        if ! command -v "$1" >/dev/null 2>&1; then
                echo "ERROR: required command not found: $1"
                exit 1
        fi
}

for cmd in git swig sed mktemp "$PYTHON_BIN"; do
        need_cmd "$cmd"
done

echo "Installing wiringOP-Python into: $($PYTHON_BIN -c 'import sys; print(sys.executable)')"
echo "Repository: $REPO_URL (branch: $REPO_BRANCH)"

TMP_DIR="$(mktemp -d)"
WORK_DIR="$TMP_DIR/wiringOP-Python"

git clone --depth 1 --branch "$REPO_BRANCH" --recurse-submodules "$REPO_URL" "$WORK_DIR"
cd "$WORK_DIR"

"$PYTHON_BIN" -c 'import setuptools,sys; print("setuptools", setuptools.__version__); print("python", sys.version.split()[0])'

"$PYTHON_BIN" generate-bindings.py > bindings.i
sed -i '/getGpioNum/d;/piGpioLayoutOops/d' bindings.i
swig -python -threads -o wiringpi_wrap.c wiringpi.i

"$PYTHON_BIN" - <<'PY'
from pathlib import Path
import re
import sys

p = Path("wiringpi_wrap.c")
s = p.read_text()


def _print_diagnostics(reason: str) -> None:
        print("SWIG patch diagnostics:")
        print(f"  reason: {reason}")
        print(f"  file: {p}")
        print(f"  size_bytes: {len(s.encode('utf-8'))}")
        print(f"  signature_2_arg: {sig2}")
        print(f"  signature_3_arg: {sig3}")

        append_lines = []
        resultobj_lines = []
        for idx, raw in enumerate(s.splitlines(), start=1):
                if "SWIG_Python_AppendOutput(" in raw:
                        append_lines.append((idx, raw.strip()))
                if "resultobj = SWIG_Python_AppendOutput(" in raw:
                        resultobj_lines.append((idx, raw.strip()))

        print(f"  append_output_line_count: {len(append_lines)}")
        print(f"  resultobj_append_line_count: {len(resultobj_lines)}")

        print("  sample_append_output_lines:")
        for idx, raw in append_lines[:8]:
                print(f"    L{idx}: {raw}")

        print("  sample_resultobj_lines:")
        for idx, raw in resultobj_lines[:8]:
                print(f"    L{idx}: {raw}")

sig3 = re.search(
        r"SWIG_Python_AppendOutput\s*\(\s*PyObject\s*\*\s*result\s*,\s*PyObject\s*\*\s*obj\s*,\s*int\s+[A-Za-z_][A-Za-z0-9_]*\s*\)",
        s,
) is not None
sig2 = re.search(
        r"SWIG_Python_AppendOutput\s*\(\s*PyObject\s*\*\s*result\s*,\s*PyObject\s*\*\s*obj\s*\)",
        s,
) is not None

if not (sig2 or sig3):
        _print_diagnostics("signature detection failed")
        sys.exit("Failed to detect SWIG_Python_AppendOutput signature in wiringpi_wrap.c")

s2 = s
n = 0
patched_lines = []
for line in s2.splitlines(keepends=True):
        if "resultobj = SWIG_Python_AppendOutput(" not in line:
                patched_lines.append(line)
                continue

        updated = line
        if sig2:
                updated, local_n = re.subn(
                        r"(resultobj\s*=\s*SWIG_Python_AppendOutput\(\s*resultobj\s*,.*),\s*0\s*\);",
                        r"\1);",
                        updated,
                )
                n += local_n
        else:
                if not re.search(r",\s*0\s*\);", updated):
                        updated, local_n = re.subn(
                                r"(resultobj\s*=\s*SWIG_Python_AppendOutput\(\s*resultobj\s*,.*)\);",
                                r"\1, 0);",
                                updated,
                        )
                        n += local_n

        patched_lines.append(updated)

s2 = "".join(patched_lines)

print(f"Patched SWIG_Python_AppendOutput call(s): {n}")
if n == 0:
        if "resultobj = SWIG_Python_AppendOutput(" in s:
                _print_diagnostics("found call sites but no replacement applied")
        print("No SWIG_Python_AppendOutput call needed patching; continuing.")

p.write_text(s2)
PY

sed -i "s/sources += \['wiringpi.i'\]/sources += ['wiringpi_wrap.c']/" setup.py

"$PYTHON_BIN" setup.py install

"$PYTHON_BIN" -c 'import wiringpi; print("wiringpi import OK")'

echo "Done: wiringOP-Python installed successfully."