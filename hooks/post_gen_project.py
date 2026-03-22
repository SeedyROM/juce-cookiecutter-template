"""Post-generation hook: remove conditional files based on cookiecutter options."""

import os
import shutil

# Flags from cookiecutter.json
include_faust = "{{ cookiecutter.include_faust }}" == "yes"
include_ci = "{{ cookiecutter.include_ci }}" == "yes"

# Paths relative to the generated project root
FAUST_PATHS = [
    "dsp",
    "src/dsp/generated",
    "scripts/codegen.py",
    "docs/faust-codegen.md",
]

CI_PATHS = [
    ".github",
]


def remove_path(path: str) -> None:
    """Remove a file or directory if it exists."""
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.isfile(path):
        os.remove(path)


if not include_faust:
    for p in FAUST_PATHS:
        remove_path(p)

if not include_ci:
    for p in CI_PATHS:
        remove_path(p)
