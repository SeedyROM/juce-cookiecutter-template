"""Post-generation hook: remove conditional files based on cookiecutter options."""

import os
import shutil

# Flags from cookiecutter.json
include_faust = "{{ cookiecutter.include_faust }}" == "yes"
include_daisy = "{{ cookiecutter.include_daisy }}" == "yes"
include_ci = "{{ cookiecutter.include_ci }}" == "yes"
include_advanced_ui = "{{ cookiecutter.include_advanced_ui }}" == "yes"

# Paths relative to the generated project root
FAUST_PATHS = [
    "dsp",
    "src/dsp/generated",
    "scripts/codegen.py",
    "docs/faust-codegen.md",
]

DAISY_PATHS = [
    "daisy",
]

CI_PATHS = [
    ".github",
]

ADVANCED_UI_PATHS = [
    "src/ui",
    "src/components/controls/RotaryKnob.h",
    "src/components/controls/RotaryKnob.cpp",
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

    if include_daisy:
        print(
            "[WARNING] include_daisy=yes requires include_faust=yes "
            "(the Daisy scaffold builds the same generated DSP class the "
            "plugin uses) -- skipping the Daisy scaffold."
        )
        include_daisy = False

if not include_daisy:
    for p in DAISY_PATHS:
        remove_path(p)

if not include_ci:
    for p in CI_PATHS:
        remove_path(p)

if not include_advanced_ui:
    for p in ADVANCED_UI_PATHS:
        remove_path(p)
