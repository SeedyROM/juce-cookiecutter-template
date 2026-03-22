{% raw %}#!/usr/bin/env python3
"""
Faust -> JUCE Parameter Bridge Code Generator

Reads Faust JSON metadata and generates:
  - FaustParams.h  (APVTS parameter layout + param ID constants)
  - FaustBridge.h  (bridge class: APVTS <-> Faust DSP zones)

Also invokes the Faust compiler to generate FaustDSP.h.

Usage:
    python3 codegen.py <path/to/file.dsp> --output <output_dir>
"""

import argparse
import json
import os
import re
import subprocess

from typing import Any


# ---------------------------------------------------------------------------
# Label -> C++ identifier conversion
# ---------------------------------------------------------------------------


def label_to_param_id(label: str) -> str:
    """Convert a Faust label like 'Pre-Delay (ms)' to a param ID like 'pre_delay_ms'."""
    s = label.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip("_")
    return s


def label_to_camel(label: str) -> str:
    """Convert a Faust label like 'Pre-Delay (ms)' to camelCase like 'preDelayMs'."""
    snake = label_to_param_id(label)
    parts = snake.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def label_to_pascal(label: str) -> str:
    """Convert a Faust label like 'Pre-Delay (ms)' to PascalCase like 'PreDelayMs'."""
    snake = label_to_param_id(label)
    return "".join(p.capitalize() for p in snake.split("_"))


# ---------------------------------------------------------------------------
# JSON traversal: flatten nested UI groups into a flat param list
# ---------------------------------------------------------------------------


def extract_params(ui_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Recursively extract all active UI widgets from the Faust JSON UI tree."""
    params = []
    for item in ui_items:
        item_type = item.get("type", "")
        if item_type in ("vgroup", "hgroup", "tgroup"):
            params.extend(extract_params(item.get("items", [])))
        elif item_type in ("hslider", "vslider", "nentry", "checkbox", "button"):
            params.append(item)
    return params


def get_sort_key(param: dict[str, Any]) -> str:
    """Extract the numeric ordering key from metadata (e.g. '01', '02')."""
    for meta_entry in param.get("meta", []):
        for key in meta_entry:
            if key.isdigit():
                return key
    return "99"


# ---------------------------------------------------------------------------
# Faust compiler invocation
# ---------------------------------------------------------------------------


def run_faust_cpp(
    dsp_path: str, output_path: str, class_name: str = "{% endraw %}{{ cookiecutter.faust_class_name }}{% raw %}"
) -> None:
    """Run faust to generate the C++ DSP class.

    Uses -scn "" to remove the dsp base class dependency, making the output
    self-contained (no Faust SDK headers needed to build).

    Optimization flags:
      -vec       : enable auto-vectorization (inner loops use vector size)
      -vs 32     : vector size = 32 samples (good balance for NEON/AVX2)
      -lv 1      : loop variant 1 (simple vector loop, best for compiler auto-vec)
      -ftz 0     : flush-to-zero OFF in generated code (handled by JUCE
                   ScopedNoDenormals + compiler -fdenormal-fp-math flag instead;
                   -ftz 2 has a known Clang rvalue-address bug with -vec)
      -mcd 0     : disable max copy delay optimization (better for vectorized code)
      -single    : single precision (float)

    Post-processes the output to inject #include "FaustDefs.h" so UI/Meta stubs
    are available.
    """
    cmd = [
        "faust",
        "-lang",
        "cpp",
        "-uim",
        "-cn",
        class_name,
        "-scn",
        "",
        "-vec",
        "-vs",
        "32",
        "-lv",
        "1",
        "-ftz",
        "0",
        "-mcd",
        "0",
        "-single",
        "-o",
        output_path,
        dsp_path,
    ]
    print(f"  Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    # Post-process the generated C++ source
    with open(output_path, "r") as f:
        content = f.read()

    # 1. Inject FaustDefs.h include after the header guard
    guard_pattern = f"#define  __{class_name}_H__"
    if guard_pattern in content:
        content = content.replace(
            guard_pattern,
            f'{guard_pattern}\n\n#include "FaustDefs.h"',
        )
    else:
        # Fallback: insert after first #define that looks like a header guard
        content = content.replace(
            "#endif \n\n/* link with",
            '#include "FaustDefs.h"\n\n#endif \n\n/* link with',
        )

    # 2. Silence -Wunused-parameter on Faust SIG helper methods.
    #    These have `int sample_rate` parameters that Faust never reads.
    content = re.sub(
        r"(void instanceInit\w+SIG\d+\(int sample_rate\) \{)",
        r"\1\n\t\t(void)sample_rate;",
        content,
    )

    with open(output_path, "w") as f:
        f.write(content)


def run_faust_json(dsp_path: str, output_dir: str) -> str:
    """Run faust -json to generate JSON metadata.

    Faust always writes <input>.json next to the source file, so we move
    it into the output directory afterwards to keep the source tree clean.
    Returns the final JSON file path.
    """
    cmd = ["faust", "-json", "-o", "/dev/null", dsp_path]
    print(f"  Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    src_json = dsp_path + ".json"
    if not os.path.exists(src_json):
        raise FileNotFoundError(f"Expected JSON output at {src_json}")

    dst_json = os.path.join(output_dir, os.path.basename(src_json))
    os.replace(src_json, dst_json)
    return dst_json


# ---------------------------------------------------------------------------
# Code generation: FaustDefs.h  (minimal stubs so FaustDSP.h compiles standalone)
# ---------------------------------------------------------------------------

FAUST_DEFS_HEADER = """\
// ==========================================================================
// AUTO-GENERATED by codegen.py -- do not edit manually.
// Minimal type stubs so the Faust-generated DSP compiles without the Faust SDK.
// ==========================================================================
#pragma once

#ifndef FAUSTFLOAT
#define FAUSTFLOAT float
#endif

// Forward declarations for types referenced by buildUserInterface() and metadata().
// We never call these methods -- the bridge writes to Faust zones directly --
// but the generated code declares them, so the types must exist.
struct UI {
    virtual ~UI() = default;
    virtual void openTabBox(const char*) {}
    virtual void openHorizontalBox(const char*) {}
    virtual void openVerticalBox(const char*) {}
    virtual void closeBox() {}
    virtual void addButton(const char*, FAUSTFLOAT*) {}
    virtual void addCheckButton(const char*, FAUSTFLOAT*) {}
    virtual void addVerticalSlider(const char*, FAUSTFLOAT*, FAUSTFLOAT, FAUSTFLOAT, FAUSTFLOAT, FAUSTFLOAT) {}
    virtual void addHorizontalSlider(const char*, FAUSTFLOAT*, FAUSTFLOAT, FAUSTFLOAT, FAUSTFLOAT, FAUSTFLOAT) {}
    virtual void addNumEntry(const char*, FAUSTFLOAT*, FAUSTFLOAT, FAUSTFLOAT, FAUSTFLOAT, FAUSTFLOAT) {}
    virtual void addHorizontalBargraph(const char*, FAUSTFLOAT*, FAUSTFLOAT, FAUSTFLOAT) {}
    virtual void addVerticalBargraph(const char*, FAUSTFLOAT*, FAUSTFLOAT, FAUSTFLOAT) {}
    virtual void addSoundfile(const char*, const char*, void**) {}
    virtual void declare(FAUSTFLOAT*, const char*, const char*) {}
};

struct Meta {
    virtual ~Meta() = default;
    virtual void declare(const char*, const char*) {}
};
"""


def generate_faust_defs_h() -> str:
    """Generate FaustDefs.h content."""
    return FAUST_DEFS_HEADER


# ---------------------------------------------------------------------------
# Code generation: FaustParams.h
# ---------------------------------------------------------------------------

PARAMS_HEADER = """\
// ==========================================================================
// AUTO-GENERATED by codegen.py from {dsp_name} -- do not edit manually.
// Regenerate by modifying the .dsp file and rebuilding.
// ==========================================================================
#pragma once

#include <juce_audio_processors/juce_audio_processors.h>

// --------------------------------------------------------------------------
// Parameter IDs (string constants for APVTS keys)
// --------------------------------------------------------------------------
namespace FaustParamIDs {{
{param_id_constants}
}} // namespace FaustParamIDs

// --------------------------------------------------------------------------
// Parameter Layout (creates the full APVTS ParameterLayout)
// --------------------------------------------------------------------------
namespace FaustParams {{

inline juce::AudioProcessorValueTreeState::ParameterLayout createLayout()
{{
    std::vector<std::unique_ptr<juce::RangedAudioParameter>> params;

{param_layout_entries}
    return {{ params.begin(), params.end() }};
}}

}} // namespace FaustParams
"""


def generate_params_h(params: list[dict[str, Any]], dsp_name: str) -> str:
    """Generate FaustParams.h content."""
    # Param ID constants
    id_lines = []
    for p in params:
        camel = label_to_camel(p["label"])
        pid = label_to_param_id(p["label"])
        id_lines.append(f'    static constexpr const char* {camel} = "{pid}";')

    # Param layout entries
    layout_lines = []
    for p in params:
        camel = label_to_camel(p["label"])
        ptype = p["type"]

        if ptype == "checkbox" or ptype == "button":
            layout_lines.append(
                f"    params.push_back(std::make_unique<juce::AudioParameterBool>(\n"
                f"        juce::ParameterID{{FaustParamIDs::{camel}, 1}},\n"
                f'        "{p["label"]}",\n'
                f"        false));"
            )
        else:
            init_val = float(p.get("init", 0))
            min_val = float(p.get("min", 0))
            max_val = float(p.get("max", 1))
            step_val = float(p.get("step", 0.01))
            layout_lines.append(
                f"    params.push_back(std::make_unique<juce::AudioParameterFloat>(\n"
                f"        juce::ParameterID{{FaustParamIDs::{camel}, 1}},\n"
                f'        "{p["label"]}",\n'
                f"        juce::NormalisableRange<float>({min_val}f, {max_val}f, {step_val}f),\n"
                f"        {init_val}f));"
            )

    return PARAMS_HEADER.format(
        dsp_name=dsp_name,
        param_id_constants="\n".join(id_lines),
        param_layout_entries="\n".join(layout_lines),
    )


# ---------------------------------------------------------------------------
# Code generation: FaustBridge.h
# ---------------------------------------------------------------------------

BRIDGE_HEADER = """\
// ==========================================================================
// AUTO-GENERATED by codegen.py from {dsp_name} -- do not edit manually.
// Regenerate by modifying the .dsp file and rebuilding.
// ==========================================================================
#pragma once

#include "FaustDefs.h"
#include "FaustDSP.h"
#include "FaustParams.h"

#include <juce_audio_processors/juce_audio_processors.h>

class FaustBridge {{
public:
    explicit FaustBridge(juce::AudioProcessorValueTreeState& apvts)
        : apvts_(apvts) {{}}

    /// Call from prepareToPlay
    void prepare(double sampleRate, int /*samplesPerBlock*/)
    {{
        dsp_.init(static_cast<int>(sampleRate));
    }}

    /// Call from processBlock -- syncs APVTS values to Faust zones, then computes
    void process(juce::AudioBuffer<float>& buffer)
    {{
        const int numSamples = buffer.getNumSamples();
        const int numChannels = buffer.getNumChannels();

        // Sync APVTS -> Faust parameter zones (once per block)
{sync_lines}

        // Set up channel pointers for Faust
        // Faust expects separate input/output arrays; we process in-place.
        float* channels[{num_channels}];
        for (int ch = 0; ch < std::min(numChannels, {num_channels}); ++ch)
            channels[ch] = buffer.getWritePointer(ch);

        dsp_.compute(numSamples, channels, channels);
    }}

    /// Access the underlying Faust DSP instance (for advanced use)
    {class_name}& getDSP() {{ return dsp_; }}
    const {class_name}& getDSP() const {{ return dsp_; }}

    // ----------------------------------------------------------------------
    // Named getters (read current APVTS values)
    // ----------------------------------------------------------------------
{getter_methods}

private:
    {class_name} dsp_;
    juce::AudioProcessorValueTreeState& apvts_;
}};
"""


def generate_bridge_h(
    params: list[dict[str, Any]],
    dsp_name: str,
    class_name: str = "{% endraw %}{{ cookiecutter.faust_class_name }}{% raw %}",
    num_inputs: int = 2,
    num_outputs: int = 2,
) -> str:
    """Generate FaustBridge.h content."""
    num_channels = max(num_inputs, num_outputs)

    # Sync lines: APVTS -> Faust zone
    sync_lines = []
    for p in params:
        camel = label_to_camel(p["label"])
        varname = p["varname"]  # e.g. "fHslider0", "fCheckbox0"
        ptype = p["type"]

        if ptype == "checkbox" or ptype == "button":
            sync_lines.append(
                f"        dsp_.{varname} = *apvts_.getRawParameterValue(FaustParamIDs::{camel}) > 0.5f ? 1.0f : 0.0f;"
            )
        else:
            sync_lines.append(
                f"        dsp_.{varname} = *apvts_.getRawParameterValue(FaustParamIDs::{camel});"
            )

    # Getter methods
    getter_lines = []
    for p in params:
        camel = label_to_camel(p["label"])
        pascal = label_to_pascal(p["label"])
        ptype = p["type"]

        if ptype == "checkbox" or ptype == "button":
            getter_lines.append(
                f"    bool get{pascal}() const {{ return *apvts_.getRawParameterValue(FaustParamIDs::{camel}) > 0.5f; }}"
            )
        else:
            getter_lines.append(
                f"    float get{pascal}() const {{ return *apvts_.getRawParameterValue(FaustParamIDs::{camel}); }}"
            )

    return BRIDGE_HEADER.format(
        dsp_name=dsp_name,
        class_name=class_name,
        num_channels=num_channels,
        sync_lines="\n".join(sync_lines),
        getter_methods="\n".join(getter_lines),
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Faust -> JUCE parameter bridge codegen"
    )
    parser.add_argument("dsp_file", help="Path to the .dsp file")
    parser.add_argument(
        "--output", "-o", required=True, help="Output directory for generated files"
    )
    parser.add_argument(
        "--class-name",
        default="{% endraw %}{{ cookiecutter.faust_class_name }}{% raw %}",
        help="C++ class name for the Faust DSP (default: {% endraw %}{{ cookiecutter.faust_class_name }}{% raw %})",
    )
    parser.add_argument(
        "--skip-faust",
        action="store_true",
        help="Skip running faust compiler (use existing .json and FaustDSP.h)",
    )
    args = parser.parse_args()

    dsp_path = os.path.abspath(args.dsp_file)
    output_dir = os.path.abspath(args.output)
    class_name = args.class_name
    dsp_name = os.path.basename(dsp_path)

    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Run Faust compiler
    faust_dsp_h = os.path.join(output_dir, "FaustDSP.h")
    if not args.skip_faust:
        print("[codegen] Running Faust compiler...")
        run_faust_cpp(dsp_path, faust_dsp_h, class_name)

        print("[codegen] Generating Faust JSON metadata...")
        json_path = run_faust_json(dsp_path, output_dir)
    else:
        json_path = os.path.join(output_dir, os.path.basename(dsp_path) + ".json")
        print(f"[codegen] Skipping Faust compiler, reading existing {json_path}")

    # Step 2: Parse JSON
    print(f"[codegen] Reading {json_path}...")
    with open(json_path, "r") as f:
        faust_json = json.load(f)

    ui_tree = faust_json.get("ui", [])
    params = extract_params(ui_tree)
    params.sort(key=get_sort_key)

    num_inputs = faust_json.get("inputs", 2)
    num_outputs = faust_json.get("outputs", 2)

    print(
        f"[codegen] Found {len(params)} parameters, {num_inputs} inputs, {num_outputs} outputs"
    )
    for p in params:
        pid = label_to_param_id(p["label"])
        print(f"  [{get_sort_key(p)}] {p['label']:20s} -> {pid:20s} ({p['varname']})")

    # Step 3: Generate FaustDefs.h (minimal stubs for Faust types)
    defs_h = generate_faust_defs_h()
    defs_path = os.path.join(output_dir, "FaustDefs.h")
    with open(defs_path, "w") as f:
        f.write(defs_h)
    print(f"[codegen] Wrote {defs_path}")

    # Step 4: Generate FaustParams.h
    params_h = generate_params_h(params, dsp_name)
    params_path = os.path.join(output_dir, "FaustParams.h")
    with open(params_path, "w") as f:
        f.write(params_h)
    print(f"[codegen] Wrote {params_path}")

    # Step 5: Generate FaustBridge.h
    bridge_h = generate_bridge_h(params, dsp_name, class_name, num_inputs, num_outputs)
    bridge_path = os.path.join(output_dir, "FaustBridge.h")
    with open(bridge_path, "w") as f:
        f.write(bridge_h)
    print(f"[codegen] Wrote {bridge_path}")

    print("[codegen] Done.")


if __name__ == "__main__":
    main()
{% endraw %}
