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

"$PYTHON_BIN" -c 'from pathlib import Path; import re,sys; p=Path("wiringpi_wrap.c"); s=p.read_text(); s2,n=re.subn(r"SWIG_Python_AppendOutput\s*\(\s*resultobj\s*,\s*PyString_FromStringAndSize\s*\(\s*\(char \*\)\s*arg2\s*,\s*result\s*\)\s*\)", "SWIG_Python_AppendOutput(resultobj, PyString_FromStringAndSize((char *) arg2, result), 0)", s); print(f"Patched SWIG_Python_AppendOutput call(s): {n}"); n or sys.exit("Failed to patch SWIG_Python_AppendOutput call in wiringpi_wrap.c"); p.write_text(s2)'

sed -i "s/sources += \['wiringpi.i'\]/sources += ['wiringpi_wrap.c']/" setup.py

"$PYTHON_BIN" setup.py install

"$PYTHON_BIN" -c 'import wiringpi; print("wiringpi import OK")'

echo "Done: wiringOP-Python installed successfully."